import os
import time
import json
import sqlite3
import chromadb
from google import genai
from chromadb import EmbeddingFunction, Documents, Embeddings
from pathlib import Path
import numpy as np  # 👈 [Patch 3.1] 임포트를 최상단으로 이동하여 오버헤드 제거
# [V44] 중복 import time 제거됨

class GoogleEmbeddingFunction(EmbeddingFunction):
    """[V25 Sovereign] 고정밀 임베딩 함수 (지수 백오프 적용)"""
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        # 주의: numpy(np) 임포트는 성능을 위해 파일 최상단으로 이동되었습니다.

        for text in input:
            # [V27 Patch] 서사 샘플링 전략: 도입부(60%)와 결말부(30%)를 보존하여 벡터 희석 방지
            # 전체를 청킹해서 평균을 내는 기존 방식보다 고해상도의 특징을 유지함
            max_chars = 10000 
            clean_text = text.replace("\n", " ").strip()
            
            if len(clean_text) > max_chars:
                # 앞 6000자(설정/발단) + 공백 + 뒤 3000자(결과/복선) 조합
                processed_text = clean_text[:6000] + " " + clean_text[-3000:]
            else:
                processed_text = clean_text
            
            max_retries = 3
            retry_delay = 5 # 초기 대기 시간 단축
            success = False

            for attempt in range(max_retries):
                try:
                    res = self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=processed_text
                    )
                    # [V45] 중복 import time 제거 (파일 상단에서 이미 임포트됨)
                    time.sleep(0.8)
                    
                    # 🚨 [무결성 보완] 응답 속성 이중 체크 및 값 추출
                    val = None
                    if hasattr(res, 'embeddings') and res.embeddings:
                        val = res.embeddings[0].values
                    elif hasattr(res, 'embedding'):
                        val = res.embedding.values
                    
                    if val is not None:
                        embeddings.append(val)
                        success = True
                        break
                    
                    time.sleep(0.5) # API 안정성을 위한 미세 지연
                        
                except Exception as e:
                    # 429(할당량 초과) 및 5xx(서버 오류) 대응을 위한 지수 백오프
                    if any(code in str(e) for code in ["429", "503", "504"]) and attempt < max_retries - 1:
                        # [V44] 최대 60초로 백오프 제한
                        wait_time = min(retry_delay * (2 ** attempt), 60)
                        print(f"⚠️ [Memory Quota] {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    # 기타 치명적 에러 발생 시 해당 텍스트 처리 중단
                    print(f"🚨 [Embedding Error] 치명적 오류: {e}")
                    break

            if not success:
                # 모든 재시도 실패 시 시스템 전체 중단을 방지하기 위해 제로 벡터 주입
                # [V44] 기존 임베딩에서 차원 추론, 없으면 768 (gemini-embedding-001 기본값)
                embed_dim = len(embeddings[0]) if embeddings else 768
                embeddings.append([0.0] * embed_dim) 

        return embeddings
class LongTermMemory:
    """[V44] JSON 무결성 및 시스템 동기화 통합 기억 엔진 (안전성 강화)"""

    def __init__(self, project_context):
        self.context = project_context
        self.db_path = self.context.paths.memory / "long_term_anchor.db"
        api_key = os.getenv("GOOGLE_API_KEY")

        # [V44] 초기화 상태 플래그
        self.has_valid_memory = False
        self.collection = None
        self.initialization_error = None

        # 1. SQLite3 초기화 (JSON 앵커 및 상태 관리용)
        # [V44] 연결 누수 방지를 위한 초기화
        self.conn = None
        self.cursor = None
        self.client = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._prepare_sql_table()
        except Exception as e:
            self.ui_log(f"[Memory] SQLite 초기화 실패: {e}")
            # [V44] 실패 시 기존 연결 정리
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass
            self.conn = None
            self.cursor = None

        # 2. ChromaDB 초기화 (벡터 검색용)
        # [V45] 임시 변수로 초기화하여 실패 시 정리 용이하게
        temp_client = None
        temp_collection = None
        embedding_func = None
        try:
            vector_db_path = self.db_path.parent / "vector_db"
            temp_client = chromadb.PersistentClient(path=str(vector_db_path))
            embedding_func = GoogleEmbeddingFunction(api_key)
            temp_collection = temp_client.get_or_create_collection(
                name="v20_sovereign_memory",
                embedding_function=embedding_func
            )
            # 성공 시에만 인스턴스 변수에 할당
            self.client = temp_client
            self.collection = temp_collection
            self.has_valid_memory = True
            self.ui_log("[Memory] ChromaDB 초기화 성공")
        except Exception as e:
            self.initialization_error = str(e)
            error_str = str(e).lower()

            # [V44] 에러 타입별 해결책 제시
            if "lock" in error_str:
                self.ui_log(f"[Memory] ChromaDB 잠금 오류: {e}")
                self.ui_log(f"   -> 해결책: LOCK 파일 삭제 후 재시작")
                self.ui_log(f"   -> 위치: {self.db_path.parent / 'vector_db'}")
            elif "permission" in error_str or "access" in error_str:
                self.ui_log(f"[Memory] ChromaDB 권한 오류: {e}")
                self.ui_log(f"   -> 해결책: 폴더 권한 확인")
            elif "corrupt" in error_str or "invalid" in error_str:
                self.ui_log(f"[Memory] ChromaDB 손상 감지: {e}")
                self.ui_log(f"   -> 해결책: vector_db 폴더 삭제 후 재동기화")
            else:
                self.ui_log(f"[Memory] ChromaDB 연결 실패: {e}")
                self.ui_log(f"   -> 벡터 검색 없이 계속 진행합니다")

            # [V44] 실패 시 client 정리
            self.client = None
            self.collection = None
            self.has_valid_memory = False

    def _clear_chromadb_locks(self) -> bool:
        """[V44] ChromaDB 락 파일 정리"""
        vector_db_path = self.db_path.parent / "vector_db"
        if not vector_db_path.exists():
            return False

        lock_cleared = False
        # 락 관련 파일들 정리 (데이터 파일은 보존)
        lock_patterns = ["LOCK", "*.lock", ".lock"]
        for pattern in lock_patterns:
            for lock_file in vector_db_path.glob(pattern):
                try:
                    lock_file.unlink()
                    self.ui_log(f"   🔓 [Memory] 락 파일 삭제: {lock_file.name}")
                    lock_cleared = True
                except (OSError, PermissionError) as e:
                    self.ui_log(f"   ⚠️ [Memory] 락 파일 삭제 실패: {lock_file.name} - {e}")

        # -shm, -wal 파일도 정리 (SQLite 저널)
        for ext in ["-shm", "-wal"]:
            for journal_file in vector_db_path.glob(f"*{ext}"):
                try:
                    journal_file.unlink()
                    self.ui_log(f"   🧹 [Memory] 저널 파일 삭제: {journal_file.name}")
                    lock_cleared = True
                except (OSError, PermissionError) as e:
                    # [V44] 저널 파일 삭제 실패 로깅 (ChromaDB가 사용 중일 수 있음)
                    self.ui_log(f"   ⚠️ [Memory] 저널 파일 삭제 실패 (사용 중): {journal_file.name}")

        return lock_cleared

    def _ensure_collection(self) -> bool:
        """[V44] 컬렉션 접근 전 유효성 확인 (락 복구 재시도 포함)"""
        if self.collection is not None:
            return True

        # [V44 Fix] 락 관련 에러였다면 락 정리 후 재시도
        if self.initialization_error:
            error_lower = self.initialization_error.lower()
            if "lock" in error_lower:
                self.ui_log("🔄 [Memory] ChromaDB 락 오류 감지 - 락 정리 후 재시도...")
                if self._clear_chromadb_locks():
                    # 락 정리 성공 시 에러 플래그 리셋하고 재시도
                    self.initialization_error = None
                    time.sleep(1)  # 잠시 대기
                else:
                    # 락 정리 실패 시 포기
                    return False
            else:
                # 락 외 다른 에러는 재시도하지 않음
                return False

        # 재초기화 시도
        max_retries = 2
        for attempt in range(max_retries):
            try:
                api_key = os.getenv("GOOGLE_API_KEY")
                vector_db_path = self.db_path.parent / "vector_db"
                self.client = chromadb.PersistentClient(path=str(vector_db_path))
                self.collection = self.client.get_or_create_collection(
                    name="v20_sovereign_memory",
                    embedding_function=GoogleEmbeddingFunction(api_key)
                )
                self.has_valid_memory = True
                self.ui_log("✅ [Memory] ChromaDB 재초기화 성공")
                return True
            except Exception as e:
                error_str = str(e).lower()
                if "lock" in error_str and attempt < max_retries - 1:
                    self.ui_log(f"   ⚠️ [Memory] 재시도 {attempt + 1}/{max_retries}: 락 오류 - 정리 시도...")
                    self._clear_chromadb_locks()
                    time.sleep(2)
                    continue
                else:
                    self.initialization_error = str(e)
                    self.ui_log(f"⚠️ [Memory] ChromaDB 재초기화 실패: {e}")
                    return False

        return False

    def _prepare_sql_table(self):
        """V25 앵커 테이블 생성"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS anchors (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP
            )
        """)
        self.conn.commit()

    def save_v20_anchor(self, key, data):
        """[V25] JSON 직렬화 저장"""
        try:
            serialized_data = json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)
            self.cursor.execute(
                "INSERT OR REPLACE INTO anchors (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, serialized_data)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.ui_log(f"❌ [DB Save Error] {key}: {e}")
            return False

    def load_v20_anchor(self, key):
        """[V25] JSON 역직렬화 복원"""
        try:
            row = self.cursor.execute("SELECT value FROM anchors WHERE key = ?", (key,)).fetchone()
            if row:
                try: return json.loads(row[0])
                except json.JSONDecodeError: return row[0]
            return None
        except Exception as e:
            self.ui_log(f"❌ [DB Load Error] {key}: {e}")
            return None

    def retrieve_high_res_context(self, query, current_ep, n_results=3):
        """[V44] JSON 쿼리 대응 고해상도 벡터 검색 및 맥락 인출 (안전 접근)"""
        # 1. [V44] 컬렉션 안전 접근 확인
        if not self._ensure_collection():
            # 메모리 없이도 시스템 동작 - 빈 컨텍스트 반환
            return ""

        # 2. 쿼리 데이터 정규화 (딕셔너리/리스트를 JSON 문자열로 변환)
        query_text = json.dumps(query, ensure_ascii=False) if isinstance(query, (dict, list)) else str(query)

        try:
            # 3. 벡터 DB 검색 실행 (현재 에피소드보다 이전의 데이터만 필터링)
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"episode": {"$lt": current_ep}}
            )

            # 4. 결과 데이터 추출
            # [V44] 빈 리스트 안전 체크 - results가 [[]] 대신 []를 반환할 수 있음
            docs_list = results.get('documents', [[]])
            docs = docs_list[0] if docs_list else []
            metas_list = results.get('metadatas', [[]])
            metas = metas_list[0] if metas_list else []

            # 검색 결과가 없는 경우 빈 문자열 즉시 반환
            if not docs:
                return ""

            # 5. 서사적 맥락 블록 구성 (800자 최적화 발췌)
            context_blocks = []
            for d, m in zip(docs, metas):
                ep_num = m.get('episode', '??')
                summary = m.get('summary', '요약 정보가 없는 기억입니다.')
                # V27 표준: 토큰 절약 및 핵심 맥락 전달을 위해 발췌 분량을 800자로 조절
                excerpt = d[:800].replace('\n', ' ').strip()
                
                block = (
                    f"### [제 {ep_num} 화의 기억]\n"
                    f"요약: {summary}\n"
                    f"본문 발췌: {excerpt}..."
                )
                context_blocks.append(block)

            # 6. 블록 간 줄바꿈을 포함하여 최종 맥락 반환
            return "\n\n".join(context_blocks)

        except Exception as e:
            # 검색 엔진 오류 시 시스템 중단 방지를 위해 로그 기록 후 빈 값 반환
            self.ui_log(f"⚠️ [Memory Retrieve Error] {e}")
            return ""

    def memorize_v20_episode(self, ep_num, text, summary, causal_links):
        """[V44] 에피소드 박제 및 시스템 상태 동기화 (안전 접근)"""
        if not self._ensure_collection():
            self.ui_log(f"⚠️ [Memory] 컬렉션 없음 - 제 {ep_num}화 벡터 저장 건너뜀")
            return False
        doc_id = f"ep_{ep_num:04d}"
        metadata = {
            "episode": ep_num, 
            "summary": summary[:500], 
            "causal_data": json.dumps(causal_links, ensure_ascii=False)[:500]
        }
        try:
            self.collection.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])
            if hasattr(self.context, 'db') and hasattr(self.context.db, 'update_sync_status'):
                self.context.db.update_sync_status(ep_num, 1)
            return True
        except Exception as e:
            self.ui_log(f"🚨 [Memory Error] 제 {ep_num} 화 주입 실패: {e}")
            return False

    def sync_v20_drafts(self, force_repair=False):
        """[V44] 청크 기반 지연을 포함한 대량 동기화 안정화 로직 (안전 접근)"""
        if not self._ensure_collection():
            self.ui_log("⚠️ [Memory] 컬렉션 없음 - 원고 동기화 건너뜀")
            return
        draft_files = sorted(list(self.context.paths.drafts.glob("*.txt")))
        
        # #### [V31.6] 청크 제어 변수 (Rate Limit 대응) ####
        chunk_counter = 0
        CHUNK_SIZE = 5 # 5개 파일마다 긴 휴식 적용

        for f_path in draft_files:
            if not f_path.name[:4].isdigit(): continue
            ep_num = int(f_path.name[:4])
            
            # DB에서 현재 동기화 상태 확인
            is_synced = self.context.db.get_sync_status(ep_num) if hasattr(self.context, 'db') else 0
            
            if (is_synced == 0) or force_repair:
                try:
                    content = f_path.read_text(encoding='utf-8')
                    first_line = content.split('\n')[0].strip()[:100]
                    
                    # 벡터 DB 주입 (API 호출 발생 지점)
                    self.collection.upsert(
                        ids=[f"ep_{ep_num:04d}"],
                        documents=[content],
                        metadatas=[{"episode": ep_num, "summary": f"[복구] {first_line}"}]
                    )
                    
                    # 성공 시 SQLite 상태 업데이트
                    if hasattr(self.context, 'db'): 
                        self.context.db.update_sync_status(ep_num, 1)
                    
                    # #### [V31.6] Throttling 실행: 실질적 API 호출 시에만 카운트 ####
                    chunk_counter += 1
                    if chunk_counter >= CHUNK_SIZE:
                        self.ui_log(f"⏳ [System] API 부하 방지 대기 중 (Chunk {CHUNK_SIZE} 완료)")
                        time.sleep(3.0) # 5개마다 3초 휴식
                        chunk_counter = 0
                    else:
                        time.sleep(0.5) # 파일 간 미세 지연

                except Exception as e:
                    self.ui_log(f"⚠️ [Sync Failed] 제 {ep_num} 화: {e}")

    def ui_log(self, msg):
        ui = getattr(self.context, 'ui', None)
        if ui and hasattr(ui, 'log'): ui.log(msg)
        else: print(f"[Memory] {msg}")

    def get_status(self) -> dict:
        """[V44] 메모리 엔진 상태 진단 정보 반환"""
        status = {
            "has_valid_memory": self.has_valid_memory,
            "collection_available": self.collection is not None,
            "sqlite_available": self.conn is not None,
            "initialization_error": self.initialization_error,
            "db_path": str(self.db_path) if self.db_path else None
        }

        # 컬렉션 통계 (가능한 경우)
        if self.collection:
            try:
                status["document_count"] = self.collection.count()
            except Exception:
                status["document_count"] = "unknown"

        return status

    def is_operational(self) -> bool:
        """[V44] 메모리 엔진이 작동 가능한지 확인"""
        return self.has_valid_memory and self.collection is not None

    def close(self):
        """[V44] 리소스 정리 및 연결 종료"""
        # SQLite 연결 종료
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
            self.cursor = None

        # ChromaDB 클라이언트 정리
        self.client = None
        self.collection = None
        self.has_valid_memory = False

    def __del__(self):
        """[V44] 소멸자에서 리소스 정리"""
        self.close()