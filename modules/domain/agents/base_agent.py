import ast  # 👈 [필수] literal_eval 가동을 위해 반드시 필요
import json
import logging
import os
import re
import threading
import time
from pathlib import Path

import yaml
from google import genai
from google.genai import types

from modules.core.constants import ContextLimits  # [TF-25-04] validation.yaml SSOT
from modules.validation.threshold_helper import _threshold

# [V44] 에스케이프 유틸리티 임포트
try:
    from modules.core.escape_utils import escape_braces as util_escape_braces
except ImportError:
    # 폴백: 유틸리티 없을 시 기본 구현 사용
    util_escape_braces = None

# [V49.3] 비용 추적 시스템 임포트
try:
    from modules.core.metrics_collector import get_metrics_collector

    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

    def get_metrics_collector() -> None:
        return None


# [V44] 에러 타입 분류
class AgentErrorType:
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    MALFORMED_RESPONSE = "malformed_response"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


DEFAULT_MODEL_TIER = "gemini-2.5-flash"
DEFAULT_MODEL_FALLBACK_CHAIN = {
    "gemini-3.1-pro-preview": "gemini-3-pro-preview",
    "gemini-3-pro-preview": "gemini-2.5-pro",
    "gemini-3-flash-preview": "gemini-2.5-flash",
    "gemini-2.5-flash": "gemini-2.5-flash",
}


def _resolve_models_config_path() -> Path:
    """Return config/models.yaml path from project root."""
    return Path(__file__).resolve().parents[3] / "config" / "models.yaml"


def _load_model_config() -> dict:
    """Load config/models.yaml. Return empty dict on failure."""
    config_path = _resolve_models_config_path()
    try:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    return data
    except (OSError, yaml.YAMLError):
        logging.warning("models.yaml 로드 실패 — 하드코딩 모델 목록 사용")
    return {}


def _to_snake_case(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _get_agent_default_model(agent_key: str) -> str | None:
    config = _load_model_config()
    agents = config.get("agents", {})
    if not isinstance(agents, dict):
        return None
    model = agents.get(agent_key)
    if isinstance(model, str) and model.strip():
        return model.strip()
    return None


def _get_sub_component_models(agent_key: str) -> dict:
    config = _load_model_config()
    sub_components = config.get("sub_components", {})
    if not isinstance(sub_components, dict):
        return {}
    entry = sub_components.get(agent_key, {})
    if not isinstance(entry, dict):
        return {}
    return {k: v for k, v in entry.items() if isinstance(k, str) and isinstance(v, str)}


def _get_model_fallback_chain() -> dict:
    config = _load_model_config()
    chain = config.get("fallback_chain", {})
    if isinstance(chain, dict):
        normalized = {k: v for k, v in chain.items() if isinstance(k, str) and isinstance(v, str)}
        if normalized:
            return normalized
    return DEFAULT_MODEL_FALLBACK_CHAIN.copy()


def _load_system_config() -> dict:
    """Load config/system.yaml. Return empty dict on failure."""
    config_path = _resolve_models_config_path().parent / "system.yaml"
    try:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    return data
    except (OSError, yaml.YAMLError):
        logging.warning("system.yaml load failed. Using hard-coded defaults.")
    return {}


_SYSTEM_CFG = _load_system_config()


class BaseAgent:
    # [V60.27] Thinking Level → Budget 변환 맵 (Gemini 3 API)
    THINKING_BUDGET_MAP = _SYSTEM_CFG.get(
        "thinking_budget_map", {"minimal": 1024, "low": 4096, "medium": 8192, "high": 16384, "maximum": 24576}
    )

    # [V60.37] 모델별 폴백 체인 정의 (할당량 초과 시)
    # [V62.1] 2.5-pro가 최종 폴백 (2.5-flash 폴백 제거 - 품질 하한선 보장)
    MODEL_FALLBACK_CHAIN = _get_model_fallback_chain()

    # [LOG-1] SessionLogger 싱글톤 (MetricsCollector와 동일 패턴)
    _session_logger_global = None

    @classmethod
    def set_session_logger(cls, logger):
        """[LOG-1] SessionLogger 주입 (main_a.py에서 1회 호출)."""
        cls._session_logger_global = logger

    # [V60.68] 쿼터 소진 모델 캐싱 (클래스 변수 - 세션 전체 공유)
    _quota_exhausted_models = {}  # {model_name: exhausted_until_timestamp}
    _quota_lock = threading.Lock()  # [I-18] 쿼터 캐시 읽기/쓰기 경쟁 방지
    _QUOTA_CACHE_DURATION = _SYSTEM_CFG.get("api", {}).get("quota_cache_duration", 3600)

    # [S-02] max_output_tokens 클래스 상수
    MAX_OUTPUT_TOKENS = _SYSTEM_CFG.get("api", {}).get("max_output_tokens", 8192)

    # [V60.99] API Rate Limit 예방 딜레이 (초)
    API_DELAY = _SYSTEM_CFG.get("api", {}).get("delay", 0.1)

    # [TF3-H7] 프롬프트 총량 사전 게이트 (API 호출 전)
    MAX_CONTEXT_CHARS = ContextLimits.MAX_CONTEXT_CHARS  # [TF-25-04] validation.yaml SSOT

    # [V61.5] API 키 순환 (429 방어)
    _api_keys = []
    _current_key_idx = 0
    _keys_initialized = False
    _key_rotation_pending = False
    _last_rotation_time = 0
    _MIN_ROTATION_INTERVAL = _SYSTEM_CFG.get("key_rotation", {}).get("min_interval", 10)
    _rotation_lock = threading.RLock()  # [V61.7+TF-XC-05] 재진입 허용 (init→rotate 체인)
    _rotation_count = 0  # [V62.3] 연속 키 순환 횟수 (전체 키 수 도달 시 순환 중단)

    @classmethod
    def _init_api_keys(cls) -> None:
        """환경변수에서 모든 API 키 로드 (GOOGLE_API_KEY, _2, _3, ...)"""
        # [TF-XC-05] check-then-act를 _rotation_lock 안으로 이동 (TOCTOU 방지)
        with cls._rotation_lock:
            if cls._keys_initialized:
                return
            cls._keys_initialized = True
            keys = []
            primary = os.getenv("GOOGLE_API_KEY")
            if primary:
                keys.append(primary)
            for i in range(2, 10):
                k = os.getenv(f"GOOGLE_API_KEY_{i}")
                if k:
                    keys.append(k)
            cls._api_keys = keys
            if len(keys) > 1:
                logging.info(f"🔑 [V61.5] API 키 {len(keys)}개 로드 완료 (자동 순환 활성화)")

    @classmethod
    def _try_rotate_key(cls):
        """다음 API 키로 순환. 새 Client 반환 또는 None. [V61.7] Lock 보호."""
        with cls._rotation_lock:
            cls._init_api_keys()
            if len(cls._api_keys) <= 1:
                cls._key_rotation_pending = False
                return None

            # [V62.3] 전체 키 순환 완료 시 더 이상 순환하지 않음
            if cls._rotation_count >= len(cls._api_keys) - 1:
                cls._key_rotation_pending = False
                return None

            # 너무 빠른 순환 방지
            if time.time() - cls._last_rotation_time < cls._MIN_ROTATION_INTERVAL:
                cls._key_rotation_pending = False
                return None

            old_idx = cls._current_key_idx
            prev_rotation_time = cls._last_rotation_time
            cls._current_key_idx = (cls._current_key_idx + 1) % len(cls._api_keys)
            cls._last_rotation_time = time.time()
            cls._rotation_count += 1  # [V62.3]
            with cls._quota_lock:
                cls._quota_exhausted_models.clear()  # 새 키에서 3-pro 한 번은 시도
            with cls._cache_lock:  # [INF-P1-8]
                cls._context_caches.clear()  # [V61.9] 키 변경 시 캐시 무효화 (API 키별 캐시 격리)
            cls._key_rotation_pending = False

            # [A4-P1-3] Client 생성도 lock 내에서 수행 — TOCTOU 방지
            # (_current_key_idx가 lock 밖에서 읽히면 다른 스레드가 재순환할 수 있음)
            new_key_idx = cls._current_key_idx
            new_key = cls._api_keys[new_key_idx]

        # Client 생성은 lock 밖에서 (네트워크 IO 포함하므로)
        # 단, key index/key 값은 lock 내에서 캡처해두었으므로 TOCTOU 안전
        try:
            new_client = genai.Client(api_key=new_key)
        except Exception as create_err:
            with cls._rotation_lock:
                cls._current_key_idx = old_idx
                cls._last_rotation_time = prev_rotation_time
                cls._rotation_count = max(0, cls._rotation_count - 1)
                cls._key_rotation_pending = False
            logging.warning("[TF-15/P0] API key rotation client creation failed: %s", create_err)
            return None
        logging.info(
            f"🔑 [V61.5] API 키 순환: Key {old_idx + 1} → Key {cls._current_key_idx + 1} (총 {len(cls._api_keys)}개)"
        )
        # [INF-I5] 키 순환 구조화 로그
        logging.debug(
            "[SilentPass:Agent] key_rotate old_idx=%d new_idx=%d total_keys=%d",
            old_idx,
            cls._current_key_idx,
            len(cls._api_keys),
        )
        return new_client

    # [V61.2] 네트워크 복원력 설정 (야간 무인 운영 대응)
    API_TIMEOUT = _SYSTEM_CFG.get("api", {}).get("timeout", _threshold("retry.api_timeout_seconds", 300))
    NETWORK_RETRY_DELAY_BASE = _SYSTEM_CFG.get("network_retry", {}).get("delay_base", 10)
    NETWORK_RETRY_DELAY_MAX = _SYSTEM_CFG.get("network_retry", {}).get("delay_max", 30)
    MAX_NETWORK_RETRIES = _SYSTEM_CFG.get("network_retry", {}).get("max_retries", 22)

    def __init__(self, context, client, model_tier=None) -> None:
        self.context = context
        self.client = client
        resolved_model = model_tier
        if resolved_model is None:
            agent_key = _to_snake_case(self.__class__.__name__)
            resolved_model = _get_agent_default_model(agent_key)
        self.primary_model = resolved_model or DEFAULT_MODEL_TIER
        # [V60.37] 스마트 폴백: 모델 티어에 따라 자동 백업 모델 설정
        # [V60.78] 기본 폴백을 2.5-flash로 변경 (2.0 이하 미사용 정책)
        self.backup_model = self.MODEL_FALLBACK_CHAIN.get(self.primary_model, DEFAULT_MODEL_TIER)
        self.cache_name = None
        # [V44] 실패 복구 상태 추적
        self.last_partial_response = ""
        self.requires_human_intervention = False
        self.last_error_type = None
        # [V49.3] 에이전트 이름 (비용 추적용)
        self._agent_name = self.__class__.__name__
        self._last_thinking = ""  # [TF-28c] 최근 ask() thinking content

    def _apply_prompt_size_gate(self, prompt: str) -> str:
        """[TF3-H7] 과대 프롬프트를 API 호출 전에 절삭."""
        max_chars = int(self.MAX_CONTEXT_CHARS or 0)
        if max_chars <= 0:
            return prompt
        if len(prompt) <= max_chars:
            return prompt

        notice = (
            "\n\n[System Note] Prompt truncated by safety gate to prevent context overflow."
            " Focus on the most recent instructions."
        )
        keep = max(0, max_chars - len(notice))
        clipped = prompt[:keep] + notice
        logging.warning(
            "[TF3-H7] Prompt length gate applied: %d -> %d chars (agent=%s)",
            len(prompt),
            len(clipped),
            self._agent_name,
        )
        self.requires_human_intervention = True
        return clipped

    @property
    def agent_name(self) -> str:
        """[V49.3] 에이전트 이름 반환 (비용 추적용)"""
        return self._agent_name

    # 📂 modules/domain/agents/base_agent.py

    def ask(self, prompt, temperature=0.5, response_schema=None, thinking_level=None):
        """
        LLM에 질의

        Args:
            prompt: 질의 프롬프트
            temperature: 생성 온도 (0.0-1.0)
            response_schema: JSON 스키마 (선택). 현재 analyst.py에서만 사용 중.
                             TODO: 다른 에이전트에도 구조화 응답이 필요하면 활용 확대 검토.
            thinking_level: [V60.25] Gemini 3 thinking level ("minimal", "low", "medium", "high")
        """
        # [B4-P2-4] 이전 ask() 호출의 부분 응답이 남아있으면 새 호출에서 오염됨 — 초기화
        self.last_partial_response = ""
        directives = self._escape_braces(getattr(self.context, "author_directives", ""))
        base_prompt = (
            f"### [AUTHOR'S ABSOLUTE DIRECTIVES]\n{directives}\n\n"
            f"### [TASK]\n{prompt}\n\n"
            f"### [FORMAT]\nRespond ONLY in valid JSON format."
        )
        base_prompt = self._apply_prompt_size_gate(base_prompt)

        full_response = ""
        current_prompt = base_prompt

        # [V61.5] API 키 순환 체크 (이전 작업에서 429 발생 시) [V61.7] Lock 보호
        with BaseAgent._rotation_lock:
            pending = BaseAgent._key_rotation_pending
        if pending:
            new_client = self._try_rotate_key()
            if new_client:
                self.client = new_client

        # [V60.66] 429 폴백용 모델 스택 (primary → fallbacks)
        model_stack = [self.primary_model]
        if self.backup_model and self.backup_model != self.primary_model:
            model_stack.append(self.backup_model)
        # 추가 폴백 체인 확장
        next_fallback = self.MODEL_FALLBACK_CHAIN.get(self.backup_model)
        if next_fallback and next_fallback not in model_stack:
            model_stack.append(next_fallback)

        # [V60.68] 쿼터 소진 모델 필터링 (세션 캐싱) [I-18] Lock 보호
        current_time = time.time()
        available_models = []
        with BaseAgent._quota_lock:
            quota_snapshot = dict(BaseAgent._quota_exhausted_models)
        for model in model_stack:
            exhausted_until = quota_snapshot.get(model, 0)
            if current_time >= exhausted_until:
                available_models.append(model)
            else:
                remaining = int(exhausted_until - current_time)
                # 첫 번째 모델(primary)이 스킵되는 경우에만 로그 출력
                if model == self.primary_model:
                    logging.info(f"⏭️ [V60.68] {model} 쿼터 캐시 히트 - {remaining}초 남음, 스킵")

        # [V60.68] 사용 가능한 모델이 있으면 그것으로 시작, 없으면 원래 스택 사용
        if available_models:
            model_stack = available_models
            current_model = available_models[0]
        else:
            current_model = self.primary_model  # fallback: 원래대로

        # [V60.66] 현재 사용 중인 모델 추적 (V60.68에서 업데이트됨)

        config_params = {
            "temperature": temperature,
            "max_output_tokens": self.MAX_OUTPUT_TOKENS,
            "top_p": 0.95,
            "response_mime_type": "application/json",
            "http_options": types.HttpOptions(timeout=max(10, int(self.API_TIMEOUT))),
        }
        # [V0128] JSON Schema enforcement if provided
        if response_schema:
            config_params["response_schema"] = response_schema

        # [V61.6] Thinking Budget 지원 (모든 모델 공통 - gemini-3, 2.5-pro, 2.5-flash)
        if thinking_level:
            # 문자열이면 정수로 변환, 이미 정수면 그대로 사용
            if isinstance(thinking_level, str):
                budget = self.THINKING_BUDGET_MAP.get(thinking_level.lower(), 8192)
            else:
                budget = int(thinking_level)
            config_params["thinking_config"] = types.ThinkingConfig(thinking_budget=budget, include_thoughts=True)

        config = types.GenerateContentConfig(**config_params)

        # [INF-I5] API 호출 시작 구조화 로그
        logging.debug(
            "[SilentPass:Agent] call_start agent=%s model=%s prompt_len=%d",
            self._agent_name,
            current_model,
            len(base_prompt),
        )

        # [V49.3] 비용 추적 시작
        metric_id = None
        if METRICS_ENABLED:
            try:
                collector = get_metrics_collector()
                metric_id = collector.start_call(self.agent_name, current_model)
            except Exception as e:  # [V64.P4] OPTIONAL: metrics startup
                logging.debug(f"[SILENT] metrics startup: {e}")
                pass  # 메트릭 실패가 본 작업에 영향 주지 않음

        try:
            # 🔒 Circuit Breaker: 최대 5회 시도 (API 비용 폭증 방지)
            MAX_CONTINUATIONS = 5
            WARN_THRESHOLD = 3

            # [V60.97] Rate Limit vs Quota 구분 대응
            MAX_QUOTA_RETRIES = len(model_stack)
            quota_retry_count = 0
            rate_limit_retry_count = 0  # [V60.97] Rate Limit 전용 재시도 카운터
            MAX_RATE_LIMIT_RETRIES = 3  # [V60.97] Rate Limit 최대 재시도 (같은 모델)
            network_retry_count = 0  # [V61.2] 네트워크 오류 재시도 카운터

            _thinking_text = ""  # [TF-28] LLM thinking content

            attempt = 0
            while attempt < MAX_CONTINUATIONS:
                try:
                    # [V60.99] API Rate Limit 예방 딜레이
                    time.sleep(self.API_DELAY)
                    response = self.client.models.generate_content(
                        model=current_model, contents=current_prompt, config=config
                    )
                    # [V60.97] 성공 시 카운터 리셋
                    rate_limit_retry_count = 0
                    network_retry_count = 0  # [V61.2] 네트워크 카운터도 리셋
                    # [V62.3] primary 모델 성공 시 키 순환 카운터 리셋
                    if current_model == self.primary_model:
                        with BaseAgent._rotation_lock:
                            BaseAgent._rotation_count = 0
                except Exception as api_error:
                    # ═══════════════════════════════════════════════════════════════
                    # [V61.2] Case 0: 네트워크/타임아웃 오류 → 백오프 + 연결 체크 후 재시도
                    # 야간 무인 운영 시 3-5분 인터넷 끊김에도 작업 유지
                    # ═══════════════════════════════════════════════════════════════
                    if self._is_network_error(api_error) and network_retry_count < self.MAX_NETWORK_RETRIES:
                        network_retry_count += 1
                        # 백오프: 10초 → 15초 → 20초 → ... → 최대 30초
                        wait_time = min(
                            self.NETWORK_RETRY_DELAY_BASE + (network_retry_count - 1) * 5, self.NETWORK_RETRY_DELAY_MAX
                        )
                        total_waited = sum(
                            min(self.NETWORK_RETRY_DELAY_BASE + i * 5, self.NETWORK_RETRY_DELAY_MAX)
                            for i in range(network_retry_count)
                        )

                        # [V61.2] 타임스탬프 포함 출력 (하트비트 역할)
                        from datetime import datetime

                        timestamp = datetime.now().strftime("%H:%M:%S")
                        logging.warning(
                            f"\n      🌐 [{timestamp}] 연결 오류 → {wait_time}초 대기 ({network_retry_count}/{self.MAX_NETWORK_RETRIES}, 누적 {total_waited}초)"
                        )

                        # 대기 중 — 메인 스레드에서만 print (워커 스레드는 logging만)
                        if threading.current_thread() is threading.main_thread():
                            print(
                                f"         🌐 네트워크 재시도 {network_retry_count}/{self.MAX_NETWORK_RETRIES} ({wait_time}초 대기)"
                            )
                        time.sleep(wait_time)

                        # 연결 체크
                        if self._check_connectivity():
                            logging.info(f"✅ [{datetime.now().strftime('%H:%M:%S')}] 연결 복구! 재시도...")
                            continue  # 루프 처음으로
                        else:
                            # 연결 안 됨 - 다음 재시도로 (루프 계속)
                            logging.info(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] 연결 대기 중...")
                            continue

                    # [V60.97] Rate Limit vs Quota Exhausted 구분
                    error_str = str(api_error).lower()

                    # Rate Limit: 429 + (rate 또는 limit) - 분당 요청 제한
                    is_rate_limit = "429" in error_str and ("rate" in error_str or "limit" in error_str)
                    # Quota Exhausted: resource_exhausted 또는 quota - 일일/월간 할당량 초과
                    is_quota_exhausted = "resource_exhausted" in error_str or (
                        "quota" in error_str and "429" not in error_str
                    )
                    # 애매한 경우 (429만 있음) - Rate Limit으로 간주
                    is_ambiguous_429 = "429" in error_str and not is_rate_limit and not is_quota_exhausted

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.98] gemini-3-pro는 할당량이 적으므로 Rate Limit 시 즉시 폴백
                    # ═══════════════════════════════════════════════════════════════
                    is_gemini3_rate_limit = (is_rate_limit or is_ambiguous_429) and "gemini-3-pro" in current_model

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.97] Case A: Rate Limit (gemini-3-pro 제외) → Backoff 후 재시도
                    # ═══════════════════════════════════════════════════════════════
                    if (
                        (is_rate_limit or is_ambiguous_429)
                        and not is_gemini3_rate_limit
                        and rate_limit_retry_count < MAX_RATE_LIMIT_RETRIES
                    ):
                        rate_limit_retry_count += 1
                        # Linear Backoff: 30초 → 60초 → 90초 (분당 제한 대응)
                        wait_time = 30 * rate_limit_retry_count
                        logging.info(
                            f"⏳ [V60.97 Rate Limit] {current_model} 분당 제한 감지 → {wait_time}초 대기 후 재시도 ({rate_limit_retry_count}/{MAX_RATE_LIMIT_RETRIES})"
                        )
                        time.sleep(wait_time)
                        # 루프 처음으로 돌아가서 try/except 안에서 재시도
                        continue

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.97] Case B: Quota/Rate Limit 초과 또는 gemini-3-pro Rate Limit → 즉시 폴백
                    # ═══════════════════════════════════════════════════════════════
                    elif (
                        is_quota_exhausted
                        or is_gemini3_rate_limit
                        or (is_rate_limit and rate_limit_retry_count >= MAX_RATE_LIMIT_RETRIES)
                    ):
                        if is_gemini3_rate_limit:
                            logging.info(f"⚡ [V60.98] {current_model} Rate Limit → 즉시 폴백 (할당량 부족 모델)")
                        if quota_retry_count < MAX_QUOTA_RETRIES - 1:
                            quota_retry_count += 1
                            rate_limit_retry_count = 0  # 폴백 시 Rate Limit 카운터 리셋

                            old_model = current_model
                            current_model = (
                                model_stack[quota_retry_count]
                                if quota_retry_count < len(model_stack)
                                else model_stack[-1]
                            )

                            # [V60.68] 쿼터 소진 모델 캐시 등록 [I-18] Lock 보호
                            # [V62.3] 3-pro는 시간 단위 차단 — Rate Limit도 길게 캐싱
                            cache_duration = BaseAgent._QUOTA_CACHE_DURATION
                            with BaseAgent._quota_lock:
                                BaseAgent._quota_exhausted_models[old_model] = time.time() + cache_duration

                            # [V62.3] 전체 키 시도 전까지만 순환 예약
                            with BaseAgent._rotation_lock:
                                if BaseAgent._rotation_count < len(BaseAgent._api_keys) - 1:
                                    BaseAgent._key_rotation_pending = True

                            error_type = "Quota 소진" if is_quota_exhausted else "Rate Limit 초과"
                            logging.info(f"🔄 [V60.97 Fallback] {old_model} {error_type} → {current_model}로 전환")
                            # [INF-I5] 폴백 전환 구조화 로그
                            logging.debug(
                                "[SilentPass:Agent] fallback agent=%s from=%s to=%s reason=%s",
                                self._agent_name,
                                old_model,
                                current_model,
                                error_type,
                            )

                            # 폴백 모델용 config 재생성
                            fallback_config_params = {
                                "temperature": temperature,
                                "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                                "top_p": 0.95,
                                "response_mime_type": "application/json",
                            }
                            if response_schema:
                                fallback_config_params["response_schema"] = response_schema
                            if thinking_level:
                                if isinstance(thinking_level, str):
                                    budget = self.THINKING_BUDGET_MAP.get(thinking_level.lower(), 8192)
                                else:
                                    budget = int(thinking_level)
                                fallback_config_params["thinking_config"] = types.ThinkingConfig(
                                    thinking_budget=budget, include_thoughts=True
                                )
                            config = types.GenerateContentConfig(**fallback_config_params)

                            # [V60.99] API Rate Limit 예방 딜레이
                            time.sleep(self.API_DELAY)
                            response = self.client.models.generate_content(
                                model=current_model, contents=current_prompt, config=config
                            )
                        else:
                            # 모든 폴백 소진
                            raise api_error
                    else:
                        # 기타 에러 - 예외 재발생
                        raise api_error

                try:
                    chunk = response.text if response.text else ""
                except (ValueError, AttributeError):
                    chunk = ""
                    logging.warning("[base_agent] response.text 접근 실패 (safety filter?) — 빈 응답 처리")

                # [TF-28] thinking content 추출 (첫 응답에서만)
                if thinking_level and attempt == 0 and not _thinking_text:
                    try:
                        if response.candidates and response.candidates[0].content:
                            _tparts = []
                            for _p in response.candidates[0].content.parts:
                                if getattr(_p, "thought", False) and isinstance(_p.text, str):
                                    _tparts.append(_p.text)
                            if _tparts:
                                _thinking_text = "\n".join(_tparts)
                    except Exception:
                        pass

                # 💡 [Sovereign Logic] 지능형 중첩 제거 병합 (Overlap-Aware Merge)
                if full_response:
                    # 앞 응답의 끝부분과 뒤 응답의 시작부분이 겹치는지 최대 100자 대조
                    max_overlap = min(len(full_response), len(chunk), 100)
                    overlap_found = 0
                    for i in range(max_overlap, 0, -1):
                        if full_response.endswith(chunk[:i]):
                            overlap_found = i
                            break

                    # 중복된 부분은 제외하고 순수 데이터만 정밀하게 접합
                    full_response += chunk[overlap_found:]
                else:
                    full_response = chunk

                # 이어쓰기 중 이스케이프 단절 방지
                # [V44] 최소 길이 체크 (빈 문자열/단일 백슬래시 방지)
                if len(full_response) > 1 and full_response.endswith("\\"):
                    logging.info("[JSON Repair] 후행 이스케이프 감지 — 강제 제거")
                    full_response = full_response[:-1]

                if not response.candidates:
                    break
                candidate = response.candidates[0]

                # 토큰 제한(MAX_TOKENS) 발생 시 '비트 3' 유실 방지를 위한 이어쓰기 시퀀스
                if hasattr(candidate, "finish_reason") and candidate.finish_reason in ["MAX_TOKENS", "LENGTH"]:
                    # 🔒 Circuit Breaker 경고
                    if attempt >= WARN_THRESHOLD:
                        logging.warning(
                            f"⚠️ [Circuit Breaker] 과도한 continuation 감지 ({attempt + 1}/{MAX_CONTINUATIONS}회)"
                        )
                        logging.warning(
                            f"⚠️ [Cost Warning] API 비용 증가 중 - 누적 응답 길이: {len(full_response)} chars"
                        )

                    # 🔒 Circuit Breaker 트립 (최대 시도 횟수 도달)
                    if attempt >= MAX_CONTINUATIONS - 1:
                        logging.warning(
                            f"🚨 [Circuit Breaker TRIP] 최대 continuation 횟수 도달 ({MAX_CONTINUATIONS}회)"
                        )
                        logging.warning("🚨 [WARNING] 응답 불완전 가능 - 수동 검토 필요")
                        break

                    # 마지막 50자를 앵커로 사용하여 다음 응답의 시작점을 강제 고정
                    overlap_anchor = full_response[-50:].strip()
                    # [FIX] 중괄호 이스케이프 적용 (f-string 오류 방지)
                    safe_anchor = self._escape_braces(overlap_anchor)
                    logging.warning(
                        f"🔄 [System] 데이터 절단 감지. '{overlap_anchor[:20]}...' 지점부터 인과율 용접 시도 ({attempt + 1}/{MAX_CONTINUATIONS})"
                    )

                    current_prompt = (
                        f"--- [SYSTEM: CONTINUATION MISSION] ---\n"
                        f"Your previous response was cut off exactly at: '...{safe_anchor}'\n"
                        f"CONTINUE the JSON structure IMMEDIATELY from the next character.\n"
                        f"Do not summarize. Do not skip any bits (especially 'Beat 3')."
                    )
                    time.sleep(1)
                    attempt += 1
                    continue
                else:
                    break

            # [V49.3] 비용 추적 종료 (성공)
            if METRICS_ENABLED and metric_id:
                try:
                    collector = get_metrics_collector()
                    input_tokens = collector.estimate_tokens(base_prompt, is_input=True)
                    output_tokens = collector.estimate_tokens(full_response, is_input=False)
                    collector.end_call(metric_id, success=True, input_tokens=input_tokens, output_tokens=output_tokens)
                except Exception as e:  # [V64.P4] OPTIONAL: metrics end (success)
                    logging.debug(f"[SILENT] metrics end (success): {e}")
                    pass

            # [INF-I5] API 호출 성공 구조화 로그
            logging.debug(
                "[SilentPass:Agent] call_success agent=%s model=%s response_len=%d",
                self._agent_name,
                current_model,
                len(full_response),
            )

            # [LOG-1] LLM I/O 세션 로깅 (성공)
            if BaseAgent._session_logger_global:
                try:
                    _elapsed = (time.time() - current_time) * 1000 if current_time else 0
                    BaseAgent._session_logger_global.log_llm_call(
                        agent_name=self._agent_name,
                        model=current_model,
                        prompt=base_prompt,
                        response=full_response,
                        temperature=temperature,
                        duration_ms=_elapsed,
                        success=True,
                        thinking=_thinking_text,  # [TF-28]
                    )
                except Exception:
                    pass

            # [TF-28] thinking 캡처 debug 로그
            if _thinking_text:
                logging.debug(
                    "[TF-28:Thinking] agent=%s thinking_len=%d",
                    self._agent_name,
                    len(_thinking_text),
                )

            self._last_thinking = _thinking_text  # [TF-28c]
            return full_response

        except Exception as e:
            _ask_error = e  # [LOG-1] 내부 except에서 e 삭제 방지용 보존
            # [V44] 에러 타입 분류 및 적절한 복구 전략 선택
            error_type = self._classify_error(e)
            self.last_error_type = error_type
            # [INF-I5] API 호출 실패 구조화 로그
            logging.debug(
                "[SilentPass:Agent] call_failure agent=%s model=%s error_type=%s backup=%s",
                self._agent_name,
                current_model,
                error_type,
                self.backup_model,
            )
            # [V60.66] 429 폴백이 인라인에서 이미 시도되었음을 표시
            if error_type == AgentErrorType.QUOTA_EXCEEDED:
                logging.warning(f"🚨 [V60.66] 모든 폴백 모델 할당량 초과 ({model_stack}): {str(e)[:50]}")
            else:
                logging.warning(f"⚠️ [Warning] 모델 실패 ({error_type}), 백업 가동: {str(e)[:50]}")

            # [V49.3] 비용 추적 종료 (실패, 백업 시도 전)
            if METRICS_ENABLED and metric_id:
                try:
                    collector = get_metrics_collector()
                    input_tokens = collector.estimate_tokens(base_prompt, is_input=True)
                    output_tokens = collector.estimate_tokens(full_response, is_input=False) if full_response else 0
                    collector.end_call(
                        metric_id,
                        success=False,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        error_type=error_type,
                    )
                except Exception as e:  # [V64.P4] OPTIONAL: metrics end (failure)
                    logging.debug(f"[SILENT] metrics end (failure): {e}")
                    pass

            # [LOG-1] LLM I/O 세션 로깅 (실패)
            if BaseAgent._session_logger_global:
                try:
                    _elapsed = (time.time() - current_time) * 1000 if current_time else 0
                    BaseAgent._session_logger_global.log_llm_call(
                        agent_name=self._agent_name,
                        model=current_model,
                        prompt=base_prompt,
                        response=full_response or "",
                        temperature=temperature,
                        duration_ms=_elapsed,
                        success=False,
                        error=str(_ask_error)[:500],
                        thinking=_thinking_text,  # [TF-28]
                    )
                except Exception:
                    pass

            # 부분 응답이 있으면 저장
            if full_response:
                self.last_partial_response = full_response
                logging.info(f"📝 [Recovery] 부분 응답 {len(full_response)}자 보존")

            try:
                # [FIX] 백업 모델용 별도 config
                backup_config_params = {
                    "temperature": temperature,
                    "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                    "top_p": 0.95,
                    "response_mime_type": "application/json",
                }
                if response_schema:
                    backup_config_params["response_schema"] = response_schema
                backup_config = types.GenerateContentConfig(**backup_config_params)

                # [V49.3] 백업 모델 비용 추적 시작
                backup_metric_id = None
                if METRICS_ENABLED:
                    try:
                        collector = get_metrics_collector()
                        backup_metric_id = collector.start_call(f"{self.agent_name}_Backup", self.backup_model)
                    except Exception as e:  # [V64.P4] OPTIONAL: backup metrics startup
                        logging.debug(f"[SILENT] backup metrics startup: {e}")
                        pass

                # [V60.99] API Rate Limit 예방 딜레이
                time.sleep(self.API_DELAY)
                res = self.client.models.generate_content(
                    model=self.backup_model, contents=base_prompt, config=backup_config
                )
                try:
                    backup_text = res.text if res.text else ""
                except (ValueError, AttributeError):
                    backup_text = ""
                    logging.warning("[base_agent] backup response.text 접근 실패 (safety filter?) — 빈 응답 처리")

                # [V49.3] 백업 모델 비용 추적 종료
                if METRICS_ENABLED and backup_metric_id:
                    try:
                        collector = get_metrics_collector()
                        input_tokens = collector.estimate_tokens(base_prompt, is_input=True)
                        output_tokens = collector.estimate_tokens(backup_text, is_input=False)
                        collector.end_call(
                            backup_metric_id,
                            success=bool(backup_text),
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )
                    except Exception as e:  # [V64.P4] OPTIONAL: backup metrics end
                        logging.debug(f"[SILENT] backup metrics end: {e}")
                        pass

                # [V44] 응답 검증
                if backup_text:
                    validation = self._validate_response(backup_text)
                    if validation["valid"]:
                        self.requires_human_intervention = False
                        return backup_text
                    else:
                        logging.warning(f"⚠️ [Validation] 백업 응답 검증 실패: {validation['reason']}")
                        # 부분 응답 병합 시도
                        if self.last_partial_response:
                            merged = self._try_merge_responses(self.last_partial_response, backup_text)
                            if merged:
                                logging.info("✅ [Recovery] 부분 응답 병합 성공")
                                return merged

                # 빈 응답 처리
                if self.last_partial_response:
                    logging.info(f"📝 [Fallback] 부분 응답 반환 ({len(self.last_partial_response)}자)")
                    # [V44] 부분 응답은 검증되지 않음 - 플래그 설정
                    self.requires_human_intervention = True
                    return self.last_partial_response

                return self._create_error_response(error_type, "백업 모델 빈 응답")

            except Exception as e_inner:
                inner_error_type = self._classify_error(e_inner)
                logging.warning(f"🚨 [Critical] 백업 실패 ({inner_error_type}): {str(e_inner)[:50]}")

                # [V44] 최후의 복구 시도
                if self.last_partial_response:
                    logging.info(f"📝 [Last Resort] 부분 응답 반환 ({len(self.last_partial_response)}자)")
                    self.requires_human_intervention = True
                    return self.last_partial_response

                # 빈 JSON 대신 구조화된 에러 응답 반환
                self.requires_human_intervention = True
                return self._create_error_response(inner_error_type, str(e_inner)[:100])

    def _escape_braces(self, text, force=False) -> str:
        """
        [V44] 중괄호 에스케이프 (최적화 버전)

        Args:
            text: 에스케이프할 텍스트
            force: True면 중복 검사 없이 강제 에스케이프

        Returns:
            str: 에스케이프된 텍스트
        """
        # V44 유틸리티 사용 (중복 에스케이프 방지 내장)
        if util_escape_braces is not None:
            return util_escape_braces(text, force)

        # 폴백 구현
        if not isinstance(text, str):
            return str(text) if text is not None else ""

        if not text:
            return ""

        # [V44] 중복 에스케이프 방지: 이미 이중 중괄호가 있으면 스킵
        if not force:
            has_double = "{{" in text or "}}" in text
            has_single = "{" in text.replace("{{", "") or "}" in text.replace("}}", "")
            if has_double and not has_single:
                return text  # 이미 에스케이프됨

        return text.replace("{", "{{").replace("}", "}}")

    # [V44] 에러 분류 메서드
    def _classify_error(self, error: Exception) -> str:
        """에러 타입을 분류하여 적절한 복구 전략 결정에 활용"""
        error_str = str(error).lower()

        if "timeout" in error_str or "timed out" in error_str or "deadline" in error_str:
            return AgentErrorType.TIMEOUT
        elif "quota" in error_str or "rate" in error_str or "429" in error_str:
            return AgentErrorType.QUOTA_EXCEEDED
        elif "connection" in error_str or "network" in error_str or "ssl" in error_str:
            return AgentErrorType.NETWORK_ERROR
        elif "json" in error_str or "parse" in error_str or "decode" in error_str:
            return AgentErrorType.MALFORMED_RESPONSE
        else:
            return AgentErrorType.UNKNOWN

    # [V61.2] 네트워크 연결 체크
    def _check_connectivity(self, timeout: int = 15) -> bool:
        """
        네트워크 연결 상태 확인 (가벼운 요청으로)

        [INF-P2-5] 이전 구현은 ``models.list()``를 호출하여 API 쿼터를 소비했음.
        현재는 ``urllib``으로 Google endpoint에 HEAD 요청을 보내 네트워크 연결만 확인.
        API 쿼터 소비 없이 순수 네트워크 가용성만 점검한다.

        Args:
            timeout: 최대 대기 시간 (초). 기본 15초.

        Returns:
            True: 연결 정상
            False: 연결 불가 또는 타임아웃
        """
        import urllib.request

        try:
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta",
                method="HEAD",
            )
            urllib.request.urlopen(req, timeout=timeout)
            return True
        except Exception as e:  # [V64.P4] connectivity check — any failure means offline
            logging.debug(f"[V66.3] 온라인 체크 실패: {e}")
            return False

    # [V61.2] 네트워크 오류 여부 판단
    def _is_network_error(self, error: Exception) -> bool:
        """타임아웃/네트워크 관련 오류인지 판단"""
        error_str = str(error).lower()
        network_keywords = [
            "timeout",
            "deadline",
            "connection",
            "network",
            "ssl",
            "socket",
            "refused",
            "reset",
            "broken pipe",
            "eof",
            "closed",
            "unavailable",
        ]
        return any(kw in error_str for kw in network_keywords)

    def _validate_response(self, response: str) -> dict:
        """응답이 유효한 JSON 구조인지 검증"""
        if not response or not isinstance(response, str):
            return {"valid": False, "reason": "빈 응답 또는 문자열 아님"}

        response = response.strip()

        # 최소 길이 검사
        if len(response) < 10:
            return {"valid": False, "reason": f"응답 너무 짧음 ({len(response)}자)"}

        # JSON 구조 검사
        if not (response.startswith("{") or response.startswith("[")):
            return {"valid": False, "reason": "JSON 시작 문자 없음"}

        # 괄호 균형 검사
        open_braces = response.count("{")
        close_braces = response.count("}")
        if abs(open_braces - close_braces) > 2:
            return {"valid": False, "reason": f"괄호 불균형 ({open_braces} vs {close_braces})"}

        # 핵심 필드 존재 검사 (최소 하나) — Writer/Director/Validator 공통
        key_fields = [
            "content",
            "tactical_doc",
            "integrated_scenario",
            "title",
            "state_updates",
            "decision",
            "score",
            "reason",
            "feedback",
            "conflicts",
            "scores",
            "corrected_content",
            "beat_sequence",
            "arc_no",
        ]
        has_key_field = any(f'"{field}"' in response for field in key_fields)
        if not has_key_field:
            return {"valid": False, "reason": "핵심 필드 없음"}

        return {"valid": True, "reason": "OK"}

    def _try_merge_responses(self, partial: str, backup: str) -> str:
        """부분 응답과 백업 응답을 병합 시도"""
        if not partial or not backup:
            return None

        try:
            # 두 응답 모두 JSON 파싱 시도
            partial_data = self._extract_json_robust(partial)
            backup_data = self._extract_json_robust(backup)

            if not isinstance(partial_data, dict) or not isinstance(backup_data, dict):
                return None

            # partial에 없는 키만 backup에서 보충
            merged = partial_data.copy()
            for key, value in backup_data.items():
                if key not in merged or merged[key] in [None, "", "None"]:
                    merged[key] = value

            # 병합 결과가 유효한지 확인
            if "parsing_error" in merged and merged.get("parsing_error"):
                return None

            return json.dumps(merged, ensure_ascii=False)
        except (
            json.JSONDecodeError,
            ValueError,
            TypeError,
            KeyError,
        ) as e:  # [V64.P4] IMPORTANT: partial merge failure
            logging.warning(f"⚠️ [V64.P4] 부분 응답 병합 실패: {str(e)[:60]}")
            return None

    def _create_error_response(self, error_type: str, message: str) -> str:
        """구조화된 에러 응답 생성 (빈 JSON 대신)"""
        error_response = {
            "error": True,
            "error_type": error_type,
            "error_message": message,
            "requires_human_intervention": True,
            "recovery_hint": self._get_recovery_hint(error_type),
        }
        return json.dumps(error_response, ensure_ascii=False)

    def _get_recovery_hint(self, error_type: str) -> str:
        """에러 타입별 복구 힌트 제공"""
        hints = {
            AgentErrorType.TIMEOUT: "API 응답 시간 초과. 잠시 후 재시도하거나 프롬프트를 줄이세요.",
            AgentErrorType.QUOTA_EXCEEDED: "API 할당량 초과. 잠시 대기 후 재시도하세요.",
            AgentErrorType.NETWORK_ERROR: "네트워크 연결 오류. 인터넷 연결을 확인하세요.",
            AgentErrorType.MALFORMED_RESPONSE: "응답 형식 오류. 프롬프트를 단순화하여 재시도하세요.",
            AgentErrorType.UNKNOWN: "알 수 없는 오류. 로그를 확인하고 재시도하세요.",
        }
        return hints.get(error_type, hints[AgentErrorType.UNKNOWN])

    try:
        _MAX_JSON_PAYLOAD = int(_SYSTEM_CFG.get("retry", {}).get("max_json_payload", 500_000))
    except (ValueError, TypeError):
        _MAX_JSON_PAYLOAD = 500_000

    def _extract_json_robust(self, text):
        """
        [V40.5 Ultimate Sovereign]
        자가 치유(Self-Healing) + 재귀적 평탄화(Flattening) 통합 엔진
        """

        if not text or not isinstance(text, str):
            return {"parsing_error": True, "content": "Empty or Invalid Input"}

        # [TF-C11] 페이로드 크기 가드 — 500KB 초과 시 절삭 후 처리
        if len(text) > self._MAX_JSON_PAYLOAD:
            logging.info("[TF-C11] JSON 페이로드 %d자 → %d자로 절삭", len(text), self._MAX_JSON_PAYLOAD)
            text = text[: self._MAX_JSON_PAYLOAD]

        # 1. [Self-Healing] 괄호/따옴표 쌍 검사 및 강제 폐쇄
        open_braces = text.count("{")
        close_braces = text.count("}")
        if open_braces > close_braces:
            text += "}" * (open_braces - close_braces)
        quote_count = len(re.findall(r'(?<!\\)"', text))  # [V70] 이스케이프 따옴표 정확히 제외
        if quote_count % 2 != 0:
            text += '"'

        try:
            # 2. 전처리 및 JSON 블록 추출
            clean_text = re.sub(r"```json\s*|```\s*", "", text.strip())
            json_pattern = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)
            match = json_pattern.search(clean_text)
            raw_json = match.group(1) if match else clean_text

            # 3. 2단계 파싱 (json -> ast)  [V64.P4] specific exception types
            data = None
            try:
                data = json.loads(raw_json, strict=False)
            except (json.JSONDecodeError, ValueError):
                try:
                    data = ast.literal_eval(raw_json)
                except (ValueError, SyntaxError):
                    # [Hard Repair] 구조 강제 수리 시도
                    repaired = self._parse_and_repair_hard(raw_json)
                    if isinstance(repaired, dict):
                        return repaired
                    # [Fallback] 파싱 실패 시 정규식으로 핵심 전술 데이터 강제 추출
                    doc_match = re.search(r'"tactical_doc"\s*:\s*"(.*?)"', text, re.DOTALL)
                    if doc_match:
                        return {"tactical_doc": doc_match.group(1), "repaired": True}

                    # [V35 Fix] Writer Agent를 위한 content 필드 강제 추출
                    content_match = re.search(r'"content"\s*:\s*"(.*?)"', text, re.DOTALL)
                    if content_match:
                        return {"content": content_match.group(1), "repaired": True}

                    # [V47 Fix] Architect Agent를 위한 scene_breakdown 강제 추출
                    scene_match = re.search(r'"scene_breakdown"\s*:\s*(\{[^}]+\})', text, re.DOTALL)
                    if scene_match:
                        try:
                            scene_data = json.loads(scene_match.group(1))
                            return {"scene_breakdown": scene_data, "repaired": True}
                        except (json.JSONDecodeError, ValueError):  # [V64.P4]
                            return {"scene_breakdown": {"scene_1": scene_match.group(1)}, "repaired": True}

                    # [V47 Fix] integrated_scenario 강제 추출
                    scenario_match = re.search(r'"integrated_scenario"\s*:\s*"(.*?)"', text, re.DOTALL)
                    if scenario_match:
                        return {"integrated_scenario": scenario_match.group(1), "repaired": True}

                    return {"parsing_error": True, "content": text, "status": "RAW_TEXT_ONLY"}

            # 4. 재귀적 데이터 평탄화 엔진 (성경 무결성 보존)
            # [V44] 순환 참조 감지 및 깊이 제한 추가
            final_dict = {}
            seen_ids = set()  # 순환 참조 감지용
            _visit_count = [0]  # [TF-C11] mutable counter for nonlocal
            MAX_DEPTH = 20  # JSON 중첩 깊이 한계 (보안)
            _MAX_VISITS = 100  # JSON 노드 방문 상한 (무한루프 방지)

            def process_node(node, depth=0) -> None:
                nonlocal final_dict
                # [TF-C11] 전체 방문 횟수 상한 — 이론적 무한루프 차단
                _visit_count[0] += 1
                if _visit_count[0] > _MAX_VISITS:
                    return
                # [V44] 깊이 제한 체크
                if depth > MAX_DEPTH:
                    return
                # [V44] 순환 참조 체크
                node_id = id(node)
                if node_id in seen_ids:
                    return
                seen_ids.add(node_id)

                try:
                    if isinstance(node, list):
                        for item in node:
                            process_node(item, depth + 1)
                    elif isinstance(node, dict):
                        # 표준 키 우선 추출 (Target, Value 등)
                        t = node.get("target") or node.get("npc_name") or node.get("item") or node.get("name")
                        v = node.get("value") or node.get("misunderstanding") or node.get("description")
                        if t and v is not None:
                            final_dict[str(t).strip("'\" ")] = v

                        # 중첩 구조 해제 루프
                        _RECURSE_KEYS = {"actual_truth", "ProjectData", "MasterBible"}
                        for k, val in node.items():
                            if k in _RECURSE_KEYS and isinstance(val, dict | list):
                                process_node(val, depth + 1)
                            else:
                                # [Sweep64] state_updates/content는 원본 키 보존
                                # — 호출자가 result.get("state_updates") 등으로 접근
                                clean_k = str(k).strip("'\" ")
                                if clean_k not in final_dict or val is not None:
                                    final_dict[clean_k] = val
                finally:
                    # 처리 완료 후 seen에서 제거 (다른 경로에서 재방문 허용)
                    seen_ids.discard(node_id)

            process_node(data)

            # 5. 최종 키 정규화 및 반환
            return {str(k).replace('"', "").replace("'", ""): v for k, v in final_dict.items()}

        except Exception as e:
            return {"parsing_error": True, "error": str(e), "fallback_content": str(text)[:100]}

    def _parse_and_repair_hard(self, json_str) -> dict:
        """[V27.5 Hardened] 물리적 구조 강제 수리"""
        try:
            open_cnt, close_cnt = json_str.count("{"), json_str.count("}")
            if open_cnt > close_cnt:
                json_str += "}" * (open_cnt - close_cnt)

            processed = re.sub(r":\s*null\b", ": None", json_str)
            processed = re.sub(r":\s*true\b", ": True", processed)
            processed = re.sub(r":\s*false\b", ": False", processed)

            try:
                return ast.literal_eval(processed)
            except (ValueError, SyntaxError):
                # [V44] JSON 파싱 실패 시 정규식 추출 경고
                logging.warning(
                    f"⚠️ [JSON Parser] ast.literal_eval 실패, 정규식 fallback 사용 (길이: {len(json_str)}자)"
                )
                # [TF-C11] 2-pass regex: 문자열 값 + 숫자/불리언 값
                kv_pattern = r'"(\w+)"\s*:\s*"(.*?)"(?="|\s*\}|\s*,)'
                found_pairs = re.findall(kv_pattern, json_str, re.DOTALL)
                result_dict = {k: v.replace("\\n", "\n").strip() for k, v in found_pairs}
                # pass 2: 숫자, 불리언, null
                kv_num_pattern = r'"(\w+)"\s*:\s*([-+]?\d+(?:\.\d+)?|true|false|null)(?:\s*[,}\]])'
                for k, v in re.findall(kv_num_pattern, json_str, re.IGNORECASE):
                    if k not in result_dict:
                        if v.lower() == "true":
                            result_dict[k] = True
                        elif v.lower() == "false":
                            result_dict[k] = False
                        elif v.lower() == "null":
                            result_dict[k] = None
                        elif "." in v:
                            result_dict[k] = float(v)
                        else:
                            result_dict[k] = int(v)
                if result_dict:
                    logging.info(f"→ 정규식으로 {len(result_dict)}개 키-값 추출 성공")
                    return result_dict
                logging.warning("→ 정규식 추출 실패, RAW 반환")
                return {"content": json_str, "status": "REPAIRED_RAW"}
        except Exception as e:
            logging.warning(f"🚨 [JSON Parser] CRITICAL_FAILURE: {str(e)[:100]}")
            return {"content": json_str, "error": "CRITICAL_FAILURE"}

    # ═══════════════════════════════════════════════════════════════════════════
    # [V61.5] Context Caching 유틸리티 (Blueprint/Manuscript 연속성 검증용)
    # ═══════════════════════════════════════════════════════════════════════════

    # 클래스 변수: 캐시 저장소
    _context_caches = {}  # {cache_key: {"name": str, "created_at": float, "content_hash": str}}
    _cache_lock = threading.Lock()  # [INF-P1-8] _context_caches 동시 접근 보호
    _CONTEXT_CACHE_MAX = int(_SYSTEM_CFG.get("cache", {}).get("context_max_entries", 50))
    _MIN_CACHE_CONTENT = int(_SYSTEM_CFG.get("cache", {}).get("min_content_chars", 50000))

    def _get_or_create_context_cache(
        self, cache_type: str, content: str, ttl_seconds: int = 1800, project_name: str = ""
    ) -> dict:
        """
        [V61.5] 컨텍스트 캐시 생성 또는 기존 캐시 반환

        Gemini Context Caching API를 활용하여 대용량 컨텍스트를 캐싱한다.
        TTL 내에 동일 content_hash면 기존 캐시 재사용.

        Args:
            cache_type: 캐시 타입 ("blueprint", "manuscript")
            content: 캐싱할 컨텍스트 텍스트
            ttl_seconds: 캐시 TTL (기본 30분)
            project_name: 프로젝트 이름 (캐시 식별용)

        Returns:
            {
                "cache_name": str,  # Gemini 캐시 이름 (None이면 캐싱 실패)
                "cached": bool,     # 기존 캐시 재사용 여부
                "content_hash": str # 콘텐츠 해시
            }
        """
        import hashlib

        # 콘텐츠 해시 생성
        content_hash = hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
        cache_key = f"{cache_type}_{project_name}_{content_hash}"

        current_time = time.time()

        # [INF-P1-8] Lock으로 _context_caches 동시 접근 보호
        with self._cache_lock:
            # 기존 캐시 확인 — [TF-R4] .get()으로 TOCTOU 제거 (키 순환 시 .clear() 경합 방지)
            cached_info = self._context_caches.get(cache_key)
            if cached_info:
                if current_time - cached_info["created_at"] < ttl_seconds:
                    logging.info(f"📦 [CTX-CACHE] HIT: {cache_type} (TTL 내 재사용)")
                    return {"cache_name": cached_info.get("name"), "cached": True, "content_hash": content_hash}
                else:
                    # 만료된 캐시 삭제 [I-20] KeyError 방지
                    self._context_caches.pop(cache_key, None)

        # Gemini Context Caching API 호출 시도
        try:
            # 콘텐츠가 너무 짧으면 캐싱 스킵 (32k 토큰 이하)
            if len(content) < self._MIN_CACHE_CONTENT:
                return {
                    "cache_name": None,
                    "cached": False,
                    "content_hash": content_hash,
                    "reason": "content_too_short",
                }

            # [V69.1] Gemini API 시그니처 변경 대응: config 파라미터 사용
            cache = self.client.caches.create(
                model=self.primary_model,
                config=types.CreateCachedContentConfig(
                    contents=[{"role": "user", "parts": [{"text": content}]}],
                    ttl=f"{ttl_seconds}s",
                    display_name=f"{cache_type}_cache_{project_name}",
                ),
            )

            # [INF-P1-8] Lock으로 캐시 쓰기 보호
            with self._cache_lock:
                # 캐시 정보 저장
                self._context_caches[cache_key] = {
                    "name": cache.name,
                    "created_at": current_time,
                    "content_hash": content_hash,
                }
                # [I-20] list() 스냅샷 1회로 TOCTOU 제거
                if len(self._context_caches) > self._CONTEXT_CACHE_MAX:
                    snapshot = list(self._context_caches.items())
                    snapshot.sort(key=lambda kv: kv[1].get("created_at", 0))
                    for old_key, _ in snapshot[: len(snapshot) - self._CONTEXT_CACHE_MAX]:
                        self._context_caches.pop(old_key, None)

            logging.info(f"📦 [V61.5] 컨텍스트 캐시 생성: {cache_type} ({len(content)}자)")

            return {"cache_name": cache.name, "cached": False, "content_hash": content_hash}

        except Exception as e:
            # 캐싱 실패해도 진행 (폴백: 캐싱 없이 직접 사용)
            error_str = str(e).lower()
            # [V61.9] 캐싱 중 429/quota → 현재 작업은 캐시 없이 진행, 다음 작업에서 키 전환
            if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                logging.warning("⚠️ [V61.9] 캐싱 중 API 제한 감지 → 키 전환 예약 (현재 작업은 캐시 없이 진행)")
                with BaseAgent._rotation_lock:
                    BaseAgent._key_rotation_pending = True
            else:
                logging.warning(f"⚠️ [V61.5] 컨텍스트 캐싱 실패 (계속 진행): {str(e)[:50]}")
            return {"cache_name": None, "cached": False, "content_hash": content_hash, "error": str(e)[:100]}

    def _ask_with_cached_context(
        self,
        cache_name: str,
        prompt: str,
        temperature: float = 0.3,
        thinking_level=None,
        full_prompt_fallback: str = "",
        response_schema=None,
    ) -> str:
        """
        [V61.5] 캐시된 컨텍스트를 사용하여 LLM 질의
        [V61.7] thinking_level 지원, max_output_tokens 보정, 프롬프트 래핑 추가

        Args:
            cache_name: 캐시 이름 (from _get_or_create_context_cache)
            prompt: 추가 프롬프트 (전략별 부분만)
            temperature: 생성 온도
            thinking_level: Gemini thinking budget ("minimal"/"low"/"medium"/"high")
            full_prompt_fallback: 캐시 실패 시 ask()에 전달할 전체 프롬프트

        Returns:
            LLM 응답 텍스트
        """
        if not cache_name:
            fallback_prompt = full_prompt_fallback if full_prompt_fallback else prompt
            return self.ask(
                fallback_prompt, temperature=temperature, thinking_level=thinking_level, response_schema=response_schema
            )

        try:
            # [V61.7] 전략 프롬프트를 ask()와 동일한 형식으로 래핑
            directives = self._escape_braces(getattr(self.context, "author_directives", ""))
            wrapped_prompt = (
                f"### [AUTHOR'S ABSOLUTE DIRECTIVES]\n{directives}\n\n"
                f"### [TASK]\n{prompt}\n\n"
                f"### [FORMAT]\nRespond ONLY in valid JSON format."
            )
            wrapped_prompt = self._apply_prompt_size_gate(wrapped_prompt)

            config_params = {
                "temperature": temperature,
                "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                "top_p": 0.95,
                "response_mime_type": "application/json",
                "cached_content": cache_name,
                "http_options": types.HttpOptions(timeout=max(10, int(self.API_TIMEOUT))),
            }
            # [TF11] response_schema 확대 적용 — API 레벨 타입 강제
            if response_schema:
                config_params["response_schema"] = response_schema
            # [V61.7] Thinking Budget 지원
            if thinking_level:
                if isinstance(thinking_level, str):
                    budget = self.THINKING_BUDGET_MAP.get(thinking_level.lower(), 8192)
                else:
                    budget = int(thinking_level)
                config_params["thinking_config"] = types.ThinkingConfig(thinking_budget=budget, include_thoughts=True)

            config = types.GenerateContentConfig(**config_params)

            time.sleep(self.API_DELAY)
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=[{"role": "user", "parts": [{"text": wrapped_prompt}]}],
                config=config,
            )

            # [TF-28] thinking content 추출 (캐시 경로)
            self._last_thinking = ""  # [TF-28c] reset
            if thinking_level:
                try:
                    if response.candidates and response.candidates[0].content:
                        _tparts = []
                        for _p in response.candidates[0].content.parts:
                            if getattr(_p, "thought", False) and isinstance(_p.text, str):
                                _tparts.append(_p.text)
                        if _tparts:
                            logging.debug(
                                "[TF-28:Thinking] agent=%s cached_path thinking_len=%d",
                                self._agent_name,
                                sum(len(t) for t in _tparts),
                            )
                            self._last_thinking = "\n".join(_tparts)  # [TF-28c]
                except Exception:
                    pass

            try:
                return response.text if response.text else ""
            except (ValueError, AttributeError):
                logging.warning("[V61.7] 캐시 응답 response.text 접근 실패 — 빈 문자열 반환")
                return ""

        except Exception as e:
            logging.warning(f"⚠️ [V61.7] 캐시 기반 질의 실패, 일반 질의로 폴백: {str(e)[:80]}")
            fallback_prompt = full_prompt_fallback if full_prompt_fallback else prompt
            return self.ask(
                fallback_prompt, temperature=temperature, thinking_level=thinking_level, response_schema=response_schema
            )

    def merge_contexts_for_caching(self, items: list, item_type: str = "blueprint") -> str:
        """
        [V61.5] Blueprint/Manuscript 리스트를 캐싱용 텍스트로 병합

        Args:
            items: Blueprint 또는 Manuscript dict 리스트
            item_type: "blueprint" 또는 "manuscript"

        Returns:
            병합된 텍스트 (캐싱용)
        """
        if not items:
            return ""

        lines = [f"=== {item_type.upper()} 연속성 컨텍스트 ===\n"]

        _merge_chars = _threshold("context.cache_merge_chars_per_ep", 4000)

        for item in items:
            if item_type == "blueprint":
                ep_num = item.get("ep_num", "?")
                data = item.get("data", item)
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] specific exception
                        data = {}

                title = data.get("title", "")
                end_loc = data.get("end_location", "")
                time_flow = data.get("time_flow", "")
                ending_hook = data.get("ending_hook", "")
                ending_state = data.get("ending_state", {})

                lines.append(f"\n--- 제{ep_num}화 Blueprint ---")
                if title:
                    lines.append(f"제목: {title}")
                if end_loc:
                    lines.append(f"종료 위치: {end_loc}")
                if time_flow:
                    lines.append(f"시간 흐름: {time_flow}")
                if ending_hook:
                    lines.append(f"엔딩 훅: {ending_hook}")
                if ending_state:
                    lines.append(f"종료 상태: {json.dumps(ending_state, ensure_ascii=False)}")

            elif item_type == "manuscript":
                ep_num = item.get("ep_num", "?")
                title = item.get("title", "")
                content = item.get("content", "")

                lines.append(f"\n--- 제{ep_num}화 원고 ---")
                if title:
                    lines.append(f"제목: {title}")
                # 원고는 앞부분만 (토큰 절약)
                if content:
                    lines.append(f"내용 요약: {content[:_merge_chars]}...")

        return "\n".join(lines)
