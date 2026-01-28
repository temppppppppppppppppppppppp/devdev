import os
import time
import json
import sqlite3
import chromadb
from google import genai
from chromadb import EmbeddingFunction, Documents, Embeddings
from pathlib import Path
import numpy as np  # 👈 [Patch 3.1] 임포트를 최상단으로 이동하여 오버헤드 제거
import time

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
                    import time
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
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"⚠️ [Memory Quota] {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    # 기타 치명적 에러 발생 시 해당 텍스트 처리 중단
                    print(f"🚨 [Embedding Error] 치명적 오류: {e}")
                    break

            if not success:
                # 모든 재시도 실패 시 시스템 전체 중단을 방지하기 위해 제로 벡터(768차원) 주입
                # gemini-embedding-001 모델의 기본 출력 차원은 768입니다.
                embeddings.append([0.0] * 768) 

        return embeddings
class LongTermMemory:
    """[V25 Sovereign] JSON 무결성 및 시스템 동기화 통합 기억 엔진"""
    
    def __init__(self, project_context):
        self.context = project_context
        self.db_path = self.context.paths.memory / "long_term_anchor.db"
        api_key = os.getenv("GOOGLE_API_KEY")
        
        # 1. SQLite3 초기화 (JSON 앵커 및 상태 관리용)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._prepare_sql_table()

        # 2. ChromaDB 초기화 (벡터 검색용)
        try:
            vector_db_path = self.db_path.parent / "vector_db"
            self.client = chromadb.PersistentClient(path=str(vector_db_path))
            self.collection = self.client.get_or_create_collection(
                name="v20_sovereign_memory", 
                embedding_function=GoogleEmbeddingFunction(api_key)
            )
        except Exception as e:
            self.ui_log(f"🚨 [Memory] ChromaDB 연결 실패: {e}")
            self.collection = None

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
        """[V27] JSON 쿼리 대응 고해상도 벡터 검색 및 맥락 인출"""
        # 1. 컬렉션 로드 여부 확인
        if not self.collection: 
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
            docs = results.get('documents', [[]])[0]
            metas = results.get('metadatas', [[]])[0]

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
        """[V25] 에피소드 박제 및 시스템 상태 동기화"""
        if not self.collection: return False
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
        """[V31.6] 청크 기반 지연을 포함한 대량 동기화 안정화 로직"""
        if not self.collection: return
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