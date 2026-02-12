import sqlite3
import logging
import json
from pathlib import Path
import time
import traceback
import threading
from .constants import MARTIAL_METRICS # 👈 상수 임포트
from contextlib import contextmanager


# [V44] DB 에러 심각도 분류
class DBErrorSeverity:
    CRITICAL = "CRITICAL"  # 데이터 손실 위험
    HIGH = "HIGH"          # 작업 실패, 복구 가능
    WARN = "WARN"          # 경고, 계속 진행 가능


# [V44] 커스텀 DB 예외 클래스
class DBError(Exception):
    """DB 작업 중 발생하는 기본 예외"""
    def __init__(self, message, severity=DBErrorSeverity.HIGH, original_error=None) -> None:
        super().__init__(message)
        self.severity = severity
        self.original_error = original_error


class DBIntegrityError(DBError):
    """데이터 무결성 오류 (제약조건 위반 등)"""
    pass


class DBConnectionError(DBError):
    """DB 연결 오류"""
    pass


class DBTransactionError(DBError):
    """트랜잭션 관련 오류"""
    pass


class DBManager:
    """[V20 Sovereign DB Engine] S등급 무결성: 트랜잭션 보호 및 로어 테이블화 완비"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        # [V45] 멀티스레드 안전성을 위한 Lock
        self._lock = threading.RLock()
        # [V64 P2-7] 누적 Bible 증분 캐시 {up_to_ep: cumulative_dict}
        self._cumulative_bible_cache: dict = {}
        self._boot_db()

    def _boot_db(self) -> None:
        """DB 연결 및 10대 핵심 테이블 초기화"""
        # [V45] check_same_thread=False 사용 시 RLock으로 보호
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
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
        # [V45] ALTER TABLE 오류 처리 강화 - commit/rollback 추가
        try:
            self.cursor.execute("PRAGMA table_info(state_logs)")
            existing_cols = {row['name'] for row in self.cursor.fetchall()}
            if 'summary' not in existing_cols:
                self.cursor.execute("ALTER TABLE state_logs ADD COLUMN summary TEXT")
                self.conn.commit()  # [V45] 마이그레이션 성공 시 즉시 커밋
        except sqlite3.OperationalError as e:
            # 테이블 자체가 없는 경우 (CREATE TABLE IF NOT EXISTS에서 처리됨)
            if "no such table" not in str(e).lower():
                logging.warning(f"[WARNING] state_logs 마이그레이션 실패: {e}")
                try:
                    self.conn.rollback()  # [V45] 실패 시 롤백
                except Exception as e:
                    logging.debug(f"[SILENT] state_logs rollback: {e}")
                    pass

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

        # [Phase 5.2.2] 7. Reflexion Memory (과거 실패 패턴 학습)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reflexion_memory (
                pattern_type TEXT PRIMARY KEY,
                description TEXT,
                frequency INTEGER DEFAULT 1,
                solution TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                first_ep INTEGER,
                last_ep INTEGER
            )
        ''')

        # ------------------------------------------------------------------
        # 🚨 [Patch 1.1] Martial Tracker 자동 스키마 마이그레이션 로직
        # ------------------------------------------------------------------
        # 1. 테이블 생성 (없을 경우)
        # [V44] SQL 컬럼명 검증 (알파벳, 숫자, 언더스코어만 허용)
        import re
        safe_column_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        validated_metrics = [k for k in MARTIAL_METRICS if safe_column_pattern.match(k)]
        if len(validated_metrics) != len(MARTIAL_METRICS):
            invalid = set(MARTIAL_METRICS) - set(validated_metrics)
            logging.warning(f"[WARNING] 잘못된 컬럼명 무시됨: {invalid}")
        columns_def = ", ".join([f"{k} TEXT" for k in validated_metrics])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS martial_tracker (ep_num INTEGER PRIMARY KEY, {columns_def})")
        
        # 2. 컬럼 동기화 검사 (코드에는 있는데 DB에 없는 컬럼 찾기)
        try:
            # 현재 DB의 컬럼 목록 조회
            self.cursor.execute("PRAGMA table_info(martial_tracker)")
            existing_columns = {row['name'] for row in self.cursor.fetchall()}
            
            # MARTIAL_METRICS 순회하며 누락된 컬럼 추가
            for metric in MARTIAL_METRICS:
                if metric not in existing_columns:
                    logging.info(f"🔧 [DB Migration] 새로운 지표 '{metric}' 발견. 테이블에 컬럼을 추가합니다.")
                    self.cursor.execute(f"ALTER TABLE martial_tracker ADD COLUMN {metric} TEXT")
            
            self.conn.commit()
            
        except sqlite3.IntegrityError as e:
            # 무결성 오류: 컬럼 이름 충돌 등
            logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 마이그레이션 무결성 오류: {e}")
            # 기존 테이블 구조 유지, 계속 진행
        except sqlite3.OperationalError as e:
            # 운영 오류: 테이블 잠금, 디스크 오류 등
            error_str = str(e).lower()
            if "locked" in error_str:
                logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] DB 잠금 상태. 다른 프로세스 확인 필요: {e}")
            elif "disk" in error_str or "i/o" in error_str:
                logging.warning(f"🚨 [{DBErrorSeverity.CRITICAL}] 디스크 I/O 오류: {e}")
            else:
                logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 마이그레이션 운영 오류: {e}")
        except Exception as e:
            logging.warning(f"🚨 [{DBErrorSeverity.WARN}] 마이그레이션 기타 오류: {e}")
            logging.info(f"→ 상세: {traceback.format_exc()[:200]}")
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

        # 10. [V49.5] 화별 Bible (에피소드별 설정 변화 추적)
        # [V60.82] causal_links, karma_matrix, knowledge_map 컬럼 추가
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS episode_bibles (
                ep_num INTEGER PRIMARY KEY,
                new_items TEXT,              -- JSON: 새로 획득한 아이템
                lost_items TEXT,             -- JSON: 잃어버린/파괴된 아이템
                new_npcs TEXT,               -- JSON: 새로 등장한 NPC
                npc_deaths TEXT,             -- JSON: 사망한 NPC
                relationship_changes TEXT,   -- JSON: [{target, from, to, justification}]
                state_changes TEXT,          -- JSON: 상태 변화 (부상, 경지 등)
                time_passed TEXT,            -- 경과 시간 (예: "같은 날 밤", "3일 후")
                reveals TEXT,                -- JSON: 밝혀진 사실/복선 회수
                causal_links TEXT,           -- [V60.82] JSON: 인과관계 링크
                karma_matrix TEXT,           -- [V60.82] JSON: 카르마 매트릭스
                knowledge_map TEXT,          -- [V60.82] JSON: 지식 맵 (목격자/오해자)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # [V60.82] 기존 테이블에 새 컬럼 추가 (마이그레이션)
        # [V64.P4] sqlite3.OperationalError: column already exists — expected during migration
        try:
            self.cursor.execute("ALTER TABLE episode_bibles ADD COLUMN causal_links TEXT")
        except sqlite3.OperationalError:
            logging.debug("[SILENT] ALTER TABLE causal_links: column already exists")
            pass  # 이미 존재
        try:
            self.cursor.execute("ALTER TABLE episode_bibles ADD COLUMN karma_matrix TEXT")
        except sqlite3.OperationalError:
            logging.debug("[SILENT] ALTER TABLE karma_matrix: column already exists")
            pass  # 이미 존재
        try:
            self.cursor.execute("ALTER TABLE episode_bibles ADD COLUMN knowledge_map TEXT")
        except sqlite3.OperationalError:
            logging.debug("[SILENT] ALTER TABLE knowledge_map: column already exists")
            pass  # 이미 존재

        # 11. Reflexion 메모리 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reflexion_memory (
                pattern_type TEXT PRIMARY KEY,
                description TEXT,
                frequency INTEGER DEFAULT 1,
                solution TEXT,
                first_seen TEXT,
                last_seen TEXT,
                first_ep INTEGER,
                last_ep INTEGER
            )
        ''')

        self.conn.commit()

    # --- [트랜잭션 제어] ---
    def begin(self): self.cursor.execute("BEGIN TRANSACTION")
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()

    # --- [범용 쿼리] ---
    def execute_query(self, sql: str, params: tuple = ()) -> list:
        """SELECT 쿼리 실행 후 결과 리스트 반환"""
        with self._lock:
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()

    def execute_update(self, sql: str, params: tuple = ()):
        """INSERT/UPDATE/DELETE 쿼리 실행"""
        with self._lock:
            self.cursor.execute(sql, params)

    # --- [Section 1: 원고 및 지표] ---
    def save_manuscript(self, ep_num, title, content) -> None:
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
        if not row:
            return None
        try:
            return json.loads(row['data'])
        except (json.JSONDecodeError, TypeError) as e:  # [V70] NULL data → TypeError 방어
            logging.warning(f"🚨 [DB] Blueprint JSON 파싱 실패 (ep_num={ep_num}): {e}")
            return None
    
    
    def update_martial_tracker(self, ep_num, martial_data) -> None:
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

    # --- [V49.5] 화별 Bible CRUD ---
    # [V60.82] causal_links, karma_matrix, knowledge_map 필드 추가
    def save_episode_bible(self, ep_num: int, bible_delta: dict):
        """화별 Bible 저장 (원고에서 추출된 설정 변화)"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO episode_bibles
            (ep_num, new_items, lost_items, new_npcs, npc_deaths,
             relationship_changes, state_changes, time_passed, reveals,
             causal_links, karma_matrix, knowledge_map)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ep_num,
            json.dumps(bible_delta.get('new_items', []), ensure_ascii=False),
            json.dumps(bible_delta.get('lost_items', []), ensure_ascii=False),
            json.dumps(bible_delta.get('new_npcs', []), ensure_ascii=False),
            json.dumps(bible_delta.get('npc_deaths', []), ensure_ascii=False),
            json.dumps(bible_delta.get('relationship_changes', []), ensure_ascii=False),
            json.dumps(bible_delta.get('state_changes', {}), ensure_ascii=False),
            bible_delta.get('time_passed', ''),
            json.dumps(bible_delta.get('reveals', []), ensure_ascii=False),
            json.dumps(bible_delta.get('causal_links', []), ensure_ascii=False),
            json.dumps(bible_delta.get('karma_matrix', []), ensure_ascii=False),
            json.dumps(bible_delta.get('knowledge_map', {}), ensure_ascii=False)
        ))
        if not self.conn.in_transaction:
            self.conn.commit()
        # [V64 P2-7] 누적 Bible 캐시 무효화: 이 ep 이후 캐시 모두 삭제
        invalidate_eps = [k for k in self._cumulative_bible_cache if k >= ep_num]
        for k in invalidate_eps:
            del self._cumulative_bible_cache[k]

    def get_episode_bible(self, ep_num: int) -> dict:
        """특정 화의 Bible delta 조회"""
        cur = self.cursor.execute(
            "SELECT * FROM episode_bibles WHERE ep_num = ?", (ep_num,)
        )
        row = cur.fetchone()
        if not row:
            return {}
        # [V60.82] 새 컬럼 안전 조회 (마이그레이션 전 DB 호환)
        def safe_get(key, default='[]'):
            try:
                return row[key] if key in row.keys() else default
            except (KeyError, IndexError, TypeError):  # [V64.P4] specific exception for row access
                return default

        return {
            'ep_num': row['ep_num'],
            'new_items': json.loads(row['new_items'] or '[]'),
            'lost_items': json.loads(row['lost_items'] or '[]'),
            'new_npcs': json.loads(row['new_npcs'] or '[]'),
            'npc_deaths': json.loads(row['npc_deaths'] or '[]'),
            'relationship_changes': json.loads(row['relationship_changes'] or '[]'),
            'state_changes': json.loads(row['state_changes'] or '{}'),
            'time_passed': row['time_passed'] or '',
            'reveals': json.loads(row['reveals'] or '[]'),
            # [V60.82] 새 필드
            'causal_links': json.loads(safe_get('causal_links', '[]') or '[]'),
            'karma_matrix': json.loads(safe_get('karma_matrix', '[]') or '[]'),
            'knowledge_map': json.loads(safe_get('knowledge_map', '{}') or '{}')
        }

    def get_cumulative_bible(self, up_to_ep: int) -> dict:
        """
        1화부터 특정 화까지의 누적 Bible 계산
        [V64 P2-7] 증분 캐시: 이전 결과를 재활용하여 새 에피소드만 DB 조회
        """
        import copy as _copy

        # [V64 P2-7] 정확히 같은 ep 캐시가 있으면 즉시 반환 (deep copy로 mutation 방지)
        if up_to_ep in self._cumulative_bible_cache:
            return _copy.deepcopy(self._cumulative_bible_cache[up_to_ep])

        # 이전 캐시 중 가장 큰 ep 찾아서 재활용
        best_cached_ep = 0
        for cached_ep in self._cumulative_bible_cache:
            if cached_ep < up_to_ep and cached_ep > best_cached_ep:
                best_cached_ep = cached_ep

        if best_cached_ep > 0:
            cumulative = _copy.deepcopy(self._cumulative_bible_cache[best_cached_ep])
            start_ep = best_cached_ep + 1
        else:
            cumulative = {
                'items': [],           # 현재 소지 아이템
                'npcs': [],            # 등장한 NPC 목록
                'dead_npcs': [],       # 사망 NPC 목록
                'relationships': {},   # {target: current_state}
                'states': {},          # {subject: current_state}
                'total_time': '',      # 누적 시간 흐름
                'all_reveals': []      # 모든 밝혀진 사실
            }
            start_ep = 1

        cur = self.cursor.execute(
            "SELECT * FROM episode_bibles WHERE ep_num >= ? AND ep_num <= ? ORDER BY ep_num",
            (start_ep, up_to_ep)
        )
        rows = cur.fetchall()

        for row in rows:
            # 아이템: 획득은 추가, 분실은 제거
            new_items = json.loads(row['new_items'] or '[]')
            lost_items = json.loads(row['lost_items'] or '[]')
            cumulative['items'].extend(new_items)
            cumulative['items'] = [i for i in cumulative['items'] if i not in lost_items]

            # NPC: 등장 추가, 사망은 별도 추적
            new_npcs = json.loads(row['new_npcs'] or '[]')
            npc_deaths = json.loads(row['npc_deaths'] or '[]')
            cumulative['npcs'].extend(new_npcs)
            cumulative['dead_npcs'].extend(npc_deaths)

            # 관계: 최신 상태로 덮어씀
            rel_changes = json.loads(row['relationship_changes'] or '[]')
            for change in rel_changes:
                if isinstance(change, dict):
                    target = change.get('target', '')
                    if target:
                        cumulative['relationships'][target] = change.get('to', '')

            # 상태: 최신 상태로 덮어씀 [V61.5] dict/list 양방향 처리
            state_changes = json.loads(row['state_changes'] or '{}')
            if isinstance(state_changes, dict):
                # dict 형태: {"internal_energy": "80%", "realm": "기경팔맥"}
                for subject, value in state_changes.items():
                    if isinstance(value, (str, int, float)):
                        cumulative['states'][subject] = str(value)
            elif isinstance(state_changes, list):
                # 레거시 list 형태: [{"subject": "내공", "to": "80%"}]
                for state in state_changes:
                    if isinstance(state, dict):
                        subject = state.get('subject', '')
                        if subject:
                            cumulative['states'][subject] = state.get('to', '')

            # 밝혀진 사실 누적
            reveals = json.loads(row['reveals'] or '[]')
            cumulative['all_reveals'].extend(reveals)

        # 캐시 저장
        self._cumulative_bible_cache[up_to_ep] = _copy.deepcopy(cumulative)

        # [V66.1] C-3: LRU 캐시 크기 제한 (최대 5개 — 장기 세션 메모리 안정화)
        _MAX_BIBLE_CACHE = 5
        while len(self._cumulative_bible_cache) > _MAX_BIBLE_CACHE:
            # 가장 오래된 (가장 작은 ep) 캐시 제거
            oldest_ep = min(self._cumulative_bible_cache.keys())
            del self._cumulative_bible_cache[oldest_ep]

        return cumulative

    def get_all_episode_bibles(self) -> list:
        """
        [V60.8] 모든 Episode Bible 조회
        [V60.82] causal_links, karma_matrix, knowledge_map 추가

        Returns:
            list: Episode Bible dict 목록 (ep_num 순 정렬)
        """
        cur = self.cursor.execute(
            "SELECT * FROM episode_bibles ORDER BY ep_num"
        )
        rows = cur.fetchall()

        bibles = []
        for row in rows:
            # [V60.82] 새 컬럼 안전 조회
            def safe_get(key, default='[]'):
                try:
                    return row[key] if key in row.keys() else default
                except (KeyError, IndexError, TypeError):  # [V64.P4] specific exception for row access
                    return default

            bibles.append({
                'ep_num': row['ep_num'],
                'new_items': json.loads(row['new_items'] or '[]'),
                'lost_items': json.loads(row['lost_items'] or '[]'),
                'new_npcs': json.loads(row['new_npcs'] or '[]'),
                'npc_deaths': json.loads(row['npc_deaths'] or '[]'),
                'relationship_changes': json.loads(row['relationship_changes'] or '[]'),
                'state_changes': json.loads(row['state_changes'] or '{}'),
                'time_passed': row['time_passed'] or '',
                'reveals': json.loads(row['reveals'] or '[]'),
                # [V60.82] 새 필드
                'causal_links': json.loads(safe_get('causal_links', '[]') or '[]'),
                'karma_matrix': json.loads(safe_get('karma_matrix', '[]') or '[]'),
                'knowledge_map': json.loads(safe_get('knowledge_map', '{}') or '{}')
            })

        return bibles

    def delete_episode_bibles_after(self, ep_num: int):
        """특정 화 이후의 Bible delta 삭제 (롤백용)"""
        self.cursor.execute(
            "DELETE FROM episode_bibles WHERE ep_num > ?", (ep_num,)
        )
        if not self.conn.in_transaction:
            self.conn.commit()
        # [V70] 누적 Bible 캐시 무효화 (save_episode_bible과 동일 패턴)
        invalidate_eps = [k for k in self._cumulative_bible_cache if k > ep_num]
        for k in invalidate_eps:
            del self._cumulative_bible_cache[k]
        return self.cursor.rowcount

    # --- [Section 2: 복선 및 로어] ---
# modules/core/db_manager.py
# [V35.5] 수술 기록 박제 메서드 추가
    def save_surgery_log(self, ep_num, category, failed_logic, result) -> None:
        self.cursor.execute('''
            INSERT INTO surgery_logs (ep_num, error_category, failed_logic, surgery_result)
            VALUES (?, ?, ?, ?)
        ''', (ep_num, category, failed_logic, result))
        # [V44 Fix] 중첩 트랜잭션 안전성 보장
        if not self.conn.in_transaction:
            self.conn.commit()



    def sync_seeds(self, seeds_list) -> None:
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
    def archive_seed(self, seed_id, ep_num) -> None:
        self.cursor.execute("UPDATE seeds SET status = 'archived', recovered_ep = ? WHERE seed_id = ?", (ep_num, seed_id))
        if not self.conn.in_transaction: self.conn.commit()

    def update_lore_item(self, category, item, description) -> None:
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

    def update_lore_items_batch(self, lore_items_list) -> None:
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

        except sqlite3.IntegrityError as e:
            # 중복 키 등 무결성 오류 - 개별 항목으로 재시도 가능
            if not nested:
                self.rollback()
            logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 로어 일괄 저장 무결성 오류: {e}")
            logging.info(f"→ 해결책: 중복 항목 확인 후 개별 저장 시도")
            if nested:
                raise DBIntegrityError(f"로어 저장 무결성 오류: {e}", original_error=e) from e
        except sqlite3.OperationalError as e:
            if not nested:
                self.rollback()
            error_str = str(e).lower()
            if "locked" in error_str:
                logging.warning(f"🚨 [{DBErrorSeverity.CRITICAL}] DB 잠금 상태: {e}")
                logging.info(f"→ 해결책: 다른 프로세스/연결 종료 후 재시도")
            else:
                logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 로어 저장 운영 오류: {e}")
            if nested:
                raise DBTransactionError(f"로어 저장 트랜잭션 오류: {e}", original_error=e) from e
        except Exception as e:
            if not nested:
                self.rollback()
            logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 로어 일괄 저장 실패: {e}")
            logging.info(f"→ 상세: {traceback.format_exc()[:300]}")
            if nested:
                raise DBError(f"로어 저장 기타 오류: {e}", original_error=e) from e

# --- [Section 2 보완: 로어 인출] ---
    def get_lore_item(self, item_name):
        """특정 인물/아이템의 설정을 테이블에서 즉시 조회"""
        cur = self.cursor.execute("SELECT * FROM encyclopedia WHERE item = ?", (item_name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_lore_list_by_category(self, category):
        """특정 카테고리(NPC, ITEM 등) 전체 리스트 인출. category가 None이면 전체 반환"""
        if category is None:
            cur = self.cursor.execute("SELECT * FROM encyclopedia")
        else:
            cur = self.cursor.execute("SELECT * FROM encyclopedia WHERE category = ?", (category,))
        return [dict(row) for row in cur.fetchall()]



    def save_anchor(self, key, data) -> bool:
        """S등급 데이터를 박제하고 타임스탬프를 강제 갱신함"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            # 쿼리문에 CURRENT_TIMESTAMP를 명시하여 REPLACE 시에도 시간이 갱신되게 함
            self.cursor.execute("""
                INSERT OR REPLACE INTO anchors (key, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json_data))
            # [V44 Fix] 중첩 트랜잭션 안전성 보장
            if not self.conn.in_transaction:
                self.conn.commit()
            return True
        except Exception as e:
            logging.warning(f"❌ [DB Error] Anchor 저장 실패: {e}")
            return False


    def load_anchor(self, key, default=None):
        cur = self.cursor.execute("SELECT data FROM anchors WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            # [V61.5] default=[] 전달 시 [] or {} → {} 반환 버그 수정
            return default if default is not None else {}
        try:
            return json.loads(row['data'])
        except (json.JSONDecodeError, TypeError) as e:  # [V70] row['data']가 None일 때 TypeError 방어
            logging.warning(f"🚨 [DB] Anchor JSON 파싱 실패 (key={key}): {e}")
            return default if default is not None else {}
        
    def load_all_anchors(self):
        cur = self.cursor.execute("SELECT key, data FROM anchors")
        result = {}
        for row in cur.fetchall():
            try:
                result[row['key']] = json.loads(row['data'])
            except json.JSONDecodeError as e:
                logging.warning(f"🚨 [DB] Anchor JSON 파싱 실패 (key={row['key']}): {e}")
                result[row['key']] = {}
        return result

    # --- [Section 4: 설계도 및 로그] ---
    def save_blueprint(self, ep_num, data_dict) -> None:
        serialized = json.dumps(data_dict, ensure_ascii=False)
        self.cursor.execute("INSERT OR REPLACE INTO blueprints (ep_num, data) VALUES (?, ?)", (ep_num, serialized))
        # [수정] 트랜잭션 안전성 확보
        if not self.conn.in_transaction: self.conn.commit()

    def get_previous_blueprint(self, current_ep):
        cur = self.cursor.execute("SELECT data FROM blueprints WHERE ep_num = ?", (current_ep - 1,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row['data'])
        except (json.JSONDecodeError, TypeError) as e:  # [V70] NULL data → TypeError 방어
            logging.warning(f"🚨 [DB] Blueprint JSON 파싱 실패 (ep_num={current_ep - 1}): {e}")
            return None

    def save_state_log(self, ep_num, data_dict) -> None:
        """기존 메서드 호환성 유지"""
        self.save_state_log_with_summary(ep_num, data_dict, "")

    def save_state_log_with_summary(self, ep_num, data_dict, summary) -> None:
        """[NEW] 요약 포함 로그 저장"""
        serialized = json.dumps(data_dict, ensure_ascii=False)
        self.cursor.execute("INSERT OR REPLACE INTO state_logs (ep_num, data, summary) VALUES (?, ?, ?)", (ep_num, serialized, summary))
        if not self.conn.in_transaction: self.conn.commit()

    def get_latest_state(self) -> dict:
        cur = self.cursor.execute("SELECT data FROM state_logs ORDER BY ep_num DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            return {}
        try:
            return json.loads(row['data'])
        except json.JSONDecodeError as e:
            logging.warning(f"🚨 [DB] State log JSON 파싱 실패: {e}")
            return {}

    def load_state_log(self, ep_num: int) -> dict:
        """[FIX] 특정 에피소드의 state_log 조회"""
        try:
            cur = self.cursor.execute(
                "SELECT data, summary FROM state_logs WHERE ep_num = ?", (ep_num,)
            )
            row = cur.fetchone()
            if not row:
                return None
            result = {'summary': row['summary'] if row['summary'] else ''}
            try:
                result['data'] = json.loads(row['data']) if row['data'] else {}
            except json.JSONDecodeError:
                result['data'] = {}
            return result
        except Exception as e:
            logging.warning(f"🚨 [DB] State log 조회 실패 (ep {ep_num}): {e}")
            return None

    def get_causal_summary_chain(self, limit=5):
        """[NEW] 과거 요약 체인 인출"""
        cur = self.cursor.execute("SELECT ep_num, summary FROM state_logs WHERE summary IS NOT NULL ORDER BY ep_num DESC LIMIT ?", (limit,))
        return "\n".join([f"- [제 {r['ep_num']} 화]: {r['summary']}" for r in reversed(cur.fetchall())])

    # --- [Section 5: 관계 및 인과] ---
    def update_karma(self, npc_name, mis_val, obs_val, ep_num) -> None:
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

    def save_causal_links(self, new_links, current_ep) -> None:
        if not new_links: return
        data_to_insert = []
        for link in new_links:
            ep = link.get('ep') or current_ep
            serialized = json.dumps(link, ensure_ascii=False)
            data_to_insert.append((ep, serialized))
        self.cursor.executemany("INSERT INTO causal_graph (ep_num, data) VALUES (?, ?)", data_to_insert)
        if not self.conn.in_transaction: self.conn.commit()

    # --- [Sovereign Unified Transaction: 최종 박제] ---
    def commit_episode_factory(self, ep_num, manuscript_data, martial_data, state_data, causal_links, karma_data, lore_data, recovered_seeds=None) -> bool:
        """
        [V27.0 S-Grade] 하위 항목 문자열화 현상까지 완벽 차단하는 무결성 엔진
        - 원자적 트랜잭션 보장
        - AI 데이터 파싱 유연성 극대화
        - 하위 엔터티(카르마, 로어, 복선)의 정규화 및 박제
        """
        # [FIX] RLock으로 멀티스레드 동시 접근 보호
        self._lock.acquire()
        try:
            # 1. 최상위 데이터 파싱 및 정규화 (딕셔너리 보장)
            if isinstance(manuscript_data, str):
                try:
                    manuscript_data = json.loads(manuscript_data)
                except (json.JSONDecodeError, ValueError):
                    manuscript_data = {'title': f"제 {ep_num} 화", 'content': manuscript_data}

            if isinstance(state_data, str):
                try:
                    state_data = json.loads(state_data)
                except (json.JSONDecodeError, ValueError):
                    state_data = {'context_audit': {'summary': '데이터 파싱 오류'}}

            # 트랜잭션 중첩 상태 확인 (상위 루프에서 이미 열려있는지 체크)
            nested_transaction = self.conn.in_transaction
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
                logging.info(f"🎬 [DB Transaction] 제 {ep_num}화 데이터 안전 박제 완료.")
            
            return True

        except sqlite3.IntegrityError as e:
            # 무결성 오류: 중복 키, 제약 조건 위반 등
            if not nested_transaction:
                self.rollback()
                logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 데이터 무결성 오류(롤백 완료): {e}")
                logging.info(f"→ 해결책: 중복 에피소드 번호 또는 키 확인")
                return False
            else:
                logging.warning(f"⚠️ [{DBErrorSeverity.HIGH}] 내부 무결성 오류 (상위 롤백 유도): {e}")
                raise DBIntegrityError(f"에피소드 {ep_num} 저장 무결성 오류",
                                       severity=DBErrorSeverity.HIGH, original_error=e) from e

        except sqlite3.OperationalError as e:
            # 운영 오류: DB 잠금, 디스크 오류, 쿼리 오류 등
            error_str = str(e).lower()
            if not nested_transaction:
                self.rollback()

            if "locked" in error_str:
                logging.warning(f"🚨 [{DBErrorSeverity.CRITICAL}] DB 잠금 상태(롤백 완료): {e}")
                logging.info(f"→ 해결책: ChromaDB LOCK 파일 삭제 또는 프로세스 재시작")
            elif "disk" in error_str or "i/o" in error_str:
                logging.warning(f"🚨 [{DBErrorSeverity.CRITICAL}] 디스크 I/O 오류(롤백 완료): {e}")
                logging.info(f"→ 해결책: 디스크 공간 및 권한 확인")
            else:
                logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] DB 운영 오류(롤백 완료): {e}")

            if not nested_transaction:
                return False
            else:
                raise DBTransactionError(f"에피소드 {ep_num} 저장 트랜잭션 오류",
                                        severity=DBErrorSeverity.CRITICAL, original_error=e) from e

        except (DBError, DBIntegrityError, DBTransactionError) as e:
            # 커스텀 DB 예외 (하위 메서드에서 발생)
            if not nested_transaction:
                self.rollback()
                logging.warning(f"🚨 [{e.severity}] 하위 저장 오류(롤백 완료): {e}")
                return False
            else:
                raise  # 상위로 전파

        except Exception as e:
            # 🛡️ [핵심] 기타 예외 - 롤백 및 전파 전략
            if not nested_transaction:
                self.rollback()
                logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 트랜잭션 실패(롤백 완료): {e}")
                logging.info(f"→ 상세: {traceback.format_exc()[:400]}")
                return False
            else:
                logging.warning(f"⚠️ [{DBErrorSeverity.HIGH}] 내부 저장 실패 (상위 롤백 유도): {e}")
                raise DBError(f"에피소드 {ep_num} 저장 기타 오류", original_error=e) from e
        finally:
            # [FIX] RLock 해제 보장
            self._lock.release()


    @contextmanager
    def transaction(self) -> None:
        """[V44] 원자적 트랜잭션 보장 가드. 에러 타입별 롤백 및 세션 보호"""
        nested = self.conn.in_transaction
        try:
            if not nested:
                self.cursor.execute("BEGIN TRANSACTION")
            yield
            if not nested:
                self.conn.commit()
        except sqlite3.IntegrityError as e:
            if not nested:
                self.conn.rollback()
            logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 트랜잭션 무결성 오류 - 롤백 수행: {e}")
            raise DBIntegrityError(str(e), original_error=e) from e
        except sqlite3.OperationalError as e:
            if not nested:
                self.conn.rollback()
            error_str = str(e).lower()
            severity = DBErrorSeverity.CRITICAL if "locked" in error_str or "disk" in error_str else DBErrorSeverity.HIGH
            logging.warning(f"🚨 [{severity}] 트랜잭션 운영 오류 - 롤백 수행: {e}")
            if "locked" in error_str:
                logging.info(f"→ 해결책: DB 잠금 해제 후 재시도")
            raise DBTransactionError(str(e), severity=severity, original_error=e) from e
        except Exception as e:
            if not nested:
                self.conn.rollback()
            logging.warning(f"🚨 [{DBErrorSeverity.HIGH}] 트랜잭션 오류 - 롤백 수행: {e}")
            logging.info(f"→ 상세: {traceback.format_exc()[:300]}")
            raise DBError(str(e), original_error=e) from e



            
    # --- [Utility] ---
    def get_latest_episode_number(self) -> int:
        cur = self.cursor.execute("SELECT MAX(ep_num) as max_ep FROM manuscripts")
        row = cur.fetchone()
        return (row['max_ep'] or 0) + 1

    def get_latest_blueprint_number(self) -> int:
        """Blueprint 테이블의 최대 ep_num 반환 (없으면 0)"""
        cur = self.cursor.execute("SELECT MAX(ep_num) as max_ep FROM blueprints")
        row = cur.fetchone()
        return row['max_ep'] or 0

    def get_context_manuscripts(self, current_ep, limit=3):
        cur = self.cursor.execute("SELECT ep_num, title, content FROM manuscripts WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?", (current_ep, limit))
        return [dict(row) for row in cur.fetchall()]

    def reset_after(self, target_ep) -> None:
        """전체 테이블 리셋 및 롤백"""
        tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]
        for tbl in tables: self.cursor.execute(f"DELETE FROM {tbl} WHERE ep_num >= ?", (target_ep,))
        self.cursor.execute("DELETE FROM episode_bibles WHERE ep_num >= ?", (target_ep,))  # [V70] 누락 수정
        self.cursor.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))  # [V70] 동기화 상태도 리셋
        self.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
        self.cursor.execute("DELETE FROM seeds WHERE planted_ep >= ?", (target_ep,))
        # [V70] 누적 Bible 캐시 무효화
        invalidate_eps = [k for k in self._cumulative_bible_cache if k >= target_ep]
        for k in invalidate_eps:
            del self._cumulative_bible_cache[k]
        # 로어는 시간 개념이 모호하므로 유지하거나 별도 정책 필요 (여기선 유지)
        self.conn.commit()
        self.cursor.execute("VACUUM")

    # --- [Memory Sync 전용 메서드] ---
    def get_sync_status(self, ep_num):
        """특정 에피소드의 벡터 DB 동기화 여부 조회"""
        cur = self.cursor.execute("SELECT vector_synced FROM sync_status WHERE ep_num = ?", (ep_num,))
        row = cur.fetchone()
        return row['vector_synced'] if row else None

    def update_sync_status(self, ep_num, status) -> None:
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

    # --- [V61.5] Blueprint/Manuscript 연속성 캐싱용 메서드 ---
    def get_recent_blueprints(self, before_ep: int, limit: int = 10) -> list:
        """
        [V61.5] ep_num < before_ep인 blueprint 중 최근 limit개 조회

        Args:
            before_ep: 이 에피소드 이전의 blueprint만 조회
            limit: 최대 조회 개수

        Returns:
            list: [{'ep_num': int, 'data': dict}, ...] (ep_num 오름차순)
        """
        cur = self.cursor.execute(
            """SELECT ep_num, data FROM blueprints
               WHERE ep_num < ?
               ORDER BY ep_num DESC
               LIMIT ?""",
            (before_ep, limit)
        )
        results = []
        for row in cur.fetchall():
            try:
                data = json.loads(row['data']) if row['data'] else {}
            except json.JSONDecodeError:
                data = {}
            results.append({'ep_num': row['ep_num'], 'data': data})
        # 오름차순으로 정렬 (시간순)
        return list(reversed(results))

    def get_recent_manuscripts(self, before_ep: int, limit: int = 10) -> list:
        """
        [V61.5] ep_num < before_ep인 manuscript 중 최근 limit개 조회

        Args:
            before_ep: 이 에피소드 이전의 manuscript만 조회
            limit: 최대 조회 개수

        Returns:
            list: [{'ep_num': int, 'title': str, 'content': str}, ...] (ep_num 오름차순)
        """
        cur = self.cursor.execute(
            """SELECT ep_num, title, content FROM manuscripts
               WHERE ep_num < ?
               ORDER BY ep_num DESC
               LIMIT ?""",
            (before_ep, limit)
        )
        results = [dict(row) for row in cur.fetchall()]
        # 오름차순으로 정렬 (시간순)
        return list(reversed(results))

    def get_recent_manuscript_excerpts(self, before_ep: int, limit: int = 10, max_chars: int = 200) -> list:
        """
        [V66.1] B-4: ep_num < before_ep인 manuscript 중 최근 limit개의 발췌만 조회.
        SQL SUBSTR로 content의 첫 max_chars 문자만 가져와 ~100KB I/O 제거/ep.

        Args:
            before_ep: 이 에피소드 이전의 manuscript만 조회
            limit: 최대 조회 개수
            max_chars: content에서 가져올 최대 문자 수 (기본 200)

        Returns:
            list: [{'ep_num': int, 'title': str, 'content': str}, ...] (ep_num 오름차순)
        """
        cur = self.cursor.execute(
            """SELECT ep_num, title, SUBSTR(content, 1, ?) AS content FROM manuscripts
               WHERE ep_num < ?
               ORDER BY ep_num DESC
               LIMIT ?""",
            (max_chars, before_ep, limit)
        )
        results = [dict(row) for row in cur.fetchall()]
        # 오름차순으로 정렬 (시간순)
        return list(reversed(results))

    def get_all_manuscripts(self) -> list:
        """전체 원고 목록 조회 (ep_num 오름차순)"""
        cur = self.cursor.execute(
            "SELECT ep_num, title, content FROM manuscripts ORDER BY ep_num ASC"
        )
        return [dict(row) for row in cur.fetchall()]

    def get_all_blueprints(self) -> list:
        """전체 블루프린트 목록 조회 (ep_num 오름차순)"""
        cur = self.cursor.execute(
            "SELECT ep_num, data FROM blueprints ORDER BY ep_num ASC"
        )
        results = []
        for row in cur.fetchall():
            try:
                data = json.loads(row['data']) if row['data'] else {}
            except json.JSONDecodeError:
                data = {}
            results.append({'ep_num': row['ep_num'], 'data': data})
        return results