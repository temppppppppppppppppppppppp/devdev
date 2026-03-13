"""FastAPI 브리지 — bridge_server.py (실체화)

역할:
- POST /run      → T4(RunValidator) + T6(RiskApprovalGate) + ProcessRunner.start()
- POST /stop     → ProcessRunner.stop() (멱등)
- GET  /status   → 현재 러너 상태 반환
- WS   /events   → run 이벤트 실시간 스트림 (event-schema-v1.json 준수)
- POST /run/{run_id}/input → T5(PromptBroker) 위임 (Mode B)

기동:
    uvicorn modules.api.bridge_server:app --port 8300

판정:
    curl http://127.0.0.1:8300/status
    # → {"ok":true,"code":"OK","data":{"state":"idle"}}
"""

from __future__ import annotations

import itertools
import json
import logging
import os
import re
import statistics
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from modules.api.process_runner import MODE_B_KEYS, PROJECT_ROOT, ProcessRunner
from modules.api.prompt_broker import PromptBroker, PromptState
from modules.api.prompt_classifier import classify as classify_prompt
from modules.api.risk_approval import RiskApprovalGate
from modules.api.run_validator import RISK_KEYS, validate_run_request
from modules.core.db_manager import DBManager
from modules.core.project_support import inspect_project_support_assets
from modules.core.quality_dashboard import QualityDashboard
from modules.core.quality_sidecar_bootstrap import inspect_quality_sidecar_health
from modules.core.runtime_paths import resolve_project_dir, resolve_projects_root

logger = logging.getLogger(__name__)

_QUALITY_SIGNAL_LABELS = {
    "ced": "CED",
    "ai_slop": "AI Slop",
    "compression": "gzip",
    "burstiness": "Rhythm",
    "complexity": "Density",
}

_QUALITY_REVIEW_LABELS = ("좋음", "경계", "AI 티", "지나친 단조", "과잉 설명")
_QUALITY_REVIEW_HELP = {
    "좋음": "지금 신호보다 원고 체감이 좋다고 판단된 화",
    "경계": "품질은 통과지만 다음 화에 주의가 필요한 화",
    "AI 티": "상투구, 설명문, 기계적 전환이 눈에 띈 화",
    "지나친 단조": "리듬과 전개가 지나치게 평평한 화",
    "과잉 설명": "설명과 압축이 과해 체감이 무거운 화",
}

_CHECKLIST_LABELS = {
    "scene_variety": "씬 다양성",
    "pacing_quality": "호흡/페이싱",
    "dialogue_naturalness": "대사 자연성",
    "emotional_authenticity": "감정 진정성",
    "tone_consistency": "톤 일관성",
    "continuity_contradiction": "연속성",
    "blueprint_coverage": "청사진 반영",
    "fiction_term_leak": "용어 일관성",
    "time_logic": "시간 논리",
    "paragraph_structure": "문단 구조",
    "scene_transition": "씬 전환",
    "identity_consistency": "정체성 일관성",
    "secret_consistency": "비밀 유지",
    "npc_knowledge_boundary": "NPC 지식 경계",
}

# ─── seq 카운터 (전역, 단조 증가) ────────────────────────────────────────────
_seq_iter = itertools.count(1)

def _next_seq() -> int:
    return next(_seq_iter)

def _ts() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")

# ─── WS 연결 관리자 ──────────────────────────────────────────────────────────

class WSManager:
    """연결된 WebSocket 클라이언트 목록 유지 + 브로드캐스트."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.debug("WS connected total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        try:
            self._connections.remove(ws)
        except ValueError:
            pass
        logger.debug("WS disconnected total=%d", len(self._connections))

    async def broadcast(self, event: dict) -> None:
        """event-schema-v1.json 형식 dict를 모든 클라이언트에 전송."""
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def emit_sync(self, run_id: str, event: dict) -> None:
        """PromptBroker emit_fn 인터페이스 — sync 진입점.

        asyncio.get_event_loop().is_running() 환경에서
        ensure_future로 비동기 broadcast를 예약한다.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.broadcast(event))
            else:
                loop.run_until_complete(self.broadcast(event))
        except Exception:
            logger.exception("WS broadcast 실패 run_id=%r type=%r", run_id, event.get("type"))

# ─── 이벤트 빌더 헬퍼 ────────────────────────────────────────────────────────

def _build_event(run_id: str, event_type: str, payload: dict) -> dict:
    """event-schema-v1.json 필수 필드 전량 포함."""
    return {
        "event_version": "v1",
        "seq": _next_seq(),
        "run_id": run_id,
        "type": event_type,
        "ts": _ts(),
        "payload": payload,
    }


def _build_run_exit_payload(runner: ProcessRunner, returncode: int) -> dict:
    payload = {"returncode": returncode}
    try:
        diagnostics = runner.get_runtime_diagnostics()
    except Exception as exc:
        logger.debug("runtime diagnostics unavailable: %s", exc)
        diagnostics = {}
    if diagnostics:
        payload.update(diagnostics)
    return payload

# ─── Envelope 헬퍼 (api-contract-v1.yaml) ────────────────────────────────────

def _accepted(run_id: str, message: str = "accepted") -> dict:
    return {"ok": True, "run_id": run_id, "code": "OK", "message": message, "data": {}}

def _ok(message: str = "ok") -> dict:
    return {"ok": True, "code": "OK", "message": message, "data": None}

def _err(code: str, message: str, run_id: str | None = None) -> dict:
    return {"ok": False, "run_id": run_id, "code": code, "message": message, "data": None}


def _get_projects_root() -> Path:
    return resolve_projects_root(PROJECT_ROOT)


def _get_project_dir(project_name: str) -> Path:
    return resolve_project_dir(project_name, PROJECT_ROOT)


def _get_project_db_path(project_name: str) -> Path:
    candidate = (_get_project_dir(project_name) / "project_data.db").resolve()
    return candidate


def _quality_dashboard_defaults(project: str, lookback: int) -> dict:
    return {
        "project": project,
        "available": False,
        "lookback": lookback,
        "latest_ep": None,
        "safe_ops": {
            "available": False,
            "project": project,
            "latest_ep": None,
            "arc_count": 0,
            "stage2_selection_count": 0,
            "stage4_selection_count": 0,
            "hint": "프로젝트를 선택하면 rollback / wipe / reset / rewind 영향 범위를 보여줍니다.",
            "actions": {},
        },
        "artifact_ladder": {
            "available": False,
            "project": project,
            "hint": "프로젝트를 선택하면 BI -> TR -> Arc -> Blueprint -> Manuscript 흐름이 표시됩니다.",
            "items": [],
            "support": [],
        },
        "quality_summary": {
            "available": False,
            "lookback": lookback,
            "latest_ep": None,
            "signals": {},
            "recent": [],
            "latest_ai_slop_hits": [],
            "latest_signal_summary": {},
            "project": project,
        },
        "result_summary": {
            "available": False,
            "headline": "최근 심사 결과가 아직 없습니다.",
            "verdict": None,
            "score": None,
            "ep_num": None,
            "selection_reason": "",
            "open_review": "",
            "issues": [],
            "signal_alerts": [],
            "next_action": "Stage 4 PASS 원고가 누적되면 결과 요약이 표시됩니다.",
        },
        "episode_trend": [],
        "compare_rows": [],
        "score_trend": {
            "trend": "insufficient_data",
            "window_size": lookback,
            "avg": 0,
            "min": 0,
            "max": 0,
            "delta": 0,
            "samples": 0,
            "summary": "데이터 부족 (0화)",
        },
        "stage_stats": [],
        "common_violations": [],
        "failure_patterns": {
            "top_types": [],
            "by_stage": [],
            "by_episode_range": [],
        },
        "runtime_health": {
            "available": False,
            "recent_count": 0,
            "top_components": [],
            "recent": [],
        },
        "retrieval_summary": {
            "available": False,
            "total_observations": 0,
            "stage_rows": [],
            "top_warnings": [],
            "recent": [],
        },
        "calibration": {
            "available": False,
            "lookback": lookback,
            "latest_ep": None,
            "total_reviews": 0,
            "label_counts": [],
            "recent_observations": [],
            "advisory_candidates": [],
            "next_step": "실제 회차를 보며 '좋음/경계/AI 티/지나친 단조/과잉 설명'을 기록하면 승격 후보가 누적됩니다.",
            "allowed_labels": list(_QUALITY_REVIEW_LABELS),
            "data_health": {
                "metrics_rows": 0,
                "stage4_validation_eps": 0,
                "retrieval_observation_rows": 0,
                "quality_label_rows": 0,
                "quality_signal_rows": 0,
                "manual_review_rows": 0,
                "missing_label_eps": 0,
                "missing_signal_eps": 0,
                "work_guard_exists": False,
                "tracking_slots": 0,
                "registry_profiles": 0,
                "role_fit_constraints": 0,
            },
        },
    }


def _safe_rel_path(path: Path, project_dir: Path) -> str:
    try:
        return str(path.relative_to(project_dir))
    except ValueError:
        return str(path)


def _safe_json_load(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def _latest_file(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda candidate: candidate.stat().st_mtime)


def _build_artifact_item(
    *,
    key: str,
    short: str,
    label: str,
    status: str,
    title: str,
    meta: str,
    detail: str = "",
    path: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "short": short,
        "label": label,
        "status": status,
        "title": title,
        "meta": meta,
        "detail": detail,
        "path": path,
    }


def _build_artifact_ladder_payload(project: str, project_dir: Path, db_path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "project": project,
        "hint": "",
        "items": [],
        "support": [],
    }

    config_dir = project_dir / "config"
    plans_dir = project_dir / "plans"
    drafts_dir = project_dir / "drafts"
    stage0_dir = project_dir / "stage0_output"

    support_assets = inspect_project_support_assets(project_dir)
    author_directives = Path(support_assets["author_directives"]["path"])
    work_guard = Path(support_assets["work_guard"]["path"])
    style_guide = Path(support_assets["style_guide"]["path"])
    treatment_candidates = [
        project_dir / "treatment_extended.json",
        project_dir / "treatment_generated.json",
        project_dir / "treatment.json",
    ]
    latest_treatment = _latest_file(treatment_candidates)

    latest_arc = _latest_file(sorted((plans_dir / "arcs").glob("arc_*.txt"))) if (plans_dir / "arcs").exists() else None
    latest_blueprint = (
        _latest_file(sorted((plans_dir / "blueprints").glob("blueprint_*.txt")))
        if (plans_dir / "blueprints").exists()
        else None
    )
    latest_manuscript = _latest_file(sorted(drafts_dir.glob("ep_*.txt"))) if drafts_dir.exists() else None

    bible_title = ""
    roadmap_count = 0
    blueprint_count = 0
    manuscript_count = 0
    arc_count_from_anchor = 0

    if db_path.exists():
        db = DBManager(db_path)
        try:
            bible_anchor = db.load_anchor("bible") or {}
            bible_root = bible_anchor.get("MasterBible", bible_anchor) if isinstance(bible_anchor, dict) else {}
            meta_info = bible_root.get("ProjectData", {}).get("MetaInfo", {}) if isinstance(bible_root, dict) else {}
            bible_title = str(meta_info.get("title") or "").strip()
            plot_roadmap = bible_root.get("plot_roadmap") or []
            roadmap_count = len(plot_roadmap) if isinstance(plot_roadmap, list) else 0

            arcs_anchor = db.load_anchor("arcs") or []
            if isinstance(arcs_anchor, list):
                arc_count_from_anchor = len(arcs_anchor)
            elif isinstance(arcs_anchor, dict):
                arc_count_from_anchor = len(arcs_anchor)

            blueprint_count = int(db.get_latest_blueprint_number() or 0)
            manuscript_count = max(0, int(db.get_latest_episode_number() or 0) - 1)
        except Exception as exc:
            logger.debug("artifact ladder db read failed for %s: %s", project, exc)
        finally:
            try:
                db.close()
            except Exception:
                pass

    treatment_data = _safe_json_load(latest_treatment) if latest_treatment else None
    treatment_blocks = len(treatment_data) if isinstance(treatment_data, list) else 0
    arc_files = sorted((plans_dir / "arcs").glob("arc_*.txt")) if (plans_dir / "arcs").exists() else []
    blueprint_files = sorted((plans_dir / "blueprints").glob("blueprint_*.txt")) if (plans_dir / "blueprints").exists() else []
    manuscript_files = sorted(drafts_dir.glob("ep_*.txt")) if drafts_dir.exists() else []
    blueprint_count = max(blueprint_count, len(blueprint_files))
    manuscript_count = max(manuscript_count, len(manuscript_files))

    bible_status = "ready" if bible_title or roadmap_count else "pending"
    bible_meta = f"plot_roadmap {roadmap_count} blocks" if roadmap_count else "DB bible anchor 미감지"
    bible_detail = bible_title or "MasterBible title 미확인"
    payload["items"].append(
        _build_artifact_item(
            key="bible",
            short="BI",
            label="Bible",
            status=bible_status,
            title=bible_detail,
            meta=bible_meta,
            detail="현재 프로젝트 DB anchor 기준",
            path="project_data.db :: anchors[bible]" if db_path.exists() else "",
        )
    )

    if latest_treatment:
        treatment_status = "ready"
        treatment_title = latest_treatment.name
        treatment_meta = f"{treatment_blocks} blocks" if treatment_blocks else "local treatment file"
        treatment_detail = "project-local generated treatment"
        treatment_path = _safe_rel_path(latest_treatment, project_dir)
    elif roadmap_count:
        treatment_status = "derived"
        treatment_title = "Bible plot_roadmap로 동기화됨"
        treatment_meta = f"{roadmap_count} blocks"
        treatment_detail = "로컬 treatment 파일은 없지만 Bible anchor에서 블록 확인"
        treatment_path = "project_data.db :: anchors[bible].plot_roadmap"
    else:
        treatment_status = "pending"
        treatment_title = "Treatment 대기"
        treatment_meta = "project-local treatment 없음"
        treatment_detail = "Stage 0 생성 또는 DNA sync 전"
        treatment_path = ""
    payload["items"].append(
        _build_artifact_item(
            key="treatment",
            short="TR",
            label="Treatment",
            status=treatment_status,
            title=treatment_title,
            meta=treatment_meta,
            detail=treatment_detail,
            path=treatment_path,
        )
    )

    arc_count = len(arc_files) or arc_count_from_anchor
    payload["items"].append(
        _build_artifact_item(
            key="arc",
            short="ARC",
            label="Arc Plan",
            status="ready" if arc_count else "pending",
            title=f"Arc {arc_count}개" if arc_count else "Arc 설계 대기",
            meta=latest_arc.name if latest_arc else "plans/arcs 비어 있음",
            detail="Stage 2 산출물",
            path=_safe_rel_path(latest_arc, project_dir) if latest_arc else "",
        )
    )

    payload["items"].append(
        _build_artifact_item(
            key="blueprint",
            short="BP",
            label="Blueprint",
            status="ready" if blueprint_count else "pending",
            title=f"Blueprint {blueprint_count}개" if blueprint_count else "Blueprint 대기",
            meta=latest_blueprint.name if latest_blueprint else "plans/blueprints 비어 있음",
            detail="Stage 3 산출물",
            path=_safe_rel_path(latest_blueprint, project_dir) if latest_blueprint else "",
        )
    )

    payload["items"].append(
        _build_artifact_item(
            key="manuscript",
            short="MS",
            label="Manuscript",
            status="ready" if manuscript_count else "pending",
            title=f"원고 {manuscript_count}화" if manuscript_count else "원고 대기",
            meta=latest_manuscript.name if latest_manuscript else "drafts 비어 있음",
            detail="Stage 4 산출물",
            path=_safe_rel_path(latest_manuscript, project_dir) if latest_manuscript else "",
        )
    )

    payload["support"] = [
        {
            "label": "Author",
            "status": "ready" if support_assets["author_directives"]["ready"] else "pending",
            "value": "author_directives.txt",
            "detail": (
                f"{int(support_assets['author_directives']['size_bytes'] or 0)} bytes"
                if support_assets["author_directives"]["ready"]
                else "not configured"
            ),
        },
        {
            "label": "Guard",
            "status": "ready" if support_assets["work_guard"]["ready"] else "pending",
            "value": "work_guard.yaml",
            "detail": (
                f"slots={support_assets['work_guard']['tracking_slots']}, "
                f"registry={support_assets['work_guard']['registry_profiles']}, "
                f"role_fit={support_assets['work_guard']['role_fit_constraints']}"
                if support_assets["work_guard"]["ready"]
                else "not configured"
            ),
        },
        {
            "label": "Style",
            "status": "ready" if support_assets["style_guide"]["ready"] else "pending",
            "value": "style_guide.json",
            "detail": (
                (
                    ", ".join(
                        part
                        for part in (
                            f"tone={support_assets['style_guide']['tone']}" if support_assets["style_guide"]["tone"] else "",
                            f"pov={support_assets['style_guide']['pov']}" if support_assets["style_guide"]["pov"] else "",
                        )
                        if part
                    )
                    or "ready"
                )
                if support_assets["style_guide"]["ready"]
                else "not configured"
            ),
        },
    ]
    payload["available"] = any(item["status"] != "pending" for item in payload["items"]) or any(
        chip["status"] == "ready" for chip in payload["support"]
    )
    pending_key = next((item["key"] for item in payload["items"] if item["status"] == "pending"), None)
    payload["hint"] = {
        "bible": "Bible anchor를 먼저 확인하거나 DNA sync 상태를 점검하세요.",
        "treatment": "Stage 0 treatment를 만들거나 plot_roadmap 동기화를 확인하세요.",
        "arc": "Stage 2를 실행해서 Arc 설계를 생성하세요.",
        "blueprint": "Stage 3를 실행해서 Blueprint를 누적하세요.",
        "manuscript": "Stage 4를 실행해서 최근 원고를 생성하세요.",
    }.get(pending_key, "현재 프로젝트는 기본 산출물이 준비되어 있습니다.")
    return payload


def _build_safe_ops_action(
    *,
    action: str,
    title: str,
    summary: str,
    requires_target: bool,
    deletes: list[str],
    preserves: list[str],
    notes: list[str],
    impact_counts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "action": action,
        "title": title,
        "summary": summary,
        "requires_target": requires_target,
        "deletes": deletes,
        "preserves": preserves,
        "notes": notes,
        "impact_counts": impact_counts or [],
    }


def _build_safe_ops_preview_payload(project: str, project_dir: Path, db_path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "available": False,
        "project": project,
        "latest_ep": None,
        "arc_count": 0,
        "stage2_selection_count": 0,
        "stage4_selection_count": 0,
        "hint": "프로젝트를 선택하면 rollback / wipe / reset / rewind 영향 범위를 보여줍니다.",
        "actions": {},
    }
    if not db_path.exists():
        return payload

    db = DBManager(db_path)
    try:
        latest_ep = max(0, int(db.get_latest_episode_number() or 0) - 1)
        arcs_anchor = db.load_anchor("arcs") or []
        if isinstance(arcs_anchor, list):
            arc_count = len(arcs_anchor)
        elif isinstance(arcs_anchor, dict):
            arc_count = len(arcs_anchor)
        else:
            arc_count = 0

        stage2_predicate = db._director_stage_predicate(2)
        stage4_predicate = db._director_stage_predicate(4)
        cur = db.cursor.execute("SELECT COUNT(*) AS cnt FROM director_selections WHERE " + stage2_predicate)
        stage2_selection_count = int(cur.fetchone()["cnt"])
        cur = db.cursor.execute("SELECT COUNT(*) AS cnt FROM director_selections WHERE " + stage4_predicate)
        stage4_selection_count = int(cur.fetchone()["cnt"])
        cur = db.cursor.execute("SELECT COUNT(*) AS cnt FROM stage_attempts WHERE stage = 2")
        stage2_attempt_count = int(cur.fetchone()["cnt"])

        wipe_impact = db.get_rollback_impact(1)
    finally:
        try:
            db.close()
        except Exception:
            pass

    wipe_counts = [
        {"label": "원고", "count": int(wipe_impact.get("manuscripts", 0))},
        {"label": "블루프린트", "count": int(wipe_impact.get("blueprints", 0))},
        {"label": "상태 로그", "count": int(wipe_impact.get("state_logs", 0))},
        {"label": "Stage 4 심사 이력", "count": int(wipe_impact.get("director_selections", 0))},
        {"label": "품질 신호", "count": int(wipe_impact.get("episode_quality_signals", 0))},
        {"label": "관계 히스토리", "count": int(wipe_impact.get("npc_relationship_history", 0))},
        {"label": "Stage 3/4 시도 이력", "count": int(wipe_impact.get("stage_attempts_stage34", 0))},
    ]
    reset_counts = [
        {"label": "Arc 설계", "count": int(arc_count)},
        {"label": "Stage 2 시도 이력", "count": int(stage2_attempt_count)},
        {"label": "Stage 2 선택 이력", "count": int(stage2_selection_count)},
        *wipe_counts,
    ]

    payload.update(
        {
            "available": True,
            "latest_ep": latest_ep,
            "arc_count": arc_count,
            "stage2_selection_count": stage2_selection_count,
            "stage4_selection_count": stage4_selection_count,
            "hint": "Rollback/Wipe는 Stage 4 review history를, Reset/Rewind는 Stage 2 design history를 중심으로 정리합니다.",
            "actions": {
                "rollback": _build_safe_ops_action(
                    action="rollback",
                    title="Rollback",
                    summary="지정한 episode부터 이후 Stage 4 산출물과 review history를 되돌립니다.",
                    requires_target=True,
                    deletes=[
                        "target episode 이상 원고 / 블루프린트 / 상태 로그",
                        "Stage 4 director selections / 품질 신호 / 관측 기록",
                        "foreshadow / 관계 히스토리 / Stage 3/4 시도 이력",
                    ],
                    preserves=[
                        "Bible / Treatment / 스타일 가이드",
                        "Stage 2 Arc 설계 / Stage 2 director selections",
                        "target episode 이전 확정 산출물",
                    ],
                    notes=[
                        f"현재 latest episode는 {latest_ep}화입니다.",
                        "세부 삭제 건수는 실행 중 target episode 입력 이후 결정됩니다.",
                        "Stage 2 selection history는 보존됩니다.",
                    ],
                ),
                "wipe": _build_safe_ops_action(
                    action="wipe",
                    title="Wipe",
                    summary="episode-derived production data만 지우고 setup/design은 유지합니다.",
                    requires_target=False,
                    deletes=[
                        "모든 원고 / 블루프린트 / 상태 로그",
                        "Stage 4 director selections / 품질 신호 / pacing / relation history",
                        "Stage 3/4 시도 이력과 episode-derived memory",
                    ],
                    preserves=[
                        "Bible / Treatment / 스타일 가이드",
                        "Stage 2 Arc 설계 / Stage 2 director selections",
                        "작가 지시사항 / Work Guard / 재료 파일",
                    ],
                    notes=[
                        "setup data는 남기고 production data만 초기화합니다.",
                        "Stage 4 review history만 지우고 Stage 2 design history는 유지합니다.",
                    ],
                    impact_counts=wipe_counts,
                ),
                "reset": _build_safe_ops_action(
                    action="reset",
                    title="Reset",
                    summary="Stage 2 Arc 설계와 모든 downstream production data를 전부 초기화합니다.",
                    requires_target=False,
                    deletes=[
                        "모든 Arc 설계 / Stage 2 시도 이력 / Stage 2 selection history",
                        "모든 원고 / 블루프린트 / 상태 로그",
                        "Stage 4 review history / 품질 신호 / episode-derived memory",
                    ],
                    preserves=[
                        "Bible / Treatment / 스타일 가이드",
                        "작가 지시사항 / Work Guard / 재료 파일",
                    ],
                    notes=[
                        "Safe Ops 중 가장 넓은 blast radius를 가집니다.",
                        "Stage 2 / Stage 4 selection history가 서로 다른 경로로 정리됩니다.",
                    ],
                    impact_counts=reset_counts,
                ),
                "rewind": _build_safe_ops_action(
                    action="rewind",
                    title="Rewind",
                    summary="지정한 arc부터 이후 Arc 설계와 downstream episode data를 제거합니다.",
                    requires_target=True,
                    deletes=[
                        "target arc 이상 Arc 설계 / Stage 2 selection history",
                        "해당 arc 이후 episode-derived production data",
                        "해당 구간의 Stage 4 review history",
                    ],
                    preserves=[
                        "target arc 이전 Arc 설계와 setup/config",
                        "Bible / Treatment / 스타일 가이드 / Work Guard",
                    ],
                    notes=[
                        f"현재 Arc 설계는 {arc_count}개입니다.",
                        "세부 삭제 건수는 실행 중 target arc 입력 이후 결정됩니다.",
                        "Stage 2 design history를 arc 경계 기준으로 정리합니다.",
                    ],
                ),
            },
        }
    )
    return payload


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _split_issue_text(text: str, *, limit: int = 3) -> list[str]:
    raw = str(text or "").strip()
    if not raw or raw in {"없음", "특이사항 없음", "문제 없음"}:
        return []

    chunks = [piece.strip(" -•\t") for piece in re.split(r"[\r\n]+|(?<=[.!?])\s+|[;·]+", raw) if piece.strip()]
    if not chunks:
        chunks = [raw]
    return _dedupe_preserve_order(chunks)[:limit]


def _format_checklist_label(key: str) -> str:
    if key in _CHECKLIST_LABELS:
        return _CHECKLIST_LABELS[key]
    return key.replace("_", " ").strip().title()


def _extract_checklist_issues(checklist: dict | None, *, limit: int = 3) -> list[str]:
    issues: list[str] = []
    for key, value in (checklist or {}).items():
        normalized = str(value or "").upper()
        if normalized in {"", "OK", "PASS", "NONE"}:
            continue
        issues.append(f"{_format_checklist_label(str(key))}: {value}")
    return _dedupe_preserve_order(issues)[:limit]


def _build_signal_alerts(summary: dict | None) -> list[str]:
    alerts: list[str] = []
    for key, stat in (summary or {}).get("signals", {}).items():
        status = str((stat or {}).get("status") or "watch")
        if status == "good":
            continue
        label = _QUALITY_SIGNAL_LABELS.get(key, key)
        delta = float((stat or {}).get("delta") or 0)
        direction = "악화" if status == "alert" else "주의"
        alerts.append(f"{label} {direction} (Δ {delta:+.2f})")
    return alerts[:3]


def _contains_positive_hint(text: str) -> bool:
    return bool(re.search(r"(좋|강점|안정|선명|유효|자연|매력|살아|성공|탄탄)", text))


def _contains_negative_hint(text: str) -> bool:
    return bool(re.search(r"(필요|반복|과다|과잉|부족|경고|문제|이슈|약함|낮음|흔들|누락|미흡)", text))


def _build_fix_now_items(issues: list[str], signal_alerts: list[str]) -> list[str]:
    return _dedupe_preserve_order(signal_alerts + issues)[:3]


def _pick_keep_next(selection_reason: str, open_review: str, verdict: str | None) -> str:
    candidates = _split_issue_text(selection_reason, limit=6) + _split_issue_text(open_review, limit=6)
    for item in candidates:
        if _contains_positive_hint(item) and not _contains_negative_hint(item):
            return f"다음 화에서도 {item} 흐름은 유지하세요."
    if verdict == "PASS":
        return "이번 화에서 안정적으로 작동한 강점 한 축은 다음 화에도 유지하세요."
    if verdict == "PASS_WITH_FIX":
        return "살아난 장면 감각과 강점은 유지하고, 수정은 국소적으로만 가하세요."
    return "문제가 없는 핵심 강점 한 축은 건드리지 말고 유지하세요."


def _pick_avoid_next(issues: list[str], signal_alerts: list[str], verdict: str | None) -> str:
    warning = next((item for item in signal_alerts if item), None) or next((item for item in issues if item), None)
    if warning:
        return f"다음 화에서는 {warning} 재발을 막으세요."
    if verdict == "REJECT":
        return "문제 범위를 넓히지 말고, 이번 화에서 걸린 핵심 원인만 먼저 정리하세요."
    return "다음 화에서 같은 감점 포인트가 반복되지 않게 직전 경고를 먼저 점검하세요."


def _build_next_action(verdict: str | None, issues: list[str], signal_alerts: list[str]) -> str:
    if verdict == "REJECT":
        return "상위 문제 3개를 먼저 정리하고 재실행하는 편이 안전합니다."
    if verdict == "PASS_WITH_FIX":
        return "국소 수정 지시를 반영한 뒤 빠르게 재심사하세요."
    if signal_alerts:
        return "통과 원고라도 경고 신호를 한 번 점검하고 다음 화 톤을 맞추세요."
    if issues:
        return "이번 화의 지적 포인트를 다음 화 설계/원고에 미리 반영하세요."
    return "현재 품질 흐름을 유지하면서 다음 화에 같은 밀도와 톤을 이어가면 됩니다."


def _build_result_summary(
    latest_ep: int | None,
    latest_label: dict | None,
    quality_summary: dict,
) -> dict:
    if not latest_ep or not latest_label:
        return {
            "available": False,
            "headline": "최근 심사 결과가 아직 없습니다.",
            "verdict": None,
            "score": None,
            "ep_num": latest_ep,
            "selection_reason": "",
            "open_review": "",
            "issues": [],
            "signal_alerts": [],
            "next_action": "Stage 4 PASS 원고가 누적되면 결과 요약이 표시됩니다.",
        }

    verdict = str(latest_label.get("verdict") or "")
    score = latest_label.get("score")
    selection_reason = str(latest_label.get("selection_reason") or "").strip()
    open_review = str(latest_label.get("open_review") or "").strip()
    checklist_issues = _extract_checklist_issues(latest_label.get("consistency_checklist") or {})
    review_issues = _split_issue_text(open_review)
    signal_alerts = _build_signal_alerts(quality_summary)

    issues = _dedupe_preserve_order(checklist_issues + review_issues)
    if not issues and selection_reason and verdict != "PASS":
        issues = _split_issue_text(selection_reason)
    fix_now = _build_fix_now_items(issues, signal_alerts)
    keep_next = _pick_keep_next(selection_reason, open_review, verdict)
    avoid_next = _pick_avoid_next(issues, signal_alerts, verdict)

    headline = f"ep {latest_ep} · {verdict or 'UNKNOWN'}"
    if score:
        headline += f" · {score}점"

    return {
        "available": True,
        "headline": headline,
        "verdict": verdict or None,
        "score": score,
        "ep_num": latest_ep,
        "selection_reason": selection_reason,
        "open_review": open_review,
        "issues": issues[:3],
        "signal_alerts": signal_alerts,
        "fix_now": fix_now,
        "keep_next": keep_next,
        "avoid_next": avoid_next,
        "next_action": _build_next_action(verdict, issues, signal_alerts),
    }


def _build_compare_rows(labels: list[dict], signals: list[dict]) -> list[dict]:
    label_map = {int(row.get("ep_num")): row for row in labels if row.get("ep_num") is not None}
    signal_map = {int(row.get("ep_num")): row for row in signals if row.get("ep_num") is not None}
    ep_nums = sorted(set(label_map) | set(signal_map), reverse=True)
    rows: list[dict] = []
    for ep_num in ep_nums[:8]:
        label = label_map.get(ep_num, {})
        signal = signal_map.get(ep_num, {})
        rows.append(
            {
                "ep_num": ep_num,
                "verdict": label.get("verdict"),
                "score": label.get("score"),
                "ced": signal.get("ced_score"),
                "ai_slop": signal.get("ai_slop_score"),
                "compression": signal.get("compression_ratio"),
                "burstiness": signal.get("burstiness"),
                "complexity": signal.get("complexity"),
            }
        )
    return rows


def _build_stage_stats(summary: dict) -> list[dict]:
    stage_stats = summary.get("stage_stats", {}) if isinstance(summary, dict) else {}
    rows: list[dict] = []
    for stage, stats in sorted(stage_stats.items(), key=lambda item: int(item[0])):
        rows.append(
            {
                "stage": int(stage),
                "pass_rate": float(stats.get("pass_rate", 0)),
                "avg_score": float(stats.get("avg_score", 0)),
                "total": int(stats.get("total", 0)),
            }
        )
    return rows


def _build_failure_patterns(patterns: dict) -> dict:
    by_type = patterns.get("by_type", {}) if isinstance(patterns, dict) else {}
    by_stage = patterns.get("by_stage", {}) if isinstance(patterns, dict) else {}
    by_episode_range = patterns.get("by_episode_range", {}) if isinstance(patterns, dict) else {}

    top_types = [
        {"type": key, "count": int(value)}
        for key, value in sorted(by_type.items(), key=lambda item: item[1], reverse=True)[:5]
    ]
    stage_rows = [
        {"stage": int(stage), "count": len(entries)}
        for stage, entries in sorted(by_stage.items(), key=lambda item: int(item[0]))
    ]
    range_rows = [
        {"range": key, "count": int(value)}
        for key, value in sorted(
            by_episode_range.items(),
            key=lambda item: int(str(item[0]).split("-", 1)[0]),
        )
    ]
    return {
        "top_types": top_types,
        "by_stage": stage_rows,
        "by_episode_range": range_rows,
    }


def _safe_signal_float(row: dict | None, field: str) -> float:
    if not isinstance(row, dict):
        return 0.0
    try:
        return float(row.get(field) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _build_calibration_signal_notes(
    observation_label: str,
    signal_row: dict,
    medians: dict[str, float],
) -> list[str]:
    notes: list[str] = []
    ai_slop = _safe_signal_float(signal_row, "ai_slop_score")
    ced = _safe_signal_float(signal_row, "ced_score")
    compression = _safe_signal_float(signal_row, "compression_ratio")
    burstiness = _safe_signal_float(signal_row, "burstiness")
    complexity = _safe_signal_float(signal_row, "complexity")
    hit_count = len(signal_row.get("ai_slop_hits") or [])

    if observation_label == "AI 티":
        if ai_slop >= max(medians["ai_slop"] * 1.05, 0.5) or hit_count >= 2:
            notes.append("AI Slop 동반")
        if compression >= medians["compression"] * 1.03 and medians["compression"] > 0:
            notes.append("gzip 압축 비율 상승")
    elif observation_label == "지나친 단조":
        if burstiness <= medians["burstiness"] * 0.92 and medians["burstiness"] > 0:
            notes.append("Rhythm 저하")
    elif observation_label == "과잉 설명":
        if complexity >= medians["complexity"] * 1.05 and medians["complexity"] > 0:
            notes.append("Density 상승")
        if compression >= medians["compression"] * 1.03 and medians["compression"] > 0:
            notes.append("gzip 압축 비율 상승")
    elif observation_label == "경계":
        if ced >= medians["ced"] * 1.08 and medians["ced"] > 0:
            notes.append("CED 상승")

    return notes[:2]


def _build_calibration_payload(
    *,
    latest_ep: int | None,
    lookback: int,
    labels: list[dict],
    signals: list[dict],
    observations: list[dict],
    data_health: dict | None = None,
) -> dict:
    payload = {
        "available": False,
        "lookback": lookback,
        "latest_ep": latest_ep,
        "total_reviews": 0,
        "label_counts": [],
        "recent_observations": [],
        "advisory_candidates": [],
        "next_step": "실제 회차를 보며 '좋음/경계/AI 티/지나친 단조/과잉 설명'을 기록하면 승격 후보가 누적됩니다.",
        "allowed_labels": list(_QUALITY_REVIEW_LABELS),
        "data_health": data_health or {},
    }
    if not observations:
        health = data_health or {}
        if health.get("stage4_validation_eps", 0) > 0 and health.get("manual_review_rows", 0) <= 0:
            payload["next_step"] = "수동 review 라벨이 아직 없습니다. 최근 Stage 4 원고부터 운영자 라벨을 5건 이상 쌓으세요."
        elif health.get("retrieval_observation_rows", 0) <= 0 and health.get("stage4_validation_eps", 0) > 0:
            payload["next_step"] = "retrieval 관측 로그가 부족합니다. 최신 코드로 Stage 2/3/4를 다시 실행해 표본을 쌓으세요."
        return payload

    signal_map = {int(row.get("ep_num")): row for row in signals if row.get("ep_num") is not None}
    label_map = {int(row.get("ep_num")): row for row in labels if row.get("ep_num") is not None}
    scoped_signal_rows = [signal_map[int(row["ep_num"])] for row in observations if int(row["ep_num"]) in signal_map]

    def _median(field: str) -> float:
        values = [_safe_signal_float(row, field) for row in scoped_signal_rows]
        return statistics.median(values) if values else 0.0

    medians = {
        "ced": _median("ced_score"),
        "ai_slop": _median("ai_slop_score"),
        "compression": _median("compression_ratio"),
        "burstiness": _median("burstiness"),
        "complexity": _median("complexity"),
    }

    label_counts = Counter(str(row.get("operator_label") or "").strip() for row in observations if row.get("operator_label"))
    candidate_counts = Counter()
    recent_rows: list[dict] = []

    for observation in observations:
        ep_num = int(observation.get("ep_num") or 0)
        operator_label = str(observation.get("operator_label") or "").strip()
        signal_row = signal_map.get(ep_num, {})
        label_row = label_map.get(ep_num, {})
        signal_notes = _build_calibration_signal_notes(operator_label, signal_row, medians)

        if operator_label == "AI 티" and "AI Slop 동반" in signal_notes:
            candidate_counts["AI Slop"] += 1
        if operator_label == "과잉 설명" and any(note in {"Density 상승", "gzip 압축 비율 상승"} for note in signal_notes):
            candidate_counts["Density/gzip"] += 1
        if operator_label == "지나친 단조" and "Rhythm 저하" in signal_notes:
            candidate_counts["Rhythm"] += 1
        if operator_label == "경계" and "CED 상승" in signal_notes:
            candidate_counts["CED"] += 1

        recent_rows.append(
            {
                "ep_num": ep_num,
                "operator_label": operator_label,
                "note": str(observation.get("note") or "").strip(),
                "score": label_row.get("score"),
                "verdict": label_row.get("verdict"),
                "signal_notes": signal_notes,
                "updated_at": observation.get("updated_at"),
            }
        )

    advisory_candidates: list[dict] = []
    advisory_copy = {
        "AI Slop": "AI 티 라벨과 동행하는 경우가 반복됨",
        "Density/gzip": "과잉 설명 라벨과 동행하는 경우가 반복됨",
        "Rhythm": "지나친 단조 라벨과 동행하는 경우가 반복됨",
        "CED": "경계 라벨에서 CED 상승이 반복됨",
    }
    for signal_name, count in candidate_counts.most_common():
        if count < 2:
            continue
        advisory_candidates.append(
            {
                "signal": signal_name,
                "count": count,
                "reason": advisory_copy.get(signal_name, "반복 동행 관측"),
            }
        )

    payload["available"] = True
    payload["total_reviews"] = sum(label_counts.values())
    payload["label_counts"] = [
        {"label": label, "count": int(count), "hint": _QUALITY_REVIEW_HELP.get(label, "")}
        for label, count in label_counts.most_common()
    ]
    payload["recent_observations"] = list(reversed(recent_rows[-8:]))
    payload["advisory_candidates"] = advisory_candidates[:4]
    if advisory_candidates:
        payload["next_step"] = "후보 신호를 바로 hard gate로 올리지 말고, CW retry feedback advisory부터 제한적으로 시험하는 편이 안전합니다."
    elif payload["total_reviews"] < 5:
        payload["next_step"] = "관측 샘플이 아직 적습니다. 최소 5화 이상에서 라벨을 더 쌓는 편이 좋습니다."
    else:
        payload["next_step"] = "지금은 관측은 되지만 승격 후보가 약합니다. 샘플을 더 쌓아 방향성을 확인하세요."
    return payload


def _load_runtime_health(project_dir: Path, *, limit: int = 10) -> dict:
    log_path = project_dir / "logs" / "soft_failures.jsonl"
    payload = {
        "available": False,
        "recent_count": 0,
        "top_components": [],
        "recent": [],
    }
    if not log_path.exists():
        return payload

    recent: list[dict] = []
    try:
        with log_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    recent.append(json.loads(line))
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
    except Exception as exc:
        logger.debug("runtime_health load failed for %s: %s", project_dir, exc)
        return payload

    if not recent:
        return payload

    window = recent[-max(1, limit):]
    component_counts = Counter(
        f"{row.get('component', 'unknown')}.{row.get('operation', 'unknown')}" for row in window
    )
    payload["available"] = True
    payload["recent_count"] = len(window)
    payload["top_components"] = [
        {"component": component, "count": count}
        for component, count in component_counts.most_common(5)
    ]
    payload["recent"] = [
        {
            "ts": row.get("ts"),
            "component": row.get("component"),
            "operation": row.get("operation"),
            "message": row.get("message"),
            "exception_type": row.get("exception_type"),
            "ep_num": row.get("ep_num"),
        }
        for row in reversed(window)
    ]
    return payload


def _build_quality_dashboard_payload(project: str, lookback: int) -> dict:
    db_path = _get_project_db_path(project)
    project_dir = _get_project_dir(project)
    safe_lookback = max(1, min(int(lookback or 5), 20))
    payload = _quality_dashboard_defaults(project, safe_lookback)

    dashboard = QualityDashboard(project_dir)
    dashboard_summary = dashboard.get_summary()
    payload["stage_stats"] = _build_stage_stats(dashboard_summary)
    payload["common_violations"] = [
        {"type": violation, "count": int(count)}
        for violation, count in (dashboard_summary.get("common_violations") or [])[:5]
    ]
    payload["episode_trend"] = dashboard.get_episode_trend(n_episodes=max(safe_lookback, 8))
    payload["score_trend"] = dashboard.get_score_trend_summary(stage=4, recent_n=max(safe_lookback, 5))
    payload["failure_patterns"] = _build_failure_patterns(dashboard.get_failure_patterns())
    payload["runtime_health"] = _load_runtime_health(project_dir, limit=max(safe_lookback, 5))
    payload["retrieval_summary"] = dashboard.get_retrieval_summary(recent_n=max(safe_lookback, 8))
    payload["artifact_ladder"] = _build_artifact_ladder_payload(project, project_dir, db_path)
    payload["safe_ops"] = _build_safe_ops_preview_payload(project, project_dir, db_path)

    if not db_path.exists():
        return payload

    db = DBManager(db_path)
    calibration_health = payload["calibration"]["data_health"]
    try:
        calibration_health = inspect_quality_sidecar_health(project_dir, db)
        quality_summary = db.get_quality_signal_summary(lookback=safe_lookback)
        quality_summary["project"] = project
        payload["quality_summary"] = quality_summary
        payload["available"] = bool(quality_summary.get("available"))
        payload["latest_ep"] = quality_summary.get("latest_ep")

        latest_ep = quality_summary.get("latest_ep")
        latest_label = db.get_episode_quality_label(latest_ep) if latest_ep else None
        compare_labels = (
            db.get_recent_episode_quality_labels(before_ep=int(latest_ep) + 1, lookback=max(safe_lookback, 8))
            if latest_ep
            else []
        )
        compare_signals = (
            db.get_recent_episode_quality_signals(before_ep=int(latest_ep) + 1, lookback=max(safe_lookback, 8))
            if latest_ep
            else []
        )
        observations = db.get_recent_episode_quality_observations(
            before_ep=int(latest_ep) + 1 if latest_ep else None,
            lookback=max(safe_lookback, 12),
        )
    finally:
        try:
            db.close()
        except Exception:
            pass

    payload["result_summary"] = _build_result_summary(payload["latest_ep"], latest_label, payload["quality_summary"])
    payload["compare_rows"] = _build_compare_rows(compare_labels, compare_signals)
    payload["calibration"] = _build_calibration_payload(
        latest_ep=payload["latest_ep"],
        lookback=safe_lookback,
        labels=compare_labels,
        signals=compare_signals,
        observations=observations,
        data_health=calibration_health,
    )
    if not payload["available"]:
        payload["available"] = bool(payload["stage_stats"] or payload["episode_trend"])
    return payload

# ─── 앱 수명주기 ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    ws_manager = WSManager()
    runner = ProcessRunner()
    risk_gate = RiskApprovalGate()

    broker = PromptBroker(
        emit_fn=ws_manager.emit_sync,
        seq_counter_fn=_next_seq,
    )
    logger.info("PromptBroker 활성화 — Mode B 사용 가능")

    app.state.ws_manager = ws_manager
    app.state.runner = runner
    app.state.risk_gate = risk_gate
    app.state.prompt_broker = broker

    yield

    # 종료 정리
    await runner.stop()
    logger.info("bridge_server 종료")

# ─── FastAPI 앱 ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Geuldobi Bridge",
    version="v1",
    lifespan=lifespan,
)

# ─── POST /run ────────────────────────────────────────────────────────────────

@app.post("/run")
async def run_endpoint(request: Request) -> JSONResponse:
    """메뉴 key 실행 요청.

    T4 RunValidator → T6 RiskApprovalGate → ProcessRunner.start() 순서로 처리.
    202 Accepted + run_id 반환.
    """
    runner: ProcessRunner = request.app.state.runner
    risk_gate: RiskApprovalGate = request.app.state.risk_gate
    ws_manager: WSManager = request.app.state.ws_manager

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content=_err("INVALID_KEY", "request body must be valid JSON"))

    key: str = str(body.get("key", ""))
    sub_key: str | None = body.get("sub_key") or None
    approval_id: str | None = body.get("approval_id") or None
    inputs: dict = body.get("inputs") or {}

    # T4: key / sub_key / 실행 상태 검증
    v = validate_run_request(key, sub_key, runner.state)
    if not v.ok:
        return JSONResponse(status_code=v.http_status, content=_err(v.code, v.message))

    # T6: 위험키 승인 게이트
    if key in RISK_KEYS:
        approval = risk_gate.validate(key, approval_id)
        if not approval.ok:
            return JSONResponse(status_code=approval.http_status, content=_err(approval.code, approval.message))

    run_id = str(uuid.uuid4())
    broker: PromptBroker = request.app.state.prompt_broker
    use_mode_b = key in MODE_B_KEYS

    # stdout/exit 콜백 → WS 이벤트 브로드캐스트
    async def _on_line(text: str) -> None:
        await ws_manager.broadcast(_build_event(run_id, "stdout", {"text": text}))

    async def _on_exit(returncode: int) -> None:
        etype = "run_completed" if returncode == 0 else "run_failed"
        await ws_manager.broadcast(_build_event(run_id, etype, _build_run_exit_payload(runner, returncode)))
        broker.cleanup_run(run_id)

    # Mode B: 프롬프트 감지 → PromptBroker → WS → UI → stdin
    async def _on_prompt(prompt_text: str, context_lines: list[str]) -> None:
        meta = classify_prompt(prompt_text, context_lines)
        runner.remember_prompt_step(meta.get("step_id"))
        prompt_id = str(uuid.uuid4())
        prompt_state = PromptState(
            prompt_id=prompt_id,
            step_id=meta["step_id"],
            input_type=meta["input_type"],
            default=meta["default"],
            timeout_sec=300,
            options=meta.get("options"),
        )
        # prompt_text도 payload에 포함 (UI 렌더링용)
        prompt_state.prompt_text = meta["prompt_text"]

        # broker가 prompt_request WS 이벤트 발행 + 사용자 응답 대기
        value = await broker.request_input(run_id, prompt_state)
        # 응답을 subprocess stdin에 전달
        await runner.write_stdin(str(value) if value is not None else "")

    try:
        await runner.start(
            key=key,
            run_id=run_id,
            sub_key=sub_key,
            inputs=inputs,
            on_line=_on_line,
            on_exit=_on_exit,
            on_prompt=_on_prompt if use_mode_b else None,
        )
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", str(exc), run_id),
        )
    except RuntimeError as exc:
        return JSONResponse(
            status_code=409,
            content=_err("RUN_ALREADY_ACTIVE", str(exc), run_id),
        )
    except Exception as exc:
        logger.exception("ProcessRunner start failed run_id=%r", run_id)
        return JSONResponse(
            status_code=500,
            content=_err("INTERNAL_ERROR", "subprocess start failed", run_id),
        )

    logger.info("RUN_STARTED run_id=%r key=%r", run_id, key)

    # run_started 이벤트 브로드캐스트
    await ws_manager.broadcast(_build_event(run_id, "run_started", {"key": key}))

    return JSONResponse(status_code=202, content=_accepted(run_id))

# ─── POST /run/{run_id}/input ────────────────────────────────────────────────

@app.post("/run/{run_id}/input")
async def resolve_prompt(run_id: str, request: Request) -> JSONResponse:
    """Mode B 인터랙티브 프롬프트 응답 (T5 PromptBroker 위임).

    200 — 성공 (prompt_resolved WS 이벤트 발행됨)
    400 — INVALID_PROMPT_ID
    409 — PROMPT_ALREADY_RESOLVED
    """
    broker: PromptBroker = request.app.state.prompt_broker

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content=_err("INVALID_PROMPT_ID", "request body must be valid JSON"))

    prompt_id: str = body.get("prompt_id", "")
    value = body.get("value")

    if not prompt_id:
        return JSONResponse(status_code=400, content=_err("INVALID_PROMPT_ID", "prompt_id is required"))

    status, error_code = broker.resolve(run_id, prompt_id, value)
    if status == "error":
        http_status = 409 if error_code == "PROMPT_ALREADY_RESOLVED" else 400
        return JSONResponse(status_code=http_status, content=_err(error_code, error_code.lower().replace("_", " ")))

    return JSONResponse(status_code=200, content=_ok("prompt accepted"))

# ─── POST /stop ───────────────────────────────────────────────────────────────

@app.post("/stop")
async def stop_endpoint(request: Request) -> JSONResponse:
    """현재 실행 중지 (멱등).

    실행 중이 아니어도 200 OK 반환.
    """
    runner: ProcessRunner = request.app.state.runner
    ws_manager: WSManager = request.app.state.ws_manager
    run_id = runner.run_id or "unknown"

    await runner.stop()
    await ws_manager.broadcast(_build_event(run_id, "run_stopped", {}))
    logger.info("STOP run_id=%r", run_id)

    return JSONResponse(status_code=200, content=_ok("stopped"))

# ─── GET /status ──────────────────────────────────────────────────────────────

@app.get("/status")
async def status_endpoint(request: Request) -> JSONResponse:
    """현재 러너 상태 조회.

    Returns:
        {"ok": true, "code": "OK", "data": {"state": "idle|running|...", "run_id": "..."}}
    """
    runner: ProcessRunner = request.app.state.runner

    data: dict = {"state": runner.state}
    if runner.run_id is not None:
        data["run_id"] = runner.run_id
    if runner.pid is not None:
        data["pid"] = runner.pid

    return JSONResponse(status_code=200, content={"ok": True, "code": "OK", "data": data})


@app.get("/quality/summary")
async def quality_summary_endpoint(project: str = "", lookback: int = 5) -> JSONResponse:
    """프로젝트 최근 품질 신호 요약 조회."""
    try:
        payload = _build_quality_dashboard_payload(project, lookback)
    except ValueError as exc:
        return JSONResponse(status_code=400, content=_err("INVALID_PROJECT", str(exc)))
    except Exception as exc:
        logger.exception("quality summary failed for project=%r", project)
        return JSONResponse(status_code=500, content=_err("INTERNAL_ERROR", str(exc)))

    return JSONResponse(
        status_code=200,
        content={"ok": True, "code": "OK", "data": payload["quality_summary"]},
    )


@app.get("/quality/dashboard")
async def quality_dashboard_endpoint(project: str = "", lookback: int = 5) -> JSONResponse:
    """프로젝트 품질 대시보드용 read-only 집계 조회."""
    try:
        payload = _build_quality_dashboard_payload(project, lookback)
    except ValueError as exc:
        return JSONResponse(status_code=400, content=_err("INVALID_PROJECT", str(exc)))
    except Exception as exc:
        logger.exception("quality dashboard failed for project=%r", project)
        return JSONResponse(status_code=500, content=_err("INTERNAL_ERROR", str(exc)))

    return JSONResponse(status_code=200, content={"ok": True, "code": "OK", "data": payload})


@app.get("/safe-ops/preview")
async def safe_ops_preview_endpoint(project: str = "") -> JSONResponse:
    """프로젝트 Safe Ops read-only preview 조회."""
    try:
        project_dir = _get_project_dir(project)
        db_path = _get_project_db_path(project)
        payload = _build_safe_ops_preview_payload(project, project_dir, db_path)
    except ValueError as exc:
        return JSONResponse(status_code=400, content=_err("INVALID_PROJECT", str(exc)))
    except Exception as exc:
        logger.exception("safe ops preview failed for project=%r", project)
        return JSONResponse(status_code=500, content=_err("INTERNAL_ERROR", str(exc)))

    return JSONResponse(status_code=200, content={"ok": True, "code": "OK", "data": payload})


@app.post("/quality/review")
async def quality_review_endpoint(request: Request) -> JSONResponse:
    """운영자 수기 품질 관측 저장."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content=_err("INVALID_REQUEST", "request body must be valid JSON"))

    try:
        project = str(body.get("project") or "").strip()
        project_dir = _get_project_dir(project)
        if not project_dir.exists():
            raise ValueError("project does not exist")
        ep_num = int(body.get("ep_num") or 0)
        operator_label = str(body.get("operator_label") or "").strip()
        note = str(body.get("note") or "").strip()
        if ep_num <= 0:
            raise ValueError("ep_num must be positive")
        if operator_label not in _QUALITY_REVIEW_LABELS:
            raise ValueError("operator_label is invalid")
    except ValueError as exc:
        return JSONResponse(status_code=400, content=_err("INVALID_REQUEST", str(exc)))

    db = DBManager(project_dir / "project_data.db")
    try:
        db.save_episode_quality_observation(
            ep_num,
            {
                "operator_label": operator_label,
                "note": note,
            },
        )
        saved = db.get_episode_quality_observation(ep_num) or {
            "ep_num": ep_num,
            "operator_label": operator_label,
            "note": note,
        }
    finally:
        try:
            db.close()
        except Exception:
            pass

    return JSONResponse(status_code=200, content={"ok": True, "code": "OK", "data": saved})

# ─── WS /events ───────────────────────────────────────────────────────────────

@app.websocket("/events")
async def ws_events(websocket: WebSocket) -> None:
    """실시간 이벤트 스트림 (event-schema-v1.json 형식).

    클라이언트는 연결 후 JSON 이벤트를 수신한다.
    연결 유지용 ping은 uvicorn websockets 핸들러가 처리.
    """
    ws_manager: WSManager = websocket.app.state.ws_manager
    await ws_manager.connect(websocket)
    try:
        while True:
            # 클라이언트 메시지 수신 대기 (연결 유지)
            # Mode B에서 클라이언트가 텍스트를 보내면 무시 (입력은 /run/{id}/input 경로)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)
