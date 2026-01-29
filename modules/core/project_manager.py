import json
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from .db_manager import DBManager, DBError
import re
from typing import Any, Optional


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
    
    def __init__(self, project_name: str, root_dir: str = "projects"):
        load_dotenv(override=True)
        
        self.name = project_name
        self.base_path = Path(root_dir) / self.name
        self.db_path = self.base_path / "project_data.db" 

        self.selected_tone = {"name": "Sovereign Standard", "writer": "DB Mode"}
        self.author_directives = ""
        
        self.paths = ProjectPaths(
            root=self.base_path, config=self.base_path / "config",
            drafts=self.base_path / "drafts", memory=self.base_path / "chroma_db",
            db_file=self.db_path
        )
        self._initialize_structure()

        # 1. DB 엔진 기동
        self.db = DBManager(self.paths.db_file)
        print(f"      🗄️ [Sovereign DB] SQLite S-Grade 엔진 가동: {self.db_path.name}")

        self.master_bible = {}
        self.volumes = []
        self.arcs = []
        self.karma_status = {}
        
        self._load_from_db()
        self._load_directives()

    def _initialize_structure(self):
        for path in [self.paths.root, self.paths.config, self.paths.drafts, self.paths.memory]:
            path.mkdir(parents=True, exist_ok=True)

        # [V40.1] plans 폴더 구조 생성 (arcs, blueprints txt 저장용)
        self.paths.plans = self.paths.root / "plans"
        self.paths.plans_arcs = self.paths.plans / "arcs"
        self.paths.plans_blueprints = self.paths.plans / "blueprints"
        for plan_path in [self.paths.plans, self.paths.plans_arcs, self.paths.plans_blueprints]:
            plan_path.mkdir(parents=True, exist_ok=True)

        # 2. [V27.6 AUTO-INIT] 스타일 시드(Cash) 폴더 및 파일 자동 생성
        cash_dir = self.paths.config / "cash"
        cash_dir.mkdir(parents=True, exist_ok=True)

        seed_file = cash_dir / "style_seeds_final.txt"
        if not seed_file.exists():
            default_seed = (
                "[참고내용 없음]"
                            )
            try:
                with open(seed_file, "w", encoding="utf-8") as f:
                    f.write(default_seed)
                print(f"      ✨ [System] 스타일 시드 파일이 생성되었습니다: {seed_file.name}")
            except Exception as e:
                print(f"      ⚠️ [System] 스타일 시드 생성 실패: {e}")


    def _load_directives(self):
        d_path = self.paths.config / "author_directives.txt"
        if d_path.exists():
            self.author_directives = d_path.read_text(encoding="utf-8")
        else:
            d_path.write_text("# 절대 지시 사항을 입력하세요.\n", encoding="utf-8")

    def _load_from_db(self):
        """[V44] 기동 시 DB의 앵커 데이터를 메모리로 수혈 (타입 검증 강화)"""
        # [V44] anchors 로드 및 타입 검증
        try:
            anchors = self.db.load_all_anchors()
        except (DBError, Exception) as e:
            print(f"      🚨 [ProjectContext] DB 앵커 로드 실패: {e}")
            print(f"         → 빈 상태로 초기화합니다")
            anchors = {}

        # [V44] anchors 타입 검증
        if not isinstance(anchors, dict):
            print(f"      ⚠️ [ProjectContext] anchors가 dict가 아님: {type(anchors)}")
            anchors = {}

        # [V44] 각 앵커 데이터 안전 추출
        self.master_bible = anchors.get("bible") if isinstance(anchors.get("bible"), dict) else {}
        self.volumes = anchors.get("volumes") if isinstance(anchors.get("volumes"), list) else []
        self.arcs = anchors.get("arcs") if isinstance(anchors.get("arcs"), list) else []

        # [V44] karma 로드 (별도 예외 처리)
        try:
            self.karma_status = self.db.get_all_karma()
            if not isinstance(self.karma_status, dict):
                self.karma_status = {}
        except Exception as e:
            print(f"      ⚠️ [ProjectContext] karma 로드 실패: {e}")
            self.karma_status = {}

        # [V44] safe_nested_get으로 중첩 접근
        success_device = safe_nested_get(
            self.master_bible,
            'MasterBible', 'CommercialCode', 'SuccessDevice',
            default=self.selected_tone.get("writer", "DB Mode")
        )
        # 추가 fallback: MasterBible 래퍼 없이 직접 접근하는 경우
        if success_device == self.selected_tone.get("writer", "DB Mode"):
            success_device = safe_nested_get(
                self.master_bible,
                'CommercialCode', 'SuccessDevice',
                default=self.selected_tone.get("writer", "DB Mode")
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
            bible_root = data.get('MasterBible', data)
            
            # [A] 복선(Seeds) 테이블 동기화
            seeds = bible_root.get('Seeds', [])
            if seeds: self.db.sync_seeds(seeds)
            
            # [B] 로어(Encyclopedia) 일괄 동기화 (Type Safety Logic)
            lore_batch = []
            assets = bible_root.get('AssetLibrary', {})
            
            for cat, items in assets.items():
                if isinstance(items, list): # KeyNPCs, KeyItems 등
                    for item in items:
                        # [V44] item이 dict인 경우에만 .get() 사용
                        if isinstance(item, dict):
                            name = item.get('Item') or item.get('name')
                            desc = item.get('Description') or item.get('desc')
                            if name and desc:
                                if isinstance(desc, (list, dict)): desc = json.dumps(desc, ensure_ascii=False)
                                lore_batch.append((cat, name, desc))
                        elif isinstance(item, str) and item.strip():
                            # 문자열 아이템인 경우 이름과 설명을 동일하게 처리
                            lore_batch.append((cat, item, item))
                            
                elif isinstance(items, dict): # SpeechStyle 등
                    for name, desc in items.items():
                        if isinstance(desc, (list, dict)): desc = json.dumps(desc, ensure_ascii=False)
                        lore_batch.append((cat, name, desc))
                
                # 🚨 [Final Patch] Persona 같은 단일 문자열 데이터까지 완벽 포획
                elif isinstance(items, str): 
                    lore_batch.append((cat, cat, items))

            if lore_batch: 
                self.db.update_lore_items_batch(lore_batch)
            
            # [C] Martial Tracker(HUD) 강제 동기화
            protagonist = bible_root.get('MartialHUD', {}).get('Protagonist', {})
            actual_data = protagonist.get('actual_truth', {})
            if actual_data:
                self.record_martial_stats(0, actual_data)
                print(f"      🛡️ [Sync] 성경 저장과 동시에 HUD 테이블 동기화 완료.")

        elif stage == "volumes": self.volumes = data
        elif stage == "arcs":
            self.arcs = data
            # [V40.1] Arc txt 파일 저장
            self._save_arcs_to_txt(data)
        elif stage == "karma": self.karma_status = data

        # 3. Anchor(JSON) 최종 박제
        return self.db.save_anchor(stage, data)

    def save_episode_blueprint(self, ep_num, data):
        """Stage 3 설계도 DB 박제"""
        self.db.save_blueprint(ep_num, data)
        # [V40.1] Blueprint txt 파일 저장
        self._save_blueprint_to_txt(ep_num, data)

    def _save_arcs_to_txt(self, arcs_data):
        """[V40.1] Arc 데이터를 txt 파일로 저장"""
        if not arcs_data or not isinstance(arcs_data, list):
            return

        try:
            # [V40.1 Safety] 폴더가 없으면 생성
            if not hasattr(self.paths, 'plans_arcs'):
                self.paths.plans_arcs = self.paths.root / "plans" / "arcs"
            self.paths.plans_arcs.mkdir(parents=True, exist_ok=True)
            for arc in arcs_data:
                if not isinstance(arc, dict):
                    continue

                arc_no = arc.get('arc_no', arc.get('global_arc_no', 0))
                if not arc_no:
                    continue

                # 파일명: arc_001.txt
                filename = f"arc_{arc_no:03d}.txt"
                filepath = self.paths.plans_arcs / filename

                # Arc 내용 포맷팅
                lines = [
                    f"{'='*60}",
                    f"ARC {arc_no}",
                    f"{'='*60}",
                    f"",
                    f"[기본 정보]",
                    f"- 볼륨: {arc.get('volume_no', 'N/A')}",
                    f"- 에피소드 범위: {arc.get('ep_start', 'N/A')} ~ {arc.get('ep_end', 'N/A')}",
                    f"- 에피소드 수: {arc.get('ep_count', 'N/A')}",
                    f"",
                    f"[전술 문서 (Tactical Doc)]",
                    f"{'-'*40}",
                    f"{arc.get('tactical_doc', '내용 없음')}",
                    f"",
                    f"[비트 시퀀스 (Beat Sequence)]",
                    f"{'-'*40}",
                ]

                beat_seq = arc.get('beat_sequence', [])
                if isinstance(beat_seq, list):
                    for i, beat in enumerate(beat_seq, 1):
                        if isinstance(beat, dict):
                            lines.append(f"Beat {i}: {beat.get('beat', beat.get('description', str(beat)))}")
                        else:
                            lines.append(f"Beat {i}: {beat}")
                elif isinstance(beat_seq, str):
                    lines.append(beat_seq)

                # 복선 정보
                seeds = arc.get('seed_injection', arc.get('seeds', []))
                if seeds:
                    lines.append(f"")
                    lines.append(f"[복선 (Seeds)]")
                    lines.append(f"{'-'*40}")
                    if isinstance(seeds, list):
                        for seed in seeds:
                            if isinstance(seed, dict):
                                lines.append(f"- {seed.get('id', seed.get('seed_id', 'N/A'))}: {seed.get('hint', seed.get('description', ''))}")
                            else:
                                lines.append(f"- {seed}")

                filepath.write_text('\n'.join(lines), encoding='utf-8')

            print(f"      📁 [Plans] Arc txt 파일 {len(arcs_data)}개 저장 완료")
        except Exception as e:
            print(f"      ⚠️ [Plans] Arc txt 저장 실패: {e}")

    def _save_blueprint_to_txt(self, ep_num, data):
        """[V40.1] Blueprint 데이터를 txt 파일로 저장"""
        if not data or not isinstance(data, dict):
            return

        try:
            # [V40.1 Safety] 폴더가 없으면 생성
            if not hasattr(self.paths, 'plans_blueprints'):
                self.paths.plans_blueprints = self.paths.root / "plans" / "blueprints"
            self.paths.plans_blueprints.mkdir(parents=True, exist_ok=True)

            # 파일명: blueprint_0001.txt
            filename = f"blueprint_{ep_num:04d}.txt"
            filepath = self.paths.plans_blueprints / filename

            lines = [
                f"{'='*60}",
                f"BLUEPRINT - Episode {ep_num}",
                f"{'='*60}",
                f"",
                f"[통합 시나리오 (Integrated Scenario)]",
                f"{'-'*40}",
                f"{data.get('integrated_scenario', '내용 없음')}",
                f"",
                f"[씬 분해 (Scene Breakdown)]",
                f"{'-'*40}",
            ]

            scene_breakdown = data.get('scene_breakdown', {})
            if isinstance(scene_breakdown, dict):
                for scene_key, scene_data in scene_breakdown.items():
                    lines.append(f"")
                    lines.append(f"## {scene_key}")
                    if isinstance(scene_data, dict):
                        for k, v in scene_data.items():
                            lines.append(f"  - {k}: {v}")
                    else:
                        lines.append(f"  {scene_data}")
            elif isinstance(scene_breakdown, str):
                lines.append(scene_breakdown)

            # 핵심 갈등/긴장
            if 'core_tension' in data:
                lines.append(f"")
                lines.append(f"[핵심 긴장 (Core Tension)]")
                lines.append(f"{'-'*40}")
                lines.append(f"{data['core_tension']}")

            # 예상 결말
            if 'expected_ending' in data:
                lines.append(f"")
                lines.append(f"[예상 결말 (Expected Ending)]")
                lines.append(f"{'-'*40}")
                lines.append(f"{data['expected_ending']}")

            filepath.write_text('\n'.join(lines), encoding='utf-8')
            print(f"      📁 [Plans] Blueprint {ep_num}화 txt 저장 완료")
        except Exception as e:
            print(f"      ⚠️ [Plans] Blueprint txt 저장 실패: {e}")

    def _normalize_seed_id(self, raw_id):
        """[V26 Integrity Filter] AI 오타 교정 및 성경 ID 매칭"""
        # 1. 성경 내 실제 ID 목록 확보
        bible_seeds = self.master_bible.get('MasterBible', {}).get('Seeds', [])
        valid_ids = {s.get('id'): s.get('id') for s in bible_seeds}
        
        # 2. 완전 일치 여부 확인
        if raw_id in valid_ids: return raw_id
        
        # 3. 퍼지 매칭 (특수문자 제거 후 대조)
        clean_raw = re.sub(r'[^a-zA-Z0-9]', '', raw_id).upper()
        for vid in valid_ids:
            clean_vid = re.sub(r'[^a-zA-Z0-9]', '', vid).upper()
            if clean_raw == clean_vid:
                print(f"      🔧 [Normalized] Seed ID 교정: {raw_id} -> {vid}")
                return vid
                
        return raw_id # 매칭 실패 시 원본 유지(데이터 보존)


    def sync_and_cleanup_seeds(self):
        """[V27.5 S-Grade] 성경(Bible) 기반 복선 데이터 동기화 및 유령 ID 정화"""
        bible_root = self.master_bible.get('MasterBible', self.master_bible)
        bible_seeds = bible_root.get('Seeds', [])
        
        if not bible_seeds:
            return

        # 1. 성경에 등록된 유효 ID 목록 확보
        valid_ids = [s.get('id') for s in bible_seeds if s.get('id')]
        
        # 2. DB에는 존재하지만 성경에는 없는 '유령 복선' 삭제 (Orphaned Data Cleanup)
        if valid_ids:
            placeholders = ', '.join(['?'] * len(valid_ids))
            query = f"DELETE FROM seeds WHERE seed_id NOT IN ({placeholders})"
            self.db.cursor.execute(query, valid_ids)
            
        # 3. 성경의 최신 내용을 DB에 강제 동기화 (Upsert)
        self.db.sync_seeds(bible_seeds)
        self.db.conn.commit()
        print(f"      🧹 [Cleanup] 복선 데이터 정화 완료 (유효 ID: {len(valid_ids)}건)")

    def commit_full_episode_data(self, ep_num, manuscript_data, martial_data, state_data, causal_links, karma_data, lore_data, recovered_seeds, memory_engine):
        """
        [V35 Alpha] 트랜잭션 원자성 강화 + NPC HUD 실시간 동기화 통합 버전
        """
        # 1. 먼저 '미동기화' 상태로 마킹 (Safety First)
        self.db.update_sync_status(ep_num, 0) 

        try:
            # --- [Part 1: 데이터 및 복선 정규화] ---
            normalized_seeds = []
            if recovered_seeds and isinstance(recovered_seeds, list):
                for rec in recovered_seeds:
                    if isinstance(rec, dict):
                        raw_id = rec.get('seed_id') or rec.get('id')
                        rec['seed_id'] = self._normalize_seed_id(raw_id) if raw_id else 'UNKNOWN'
                        normalized_seeds.append(rec)
            recovered_seeds = normalized_seeds

            # --- [Part 2: 🚨 NPC HUD 변화 추적 및 성경 반영] ---
            if lore_data and isinstance(lore_data, dict) and "Key_NPCs" in lore_data:
                bible_root = self.master_bible.get('MasterBible', self.master_bible)
                bible_npcs = bible_root.get('AssetLibrary', {}).get('KeyNPCs', [])

                for new_npc in lore_data["Key_NPCs"]:
                    # [V45 Fix] new_npc 타입 검증
                    if not isinstance(new_npc, dict):
                        continue
                    npc_name = new_npc.get('name') or new_npc.get('Name')
                    for target in bible_npcs:
                        if target.get('name') == npc_name:
                            if 'NPC_Martial_HUD' in new_npc:
                                new_hud = new_npc['NPC_Martial_HUD']
                                # [V45 Fix] new_hud가 dict가 아니면 건너뜀 (AttributeError 방지)
                                if not isinstance(new_hud, dict):
                                    continue
                                old_hud = target.get('NPC_Martial_HUD', {})
                                # [V45 Fix] old_hud도 dict 보장
                                if not isinstance(old_hud, dict):
                                    old_hud = {}

                                # 변화량 추적 및 출력
                                changes = []
                                for key in ['achievement_rate', 'current_status', 'realm']:
                                    if new_hud.get(key) and new_hud.get(key) != old_hud.get(key):
                                        changes.append(f"{key}: {old_hud.get(key, 'N/A')} -> {new_hud[key]}")

                                # [V45] NPC equipment 변화 추적
                                old_equip = old_hud.get('equipment', [])
                                new_equip = new_hud.get('equipment', [])
                                if new_equip and new_equip != old_equip:
                                    # 리스트 비교를 위한 정규화
                                    old_set = set(old_equip) if isinstance(old_equip, list) else set()
                                    new_set = set(new_equip) if isinstance(new_equip, list) else set()
                                    added = new_set - old_set
                                    removed = old_set - new_set
                                    if added:
                                        changes.append(f"equipment 획득: {list(added)}")
                                    if removed:
                                        changes.append(f"equipment 상실: {list(removed)}")

                                if changes:
                                    print(f"      🕸️ [NPC Trace] {npc_name} 변화 감지: {', '.join(changes)}")

                                # 데이터 병합 (성경 메모리 동기화)
                                target.setdefault('NPC_Martial_HUD', {}).update(new_hud)
                            break

            # --- [Part 3: 원자적 저장 - Bible 먼저, DB 나중] ---
            # [V44 Fix] Bible을 먼저 저장하여 crash 시 데이터 복구 가능하게 함
            # 순서: Bible 저장 → DB commit → Vector sync
            # 이유: DB commit 실패 시 Bible은 최신 상태 유지, 다음 실행에서 복구 가능

            # 3-1. Bible 선행 저장 (NPC HUD 변화 포함)
            try:
                self.save_v20_anchor('bible', self.master_bible)
                self.sync_and_cleanup_seeds()
            except Exception as bible_err:
                print(f"      🚨 [Critical] Bible 선행 저장 실패: {bible_err}")
                raise Exception(f"Bible 저장 실패로 에피소드 커밋 중단: {bible_err}")

            # 3-2. SQLite 핵심 트랜잭션 (원고, HUD, 로그, 카르마, 로어)
            db_success = self.db.commit_episode_factory(
                ep_num, manuscript_data, martial_data, state_data,
                causal_links, karma_data, lore_data, recovered_seeds
            )

            if not db_success:
                raise Exception("SQLite Episode Factory 저장 실패")

            # --- [Part 4: 벡터 동기화 (ChromaDB)] ---
            try:
                # 벡터 기억 주입
                summary = state_data.get('context_audit', {}).get('summary', "요약 없음")
                content_text = manuscript_data['content'] if isinstance(manuscript_data, dict) else str(manuscript_data)
                
                vector_success = memory_engine.memorize_v20_episode(ep_num, content_text, summary, causal_links)
                
                if vector_success:
                    # 모든 공정 성공 시에만 최종 동기화 완료 마킹
                    self.db.update_sync_status(ep_num, 1)
                else:
                    print(f"      ⚠️ [Sync Warning] 제 {ep_num}화 벡터 주입 지연 (플래그 0 유지)")
                
                return True

            except Exception as sub_e:
                # [V44 Fix] 부분 실패 시 경고 강화 및 sync 상태 업데이트
                print(f"      🚨 [Partial Failure] 벡터 동기화 중 오류: {sub_e}")
                print(f"      ⚠️ [WARNING] 에피소드 {ep_num}: DB/Bible 저장됨, Vector 동기화 불완전")
                # sync_status를 2로 설정하여 "부분 성공" 상태 표시
                try:
                    self.db.update_sync_status(ep_num, 2)  # 2 = partial sync
                except Exception:
                    pass
                return True  # DB는 성공했으므로 진행 (단, 경고 로깅됨)

        except Exception as e:
            print(f"      🛑 [Critical Error] 제 {ep_num}화 원자적 저장 실패: {e}")
            self.db.update_sync_status(ep_num, 0)
            return False

    # --- [Getter: 하이브리드 맥락 인출] ---
    @property
    def latest_state(self):
        state = self.db.get_latest_state()
        if not state:
            bible_root = self.master_bible.get('MasterBible', self.master_bible)
            return bible_root.get('MartialHUD', bible_root.get('martial_hud', {}))
        return state

    def get_sequential_context(self, current_ep):
        """직전 원고 3화와 직전 설계도를 DB에서 인출 (에이전트 지능용)"""
        manuscripts = self.db.get_context_manuscripts(current_ep, limit=3) #
        prev_blueprint = self.db.get_previous_blueprint(current_ep) #
        return manuscripts, prev_blueprint

    def get_causal_history_summary(self):
        """최근 5화의 인과 요약 체인 인출"""
        return self.db.get_causal_summary_chain(limit=5) #

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
                if f.name[:4].isdigit():
                    file_ep = max(file_ep, int(f.name[:4]))

            # 둘 중 큰 값 반환 (안전장치)
            return max(db_ep, file_ep)
        except Exception:
            # 파일 확인 실패 시 DB 값 사용
            return db_ep

    # --- [Bridge 보완: 에이전트용 로어 인출] ---
    def get_lore_data(self, item_name):
        """[Main 연결] 에이전트가 특정 인물/아이템 설정을 DB에서 즉시 인출"""
        return self.db.get_lore_item(item_name)

    def get_all_lore_by_category(self, category):
        """특정 카테고리(NPC/ITEM 등) 전체 정보를 리스트로 인출"""
        return self.db.get_lore_list_by_category(category)

    # --- [Bridge 보완: 15대 지표 데이터 가드] ---
    def record_martial_stats(self, ep_num, stats_data):
        """에이전트의 데이터 키 누락이나 오타로부터 DB를 보호하며 기록"""
        # DB 테이블 컬럼과 일치하는 15대 지표 화이트리스트
        valid_keys = [
            'alias', 'rank', 'realm', 'internal_energy', 'mental_method',
            'reputation', 'public_image', 'equipment', 'wealth', 'token',
            'misunderstanding', 'obsession', 'current_objective', 'qi_nature', 'causal_injuries'
        ]
        # 규격에 맞는 데이터만 필터링 (누락 시 None 처리하여 DB 에러 방지)
        sanitized_data = {k: stats_data.get(k) for k in valid_keys}
        self.db.update_martial_tracker(ep_num, sanitized_data)
        print(f"      📊 [DB] 제 {ep_num}화 15대 지표 트래커 박제 완료.")

    # modules/core/project_manager.py 파일 내부 ProjectContext 클래스에 추가

    def save_manuscript_to_db(self, ep_num, title, content):
        """[Phase 0 전용] 물리 원고 데이터를 DB로 직접 미러링하여 박제"""
        # DBManager의 save_manuscript 기능을 호출함
        self.db.save_manuscript(ep_num, title, content)
        print(f"      📝 [Mirroring] 제 {ep_num}화 원고 DB 동기화 완료.")
    # --- [Utility: 리셋 및 동기화] ---
    def reset_project(self, target_ep):
        """DB와 물리 파일을 동시에 정화"""
        self.db.reset_after(target_ep) #
        
        if self.paths.drafts.exists():
            for f in self.paths.drafts.glob("*.txt"):
                if f.name[:4].isdigit() and int(f.name[:4]) >= target_ep:
                    f.unlink()
        print(f"🔥 [Reset] 제 {target_ep}화 이후의 모든 타임라인이 소거되었습니다.")

    def force_sync_v25_dna(self, bible_file_name, treatment_file_name):
        """
        [Phase 0] AI의 출력 제한을 우회하여 50개 전술 블록을 Bible에 강제 주입 및 DB 박제
        """
        print(f"🧬 [DNA Injection] '{treatment_file_name}' 데이터를 Bible에 강제 이식합니다...")

        # 1. Bible(성경) 데이터 로드
        bible_path = self.paths.root.parent.parent / "bible" / bible_file_name
        treatment_path = self.paths.root.parent.parent / "treatments" / treatment_file_name

        try:
            with open(bible_path, 'r', encoding='utf-8') as f:
                bible_data = json.load(f)
            
            with open(treatment_path, 'r', encoding='utf-8') as f:
                treatment_data = json.load(f)

            # 2. MasterBible 루트 확보 (포장지가 있든 없든 대응)
            master_bible = bible_data.get("MasterBible", bible_data)
            
            # 3. 50개 트리트먼트 블록을 plot_roadmap 규격으로 변환하여 주입
            # AI가 짤라먹지 못하도록 파이썬 리스트 연산으로 직접 합침
            refined_roadmap = []
            for i, block in enumerate(treatment_data):
                # 원본 JSON의 구조에 맞춰 block_no와 내용을 매핑
                refined_roadmap.append({
                    "block_no": i + 1,
                    "logic": {
                        "title": block.get("title", f"제 {i+1} 단계"),
                        "objective": block.get("content", {}).get("solution", "목표 분석 필요")
                    },
                    "raw_data": block # 원본 데이터 전체를 보존 (나중에 AI가 참고하도록)
                })

            # 4. 성경 객체에 최종 로드맵 결합
            master_bible["plot_roadmap"] = refined_roadmap
            self.master_bible = {"MasterBible": master_bible}

            # 5. [핵심] SQLite DB에 'bible' 앵커로 50개 전체 강제 박제
            # 여기서 DBManager의 save_anchor를 호출함
            success = self.save_v20_anchor('bible', self.master_bible)

            if success:
                print(f"✅ [S-Grade Success] 50개 블록이 포함된 '완전한 성경'이 DB에 안착되었습니다.")
                print(f"📊 로드맵 크기: {len(self.master_bible['MasterBible']['plot_roadmap'])} blocks")
                return True
        
        except Exception as e:
            print(f"🚨 [DNA Sync Error] 강제 주입 실패: {e}")
            return False
        # 📂 modules/core/project_manager.py 내부에 추가

    def get_blueprint(self, ep_num):
        """DB에서 해당 회차의 설계도를 가져옴"""
        return self.db.get_blueprint(ep_num)
    
    def sync_existing_manuscripts(self, memory_engine):
        """
        [Phase 0] 기존 원고를 AI 요약 없이 DB에 직접 박제
        """
        draft_files = sorted(list(self.paths.drafts.glob("*.txt")))
        
        for f_path in draft_files:
            if not f_path.name[:4].isdigit(): continue
            ep_num = int(f_path.name[:4])
            
            # 중복 체크 (이미 DB에 있으면 패스)
            if self.db.get_sync_status(ep_num) == 1: continue

            content = f_path.read_text(encoding='utf-8')
            # [V44] 빈 content 안전 처리
            if not content or not content.strip():
                print(f"   ⚠️ 제 {ep_num}화 파일이 비어있음. 건너뜀.")
                continue
            title = content.split('\n')[0].strip()[:50] if content else f"제{ep_num}화"

            # 1. SQLite 원고 테이블에 직접 저장
            self.save_manuscript_to_db(ep_num, title, content)
            
            # 2. Vector DB 기억 주입 (AI 요약 대신 원고 앞부분 사용해서 토큰 절약)
            summary = content[:300].replace('\n', ' ') + "..."
            memory_engine.memorize_v20_episode(ep_num, content, summary, causal_links=[])
            
            # 3. 동기화 상태 갱신
            self.db.update_sync_status(ep_num, 1)
            print(f"   ⚓ 제 {ep_num}화 역사 박제 완료.")        


    # modules/core/project_manager.py (ProjectContext 클래스 내부)

    # --- [V35.5 Pro Candidate: 자율 수술실 로직] ---

    def auto_backtrack_v35(self, error_report, memory_engine):
        """
        [V35.5] 논리 모순이 발생한 '인과의 기점'을 찾아 자동 되감기(Rewind) 수행
        - Analyst의 진단 보고서를 바탕으로 물리적 DB와 파일 소거 실행
        """
        # 1. 에러 보고서에서 Origin EP(모순 시작점) 추출 (Analyst에게 판단 위임 가능)
        # 여기서는 보고서에 포함된 숫자나 텍스트를 분석하여 타겟 화수 결정
        try:
            # 에러 메시지 내의 화수 패턴 검색 (예: "제 12화부터 설정 오류")
            match = re.search(r'(\d+)\s*화', error_report)
            origin_ep = int(match.group(1)) if match else self.get_latest_episode_number()
            
            # 너무 과거로 가는 것 방지 가드 (최대 3화 전까지만 자동 허용)
            current_ep = self.get_latest_episode_number()
            target_ep = max(origin_ep, current_ep - 3)
            
            print(f"      🚑 [V35 Backtrack] 제 {target_ep}화로 인과율을 강제 되감기합니다.")
            
            # 2. 기존 reset_project 함수명 존중하여 호출 (DB 및 물리 파일 삭제)
            # self.reset_project는 이미 구현되어 있음
            self.reset_project(target_ep)
            
            # 3. 벡터 DB(ChromaDB) 기억 소거
            if memory_engine and memory_engine.collection:
                memory_engine.collection.delete(where={"episode": {"$gte": target_ep}})
                print(f"      🌌 [Memory] 제 {target_ep}화 이후의 벡터 기억을 소거했습니다.")
                
            return target_ep
        except Exception as e:
            print(f"      🚨 [Backtrack Error] 자동 되감기 실패: {e}")
            return None

    def record_surgery_result(self, ep_num, category, failed_logic, result):
        """수술 결과를 DB에 저장하여 향후 '실패 사례' 지능으로 활용"""
        self.db.save_surgery_log(ep_num, category, failed_logic, result)

    def get_surgery_intelligence(self, limit=3):
        """최근 수술 기록을 가져와 프롬프트에 주입할 '반성문' 형태로 반환"""
        cur = self.db.cursor.execute(
            "SELECT ep_num, error_category, surgery_result FROM surgery_logs ORDER BY id DESC LIMIT ?", 
            (limit,)
        )
        logs = cur.fetchall()
        if not logs: return ""
        
        intel = "\n[⚠️ 최근 발생한 설정 오류 및 교정 사례]\n"
        for log in logs:
            intel += f"- 제 {log['ep_num']}화 ({log['error_category']}): {log['surgery_result']}\n"
        return intel            