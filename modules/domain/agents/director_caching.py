"""
[V64 P2-1] Director CachingManager — 캐시 관리 전담 모듈

Director God Object 분해의 첫 번째 단계.
원고 캐시 생성, 원고 역사 구성, protagonist_config 캐싱을 담당.
"""

from .base_agent import BaseAgent
import logging


class DirectorCachingManager:
    """
    [V64 P2-1] Director에서 분리된 캐싱 관리 모듈

    담당:
    - create_manuscript_cache(): 전체 원고 합본 Gemini 캐시 생성
    - build_manuscript_history_for_check(): DB에서 이전 원고 역사 구성
    - get_protagonist_config(): protagonist_config 캐싱 조회
    """

    def __init__(self, client, primary_model, context=None) -> None:
        """
        Args:
            client: Google GenAI 클라이언트 (BaseAgent.client)
            primary_model: 기본 모델 이름 (BaseAgent.primary_model)
            context: ProjectContext (BaseAgent.context)
        """
        self.client = client
        self.primary_model = primary_model
        self.context = context

        # [V60.88] 원고 컨텍스트 캐싱 상태
        self.manuscript_cache_name = None
        self.manuscript_cache_enabled = True
        self._cached_manuscript_count = 0

        # [V60.89] protagonist_config 캐싱
        self._protagonist_config = None

    def build_manuscript_history_for_check(self, db_manager, ep_num: int) -> list:
        """
        [V60.87] DB에서 이전 원고 역사를 가져와 충돌 검사용으로 구성

        Args:
            db_manager: DBManager 인스턴스
            ep_num: 현재 회차 (이전 회차들만 가져옴)

        Returns:
            [{"ep_num": 1, "text": "...", "summary": "..."}, ...]
        """
        history = []
        try:
            for prev_ep in range(1, ep_num):
                ms_data = db_manager.get_manuscript(prev_ep)
                if ms_data and ms_data.get('content'):
                    history.append({
                        "ep_num": prev_ep,
                        "text": ms_data.get('content', ''),
                        "summary": ms_data.get('summary', '')
                    })
        except Exception as e:
            logging.warning(f"⚠️ [V60.87] 원고 역사 로드 실패: {e}")

        return history

    def create_manuscript_cache(
        self,
        db_manager,
        current_ep: int,
        ttl_seconds: int = 3600
    ) -> str:
        """
        [V60.88] 전체 원고를 합본하여 Gemini 컨텍스트 캐시 생성

        Args:
            db_manager: DBManager 인스턴스
            current_ep: 현재 작성 중인 회차 (이전 회차들만 캐싱)
            ttl_seconds: 캐시 유효 시간 (초)

        Returns:
            캐시 이름 (성공 시) 또는 None (실패 시)
        """
        if not self.manuscript_cache_enabled:
            logging.info("⏭️ [V60.88] 원고 캐싱 비활성화됨")
            return None

        try:
            from google.genai import types

            # 1. 모든 이전 원고 수집 (순서대로)
            manuscripts_compiled = []
            total_chars = 0

            for ep_num in range(1, current_ep):
                ms_data = db_manager.get_manuscript(ep_num)
                if ms_data and ms_data.get('content'):
                    ep_text = ms_data.get('content', '')
                    ep_title = ms_data.get('title', f'제{ep_num}화')
                    formatted = f"\n{'='*60}\n# 제{ep_num}화. {ep_title}\n{'='*60}\n{ep_text}\n"
                    manuscripts_compiled.append(formatted)
                    total_chars += len(formatted)

            if not manuscripts_compiled:
                logging.info("⚠️ [V60.88] 캐싱할 이전 원고가 없습니다.")
                return None

            # 2. 합본 텍스트 구성
            compiled_text = f"""[📚 V60.88 원고 합본 - 총 {len(manuscripts_compiled)}화]
이 캐시는 제1화부터 제{current_ep - 1}화까지의 전체 원고입니다.
원고 연속성 전문가로서 이 내용을 숙지하고 새 원고의 충돌을 검사하세요.

[🔍 검사 핵심]
1. 사망 충돌: 죽은 인물이 다시 등장하면 CRITICAL
2. 아이템 충돌: 잃어버린/파괴된 아이템이 다시 사용되면 CRITICAL
3. 관계 충돌: 적대 관계가 갑자기 우호적으로 변하면 검토 필요
4. 타임라인 충돌: 시간 순서가 맞지 않으면 검토 필요
5. 지리 충돌: 물리적으로 불가능한 이동이면 검토 필요

{''.join(manuscripts_compiled)}
"""

            # 3. 캐시 최소 크기 체크 (1024 토큰 ≈ 1500자)
            if total_chars < 1500:
                logging.info(f"⚠️ [V60.88] 원고 분량 부족 ({total_chars}자) - 캐싱 스킵")
                return None

            # 4. 기존 캐시가 유효하고 원고 수가 동일하면 재사용
            if self.manuscript_cache_name and self._cached_manuscript_count == len(manuscripts_compiled):
                logging.info(f"⚡ [V60.88] 기존 캐시 재사용 ({self._cached_manuscript_count}화)")
                return self.manuscript_cache_name

            # 5. 새 캐시 생성
            logging.info(f"⚡ [V60.88] 원고 캐시 생성 중... ({len(manuscripts_compiled)}화, {total_chars:,}자)")

            cache = self.client.caches.create(
                model=self.primary_model,
                config=types.CreateCachedContentConfig(
                    display_name=f"MANUSCRIPT_HISTORY_EP{current_ep}",
                    system_instruction="원고 연속성 전문가 (Manuscript Continuity Expert)",
                    contents=[compiled_text],
                    ttl=f"{ttl_seconds}s"
                )
            )

            self.manuscript_cache_name = cache.name
            self._cached_manuscript_count = len(manuscripts_compiled)

            logging.info(f"✅ [V60.88] 원고 캐시 생성 완료: {cache.name}")
            logging.info(f"- 총 {len(manuscripts_compiled)}화 / {total_chars:,}자 캐싱됨")

            return cache.name

        except Exception as e:
            # [V61.9] 캐싱 중 429/quota → 키 전환 예약
            error_str = str(e).lower()
            if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                logging.info(f"⚠️ [V61.9] 원고 캐시 생성 중 API 제한 → 키 전환 예약")
                with BaseAgent._rotation_lock:
                    BaseAgent._key_rotation_pending = True
            else:
                logging.warning(f"❌ [V60.88] 원고 캐시 생성 실패: {e}")
            self.manuscript_cache_name = None
            return None

    def get_protagonist_config(self) -> dict:
        """[V60.89] context에서 protagonist_config 추출 (캐싱)"""
        if self._protagonist_config is not None:
            return self._protagonist_config

        try:
            master_bible = getattr(self.context, 'master_bible', {})
            if master_bible:
                bible_root = master_bible.get('MasterBible', master_bible)
                self._protagonist_config = bible_root.get('protagonist_config', {})
            else:
                self._protagonist_config = {}
        except Exception:
            self._protagonist_config = {}

        return self._protagonist_config
