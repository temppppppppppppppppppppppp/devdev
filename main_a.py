import atexit

# [V61.3] Faulthandler 활성화 - segfault 등 치명적 오류 추적
import faulthandler
import os
import sys

_STDIO_BOOTSTRAPPED = False
_ASYNCIO_POLICY_BOOTSTRAPPED = False


def _bootstrap_windows_stdio_utf8() -> None:
    """Normalize Windows console stdio before bootstrap notices hit stderr."""

    global _STDIO_BOOTSTRAPPED
    if _STDIO_BOOTSTRAPPED:
        return
    if sys.platform != "win32" or "pytest" in sys.modules:
        return

    try:
        import io

        # Console-only fallback. Durable sinks still need explicit UTF-8 writers.
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        _STDIO_BOOTSTRAPPED = True
    except (AttributeError, OSError):
        return

# [CrosscutR70] 읽기전용 디렉토리/디스크풀 시 앱 크래시 방지
def _bootstrap_windows_asyncio_policy() -> None:
    """Prefer selector policy on Windows to reduce Proactor loop teardown noise."""

    global _ASYNCIO_POLICY_BOOTSTRAPPED
    if _ASYNCIO_POLICY_BOOTSTRAPPED:
        return
    if sys.platform != "win32" or "pytest" in sys.modules:
        return

    try:
        import asyncio

        selector_policy = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
        if selector_policy is None:
            return
        asyncio.set_event_loop_policy(selector_policy())
        _ASYNCIO_POLICY_BOOTSTRAPPED = True
    except Exception:
        return


_bootstrap_windows_stdio_utf8()
_bootstrap_windows_asyncio_policy()

try:
    _fault_log = open("crash_dump.log", "a", encoding="utf-8")
    faulthandler.enable(file=_fault_log, all_threads=True)
    atexit.register(_fault_log.close)
    print("[V61.3] Faulthandler 활성화 → crash_dump.log")
except OSError as _fh_err:
    print(f"[V61.3] Faulthandler 초기화 실패 (비차단): {_fh_err}", file=sys.stderr)

# Windows에서 UTF-8 인코딩 강제 설정 (이모지 및 한글 출력 지원)
# pytest 환경에서는 capture fd 충돌 방지를 위해 스킵
if not _STDIO_BOOTSTRAPPED and sys.platform == "win32" and "pytest" not in sys.modules:
    try:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        # [BUG-FIX] stdin을 새 TextIOWrapper로 교체하면 GC가 원본을 수집할 때
        # underlying buffer를 닫아 ValueError: I/O operation on closed file 발생.
        # reconfigure()로 기존 wrapper를 유지하면서 인코딩만 변경.
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv(override=True)  # Slack 알림용 환경변수 먼저 로드

# [V65] 스피너 & 전역 콘솔 → modules/core/spinners.py로 이동 (순환 참조 해소)
import re

from google import genai

import modules.core.spinners as _spinners_mod  # [V65] 플래그 동기화용
from modules.core.constants import VolumeSettings
from modules.core.feedback_system import FeedbackSystem  # [V64 P2-3]
from modules.core.llm_generate import generate_content_via_router
from modules.core.logging_keys import resolve_logging_session_id
from modules.core.metrics_collector import get_metrics_collector  # [V49.3] 비용 추적 시스템
from modules.core.models_config import load_models_yaml
from modules.core.narrative_diversity import NarrativeDiversityEngine  # [V48] 서사 다양성 엔진
from modules.core.perf_timer import PerfTimer  # [V65] 파이프라인 성능 프로파일링
from modules.core.prompt_builder import PromptBuilder  # [V64 P2-2]
from modules.core.runtime_paths import resolve_project_dir, resolve_projects_root
from modules.core.services.audit_service import AuditService  # [Phase 4B-1]
from modules.core.services.project_service import ProjectService  # [Phase 4B-3]
from modules.core.services.state_service import StateService  # [Phase 4B-3]
from modules.core.services.ui_service import UIService  # [Phase 4B-2]
from modules.core.session_logger import SessionLogger  # [LOG-1] JSONL 세션 로깅
from modules.core.stage01_helpers import Stage01Helpers  # [Phase 4C-1b]
from modules.core.stage2_contracts import TACTICAL_DOC_DUPLICATE_THRESHOLD
from modules.core.stage2_orchestrator import Stage2Orchestrator  # [V64.P3]
from modules.core.stage3_orchestrator import Stage3Orchestrator  # [Phase 4C-1a]
from modules.core.stage4_orchestrator import Stage4Orchestrator  # [V64.P3]
from modules.core.studio_visualizer import StudioVisualizer
from modules.core.system import StudioSystem
from modules.core.vec_memory import VecMemory  # [Phase 4D-2] ChromaDB → sqlite-vec
from modules.validation.threshold_helper import _threshold as _val_threshold  # [LOG-1]

# [INF-I8] Stage 전용 에이전트 및 V50 모듈은 lazy import로 전환
# _attach_agents() 진입 시에만 import하여 초기 로드 시간 절감
# 아래 변수만 미리 선언 (boot 전 참조 방어)
V50_MODULES_AVAILABLE = False  # _attach_agents()에서 실제 판정
STAGE0_AVAILABLE = False  # _lazy_load_stage0()에서 실제 판정

# StateService facade 중 일부는 레거시/manual ops용으로만 유지한다.
# 현재 Stage2/3/4 live context graph에는 바인딩하지 않는다.
RESERVED_STATE_SERVICE_FACADE_SHIMS = (
    "_extract_block_index",
    "_extract_pattern_keywords",
    "_pattern_presence_check",
    "_build_validation_context",
    "_load_genre_references",
)


@dataclass(slots=True)
class BootstrapStatus:
    core_ok: bool = False
    v50_ok: bool = False
    partial_failures: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.core_ok


def _lazy_load_stage0():
    """[INF-I8] Stage 0 모듈 lazy import"""
    global STAGE0_AVAILABLE
    try:
        from modules.core.stage0 import PresetRegistry, StyleGuide  # noqa: F811

        STAGE0_AVAILABLE = True
        return PresetRegistry, StyleGuide
    except ImportError as e:
        print(f"[!] Stage 0 모듈 로드 실패: {e}")
        STAGE0_AVAILABLE = False
        return None, None


def _lazy_load_agents():
    """[INF-I8] Stage 전용 에이전트 lazy import — _attach_agents()에서 호출"""
    from modules.domain.agents.analyst import Analyst
    from modules.domain.agents.arc_corrector import ArcCorrector
    from modules.domain.agents.arc_critic import ArcCritic
    from modules.domain.agents.arc_draft_validator import ArcDraftValidator
    from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator
    from modules.domain.agents.consensus_validator import ConsensusValidator
    from modules.domain.agents.constraint_compiler import ConstraintCompiler
    from modules.domain.agents.continuity_inspector import ContinuityInspector
    from modules.domain.agents.critic import Critic
    from modules.domain.agents.director import Director
    from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
    from modules.domain.agents.manager import Manager
    from modules.domain.agents.preflight_checker import PreflightChecker
    from modules.domain.agents.state_extractor import StateExtractor
    from modules.domain.agents.state_locked_arc_generator import StateLockedArcGenerator
    from modules.domain.agents.state_tracker import StateTracker  # noqa: F811
    from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator
    from modules.domain.agents.weaver import Weaver
    from modules.domain.agents.writer import Writer

    return {
        "Analyst": Analyst,
        "ArcCorrector": ArcCorrector,
        "ArcCritic": ArcCritic,
        "ArcDraftValidator": ArcDraftValidator,
        "ArcEnsembleGenerator": ArcEnsembleGenerator,
        "ConsensusValidator": ConsensusValidator,
        "ConstraintCompiler": ConstraintCompiler,
        "ContinuityInspector": ContinuityInspector,
        "Critic": Critic,
        "Director": Director,
        "FourPhaseArcGenerator": FourPhaseArcGenerator,
        "Manager": Manager,
        "PreflightChecker": PreflightChecker,
        "StateExtractor": StateExtractor,
        "StateLockedArcGenerator": StateLockedArcGenerator,
        "StateTracker": StateTracker,
        "ThreePhaseBlueprintGenerator": ThreePhaseBlueprintGenerator,
        "Weaver": Weaver,
        "Writer": Writer,
    }


def _lazy_load_v50_modules():
    """[INF-I8] V50 서사 품질 향상 모듈 lazy import — _attach_agents()에서 호출"""
    global V50_MODULES_AVAILABLE
    try:
        from modules.core.adaptive_retry import get_adaptive_manager
        from modules.core.adversarial_self_play import AdversarialSelfPlay
        from modules.core.agent_intelligence import AgentIntelligence
        from modules.core.chain_of_verification import ChainOfVerification
        from modules.core.character_voice import CharacterVoiceTracker
        from modules.core.character_voice_profiler import CharacterVoiceProfiler
        from modules.core.confidence_calibration import ConfidenceCalibrator
        from modules.core.constitutional_checker import ConstitutionalChecker
        from modules.core.context_advisor import ContextAdvisor
        from modules.core.cross_agent_verifier import CrossAgentVerifier
        from modules.core.dynamic_prompt_weighting import DynamicPromptWeighter
        from modules.core.emotion_tracker import EmotionArcTracker
        from modules.core.expert_mixture import ExpertMixture
        from modules.core.failure_learning import FailureLearner
        from modules.core.foreshadow_tracker import ForeshadowTracker
        from modules.core.multi_agent_deliberation import MultiAgentDeliberation
        from modules.core.pacing_analyzer import PacingAnalyzer
        from modules.core.pass_rate_monitor import PassRateMonitor
        from modules.core.power_scaling import PowerScalingTracker
        from modules.core.pre_director_checklist import PreDirectorChecklist
        from modules.core.quality_amplifier import QualityAmplifier
        from modules.core.quality_dashboard import QualityDashboard
        from modules.core.self_reflection import SelfReflector
        from modules.core.semantic_item_registry import SemanticItemRegistry
        from modules.core.stage2_optimizer import create_stage2_optimizer
        from modules.core.state_delta_tracker import StateDeltaTracker
        from modules.core.tree_of_thoughts import TreeOfThoughts
        from modules.core.writer_template import WriterTemplate

        V50_MODULES_AVAILABLE = True
        return {
            "get_adaptive_manager": get_adaptive_manager,
            "AdversarialSelfPlay": AdversarialSelfPlay,
            "AgentIntelligence": AgentIntelligence,
            "ChainOfVerification": ChainOfVerification,
            "CharacterVoiceTracker": CharacterVoiceTracker,
            "CharacterVoiceProfiler": CharacterVoiceProfiler,
            "ConfidenceCalibrator": ConfidenceCalibrator,
            "ConstitutionalChecker": ConstitutionalChecker,
            "ContextAdvisor": ContextAdvisor,
            "CrossAgentVerifier": CrossAgentVerifier,
            "DynamicPromptWeighter": DynamicPromptWeighter,
            "EmotionArcTracker": EmotionArcTracker,
            "ExpertMixture": ExpertMixture,
            "FailureLearner": FailureLearner,
            "ForeshadowTracker": ForeshadowTracker,
            "MultiAgentDeliberation": MultiAgentDeliberation,
            "PacingAnalyzer": PacingAnalyzer,
            "PassRateMonitor": PassRateMonitor,
            "PowerScalingTracker": PowerScalingTracker,
            "PreDirectorChecklist": PreDirectorChecklist,
            "QualityAmplifier": QualityAmplifier,
            "QualityDashboard": QualityDashboard,
            "SelfReflector": SelfReflector,
            "SemanticItemRegistry": SemanticItemRegistry,
            "create_stage2_optimizer": create_stage2_optimizer,
            "StateDeltaTracker": StateDeltaTracker,
            "TreeOfThoughts": TreeOfThoughts,
            "WriterTemplate": WriterTemplate,
        }
    except ImportError as e:
        V50_MODULES_AVAILABLE = False
        print(f"⚠️ [V50] 일부 모듈 미설치: {e}")
        return None


# [V65][INF-I8] 모듈 가용성 플래그 — lazy import 전환으로 boot 시 동기화
# 초기값 False, _attach_agents()에서 실제 import 후 동기화
_spinners_mod.V50_MODULES_AVAILABLE = V50_MODULES_AVAILABLE
_spinners_mod.STAGE0_AVAILABLE = STAGE0_AVAILABLE

import asyncio

from google.genai import types

# [V40 Enhanced] 중앙 상수 관리
from modules.core.constants import (
    AIModels,
    AuditEvents,
    Emojis,
    ErrorMessages,
    GenreTypes,
    HUDKeys,
    ManuscriptLimits,
    RetryLimits,
    SuccessMessages,
)

# [V65] 모델명 상수 — constants.py AIModels SSOT
_V50_MODULE_MODEL = AIModels.V50_MODULE_MODEL
_FLASH_ANALYSIS_MODEL = AIModels.FLASH_ANALYSIS_MODEL
_SUMMARY_MODEL = AIModels.SUMMARY_MODEL
_APP_ROOT = Path(__file__).resolve().parent


class SovereignApp:
    _PROJECTS_DIR = "projects"

    def __init__(self):
        load_dotenv(override=True)
        self.ui = StudioVisualizer()
        from modules.core.logger import init_logger

        init_logger()  # [TF-26] logs/session_*.log 듀얼 출력 활성화
        self.sys = StudioSystem(api_client=genai.Client(api_key=os.getenv("GOOGLE_API_KEY")))
        self.memory = None
        self.agents = {}
        self.current_project = None
        self.metrics_session_id = None
        self.runtime_audit = []
        self.selected_genre = None  # [V40] 선택된 장르 정보
        self.diversity_engine = None  # [V48] 서사 다양성 엔진
        self.stage_rejection_history = []  # [V60.3] Stage간 REJECT 히스토리 전달
        # [V62.5] extract_cumulative_state 배치 캐시
        self._cumulative_state_cache = None
        self._cumulative_state_cache_key = None  # [S-08] 센티넬 (0은 유효한 키)
        self._state_tracker_loaded_arcs = 0  # [V62.5] StateTracker 증분 업데이트 추적
        self._prompt_builder = PromptBuilder(app=self)  # [V64 P2-2]
        self._feedback_system = FeedbackSystem()  # [V64 P2-3]
        self._stage01_helpers = Stage01Helpers(app=self)  # [Phase 4C-1b]
        self._stage2_orch = Stage2Orchestrator(app=self)  # [V64.P3]
        self._stage3_orch = Stage3Orchestrator(app=self)  # [Phase 4C-1a]
        self._stage4_orch = Stage4Orchestrator(app=self)  # [V64.P3]
        self._bootstrap_status = BootstrapStatus()
        self.perf_timer = PerfTimer("Pipeline")  # [V65] 파이프라인 성능 프로파일링
        self.world_state = None  # [V68] WorldStateManager (Stage 4에서 lazy init)
        self.fact_ledger = None  # [V68] FactLedger 누적 팩트 원장 (Stage 4에서 lazy init)

        # [LOG-1] SessionLogger — JSONL 세션 로깅
        self._session_logger = SessionLogger(
            log_dir=Path("logs/session"),
            enabled=bool(_val_threshold("session_logging.enabled", False)),
            max_file_mb=int(_val_threshold("session_logging.max_file_mb", 100)),
            max_prompt_chars=int(_val_threshold("session_logging.max_prompt_chars", 200000)),
            max_rotations=int(_val_threshold("session_logging.max_rotations", 10)),
        )
        self._pending_ui_events: list[dict[str, Any]] = []
        self.ui.set_operator_event_sink(self._capture_ui_event)
        from modules.domain.agents.base_agent import BaseAgent as _BA

        _BA.set_session_logger(self._session_logger)

        # [V66.1] B-1: narrative_summaries 캐시 (99회 DB 조회 → 1회)
        self._narrative_summaries_cache: str | None = None

        # [Phase 4B-1] AuditService 추출 — 버퍼/기록 위임
        self._audit_service = AuditService(
            runtime_audit=self.runtime_audit,
            project_paths_fn=lambda: self.current_project.paths if self.current_project else None,
            ui_log_fn=self.ui.log,
            before_summary_write_fn=self._save_pass_rate_monitor_for_audit_summary,
            project_db_fn=lambda: self.current_project.db if self.current_project else None,
        )
        self._audit_buffer = self._audit_service.buffer  # 하위 호환 참조
        atexit.register(self._flush_audit_buffer)  # [V66.1] B-3: 프로세스 종료 시 flush 보장

        # [Phase 4B-2] UIService 추출 — UI 선택/입력/표시 위임
        self._ui_service = UIService(
            ui=self.ui,
            project_fn=lambda: self.current_project,
        )

        # [Phase 4B-3] StateService 추출 — 검증/패턴/아키타입 위임
        self._state_service = StateService(
            ui=self.ui,
            audit_event_fn=self._audit_event,
            genre_fn=lambda: self.selected_genre,
            prompt_builder=self._prompt_builder,
            feedback_system=self._feedback_system,
        )

        # [Phase 4B-3] ProjectService 추출 — 리셋/되감기/롤백/소거 위임
        self._project_service = ProjectService(
            project_fn=lambda: self.current_project,
            ui=self.ui,
            safe_commit_fn=self._safe_commit,
            genre_fn=lambda: self.selected_genre,
            memory_fn=lambda: self.memory,
            state_tracker_invalidator=lambda: setattr(self, "state_tracker", None),
            world_state_fn=lambda: getattr(self, "world_state", None),
            fact_ledger_fn=lambda: getattr(self, "fact_ledger", None),
            preset_registry_restorer=self._restore_preset_registry,
            emotion_tracker_fn=lambda: getattr(self, "emotion_tracker", None),
            state_delta_tracker_fn=lambda: getattr(self, "state_delta_tracker", None),
        )

        # [V64.P4] 동적 주입 속성 선언 (monkey-patching 제거)
        self._entity_cache_arc_idx = -1  # Entity Registry 캐시 arc 인덱스
        self._cached_entity_registry = None  # Entity Registry 캐시

        # [V50] 서사 품질 향상 모듈
        # [V65] V50.1~V51.1 속성 삭제 (tension_manager, dialogue_engine, subplot_weaver, reader_simulator)
        self.pacing_analyzer = None  # [V65] 호흡 분석기 재연결
        self.quality_amplifier = None  # [V51.2] 품질 증폭기
        self.agent_intelligence = None  # [V51.3] 에이전트 지능 향상
        self.failure_learner = None  # [V51.4] 실패 학습 시스템
        self.character_voice = None  # [V51.5] 캐릭터 음성 추적
        self.foreshadow_tracker = None  # [V51.6] 복선 추적
        self.emotion_tracker = None  # [V60.26] 감정선 추적
        self.power_scaling = None  # [V60.26] 파워 스케일링 추적
        self.state_delta_tracker = None  # [V60.26] 상태 변화 추적
        self.semantic_item_registry = None  # [V60.26] 의미적 아이템 레지스트리
        self.voice_profiler = None  # [V60.26] 캐릭터 음성 프로파일러 (V58)
        self.self_reflector = None  # [V52.1] 자기 성찰 체인
        self.expert_mixture = None  # [V52.3] 전문가 혼합
        self.cross_verifier = None  # [V52.4] 교차 에이전트 검증

        # [V53] 지능 향상 모듈
        self.prompt_weighter = None  # [V53.1] 동적 프롬프트 가중치
        self.chain_of_verification = None  # [V53.2] 사실 검증 체인
        self.confidence_calibrator = None  # [V53.3] 신뢰도 보정
        self.pre_director_checklist = None  # [V53.4] 사전 체크리스트
        self.tree_of_thoughts = None  # [V53.5] Tree of Thoughts
        self.adversarial_self_play = None  # [V53.6] 적대적 자기 대결
        self.multi_agent_deliberation = None  # [V53.7] 다중 에이전트 토론

        # [V54] 비용 절감 + 품질 향상 모듈
        self.adaptive_manager = None  # [V54.3] 적응형 재시도 관리자
        # [V65] two_phase_ms/bp/arc 삭제 (Dead Code — TwoPhaseGenerator 제거)
        # [Phase 4D-4] success_patterns 삭제 (ChromaDB 레거시 제거)
        self.constitutional_checker = None  # [V55.2] 헌법적 자기검증
        self.writer_template = None  # [V55.3] 원고 템플릿
        self.pass_rate_monitor = None  # [V55.3] 통과율 모니터
        self.quality_dashboard = None  # [V60] 품질 대시보드
        self.context_advisor = None  # [SC] Smart Context Retrieval

        # [V66] SemanticPlotGuard 활성화
        self.semantic_plot_guard = None

        # [V60.95] Stage 0 프리셋 레지스트리
        self.preset_registry = None  # PresetRegistry 인스턴스

    def _restore_preset_registry(self) -> None:
        """[TF-7-P0-03] 프로젝트 _preset_state_raw에서 app.preset_registry 복원."""
        self.preset_registry = None
        _ps_raw = getattr(self.current_project, "_preset_state_raw", None) if self.current_project else None
        if _ps_raw is None:
            return
        try:
            from modules.core.stage0.preset_registry import PresetRegistry as _PresetRegistry

            self.preset_registry = _PresetRegistry.from_json(json.dumps(_ps_raw, ensure_ascii=False))
        except Exception as _e:
            self.ui.log(f"   ⚠️ [TF7-P0-03] preset_registry 복원 실패 (무시): {_e}")

    def _safe_commit(self) -> bool:
        """
        [V40 Enhanced] 안전한 DB 커밋 래퍼 (동기 전용)
        [V61.7] 항상 커밋 보장 (in_transaction 조건 제거)

        Returns:
            bool: 커밋 성공 여부
        """
        if hasattr(self, "current_project") and self.current_project and hasattr(self.current_project, "db"):
            try:
                self.current_project.db.conn.commit()
                self._audit_event(AuditEvents.DB_COMMIT, SuccessMessages.DB_COMMIT_SUCCESS)
                return True
            except Exception as e:
                self.ui.log(f"{Emojis.ERROR} [DB] {ErrorMessages.DB_COMMIT_FAILED}: {e}")
                self._audit_event(AuditEvents.DB_ROLLBACK, ErrorMessages.DB_COMMIT_FAILED, {"error": str(e)})
                try:
                    self.current_project.db.conn.rollback()
                    self.ui.log("↩️ [DB] 롤백 완료")
                except Exception as rollback_error:
                    self.ui.log(f"{Emojis.WARNING} [DB] 롤백도 실패: {rollback_error}")
                return False
        return False

    def _resolve_ui_event_session_id(self) -> str | None:
        fallback = None
        try:
            from modules.core.logger import _studio_logger

            if _studio_logger is not None:
                fallback = getattr(_studio_logger, "session_name", None)
        except Exception:
            fallback = None
        return resolve_logging_session_id(
            getattr(self, "current_project", None),
            getattr(self, "metrics_session_id", None),
            fallback=fallback,
        )

    def _persist_ui_event(self, event: dict) -> None:
        payload = dict(event)
        payload["session_id"] = self._resolve_ui_event_session_id()
        self._session_logger.log_ui_event(**payload)
        current_project = getattr(self, "current_project", None)
        db = getattr(current_project, "db", None)
        if db is not None and hasattr(db, "save_ui_event"):
            db.save_ui_event(**payload)

    def _capture_ui_event(self, event: dict) -> None:
        if not isinstance(event, dict):
            return
        current_project = getattr(self, "current_project", None)
        if current_project is None or getattr(current_project, "db", None) is None:
            pending = getattr(self, "_pending_ui_events", None)
            if isinstance(pending, list):
                pending.append(dict(event))
            return
        self._persist_ui_event(event)

    def _flush_pending_ui_events(self) -> None:
        pending = getattr(self, "_pending_ui_events", None)
        if not pending:
            return
        current_project = getattr(self, "current_project", None)
        if current_project is None or getattr(current_project, "db", None) is None:
            return
        buffered = list(pending)
        pending.clear()
        for event in buffered:
            self._persist_ui_event(event)

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

    def _enrich_director_result(self, audit_result: dict, stage: int, content_length: int = 0) -> dict:
        """
        [V60.3] Director 결과에 action_items 및 에러 카테고리 정보 추가

        Args:
            audit_result: Director 원본 결과
            stage: 현재 Stage (2, 3, 4)
            content_length: 콘텐츠 길이 (분량 체크용)

        Returns:
            dict: 풍부해진 Director 결과
        """
        if not isinstance(audit_result, dict):
            return audit_result

        # 에러 카테고리 구분 (QUALITY_ISSUE vs LOGIC_ERROR)
        error_category = audit_result.get("error_category", "UNKNOWN")
        reason = audit_result.get("reason", "")

        # 에러 카테고리 자동 분류
        if error_category == "UNKNOWN":
            logic_error_keywords = ["인과", "설정 오류", "죽은", "순간이동", "무기 전환", "캐릭터 붕괴", "타임라인"]
            quality_issue_keywords = ["분량", "밀도", "묘사", "문체", "건조", "재미"]

            if any(kw in reason for kw in logic_error_keywords):
                error_category = "LOGIC_ERROR"
            elif any(kw in reason for kw in quality_issue_keywords):
                error_category = "QUALITY_ISSUE"
            else:
                error_category = "QUALITY_ISSUE"  # 기본값

        audit_result["error_category"] = error_category

        # action_items 생성
        action_items = []

        if audit_result.get("decision") == "REJECT":
            # 분량 문제
            if stage == 4 and content_length > 0:
                if content_length < ManuscriptLimits.MIN_LENGTH:
                    action_items.append(
                        {
                            "type": "QUALITY_ISSUE",
                            "description": f"분량 절대 미달 ({content_length}자)",
                            "severity": "CRITICAL",
                            "suggestion": f"최소 {ManuscriptLimits.MIN_LENGTH - content_length}자 추가 필요. 심리 묘사, 조연 리액션, 환경 묘사로 보충.",
                        }
                    )
                elif content_length < ManuscriptLimits.WARNING_LENGTH:
                    action_items.append(
                        {
                            "type": "QUALITY_ISSUE",
                            "description": f"분량 위험 영역 ({content_length}자)",
                            "severity": "HIGH",
                            "suggestion": "500자 이상 추가하여 안전 영역(4,500자)으로 확보.",
                        }
                    )

            # 서사 흐름 문제
            if "폭주" in reason:
                action_items.append(
                    {
                        "type": "LOGIC_ERROR",
                        "description": "서사 폭주 감지",
                        "severity": "CRITICAL",
                        "suggestion": "사건을 더 잘게 쪼개라. 1~2개 장면에 모든 사건이 해결되면 안 됨.",
                    }
                )
            if "정체" in reason:
                action_items.append(
                    {
                        "type": "LOGIC_ERROR",
                        "description": "서사 정체 감지",
                        "severity": "CRITICAL",
                        "suggestion": "3개 장면 이상 같은 상황 반복 금지. 인과적 전진을 확보하라.",
                    }
                )

            # 에러 카테고리별 일반 가이드
            if error_category == "LOGIC_ERROR" and not action_items:
                action_items.append(
                    {
                        "type": "LOGIC_ERROR",
                        "description": reason[:100] if reason else "논리 오류",
                        "severity": "HIGH",
                        "suggestion": "Analyst의 Arc 설계 재검토 필요. 설정 충돌 또는 인과 오류 수정.",
                    }
                )
            elif error_category == "QUALITY_ISSUE" and not action_items:
                action_items.append(
                    {
                        "type": "QUALITY_ISSUE",
                        "description": reason[:100] if reason else "품질 미달",
                        "severity": "MEDIUM",
                        "suggestion": "Writer가 직접 수정 가능. 밀도 높이고 묘사 추가.",
                    }
                )

        audit_result["action_items"] = action_items

        # [V60.5] score_breakdown 분석 및 단계별 피드백 생성
        score_breakdown = audit_result.get("score_breakdown", {})
        if score_breakdown and audit_result.get("decision") == "REJECT":
            breakdown_feedback = self._analyze_score_breakdown(score_breakdown)
            if breakdown_feedback:
                audit_result["breakdown_feedback"] = breakdown_feedback
                # action_items에 단계별 감점 정보 추가
                for area, info in breakdown_feedback.items():
                    if info.get("severity") in ["CRITICAL", "HIGH"]:
                        action_items.append(
                            {
                                "type": "SCORE_BREAKDOWN",
                                "description": f"{info['name']}: {info['score']}/{info['max']}점",
                                "severity": info["severity"],
                                "suggestion": info["suggestion"],
                            }
                        )

        # 책임 소재 명시
        if error_category == "LOGIC_ERROR":
            audit_result["responsibility"] = "ANALYST"  # Arc 재설계 필요
            audit_result["responsibility_guide"] = "Analyst의 Arc 설계에 문제 있음. 재설계 검토."
        else:
            audit_result["responsibility"] = "WRITER"  # 재작성으로 해결 가능
            audit_result["responsibility_guide"] = "Writer가 재작성으로 해결 가능."

        # [V60.6] REJECT 사유 정량화
        if audit_result.get("decision") == "REJECT" and stage == 4:
            quantified = self._quantify_reject_feedback(
                reason=reason, content_length=content_length, audit_result=audit_result
            )
            if quantified:
                audit_result["quantified_feedback"] = quantified
                # action_items에 정량화된 지시 추가
                for q_item in quantified:
                    action_items.append(q_item)

        return audit_result

    def _quantify_reject_feedback(self, reason: str, content_length: int, audit_result: dict) -> list:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.quantify_reject_feedback(reason, content_length, audit_result)

    def _analyze_score_breakdown(self, breakdown: dict) -> dict:
        """
        [V60.5] Director의 score_breakdown을 분석하여 단계별 피드백 생성

        Args:
            breakdown: Director의 score_breakdown 딕셔너리

        Returns:
            dict: 영역별 분석 결과
        """
        # 영역별 설정
        area_config = {
            "setting_consistency": {
                "name": "설정 일관성",
                "max": 25,
                "thresholds": {"critical": 0, "high": 15, "medium": 20},
                "suggestions": {
                    "critical": "미습득 무공 사용, 죽은 인물 등장, 물리적 인과 붕괴 확인. Hard Constraint 위반 수정 필수.",
                    "high": "보조 NPC 이름, 장소명 등 경미한 설정 확인. 직전 원고와 대조.",
                    "medium": "세부 설정 일관성 점검. 무기, 의복, 시간대 확인.",
                },
            },
            "scene_composition": {
                "name": "장면 구성",
                "max": 25,
                "thresholds": {"critical": 10, "high": 15, "medium": 20},
                "suggestions": {
                    "critical": "씬 수가 부족함. Blueprint의 6개 씬을 모두 균등하게 반영하라.",
                    "high": "일부 씬이 누락되거나 요약됨. 후반부 씬 밀도를 높여라.",
                    "medium": "씬간 밀도 불균형. 전반부와 후반부 분량을 균등하게 배분하라.",
                },
            },
            "narrative_flow": {
                "name": "서사 흐름",
                "max": 20,
                "thresholds": {"critical": 0, "high": 10, "medium": 15},
                "suggestions": {
                    "critical": "서사 폭주 또는 정체 감지됨. 사건 속도를 조절하고 인과적 전진을 확보하라.",
                    "high": "약간의 반복 또는 급전개. 장면간 연결을 자연스럽게 다듬어라.",
                    "medium": "추진력 부족. 다음 화로 이어지는 긴장감을 추가하라.",
                },
            },
            "length_fulfillment": {
                "name": "분량 충족",
                "max": 15,
                "thresholds": {"critical": 0, "high": 8, "medium": 12},
                "suggestions": {
                    "critical": "4,000자 미만으로 절대 부족. 심리 묘사, 조연 리액션, 환경 묘사로 보충하라.",
                    "high": "4,000~4,500자로 위험 영역. 500자 이상 추가 필요.",
                    "medium": "4,500~5,000자로 안전 영역이나 5,000자 이상 권장.",
                },
            },
            "prose_quality": {
                "name": "문체 품질",
                "max": 15,
                "thresholds": {"critical": 0, "high": 5, "medium": 10},
                "suggestions": {
                    "critical": "가독성 심각하게 떨어짐. 문장 구조를 다듬고 리듬감을 살려라.",
                    "high": "건조한 문체. 감각 묘사, 비유, 대화의 생동감을 추가하라.",
                    "medium": "가독성은 양호하나 몰입감 부족. 독자 경험 향상 필요.",
                },
            },
        }

        result = {}
        for area, config in area_config.items():
            score = breakdown.get(area, config["max"])  # 없으면 만점으로 간주
            # [TypeSafety] LLM이 score를 문자열로 반환할 수 있음
            try:
                score = int(score)
            except (TypeError, ValueError):
                score = config["max"]

            # 심각도 판단
            if score <= config["thresholds"]["critical"]:
                severity = "CRITICAL"
            elif score <= config["thresholds"]["high"]:
                severity = "HIGH"
            elif score <= config["thresholds"]["medium"]:
                severity = "MEDIUM"
            else:
                severity = "OK"

            if severity != "OK":
                result[area] = {
                    "name": config["name"],
                    "score": score,
                    "max": config["max"],
                    "severity": severity,
                    "suggestion": config["suggestions"].get(severity.lower(), ""),
                }

        return result

    def _simplify_prompt_for_retry(self, enhanced_feedback: str, core_feedback: str, attempt: int) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.simplify_prompt_for_retry(enhanced_feedback, core_feedback, attempt)

    def _build_strong_kind_feedback(self, violations: list, attempt: int, protagonist_name: str = "주인공") -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.build_strong_kind_feedback(violations, attempt, protagonist_name)

    def _build_focused_context(self, violations: list, prev_arcs: list, protagonist_name: str) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.build_focused_context(violations, prev_arcs, protagonist_name)

    def _build_minimal_arc_context(self, prev_arcs: list, protagonist_name: str) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.build_minimal_arc_context(prev_arcs, protagonist_name)

    def _generate_arc_position_guide(self, arc_pos: int, total_eps: int) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.generate_arc_position_guide(arc_pos, total_eps)

    def _get_dynamic_critical_keywords(self) -> list:
        """
        [V60.3] FailureLearner에서 고빈도 실패 패턴을 동적으로 추출

        Returns:
            list: 기본 키워드 + 고빈도 실패 패턴 키워드
        """
        # 기본 하드코딩 키워드
        base_keywords = ["서사 폭주", "서사 정체", "모순", "동선 충돌", "시간 역행", "중복", "CRITICAL"]

        if not V50_MODULES_AVAILABLE or not self.failure_learner:
            return base_keywords

        try:
            # FailureLearner에서 고빈도 카테고리 추출
            category_counts = {}
            for record in self.failure_learner.records:
                cat = record.category.value if hasattr(record.category, "value") else str(record.category)
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # 3회 이상 발생한 카테고리를 critical로 추가
            high_freq_keywords = []
            category_to_keyword = {
                "item_duplicate": "중복 획득",
                "item_missing": "미획득 사용",
                "state_discontinuity": "상태 불연속",
                "timeline_error": "타임라인",
                "scope_overflow": "범위 초과",
                "relationship_jump": "관계 급변",
                "villain_stupidity": "악역 지능",
                "free_powerup": "공짜 파워업",
            }
            for cat, count in category_counts.items():
                if count >= 3 and cat in category_to_keyword:
                    high_freq_keywords.append(category_to_keyword[cat])

            return base_keywords + high_freq_keywords
        except (AttributeError, KeyError, TypeError):  # [V64.P4] OPTIONAL: keyword extraction fallback
            return base_keywords

    # ═══════════════════════════════════════════════════════════════════════════
    # [V60.8] Writer 사전 가이드 시스템 - Director REJECT 방지
    # ═══════════════════════════════════════════════════════════════════════════

    def _generate_writer_guidance_v60_8(
        self,
        blueprint: dict,
        prev_manuscript: str = "",
        episode_bibles: list = None,
        cliche_check_result: dict = None,
        target_len: int = ManuscriptLimits.TARGET_LENGTH,
    ) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.generate_writer_guidance_v60_8(
            blueprint, prev_manuscript, episode_bibles, cliche_check_result, target_len
        )

    def _generate_structured_arc_feedback(
        self, continuity_result: dict, prev_arcs: list = None, arc_no: int = 1
    ) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_structured_arc_feedback(continuity_result, prev_arcs, arc_no)

    def _generate_reverse_feedback_stage4_to_3(
        self, writer_reject_reason: str, pre_checklist_result: dict = None
    ) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_reverse_feedback_stage4_to_3(writer_reject_reason, pre_checklist_result)

    def _generate_reverse_feedback_stage3_to_2(self, architect_failures: list = None, arc_no: int = 1) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_reverse_feedback_stage3_to_2(architect_failures, arc_no)

    def _generate_reverse_feedback_stage4_to_2(self, arc_difficulty: dict | None = None) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_reverse_feedback_stage4_to_2(arc_difficulty)

    def _generate_arc_context_v60(self, all_refined_arcs: list, current_arc_no: int = None) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.generate_arc_context_v60(all_refined_arcs, current_arc_no)

    def _get_adaptive_feedback_intensity(self, retry_count: int, stage: int = 4) -> dict:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.get_adaptive_feedback_intensity(retry_count, stage)

    def _analyze_rejection_pattern_v60(self, rejection_history: list, current_arc_no: int) -> str:
        """
        [V60.10] REJECT 패턴 분석 및 타겟 피드백 생성

        반복되는 REJECT 사유를 분석하여 집중해야 할 수정 포인트를 도출

        Args:
            rejection_history: 이 Arc의 REJECT 이력
            current_arc_no: 현재 Arc 번호

        Returns:
            구조화된 피드백 문자열
        """
        if not rejection_history:
            return ""

        # 사유별 카운트
        reason_counts = {}
        bucket_samples = {}
        detail_samples = []

        for reject in rejection_history:
            reason = str(reject.get("reason", "unknown") or "unknown")
            # 사유 정규화
            normalized = self._normalize_rejection_reason(reason)
            reason_counts[normalized] = reason_counts.get(normalized, 0) + 1
            bucket_samples.setdefault(normalized, [])
            compact_reason = reason[:100]
            if compact_reason and compact_reason not in bucket_samples[normalized]:
                bucket_samples[normalized].append(compact_reason)

            for detail_key in ("specific_issue", "failure_category", "fix_scope"):
                detail = str(reject.get(detail_key, "") or "").strip()
                if detail and detail not in detail_samples:
                    detail_samples.append(detail[:120])

        if not reason_counts:
            return ""

        # 가장 많이 반복된 사유 추출
        top_reasons = sorted(reason_counts.items(), key=lambda x: -x[1])[:3]

        lines = [
            "",
            "=" * 60,
            f"🔍 [V60.10] Arc {current_arc_no} REJECT 패턴 분석",
            "=" * 60,
            "",
            f"📊 총 {len(rejection_history)}회 REJECT 발생. 반복 패턴:",
            "",
        ]

        for reason, count in top_reasons:
            lines.append(f"   🔴 {reason}: {count}회")
            samples = bucket_samples.get(reason, [])
            if samples:
                lines.append(f"      ↳ 대표 사유: {samples[0]}")
            # 패턴별 수정 가이드
            guide = self._get_rejection_fix_guide(reason)
            if guide:
                lines.append(f"      💡 수정 방향: {guide}")

        if detail_samples:
            lines.append("")
            lines.append("📋 구체적 문제 지점:")
            for issue in detail_samples[:3]:
                lines.append(f"   - {issue}")

        lines.extend(["", "=" * 60, ""])

        return "\n".join(lines)

    def _normalize_rejection_reason(self, reason: str) -> str:
        """REJECT 사유 정규화"""
        reason = reason or ""
        reason_lower = reason.lower()

        if "중복" in reason or "duplicate" in reason_lower:
            return "아이템 중복 획득"
        if "수여" in reason or "grant" in reason_lower or "획득 시점" in reason:
            return "수여/획득 타이밍 오류"
        if "부상" in reason or "injury" in reason_lower or "회복" in reason:
            return "부상/회복 연속성 오류"
        if "위치" in reason or "location" in reason_lower or "이동" in reason:
            return "위치/이동 연속성 오류"
        if "소지" in reason or "inventory" in reason_lower or "장비" in reason:
            return "소지품 연속성 오류"
        if "내공" in reason or "energy" in reason_lower or "마나" in reason or "자원" in reason:
            return "내공/자원 상태 오류"
        if "json" in reason_lower or "parsing" in reason_lower or "format" in reason_lower:
            return "JSON 파싱 오류"
        if (
            "설정" in reason
            or "모순" in reason
            or "continuity" in reason_lower
            or "consistency" in reason_lower
            or "충돌" in reason
        ):
            return "설정/연속성 충돌"
        if (
            "인과" in reason
            or "logic" in reason_lower
            or "causal" in reason_lower
            or "구조" in reason
            or "개연" in reason
        ):
            return "인과/구조 붕괴"
        if (
            "반복" in reason
            or "정체" in reason
            or "stagn" in reason_lower
            or "repet" in reason_lower
            or "루프" in reason
        ):
            return "반복 전개/서사 정체"
        if (
            "길이" in reason
            or "length" in reason_lower
            or "분량" in reason
            or "밀도" in reason
            or "후반" in reason
            or "scene count" in reason_lower
        ):
            return "밀도/분량 부족"
        if "범위" in reason or "scope" in reason_lower or "화수" in reason or "ep_count" in reason_lower:
            return "범위 초과/미달"

        return "기타"

    def _get_rejection_fix_guide(self, normalized_reason: str) -> str:
        """정규화된 REJECT 사유에 대한 수정 가이드"""
        guides = {
            "아이템 중복 획득": "이전 Arc에서 획득한 아이템 목록을 확인하고, 새 아이템만 설계하세요.",
            "수여/획득 타이밍 오류": "획득/수여 장면보다 먼저 결과물을 사용하지 말고, 획득 시점을 Arc 본문에 명시하세요.",
            "부상/회복 연속성 오류": "직전 Arc 종료 시 부상 상태를 확인하고, 회복 장면 없이 멀쩡해지지 마세요.",
            "위치/이동 연속성 오류": "직전 Arc 종료 위치에서 시작하고, 이동 경로를 명시하세요.",
            "소지품 연속성 오류": "직전 Arc 종료 시 소지품 그대로 시작하고, 새 획득은 명확히 구분하세요.",
            "내공/자원 상태 오류": "내공·마나·자원 소모/회복을 누적 추적하고, 급격한 변화를 피하세요.",
            "JSON 파싱 오류": "출력이 순수 JSON인지 확인하세요. 설명문이나 마크다운을 포함하지 마세요.",
            "밀도/분량 부족": "후반부 사건과 반응을 늘리고, 씬별 목표 분량을 먼저 배정하세요.",
            "범위 초과/미달": "할당된 화수 범위를 정확히 지키세요.",
            "설정/연속성 충돌": "직전 Arc의 상태, 인물 관계, 세계 규칙을 체크리스트로 고정한 뒤 설계를 다시 정렬하세요.",
            "인과/구조 붕괴": "사건의 원인-결과 사슬을 다시 쓰고, 장면 의존성을 줄여 구조를 단순화하세요.",
            "반복 전개/서사 정체": "같은 목적·장소·대화가 반복되는 구간을 줄이고, 장면마다 서사적 전진을 1개 이상 배치하세요.",
            "기타": "반복된 raw REJECT 사유를 그대로 제약 블록에 승격하고, 가장 최근 수정 지시부터 우선 반영하세요.",
        }
        return guides.get(normalized_reason, guides["기타"])

    def _emergency_shutdown(self) -> None:
        """
        [V40.1 Critical Fix] 긴급 시스템 종료 핸들러

        초기화 단계에서 치명적 오류 발생 시 리소스를 안전하게 정리합니다.
        - DB 연결 종료
        - 벡터 DB 연결 해제
        - 감사 로그 기록
        """
        self._audit_event("emergency_shutdown", "System emergency shutdown initiated")
        # [V66.1] B-3: 종료 전 버퍼 flush
        self._flush_audit_buffer()
        try:
            if hasattr(self, "current_project") and self.current_project:
                if hasattr(self.current_project, "db") and self.current_project.db:
                    try:
                        self.current_project.db.conn.close()
                        self.ui.log("🔌 [Shutdown] DB 연결 종료")
                    except Exception as db_err:
                        self.ui.log(f"{Emojis.WARNING} [Shutdown] DB 종료 중 오류: {db_err}")
            if hasattr(self, "memory") and self.memory:
                try:
                    # [Phase 4D-2] VecMemory 리소스 정리
                    self.memory.close()
                    self.memory = None
                    self.ui.log("🔌 [Shutdown] 벡터 DB 연결 해제")
                except Exception as mem_err:
                    self.ui.log(f"{Emojis.WARNING} [Shutdown] 메모리 정리 중 오류: {mem_err}")
        except Exception as e:
            self.ui.log(f"{Emojis.ERROR} [Shutdown] 긴급 종료 중 예외: {e}")

    def _init_diversity_engine(self, window_size: int = 10) -> bool:
        """
        [V48] 서사 다양성 엔진 초기화

        Pattern Tracking + Diversity Sampling + Contrastive CoT 통합 시스템을
        현재 프로젝트에 맞게 초기화합니다.

        Args:
            window_size: 패턴 분석 윈도우 크기 (기본 10화)

        Returns:
            bool: 초기화 성공 여부
        """
        if not self.current_project:
            self.ui.log(f"{Emojis.WARNING} [DiversityEngine] 프로젝트가 로드되지 않아 초기화 생략")
            return False

        try:
            genre_type = "wuxia"
            if self.selected_genre:
                genre_type = self.selected_genre.get("type", "wuxia")

            self.diversity_engine = NarrativeDiversityEngine(
                context=self.current_project, genre=genre_type, window_size=window_size
            )

            # 최근 에피소드 분석
            report = self.diversity_engine.analyze_recent_episodes(window_size)

            if report and report.get("status") == "analyzed":
                high_count = report.get("high_severity_count", 0)
                if high_count > 0:
                    self.ui.log(f"📊 [V48 DiversityEngine] 패턴 분석 완료 - HIGH 경고 {high_count}개 감지")
                else:
                    self.ui.log("📊 [V48 DiversityEngine] 패턴 분석 완료 - 반복 수준 양호")

                self._audit_event(
                    "diversity_engine_init",
                    "NarrativeDiversityEngine initialized",
                    {"genre": genre_type, "window_size": window_size, "high_severity_count": high_count},
                )
            else:
                self.ui.log("📊 [V48 DiversityEngine] 초기화 완료 (분석 데이터 부족)")

            return True

        except Exception as e:
            self.ui.log(f"{Emojis.WARNING} [DiversityEngine] 초기화 실패: {e}")
            self._audit_event("diversity_engine_error", "init failed", {"error": str(e)})
            self.diversity_engine = None
            return False

    def _get_projects_root(self) -> Path:
        return resolve_projects_root(_APP_ROOT)

    def _get_project_dir(self, project_name: str) -> Path:
        return resolve_project_dir(project_name, _APP_ROOT)

    def _get_current_project_log_path(self, filename: str) -> Path:
        if self.current_project and hasattr(self.current_project, "paths"):
            return self.current_project.paths.root / "logs" / filename
        if self.current_project and getattr(self.current_project, "name", ""):
            return self._get_project_dir(self.current_project.name) / "logs" / filename
        raise RuntimeError("current project is not bound")

    def _reload_project_environment(self, project_name: str) -> Path | None:
        """Load project-local environment from the bound project root."""
        project_env_path = self._get_project_dir(project_name) / ".env"
        if not project_env_path.exists():
            return None

        load_dotenv(project_env_path, override=True)
        self.ui.log(f"   🔑 [V60.37] 프로젝트별 API 키 로드: {project_env_path}")

        new_api_key = os.getenv("GOOGLE_API_KEY")
        if new_api_key:
            self.sys = StudioSystem(api_client=genai.Client(api_key=new_api_key))
            # [V61.9] 프로젝트별 멀티키 재초기화 (GOOGLE_API_KEY_2~9 반영)
            from modules.domain.agents.base_agent import BaseAgent

            BaseAgent._keys_initialized = False
            BaseAgent._current_key_idx = 0
            BaseAgent._context_caches.clear()
            BaseAgent._init_api_keys()

        return project_env_path

    def _retarget_project_runtime_sinks(self) -> None:
        current_project = getattr(self, "current_project", None)
        paths = getattr(current_project, "paths", None)
        if paths is None:
            return

        session_logger = getattr(self, "_session_logger", None)
        if session_logger is not None and hasattr(session_logger, "set_log_dir"):
            session_logger.set_log_dir(paths.root / "logs" / "session")

        from modules.core.logger import _studio_logger

        if _studio_logger is not None:
            _studio_logger.retarget(paths.root / "logs")

        collector = get_metrics_collector(paths.root / "logs" / "metrics")
        metrics_session_id = getattr(collector, "session_id", None)
        if isinstance(metrics_session_id, str) and metrics_session_id.strip():
            self.metrics_session_id = metrics_session_id.strip()
            setattr(current_project, "metrics_session_id", self.metrics_session_id)

        SovereignApp._flush_pending_ui_events(self)

    def _bind_selected_project(self, project_name: str) -> None:
        reload_env = getattr(self, "_reload_project_environment", None)
        if callable(reload_env):
            reload_env(project_name)

        genre_type = self.selected_genre.get("type", "wuxia") if isinstance(self.selected_genre, dict) else "wuxia"
        projects_root_fn = getattr(self, "_get_projects_root", None)
        projects_root = projects_root_fn() if callable(projects_root_fn) else None
        self.sys.boot_v20_project(project_name, genre=genre_type, projects_root=projects_root)
        self.current_project = self.sys.project
        SovereignApp._retarget_project_runtime_sinks(self)

    def _restore_boot_runtime_state(self) -> None:
        from modules.core.prompt_loader import PromptLoader

        PromptLoader().invalidate_cache()

        restore_preset_registry = getattr(self, "_restore_preset_registry", None)
        if callable(restore_preset_registry):
            restore_preset_registry()
        if getattr(self, "preset_registry", None) is not None:
            self.ui.log("   ✅ [TF7-P0-03] preset_registry DB에서 복원 완료")

    def _ensure_project_genre_alignment(self) -> bool:
        current_project = getattr(self, "current_project", None)
        if current_project is None:
            return False

        current_project.genre = self.selected_genre
        db = getattr(current_project, "db", None)
        if db is None:
            return True

        stored_genre = db.load_anchor("genre_info")
        if stored_genre:
            if stored_genre.get("type") != self.selected_genre["type"]:
                self.ui.log("⚠️ [Warning] 프로젝트 장르 불일치 감지!")
                self.ui.log(f"   저장된 장르: {stored_genre.get('name', '알 수 없음')}")
                self.ui.log(f"   선택한 장르: {self.selected_genre['name']}")

                choice = input("\n계속하시겠습니까? (y/n): ").strip().lower()
                if choice != "y":
                    self.ui.log("❌ 시스템을 종료합니다.")
                    SovereignApp._emergency_shutdown(self)
                    sys.exit(0)
        else:
            db.save_anchor("genre_info", self.selected_genre)
            self.ui.log(f"💾 프로젝트 장르 정보 저장: {self.selected_genre['name']}")

        return True

    def _initialize_project_genre_runtime(self) -> None:
        current_project = getattr(self, "current_project", None)
        if current_project is None:
            return

        from modules.core.genre_hud_manager import create_hud_manager, log_hud_compatibility_report

        self.sys.hud = create_hud_manager(self.selected_genre["type"], current_project)
        self.ui.log(f"   ✅ [{self.selected_genre['name']}] HUD 시스템 초기화 완료")
        log_hud_compatibility_report(self.sys.hud, logger=self.ui.log)

        from modules.core.genre_guards import create_genre_guard

        self.sys.guard = create_genre_guard(self.selected_genre["type"])
        current_project.guard = self.sys.guard
        self.ui.log(f"🛡️ [{self.selected_genre['name']}] Guard 시스템 초기화 완료")

        work_guard_path = current_project.paths.config / "work_guard.yaml"
        if work_guard_path.exists():
            from modules.core.genre_guards.work_guard import WorkGuard

            self.sys.guard = WorkGuard(self.sys.guard, work_guard_path)
            current_project.guard = self.sys.guard
            self.ui.log("   🧥 WorkGuard 적용 완료 (작품별 커스텀 규칙 활성)")

    def _initialize_project_runtime_support(self, project_name: str) -> bool:
        check_vector_db_lock = getattr(self, "_check_vector_db_lock", None)
        if callable(check_vector_db_lock) and not check_vector_db_lock(project_name):
            self.ui.log("❌ [System] 치명적 데이터 결함으로 인해 기동을 중단합니다.")
            return False

        current_project = getattr(self, "current_project", None)
        if current_project is None or getattr(current_project, "db", None) is None:
            return False

        current_project.paths.memory.mkdir(parents=True, exist_ok=True)
        self.memory = VecMemory(
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            ui_log=self.ui.log,
            conn=current_project.db.conn,
            lock=current_project.db._lock,
        )
        if self.memory.is_operational():
            self.ui.log("✅ [VecMemory] sqlite-vec 벡터 엔진 초기화 완료")
        else:
            self.ui.log(f"⚠️ [VecMemory] 벡터 엔진 비활성: {self.memory.initialization_error}")

        attach_agents = getattr(self, "_attach_agents", None)
        if callable(attach_agents) and not attach_agents():
            self.ui.log("❌ [System] 에이전트 초기화 실패로 인해 기동을 중단합니다.")
            return False

        return True

    def boot(self):
        self.ui.title("V40 SOVEREIGN COCKPIT", "Multi-Genre Production Factory")

        # [V40] 장르 선택 우선
        self.selected_genre = self._select_genre()

        project_name = self._select_project()
        if not project_name:
            self.ui.log("⚠️ 프로젝트 선택이 취소되어 부팅을 중단합니다.")
            return

        # [V60.37] 프로젝트별 .env 로드 지원
        SovereignApp._bind_selected_project(self, project_name)

        SovereignApp._restore_boot_runtime_state(self)
        if not SovereignApp._ensure_project_genre_alignment(self):
            return
        SovereignApp._initialize_project_genre_runtime(self)
        if not SovereignApp._initialize_project_runtime_support(self, project_name):
            return

        self._run_main_process()

    def _load_models_yaml(self) -> dict:
        """Load the canonical repo-root models config."""
        try:
            return load_models_yaml()
        except Exception as e:
            self.ui.log(f"{Emojis.WARNING} [Config] models.yaml load failed: {e}")
            return {}

    def _get_agent_model_map(self) -> dict:
        config = self._load_models_yaml()
        agents = config.get("agents", {})
        if isinstance(agents, dict) and agents:
            return agents

        # Legacy fallback for compatibility if models.yaml is absent.
        legacy = self.sys.get_v20_orchestrator_config().get("models", {})
        return legacy if isinstance(legacy, dict) else {}

    def _ignite_quad_cache_system(self):
        """[V31] 4중 캐시 시스템 (Writer, Architect, Analyst, Weaver)"""
        import json

        self.ui.log("🧬 [System] V31 3중 캐싱 시스템(Triple-Cache) 동기화 중...")

        # 0. 설정된 모델명 확보 (ConfigManager 기반)
        config = self._get_agent_model_map()

        # API 호출을 위해 'models/' 접두사 확인
        def fix_model_id(mid):
            return f"models/{mid}" if not mid.startswith("models/") else mid

        # 1. 파일 데이터 로드 및 조립
        # (A) Writer
        writer_rules_path = self.current_project.paths.config / "prompts" / "writer_rules.json"
        writer_context = "[SYSTEM: ABSOLUTE WRITER MANIFESTO]\n"
        if writer_rules_path.exists():
            try:
                w_data = json.loads(writer_rules_path.read_text(encoding="utf-8"))
                writer_context += "\n".join(w_data.get("common_manifesto", [])) + "\n"
            except (json.JSONDecodeError, ValueError) as _wr_err:
                logging.warning("[P1] writer_rules.json 파싱 실패 (무시): %s", _wr_err)
        # [V65] (B) Architect 캐시 삭제 (레거시 에이전트 제거)

        # (C) Analyst
        analyst_lib_path = self.current_project.paths.config / "prompts" / "analyst_libraries.json"
        analyst_context = "[SYSTEM: NARRATIVE STRATEGY LIBRARIES]\n"
        if analyst_lib_path.exists():
            analyst_context += analyst_lib_path.read_text(encoding="utf-8")

        # [D] Weaver Cache 추가
        weaver_rules_path = self.current_project.paths.config / "prompts" / "weaver_rules.json"
        weaver_context = "[SYSTEM: GRAND WEAVER MANIFESTO]\n"
        if weaver_rules_path.exists():
            weaver_context += weaver_rules_path.read_text(encoding="utf-8")

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
                        model=fix_model_id(config.get("writer", AIModels.STAGE2_MAIN_MODEL)),
                        config=types.CreateCachedContentConfig(
                            display_name="WRITER_V31",
                            system_instruction="소설가",
                            contents=[writer_context],
                            ttl="86400s",
                        ),
                    )
                    cache_info["writer_cache"] = w_cache.name
                except Exception as e:
                    self.ui.log(f"   ❌ 캐시 생성 실패: {e}")
                    cache_info["writer_cache"] = None

        # [V65] [B] Architect Cache 삭제 (레거시 에이전트 제거)

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
                        model=fix_model_id(config.get("analyst", AIModels.STAGE2_MAIN_MODEL)),
                        config=types.CreateCachedContentConfig(
                            display_name="ANALYST_V31",
                            system_instruction="전략가",
                            contents=[analyst_context],
                            ttl="86400s",
                        ),
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
                        model=fix_model_id(config.get("weaver", config.get("manager", _V50_MODULE_MODEL))),
                        config=types.CreateCachedContentConfig(
                            display_name="WEAVER_V31",
                            system_instruction="복선 설계자",
                            contents=[weaver_context],
                            ttl="86400s",
                        ),
                    )
                    cache_info["weaver_cache"] = w_cache.name
                except Exception as e:
                    self.ui.log(f"   ❌ Weaver 캐시 생성 실패: {e}")
                    cache_info["weaver_cache"] = None

        # [V40.1 Critical Fix] 캐시 정보를 DB에 영속화 (재시작 시 캐시 재사용 보장)
        cache_metadata_persisted = False
        try:
            save_ok = bool(self.current_project.db.save_anchor("sys_caches", cache_info))
            commit_ok = bool(self._safe_commit())
            cache_metadata_persisted = save_ok and commit_ok
            if cache_metadata_persisted:
                self.ui.log(f"{Emojis.SAVE} [System] 캐시 정보 DB 저장 완료")
                self._audit_event(
                    AuditEvents.CACHE_CREATED,
                    SuccessMessages.CACHE_CREATED,
                    {
                        "writer": bool(cache_info.get("writer_cache")),
                        # [V65] architect 캐시 항목 삭제
                        "analyst": bool(cache_info.get("analyst_cache")),
                        "weaver": bool(cache_info.get("weaver_cache")),
                    },
                )
            else:
                self.ui.log(f"{Emojis.WARNING} [System] 캐시 정보 저장 실패 - 캐시 주입 생략")
                self._audit_event(
                    "cache_save_error",
                    ErrorMessages.DB_COMMIT_FAILED,
                    {"save_ok": save_ok, "commit_ok": commit_ok},
                )
        except Exception as save_err:
            self.ui.log(f"{Emojis.ERROR} [System] 캐시 정보 DB 저장 실패: {save_err}")
            self._audit_event("cache_save_error", ErrorMessages.DB_COMMIT_FAILED, {"error": str(save_err)})

        # [V40 Fix] 생성된 캐시를 에이전트에 주입
        if cache_metadata_persisted and hasattr(self, "agents") and self.agents:
            if cache_info.get("writer_cache"):
                self.agents["writer"].cache_name = cache_info["writer_cache"]
                self.ui.log("   ✅ Writer 캐시 주입 완료")
            # [V65] Architect 캐시 주입 삭제
            if cache_info.get("analyst_cache"):
                self.agents["analyst"].cache_name = cache_info["analyst_cache"]
                self.ui.log("   ✅ Analyst 캐시 주입 완료")
            if cache_info.get("weaver_cache"):
                self.agents["weaver"].cache_name = cache_info["weaver_cache"]
                self.ui.log("   ✅ Weaver 캐시 주입 완료")

    def _is_cache_alive(self, cache_name):
        if not cache_name:
            return False
        try:
            self.sys.api_client.caches.get(name=cache_name)
            return True
        except Exception as e:  # API 예외 종류가 다양하므로 Exception 유지
            logging.debug(f"[SilentPass:CacheCheck] 캐시 헬스체크 실패: {e!s:.100}")
            return False

    def _check_vector_db_lock(self, project_name: str) -> bool:
        """[DB-MERGE] DB file integrity check (project_data.db)."""
        db_file = self._get_project_dir(project_name) / "project_data.db"
        if db_file.exists() and db_file.stat().st_size == 0:
            self.ui.log(f"🚨 [Critical] DB file ({db_file.name}) looks corrupted (0KB).")
            self.ui.log("💡 [Fix] Remove the file and rerun from Stage 0.")
            return False

        self.ui.log("✅ [System] Vector DB integrity check complete.")
        return True

    def _ui_select_bible(self) -> str | None:
        """[4B-2] Facade → UIService"""
        return self._ui_service.select_bible()

    def _ui_select_treatment(self) -> str | None:
        """[4B-2] Facade → UIService"""
        return self._ui_service.select_treatment()

    def _enrich_treatment_blocks(self, treatment_file: str) -> str:
        """
        [V60.10] Treatment Block 자동 농축

        정보량이 부족한 Block들을 Block 1 수준으로 자동 농축합니다.
        농축된 Treatment는 별도 파일로 저장되고 그 경로를 반환합니다.

        Args:
            treatment_file: 원본 Treatment 파일명

        Returns:
            농축된 Treatment 파일명 (또는 실패 시 원본 파일명)
        """
        from pathlib import Path

        self.ui.log("🔧 [V60.10] Treatment Block 농축 시작...")

        try:
            # 1. 원본 Treatment 로드
            treat_path = Path("treatments") / treatment_file
            with open(treat_path, encoding="utf-8") as f:
                treatment_blocks = json.load(f)

            if not treatment_blocks or len(treatment_blocks) < 2:
                self.ui.log("⚠️ Treatment 블록이 부족합니다.")
                return treatment_file

            # 2. BlockEnricher 초기화 (context, client, model_tier 순서로 전달)
            # [V60.24] Flash (농축용)
            from modules.domain.agents.block_enricher import BlockEnricher  # [INF-I8] lazy import

            enricher = BlockEnricher(self.current_project, self.sys.api_client, model_tier=_SUMMARY_MODEL)

            # 3. 각 Block 분석 및 농축 필요 여부 확인
            needs_enrichment = []
            for i, block in enumerate(treatment_blocks):
                analysis = enricher.analyze_block_density(block)
                if analysis["needs_enrichment"]:
                    needs_enrichment.append(
                        {
                            "index": i,
                            "block_id": block.get("block_id", f"Block {i + 1}"),
                            "density_score": analysis["density_score"],
                            "missing": analysis["missing_elements"],
                        }
                    )

            if not needs_enrichment:
                self.ui.log("✅ 모든 Block이 충분한 정보량을 가지고 있습니다.")
                return treatment_file

            self.ui.log(f"📊 농축 필요 Block: {len(needs_enrichment)}/{len(treatment_blocks)}개")
            for info in needs_enrichment[:5]:  # 최대 5개만 표시
                self.ui.log(f"   - {info['block_id']}: 밀도 {info['density_score']:.2f}, 부족 요소: {info['missing']}")
            if len(needs_enrichment) > 5:
                self.ui.log(f"   ... 외 {len(needs_enrichment) - 5}개")

            # 4. 사용자 확인
            proceed = input(f"   → {len(needs_enrichment)}개 Block을 농축하시겠습니까? (Y/n): ").strip().lower()
            if proceed == "n":
                self.ui.log("⏭️ 농축을 건너뜁니다.")
                return treatment_file

            # 5. 주인공 이름 추출 (Bible에서) [V61.2 Fix] 장르별 HUD 탐색
            # 6. 장르 확인
            genre = self.selected_genre.get("type", "wuxia") if self.selected_genre else "wuxia"

            protagonist_name = "주인공"
            try:
                bible_path = Path("bible")
                bible_files = list(bible_path.glob("*.json"))
                if bible_files:
                    with open(bible_files[0], encoding="utf-8") as f:
                        bible_data = json.load(f)
                    bible_root = bible_data.get("MasterBible", bible_data)
                    protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
            except (
                FileNotFoundError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
            ) as e:  # [V64.P4] IMPORTANT: protagonist name extraction
                self.ui.log(f"   ⚠️ [V64.P4] 주인공 이름 추출 실패: {str(e)[:60]}")

            # 7. [V60.10] 병렬 농축 + 인과 검증 수행
            self.ui.log("🔄 Block 병렬 농축 시작... (Block 1을 품질 기준으로 사용)")
            self.ui.log("   📋 Phase 1: 배치 병렬 농축 → Phase 2: 인과 검증 → Phase 3: 문제 Block 재농축")

            result = enricher.enrich_all_blocks_parallel(
                treatment_blocks=treatment_blocks,
                protagonist_name=protagonist_name,
                genre=genre,
                reference_block_index=0,
                batch_size=5,  # Rate Limit 회피용
                ui=self.ui,
            )

            enriched_blocks_raw = result.get("enriched_blocks", [])
            stats = result.get("statistics", {})
            causal_fixes = result.get("causal_issues_found", 0)

            # [V62.2] 결과 정리: 원본 필드 보존 + 농축 결과 머지 (genre_ext 등 유지)
            enriched_blocks = []
            for i, block in enumerate(enriched_blocks_raw):
                if block is None:
                    enriched_blocks.append(treatment_blocks[i])
                elif isinstance(block, dict):
                    clean_block = dict(treatment_blocks[i]) if i < len(treatment_blocks) else {}
                    clean_block["block_id"] = block.get("block_id", clean_block.get("block_id", f"Block {i + 1}"))
                    clean_block["title"] = block.get("title", clean_block.get("title", ""))
                    clean_block["content"] = block.get("content", clean_block.get("content", {}))
                    if "joint_docs" in block:
                        clean_block["joint_docs"] = block["joint_docs"]
                    if "status_shadow" in block:
                        clean_block["status_shadow"] = block["status_shadow"]
                    enriched_blocks.append(clean_block)
                else:
                    enriched_blocks.append(treatment_blocks[i])

            # 통계 출력
            self.ui.log(
                f"   📊 농축 완료: {stats.get('enriched_count', 0)}개 성공, "
                f"{stats.get('skipped_count', 0)}개 스킵, "
                f"{stats.get('failed_count', 0)}개 실패"
            )
            if causal_fixes > 0:
                self.ui.log(f"   🔧 인과 수정: {causal_fixes}개 Block 재농축됨")

            # 8. 농축된 Treatment 저장
            enriched_filename = treatment_file.replace(".json", "_enriched.json")
            enriched_path = Path("treatments") / enriched_filename

            with open(enriched_path, "w", encoding="utf-8") as f:
                json.dump(enriched_blocks, f, ensure_ascii=False, indent=2)

            self.ui.log(f"✅ 농축된 Treatment 저장 완료: {enriched_filename}")
            self.ui.log(f"   원본: {treatment_file} (보존)")
            self.ui.log(f"   농축본: {enriched_filename} (사용)")

            return enriched_filename

        except Exception as e:
            self.ui.log(f"🚨 [V60.10] 농축 실패: {e}")
            self._audit_event("block_enrichment_error", "treatment enrichment failed", {"error": str(e)[:200]})
            return treatment_file

    def _init_core_agents(self, _agents: dict, _v50: dict | None, models: dict, default_model: str) -> None:
        """[God-2] self.agents dict 구성 + arc_corrector/stage2_optimizer 초기화.

        Args:
            _agents: _lazy_load_agents() 반환값
            _v50: _lazy_load_v50_modules() 반환값 (None 허용)
            models: _get_agent_model_map() 반환값
            default_model: 기본 모델 tier 문자열
        """
        Analyst = _agents["Analyst"]
        ArcCorrector = _agents["ArcCorrector"]
        ArcCritic = _agents["ArcCritic"]
        ArcDraftValidator = _agents["ArcDraftValidator"]
        ArcEnsembleGenerator = _agents["ArcEnsembleGenerator"]
        ConsensusValidator = _agents["ConsensusValidator"]
        ConstraintCompiler = _agents["ConstraintCompiler"]
        ContinuityInspector = _agents["ContinuityInspector"]
        Critic = _agents["Critic"]
        Director = _agents["Director"]
        FourPhaseArcGenerator = _agents["FourPhaseArcGenerator"]
        Manager = _agents["Manager"]
        PreflightChecker = _agents["PreflightChecker"]
        StateExtractor = _agents["StateExtractor"]
        StateLockedArcGenerator = _agents["StateLockedArcGenerator"]
        ThreePhaseBlueprintGenerator = _agents["ThreePhaseBlueprintGenerator"]
        Weaver = _agents["Weaver"]
        Writer = _agents["Writer"]

        _flash_ask_cb = None
        if bool(_val_threshold("investment_math.flash_enabled", True)):
            try:
                _flash_client = self.sys.api_client

                def _flash_ask_cb(prompt: str, _c=_flash_client) -> str:
                    resp = generate_content_via_router(
                        client=_c,
                        model=AIModels.FLASH_ANALYSIS_MODEL,
                        contents=prompt,
                    )
                    return resp.text or ""
            except Exception as _flash_init_err:
                logging.warning("[Codex F] flash_ask 콜백 준비 실패: %s", str(_flash_init_err)[:120])
                _flash_ask_cb = None

        self.agents = {
            "analyst": Analyst(self.current_project, self.sys.api_client, model_tier=models.get("analyst", default_model)),
            # [V65] Architect 삭제 (ThreePhaseBlueprintGenerator로 완전 대체)
            "writer": Writer(self.current_project, self.sys.api_client, model_tier=models.get("writer", default_model)),
            "director": Director(
                self.current_project, self.sys.api_client, model_tier=models.get("director", default_model)
            ),
            "manager": Manager(self.current_project, self.sys.api_client, model_tier=models.get("manager", default_model)),
            # [V45 Fix] weaver는 manager가 아닌 weaver 모델 사용 (fallback: manager)
            "weaver": Weaver(
                self.current_project,
                self.sys.api_client,
                model_tier=models.get("weaver", models.get("manager", default_model)),
            ),
            # [V48.1] ContinuityInspector - Director 산하 연속성 검증 에이전트
            "continuity_inspector": ContinuityInspector(
                self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            # [V52.2] Critic - 원고 비평 에이전트
            # [V60.78] 2.5-flash로 변경 (2.0 이하 미사용 정책)
            "critic": Critic(self.current_project, self.sys.api_client, model_tier=_SUMMARY_MODEL),
            # [V60.10] StateExtractor - 상태 추출 에이전트 (빠른 모델로 구조화된 상태 추출)
            "state_extractor": StateExtractor(
                self.current_project, self.sys.api_client, model_tier=_FLASH_ANALYSIS_MODEL
            ),
            # [V60.11] ArcEnsembleGenerator - Arc 앙상블 생성기 (3개 후보 병렬 생성)
            "arc_ensemble": ArcEnsembleGenerator(
                self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            # [V60.12] FourPhaseArcGenerator - 4단계 Arc 생성 파이프라인 (초기 통과율 극대화)
            "four_phase": FourPhaseArcGenerator(
                self.current_project,
                self.sys.api_client,
                model_tier=AIModels.STAGE2_MAIN_MODEL,
                flash_ask=_flash_ask_cb,
            ),
            # [V60.14] StateLockedArcGenerator - 상태 잠금 Arc 생성기 (구조적 모순 불가)
            "state_locked": StateLockedArcGenerator(
                self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            # [V60.12] PreflightChecker - 생성 전 완벽 분석
            "preflight": PreflightChecker(
                self.current_project, self.sys.api_client, model_tier=_FLASH_ANALYSIS_MODEL
            ),
            # [V60.12] ArcCritic - Arc 즉시 비평
            "arc_critic": ArcCritic(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
            # [V60.12] ConsensusValidator - 3-LLM 합의 검증
            "consensus": ConsensusValidator(
                self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            # [V60.80] ThreePhaseBlueprintGenerator - 3단계 Blueprint 파이프라인
            "three_phase_bp": ThreePhaseBlueprintGenerator(
                self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
        }

        # [V60.11] Python 기반 헬퍼 초기화 (LLM 미사용)
        _genre_for_stage2 = self.selected_genre.get("type", "") if isinstance(self.selected_genre, dict) else ""
        self.arc_draft_validator = ArcDraftValidator(genre=_genre_for_stage2)
        self.constraint_compiler = ConstraintCompiler(genre=_genre_for_stage2)
        # [V60.42] Arc Corrector - MAJOR 이슈 부분 수정 (ON/OFF 토글 가능)
        self.arc_corrector = ArcCorrector(
            context=self.current_project,
            client=self.sys.api_client,
            model_tier=_FLASH_ANALYSIS_MODEL,  # [V65] 경량 모델 상수
        )
        self.use_arc_corrector = True  # [V60.42] 기본 활성화 (False로 설정하면 비활성화)
        # [V60.25] Stage 2 Optimizer - 통과율 최적화
        create_stage2_optimizer = _v50["create_stage2_optimizer"] if _v50 else None
        self.stage2_optimizer = create_stage2_optimizer() if create_stage2_optimizer else None
        self.ui.log("   🔧 [V60.11] Stage 2 고도화 모듈 초기화 (Ensemble + DraftValidator + ConstraintCompiler)")
        self.ui.log(
            "   🚀 [V60.12] Stage 2 초기통과율 극대화 모듈 초기화 (FourPhase + Preflight + Critic + Consensus)"
        )
        self.ui.log(
            f"   🔧 [V60.42] Arc Corrector 초기화 (MAJOR 이슈 부분 수정: {'활성화' if self.use_arc_corrector else '비활성화'})"
        )
        if self.stage2_optimizer:
            self.ui.log("   ⚡ [V60.25] Stage 2 Optimizer 활성화 (StateSnapshot + AutoCorrector + ConstraintAmplifier)")

    def _init_v50_modules(self, _v50: dict | None) -> list[str]:
        """[God-2] V50 서사 품질 향상 모듈 전체 초기화.

        Args:
            _v50: _lazy_load_v50_modules() 반환값 (None이면 기본 모드)
        """
        if V50_MODULES_AVAILABLE and _v50:
            try:
                genre_type = self.selected_genre.get("type", "wuxia") if self.selected_genre else "wuxia"

                # [V65] V50.1~V51.1 초기화 삭제 (Dead Code 정리)

                # [V65] V51.1 호흡 분석기 재연결
                self.pacing_analyzer = _v50["PacingAnalyzer"]()

                # V51.2 품질 증폭기
                self.quality_amplifier = _v50["QualityAmplifier"]()

                # V51.3 에이전트 지능 향상
                self.agent_intelligence = _v50["AgentIntelligence"](genre=genre_type)

                # V51.4 실패 학습 시스템
                self.failure_learner = _v50["FailureLearner"]()
                # [DB-Eff-P2] DB 우선 로드, 폴백: JSON 1회 마이그레이션
                _fl_loaded = False
                try:
                    _fl_row = self.current_project.db.conn.execute(
                        "SELECT description FROM reflexion_memory WHERE pattern_type = ?",
                        ("failure_learner_snapshot",),
                    ).fetchone()
                    if _fl_row and _fl_row[0]:
                        from collections import defaultdict as _defaultdict

                        from modules.core.failure_learning import (
                            FailureCategory as _FailureCategory,
                        )
                        from modules.core.failure_learning import (
                            FailureRecord as _FailureRecord,
                        )

                        _snapshot = json.loads(_fl_row[0])
                        self.failure_learner.records = []
                        self.failure_learner.category_counts = _defaultdict(int)
                        self.failure_learner.stage_counts = {
                            2: _defaultdict(int),
                            3: _defaultdict(int),
                            4: _defaultdict(int),
                        }
                        self.failure_learner.recent_failures = {2: [], 3: [], 4: []}

                        for _r in _snapshot.get("records", []):
                            try:
                                _category = _FailureCategory(_r.get("category", "unknown"))
                            except ValueError:
                                _category = _FailureCategory.UNKNOWN

                            _stage = int(_r.get("stage", 4))
                            _record = _FailureRecord(
                                category=_category,
                                stage=_stage,
                                episode=int(_r.get("episode", 0)),
                                arc=int(_r.get("arc", 0)),
                                reason=str(_r.get("reason", "")),
                                details=_r.get("details", {}),
                                timestamp=str(_r.get("timestamp", "")),
                            )
                            self.failure_learner.records.append(_record)
                            self.failure_learner.category_counts[_category] += 1
                            self.failure_learner.stage_counts.setdefault(_stage, _defaultdict(int))[_category] += 1
                            self.failure_learner.recent_failures.setdefault(_stage, []).append(_record)
                            if len(self.failure_learner.recent_failures[_stage]) > 10:
                                self.failure_learner.recent_failures[_stage].pop(0)
                        _fl_loaded = bool(self.failure_learner.records)
                except Exception as _fl_db_err:
                    logging.debug("[DB-Eff] failure_learner DB load 실패: %s", _fl_db_err)

                if _fl_loaded:
                    self.ui.log(f"   📚 [V51.4] 실패 기록 {len(self.failure_learner.records)}건 로드(DB)")
                else:
                    failure_log_path = self._get_current_project_log_path("failure_learning.json")
                    if failure_log_path.exists():
                        self.failure_learner.load_from_json(failure_log_path)
                        if self.failure_learner.records:
                            _snapshot = {
                                "records": [
                                    {
                                        "category": r.category.value,
                                        "stage": r.stage,
                                        "episode": r.episode,
                                        "arc": r.arc,
                                        "reason": r.reason,
                                        "details": r.details,
                                        "timestamp": r.timestamp,
                                    }
                                    for r in self.failure_learner.records
                                ],
                                "stats": self.failure_learner.get_failure_stats(),
                            }
                            _ts = time.strftime("%Y-%m-%d %H:%M:%S")
                            _first_ep = min((int(r.episode) for r in self.failure_learner.records), default=0)
                            _last_ep = max((int(r.episode) for r in self.failure_learner.records), default=0)
                            self.current_project.db.conn.execute(
                                """INSERT INTO reflexion_memory
                                   (pattern_type, description, frequency, solution, first_seen, last_seen, first_ep, last_ep)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ON CONFLICT(pattern_type) DO UPDATE SET
                                     description=excluded.description,
                                     frequency=excluded.frequency,
                                     solution=excluded.solution,
                                     last_seen=excluded.last_seen,
                                     first_ep=excluded.first_ep,
                                     last_ep=excluded.last_ep""",
                                (
                                    "failure_learner_snapshot",
                                    json.dumps(_snapshot, ensure_ascii=False),
                                    len(self.failure_learner.records),
                                    "failure_learner_json_migrated",
                                    _ts,
                                    _ts,
                                    _first_ep,
                                    _last_ep,
                                ),
                            )
                            self.current_project.db.conn.commit()
                            self.ui.log("   📚 [DB-Eff] failure_learning JSON→DB 마이그레이션 완료")

                # V51.5 캐릭터 음성 추적
                self.character_voice = _v50["CharacterVoiceTracker"]()
                # [DB-Eff-P1] DB 우선 로드, 폴백: 파일
                _cv_db_count = self.character_voice.load_from_db(self.current_project.db)
                if _cv_db_count == 0:
                    voice_log_path = self._get_current_project_log_path("character_voice.json")
                    if voice_log_path.exists():
                        self.character_voice.load_from_json(voice_log_path)
                        self.character_voice.save_to_db(self.current_project.db)
                        self.ui.log("   🎭 [DB-Eff] character_voice JSON→DB 마이그레이션 완료")
                else:
                    self.ui.log(f"   🎭 [V51.5] 캐릭터 음성 {len(self.character_voice.profiles)}명 로드(DB)")

                # V51.6 복선 추적
                self.foreshadow_tracker = _v50["ForeshadowTracker"]()
                # [DB-Eff-P1] DB 우선 로드, 폴백: 파일
                _ft_db_count = self.foreshadow_tracker.load_from_db(self.current_project.db)
                if _ft_db_count == 0:
                    foreshadow_log_path = self._get_current_project_log_path("foreshadow.json")
                    if foreshadow_log_path.exists():
                        self.foreshadow_tracker.load_from_json(foreshadow_log_path)
                        self.foreshadow_tracker.save_to_db(self.current_project.db)
                        self.ui.log("   🔮 [DB-Eff] foreshadow JSON→DB 마이그레이션 완료")
                else:
                    stats = self.foreshadow_tracker.get_stats()
                    self.ui.log(
                        f"   🔮 [V51.6] 복선 {stats['total']}개 로드(DB) "
                        f"(활성: {stats['active']}, 회수율: {stats['payoff_rate']}%)"
                    )

                # [V66] SemanticPlotGuard 활성화
                try:
                    from modules.core.semantic_plot_guard import SemanticPlotGuard

                    self.semantic_plot_guard = SemanticPlotGuard(api_key=os.getenv("GOOGLE_API_KEY", ""))
                    if self.semantic_plot_guard._client:
                        self.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료 (임베딩 모드)")
                    else:
                        self.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료 (키워드 폴백 모드)")
                except Exception as e:
                    self.ui.log(f"   ⚠️ [V66] SemanticPlotGuard 초기화 실패: {str(e)[:80]}")
                    self.semantic_plot_guard = None

                # ============================================================
                # [V60.26] 품질 향상 모듈 (미사용 → 활성화)
                # ============================================================

                # V60.26-1 감정선 추적
                self.emotion_tracker = _v50["EmotionArcTracker"](self.current_project)
                # [V70] JSON 파일이 아닌 DB anchor에서 직접 로드 (emotion_arc.json은 미생성)
                try:
                    self.emotion_tracker.load_from_db(self.current_project.db)
                    if self.emotion_tracker.history:
                        self.ui.log(f"   💓 [V60.26] 감정선 추적기 로드 ({len(self.emotion_tracker.history)}개 기록)")
                    else:
                        self.ui.log("   💓 [V60.26] 감정선 추적기 활성화")
                except Exception:  # [V70] DB 오류 시 비차단
                    self.ui.log("   💓 [V60.26] 감정선 추적기 활성화")

                # V60.26-2 파워 스케일링 추적
                self.power_scaling = _v50["PowerScalingTracker"]()
                self.ui.log("   ⚡ [V60.26] 파워 스케일링 추적기 활성화")

                # V60.26-3 상태 변화 추적
                self.state_delta_tracker = _v50["StateDeltaTracker"]()
                self.ui.log("   📊 [V60.26] 상태 변화 추적기 활성화")

                # V60.26-4 의미적 아이템 레지스트리
                self.semantic_item_registry = _v50["SemanticItemRegistry"]()
                self.ui.log("   📦 [V60.26] 의미적 아이템 레지스트리 활성화")

                # V60.26-5 캐릭터 음성 프로파일러 (V58, 기존 V51.5보다 고급)
                self.voice_profiler = _v50["CharacterVoiceProfiler"]()
                voice_profiler_path = self._get_current_project_log_path("voice_profiles.json")
                if voice_profiler_path.exists():
                    try:
                        with open(voice_profiler_path, encoding="utf-8") as f:
                            profiles_data = json.load(f)
                            for name_key, profile_data in profiles_data.items():
                                self.voice_profiler.add_profile(name_key, profile_data)
                        self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 로드 ({len(self.voice_profiler.profiles)}명)")
                    except (
                        json.JSONDecodeError,
                        KeyError,
                        TypeError,
                        OSError,
                    ) as e:  # [V64.P4] OPTIONAL: voice profiler load
                        self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 활성화 (로드 실패: {str(e)[:40]})")
                else:
                    self.ui.log("   🎭 [V60.26] 캐릭터 음성 프로파일러 활성화")

                # V52.1 자기 성찰 체인
                self.self_reflector = _v50["SelfReflector"](
                    api_client=self.sys.api_client,
                    model=_V50_MODULE_MODEL,  # [V65] 중앙 상수
                )
                self.ui.log("   🔄 [V52.1] Self-Reflection Chain 활성화")

                # V52.3 전문가 혼합
                self.expert_mixture = _v50["ExpertMixture"](genre=genre_type)
                self.ui.log(f"   🎯 [V52.3] Expert Mixture 활성화 ({genre_type})")

                # V52.4 교차 에이전트 검증
                self.cross_verifier = _v50["CrossAgentVerifier"](
                    api_client=self.sys.api_client,
                    model=_V50_MODULE_MODEL,  # [V65] 중앙 상수
                )
                self.ui.log("   🔗 [V52.4] Cross-Agent Verifier 활성화")

                # V53.1 동적 프롬프트 가중치
                self.prompt_weighter = _v50["DynamicPromptWeighter"](failure_learner=self.failure_learner)
                self.ui.log("   ⚖️ [V53.1] Dynamic Prompt Weighter 활성화")

                # V53.2 사실 검증 체인
                self.chain_of_verification = _v50["ChainOfVerification"](
                    api_client=self.sys.api_client,
                    model=_V50_MODULE_MODEL,  # [V65] 중앙 상수
                )
                self.ui.log("   🔍 [V53.2] Chain-of-Verification 활성화")

                # V53.3 신뢰도 보정
                self.confidence_calibrator = _v50["ConfidenceCalibrator"](
                    api_client=self.sys.api_client,
                    use_llm=False,  # Python 휴리스틱만 (비용 0)
                )
                self.ui.log("   📊 [V53.3] Confidence Calibrator 활성화")

                # V53.4 사전 체크리스트
                self.pre_director_checklist = _v50["PreDirectorChecklist"]()
                self.ui.log("   ✅ [V53.4] Pre-Director Checklist 활성화")

                # V53.5 Tree of Thoughts
                self.tree_of_thoughts = _v50["TreeOfThoughts"](
                    api_client=self.sys.api_client,
                    model=AIModels.STAGE2_MAIN_MODEL,  # [V65] 중앙 상수
                )
                self.ui.log("   🌳 [V53.5] Tree of Thoughts 활성화 (Gemini 3)")

                # V53.6 적대적 자기 대결
                self.adversarial_self_play = _v50["AdversarialSelfPlay"](
                    api_client=self.sys.api_client,
                    model=_V50_MODULE_MODEL,  # [V65] 중앙 상수
                )
                self.ui.log("   ⚔️ [V53.6] Adversarial Self-Play 활성화")

                # V53.7 다중 에이전트 토론
                self.multi_agent_deliberation = _v50["MultiAgentDeliberation"](
                    api_client=self.sys.api_client,
                    model=_V50_MODULE_MODEL,  # [V65] 중앙 상수
                )
                self.ui.log("   🗣️ [V53.7] Multi-Agent Deliberation 활성화")

                # ============================================================
                # [V54] 비용 절감 + 품질 향상 모듈
                # ============================================================

                # V54.3 적응형 재시도 관리자
                self.adaptive_manager = _v50["get_adaptive_manager"]()
                # [V54.3.1] FailureLearner 연동
                if self.failure_learner:
                    self.adaptive_manager.connect_failure_learner(self.failure_learner)
                    self.ui.log("   🔄 [V54.3] Adaptive Retry Manager 활성화 (FailureLearner 연동)")
                else:
                    self.ui.log("   🔄 [V54.3] Adaptive Retry Manager 활성화")

                # [V65] TwoPhaseGenerator 삭제 (two_phase_ms/bp/arc — Dead Code)

                # [Phase 4D-4] SuccessPatternMemory 삭제 (ChromaDB 레거시 제거)

                # V55.2 헌법적 자기검증
                self.constitutional_checker = _v50["ConstitutionalChecker"](genre=genre_type)
                self.ui.log("   📜 [V55.2] Constitutional Checker 활성화")

                # V55.3 원고 템플릿
                self.writer_template = _v50["WriterTemplate"](genre=genre_type)
                self.ui.log("   📝 [V55.3] Writer Template 활성화")

                # V55.3 통과율 모니터
                project_path = str(self.current_project.paths.root) if self.current_project else "."
                self.pass_rate_monitor = _v50["PassRateMonitor"](project_path)
                self.ui.log("   📊 [V55.3] Pass Rate Monitor 활성화")

                # V60 품질 대시보드
                self.quality_dashboard = _v50["QualityDashboard"](Path(project_path))
                self.ui.log("   📊 [V60] Quality Dashboard 활성화")

                # [SC] Smart Context Retrieval
                self.context_advisor = _v50["ContextAdvisor"]()
                self.ui.log("   🧭 [SC] Context Advisor 활성화")

                self.ui.log(f"   📊 [V50~V60] 서사 품질 모듈 초기화 완료 (장르: {genre_type})")

                # 기존 에피소드에서 데이터 로드
                self._load_v50_history()
                return []

            except Exception as v50_err:
                self.ui.log(f"   ⚠️ [V50] 모듈 초기화 실패 (비치명적): {v50_err}")
                return [f"v50_init_failed:{type(v50_err).__name__}:{v50_err}"]
        else:
            self.ui.log("   ⚠️ [V50] 모듈 미설치 - 기본 모드")
            return []

    def _load_bootstrap_components(self) -> tuple[dict, dict | None]:
        """Load lazy bootstrap components and synchronize spinner flags."""
        global V50_MODULES_AVAILABLE, STAGE0_AVAILABLE

        _agents = _lazy_load_agents()
        _v50 = _lazy_load_v50_modules()
        _lazy_load_stage0()

        _spinners_mod.V50_MODULES_AVAILABLE = V50_MODULES_AVAILABLE
        _spinners_mod.STAGE0_AVAILABLE = STAGE0_AVAILABLE
        return _agents, _v50

    def _resolve_project_guard(self):
        """Return the current guard, optionally wrapped with StyleGuard metadata."""
        guard = getattr(self.sys, "guard", None)
        if not guard:
            return None

        try:
            _sg_data = self.current_project.load_v20_anchor("style_guide")
            if _sg_data and isinstance(_sg_data, dict):
                from modules.core.genre_guards import StyleGuard
                from modules.core.stage0 import StyleGuide

                _sg = StyleGuide.from_dict(_sg_data)
                guard = StyleGuard(guard, _sg)
                self.ui.log("   🎨 StyleGuard 래핑 완료 (문체 기반 검증 활성)")
        except Exception as e:
            logging.warning(f"[D-3] StyleGuard 래핑 실패 (장르 Guard만 사용): {e}")

        return guard

    def _apply_genre_bindings(self) -> None:
        """Bind genre and guard state onto the active director/writer agents."""
        if not self.selected_genre:
            return

        genre_type = self.selected_genre.get("type", "wuxia")
        director = self.agents["director"]
        director.set_genre(genre_type)
        self.ui.log(f"   🎭 Director 장르 설정: {genre_type}")

        guard = self._resolve_project_guard()
        if guard is not None:
            director.set_guard(guard)
            self.ui.log("   🛡️ Director Guard 연결 완료")

            writer = self.agents.get("writer")
            if writer and hasattr(writer, "set_guard"):
                writer.set_guard(guard)

        writer = self.agents.get("writer")
        if writer:
            if hasattr(writer, "set_genre"):
                writer.set_genre(genre_type)
            self.ui.log("   ✍️ Writer Guard/Genre 연결 완료")

    def _load_validation_settings(self) -> dict:
        """Load runtime validation settings from project config or root fallback."""
        try:
            settings_path = self.current_project.paths.config / "settings.json"
            if not settings_path.exists():
                settings_path = Path("config/settings.json")

            if settings_path.exists():
                with open(settings_path, encoding="utf-8") as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

        return {}

    def _apply_validation_settings(self, settings: dict) -> None:
        """Apply validation feature toggles onto initialized agents."""
        validation_config = settings.get("validation", {})
        if validation_config.get("use_v0128", False):
            self.agents["director"].set_v0128_enabled(True)
            self.ui.log("   ✅ V0128 검증 시스템 활성화")

    def _bootstrap_continuity_inspector(self) -> None:
        """Load continuity tracker state when the inspector supports it."""
        try:
            ci = self.agents.get("continuity_inspector")
            if ci and hasattr(ci, "v49_7_enabled") and ci.v49_7_enabled:
                arcs_data = self.current_project.db.load_anchor("arcs") or []
                if arcs_data:
                    load_result = ci.load_trackers_from_db(arcs_data)
                    self.ui.log(
                        f"   🔩 [V49.7] 트래커 초기화 완료: "
                        f"복선 {load_result.get('foreshadowings', 0)}개 "
                        f"관계 {load_result.get('relationships', 0)}개 "
                        f"파워 {load_result.get('power_entries', 0)}개"
                    )
                else:
                    self.ui.log("   🔩 [V49.7] 트래커 대기 (Arc 데이터 없음)")
            else:
                self.ui.log("   ⏭️ [V49.7] 모듈 미설치 - 기본 검증 모드")
        except Exception as tracker_err:
            self.ui.log(f"   ⏭️ [V49.7] 트래커 초기화 실패 (비치명적): {tracker_err}")

    def _validate_initialized_agents(self) -> BootstrapStatus | None:
        """Ensure every initialized agent exposes the required ask contract."""
        for name, agent in self.agents.items():
            if not hasattr(agent, "ask"):
                self.ui.log(f"🚨 [Critical] {name} 에이전트 초기화 실패")
                self._bootstrap_status = BootstrapStatus(
                    core_ok=False,
                    v50_ok=False,
                    partial_failures=[f"agent_missing_ask:{name}"],
                )
                return self._bootstrap_status

        return None

    def _finalize_bootstrap_status(self, partial_failures: list[str]) -> BootstrapStatus:
        """Persist the final bootstrap result and emit the closing operator logs."""
        self._bootstrap_status = BootstrapStatus(
            core_ok=True,
            v50_ok=not partial_failures,
            partial_failures=partial_failures,
        )
        if partial_failures:
            self.ui.log(f"   ⚠️ [Bootstrap] optional module partial failure {len(partial_failures)}건")

        self.ui.log("✅ [System] 모든 에이전트 안전하게 초기화 완료")
        return self._bootstrap_status

    def _attach_agents(self) -> BootstrapStatus:
        """
        [V38 패치] 방어적 에이전트 초기화
        [INF-I8] lazy import 적용 — 에이전트/V50 모듈을 이 시점에서만 import

        시스템에 필요한 모든 AI 에이전트(Analyst, Architect, Writer, Director,
        Manager, Weaver)를 초기화합니다.

        Returns:
            BootstrapStatus: core/v50/partial failure 상태
        """
        try:
            _agents, _v50 = self._load_bootstrap_components()

            models = self._get_agent_model_map()

            if not models:
                self.ui.log("🚨 [Critical] 모델 설정을 불러올 수 없습니다.")
                self._bootstrap_status = BootstrapStatus(
                    core_ok=False,
                    v50_ok=False,
                    partial_failures=["missing_model_map"],
                )
                return self._bootstrap_status

            default_model = AIModels.STAGE2_MAIN_MODEL  # [V65] 중앙 상수 참조
            self._init_core_agents(_agents=_agents, _v50=_v50, models=models, default_model=default_model)

            invalid_status = self._validate_initialized_agents()
            if invalid_status:
                return invalid_status

            self._apply_genre_bindings()
            self._apply_validation_settings(self._load_validation_settings())
            self._bootstrap_continuity_inspector()

            # ═══════════════════════════════════════════════════════════════
            # [V50] 서사 품질 향상 모듈 초기화
            # ═══════════════════════════════════════════════════════════════
            partial_failures = self._init_v50_modules(_v50=_v50)

            return self._finalize_bootstrap_status(partial_failures)

        except Exception as e:
            self.ui.log(f"🚨 [Critical] 에이전트 초기화 중 오류: {e}")
            self._bootstrap_status = BootstrapStatus(
                core_ok=False,
                v50_ok=False,
                partial_failures=[f"critical_attach_error:{type(e).__name__}:{e}"],
            )
            import traceback

            traceback.print_exc()
            return self._bootstrap_status

    def _load_v50_history(self) -> None:
        """
        [V50] 기존 에피소드 데이터를 V50 모듈에 로드 (현재 비활성)

        [V65] V50.1~V51.1 모듈 삭제로 히스토리 로딩 로직 제거.
        모듈 파일(tension_curve.py 등)은 보존되어 재연결 시 복원 가능.
        """
        if not V50_MODULES_AVAILABLE:
            return

        # [V65] V50.1~V51.1 히스토리 로딩 삭제 (Dead Code 정리)
        # tension_manager, dialogue_engine, subplot_weaver, reader_simulator, pacing_analyzer
        # 모듈 파일은 보존되어 있으므로 재연결 시 이 메서드에 로딩 로직 복원 가능
        pass

    def _get_protagonist_name(self) -> str:
        """
        주인공 이름 추출 (bible에서)

        [V61.2 Fix] 장르별 HUD 탐색으로 변경 (MartialHUD 하드코딩 제거)
        HUDKeys.get_protagonist_name()이 모든 HUD 후보를 순회하고
        AssetLibrary.KeyNPCs 폴백까지 처리함
        """
        try:
            genre = self.selected_genre.get("type", "") if self.selected_genre else ""

            def _extract_name(bible_payload: Any) -> str | None:
                if not isinstance(bible_payload, dict):
                    return None
                bible_root = bible_payload.get("MasterBible", bible_payload)
                name = HUDKeys.get_protagonist_name(bible_root, genre)
                if name and name != "주인공":
                    return name

                chars = bible_root.get("characters", bible_root.get("등장인물", []))
                if chars and isinstance(chars, list):
                    first_char = chars[0]
                    if isinstance(first_char, dict):
                        return first_char.get("name") or first_char.get("이름")
                    if first_char:
                        return str(first_char)
                return None

            live_bible = getattr(self.current_project, "master_bible", None) if self.current_project else None
            name = _extract_name(live_bible)
            if name:
                return name

            db = getattr(getattr(self.current_project, "db", None), "load_anchor", None)
            if callable(db):
                name = _extract_name(db("bible") or {})
                if name:
                    return name

            return "주인공"
        except Exception as e:
            if getattr(self, "ui", None):
                self.ui.log(
                    f"      ⚠️ [V61.2] 주인공 이름 추출 실패: {e}",
                    stage="runtime",
                    component="protagonist_lookup",
                    level="warning",
                    event_kind="warning",
                )
            else:
                logging.warning("[V61.2] 주인공 이름 추출 실패: %s", e)
            return "주인공"

    def _fix_entity_registry_protagonist(self, entity_registry: dict, protagonist_name: str = None) -> dict:
        """
        [V62.4] Entity Registry에서 주인공 이름을 락된 이름으로 보정

        StateExtractor LLM이 주인공 이름을 잘못 추출하거나,
        '주인공 제외' 지시에도 불구하고 빠뜨리는 경우 방지.
        주인공이 Registry에 없으면 Director가 비슷한 NPC 이름과 혼동하여 오탐 REJECT 발생.
        """
        if not entity_registry or not protagonist_name or protagonist_name == "주인공":
            return entity_registry

        chars = entity_registry.get("characters")
        if not isinstance(chars, list):
            chars = []
            entity_registry["characters"] = chars

        protagonist_row = None
        for ch in chars:
            if isinstance(ch, dict) and ch.get("name") == protagonist_name:
                protagonist_row = ch
                break

        if protagonist_row is None:
            for ch in chars:
                if isinstance(ch, dict) and ch.get("role") in ("주인공", "protagonist", "주역"):
                    protagonist_row = ch
                    break

        if protagonist_row is None:
            chars.insert(0, {"name": protagonist_name, "role": "주인공", "context": "락 고정"})
            entity_registry["characters"] = chars
            return entity_registry

        old_name = protagonist_row.get("name", "?")
        if old_name != protagonist_name:
            protagonist_row["name"] = protagonist_name
            if getattr(self, "ui", None):
                self.ui.log(
                    f"      🔒 [V62.4] Entity Registry 주인공 보정: {old_name} → {protagonist_name}",
                    stage="runtime",
                    component="entity_registry",
                    event_kind="result",
                    meta={"old_name": old_name, "new_name": protagonist_name},
                )
            else:
                logging.info("[V62.4] Entity Registry 주인공 보정: %s -> %s", old_name, protagonist_name)
        if protagonist_row.get("role") not in ("주인공", "protagonist", "주역"):
            protagonist_row["role"] = "주인공"
        protagonist_row.setdefault("context", "락 고정")

        return entity_registry

    # [V65] _process_v50_post_episode 삭제 — Stage 4 V2 파이프라인에서 미호출 Dead Code
    # [V65] _generate_v50_writer_prompt 삭제 — Stage 4 V2 파이프라인에서 미호출 Dead Code

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
                genre_label = self.selected_genre["name"]
                self.ui.title(
                    "V40 SOVEREIGN PRODUCTION", f"Genre: {genre_label} | Project: {self.current_project.name}"
                )

                # 2. 상태 체크 (DB Anchors 기반의 무결성 확인)
                # 이 함수는 self.current_project.db의 'bible', 'volumes', 'arcs' 키를 체크해야 함
                status = self.sys.check_v20_readiness()

                # 3. 메뉴 구성 (V41 유동 아크 + 스킵 옵션)
                vol_status = "✅" if status.get("Stage 1 (Volumes)", False) else "⏭️ 스킵가능"
                menu = {
                    "0": f"Stage 0: Bible/역설계/스타일 추출 [{'✅' if status.get('Stage 0 (Bible)', False) else '❌'}]",
                    "1": f"Stage 1: Volume Strategy (선택) [{vol_status}]",
                    "2": f"Stage 2: Arc Tactical Design (유동) [{'✅' if status.get('Stage 2 (Arcs)', False) else '❌'}]",
                    "3": "📐 Stage 3: Episode Blueprinting (Batch Design)",  # 분리됨
                    "4": "🚀 Stage 4: Sovereign Production (Writing)",  # 분리됨
                    "5": "Exit",
                    "6": "🔄 One-Stop: Arc-by-Arc 자동 파이프라인",
                    "7": "🧭 One-Stop: Frontier Lag (S3=-1 / S4=-2)",
                    "44": "⏪ [ROLLBACK] Stage 4 회차별 롤백 (Episode Rewind)",
                    "77": "🧹 [WIPE] 원고 생산 기록만 삭제 (Stage 4 초기화)",
                    "88": "🔥 [RESET] Stage 2 (Arcs) 초기화",
                    "99": "⏪ Stage 2 정밀 되감기 (Selective Rewind)",
                }

                choice = self.ui.menu(menu)
                # 4. 공정 디스패치
                if choice == "0":
                    self._phase_0_recovery()
                elif choice == "1":
                    self._stage_1_volumes()
                elif choice == "2":
                    if not status.get("Stage 1 (Volumes)", False):
                        self.ui.log("⚠️ Stage 1 (Volume Strategy)이 완료되지 않았습니다.")
                        self.ui.log("💡 Volume 전략 없이도 Arc 설계를 진행할 수 있습니다.")
                        skip_confirm = input("   Stage 1을 건너뛰고 진행하시겠습니까? (y/N): ").strip().lower()
                        if skip_confirm != "y":
                            continue
                    self._stage_2_arcs()
                elif choice == "3":
                    # 📐 [Stage 3] 설계도만 일괄 생성 (Architect 전용)
                    self._stage_3_batch_blueprinting()
                elif choice == "4":
                    # [V60.95] Stage 4 - Chief Writer 단일화 (V1 레거시 제거)
                    self._stage_4_v2_chief_writer(limit_mode=True)
                elif choice == "5":
                    self._shutdown_app()
                    break
                elif choice == "6":
                    self._one_stop_pipeline()
                elif choice == "7":
                    self._one_stop_pipeline_frontier_lag()
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

            if self.current_project and hasattr(self.current_project, "paths"):
                error_log = self.current_project.paths.root / "logs" / "error.log"
            else:
                error_log = Path("logs") / "error.log"
            error_log.parent.mkdir(exist_ok=True)

            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 50}\n")
                f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(traceback.format_exc())

            self.ui.log(f"📝 에러 로그 저장: {error_log}")

            # 안전한 종료 시도
            try:
                self._shutdown_app()
            except Exception as e:  # 종료 시 모든 예외 무시
                logging.warning(f"[SilentPass:Shutdown] 앱 종료 중 예외: {e!s:.100}")

            sys.exit(1)

    # SovereignApp 클래스 내부에 추가할 메서드
    # [수정] main_a.py / SovereignApp 클래스 내부 메서드

    def _shutdown_log(self, message: str, **context) -> None:
        context.setdefault("stage", "shutdown")
        context.setdefault("component", "shutdown")
        ui = getattr(self, "ui", None)
        log_fn = getattr(ui, "log", None)
        if callable(log_fn):
            log_fn(message, **context)
            return

        text = message if message.endswith("\n") else f"{message}\n"
        sys.stdout.write(text)
        sys.stdout.flush()

    def _persist_shutdown_metrics(self) -> None:
        def _process_metrics():
            collector = get_metrics_collector()
            if not collector:
                return None, None
            report = collector.get_summary_report()
            saved_path = collector.save_metrics()
            return report, saved_path

        try:
            import concurrent.futures

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(_process_metrics)
                try:
                    report, saved_path = future.result(timeout=5)
                    if report:
                        SovereignApp._shutdown_log(
                            self,
                            "\n" + report,
                            component="metrics",
                            event_kind="summary",
                        )
                    if saved_path:
                        SovereignApp._shutdown_log(
                            self,
                            f"📊 [Metrics] 세션 메트릭 저장: {saved_path}",
                            component="metrics",
                            event_kind="result",
                            artifact_path=str(saved_path),
                        )
                except concurrent.futures.TimeoutError:
                    SovereignApp._shutdown_log(
                        self,
                        "⚠️ [Metrics] 메트릭 처리 타임아웃 (건너뜀)",
                        component="metrics",
                        level="warning",
                        event_kind="warning",
                    )
            finally:
                executor.shutdown(wait=False)
        except Exception as metrics_err:
            SovereignApp._shutdown_log(
                self,
                f"⚠️ [Metrics] 비용 추적 리포트 생성 실패: {metrics_err}",
                component="metrics",
                level="warning",
                event_kind="warning",
            )

    def _persist_shutdown_cost_scope(self) -> None:
        try:
            collector = get_metrics_collector()
            current_project = getattr(self, "current_project", None)
            db = getattr(current_project, "db", None)
            if collector and db is not None and hasattr(db, "save_cost_record"):
                scope = collector.snapshot_and_reset_scope()
                if (
                    scope.get("total_calls", 0) > 0
                    or scope.get("total_tokens", 0) > 0
                    or scope.get("total_cost_usd", 0.0) > 0
                ):
                    db.save_cost_record(
                        session_id=collector.session_id,
                        scope_type="session",
                        scope_id=0,
                        total_calls=scope.get("total_calls", 0),
                        total_tokens=scope.get("total_tokens", 0),
                        total_cost_usd=scope.get("total_cost_usd", 0.0),
                        model_breakdown=scope.get("model_breakdown", "{}"),
                    )
                    SovereignApp._shutdown_log(
                        self,
                        f"💾 [CostDB] Session 비용 저장: ${scope.get('total_cost_usd', 0.0):.4f} "
                        f"({scope.get('total_tokens', 0):,} tokens)",
                        component="cost_db",
                        event_kind="result",
                        meta={
                            "total_cost_usd": scope.get("total_cost_usd", 0.0),
                            "total_tokens": scope.get("total_tokens", 0),
                            "total_calls": scope.get("total_calls", 0),
                        },
                    )
        except Exception as cost_err:
            SovereignApp._shutdown_log(
                self,
                f"⚠️ [CostDB] Session 비용 저장 실패: {cost_err}",
                component="cost_db",
                level="warning",
                event_kind="warning",
            )

    def _save_pass_rate_monitor_for_audit_summary(self) -> None:
        if not (V50_MODULES_AVAILABLE and getattr(self, "pass_rate_monitor", None)):
            return
        try:
            self.pass_rate_monitor.save()
        except Exception as pr_err:
            logging.debug("[Audit] pass_rate_monitor save before summary failed: %s", pr_err)

    def _persist_shutdown_advisory_state(self) -> None:
        if V50_MODULES_AVAILABLE and getattr(self, "pass_rate_monitor", None):
            try:
                self.pass_rate_monitor.save()
                record_count = len(getattr(self.pass_rate_monitor, "records", []))
                SovereignApp._shutdown_log(
                    self,
                    f"📈 [PassRate] 통과율 기록 저장: {record_count}건",
                    component="pass_rate",
                    event_kind="result",
                    meta={"record_count": record_count},
                )
            except Exception as pr_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [PassRate] 저장 실패: {pr_err}",
                    component="pass_rate",
                    level="warning",
                    event_kind="warning",
                )

        current_project = getattr(self, "current_project", None)
        db = getattr(current_project, "db", None)
        if (
            V50_MODULES_AVAILABLE
            and getattr(self, "quality_dashboard", None)
            and db is not None
            and hasattr(db, "get_selection_analysis")
        ):
            try:
                selections = db.get_selection_analysis(lookback=100)
                if selections:
                    bias_result = self.quality_dashboard.detect_director_bias(selections)
                    warnings = bias_result.get("bias_warnings", [])
                    if warnings:
                        SovereignApp._shutdown_log(
                            self,
                            "⚖️ [Director Bias] 편향 경고:",
                            component="director_bias",
                            level="warning",
                            event_kind="warning",
                            meta={"warning_count": len(warnings)},
                        )
                        for warning in warnings[:5]:
                            SovereignApp._shutdown_log(
                                self,
                                f"   - {warning}",
                                component="director_bias",
                                level="warning",
                                event_kind="warning",
                            )
                    else:
                        SovereignApp._shutdown_log(
                            self,
                            "⚖️ [Director Bias] 유의미한 편향 경고 없음",
                            component="director_bias",
                            event_kind="result",
                        )
            except Exception as bias_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [Director Bias] 분석 실패: {bias_err}",
                    component="director_bias",
                    level="warning",
                    event_kind="warning",
                )

        if V50_MODULES_AVAILABLE and getattr(self, "quality_dashboard", None):
            try:
                drift = self.quality_dashboard.detect_quality_drift(stage=4, min_windows=3, window_size=10)
                drift_status = drift.get("drift", "insufficient_data")
                if drift_status == "declining":
                    SovereignApp._shutdown_log(
                        self,
                        f"📉 [Quality Drift] Stage 4 품질 하락 감지: "
                        f"최근 평균 {drift.get('recent_avg', 0)}점, 전체 평균 {drift.get('overall_avg', 0)}점",
                        component="quality_drift",
                        level="warning",
                        event_kind="warning",
                        meta={"drift_status": drift_status},
                    )
                elif drift_status == "improving":
                    SovereignApp._shutdown_log(
                        self,
                        f"📈 [Quality Drift] Stage 4 품질 상승 추세: 최근 평균 {drift.get('recent_avg', 0)}점",
                        component="quality_drift",
                        event_kind="result",
                        meta={"drift_status": drift_status},
                    )
                elif drift_status == "stable":
                    SovereignApp._shutdown_log(
                        self,
                        f"➡️ [Quality Drift] Stage 4 품질 안정: 평균 {drift.get('overall_avg', 0)}점",
                        component="quality_drift",
                        event_kind="result",
                        meta={"drift_status": drift_status},
                    )
            except Exception as drift_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [Quality Drift] 분석 실패: {drift_err}",
                    component="quality_drift",
                    level="warning",
                    event_kind="warning",
                )

    def _persist_shutdown_trackers(self) -> None:
        current_project = getattr(self, "current_project", None)
        db = getattr(current_project, "db", None)

        if V50_MODULES_AVAILABLE and getattr(self, "failure_learner", None) and current_project:
            try:
                snapshot = {
                    "records": [
                        {
                            "category": r.category.value,
                            "stage": r.stage,
                            "episode": r.episode,
                            "arc": r.arc,
                            "reason": r.reason,
                            "details": r.details,
                            "timestamp": r.timestamp,
                        }
                        for r in self.failure_learner.records
                    ],
                    "stats": self.failure_learner.get_failure_stats(),
                }
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                first_ep = min((int(r.episode) for r in self.failure_learner.records), default=0)
                last_ep = max((int(r.episode) for r in self.failure_learner.records), default=0)
                db.conn.execute(
                    """INSERT INTO reflexion_memory
                       (pattern_type, description, frequency, solution, first_seen, last_seen, first_ep, last_ep)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(pattern_type) DO UPDATE SET
                         description=excluded.description,
                         frequency=excluded.frequency,
                         solution=excluded.solution,
                         last_seen=excluded.last_seen,
                         first_ep=excluded.first_ep,
                         last_ep=excluded.last_ep""",
                    (
                        "failure_learner_snapshot",
                        json.dumps(snapshot, ensure_ascii=False),
                        len(self.failure_learner.records),
                        "failure_learner_snapshot",
                        ts,
                        ts,
                        first_ep,
                        last_ep,
                    ),
                )
                db.conn.commit()
                stats = self.failure_learner.get_failure_stats()
                SovereignApp._shutdown_log(
                    self,
                    f"📚 [V51.4] 실패 학습 기록 저장(DB): {stats['total_failures']}건",
                    component="failure_learner",
                    event_kind="result",
                    meta={"total_failures": stats["total_failures"]},
                )
            except Exception as fl_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [V51.4] 실패 기록 저장 실패: {fl_err}",
                    component="failure_learner",
                    level="warning",
                    event_kind="warning",
                )

        if V50_MODULES_AVAILABLE and getattr(self, "character_voice", None) and current_project:
            try:
                self.character_voice.save_to_db(db)
                SovereignApp._shutdown_log(
                    self,
                    f"🎭 [V51.5] 캐릭터 음성 저장: {len(self.character_voice.profiles)}명",
                    component="character_voice",
                    event_kind="result",
                    meta={"profile_count": len(self.character_voice.profiles)},
                )
            except Exception as cv_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [V51.5] 캐릭터 음성 저장 실패: {cv_err}",
                    component="character_voice",
                    level="warning",
                    event_kind="warning",
                )

        if V50_MODULES_AVAILABLE and getattr(self, "foreshadow_tracker", None) and current_project:
            try:
                self.foreshadow_tracker.save_to_db(db)
                stats = self.foreshadow_tracker.get_stats()
                SovereignApp._shutdown_log(
                    self,
                    f"🔮 [V51.6] 복선 저장: {stats['total']}개 (회수율: {stats['payoff_rate']}%)",
                    component="foreshadow",
                    event_kind="result",
                    meta={"total": stats["total"], "payoff_rate": stats["payoff_rate"]},
                )
            except Exception as fs_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [V51.6] 복선 저장 실패: {fs_err}",
                    component="foreshadow",
                    level="warning",
                    event_kind="warning",
                )

        if V50_MODULES_AVAILABLE and getattr(self, "emotion_tracker", None) and current_project:
            try:
                if db is not None:
                    self.emotion_tracker.save_to_db(db)
                    SovereignApp._shutdown_log(
                        self,
                        f"💓 [V60.26] 감정선 기록 저장: {len(self.emotion_tracker.history)}건",
                        component="emotion_tracker",
                        event_kind="result",
                        meta={"history_count": len(self.emotion_tracker.history)},
                    )
            except Exception as et_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [V60.26] 감정선 저장 실패: {et_err}",
                    component="emotion_tracker",
                    level="warning",
                    event_kind="warning",
                )

    def _persist_shutdown_project_state(self) -> None:
        current_project = getattr(self, "current_project", None)
        db = getattr(current_project, "db", None)

        if hasattr(current_project, "master_bible"):
            try:
                current_project.save_v20_anchor("bible", current_project.master_bible)
            except Exception as bible_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [Shutdown] Bible 저장 실패: {bible_err}",
                    component="bible",
                    level="warning",
                    event_kind="warning",
                )

        if self.selected_genre and db is not None:
            try:
                db.save_anchor("genre_info", self.selected_genre)
            except Exception as genre_err:
                SovereignApp._shutdown_log(
                    self,
                    f"⚠️ [Shutdown] genre_info 저장 실패: {genre_err}",
                    component="genre_info",
                    level="warning",
                    event_kind="warning",
                )

        if getattr(self, "semantic_item_registry", None) and self.selected_genre:
            try:
                from modules.core.failure_analyzer import FailureAnalyzer

                genre_type = self.selected_genre.get("type", "") if isinstance(self.selected_genre, dict) else ""
                analyzer = FailureAnalyzer(db=db if db is not None else None)
                llm_ask = None
                if hasattr(self, "sys") and hasattr(self.sys, "api_client"):
                    client = self.sys.api_client

                    def llm_ask(prompt, _c=client):
                        from modules.core.constants import AIModels

                        resp = generate_content_via_router(
                            client=_c,
                            model=AIModels.FLASH_ANALYSIS_MODEL,
                            contents=prompt,
                        )
                        return resp.text or ""

                result = analyzer.review_and_apply_suffixes(
                    self.semantic_item_registry, genre=genre_type, llm_ask=llm_ask
                )
                if result["approved"]:
                    SovereignApp._shutdown_log(
                        self,
                        f"🔧 [ItemGap] 접미사 자동 추가: {result['approved']} "
                        f"(심사 {result['reviewed']}건, 거절 {len(result['rejected'])}건)",
                        component="item_gap",
                        event_kind="result",
                        meta={
                            "approved": result["approved"],
                            "reviewed": result["reviewed"],
                            "rejected_count": len(result["rejected"]),
                        },
                    )
                elif result["reviewed"] > 0:
                    SovereignApp._shutdown_log(
                        self,
                        f"🔧 [ItemGap] 심사 {result['reviewed']}건 — 추가 없음",
                        component="item_gap",
                        event_kind="result",
                        meta={"approved": 0, "reviewed": result["reviewed"]},
                    )
            except Exception as gap_err:
                logging.debug("[ItemGap] 접미사 자동 확장 실패: %s", gap_err)

    def _close_shutdown_resources(self) -> None:
        if getattr(self, "memory", None):
            try:
                self.memory.close()
                self.ui.log("[System] VecMemory 연결 해제 완료")
            except Exception as mem_err:
                SovereignApp._shutdown_log(
                    self,
                    f"VecMemory close 오류: {mem_err}",
                    component="vec_memory",
                    level="warning",
                    event_kind="warning",
                )

        current_project = getattr(self, "current_project", None)
        db = getattr(current_project, "db", None)
        db_conn = getattr(db, "conn", None)
        if db_conn:
            try:
                if hasattr(db, "resolve_pending_transaction"):
                    db.resolve_pending_transaction(commit=True)
                else:
                    db_conn.commit()
                self.ui.log("[System] DB 커밋 완료")
            except Exception as commit_err:
                SovereignApp._shutdown_log(
                    self,
                    f"종료 중 DB 커밋 오류: {commit_err}",
                    component="database",
                    level="warning",
                    event_kind="warning",
                )
            finally:
                try:
                    if hasattr(db, "close"):
                        db.close()
                    else:
                        db_conn.close()
                    self.ui.log("[System] DB 연결 안전하게 해제됨")
                except Exception as close_err:
                    SovereignApp._shutdown_log(
                        self,
                        f"DB close 오류: {close_err}",
                        component="database",
                        level="warning",
                        event_kind="warning",
                    )

    def _shutdown_app(self):
        """[V27 Safe Shutdown] 앱 종료 시에만 DB 연결을 완전히 해제"""
        SovereignApp._shutdown_log(self, "\n🛑 [System] 시스템 종료 시퀀스 가동...", event_kind="progress")
        sys.stdout.flush()
        SovereignApp._persist_shutdown_metrics(self)
        SovereignApp._persist_shutdown_cost_scope(self)
        SovereignApp._persist_shutdown_advisory_state(self)
        SovereignApp._persist_shutdown_trackers(self)
        SovereignApp._persist_shutdown_project_state(self)
        session_logger = getattr(self, "_session_logger", None)
        if session_logger is not None and hasattr(session_logger, "begin_shutdown"):
            session_logger.begin_shutdown()
        current_project = getattr(self, "current_project", None)
        db = getattr(current_project, "db", None)
        if db is not None and hasattr(db, "begin_shutdown"):
            db.begin_shutdown()
        if hasattr(self, "_write_audit_summary"):
            self._write_audit_summary("shutdown_final")
        SovereignApp._close_shutdown_resources(self)
        SovereignApp._shutdown_log(self, "✅ [System] 종료 완료", event_kind="result")

    def _phase_0_recovery(self):
        """[V60.95] Phase 0: 프로젝트 설정 서브메뉴"""
        self._stage01_helpers.phase_0_recovery()  # [Phase 4C-1b-a] thin delegate

    def _stage_0_extended(self, mode: int = 0):
        """[V60.95] Stage 0 확장 기능"""
        self._stage01_helpers.stage_0_extended(mode)  # [Phase 4C-1b-b] thin delegate

    def _extend_blocks(self, stage0_manager) -> list[dict[str, Any]]:
        """[V61] Block 확장 기능 — 기존 Treatment에 블록 추가"""
        return self._stage01_helpers.extend_blocks(stage0_manager)  # [Phase 4C-1b-a] thin delegate

    def _stage_1_volumes(self):
        """[Stage 1] 아크 기반 권별 고해상도 전략 설계"""
        self._stage01_helpers.stage_1_volumes()  # [Phase 4C-1b-b] thin delegate

    def _get_max_episode_from_manuscripts(self):
        """원고 진행 head를 hybrid getter 기준으로 반환한다."""
        try:
            latest_ep_fn = getattr(self.current_project, "get_latest_episode_number", None)
            if callable(latest_ep_fn):
                return max(0, int(latest_ep_fn() or 1) - 1)

            import re as _re

            draft_files = list(self.current_project.paths.drafts.glob("*.txt"))
            if not draft_files:
                return 0

            max_ep = 0
            for f in draft_files:
                # [V70] ep_NNNN.txt 패턴 매칭 (기존 [:4].isdigit()는 "ep_0"이라 항상 False)
                _m = _re.match(r"ep_(\d+)\.txt", f.name)
                if _m:
                    ep_num = int(_m.group(1))
                    max_ep = max(max_ep, ep_num)

            return max_ep
        except Exception as e:
            self.ui.log(f"⚠️ [Manuscript Check] 원고 파일 확인 실패: {e}")
            return 0

    def _calculate_arc_from_episode(self, ep_num):
        """에피소드 번호로부터 Arc 번호 계산."""
        try:
            ep_num = int(ep_num)
        except (TypeError, ValueError):
            return 0
        if ep_num <= 0:
            return 0

        def _safe_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        arcs = getattr(getattr(self, "current_project", None), "arcs", None)
        if isinstance(arcs, list):
            for idx, arc in enumerate(arcs, start=1):
                if not isinstance(arc, dict):
                    continue
                ep_start = _safe_int(
                    arc.get("ep_start")
                    or arc.get("start_ep")
                    or arc.get("episode_start")
                    or arc.get("start_episode")
                )
                ep_end = _safe_int(arc.get("ep_end") or arc.get("end_ep") or arc.get("episode_end"))
                if ep_start > 0 and ep_end <= 0:
                    ep_count = _safe_int(arc.get("ep_count"))
                    if ep_count > 0:
                        ep_end = ep_start + ep_count - 1
                if ep_start > 0 and ep_end > 0 and ep_start <= ep_num <= ep_end:
                    return _safe_int(arc.get("arc_no")) or idx

        episodes_per_arc = max(1, int(VolumeSettings.EPISODES_PER_ARC))
        return (ep_num - 1) // episodes_per_arc + 1

    def _show_resume_status(self):
        """프로젝트 진행 현황 출력 (크래시 후 재시작 포함)."""
        if not self.current_project or not hasattr(self.current_project, "db"):
            return

        try:
            arcs = self.current_project.db.load_anchor("arcs") or []
            bp_max = self.current_project.db.get_latest_blueprint_number()
            latest_ep_fn = getattr(self.current_project, "get_latest_episode_number", None)
            ms_max = max(0, int(latest_ep_fn() - 1)) if callable(latest_ep_fn) else 0
            arc_count = len(arcs) if isinstance(arcs, list) else 0

            def _safe_ep(v):
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return 0

            total_eps = (
                sum(_safe_ep(a.get("ep_count", 0)) for a in arcs if isinstance(a, dict))
                if isinstance(arcs, list)
                else 0
            )

            self.ui.log("─" * 50)
            self.ui.log(f"📥 [Resume] 프로젝트: {self.current_project.name}")
            self.ui.log(f"   Arc 설계: {arc_count}개 완료")
            self.ui.log(f"   Blueprint: ep {bp_max}까지 완료")
            self.ui.log(f"   원고: ep {ms_max}까지 완료")
            if total_eps > 0:
                self.ui.log(f"   예상 총 에피소드: {total_eps}")
            self.ui.log("─" * 50)
        except Exception as e:
            logging.warning(f"[Resume] 상태 보고 실패: {e}")

    def _stage_2_arcs(self):
        """[V64.P3] Stage 2 Arc 설계 → Stage2Orchestrator 위임"""
        self._show_resume_status()

        # [Phase 4C-3] DI 컨텍스트 주입 (최신 속성 반영)
        from modules.core.stage2_context import Stage2Context

        self._stage2_orch.ctx = Stage2Context.from_app(self)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._stage2_orch.stage_2_arcs_async_logic())
                future.result(timeout=600)  # [Sweep3-G1] 10분 타임아웃 — 무한 블록 방지
        else:
            asyncio.run(self._stage2_orch.stage_2_arcs_async_logic())

        # [Sweep2-A1] Stage 2에서 구축한 StateTracker를 app에 동기화
        # Stage 3/4 lazy init이 재사용할 수 있도록 함
        _s2_ctx = self._stage2_orch.ctx
        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
            self.state_tracker = _s2_ctx.state_tracker
        self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)

    # -- [V64.P3] Stage 2 helpers -> Stage2Orchestrator delegation stubs ------

    def _normalize_tactical_text(self, text):
        """[V64.P3] -> Stage2Orchestrator"""
        return self._stage2_orch._normalize_tactical_text(text)

    def _is_tactical_doc_duplicate(
        self,
        candidate_text,
        reference_texts,
        threshold=TACTICAL_DOC_DUPLICATE_THRESHOLD,
    ):
        """[V64.P3] -> Stage2Orchestrator"""
        return self._stage2_orch._is_tactical_doc_duplicate(candidate_text, reference_texts, threshold)

    def _normalize_flow_text(self, text):
        """[V64.P3] -> Stage2Orchestrator"""
        return self._stage2_orch._normalize_flow_text(text)

    def _stage2_flow_guard(self, refined_arc):
        """[V64.P3] -> Stage2Orchestrator"""
        return self._stage2_orch._stage2_flow_guard(refined_arc)

    def _stage2_flow_guard_legacy(self, normalized):
        """[V64.P3] -> Stage2Orchestrator"""
        return self._stage2_orch._stage2_flow_guard_legacy(normalized)

    def _validate_volume_boundaries(self, vol_data, vol_idx):
        """[V39 패치 D] Volume 설계에서 미래 권 정보 누수 차단"""
        return Stage01Helpers.validate_volume_boundaries(vol_data, vol_idx)

    def _format_episode_coverage_label(self, episodes: list[int]) -> str:
        normalized = []
        for ep in episodes or []:
            try:
                ep_no = int(ep)
            except (TypeError, ValueError):
                continue
            if ep_no > 0:
                normalized.append(ep_no)

        normalized = sorted(set(normalized))
        if not normalized:
            return ""
        if len(normalized) == 1:
            return str(normalized[0])
        if len(normalized) == normalized[-1] - normalized[0] + 1:
            return f"{normalized[0]}-{normalized[-1]}"
        return ",".join(str(ep) for ep in normalized)

    def _build_item_acquisition_timeline(self, up_to_ep: int) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.build_item_acquisition_timeline(up_to_ep)

    def _get_int_input(
        self,
        prompt: str,
        default: int | None = None,
        min_val: int | None = None,
        max_val: int | None = None,
        attempts: int = RetryLimits.USER_INPUT_ATTEMPTS,
    ) -> int | None:
        """[4B-2] Facade → UIService"""
        return self._ui_service.get_int_input(prompt, default, min_val, max_val, attempts)

    def _extract_block_index(self, block_id: Any) -> int | None:
        """블록 ID 문자열에서 인덱스 번호 추출"""
        return self._state_service.extract_block_index(block_id)  # [Phase 4B-3] thin delegate

    def _validate_arc_mapping(self, refined_arc, enriched_block, expected_arc_no, expected_ep_start):
        return self._state_service.validate_arc_mapping(
            refined_arc, enriched_block, expected_arc_no, expected_ep_start
        )  # [Phase 4B-3] thin delegate

    def _extract_pattern_keywords(self, pattern_profile):
        return self._state_service.extract_pattern_keywords(pattern_profile)  # [Phase 4B-3] thin delegate

    def _pattern_presence_check(self, text, pattern_profile, min_hits=1):  # [V40.3 패치] 2 → 1 (완화)
        return self._state_service.pattern_presence_check(text, pattern_profile, min_hits)  # [Phase 4B-3] thin delegate

    # =================================================================
    # [V45] Validation Context 구성 헬퍼
    # =================================================================

    def _build_validation_context(
        self, ep_num: int, blueprint: dict = None, mode: str = "MANUSCRIPT", blueprint_text: str = ""
    ) -> dict:
        """[V64 P2-2] -> StateService -> PromptBuilder"""
        return self._state_service.build_validation_context(
            ep_num, blueprint, mode, blueprint_text
        )  # [Phase 4B-3] thin delegate

    # =================================================================
    # [V41] Director Sovereignty 헬퍼 메서드
    # =================================================================

    def _extract_npc_profiles(self, arc_data: dict) -> dict:
        """[V64 P2-2] -> StateService -> PromptBuilder"""
        return self._state_service.extract_npc_profiles(arc_data)  # [Phase 4B-3] thin delegate

    def _get_character_traits(self) -> dict:
        """[V64 P2-2] -> StateService -> PromptBuilder"""
        return self._state_service.get_character_traits()  # [Phase 4B-3] thin delegate

    def _load_character_archetypes(self, genre: str = "wuxia") -> dict:
        """[V41] 장르별 캐릭터 아키타입 JSON 로드"""
        return self._state_service.load_character_archetypes(genre)  # [Phase 4B-3] thin delegate

    def _get_archetype_reference_for_npcs(self, npc_profiles: dict, genre: str = "wuxia") -> str:
        """[V41] NPC 프로필에 맞는 아키타입 참고 자료 생성"""
        return self._state_service.get_archetype_reference_for_npcs(npc_profiles, genre)  # [Phase 4B-3] thin delegate

    def _classify_rejection_feedback(self, reason: str, feedback: str, blueprint: dict = None) -> str:
        """[V64 P2-3] -> StateService -> FeedbackSystem"""
        return self._state_service.classify_rejection_feedback(
            reason, feedback, blueprint
        )  # [Phase 4B-3] thin delegate

    def _audit_event(self, event_type, message, data=None):
        """[V66.1→4B-1] Facade → AuditService"""
        return self._audit_service.audit_event(event_type, message, data)

    def _flush_audit_buffer(self):
        """[V66.1→4B-1] Facade → AuditService"""
        return self._audit_service.flush_audit_buffer()

    def _write_audit_summary(self, tag="snapshot"):
        """[V66.1→4B-1] Facade → AuditService"""
        return self._audit_service.write_audit_summary(tag)

    def _get_arc_context_for_episode(self, ep_num: int) -> tuple[int | None, dict | None]:
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
            arc_idx = next(
                (
                    i
                    for i, a in enumerate(self.current_project.arcs)
                    if isinstance(a, dict)
                    and isinstance(a.get("ep_start"), int)
                    and isinstance(a.get("ep_end"), int)
                    and a.get("ep_start") <= ep_num <= a.get("ep_end")
                ),
                None,
            )
        except Exception as idx_err:
            self.ui.log(f"🚨 [Error] 아크 인덱스 추출 중 오류: {idx_err}")
            self._audit_event(
                "data_extraction_error", "arc_idx search failed", {"ep_num": ep_num, "error": str(idx_err)}
            )
            return None, None

        if arc_idx is None:
            self.ui.log(f"⚠️ 제 {ep_num}화에 해당하는 아크 계획이 없습니다.")
            self._audit_event("data_missing", "arc_index not found", {"ep_num": ep_num})
            return None, None

        arc_data = self.current_project.arcs[arc_idx]
        if not isinstance(arc_data, dict):
            self.ui.log(f"🚨 [Stop] arc_data가 딕셔너리가 아닙니다: type={type(arc_data)}")
            self._audit_event(
                "data_type_error", "arc_data invalid type", {"arc_idx": arc_idx, "type": str(type(arc_data))}
            )
            return None, None

        return arc_idx, arc_data

    def _validate_arc_data_fields(self, arc_data: dict, arc_idx: int) -> dict | None:
        """[V43] arc_data 필수 필드 검증 및 자동 복구"""
        return self._state_service.validate_arc_data_fields(arc_data, arc_idx)  # [Phase 4B-3] thin delegate

    def _load_genre_references(self) -> tuple[list, list]:
        """[V40.1 Medium Fix] 장르별 레퍼런스 데이터 로드"""
        return self._state_service.load_genre_references()  # [Phase 4B-3] thin delegate

    def _validate_arc_integrity(self, arc_data: dict[str, Any]) -> bool:
        """아크 데이터의 무결성 검증"""
        return self._state_service.validate_arc_integrity(arc_data)  # [Phase 4B-3] thin delegate

    def _validate_blueprint_integrity(self, blueprint: Any) -> bool:
        """블루프린트 데이터의 무결성 검증"""
        return self._state_service.validate_blueprint_integrity(blueprint)  # [Phase 4B-3] thin delegate

    def _show_volume_table(self, volumes: list[dict[str, Any]]) -> None:
        """[4B-2] Facade → UIService"""
        return self._ui_service.show_volume_table(volumes)

    def _stage_3_batch_blueprinting(self) -> dict:
        """[V60.80] Stage 3 - Three Phase Blueprint Generator"""
        self._show_resume_status()

        # [Phase 4C-4] DI 컨텍스트 주입 (최신 속성 반영)
        from modules.core.stage3_context import Stage3Context

        self._stage3_orch.ctx = Stage3Context.from_app(self)

        return self._stage3_orch.stage_3_batch_blueprinting()  # [Phase 4C-1a] thin delegate

    def _select_genre(self) -> dict[str, Any]:
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
                "critical_keys": [
                    "realm",
                    "internal_energy",
                    "mental_method",
                    "wealth",
                    "reputation",
                    "causal_injuries",
                    "current_objective",
                ],
            },
            "2": {
                "name": f"{GenreTypes.get_name(GenreTypes.HUNTER)} (Hunter Fantasy)",
                "type": GenreTypes.HUNTER,
                "hud_key": HUDKeys.HUNTER_HUD_ROOT,
                "description": "현대 배경, 각성/던전 시스템, 길드",
                "critical_keys": [
                    "awakening_rank",
                    "mana",
                    "skills",
                    "wealth",
                    "reputation",
                    "injuries",
                    "guild",
                    "level",
                ],
            },
            "3": {
                "name": f"{GenreTypes.get_name(GenreTypes.INVESTMENT)} (Investment Fiction)",
                "type": GenreTypes.INVESTMENT,
                "hud_key": HUDKeys.INVESTMENT_HUD_ROOT,
                "description": "금융 배경, 자본/투자 시스템, 기업/시장",
                "critical_keys": [
                    "capital",
                    "total_assets",
                    "stocks",
                    "reputation",
                    "connections",
                    "market_insight",
                    "status",
                ],
            },
            "4": {
                "name": f"{GenreTypes.get_name(GenreTypes.FANTASY)} (Fantasy)",
                "type": GenreTypes.FANTASY,
                "hud_key": HUDKeys.FANTASY_HUD_ROOT,
                "description": "이세계 배경, 마법/마나 시스템, 종족/길드",
                "critical_keys": [
                    "magic_tier",
                    "mana",
                    "spells",
                    "race",
                    "blessings",
                    "level",
                    "wealth",
                    "injuries",
                    "reputation",
                    "current_objective",
                ],
            },
            "5": {
                "name": f"{GenreTypes.get_name(GenreTypes.COMPOSER)} (Composer Fiction)",
                "type": GenreTypes.COMPOSER,
                "hud_key": HUDKeys.COMPOSER_HUD_ROOT,
                "description": "현대 배경, 음악 창작/산업 시스템, 작곡/프로듀싱",
                "critical_keys": [
                    "composition",
                    "arrangement",
                    "production",
                    "reputation",
                    "wealth",
                    "mental_state",
                    "current_objective",
                ],
            },
            "6": {
                "name": f"{GenreTypes.get_name(GenreTypes.COOKING)} (Cooking Fiction)",
                "type": GenreTypes.COOKING,
                "hud_key": HUDKeys.COOKING_HUD_ROOT,
                "description": "현대 배경, 셰프 성장/식당 경영 시스템, 요리/미식",
                "critical_keys": [
                    "chef_rank",
                    "signature_dish",
                    "culinary_techniques",
                    "restaurant_tier",
                    "reputation_score",
                    "capital",
                    "current_objective",
                ],
            },
            "7": {
                "name": f"{GenreTypes.get_name(GenreTypes.ALT_HISTORY)} (Alt History)",
                "type": GenreTypes.ALT_HISTORY,
                "hud_key": HUDKeys.ALT_HISTORY_HUD_ROOT,
                "description": "조선 시대 배경, 관직/당파/신분 시스템, 궁중 정치",
                "critical_keys": [
                    "social_class",
                    "court_rank",
                    "position",
                    "faction",
                    "political_influence",
                    "wealth",
                    "public_trust",
                    "current_objective",
                ],
            },
            "8": {
                "name": f"{GenreTypes.get_name(GenreTypes.ACTOR)} (Actor Fiction)",
                "type": GenreTypes.ACTOR,
                "hud_key": HUDKeys.ACTOR_HUD_ROOT,
                "description": "현대 배경, 연예계/배우 성장 시스템, 오디션/촬영/시상식",
                "critical_keys": [
                    "acting_skill",
                    "fame",
                    "filmography",
                    "agency",
                    "fandom",
                    "scandal_index",
                    "box_office",
                    "current_objective",
                ],
            },
            "9": {
                "name": f"{GenreTypes.get_name(GenreTypes.SPORTS)} (Sports Fiction)",
                "type": GenreTypes.SPORTS,
                "hud_key": HUDKeys.SPORTS_HUD_ROOT,
                "description": "현대 배경, 선수 성장/팀 스포츠 시스템, 경기/훈련",
                "critical_keys": [
                    "athlete_tier",
                    "sport_type",
                    "physical_stats",
                    "record",
                    "team",
                    "ranking",
                    "reputation",
                    "current_objective",
                ],
            },
            "10": {
                "name": f"{GenreTypes.get_name(GenreTypes.MEDICAL)} (Medical Fiction)",
                "type": GenreTypes.MEDICAL,
                "hud_key": HUDKeys.MEDICAL_HUD_ROOT,
                "description": "현대 배경, 의사 성장/병원 시스템, 수술/진료",
                "critical_keys": [
                    "doctor_rank",
                    "specialty",
                    "hospital",
                    "surgery_count",
                    "success_rate",
                    "reputation",
                    "current_objective",
                ],
            },
        }

        self.ui.log(
            f"\n{Emojis.BOOK} [V40 Multi-Genre Factory] 장르를 선택하십시오:\n",
            stage="stage0",
            component="genre_selection",
            event_kind="prompt",
            prompt_id="select_genre",
        )
        for key, genre in genres.items():
            self.ui.log(
                f"   {key}. {genre['name']}",
                stage="stage0",
                component="genre_selection",
                event_kind="choice_list",
                selection_value=key,
                meta={"genre_name": genre["name"]},
            )
            self.ui.log(
                f"      → {genre['description']}\n",
                stage="stage0",
                component="genre_selection",
                event_kind="choice_detail",
                selection_value=key,
                meta={"genre_name": genre["name"]},
            )

        choice = self._get_int_input(
            f"{Emojis.PENCIL} Choice (1.무협 / 2.헌터 / 3.투자 / 4.판타지 / 5.작곡가 / 6.요리 / 7.대체역사 / 8.배우물 / 9.스포츠 / 10.의학): ",  # [V70] 번호 정합성 수정
            default=1,
            min_val=1,
            max_val=10,  # [V70] Medical(10) 선택 가능하도록
        )
        if choice is None:
            choice = 1

        selected = genres.get(str(choice), genres["1"])
        self.ui.log(f"✅ [{selected['name']}] 전문 공정이 선택되었습니다.")
        self.ui.log(f"   📌 HUD 시스템: {selected['type'].upper()}")

        # [V60.95] PresetRegistry 초기화 — [INF-I8] lazy import 적용
        _PresetRegistry, _ = _lazy_load_stage0()
        if STAGE0_AVAILABLE and _PresetRegistry:
            genre_map = {
                GenreTypes.WUXIA: "wuxia",
                GenreTypes.HUNTER: "hunter",
                GenreTypes.INVESTMENT: "investment",
                GenreTypes.FANTASY: "fantasy",  # [V70] 누락된 Fantasy 추가
                GenreTypes.COMPOSER: "composer",
                GenreTypes.COOKING: "cooking",
                GenreTypes.ALT_HISTORY: "alt_history",
                GenreTypes.ACTOR: "actor",
                GenreTypes.SPORTS: "sports",
                GenreTypes.MEDICAL: "medical",
            }
            base_genre = genre_map.get(selected["type"], "wuxia")
            self.preset_registry = _PresetRegistry(base_genre=base_genre)
            self.ui.log(f"   📦 프리셋 초기화: {base_genre}")

        input("\n[Enter] 프로젝트 선택으로 이동")

        return selected

    def _select_project(self) -> str:
        """
        프로젝트 선택 UI

        projects 폴더 내 디렉토리 목록을 표시하고 사용자 선택을 받습니다.

        Returns:
            str: 선택된 프로젝트 이름
        """
        root = self._get_projects_root()
        root.mkdir(parents=True, exist_ok=True)
        # Desktop bridge also derives 1-based project_index from a lexical sort.
        projects = sorted(d.name for d in root.iterdir() if d.is_dir())
        if not projects:  # [V70] 빈 프로젝트 폴더 방어
            self.ui.log(f"❌ 프로젝트 루트({root})에 프로젝트가 없습니다. 먼저 프로젝트를 생성하세요.")
            return ""
        for i, p in enumerate(projects):
            self.ui.log(
                f" {i + 1}. {p}",
                stage="stage0",
                component="project_selection",
                event_kind="choice_list",
                selection_value=i + 1,
                meta={"project_name": p},
            )
        idx = (self._get_int_input("\n👉 Choice: ", default=1, min_val=1, max_val=len(projects)) or 1) - 1
        return projects[idx]

    def _reset_stage_2(self):
        """[V20] Stage 2(Arcs)만 SQL DB에서 삭제하여 1번 완료 상태로 회귀"""
        success = self._project_service.reset_stage_2()  # [Phase 4B-3] thin delegate
        if success:
            self.state_tracker = None
            self._prompt_builder.invalidate_timeline_cache()
            self._cumulative_state_cache = None
            self._cumulative_state_cache_key = None
            self._narrative_summaries_cache = None
            try:
                _se = self.agents.get("state_extractor") if isinstance(self.agents, dict) else None
                if _se and hasattr(_se, "invalidate_cache"):
                    _se.invalidate_cache()
                _writer = self.agents.get("writer") if isinstance(self.agents, dict) else None
                if _writer and hasattr(_writer, "invalidate_manuscript_cache"):
                    _writer.invalidate_manuscript_cache()
                _director = self.agents.get("director") if isinstance(self.agents, dict) else None
                if _director and hasattr(_director, "invalidate_caches"):
                    _director.invalidate_caches()
            except Exception as _svc_err:
                logging.warning("[SafeOps] reset_stage_2 cache invalidation failed (non-blocking): %s", _svc_err)
            try:
                _ft = getattr(self, "foreshadow_tracker", None)
                if _ft is not None and hasattr(_ft, "clear"):
                    _ft.clear()
                    if self.current_project and hasattr(self.current_project, "db"):
                        _ft.save_to_db(self.current_project.db)
            except Exception as _ft_err:
                logging.warning("[SafeOps] reset_stage_2 foreshadow sync failed (non-blocking): %s", _ft_err)

    def _rewind_stage_2(self):
        """[V20] 특정 아크 번호부터 그 이후를 전부 삭제 (정밀 되감기)"""
        success = self._project_service.rewind_stage_2()  # [Phase 4B-3] thin delegate
        # [Sweep35] clear state-related caches after rewind [I-16] 공개 메서드 사용
        if success:
            self.state_tracker = None
            self._cumulative_state_cache = None
            self._cumulative_state_cache_key = None
            self._prompt_builder.invalidate_timeline_cache()
            self._narrative_summaries_cache = None
            try:
                _se = self.agents.get("state_extractor") if isinstance(self.agents, dict) else None
                if _se and hasattr(_se, "invalidate_cache"):
                    _se.invalidate_cache()
                _writer = self.agents.get("writer") if isinstance(self.agents, dict) else None
                if _writer and hasattr(_writer, "invalidate_manuscript_cache"):
                    _writer.invalidate_manuscript_cache()
                _director = self.agents.get("director") if isinstance(self.agents, dict) else None
                if _director and hasattr(_director, "invalidate_caches"):
                    _director.invalidate_caches()
            except Exception as _se_err:
                logging.warning(f"[Sweep35] StateExtractor cache clear failed (non-blocking): {_se_err}")
            try:
                _ft = getattr(self, "foreshadow_tracker", None)
                if _ft is not None and self.current_project and hasattr(self.current_project, "db"):
                    if hasattr(_ft, "load_from_db"):
                        _ft.load_from_db(self.current_project.db)
                    elif hasattr(_ft, "clear"):
                        _ft.clear()
            except Exception as _ft_err:
                logging.warning(f"[SafeOps] rewind_stage_2 foreshadow sync failed (non-blocking): {_ft_err}")

    def _rollback_episode(self):
        """[V40.1 Rollback] 특정 회차로 되감기 (HUD, DB, Vector DB, 파일 모두 롤백)"""
        success = self._project_service.rollback_episode()  # [Phase 4B-3] thin delegate
        if success:
            self.state_tracker = None  # [NPC-L2] 롤백 후 stale NPC 레지스트리 방지
            # [Debug Sweep] 롤백 후 캐시 무효화 [I-16] 공개 메서드 사용
            self._prompt_builder.invalidate_timeline_cache()
            self._cumulative_state_cache = None
            self._cumulative_state_cache_key = None
            self._narrative_summaries_cache = None
            try:
                _writer = self.agents.get("writer") if isinstance(self.agents, dict) else None
                if _writer and hasattr(_writer, "invalidate_manuscript_cache"):
                    _writer.invalidate_manuscript_cache()
            except Exception as cache_err:
                logging.warning(
                    "[Sweep5-D] writer cache invalidation failed during rollback (non-blocking): %s",
                    cache_err,
                )

            # [Sweep35] clear director manuscript caches after rollback [I-16] 공개 메서드 사용
            try:
                _director = self.agents.get("director") if isinstance(self.agents, dict) else None
                if _director and hasattr(_director, "invalidate_caches"):
                    _director.invalidate_caches()
            except Exception as _dc_err:
                logging.warning(f"[Sweep35] Director cache invalidation failed (non-blocking): {_dc_err}")

            # [TF7-P1-08] ForeshadowTracker 롤백 동기화 — stale 복선 방지
            try:
                _ft = getattr(self, "foreshadow_tracker", None)
                if _ft is not None and self.current_project and hasattr(self.current_project, "db"):
                    if hasattr(_ft, "load_from_db"):
                        _ft.load_from_db(self.current_project.db)
                        logging.info("[TF7-P1-08] ForeshadowTracker DB 상태 재로드 완료")
                    elif hasattr(_ft, "clear"):
                        _ft.clear()
            except Exception as _ft_err:
                logging.warning(f"[TF7-P1-08] ForeshadowTracker rollback sync 실패 (비치명): {_ft_err}")

    def _wipe_production_data(self):
        """[V27.1 Wipe] 설계도는 유지하고 실제 집필 기록(Manuscripts/Blueprints)만 소거"""
        success = self._project_service.wipe_production_data()  # [Phase 4B-3] thin delegate
        if success:
            self.state_tracker = None
            self._prompt_builder.invalidate_timeline_cache()
            self._cumulative_state_cache = None
            self._cumulative_state_cache_key = None
            self._narrative_summaries_cache = None
            try:
                _writer = self.agents.get("writer") if isinstance(self.agents, dict) else None
                if _writer and hasattr(_writer, "invalidate_manuscript_cache"):
                    _writer.invalidate_manuscript_cache()
                _director = self.agents.get("director") if isinstance(self.agents, dict) else None
                if _director and hasattr(_director, "invalidate_caches"):
                    _director.invalidate_caches()
                _se = self.agents.get("state_extractor") if isinstance(self.agents, dict) else None
                if _se and hasattr(_se, "invalidate_cache"):
                    _se.invalidate_cache()
            except Exception as _svc_err:
                logging.warning("[SafeOps] wipe cache invalidation failed (non-blocking): %s", _svc_err)
            try:
                _ft = getattr(self, "foreshadow_tracker", None)
                if _ft is not None and hasattr(_ft, "clear"):
                    _ft.clear()
                    if self.current_project and hasattr(self.current_project, "db"):
                        _ft.save_to_db(self.current_project.db)
            except Exception as _ft_err:
                logging.warning(f"[SafeOps] wipe foreshadow sync failed (non-blocking): {_ft_err}")

    # =================================================================
    # [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처
    # =================================================================

    # ═══════════════════════════════════════════════════════════════
    # [V63.2] 10화 단위 내러티브 요약 시스템
    # ═══════════════════════════════════════════════════════════════

    def _generate_narrative_summary(self, up_to_ep: int) -> None:
        """
        [V66] 5화 단위 내러티브 요약 생성 및 DB 저장.
        [V66.1] 발췌 품질 개선: 앞 800자 + 중간 핵심 500자 + 뒤 500자 (~1800자/화)
                키워드 기반 중간 핵심 추출, LLM 요약 800자로 확대

        최근 5화 원고를 LLM(gemini-2.5-flash)으로 요약하여
        'narrative_summary_ep_XXX' anchor에 저장.
        이후 생성 시 장기 기억으로 활용.
        """
        import re as _re
        import time as _time

        start_ep = max(1, up_to_ep - 4)  # [V66] 10→5화 범위

        # 최근 5화 원고 수집
        manuscripts = self.current_project.db.get_recent_manuscripts(before_ep=up_to_ep + 1, limit=5)
        manuscript_count = len(manuscripts) if isinstance(manuscripts, list) else 0
        if manuscript_count < 2:  # [V66] 최소 2화로 완화
            self.ui.log(f"   ⚠️ 원고 부족 ({manuscript_count}화) - 요약 건너뜀")
            return

        episode_numbers = []
        for ms in manuscripts:
            if not isinstance(ms, dict):
                continue
            try:
                ep_no = int(ms.get("ep_num"))
            except (TypeError, ValueError):
                continue
            if ep_no > 0:
                episode_numbers.append(ep_no)
        coverage_label = self._format_episode_coverage_label(episode_numbers) or f"{start_ep}-{up_to_ep}"
        self.ui.log(f"   📝 [V66.1] 내러티브 요약 생성 중 (제{coverage_label}화)...")

        # [V66.1] 원고 텍스트 결합 (앞 800자 + 중간 핵심 500자 + 뒤 500자 ≈ 1800자/화)
        # 중간 핵심: 사망/습득/부상/배신 등 키워드 주변 250자씩 추출
        _KEY_EVENT_PATTERN = _re.compile(
            r"사망|죽|습득|획득|부상|배신|발견|파괴|탈출|각성|잃|빼앗|살해|처단|중상|결별|동맹|합류"
        )

        combined = []
        for ms in manuscripts:
            ep = ms.get("ep_num", "?")
            content = ms.get("content", "")
            if not content:
                continue

            if len(content) <= 1800:
                # 짧은 원고는 전문 사용
                combined.append(f"[제{ep}화]\n{content}")
                continue

            # 앞 800자
            head = content[:800]

            # [V66.1] 중간 핵심 500자: 키워드 기반 추출
            middle_section = ""
            mid_start = 800  # 앞 800자 이후부터 검색
            mid_end = max(mid_start, len(content) - 500)  # 뒤 500자 이전까지
            mid_content = content[mid_start:mid_end]

            match = _KEY_EVENT_PATTERN.search(mid_content)
            if match:
                # 키워드 발견: 키워드 중심 앞뒤 250자
                kw_pos = match.start() + mid_start  # 원문 기준 위치
                extract_start = max(mid_start, kw_pos - 250)
                extract_end = min(len(content) - 500, kw_pos + 250)
                middle_section = content[extract_start:extract_end]
            else:
                # 키워드 미발견: 원고 중간 지점 500자
                mid_point = len(content) // 2
                middle_section = content[max(0, mid_point - 250) : mid_point + 250]

            # 뒤 500자
            tail = content[-500:]

            excerpt = head + "\n...(중략)...\n" + middle_section + "\n...(중략)...\n" + tail
            combined.append(f"[제{ep}화]\n{excerpt}")

        combined_text = "\n\n---\n\n".join(combined)

        # LLM 요약 호출
        try:
            from google.genai import types as _types

            # [V66.1] 요약 800자로 확대, 우선순위 지시 추가
            prompt = (
                f"다음은 웹소설의 제{coverage_label}화 원고 발췌입니다.\n"
                f"800자 이내로 핵심 내러티브를 요약해주세요.\n\n"
                f"**우선 포함 항목 (절대 누락 금지)**:\n"
                f"1. 사망/살해: 누가, 어떻게 죽었는지 (사망자 이름 필수 기재)\n"
                f"2. 아이템 변화: 획득/상실/파괴된 무기/비급/소지품\n"
                f"3. 관계 변화: 동맹/배신/결별 등 인물 간 관계 전환\n"
                f"4. 위치 변화: 주인공 및 핵심 인물의 이동/현재 위치\n"
                f"5. 중요 결정: 주인공의 핵심 선택과 그 결과\n\n"
                f"추가 포함 내용:\n"
                f"6. 캐릭터 성장/각성/부상 상태\n"
                f"7. 미해결 갈등/복선\n"
                f"8. 현재 상황 (마지막 화 기준 위치, 상태, 다음 전개 방향)\n\n"
                f"[원고 발췌]\n{combined_text[:12000]}\n\n"
                f"요약 (800자 이내, 한국어):"
            )

            _time.sleep(0.3)
            response = generate_content_via_router(
                client=self.sys.api_client,
                model=_SUMMARY_MODEL,  # [V65] 중앙 상수
                contents=prompt,
                config=_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2048,  # [V66.1] 1024→2048 (800자 요약 수용)
                ),
            )

            summary = response.text.strip()
            if summary and len(summary) > 50:
                anchor_key = f"narrative_summary_ep_{up_to_ep:03d}"
                self.current_project.db.save_anchor(
                    anchor_key,
                    {
                        "ep_range": coverage_label,
                        "episode_list": sorted(set(episode_numbers)),
                        "summary": summary,
                        "ep_count": len(set(episode_numbers)) or len(manuscripts),
                    },
                )
                self.current_project.db.conn.commit()
                self.ui.log(f"   ✅ [V66.1] 내러티브 요약 저장: {anchor_key} ({len(summary)}자)")
            else:
                self.ui.log(f"   ⚠️ 요약이 너무 짧음 ({len(summary)}자) - 저장 건너뜀")

        except Exception as e:
            self.ui.log(f"   ⚠️ [V66.1] LLM 요약 실패: {str(e)[:60]}")
        finally:
            # [V66.1] B-1: 요약 생성/실패 후 캐시 무효화 (다음 로드 시 재구축)
            self._narrative_summaries_cache = None

    def _load_narrative_summaries(self) -> str:
        """
        [V63.2] 저장된 내러티브 요약들을 로드하여 프롬프트 주입용 문자열 반환.
        [V66.1] B-1: 캐시 적용 — 첫 호출 시 전체 로드, 이후 캐시 반환 (~2s/ep 절감)
        """
        # [V66.1] B-1: 캐시 히트 시 즉시 반환
        if self._narrative_summaries_cache is not None:
            return self._narrative_summaries_cache

        frontier_ep = None
        latest_ep_fn = getattr(self.current_project, "get_latest_episode_number", None)
        if callable(latest_ep_fn):
            try:
                frontier_ep = max(0, int(latest_ep_fn()) - 1)
            except (TypeError, ValueError):
                frontier_ep = None

        summaries = []
        try:
            all_anchors = self.current_project.db.load_all_anchors()
        except Exception:
            logging.warning("[V66.1] narrative summary anchor 전체 로드 실패", exc_info=True)
            all_anchors = {}

        def _parse_ep_marker(key: str) -> int:
            try:
                return int(key.rsplit("_", 1)[-1])
            except (AttributeError, TypeError, ValueError):
                return 0

        narrative_items = []
        if isinstance(all_anchors, dict):
            for key, value in all_anchors.items():
                if isinstance(key, str) and key.startswith("narrative_summary_ep_"):
                    narrative_items.append((key, value))

        for anchor_key, data in sorted(narrative_items, key=lambda item: _parse_ep_marker(item[0])):
            ep_marker = _parse_ep_marker(anchor_key)
            if frontier_ep is not None and ep_marker > frontier_ep:
                continue
            if not isinstance(data, dict) or not data.get("summary"):
                continue
            ep_label = data.get("ep_range") or self._format_episode_coverage_label(data.get("episode_list") or [])
            if not ep_label:
                ep_label = str(ep_marker)
            summaries.append(f"[제{ep_label}화 요약] {data['summary']}")

        result = "### 📚 장기 내러티브 요약 (과거 스토리)\n" + "\n\n".join(summaries) if summaries else ""

        # [V66.1] B-1: 캐시 저장
        self._narrative_summaries_cache = result
        return result

    def _stage_4_v2_chief_writer(self, limit_mode: bool = False, *, target_ep: int | None = None) -> None:
        """[V64.P3] Stage 4 V2 Chief Writer -> Stage4Orchestrator 위임
        [V69.1] Stage 4 진입 시 StateTracker/WorldState/FactLedger lazy init
        """
        self._show_resume_status()

        # ═══════════════════════════════════════════════════════════════
        # [V69.1] StateTracker 초기화 (Stage 3 없이 Stage 4 직행 시 필요)
        # ═══════════════════════════════════════════════════════════════
        if not hasattr(self, "state_tracker") or self.state_tracker is None:
            try:
                from modules.domain.agents.state_tracker import StateTracker as _StateTracker  # [INF-I8] lazy import

                self.state_tracker = _StateTracker(preset_registry=self.preset_registry, llm_client=self.sys.api_client)
                self.state_tracker.bind_db(self.current_project.db)  # [NPC-L1] NPC 이력 DB 배선
                all_arcs = self.current_project.db.load_anchor("arcs") or []
                _g = self.selected_genre.get("type", "") if self.selected_genre else ""
                self.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
                if self.state_tracker.npc_registry:
                    dead_count = sum(
                        1 for info in self.state_tracker.npc_registry.values() if info.get("status") == "dead"
                    )
                    self.ui.log(
                        f"      👤 [V69.1] StateTracker 초기화: NPC {len(self.state_tracker.npc_registry)}명 (사망: {dead_count}명)"
                    )
            except Exception as _st_err:
                self.ui.log(f"      ⚠️ [V69.1] StateTracker 초기화 실패 (비차단): {str(_st_err)[:60]}")
                self.state_tracker = None

        # [V69.1] WorldStateManager 초기화
        if not hasattr(self, "world_state") or self.world_state is None:
            try:
                from modules.core.world_state import WorldStateManager

                self.world_state = WorldStateManager(self.current_project.db)
                _ws_ep = self.world_state.last_updated_ep
                if _ws_ep > 0:
                    self.ui.log(f"      🌍 [V69.1] WorldStateManager 로드 완료 (제{_ws_ep}화 기준)")
                else:
                    self.ui.log("      🌍 [V69.1] WorldStateManager 초기화 (신규)")
            except Exception as _ws_err:
                self.ui.log(f"      ⚠️ [V69.1] WorldStateManager 초기화 실패 (비차단): {str(_ws_err)[:60]}")
                self.world_state = None

        # [TF-36] WorldState → StateTracker 바인딩
        if self.world_state is not None and self.state_tracker is not None:
            self.state_tracker.bind_world_state(self.world_state)

        # [V69.1] FactLedger 초기화
        if not hasattr(self, "fact_ledger") or self.fact_ledger is None:
            try:
                from modules.core.fact_ledger import FactLedger

                self.fact_ledger = FactLedger(self.current_project.db)
                _fl_ep = self.fact_ledger.last_updated_ep
                if _fl_ep > 0:
                    _fl_stats = self.fact_ledger.get_stats()
                    self.ui.log(
                        f"      📋 [V69.1] 팩트 원장 로드 완료 (제{_fl_ep}화 기준, 인물 {_fl_stats.get('characters', 0)}명, 아이템 {_fl_stats.get('items', 0)}개)"
                    )
                else:
                    self.ui.log("      📋 [V69.1] 팩트 원장 초기화 (신규)")
            except Exception as _fl_err:
                self.ui.log(f"      ⚠️ [V69.1] 팩트 원장 초기화 실패 (비차단): {str(_fl_err)[:60]}")
                self.fact_ledger = None

        # [Phase 4C-2a/2b/2c] DI 컨텍스트 주입 (lazy init 후)
        # [S-13] 조건부 모듈 8종 → conditional_modules dict
        from modules.core.stage4_context import Stage4Context

        # Legacy manual DI equivalent: context_advisor=getattr(self, "context_advisor", None),
        self._stage4_orch.ctx = Stage4Context.from_app(self)

        return self._stage4_orch.stage_4_v2_chief_writer(limit_mode=limit_mode, target_ep=target_ep)

    # ═══════════════════════════════════════════════════════════════
    # [OneStop] Arc-by-Arc 자동 파이프라인
    # ═══════════════════════════════════════════════════════════════
    def _compute_frontier_targets(
        self,
        *,
        ep_start: int,
        ep_end: int,
        designed_frontier_arc_no: int,
        true_final_arc_no: int,
    ) -> dict[str, Any]:
        """[FrontierLag] 현재 설계 frontier 기준 Stage 3/4 목표 회차 계산."""
        is_true_final_frontier = designed_frontier_arc_no >= true_final_arc_no
        if is_true_final_frontier:
            stage3_target = ep_end
            stage4_target = ep_end
        else:
            stage3_target = max(ep_start, ep_end - 1)
            stage4_target = max(ep_start, ep_end - 2)
        return {
            "frontier_ep_start": ep_start,
            "frontier_ep_end": ep_end,
            "designed_frontier_arc_no": designed_frontier_arc_no,
            "true_final_arc_no": true_final_arc_no,
            "is_true_final_frontier": is_true_final_frontier,
            "stage3_target": stage3_target,
            "stage4_target": stage4_target,
        }

    def _resolve_one_stop_frontier_lag_plan(
        self, *, total_arcs: int, designed_arcs: list[dict[str, Any]] | None = None
    ) -> dict[str, Any] | None:
        """[FrontierLag] 설계 frontier, 목표 회차, 현재 정렬 상태를 단일 plan으로 반환."""
        arcs = designed_arcs if designed_arcs is not None else (self.current_project.db.load_anchor("arcs") or [])
        if not arcs:
            return None

        frontier_arc = arcs[-1]
        ep_start = int(frontier_arc.get("ep_start", 1) or 1)
        ep_end = int(frontier_arc.get("ep_end", ep_start + 4) or (ep_start + 4))
        targets = self._compute_frontier_targets(
            ep_start=ep_start,
            ep_end=ep_end,
            designed_frontier_arc_no=len(arcs),
            true_final_arc_no=total_arcs,
        )

        bp_max = int(self.current_project.db.get_latest_blueprint_number() or 0)
        ms_max = int(self.current_project.get_latest_episode_number() or 1) - 1

        def _classify_alignment(max_ep: int, target_ep: int) -> str:
            if max_ep < target_ep:
                return "backlog"
            if max_ep == target_ep:
                return "aligned"
            return "ahead"

        return {
            **targets,
            "bp_max": bp_max,
            "ms_max": ms_max,
            "stage3_alignment": _classify_alignment(bp_max, targets["stage3_target"]),
            "stage4_alignment": _classify_alignment(ms_max, targets["stage4_target"]),
        }

    def _one_stop_pipeline_frontier_lag(
        self,
        *,
        max_arc_advances: int | None = None,
        batch_size_override: int | None = None,
        wait_for_menu_return: bool = True,
    ) -> dict[str, Any]:
        """[FrontierLag] Stage 2 frontier는 유지하되 Stage 3/4는 한 박자 늦춰 미래 정보를 확보."""
        self._show_resume_status()

        if not self.current_project.master_bible:
            self.current_project.master_bible = self.current_project.db.load_anchor("bible")
        if not self.current_project.master_bible:
            self.ui.log("❌ Bible 데이터가 없습니다. Stage 0을 먼저 실행하세요.")
            return

        bible_root = self.current_project.master_bible.get("MasterBible", self.current_project.master_bible)
        arcs_source = bible_root.get("plot_roadmap", [])
        total_arcs = len(arcs_source)
        if total_arcs == 0:
            self.ui.log("❌ plot_roadmap이 비어 있습니다. Stage 0에서 Treatment를 먼저 설정하세요.")
            return

        all_arcs = self.current_project.db.load_anchor("arcs") or []
        designed_arcs = len(all_arcs)
        remaining_design = max(0, total_arcs - designed_arcs)

        self.ui.log(f"\n{'═' * 60}")
        self.ui.log("🧭 [FrontierLag] One-Stop Frontier Lag")
        self.ui.log(f"   설계 frontier: {designed_arcs} / {total_arcs} (추가 설계 가능: {remaining_design}개)")
        requested_arc_limit = None
        if max_arc_advances is not None:
            try:
                requested_arc_limit = max(1, int(max_arc_advances))
            except (TypeError, ValueError):
                requested_arc_limit = None
        requested_limit_hit = False
        stop_reason = "completed"
        if requested_arc_limit is not None:
            self.ui.log(f"   🎯 [FrontierLag] 하네스 정지 경계: {requested_arc_limit}개 Arc 전진 후 정지")
        if designed_arcs > 0:
            current_plan = self._resolve_one_stop_frontier_lag_plan(total_arcs=total_arcs, designed_arcs=all_arcs)
            if current_plan:
                self.ui.log(
                    "   현재 정렬:"
                    f" S3→{current_plan['stage3_target']} ({current_plan['stage3_alignment']})"
                    f" / S4→{current_plan['stage4_target']} ({current_plan['stage4_alignment']})"
                )
                self.ui.log(
                    f"   현재 증거: bp_max={current_plan['bp_max']} / ms_max={current_plan['ms_max']}"
                )
        self.ui.log(f"{'═' * 60}\n")

        total_manuscripts = 0
        arcs_advanced = 0

        def _mark_requested_limit_hit() -> None:
            nonlocal requested_limit_hit, stop_reason
            requested_limit_hit = True
            stop_reason = "requested_arc_limit_reached"
            self.ui.log(
                f"   🛑 [FrontierLag] 요청된 Arc 경계 도달"
                f" ({arcs_advanced}/{requested_arc_limit}) — 자동 정지"
            )

        if remaining_design <= 0:
            final_plan = self._resolve_one_stop_frontier_lag_plan(total_arcs=total_arcs, designed_arcs=all_arcs)
            if not final_plan:
                self.ui.log("❌ 설계된 Arc가 없어 Frontier Lag final close를 수행할 수 없습니다.")
                return {
                    "arcs_advanced": arcs_advanced,
                    "total_manuscripts": total_manuscripts,
                    "requested_arc_limit": requested_arc_limit,
                    "requested_limit_hit": requested_limit_hit,
                    "stop_reason": "final_close_plan_missing",
                    "final_plan": None,
                }

            arc_ep_start = final_plan["frontier_ep_start"]
            arc_ep_end = final_plan["frontier_ep_end"]
            self.ui.log("   🏁 모든 Arc가 이미 설계되어 final close만 수행합니다.")
            self.ui.log(
                "   🧭 [FrontierLag]"
                f" true_final={final_plan['true_final_arc_no']}"
                f", frontier={final_plan['designed_frontier_arc_no']}"
                f", ep={arc_ep_start}~{arc_ep_end}"
                f", S3→{final_plan['stage3_target']} ({final_plan['stage3_alignment']})"
                f", S4→{final_plan['stage4_target']} ({final_plan['stage4_alignment']})"
            )

            try:
                from modules.core.stage3_context import Stage3Context

                self._stage3_orch.ctx = Stage3Context.from_app(self)
                self._stage3_orch.stage_3_batch_blueprinting(target_ep=final_plan["stage3_target"])
            except Exception as s3_err:
                self.ui.log(f"   ❌ [Stage 3] Final close 오류: {str(s3_err)[:100]}")
                return {
                    "arcs_advanced": arcs_advanced,
                    "total_manuscripts": total_manuscripts,
                    "requested_arc_limit": requested_arc_limit,
                    "requested_limit_hit": requested_limit_hit,
                    "stop_reason": "stage3_final_close_error",
                    "final_plan": final_plan,
                }

            ms_max_before = self._get_max_episode_from_manuscripts()
            try:
                self._stage_4_v2_chief_writer(target_ep=final_plan["stage4_target"])
                ms_max_after = self._get_max_episode_from_manuscripts()
                total_manuscripts += max(0, ms_max_after - ms_max_before)
            except Exception as s4_err:
                self.ui.log(f"   ❌ [Stage 4] Final close 오류: {str(s4_err)[:100]}")
                return {
                    "arcs_advanced": arcs_advanced,
                    "total_manuscripts": total_manuscripts,
                    "requested_arc_limit": requested_arc_limit,
                    "requested_limit_hit": requested_limit_hit,
                    "stop_reason": "stage4_final_close_error",
                    "final_plan": final_plan,
                }
        else:
            default_count = min(remaining_design, 3)
            if batch_size_override is not None:
                try:
                    batch_size = max(1, min(int(batch_size_override), remaining_design))
                except (TypeError, ValueError):
                    batch_size = default_count
                self.ui.log(f"   🤖 [FrontierLag] 하네스 batch_size override 적용: {batch_size}")
            else:
                batch_size = default_count
                self.ui.log(
                    "   [FrontierLag] auto-selected default batch_size: "
                    f"{batch_size} (remaining_design={remaining_design})"
                )
            target_count = batch_size

            while True:
                tranche_completed = True
                for arc_offset in range(target_count):
                    current_arc_no = designed_arcs + arcs_advanced + 1
                    self.ui.log(f"\n{'━' * 60}")
                    self.ui.log(
                        f"🧭 [FrontierLag] Arc {current_arc_no}/{total_arcs} frontier 전진 ({arc_offset + 1}/{target_count})"
                    )
                    self.ui.log(f"{'━' * 60}")

                    refreshed_arcs = self.current_project.db.load_anchor("arcs") or []
                    if current_arc_no <= len(refreshed_arcs):
                        current_arc = refreshed_arcs[current_arc_no - 1]
                        arc_ep_start = current_arc.get("ep_start", 1)
                        arc_ep_end = current_arc.get("ep_end", arc_ep_start + 4)
                        self.ui.log(
                            f"   ✅ [Stage 2] Arc {current_arc_no} 이미 설계됨 (ep {arc_ep_start}~{arc_ep_end}) — 건너뜀"
                        )
                    else:
                        self.ui.log(f"\n   📐 [Stage 2] Arc {current_arc_no} 설계 중...")
                        try:
                            from modules.core.stage2_context import Stage2Context

                            self._stage2_orch.ctx = Stage2Context.from_app(self)

                            try:
                                loop = asyncio.get_running_loop()
                            except RuntimeError:
                                loop = None

                            if loop and loop.is_running():
                                import concurrent.futures

                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        asyncio.run,
                                        self._stage2_orch.stage_2_arcs_async_logic(target_arc_count=1),
                                    )
                                    future.result(timeout=600)
                            else:
                                asyncio.run(self._stage2_orch.stage_2_arcs_async_logic(target_arc_count=1))

                            _s2_ctx = self._stage2_orch.ctx
                            if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
                                self.state_tracker = _s2_ctx.state_tracker
                            self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)
                        except Exception as s2_err:
                            self.ui.log(f"   ❌ [Stage 2] Arc {current_arc_no} 설계 실패: {str(s2_err)[:100]}")
                            self.ui.log("   🛑 Arc 없이 진행 불가 — 파이프라인을 중단합니다.")
                            stop_reason = "stage2_design_error"
                            tranche_completed = False
                            break

                        refreshed_arcs = self.current_project.db.load_anchor("arcs") or []
                        if current_arc_no > len(refreshed_arcs):
                            self.ui.log(f"   ❌ [Stage 2] Arc {current_arc_no} 생성이 확인되지 않습니다.")
                            self.ui.log("   🛑 파이프라인을 중단합니다.")
                            stop_reason = "stage2_arc_missing_after_generation"
                            tranche_completed = False
                            break

                        current_arc = refreshed_arcs[current_arc_no - 1]
                        arc_ep_start = current_arc.get("ep_start", 1)
                        arc_ep_end = current_arc.get("ep_end", arc_ep_start + 4)
                        self.ui.log(f"   ✅ [Stage 2] Arc {current_arc_no} 완료 (ep {arc_ep_start}~{arc_ep_end})")

                    frontier_plan = self._resolve_one_stop_frontier_lag_plan(
                        total_arcs=total_arcs,
                        designed_arcs=refreshed_arcs,
                    )
                    if not frontier_plan:
                        self.ui.log("   ❌ [FrontierLag] 설계 frontier 계산 실패")
                        stop_reason = "frontier_plan_missing"
                        tranche_completed = False
                        break

                    self.ui.log(
                        "   🧭 [FrontierLag]"
                        f" true_final={frontier_plan['true_final_arc_no']}"
                        f", frontier={frontier_plan['designed_frontier_arc_no']}"
                        f", ep={frontier_plan['frontier_ep_start']}~{frontier_plan['frontier_ep_end']}"
                        f", S3→{frontier_plan['stage3_target']} ({frontier_plan['stage3_alignment']})"
                        f", S4→{frontier_plan['stage4_target']} ({frontier_plan['stage4_alignment']})"
                    )
                    self.ui.log(
                        f"   📌 [FrontierLag] bp_max={frontier_plan['bp_max']} / ms_max={frontier_plan['ms_max']}"
                    )

                    self.ui.log(
                        "\n"
                        f"   📐 [Stage 3] Blueprint frontier 동기화"
                        f" (target <= ep {frontier_plan['stage3_target']})..."
                    )
                    try:
                        from modules.core.stage3_context import Stage3Context

                        self._stage3_orch.ctx = Stage3Context.from_app(self)
                        s3_result = self._stage3_orch.stage_3_batch_blueprinting(
                            target_ep=frontier_plan["stage3_target"]
                        )
                        s3_success = s3_result.get("success_count", 0) if s3_result else 0
                        s3_fail = s3_result.get("fail_count", 0) if s3_result else 0

                        if s3_success == 0 and s3_fail > 0:
                            self.ui.log(f"   ⚠️ [Stage 3] Blueprint 생성 실패 (성공: 0, 실패: {s3_fail})")
                            try:
                                skip_choice = input("   건너뛰고 다음 Arc로? (1=건너뛰기 / 2=중단, 기본: 2): ").strip()
                            except (EOFError, KeyboardInterrupt):
                                skip_choice = "2"
                            if skip_choice != "1":
                                self.ui.log("   🛑 사용자 요청으로 파이프라인을 중단합니다.")
                                stop_reason = "stage3_user_abort"
                                tranche_completed = False
                                break
                            self.ui.log("   ⏭️ Stage 3 건너뛰고 다음 Arc로...")
                            arcs_advanced += 1
                            if requested_arc_limit is not None and arcs_advanced >= requested_arc_limit:
                                _mark_requested_limit_hit()
                                tranche_completed = False
                                break
                            continue
                        elif s3_success == 0 and s3_fail == 0:
                            self.ui.log(
                                f"   ✅ [Stage 3] 이미 frontier target({frontier_plan['stage3_target']}화)까지 정렬됨"
                            )
                        else:
                            self.ui.log(f"   ✅ [Stage 3] Blueprint 완료 (성공: {s3_success}, 실패: {s3_fail})")
                    except Exception as s3_err:
                        self.ui.log(f"   ❌ [Stage 3] Blueprint 생성 오류: {str(s3_err)[:100]}")
                        try:
                            skip_choice = input("   건너뛰고 다음 Arc로? (1=건너뛰기 / 2=중단, 기본: 2): ").strip()
                        except (EOFError, KeyboardInterrupt):
                            skip_choice = "2"
                        if skip_choice != "1":
                            self.ui.log("   🛑 사용자 요청으로 파이프라인을 중단합니다.")
                            stop_reason = "stage3_exception_user_abort"
                            tranche_completed = False
                            break
                        arcs_advanced += 1
                        if requested_arc_limit is not None and arcs_advanced >= requested_arc_limit:
                            _mark_requested_limit_hit()
                            tranche_completed = False
                            break
                        continue

                    self.ui.log(
                        "\n"
                        f"   🚀 [Stage 4] Manuscript frontier 동기화"
                        f" (target <= ep {frontier_plan['stage4_target']})..."
                    )
                    ms_max_before = self._get_max_episode_from_manuscripts()
                    try:
                        self._stage_4_v2_chief_writer(target_ep=frontier_plan["stage4_target"])
                        ms_max_after = self._get_max_episode_from_manuscripts()
                        arc_manuscripts = max(0, ms_max_after - ms_max_before)
                        total_manuscripts += arc_manuscripts
                        self.ui.log(f"   ✅ [Stage 4] 원고 완료 ({arc_manuscripts}화 생산)")
                    except KeyboardInterrupt:
                        self.ui.log("\n   ⚠️ 사용자 중단 요청.")
                        stop_reason = "keyboard_interrupt"
                        tranche_completed = False
                        break
                    except Exception as s4_err:
                        self.ui.log(f"   ❌ [Stage 4] 원고 집필 오류: {str(s4_err)[:100]}")
                        self.ui.log("   (기존 에러 핸들링에 따라 최선 결과 수용)")

                    arcs_advanced += 1
                    if requested_arc_limit is not None and arcs_advanced >= requested_arc_limit:
                        _mark_requested_limit_hit()
                        tranche_completed = False
                        break
                if requested_limit_hit:
                    break
                if not tranche_completed:
                    break

                self.ui.log(f"\n   ✅ 요청한 {target_count}개 Arc frontier 전진 완료!")

                remaining_design = total_arcs - (designed_arcs + arcs_advanced)
                if remaining_design <= 0:
                    self.ui.log("   🎉 모든 Arc frontier 전진 완료!")
                    break

                target_count = min(remaining_design, batch_size)
                self.ui.log(
                    "   🔁 [FrontierLag] 승인 없이 자동 계속"
                    f" (남은 Arc: {remaining_design}개 / 다음 tranche: {target_count}개 / batch_size: {batch_size})"
                )
                continue

        final_arcs = self.current_project.db.load_anchor("arcs") or []
        final_plan = self._resolve_one_stop_frontier_lag_plan(total_arcs=total_arcs, designed_arcs=final_arcs)
        self.ui.log(f"\n{'═' * 60}")
        self.ui.log("📊 [FrontierLag] 파이프라인 완료 보고")
        self.ui.log(f"   추가 설계 Arc: {arcs_advanced}개")
        self.ui.log(f"   전체 Arc: {len(final_arcs)}/{total_arcs}")
        self.ui.log(f"   생산 원고: 약 {total_manuscripts}화")
        if final_plan:
            self.ui.log(
                f"   최종 정렬: S3→{final_plan['stage3_target']} ({final_plan['stage3_alignment']})"
                f" / S4→{final_plan['stage4_target']} ({final_plan['stage4_alignment']})"
            )
        self.ui.log(f"{'═' * 60}\n")

        if wait_for_menu_return:
            try:
                input("[Enter] 메뉴로 돌아가기")
            except (EOFError, KeyboardInterrupt):
                pass

        return {
            "arcs_advanced": arcs_advanced,
            "total_manuscripts": total_manuscripts,
            "requested_arc_limit": requested_arc_limit,
            "requested_limit_hit": requested_limit_hit,
            "stop_reason": stop_reason,
            "final_plan": final_plan,
        }

    def _one_stop_pipeline(self) -> None:
        """[OneStop] Arc 1개씩 Stage 2→3→4를 순차 실행하여 상류 오염을 조기 감지."""
        self._show_resume_status()

        # ─── 1. 전제 확인 ───
        if not self.current_project.master_bible:
            self.current_project.master_bible = self.current_project.db.load_anchor("bible")
        if not self.current_project.master_bible:
            self.ui.log("❌ Bible 데이터가 없습니다. Stage 0을 먼저 실행하세요.")
            return

        bible_root = self.current_project.master_bible.get("MasterBible", self.current_project.master_bible)
        arcs_source = bible_root.get("plot_roadmap", [])
        total_arcs = len(arcs_source)
        if total_arcs == 0:
            self.ui.log("❌ plot_roadmap이 비어 있습니다. Stage 0에서 Treatment를 먼저 설정하세요.")
            return

        all_arcs = self.current_project.db.load_anchor("arcs") or []
        designed_arcs = len(all_arcs)

        # [TF-35d] "완료된 Arc" = 마지막 에피소드 원고까지 존재하는 Arc
        latest_written = self.current_project.get_latest_episode_number() - 1  # 작성된 최종 ep (0 if none)
        fully_done_arcs = 0
        for arc in all_arcs:
            if latest_written >= arc.get("ep_end", 0):
                fully_done_arcs += 1
            else:
                break  # 순차적이므로 첫 미완성 이후는 전부 미완성

        remaining = total_arcs - fully_done_arcs

        if remaining <= 0:
            self.ui.log(f"✅ 모든 Arc({total_arcs}개)의 원고가 이미 완료되었습니다.")
            return

        # ─── 2. 유저 입력 ───
        self.ui.log(f"\n{'═' * 60}")
        self.ui.log("🔄 [OneStop] Arc-by-Arc 자동 파이프라인")
        self.ui.log(f"   완료된 Arc: {fully_done_arcs} / 전체: {total_arcs} (남은: {remaining}개)")
        if designed_arcs > fully_done_arcs:
            _incomplete = designed_arcs - fully_done_arcs
            self.ui.log(f"   ⚠️ 미완성 Arc {_incomplete}개 감지 — 이어쓰기 진행")
        self.ui.log(f"{'═' * 60}\n")

        default_count = min(remaining, 3)
        target_count = self._get_int_input(
            f"👉 몇 개 Arc를 처리할까요? (1~{remaining}, 기본: {default_count}): ",
            default=default_count,
            min_val=1,
            max_val=remaining,
        )
        if target_count is None:
            target_count = default_count

        total_manuscripts = 0
        arcs_completed = 0

        # ─── 3. Arc-by-Arc 루프 (배치 반복) ───
        while True:
            for arc_offset in range(target_count):
                current_arc_no = fully_done_arcs + arcs_completed + 1
                self.ui.log(f"\n{'━' * 60}")
                self.ui.log(
                    f"🔄 [OneStop] Arc {current_arc_no}/{total_arcs} 처리 시작 ({arc_offset + 1}/{target_count})"
                )
                self.ui.log(f"{'━' * 60}")

                # [TF-35d] Arc가 이미 설계되었으면 Stage 2 건너뛰기
                refreshed_arcs = self.current_project.db.load_anchor("arcs") or []
                if current_arc_no <= len(refreshed_arcs):
                    # Arc already designed — skip Stage 2
                    current_arc = refreshed_arcs[current_arc_no - 1]
                    arc_ep_start = current_arc.get("ep_start", 1)
                    arc_ep_end = current_arc.get("ep_end", arc_ep_start + 4)
                    self.ui.log(
                        f"   ✅ [Stage 2] Arc {current_arc_no} 이미 설계됨 (ep {arc_ep_start}~{arc_ep_end}) — 건너뜀"
                    )
                else:
                    # New arc — 기존 Stage 2 로직
                    self.ui.log(f"\n   📐 [Stage 2] Arc {current_arc_no} 설계 중...")
                    try:
                        from modules.core.stage2_context import Stage2Context

                        self._stage2_orch.ctx = Stage2Context.from_app(self)

                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            loop = None

                        if loop and loop.is_running():
                            import concurrent.futures

                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    asyncio.run,
                                    self._stage2_orch.stage_2_arcs_async_logic(target_arc_count=1),
                                )
                                future.result(timeout=600)
                        else:
                            asyncio.run(self._stage2_orch.stage_2_arcs_async_logic(target_arc_count=1))

                        # StateTracker 동기화 (기존 _stage_2_arcs 패턴)
                        _s2_ctx = self._stage2_orch.ctx
                        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
                            self.state_tracker = _s2_ctx.state_tracker
                        self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)

                    except Exception as s2_err:
                        self.ui.log(f"   ❌ [Stage 2] Arc {current_arc_no} 설계 실패: {str(s2_err)[:100]}")
                        self.ui.log("   🛑 Arc 없이 진행 불가 — 파이프라인을 중단합니다.")
                        break

                    # Arc 생성 확인
                    refreshed_arcs = self.current_project.db.load_anchor("arcs") or []
                    if current_arc_no > len(refreshed_arcs):
                        self.ui.log(f"   ❌ [Stage 2] Arc {current_arc_no} 생성이 확인되지 않습니다.")
                        self.ui.log("   🛑 파이프라인을 중단합니다.")
                        break

                    current_arc = refreshed_arcs[current_arc_no - 1]
                    arc_ep_start = current_arc.get("ep_start", 1)
                    arc_ep_end = current_arc.get("ep_end", arc_ep_start + 4)
                    self.ui.log(f"   ✅ [Stage 2] Arc {current_arc_no} 완료 (ep {arc_ep_start}~{arc_ep_end})")

                # ━━━ Stage 3: Blueprint (arc 범위) ━━━
                self.ui.log(f"\n   📐 [Stage 3] Blueprint 생성 중 (ep {arc_ep_start}~{arc_ep_end})...")
                try:
                    from modules.core.stage3_context import Stage3Context

                    self._stage3_orch.ctx = Stage3Context.from_app(self)
                    s3_result = self._stage3_orch.stage_3_batch_blueprinting(target_ep=arc_ep_end)
                    s3_success = s3_result.get("success_count", 0) if s3_result else 0
                    s3_fail = s3_result.get("fail_count", 0) if s3_result else 0

                    if s3_success == 0 and s3_fail > 0:
                        # 실제 실패
                        self.ui.log(f"   ⚠️ [Stage 3] Blueprint 생성 실패 (성공: 0, 실패: {s3_fail})")
                        try:
                            skip_choice = input("   건너뛰고 다음 Arc로? (1=건너뛰기 / 2=중단, 기본: 2): ").strip()
                        except (EOFError, KeyboardInterrupt):
                            skip_choice = "2"
                        if skip_choice != "1":
                            self.ui.log("   🛑 사용자 요청으로 파이프라인을 중단합니다.")
                            break
                        self.ui.log("   ⏭️ Stage 3 건너뛰고 다음 Arc로...")
                        arcs_completed += 1
                        continue
                    elif s3_success == 0 and s3_fail == 0:
                        # [TF-35d] 모든 Blueprint 이미 존재 — 정상
                        self.ui.log(f"   ✅ [Stage 3] Blueprint 이미 완료 (ep {arc_ep_start}~{arc_ep_end}) — 건너뜀")
                    else:
                        self.ui.log(f"   ✅ [Stage 3] Blueprint 완료 (성공: {s3_success}, 실패: {s3_fail})")
                except Exception as s3_err:
                    self.ui.log(f"   ❌ [Stage 3] Blueprint 생성 오류: {str(s3_err)[:100]}")
                    try:
                        skip_choice = input("   건너뛰고 다음 Arc로? (1=건너뛰기 / 2=중단, 기본: 2): ").strip()
                    except (EOFError, KeyboardInterrupt):
                        skip_choice = "2"
                    if skip_choice != "1":
                        self.ui.log("   🛑 사용자 요청으로 파이프라인을 중단합니다.")
                        break
                    arcs_completed += 1
                    continue

                # ━━━ Stage 4: 원고 (arc 범위) ━━━
                self.ui.log(f"\n   🚀 [Stage 4] 원고 집필 중 (ep {arc_ep_start}~{arc_ep_end})...")
                ms_max_before = self._get_max_episode_from_manuscripts()  # [감리] pre-baseline
                try:
                    self._stage_4_v2_chief_writer(target_ep=arc_ep_end)
                    # 생산된 원고 수 확인 (delta 방식 — 과다 집계 방지)
                    ms_max_after = self._get_max_episode_from_manuscripts()
                    arc_manuscripts = max(0, ms_max_after - ms_max_before)
                    total_manuscripts += arc_manuscripts
                    self.ui.log(f"   ✅ [Stage 4] 원고 완료 ({arc_manuscripts}화 생산)")
                except KeyboardInterrupt:
                    self.ui.log("\n   ⚠️ 사용자 중단 요청.")
                    break
                except Exception as s4_err:
                    self.ui.log(f"   ❌ [Stage 4] 원고 집필 오류: {str(s4_err)[:100]}")
                    self.ui.log("   (기존 에러 핸들링에 따라 최선 결과 수용)")

                arcs_completed += 1
            else:
                # for 루프 정상 완료 (break 없이) — 배치 완료
                self.ui.log(f"\n   ✅ 요청한 {target_count}개 Arc 전부 완료!")

                # 남은 Arc 확인
                remaining = total_arcs - (fully_done_arcs + arcs_completed)
                if remaining <= 0:
                    self.ui.log("   🎉 모든 Arc 처리 완료!")
                    break

                try:
                    cont_choice = input(
                        f"   계속할까요? (남은 Arc: {remaining}개) (1=계속 / 2=중단, 기본: 1): "
                    ).strip()
                except (EOFError, KeyboardInterrupt):
                    cont_choice = "2"
                if cont_choice == "2":
                    self.ui.log("   🛑 사용자 요청으로 파이프라인을 중단합니다.")
                    break

                # 다음 배치 크기 입력
                default_next = min(remaining, 3)
                target_count = self._get_int_input(
                    f"   👉 추가로 몇 개 Arc? (1~{remaining}, 기본: {default_next}): ",
                    default=default_next,
                    min_val=1,
                    max_val=remaining,
                )
                if target_count is None:
                    target_count = default_next
                continue  # while 루프 다음 배치
            # for 루프가 break로 종료됨 — 전체 중단
            break

        # ─── 4. 최종 보고 ───
        final_arcs = self.current_project.db.load_anchor("arcs") or []
        self.ui.log(f"\n{'═' * 60}")
        self.ui.log("📊 [OneStop] 파이프라인 완료 보고")
        if arcs_completed > 0:
            self.ui.log(
                f"   Arc 처리: {arcs_completed}개 (Arc {fully_done_arcs + 1}~{fully_done_arcs + arcs_completed})"
            )
        else:
            self.ui.log("   Arc 처리: 0개")
        self.ui.log(f"   전체 Arc: {len(final_arcs)}/{total_arcs}")
        self.ui.log(f"   생산 원고: 약 {total_manuscripts}화")
        self.ui.log(f"{'═' * 60}\n")

        try:
            input("[Enter] 메뉴로 돌아가기")
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    SovereignApp().boot()
