import sys
import os

# Windows에서 UTF-8 인코딩 강제 설정 (이모지 및 한글 출력 지원)
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        pass

import time
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dotenv import load_dotenv
load_dotenv(override=True)  # Slack 알림용 환경변수 먼저 로드
from rich.live import Live
from rich.panel import Panel
from google import genai
import re 
from modules.core.slack_bot import notifier # [V40] Slack 알림 추가 
from modules.core.system import StudioSystem
from modules.core.studio_visualizer import StudioVisualizer
from modules.core.memory_engine import LongTermMemory
from modules.domain.agents.analyst import Analyst
from modules.domain.agents.architect import Architect
from modules.domain.agents.writer import Writer
from modules.domain.agents.director import Director
from modules.domain.agents.manager import Manager
from modules.domain.agents.weaver import Weaver 
import random
from google.genai import types
import asyncio

# [V40 Enhanced] 중앙 상수 관리
from modules.core.constants import (
    GenreTypes, RetryLimits, BatchSizes, Thresholds, VolumeSettings,
    AIParameters, HUDKeys, NPCHUDKeys, FileExtensions, DirectoryNames,
    LogLevels, AuditEvents, Stages, PatternTypes, ErrorMessages,
    SuccessMessages, Emojis, RecoveryLimits, AIModels, WritingLimits
)




class SovereignApp:
    def __init__(self):
        load_dotenv(override=True)
        self.ui = StudioVisualizer()
        self.sys = StudioSystem(api_client=genai.Client(api_key=os.getenv("GOOGLE_API_KEY")))
        self.memory = None
        self.agents = {}
        self.current_project = None
        self.runtime_audit = []
        self.selected_genre = None  # [V40] 선택된 장르 정보
    
    def _safe_commit(self) -> bool:
        """
        [V40 Enhanced] 안전한 DB 커밋 래퍼 (동기 전용)

        Returns:
            bool: 커밋 성공 여부
        """
        if hasattr(self, 'current_project') and self.current_project and hasattr(self.current_project, 'db'):
            try:
                if self.current_project.db.conn.in_transaction:
                    self.current_project.db.conn.commit()
                    self._audit_event(AuditEvents.DB_COMMIT, SuccessMessages.DB_COMMIT_SUCCESS)
                    return True
                return True
            except Exception as e:
                self.ui.log(f"{Emojis.ERROR} [DB] {ErrorMessages.DB_COMMIT_FAILED}: {e}")
                self._audit_event(AuditEvents.DB_ROLLBACK, ErrorMessages.DB_COMMIT_FAILED, {"error": str(e)})
                try:
                    self.current_project.db.conn.rollback()
                    self.ui.log(f"↩️ [DB] 롤백 완료")
                except Exception as rollback_error:
                    self.ui.log(f"{Emojis.WARNING} [DB] 롤백도 실패: {rollback_error}")
                return False
        return False

    async def _safe_commit_async(self) -> bool:
        """
        [V40.1 Critical Fix] 비동기 컨텍스트에서 안전한 DB 커밋

        비동기 함수 내에서 DB 커밋을 호출할 때 스레드 안전성을 보장합니다.
        asyncio.to_thread를 사용하여 동기 커밋 로직을 별도 스레드에서 실행합니다.

        Returns:
            bool: 커밋 성공 여부
        """
        try:
            return await asyncio.to_thread(self._safe_commit)
        except Exception as e:
            self.ui.log(f"{Emojis.ERROR} [DB Async] 비동기 커밋 실패: {e}")
            self._audit_event("async_commit_error", "async commit failed", {"error": str(e)})
            return False

    def _emergency_shutdown(self) -> None:
        """
        [V40.1 Critical Fix] 긴급 시스템 종료 핸들러

        초기화 단계에서 치명적 오류 발생 시 리소스를 안전하게 정리합니다.
        - DB 연결 종료
        - 벡터 DB 연결 해제
        - 감사 로그 기록
        """
        self._audit_event("emergency_shutdown", "System emergency shutdown initiated")
        try:
            if hasattr(self, 'current_project') and self.current_project:
                if hasattr(self.current_project, 'db') and self.current_project.db:
                    try:
                        self.current_project.db.conn.close()
                        self.ui.log("🔌 [Shutdown] DB 연결 종료")
                    except Exception as db_err:
                        self.ui.log(f"{Emojis.WARNING} [Shutdown] DB 종료 중 오류: {db_err}")
            if hasattr(self, 'memory') and self.memory:
                try:
                    # ChromaDB 클라이언트 정리 (필요 시)
                    self.memory = None
                    self.ui.log("🔌 [Shutdown] 벡터 DB 연결 해제")
                except Exception as mem_err:
                    self.ui.log(f"{Emojis.WARNING} [Shutdown] 메모리 정리 중 오류: {mem_err}")
        except Exception as e:
            self.ui.log(f"{Emojis.ERROR} [Shutdown] 긴급 종료 중 예외: {e}")

    def boot(self):
        self.ui.title("V40 SOVEREIGN COCKPIT", "Multi-Genre Production Factory")
        
        # [V40] 장르 선택 우선
        self.selected_genre = self._select_genre()
        
        project_name = self._select_project()
        self.sys.boot_v20_project(project_name)
        self.current_project = self.sys.project
        
        # [V40] 장르 정보를 프로젝트에 주입
        self.current_project.genre = self.selected_genre
        
        # [V40] 기존 프로젝트의 장르 정보 확인 및 동기화
        if hasattr(self.current_project, 'db'):
            stored_genre = self.current_project.db.load_anchor('genre_info')
            if stored_genre:
                # 기존 프로젝트의 장르와 선택한 장르가 다르면 경고
                if stored_genre.get('type') != self.selected_genre['type']:
                    self.ui.log(f"⚠️ [Warning] 프로젝트 장르 불일치 감지!")
                    self.ui.log(f"   저장된 장르: {stored_genre.get('name', '알 수 없음')}")
                    self.ui.log(f"   선택한 장르: {self.selected_genre['name']}")

                    choice = input("\n계속하시겠습니까? (y/n): ").strip().lower()
                    if choice != 'y':
                        self.ui.log("🛑 시스템을 종료합니다.")
                        # [V40.1 Critical Fix] 안전한 종료 처리
                        self._emergency_shutdown()
                        sys.exit(0)
            else:
                # 장르 정보가 없으면 현재 선택한 장르로 저장
                self.current_project.db.save_anchor('genre_info', self.selected_genre)
                self.ui.log(f"💾 프로젝트 장르 정보 저장: {self.selected_genre['name']}")
        
        # [V40] 장르별 HUD 매니저 초기화
        from modules.core.genre_hud_manager import create_hud_manager
        self.sys.hud = create_hud_manager(self.selected_genre['type'], self.current_project)
        self.ui.log(f"✅ [{self.selected_genre['name']}] HUD 시스템 초기화 완료")
        
        # [V40] 장르별 GenreGuard 초기화
        from modules.core.genre_guards import create_genre_guard
        self.sys.guard = create_genre_guard(self.selected_genre['type'])
        self.current_project.guard = self.sys.guard  # 프로젝트 컨텍스트에 가드 주입
        self.ui.log(f"✅ [{self.selected_genre['name']}] Guard 시스템 초기화 완료")
        
        # [V27.5 수정 적용] 반환값을 체크하여 부팅 여부 결정
        if not self._check_vector_db_lock(project_name):
            self.ui.log("🛑 [System] 치명적 데이터 결함으로 인해 기동을 중지합니다.")
            return # 또는 sys.exit()
            
        self.memory = LongTermMemory(self.current_project) 
        
        # [V38 패치] 에이전트 초기화 검증
        if not self._attach_agents():
            self.ui.log("🛑 [System] 에이전트 초기화 실패로 인해 기동을 중지합니다.")
            return
        
        self._run_main_process()

    def _ignite_quad_cache_system(self):
        """[V31] 4중 캐시 시스템 (Writer, Architect, Analyst, Weaver)"""
        from google.genai import types
        import json

        self.ui.log("🧬 [System] V31 3중 캐싱 시스템(Triple-Cache) 동기화 중...")

        # 0. 설정된 모델명 확보 (ConfigManager 기반)
        config = self.sys.get_v20_orchestrator_config()["models"]
        # API 호출을 위해 'models/' 접두사 확인
        def fix_model_id(mid): return f"models/{mid}" if not mid.startswith("models/") else mid

        # 1. 파일 데이터 로드 및 조립
        # (A) Writer
        writer_rules_path = self.current_project.paths.config / "prompts" / "writer_rules.json"
        style_seed_path = self.current_project.paths.config / "cash" / "style_seeds_final.txt"
        writer_context = "[SYSTEM: ABSOLUTE WRITER MANIFESTO]\n"
        if writer_rules_path.exists():
            w_data = json.loads(writer_rules_path.read_text(encoding='utf-8'))
            writer_context += "\n".join(w_data.get("common_manifesto", [])) + "\n"
        if style_seed_path.exists():
            writer_context += f"### [STYLE SEEDS]\n{style_seed_path.read_text(encoding='utf-8')}"

        # (B) Architect
        arch_rules_path = self.current_project.paths.config / "prompts" / "architect_rules.json"
        architect_context = "[SYSTEM: ARCHITECT STRUCTURAL RULES]\n"
        if arch_rules_path.exists():
            architect_context += arch_rules_path.read_text(encoding='utf-8')

        # (C) Analyst
        analyst_lib_path = self.current_project.paths.config / "prompts" / "analyst_libraries.json"
        analyst_context = "[SYSTEM: NARRATIVE STRATEGY LIBRARIES]\n"
        if analyst_lib_path.exists():
            analyst_context += analyst_lib_path.read_text(encoding='utf-8')

        # [D] Weaver Cache 추가
        weaver_rules_path = self.current_project.paths.config / "prompts" / "weaver_rules.json"
        weaver_context = "[SYSTEM: GRAND WEAVER MANIFESTO]\n"
        if weaver_rules_path.exists():
            weaver_context += weaver_rules_path.read_text(encoding='utf-8')



        # 2. 캐시 상태 점검 및 생성
        cache_info = self.current_project.db.load_anchor("sys_caches", default={})
        
        # [A] Writer Cache
        if not self._is_cache_alive(cache_info.get("writer_cache")):
            # 1024 토큰 체크 (한글/특수문자 포함 안전권으로 약 1,500글자 기준)
            context_str = str(writer_context)
            if len(context_str) < 1500:
                self.ui.log(f"   ⚠️ [System] 데이터량이 적어 캐싱을 건너뜁니다. ({len(context_str)} chars)")
                cache_info["writer_cache"] = None
            else:
                self.ui.log("   ⚡ [Writer] 신규 캐시 생성 중...")
                try:
                    w_cache = self.sys.api_client.caches.create(
                        model=fix_model_id(config["writer"]),
                        config=types.CreateCachedContentConfig(
                            display_name="WRITER_V31", system_instruction="소설가",
                            contents=[writer_context], ttl="86400s"
                        )
                    )
                    cache_info["writer_cache"] = w_cache.name
                except Exception as e:
                    self.ui.log(f"   ❌ 캐시 생성 실패: {e}")
                    cache_info["writer_cache"] = None





        # [B] Architect Cache (수정됨)
        if not self._is_cache_alive(cache_info.get("architect_cache")):
            context_str = str(architect_context)
            if len(context_str) < 1500: # 1024 토큰 가드 
                self.ui.log(f"   ⚠️ [System] Architect 데이터량이 적어 캐싱을 건너뜁니다. ({len(context_str)} chars)")
                cache_info["architect_cache"] = None
            else:
                self.ui.log("   ⚡ [Architect] 신규 캐시 생성 중...")
                try:
                    a_cache = self.sys.api_client.caches.create(
                        model=fix_model_id(config["architect"]),
                        config=types.CreateCachedContentConfig(
                            display_name="ARCHITECT_V31", system_instruction="아키텍트",
                            contents=[architect_context], ttl="86400s"
                        )
                    )
                    cache_info["architect_cache"] = a_cache.name
                except Exception as e:
                    self.ui.log(f"   ❌ Architect 캐시 생성 실패: {e}")
                    cache_info["architect_cache"] = None

        # [C] Analyst Cache (수정됨)
        if not self._is_cache_alive(cache_info.get("analyst_cache")):
            context_str = str(analyst_context)
            if len(context_str) < 1500:
                self.ui.log(f"   ⚠️ [System] Analyst 데이터량이 적어 캐싱을 건너뜁니다. ({len(context_str)} chars)")
                cache_info["analyst_cache"] = None
            else:
                self.ui.log("   ⚡ [Analyst] 신규 캐시 생성 중...")
                try:
                    ana_cache = self.sys.api_client.caches.create(
                        model=fix_model_id(config["analyst"]),
                        config=types.CreateCachedContentConfig(
                            display_name="ANALYST_V31", system_instruction="전략가",
                            contents=[analyst_context], ttl="86400s"
                        )
                    )
                    cache_info["analyst_cache"] = ana_cache.name
                except Exception as e:
                    self.ui.log(f"   ❌ Analyst 캐시 생성 실패: {e}")
                    cache_info["analyst_cache"] = None

        # [D] Weaver Cache (수정됨)
        if not self._is_cache_alive(cache_info.get("weaver_cache")):
            context_str = str(weaver_context)
            if len(context_str) < 1500:
                self.ui.log(f"   ⚠️ [System] Weaver 데이터량이 적어 캐싱을 건너뜁니다. ({len(context_str)} chars)")
                cache_info["weaver_cache"] = None
            else:
                self.ui.log("   ⚡ [Weaver] 신규 복선 캐시 생성 중...")
                try:
                    # [V44 Fix] config["manager"] → config["weaver"] 수정
                    w_cache = self.sys.api_client.caches.create(
                        model=fix_model_id(config.get("weaver", config.get("manager", "gemini-2.0-flash"))),
                        config=types.CreateCachedContentConfig(
                            display_name="WEAVER_V31", system_instruction="복선 설계자",
                            contents=[weaver_context], ttl="86400s"
                        )
                    )
                    cache_info["weaver_cache"] = w_cache.name
                except Exception as e:
                    self.ui.log(f"   ❌ Weaver 캐시 생성 실패: {e}")
                    cache_info["weaver_cache"] = None

        # [V40.1 Critical Fix] 캐시 정보를 DB에 영속화 (재시작 시 캐시 재사용 보장)
        try:
            self.current_project.db.save_anchor("sys_caches", cache_info)
            self._safe_commit()
            self.ui.log(f"{Emojis.SAVE} [System] 캐시 정보 DB 저장 완료")
            self._audit_event(AuditEvents.CACHE_CREATED, SuccessMessages.CACHE_CREATED, {
                "writer": bool(cache_info.get("writer_cache")),
                "architect": bool(cache_info.get("architect_cache")),
                "analyst": bool(cache_info.get("analyst_cache")),
                "weaver": bool(cache_info.get("weaver_cache"))
            })
        except Exception as save_err:
            self.ui.log(f"{Emojis.ERROR} [System] 캐시 정보 DB 저장 실패: {save_err}")
            self._audit_event("cache_save_error", ErrorMessages.DB_COMMIT_FAILED, {"error": str(save_err)})

        # [V40 Fix] 생성된 캐시를 에이전트에 주입
        if hasattr(self, 'agents') and self.agents:
            if cache_info.get("writer_cache"):
                self.agents['writer'].cache_name = cache_info["writer_cache"]
                self.ui.log("   ✅ Writer 캐시 주입 완료")
            if cache_info.get("architect_cache"):
                self.agents['architect'].cache_name = cache_info["architect_cache"]
                self.ui.log("   ✅ Architect 캐시 주입 완료")
            if cache_info.get("analyst_cache"):
                self.agents['analyst'].cache_name = cache_info["analyst_cache"]
                self.ui.log("   ✅ Analyst 캐시 주입 완료")
            if cache_info.get("weaver_cache"):
                self.agents['weaver'].cache_name = cache_info["weaver_cache"]
                self.ui.log("   ✅ Weaver 캐시 주입 완료")

    def _is_cache_alive(self, cache_name):
        if not cache_name: return False
        try:
            self.sys.api_client.caches.get(name=cache_name)
            return True
        except Exception:  # API 예외 종류가 다양하므로 Exception 유지
            return False

    def _check_vector_db_lock(self, project_name: str) -> bool:
        """
        [V35.6 S-Grade] 벡터 DB 안정화 (저널 보존형 LOCK 해제)

        ChromaDB의 잔류 잠금 파일을 제거하고 데이터 무결성을 검증합니다.

        Args:
            project_name: 프로젝트 이름

        Returns:
            bool: 무결성 검증 통과 여부 (True=정상, False=손상 감지)
        """
        memory_path = Path(f"projects/{project_name}/chroma_db")
        if not memory_path.exists(): return True

        # 1. 단순 잠금 및 공유 메모리 찌꺼기만 선별 삭제
        # wal 파일은 삭제 시 데이터 유실 위험이 있으므로, 본체 파일 검사로 대체합니다.
        lock_files = ["LOCK", "chroma.sqlite3-shm"]
        for lock_name in lock_files:
            f = memory_path / lock_name
            if f.exists():
                try:
                    os.remove(f)
                    self.ui.log(f"🧹 [System] 잔류 잠금 파일({lock_name})을 제거했습니다.")
                except Exception as e:
                    self.ui.log(f"⚠️ [System] {lock_name} 제거 실패: {e}")

        # 2. 데이터 오염(0KB) 및 본체 무결성 점검
        # .sqlite3 본체나 .wal 파일 중 하나라도 0KB라면 인과율이 깨진 것으로 간주합니다.
        all_db_files = list(memory_path.rglob("*.sqlite3*")) 
        for db_f in all_db_files:
            if db_f.exists() and db_f.stat().st_size == 0:
                self.ui.log(f"🚨 [Critical] 벡터 데이터 파일({db_f.name}) 손상 감지.")
                self.ui.log("👉 [해결] 'Phase 0'를 실행하여 성경과 원고를 재이식하십시오.")
                return False 

        self.ui.log("✅ [System] 벡터 DB 엔진 무결성 점검 완료.")
        return True

    def _ui_select_bible(self) -> Optional[str]:
        """
        bible 폴더에서 성경(Lore) JSON 파일 선택

        사용자에게 bible 폴더 내 JSON 파일 목록을 보여주고 선택을 받습니다.

        Returns:
            Optional[str]: 선택된 파일명 (없으면 None)
        """
        bible_dir = Path("bible")
        files = sorted(list(bible_dir.glob("*.json")))
        if not files:
            print("❌ bible 폴더에 JSON 파일이 없습니다.")
            return None
        
        print("\n📚 [Bible Selection] 사용할 성경(Lore)을 선택하십시오:")
        for i, f in enumerate(files, 1):
            print(f"   {i}. {f.name}")
        
        idx = (self._get_int_input(f"\n👉 Choice (1-{len(files)}): ", default=1, min_val=1, max_val=len(files)) or 1) - 1
        return files[idx].name if 0 <= idx < len(files) else files[0].name

    def _ui_select_treatment(self) -> Optional[str]:
        """
        [V27 Standard] treatments 폴더에서 설계도 JSON 선택 및 시스템 등록

        사용자에게 treatments 폴더 내 JSON 파일 목록을 보여주고 선택을 받습니다.
        선택된 파일은 프로젝트의 treatment_path 속성에 등록됩니다.

        Returns:
            Optional[str]: 선택된 파일명 (없으면 None)
        """
        treat_dir = Path("treatments")
        if not treat_dir.exists(): 
            treat_dir.mkdir(parents=True, exist_ok=True)
            
        files = sorted(list(treat_dir.glob("*.json")))
        if not files:
            self.ui.log("❌ treatments 폴더에 JSON 파일이 없습니다.")
            return None
        
        print("\n🧬 [Roadmap Selection] V25 상세 설계도(JSON)를 선택하십시오:")
        for i, f in enumerate(files, 1):
            # 현재 로드된 파일인지 시각적으로 표시
            is_current = hasattr(self.current_project, 'treatment_path') and self.current_project.treatment_path == f
            print(f"   {i}. {f.name} {'⭐ (Current)' if is_current else ''}")
        
        try:
            idx = (self._get_int_input(f"\n👉 Choice (1-{len(files)}, 미입력 시 1번): ", default=1, min_val=1, max_val=len(files)) or 1) - 1
            
            if 0 <= idx < len(files):
                selected_file = files[idx]
                # [무결성 포인트] 선택과 동시에 프로젝트 경로 속성 업데이트
                self.current_project.treatment_path = selected_file
                self.ui.log(f"✅ 로드맵 선택 완료: {selected_file.name}")
                return selected_file.name # 파일명 문자열만 반환 (Phase 0 규격 준수)
            else:
                # [V44] 빈 리스트 안전 체크
                return files[0].name if files else None

        except Exception as e:
            self.ui.log(f"⚠️ 선택 중 오류 발생: {e}")
            return files[0].name if files else None

    def _attach_agents(self) -> bool:
        """
        [V38 패치] 방어적 에이전트 초기화

        시스템에 필요한 모든 AI 에이전트(Analyst, Architect, Writer, Director,
        Manager, Weaver)를 초기화합니다.

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            config = self.sys.get_v20_orchestrator_config()
            models = config.get("models", {})
            
            if not models:
                self.ui.log("🚨 [Critical] 모델 설정을 불러올 수 없습니다.")
                return False
            
            default_model = "gemini-2.0-flash"
            
            self.agents = {
                'analyst': Analyst(self.current_project, self.sys.api_client, model_tier=models.get("analyst", default_model)),
                'architect': Architect(self.current_project, self.sys.api_client, model_tier=models.get("architect", default_model)),
                'writer': Writer(self.current_project, self.sys.api_client, model_tier=models.get("writer", default_model)),
                'director': Director(self.current_project, self.sys.api_client, model_tier=models.get("director", default_model)),
                'manager': Manager(self.current_project, self.sys.api_client, model_tier=models.get("manager", default_model)),
                # [V45 Fix] weaver는 manager가 아닌 weaver 모델 사용 (fallback: manager)
                'weaver': Weaver(self.current_project, self.sys.api_client, model_tier=models.get("weaver", models.get("manager", default_model))),
            }
            
            # 초기화 검증
            for name, agent in self.agents.items():
                if not hasattr(agent, 'ask'):
                    self.ui.log(f"🚨 [Critical] {name} 에이전트 초기화 실패")
                    return False

            # [V43] Director에 장르 및 V0128 설정 주입
            if self.selected_genre:
                genre_type = self.selected_genre.get('type', 'wuxia')
                self.agents['director'].set_genre(genre_type)
                self.ui.log(f"   🎭 Director 장르 설정: {genre_type}")

            # V0128 검증 시스템 활성화 여부 확인
            # [V44 Fix] settings 변수 안전하게 로드
            try:
                settings_path = self.current_project.paths.config / "settings.json"
                if settings_path.exists():
                    import json
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                else:
                    settings = {}
            except Exception:
                settings = {}

            validation_config = settings.get('validation', {})
            if validation_config.get('use_v0128', False):
                self.agents['director'].set_v0128_enabled(True)
                self.ui.log("   ✅ V0128 검증 시스템 활성화")

            self.ui.log("✅ [System] 모든 에이전트 안전하게 초기화 완료")
            return True
            
        except Exception as e:
            self.ui.log(f"🚨 [Critical] 에이전트 초기화 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _run_main_process(self) -> None:
        """
        [V38 패치] 메인 생산 라인 통제 및 강화된 에러 핸들링

        5단계 생산 파이프라인의 메인 메뉴를 표시하고 사용자 선택에 따라
        각 Stage를 실행합니다.

        Stages:
            - Phase 0: Bible Recovery & DNA Sync
            - Stage 1: Volume Strategy
            - Stage 2: Arc Tactical Design
            - Stage 3: Episode Blueprinting
            - Stage 4: Sovereign Production
        """
        # [V40 Safety] 장르 선택 검증
        if not self.selected_genre:
            self.ui.log("🚨 [Critical] 장르가 선택되지 않았습니다. 시스템을 종료합니다.")
            return
        
        try:
            while True:
                self.ui.console.clear()
                # 1. UI 타이틀 업데이트 (V40 장르 반영)
                genre_label = self.selected_genre['name']
                self.ui.title("V40 SOVEREIGN PRODUCTION", f"Genre: {genre_label} | Project: {self.current_project.name}")
                
                # 2. 상태 체크 (DB Anchors 기반의 무결성 확인)
                # 이 함수는 self.current_project.db의 'bible', 'volumes', 'arcs' 키를 체크해야 함
                status = self.sys.check_v20_readiness() 
                
                # 3. 메뉴 구성 (V41 유동 아크 + 스킵 옵션)
                vol_status = '✅' if status.get('Stage 1 (Volumes)', False) else '⏭️ 스킵가능'
                menu = {
                    "0": f"Phase 0: Bible Recovery & DNA Sync [{'✅' if status.get('Stage 0 (Bible)', False) else '❌'}]",
                    "1": f"Stage 1: Volume Strategy (선택) [{vol_status}]",
                    "2": f"Stage 2: Arc Tactical Design (유동) [{'✅' if status.get('Stage 2 (Arcs)', False) else '❌'}]",
                    "3": "📐 Stage 3: Episode Blueprinting (Batch Design)", # 분리됨
                    "4": "🚀 Stage 4: Sovereign Production (Writing)",     # 분리됨
                    "5": "Exit",
                    "44": "⏪ [ROLLBACK] Stage 4 회차별 롤백 (Episode Rewind)",
                    "77": "🧹 [WIPE] 원고 생산 기록만 삭제 (Stage 4 초기화)",
                    "88": "🔥 [RESET] Stage 2 (Arcs) 초기화",
                    "99": "⏪ Stage 2 정밀 되감기 (Selective Rewind)"
                }
                
                choice = self.ui.menu(menu)
                # 4. 공정 디스패치
                if choice == "0": 
                    self._phase_0_recovery()
                elif choice == "1": 
                    self._stage_1_volumes()
                elif choice == "2":
                    if not status.get('Stage 1 (Volumes)', False):
                        self.ui.log("⚠️ Stage 1 (Volume Strategy)이 완료되지 않았습니다.")
                        self.ui.log("💡 Volume 전략 없이도 Arc 설계를 진행할 수 있습니다.")
                        skip_confirm = input("   Stage 1을 건너뛰고 진행하시겠습니까? (y/N): ").strip().lower()
                        if skip_confirm != 'y':
                            continue
                    self._stage_2_arcs()
                elif choice == "3": 
                    # 📐 [Stage 3] 설계도만 일괄 생성 (Architect 전용)
                    self._stage_3_batch_blueprinting()
                elif choice == "4":
                    # 캐시는 _stage_4_sovereign_writing() 내부에서 호출됨 (중복 제거)
                    self._stage_4_sovereign_writing(limit_mode=True)
                elif choice == "5":
                    self._shutdown_app()
                    break
                elif choice == "44":
                    self._rollback_episode()
                elif choice == "77":
                    self._wipe_production_data()
                elif choice == "88":
                    self._reset_stage_2()
                elif choice == "99":
                    self._rewind_stage_2()
        
        except KeyboardInterrupt:
            # Ctrl+C 입력 시에도 안전하게 셧다운 함수를 거치도록 함
            self._shutdown_app()
            sys.exit(0)
        
        except Exception as e:
            self.ui.log(f"🚨 [Critical Error] 시스템 오류 발생: {e}")
            
            # 에러 스택 저장
            import traceback
            error_log = self.current_project.paths.root / "logs" / "error.log"
            error_log.parent.mkdir(exist_ok=True)
            
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(traceback.format_exc())
            
            self.ui.log(f"📝 에러 로그 저장: {error_log}")
            
            # 안전한 종료 시도
            try:
                self._shutdown_app()
            except Exception:  # 종료 시 모든 예외 무시
                pass
            
            sys.exit(1)

    # SovereignApp 클래스 내부에 추가할 메서드
    # [수정] main_a.py / SovereignApp 클래스 내부 메서드




    def _shutdown_app(self):
        """[V27 Safe Shutdown] 앱 종료 시에만 DB 연결을 완전히 해제"""
        print("\n🛑 [System] 시스템 종료 시퀀스 가동...")
        
        # 1. 현재 메모리의 성경 데이터 최종 저장
        if hasattr(self.current_project, 'master_bible'):
            self.current_project.save_v20_anchor("bible", self.current_project.master_bible)
        
        # [V40] 장르 정보 저장
        if self.selected_genre and hasattr(self.current_project, 'db'):
            self.current_project.db.save_anchor('genre_info', self.selected_genre)
        
        # 2. DB 연결 종료 (이 시점에 close를 수행)
        # [V44] try-finally로 안전한 연결 종료 보장
        if self.current_project and hasattr(self.current_project, 'db') and self.current_project.db:
            db_conn = self.current_project.db.conn
            if db_conn:
                try:
                    db_conn.commit()
                    self.ui.log("[System] DB 커밋 완료")
                except Exception as e:
                    print(f"종료 중 DB 커밋 오류: {e}")
                finally:
                    try:
                        db_conn.close()
                        self.ui.log("[System] DB 연결 안전하게 해제됨")
                    except Exception as close_err:
                        print(f"DB close 오류: {close_err}")
            
    def _phase_0_recovery(self):
        print("\n⚙️ Phase 0: S-Grade 데이터 주권 동기화 가동...")
        
        # [V40] 장르 정보 표시
        if self.selected_genre:
            print(f"📌 현재 장르: {self.selected_genre['name']} ({self.selected_genre['type']})")
        
        # 1. 파일 선택 (Bible & Treatment)
        bible_file = self._ui_select_bible()
        treatment_file = self._ui_select_treatment()

        if not bible_file or not treatment_file:
            print("❌ 파일 선택이 취소되어 중단합니다.")
            return

        # 2. [필수] 50개 설계도 DNA 강제 이식 (원고 유무 상관없이 무조건 수행)
        # 이 함수가 실행되면 AI를 안 거치고 50개 블록이 DB에 100% 들어갑니다.
        dna_success = self.current_project.force_sync_v25_dna(bible_file, treatment_file)

        if dna_success:
            # 3. [선택] 기존 원고 유무 확인 및 자동 동기화
            draft_path = self.current_project.paths.drafts
            existing_drafts = list(draft_path.glob("*.txt"))

            if existing_drafts:
                print(f"📂 [Detect] 기존 원고 {len(existing_drafts)}건 발견. 역사 이식을 시작합니다...")
                # AI 안 거치고 직접 원고를 DB와 벡터 DB에 박제하는 함수 호출
                try:
                    sync_result = self.current_project.sync_existing_manuscripts(self.memory)
                    if sync_result:
                        print("✅ [History] 기존 원고의 역사가 모두 시스템에 안착되었습니다.")
                    else:
                        print("⚠️ [Warning] 일부 원고 동기화 실패. 로그를 확인하세요.")
                except Exception as sync_err:
                    print(f"🚨 [Error] 원고 동기화 중 오류 발생: {sync_err}")
                    self._audit_event("sync_error", "sync_existing_manuscripts failed", {
                        "error": str(sync_err),
                        "draft_count": len(existing_drafts)
                    })
                    print("⚠️ [Fallback] 원고 동기화를 건너뛰고 계속 진행합니다.")
            else:
                print("🆕 [New Project] 기존 원고가 없습니다. 신규 프로젝트로 기동합니다.")

            # 4. 최종 데이터 리로드
            self.current_project._load_from_db()
            print(f"✨ [Success] 설계도(50개)와 원고 역사가 무결하게 통합되었습니다.")
        
        input("\n[Enter] 메뉴로 돌아가기")

    def _stage_1_volumes(self):
        """[Stage 1] 아크 기반 권별 고해상도 전략 설계 (V41 스킵 옵션 추가)"""
        self.ui.log("📜 [Stage 1] 권별 고해상도 순차 설계 (V41 유동 아크)")

        # [V41 Patch] 스킵 옵션 제공
        self.ui.log("💡 Stage 1은 선택 사항입니다. 스킵해도 Stage 2 진행이 가능합니다.")
        skip_choice = input("   [1] 진행  [2] 스킵 (기본: 1): ").strip()
        if skip_choice == '2':
            self.ui.log("⏭️ Stage 1을 건너뜁니다. Stage 2에서 기본값으로 진행됩니다.")
            input("\n[Enter] 메뉴로 돌아가기")
            return

        # [V38 패치] 안전한 커밋으로 변경
        self._safe_commit()

        # [V38 패치] 안전한 데이터 추출 [V44 강화: None 체크]
        if not self.current_project or not hasattr(self.current_project, 'master_bible'):
            self.ui.log("❌ 프로젝트가 로드되지 않았습니다.")
            input("\n[Enter] 메뉴로 돌아가기")
            return
        master_bible = self.current_project.master_bible or {}
        bible_root = master_bible.get('MasterBible', master_bible) if isinstance(master_bible, dict) else {}
        arcs_source = bible_root.get('plot_roadmap', []) if isinstance(bible_root, dict) else []

        # [V43 패치] plot_roadmap 복구 메커니즘
        if not arcs_source:
            self.ui.log("⚠️ [Recovery] 메모리 내 로드맵이 없습니다. DB에서 재로드를 시도합니다...")
            try:
                # DB 앵커에서 직접 로드 시도
                self.current_project._load_from_db()
                master_bible = self.current_project.master_bible or {}
                bible_root = master_bible.get('MasterBible', master_bible) if isinstance(master_bible, dict) else {}
                arcs_source = bible_root.get('plot_roadmap', []) if isinstance(bible_root, dict) else []

                if arcs_source:
                    self.ui.log(f"✅ [Recovery] DB에서 {len(arcs_source)}개 아크 복구 성공!")
            except Exception as reload_err:
                self.ui.log(f"🚨 [Recovery Failed] DB 재로드 실패: {reload_err}")
                self._audit_event("recovery_failed", "plot_roadmap reload failed", {"error": str(reload_err)})

        if not arcs_source:
            self.ui.log("❌ 에러: 성경 내 로드맵 데이터가 없습니다. Phase 0을 다시 실행하세요.")
            input("\n[Enter] 메뉴로 돌아가기")
            return

        # [V41 Patch] 아크 총량 유동화 - plot_roadmap 길이에 따라 권 수 자동 계산
        total_arcs = len(arcs_source)
        total_volumes = (total_arcs + VolumeSettings.ARCS_PER_VOLUME - 1) // VolumeSettings.ARCS_PER_VOLUME  # 올림 처리
        self.ui.log(f"📊 총 {total_arcs}개 아크 발견 → {total_volumes}권 분권 설계를 시작합니다.")

        final_volumes = []
        context_accumulator = "" # 이전 권의 요약본을 누적하여 서사적 일관성 유지
        # [V44] 안전한 중첩 dict 접근
        project_data = bible_root.get('ProjectData', {}) if isinstance(bible_root, dict) else {}
        project_data = project_data if isinstance(project_data, dict) else {}
        meta_info = json.dumps(project_data.get('MetaInfo', {}), ensure_ascii=False)

        # [V41 Patch] 유동적 권 수 순차 설계 루프
        arcs_per_vol = VolumeSettings.ARCS_PER_VOLUME
        for vol_idx in range(1, total_volumes + 1):
            start_idx = (vol_idx - 1) * arcs_per_vol
            end_idx = vol_idx * arcs_per_vol
            vol_arcs_chunk = arcs_source[start_idx:end_idx]

            if not vol_arcs_chunk:
                self.ui.log(f"⚠️ [Warning] {vol_idx}권에 해당하는 데이터가 부족합니다. 스킵합니다.")
                continue

            treatment_slice = json.dumps(vol_arcs_chunk, ensure_ascii=False, indent=2)
            passed = False
            

            # [V40 Enhanced] 밀도 확보를 위한 재시도 루프
            for attempt in range(RetryLimits.DIRECTOR_MAX_ATTEMPTS):
                self.ui.log(f"   {Emojis.BRAIN} 제 {vol_idx}권 전략 설계 중... (시도 {attempt+1}/{RetryLimits.DIRECTOR_MAX_ATTEMPTS})")

                # [안전성 패치] Analyst에게 슬라이싱된 데이터와 성경, 그리고 '누적된 앞 권 내용' 주입
                try:
                    vol_data = self.agents['analyst'].plan_single_volume_v20(
                        vol_idx,
                        self.current_project.master_bible,
                        treatment_slice,
                        context_accumulator,
                        meta_info
                    )
                except Exception as analyst_err:
                    self.ui.log(f"🚨 [Analyst Error] 제 {vol_idx}권 설계 중 에러: {analyst_err}")
                    self._audit_event("analyst_error", "plan_single_volume_v20 failed", {
                        "vol_no": vol_idx,
                        "error": str(analyst_err)
                    })
                    continue  # 재시도

                # [데이터 검증] vol_data가 유효한지 확인
                if not vol_data or not isinstance(vol_data, dict):
                    self.ui.log(f"🚨 [Analyst Error] 제 {vol_idx}권 설계 결과가 유효하지 않음: {type(vol_data)}")
                    self._audit_event("analyst_error", "invalid volume data", {
                        "vol_no": vol_idx,
                        "type": str(type(vol_data))
                    })
                    continue

                # V25 품질 기준: 전략 문서가 최소 2,500~3,000자 이상이어야 함
                raw_doc = vol_data.get('strategy_doc', '')
                if isinstance(raw_doc, dict): # 만약 AI가 객체로 줬다면 문자열로 변환
                    raw_doc = json.dumps(raw_doc, ensure_ascii=False)
                doc_len = len(raw_doc)
                if doc_len >= 2000: # 한글 기준 2500자면 충분한 고해상도
                    # [V39 패치 D] Volume 경계 검증 추가
                    boundary_check = self._validate_volume_boundaries(vol_data, vol_idx)
                    if boundary_check.get("status") == "REJECT":
                        self.ui.log(f"   🚨 [Boundary Violation] {boundary_check.get('reason')}")
                        self.ui.log(f"   📝 수정 요청: {boundary_check.get('feedback')}")
                        # [V39.1 패치] 경고 → 강제 재시도로 격상
                        self._audit_event("volume_boundary_violation", boundary_check.get("reason"), {
                            "vol_no": vol_idx,
                            "feedback": boundary_check.get("feedback")
                        })
                        continue  # 재시도 루프로 돌아감
                    
                    self.ui.log(f"   ✅ [Pass] {vol_idx}권 검수 완료 (분량: {doc_len}자)")
                    final_volumes.append(vol_data)
                    
                    # [중요] 다음 권 설계를 위해 현재 권의 요약을 누적
                    summary = vol_data.get('strategy_doc', '')[:500]
                    context_accumulator += f"\n[제 {vol_idx}권 요약]: {summary}..."
                    passed = True
                    break
                else:
                    self.ui.log(f"   ⚠️ [Low Density] 분량 부족({doc_len}/2000). 다시 설계합니다.")

            if not passed:
                self.ui.log(f"❌ [Critical] 제 {vol_idx}권 품질 미달로 공정 중단.")
                return

        # 3. 전체 데이터 DB 박제 및 메모리 동기화
        self.current_project.save_v20_anchor("volumes", final_volumes)
        self.current_project.volumes = final_volumes
        # [추가] 시각적 확인을 위해 표 출력 기능 유지
        if hasattr(self, '_show_volume_table'):
            self._show_volume_table(final_volumes)
        self.ui.log(f"✨ [Complete] {len(final_volumes)}권 대서사시 로드맵이 DB에 최종 안착되었습니다.")
        
        input("\n[Enter] 메뉴로 이동")



    
    def _get_max_episode_from_manuscripts(self):
        """기존 원고 파일에서 최대 에피소드 번호 추출"""
        try:
            draft_files = list(self.current_project.paths.drafts.glob("*.txt"))
            if not draft_files:
                return 0

            max_ep = 0
            for f in draft_files:
                # 파일명 앞 4자리가 숫자인지 확인
                if f.name[:4].isdigit():
                    ep_num = int(f.name[:4])
                    max_ep = max(max_ep, ep_num)

            return max_ep
        except Exception as e:
            self.ui.log(f"⚠️ [Manuscript Check] 원고 파일 확인 실패: {e}")
            return 0

    def _calculate_arc_from_episode(self, ep_num):
        """에피소드 번호로부터 Arc 번호 계산 (각 Arc는 10화)"""
        if ep_num <= 0:
            return 0
        # 1-10화 -> Arc 1, 11-20화 -> Arc 2, ...
        return (ep_num - 1) // 10 + 1


    def _stage_2_arcs(self):
        """[V35.5 S-Grade] 50개 아크 가변 페이싱 설계 (비동기 래퍼 적용)"""
        # [V44] 안전한 이벤트 루프 실행 (기존 루프 충돌 방지)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # 이미 이벤트 루프가 실행 중인 경우 (Jupyter, Streamlit 등)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._stage_2_arcs_async_logic())
                future.result()
        else:
            # 일반적인 경우
            asyncio.run(self._stage_2_arcs_async_logic())

    async def _stage_2_arcs_async_logic(self):
        """
        [V37 S-Grade: 260124 매니페스토] 
        0124 욕망 엔진(Desire Engine) 통합 파이프라인 완전판
        """
        ### [0124 핵심] 욕망 엔진 가동 로고 및 로그 출력
        self.ui.log("🎯 [Stage 2] 0124 매니페스토: 욕망 엔진 및 인과율 용접 공정 기동...")

        # 1. 기초 데이터 확보 및 무결성 점검
        if not self.current_project.master_bible:
            self.current_project.master_bible = self.current_project.db.load_anchor('bible')
        if not self.current_project.volumes:
            self.current_project.volumes = self.current_project.db.load_anchor('volumes')

        bible_data = self.current_project.master_bible
        # [V41 Patch] Stage 1 스킵 시 빈 volumes 안전 처리
        volumes_strategy = self.current_project.volumes or []
        if not volumes_strategy:
            self.ui.log("⚠️ [Notice] Volume 전략이 없습니다. 기본값으로 Arc 설계를 진행합니다.")
        bible_root = bible_data.get('MasterBible', bible_data)
        arcs_source = bible_root.get('plot_roadmap', [])

        # [V42] 주인공 이름 추출 (PROTAGONIST IDENTITY LOCK)
        protagonist_name = None
        try:
            hud = bible_root.get('MartialHUD', {})
            protag = hud.get('Protagonist', {})
            actual = protag.get('actual_truth', {})
            protagonist_name = actual.get('name')
            if protagonist_name:
                self.ui.log(f"🔒 [V42] 주인공 이름 락: {protagonist_name}")
        except Exception as e:
            self.ui.log(f"⚠️ [V42] 주인공 이름 추출 실패: {e}")
        
        ### [V38 패치] 안전한 북극성 추출
        project_data = bible_root.get('ProjectData', {})
        meta_info = project_data.get('MetaInfo', {}) if isinstance(project_data, dict) else {}
        grand_obj = meta_info.get('grand_objective', "천하제일") if isinstance(meta_info, dict) else "천하제일"

        all_refined_arcs = self.current_project.db.load_anchor('arcs') or []
        done_count = len(all_refined_arcs)
        total_count = len(arcs_source)

        # [V40.1 Smart Skip] 기존 원고가 있다면 해당 Arc까지 자동 건너뛰기
        # ⚠️ 주의: 원고가 있어도 Arc 데이터가 DB에 없으면 생성이 필요함
        existing_ms_max_ep = self._get_max_episode_from_manuscripts()
        if existing_ms_max_ep > 0:
            skip_arc_no = self._calculate_arc_from_episode(existing_ms_max_ep)
            # Arc가 실제로 DB에 있을 때만 건너뛰기 (안전장치)
            if skip_arc_no <= done_count:
                # 이미 Arc가 있으면 정상 진행
                pass
            elif skip_arc_no > done_count:
                # Arc가 없으면 경고만 하고 정상 진행
                self.ui.log(f"📂 [Manuscript Detected] 기존 원고 {existing_ms_max_ep}화까지 발견")
                self.ui.log(f"⚠️  [Warning] Arc {skip_arc_no}까지 필요하지만 Arc {done_count}까지만 DB에 존재합니다.")
                self.ui.log(f"💡 [Info] Arc {done_count + 1}부터 설계를 시작합니다. (원고와 Arc 동기화 필요)")
                # done_count는 변경하지 않음 (실제 DB 상태 유지)

        if done_count >= total_count:
            self.ui.log("✅ 모든 아크 설계가 이미 완료되었습니다.")
            return

        ### [UI 세이프티 가드 복구] 사용자 경험 및 인과율 안정성 확보
        self.ui.log(f"📊 현재 설계 완료: {done_count} / {total_count} 아크")
        self.ui.log("💡 Tip: 인과율 정밀 용접을 위해 1회 10개(2개 배치) 이내 진행을 권장합니다.")
        
        default_limit = min(done_count + 5, total_count)
        target_limit = self._get_int_input(
            f"👉 몇 번 아크까지 설계하시겠습니까? (현재 {done_count + 1} ~ 최대 {total_count}): ",
            default=default_limit,
            min_val=done_count + 1,
            max_val=total_count
        )
        target_limit = max(done_count + 1, min(target_limit, total_count))

        sem = asyncio.Semaphore(5)
        full_roadmap_str = json.dumps(arcs_source, ensure_ascii=False)

        # 2. 배치(Batch) 처리 루프 시작
        for batch_start in range(done_count, target_limit, 5):
            batch_end = min(batch_start + 5, target_limit)
            self.ui.log(f"📦 [Batch] {batch_start + 1}~{batch_end}번 구간 욕망 수혈 공정 가동...")

            # [수혈 맥락 준비]
            last_refined_context = "서사 시작점"
            if all_refined_arcs:
                last_arc = all_refined_arcs[-1]
                last_refined_context = (
                    f"[직전 아크 {last_arc.get('arc_no')} 결말 상태]:\n"
                    f"- 물리적 위치: {last_arc.get('joint_docs', {}).get('final_location', '알 수 없음')}\n"
                    f"- 핵심 요약: {last_arc.get('tactical_doc', '')[:400]}..."
                )

            # A. [병렬 농축 단계] (비동기 처리)
            async def throttled_enrich(idx):
                async with sem:
                    prev_b = arcs_source[idx-1] if idx > 0 else None
                    curr_b = arcs_source[idx]
                    
                    # [V39 패치 A] 미래 블록 격리: 제목만 전달하여 내용 오염 차단
                    next_b_safe = {
                        "block_id": arcs_source[idx+1].get("block_id", f"Block {idx+2}"),
                        "title": arcs_source[idx+1].get("title", "미정")
                    } if idx < total_count-1 else {"title": "최종 블록"}
                    
                    return await self.agents['analyst'].enrich_raw_block_async(
                        curr_b, prev_b, next_b_safe, [],  # 👈 안전화된 next_b
                        transfused_history=last_refined_context
                    )

            enrichment_tasks = [throttled_enrich(i) for i in range(batch_start, batch_end)]
            enriched_batch = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

            # [안전성 패치] 실패한 항목에 대한 재시도 메커니즘
            sanitized_batch = []
            failed_indices = []
            for idx, item in enumerate(enriched_batch):
                if isinstance(item, Exception):
                    self.ui.log(f"⚠️ [Enrich] 병렬 농축 실패 (idx={batch_start + idx}): {item}")
                    self._audit_event("enrich_error", "batch enrich failed", {
                        "error": str(item),
                        "arc_idx": batch_start + idx
                    })
                    failed_indices.append(batch_start + idx)
                    continue
                # [데이터 검증] 유효한 딕셔너리인지 확인
                if not isinstance(item, dict):
                    self.ui.log(f"⚠️ [Enrich] 잘못된 데이터 타입 (idx={batch_start + idx}): {type(item)}")
                    failed_indices.append(batch_start + idx)
                    continue
                sanitized_batch.append(item)

            enriched_batch = sanitized_batch

            # [V40.1 Critical Fix] 복구 시도 - 원래 인덱스 위치 보존
            if failed_indices and len(enriched_batch) < (batch_end - batch_start):
                self.ui.log(f"🔄 [Recovery] {len(failed_indices)}개 항목 순차 재시도 중...")
                recovery_map = {}  # 원래 인덱스 → 복구된 데이터 매핑

                for failed_idx in failed_indices[:RecoveryLimits.MAX_PARALLEL_RECOVERY]:
                    try:
                        prev_b = arcs_source[failed_idx-1] if failed_idx > 0 else None
                        curr_b = arcs_source[failed_idx]
                        next_b_safe = {
                            "block_id": arcs_source[failed_idx+1].get("block_id", f"Block {failed_idx+2}"),
                            "title": arcs_source[failed_idx+1].get("title", "미정")
                        } if failed_idx < total_count-1 else {"title": "최종 블록"}

                        recovered_item = await self.agents['analyst'].enrich_raw_block_async(
                            curr_b, prev_b, next_b_safe, [],
                            transfused_history=last_refined_context
                        )
                        if isinstance(recovered_item, dict):
                            recovery_map[failed_idx] = recovered_item
                            self.ui.log(f"✅ [Recovery] idx={failed_idx} 복구 성공")
                    except Exception as retry_err:
                        self.ui.log(f"🚨 [Recovery] idx={failed_idx} 복구 실패: {retry_err}")

                # [V43 Fix] 원래 위치에 삽입하여 순서 보장 (재구축 방식)
                if recovery_map:
                    # 원본 배치 데이터 백업 후 재구축
                    original_batch_data = {(batch_start + i): item for i, item in enumerate(enriched_batch) if item}
                    original_batch_data.update(recovery_map)  # 복구된 데이터 병합

                    # 인덱스 순서대로 재구축
                    enriched_batch = []
                    for idx in range(batch_start, batch_end):
                        if idx in original_batch_data:
                            enriched_batch.append(original_batch_data[idx])
                        else:
                            self.ui.log(f"⚠️ [Recovery] idx={idx} 데이터 누락 - 해당 Arc 스킵")
                            self._audit_event("data_missing", "arc data not recovered", {"arc_idx": idx})

            if not enriched_batch:
                self.ui.log("❌ [Critical] 농축 결과가 비어 있습니다. 공정을 중단합니다.")
                self._audit_event("enrich_error", "empty batch after sanitize and recovery")
                return

            ### [B. 사후 용접 및 고유 명사 앵커링 (Entity Anchoring) 복구 - 예외 처리 추가]
            for i in range(len(enriched_batch) - 1):
                arc_a = enriched_batch[i]
                arc_b = enriched_batch[i+1]

                # [안전성 패치] stitch_joints 호출 예외 처리
                try:
                    stitch_res = self.agents['analyst'].stitch_joints(
                        arc_a.get('joint_docs', {}),
                        arc_b.get('joint_docs', {}),
                        arc_b.get('content', {}).get('context', "")
                    )
                except Exception as stitch_err:
                    self.ui.log(f"⚠️ [Analyst] Arc {batch_start+i+1}-{batch_start+i+2} 용접 실패: {stitch_err}")
                    self._audit_event("analyst_error", "stitch_joints failed", {
                        "arc_pair": f"{batch_start+i+1}-{batch_start+i+2}",
                        "error": str(stitch_err)
                    })
                    continue  # 용접 실패 시 다음 쌍으로 이동

                if stitch_res and isinstance(stitch_res, dict) and stitch_res.get('status') == "REPAIRED":
                    if 'content' in arc_b:
                        arc_b['content']['context'] = stitch_res.get('repaired_joint_b', arc_b['content'].get('context', ''))

                    # 생성된 고유 명사를 시스템 로어(Lore)에 즉시 반영하여 설정 충돌 방지
                    if stitch_res.get('entity_anchors'):
                        try:
                            self.sys.lore.update_v20_assets({"Temporary_Anchors": stitch_res['entity_anchors']})
                            self.ui.log(f"      ⚓ Arc {batch_start+i+1}-{batch_start+i+2} 고유 명사 앵커링 완료.")
                        except Exception as lore_err:
                            self.ui.log(f"⚠️ [Lore] 앵커링 실패: {lore_err}")
                    self.ui.log(f"   🧶 Arc {batch_start+i+1}-{batch_start+i+2} 인과율 용접 완료.")

            # C. [순차 설계 단계] 농축된 데이터를 전술서로 풀이하고 욕망을 박제
            # [V45 Fix] ep_end 키 접근 방어
            current_ep_start = 1 if not all_refined_arcs else all_refined_arcs[-1].get('ep_end', 0) + 1
            
            for idx, enriched_block in enumerate(enriched_batch):
                global_arc_no = batch_start + idx + 1
                vol_no = ((global_arc_no - 1) // VolumeSettings.ARCS_PER_VOLUME) + 1
                # [V41 Patch] Stage 1 스킵 시 빈 volumes 폴백 처리
                default_vol_strategy = {"vol_no": vol_no, "strategy_doc": ""}
                current_vol_strategy = next(
                    (v for v in volumes_strategy if v.get('vol_no') == vol_no),
                    volumes_strategy[0] if volumes_strategy else default_vol_strategy
                )
                
                ### [0124 핵심 1] Analyst: 결핍 리포트 생성 (예외 처리 추가)
                try:
                    lack_report = self.agents['analyst'].get_lack_report(self.sys.hud.pro_root)
                except Exception as lack_err:
                    self.ui.log(f"⚠️ [Analyst] 결핍 리포트 생성 실패: {lack_err}")
                    self._audit_event("analyst_error", "get_lack_report failed", {
                        "arc_no": global_arc_no,
                        "error": str(lack_err)
                    })
                    lack_report = {"martial_deficit": "분석 실패", "status": "error"}

                ### [0124 핵심 2] Weaver: 욕망 드라이브(Arc Drive) 생성 (예외 처리 추가)
                try:
                    arc_drive = self.agents['weaver'].generate_arc_drive(
                        current_arc_dna=arcs_source[batch_start + idx],
                        analyst_lack_report=lack_report,
                        grand_objective=grand_obj
                    )
                except Exception as weaver_err:
                    self.ui.log(f"⚠️ [Weaver] 욕망 드라이브 생성 실패: {weaver_err}")
                    self._audit_event("weaver_error", "generate_arc_drive failed", {
                        "arc_no": global_arc_no,
                        "error": str(weaver_err)
                    })
                    arc_drive = {"desire_vector": "생성 실패", "status": "error"}

                # [V40 Enhanced] 디렉터 감사 및 재시도 루프
                passed = False
                current_feedback = ""
                for attempt in range(RetryLimits.DIRECTOR_MAX_ATTEMPTS):
                    self.ui.log(f"   {Emojis.BRAIN} [Arc {global_arc_no}] 전술 설계 중 (시도 {attempt+1}/{RetryLimits.DIRECTOR_MAX_ATTEMPTS})...")
                    
                    recent_patterns = [
                        a.get('hybrid_composition', {}).get('primary')
                        for a in all_refined_arcs
                        if a.get('hybrid_composition', {}).get('primary')
                    ]

                    # [안전성 패치] Analyst 호출 및 결과 검증
                    try:
                        refined_arc = self.agents['analyst'].plan_single_arc_v20(
                            arc_no=global_arc_no,
                            vol_strategy=current_vol_strategy.get('strategy_doc', ''),
                            prev_block=None,
                            curr_block=enriched_block,
                            next_block=None,
                            ep_start=current_ep_start,
                            prev_arc_context=last_refined_context,
                            assets=bible_root.get('AssetLibrary', {}),
                            full_roadmap=full_roadmap_str,
                            assigned_seeds=[],
                            feedback=current_feedback,
                            recent_patterns=recent_patterns
                        )
                    except Exception as analyst_err:
                        self.ui.log(f"🚨 [Analyst Error] Arc {global_arc_no} 설계 중 에러: {analyst_err}")
                        self._audit_event("analyst_error", "plan_single_arc_v20 failed", {
                            "arc_no": global_arc_no,
                            "error": str(analyst_err)
                        })
                        current_feedback = f"Analyst 엔진 오류: {str(analyst_err)[:100]}. 안정적인 JSON 출력을 확보하라."
                        continue

                    # [데이터 검증] refined_arc가 유효한지 확인
                    if not refined_arc or not isinstance(refined_arc, dict):
                        self.ui.log(f"🚨 [Analyst Error] Arc {global_arc_no} 설계 결과가 유효하지 않음: {type(refined_arc)}")
                        self._audit_event("analyst_error", "invalid response type", {
                            "arc_no": global_arc_no,
                            "type": str(type(refined_arc))
                        })
                        current_feedback = "Analyst가 유효한 딕셔너리를 반환하지 않았습니다. JSON 규격을 확인하라."
                        continue

                    # 🧭 [Mapping Validation] 블록↔아크 매핑 및 회차 범위 정합성 점검
                    refined_arc = self._validate_arc_mapping(
                        refined_arc,
                        enriched_block,
                        global_arc_no,
                        current_ep_start
                    )

                    # 🚨 [Stage2 Flow Guard] 서사 폭주/정체 1차 차단
                    flow_guard = self._stage2_flow_guard(refined_arc)
                    if flow_guard.get("status") == "REJECT":
                        self.ui.log(f"   🚨 [Flow Guard] {flow_guard.get('reason')}")
                        self._audit_event("flow_guard", flow_guard.get("reason"), {
                            "arc_no": global_arc_no
                        })
                        current_feedback = flow_guard.get("feedback", "서사 폭주/정체 위험이 감지되었습니다.")
                        continue

                    # 🛡️ [Duplicate Guard] 직전 아크와 전술서 중복 차단
                    if all_refined_arcs:
                        prev_tactical = all_refined_arcs[-1].get('tactical_doc', '')
                        if self._is_tactical_doc_duplicate(refined_arc.get('tactical_doc', ''), [prev_tactical]):
                            self.ui.log("   🚨 [Duplicate Guard] 전술 설계가 직전 아크와 중복됩니다. 재생성합니다.")
                            self._audit_event("duplicate_guard", "arc tactical_doc duplicated", {
                                "arc_no": global_arc_no,
                                "prev_arc_no": all_refined_arcs[-1].get("arc_no")
                            })
                            current_feedback = "직전 아크와 동일한 전술 설계입니다. 사건/공간/인과를 완전히 새로 구성하십시오."
                            continue

                    # [안전성 패치] Director 호출 전 필수 데이터 검증
                    if not refined_arc or not isinstance(refined_arc, dict):
                        self.ui.log(f"🚨 [Data Error] refined_arc가 유효하지 않습니다")
                        self._audit_event("data_validation_error", "refined_arc invalid", {"arc_no": global_arc_no})
                        current_feedback = "설계 데이터 구조 오류. 전술 설계를 완전한 JSON으로 재작성하라."
                        continue

                    if not enriched_block or not isinstance(enriched_block, dict):
                        self.ui.log(f"🚨 [Data Error] enriched_block이 유효하지 않습니다")
                        self._audit_event("data_validation_error", "enriched_block invalid", {"arc_no": global_arc_no})
                        current_feedback = "농축 데이터 누락. 블록 정보를 포함하여 재설계하라."
                        continue

                    audit = self.agents['director'].audit_strategic_plan(
                        refined_arc,
                        last_refined_context,
                        curr_block=enriched_block,
                        protagonist_name=protagonist_name  # V42 LOCK
                    )
                    
                    if audit.get('decision') == 'PASS' and len(refined_arc.get('tactical_doc', '')) >= 2000:
                        ### [0124 핵심 3] 욕망 데이터 및 HUD 그림자 물리적 박제
                        refined_arc['arc_drive'] = arc_drive if arc_drive else {}
                        refined_arc['joint_docs'] = enriched_block.get('joint_docs', {})
                        refined_arc['status_shadow'] = enriched_block.get('status_shadow', {})

                        # [안전성 패치] 필수 키 누락 시 경고 후 기본값 주입
                        critical_missing = []
                        if not refined_arc.get('hybrid_composition'):
                            self.ui.log(f"⚠️ [Arc {global_arc_no}] 패턴 구성(hybrid_composition) 누락 - 기본값 주입")
                            self._audit_event("data_missing", "hybrid_composition missing", {"arc_no": global_arc_no})
                            refined_arc['hybrid_composition'] = {
                                "primary": "standard_progression",
                                "secondary": [],
                                "mixing_logic": "기본 전개"
                            }
                            critical_missing.append("hybrid_composition")

                        if not refined_arc.get('joint_docs'):
                            self.ui.log(f"⚠️ [Arc {global_arc_no}] joint_docs 누락 - 기본값 주입")
                            self._audit_event("data_missing", "joint_docs missing", {"arc_no": global_arc_no})
                            refined_arc['joint_docs'] = {
                                "final_location": "위치 미정",
                                "physical_inventory": "물품 미정",
                                "world_joint": "변화 없음"
                            }
                            critical_missing.append("joint_docs")

                        if not refined_arc.get('status_shadow'):
                            self.ui.log(f"⚠️ [Arc {global_arc_no}] status_shadow 누락 - 기본값 주입")
                            self._audit_event("data_missing", "status_shadow missing", {"arc_no": global_arc_no})
                            refined_arc['status_shadow'] = {
                                "internal_energy_loss": "0%",
                                "expected_injuries": "없음",
                                "item_consumption": []
                            }
                            critical_missing.append("status_shadow")

                        # [V40.1 Fix] 상수 사용 - 3개 이상 누락 시 재설계 요구
                        if len(critical_missing) >= RecoveryLimits.CRITICAL_MISSING_THRESHOLD:
                            self.ui.log(f"🚨 [Arc {global_arc_no}] 핵심 데이터 과다 누락({len(critical_missing)}개)")
                            current_feedback = f"필수 키 누락: {', '.join(critical_missing)}. 완전한 JSON 구조로 재설계하라."
                            continue

                        # 🧱 [Integrity Gate] 필수 키 검증 통과 시에만 저장
                        if not self._validate_arc_integrity(refined_arc):
                            current_feedback = "필수 키가 누락된 전술 설계입니다. 형식을 완전한 JSON으로 다시 출력하십시오."
                            continue
                        
                        all_refined_arcs.append(refined_arc)

                        ### [0124 핵심 4] DB 원자적 커밋 (비동기 환경 안전화)
                        try:
                            self.current_project.save_v20_anchor("arcs", all_refined_arcs)
                            await self._safe_commit_async()  # [V40.1 Fix] 비동기 안전 커밋 사용
                        except Exception as commit_err:
                            self.ui.log(f"🚨 [DB] Arc {global_arc_no} 저장 실패: {commit_err}")
                            self._audit_event("db_commit_error", "arc save failed in async", {
                                "arc_no": global_arc_no,
                                "error": str(commit_err)
                            })
                            # 저장 실패 시 해당 arc를 리스트에서 제거하고 재시도
                            all_refined_arcs.pop()
                            continue

                        last_refined_context = f"[Arc {global_arc_no} 결말]: {refined_arc['tactical_doc'][:400]}..."
                        current_ep_start = refined_arc['ep_end'] + 1
                        passed = True
                        break
                    else:
                        current_feedback = audit.get('re_slice_instruction', '밀도 보강 필요')
                        self.ui.log(f"      🎬 [Reject] {audit.get('reason')}")

                if not passed:
                    self.ui.log(f"🚨 [Critical] Arc {global_arc_no} 최종 설계 실패.")
                    self._audit_event("arc_design_failed", "max retries exhausted", {
                        "arc_no": global_arc_no,
                        "batch_start": batch_start,
                        "batch_end": batch_end
                    })
                    # [V43 패치] 진행 상황 보존 및 사용자 선택 제공
                    if all_refined_arcs:
                        self.ui.log(f"💾 [Auto-Save] 현재까지 {len(all_refined_arcs)}개 Arc 저장 완료.")
                    user_choice = input("   [1] 건너뛰고 계속  [2] 중단 (기본: 2): ").strip()
                    if user_choice != '1':
                        self.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                        return
                    # 건너뛰기 선택 시 다음 Arc를 위한 context 업데이트
                    self.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                    current_ep_start += 5  # 기본 회차 증가
                    continue

            self.ui.log(f"✅ 배치({batch_start+1}~{batch_end}) 욕망 엔진 이식 및 용접 완료.")
            
            # [V40] Slack 알림 전송 (Arc 설계 완료)
            notifier.send_notification(
                title=f"✅ [Arc] 제 {batch_start+1}~{batch_end}번 아크 설계 완료",
                message=f"프로젝트: {self.current_project.name}\n설계된 아크 수: {len(batch_results)}개",
                key_metrics={"완료 구간": f"{batch_start+1} ~ {batch_end} Arc", "생성 수": len(batch_results)}
            )

        self.ui.log("✨ [Success] 0124 매니페스토 기반 전술 설계 전 공정 완료.")
        self._write_audit_summary("stage2_complete")
        input("\n[Enter] 메뉴로 돌아가기")


    def _normalize_tactical_text(self, text):
        if not isinstance(text, str):
            return ""
        normalized = text
        # 이중 이스케이프 단계 완화
        for _ in range(2):
            normalized = normalized.replace("\\\\n", "\\n").replace("\\\\t", "\\t")
        normalized = normalized.replace("\\n", "\n").replace("\\t", "\t")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _is_tactical_doc_duplicate(self, candidate_text, reference_texts, threshold=0.98):
        from difflib import SequenceMatcher
        import hashlib
        candidate = self._normalize_tactical_text(candidate_text)
        if not candidate:
            return False
        # 최근 N개만 비교 (성능 가드)
        recent_refs = reference_texts[-3:] if len(reference_texts) > 3 else reference_texts
        candidate_hash = hashlib.md5(candidate.encode("utf-8")).hexdigest()
        ref_hashes = set()
        for ref_text in recent_refs:
            ref = self._normalize_tactical_text(ref_text)
            if not ref:
                continue
            ref_hashes.add(hashlib.md5(ref.encode("utf-8")).hexdigest())
            if candidate == ref:
                return True
        if candidate_hash in ref_hashes:
            return True
        for ref_text in recent_refs:
            ref = self._normalize_tactical_text(ref_text)
            if not ref:
                continue
            if SequenceMatcher(None, candidate, ref).ratio() >= threshold:
                return True
        return False

    def _normalize_flow_text(self, text):
        if not isinstance(text, str):
            return ""
        normalized = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", text)
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()
        return normalized

    def _validate_volume_boundaries(self, vol_data, vol_idx):
        """[V39 패치 D] Volume 설계에서 미래 권 정보 누수 차단"""
        strategy = vol_data.get('strategy_doc', '')
        
        if not isinstance(strategy, str):
            return {"status": "PASS"}
        
        # 1. 미래 권 번호 검출
        future_mentions = re.findall(r'제\s*(\d+)\s*권', strategy)
        for mention in future_mentions:
            try:
                mention_vol = int(mention)
                if mention_vol > vol_idx:
                    return {
                        "status": "REJECT",
                        "reason": f"미래 권({mention}권) 정보 누수 감지",
                        "feedback": f"제 {vol_idx}권 설계에서 {mention}권 내용을 언급하지 마십시오."
                    }
            except ValueError:
                continue
        
        # 2. 미래 지향 키워드 검출 (과도한 경우만)
        future_keywords = ["이후", "다음 권", "훗날", "나중에", "앞으로"]
        future_count = sum(strategy.count(kw) for kw in future_keywords)
        if future_count > 3:  # 3회 이상 언급 시 경고
            return {
                "status": "WARNING",
                "reason": f"미래 지향 표현 과다 ({future_count}회)",
                "feedback": "현재 권의 사건에만 집중하십시오."
            }
        
        return {"status": "PASS"}
    
    def _stage2_flow_guard(self, refined_arc):
        """Stage2: 서사 폭주/정체 1차 방지 가드"""
        beats = refined_arc.get("beat_sequence", [])
        ep_count = refined_arc.get("ep_count", 0)
        if not isinstance(beats, list) or len(beats) < max(2, ep_count):
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트 수가 화수보다 부족",
                "feedback": "각 화마다 고유 사건을 분리해 비트를 늘려라."
            }

        normalized = [self._normalize_flow_text(b) for b in beats if isinstance(b, str)]
        if len(normalized) < 2:
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트 내용이 비어 있음",
                "feedback": "각 화의 비트를 구체적 사건/행동으로 작성하라."
            }

        # 1) 서사 폭주 감지: 비트가 과도하게 짧음
        word_counts = [len(t.split()) for t in normalized if t]
        avg_words = sum(word_counts) / max(1, len(word_counts))
        if avg_words < 6 or any(c < 4 for c in word_counts):
            return {
                "status": "REJECT",
                "reason": "서사 폭주 위험: 비트가 과도하게 축약됨",
                "feedback": "각 화마다 사건/행동/반응을 최소 1개씩 명시하라."
            }

        # 2) 서사 정체 감지: 유사 비트 연속 반복
        def jaccard(a, b):
            sa, sb = set(a.split()), set(b.split())
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        stagnation_hits = 0
        for i in range(1, len(normalized)):
            if jaccard(normalized[i - 1], normalized[i]) >= 0.75:  # [V39.1 패치] 0.9 → 0.75 (더 엄격)
                stagnation_hits += 1
        if stagnation_hits >= 2:
            return {
                "status": "REJECT",
                "reason": "서사 정체 감지: 유사 비트가 연속 반복",
                "feedback": "연속 회차의 사건/공간/행동을 분리하여 변주하라."
            }

        return {"status": "PASS"}

    def _get_int_input(
        self,
        prompt: str,
        default: Optional[int] = None,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
        attempts: int = RetryLimits.USER_INPUT_ATTEMPTS
    ) -> Optional[int]:
        """
        사용자로부터 정수 입력을 받는 유틸리티 메서드

        범위 검증과 재시도 로직을 포함합니다.

        Args:
            prompt: 입력 프롬프트 문자열
            default: 빈 입력 시 반환할 기본값
            min_val: 허용 최소값 (None이면 검증 안 함)
            max_val: 허용 최대값 (None이면 검증 안 함)
            attempts: 최대 재시도 횟수

        Returns:
            Optional[int]: 입력된 정수 또는 기본값
        """
        for _ in range(attempts):
            raw = input(prompt).strip()
            if raw == "":
                return default
            if not raw.isdigit():
                self.ui.log("⚠️ 숫자만 입력 가능합니다.")
                continue
            value = int(raw)
            if min_val is not None and value < min_val:
                self.ui.log(f"⚠️ 최소값은 {min_val}입니다.")
                continue
            if max_val is not None and value > max_val:
                self.ui.log(f"⚠️ 최대값은 {max_val}입니다.")
                continue
            return value
        return default

    def _extract_block_index(self, block_id: Any) -> Optional[int]:
        """
        블록 ID 문자열에서 인덱스 번호 추출

        Args:
            block_id: "Block N" 형식의 블록 ID 문자열

        Returns:
            Optional[int]: 추출된 인덱스 번호 (실패 시 None)
        """
        if not isinstance(block_id, str):
            return None
        match = re.search(r"Block\s+(\d+)", block_id)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _validate_arc_mapping(self, refined_arc, enriched_block, expected_arc_no, expected_ep_start):
        if not refined_arc or not isinstance(refined_arc, dict):
            return refined_arc

        # 1) arc_no 보정
        if refined_arc.get("arc_no") != expected_arc_no:
            self.ui.log(
                f"⚠️ [Mapping] arc_no 불일치: {refined_arc.get('arc_no')} -> {expected_arc_no} (보정)"
            )
            self._audit_event("mapping_fix", "arc_no mismatch", {
                "original": refined_arc.get("arc_no"),
                "expected": expected_arc_no
            })
            refined_arc["arc_no"] = expected_arc_no

        # 2) ep_start/ep_end 보정
        ep_count = refined_arc.get("ep_count") or refined_arc.get("ep_end")
        if not isinstance(ep_count, int):
            ep_count = refined_arc.get("ep_count", 5)
        if refined_arc.get("ep_start") != expected_ep_start:
            self.ui.log(
                f"⚠️ [Mapping] ep_start 불일치: {refined_arc.get('ep_start')} -> {expected_ep_start} (보정)"
            )
            self._audit_event("mapping_fix", "ep_start mismatch", {
                "original": refined_arc.get("ep_start"),
                "expected": expected_ep_start
            })
            refined_arc["ep_start"] = expected_ep_start
        refined_arc["ep_end"] = expected_ep_start + int(ep_count) - 1

        # 3) plot_roadmap 블록 인덱스 매칭
        block_id = None
        if isinstance(enriched_block, dict):
            block_id = enriched_block.get("block_id") or enriched_block.get("id")
        block_index = self._extract_block_index(block_id)
        if block_index is not None and block_index != expected_arc_no:
            self.ui.log(
                f"⚠️ [Mapping] 블록 인덱스 불일치: {block_id} (arc {expected_arc_no})"
            )
            refined_arc["mapping_warning"] = f"block_id={block_id} vs arc_no={expected_arc_no}"
            self._audit_event("mapping_warning", "block_id mismatch", {
                "block_id": block_id,
                "arc_no": expected_arc_no
            })

        return refined_arc

    def _extract_pattern_keywords(self, pattern_profile):
        if not isinstance(pattern_profile, dict):
            return []
        keywords = []
        primary = pattern_profile.get("primary", "")
        secondary = pattern_profile.get("secondary", [])
        raw_items = []
        if isinstance(primary, str) and primary.strip():
            raw_items.append(primary)
        if isinstance(secondary, list):
            raw_items.extend([s for s in secondary if isinstance(s, str)])
        # 괄호/영문 보조 표기를 제거하고 핵심 한글 키워드만 추출
        for item in raw_items:
            core = re.sub(r"\([^)]*\)", "", item).strip()
            parts = re.split(r"[\s/]+", core)
            keywords.extend([p for p in parts if len(p) >= 2])
        # 중복 제거
        return list(dict.fromkeys(keywords))

    def _pattern_presence_check(self, text, pattern_profile, min_hits=1):  # [V40.3 패치] 2 → 1 (완화)
        if not isinstance(text, str) or not text.strip():
            return False
        keywords = self._extract_pattern_keywords(pattern_profile)
        if not keywords:
            return True
        hits = sum(1 for k in keywords if k in text)
        return hits >= min_hits

    # =================================================================
    # [V45] Validation Context 구성 헬퍼
    # =================================================================

    def _build_validation_context(self, ep_num: int, blueprint: dict = None, mode: str = 'MANUSCRIPT') -> dict:
        """
        [V45] BlockingValidator용 validation_context 구성

        Args:
            ep_num: 에피소드 번호
            blueprint: 설계도 (선택)
            mode: 'MANUSCRIPT' 또는 'BLUEPRINT'

        Returns:
            dict: {
                'encyclopedia': {'items': [...], 'npcs': [...], 'locations': [...]},
                'martial_hud': {...},
                'blueprint': {...},
                'mode': 'MANUSCRIPT' | 'BLUEPRINT',
                'history': [...],
                'npc_profiles': {...}
            }
        """
        context = {
            'mode': mode,
            'encyclopedia': {},
            'martial_hud': {},
            'blueprint': blueprint or {},
            'history': [],
            'npc_profiles': {}
        }

        try:
            # 1. Encyclopedia 구성 (LoreManager 사용)
            if hasattr(self.sys, 'lore') and self.sys.lore:
                context['encyclopedia'] = self.sys.lore.build_validation_encyclopedia()

            # 2. Martial HUD 구성
            if hasattr(self.sys, 'hud') and self.sys.hud:
                hud_data = self.sys.hud.pro_root
                context['martial_hud'] = {
                    'actual_truth': self.sys.hud.pro_data
                }

            # 3. 최근 히스토리 추출 (인과 요약 체인 사용)
            if self.current_project:
                causal_summary = self.current_project.get_causal_history_summary()
                if causal_summary:
                    context['history'] = [{'summary': causal_summary}]

            # 4. NPC 프로필 추출
            if self.current_project:
                bible = self.current_project.master_bible.get('MasterBible', {})
                # [V45 Fix] KeyNPCs와 Key_NPCs 두 가지 키 모두 지원
                asset_lib = bible.get('AssetLibrary', {})
                npc_lib = asset_lib.get('KeyNPCs', []) or asset_lib.get('Key_NPCs', [])
                for npc in npc_lib:
                    npc_name = npc.get('name', '') or npc.get('Name', '')
                    if npc_name:
                        context['npc_profiles'][npc_name] = npc

        except Exception as e:
            self.ui.log(f"⚠️ [Validation Context] 구성 중 오류 (비치명적): {e}")

        return context

    # =================================================================
    # [V41] Director Sovereignty 헬퍼 메서드
    # =================================================================

    def _extract_npc_profiles(self, arc_data: dict) -> dict:
        """[V41] 아크 데이터에서 등장 NPC 프로필 추출"""
        npcs = {}
        if not self.current_project:
            return npcs

        bible = self.current_project.master_bible.get('MasterBible', {})
        npc_lib = bible.get('AssetLibrary', {}).get('Key_NPCs', [])

        # 아크에서 언급된 NPC만 필터링
        arc_text = json.dumps(arc_data, ensure_ascii=False) if arc_data else ""
        for npc in npc_lib:
            npc_name = npc.get('name', '') or npc.get('Name', '')
            if npc_name and npc_name in arc_text:
                npcs[npc_name] = npc

        return npcs

    def _get_character_traits(self) -> dict:
        """[V41] 캐릭터 특성 DB 로드 (성격, 지능, 무공수준)"""
        traits = {}
        if not self.current_project:
            return traits

        bible = self.current_project.master_bible.get('MasterBible', {})

        for npc in bible.get('AssetLibrary', {}).get('Key_NPCs', []):
            npc_name = npc.get('name', '') or npc.get('Name', '')
            if npc_name:
                traits[npc_name] = {
                    'personality': npc.get('personality', npc.get('Personality', '')),
                    'intelligence': npc.get('intelligence', 'normal'),
                    'martial_level': npc.get('NPC_Martial_HUD', {}).get('realm', '알 수 없음'),
                    'faction': npc.get('faction', npc.get('Faction', '')),
                    'role': npc.get('role', npc.get('Role', ''))
                }

        return traits

    def _load_character_archetypes(self, genre: str = 'wuxia') -> dict:
        """[V41] 장르별 캐릭터 아키타입 JSON 로드"""
        archetypes = {}
        try:
            archetype_path = Path("modules/core/laws/archetypes") / f"{genre}.json"
            if archetype_path.exists():
                archetypes = json.loads(archetype_path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"      ⚠️ [Archetype] 아키타입 로드 실패: {e}")
        return archetypes

    def _get_archetype_reference_for_npcs(self, npc_profiles: dict, genre: str = 'wuxia') -> str:
        """[V41] NPC 프로필에 맞는 아키타입 참고 자료 생성"""
        if not npc_profiles:
            return ""

        archetypes = self._load_character_archetypes(genre)
        if not archetypes:
            return ""

        reference_lines = ["[📚 캐릭터 아키타입 참고 자료]",
                          "등장 NPC들의 유형입니다. 참고하되 변주는 자유롭게 하십시오.", ""]

        for npc_name, npc_data in npc_profiles.items():
            npc_role = npc_data.get('role', '') or npc_data.get('Role', '')
            npc_archetype = npc_data.get('archetype', '')  # NPC에 지정된 아키타입

            # NPC 역할에서 아키타입 카테고리 추론
            role_lower = npc_role.lower() if npc_role else ''
            archetype_info = None

            # 역할 기반 매칭
            if '히로인' in role_lower or 'heroine' in role_lower or '여주' in role_lower:
                category = 'supporter'
                subcategory = 'heroine'
            elif '스승' in role_lower or 'mentor' in role_lower or '사부' in role_lower:
                category = 'mentor'
                subcategory = 'master'
            elif '적' in role_lower or '악당' in role_lower or 'antagonist' in role_lower:
                category = 'antagonist'
                subcategory = 'rival'
            elif '제자' in role_lower or '수혜' in role_lower:
                category = 'beneficiary'
                subcategory = 'disciple'
            elif '장로' in role_lower or '검증' in role_lower:
                category = 'validator'
                subcategory = 'authority'
            else:
                category = None
                subcategory = None

            # 아키타입 정보 추출
            if category and subcategory:
                cat_data = archetypes.get(category, {})
                subcat_data = cat_data.get(subcategory, {})

                # 첫 번째 아키타입 사용 (또는 지정된 아키타입)
                if npc_archetype and npc_archetype in subcat_data:
                    archetype_info = subcat_data[npc_archetype]
                    archetype_name = npc_archetype
                elif subcat_data:
                    # 내부 필드 제외하고 첫 번째 아키타입 선택
                    for key, val in subcat_data.items():
                        if not key.startswith('_') and isinstance(val, dict):
                            archetype_info = val
                            archetype_name = key
                            break

            if archetype_info:
                traits = archetype_info.get('core_traits', [])
                speech = archetype_info.get('speech', '')
                forbidden = archetype_info.get('forbidden', [])

                reference_lines.append(f"- **{npc_name}**: '{archetype_name}' 유형")
                if traits:
                    reference_lines.append(f"  - 핵심 특성: {', '.join(traits[:4])}")
                if speech:
                    reference_lines.append(f"  - 말투: {speech[:50]}...")
                if forbidden:
                    reference_lines.append(f"  - 금기: {', '.join(forbidden[:3])}")
                reference_lines.append("")

        if len(reference_lines) <= 3:
            return ""  # 매칭된 NPC가 없으면 빈 문자열

        return "\n".join(reference_lines)

    def _audit_event(self, event_type, message, data=None):
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        self.runtime_audit.append(event)
        if not self.current_project:
            return
        try:
            log_dir = self.current_project.paths.root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "runtime_audit.jsonl"
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            self.ui.log(f"⚠️ [Audit] 로그 기록 실패: {e}")

    def _write_audit_summary(self, tag="snapshot"):
        if not self.current_project:
            return
        try:
            summary = {
                "tag": tag,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_events": len(self.runtime_audit),
                "counts": {}
            }
            for evt in self.runtime_audit[-200:]:
                summary["counts"][evt["type"]] = summary["counts"].get(evt["type"], 0) + 1
            log_dir = self.current_project.paths.root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            summary_path = log_dir / "runtime_audit_summary.json"
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self.ui.log(f"⚠️ [Audit] 요약 기록 실패: {e}")

    def _get_arc_context_for_episode(self, ep_num: int) -> Tuple[Optional[int], Optional[Dict]]:
        """
        [V40.1 Medium Fix] 에피소드 번호에 해당하는 아크 컨텍스트 추출

        Args:
            ep_num: 에피소드 번호

        Returns:
            Tuple[Optional[int], Optional[Dict]]: (arc_idx, arc_data) 튜플
                - arc_idx: 아크 인덱스 (없으면 None)
                - arc_data: 아크 데이터 딕셔너리 (없으면 None)
        """
        arc_idx = None
        arc_data = None

        try:
            arc_idx = next((i for i, a in enumerate(self.current_project.arcs)
                        if isinstance(a, dict) and
                           isinstance(a.get('ep_start'), int) and
                           isinstance(a.get('ep_end'), int) and
                           a.get('ep_start') <= ep_num <= a.get('ep_end')), None)
        except Exception as idx_err:
            self.ui.log(f"🚨 [Error] 아크 인덱스 추출 중 오류: {idx_err}")
            self._audit_event("data_extraction_error", "arc_idx search failed", {
                "ep_num": ep_num,
                "error": str(idx_err)
            })
            return None, None

        if arc_idx is None:
            self.ui.log(f"⚠️ 제 {ep_num}화에 해당하는 아크 계획이 없습니다.")
            self._audit_event("data_missing", "arc_index not found", {"ep_num": ep_num})
            return None, None

        arc_data = self.current_project.arcs[arc_idx]
        if not isinstance(arc_data, dict):
            self.ui.log(f"🚨 [Stop] arc_data가 딕셔너리가 아닙니다: type={type(arc_data)}")
            self._audit_event("data_type_error", "arc_data invalid type", {
                "arc_idx": arc_idx,
                "type": str(type(arc_data))
            })
            return None, None

        return arc_idx, arc_data

    def _validate_arc_data_fields(self, arc_data: Dict, arc_idx: int) -> Optional[Dict]:
        """
        [V43] arc_data 필수 필드 검증 및 자동 복구

        Args:
            arc_data: 검증할 아크 데이터
            arc_idx: 아크 인덱스 (로깅용)

        Returns:
            Optional[Dict]: 검증/복구된 데이터, 복구 불가 시 None
        """
        if not isinstance(arc_data, dict):
            self.ui.log(f"🚨 [V43] arc_data가 딕셔너리가 아닙니다: {type(arc_data)}")
            return None

        # 필수 필드 기본값 정의
        required_defaults = {
            'tactical_doc': '',
            'beat_sequence': [],
            'joint_docs': {},
            'status_shadow': {},
            'arc_drive': {},
            'hybrid_composition': {'primary': 'standard', 'secondary': [], 'mixing_logic': '기본'},
            # [V44 Fix] ep_count와 ep_end 계산 시 실제 arc 데이터 우선 사용
            'ep_count': arc_data.get('ep_count', VolumeSettings.EPISODES_PER_ARC),
            'ep_end': arc_data.get('ep_start', 1) + arc_data.get('ep_count', VolumeSettings.EPISODES_PER_ARC) - 1
        }

        repaired = False
        for field, default_val in required_defaults.items():
            current_val = arc_data.get(field)

            # None이거나 타입이 맞지 않는 경우 기본값으로 복구
            if current_val is None:
                arc_data[field] = default_val
                self.ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 누락 → 기본값 주입")
                self._audit_event("field_repair", f"{field} missing", {"arc_idx": arc_idx})
                repaired = True
            elif isinstance(default_val, dict) and not isinstance(current_val, dict):
                arc_data[field] = default_val
                self.ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 타입 오류 → dict로 복구")
                repaired = True
            elif isinstance(default_val, list) and not isinstance(current_val, list):
                arc_data[field] = default_val
                self.ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 타입 오류 → list로 복구")
                repaired = True
            elif isinstance(default_val, str) and not isinstance(current_val, str):
                arc_data[field] = str(current_val) if current_val else default_val
                self.ui.log(f"   ⚠️ [V43] Arc {arc_idx}: {field} 타입 오류 → str로 변환")
                repaired = True

        if repaired:
            self.ui.log(f"   🔧 [V43] Arc {arc_idx} 데이터 복구 완료")

        return arc_data

    def _get_prev_manuscript_ending(self, ep_num: int, sentence_count: int = 3) -> str:
        """
        [V40.1 Medium Fix] 직전 화 원고의 마지막 문장들 추출

        Args:
            ep_num: 현재 에피소드 번호
            sentence_count: 추출할 문장 수 (기본값: 3)

        Returns:
            str: 직전 화 마지막 문장들 (없으면 기본 메시지)
        """
        prev_ms_data = self.current_project.db.get_manuscript(ep_num - 1)
        if not prev_ms_data:
            return "이전 회차가 없습니다."

        try:
            sentences = re.split(r'(?<=[.!?])\s+', prev_ms_data['content'].strip())
            return " ".join(sentences[-sentence_count:])
        except Exception as e:
            self._audit_event("text_extraction_error", "prev manuscript ending extraction failed", {
                "ep_num": ep_num,
                "error": str(e)
            })
            return "이전 회차 추출 실패"

    def _load_genre_references(self) -> Tuple[List, List]:
        """
        [V40.1 Medium Fix] 장르별 레퍼런스 데이터 로드 (공통 메서드)

        Stage 3, Stage 4에서 중복 사용되던 장르별 레퍼런스 로딩 로직을 통합합니다.
        장르별 전용 파일이 없으면 기본 파일을 사용합니다.

        Returns:
            Tuple[List, List]: (cliche_data, location_data) 튜플
                - cliche_data: 클리셰/패턴 풀 데이터
                - location_data: 장소/배경 풀 데이터

        Raises:
            Exception: 파일 로드 실패 시 빈 리스트 반환
        """
        seeds_path = Path("modules/core/laws/seeds")
        genre_type = self.selected_genre.get('type', GenreTypes.WUXIA) if self.selected_genre else GenreTypes.WUXIA

        cliche_data = []
        location_data = []

        try:
            # 장르별 파일 우선 시도, 없으면 기본 파일 사용
            cliche_file = seeds_path / f"cliche_pool_{genre_type}.json"
            if not cliche_file.exists():
                cliche_file = seeds_path / "cliche_pool.json"

            location_file = seeds_path / f"location_pool_{genre_type}.json"
            if not location_file.exists():
                location_file = seeds_path / "location_pool.json"

            if cliche_file.exists():
                cliche_data = json.loads(cliche_file.read_text(encoding="utf-8"))
            if location_file.exists():
                location_data = json.loads(location_file.read_text(encoding="utf-8"))

            self.ui.log(f"{Emojis.CHECK} [{genre_type}] 장르 전용 레퍼런스 데이터 로드 완료")
            self._audit_event("reference_loaded", f"genre references loaded for {genre_type}", {
                "cliche_count": len(cliche_data),
                "location_count": len(location_data)
            })
        except Exception as e:
            self.ui.log(f"{Emojis.ERROR} 레퍼런스 파일 로드 실패: {e}")
            self._audit_event("reference_load_error", "failed to load genre references", {"error": str(e)})

        return cliche_data, location_data

    def _validate_arc_integrity(self, arc_data: Dict[str, Any]) -> bool:
        """
        아크 데이터의 무결성 검증

        필수 키 존재 여부, beat_sequence 형식, tactical_doc 분량을 검사합니다.

        Args:
            arc_data: 검증할 아크 데이터 딕셔너리

        Returns:
            bool: 검증 통과 여부
        """
        required_keys = ["arc_no", "ep_start", "ep_end", "ep_count", "tactical_doc", "beat_sequence"]
        missing = [k for k in required_keys if not arc_data.get(k)]
        if missing:
            self.ui.log(f"🚨 [Integrity] Arc 필수 키 누락: {missing}")
            self._audit_event("integrity_fail", "arc missing keys", {"missing": missing, "arc_no": arc_data.get("arc_no")})
            return False
        if not isinstance(arc_data.get("beat_sequence"), list) or len(arc_data.get("beat_sequence")) < 1:
            self.ui.log("🚨 [Integrity] beat_sequence 형식 오류")
            self._audit_event("integrity_fail", "beat_sequence invalid", {"arc_no": arc_data.get("arc_no")})
            return False
        if not isinstance(arc_data.get("tactical_doc"), str) or len(arc_data.get("tactical_doc", "")) < 500:
            self.ui.log("🚨 [Integrity] tactical_doc 분량 부족")
            self._audit_event("integrity_fail", "tactical_doc too short", {"arc_no": arc_data.get("arc_no")})
            return False
        return True

    def _validate_blueprint_integrity(self, blueprint: Any) -> bool:
        """
        블루프린트 데이터의 무결성 검증

        딕셔너리 타입, integrated_scenario, scene_breakdown 존재 여부를 검사합니다.

        Args:
            blueprint: 검증할 블루프린트 데이터

        Returns:
            bool: 검증 통과 여부
        """
        if not isinstance(blueprint, dict):
            self.ui.log(f"{Emojis.ERROR} [Integrity] Blueprint 형식 오류")
            self._audit_event("integrity_fail", "blueprint invalid type")
            return False
        if "integrated_scenario" not in blueprint or not isinstance(blueprint.get("integrated_scenario"), str):
            self.ui.log(f"{Emojis.ERROR} [Integrity] integrated_scenario 누락")
            self._audit_event("integrity_fail", "integrated_scenario missing")
            return False
        if "scene_breakdown" not in blueprint or not isinstance(blueprint.get("scene_breakdown"), dict):
            self.ui.log(f"{Emojis.ERROR} [Integrity] scene_breakdown 누락")
            self._audit_event("integrity_fail", "scene_breakdown missing")
            return False
        return True

    def _show_volume_table(self, volumes: List[Dict[str, Any]]) -> None:
        """
        권별 전략 설계 테이블 출력

        Rich 라이브러리를 사용하여 권별 전략과 사이다 점수를 테이블로 표시합니다.

        Args:
            volumes: 권 데이터 딕셔너리 리스트
        """
        from rich.table import Table
        from rich import box
        table = Table(title="📊 [V20] 10권 전략 설계 상업성 성적표", box=box.ROUNDED)
        table.add_column("Vol", justify="center", style="cyan")
        table.add_column("Strategy Title", style="white")
        table.add_column("Cider Score", justify="right", style="bold yellow")
        for v in volumes:
            title = v['strategy_doc'].split('\n')[0].replace('### ', '')
            cider = v.get('cider_score', 'N/A') # 키가 없으면 'N/A' 출력
            table.add_row(f"제 {v.get('vol_no', '?')} 권", title, str(cider))
        self.ui.console.print(table)






    def _stage_3_batch_blueprinting(self) -> None:
        """
        [Stage 3] 설계도 일괄 생성 및 V35 매니페스토 역전파 제어 공정

        에피소드별 블루프린트를 생성합니다. V35 Strike-Enrichment System을
        사용하여 설계 품질을 보장하고, 디렉터 검증을 통과한 설계도만 저장합니다.

        주요 기능:
            - 장르별 레퍼런스 데이터 로드
            - 아크 컨텍스트 기반 블루프린트 생성
            - 디렉터 검증 및 반려 시 재설계
            - 동적 모델 스위칭 (Emergency Fallback)

        Raises:
            Stage 2 설계가 선행되지 않은 경우 조기 종료
        """
        if not self.current_project.arcs:
            self.ui.log(f"{Emojis.ERROR} {ErrorMessages.STAGE_PREREQUISITE_MISSING}")
            return

        # 1. 목표 범위 설정
        # [V45 Fix] ep_end 키 접근 방어
        total_planned_ep = self.current_project.arcs[-1].get('ep_end', 50)
        production_head = self.current_project.get_latest_episode_number()

        # [V40.1 Smart Skip] 기존 원고가 있다면 자동으로 다음 화부터 시작
        existing_ms_max_ep = self._get_max_episode_from_manuscripts()
        if existing_ms_max_ep > production_head:
            self.ui.log(f"📂 [Manuscript Detected] 기존 원고 {existing_ms_max_ep}화까지 발견")
            self.ui.log(f"⏭️  [Smart Skip] {existing_ms_max_ep + 1}화부터 설계도 생성을 시작합니다")
            production_head = existing_ms_max_ep

        self.ui.log(f"📊 [Info] 현재 총 {total_planned_ep}화까지 설계가 가능합니다.")
        target_ep = self._get_int_input(
            f"👉 몇 화까지 설계도를 생성하시겠습니까? (현재 {production_head}화 / 최대 {total_planned_ep}화): ",
            default=total_planned_ep,
            min_val=production_head + 1,
            max_val=total_planned_ep
        )

        # 2. [V40.1 Fix] 장르별 레퍼런스 데이터 로드 (공통 메서드 사용)
        cliche_data, location_data = self._load_genre_references()
        if not cliche_data or not location_data:
            self.ui.log(f"{Emojis.ERROR} 레퍼런스 데이터가 비어있어 공정을 중단합니다.")
            return

        working_ep = production_head

        # 메인 에피소드 루프
        while working_ep <= target_ep:

            # [V40.1 Fix] 3. 아크 맥락 확보 (공통 메서드 사용)
            arc_idx, arc_data = self._get_arc_context_for_episode(working_ep)
            if arc_idx is None or arc_data is None:
                break

            ep_start_val = arc_data.get('ep_start')
            if ep_start_val is None or not isinstance(ep_start_val, int):
                self.ui.log(f"⚠️ [Stop] 아크 ep_start 누락 또는 잘못된 타입: arc_idx={arc_idx}, ep_start={ep_start_val}")
                self._audit_event("data_missing", "arc ep_start missing or invalid", {
                    "arc_idx": arc_idx,
                    "ep_start": ep_start_val
                })
                break

            # [V43 패치] arc_data 필수 필드 검증 및 자동 복구
            arc_data_validated = self._validate_arc_data_fields(arc_data, arc_idx)
            if arc_data_validated:
                arc_data = arc_data_validated  # 검증/복구된 데이터로 교체

            arc_pos = working_ep - ep_start_val + 1
            total_ep_in_arc = arc_data.get('ep_count', VolumeSettings.EPISODES_PER_ARC)

            # 이미 설계도가 존재하는 경우 스킵
            if self.current_project.get_blueprint(working_ep):
                working_ep += 1
                continue

            # [V40.1 Fix] 직전 화 원고 엔딩 추출 (공통 메서드 사용)
            prev_ms_ending = self._get_prev_manuscript_ending(working_ep)

            # 4. [V35 무결성 루프: Strike-Enrichment System]
            blueprint = None
            reject_count = 0     # 설계 시도 및 반려 횟수
            surgery_count = 0    # 아크 수술 횟수
            enrichment_level = 0 # 정밀도 레벨
            retry_feedback = ""
            blueprint_attempts = 0
            max_blueprint_attempts = 12

            while not blueprint:
                blueprint_attempts += 1
                if blueprint_attempts > RetryLimits.BLUEPRINT_MAX_ATTEMPTS:
                    self.ui.log("🛑 [Safety] 설계도 시도 횟수 초과로 공정을 중단합니다.")
                    self._audit_event("safety_stop", "blueprint attempts exceeded", {
                        "ep_num": working_ep,
                        "attempts": blueprint_attempts
                    })
                    # [V40.1 Critical Fix] break 대신 return으로 메서드 완전 종료
                    # break 후 blueprint=None 상태로 다음 코드 진행 방지
                    self._write_audit_summary("stage3_safety_stop")
                    return
                # 🛡️ [S-Grade Dynamic Model Switching] - 점진적 모델 업그레이드
                if reject_count == 0 and enrichment_level == 0:
                    # 1차 시도: Tier 1 (gemini-2.5-flash)
                    current_model = AIModels.TIER_1_ARCHITECT
                elif reject_count == 1 or enrichment_level == 1:
                    # 2차 시도: Tier 2 (gemini-2.5-pro)
                    current_model = AIModels.TIER_2_ARCHITECT
                    self.ui.log(f"🚀 [Emergency] 아키텍트 지능 격상: {current_model}")
                else:
                    # 3차 시도 이후: Tier 3 (gemini-3-pro-preview)
                    current_model = AIModels.TIER_3_ARCHITECT
                    self.ui.log(f"🚀 [Emergency] 아키텍트 지능 격상: {current_model}")

                self.agents['architect'].primary_model = current_model
                if hasattr(self.agents['architect'], 'model_tier'):
                    self.agents['architect'].model_tier = current_model

                self.ui.log(f"🧠 [Architect] 제 {working_ep}화 설계 시도... (Strike {reject_count}/3, Lv.{enrichment_level})")
                

                if reject_count == 0:
                    retry_feedback = arc_data.get('feedback', "")                
                # 🔥 [V35.5] 정밀도 레벨에 따른 동적 지시어 강화 (User Suggestion Applied)
                enrichment_directive = ""
                if enrichment_level > 0:
                    intensity = "HIGH" if enrichment_level == 1 else "EXTREME"
                    enrichment_directive = (
                        f"\n\n[🚨 SYSTEM OVERRIDE: ENRICHMENT LEVEL {enrichment_level} ({intensity})]\n"
                        f"현재 설계 정밀도가 부족하여 {enrichment_level}단계로 격상되었습니다. 아래 지침을 강제 이행하십시오:\n"
                        "1. **Micro-Segmentation**: 사건을 진행하려 하지 말고, 현재의 장면을 0.1초 단위로 쪼개어 묘사하십시오.\n"
                        "2. **Sensory Amplification**: 시각, 청각, 후각적 디테일을 문단마다 필수적으로 포함하십시오.\n"
                        "3. **Reaction Shot**: 주인공의 행동에 대한 조연들의 미세한 표정 변화와 귓속말을 대사에 포함하십시오."
                    )

                # 매 시도마다 새로운 아이템 수혈
                sampled_cliches = [c.get('description', '') for c in random.sample(cliche_data, min(len(cliche_data), 3))]
                sampled_locations = [l.get('name', '') + ": " + l.get('note', '') for l in random.sample(location_data, min(len(location_data), 2))]
                
                # [V40] 장르별 전투/스킬 시스템 분기
                combat_ref = ""
                genre_type = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'
                
                if genre_type == 'wuxia':
                    # 무협만 techniques 시스템 사용
                    if hasattr(self.sys, 'techniques') and hasattr(self.sys.hud, 'mental_method'):
                        combat_ref = "[⚔️ 실시간 무공/전투]: " + str(self.sys.techniques.weave_v20_combat(self.sys.hud.mental_method, '강(强)'))
                    else:
                        combat_ref = "[⚔️ 무공/전투]: 기본 무공 시스템"
                elif genre_type == 'hunter':
                    combat_ref = "[⚔️ 스킬/전투]: 각성 능력 기반 전투"
                elif genre_type == 'investment':
                    combat_ref = "[💼 협상/거래]: 비즈니스 전략 기반 교섭"
                else:
                    combat_ref = "[⚔️ 전투]: 기본 전투 시스템"
                
                tactical_references = (
                    "[💡 이번 화 수혈 아이템]\n - " + "\n - ".join(sampled_cliches) + "\n\n" +
                    "[🏮 배경 지리 레퍼런스]\n - " + "\n - ".join(sampled_locations) + "\n\n" +
                    combat_ref
                )

                # 💡 Architect 호출 (try-except 추가)

                # --- [강조 패치: Spotlight & Stop-line Logic] ---
                # 1. 이번 화 전술 섹션만 정밀 추출 (정규식 활용)


                # --- [V33.1 긴급 패치: 딕셔너리 탈출 로직] ---
                full_tactical = arc_data.get('tactical_doc', '')
                if isinstance(full_tactical, dict):
                    # 만약 AI가 구조화된 데이터를 줬다면, 이를 문자열로 평탄화하여 정규식이 읽을 수 있게 함
                    full_tactical = json.dumps(full_tactical, ensure_ascii=False, indent=2)
                # --------------------------------------------

                focus_tag = f"[제 {working_ep}화 전술 설계]"

                # 🎯 f-string의 중복 중괄호 문제를 피하기 위해 변수를 분리하여 안전하게 조립합니다.
                escaped_tag = re.escape(focus_tag) 
                pattern = escaped_tag + r".*?(?=\[제 \d+화 전술 설계\]|$)"

                match = re.search(pattern, full_tactical, re.DOTALL)
                ep_material = match.group(0).strip() if match else ""
                
                # [V39.1 패치] 정규식 실패 시 전술서 앞부분 사용
                if not ep_material or ep_material == "이번 화 상세 재료를 찾을 수 없습니다.":
                    ep_material = full_tactical[:2000]  # 앞부분만 사용
                    self.ui.log(f"   ⚠️ [Regex Fail] 정규식 매칭 실패, 전술서 앞부분({len(ep_material)}자) 사용")
                    self._audit_event("regex_fallback", "tactical doc regex failed", {
                        "ep_num": working_ep,
                        "fallback_length": len(ep_material)
                    })

                # 2. 다음 화의 비트 (정지선/브레이크 역할)
                beats = arc_data.get('beat_sequence', [])
                next_beat = beats[arc_pos] if arc_pos < len(beats) else "아크 최종 결말 및 보상"

                # [V39 패치 C] FULL_MAP 마스킹 - 미래 정보 차단
                masked_full_map = (
                    "[🚨 FULL MAP MASKED]\n"
                    "전체 아크 지도는 마스킹되었습니다.\n"
                    "MUST_FOCUS 섹션의 내용만 사용하십시오.\n"
                    "다른 화의 내용을 가져오면 즉시 REJECT됩니다."
                )
                
                # 3. 🔦 아키텍트에게 '강조 패키지'로 변환하여 전달
                focus_package = {
                    "MUST_FOCUS": ep_material,          # 🎯 이번 화 핵심 재료 (Spotlight)
                    "FULL_MAP": masked_full_map,        # 🗺️ [V39 마스킹] 미래 오염 차단
                    "STOP_LINE": next_beat,             # 🛑 넘지 말아야 할 선 (Pacing Guard)
                    "target_episode_focus": focus_tag,
                    "beat_sequence": arc_data.get('beat_sequence', []),
                    "arc_drive": arc_data.get('arc_drive', {}),
                    "joint_docs": arc_data.get('joint_docs', {}),
                    "status_shadow": arc_data.get('status_shadow', {}),
                    "v35_surgery": arc_data.get('v35_surgery', False),
                    "tactical_doc": arc_data.get('tactical_doc', ''),
                    "ep_count": arc_data.get('ep_count', 5),
                    "hybrid_composition": arc_data.get('hybrid_composition', {})
                }
                # ---------------------------------------------
                # [안전성 패치] Architect 호출 및 예외 처리
                try:
                    blueprint_candidate = self.agents['architect'].design_v20_breakdown(
                    ep_num=working_ep,
                    arc_pos=arc_pos,
                    arc_tactical_doc=focus_package,
                    martial_hud=self.sys.hud.get_v20_hud_report(),
                    encyclopedia=self.sys.lore.db.get_lore_list_by_category(None),
                    # 강화된 지시어를 맥락 최하단에 배치하여 최우선 반영 유도
                    narrative_context=str(self.current_project.get_causal_history_summary()) + f"\n{enrichment_directive}\n\n[🚨 Retry Feedback]: {retry_feedback}",
                    tactical_references=tactical_references,
                    style_guide=self.current_project.selected_tone.get('guide', '표준 웹소설 연출'),
                    prev_ms_ending=prev_ms_ending,
                    surgery_intel = self.current_project.get_surgery_intelligence(limit=3),
                    enrichment_level=enrichment_level
                    )
                except Exception as architect_err:
                    self.ui.log(f"🚨 [Architect Error] 제 {working_ep}화 설계 중 에러: {architect_err}")
                    self._audit_event("architect_error", "design_v20_breakdown failed", {
                        "ep_num": working_ep,
                        "error": str(architect_err)
                    })
                    retry_feedback = f"Architect 엔진 오류: {str(architect_err)[:100]}. 안정적인 JSON 출력을 확보하라."
                    reject_count += 1
                    continue

                # 5. 설계도 품질 및 논리 검수 (Director 가동)
                if blueprint_candidate and "integrated_scenario" in blueprint_candidate:
                    raw_content = blueprint_candidate['integrated_scenario']
                    threshold = 1200 if enrichment_level == 0 else 1000 

                    # 🧩 [Pattern Check] 블루프린트에 패턴이 반영되었는지 확인
                    # [V40.3 User Fix] gemini-2.5-pro부터는 패턴 부족으로 반려하지 않음
                    # [V40.3 User Fix] 4개 이상 장면이면 패턴 부족 무시
                    scene_count = len(blueprint_candidate.get('scene_breakdown', {}))
                    should_check_pattern = (reject_count == 0 and current_model == AIModels.TIER_1_ARCHITECT) and scene_count < 4

                    if should_check_pattern:
                        if not self._pattern_presence_check(raw_content, arc_data.get('hybrid_composition', {})):
                            self.ui.log("   🚨 [Pattern Check] 패턴 반영이 부족합니다. 재설계합니다.")
                            self._audit_event("pattern_missing", "blueprint pattern missing", {
                                "ep_num": working_ep,
                                "arc_no": arc_data.get("arc_no")
                            })
                            retry_feedback = "아크의 주/부 패턴이 장면에 드러나지 않습니다. 패턴을 최소 2개 장면에 명시적으로 반영하십시오."
                            reject_count += 1
                            time.sleep(1)
                            continue
                    else:
                        # Tier 2 이상 모델이거나 4개 이상 장면이면 패턴 부족은 경고만
                        if not self._pattern_presence_check(raw_content, arc_data.get('hybrid_composition', {})):
                            if current_model != AIModels.TIER_1_ARCHITECT:
                                self.ui.log(f"   ⚠️ [Pattern Check] 패턴 반영이 부족하지만, {current_model} 사용으로 진행합니다.")
                            elif scene_count >= 4:
                                self.ui.log(f"   ⚠️ [Pattern Check] 패턴 반영이 부족하지만, {scene_count}개 장면 확보로 진행합니다.")
                            else:
                                self.ui.log("   ⚠️ [Pattern Check] 패턴 반영이 부족하지만, 재시도 횟수를 고려하여 진행합니다.")
                            self._audit_event("pattern_warning", "blueprint pattern weak but accepted", {
                                "ep_num": working_ep,
                                "arc_no": arc_data.get("arc_no"),
                                "reject_count": reject_count,
                                "model": current_model,
                                "scene_count": scene_count
                            })

                    # [V39 패치 B] 정지선 강제 검증
                    stopline_violation = False
                    if next_beat and next_beat != "아크 최종 결말 및 보상":
                        # 다음 화의 핵심 키워드가 현재 설계도에 포함되었는지 체크
                        next_beat_keywords = next_beat[:30].strip()
                        if next_beat_keywords in raw_content:
                            self.ui.log(f"   🚨 [Stopline Violation] 다음 화 내용 감지: '{next_beat_keywords}...'")
                            retry_feedback = f"[정지선 위반] '{next_beat_keywords}'는 다음 화 내용입니다. 현재 화에서 제거하십시오."
                            reject_count += 1
                            stopline_violation = True
                    
                    if not stopline_violation:
                        # [안전성 패치] Director 호출 예외 처리
                        try:
                            # [V45] validation_context 구성 (V0128 검증용)
                            validation_context = self._build_validation_context(
                                ep_num=working_ep,
                                blueprint=blueprint_candidate,
                                mode='BLUEPRINT'
                            )
                            blueprint_audit = self.agents['director'].audit_manuscript(
                                ep_num=working_ep,
                                manuscript=raw_content,
                                arc_doc=self.current_project.arcs[arc_idx].get('tactical_doc', ''),
                                history_summary=self.current_project.get_causal_history_summary(),
                                prev_full_text=prev_ms_ending,
                                arc_pos=arc_pos,
                                total_eps=total_ep_in_arc,
                                target_len=threshold,
                                retry_count=reject_count,  # [V40.3 추가] 재시도 횟수 전달
                                validation_context=validation_context  # [V45] V0128 검증용
                            )
                        except Exception as director_err:
                            self.ui.log(f"🚨 [Director Error] 제 {working_ep}화 검수 중 에러: {director_err}")
                            self._audit_event("director_error", "audit_manuscript failed", {
                                "ep_num": working_ep,
                                "error": str(director_err)
                            })
                            # Director 실패 시 기본 통과 처리 (블로커 방지)
                            blueprint_audit = {
                                "decision": "PASS",
                                "reason": "Director 오류로 인한 기본 통과",
                                "feedback": "",
                                "score": 50
                            }
                    else:
                        continue  # 정지선 위반 시 재시도

                    if blueprint_audit.get('decision') == "PASS":
                        if self._validate_blueprint_integrity(blueprint_candidate):
                            blueprint = blueprint_candidate
                        else:
                            retry_feedback = "설계도 필수 키 누락. scene_breakdown과 integrated_scenario를 포함하라."
                            reject_count += 1
                            continue
                        self.ui.log(f"   ✅ [PASS] 제 {working_ep}화 설계도 안착.")
                        break
                    else:
                        reason = blueprint_audit.get('reason', '품질 미달')
                        feedback = blueprint_audit.get('feedback', '상세 묘사 부족')
                        score = blueprint_audit.get('score', 0)

                        # [V40.2 User Request] 2번 재시도 후에는 심각한 문제가 아니면 수용
                        if reject_count >= 2:
                            # 심각한 문제 체크 (서사 폭주, 서사 정체, 모순)
                            critical_keywords = ['서사 폭주', '서사 정체', '모순', '동선 충돌', '시간 역행', '중복', 'CRITICAL']
                            is_critical = any(kw in reason for kw in critical_keywords) or score < 20

                            if is_critical:
                                # 심각한 문제는 계속 거부
                                self.ui.log(f"   🚨 [Critical Issue] {reason} - 심각한 문제로 계속 재시도합니다.")
                                self._audit_event("critical_issue", "serious problem detected", {
                                    "ep_num": working_ep,
                                    "reason": reason,
                                    "score": score
                                })
                                retry_feedback = f"심각한 문제: {reason} -> {feedback}"
                                reject_count += 1
                            else:
                                # 심각하지 않은 문제는 경고만 하고 통과
                                self.ui.log(f"   ⚠️ [Director Warning] {reason} - 재시도 횟수를 고려하여 수용합니다.")
                                self._audit_event("quality_warning", "minor issue accepted after retries", {
                                    "ep_num": working_ep,
                                    "reason": reason,
                                    "score": score,
                                    "reject_count": reject_count
                                })
                                if self._validate_blueprint_integrity(blueprint_candidate):
                                    blueprint = blueprint_candidate
                                    self.ui.log(f"   ✅ [ACCEPTED] 제 {working_ep}화 설계도 안착 (품질 경고 포함).")
                                    break
                                else:
                                    retry_feedback = "설계도 필수 키 누락. scene_breakdown과 integrated_scenario를 포함하라."
                                    reject_count += 1
                                    continue
                        else:
                            # 일반 거부 (2번 미만)
                            self.ui.log(f"   🎬 [Director REJECT]: {reason}")
                            self.ui.log(f"   📝 [수정 지시]: {feedback}")
                            retry_feedback = f"이전 설계 거절 사유: {reason} -> {feedback}"
                            reject_count += 1
                else:
                    self.ui.log("   🚨 [Structure Error] JSON 파싱 실패 또는 필드 누락.")
                    retry_feedback = "반드시 'integrated_scenario' 필드를 포함한 유효한 JSON으로 응답하라."
                    reject_count += 1
                    time.sleep(1)

                # 6. ####== [V35.5 Pro: 다층적 역전파 자율 수술 시스템]
                if reject_count >= 3:
                    surgery_count += 1
                    
                    # [Step 1] 아크 전술서 재구성 (기존 수술 로직)
                    self.ui.log(f"🚑 [V35 Emergency] {surgery_count}차 아크 수술 및 인과관계 용접 시작")
                    
                    prev_arc = self.current_project.arcs[arc_idx-1] if arc_idx > 0 else None
                    curr_arc = self.current_project.arcs[arc_idx]
                    next_arc = self.current_project.arcs[arc_idx+1] if arc_idx < len(self.current_project.arcs)-1 else None
                    
                    surgical_feedback = f"에피소드 {working_ep} 설계 반복 실패: {retry_feedback}"

                    # [안전성 패치] Analyst를 호출하여 아크 전술서 자체를 5배 농축 보강
                    try:
                        new_arc_data = self.agents['analyst'].analyze_context(
                            mode="ARC_RECONSTRUCTION",
                            prev_arc=prev_arc, curr_arc=curr_arc, next_arc=next_arc,
                            feedback=surgical_feedback
                        )
                    except Exception as analyst_surgery_err:
                        self.ui.log(f"🚨 [Analyst Surgery Error] 아크 수술 실패: {analyst_surgery_err}")
                        self._audit_event("analyst_error", "analyze_context failed", {
                            "ep_num": working_ep,
                            "arc_idx": arc_idx,
                            "error": str(analyst_surgery_err)
                        })
                        new_arc_data = None

                    if new_arc_data and isinstance(new_arc_data, dict):
                        reference_docs = []
                        if curr_arc:
                            reference_docs.append(curr_arc.get('tactical_doc', ''))
                        if prev_arc:
                            reference_docs.append(prev_arc.get('tactical_doc', ''))
                        if reference_docs and self._is_tactical_doc_duplicate(new_arc_data.get('tactical_doc', ''), reference_docs):
                            self.ui.log("🚨 [Duplicate Guard] 수술 결과가 기존 아크와 중복됩니다. 수술을 무효 처리합니다.")
                            new_arc_data = None

                    if new_arc_data:
                        # 🔧 [V40.2 Fix] 수술 결과 무결성 검증 후 저장
                        if not self._validate_arc_integrity(new_arc_data):
                            self.ui.log(f"🚨 [Surgery Validation] Arc {arc_idx+1} 수술 결과 무결성 검증 실패")
                            self._audit_event("surgery_validation_fail", "arc integrity check failed after surgery", {
                                "arc_idx": arc_idx,
                                "missing_keys": [k for k in ["arc_no", "ep_start", "ep_end", "ep_count", "tactical_doc", "beat_sequence"] if not new_arc_data.get(k)]
                            })
                            new_arc_data = None
                        else:
                            self.current_project.arcs[arc_idx] = new_arc_data
                            self.current_project.save_v20_anchor("arcs", self.current_project.arcs)
                            self.ui.log(f"   ✨ [V35] Arc {arc_idx+1} 전술서 수술 및 DB 박제 완료.")

                            # [무결성 보완] 수술 후 페이싱 변수 재계산 (검증 통과 시에만)
                            arc_data = new_arc_data
                            total_ep_in_arc = arc_data.get('ep_count', 5)
                            arc_pos = working_ep - arc_data.get('ep_start', working_ep) + 1

                    if not new_arc_data:
                        # Analyst 수술 실패 시 무리하게 진행하지 않고 중단 가드
                        self.ui.log("🚨 [Critical] Analyst의 아크 재구성이 실패했습니다. 수동 확인이 필요합니다.")
                        break
                    
                    # ####== [Step 2] 성경 수치 강제 보정 (Bible Calibration)
                    # 수술 후 첫 번째 시도(surgery_count == 1)에서 해결되지 않을 조짐일 때 HUD 수치 교정
                    if surgery_count == 1:
                        self.ui.log("🧬 [V35.5 Calibration] HUD 수치 보정을 통한 개연성 확보 가동")
                        # [안전성 패치] calibration 호출 예외 처리
                        try:
                            calibration = self.agents['analyst'].perform_v35_calibration(
                                self.sys.hud.pro_data,
                                arc_data # 👈 arc_data 딕셔너리를 통째로 전달
                            )
                        except Exception as calibration_err:
                            self.ui.log(f"🚨 [Calibration Error] HUD 보정 실패: {calibration_err}")
                            self._audit_event("analyst_error", "perform_v35_calibration failed", {
                                "ep_num": working_ep,
                                "error": str(calibration_err)
                            })
                            calibration = None

                        if calibration and isinstance(calibration, dict):
                            # 1. 물리적 HUD 수치 강제 업데이트 및 성경 박제 (예외 처리 추가)
                            try:
                                if 'calibrated_metrics' in calibration:
                                    self.sys.hud.update_physical_status(calibration['calibrated_metrics'])
                                else:
                                    self.ui.log("⚠️ [Calibration] calibrated_metrics 누락")
                            except Exception as hud_calibration_err:
                                self.ui.log(f"🚨 [HUD Calibration Error] 수치 업데이트 실패: {hud_calibration_err}")
                                self._audit_event("hud_error", "calibration update failed", {
                                    "ep_num": working_ep,
                                    "error": str(hud_calibration_err)
                                })

                            # 2. 작가 에이전트에게 수치 상승의 정당성(기연 등)을 강제로 주입
                            if 'narrative_patch' in calibration:
                                retry_feedback += f"\n[🚨 BIBLE PATCH]: {calibration['narrative_patch']}"
                            # 3. 수술 기록 저장 (Surgery Log - 예외 처리 추가)
                            try:
                                self.current_project.record_surgery_result(
                                    working_ep, "CALIBRATION", surgical_feedback,
                                    str(calibration.get('calibrated_metrics', {}))
                                )
                            except Exception as surgery_log_err:
                                self.ui.log(f"⚠️ [Surgery Log] 기록 저장 실패: {surgery_log_err}")
                                self._audit_event("surgery_log_error", "record failed", {
                                    "ep_num": working_ep,
                                    "error": str(surgery_log_err)
                                })
                            
                            # 수치 수정 후 즉시 다시 시도 (reject_count 초기화)
                            reject_count = 0
                            enrichment_level = 0
                            continue

                    # ####== [Step 3] 자동 타임라인 되감기 (Multi-Step Backtracking)
                    # 수술과 수치 보정으로도 해결 불가능한(surgery_count >= 2) '인과의 기점' 발견 시 강제 리셋
                    if surgery_count >= 2:
                        self.ui.log("⏪ [V35.5 Backtrack] 설계 불능 판단. 타임라인 자동 되감기 실행")
                        
                        # Director의 반려 사유를 분석하여 모순이 시작된 지점으로 롤백 수행
                        rewind_ep = self.current_project.auto_backtrack_v35(
                                blueprint_audit.get('reason', '설계 불능'), 
                                self.memory
                            )
                        
                        if rewind_ep:
                            self.ui.log(f"🔄 제 {rewind_ep}화로 되감기 완료. 공정을 이 시점부터 다시 시작합니다.")
                            # [핵심] 되감기 후 DB 연결을 안전하게 커밋하고 루프 종료
                            if hasattr(self.current_project, 'db'):
                                self.current_project.db.conn.commit()
                            return 
                        else:
                            # 되감기 로직 실패 시 최후의 인간 개입 가드
                            self.ui.log("🛑 [CRITICAL] 자율 되감기 실패. 시스템을 정지합니다.")
                            choice = input("👉 직접 수정 후 [R]etry / 공정 [S]top: ").upper()
                            if choice == 'R':
                                reject_count = 0; enrichment_level = 0; surgery_count = 0; continue
                            else: return

                    # 일반적인 반려 상황 시 피드백 초기화 및 재시도
                    retry_feedback = "" 
                    reject_count = 0
                    enrichment_level = 0
                    continue 
                
                # 아직 3회 미달이면 밀도(Enrichment)만 높여서 단순 리트라이
                enrichment_level += 1

            # 7. ####== [Sovereign 결과 확정 및 트랜잭션 종료]
            if blueprint:
                # 설계도 무결성 재검증 후 박제
                if not self._validate_blueprint_integrity(blueprint):
                    self.ui.log(f"🚨 [Integrity] 제 {working_ep}화 설계도 무결성 실패로 저장 중단")
                    self._audit_event("integrity_fail", "blueprint save blocked", {"ep_num": working_ep})
                    break
                self.current_project.save_episode_blueprint(working_ep, blueprint)
                
                # [V38 패치] 안전한 커밋
                self._safe_commit()
                
                # [V45 Fix] blueprints는 anchors 테이블이 아니므로 불필요한 로드 제거
                # 개별 blueprint는 self.current_project.get_blueprint(ep_num)으로 접근
                self.ui.log(f"💾 [System] 제 {working_ep}화 설계도 최종 박제 완료.")
                working_ep += 1 
            else:
                self.ui.log(f"🚨 제 {working_ep}화 공정 최종 실패.")
                break

        self._write_audit_summary("stage3_complete")
        
        # [V40] Slack 알림 전송 (Blueprint 설계 완료 - 전체 루프 종료 후)
        if working_ep > production_head:
            completed_count = working_ep - production_head
            notifier.send_notification(
                title=f"✅ [Blueprint] 제 {production_head}~{working_ep-1}화 설계도 생성 완료",
                message=f"프로젝트: {self.current_project.name}\n생성된 화수: {completed_count}화",
                key_metrics={"완료 구간": f"{production_head} ~ {working_ep-1}화", "총 생성": f"{completed_count}개"}
            )


    def _stage_4_sovereign_writing(self, limit_mode: bool = False) -> None:
        """
        [V35.5 S-Grade] 원자적 집필 및 자동 에러 복구 파이프라인

        블루프린트 기반으로 최종 원고를 생성합니다. 디렉터 검증, 자동 에러 복구,
        스타일 일관성 유지 등의 기능을 포함합니다.

        Args:
            limit_mode: True면 특정 화수까지만 집필, False면 전체 집필

        주요 기능:
            - Quad-Cache 시스템으로 API 비용 최적화
            - 플랫폼별(카카오/네이버) 문체 최적화
            - 디렉터 검증 및 자동 되감기(Backtrack)
            - 에피소드별 원자적 저장
            - 벡터 DB 동기화

        Raises:
            Stage 0~2 설계가 선행되지 않은 경우 조기 종료
        """

        # 1. 기초 데이터 및 무결성 점검
        if not self.current_project.master_bible or not self.current_project.arcs:
            self.ui.log(f"{Emojis.ERROR} [System] {ErrorMessages.STAGE_PREREQUISITE_MISSING}")
            return

        # 2. 🔥 V30 유전자 점화 (문체 복제 엔진 가동)
        self._ignite_quad_cache_system()

        # 2-1. 🔒 [V40 Fix] Stage 4 Writer 모델을 gemini-3-pro-preview로 고정
        from modules.core.constants import AIModels
        self.agents['writer'].primary_model = AIModels.STAGE4_FIXED_WRITER_MODEL
        if hasattr(self.agents['writer'], 'model_tier'):
            self.agents['writer'].model_tier = AIModels.STAGE4_FIXED_WRITER_MODEL
        self.ui.log(f"🔒 [Stage 4] Writer 모델 고정: {AIModels.STAGE4_FIXED_WRITER_MODEL}")

        # 3. 환경 변수 초기화
        output_dir = self.current_project.paths.drafts
        output_dir.mkdir(exist_ok=True)
        # [V46 Fix] Blueprint 기준으로 최대 화수 결정 (Arc 기준 → Blueprint 기준)
        total_planned_ep = self.current_project.db.get_latest_blueprint_number()
        target_ep = None

        try:
            # 4. 플랫폼 최적화 스타일 및 도입부 DNA 설정
            if limit_mode:
                target_ep = self._get_int_input(
                    f"\n👉 몇 화까지 집필하시겠습니까? (최대 {total_planned_ep}화): ",
                    default=None,
                    min_val=1,
                    max_val=total_planned_ep
                )

            self.ui.console.clear()
            self.ui.title("V30 STYLE SELECTOR", "플랫폼 최적화 문체 설정")
            style_choice = self._get_int_input(
                "\n👉 집필 스타일을 선택하십시오 (1.카카오 / 2.네이버): ",
                default=1,
                min_val=1,
                max_val=2
            )

            # [V45 Fix] style_choice는 int이므로 정수로 비교
            selected_style = {
                "tag": "NAVER" if style_choice == 2 else "KAKAO",
                "guide": (
                    "네이버 시리즈: 유려한 문장, 심리 묘사 강조. "
                    "3~4문장 단위로 줄바꿈을 수행하여 여백을 극대화하라."
                ) if style_choice == 2 else (
                    "카카오페이지: 매 화 사이다 전개 및 절벽걸기. "
                    "설명을 생략하는 것이 아니라, 장면의 해상도를 4K 수준으로 높여라. 인물이 숨을 들이키는 찰나의 폐부 감각, 옷자락이 스치는 소리까지 문장에 녹여내라."
                )
            }
            self.current_project.selected_tone = selected_style

            # 제1화 전용 DNA 선택 UI
            if self.current_project.get_latest_episode_number() == 1:
                self.ui.title("V27 DNA SELECTOR", "도입부 서사 DNA 결정")
                dna_choice = self._get_int_input(
                    "\n👉 Choice => 1: CYNICAL / 2: CHRONICLE / 3: SENSORY / 4: PERSONAL: ",
                    default=1,
                    min_val=1,
                    max_val=4
                )
                dna_map = {1: "CYNICAL", 2: "CHRONICLE", 3: "SENSORY", 4: "PERSONAL"}
                self.current_project.intro_dna = dna_map.get(dna_choice, "CYNICAL")

            # [V40.1 Fix] 장르별 레퍼런스 데이터 로드 (공통 메서드 사용)
            cliche_data, location_data = self._load_genre_references()

            failure_streak = 0
            MAX_RETRY = WritingLimits.MAX_RETRY_PER_EPISODE  # [V40.1 Fix] 상수화
            loop_guard = 0
            max_episode_loops = (target_ep or total_planned_ep) - self.current_project.get_latest_episode_number() + 3
            if max_episode_loops < WritingLimits.MIN_EPISODE_LOOP_GUARD:
                max_episode_loops = WritingLimits.MIN_EPISODE_LOOP_GUARD

            # 5. 원고 생산 루프 (Sovereign Production)
            while True:
                loop_guard += 1
                if loop_guard > max_episode_loops:
                    self.ui.log("🛑 [Safety] 집필 루프 제한에 도달했습니다. 공정을 중단합니다.")
                    self._audit_event("safety_stop", "writing loop limit reached", {
                        "loop_guard": loop_guard,
                        "max": max_episode_loops
                    })
                    break
                try: 
                    next_ep = self.current_project.get_latest_episode_number()
                    if target_ep and next_ep > target_ep: 
                        self.ui.log(f"🏁 목표 회차({target_ep}화)에 도달하여 집필을 종료합니다.")
                        break

                    # 설계도(Blueprint) 로드
                    blueprint = self.current_project.get_blueprint(next_ep)
                    if not blueprint:
                        self.ui.log(f"⚠️ [Stop] 제 {next_ep}화 설계도가 없습니다. 3번 메뉴를 먼저 실행하십시오.")
                        break

                    # [V38 + 강화 패치] 안전한 아크 데이터 검색
                    arc_data = None
                    try:
                        if self.current_project.arcs and isinstance(self.current_project.arcs, list):
                            arc_data = next(
                                (
                                    a for a in self.current_project.arcs
                                    if isinstance(a, dict) and
                                       isinstance(a.get('ep_start'), int) and
                                       isinstance(a.get('ep_end'), int) and
                                       a.get('ep_start') <= next_ep <= a.get('ep_end')
                                ),
                                None
                            )
                    except Exception as arc_search_err:
                        self.ui.log(f"🚨 [Error] 아크 데이터 검색 중 오류: {arc_search_err}")
                        self._audit_event("data_search_error", "arc_data search failed", {
                            "ep_num": next_ep,
                            "error": str(arc_search_err)
                        })

                    if not arc_data or not isinstance(arc_data, dict):
                        self.ui.log(f"⚠️ [Stop] 제 {next_ep}화에 해당하는 아크 데이터가 없습니다.")
                        self._audit_event("data_missing", "arc_data not found for episode", {"ep_num": next_ep})
                        break

                    ep_start_val = arc_data.get('ep_start')
                    if ep_start_val is None or not isinstance(ep_start_val, int):
                        self.ui.log(f"⚠️ [Stop] 아크 ep_start 누락 또는 잘못된 타입: arc_no={arc_data.get('arc_no')}, ep_start={ep_start_val}")
                        self._audit_event("data_missing", "arc ep_start missing or invalid", {
                            "arc_no": arc_data.get("arc_no"),
                            "ep_start": ep_start_val,
                            "type": str(type(ep_start_val))
                        })
                        break
                    arc_pos = next_ep - ep_start_val + 1
                    total_ep_in_arc = arc_data.get('ep_count', 5)
                    arc_tactical = arc_data.get('tactical_doc', '설계도 내용 없음')

                    # 직전 화 원고 및 엔딩 추출 [V43 안전 패치]
                    prev_ms_data = self.current_project.db.get_manuscript(next_ep - 1)
                    prev_text = "이전 회차가 없습니다."
                    if prev_ms_data and isinstance(prev_ms_data, dict):
                        content = prev_ms_data.get('content')
                        if content and isinstance(content, str):
                            prev_text = content
                        else:
                            self.ui.log(f"⚠️ [V43] 이전 회차 content가 유효하지 않음: {type(content)}")
                            self._audit_event("data_warning", "prev manuscript content invalid", {
                                "ep_num": next_ep - 1,
                                "content_type": str(type(content))
                            })
                    try:
                        prev_ms_ending = " ".join(re.split(r'(?<=[.!?])\s+', prev_text.strip())[-3:])
                    except Exception as split_err:
                        self.ui.log(f"⚠️ [V43] prev_ms_ending 추출 실패: {split_err}")
                        prev_ms_ending = prev_text[-500:] if len(prev_text) > 500 else prev_text
                    
                    # [V38 패치] 안전한 HUD 및 자산 추출
                    causal_summary = self.current_project.get_causal_history_summary()
                    hud_report = self.sys.hud.get_v20_hud_report()
                    
                    # [V40] 적대 NPC 데이터 안전 추출 (장르 독립)
                    enemy_data = {}
                    bible_root = self.current_project.master_bible.get('MasterBible', {})
                    if isinstance(bible_root, dict):
                        asset_lib = bible_root.get('AssetLibrary', {})
                        if isinstance(asset_lib, dict):
                            key_npcs = asset_lib.get('KeyNPCs', [])
                            if isinstance(key_npcs, list):
                                main_antagonist = arc_data.get('main_antagonist', '')
                                enemy_data = next((n for n in key_npcs 
                                                 if isinstance(n, dict) and n.get('name') == main_antagonist), {})
                    
                    # [V43] 장르별 NPC HUD 키 분기 (fallback 강화)
                    genre_type = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'
                    npc_hud_keys = {
                        'wuxia': ['NPC_Martial_HUD', 'martial_hud', 'combat_stats'],
                        'hunter': ['NPC_Hunter_HUD', 'hunter_hud', 'awakening_stats'],
                        'investment': ['NPC_Finance_HUD', 'finance_hud', 'business_stats']
                    }
                    possible_keys = npc_hud_keys.get(genre_type, npc_hud_keys['wuxia'])

                    npc_hud = {}
                    if isinstance(enemy_data, dict):
                        # 가능한 키들을 순회하며 첫 번째로 발견되는 데이터 사용
                        for key in possible_keys:
                            if key in enemy_data and isinstance(enemy_data[key], dict):
                                npc_hud = enemy_data[key]
                                break
                        # 모든 키가 없으면 enemy_data 자체에서 전투 관련 필드 추출
                        if not npc_hud and enemy_data:
                            npc_hud = {k: v for k, v in enemy_data.items()
                                      if k in ['rank', 'realm', 'level', 'skills', 'combat_style', 'strength']}

                    # 유동적 서사 아이템 수혈
                    # [V44 Fix] 리스트가 비어있거나 샘플 수보다 작을 때 처리
                    sampled_cliches = []
                    if cliche_data and len(cliche_data) >= 3:
                        sampled_cliches = [c.get('description', '') for c in random.sample(cliche_data, 3)]
                    elif cliche_data:
                        sampled_cliches = [c.get('description', '') for c in cliche_data]

                    sampled_locations = []
                    if location_data and len(location_data) >= 2:
                        sampled_locations = [l.get('name', '') + ": " + l.get('note', '') for l in random.sample(location_data, 2)]
                    elif location_data:
                        sampled_locations = [l.get('name', '') + ": " + l.get('note', '') for l in location_data]

                    # [V41] 캐릭터 아키타입 참고 자료 생성
                    npc_profiles_for_arc = self._extract_npc_profiles(arc_data)
                    archetype_reference = self._get_archetype_reference_for_npcs(npc_profiles_for_arc, genre_type)

                    tactical_refs = f"[💡 연출 지침]\n{sampled_cliches}\n\n[🏮 지리]\n{sampled_locations}\n\n[👥 NPC HUD]: {json.dumps(npc_hud, ensure_ascii=False)}"
                    if archetype_reference:
                        tactical_refs += f"\n\n{archetype_reference}"

                    # 🎬 실시간 대시보드 기동
                    cockpit = self.ui.make_cockpit_layout(next_ep, hud_report, "🔗 V30 Sovereign Writing...")
                    with Live(cockpit, refresh_per_second=4, console=self.ui.console):
                        final_pure_content, final_ep_title, current_feedback = "", "", ""
                            
                        for audit_attempt in range(RetryLimits.WRITER_MAX_ATTEMPTS):
                            writer_state_updates = {}  # [V41] 초기화 (정의되지 않은 참조 방지)

                            # 🔒 [V40 Fix] Stage 4에서는 모델 변경 없이 gemini-3-pro-preview 고정 사용
                            from modules.core.constants import AIModels
                            current_writer_model = AIModels.STAGE4_FIXED_WRITER_MODEL

                            # 재시도 시에도 동일 모델 유지 (로그만 출력)
                            if audit_attempt > 0:
                                self.ui.log(f"🔄 [Retry {audit_attempt+1}] 동일 모델로 재시도: {current_writer_model}")

                            # 모델 재확인 (혹시 모를 변경 방지)
                            self.agents['writer'].primary_model = current_writer_model
                            if hasattr(self.agents['writer'], 'model_tier'):
                                self.agents['writer'].model_tier = current_writer_model

                            self.ui.layout["main"].update(Panel(f"✍️ Stage 4: 제 {next_ep}화 집필 중... (시도 {audit_attempt+1}/{RetryLimits.WRITER_MAX_ATTEMPTS})", title="Writer"))

                            fact_sheet = self.sys.lore.get_v20_fact_sheet(blueprint['integrated_scenario'])
                            vector_memory = self.memory.retrieve_high_res_context(prev_ms_ending, next_ep, n_results=3)
                            enriched_breakdown = f"{blueprint['integrated_scenario']}\n\n[🔍 참고 맥락]\n{vector_memory}\n{fact_sheet}"
                            focus_tag = f"[제 {next_ep}화 전술 설계]" # 🔦 강조 태그 생성
                            
                            # [V40] 장르별 Purism Prompt 분기
                            genre_type = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'
                            
                            if genre_type == 'wuxia' and hasattr(self.sys, 'guard'):
                                purism = self.sys.guard.get_v20_purism_prompt()
                            elif genre_type == 'hunter':
                                purism = "[헌터 장르 가이드] 각성/던전/길드 설정을 준수하라. 게임 시스템은 일관성 있게 유지하라."
                            elif genre_type == 'investment':
                                purism = "[투자 장르 가이드] 금융 상식과 시장 논리를 준수하라. 자본 증식은 개연성 있게 서술하라."
                            else:
                                purism = ""
                            
                            # 💡 Writer 집필 호출 (예외 처리 추가)
                            try:
                                writer_res = self.agents['writer'].write_v20_manuscript(
                                    ep_num=next_ep, breakdown_doc=enriched_breakdown,
                                    master_bible=self.current_project.master_bible,
                                    hud_report=hud_report, purism_prompt=purism,
                                    style_mode=selected_style["guide"], intro_dna=getattr(self.current_project, 'intro_dna', 'CYNICAL'),
                                    feedback=current_feedback, prev_full_manuscript=prev_text,
                                    arc_doc={
                                            "MUST_FOCUS_ON": focus_tag,
                                            "FULL_ARC_MAP": arc_tactical, # 전체 흐름은 맥락으로만 제공
                                            "PATTERN_PROFILE": arc_data.get('hybrid_composition', {}),
                                            "PATTERN_MIXING_LOGIC": arc_data.get('hybrid_composition', {}).get('mixing_logic', '')
                                        },
                                    tactical_references=tactical_refs
                                )
                            except Exception as writer_err:
                                self.ui.log(f"🚨 [Writer Error] 제 {next_ep}화 집필 중 에러: {writer_err}")
                                self._audit_event("writer_error", "write_v20_manuscript failed", {
                                    "ep_num": next_ep,
                                    "error": str(writer_err)
                                })
                                current_feedback = f"Writer 엔진 오류: {str(writer_err)[:100]}. 안정적인 JSON 출력을 확보하라."
                                continue

                            writer_data = writer_res if isinstance(writer_res, dict) else self.agents['writer']._extract_json_robust(writer_res)

                            if writer_data and isinstance(writer_data, dict):
                                # [V40] 장르 독립적 HUD 태그 제거
                                temp_content = re.sub(r"\[V20 (MARTIAL|HUNTER|FINANCE) HUD.*?\]", "", writer_data.get('content', ""), flags=re.DOTALL | re.IGNORECASE)
                                temp_title = writer_data.get('title', f"제 {next_ep} 화")

                                # [V41] Writer가 제안한 state_updates 추출
                                writer_state_updates = writer_data.get('state_updates', {})

                                # 🧩 [Pattern Check] 원고에 패턴 반영 여부 확인
                                # [V40.3 User Fix] gemini-2.5-pro부터는 패턴 부족으로 반려하지 않음
                                # [V40.3 User Fix] 4개 이상 장면이면 패턴 부족 무시
                                # [V45 Note] Stage 4는 STAGE4_FIXED_WRITER_MODEL 고정이므로 TIER_1 체크는 항상 False
                                # 의도적으로 Stage 4에서는 패턴 체크를 비활성화 (품질보다 일관성 우선)
                                blueprint_for_ep = self.current_project.get_blueprint(next_ep) or {}
                                scene_count = len(blueprint_for_ep.get('scene_breakdown', {}))
                                should_check_pattern = False  # [V45] Stage 4에서는 패턴 체크 비활성화

                                if should_check_pattern:
                                    if not self._pattern_presence_check(temp_content, arc_data.get('hybrid_composition', {})):
                                        self.ui.log("🚨 [Pattern Check] 패턴 반영이 부족합니다. 재집필합니다.")
                                        self._audit_event("pattern_missing", "manuscript pattern missing", {
                                            "ep_num": next_ep,
                                            "arc_no": arc_data.get("arc_no")
                                        })
                                        current_feedback = "\n[🚨 PATTERN MISSING]: 아크의 주/부 패턴을 명시적으로 드러내는 장면을 최소 2개 포함하라."
                                        continue
                                else:
                                    # Tier 2 이상 모델이거나 4개 이상 장면이면 패턴 부족은 경고만
                                    if not self._pattern_presence_check(temp_content, arc_data.get('hybrid_composition', {})):
                                        if current_writer_model != AIModels.TIER_1_WRITER:
                                            self.ui.log(f"⚠️ [Pattern Check] 패턴 반영이 부족하지만, {current_writer_model} 사용으로 진행합니다.")
                                        elif scene_count >= 4:
                                            self.ui.log(f"⚠️ [Pattern Check] 패턴 반영이 부족하지만, {scene_count}개 장면 확보로 진행합니다.")
                                        else:
                                            self.ui.log("⚠️ [Pattern Check] 패턴 반영이 부족하지만, 재시도 횟수를 고려하여 진행합니다.")
                                        self._audit_event("pattern_warning", "manuscript pattern weak but accepted", {
                                            "ep_num": next_ep,
                                            "arc_no": arc_data.get("arc_no"),
                                            "attempt": audit_attempt,
                                            "model": current_writer_model,
                                            "scene_count": scene_count
                                        })

                                # 🎬 Director 최종 원고 정밀 검수 (예외 처리 추가)
                                self.ui.layout["main"].update(Panel(f"🎬 Stage 4.5: 편집장 원고 정밀 검수 중...", title="Director"))
                                try:
                                    # [V45] validation_context 구성 (V0128 검증용)
                                    validation_context = self._build_validation_context(
                                        ep_num=next_ep,
                                        blueprint=self.current_project.get_blueprint(next_ep),
                                        mode='MANUSCRIPT'
                                    )
                                    audit_res = self.agents['director'].audit_manuscript(
                                        ep_num=next_ep, manuscript=temp_content, arc_doc=arc_tactical,
                                        history_summary=causal_summary, prev_full_text=prev_text,
                                        arc_pos=arc_pos, total_eps=total_ep_in_arc,
                                        target_len=5000,
                                        retry_count=audit_attempt,  # [V40.3 추가] 재시도 횟수 전달
                                        validation_context=validation_context  # [V45] V0128 검증용
                                    )
                                except Exception as director_err:
                                    self.ui.log(f"🚨 [Director Error] 제 {next_ep}화 원고 검수 중 에러: {director_err}")
                                    self._audit_event("director_error", "manuscript audit failed", {
                                        "ep_num": next_ep,
                                        "error": str(director_err)
                                    })
                                    # Director 실패 시 기본 통과 처리 (블로커 방지)
                                    audit_res = {
                                        "decision": "PASS",
                                        "reason": "Director 오류로 인한 기본 통과",
                                        "feedback": "",
                                        "score": 50
                                    }

                                if audit_res.get('decision') == "PASS":
                                    self.ui.log(f"✅ [Director 품질 승인] 점수: {audit_res.get('score')}")

                                    # [V41] 캐릭터 논리성 검수 (Red Team)
                                    npc_profiles = self._extract_npc_profiles(arc_data)
                                    character_traits = self._get_character_traits()

                                    logic_passed = True
                                    if npc_profiles or character_traits:
                                        try:
                                            logic_res = self.agents['director'].assess_character_logic(
                                                ep_num=next_ep,
                                                manuscript=temp_content,
                                                npc_profiles=npc_profiles,
                                                character_traits=character_traits
                                            )
                                            if logic_res.get('decision') == "REJECT":
                                                logic_passed = False
                                                severity = logic_res.get('severity', 'UNKNOWN')
                                                self.ui.log(f"🚨 [캐릭터 논리 검수] 거부 - 심각도: {severity}")
                                                self._audit_event("character_logic_reject", "character logic violation", {
                                                    "ep_num": next_ep,
                                                    "violations": logic_res.get('violations', []),
                                                    "severity": severity
                                                })
                                                current_feedback = f"\n[🚨 CHARACTER LOGIC REJECTED]: {logic_res.get('feedback', '캐릭터 행동이 설정과 불일치')}"
                                            else:
                                                self.ui.log(f"✅ [캐릭터 논리 검수] 통과 - 점수: {logic_res.get('score', 'N/A')}")
                                        except Exception as logic_err:
                                            self.ui.log(f"⚠️ [캐릭터 논리 검수] 오류 발생, 생략: {logic_err}")
                                            logic_passed = True  # 오류 시 통과 처리

                                    if not logic_passed:
                                        continue  # 캐릭터 논리 검수 실패 시 재시도

                                    # [V41] state_updates 승인 (Director Sovereignty)
                                    approved_state_updates = {}
                                    if writer_state_updates:
                                        try:
                                            approval_res = self.agents['director'].on_approve_workflow(
                                                ep_num=next_ep,
                                                state_updates=writer_state_updates,
                                                current_hud=self.current_project.latest_state,
                                                martial_manager=self.sys.hud
                                            )
                                            approved_state_updates = approval_res.get('applied_updates', {})
                                            rejected_updates = approval_res.get('rejected_updates', {})
                                            warnings = approval_res.get('warnings', [])

                                            # 로그 출력
                                            if approved_state_updates:
                                                self.ui.log(f"✅ [State Updates 승인] {len(approved_state_updates)}개 항목")
                                            if rejected_updates:
                                                self.ui.log(f"⚠️ [State Updates 거부] {len(rejected_updates)}개 항목: {list(rejected_updates.keys())}")
                                            for w in warnings[:3]:  # 최대 3개 경고만 출력
                                                self.ui.log(f"   ↳ {w}")

                                            self._audit_event("state_updates_approval", "Writer state_updates processed", {
                                                "ep_num": next_ep,
                                                "approved": list(approved_state_updates.keys()),
                                                "rejected": list(rejected_updates.keys()),
                                                "warnings_count": len(warnings)
                                            })
                                        except Exception as approval_err:
                                            self.ui.log(f"⚠️ [State Updates 승인] 오류 발생: {approval_err}")
                                            approved_state_updates = writer_state_updates  # 오류 시 원본 사용

                                    # [V41] 승인된 state_updates를 임시 저장 (Stage 5에서 사용)
                                    self._v41_approved_state_updates = approved_state_updates

                                    final_pure_content = temp_content
                                    final_ep_title = temp_title
                                    self.ui.log(f"✅ [Director 최종 승인] 제 {next_ep}화 무결성 확인 완료.")
                                    break
                                else:
                                    reason = audit_res.get('reason', '품질 미달')
                                    feedback = audit_res.get('feedback', '상세 묘사 부족')
                                    score = audit_res.get('score', 0)

                                    # [V40.2 User Request] 2번 재시도 후에는 심각한 문제가 아니면 수용
                                    if audit_attempt >= 2:
                                        # 심각한 문제 체크 (서사 폭주, 서사 정체, 모순)
                                        critical_keywords = ['서사 폭주', '서사 정체', '모순', '동선 충돌', '시간 역행', '중복', 'CRITICAL']
                                        is_critical = any(kw in reason for kw in critical_keywords) or score < 20

                                        if is_critical:
                                            # 심각한 문제는 계속 거부
                                            self.ui.log(f"🚨 [Critical Issue] {reason} - 심각한 문제로 계속 재시도합니다.")
                                            self._audit_event("critical_issue", "serious problem in manuscript", {
                                                "ep_num": next_ep,
                                                "reason": reason,
                                                "score": score
                                            })
                                            current_feedback = f"\n[🚨 CRITICAL REJECTED]: {reason} -> {feedback}"
                                        else:
                                            # 심각하지 않은 문제는 경고만 하고 통과
                                            self.ui.log(f"⚠️ [Director Warning] {reason} - 재시도 횟수를 고려하여 수용합니다.")
                                            self._audit_event("quality_warning", "minor issue accepted in manuscript", {
                                                "ep_num": next_ep,
                                                "reason": reason,
                                                "score": score,
                                                "attempt": audit_attempt
                                            })

                                            # [V41] 재시도 완화 경로에서도 state_updates 승인 처리
                                            approved_state_updates = {}
                                            if writer_state_updates:
                                                try:
                                                    approval_res = self.agents['director'].on_approve_workflow(
                                                        ep_num=next_ep,
                                                        state_updates=writer_state_updates,
                                                        current_hud=self.current_project.latest_state,
                                                        martial_manager=self.sys.hud
                                                    )
                                                    approved_state_updates = approval_res.get('applied_updates', {})
                                                    if approved_state_updates:
                                                        self.ui.log(f"✅ [State Updates 승인] {len(approved_state_updates)}개 항목 (완화 경로)")
                                                except Exception as approval_err:
                                                    self.ui.log(f"⚠️ [State Updates] 승인 오류: {approval_err}")
                                                    approved_state_updates = writer_state_updates
                                            self._v41_approved_state_updates = approved_state_updates

                                            final_pure_content = temp_content
                                            final_ep_title = temp_title
                                            self.ui.log(f"✅ [ACCEPTED] 제 {next_ep}화 원고 수용 (품질 경고 포함).")
                                            break
                                    else:
                                        # 일반 거부 (2번 미만)
                                        self.ui.log(f"🚨 [Director 반려] 사유: {reason}")
                                        current_feedback = f"\n[🚨 REJECTED]: {reason} -> {feedback}"
                            else:
                                self.ui.log(f"🚨 [Structure Error] Writer JSON 파싱 실패")
                                current_feedback = "\n[🚨 System Error]: JSON 규격을 엄수하여 다시 집필하라."

                        if not final_pure_content:
                            self.ui.log(f"❌ [Critical] 제 {next_ep}화 집필 최종 실패."); return 
                    



 # 💼 Stage 5: 데이터 정산 및 박제 중...
                        self.ui.layout["main"].update(Panel(f"💼 Stage 5: 데이터 정산 및 박제 중...", title="Manager"))
                        
                        try:
                            # 1. Manager로부터 정산 데이터 수신 (예외 처리 강화)
                            try:
                                raw_res = self.agents['manager'].update_state_and_lore_v20(
                                    next_ep,
                                    final_pure_content,
                                    self.current_project.latest_state,
                                    self.sys.lore.db.get_lore_list_by_category(None),
                                    [s for s in self.current_project.master_bible.get('MasterBible', {}).get('Seeds', []) if s.get('status') == 'active'],
                                    causal_history=causal_summary
                                )
                            except Exception as manager_call_err:
                                self.ui.log(f"🚨 [Manager Error] 정산 엔진 호출 실패: {manager_call_err}")
                                self._audit_event("manager_error", "update_state_and_lore_v20 failed", {
                                    "ep_num": next_ep,
                                    "error": str(manager_call_err)
                                })
                                raise Exception(f"Manager 호출 실패: {manager_call_err}")

                            # 2. 🛡️ [V43 강화] 강제 파싱 및 빈 응답 방어
                            if raw_res is None:
                                self.ui.log("⚠️ [Manager] 빈 응답(None) 반환. 기본 정산으로 진행합니다.")
                                self._audit_event("manager_warning", "empty response from Manager", {"ep_num": next_ep})
                                audit = {}
                            elif isinstance(raw_res, str):
                                audit = self.agents['manager']._extract_json_robust(raw_res)
                                if audit is None:
                                    self.ui.log("⚠️ [Warning] 정산 데이터 파싱 실패. 빈 객체로 대체합니다.")
                                    audit = {}
                            elif isinstance(raw_res, dict):
                                audit = raw_res
                            else:
                                self.ui.log(f"⚠️ [Manager] 예상치 못한 응답 타입: {type(raw_res)}")
                                self._audit_event("manager_warning", "unexpected response type", {
                                    "ep_num": next_ep,
                                    "type": str(type(raw_res))
                                })
                                audit = {}

                            # 3. 데이터 정산 및 HUD 연동용 딕셔너리 생성
                            actual_truth_data = {}
                            # 이전 상태 데이터 확보 (데이터 유실 시 복원용)
                            prev_actual = self.current_project.latest_state.get('actual_truth', {})

                            # [V41] Director가 승인한 state_updates 우선 적용
                            v41_approved = getattr(self, '_v41_approved_state_updates', {})
                            if v41_approved:
                                self.ui.log(f"🎯 [V41 Director Sovereignty] 승인된 state_updates 적용 ({len(v41_approved)}개 항목)")
                                actual_truth_data.update(v41_approved)

                            # 4. 🛡️ Manager state_updates 추출 (보조 데이터 - Director 승인분과 병합)
                            raw_updates = audit.get('state_updates', {})

                            # [V40.1 Critical Fix] Manager JSON 스키마 준수
                            manager_updates = {}
                            if isinstance(raw_updates, dict):
                                # 1순위: actual_truth 키 사용 (정상 경로 - Manager 프롬프트 스키마)
                                if 'actual_truth' in raw_updates:
                                    manager_updates = raw_updates['actual_truth']
                                    self.ui.log(f"✅ [HUD] Manager actual_truth 데이터 추출 (키 개수: {len(manager_updates)})")
                                # 2순위: 전체 딕셔너리 사용 (레거시 대응)
                                else:
                                    manager_updates = raw_updates
                                    self.ui.log(f"⚠️ [HUD] actual_truth 키 없음. raw_updates 전체 사용 (키 개수: {len(manager_updates)})")
                            elif isinstance(raw_updates, list):
                                # 리스트 형식 대응 (예외 케이스)
                                for item in raw_updates:
                                    if isinstance(item, dict):
                                        t = item.get("target") or item.get('"target"')
                                        v = item.get("value") or item.get('"value"')
                                        if t: manager_updates[str(t).strip("'\" ")] = v
                                self.ui.log(f"⚠️ [HUD] 리스트 형식 state_updates 감지 (항목 수: {len(manager_updates)})")
                            else:
                                self.ui.log(f"🚨 [HUD] state_updates 형식 오류: {type(raw_updates)}")
                                manager_updates = {}

                            # [V41] Director 승인분이 없는 키만 Manager 데이터로 보충
                            for k, v in manager_updates.items():
                                if k not in actual_truth_data:
                                    actual_truth_data[k] = v

                            # [디버깅] actual_truth_data 구조 확인
                            if actual_truth_data:
                                self.ui.log(f"🔍 [DEBUG] actual_truth_data 주요 키: {list(actual_truth_data.keys())[:10]}")
                                if 'actual_truth' in actual_truth_data:
                                    self.ui.log(f"🚨 [WARNING] actual_truth가 중첩되어 있음! HUD 업데이트 실패 예상")

                            # 5. 🛡️ [무결성 가드] 필수 서사 지표 유실 방지 (None이면 이전 화 값 계승)
                            # [V43 패치] 장르별 critical_keys 동적 로드 (fallback 강화)
                            genre_type = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'
                            genre_fallback_keys = {
                                'wuxia': ['alias', 'rank', 'realm', 'internal_energy', 'mental_method', 'reputation'],
                                'hunter': ['awakening_rank', 'mana', 'skills', 'guild', 'level', 'reputation'],
                                'investment': ['capital', 'total_assets', 'reputation', 'connections', 'market_insight']
                            }
                            default_keys = genre_fallback_keys.get(genre_type, genre_fallback_keys['wuxia'])

                            if hasattr(self.sys, 'hud') and self.sys.hud:
                                try:
                                    critical_keys = self.sys.hud.get_critical_keys()
                                    for key in critical_keys:
                                        if key not in actual_truth_data or actual_truth_data[key] in [None, "None", ""]:
                                            actual_truth_data[key] = prev_actual.get(key, "기록 없음")
                                except Exception as hud_key_err:
                                    self.ui.log(f"⚠️ [HUD] critical_keys 추출 실패: {hud_key_err}")
                                    # [V43] 장르별 기본 키 사용
                                    self.ui.log(f"   → 장르({genre_type})별 기본 키로 대체: {default_keys}")
                                    for key in default_keys:
                                        if key not in actual_truth_data:
                                            actual_truth_data[key] = prev_actual.get(key, "기록 없음")
                            else:
                                self.ui.log("⚠️ [HUD] HUD 시스템이 초기화되지 않았습니다. 장르별 기본 키만 사용합니다.")
                                for key in default_keys:
                                    if key not in actual_truth_data:
                                        actual_truth_data[key] = prev_actual.get(key, "기록 없음")

                            # 6. 물리 상태 업데이트 실행 (HUD 실시간 반영)
                            if actual_truth_data and hasattr(self.sys, 'hud') and self.sys.hud:
                                try:
                                    # 정제된 딕셔너리를 주입하여 'AttributeError' 방지
                                    changes = self.sys.hud.update_physical_status(actual_truth_data)
                                    for c in changes:
                                        self.ui.log(f"🔥 [HUD Update] {c}")
                                except Exception as hud_update_err:
                                    self.ui.log(f"🚨 [HUD] 상태 업데이트 실패: {hud_update_err}")
                                    self._audit_event("hud_update_error", "failed to update HUD", {
                                        "ep_num": next_ep,
                                        "error": str(hud_update_err)
                                    })

                            # [V45] 새 아이템 자동 동기화 (Writer 창작 아이템 → Encyclopedia 등록)
                            if hasattr(self.sys, 'lore') and self.sys.lore:
                                try:
                                    old_equipment = prev_actual.get('equipment', [])
                                    new_equipment = actual_truth_data.get('equipment', [])
                                    sync_result = self.sys.lore.sync_equipment_to_encyclopedia(
                                        old_equipment=old_equipment,
                                        new_equipment=new_equipment,
                                        ep_num=next_ep
                                    )
                                    if sync_result.get('added'):
                                        self.ui.log(f"📦 [Item Sync] {len(sync_result['added'])}개 신규 아이템 등록 완료")
                                        self._audit_event("item_sync", "new items registered", {
                                            "ep_num": next_ep,
                                            "added_items": sync_result['added']
                                        })
                                except Exception as sync_err:
                                    self.ui.log(f"⚠️ [Item Sync] 동기화 실패 (비치명적): {sync_err}")

                            # [V38 패치] 원자적 커밋 전 안전 체크
                            try:
                                success = self.current_project.commit_full_episode_data(
                                    ep_num=next_ep, 
                                    manuscript_data={'title': final_ep_title, 'content': final_pure_content},
                                    martial_data=actual_truth_data, 
                                    state_data=audit, 
                                    causal_links=audit.get('causal_links', []),
                                    karma_data=audit.get('karma_matrix', []), 
                                    lore_data=audit.get('new_lore', {}),
                                    recovered_seeds=audit.get('recovered_seeds', []), 
                                    memory_engine=self.memory
                                )
                            except Exception as commit_error:
                                self.ui.log(f"🚨 [DB] 데이터 커밋 중 오류: {commit_error}")
                                success = False

                            if success:
                                # [V35 Fix] 제목 중복 방지 로직
                                clean_title = final_ep_title.strip()
                                # '제 N 화' 패턴이 이미 제목에 포함되어 있다면, 앞부분을 제거하거나 그대로 사용
                                if re.match(r"^제\s*\d+\s*화", clean_title):
                                    full_title_line = clean_title
                                else:
                                    full_title_line = f"제 {next_ep:04d} 화 - {clean_title}"

                                # [V35 Fix] Content JSON Leakage 방어
                                # 만약 본문이 JSON 형태의 문자열로 시작한다면, 억지로라도 텍스트만 추출 시도
                                if final_pure_content.strip().startswith("{") and "content" in final_pure_content:
                                    try:
                                        # 비상 파싱 시도
                                        temp_json = json.loads(final_pure_content)
                                        if "content" in temp_json:
                                            final_pure_content = temp_json["content"]
                                    except Exception as e:
                                        self.ui.log(f"⚠️ [Parse] 본문 JSON 정규화 실패: {e}")

                                (output_dir / f"{next_ep:04d}.txt").write_text(f"{full_title_line}\n\n{final_pure_content}", encoding="utf-8")
                                self.current_project.save_v20_anchor("bible", self.current_project.master_bible)

                                # [V40 Premium] 참조 앵커 추출 및 저장
                                try:
                                    from modules.core.reference_anchor import ReferenceAnchor
                                    anchor_sys = ReferenceAnchor(self.current_project)

                                    # 원고에서 주요 사건 추출
                                    new_anchors = anchor_sys.extract_anchors_from_manuscript(
                                        ep_num=next_ep,
                                        manuscript_content=final_pure_content
                                    )

                                    # 유효성 검증: 리스트이고, 각 항목이 딕셔너리이며 필수 키가 있는지 확인
                                    if new_anchors and isinstance(new_anchors, list):
                                        valid_anchors = [
                                            a for a in new_anchors
                                            if isinstance(a, dict) and 'type' in a and 'summary' in a and 'ep_num' in a
                                        ]

                                        if valid_anchors:
                                            anchor_sys.save_anchors(valid_anchors)
                                            self.ui.log(f"      🔗 [Anchor] {len(valid_anchors)}개 사건 앵커 저장 완료")
                                        elif new_anchors:
                                            # 추출은 되었으나 유효하지 않은 데이터
                                            self.ui.log(f"      ⚠️ [Anchor] 추출된 앵커 {len(new_anchors)}개 중 유효한 데이터 없음")

                                except ImportError as ie:
                                    self.ui.log(f"      ⚠️ [Anchor] ReferenceAnchor 모듈 로드 실패: {ie}")
                                except AttributeError as ae:
                                    self.ui.log(f"      ⚠️ [Anchor] 프로젝트 컨텍스트 오류: {ae}")
                                except Exception as anchor_err:
                                    self.ui.log(f"      ⚠️ [Anchor] 앵커 추출 실패: {type(anchor_err).__name__}: {anchor_err}")

                                # [V40 Premium] 감정선 추적 및 저장
                                try:
                                    from modules.core.emotion_tracker import EmotionArcTracker
                                    emotion_tracker = EmotionArcTracker(self.current_project)
                                    emotion_tracker.load_from_db(self.current_project.db)

                                    # 원고 감정 분석
                                    emotion_state, intensity = emotion_tracker.analyze_manuscript_emotion(final_pure_content)

                                    # 유효성 검증
                                    if emotion_state in EmotionArcTracker.EMOTION_STATES:
                                        # 이력에 추가
                                        emotion_tracker.add_episode_emotion(next_ep, emotion_state, intensity)

                                        # DB 저장
                                        emotion_tracker.save_to_db(self.current_project.db)

                                        self.ui.log(f"      🎭 [Emotion] {emotion_state} (강도: {intensity:.2f}) 추적 완료")
                                    else:
                                        self.ui.log(f"      ⚠️ [Emotion] 인식된 감정 상태 '{emotion_state}'가 유효하지 않음")

                                except ImportError as ie:
                                    self.ui.log(f"      ⚠️ [Emotion] EmotionTracker 모듈 로드 실패: {ie}")
                                except AttributeError as ae:
                                    self.ui.log(f"      ⚠️ [Emotion] 프로젝트 컨텍스트 오류: {ae}")
                                except Exception as emotion_err:
                                    self.ui.log(f"      ⚠️ [Emotion] 감정선 추적 실패: {type(emotion_err).__name__}: {emotion_err}")

                                self.ui.log(f"✅ 제 {next_ep}화 S등급 박제 완료!"); failure_streak = 0
                            else:
                                raise Exception("DB 트랜잭션 커밋 실패 (False 반환)")

                        except Exception as e:
                            # [V38 패치] 안전한 커밋 (트랜잭션 정리)
                            self.ui.log(f"🛑 [Surgical Error] 정산 엔진 충돌: {str(e)}")
                            # [V45 Fix] _safe_commit은 커밋 수행. 오류 시 내부에서 자동 롤백
                            self._safe_commit()
                            
                            failure_streak += 1
                            
                            # [V39.1 패치] Stage 4 자동 복구 연동
                            if failure_streak >= 2:
                                self.ui.log("⏪ [V39.1 Backtrack] 정산 실패 2회 감지. 타임라인 자동 되감기 실행")
                                rewind_ep = self.current_project.auto_backtrack_v35(
                                    f"정산 엔진 충돌: {str(e)}", 
                                    self.memory
                                )
                                if rewind_ep:
                                    self.ui.log(f"🔄 제 {rewind_ep}화로 되감기 완료. 공정을 이 시점부터 다시 시작합니다.")
                                    if hasattr(self.current_project, 'db'):
                                        self.current_project.db.conn.commit()
                                    return
                            
                            if failure_streak >= MAX_RETRY: 
                                self.ui.log("🛑 치명적 오류 반복으로 인해 집필 라인을 긴급 정지합니다.")
                                break
                            time.sleep(5)                   



                except Exception as e:
                    failure_streak += 1
                    self.ui.log(f"🚨 [System Error] {str(e)}. (연속 에러: {failure_streak}/{MAX_RETRY})")
                    
                    # [V38 패치] 안전한 롤백으로 변경
                    self._safe_commit()  # 롤백 포함
                    
                    # [V39.1 패치] Stage 4 시스템 에러 자동 복구
                    if failure_streak >= 2:
                        self.ui.log("⏪ [V39.1 Backtrack] 시스템 에러 2회 감지. 타임라인 자동 되감기 실행")
                        rewind_ep = self.current_project.auto_backtrack_v35(
                            f"시스템 에러: {str(e)}", 
                            self.memory
                        )
                        if rewind_ep:
                            self.ui.log(f"🔄 제 {rewind_ep}화로 되감기 완료. 공정을 이 시점부터 다시 시작합니다.")
                            if hasattr(self.current_project, 'db'):
                                self.current_project.db.conn.commit()
                            return
                    
                    if failure_streak >= MAX_RETRY: 
                        self.ui.log("🛑 치명적 오류 반복으로 인해 집필 라인을 긴급 정지합니다.")
                        break
                    
                    time.sleep(5)
        finally:
            # 🛑 finally에서는 커밋하지 않고 연결 상태만 관리 (성공 시엔 이미 커밋됨)
            self._write_audit_summary("stage4_complete")
                    

    def _select_genre(self) -> Dict[str, Any]:
        """
        [V40 Enhanced] 장르 선택 시스템
        
        Returns:
            Dict: 선택된 장르 정보
        """
        self.ui.console.clear()
        self.ui.title("V40 GENRE SELECTOR", "장르별 전문 공정 선택")
        
        genres = {
            "1": {
                "name": f"{GenreTypes.get_name(GenreTypes.WUXIA)} (Wuxia)",
                "type": GenreTypes.WUXIA,
                "hud_key": HUDKeys.WUXIA_HUD_ROOT,
                "description": "강호 배경, 내공/경지 시스템, 무림 세력",
                "critical_keys": ['realm', 'internal_energy', 'mental_method', 'wealth', 'reputation', 'causal_injuries', 'current_objective']
            },
            "2": {
                "name": f"{GenreTypes.get_name(GenreTypes.HUNTER)} (Hunter Fantasy)",
                "type": GenreTypes.HUNTER,
                "hud_key": HUDKeys.HUNTER_HUD_ROOT,
                "description": "현대 배경, 각성/던전 시스템, 길드",
                "critical_keys": ['awakening_rank', 'mana', 'skills', 'wealth', 'reputation', 'injuries', 'guild', 'level']
            },
            "3": {
                "name": f"{GenreTypes.get_name(GenreTypes.INVESTMENT)} (Investment Fiction)",
                "type": GenreTypes.INVESTMENT,
                "hud_key": HUDKeys.INVESTMENT_HUD_ROOT,
                "description": "금융 배경, 자본/투자 시스템, 기업/시장",
                "critical_keys": ['capital', 'total_assets', 'stocks', 'reputation', 'connections', 'market_insight', 'status']
            }
        }
        
        print(f"\n{Emojis.BOOK} [V40 Multi-Genre Factory] 장르를 선택하십시오:\n")
        for key, genre in genres.items():
            print(f"   {key}. {genre['name']}")
            print(f"      → {genre['description']}\n")
        
        choice = self._get_int_input(
            f"{Emojis.PENCIL} Choice (1.무협 / 2.헌터 / 3.투자): ",
            default=1,
            min_val=1,
            max_val=3
        )
        
        selected = genres[str(choice)]
        self.ui.log(f"✅ [{selected['name']}] 전문 공정이 선택되었습니다.")
        self.ui.log(f"   📌 HUD 시스템: {selected['type'].upper()}")
        
        input("\n[Enter] 프로젝트 선택으로 이동")
        
        return selected
    
    def _select_project(self) -> str:
        """
        프로젝트 선택 UI

        projects 폴더 내 디렉토리 목록을 표시하고 사용자 선택을 받습니다.

        Returns:
            str: 선택된 프로젝트 이름
        """
        root = Path("projects")
        projects = [d.name for d in root.iterdir() if d.is_dir()]
        for i, p in enumerate(projects):
            print(f" {i+1}. {p}")
        idx = (self._get_int_input("\n👉 Choice: ", default=1, min_val=1, max_val=len(projects)) or 1) - 1
        return projects[idx]


    def _reset_stage_2(self):
        """[V20] Stage 2(Arcs)만 SQL DB에서 삭제하여 1번 완료 상태로 회귀"""
        confirm = input("\n🚨 정말로 Stage 2(Arcs) 설계 데이터를 삭제하시겠습니까? (y/n): ").strip().lower()
        if confirm == 'y':
            # SQL DB에서 'arcs' 앵커만 삭제합니다.
            self.current_project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
            self.current_project.db.conn.commit()
            
            # 메모리에서도 아크 데이터를 비웁니다.
            self.current_project.arcs = []
            
            self.ui.log("✅ Stage 2 데이터가 삭제되었습니다. 이제 메뉴에서 2번 [❌] 상태로 보일 것입니다.")
            input("\n[Enter] 메뉴로 돌아가기")



    def _rewind_stage_2(self):
        """[V20] 특정 아크 번호부터 그 이후를 전부 삭제 (정밀 되감기)"""
        if not hasattr(self.current_project, 'arcs') or not self.current_project.arcs:
            self.ui.log("❌ 삭제할 아크 데이터가 없습니다.")
            return

        total_arcs = len(self.current_project.arcs)
        self.ui.log(f"📊 현재 총 {total_arcs}개의 아크가 설계되어 있습니다.")
        
        target_input = input(f"\n👉 몇 번 아크부터 새로 시작하시겠습니까? (1~{total_arcs} 입력) [한 번에 5개까지만 해라 웬만하면]: ").strip()
        
        if not target_input.isdigit():
            self.ui.log("❌ 숫자만 입력 가능합니다.")
            return
            
        target_no = int(target_input)
        
        # 입력한 번호 직전까지만 남깁니다. (예: 7 입력 시 1~6번까지만 유지)
        updated_arcs = [a for a in self.current_project.arcs if a['arc_no'] < target_no]
        
        confirm = input(f"⚠️ Arc {target_no}번부터 {total_arcs}번까지 삭제합니다. 계속할까요? (y/n): ").strip().lower()
        if confirm == 'y':
            # 1. SQL DB 업데이트 (덮어쓰기 방식)
            self.current_project.save_v20_anchor("arcs", updated_arcs)
            
            # 2. 실시간 메모리 동기화
            self.current_project.arcs = updated_arcs
            
            self.ui.log(f"✨ Arc {target_no}번 이후 데이터가 삭제되었습니다.")
            self.ui.log(f"🔄 이제 2번 메뉴를 실행하면 {target_no}번부터 다시 설계를 시작합니다.")
            input("\n[Enter] 메뉴로 돌아가기")            




    def _rollback_episode(self):
        """[V40.1 Rollback] 특정 회차로 되감기 (HUD, DB, Vector DB, 파일 모두 롤백)"""
        latest_ep = self.current_project.get_latest_episode_number()

        if latest_ep == 0:
            self.ui.log("❌ 롤백할 에피소드가 없습니다.")
            return

        self.ui.log(f"📊 현재 최신 에피소드: {latest_ep}화")
        target_input = input(f"\n👉 몇 화로 되감기하시겠습니까? (1~{latest_ep} 입력, 1 입력 시 전체 삭제): ").strip()

        if not target_input.isdigit():
            self.ui.log("❌ 숫자만 입력 가능합니다.")
            return

        target_ep = int(target_input)

        if target_ep < 1 or target_ep > latest_ep:
            self.ui.log(f"❌ 1~{latest_ep} 범위 내에서 입력해주세요.")
            return

        confirm = input(f"\n⚠️ [{target_ep}화 이후 삭제] 모든 데이터가 {target_ep}화 직전 상태로 되돌아갑니다. 계속할까요? (y/n): ").strip().lower()
        if confirm != 'y':
            self.ui.log("❌ 취소되었습니다.")
            return

        try:
            import json
            from pathlib import Path

            # 1. 📉 HUD 롤백 (state_logs에서 이전 화의 HUD 복구)
            if target_ep > 1:
                self.current_project.db.cursor.execute("SELECT data FROM state_logs WHERE ep_num = ?", (target_ep - 1,))
                row = self.current_project.db.cursor.fetchone()
                if row:
                    past_data = json.loads(row['data'])
                    past_actual = past_data.get('state_updates', {}).get('actual_truth')

                    if past_actual:
                        # Bible의 HUD를 롤백
                        self.current_project.db.cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
                        bible_row = self.current_project.db.cursor.fetchone()
                        if bible_row:
                            bible_data = json.loads(bible_row['data'])
                            if 'MasterBible' in bible_data and 'MartialHUD' in bible_data['MasterBible']:
                                bible_data['MasterBible']['MartialHUD']['Protagonist']['actual_truth'] = past_actual
                                self.current_project.db.cursor.execute(
                                    "UPDATE anchors SET data = ? WHERE key = 'bible'",
                                    (json.dumps(bible_data, ensure_ascii=False),)
                                )
                                self.ui.log(f"   📉 [Rollback] HUD를 {target_ep-1}화 시점으로 복구했습니다.")
                                # 메모리에도 반영
                                self.current_project.master_bible = bible_data

            # 2. ✂️ SQL DB 데이터 삭제
            ep_tables = [
                'manuscripts', 'blueprints', 'state_logs', 'martial_tracker',
                'sync_status', 'causal_graph'
            ]

            for t in ep_tables:
                self.current_project.db.cursor.execute(f"DELETE FROM {t} WHERE ep_num >= ?", (target_ep,))
                self.ui.log(f"   ✂️  '{t}' 테이블: {target_ep}화 이후 삭제 완료")

            # 3. 로어, 카르마, 씨드 처리
            self.current_project.db.cursor.execute("DELETE FROM encyclopedia") # 인과 꼬임 방지
            self.current_project.db.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
            self.current_project.db.cursor.execute(
                "UPDATE seeds SET status = 'active', recovered_ep = NULL WHERE recovered_ep >= ?",
                (target_ep,)
            )
            self.ui.log("   📚 [Lore/Seeds] 인과 관계 초기화 완료")

            # 4. 🔢 ID 카운터 초기화 (sqlite_sequence)
            seq_targets = "('manuscripts', 'blueprints', 'state_logs', 'martial_tracker', 'causal_graph', 'sync_status')"
            self.current_project.db.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN {seq_targets}")
            self.ui.log("   🔢 [Sequence] 테이블 ID 카운터 초기화 완료")

            # 커밋
            self.current_project.db.conn.commit()

            # 5. 📝 물리 파일 삭제
            for f in self.current_project.paths.drafts.glob("*.txt"):
                try:
                    # 파일명 앞 4자리가 숫자이고, target_ep 이상이면 삭제
                    if f.name[:4].isdigit() and int(f.name[:4]) >= target_ep:
                        f.unlink()
                except (OSError, ValueError, IndexError):
                    pass
            self.ui.log("   📂 원고 파일 삭제 완료")

            # 6. 🌌 벡터 DB 소거
            try:
                if self.memory and hasattr(self.memory, 'collection'):
                    self.memory.collection.delete(where={"episode": {"$gte": target_ep}})
                    self.ui.log("   🌌 벡터 메모리 소거 완료")
                else:
                    self.ui.log("   ⚠️ [VectorDB] 메모리 미초기화로 벡터 소거 생략")
            except Exception as e:
                self.ui.log(f"   ⚠️ [VectorDB] 소거 실패: {e}")

            # 7. 데이터 리로드
            self.current_project._load_from_db()

            self.ui.log(f"\n✅ [Success] {target_ep}화 직전 상태로 롤백 완료!")
            self.ui.log(f"👉 이제 Stage 4를 실행하면 {target_ep}화부터 새로 집필합니다.")
            input("\n[Enter] 메뉴로 돌아가기")

        except Exception as e:
            self.ui.log(f"❌ 롤백 실패: {e}")
            import traceback
            traceback.print_exc()



    def _wipe_production_data(self):
        """[V27.1 Wipe] 설계도는 유지하고 실제 집필 기록(Manuscripts/Blueprints)만 소거"""
        confirm = input("\n🚨 [WIPE] 설계도는 남기고 '실제 원고' 기록만 모두 삭제할까요? (y/n): ").strip().lower()
        if confirm != 'y': return

        try:
            # 1. 생산 데이터 테이블만 정밀 타격 (설계도 앵커는 건드리지 않음)
            production_tables = [
                'manuscripts', 'blueprints', 'state_logs', 'martial_tracker', 
                'causal_graph', 'sync_status', 'karma_status'
            ]
            
            for t in production_tables:
                self.current_project.db.cursor.execute(f"DELETE FROM {t}")
            
            # 2. 복선 상태 복구
            self.current_project.db.cursor.execute("UPDATE seeds SET status = 'active', recovered_ep = NULL")
            self.current_project.db.conn.commit()

            # 3. 물리 파일 및 벡터 메모리 삭제
            for f in self.current_project.paths.drafts.glob("*.txt"): f.unlink()
            
            # 벡터 DB 컬렉션 초기화
            try:
                self.memory.collection.delete(where={"episode": {"$gt": 0}})
            except Exception as e:
                self.ui.log(f"⚠️ [VectorDB] 컬렉션 초기화 실패: {e}")

            self.ui.log("✅ [Wipe] 원고 기록이 청소되었습니다. 이제 1화부터 다시 생산 가능합니다.")
            input("\n[Enter] 메뉴로 돌아가기")
        except Exception as e:
            self.ui.log(f"❌ 리셋 실패: {e}")            
if __name__ == "__main__":
    SovereignApp().boot()