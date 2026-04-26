"""
[B-1-1] Stage4 Post-Processor — PASS 후처리 및 세션 종료 로직 분리
"""

import hashlib
import json
import logging
import os
import re
from pathlib import Path

from modules.core.metrics_collector import get_metrics_collector
from modules.core.non_wuxia_recovery_policy import normalize_chain_link_for_genre
from modules.core.project_support import resolve_project_pov_contract
from modules.core.quality_signal_metrics import compute_quality_signal_bundle, extract_warning_count
from modules.core.soft_failure import report_soft_failure, resolve_project_log_dir
from modules.core.stage4_post_pass_runtime import Stage4PostPassRuntime


class Stage4PostProcessor:
    """[B-1-1] Stage4 PASS 후처리 전담 모듈"""

    _SETTLEMENT_STATUS_FLAGS = {
        "primary_db_failed": {
            "manuscript_persisted": False,
            "metadata_settled": False,
            "settlement_packet_persisted": False,
            "human_export_persisted": False,
            "fully_settled": False,
        },
        "primary_persisted_meta_failed": {
            "manuscript_persisted": True,
            "metadata_settled": False,
            "settlement_packet_persisted": False,
            "human_export_persisted": False,
            "fully_settled": False,
        },
        "settlement_packet_failed": {
            "manuscript_persisted": True,
            "metadata_settled": True,
            "settlement_packet_persisted": False,
            "human_export_persisted": False,
            "fully_settled": False,
        },
        "human_export_failed": {
            "manuscript_persisted": True,
            "metadata_settled": True,
            "settlement_packet_persisted": True,
            "human_export_persisted": False,
            "fully_settled": False,
        },
        "fully_settled": {
            "manuscript_persisted": True,
            "metadata_settled": True,
            "settlement_packet_persisted": True,
            "human_export_persisted": True,
            "fully_settled": True,
        },
    }

    _SCENE_HEADER_LINE_RE = re.compile(
        r"(?m)^\s*#{1,6}\s*씬\s*\d+\s*[:\-].*$"  # utf8-hygiene: allow-line -- regex uses literal ? token safely for scene-header normalization
    )
    _STANDALONE_STAGE_CUE_RE = re.compile(r"(?m)^\s*\[([^\[\]\n]{1,160})\]\s*$")

    _PRESSURE_STOPWORDS = {
        "다음",
        "계속",
        "현재",
        "상황",
        "위기",
        "긴장",
        "시작",
        "마침내",
        "반격",
        "예고",
        "장면",
        "순간",
        "직후",
        "직전",
    }
    _PRESSURE_PARTICLE_SUFFIXES = (
        "으로부터",
        "으로는",
        "에서는",
        "에게는",
        "에게서",
        "이라는",
        "라는",
        "이라고",
        "라고",
        "으로",
        "에서",
        "에게",
        "한테",
        "부터",
        "까지",
        "처럼",
        "보다",
        "으로",
        "로",
        "의",
        "이",
        "가",
        "은",
        "는",
        "을",
        "를",
        "와",
        "과",
        "도",
        "만",
    )

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        self.post_pass_runtime = Stage4PostPassRuntime(self)

    def _report_soft_failure(
        self,
        *,
        operation: str,
        message: str,
        exc: Exception | None = None,
        ep_num: int | None = None,
        extra: dict | None = None,
        user_visible: bool = True,
        learnable: bool = True,
    ) -> None:
        audit_event = getattr(self.ctx, "audit_event", None)
        report_soft_failure(
            component="stage4_post_processor",
            operation=operation,
            message=message,
            exc=exc,
            stage=4,
            ep_num=ep_num,
            degraded=True,
            user_visible=user_visible,
            learnable=learnable,
            extra=extra,
            log_dir=self._resolve_project_log_dir(),
            audit_event=audit_event if callable(audit_event) else None,
            warning_window_sec=120.0,
        )

    def _resolve_project_log_dir(self):
        current_project = getattr(self.ctx, "current_project", None)
        return resolve_project_log_dir(current_project)

    @staticmethod
    def _write_emergency_manuscript_dump(*, output_dir, next_ep: int, final_title: str, final_manuscript: str) -> Path:
        dump_dir = Path(output_dir)
        dump_dir.mkdir(parents=True, exist_ok=True)
        dump_path = dump_dir / f"emergency_ep_{next_ep:04d}.txt"
        title = str(final_title or f"제{next_ep}화").strip() or f"제{next_ep}화"
        dump_path.write_text(f"# {title}\n\n{final_manuscript}", encoding="utf-8")
        return dump_path

    @staticmethod
    def _build_human_facing_manuscript_path(*, output_dir, next_ep: int) -> Path:
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir / f"ep_{next_ep:04d}.txt"

    @staticmethod
    def _build_stage4_settlement_packet_path(*, output_dir, next_ep: int) -> Path:
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir / f"ep_{next_ep:04d}.settlement.json"

    def _relativize_artifact_path(self, path: Path) -> str:
        project_paths = getattr(getattr(self.ctx, "current_project", None), "paths", None)
        project_root = getattr(project_paths, "root", None)
        if isinstance(project_root, str | Path):
            try:
                return path.relative_to(Path(project_root)).as_posix()
            except ValueError:
                pass
        return str(path)

    def _write_human_facing_manuscript_export(
        self,
        *,
        next_ep: int,
        final_title: str,
        final_manuscript: str,
        output_dir,
    ) -> Path:
        file_path = self._build_human_facing_manuscript_path(output_dir=output_dir, next_ep=next_ep)
        file_path.write_text(f"# {final_title}\n\n{final_manuscript}", encoding="utf-8")
        return file_path

    def _build_stage4_settlement_packet(
        self,
        *,
        next_ep: int,
        final_title: str,
        final_manuscript: str,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        quality_labels,
        quality_signals,
        post_pass_payload: dict,
        output_dir,
    ) -> dict:
        txt_path = self._build_human_facing_manuscript_path(output_dir=output_dir, next_ep=next_ep)
        packet_path = self._build_stage4_settlement_packet_path(output_dir=output_dir, next_ep=next_ep)
        stage3_meta = {}
        if isinstance(blueprint, dict) and isinstance(blueprint.get("_stage3_meta"), dict):
            stage3_meta = dict(blueprint.get("_stage3_meta") or {})
        actual_truth = post_pass_payload.get("actual_truth", {}) if isinstance(post_pass_payload, dict) else {}
        state_truth_owner_contract = (
            post_pass_payload.get("state_truth_owner_contract", {}) if isinstance(post_pass_payload, dict) else {}
        )
        bible_delta = post_pass_payload.get("bible_delta", {}) if isinstance(post_pass_payload, dict) else {}
        title = str(final_title or f"제{next_ep}화").strip() or f"제{next_ep}화"
        manuscript_hash = hashlib.sha256(str(final_manuscript or "").encode("utf-8")).hexdigest()
        return {
            "packet_version": "stage4_settlement_packet_v1",
            "stage": 4,
            "ep_num": int(next_ep),
            "title": title,
            "arc_no": int((arc_data or {}).get("arc_no", 0) or 0) if isinstance(arc_data, dict) else 0,
            "blueprint_ep": int(next_ep),
            "manuscript": {
                "db_table": "manuscripts",
                "char_count": len(final_manuscript or ""),
                "content_hash": manuscript_hash,
                "human_facing_txt_path": self._relativize_artifact_path(txt_path),
            },
            "stage3_meta": stage3_meta,
            "quality": {
                "labels": dict(quality_labels or {}) if isinstance(quality_labels, dict) else {},
                "signals": dict(quality_signals or {}) if isinstance(quality_signals, dict) else {},
            },
            "settlement": {
                "episode_bible": dict(bible_delta or {}) if isinstance(bible_delta, dict) else {},
                "actual_truth": dict(actual_truth or {}) if isinstance(actual_truth, dict) else {},
                "final_state_updates": dict(final_state_updates or {}) if isinstance(final_state_updates, dict) else {},
                "state_truth_owner_contract": (
                    dict(state_truth_owner_contract or {}) if isinstance(state_truth_owner_contract, dict) else {}
                ),
                "meta_save_failed": bool(post_pass_payload.get("meta_save_failed", False))
                if isinstance(post_pass_payload, dict)
                else False,
            },
            "artifacts": {
                "settlement_packet_path": self._relativize_artifact_path(packet_path),
                "human_facing_txt_path": self._relativize_artifact_path(txt_path),
                "episode_bible_table": "episode_bibles",
                "state_log_table": "state_logs",
            },
        }

    def _persist_stage4_settlement_packet(
        self,
        *,
        next_ep: int,
        final_title: str,
        final_manuscript: str,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        quality_labels,
        quality_signals,
        post_pass_payload: dict,
        output_dir,
    ) -> Path:
        packet_path = self._build_stage4_settlement_packet_path(output_dir=output_dir, next_ep=next_ep)
        packet = self._build_stage4_settlement_packet(
            next_ep=next_ep,
            final_title=final_title,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            blueprint=blueprint,
            arc_data=arc_data,
            quality_labels=quality_labels,
            quality_signals=quality_signals,
            post_pass_payload=post_pass_payload,
            output_dir=output_dir,
        )
        packet_path.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        return packet_path

    @staticmethod
    def _extract_stage4_settlement_attempt_key(final_state_updates: dict | None) -> str:
        if not isinstance(final_state_updates, dict):
            return ""
        for key in ("attempt_key", "_attempt_key", "_stage4_attempt_key"):
            value = final_state_updates.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @staticmethod
    def _strip_stage4_internal_state_updates(final_state_updates: dict) -> dict:
        return {
            key: value
            for key, value in final_state_updates.items()
            if key not in {"_director_quality_labels", "_stage4_attempt_key", "_stage4_attempt_artifact_meta"}
        }

    def _build_stage4_settlement_status_payload(
        self,
        *,
        status: str,
        next_ep: int,
        arc_data: dict | None,
        final_state_updates: dict | None,
        attempt_key: str = "",
        artifact_path: Path | str | None = None,
        detail: str = "",
    ) -> dict:
        flags = dict(self._SETTLEMENT_STATUS_FLAGS.get(status, {}))
        arc_no = arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else 0
        attempt_key = str(attempt_key or "").strip() or self._extract_stage4_settlement_attempt_key(final_state_updates)
        return {
            "event": "STAGE4_PASS_SETTLEMENT_STATUS",
            "stage": 4,
            "ep_num": int(next_ep),
            "arc_num": int(arc_no or 0),
            "attempt_key": attempt_key,
            "settlement_status": status,
            "artifact_path": self._relativize_artifact_path(Path(artifact_path)) if artifact_path else "",
            "detail": str(detail or "")[:1000],
            "authority_note": "fully_settled is the only authoritative PASS settlement state",
            **flags,
        }

    def _emit_stage4_settlement_status(
        self,
        *,
        status: str,
        next_ep: int,
        arc_data: dict | None,
        final_state_updates: dict | None,
        attempt_key: str = "",
        artifact_path: Path | str | None = None,
        detail: str = "",
    ) -> dict:
        payload = self._build_stage4_settlement_status_payload(
            status=status,
            next_ep=next_ep,
            arc_data=arc_data,
            final_state_updates=final_state_updates,
            attempt_key=attempt_key,
            artifact_path=artifact_path,
            detail=detail,
        )
        audit_event = getattr(self.ctx, "audit_event", None)
        if callable(audit_event):
            audit_event("stage4_pass_settlement_status", "stage4 pass settlement status recorded", payload)

        db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        save_ui_event = getattr(db, "save_ui_event", None)
        if callable(save_ui_event):
            try:
                project = getattr(self.ctx, "current_project", None)
                save_ui_event(
                    session_id=str(getattr(project, "metrics_session_id", "") or ""),
                    stage=4,
                    ep_num=payload["ep_num"],
                    arc_num=payload["arc_num"],
                    attempt_key=payload["attempt_key"],
                    component="post_pass_settlement",
                    event_kind="status",
                    level="info" if payload.get("fully_settled") else "error",
                    message=f"stage4 pass settlement status: {status}",
                    visible=False,
                    artifact_path=payload["artifact_path"] or None,
                    meta=payload,
                )
            except Exception as ui_event_err:
                logging.debug("[S4-SETTLEMENT] status ui_event save failed: %s", ui_event_err)
        if payload.get("fully_settled") is not True:
            self._mark_stage4_attempt_settlement_failed(
                attempt_key=payload.get("attempt_key", ""),
                status=status,
                detail=detail,
            )
        return payload

    def _mark_stage4_attempt_settlement_failed(self, *, attempt_key: str, status: str, detail: str = "") -> None:
        attempt_key = str(attempt_key or "").strip()
        if not attempt_key:
            return
        db = getattr(getattr(self.ctx, "current_project", None), "db", None)
        marker = getattr(db, "mark_stage4_attempt_settlement_failed", None)
        if not callable(marker):
            return
        try:
            marker(
                attempt_key=attempt_key,
                settlement_status=str(status or "").strip(),
                detail=str(detail or "").strip(),
            )
        except Exception as exc:
            logging.debug("[S4-SETTLEMENT] stage_attempt settlement demotion failed: %s", exc)

    @staticmethod
    def _extract_save_error(manager, fallback: str) -> str:
        raw = getattr(manager, "last_save_error", "")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return fallback

    def _raise_if_save_failed(self, *, manager, label: str, save_result) -> None:
        if save_result is False:
            error = self._extract_save_error(manager, f"{label}.save() returned False")
            logging.warning("[TF-C10] %s save returned False: %s", label, error)
            self.ctx.ui.log(f"   ⚠️ [TF-C10] {label} save 실패: {error}")
            raise RuntimeError(f"{label}.save failed: {error}")

    @classmethod
    def _is_stage_cue_line(cls, inner: str) -> bool:
        if not isinstance(inner, str):
            return False
        normalized = re.sub(r"\s+", " ", inner).strip()
        if not normalized:
            return False
        cue_tokens = ("년", "월", "장소", "시간", "배경", "/", ",")
        return any(token in normalized for token in cue_tokens)

    @classmethod
    def _normalize_reader_facing_manuscript(cls, manuscript: str) -> str:
        """Strip internal scene scaffolding from final reader-facing artifacts."""
        if not isinstance(manuscript, str) or not manuscript.strip():
            return str(manuscript or "")

        normalized = manuscript.replace("\r\n", "\n").replace("\r", "\n")
        scene_index = 0

        def _replace_scene_header(_match) -> str:
            nonlocal scene_index
            scene_index += 1
            return "" if scene_index == 1 else "\n\n***\n\n"

        normalized = cls._SCENE_HEADER_LINE_RE.sub(_replace_scene_header, normalized)

        def _replace_stage_cue(match) -> str:
            inner = re.sub(r"\s+", " ", match.group(1)).strip()
            if not cls._is_stage_cue_line(inner):
                return match.group(0)
            if inner.endswith((".", "!", "?", "…", "”", '"')):
                return inner
            return inner + "."

        normalized = cls._STANDALONE_STAGE_CUE_RE.sub(_replace_stage_cue, normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        return normalized

    @staticmethod
    def _normalize_karma_entry(entry) -> dict | None:
        if not isinstance(entry, dict):
            return None
        npc_name = entry.get("target") or entry.get("npc_name") or entry.get("name") or ""
        if not npc_name:
            return None
        misunderstanding = entry.get("misunderstanding")
        if misunderstanding is None:
            misunderstanding = entry.get("value")
        if misunderstanding is None:
            misunderstanding = entry.get("point", 0)
        obsession = entry.get("obsession")
        if obsession is None:
            obsession = entry.get("point")
        if obsession is None:
            obsession = 0
        return {
            "npc_name": str(npc_name),
            "misunderstanding": misunderstanding,
            "obsession": obsession,
        }

    def _persist_karma_status(self, *, karma_matrix, next_ep: int) -> int:
        if not isinstance(karma_matrix, list) or not karma_matrix:
            return 0

        current_project = getattr(self.ctx, "current_project", None)
        db = getattr(current_project, "db", None)
        update_karma = getattr(db, "update_karma", None)
        if not callable(update_karma):
            self._report_soft_failure(
                operation="update_karma",
                message="karma_status sink unavailable on Stage4 PASS path",
                ep_num=next_ep,
                extra={"table": "karma_status"},
                user_visible=False,
            )
            return 0

        karma_status_cache = getattr(current_project, "karma_status", None)
        if not isinstance(karma_status_cache, dict):
            karma_status_cache = {}
            if current_project is not None:
                try:
                    current_project.karma_status = karma_status_cache
                except Exception:
                    karma_status_cache = {}

        persisted = 0
        for raw_entry in karma_matrix:
            normalized = self._normalize_karma_entry(raw_entry)
            if not normalized:
                continue

            npc_name = normalized["npc_name"]
            try:
                update_karma(
                    npc_name,
                    normalized["misunderstanding"],
                    normalized["obsession"],
                    next_ep,
                )
            except Exception as karma_err:
                self._report_soft_failure(
                    operation="update_karma",
                    message="karma_status save failed after Stage4 PASS",
                    exc=karma_err,
                    ep_num=next_ep,
                    extra={"table": "karma_status", "npc_name": npc_name},
                )
                self.ctx.ui.log(f"      [WARN] karma_status save failed: {npc_name} ({str(karma_err)[:40]})")
                continue

            karma_status_cache[npc_name] = {
                "npc_name": npc_name,
                "misunderstanding": normalized["misunderstanding"],
                "obsession": normalized["obsession"],
                "last_updated_ep": next_ep,
            }
            persisted += 1

        return persisted

    def _best_effort_rollback_manager(self, *, manager, label: str, target_ep: int) -> bool:
        rollback_fn = getattr(manager, "rollback_to", None)
        if not callable(rollback_fn):
            logging.warning("[TF-C10] %s rollback_to unavailable during sequential save recovery", label)
            return False
        try:
            rollback_fn(target_ep)
        except Exception as rollback_err:
            logging.warning(
                "[TF-C10] %s rollback_to(%d) failed during sequential save recovery: %s",
                label,
                target_ep,
                rollback_err,
            )
            try:
                self.ctx.ui.log(f"   ⚠️ [TF-C10] {label} 순차 저장 롤백 실패: {str(rollback_err)[:60]}")
            except Exception:
                pass
            return False
        logging.warning("[TF-C10] %s sequential save repaired via rollback_to(%d)", label, target_ep)
        try:
            self.ctx.ui.log(f"   ↩️ [TF-C10] {label} 순차 저장 롤백 복구 완료")
        except Exception:
            pass
        return True

    def _truth_gate_llm_ask(self, prompt: str) -> str:
        """[TF-30-1] TruthGate 세계법칙 검사용 LLM 콜백."""
        try:
            director = getattr(self.ctx, "agents", {}).get("director")
            if director and hasattr(director, "ask"):
                return director.ask(prompt, temperature=0.1) or ""
        except Exception as e:
            logging.debug("[TruthGate:POST] llm_ask fail: %s", e)
        return ""

    @staticmethod
    def _extract_state_change_info(state_changes) -> dict:
        """[TF-T5] state_changes에서 event_types, entity_names, summary_parts 추출.

        벡터 메모리 저장(Block 1)과 rich_summary 구성(Block 2)에서 동일 데이터를
        이중 순회하던 것을 단일 패스로 통합.
        """
        event_types: set[str] = set()
        entity_names: set[str] = set()
        summary_parts: list[str] = []

        if not isinstance(state_changes, dict):
            return {"event_types": event_types, "entity_names": entity_names, "summary_parts": summary_parts}

        # npc_deaths
        npc_deaths = state_changes.get("npc_deaths", [])
        if npc_deaths:
            event_types.add("death")
            death_names = []
            for d in npc_deaths:
                name = d.get("name", "") if isinstance(d, dict) else str(d)
                if name:
                    entity_names.add(name)
                    death_names.append(name)
            if death_names:
                summary_parts.append("사망: " + ", ".join(death_names)[:60])

        # skill_acquisitions
        skill_acqs = state_changes.get("skill_acquisitions", [])
        if skill_acqs:
            event_types.add("skill")
            for s in skill_acqs:
                entity_names.add(s.get("name", "") if isinstance(s, dict) else str(s))

        # relationship_changes
        rel_changes = state_changes.get("relationship_changes", [])
        if isinstance(rel_changes, list) and rel_changes:
            event_types.add("relationship")
            rel_texts = []
            for r in rel_changes:
                if isinstance(r, dict):
                    who = r.get("npc", "") or r.get("target", "")
                    entity_names.add(who)
                    delta = r.get("change", "")
                    rel_texts.append(f"{who}-{delta}")
                else:
                    rel_texts.append(str(r))
            if rel_texts:
                summary_parts.append("관계: " + ", ".join(rel_texts)[:80])

        # major_items
        major_items = state_changes.get("major_items", [])
        if isinstance(major_items, list) and major_items:
            event_types.add("item")
            item_names = []
            for i in major_items:
                name = i.get("name", "") if isinstance(i, dict) else str(i)
                if name:
                    entity_names.add(name)
                    item_names.append(name)
            if item_names:
                summary_parts.append("아이템: " + ", ".join(item_names)[:60])

        # npc_injuries / npc_movements
        if state_changes.get("npc_injuries"):
            event_types.add("injury")
        if state_changes.get("npc_movements"):
            event_types.add("movement")

        # resolved_plots
        resolved_plots = state_changes.get("resolved_plots", [])
        if isinstance(resolved_plots, list) and resolved_plots:
            event_types.add("resolved_plot")
            summary_parts.append("해결: " + ", ".join(str(p)[:30] for p in resolved_plots[:2]))

        entity_names.discard("")
        return {"event_types": event_types, "entity_names": entity_names, "summary_parts": summary_parts}

    @classmethod
    def _normalize_pressure_cue(cls, token: str) -> str:
        text = re.sub(r"[^0-9A-Za-z가-힣]+", "", str(token or "").strip()).lower()
        if not text or text.isdigit():
            return ""
        for suffix in cls._PRESSURE_PARTICLE_SUFFIXES:
            if len(text) > len(suffix) + 1 and text.endswith(suffix):
                text = text[: -len(suffix)]
                break
        if len(text) < 2 or text in cls._PRESSURE_STOPWORDS:
            return ""
        return text

    @classmethod
    def _extract_pressure_cue_terms(cls, text: str, *, max_terms: int = 5) -> list[str]:
        cue_terms: list[str] = []
        for token in re.findall(r"[0-9A-Za-z가-힣]+", str(text or "")):
            normalized = cls._normalize_pressure_cue(token)
            if normalized and normalized not in cue_terms:
                cue_terms.append(normalized)
            if len(cue_terms) >= max_terms:
                break
        return cue_terms

    @classmethod
    def _normalize_active_pressure_vectors(
        cls,
        raw_vectors,
        *,
        default_source: str = "",
    ) -> list[dict]:
        if not isinstance(raw_vectors, list):
            return []

        normalized_vectors: list[dict] = []
        seen_texts: set[str] = set()
        for raw in raw_vectors:
            if isinstance(raw, dict):
                text = str(raw.get("text") or raw.get("pressure") or raw.get("label") or "").strip()
                source = str(raw.get("source") or default_source or "").strip()
                cue_terms = raw.get("cue_terms", [])
            else:
                text = str(raw or "").strip()
                source = str(default_source or "").strip()
                cue_terms = []

            if len(text) < 2 or text in seen_texts:
                continue

            normalized_terms: list[str] = []
            if isinstance(cue_terms, list):
                for cue in cue_terms:
                    normalized = cls._normalize_pressure_cue(cue)
                    if normalized and normalized not in normalized_terms:
                        normalized_terms.append(normalized)
            if not normalized_terms:
                normalized_terms = cls._extract_pressure_cue_terms(text)

            normalized_vectors.append(
                {
                    "source": source,
                    "text": text[:240],
                    "cue_terms": normalized_terms[:5],
                }
            )
            seen_texts.add(text)

        return normalized_vectors[:3]

    @classmethod
    def _build_active_pressure_vectors(cls, blueprint: dict | None) -> list[dict]:
        if not isinstance(blueprint, dict):
            return []

        raw_vectors = []
        for key in ("ending_hook", "cliffhanger", "expected_ending"):
            value = blueprint.get(key)
            if isinstance(value, str) and value.strip():
                raw_vectors.append({"source": key, "text": value.strip()})
        return cls._normalize_active_pressure_vectors(raw_vectors)

    @classmethod
    def _filter_active_pressure_vectors_by_manuscript(
        cls,
        vectors: list[dict],
        final_manuscript: str | None,
    ) -> list[dict]:
        if not vectors:
            return []

        manuscript_tail = str(final_manuscript or "").strip()[-1200:]
        if not manuscript_tail:
            return []

        normalized_tail = re.sub(r"[^0-9A-Za-z가-힣]+", "", manuscript_tail).lower()
        filtered: list[dict] = []
        for vector in vectors:
            if not isinstance(vector, dict):
                continue

            text = str(vector.get("text") or "").strip()
            if not text:
                continue
            if text in manuscript_tail:
                filtered.append(vector)
                continue

            normalized_text = re.sub(r"[^0-9A-Za-z가-힣]+", "", text).lower()
            if len(normalized_text) >= 8 and normalized_text in normalized_tail:
                filtered.append(vector)
                continue

            cue_terms = vector.get("cue_terms", [])
            normalized_terms: list[str] = []
            if isinstance(cue_terms, list):
                for cue in cue_terms:
                    normalized = cls._normalize_pressure_cue(cue)
                    if normalized and normalized not in normalized_terms:
                        normalized_terms.append(normalized)
            if not normalized_terms:
                normalized_terms = cls._extract_pressure_cue_terms(text)

            matched_terms = [term for term in normalized_terms if term in normalized_tail]
            required_matches = 2 if len(normalized_terms) >= 2 else 1
            if len(matched_terms) >= required_matches:
                filtered.append(vector)

        return filtered

    # ------------------------------------------------------------------
    # [V73] 확정 원고 기준 자본금 역동기화
    # ------------------------------------------------------------------
    _CAPITAL_PATTERNS = [
        # "잔고 131억", "자본금 80억", "현금 57억"
        re.compile(
            r"(?:잔고|자본금?|현금|자산|실탄|예수금)[이가은는:의]?\s*(?:약?\s*)?(\d[\d,.]*)\s*(억|만)"  # utf8-hygiene: allow-line regex ? quantifier adjacent to Hangul literals
        ),
        # "80억의 자본", "130억 원의 잔고"
        re.compile(
            r"(\d[\d,.]*)\s*(억|만)\s*(?:원)?[의이가]?\s*(?:잔고|자본|현금|자산|실탄|예수금)"  # utf8-hygiene: allow-line regex ? quantifier adjacent to Hangul literals
        ),
    ]
    # [V73-P0] 복합 금액 패턴 (38억 3,154만 200원) — _extract에서 별도 처리
    _COMPOUND_CAPITAL_RE = re.compile(
        r"(?:잔고|자본금?|현금|자산|실탄|예수금)[이가은는:의]?\s*(?:약?\s*)?"  # utf8-hygiene: allow-line regex ? quantifier adjacent to Hangul literals
        r"(?:(\d[\d,.]*)\s*억)?\s*(?:(\d[\d,.]*)\s*만)?\s*(?:(\d[\d,.]*)\s*원?)?"  # utf8-hygiene: allow-line regex ? quantifier adjacent to Hangul literals
    )
    # [V73-방어2] 대사(따옴표 내부) 제거용 패턴
    _DIALOGUE_RE = re.compile(r'["\u201c\u201d][^"\u201c\u201d]*["\u201c\u201d]')

    @staticmethod
    def _parse_hud_capital_to_eok(raw) -> float:
        """HUD 한국어 복합 금액을 억 단위 float로 변환.

        Examples:
            "38억 3,154만 200원" → 38.3154
            "131억 원" → 131.0
            "5000만원" → 0.5
            "3831540200" (원 단위 정수) → 38.3154
        """
        s = str(raw).replace(",", "").strip()
        if not s:
            return 0.0

        eok = 0.0
        # 억 부분
        m_eok = re.search(
            r"(\d+(?:\.\d+)?)\s*억",  # utf8-hygiene: allow-line regex ? quantifier adjacent to Hangul literals
            s,
        )
        if m_eok:
            eok += float(m_eok.group(1))
        # 만 부분
        m_man = re.search(
            r"(\d+(?:\.\d+)?)\s*만",  # utf8-hygiene: allow-line regex ? quantifier adjacent to Hangul literals
            s,
        )
        if m_man:
            eok += float(m_man.group(1)) / 10000
        # 억·만 모두 없으면 순수 숫자 → 원 단위로 간주
        if not m_eok and not m_man:
            digits = re.sub(r"[^\d.]", "", s)
            try:
                eok = float(digits) / 1_0000_0000 if digits else 0.0
            except (ValueError, TypeError):
                eok = 0.0
        return eok

    @staticmethod
    def _extract_capital_from_manuscript(manuscript: str) -> float | None:
        """확정 원고에서 마지막으로 언급된 자본금(억 단위)을 추출. 없으면 None."""
        # [V73-방어2] 대사(따옴표 내부) 제거 → 타인 자산 언급 오인 방지
        narration_only = Stage4PostProcessor._DIALOGUE_RE.sub("", manuscript)
        # 모든 패턴의 매치를 (문서 내 위치, 값) 튜플로 수집 후 위치순 정렬
        candidates: list[tuple[int, float]] = []
        for pat in Stage4PostProcessor._CAPITAL_PATTERNS:
            for m in pat.finditer(narration_only):
                raw = m.group(1).replace(",", "")  # 천 단위 콤마만 제거, 소수점 유지
                try:
                    num = float(raw)
                except (ValueError, TypeError):
                    continue
                unit = m.group(2)
                if unit == "만":
                    num /= 10000  # 만 → 억 환산
                candidates.append((m.start(), num))
        # [V73-P0] 복합 금액 매칭 (억+만+원 조합)
        for m in Stage4PostProcessor._COMPOUND_CAPITAL_RE.finditer(narration_only):
            eok_part = m.group(1)  # 억
            man_part = m.group(2)  # 만
            won_part = m.group(3)  # 원
            if not eok_part and not man_part:
                continue  # 최소 억 또는 만 필요
            total = 0.0
            if eok_part:
                total += float(eok_part.replace(",", ""))
            if man_part:
                total += float(man_part.replace(",", "")) / 10000
            if won_part:
                total += float(won_part.replace(",", "")) / 1_0000_0000
            candidates.append((m.start(), total))
        if not candidates:
            return None
        # 동일 위치면 복합(정밀) 값 우선, 가장 뒤에 나온 값 반환
        pos_best: dict[int, float] = {}
        for pos, val in candidates:
            if pos not in pos_best or val > pos_best[pos]:
                pos_best[pos] = val
        return pos_best[max(pos_best)]

    def _reconcile_capital(
        self,
        final_manuscript: str,
        ep_num: int,
        final_state_updates: dict | None = None,
    ) -> None:
        """확정 원고의 자본금과 HUD를 비교하여 불일치 시 경고 + 보정. 투자물 전용."""
        # [V73-방어1] Director가 이미 capital을 state_updates에 포함한 경우 → 스킵 (Director 주권 존중)
        if final_state_updates:
            _capital_keys = {"capital", "자본", "자본금", "잔고"}
            _director_keys = {str(k).lower() for k in final_state_updates}
            if _capital_keys & _director_keys:
                logging.debug("[V73] Director state_updates에 capital 포함 → 자본금 역동기화 스킵 (ep%d)", ep_num)
                return

        if not hasattr(self.ctx.sys, "hud") or not self.ctx.sys.hud:
            return

        hud = self.ctx.sys.hud
        # [V73] 투자물(FinanceHUD)에서만 실행 — 다른 장르는 단위 체계가 달라 오탐 위험
        from modules.core.genre_hud_manager import FinanceHUDManager

        if not isinstance(hud, FinanceHUDManager):
            return

        confirmed = self._extract_capital_from_manuscript(final_manuscript)
        if confirmed is None:
            return  # 금융 언급 없음 — 스킵

        capital_key = "capital"

        current_raw = hud.pro_data.get(capital_key, "0")
        current_value = self._parse_hud_capital_to_eok(current_raw)

        diff = abs(confirmed - current_value)
        if diff <= 5:  # 5억 이하 차이는 허용
            return

        logging.warning(
            "[V73] 자본금 불일치 감지 (ep%d): HUD %s=%s(→%.0f억), 원고=%.0f억 → 원고 기준 보정",
            ep_num,
            capital_key,
            current_raw,
            current_value,
            confirmed,
        )
        # [V73-B] Advisory — HUD 수정은 Director state_updates에 위임
        self.ctx.ui.log(
            f"   ⚠️ [V73] 자본금 불일치 감지: HUD {current_value:.0f}억 vs 원고 {confirmed:.0f}억"
            " (Director state_updates 반영 대기)"
        )

    def _normalize_hud_update_payload(self, approved_hud_updates: dict | None) -> dict[str, object]:
        if not isinstance(approved_hud_updates, dict) or not approved_hud_updates:
            return {}

        payload = (
            approved_hud_updates.get("actual_truth")
            if isinstance(approved_hud_updates.get("actual_truth"), dict)
            else approved_hud_updates
        )
        if not isinstance(payload, dict):
            return {}

        normalized: dict[str, object] = {}
        for raw_key, raw_value in payload.items():
            key = str(raw_key or "").strip()
            if not key or key.startswith("_"):
                continue
            is_safe, safe_value = self._json_safe_hud_value(raw_value)
            if is_safe:
                normalized[key] = safe_value
        return normalized

    @classmethod
    def _copy_hud_snapshot(cls, hud_snapshot) -> dict[str, object] | None:
        if not isinstance(hud_snapshot, dict):
            return None

        _, safe_snapshot = cls._json_safe_hud_value(hud_snapshot)
        return safe_snapshot if isinstance(safe_snapshot, dict) else {}

    @classmethod
    def _json_safe_hud_value(cls, value) -> tuple[bool, object]:
        if value is None or isinstance(value, str | int | float | bool):
            return True, value
        if isinstance(value, dict):
            normalized: dict[str, object] = {}
            for raw_key, raw_value in value.items():
                key = str(raw_key or "").strip()
                if not key:
                    continue
                is_safe, safe_value = cls._json_safe_hud_value(raw_value)
                if is_safe:
                    normalized[key] = safe_value
            return True, normalized
        if isinstance(value, list | tuple):
            normalized_items: list[object] = []
            for item in value:
                is_safe, safe_item = cls._json_safe_hud_value(item)
                if is_safe:
                    normalized_items.append(safe_item)
            return True, normalized_items
        return False, None

    def _build_projected_hud_snapshot(self, *, approved_hud_updates: dict | None = None):
        hud_snapshot = None
        try:
            hud = getattr(getattr(self.ctx, "sys", None), "hud", None)
            if hud and hasattr(hud, "snapshot"):
                hud_snapshot = hud.snapshot()
        except Exception:
            hud_snapshot = None

        normalized_updates = self._normalize_hud_update_payload(approved_hud_updates)
        safe_snapshot = self._copy_hud_snapshot(hud_snapshot)
        if normalized_updates:
            projected_snapshot = safe_snapshot or {}
            projected_snapshot.update(normalized_updates)
            return projected_snapshot

        return safe_snapshot

    def _resolve_approved_hud_updates(
        self,
        *,
        next_ep: int,
        final_state_updates: dict | None,
    ) -> tuple[dict[str, object], str]:
        if not isinstance(final_state_updates, dict) or not final_state_updates:
            return {}, ""

        director = None
        if isinstance(getattr(self.ctx, "agents", None), dict):
            director = self.ctx.agents.get("director")
        if director is None or not hasattr(director, "on_approve_workflow"):
            return {}, ""

        current_hud = {}
        try:
            hud = getattr(getattr(self.ctx, "sys", None), "hud", None)
            if hud and hasattr(hud, "snapshot"):
                snapshot = hud.snapshot()
                current_hud = self._copy_hud_snapshot(snapshot) or {}
        except Exception:
            current_hud = {}

        try:
            approved = director.on_approve_workflow(
                ep_num=next_ep,
                state_updates=final_state_updates,
                current_hud=current_hud,
            )
        except Exception as hud_err:
            return {}, str(hud_err)

        applied_updates = approved.get("applied_updates") if isinstance(approved, dict) else {}
        return self._normalize_hud_update_payload(applied_updates), ""

    def _save_pass_result_primary_db(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        output_dir,
        approved_hud_updates: dict | None = None,
    ) -> bool:
        db = self.ctx.current_project.db
        hud_snapshot = self._build_projected_hud_snapshot(approved_hud_updates=approved_hud_updates)

        try:
            with db._lock:
                if db.conn.in_transaction:
                    db.conn.commit()
                db.conn.execute("BEGIN")
                try:
                    db.save_manuscript(
                        ep_num=next_ep,
                        title=final_title,
                        content=final_manuscript,
                        hud_snapshot=hud_snapshot,
                    )
                    if final_state_updates:
                        db.update_martial_tracker(next_ep, final_state_updates)
                    db.conn.commit()
                except Exception:
                    db.conn.rollback()
                    raise
            return True
        except Exception as db_err:
            self.ctx.ui.log(f"   DB save failed: {db_err}")
            try:
                dump_path = self._write_emergency_manuscript_dump(
                    output_dir=output_dir,
                    next_ep=next_ep,
                    final_title=final_title,
                    final_manuscript=final_manuscript,
                )
                self.ctx.ui.log(f"   Emergency manuscript dump saved: {dump_path.name}")
            except Exception as dump_err:
                logging.warning("[Stage4] emergency manuscript dump failed: %s", dump_err)
                self.ctx.ui.log(f"   Emergency manuscript dump failed: {dump_err}")
            return False

    def _save_pass_result_quality_sidecars(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_state_updates: dict,
        quality_labels,
    ):
        db = self.ctx.current_project.db
        quality_signals = None

        if isinstance(quality_labels, dict) and hasattr(db, "save_episode_quality_label"):
            try:
                db.save_episode_quality_label(next_ep, quality_labels)
            except Exception as quality_err:
                self._report_soft_failure(
                    operation="save_episode_quality_label",
                    message="episode quality label sidecar save failed",
                    exc=quality_err,
                    ep_num=next_ep,
                    extra={"table": "episode_quality_labels"},
                )
                logging.warning("[QI-QM-4] quality label save failed: %s", quality_err)

        if hasattr(db, "save_episode_quality_signal"):
            try:
                quality_signals = compute_quality_signal_bundle(
                    final_manuscript,
                    consistency_checklist=(
                        (quality_labels or {}).get("consistency_checklist", {})
                        if isinstance(quality_labels, dict)
                        else {}
                    ),
                    warning_count=extract_warning_count(final_state_updates),
                )
                db.save_episode_quality_signal(next_ep, quality_signals)
            except Exception as signal_err:
                self._report_soft_failure(
                    operation="save_episode_quality_signal",
                    message="episode quality signal sidecar save failed",
                    exc=signal_err,
                    ep_num=next_ep,
                    extra={"table": "episode_quality_signals"},
                )
                logging.warning("[P0-QS] quality signal save failed: %s", signal_err)

        return quality_signals

    def _run_pass_result_local_side_effects(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        output_dir,
        v50_modules_available: bool,
        approved_hud_updates: dict | None = None,
        hud_update_error: str = "",
    ) -> None:
        if hud_update_error:
            self.ctx.ui.log(f"   HUD update failed: {hud_update_error}")

        normalized_hud_updates = self._normalize_hud_update_payload(approved_hud_updates)
        if normalized_hud_updates and hasattr(self.ctx.sys, "hud"):
            try:
                if hasattr(self.ctx.sys.hud, "bulk_update"):
                    self.ctx.sys.hud.bulk_update(normalized_hud_updates)
                else:
                    self.ctx.sys.hud.update_physical_status(normalized_hud_updates)
            except Exception as hud_err:
                self.ctx.ui.log(f"   HUD update failed: {hud_err}")

        try:
            self._reconcile_capital(final_manuscript, next_ep, final_state_updates=final_state_updates)
        except Exception as cap_err:
            logging.warning("[V73] capital reconcile failed: %s", cap_err)

        if next_ep % 5 == 0:
            try:
                self.ctx.generate_narrative_summary(next_ep)
            except Exception as summary_err:
                self.ctx.ui.log(f"   Narrative summary generation failed: {str(summary_err)[:60]}")

        try:
            logs_dir = self._resolve_project_log_dir()
            if logs_dir is not None:
                os.makedirs(logs_dir, exist_ok=True)

            if v50_modules_available and self.ctx.character_voice:
                try:
                    self.ctx.character_voice.analyze_manuscript(next_ep, final_manuscript)
                except Exception as voice_err:
                    logging.warning("[CharacterVoice] analyze_manuscript failed: %s", voice_err)
                try:
                    self.ctx.character_voice.save_to_db(self.ctx.current_project.db)
                except Exception as voice_save_err:
                    logging.warning("[CharacterVoice] save_to_db failed: %s", voice_save_err)

            if v50_modules_available and self.ctx.foreshadow_tracker:
                try:
                    self.ctx.foreshadow_tracker.auto_detect_from_manuscript(next_ep, final_manuscript)
                except Exception as foreshadow_err:
                    logging.warning("[ForeshadowTracker] auto_detect_from_manuscript failed: %s", foreshadow_err)
                try:
                    self.ctx.foreshadow_tracker.save_to_db(self.ctx.current_project.db)
                except Exception as foreshadow_save_err:
                    logging.warning("[ForeshadowTracker] save_to_db failed: %s", foreshadow_save_err)

            if v50_modules_available and getattr(self.ctx, "emotion_tracker", None):
                try:
                    emotion_tracker = self.ctx.emotion_tracker
                    emotion_tracker.add_episode_emotion(next_ep, "neutral", 0.5)
                    if hasattr(self.ctx, "current_project") and hasattr(self.ctx.current_project, "db"):
                        emotion_tracker.save_to_db(self.ctx.current_project.db)
                except Exception as emotion_err:
                    logging.warning("[TF7-P2-06] emotion_tracker save failed: %s", emotion_err)
        except Exception as log_err:
            self.ctx.ui.log(f"   Log side effects failed: {log_err}")

    def _run_pass_result_post_pass_pipeline(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        extract_chain_link_fn,
        quality_labels,
        quality_signals,
        detect_npc_overexposure_fn,
        detect_cross_episode_repetition_fn,
        v50_modules_available: bool,
    ) -> dict:
        genre_type = (
            (self.ctx.selected_genre or {}).get("type", "wuxia")
            if hasattr(self.ctx, "selected_genre") and self.ctx.selected_genre
            else "wuxia"
        )
        critical_keys = (
            self.ctx.sys.hud.get_critical_keys()
            if hasattr(self.ctx, "sys") and hasattr(self.ctx.sys, "hud") and self.ctx.sys.hud
            else []
        )
        manager_payload = self.post_pass_runtime._submit_manager_async(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            genre_type=genre_type,
            critical_keys=critical_keys,
        )
        self.post_pass_runtime._memorize_and_validate(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            arc_data=arc_data,
            blueprint=blueprint,
        )

        delta = self.post_pass_runtime._collect_manager_and_build_delta(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            bible_future=manager_payload["bible_future"],
            current_state=manager_payload["current_state"],
            lore_list=manager_payload["lore_list"],
            active_seeds=manager_payload["active_seeds"],
            causal_history=manager_payload["causal_history"],
            genre_type=genre_type,
            critical_keys=critical_keys,
            final_state_updates=final_state_updates,
            blueprint=blueprint,
            arc_data=arc_data,
        )
        bible_delta = delta["bible_delta"]

        try:
            chain_link = {}
            if extract_chain_link_fn:
                chain_link = extract_chain_link_fn(next_ep, final_manuscript, blueprint)
            if chain_link:
                chain_link = normalize_chain_link_for_genre(chain_link, genre_type)
                self.ctx.current_project.db.save_anchor(f"chain_link_{next_ep}", chain_link)
        except Exception as chain_link_err:
            self.ctx.ui.log(f"   Chain link save failed: {str(chain_link_err)[:50]}")

        self.post_pass_runtime._save_world_state_atomic(
            next_ep=next_ep,
            actual_truth=delta["actual_truth"],
            final_state_updates=final_state_updates,
            bible_delta=bible_delta,
            arc_data=arc_data,
        )
        self.post_pass_runtime._run_post_pass_advisories(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            blueprint=blueprint,
            final_state_updates=final_state_updates,
            quality_labels=quality_labels,
            quality_signals=quality_signals,
            state_truth_owner_contract=delta.get("state_truth_owner_contract", {}),
            detect_npc_overexposure_fn=detect_npc_overexposure_fn,
            detect_cross_episode_repetition_fn=detect_cross_episode_repetition_fn,
            v50_modules_available=v50_modules_available,
        )

        return {
            "actual_truth": delta["actual_truth"],
            "bible_delta": bible_delta,
            "state_truth_owner_contract": delta.get("state_truth_owner_contract", {}),
            "meta_save_failed": delta["meta_save_failed"],
        }

    def _finalize_pass_result_session(
        self,
        *,
        next_ep: int,
        final_title: str,
        final_manuscript: str,
        arc_data: dict,
    ) -> None:
        try:
            collector = get_metrics_collector()
            db = getattr(self.ctx.current_project, "db", None)
            scope = {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "model_breakdown": "{}",
            }
            if collector and db and hasattr(db, "save_cost_record"):
                scope = collector.snapshot_and_reset_scope()
                if (
                    scope.get("total_calls", 0) > 0
                    or scope.get("total_tokens", 0) > 0
                    or scope.get("total_cost_usd", 0.0) > 0
                ):
                    db.save_cost_record(
                        session_id=collector.session_id,
                        scope_type="episode",
                        scope_id=next_ep,
                        total_calls=scope.get("total_calls", 0),
                        total_tokens=scope.get("total_tokens", 0),
                        total_cost_usd=scope.get("total_cost_usd", 0.0),
                        model_breakdown=scope.get("model_breakdown", "{}"),
                    )
            pov_contract = resolve_project_pov_contract(self.ctx.current_project)
            logging.info(
                "[EPISODE_SUMMARY] stage=4 ep=%d arc=%s title=%s manuscript_len=%d total_calls=%d total_tokens=%d total_cost_usd=%.4f primary_pov=%s external_pov_insert_policy=%s style_guide_extracted_pov=%s effective_pov=%s",
                next_ep,
                arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else 0,
                str(final_title or "")[:120],
                len(final_manuscript or ""),
                int(scope.get("total_calls", 0) or 0),
                int(scope.get("total_tokens", 0) or 0),
                float(scope.get("total_cost_usd", 0.0) or 0.0),
                pov_contract.get("primary_pov", "") or "-",
                pov_contract.get("external_pov_insert_policy", "") or "-",
                pov_contract.get("style_guide_extracted_pov", "") or "-",
                pov_contract.get("effective_pov", "") or "-",
            )
        except Exception as cost_err:
            logging.warning("[Phase 6] episode cost logging failed: %s", cost_err)

        self.ctx.ui.log(f"\n✅ 제{next_ep}화 '{final_title}' 생산 완료! ({len(final_manuscript)}자)")

        if callable(getattr(self.ctx, "flush_audit_buffer", None)):
            self.ctx.flush_audit_buffer()

        try:
            self.ctx.perf_timer.log_summary()
            self.ctx.perf_timer.reset()
        except Exception as perf_err:
            logging.debug("[PerfTimer] s4 summary/reset: %s", perf_err)

    def _prepare_pass_result_settlement_inputs(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_state_updates: dict,
        arc_data: dict,
    ) -> dict:
        quality_labels = None
        stage4_attempt_key = ""
        if isinstance(final_state_updates, dict):
            quality_labels = final_state_updates.get("_director_quality_labels")
            stage4_attempt_key = self._extract_stage4_settlement_attempt_key(final_state_updates)
            final_state_updates = self._strip_stage4_internal_state_updates(final_state_updates)
        final_manuscript = self._normalize_reader_facing_manuscript(final_manuscript)
        approved_hud_updates, hud_update_error = self._resolve_approved_hud_updates(
            next_ep=next_ep,
            final_state_updates=final_state_updates,
        )
        return {
            "quality_labels": quality_labels,
            "attempt_key": stage4_attempt_key,
            "final_manuscript": final_manuscript,
            "final_state_updates": final_state_updates,
            "approved_hud_updates": approved_hud_updates,
            "hud_update_error": hud_update_error,
            "settlement_status_context": {
                "next_ep": next_ep,
                "arc_data": arc_data,
                "final_state_updates": final_state_updates,
                "attempt_key": stage4_attempt_key,
            },
        }

    def process_pass_result(
        self,
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        final_state_updates: dict,
        blueprint: dict,
        arc_data: dict,
        output_dir,
        v50_modules_available: bool,
        extract_chain_link_fn=None,
        detect_npc_overexposure_fn=None,
        detect_cross_episode_repetition_fn=None,
    ) -> bool:
        """[4-R1-c] Pass result post-processing. Returns False on DB save failure."""
        self.ctx.ui.log(f"\n📦 제{next_ep}화 데이터 정산 중...")
        settlement_inputs = self._prepare_pass_result_settlement_inputs(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            arc_data=arc_data,
        )
        _quality_labels = settlement_inputs["quality_labels"]
        _quality_signals = None
        final_manuscript = settlement_inputs["final_manuscript"]
        final_state_updates = settlement_inputs["final_state_updates"]
        approved_hud_updates = settlement_inputs["approved_hud_updates"]
        hud_update_error = settlement_inputs["hud_update_error"]
        settlement_status_context = settlement_inputs["settlement_status_context"]

        # DB 저장 (HUD보다 먼저 — DB 실패 시 HUD 오염 방지) [Sweep56]
        # [P0-D1/D4] lock 보호 + 원자적 트랜잭션으로 부분 저장 방지
        if not self._save_pass_result_primary_db(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            output_dir=output_dir,
            approved_hud_updates=approved_hud_updates,
        ):
            self._emit_stage4_settlement_status(status="primary_db_failed", **settlement_status_context)
            return False

        _quality_signals = self._save_pass_result_quality_sidecars(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_state_updates=final_state_updates,
            quality_labels=_quality_labels,
        )

        self._run_pass_result_local_side_effects(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            output_dir=output_dir,
            v50_modules_available=v50_modules_available,
            approved_hud_updates=approved_hud_updates,
            hud_update_error=hud_update_error,
        )
        post_pass_payload = self._run_pass_result_post_pass_pipeline(
            next_ep=next_ep,
            final_manuscript=final_manuscript,
            final_title=final_title,
            final_state_updates=final_state_updates,
            blueprint=blueprint,
            arc_data=arc_data,
            extract_chain_link_fn=extract_chain_link_fn,
            quality_labels=_quality_labels,
            quality_signals=_quality_signals,
            detect_npc_overexposure_fn=detect_npc_overexposure_fn,
            detect_cross_episode_repetition_fn=detect_cross_episode_repetition_fn,
            v50_modules_available=v50_modules_available,
        )
        _meta_save_failed = post_pass_payload["meta_save_failed"]

        # [S4-001] Episode Bible 저장 실패 시 오케스트레이터에 실패 신호 전달
        # WARNING: early return below skips remaining sinks. Manuscript is already persisted.
        if _meta_save_failed:
            logging.error("[S4-001] _meta_save_failed=True → process_pass_result 반환 False")
            self._emit_stage4_settlement_status(status="primary_persisted_meta_failed", **settlement_status_context)
            self.ctx.ui.log(
                "   ❌ 후처리 메타 저장 실패: 원고 본문은 저장됐지만 PASS 정산을 성공으로 확정하지 않습니다.",
                stage="stage4",
                component="post_pass_settlement",
                ep_num=next_ep,
                arc_num=arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else 0,
                event_kind="result",
                level="error",
                meta={"result": "meta_save_failed"},
            )
            return False

        settlement_packet_path = None
        try:
            settlement_packet_path = self._persist_stage4_settlement_packet(
                next_ep=next_ep,
                final_title=final_title,
                final_manuscript=final_manuscript,
                final_state_updates=final_state_updates,
                blueprint=blueprint,
                arc_data=arc_data,
                quality_labels=_quality_labels,
                quality_signals=_quality_signals,
                post_pass_payload=post_pass_payload,
                output_dir=output_dir,
            )
        except Exception as packet_err:
            logging.error("[S4-SETTLEMENT] settlement packet save failed ep=%d: %s", next_ep, packet_err)
            self._emit_stage4_settlement_status(
                status="settlement_packet_failed", detail=str(packet_err), **settlement_status_context
            )
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "stage4_settlement_packet_save_failed",
                    "stage4 settlement packet save failed",
                    {"ep": next_ep},
                )
            self.ctx.ui.log(
                "   ❌ structured settlement packet 저장 실패: 원고 본문은 저장됐지만 PASS 정산을 성공으로 확정하지 않습니다.",
                stage="stage4",
                component="post_pass_settlement_packet",
                ep_num=next_ep,
                arc_num=arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else 0,
                event_kind="result",
                level="error",
                meta={"result": "settlement_packet_save_failed"},
            )
            return False

        try:
            self._write_human_facing_manuscript_export(
                next_ep=next_ep,
                final_title=final_title,
                final_manuscript=final_manuscript,
                output_dir=output_dir,
            )
        except Exception as file_err:
            logging.error("[S4-TXT] human-facing txt save failed ep=%d: %s", next_ep, file_err)
            self._emit_stage4_settlement_status(
                status="human_export_failed",
                artifact_path=settlement_packet_path,
                detail=str(file_err),
                **settlement_status_context,
            )
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event(
                    "stage4_human_facing_export_failed",
                    "stage4 human-facing txt export failed",
                    {"ep": next_ep},
                )
            self.ctx.ui.log(
                "   ❌ human-facing txt 저장 실패: structured settlement packet은 저장됐지만 PASS 정산을 성공으로 확정하지 않습니다.",
                stage="stage4",
                component="post_pass_human_export",
                ep_num=next_ep,
                arc_num=arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else 0,
                event_kind="result",
                level="error",
                meta={"result": "human_facing_txt_save_failed"},
            )
            return False

        self._emit_stage4_settlement_status(
            status="fully_settled",
            artifact_path=settlement_packet_path,
            **settlement_status_context,
        )
        self._finalize_pass_result_session(
            next_ep=next_ep,
            final_title=final_title,
            final_manuscript=final_manuscript,
            arc_data=arc_data,
        )
        return True

    # ═══════════════════════════════════════════════════════════════

    def run_post_episode_tasks(self, *, skip_pause: bool = False) -> None:
        """[4-R1-d] Session wrap-up: logs, vector sync."""
        # [V62.3] Stage 4 루프 종료
        self.ctx.ui.log(f"\n{'=' * 50}")
        self.ctx.ui.log("📋 Stage 4 집필 세션 종료.")
        if not skip_pause:
            try:
                # [S4-P2-3] 자동화 환경에서 blocking input() 방지
                import sys

                if sys.stdin and sys.stdin.isatty():
                    input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")
                else:
                    self.ctx.ui.log("   (비대화 모드 — 자동 진행)")
            except (EOFError, OSError):
                pass

        # [V62.3] 벡터 메모리 일괄 동기화
        # [V66.3] 벡터 메모리 비활성화 시 스킵
        if self.ctx.memory and self.ctx.memory.is_operational():
            try:
                _drafts_path = None
                _raw_drafts_path = getattr(
                    getattr(getattr(self.ctx, "current_project", None), "paths", None),
                    "drafts",
                    None,
                )
                if isinstance(_raw_drafts_path, Path):
                    _drafts_path = _raw_drafts_path
                elif isinstance(_raw_drafts_path, str | os.PathLike):
                    _drafts_path = Path(_raw_drafts_path)
                if _drafts_path is None:
                    self.ctx.ui.log("   ⚠️ 벡터 메모리 동기화 스킵 (drafts 경로 없음)")
                    return
                self.ctx.ui.log("   🔄 벡터 메모리 일괄 동기화 중...")
                self.ctx.memory.sync_v20_drafts(drafts_path=_drafts_path)
                self.ctx.ui.log("   ✅ 벡터 메모리 동기화 완료")
            except Exception as vec_err:
                self.ctx.ui.log(f"   ⚠️ 벡터 메모리 동기화 실패 (비차단): {vec_err}")
