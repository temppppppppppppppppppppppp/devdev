import sqlite3
import json
from pathlib import Path
import time
from .constants import MARTIAL_METRICS # 👈 상수 임포트
from contextlib import contextmanager

class DBManager:
    """[V20 Sovereign DB Engine] S등급 무결성: 트랜잭션 보호 및 로어 테이블화 완비"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._boot_db()

    def _boot_db(self):
        """DB 연결 및 10대 핵심 테이블 초기화"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()


        # 1. 앵커 데이터 (Bible, Volumes, Arcs)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                ep_num INTEGER PRIMARY KEY,
                vector_synced INTEGER DEFAULT 0, -- 0: 미동기화, 1: 완료
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS surgery_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_num INTEGER,
                error_category TEXT,
                failed_logic TEXT,
                surgery_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

        # anchors 테이블: 'key'가 유니크해야 REPLACE가 작동함
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS anchors (
                key TEXT PRIMARY KEY,
                data TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

        # 2. 설계도 (Blueprints)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                ep_num INTEGER PRIMARY KEY,
                data TEXT
            )
        ''')

        # 3. 상태 로그 (Logs - summary 컬럼 포함)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS state_logs (
                ep_num INTEGER PRIMARY KEY,
                data TEXT,
                summary TEXT
            )
        ''')
        # (기존 테이블 마이그레이션용: 컬럼 없으면 추가)
        try: self.cursor.execute("ALTER TABLE state_logs ADD COLUMN summary TEXT")
        except: pass

        # 4. 인과 그래프 (Causal Graph)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS causal_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_num INTEGER,
                data TEXT
            )
        ''')
        
        # 5. NPC 관계 (Karma)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS karma_status (
                npc_name TEXT PRIMARY KEY,
                misunderstanding INTEGER DEFAULT 0,
                obsession INTEGER DEFAULT 0,
                last_updated_ep INTEGER
            )
        ''')

        # 6. 원고 본문 (Manuscripts)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manuscripts (
                ep_num INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ------------------------------------------------------------------
        # 🚨 [Patch 1.1] Martial Tracker 자동 스키마 마이그레이션 로직
        # ------------------------------------------------------------------
        # 1. 테이블 생성 (없을 경우)
        columns_def = ", ".join([f"{k} TEXT" for k in MARTIAL_METRICS])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS martial_tracker (ep_num INTEGER PRIMARY KEY, {columns_def})")
        
        # 2. 컬럼 동기화 검사 (코드에는 있는데 DB에 없는 컬럼 찾기)
        try:
            # 현재 DB의 컬럼 목록 조회
            self.cursor.execute("PRAGMA table_info(martial_tracker)")
            existing_columns = {row['name'] for row in self.cursor.fetchall()}
            
            # MARTIAL_METRICS 순회하며 누락된 컬럼 추가
            for metric in MARTIAL_METRICS:
                if metric not in existing_columns:
                    print(f"      🔧 [DB Migration] 새로운 지표 '{metric}' 발견. 테이블에 컬럼을 추가합니다.")
                    self.cursor.execute(f"ALTER TABLE martial_tracker ADD COLUMN {metric} TEXT")
            
            self.conn.commit()
            
        except Exception as e:
            print(f"      🚨 [DB Error] 마이그레이션 실패: {e}")
        # 8. 복선 전용 관리 (Seeds)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS seeds (
                seed_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                status TEXT DEFAULT 'active', -- active / archived
                planted_ep INTEGER,
                recovered_ep INTEGER
            )
        ''')

        # 9. [NEW] 로어 백과사전 (Encyclopedia)
        self.cursor.execute('''                
            CREATE TABLE IF NOT EXISTS encyclopedia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                item TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item)
            )
        ''')

        self.conn.commit()

    # --- [트랜잭션 제어] ---
    def begin(self): self.cursor.execute("BEGIN TRANSACTION")
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()

    # --- [Section 1: 원고 및 지표] ---
    def save_manuscript(self, ep_num, title, content):
        self.cursor.execute("INSERT OR REPLACE INTO manuscripts (ep_num, title, content) VALUES (?, ?, ?)", (ep_num, title, content))
        if not self.conn.in_transaction: self.conn.commit()

    def get_manuscript(self, ep_num):
        cur = self.cursor.execute("SELECT * FROM manuscripts WHERE ep_num = ?", (ep_num,))
        row = cur.fetchone()
        return dict(row) if row else None

# 📂 modules/core/db_manager.py 내부에 추가

    def get_blueprint(self, ep_num):
        """특정 회차의 설계도 JSON 인출"""
        cur = self.cursor.execute("SELECT data FROM blueprints WHERE ep_num = ?", (ep_num,))
        row = cur.fetchone()
        return json.loads(row['data']) if row else None
    
    
    def update_martial_tracker(self, ep_num, martial_data):
        """[V26.6 S-Grade] DB 스키마에 존재하는 컬럼만 선별하여 저장 (Mismatched Key Guard)"""
        # 1. 약속된 15대 지표(MARTIAL_METRICS)만 필터링 (스키마 가드)
        sanitized_data = {k: martial_data[k] for k in MARTIAL_METRICS if k in martial_data}
        
        if not sanitized_data:
            return

        # 2. 필터링된 데이터로 쿼리 생성 (동적 컬럼 매핑)
        columns = ', '.join(sanitized_data.keys())
        placeholders = ', '.join(['?'] * len(sanitized_data))
        query = f"INSERT OR REPLACE INTO martial_tracker (ep_num, {columns}) VALUES (?, {placeholders})"
        
        self.cursor.execute(query, [ep_num] + list(sanitized_data.values()))
        if not self.conn.in_transaction: 
            self.conn.commit()
    # --- [Section 2: 복선 및 로어] ---
# modules/core/db_manager.py
# [V35.5] 수술 기록 박제 메서드 추가
    def save_surgery_log(self, ep_num, category, failed_logic, result):
        self.cursor.execute('''
            INSERT INTO surgery_logs (ep_num, error_category, failed_logic, surgery_result)
            VALUES (?, ?, ?, ?)
        ''', (ep_num, category, failed_logic, result))
        self.conn.commit()



    def sync_seeds(self, seeds_list):
        """[V24 Precise Mode] 데이터 누락 시 기본값 할당으로 시스템 중단 방지"""
        for s in seeds_list:
            # 1. 필수 데이터 인출 (KeyError 방지를 위해 .get() 사용)
            seed_id = s.get('id') or s.get('seed_id', f"unknown_{int(time.time())}")
            category = s.get('category', '일반') # 카테고리 누락 시 '일반'으로 처리
            content = s.get('content') or s.get('description', '내용 없음')
            status = s.get('status', 'active')
            planted_ep = s.get('planted_at') or s.get('planted_ep', 0)

            # 2. DB 박제
            self.cursor.execute('''
                INSERT OR REPLACE INTO seeds (seed_id, category, content, status, planted_ep)
                VALUES (?, ?, ?, ?, ?)
            ''', (seed_id, category, content, status, planted_ep))
        
        if not self.conn.in_transaction: 
            self.conn.commit()
    def archive_seed(self, seed_id, ep_num):
        self.cursor.execute("UPDATE seeds SET status = 'archived', recovered_ep = ? WHERE seed_id = ?", (ep_num, seed_id))
        if not self.conn.in_transaction: self.conn.commit()

    def update_lore_item(self, category, item, description):
        """[PATCHED] 카테고리+이름 복합 키 기준 저장"""
        self.cursor.execute('''
            INSERT INTO encyclopedia (category, item, description)
            VALUES (?, ?, ?)
            ON CONFLICT(item) DO UPDATE SET
                category = excluded.category,
                description = excluded.description,
                updated_at = CURRENT_TIMESTAMP
        ''', (category, item, description))
        if not self.conn.in_transaction: self.conn.commit()

    def update_lore_items_batch(self, lore_items_list):
        """[PATCHED] 일괄 업데이트 트랜잭션"""
        if not lore_items_list: return
        nested = self.conn.in_transaction
        try:
            if not nested: self.begin()
            
            self.cursor.executemany('''
                INSERT INTO encyclopedia (category, item, description)
                VALUES (?, ?, ?)
                ON CONFLICT(item) DO UPDATE SET
                    category = excluded.category,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
            ''', lore_items_list)
            
            if not nested: self.commit()

        except Exception as e:
            # 내가 시작한 트랜잭션일 때만 롤백 (끼어든 거면 상위로 에러 전파)
            if not nested:
                self.rollback()
            print(f"🚨 [DB] 로어 일괄 저장 실패: {e}")
            # 중첩 상태였다면 상위 로직이 롤백하도록 에러를 다시 던지는 것이 안전함
            if nested:
                raise e

# --- [Section 2 보완: 로어 인출] ---
    def get_lore_item(self, item_name):
        """특정 인물/아이템의 설정을 테이블에서 즉시 조회"""
        cur = self.cursor.execute("SELECT * FROM encyclopedia WHERE item = ?", (item_name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_lore_list_by_category(self, category):
        """특정 카테고리(NPC, ITEM 등) 전체 리스트 인출"""
        cur = self.cursor.execute("SELECT * FROM encyclopedia WHERE category = ?", (category,))
        return [dict(row) for row in cur.fetchall()]



    def save_anchor(self, key, data):
        """S등급 데이터를 박제하고 타임스탬프를 강제 갱신함"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            # 쿼리문에 CURRENT_TIMESTAMP를 명시하여 REPLACE 시에도 시간이 갱신되게 함
            self.cursor.execute("""
                INSERT OR REPLACE INTO anchors (key, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json_data))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ [DB Error] Anchor 저장 실패: {e}")
            return False


    def load_anchor(self, key, default=None):
        cur = self.cursor.execute("SELECT data FROM anchors WHERE key = ?", (key,))
        row = cur.fetchone()
        return json.loads(row['data']) if row else (default or {})
        
    def load_all_anchors(self):
        cur = self.cursor.execute("SELECT key, data FROM anchors")
        return {row['key']: json.loads(row['data']) for row in cur.fetchall()}

    # --- [Section 4: 설계도 및 로그] ---
    def save_blueprint(self, ep_num, data_dict):
        serialized = json.dumps(data_dict, ensure_ascii=False)
        self.cursor.execute("INSERT OR REPLACE INTO blueprints (ep_num, data) VALUES (?, ?)", (ep_num, serialized))
        # [수정] 트랜잭션 안전성 확보
        if not self.conn.in_transaction: self.conn.commit()

    def get_previous_blueprint(self, current_ep):
        cur = self.cursor.execute("SELECT data FROM blueprints WHERE ep_num = ?", (current_ep - 1,))
        row = cur.fetchone()
        return json.loads(row['data']) if row else None

    def save_state_log(self, ep_num, data_dict):
        """기존 메서드 호환성 유지"""
        self.save_state_log_with_summary(ep_num, data_dict, "")

    def save_state_log_with_summary(self, ep_num, data_dict, summary):
        """[NEW] 요약 포함 로그 저장"""
        serialized = json.dumps(data_dict, ensure_ascii=False)
        self.cursor.execute("INSERT OR REPLACE INTO state_logs (ep_num, data, summary) VALUES (?, ?, ?)", (ep_num, serialized, summary))
        if not self.conn.in_transaction: self.conn.commit()

    def get_latest_state(self):
        cur = self.cursor.execute("SELECT data FROM state_logs ORDER BY ep_num DESC LIMIT 1")
        row = cur.fetchone()
        return json.loads(row['data']) if row else {}

    def get_causal_summary_chain(self, limit=5):
        """[NEW] 과거 요약 체인 인출"""
        cur = self.cursor.execute("SELECT ep_num, summary FROM state_logs WHERE summary IS NOT NULL ORDER BY ep_num DESC LIMIT ?", (limit,))
        return "\n".join([f"- [제 {r['ep_num']} 화]: {r['summary']}" for r in reversed(cur.fetchall())])

    # --- [Section 5: 관계 및 인과] ---
    def update_karma(self, npc_name, mis_val, obs_val, ep_num):
        self.cursor.execute('''
            INSERT INTO karma_status (npc_name, misunderstanding, obsession, last_updated_ep)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(npc_name) DO UPDATE SET
                misunderstanding = ?,
                obsession = ?,
                last_updated_ep = ?
        ''', (npc_name, mis_val, obs_val, ep_num, mis_val, obs_val, ep_num))
        if not self.conn.in_transaction: self.conn.commit()
        
    def get_all_karma(self):
        cur = self.cursor.execute("SELECT * FROM karma_status")
        return {row['npc_name']: dict(row) for row in cur.fetchall()}

    def save_causal_links(self, new_links, current_ep):
        if not new_links: return
        data_to_insert = []
        for link in new_links:
            ep = link.get('ep') or current_ep
            serialized = json.dumps(link, ensure_ascii=False)
            data_to_insert.append((ep, serialized))
        self.cursor.executemany("INSERT INTO causal_graph (ep_num, data) VALUES (?, ?)", data_to_insert)
        if not self.conn.in_transaction: self.conn.commit()

    # --- [Sovereign Unified Transaction: 최종 박제] ---
    def commit_episode_factory(self, ep_num, manuscript_data, martial_data, state_data, causal_links, karma_data, lore_data, recovered_seeds=None):
        """
        [V27.0 S-Grade] 하위 항목 문자열화 현상까지 완벽 차단하는 무결성 엔진
        - 원자적 트랜잭션 보장
        - AI 데이터 파싱 유연성 극대화
        - 하위 엔터티(카르마, 로어, 복선)의 정규화 및 박제
        """
        
        # 1. 최상위 데이터 파싱 및 정규화 (딕셔너리 보장)
        if isinstance(manuscript_data, str):
            try: 
                manuscript_data = json.loads(manuscript_data)
            except: 
                manuscript_data = {'title': f"제 {ep_num} 화", 'content': manuscript_data}
            
        if isinstance(state_data, str):
            try: 
                state_data = json.loads(state_data)
            except: 
                state_data = {'context_audit': {'summary': '데이터 파싱 오류'}}

        # 트랜잭션 중첩 상태 확인 (상위 루프에서 이미 열려있는지 체크)
        nested_transaction = self.conn.in_transaction
        
        try:
            # 2. 트랜잭션 시작 (최상위 트랜잭션일 때만 실행)
            if not nested_transaction:
                self.begin()
                
            # 3. 원고 본문 및 무학 지표(HUD) 저장
            self.save_manuscript(ep_num, manuscript_data.get('title', '무제'), manuscript_data.get('content', ''))
            if martial_data: 
                self.update_martial_tracker(ep_num, martial_data)
            
            # 4. 상태 로그 저장 및 요약(Summary) 추출
            audit = state_data.get('context_audit', {})
            # context_audit 자체가 문자열로 들어오는 할루시네이션 방어
            summary = audit.get('summary', '') if isinstance(audit, dict) else str(audit)
            self.save_state_log_with_summary(ep_num, state_data, summary)
            
            # 5. 🚨 인과관계(Causal Links) 데이터 정규화 및 저장
            if causal_links:
                normalized_links = []
                for link in causal_links:
                    # AI가 {"cause": "A", "effect": "B"} 가 아니라 "A -> B" 같은 문자열을 보냈을 때 대응
                    if isinstance(link, str):
                        normalized_links.append({"cause": "서사 진행", "effect": link})
                    elif isinstance(link, dict):
                        normalized_links.append(link)
                
                # [수정] 인자 오류 해결: ep_num을 함께 전달하여 유실 방지
                self.save_causal_links(normalized_links, ep_num)
                
            # 6. 🚨 카르마(NPC 관계) 데이터 정규화 및 에피소드 번호 강제 매핑
            if karma_data:
                for k in karma_data:
                    if not isinstance(k, dict): continue
                    
                    # AI의 다양한 키값 형태(target/npc_name, misunderstanding/value)를 모두 포용
                    npc = k.get('target') or k.get('npc_name') or k.get('name', 'Unknown')
                    mis = k.get('misunderstanding') or k.get('value') or k.get('point', 0)
                    obs = k.get('obsession') or k.get('point') or 0
                    
                    # 수동 갱신 시점(ep_num)을 현재 화수로 박제하여 데이터 오염 방지
                    self.update_karma(npc, mis, obs, ep_num)
            
            # 7. 로어(Encyclopedia) 데이터 정규화 및 수혈
            if lore_data and isinstance(lore_data, dict):
                for cat, items in lore_data.items():
                    if not isinstance(items, list): continue
                    for item in items:
                        if not isinstance(item, dict): continue
                        name = item.get('name') or item.get('Item')
                        desc = item.get('description') or item.get('desc') or str(item)
                        if name: 
                            self.update_lore_item(cat, name, desc)

            # 8. 복선 회수(Seeds) 처리 (ID 정규화 및 상태 갱신)
            if recovered_seeds and isinstance(recovered_seeds, list):
                for rec in recovered_seeds:
                    if not isinstance(rec, dict): continue
                    sid = rec.get('seed_id') or rec.get('id')
                    if sid:
                        self.cursor.execute(
                            "UPDATE seeds SET status = 'archived', recovered_ep = ? WHERE seed_id = ?", 
                            (ep_num, sid)
                        )

            # 9. 트랜잭션 커밋 (최상위 트랜잭션일 때만)
            if not nested_transaction:
                self.commit() 
                print(f"      🎬 [DB Transaction] 제 {ep_num}화 데이터 안전 박제 완료.")
            
            return True

        except Exception as e:
            # 🛡️ [핵심] 롤백 및 예외 전파 전략
            if not nested_transaction:
                # 내가 시작한 트랜잭션이면 책임지고 전체 취소
                self.rollback()
                print(f"      🚨 [DB Critical] 트랜잭션 실패(롤백 완료): {e}")
                return False
            else:
                # 상위 트랜잭션이 있는 경우, 상위 로직이 롤백을 결정할 수 있게 에러를 전파
                print(f"      ⚠️ [DB Nested Error] 내부 저장 실패 (상위 롤백 유도): {e}")
                raise e
            

    @contextmanager
    def transaction(self):
        """[V35.5] 원자적 트랜잭션 보장 가드. 에러 시 자동 롤백 및 세션 보호"""
        try:
            if not self.conn.in_transaction:
                self.cursor.execute("BEGIN TRANSACTION")
            yield
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"🚨 [DB Transaction Error] 롤백 수행: {e}")
            raise e



            
    # --- [Utility] ---
    def get_latest_episode_number(self) -> int:
        cur = self.cursor.execute("SELECT MAX(ep_num) as max_ep FROM manuscripts")
        row = cur.fetchone()
        return (row['max_ep'] or 0) + 1

    def get_context_manuscripts(self, current_ep, limit=3):
        cur = self.cursor.execute("SELECT ep_num, title, content FROM manuscripts WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?", (current_ep, limit))
        return [dict(row) for row in cur.fetchall()]

    def reset_after(self, target_ep):
        """전체 테이블 리셋 및 롤백"""
        tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]
        for tbl in tables: self.cursor.execute(f"DELETE FROM {tbl} WHERE ep_num >= ?", (target_ep,))
        self.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
        self.cursor.execute("DELETE FROM seeds WHERE planted_ep >= ?", (target_ep,))
        # 로어는 시간 개념이 모호하므로 유지하거나 별도 정책 필요 (여기선 유지)
        self.conn.commit()
        self.cursor.execute("VACUUM")

    # --- [Memory Sync 전용 메서드] ---
    def get_sync_status(self, ep_num):
        """특정 에피소드의 벡터 DB 동기화 여부 조회"""
        cur = self.cursor.execute("SELECT vector_synced FROM sync_status WHERE ep_num = ?", (ep_num,))
        row = cur.fetchone()
        return row['vector_synced'] if row else None

    def update_sync_status(self, ep_num, status):
        """벡터 DB 동기화 상태 업데이트 (0: 미완료, 1: 완료)"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_status (ep_num, vector_synced, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (ep_num, status))
        if not self.conn.in_transaction: 
            self.conn.commit()

    # modules/core/db_manager.py 에 추가하면 좋은 전용 메서드
    def get_active_seeds(self):
        cur = self.cursor.execute("SELECT * FROM seeds WHERE status = 'active'")
        return [dict(row) for row in cur.fetchall()]