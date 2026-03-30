import copy
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import HUDKeys, NPCHUDKeys
from .db_manager import DBError, DBManager
from .runtime_paths import resolve_project_dir, resolve_projects_root


def safe_nested_get(data: Any, *keys, default=None) -> Any:
    """
    [V44] 중첩된 딕셔너리에서 안전하게 값을 추출

    Args:
        data: 대상 딕셔너리
        *keys: 순차적으로 접근할 키들
        default: 키가 없거나 타입 오류 시 반환할 기본값

    Example:
        safe_nested_get(data, 'MasterBible', 'CommercialCode', 'SuccessDevice', default='기본값')
    """
    current = data
    for key in keys:
        if current is None:
            return default
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


@dataclass
class ProjectPaths:
    root: Path
    config: Path
    drafts: Path
    memory: Path
    db_file: Path


class ProjectContext:
    """[V20 Data Anchor] SQLite S등급 엔진을 탑재한 데이터 주권 관리자"""

    def __init__(self, project_name: str, root_dir: str | Path | None = None):
        self.name = project_name
        default_root = Path(__file__).resolve().parents[2]
        if root_dir is None:
            self.projects_root = resolve_projects_root(default_root)
            self.base_path = resolve_project_dir(project_name, default_root)
        else:
            self.projects_root = Path(root_dir)
            self.base_path = self.projects_root / self.name
        self.db_path = self.base_path / "project_data.db"

        self.selected_tone = {"name": "Sovereign Standard", "writer": "DB Mode"}
        self.author_directives = ""

        self.paths = ProjectPaths(
            root=self.base_path,
            config=self.base_path / "config",
            drafts=self.base_path / "drafts",
            memory=self.base_path / "memory",
            db_file=self.db_path,
        )
        self._initialize_structure()

        # 1. DB 엔진 기동
        self.db = DBManager(self.paths.db_file)
        logging.info(f" [Sovereign DB] SQLite S-Grade 엔진 가동: {self.db_path.name}")

        self.master_bible = {}
        self.volumes = []
        self.arcs = []
        self.karma_status = {}

        # [V64.P4] 동적 주입 속성 선언 (monkey-patching 제거)
        self.genre = None  # main_a.py에서 selected_genre 주입
        self.guard = None  # main_a.py에서 GenreGuard 인스턴스 주입
        self.treatment_path = None  # main_a.py에서 트리트먼트 파일 경로 주입

        self._load_from_db()
        self._load_directives()

    def _initialize_structure(self) -> None:
        for path in [self.paths.root, self.paths.config, self.paths.drafts, self.paths.memory]:
            path.mkdir(parents=True, exist_ok=True)

        # [V40.1] plans 폴더 구조 생성 (arcs, blueprints txt 저장용)
        self.paths.plans = self.paths.root / "plans"
        self.paths.plans_arcs = self.paths.plans / "arcs"
        self.paths.plans_blueprints = self.paths.plans / "blueprints"
        for plan_path in [self.paths.plans, self.paths.plans_arcs, self.paths.plans_blueprints]:
            plan_path.mkdir(parents=True, exist_ok=True)

        # [TF-31-4] style_seeds_final.txt 레거시 제거 — StyleExtractor가 대체
        cash_dir = self.paths.config / "cash"
        cash_dir.mkdir(parents=True, exist_ok=True)

    def close(self):
        """Release DB resources."""
        if self.db:
            self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _load_directives(self) -> None:
        d_path = self.paths.config / "author_directives.txt"
        if d_path.exists():
            self.author_directives = d_path.read_text(encoding="utf-8")
        else:
            d_path.write_text("# 절대 지시 사항을 입력하세요.\n", encoding="utf-8")

    def _load_from_db(self) -> None:
        """[V44] 기동 시 DB의 앵커 데이터를 메모리로 수혈 (타입 검증 강화)"""
        # [V44] anchors 로드 및 타입 검증
        try:
            anchors = self.db.load_all_anchors()
        except (DBError, Exception) as e:
            logging.warning(f" [ProjectContext] DB 앵커 로드 실패: {e}")
            logging.warning("→ 빈 상태로 초기화합니다")
            anchors = {}

        # [V44] anchors 타입 검증
        if not isinstance(anchors, dict):
            logging.warning(f" [ProjectContext] anchors가 dict가 아님: {type(anchors)}")
            anchors = {}

        # [V44] 각 앵커 데이터 안전 추출
        self.master_bible = anchors.get("bible") if isinstance(anchors.get("bible"), dict) else {}
        self.volumes = anchors.get("volumes") if isinstance(anchors.get("volumes"), list) else []
        authoritative_arcs = []
        try:
            authoritative_arcs = self.db.load_arc_payloads()
        except Exception:
            authoritative_arcs = []
        self.arcs = authoritative_arcs if authoritative_arcs else (
            anchors.get("arcs") if isinstance(anchors.get("arcs"), list) else []
        )

        # [TF-7-P0-03] preset_state anchor 복원 — 호출부에서 app.preset_registry 재구성용
        try:
            _preset_raw = self.db.load_anchor("preset_state")
            self._preset_state_raw = _preset_raw if isinstance(_preset_raw, dict) else None
        except Exception:
            self._preset_state_raw = None

        # [V44] karma 로드 (별도 예외 처리)
        try:
            self.karma_status = self.db.get_all_karma()
            if not isinstance(self.karma_status, dict):
                self.karma_status = {}
        except Exception as e:
            logging.warning(f" [ProjectContext] karma 로드 실패: {e}")
            self.karma_status = {}

        # [V44] safe_nested_get으로 중첩 접근
        success_device = safe_nested_get(
            self.master_bible,
            "MasterBible",
            "CommercialCode",
            "SuccessDevice",
            default=self.selected_tone.get("writer", "DB Mode"),
        )
        # 추가 fallback: MasterBible 래퍼 없이 직접 접근하는 경우
        if success_device == self.selected_tone.get("writer", "DB Mode"):
            success_device = safe_nested_get(
                self.master_bible,
                "CommercialCode",
                "SuccessDevice",
                default=self.selected_tone.get("writer", "DB Mode"),
            )
        self.selected_tone["writer"] = success_device

    # --- [Core: 데이터 박제 및 스마트 동기화] ---
    # modules/core/project_manager.py 내부

    def save_v20_anchor(self, stage, data):
        """
        [V25.2.1 Final Integrity] 성경 저장 시 모든 데이터 타입을 TEXT로 정규화하여 DB 유실 제로화
        """
        # 1. 데이터 포맷 정규화 (리스트 래핑)
        if stage in ["volumes", "arcs"] and isinstance(data, dict):
            data = data.get(stage, [data]) if isinstance(data.get(stage), list) else [data]

        # 2. 스테이지별 메모리 동기화 및 하위 테이블 트리거
        if stage == "bible":
            self.master_bible = data
            bible_root = data.get("MasterBible", data)

            # [A] 복선(Seeds) 테이블 동기화
            seeds = bible_root.get("Seeds", [])
            if seeds:
                self.db.sync_seeds(seeds)

            # [B] 로어(Encyclopedia) 일괄 동기화 (Type Safety Logic)
            lore_batch = []
            assets = bible_root.get("AssetLibrary", {})

            for cat, items in assets.items():
                if isinstance(items, list):  # KeyNPCs, KeyItems 등
                    for item in items:
                        # [V44] item이 dict인 경우에만 .get() 사용
                        if isinstance(item, dict):
                            name = item.get("Item") or item.get("name")
                            desc = item.get("Description") or item.get("desc")
                            if name and desc:
                                if isinstance(desc, (list, dict)):
                                    desc = json.dumps(desc, ensure_ascii=False)
                                lore_batch.append((cat, name, desc))
                        elif isinstance(item, str) and item.strip():
                            # 문자열 아이템인 경우 이름과 설명을 동일하게 처리
                            lore_batch.append((cat, item, item))

                elif isinstance(items, dict):  # SpeechStyle 등
                    for name, desc in items.items():
                        if isinstance(desc, (list, dict)):
                            desc = json.dumps(desc, ensure_ascii=False)
                        lore_batch.append((cat, name, desc))

                # 🚨 [Final Patch] Persona 같은 단일 문자열 데이터까지 완벽 포획
                elif isinstance(items, str):
                    lore_batch.append((cat, cat, items))

            if lore_batch:
                self.db.update_lore_items_batch(lore_batch)

            # [C] Martial Tracker(HUD) 강제 동기화
            # [V49 FIX] ep_num=0 하드코딩 제거 - 실제 에피소드 저장은 commit_full_episode_data에서 수행
            # bible 저장 시에는 HUD 동기화를 하지 않음 (잘못된 ep_num으로 덮어쓰기 방지)
            actual_data = self._get_protagonist_actual_truth_node(bible_root)
            if actual_data:
                # 현재 최신 에피소드 번호 조회
                # [V70] get_latest_episode_number()는 NEXT ep 반환 → -1로 현재 ep 계산
                latest_ep = self.db.get_latest_episode_number() - 1
                if latest_ep > 0:
                    self.record_martial_stats(latest_ep, actual_data)
                    logging.info(f" [Sync] 성경 저장과 동시에 HUD 테이블 동기화 완료 (ep {latest_ep}).")
                else:
                    # 에피소드가 없으면 ep_num=0으로 초기 상태 저장
                    self.record_martial_stats(0, actual_data)
                    logging.info(" [Sync] 초기 HUD 상태 저장 (ep 0).")

        elif stage == "volumes":
            self.volumes = data
        elif stage == "arcs":
            self.arcs = data
        elif stage == "karma":
            self.karma_status = data

        # 3. Anchor(JSON) 최종 박제
        result = self.db.save_anchor(stage, data)
        # [V61.6 Fix] 하위 테이블 동기화(sync_seeds, lore_batch)가 암묵적 트랜잭션을 열어
        # save_anchor의 in_transaction 체크에 의해 commit이 스킵되는 버그 수정
        # [TF-30-8] resolve_pending_transaction 공개 API로 전환 (_lock 직접 접근 제거)
        try:
            self.db.resolve_pending_transaction(commit=bool(result))
        except Exception as rollback_err:
            logging.warning(f"[TF-15/P0] save_anchor resolve_pending failed: {rollback_err}")
        if stage == "arcs" and result:
            self._save_arcs_to_txt(data)
        return result

    def load_v20_anchor(self, stage, default=None):
        """
        [V61.3] DB에서 특정 앵커 데이터를 로드

        Args:
            stage: 앵커 키 (bible, volumes, arcs, style_guide 등)
            default: 키가 없을 때 반환할 기본값

        Returns:
            dict: 앵커 데이터 또는 기본값
        """
        return self.db.load_anchor(stage, default)

    def save_episode_blueprint(self, ep_num, data) -> None:
        """Stage 3 설계도 DB 박제"""
        self.db.save_blueprint(ep_num, data)
        # [V40.1] Blueprint txt 파일 저장
        self._save_blueprint_to_txt(ep_num, data)

    def _render_arc_txt(self, arc: dict) -> str:
        lines = [
            f"{'=' * 60}",
            f"ARC {arc.get('arc_no', arc.get('global_arc_no', arc.get('arc_num', 0)))}",
            f"{'=' * 60}",
            "",
            "[기본 정보]",
            f"- 볼륨: {arc.get('volume_no', 'N/A')}",
            f"- 에피소드 범위: {arc.get('ep_start', 'N/A')} ~ {arc.get('ep_end', 'N/A')}",
            f"- 에피소드 수: {arc.get('ep_count', 'N/A')}",
            "",
            "[전술 문서 (Tactical Doc)]",
            f"{'-' * 40}",
            f"{arc.get('tactical_doc', '내용 없음')}",
            "",
            "[비트 시퀀스 (Beat Sequence)]",
            f"{'-' * 40}",
        ]

        beat_seq = arc.get("beat_sequence", [])
        if isinstance(beat_seq, list):
            for i, beat in enumerate(beat_seq, 1):
                if isinstance(beat, dict):
                    lines.append(f"Beat {i}: {beat.get('beat', beat.get('description', str(beat)))}")
                else:
                    lines.append(f"Beat {i}: {beat}")
        elif isinstance(beat_seq, str):
            lines.append(beat_seq)

        seeds = arc.get("seed_injection", arc.get("seeds", []))
        if seeds:
            lines.append("")
            lines.append("[복선 (Seeds)]")
            lines.append(f"{'-' * 40}")
            if isinstance(seeds, list):
                for seed in seeds:
                    if isinstance(seed, dict):
                        lines.append(
                            f"- {seed.get('id', seed.get('seed_id', 'N/A'))}: {seed.get('hint', seed.get('description', ''))}"
                        )
                    else:
                        lines.append(f"- {seed}")

        return "\n".join(lines)

    def _save_arcs_to_txt(self, arcs_data) -> None:
        # [DB-Eff-P4] export 전용: DB(blueprints/anchors 테이블)가 primary source.
        # 이 파일은 human-readable 참조용. 배포/롤백 대상 아님.
        """[V40.1] Arc 데이터를 txt 파일로 저장"""
        if not arcs_data or not isinstance(arcs_data, list):
            return

        try:
            # [V40.1 Safety] 폴더가 없으면 생성
            if not hasattr(self.paths, "plans_arcs"):
                self.paths.plans_arcs = self.paths.root / "plans" / "arcs"
            self.paths.plans_arcs.mkdir(parents=True, exist_ok=True)
            expected_files = set()
            for arc in arcs_data:
                if not isinstance(arc, dict):
                    continue

                arc_no = arc.get("arc_no", arc.get("global_arc_no", 0))
                if not arc_no:
                    continue

                # 파일명: arc_001.txt
                filename = f"arc_{arc_no:03d}.txt"
                filepath = self.paths.plans_arcs / filename
                expected_files.add(filename)
                rendered = self._render_arc_txt(arc)
                existing = filepath.read_text(encoding="utf-8") if filepath.exists() else None
                if existing != rendered:
                    filepath.write_text(rendered, encoding="utf-8")

            for stale_file in self.paths.plans_arcs.glob("arc_*.txt"):
                if stale_file.name not in expected_files:
                    stale_file.unlink()

            logging.info(f" [Plans] Arc txt 파일 {len(arcs_data)}개 저장 완료")
        except Exception as e:
            logging.warning(f" [Plans] Arc txt 저장 실패: {e}")

    def _save_blueprint_to_txt(self, ep_num, data) -> None:
        # [DB-Eff-P4] export 전용: DB(blueprints 테이블)가 primary source.
        # 이 파일은 human-readable 참조용. 배포/롤백 대상 아님.
        """[V40.1] Blueprint 데이터를 txt 파일로 저장"""
        if not data or not isinstance(data, dict):
            return

        try:
            # [V40.1 Safety] 폴더가 없으면 생성
            if not hasattr(self.paths, "plans_blueprints"):
                self.paths.plans_blueprints = self.paths.root / "plans" / "blueprints"
            self.paths.plans_blueprints.mkdir(parents=True, exist_ok=True)

            # 파일명: blueprint_0001.txt
            filename = f"blueprint_{ep_num:04d}.txt"
            filepath = self.paths.plans_blueprints / filename

            lines = [
                f"{'=' * 60}",
                f"BLUEPRINT - Episode {ep_num}",
                f"{'=' * 60}",
                "",
                "[통합 시나리오 (Integrated Scenario)]",
                f"{'-' * 40}",
                f"{data.get('integrated_scenario', '내용 없음')}",
                "",
                "[씬 분해 (Scene Breakdown)]",
                f"{'-' * 40}",
            ]

            scene_breakdown = data.get("scene_breakdown", {})
            if isinstance(scene_breakdown, dict):
                for scene_key, scene_data in scene_breakdown.items():
                    lines.append("")
                    lines.append(f"## {scene_key}")
                    if isinstance(scene_data, dict):
                        for k, v in scene_data.items():
                            lines.append(f"  - {k}: {v}")
                    else:
                        lines.append(f"  {scene_data}")
            elif isinstance(scene_breakdown, str):
                lines.append(scene_breakdown)

            # 핵심 갈등/긴장
            if "core_tension" in data:
                lines.append("")
                lines.append("[핵심 긴장 (Core Tension)]")
                lines.append(f"{'-' * 40}")
                lines.append(f"{data['core_tension']}")

            # 예상 결말
            if "expected_ending" in data:
                lines.append("")
                lines.append("[예상 결말 (Expected Ending)]")
                lines.append(f"{'-' * 40}")
                lines.append(f"{data['expected_ending']}")

            filepath.write_text("\n".join(lines), encoding="utf-8")
            logging.info(f" [Plans] Blueprint {ep_num}화 txt 저장 완료")
        except Exception as e:
            logging.warning(f" [Plans] Blueprint txt 저장 실패: {e}")

    def _normalize_seed_id(self, raw_id):
        """[V26 Integrity Filter] AI 오타 교정 및 성경 ID 매칭"""
        # 1. 성경 내 실제 ID 목록 확보
        bible_seeds = self.master_bible.get("MasterBible", {}).get("Seeds", [])
        valid_ids = {s.get("id"): s.get("id") for s in bible_seeds if isinstance(s, dict)}

        # 2. 완전 일치 여부 확인
        if raw_id in valid_ids:
            return raw_id

        # 3. 퍼지 매칭 (특수문자 제거 후 대조)
        clean_raw = re.sub(r"[^a-zA-Z0-9]", "", raw_id).upper()
        for vid in valid_ids:
            if not vid:
                continue
            clean_vid = re.sub(r"[^a-zA-Z0-9]", "", vid).upper()
            if clean_raw == clean_vid:
                logging.info(f" [Normalized] Seed ID 교정: {raw_id} -> {vid}")
                return vid

        return raw_id  # 매칭 실패 시 원본 유지(데이터 보존)

    def sync_and_cleanup_seeds(self) -> None:
        """[V27.5 S-Grade] 성경(Bible) 기반 복선 데이터 동기화 및 유령 ID 정화"""
        bible_root = self.master_bible.get("MasterBible", self.master_bible)
        bible_seeds = bible_root.get("Seeds", [])

        if not bible_seeds:
            return

        # 1. 성경에 등록된 유효 ID 목록 확보
        valid_ids = [s.get("id") for s in bible_seeds if s.get("id")]

        # [E5c-P1-1] Atomic DELETE + sync_seeds under single lock scope with rollback
        # [TF-30-8] delete_orphaned_seeds 공개 API 사용 → _lock 직접 접근 제거
        try:
            self.db.begin()
            self.db.delete_orphaned_seeds(valid_ids)
            self.db.sync_seeds(bible_seeds)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        logging.info(f" [Cleanup] 복선 데이터 정화 완료 (유효 ID: {len(valid_ids)}건)")

    def commit_full_episode_data(
        self,
        ep_num,
        manuscript_data,
        martial_data,
        state_data,
        causal_links,
        karma_data,
        lore_data,
        recovered_seeds,
        memory,
    ) -> bool:
        """
        [V35 Alpha] 트랜잭션 원자성 강화 + NPC HUD 실시간 동기화 통합 버전
        """
        self.db.update_sync_status(ep_num, 0)
        bible_snapshot = copy.deepcopy(self.master_bible)

        try:
            recovered_seeds = self._normalize_recovered_seeds(recovered_seeds)
            self._merge_lore_npc_hud_updates(lore_data)
            self._persist_episode_bible_and_factory(
                ep_num=ep_num,
                manuscript_data=manuscript_data,
                martial_data=martial_data,
                state_data=state_data,
                causal_links=causal_links,
                karma_data=karma_data,
                lore_data=lore_data,
                recovered_seeds=recovered_seeds,
            )
            self._sync_episode_vector_memory(
                ep_num=ep_num,
                manuscript_data=manuscript_data,
                state_data=state_data,
                causal_links=causal_links,
                memory=memory,
            )
            return True
        except Exception as e:
            logging.warning(f" [Critical Error] 제 {ep_num}화 원자적 저장 실패: {e}")
            self.master_bible = bible_snapshot
            self.db.update_sync_status(ep_num, 0)
            return False

    def _normalize_recovered_seeds(self, recovered_seeds) -> list[dict]:
        normalized_seeds = []
        if recovered_seeds and isinstance(recovered_seeds, list):
            for rec in recovered_seeds:
                if not isinstance(rec, dict):
                    continue
                raw_id = rec.get("seed_id") or rec.get("id")
                rec["seed_id"] = self._normalize_seed_id(raw_id) if raw_id else "UNKNOWN"
                normalized_seeds.append(rec)
        return normalized_seeds

    def _merge_lore_npc_hud_updates(self, lore_data) -> None:
        if not lore_data or not isinstance(lore_data, dict) or "Key_NPCs" not in lore_data:
            return
        bible_root = self.master_bible.get("MasterBible", self.master_bible)
        bible_npcs = bible_root.get("AssetLibrary", {}).get("KeyNPCs", [])
        npc_hud_key = self._get_npc_hud_key()
        for new_npc in lore_data["Key_NPCs"]:
            if not isinstance(new_npc, dict):
                continue
            npc_name = new_npc.get("name") or new_npc.get("Name")
            for target in bible_npcs:
                if target.get("name") != npc_name:
                    continue
                self._merge_single_npc_hud_update(target, new_npc, npc_hud_key)
                break

    def _merge_single_npc_hud_update(self, target: dict, new_npc: dict, npc_hud_key: str) -> None:
        if npc_hud_key not in new_npc:
            return
        new_hud = new_npc[npc_hud_key]
        if not isinstance(new_hud, dict):
            return
        old_hud = target.get(npc_hud_key, {})
        if not isinstance(old_hud, dict):
            old_hud = {}
        changes = self._collect_npc_hud_changes(old_hud, new_hud)
        if changes:
            npc_name = new_npc.get("name") or new_npc.get("Name") or target.get("name", "UNKNOWN")
            logging.info(f" [NPC Trace] {npc_name} 변화 감지: {', '.join(changes)}")
        target.setdefault(npc_hud_key, {}).update(new_hud)

    def _collect_npc_hud_changes(self, old_hud: dict, new_hud: dict) -> list[str]:
        changes = []
        for key in ["achievement_rate", "current_status", "realm"]:
            if new_hud.get(key) is not None and new_hud.get(key) != old_hud.get(key):
                changes.append(f"{key}: {old_hud.get(key, 'N/A')} -> {new_hud[key]}")
        old_equip = old_hud.get("equipment", [])
        new_equip = new_hud.get("equipment", [])
        if new_equip and new_equip != old_equip:
            old_set = set(old_equip) if isinstance(old_equip, list) else set()
            new_set = set(new_equip) if isinstance(new_equip, list) else set()
            added = new_set - old_set
            removed = old_set - new_set
            if added:
                changes.append(f"equipment 획득: {list(added)}")
            if removed:
                changes.append(f"equipment 상실: {list(removed)}")
        return changes

    def _persist_episode_bible_and_factory(
        self,
        *,
        ep_num,
        manuscript_data,
        martial_data,
        state_data,
        causal_links,
        karma_data,
        lore_data,
        recovered_seeds,
    ) -> None:
        try:
            self.save_v20_anchor("bible", self.master_bible)
            self.sync_and_cleanup_seeds()
        except Exception as bible_err:
            logging.warning(f" [Critical] Bible 선행 저장 실패: {bible_err}")
            raise RuntimeError(f"Bible 저장 실패로 에피소드 커밋 중단: {bible_err}") from bible_err

        try:
            db_success = self.db.commit_episode_factory(
                ep_num,
                manuscript_data,
                martial_data,
                state_data,
                causal_links,
                karma_data,
                lore_data,
                recovered_seeds,
            )
        except Exception as factory_err:
            raise RuntimeError("SQLite Episode Factory 저장 실패") from factory_err

        if not db_success:
            raise RuntimeError("SQLite Episode Factory 저장 실패")

    def _sync_episode_vector_memory(
        self,
        *,
        ep_num,
        manuscript_data,
        state_data,
        causal_links,
        memory,
    ) -> None:
        try:
            normalized_state = self._coerce_state_dict_for_vector_sync(state_data)
            summary = (
                normalized_state.get("context_audit", {}).get("summary", "요약 없음")
                if isinstance(normalized_state, dict)
                else "요약 없음"
            )
            content_text = (
                manuscript_data.get("content", "") if isinstance(manuscript_data, dict) else str(manuscript_data)
            )
            vector_success = memory.memorize_v20_episode(ep_num, content_text, summary, causal_links)
            if vector_success:
                self.db.update_sync_status(ep_num, 1)
            else:
                logging.warning(f" [Sync Warning] 제 {ep_num}화 벡터 주입 지연 (플래그 0 유지)")
        except Exception as sub_e:
            logging.warning(f" [Partial Failure] 벡터 동기화 중 오류: {sub_e}")
            logging.warning(f" [WARNING] 에피소드 {ep_num}: DB/Bible 저장됨, Vector 동기화 불완전")
            try:
                self.db.update_sync_status(ep_num, 2)
            except Exception as sync_err:
                logging.warning("[Sweep5-D] sync_status partial update failed (ep=%s): %s", ep_num, sync_err)

    def _coerce_state_dict_for_vector_sync(self, state_data):
        if isinstance(state_data, str):
            try:
                return json.loads(state_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return state_data

    # --- [Getter: 하이브리드 맥락 인출] ---
    @property
    def latest_state(self):
        state = self.db.get_latest_state()
        if not state:
            bible_root = self.master_bible.get("MasterBible", self.master_bible)
            hud_key = self._get_protagonist_hud_key(bible_root if isinstance(bible_root, dict) else {})
            if isinstance(bible_root, dict):
                return bible_root.get(hud_key, bible_root.get("martial_hud", {}))
            return {}
        return state

    def get_sequential_context(self, current_ep) -> tuple:
        """직전 원고 3화와 직전 설계도를 DB에서 인출 (에이전트 지능용)"""
        manuscripts = self.db.get_context_manuscripts(current_ep, limit=3)  #
        prev_blueprint = self.db.get_previous_blueprint(current_ep)  #
        return manuscripts, prev_blueprint

    def get_causal_history_summary(self):
        """최근 5화의 인과 요약 체인 인출"""
        return self.db.get_causal_summary_chain(limit=5)  #

    def get_latest_episode_number(self) -> int:
        """
        [V40.1 Hybrid] DB와 물리 파일 중 최신 회차를 반환 (안전장치)

        Returns:
            int: 다음에 생성할 에피소드 번호
        """
        # DB에서 최신 에피소드 확인
        db_ep = self.db.get_latest_episode_number()

        # 물리 파일에서도 확인 (sync 누락 방지)
        try:
            draft_files = list(self.paths.drafts.glob("*.txt"))
            file_ep = 0
            for f in draft_files:
                # [V70] ep_NNNN.txt 패턴 매칭 (기존 [:4].isdigit()는 "ep_0"이라 항상 False)
                _m = re.match(r"ep_(\d+)\.txt", f.name)
                if _m:
                    file_ep = max(file_ep, int(_m.group(1)))

            # 둘 중 큰 값 반환 (안전장치) — file_ep+1: db_ep와 동일 스케일 (next ep)
            return max(db_ep, file_ep + 1 if file_ep > 0 else 0)  # [V70] 스케일 통일
        except Exception:
            # 파일 확인 실패 시 DB 값 사용
            return db_ep

    def _get_genre_type(self) -> str:
        genre = getattr(self, "genre", None)
        if isinstance(genre, dict):
            return str(genre.get("type") or genre.get("name") or "")
        return str(genre or "")

    def _get_protagonist_hud_key(self, bible_root: dict) -> str:
        genre_type = self._get_genre_type()
        candidates = [HUDKeys.get_hud_root(genre_type)] if genre_type else []
        for hud_key in (
            "MartialHUD",
            "FinanceHUD",
            "HunterHUD",
            "ComposerHUD",
            "CookingHUD",
            "JoseonHUD",
            "ActorHUD",
            "SportsHUD",
            "MedicalHUD",
            "FantasyHUD",
        ):
            if hud_key not in candidates:
                candidates.append(hud_key)

        for hud_key in candidates:
            hud = bible_root.get(hud_key, {}) if isinstance(bible_root, dict) else {}
            protagonist = hud.get("Protagonist", {}) if isinstance(hud, dict) else {}
            if isinstance(protagonist, dict):
                return hud_key
        return HUDKeys.get_hud_root(genre_type)

    def _get_protagonist_actual_truth_node(self, bible_root: dict) -> dict:
        if not isinstance(bible_root, dict):
            return {}
        hud_key = self._get_protagonist_hud_key(bible_root)
        hud = bible_root.get(hud_key, {})
        protagonist = hud.get("Protagonist", {}) if isinstance(hud, dict) else {}
        if not isinstance(protagonist, dict):
            return {}
        actual_truth = protagonist.get("actual_truth", {})
        return actual_truth if isinstance(actual_truth, dict) else {}

    def _get_npc_hud_key(self) -> str:
        return NPCHUDKeys.get_key(self._get_genre_type())

    # --- [Bridge 보완: 15대 지표 데이터 가드] ---
    def record_martial_stats(self, ep_num, stats_data) -> None:
        """에이전트의 데이터 키 누락이나 오타로부터 DB를 보호하며 기록"""
        # DB 테이블 컬럼과 일치하는 15대 지표 화이트리스트
        valid_keys = [
            "alias",
            "rank",
            "realm",
            "internal_energy",
            "mental_method",
            "reputation",
            "public_image",
            "equipment",
            "wealth",
            "token",
            "misunderstanding",
            "obsession",
            "current_objective",
            "qi_nature",
            "causal_injuries",
        ]
        # 규격에 맞는 데이터만 필터링 (누락 시 None 처리하여 DB 에러 방지)
        sanitized_data = {k: stats_data.get(k) for k in valid_keys}
        self.db.update_martial_tracker(ep_num, sanitized_data)
        logging.info(f" [DB] 제 {ep_num}화 15대 지표 트래커 박제 완료.")

    # modules/core/project_manager.py 파일 내부 ProjectContext 클래스에 추가

    def save_manuscript_to_db(self, ep_num, title, content) -> None:
        """[Phase 0 전용] 물리 원고 데이터를 DB로 직접 미러링하여 박제"""
        # DBManager의 save_manuscript 기능을 호출함
        self.db.save_manuscript(ep_num, title, content)
        logging.info(f" [Mirroring] 제 {ep_num}화 원고 DB 동기화 완료.")

    # --- [Utility: 리셋 및 동기화] ---
    def reset_project(self, target_ep) -> None:
        """DB와 물리 파일을 동시에 정화"""
        self.db.reset_after(target_ep)  #

        if self.paths.drafts.exists():
            for f in self.paths.drafts.glob("*.txt"):
                # [V70] ep_NNNN.txt 패턴 매칭
                _m = re.match(r"ep_(\d+)\.txt", f.name)
                if _m and int(_m.group(1)) >= target_ep:
                    f.unlink()
        logging.info(f" [Reset] 제 {target_ep}화 이후의 모든 타임라인이 소거되었습니다.")

    def force_sync_v25_dna(self, bible_file_name, treatment_file_name) -> bool:
        """
        [Phase 0] AI의 출력 제한을 우회하여 50개 전술 블록을 Bible에 강제 주입 및 DB 박제
        """
        logging.info(f" [DNA Injection] '{treatment_file_name}' 데이터를 Bible에 강제 이식합니다...")

        # 1. Bible(성경) 데이터 로드
        bible_path = self.paths.root.parent.parent / "bible" / bible_file_name
        treatment_path = self.paths.root.parent.parent / "treatments" / treatment_file_name

        try:
            with open(bible_path, encoding="utf-8") as f:
                bible_data = json.load(f)

            with open(treatment_path, encoding="utf-8") as f:
                treatment_data = json.load(f)

            from modules.core.stage0_handoff import build_plot_roadmap_from_treatment

            # [V49.3] Phase 0 JSON 스키마 검증
            try:
                from modules.core.response_schemas import validate_phase0_files

                is_valid, report = validate_phase0_files(bible_data, treatment_data)

                # 검증 결과 출력
                logging.info(" [V49.3] Phase 0 파일 검증 결과:")
                logging.info(f"Bible: {'✅ 유효' if report['bible']['valid'] else '❌ 오류'}")
                if report["bible"]["errors"]:
                    for err in report["bible"]["errors"]:
                        logging.warning(f"❌ {err}")
                if report["bible"]["warnings"]:
                    for warn in report["bible"]["warnings"]:
                        logging.warning(f" {warn}")

                logging.info(f"Treatment: {'✅ 유효' if report['treatment']['valid'] else '❌ 오류'} ({report['treatment']['block_count']}개 블록)"
                )
                if report["treatment"]["errors"]:
                    for err in report["treatment"]["errors"]:
                        logging.warning(f"❌ {err}")
                if report["treatment"]["warnings"]:
                    for warn in report["treatment"]["warnings"][:5]:  # 최대 5개만 표시
                        logging.warning(f" {warn}")
                    if len(report["treatment"]["warnings"]) > 5:
                        logging.warning(f" ... 외 {len(report['treatment']['warnings']) - 5}개 경고")

                if not is_valid:
                    logging.warning(" [V49.3] 파일 검증 실패. Phase 0을 중단합니다.")
                    logging.warning("→ Bible 또는 Treatment 파일 구조를 확인하세요.")
                    return False
            except ImportError:
                logging.warning(" [V49.3] 스키마 검증 모듈 로드 실패. 검증 없이 진행합니다.")

            # 2. MasterBible 루트 확보 (포장지가 있든 없든 대응)
            master_bible = bible_data.get("MasterBible", bible_data)

            # 3. 트리트먼트 블록을 plot_roadmap 규격으로 변환하여 주입
            # [V62.2] flat 구조: block_no + 원본 필드 전체 (중복 래핑 제거)
            refined_roadmap = build_plot_roadmap_from_treatment(treatment_data)
            if not refined_roadmap:
                logging.warning(" [DNA Sync Error] canonical treatment normalization produced no roadmap entries")
                return False

            # 4. 성경 객체에 최종 로드맵 결합
            master_bible["plot_roadmap"] = refined_roadmap
            self.master_bible = {"MasterBible": master_bible}

            # 5. [핵심] SQLite DB에 'bible' 앵커로 전체 블록 강제 박제
            # 여기서 DBManager의 save_anchor를 호출함
            success = self.save_v20_anchor("bible", self.master_bible)

            if success:
                logging.info(f"✅ [S-Grade Success] {len(refined_roadmap)}개 블록이 포함된 '완전한 성경'이 DB에 안착되었습니다."
                )
                logging.info(f" 로드맵 크기: {len(self.master_bible['MasterBible']['plot_roadmap'])} blocks")
                return True
            else:
                # [Sweep47] save_v20_anchor False 반환 시 명시적 실패 처리
                logging.warning(" [DNA Sync Error] save_v20_anchor returned False — DB 저장 실패")
                return False

        except Exception as e:
            logging.warning(f" [DNA Sync Error] 강제 주입 실패: {e}")
            return False
        # 📂 modules/core/project_manager.py 내부에 추가

    def get_blueprint(self, ep_num):
        """DB에서 해당 회차의 설계도를 가져옴"""
        return self.db.get_blueprint(ep_num)

    def sync_existing_manuscripts(self, memory) -> bool:
        """
        [Phase 0] 기존 원고를 AI 요약 없이 DB에 직접 박제
        """
        draft_files = sorted(list(self.paths.drafts.glob("*.txt")))

        for f_path in draft_files:
            # [V70] ep_NNNN.txt + 레거시 NNNN.txt 양쪽 호환
            _m = re.match(r"(?:ep_)?(\d{1,5})\.txt", f_path.name)
            if not _m:
                continue
            ep_num = int(_m.group(1))

            # 중복 체크 (이미 DB에 있으면 패스)
            if self.db.get_sync_status(ep_num) == 1:
                continue

            content = f_path.read_text(encoding="utf-8")
            # [V44] 빈 content 안전 처리
            if not content or not content.strip():
                logging.warning(f" 제 {ep_num}화 파일이 비어있음. 건너뜀.")
                continue
            _first_line = content.split("\n")[0].strip() if content else ""
            title = _first_line[:50] if _first_line else f"제{ep_num}화"

            # 1. SQLite 원고 테이블에 직접 저장
            self.save_manuscript_to_db(ep_num, title, content)

            # 2. Vector DB 기억 주입 (AI 요약 대신 원고 앞부분 사용해서 토큰 절약)
            summary = content[:1000].replace("\n", " ") + "..."
            # [V63.3] Python regex로 핵심 이벤트 추출 (LLM 비용 0)
            _bulk_events = set()
            _bulk_entities = set()
            if re.search(r"사망|죽였|처단|숨을\s*거두", content):
                _bulk_events.add("death")
            if re.search(r"습득|비급|전수|깨달", content):
                _bulk_events.add("skill")
            if re.search(r"획득|발견|손에\s*넣", content):
                _bulk_events.add("item")
            if re.search(r"배신|동맹|화해|적대", content):
                _bulk_events.add("relationship")
            # NPC 이름 패턴 (한글 2-4자 + "은/는/이/가/을/를")
            for _m in re.finditer(r"([가-힣]{2,4})(?:은|는|이|가|을|를)\s", content[:8000]):  # utf8-hygiene: allow-line regex pattern
                _bulk_entities.add(_m.group(1))
            memory.memorize_v20_episode(
                ep_num,
                content,
                summary,
                causal_links=[],
                event_types=list(_bulk_events) if _bulk_events else None,
                entity_names=list(_bulk_entities)[:30] if _bulk_entities else None,
            )

            # 3. 동기화 상태 갱신
            self.db.update_sync_status(ep_num, 1)
            logging.info(f" 제 {ep_num}화 역사 박제 완료.")

        # [V60.60 Fix] 반환값 추가 - 동기화 성공 표시
        return True

    # modules/core/project_manager.py (ProjectContext 클래스 내부)

    # --- [V35.5 Pro Candidate: 자율 수술실 로직] ---

    def auto_backtrack_v35(self, error_report, memory, *, world_state=None, fact_ledger=None):
        """
        [V35.5] 논리 모순이 발생한 '인과의 기점'을 찾아 자동 되감기(Rewind) 수행
        - Analyst의 진단 보고서를 바탕으로 물리적 DB와 파일 소거 실행

        Args:
            error_report: Analyst 진단 보고서
            memory: VecMemory 인스턴스 (벡터 기억 소거용)
            world_state: WorldStateManager 인스턴스 (선택, 있으면 롤백)
            fact_ledger: FactLedger 인스턴스 (선택, 있으면 롤백)
        """
        try:
            match = re.search(r"(\d+)\s*화", error_report or "")
            origin_ep = int(match.group(1)) if match else max(1, self.get_latest_episode_number() - 1)

            current_ep = self.get_latest_episode_number() - 1
            # [Sweep47] 빈 프로젝트에서 전체 삭제 방지
            if current_ep <= 0:
                logging.warning("[Backtrack] 저장된 에피소드 없음 — 되감기 건너뜀")
                return None
            target_ep = max(origin_ep, current_ep - 3)

            # [D-2] 롤백 영향 범위 미리보기
            impact = self.db.get_rollback_impact(target_ep)
            total = sum(impact.values())
            logging.info(f" [V35 Backtrack] 제 {target_ep}화로 되감기 (삭제 대상: {total}건)")
            for tbl, cnt in impact.items():
                if cnt > 0:
                    logging.info(f" - {tbl}: {cnt}건")

            self.reset_project(target_ep)

            if memory and hasattr(memory, "delete_episodes_from"):
                try:
                    deleted = memory.delete_episodes_from(target_ep)
                    logging.info(f" [Memory] 제 {target_ep}화 이후 벡터 기억 {deleted}건 소거")
                except Exception as _e:
                    logging.warning(f" [Backtrack] Memory rollback 실패 (DB는 완료): {_e}")

            if world_state and hasattr(world_state, "rollback_to"):
                try:
                    world_state.rollback_to(target_ep)
                    logging.info(" [WorldState] 세계 상태 초기화 완료")
                except Exception as _e:
                    logging.warning(f" [Backtrack] WorldState rollback 실패 (DB는 완료): {_e}")

            if fact_ledger and hasattr(fact_ledger, "rollback_to"):
                try:
                    fact_ledger.rollback_to(target_ep)
                    logging.info(" [FactLedger] 팩트 원장 초기화 완료")
                except Exception as _e:
                    logging.warning(f" [Backtrack] FactLedger rollback 실패 (DB는 완료): {_e}")

            return target_ep
        except Exception as e:
            logging.warning(f" [Backtrack Error] 자동 되감기 실패: {e}")
            return None
