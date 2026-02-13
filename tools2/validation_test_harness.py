"""
V66.1 Validation Test Harness
기존 원고에 대해 V66.1 검증 파이프라인을 실행하여 모순 탐지 능력을 평가합니다.

Usage:
    python tools2/validation_test_harness.py [project_path]
    python tools2/validation_test_harness.py projects/222재벌물222
"""

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

# Windows cp949 인코딩 문제 방지
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── 프로젝트 루트 설정 ──
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.core.db_manager import DBManager
from modules.core.genre_guards import create_genre_guard
from modules.domain.agents.state_tracker import StateTracker
from modules.validation.blocking_validator import BlockingValidator
from modules.validation.consistency_validator import ConsistencyValidator
from modules.validation.continuity_validator import ContinuityValidator
from modules.validation.scoring_validator import ScoringValidator

# RetrospectiveValidator 선택적 로드
try:
    from modules.validation.retrospective_validator import RetrospectiveValidator

    RETRO_AVAILABLE = True
except ImportError:
    RETRO_AVAILABLE = False


class MinimalContext:
    """Validator가 요구하는 최소 ProjectContext mock"""

    def __init__(self, db):
        self.db = db


def load_arcs_from_db(db: DBManager) -> list:
    """DB에서 Arc 목록 로드 (arc_no 순 정렬)"""
    raw = db.load_anchor("arcs", [])
    if isinstance(raw, dict):
        raw = raw.get("arcs", raw.get("arc_list", []))
    if not isinstance(raw, list):
        return []
    return sorted(raw, key=lambda a: a.get("arc_no", 0))


def build_state_tracker(arcs: list) -> StateTracker:
    """Arc 데이터로부터 StateTracker 상태를 누적 구축"""
    tracker = StateTracker()
    for arc in arcs:
        # 모든 state_changes 추출 → 내부 레지스트리 업데이트
        tracker.extract_all_state_changes(arc)
        # NPC 기본정보 (무기/레벨 등) 등록
        tracker.extract_npc_info_from_arc(arc)
        # 아이템 상태 레지스트리 등록
        tracker.extract_item_states_from_arc(arc)
        # NPC 대화 스타일 등록
        tracker.extract_npc_dialogue_styles_from_arc(arc)
        # 장르별 레지스트리 (던전/스킬쿨다운 등)
        tracker._populate_genre_registries_from_arc(arc)
    return tracker


def build_validation_context(
    ep_num: int,
    blueprint: dict,
    state_tracker: StateTracker,
    cumulative: dict,
    genre: str,
) -> dict:
    """에피소드별 validation_context 조립"""
    # NPC encyclopedia — validator는 items/locations도 dict 리스트 기대
    raw_items = cumulative.get("items", [])
    encyclopedia = {
        "npcs": [
            {"name": name, "status": info.get("status", "alive")} for name, info in state_tracker.npc_registry.items()
        ],
        "items": [{"name": it} if isinstance(it, str) else it for it in raw_items],
        "locations": [],
    }

    # 아이템 상태
    item_states = {name: info.get("condition", "정상") for name, info in state_tracker.item_state_registry.items()}

    # NPC 성격
    npc_personalities = {}
    for name, info in state_tracker.npc_registry.items():
        if info.get("personality_traits"):
            npc_personalities[name] = {
                "traits": info.get("personality_traits", ""),
                "motivation": info.get("primary_motivation", ""),
            }

    return {
        "encyclopedia": encyclopedia,
        "martial_hud": {},
        "karma_matrix": {},
        "asset_library": {},
        "npc_profiles": {},
        "prev_episode_events": [],
        "ep_num": ep_num,
        "genre": genre,
        "mode": "MANUSCRIPT",
        "blueprint": blueprint or {},
        "item_states": item_states,
        "npc_personalities": npc_personalities,
        "time_warnings": getattr(state_tracker, "_time_consistency_warnings", []),
    }


def run_blocking(validator, manuscript, ctx) -> list:
    """BlockingValidator 실행"""
    violations = []
    try:
        result = validator.validate(manuscript, ctx)
        for f in result.get("failures", []):
            if not f.get("passed", True):
                violations.append(
                    {
                        "tier": "BLOCKING",
                        "check": f.get("check", "unknown"),
                        "severity": f.get("severity", "HIGH"),
                        "reason": f.get("reason", ""),
                    }
                )
    except Exception as e:
        violations.append({"tier": "BLOCKING", "check": "ERROR", "severity": "ERROR", "reason": str(e)[:200]})
    return violations


def run_continuity(validator, ep_num, manuscript, ctx) -> list:
    """ContinuityValidator 실행 (prev_hud 없이 — 성격/시간 체크만)"""
    violations = []
    try:
        result = validator.validate(ep_num, manuscript, ctx, prev_hud=None)
        for v in result.get("violations", []):
            vtype = v.get("type", "unknown")
            if vtype == "no_prev_hud":
                continue  # prev_hud 없는 건 예상됨 — 스킵
            violations.append(
                {
                    "tier": "CONTINUITY",
                    "check": vtype,
                    "severity": v.get("severity", "MEDIUM"),
                    "reason": v.get("reason", ""),
                }
            )
        for w in result.get("warnings", []):
            wtype = w.get("type", "warning") if isinstance(w, dict) else "warning"
            if wtype == "no_prev_hud":
                continue
            violations.append(
                {
                    "tier": "CONTINUITY",
                    "check": wtype,
                    "severity": "WARNING",
                    "reason": w.get("reason", str(w)) if isinstance(w, dict) else str(w),
                }
            )
    except Exception as e:
        violations.append({"tier": "CONTINUITY", "check": "ERROR", "severity": "ERROR", "reason": str(e)[:200]})
    return violations


def run_consistency(validator, manuscript, ctx) -> list:
    """ConsistencyValidator 실행"""
    violations = []
    try:
        result = validator.validate(manuscript, ctx)
        for v in result.get("unjustifiable_violations", []):
            violations.append(
                {
                    "tier": "CONSISTENCY",
                    "check": v.get("category", "unknown"),
                    "severity": "CRITICAL",
                    "reason": v.get("reason", ""),
                }
            )
        for v in result.get("justifiable_violations", []):
            violations.append(
                {
                    "tier": "CONSISTENCY",
                    "check": v.get("category", "unknown"),
                    "severity": v.get("severity", "MEDIUM"),
                    "reason": v.get("reason", ""),
                }
            )
    except Exception as e:
        violations.append({"tier": "CONSISTENCY", "check": "ERROR", "severity": "ERROR", "reason": str(e)[:200]})
    return violations


def run_scoring(validator, manuscript, ctx) -> int:
    """ScoringValidator 실행 (Python-only, LLM 없이 /20점)"""
    try:
        result = validator.validate(manuscript, ctx)
        return result.get("total_score", -1)
    except Exception:
        return -1


def run_retrospective(validator, ep_num, manuscript, ctx) -> list:
    """RetrospectiveValidator 실행"""
    violations = []
    try:
        result = validator.validate_long_term_consistency(ep_num, manuscript, ctx)
        for v in result.get("violations", []):
            violations.append(
                {
                    "tier": "RETROSPECTIVE",
                    "check": v.get("type", "unknown"),
                    "severity": v.get("severity", "MEDIUM"),
                    "reason": v.get("reason", ""),
                }
            )
    except Exception as e:
        violations.append({"tier": "RETROSPECTIVE", "check": "ERROR", "severity": "ERROR", "reason": str(e)[:200]})
    return violations


def run_dead_npc_check(state_tracker, manuscript, ep_num) -> list:
    """StateTracker 사망 NPC 부활 체크"""
    violations = []
    try:
        results = state_tracker.check_dead_npc_in_manuscript(manuscript, ep_num)
        for v in results:
            reason = v.get("reason", str(v)) if isinstance(v, dict) else str(v)
            violations.append(
                {
                    "tier": "STATE_TRACKER",
                    "check": "dead_npc_resurrection",
                    "severity": "CRITICAL",
                    "reason": reason,
                }
            )
    except Exception:
        pass  # StateTracker에 해당 메서드 없을 수도 있음
    return violations


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════


def main():
    # 프로젝트 경로
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
        if not project_path.is_absolute():
            project_path = ROOT / project_path
    else:
        project_path = ROOT / "projects" / "222재벌물222"

    db_path = project_path / "project_data.db"
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        sys.exit(1)

    print("=" * 72)
    print(" V66.1 Validation Test Harness")
    print(f" Project : {project_path.name}")
    print(f" Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    # ── 1. 초기화 ──
    db = DBManager(db_path)
    context = MinimalContext(db)

    genre_info = db.load_anchor("genre_info", {})
    genre = genre_info.get("genre", "investment")
    print(f"\n  Genre: {genre}")

    # ── 2. Arc 로드 & StateTracker 구축 ──
    arcs = load_arcs_from_db(db)
    print(f"  Arcs : {len(arcs)}")

    state_tracker = build_state_tracker(arcs)
    dead_npcs = [n for n, info in state_tracker.npc_registry.items() if info.get("status") == "dead"]
    print(f"  NPCs : {len(state_tracker.npc_registry)} (dead: {len(dead_npcs)})")
    print(f"  Items: {len(state_tracker.item_state_registry)}")
    print(f"  Plots: resolved={len(state_tracker.resolved_plots)}, active={len(state_tracker.active_plots)}")
    print(f"  Entity destructions: {len(state_tracker.entity_destructions)}")

    # ── 3. Validator 초기화 ──
    guard = create_genre_guard(genre)
    blocking_v = BlockingValidator(context=context)
    continuity_v = ContinuityValidator(context=context)
    consistency_v = ConsistencyValidator(guard=guard, genre=genre)
    scoring_v = ScoringValidator(client=None, genre=genre)
    retrospective_v = RetrospectiveValidator(context=context) if RETRO_AVAILABLE else None

    # ── 4. 에피소드 범위 결정 ──
    ep_num = 1
    max_ep = 300
    manuscripts_found = 0
    while ep_num <= max_ep:
        ms = db.get_manuscript(ep_num)
        if ms:
            manuscripts_found = ep_num
        elif ep_num > manuscripts_found + 5:
            break
        ep_num += 1
    total_eps = manuscripts_found
    print(f"\n  Manuscripts: 1 ~ {total_eps} ({total_eps}화)")

    # ── 5. 검증 실행 ──
    all_results = []
    severity_counter = Counter()
    check_counter = Counter()
    tier_counter = Counter()

    print(f"\n{'─' * 72}")
    print(f" Validation Run ({total_eps} episodes)")
    print(f"{'─' * 72}\n")

    t0 = time.time()

    for ep in range(1, total_eps + 1):
        ms = db.get_manuscript(ep)
        if not ms:
            continue

        manuscript = ms.get("content", "") or ms.get("text", "")
        if not manuscript or len(manuscript) < 100:
            continue

        bp = db.get_blueprint(ep)
        cumulative = db.get_cumulative_bible(ep)

        ctx = build_validation_context(ep, bp, state_tracker, cumulative, genre)

        ep_violations = []

        # (a) Blocking
        ep_violations.extend(run_blocking(blocking_v, manuscript, ctx))
        # (b) Continuity
        ep_violations.extend(run_continuity(continuity_v, ep, manuscript, ctx))
        # (c) Consistency
        ep_violations.extend(run_consistency(consistency_v, manuscript, ctx))
        # (d) Retrospective (ep > 5)
        if retrospective_v and ep > 5:
            ep_violations.extend(run_retrospective(retrospective_v, ep, manuscript, ctx))
        # (e) Dead NPC
        ep_violations.extend(run_dead_npc_check(state_tracker, manuscript, ep))
        # (f) Scoring (Python-only)
        score = run_scoring(scoring_v, manuscript, ctx)

        # 집계
        for v in ep_violations:
            severity_counter[v["severity"]] += 1
            check_counter[v["check"]] += 1
            tier_counter[v["tier"]] += 1

        all_results.append(
            {
                "ep_num": ep,
                "violations": ep_violations,
                "violation_count": len(ep_violations),
                "score": score,
                "length": len(manuscript),
            }
        )

        # Per-episode 출력
        n_crit = sum(1 for v in ep_violations if v["severity"] in ("CRITICAL", "BLOCKING"))
        status = "CLEAN" if not ep_violations else f"{len(ep_violations)} violations"
        suffix = f"  ** CRITICAL: {n_crit}" if n_crit else ""
        print(f"  EP {ep:04d} | {len(manuscript):>6,}c | score {score:>3}/100 | {status}{suffix}")

    elapsed = time.time() - t0

    # ── 6. Summary Report ──
    print(f"\n{'=' * 72}")
    print(" SUMMARY REPORT")
    print(f"{'=' * 72}")

    total_v = sum(r["violation_count"] for r in all_results)
    clean = sum(1 for r in all_results if r["violation_count"] == 0)
    n_eps = len(all_results)

    print(f"\n  Episodes scanned : {n_eps}")
    print(f"  Total violations : {total_v}")
    print(f"  Clean episodes   : {clean}/{n_eps} ({clean / max(n_eps, 1) * 100:.1f}%)")
    print(f"  Elapsed          : {elapsed:.1f}s ({elapsed / max(n_eps, 1) * 1000:.0f}ms/ep)")

    # 심각도별
    print("\n  ── Severity Distribution ──")
    for sev in ["CRITICAL", "BLOCKING", "HIGH", "MAJOR", "MEDIUM", "LOW", "WARNING", "INFO", "ERROR"]:
        if severity_counter[sev]:
            bar = "#" * min(severity_counter[sev], 40)
            print(f"    {sev:>10}: {severity_counter[sev]:>4}  {bar}")

    # 티어별
    print("\n  ── Tier Distribution ──")
    for tier, cnt in tier_counter.most_common():
        print(f"    {tier:>15}: {cnt:>4}")

    # 체크별
    print("\n  ── Top Checks ──")
    for check, cnt in check_counter.most_common(15):
        print(f"    {check:>35}: {cnt:>4}")

    # 위반 상위 에피소드
    print("\n  ── Worst Episodes ──")
    worst = sorted(all_results, key=lambda r: r["violation_count"], reverse=True)[:10]
    for r in worst:
        if r["violation_count"] == 0:
            break
        types = Counter(v["check"] for v in r["violations"]).most_common(3)
        type_str = ", ".join(f"{c}({n})" for c, n in types)
        print(f"    EP {r['ep_num']:04d}: {r['violation_count']:>3} violations — {type_str}")

    # CRITICAL/BLOCKING 샘플
    print("\n  ── Critical/Blocking Samples (max 20) ──")
    samples = []
    for r in all_results:
        for v in r["violations"]:
            if v["severity"] in ("CRITICAL", "BLOCKING"):
                samples.append((r["ep_num"], v))
    for ep_n, v in samples[:20]:
        reason = v["reason"][:90].replace("\n", " ")
        print(f"    EP {ep_n:04d} [{v['tier']:>13}] {v['check']}: {reason}")

    # 점수 통계
    scores = [r["score"] for r in all_results if r["score"] >= 0]
    if scores:
        print("\n  ── Writing Score (LLM 미사용 fallback, /100) ──")
        print(f"    Average : {sum(scores) / len(scores):.1f}")
        print(f"    Min     : {min(scores)}")
        print(f"    Max     : {max(scores)}")

    # ── 7. JSON 리포트 저장 ──
    report_path = project_path / "validation_report.json"
    report = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "project": project_path.name,
            "genre": genre,
            "system_version": "V66.1",
            "elapsed_sec": round(elapsed, 1),
        },
        "summary": {
            "total_episodes": n_eps,
            "total_violations": total_v,
            "clean_episodes": clean,
            "severity": dict(severity_counter),
            "tier": dict(tier_counter),
            "checks": dict(check_counter.most_common(30)),
        },
        "episodes": all_results,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n  Report saved: {report_path}")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
