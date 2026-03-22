"""
utf8-hygiene: allow-file -- Korean regex patterns are intentional in this validator module.
[V60.56] Arc Draft Validator - Advisory Mode
Python 사전 검증 → LLM에게 정보 제공용 (REJECT 권한 없음)

목적:
- [V60.56 변경] Python은 정보 수집만, 최종 판정은 LLM(ConsensusValidator)에 위임
- 소설은 컨텍스트가 중요하므로 LLM이 문맥을 보고 판단해야 함
- Python 패턴 매칭의 오탐 문제 해결

검증 항목 (모두 advisory - 정보 제공만):
1. 필수 필드 존재 여부
2. 중복 아이템 획득 (이전 Arc들에서 이미 획득한 것)
3. 위치 연속성 (시작 위치 ≠ 이전 종료 위치)
4. 부상 상태 연속성 (급격한 회복 없이)
5. 수여물 타임라인 (수여 전 소지)
6. tactical_doc 최소 분량

[V60.56] valid는 항상 True, warnings만 수집하여 LLM에게 전달
"""

import logging
import re
from typing import Any

from modules.core.constants import Stage2Limits
from modules.core.genre_schema_builder import get_item_suffixes


class ArcDraftValidator:
    """
    [V60.11] Arc 초안 빠른 검증기

    ContinuityInspector 전 Python 기반 사전 검증
    비용: 0원 (LLM 미사용)
    """

    def __init__(self, genre: str = "") -> None:
        # [BUG-3] 장르별 아이템 접미사 SSOT
        self._item_suffixes = get_item_suffixes(genre)
        _suffix_group = "|".join(sorted((re.escape(s) for s in self._item_suffixes), key=len, reverse=True))
        _suffix_group = _suffix_group or r"아이템"

        # 아이템 획득 패턴 (장르 동적 접미사)
        self.acquire_patterns = [
            rf"([가-힣A-Za-z0-9]{{0,20}}(?:{_suffix_group}))[를을]?\s*(?:획득|얻|받|손에\s*넣|입수)",
            rf"(?:획득|얻|받|손에\s*넣)[가-힣A-Za-z0-9\s]*([가-힣A-Za-z0-9]{{0,20}}(?:{_suffix_group}))",
            rf"([가-힣A-Za-z0-9]{{0,20}}(?:{_suffix_group}))[를을]?\s*(?:하사|수여|받|얻)",
        ]

        # 수여물 키워드 (장르 공통 확장)
        self.grant_keywords = ["패", "권", "인장", "직위", "자격", "서", "부", "직", "명함", "계약서"]
        _grant_suffixes = sorted(set(self.grant_keywords + self._item_suffixes), key=len, reverse=True)
        _grant_group = "|".join(re.escape(s) for s in _grant_suffixes) or r"패|권|인장"

        # 수여물 패턴 (장르 동적)
        self.grant_patterns = [
            rf"([가-힣A-Za-z0-9\s]{{2,30}}(?:{_grant_group}))[를을]?\s*(?:하사|수여|받|얻|위임|부여)",
            rf"(?:하사|수여|받|얻|위임|부여)[가-힣A-Za-z0-9\s]*([가-힣A-Za-z0-9\s]{{2,30}}(?:{_grant_group}))",
            r"([가-힣]{2,20}직|[가-힣]{2,20}장)[에으로]?\s*(?:임명|취임|올|받)",
        ]

        # 무기/핵심 아이템 키워드 (장르 동적)
        self.weapon_keywords = list(self._item_suffixes)

    def _safe_tactical(self, arc: dict) -> str:
        """[V60.37] tactical_doc을 안전하게 문자열로 변환"""
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, str):
            return tactical
        if isinstance(tactical, dict):
            try:
                return "\n".join(str(v) for v in tactical.values() if v)
            except Exception:
                return str(tactical)
        return str(tactical) if tactical else ""

    def validate(
        self,
        arc: dict,
        prev_arcs: list[dict],
        constraint_block: str = "",
        state_tracker=None,  # [V60.94] StateTracker 인스턴스 (NPC 생사 검증용)
        forbidden_items: list[str] | None = None,  # [BUG-3] 구조적 금지 아이템 (선택)
    ) -> dict[str, Any]:
        """
        Arc 초안 검증

        Args:
            arc: 검증할 Arc 데이터
            prev_arcs: 이전 Arc들
            constraint_block: 제약 조건 블록
            state_tracker: [V60.94] StateTracker 인스턴스 (죽은 NPC 검증용)

        Returns:
            {
                "valid": bool,
                "score": int (0-100),
                "critical_issues": [...],
                "warnings": [...],
                "suggestions": [...]
            }
        """
        critical_issues = []
        warnings = []
        suggestions = []
        score = 100
        reject_reason = None  # [V60.94] REJECT 사유

        # [V60.74] Arc 1 처리 명시적 로그
        if not prev_arcs:
            logging.info(" [ArcDraftValidator] Arc 1 - 연속성 검증 스킵, 구조만 검증")

        # [V60.94] 0. 죽은 NPC 등장 검증 - 유일한 REJECT 사유
        if state_tracker and prev_arcs:
            dead_npc_result = self._validate_dead_npc_appearance(arc, state_tracker)
            if dead_npc_result["critical"]:
                critical_issues.extend(dead_npc_result["critical"])
                score -= dead_npc_result["penalty"]
                reject_reason = dead_npc_result["critical"][0]  # 첫 번째 위반 사유

        # 1. 필수 필드 검증
        field_result = self._validate_required_fields(arc)
        score -= field_result["penalty"]
        critical_issues.extend(field_result["critical"])
        warnings.extend(field_result["warnings"])

        # 2. 중복 아이템 획득 검증
        if prev_arcs:
            duplicate_result = self._validate_duplicate_acquisition(arc, prev_arcs)
            score -= duplicate_result["penalty"]
            critical_issues.extend(duplicate_result["critical"])

        # 3. 위치 연속성 검증
        if prev_arcs:
            location_result = self._validate_location_continuity(arc, prev_arcs[-1])
            score -= location_result["penalty"]
            if location_result["critical"]:
                critical_issues.extend(location_result["critical"])
            warnings.extend(location_result["warnings"])

        # 4. 부상 상태 연속성 검증
        if prev_arcs:
            injury_result = self._validate_injury_continuity(arc, prev_arcs[-1])
            score -= injury_result["penalty"]
            warnings.extend(injury_result["warnings"])

        # 5. 수여물 타임라인 검증
        if prev_arcs:
            grant_result = self._validate_grant_timeline(arc, prev_arcs)
            score -= grant_result["penalty"]
            critical_issues.extend(grant_result["critical"])

        # 6. tactical_doc 분량 검증
        tactical_result = self._validate_tactical_doc(arc)
        score -= tactical_result["penalty"]
        if tactical_result["critical"]:
            critical_issues.extend(tactical_result["critical"])
        warnings.extend(tactical_result["warnings"])
        suggestions.extend(tactical_result["suggestions"])

        # 7. 제약 블록 검증
        if constraint_block or forbidden_items or arc.get("_forbidden_items"):
            constraint_result = self._validate_against_constraints(
                arc,
                constraint_block,
                forbidden_items=forbidden_items,
            )
            score -= constraint_result["penalty"]
            critical_issues.extend(constraint_result["critical"])

        # [V60.94] 죽은 NPC 등장만 REJECT, 나머지는 advisory
        # critical_issues를 advisory_issues로 변환 (LLM에게 전달할 정보)
        advisory_issues = [c for c in critical_issues if "사망한" not in c and "죽은" not in c]
        advisory_issues.extend(f"[warning] {w}" for w in warnings)
        advisory_issues.extend(f"[suggestion] {s}" for s in suggestions)

        # [BUG-5] advisory_issues 세부 내용 로깅 (디버깅 지원)
        if advisory_issues:
            logging.warning(f" [ArcDraftValidator] advisory 이슈 {len(advisory_issues)}건:")
            for _ai in advisory_issues[:10]:
                logging.warning(f"   - {str(_ai)[:200]}")

        # [V60.94] 죽은 NPC 등장만 REJECT 가능
        is_valid = reject_reason is None

        return {
            "valid": is_valid,
            "score": max(0, score),
            "critical_issues": [reject_reason] if reject_reason else [],  # [V60.94] 죽은 NPC만 REJECT
            "advisory_issues": advisory_issues,  # [V60.56] LLM에게 전달할 정보
            "warnings": warnings,
            "suggestions": suggestions,
            "reject_reason": reject_reason,  # [V60.94] REJECT 사유
        }

    def _validate_required_fields(self, arc: dict) -> dict:
        """필수 필드 검증"""
        critical = []
        warnings = []
        penalty = 0

        # [V60.41] 필수 필드는 WARNING으로 변경 (재생성으로 해결 가능)
        required_fields = ["arc_no", "tactical_doc", "joint_docs", "state_constraints", "ep_start", "ep_end"]
        # [V60.42 Fix] 중요 필드 정의 추가
        # [BUG-F] protagonist_items도 허용 (API 스키마 정합)
        required_important = ["ep_count", "items_acquired", "protagonist_items", "grants_received"]

        for field in required_fields:
            if field not in arc or not arc[field]:
                warnings.append(f"필수 필드 누락: {field}")
                penalty += 10

        for field in required_important:
            # 중요 필드는 arc 또는 state_constraints 내부에 있을 수 있음
            value = arc.get(field) or arc.get("state_constraints", {}).get(field)
            if not value and value != 0:  # 0은 유효한 값
                warnings.append(f"중요 필드 누락: {field}")
                penalty += 5

        return {"penalty": penalty, "critical": critical, "warnings": warnings}

    def _validate_duplicate_acquisition(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """중복 아이템 획득 검증"""
        critical = []
        penalty = 0

        # [Sweep-Codex] dict 아이템 방어 (unhashable type 방지)
        def _ikey(x):
            return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)

        # 이전 Arc들에서 획득한 모든 아이템 수집
        all_acquired = set()
        for prev_arc in prev_arcs:
            # state_constraints.items_acquired
            # [BUG-F] protagonist_items 우선 폴백
            _psc_adv = prev_arc.get("state_constraints", {})
            items = _psc_adv.get("protagonist_items") or _psc_adv.get("items_acquired", [])
            if isinstance(items, list):
                all_acquired.update(_ikey(i) for i in items)

            # joint_docs.physical_inventory
            inventory = prev_arc.get("joint_docs", {}).get("physical_inventory", [])
            if isinstance(inventory, list):
                all_acquired.update(_ikey(i) for i in inventory)
            elif isinstance(inventory, str):
                all_acquired.update([i.strip() for i in inventory.split(",") if i.strip()])

            # tactical_doc에서 획득 패턴 추출
            tactical = self._safe_tactical(prev_arc)
            for pattern in self.acquire_patterns:
                matches = re.findall(pattern, tactical)
                for m in matches:
                    item = m.strip() if isinstance(m, str) else m[0].strip() if m else None
                    if item and 2 <= len(item) <= 20:
                        all_acquired.add(item)

        # 현재 Arc의 획득 아이템
        # [BUG-F] protagonist_items 우선 폴백
        _csc_dup = arc.get("state_constraints", {})
        current_items = _csc_dup.get("protagonist_items") or _csc_dup.get("items_acquired", [])
        if not isinstance(current_items, list):
            current_items = [current_items] if isinstance(current_items, str) else []
        tactical = self._safe_tactical(arc)

        # tactical_doc에서도 획득 패턴 추출
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, tactical)
            for m in matches:
                item = m.strip() if isinstance(m, str) else m[0].strip() if m else None
                if item and 2 <= len(item) <= 20:
                    current_items.append(item)

        # 중복 검사
        for item in current_items:
            if not item:
                continue
            for prev_item in all_acquired:
                if self._is_same_item(item, prev_item):
                    critical.append(f"중복 획득 시도: '{item}' (이미 획득됨)")
                    penalty += 30
                    break

        return {"penalty": penalty, "critical": critical}

    def _validate_location_continuity(self, arc: dict, prev_arc: dict) -> dict:
        """위치 연속성 검증"""
        critical = []
        warnings = []
        penalty = 0

        prev_joint = prev_arc.get("joint_docs", {})
        prev_location = prev_joint.get("final_location", "")

        curr_state = arc.get("state_constraints", {}).get("arc_start_state", {})
        curr_location = curr_state.get("location", "")

        if prev_location and curr_location:
            # 위치가 완전히 다른 경우
            if not self._locations_compatible(prev_location, curr_location):
                # 이동 시간이 있는지 tactical_doc 검사
                tactical = self._safe_tactical(arc)
                has_travel = any(kw in tactical[:500] for kw in ["이동", "도착", "길을", "향해", "출발"])

                if not has_travel:
                    warnings.append(
                        f"위치 불연속: 이전='{prev_location[:20]}' → 현재='{curr_location[:20]}' (이동 장면 필요)"
                    )
                    penalty += 10

        return {"penalty": penalty, "critical": critical, "warnings": warnings}

    def _validate_injury_continuity(self, arc: dict, prev_arc: dict) -> dict:
        """부상 상태 연속성 검증"""
        warnings = []
        penalty = 0

        # [V60.13 FIX] arc_end_state 우선 사용
        prev_state = prev_arc.get("state_constraints", {})
        prev_end_state = prev_state.get("arc_end_state", {})
        prev_shadow = prev_arc.get("status_shadow", {})

        # arc_end_state 우선, 없으면 shadow 폴백
        prev_injury = prev_end_state.get("injuries") or prev_shadow.get("expected_injuries", "")

        # 이전 부상이 있는데 현재 시작 상태에 부상이 없으면 경고
        if prev_injury and prev_injury not in ["없음", "경미", "완치"]:
            curr_start = arc.get("state_constraints", {}).get("arc_start_state", {})
            curr_injury = curr_start.get("injuries", "")

            if not curr_injury or curr_injury in ["없음", ""]:
                # 회복 장면이 있는지 확인
                tactical = arc.get("tactical_doc", "")
                if isinstance(tactical, dict):
                    tactical = "\n".join(f"{k}: {v}" for k, v in tactical.items())
                has_recovery = any(kw in tactical[:1000] for kw in ["회복", "치료", "조식", "휴식", "요양"])

                if not has_recovery:
                    warnings.append(f"부상 급격 회복: 이전='{prev_injury[:30]}' → 현재='없음' (회복 장면 권장)")
                    penalty += 5

        return {"penalty": penalty, "warnings": warnings}

    def _validate_grant_timeline(self, arc: dict, prev_arcs: list[dict]) -> dict:
        """수여물 타임라인 검증"""
        critical = []
        penalty = 0

        # 이전 Arc들에서 수여된 것들 수집
        all_granted = set()
        for prev_arc in prev_arcs:
            grants = prev_arc.get("state_constraints", {}).get("grants_received", [])
            if isinstance(grants, list):
                all_granted.update(grants)

            tactical = self._safe_tactical(prev_arc)
            for pattern in self.grant_patterns:
                matches = re.findall(pattern, tactical)
                for m in matches:
                    grant = m.strip() if isinstance(m, str) else m[0].strip() if m else None
                    if grant and 2 <= len(grant) <= 20:
                        all_granted.add(grant)

        # 현재 Arc에서 이미 수여된 것을 다시 수여받으려 하는지 검사
        current_grants = arc.get("state_constraints", {}).get("grants_received", [])
        if isinstance(current_grants, list):
            for grant in current_grants:
                if grant and grant in all_granted:
                    critical.append(f"중복 수여 시도: '{grant}' (state_constraints에서 발견)")
                    penalty += 25
        tactical = self._safe_tactical(arc)

        for pattern in self.grant_patterns:
            matches = re.findall(pattern, tactical)
            for m in matches:
                grant = m.strip() if isinstance(m, str) else m[0].strip() if m else None
                if grant and grant in all_granted:
                    critical.append(f"중복 수여 시도: '{grant}' (이미 수여됨)")
                    penalty += 25

        return {"penalty": penalty, "critical": critical}

    def _coerce_tactical_doc_value(self, arc: dict) -> tuple[str, list[str], int]:
        tactical = arc.get("tactical_doc", "")
        warnings = []
        penalty = 0
        if isinstance(tactical, str):
            return tactical, warnings, penalty

        if isinstance(tactical, dict):
            try:
                tactical = "\n".join(str(value) for value in tactical.values() if value)
                warnings.append("tactical_doc\uc774 dict \ud615\ud0dc\ub85c \ubc18\ud658\ub428 - \uc790\ub3d9 \ubcc0\ud658 \uc2dc\ub3c4")
            except Exception:
                tactical = str(tactical)
        else:
            tactical = str(tactical) if tactical else ""

        if len(tactical) < 100:
            warnings.append(
                f"tactical_doc \ud615\uc2dd \uc624\ub958: \ubb38\uc790\uc5f4\uc774 \uc544\ub2cc {type(arc.get('tactical_doc')).__name__} \ud0c0\uc785 \ubc18\ud658"
            )
            penalty += 20
        return tactical, warnings, penalty

    def _resolve_tactical_doc_expectations(self, arc: dict) -> tuple[int, int, list[int], int, int]:
        ep_start = arc.get("ep_start", 1)
        try:
            ep_count = int(arc.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT))
        except (TypeError, ValueError):
            ep_count = Stage2Limits.DEFAULT_EP_COUNT

        expected_eps = list(range(ep_start, ep_start + ep_count))
        min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE
        warn_length = ep_count * 400
        return ep_start, ep_count, expected_eps, min_length, warn_length

    @staticmethod
    def _validate_tactical_length(length: int, *, ep_count: int, min_length: int, warn_length: int) -> tuple[list[str], int]:
        warnings = []
        penalty = 0
        if length < warn_length:
            warnings.append(
                f"tactical_doc \ubd84\ub7c9 \uc2ec\uac01 \ubbf8\ub2ec: {length}\uc790 (\ucd5c\uc18c {min_length}\uc790 = {ep_count}\ud654 \xd7 500\uc790)"
            )
            penalty += 25
        elif length < min_length:
            warnings.append(f"tactical_doc \ubd84\ub7c9 \ubd80\uc871: {length}\uc790 (\uad8c\uc7a5 {min_length}\uc790)")
            penalty += 10
        return warnings, penalty

    def _validate_tactical_episode_layout(
        self, episode_sections: dict[int, str], expected_eps: list[int]
    ) -> tuple[list[str], int]:
        warnings = []
        penalty = 0

        missing_eps = [ep_no for ep_no in expected_eps if ep_no not in episode_sections]
        if missing_eps:
            warnings.append(f"\ub204\ub77d\ub41c \ud654: {missing_eps} (\ud544\uc218: {expected_eps})")
            penalty += 15

        min_ep_length = 300
        short_eps = [f"{ep_no}\ud654({len(content)}\uc790)" for ep_no, content in episode_sections.items() if len(content) < min_ep_length]
        if short_eps:
            warnings.append(f"\ubd84\ub7c9 \ubd80\uc871 \ud654: {', '.join(short_eps)} (\ucd5c\uc18c {min_ep_length}\uc790)")
            penalty += len(short_eps) * 3

        if len(episode_sections) >= 2:
            lengths = [len(content) for content in episode_sections.values()]
            max_len = max(lengths)
            min_len = max(min(lengths), 1)
            if max_len / min_len > 5:
                warnings.append(
                    f"\ud654\ubcc4 \ubd84\ub7c9 \ubd88\uade0\ud615: \ucd5c\uc18c {min_len}\uc790 vs \ucd5c\ub300 {max_len}\uc790 (5\ubc30 \ucd08\uacfc)"
                )
                penalty += 5

        if episode_sections:
            found_eps = sorted(episode_sections.keys())
            if found_eps != expected_eps[: len(found_eps)]:
                warnings.append(f"\ud654 \uc21c\uc11c \ubd88\uc77c\uce58: \ubc1c\uacac={found_eps}, \uae30\ub300={expected_eps}")
                penalty += 5

        return warnings, penalty

    def _validate_tactical_episode_density(
        self, episode_sections: dict[int, str]
    ) -> tuple[list[str], list[str], int]:
        warnings = []
        suggestions = []
        penalty = 0

        sparse_eps = []
        for ep_no, content in episode_sections.items():
            has_dialogue = '"' in content or '"' in content
            has_action = any(kw in content for kw in ["\ud588\ub2e4", "\ud588\ub2e4", "\ub410\ub2e4", "\uc600\ub2e4", "\ud55c\ub2e4", "\ubcf8\ub2e4", "\uac14\ub2e4", "\uc654\ub2e4"])
            if not has_dialogue and not has_action and len(content) > 50:
                sparse_eps.append(ep_no)
        if sparse_eps:
            suggestions.append(f"\ub0b4\uc6a9 \ube48\uc57d\ud55c \ud654: {sparse_eps} (\ub300\uc0ac/\ud589\ub3d9 \ucd94\uac00 \uad8c\uc7a5)")

        low_beat_eps = []
        for ep_no, content in episode_sections.items():
            beat_count = self._count_tactical_beats(content)
            if beat_count < 3 and len(content) > 100:
                low_beat_eps.append(f"{ep_no}\ud654({beat_count}\ube44\ud2b8)")
        if low_beat_eps:
            warnings.append(f"\ube44\ud2b8 \ubd80\uc871 \ud654: {', '.join(low_beat_eps)} (\ucd5c\uc18c 3\ube44\ud2b8 \ud544\uc694)")
            penalty += len(low_beat_eps) * 2

        incomplete_eps = []
        for ep_no, content in episode_sections.items():
            missing_elements = self._check_structural_elements(content)
            if missing_elements and len(content) > 200:
                incomplete_eps.append(f"{ep_no}\ud654({','.join(missing_elements)})")
        if incomplete_eps:
            suggestions.append(f"\uad6c\uc870 \ubbf8\ube44 \ud654: {', '.join(incomplete_eps[:3])}")

        return warnings, suggestions, penalty

    def _validate_tactical_episode_metadata(
        self, episode_sections: dict[int, str], arc: dict
    ) -> tuple[list[str], int]:
        warnings = []
        penalty = 0

        actual_ep_count = len(episode_sections)
        declared_ep_count = arc.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)
        if actual_ep_count > 0 and abs(actual_ep_count - declared_ep_count) >= 2:
            warnings.append(f"ep_count \ubd88\uc77c\uce58: \uc120\uc5b8={declared_ep_count}, \uc2e4\uc81c={actual_ep_count}")
            penalty += 5

        checkpoint_result = self._validate_state_checkpoints(episode_sections, arc)
        if checkpoint_result.get("missing_checkpoints"):
            warnings.append(
                f"\uc0c1\ud0dc \uccb4\ud06c\ud3ec\uc778\ud2b8 \ub204\ub77d: {checkpoint_result['missing_checkpoints'][:3]}"
            )
            penalty += len(checkpoint_result.get("missing_checkpoints", [])) * 2
        if checkpoint_result.get("state_mismatches"):
            warnings.append(
                f"\ud654\uac04 \uc0c1\ud0dc \ubd88\uc77c\uce58: {checkpoint_result['state_mismatches'][:2]}"
            )
            penalty += len(checkpoint_result.get("state_mismatches", [])) * 3

        return warnings, penalty

    @staticmethod
    def _collect_tactical_relationship_npcs(arc: dict) -> list[str]:
        npc_names: set[str] = set()
        state_constraints = arc.get("state_constraints") or {}

        for rel in state_constraints.get("relationship_changes") or []:
            if isinstance(rel, dict):
                npc_name = rel.get("target") or rel.get("npc")
                if npc_name and isinstance(npc_name, str) and len(npc_name) >= 2:
                    npc_names.add(npc_name)

        for rel in (arc.get("state_changes") or {}).get("relationship_changes") or []:
            if isinstance(rel, dict):
                npc_name = rel.get("target") or rel.get("npc")
                if npc_name and isinstance(npc_name, str) and len(npc_name) >= 2:
                    npc_names.add(npc_name)

        return sorted(npc_names)

    def _validate_tactical_relationship_mentions(self, tactical: str, arc: dict) -> tuple[list[str], int]:
        warnings = []
        penalty = 0
        if not tactical or len(tactical) <= 500:
            return warnings, penalty

        npc_names = self._collect_tactical_relationship_npcs(arc)
        if npc_names:
            mentioned = sum(1 for npc_name in npc_names if npc_name in tactical)
            if mentioned == 0:
                warnings.append(
                    f"tactical_doc\uc5d0 \uad00\uacc4 \ubcc0\ud654 NPC \ubbf8\uc5b8\uae09: {', '.join(npc_names[:3])}"
                )
                penalty += 3
        return warnings, penalty

    @staticmethod
    def _validate_tactical_action_density(tactical: str) -> list[str]:
        suggestions = []
        if tactical and len(tactical) > 800:
            action_count = len(
                re.findall(
                    r"[\uac00-\ud7a3]+(?:\ud588\ub2e4|\ud55c\ub2e4|\ub41c\ub2e4|\ubc1b\ub294\ub2e4|\uc5bb\ub294\ub2e4|\ubc1c\uacac\ud55c\ub2e4|\ub3c4\ucc29\ud55c\ub2e4|\ub9cc\ub09c\ub2e4|\ub5a0\ub09c\ub2e4|\uc2f8\uc6b4\ub2e4|\uc8fd\ub294\ub2e4|\uae68\ub2eb\ub294\ub2e4)",
                    tactical,
                )
            )
            sentence_approx = max(1, tactical.count("\ub2e4.") + tactical.count("\ub2e4\n"))
            if sentence_approx >= 5 and action_count < max(2, sentence_approx // 4):
                suggestions.append(
                    f"tactical_doc \uad6c\uccb4\uc131 \ubd80\uc871: \ud589\ub3d9 \ud45c\ud604 {action_count}\uac1c / ~{sentence_approx}\ubb38\uc7a5"
                )
        return suggestions

    def _validate_tactical_doc(self, arc: dict) -> dict:
        """[V60.29] tactical_doc 분량 + 화별 분할 검증 강화"""
        critical = []
        warnings = []
        suggestions = []
        penalty = 0

        tactical, coercion_warnings, coercion_penalty = self._coerce_tactical_doc_value(arc)
        warnings.extend(coercion_warnings)
        penalty += coercion_penalty

        ep_start, ep_count, expected_eps, min_length, warn_length = self._resolve_tactical_doc_expectations(arc)
        length_warnings, length_penalty = self._validate_tactical_length(
            len(tactical),
            ep_count=ep_count,
            min_length=min_length,
            warn_length=warn_length,
        )
        warnings.extend(length_warnings)
        penalty += length_penalty

        episode_sections = self._extract_episode_sections(tactical, ep_start, ep_count)

        layout_warnings, layout_penalty = self._validate_tactical_episode_layout(episode_sections, expected_eps)
        warnings.extend(layout_warnings)
        penalty += layout_penalty

        density_warnings, density_suggestions, density_penalty = self._validate_tactical_episode_density(episode_sections)
        warnings.extend(density_warnings)
        suggestions.extend(density_suggestions)
        penalty += density_penalty

        metadata_warnings, metadata_penalty = self._validate_tactical_episode_metadata(episode_sections, arc)
        warnings.extend(metadata_warnings)
        penalty += metadata_penalty

        relationship_warnings, relationship_penalty = self._validate_tactical_relationship_mentions(tactical, arc)
        warnings.extend(relationship_warnings)
        penalty += relationship_penalty

        suggestions.extend(self._validate_tactical_action_density(tactical))
        return {"penalty": penalty, "critical": critical, "warnings": warnings, "suggestions": suggestions}

    def _validate_state_checkpoints(self, episode_sections: dict[int, str], arc: dict) -> dict:
        """[V60.40] 화간 상태 체크포인트 검증 - StateLocked 개념 흡수"""
        missing_checkpoints = []
        state_mismatches = []

        # 상태 관련 키워드
        state_keywords = ["위치:", "내공:", "부상:", "소지품:", "획득:", "소모:", "종료 상태", "시작 상태"]

        sorted_eps = sorted(episode_sections.keys())

        for i, ep_no in enumerate(sorted_eps):
            content = episode_sections[ep_no]

            # 시작 상태 체크 (첫 화 제외하고는 이전 화 종료 상태 언급 필요)
            if i > 0:
                has_start_state = any(kw in content for kw in ["시작 상태", "이전", "직전", "에서 이어"])
                if not has_start_state and len(content) > 300:
                    pass  # [BUG-4] 복잡한 연속성 검증은 LLM에 위임

            # 종료 상태 체크 (마지막 화 포함 모든 화)
            has_state_info = sum(1 for kw in state_keywords if kw in content)

            # 상태 정보가 2개 미만이면 체크포인트 부족
            if has_state_info < 2 and len(content) > 300:
                missing_checkpoints.append(f"{ep_no}화")

        return {"missing_checkpoints": missing_checkpoints, "state_mismatches": state_mismatches}

    def _count_tactical_beats(self, content: str) -> int:
        """[V60.30] 화 내용에서 전술 비트 수 카운트"""
        beat_count = 0

        # 번호 매겨진 비트 패턴: (1), (2), ①, ②, 1., 2.
        numbered_patterns = [
            r"\([1-9]\)",  # (1), (2), ...
            r"[①②③④⑤⑥⑦⑧⑨⑩]",  # ①, ②, ...
            r"\b[1-9]\.\s",  # 1. 2. ...
        ]
        for pattern in numbered_patterns:
            matches = re.findall(pattern, content)
            beat_count = max(beat_count, len(matches))

        # 구조적 키워드 비트
        structure_keywords = [
            "공간",
            "장소",
            "배경",  # 공간 묘사
            "행동",
            "대결",
            "전투",
            "수련",  # 인과 마디
            "반응",
            "충격",
            "놀라",
            "경악",  # 파동 전이
            "상태",
            "변화",
            "획득",
            "소모",  # 연속성 체크
        ]
        keyword_beats = sum(1 for kw in structure_keywords if kw in content)

        # 더 많은 것 사용
        return max(beat_count, min(keyword_beats // 2, 5))

    def _check_structural_elements(self, content: str) -> list[str]:
        """[V60.30] 화 내용에서 필수 구조 요소 확인"""
        missing = []

        # 1. 공간 묘사 키워드
        space_keywords = [
            "장소",
            "공간",
            "객잔",
            "무기고",
            "광장",
            "산",
            "강",
            "숲",
            "도시",
            "마을",
            "방",
            "청",
            "관",
            "전각",
            "동굴",
            "골목",
            "거리",
            "길",
        ]
        if not any(kw in content for kw in space_keywords):
            # 위치 관련 조사 패턴도 체크
            if not re.search(r"[가-힣]+(?:에서|으로|에|를)", content):
                missing.append("공간")

        # 2. 인과/행동 키워드
        action_keywords = [
            "했다",
            "한다",
            "된다",
            "였다",
            "갔다",
            "왔다",
            "봤다",
            "보았다",
            "치다",
            "막다",
            "피하다",
            "공격",
            "방어",
            "수련",
        ]
        if not any(kw in content for kw in action_keywords):
            missing.append("행동")

        # 3. 상태 변화 키워드
        state_keywords = [
            "획득",
            "소모",
            "부상",
            "회복",
            "상승",
            "하락",
            "변화",
            "성장",
            "내공",
            "경지",
            "상처",
            "치료",
        ]
        if not any(kw in content for kw in state_keywords):
            missing.append("상태")

        return missing

    def _extract_episode_sections(self, tactical: str, ep_start: int, ep_count: int) -> dict[int, str]:
        """
        [V60.29] tactical_doc에서 각 화 섹션 추출

        Returns:
            {화번호: 해당 화 내용} 딕셔너리
        """
        sections = {}

        # [V60.34] 다양한 화 헤더 패턴 확장
        patterns = [
            r"##\s*제\s*(\d+)\s*화[:\s]",  # ## 제 N화: (StateLocked V60.34 형식)
            r"\[?제\s*(\d+)\s*화[^\]]*\]?",  # [제 N화 ...] 또는 제 N화
            r"【제\s*(\d+)\s*화[^】]*】",  # 【제 N화 ...】
            r"#\s*제\s*(\d+)\s*화",  # # 제 N화
            r"(\d+)화[:\s]",  # N화: 또는 N화
            r"---\s*\n\s*제\s*(\d+)\s*화",  # --- 구분자 후 제 N화
        ]

        # 모든 화 위치 찾기
        ep_positions = []
        for pattern in patterns:
            for match in re.finditer(pattern, tactical):
                ep_no = int(match.group(1))
                if ep_start <= ep_no < ep_start + ep_count + 2:  # 범위 체크 (+2 여유)
                    ep_positions.append((ep_no, match.start(), match.end()))

        # 중복 제거 및 정렬 (같은 화 번호는 첫 번째 위치 사용)
        seen_eps = {}
        for ep_no, start, end in sorted(ep_positions, key=lambda x: x[1]):
            if ep_no not in seen_eps:
                seen_eps[ep_no] = (start, end)
        ep_positions = [(ep, start, end) for ep, (start, end) in sorted(seen_eps.items(), key=lambda x: x[1][0])]

        # [V60.34] 화 종료 마커 패턴 (StateLocked 형식)
        end_markers = [
            r"【화\s*종료\s*상태】",
            r"\[종료\s*상태\]",
            r"---\s*$",
        ]

        # 각 화 내용 추출
        for i, (ep_no, start, end) in enumerate(ep_positions):
            # 다음 화 시작점까지 또는 문서 끝까지
            if i + 1 < len(ep_positions):
                next_start = ep_positions[i + 1][1]  # [V70] 다음 화의 시작 위치 (index 1=start, 0=ep_no)
                raw_content = tactical[end:next_start]
            else:
                raw_content = tactical[end:]

            # [V60.34] 종료 마커 이전까지만 본문으로 취급
            content = raw_content
            for marker in end_markers:
                marker_match = re.search(marker, raw_content)
                if marker_match:
                    # 종료 마커 포함하여 내용 유지 (상태 정보도 분량에 포함)
                    break

            # 이미 있으면 첫 번째 것 사용 (중복 방지)
            if ep_no not in sections:
                sections[ep_no] = content.strip()

        return sections

    def _validate_against_constraints(
        self,
        arc: dict,
        constraint_block: str,
        forbidden_items: list[str] | None = None,
    ) -> dict:
        """제약 블록 검증"""
        critical = []
        penalty = 0

        # Tier 1: 구조적 금지 아이템 우선
        if forbidden_items is None:
            forbidden_items = arc.get("_forbidden_items", [])
        if forbidden_items:
            forbidden_items = [str(item).strip() for item in forbidden_items if str(item).strip()]
        else:
            # Tier 3: 문자열 regex 폴백
            forbidden_items = re.findall(r"❌\s*([가-힣\w]+)", constraint_block)

        # 획득 금지 목록에서 추출
        forbidden_matches = re.findall(r"획득\s*(?:금지|불가)[^:]*[:：]\s*([^\n]+)", constraint_block)
        for match in forbidden_matches:
            items = [i.strip() for i in match.split(",")]
            forbidden_items.extend(items)

        # 현재 Arc의 획득 아이템과 비교
        # [BUG-F] protagonist_items 우선 폴백
        _sc_forb = arc.get("state_constraints", {})
        items_acquired = _sc_forb.get("protagonist_items") or _sc_forb.get("items_acquired", [])
        if not isinstance(items_acquired, list):
            items_acquired = []
        tactical = self._safe_tactical(arc)

        for forbidden in forbidden_items:
            if not forbidden or len(forbidden) < 2:
                continue

            # items_acquired에서 검사
            for item in items_acquired:
                if self._is_same_item(forbidden, item):
                    critical.append(f"제약 위반: 금지 아이템 '{forbidden}' 획득 시도")
                    penalty += 35
                    break

            # tactical_doc에서 획득 패턴과 함께 검사
            if forbidden in tactical:
                if any(kw in tactical for kw in ["획득", "얻", "손에"]):
                    # [Sweep47] 금지 아이템명 + 획득 키워드 근접 매칭 (기존 regex 치환 깨짐 수정)
                    acq_pattern = rf"{re.escape(forbidden)}[를을]?\s*(?:획득|얻|받|손에\s*넣|입수)"
                    if re.search(acq_pattern, tactical):
                        critical.append(f"제약 위반: 금지 아이템 '{forbidden}' 획득 시도 (tactical_doc)")
                        penalty += 35

        return {"penalty": penalty, "critical": critical}

    def _is_same_item(self, item1: str, item2: str) -> bool:
        """
        [V60.20] 두 아이템이 같은지 비교 - False Positive 방지 강화

        핵심 원칙:
        1. 길이 비율 체크: 한쪽이 2배 이상 길면 다른 아이템
        2. 최소 길이 요구: 포함 관계는 양쪽 모두 3자 이상일 때만
        3. 부분 매칭은 60% 이상 겹칠 때만 인정
        """
        if not item1 or not item2:
            return False

        item1, item2 = item1.strip(), item2.strip()

        # 완전 일치는 길이와 무관하게 True
        if item1 == item2:
            return True

        # [이슈-5] 괄호 내 수치 변형 제거 후 비교
        # "한미증권 계좌 (약 220억)" vs "한미증권 계좌 (약 300억)" → 동일 아이템으로 판정
        _item1_base = re.sub(r"\s*\([^)]*\)", "", item1).strip()
        _item2_base = re.sub(r"\s*\([^)]*\)", "", item2).strip()
        if _item1_base == _item2_base and len(_item1_base) >= 4:
            return True

        len1, len2 = len(item1), len(item2)

        # [V60.20] 최소 길이 체크 - 1글자는 부분 매칭 불가 (완전 일치 제외)
        if len1 < 2 or len2 < 2:
            return False

        # [V60.20] 길이 비율 체크 - 2배 이상 차이나면 다른 아이템
        # "비자금 장부"(5자) vs "장"(1자) → 5배 차이 → False
        length_ratio = max(len1, len2) / min(len1, len2)
        if length_ratio > 2.0:
            return False

        # 포함 관계 (긴 것이 짧은 것 포함)
        # [V60.20] 양쪽 모두 3자 이상 + 짧은쪽이 긴쪽의 60% 이상일 때만
        if len1 >= 3 and len2 >= 3:
            shorter, longer = (item1, item2) if len1 <= len2 else (item2, item1)
            overlap_ratio = len(shorter) / len(longer)

            if overlap_ratio >= 0.6:  # 60% 이상 겹쳐야 함
                if shorter in longer:
                    return True

        # 핵심 부분 비교 (접미사 제거)
        suffixes = sorted(set(self._item_suffixes + self.grant_keywords), key=len, reverse=True)
        core1 = item1
        core2 = item2
        for suffix in suffixes:
            if core1.endswith(suffix):
                core1 = core1[: -len(suffix)]
            if core2.endswith(suffix):
                core2 = core2[: -len(suffix)]

        # [V60.20] 코어 비교도 길이 체크 강화
        if core1 and core2 and len(core1) >= 2 and len(core2) >= 2:
            # 코어 길이 비율도 체크
            core_ratio = max(len(core1), len(core2)) / min(len(core1), len(core2))
            if core_ratio <= 1.5 and core1 == core2:
                return True

        return False

    def _locations_compatible(self, loc1: str, loc2: str) -> bool:
        """두 위치가 호환되는지 (근처/동일 지역)"""
        if not loc1 or not loc2:
            return True  # 정보 없으면 호환으로 간주

        loc1, loc2 = loc1.strip(), loc2.strip()

        # 완전 일치
        if loc1 == loc2:
            return True

        # 포함 관계
        if loc1 in loc2 or loc2 in loc1:
            return True

        # 주요 지명 추출 (2글자 이상)
        loc1_parts = set(re.findall(r"[가-힣]{2,}", loc1))
        loc2_parts = set(re.findall(r"[가-힣]{2,}", loc2))

        # 교집합이 있으면 호환
        if loc1_parts & loc2_parts:
            return True

        return False

    def _validate_dead_npc_appearance(self, arc: dict, state_tracker) -> dict:
        """
        [V60.94] 죽은 NPC 등장 검증 - REJECT 대상

        Args:
            arc: 검증할 Arc
            state_tracker: StateTracker 인스턴스

        Returns:
            {"penalty": int, "critical": list}
        """
        critical = []
        penalty = 0

        arc_no = arc.get("arc_no", 0)
        tactical = self._safe_tactical(arc)

        # StateTracker의 죽은 NPC 검사 메서드 활용
        violations = state_tracker.check_dead_npc_appearance(tactical, arc_no)

        for v in violations:
            npc_name = v.get("npc_name", "")
            death_arc = v.get("death_arc", 0)
            reason = v.get("reason", f"죽은 NPC '{npc_name}' 등장")

            critical.append(f"🚨 [V60.94] {reason}")
            penalty += 100  # 즉시 REJECT 수준

            logging.warning(f" [V60.94] REJECT: Arc {death_arc}에서 사망한 '{npc_name}'이 Arc {arc_no}에서 등장!")

        return {"penalty": penalty, "critical": critical}


def create_draft_validator(genre: str = "") -> ArcDraftValidator:
    """ArcDraftValidator 생성 헬퍼"""
    return ArcDraftValidator(genre=genre)
