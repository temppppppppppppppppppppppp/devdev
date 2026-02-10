import sys
import os

# [V61.3] Faulthandler 활성화 - segfault 등 치명적 오류 추적
import faulthandler
import atexit
_fault_log = open("crash_dump.log", "w", encoding="utf-8")
faulthandler.enable(file=_fault_log, all_threads=True)
atexit.register(_fault_log.close)
print(f"[V61.3] Faulthandler 활성화 → crash_dump.log", file=sys.stderr)

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
from rich.console import Console
from rich.text import Text

# [V65] 스피너 & 전역 콘솔 → modules/core/spinners.py로 이동 (순환 참조 해소)
import threading
from modules.core.spinners import rich_console, FancySpinner, StageSpinner  # noqa: F401
import modules.core.spinners as _spinners_mod  # [V65] 플래그 동기화용


from google import genai
import re 
from modules.core.slack_bot import notifier # [V40] Slack 알림 추가 
from modules.core.system import StudioSystem
from modules.core.studio_visualizer import StudioVisualizer
from modules.core.memory_engine import LongTermMemory
from modules.core.prompt_builder import PromptBuilder  # [V64 P2-2]
from modules.core.feedback_system import FeedbackSystem  # [V64 P2-3]
from modules.core.stage2_orchestrator import Stage2Orchestrator  # [V64.P3]
from modules.core.stage4_orchestrator import Stage4Orchestrator  # [V64.P3]
from modules.core.perf_timer import PerfTimer  # [V65] 파이프라인 성능 프로파일링
from modules.domain.agents.analyst import Analyst
# [V65] Architect 삭제 (완전 레거시 — ThreePhaseBlueprintGenerator로 대체됨)
from modules.domain.agents.writer import Writer
from modules.domain.agents.director import Director
from modules.domain.agents.manager import Manager
from modules.domain.agents.weaver import Weaver
from modules.domain.agents.continuity_inspector import ContinuityInspector  # [V48] 연속성 검증 에이전트
from modules.domain.agents.critic import Critic  # [V52.2] 비평가 에이전트
from modules.domain.agents.block_enricher import BlockEnricher  # [V60.10] Treatment Block 농축 에이전트
from modules.domain.agents.state_extractor import StateExtractor  # [V60.10] 상태 추출 에이전트
from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator  # [V60.11] Arc 앙상블 생성기
from modules.domain.agents.arc_draft_validator import ArcDraftValidator  # [V60.11] Arc 초안 검증기
from modules.domain.agents.constraint_compiler import ConstraintCompiler  # [V60.11] 제약 컴파일러
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator  # [V60.12] 4단계 Arc 생성기
from modules.domain.agents.state_locked_arc_generator import StateLockedArcGenerator  # [V60.14] 상태 잠금 Arc 생성기
from modules.domain.agents.preflight_checker import PreflightChecker  # [V60.12] 생성 전 분석
from modules.domain.agents.arc_critic import ArcCritic  # [V60.12] Arc 비평가
from modules.domain.agents.consensus_validator import ConsensusValidator  # [V60.12] 합의 검증기
from modules.domain.agents.negative_example_injector import NegativeExampleInjector  # [V60.12] 실패 사례 주입
from modules.domain.agents.arc_corrector import ArcCorrector  # [V60.42] Arc 부분 수정
from modules.domain.agents.state_tracker import StateTracker  # [V60.94] 상태 추적기 (NPC 생사, 무공 습득)
from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator  # [V60.80] 3단계 Blueprint 생성기
from modules.core.narrative_diversity import NarrativeDiversityEngine  # [V48] 서사 다양성 엔진
from modules.core.metrics_collector import get_metrics_collector  # [V49.3] 비용 추적 시스템
# [V65] ConstraintDB 미사용 import 삭제

# [V60.95] Stage 0 모듈 - 프로젝트 초기화 및 역설계
try:
    from modules.core.stage0 import StageZeroManager, PresetRegistry, StyleGuide
    STAGE0_AVAILABLE = True
except ImportError as e:
    print(f"[!] Stage 0 모듈 로드 실패: {e}")
    STAGE0_AVAILABLE = False

# [V50] 서사 품질 향상 모듈
try:
    # [V65] V50.1~V51.1 삭제: TensionCurveManager, DialogueQualityEngine, SubplotWeaver, ReaderSimulator
    # [V65] PacingAnalyzer 재연결 완료
    # Stage 4 V2 전환 이후 호출 경로 없음 — 모듈 파일은 보존 (재연결 가능)
    from modules.core.quality_amplifier import QualityAmplifier  # [V51.2] 품질 증폭기
    from modules.core.agent_intelligence import AgentIntelligence  # [V51.3] 에이전트 지능 향상
    from modules.core.failure_learning import FailureLearner  # [V51.4] 실패 학습 시스템
    from modules.core.character_voice import CharacterVoiceTracker  # [V51.5] 캐릭터 음성 추적
    from modules.core.foreshadow_tracker import ForeshadowTracker  # [V51.6] 복선 추적
    from modules.core.pacing_analyzer import PacingAnalyzer  # [V65] 호흡 분석기 재연결
    from modules.core.emotion_tracker import EmotionArcTracker  # [V60.26] 감정선 추적
    from modules.core.power_scaling import PowerScalingTracker  # [V60.26] 파워 스케일링 추적
    from modules.core.state_delta_tracker import StateDeltaTracker  # [V60.26] 상태 변화 추적
    from modules.core.semantic_item_registry import SemanticItemRegistry  # [V60.26] 의미적 아이템 레지스트리
    from modules.core.character_voice_profiler import CharacterVoiceProfiler  # [V60.26] 캐릭터 음성 프로파일러 (V58)
    from modules.core.self_reflection import SelfReflector, ReflectionTarget  # [V52.1] 자기 성찰
    from modules.core.expert_mixture import ExpertMixture  # [V52.3] 전문가 혼합
    from modules.core.cross_agent_verifier import CrossAgentVerifier, ComplianceLevel  # [V52.4] 교차 검증
    from modules.core.dynamic_prompt_weighting import DynamicPromptWeighter  # [V53.1] 동적 프롬프트 가중치
    from modules.core.chain_of_verification import ChainOfVerification  # [V53.2] 사실 검증 체인
    from modules.core.confidence_calibration import ConfidenceCalibrator  # [V53.3] 신뢰도 보정
    from modules.core.pre_director_checklist import PreDirectorChecklist  # [V53.4] 사전 체크리스트
    from modules.core.tree_of_thoughts import TreeOfThoughts  # [V53.5] Tree of Thoughts
    from modules.core.adversarial_self_play import AdversarialSelfPlay  # [V53.6] 적대적 자기 대결
    from modules.core.multi_agent_deliberation import MultiAgentDeliberation  # [V53.7] 다중 에이전트 토론
    # [V54] 비용 절감 + 품질 향상 모듈
    from modules.core.semantic_cache import SemanticCache  # [V54.1] 의미론적 캐시
    from modules.core.context_compression import ContextCompressor  # [V54.2] 컨텍스트 압축
    from modules.core.adaptive_retry import get_adaptive_manager  # [V54.3] 적응형 재시도
    # [V65] TwoPhaseGenerator 삭제 (Dead Code — Stage 4 V2 전환으로 미사용)
    from modules.core.blueprint_memory import SuccessPatternMemory  # [V54.5] 성공 패턴 메모리
    from modules.core.manuscript_enhancer import ManuscriptEnhancer  # [V55] 원고 품질/분량 향상
    from modules.core.constitutional_checker import ConstitutionalChecker  # [V55.2] 헌법적 자기검증
    from modules.core.writer_template import WriterTemplate  # [V55.3] 원고 템플릿
    from modules.core.pass_rate_monitor import PassRateMonitor  # [V55.3] 통과율 모니터
    from modules.core.quality_dashboard import QualityDashboard  # [V60] 품질 대시보드
    from modules.core.stage2_optimizer import create_stage2_optimizer  # [V60.25] [V65] Stage2Optimizer 미사용 삭제
    V50_MODULES_AVAILABLE = True
except ImportError as e:
    V50_MODULES_AVAILABLE = False
    print(f"⚠️ [V50] 일부 모듈 미설치: {e}")

# [V65] 모듈 가용성 플래그를 spinners 모듈에 동기화 (orchestrator 순환 참조 해소)
_spinners_mod.V50_MODULES_AVAILABLE = V50_MODULES_AVAILABLE
_spinners_mod.STAGE0_AVAILABLE = STAGE0_AVAILABLE

import random
from google.genai import types
import asyncio

# [V40 Enhanced] 중앙 상수 관리
from modules.core.constants import (
    GenreTypes, RetryLimits, VolumeSettings,
    HUDKeys, AuditEvents, Stages, ErrorMessages,
    SuccessMessages, Emojis, RecoveryLimits, AIModels, WritingLimits
)

# [V65] 모델명 상수 — constants.py AIModels SSOT
_V50_MODULE_MODEL = AIModels.V50_MODULE_MODEL
_FLASH_ANALYSIS_MODEL = AIModels.FLASH_ANALYSIS_MODEL
_SUMMARY_MODEL = AIModels.SUMMARY_MODEL




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
        self.diversity_engine = None  # [V48] 서사 다양성 엔진
        self.stage_rejection_history = []  # [V60.3] Stage간 REJECT 히스토리 전달
        # [V62.5] extract_cumulative_state 배치 캐시
        self._cumulative_state_cache = None
        self._cumulative_state_cache_key = 0
        self._state_tracker_loaded_arcs = 0  # [V62.5] StateTracker 증분 업데이트 추적
        self._prompt_builder = PromptBuilder(app=self)  # [V64 P2-2]
        self._feedback_system = FeedbackSystem()  # [V64 P2-3]
        self._stage2_orch = Stage2Orchestrator(app=self)  # [V64.P3]
        self._stage4_orch = Stage4Orchestrator(app=self)  # [V64.P3]
        self.perf_timer = PerfTimer("Pipeline")  # [V65] 파이프라인 성능 프로파일링

        # [V64.P4] 동적 주입 속성 선언 (monkey-patching 제거)
        self._entity_cache_arc_idx = -1      # Entity Registry 캐시 arc 인덱스
        self._cached_entity_registry = None  # Entity Registry 캐시

        # [V50] 서사 품질 향상 모듈
        # [V65] V50.1~V51.1 속성 삭제 (tension_manager, dialogue_engine, subplot_weaver, reader_simulator)
        self.pacing_analyzer = None   # [V65] 호흡 분석기 재연결
        self.quality_amplifier = None  # [V51.2] 품질 증폭기
        self.agent_intelligence = None # [V51.3] 에이전트 지능 향상
        self.failure_learner = None    # [V51.4] 실패 학습 시스템
        self.character_voice = None    # [V51.5] 캐릭터 음성 추적
        self.foreshadow_tracker = None # [V51.6] 복선 추적
        self.emotion_tracker = None    # [V60.26] 감정선 추적
        self.power_scaling = None      # [V60.26] 파워 스케일링 추적
        self.state_delta_tracker = None # [V60.26] 상태 변화 추적
        self.semantic_item_registry = None # [V60.26] 의미적 아이템 레지스트리
        self.voice_profiler = None     # [V60.26] 캐릭터 음성 프로파일러 (V58)
        self.self_reflector = None     # [V52.1] 자기 성찰 체인
        self.expert_mixture = None     # [V52.3] 전문가 혼합
        self.cross_verifier = None     # [V52.4] 교차 에이전트 검증

        # [V53] 지능 향상 모듈
        self.prompt_weighter = None    # [V53.1] 동적 프롬프트 가중치
        self.chain_of_verification = None  # [V53.2] 사실 검증 체인
        self.confidence_calibrator = None  # [V53.3] 신뢰도 보정
        self.pre_director_checklist = None # [V53.4] 사전 체크리스트
        self.tree_of_thoughts = None   # [V53.5] Tree of Thoughts
        self.adversarial_self_play = None  # [V53.6] 적대적 자기 대결
        self.multi_agent_deliberation = None  # [V53.7] 다중 에이전트 토론

        # [V54] 비용 절감 + 품질 향상 모듈
        self.semantic_cache = None      # [V54.1] 의미론적 캐시
        self.context_compressor = None  # [V54.2] 컨텍스트 압축
        self.adaptive_manager = None    # [V54.3] 적응형 재시도 관리자
        # [V65] two_phase_ms/bp/arc 삭제 (Dead Code — TwoPhaseGenerator 제거)
        self.success_patterns = None    # [V54.5] 성공 패턴 메모리
        self.manuscript_enhancer = None # [V55] 원고 품질/분량 향상
        self.constitutional_checker = None  # [V55.2] 헌법적 자기검증
        self.writer_template = None         # [V55.3] 원고 템플릿
        self.pass_rate_monitor = None       # [V55.3] 통과율 모니터
        self.quality_dashboard = None       # [V60] 품질 대시보드

        # [V66] SemanticPlotGuard 활성화
        self.semantic_plot_guard = None

        # [V60.95] Stage 0 프리셋 레지스트리
        self.preset_registry = None         # PresetRegistry 인스턴스

    def _safe_commit(self) -> bool:
        """
        [V40 Enhanced] 안전한 DB 커밋 래퍼 (동기 전용)
        [V61.7] 항상 커밋 보장 (in_transaction 조건 제거)

        Returns:
            bool: 커밋 성공 여부
        """
        if hasattr(self, 'current_project') and self.current_project and hasattr(self.current_project, 'db'):
            try:
                self.current_project.db.conn.commit()
                self._audit_event(AuditEvents.DB_COMMIT, SuccessMessages.DB_COMMIT_SUCCESS)
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
        error_category = audit_result.get('error_category', 'UNKNOWN')
        reason = audit_result.get('reason', '')

        # 에러 카테고리 자동 분류
        if error_category == 'UNKNOWN':
            logic_error_keywords = ['인과', '설정 오류', '죽은', '순간이동', '무기 전환', '캐릭터 붕괴', '타임라인']
            quality_issue_keywords = ['분량', '밀도', '묘사', '문체', '건조', '재미']

            if any(kw in reason for kw in logic_error_keywords):
                error_category = 'LOGIC_ERROR'
            elif any(kw in reason for kw in quality_issue_keywords):
                error_category = 'QUALITY_ISSUE'
            else:
                error_category = 'QUALITY_ISSUE'  # 기본값

        audit_result['error_category'] = error_category

        # action_items 생성
        action_items = []

        if audit_result.get('decision') == 'REJECT':
            # 분량 문제
            if stage == 4 and content_length > 0:
                if content_length < 4000:
                    action_items.append({
                        'type': 'QUALITY_ISSUE',
                        'description': f'분량 절대 미달 ({content_length}자)',
                        'severity': 'CRITICAL',
                        'suggestion': f'최소 {4000 - content_length}자 추가 필요. 심리 묘사, 조연 리액션, 환경 묘사로 보충.'
                    })
                elif content_length < 4500:
                    action_items.append({
                        'type': 'QUALITY_ISSUE',
                        'description': f'분량 위험 영역 ({content_length}자)',
                        'severity': 'HIGH',
                        'suggestion': '500자 이상 추가하여 안전 영역(4,500자)으로 확보.'
                    })

            # 서사 흐름 문제
            if '폭주' in reason:
                action_items.append({
                    'type': 'LOGIC_ERROR',
                    'description': '서사 폭주 감지',
                    'severity': 'CRITICAL',
                    'suggestion': '사건을 더 잘게 쪼개라. 1~2개 장면에 모든 사건이 해결되면 안 됨.'
                })
            if '정체' in reason:
                action_items.append({
                    'type': 'LOGIC_ERROR',
                    'description': '서사 정체 감지',
                    'severity': 'CRITICAL',
                    'suggestion': '3개 장면 이상 같은 상황 반복 금지. 인과적 전진을 확보하라.'
                })

            # 에러 카테고리별 일반 가이드
            if error_category == 'LOGIC_ERROR' and not action_items:
                action_items.append({
                    'type': 'LOGIC_ERROR',
                    'description': reason[:100] if reason else '논리 오류',
                    'severity': 'HIGH',
                    'suggestion': 'Analyst의 Arc 설계 재검토 필요. 설정 충돌 또는 인과 오류 수정.'
                })
            elif error_category == 'QUALITY_ISSUE' and not action_items:
                action_items.append({
                    'type': 'QUALITY_ISSUE',
                    'description': reason[:100] if reason else '품질 미달',
                    'severity': 'MEDIUM',
                    'suggestion': 'Writer가 직접 수정 가능. 밀도 높이고 묘사 추가.'
                })

        audit_result['action_items'] = action_items

        # [V60.5] score_breakdown 분석 및 단계별 피드백 생성
        score_breakdown = audit_result.get('score_breakdown', {})
        if score_breakdown and audit_result.get('decision') == 'REJECT':
            breakdown_feedback = self._analyze_score_breakdown(score_breakdown)
            if breakdown_feedback:
                audit_result['breakdown_feedback'] = breakdown_feedback
                # action_items에 단계별 감점 정보 추가
                for area, info in breakdown_feedback.items():
                    if info.get('severity') in ['CRITICAL', 'HIGH']:
                        action_items.append({
                            'type': 'SCORE_BREAKDOWN',
                            'description': f"{info['name']}: {info['score']}/{info['max']}점",
                            'severity': info['severity'],
                            'suggestion': info['suggestion']
                        })

        # 책임 소재 명시
        if error_category == 'LOGIC_ERROR':
            audit_result['responsibility'] = 'ANALYST'  # Arc 재설계 필요
            audit_result['responsibility_guide'] = 'Analyst의 Arc 설계에 문제 있음. 재설계 검토.'
        else:
            audit_result['responsibility'] = 'WRITER'  # 재작성으로 해결 가능
            audit_result['responsibility_guide'] = 'Writer가 재작성으로 해결 가능.'

        # [V60.6] REJECT 사유 정량화
        if audit_result.get('decision') == 'REJECT' and stage == 4:
            quantified = self._quantify_reject_feedback(
                reason=reason,
                content_length=content_length,
                audit_result=audit_result
            )
            if quantified:
                audit_result['quantified_feedback'] = quantified
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
            'setting_consistency': {
                'name': '설정 일관성',
                'max': 25,
                'thresholds': {'critical': 0, 'high': 15, 'medium': 20},
                'suggestions': {
                    'critical': '미습득 무공 사용, 죽은 인물 등장, 물리적 인과 붕괴 확인. Hard Constraint 위반 수정 필수.',
                    'high': '보조 NPC 이름, 장소명 등 경미한 설정 확인. 직전 원고와 대조.',
                    'medium': '세부 설정 일관성 점검. 무기, 의복, 시간대 확인.'
                }
            },
            'scene_composition': {
                'name': '장면 구성',
                'max': 25,
                'thresholds': {'critical': 10, 'high': 15, 'medium': 20},
                'suggestions': {
                    'critical': '씬 수가 부족함. Blueprint의 6개 씬을 모두 균등하게 반영하라.',
                    'high': '일부 씬이 누락되거나 요약됨. 후반부 씬 밀도를 높여라.',
                    'medium': '씬간 밀도 불균형. 전반부와 후반부 분량을 균등하게 배분하라.'
                }
            },
            'narrative_flow': {
                'name': '서사 흐름',
                'max': 20,
                'thresholds': {'critical': 0, 'high': 10, 'medium': 15},
                'suggestions': {
                    'critical': '서사 폭주 또는 정체 감지됨. 사건 속도를 조절하고 인과적 전진을 확보하라.',
                    'high': '약간의 반복 또는 급전개. 장면간 연결을 자연스럽게 다듬어라.',
                    'medium': '추진력 부족. 다음 화로 이어지는 긴장감을 추가하라.'
                }
            },
            'length_fulfillment': {
                'name': '분량 충족',
                'max': 15,
                'thresholds': {'critical': 0, 'high': 8, 'medium': 12},
                'suggestions': {
                    'critical': '4,000자 미만으로 절대 부족. 심리 묘사, 조연 리액션, 환경 묘사로 보충하라.',
                    'high': '4,000~4,500자로 위험 영역. 500자 이상 추가 필요.',
                    'medium': '4,500~5,000자로 안전 영역이나 5,000자 이상 권장.'
                }
            },
            'prose_quality': {
                'name': '문체 품질',
                'max': 15,
                'thresholds': {'critical': 0, 'high': 5, 'medium': 10},
                'suggestions': {
                    'critical': '가독성 심각하게 떨어짐. 문장 구조를 다듬고 리듬감을 살려라.',
                    'high': '건조한 문체. 감각 묘사, 비유, 대화의 생동감을 추가하라.',
                    'medium': '가독성은 양호하나 몰입감 부족. 독자 경험 향상 필요.'
                }
            }
        }

        result = {}
        for area, config in area_config.items():
            score = breakdown.get(area, config['max'])  # 없으면 만점으로 간주

            # 심각도 판단
            if score <= config['thresholds']['critical']:
                severity = 'CRITICAL'
            elif score <= config['thresholds']['high']:
                severity = 'HIGH'
            elif score <= config['thresholds']['medium']:
                severity = 'MEDIUM'
            else:
                severity = 'OK'

            if severity != 'OK':
                result[area] = {
                    'name': config['name'],
                    'score': score,
                    'max': config['max'],
                    'severity': severity,
                    'suggestion': config['suggestions'].get(severity.lower(), '')
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
        base_keywords = ['서사 폭주', '서사 정체', '모순', '동선 충돌', '시간 역행', '중복', 'CRITICAL']

        if not V50_MODULES_AVAILABLE or not self.failure_learner:
            return base_keywords

        try:
            # FailureLearner에서 고빈도 카테고리 추출
            category_counts = {}
            for record in self.failure_learner.records:
                cat = record.category.value if hasattr(record.category, 'value') else str(record.category)
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # 3회 이상 발생한 카테고리를 critical로 추가
            high_freq_keywords = []
            category_to_keyword = {
                'item_duplicate': '중복 획득',
                'item_missing': '미획득 사용',
                'state_discontinuity': '상태 불연속',
                'timeline_error': '타임라인',
                'scope_overflow': '범위 초과',
                'relationship_jump': '관계 급변',
                'villain_stupidity': '악역 지능',
                'free_powerup': '공짜 파워업'
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
        target_len: int = 5000
    ) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.generate_writer_guidance_v60_8(blueprint, prev_manuscript, episode_bibles, cliche_check_result, target_len)

    def _generate_structured_arc_feedback(self, continuity_result: dict, prev_arcs: list = None, arc_no: int = 1) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_structured_arc_feedback(continuity_result, prev_arcs, arc_no)

    def _generate_reverse_feedback_stage4_to_3(self, writer_reject_reason: str, pre_checklist_result: dict = None) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_reverse_feedback_stage4_to_3(writer_reject_reason, pre_checklist_result)

    def _generate_reverse_feedback_stage3_to_2(self, architect_failures: list = None, arc_no: int = 1) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.generate_reverse_feedback_stage3_to_2(architect_failures, arc_no)

    def _generate_arc_context_v60(
        self,
        all_refined_arcs: list,
        current_arc_no: int = None
    ) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.generate_arc_context_v60(all_refined_arcs, current_arc_no)

    def _get_adaptive_feedback_intensity(self, retry_count: int, stage: int = 4) -> dict:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.get_adaptive_feedback_intensity(retry_count, stage)

    def _analyze_rejection_pattern_v60(
        self,
        rejection_history: list,
        current_arc_no: int
    ) -> str:
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
        specific_issues = []

        for reject in rejection_history:
            reason = reject.get('reason', 'unknown')
            # 사유 정규화
            normalized = self._normalize_rejection_reason(reason)
            reason_counts[normalized] = reason_counts.get(normalized, 0) + 1
            # 구체적 이슈 수집
            if reject.get('specific_issue'):
                specific_issues.append(reject['specific_issue'])

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
            ""
        ]

        for reason, count in top_reasons:
            lines.append(f"   🔴 {reason}: {count}회")
            # 패턴별 수정 가이드
            guide = self._get_rejection_fix_guide(reason)
            if guide:
                lines.append(f"      💡 수정 방향: {guide}")

        if specific_issues:
            lines.append("")
            lines.append("📋 구체적 문제 지점:")
            for issue in specific_issues[:3]:  # 최대 3개
                lines.append(f"   - {issue[:100]}...")

        lines.extend([
            "",
            "=" * 60,
            ""
        ])

        return "\n".join(lines)

    def _normalize_rejection_reason(self, reason: str) -> str:
        """REJECT 사유 정규화"""
        reason_lower = reason.lower()

        if "중복" in reason or "duplicate" in reason_lower:
            return "아이템 중복 획득"
        if "수여" in reason or "grant" in reason_lower:
            return "수여물 타임라인 오류"
        if "부상" in reason or "injury" in reason_lower or "회복" in reason:
            return "부상/회복 연속성 오류"
        if "위치" in reason or "location" in reason_lower:
            return "위치 연속성 오류"
        if "소지" in reason or "inventory" in reason_lower:
            return "소지품 연속성 오류"
        if "내공" in reason or "energy" in reason_lower:
            return "내공 상태 연속성 오류"
        if "json" in reason_lower or "parsing" in reason_lower:
            return "JSON 파싱 오류"
        if "길이" in reason or "length" in reason_lower:
            return "분량 부족"
        if "범위" in reason or "scope" in reason_lower:
            return "범위 초과/미달"

        return "기타"

    def _get_rejection_fix_guide(self, normalized_reason: str) -> str:
        """정규화된 REJECT 사유에 대한 수정 가이드"""
        guides = {
            "아이템 중복 획득": "이전 Arc에서 획득한 아이템 목록을 확인하고, 새 아이템만 설계하세요.",
            "수여물 타임라인 오류": "수여 시점 이전에 해당 수여물을 언급하지 마세요. 수여 장면을 먼저 작성하세요.",
            "부상/회복 연속성 오류": "직전 Arc 종료 시 부상 상태를 확인하고, 회복 장면 없이 멀쩡해지지 마세요.",
            "위치 연속성 오류": "직전 Arc 종료 위치에서 시작하고, 이동 경로를 명시하세요.",
            "소지품 연속성 오류": "직전 Arc 종료 시 소지품 그대로 시작하고, 새 획득은 명확히 구분하세요.",
            "내공 상태 연속성 오류": "내공 소모/회복을 누적 추적하고, 급격한 변화를 피하세요.",
            "JSON 파싱 오류": "출력이 순수 JSON인지 확인하세요. 설명문이나 마크다운을 포함하지 마세요.",
            "분량 부족": "각 화당 최소 800자 이상 작성하세요.",
            "범위 초과/미달": "할당된 화수 범위를 정확히 지키세요."
        }
        return guides.get(normalized_reason, "")

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
            genre_type = 'wuxia'
            if self.selected_genre:
                genre_type = self.selected_genre.get('type', 'wuxia')

            self.diversity_engine = NarrativeDiversityEngine(
                context=self.current_project,
                genre=genre_type,
                window_size=window_size
            )

            # 최근 에피소드 분석
            report = self.diversity_engine.analyze_recent_episodes(window_size)

            if report and report.get('status') == 'analyzed':
                high_count = report.get('high_severity_count', 0)
                if high_count > 0:
                    self.ui.log(f"📊 [V48 DiversityEngine] 패턴 분석 완료 - HIGH 경고 {high_count}개 감지")
                else:
                    self.ui.log(f"📊 [V48 DiversityEngine] 패턴 분석 완료 - 반복 수준 양호")

                self._audit_event("diversity_engine_init", "NarrativeDiversityEngine initialized", {
                    "genre": genre_type,
                    "window_size": window_size,
                    "high_severity_count": high_count
                })
            else:
                self.ui.log(f"📊 [V48 DiversityEngine] 초기화 완료 (분석 데이터 부족)")

            return True

        except Exception as e:
            self.ui.log(f"{Emojis.WARNING} [DiversityEngine] 초기화 실패: {e}")
            self._audit_event("diversity_engine_error", "init failed", {"error": str(e)})
            self.diversity_engine = None
            return False

    def boot(self):
        self.ui.title("V40 SOVEREIGN COCKPIT", "Multi-Genre Production Factory")
        
        # [V40] 장르 선택 우선
        self.selected_genre = self._select_genre()
        
        project_name = self._select_project()

        # [V60.37] 프로젝트별 .env 로드 지원
        project_env_path = Path("projects") / project_name / ".env"
        if project_env_path.exists():
            load_dotenv(project_env_path, override=True)
            print(f"   🔑 [V60.37] 프로젝트별 API 키 로드: {project_env_path}")
            # API 클라이언트 재초기화
            new_api_key = os.getenv("GOOGLE_API_KEY")
            if new_api_key:
                self.sys = StudioSystem(api_client=genai.Client(api_key=new_api_key))
                # [V61.9] 프로젝트별 멀티키 재초기화 (GOOGLE_API_KEY_2~9 반영)
                from modules.domain.agents.base_agent import BaseAgent
                BaseAgent._keys_initialized = False
                BaseAgent._current_key_idx = 0
                BaseAgent._context_caches.clear()
                BaseAgent._init_api_keys()

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
        from modules.core.genre_hud_manager import create_hud_manager, log_hud_compatibility_report
        self.sys.hud = create_hud_manager(self.selected_genre['type'], self.current_project)
        self.ui.log(f"   ✅ [{self.selected_genre['name']}] HUD 시스템 초기화 완료")

        # [V61.3] HUD 호환성 체크 (에러 사전 감지)
        log_hud_compatibility_report(self.sys.hud, logger=self.ui.log)

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
        # [V63.3] BlueprintMemory 초기화 (Stage 3 시맨틱 검색용)
        self.blueprint_memory = None
        try:
            from modules.core.blueprint_memory import BlueprintMemory
            self.blueprint_memory = BlueprintMemory(self.current_project)
        except Exception as _bm_err:
            self.ui.log(f"   ⚠️ [V63.3] BlueprintMemory 초기화 실패 (비차단): {str(_bm_err)[:60]}")

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

        # [V65] (B) Architect 캐시 삭제 (레거시 에이전트 제거)

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
                        model=fix_model_id(config.get("weaver", config.get("manager", _V50_MODULE_MODEL))),
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
                # [V65] architect 캐시 항목 삭제
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
            # [V65] Architect 캐시 주입 삭제
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
            is_current = self.current_project.treatment_path == f  # [V64.P4] __init__에서 선언됨
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
            with open(treat_path, 'r', encoding='utf-8') as f:
                treatment_blocks = json.load(f)

            if not treatment_blocks or len(treatment_blocks) < 2:
                self.ui.log("⚠️ Treatment 블록이 부족합니다.")
                return treatment_file

            # 2. BlockEnricher 초기화 (context, client, model_tier 순서로 전달)
            # [V60.24] Flash (농축용)
            enricher = BlockEnricher(self.current_project, self.sys.api_client, model_tier=_FLASH_ANALYSIS_MODEL)

            # 3. 각 Block 분석 및 농축 필요 여부 확인
            needs_enrichment = []
            for i, block in enumerate(treatment_blocks):
                analysis = enricher.analyze_block_density(block)
                if analysis["needs_enrichment"]:
                    needs_enrichment.append({
                        "index": i,
                        "block_id": block.get("block_id", f"Block {i+1}"),
                        "density_score": analysis["density_score"],
                        "missing": analysis["missing_elements"]
                    })

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
            if proceed == 'n':
                self.ui.log("⏭️ 농축을 건너뜁니다.")
                return treatment_file

            # 5. 주인공 이름 추출 (Bible에서) [V61.2 Fix] 장르별 HUD 탐색
            # 6. 장르 확인
            genre = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'

            protagonist_name = "주인공"
            try:
                bible_path = Path("bible")
                bible_files = list(bible_path.glob("*.json"))
                if bible_files:
                    with open(bible_files[0], 'r', encoding='utf-8') as f:
                        bible_data = json.load(f)
                    bible_root = bible_data.get('MasterBible', bible_data)
                    protagonist_name = HUDKeys.get_protagonist_name(bible_root, genre)
            except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:  # [V64.P4] IMPORTANT: protagonist name extraction
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
                ui=self.ui
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
                    clean_block["block_id"] = block.get("block_id", clean_block.get("block_id", f"Block {i+1}"))
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
            self.ui.log(f"   📊 농축 완료: {stats.get('enriched_count', 0)}개 성공, "
                       f"{stats.get('skipped_count', 0)}개 스킵, "
                       f"{stats.get('failed_count', 0)}개 실패")
            if causal_fixes > 0:
                self.ui.log(f"   🔧 인과 수정: {causal_fixes}개 Block 재농축됨")

            # 8. 농축된 Treatment 저장
            enriched_filename = treatment_file.replace('.json', '_enriched.json')
            enriched_path = Path("treatments") / enriched_filename

            with open(enriched_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_blocks, f, ensure_ascii=False, indent=2)

            self.ui.log(f"✅ 농축된 Treatment 저장 완료: {enriched_filename}")
            self.ui.log(f"   원본: {treatment_file} (보존)")
            self.ui.log(f"   농축본: {enriched_filename} (사용)")

            return enriched_filename

        except Exception as e:
            self.ui.log(f"🚨 [V60.10] 농축 실패: {e}")
            self._audit_event("block_enrichment_error", "treatment enrichment failed", {"error": str(e)[:200]})
            return treatment_file

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
            
            default_model = AIModels.STAGE2_MAIN_MODEL  # [V65] 중앙 상수 참조

            self.agents = {
                'analyst': Analyst(self.current_project, self.sys.api_client, model_tier=models.get("analyst", default_model)),
                # [V65] Architect 삭제 (ThreePhaseBlueprintGenerator로 완전 대체)
                'writer': Writer(self.current_project, self.sys.api_client, model_tier=models.get("writer", default_model)),
                'director': Director(self.current_project, self.sys.api_client, model_tier=models.get("director", default_model)),
                'manager': Manager(self.current_project, self.sys.api_client, model_tier=models.get("manager", default_model)),
                # [V45 Fix] weaver는 manager가 아닌 weaver 모델 사용 (fallback: manager)
                'weaver': Weaver(self.current_project, self.sys.api_client, model_tier=models.get("weaver", models.get("manager", default_model))),
                # [V48.1] ContinuityInspector - Director 산하 연속성 검증 에이전트
                'continuity_inspector': ContinuityInspector(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
                # [V52.2] Critic - 원고 비평 에이전트
                # [V60.78] 2.5-flash로 변경 (2.0 이하 미사용 정책)
                'critic': Critic(self.current_project, self.sys.api_client, model_tier=_SUMMARY_MODEL),
                # [V60.10] StateExtractor - 상태 추출 에이전트 (빠른 모델로 구조화된 상태 추출)
                'state_extractor': StateExtractor(self.current_project, self.sys.api_client, model_tier=_FLASH_ANALYSIS_MODEL),
                # [V60.11] ArcEnsembleGenerator - Arc 앙상블 생성기 (3개 후보 병렬 생성)
                'arc_ensemble': ArcEnsembleGenerator(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
                # [V60.12] FourPhaseArcGenerator - 4단계 Arc 생성 파이프라인 (초기 통과율 극대화)
                'four_phase': FourPhaseArcGenerator(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
                # [V60.14] StateLockedArcGenerator - 상태 잠금 Arc 생성기 (구조적 모순 불가)
                'state_locked': StateLockedArcGenerator(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
                # [V60.12] PreflightChecker - 생성 전 완벽 분석
                'preflight': PreflightChecker(self.current_project, self.sys.api_client, model_tier=_FLASH_ANALYSIS_MODEL),
                # [V60.12] ArcCritic - Arc 즉시 비평
                'arc_critic': ArcCritic(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
                # [V60.12] ConsensusValidator - 3-LLM 합의 검증
                'consensus': ConsensusValidator(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
                # [V60.80] ThreePhaseBlueprintGenerator - 3단계 Blueprint 파이프라인
                'three_phase_bp': ThreePhaseBlueprintGenerator(self.current_project, self.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL),
            }

            # [V60.11] Python 기반 헬퍼 초기화 (LLM 미사용)
            self.arc_draft_validator = ArcDraftValidator()
            self.constraint_compiler = ConstraintCompiler()
            # [V60.12] Negative Example Injector - 실패 사례 주입
            self.negative_injector = NegativeExampleInjector("wuxia")
            # [V60.42] Arc Corrector - MAJOR 이슈 부분 수정 (ON/OFF 토글 가능)
            self.arc_corrector = ArcCorrector(
                context=self.current_project,
                client=self.sys.api_client,
                model_tier=_FLASH_ANALYSIS_MODEL  # [V65] 경량 모델 상수
            )
            self.use_arc_corrector = True  # [V60.42] 기본 활성화 (False로 설정하면 비활성화)
            # [V60.25] Stage 2 Optimizer - 통과율 최적화
            self.stage2_optimizer = create_stage2_optimizer() if V50_MODULES_AVAILABLE else None
            self.ui.log(f"   🔧 [V60.11] Stage 2 고도화 모듈 초기화 (Ensemble + DraftValidator + ConstraintCompiler)")
            self.ui.log(f"   🚀 [V60.12] Stage 2 초기통과율 극대화 모듈 초기화 (FourPhase + Preflight + Critic + Consensus)")
            self.ui.log(f"   🔧 [V60.42] Arc Corrector 초기화 (MAJOR 이슈 부분 수정: {'활성화' if self.use_arc_corrector else '비활성화'})")
            if self.stage2_optimizer:
                self.ui.log(f"   ⚡ [V60.25] Stage 2 Optimizer 활성화 (StateSnapshot + AutoCorrector + ConstraintAmplifier)")

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

                # [V60.90] Director에 Guard 연결 (장르별 특화 검증용)
                if hasattr(self.sys, 'guard') and self.sys.guard:
                    self.agents['director'].set_guard(self.sys.guard)
                    self.ui.log(f"   🛡️ Director Guard 연결 완료")

                # [V60.90] Writer에 Guard/Genre 연결 (장르별 프롬프트 주입용)
                if 'writer' in self.agents:
                    if hasattr(self.agents['writer'], 'set_genre'):
                        self.agents['writer'].set_genre(genre_type)
                    if hasattr(self.agents['writer'], 'set_guard') and hasattr(self.sys, 'guard'):
                        self.agents['writer'].set_guard(self.sys.guard)
                    self.ui.log(f"   ✍️ Writer Guard/Genre 연결 완료")

            # V0128 검증 시스템 활성화 여부 확인
            # [V44 Fix] settings 변수 안전하게 로드
            # [V60 Fix] 프로젝트 config 없으면 루트 config로 fallback
            try:
                settings_path = self.current_project.paths.config / "settings.json"
                if not settings_path.exists():
                    # 프로젝트 설정 없으면 루트 config로 fallback
                    settings_path = Path("config/settings.json")

                if settings_path.exists():
                    import json
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                else:
                    settings = {}
            except (FileNotFoundError, json.JSONDecodeError, OSError):  # [V64.P4] OPTIONAL: settings load
                settings = {}

            validation_config = settings.get('validation', {})
            if validation_config.get('use_v0128', False):
                self.agents['director'].set_v0128_enabled(True)
                self.ui.log("   ✅ V0128 검증 시스템 활성화")

            # ═══════════════════════════════════════════════════════════════
            # [V49.7] ContinuityInspector 트래커 초기화
            # ═══════════════════════════════════════════════════════════════
            try:
                if 'continuity_inspector' in self.agents:
                    ci = self.agents['continuity_inspector']
                    if hasattr(ci, 'v49_7_enabled') and ci.v49_7_enabled:
                        # DB에서 Arc 데이터 로드하여 트래커 초기화
                        arcs_data = self.current_project.db.load_anchor("arcs") or []
                        if arcs_data:
                            load_result = ci.load_trackers_from_db(arcs_data)
                            self.ui.log(f"   🔧 [V49.7] 트래커 초기화 완료: "
                                       f"복선 {load_result.get('foreshadowings', 0)}개, "
                                       f"관계 {load_result.get('relationships', 0)}개, "
                                       f"파워 {load_result.get('power_entries', 0)}개")
                        else:
                            self.ui.log("   🔧 [V49.7] 트래커 대기 (Arc 데이터 없음)")
                    else:
                        self.ui.log("   ⚠️ [V49.7] 모듈 미설치 - 기본 검증 모드")
            except Exception as tracker_err:
                self.ui.log(f"   ⚠️ [V49.7] 트래커 초기화 실패 (비치명적): {tracker_err}")

            # ═══════════════════════════════════════════════════════════════
            # [V50] 서사 품질 향상 모듈 초기화
            # ═══════════════════════════════════════════════════════════════
            if V50_MODULES_AVAILABLE:
                try:
                    genre_type = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'

                    # [V65] V50.1~V51.1 초기화 삭제 (Dead Code 정리)

                    # [V65] V51.1 호흡 분석기 재연결
                    self.pacing_analyzer = PacingAnalyzer()

                    # V51.2 품질 증폭기
                    self.quality_amplifier = QualityAmplifier()

                    # V51.3 에이전트 지능 향상
                    self.agent_intelligence = AgentIntelligence(genre=genre_type)

                    # V51.4 실패 학습 시스템
                    self.failure_learner = FailureLearner()
                    # 프로젝트별 실패 기록 로드 시도
                    failure_log_path = os.path.join(
                        "projects", self.current_project.name, "logs", "failure_learning.json"
                    )
                    if os.path.exists(failure_log_path):
                        self.failure_learner.load_from_json(failure_log_path)
                        self.ui.log(f"   📚 [V51.4] 실패 기록 {len(self.failure_learner.records)}건 로드")

                    # V51.5 캐릭터 음성 추적
                    self.character_voice = CharacterVoiceTracker()
                    voice_log_path = os.path.join(
                        "projects", self.current_project.name, "logs", "character_voice.json"
                    )
                    if os.path.exists(voice_log_path):
                        self.character_voice.load_from_json(voice_log_path)
                        self.ui.log(f"   🎭 [V51.5] 캐릭터 음성 {len(self.character_voice.profiles)}명 로드")

                    # V51.6 복선 추적
                    self.foreshadow_tracker = ForeshadowTracker()
                    foreshadow_log_path = os.path.join(
                        "projects", self.current_project.name, "logs", "foreshadow.json"
                    )
                    if os.path.exists(foreshadow_log_path):
                        self.foreshadow_tracker.load_from_json(foreshadow_log_path)
                        stats = self.foreshadow_tracker.get_stats()
                        self.ui.log(f"   🔮 [V51.6] 복선 {stats['total']}개 로드 (활성: {stats['active']}, 회수율: {stats['payoff_rate']}%)")

                    # [V66] SemanticPlotGuard 활성화
                    try:
                        from modules.core.semantic_plot_guard import SemanticPlotGuard
                        self.semantic_plot_guard = SemanticPlotGuard(api_key=os.getenv("GOOGLE_API_KEY", ""))
                        self.ui.log(f"   📊 [V66] SemanticPlotGuard 초기화 완료")
                    except Exception:
                        self.semantic_plot_guard = None

                    # ============================================================
                    # [V60.26] 품질 향상 모듈 (미사용 → 활성화)
                    # ============================================================

                    # V60.26-1 감정선 추적
                    self.emotion_tracker = EmotionArcTracker(self.current_project)
                    emotion_log_path = os.path.join("projects", self.current_project.name, "logs", "emotion_arc.json")
                    if os.path.exists(emotion_log_path):
                        self.emotion_tracker.load_from_db(self.current_project.db)
                        self.ui.log(f"   💓 [V60.26] 감정선 추적기 로드 ({len(self.emotion_tracker.history)}개 기록)")
                    else:
                        self.ui.log(f"   💓 [V60.26] 감정선 추적기 활성화")

                    # V60.26-2 파워 스케일링 추적
                    self.power_scaling = PowerScalingTracker()
                    self.ui.log(f"   ⚡ [V60.26] 파워 스케일링 추적기 활성화")

                    # V60.26-3 상태 변화 추적
                    self.state_delta_tracker = StateDeltaTracker()
                    self.ui.log(f"   📊 [V60.26] 상태 변화 추적기 활성화")

                    # V60.26-4 의미적 아이템 레지스트리
                    self.semantic_item_registry = SemanticItemRegistry()
                    self.ui.log(f"   📦 [V60.26] 의미적 아이템 레지스트리 활성화")

                    # V60.26-5 캐릭터 음성 프로파일러 (V58, 기존 V51.5보다 고급)
                    self.voice_profiler = CharacterVoiceProfiler()
                    voice_profiler_path = os.path.join("projects", self.current_project.name, "logs", "voice_profiles.json")
                    if os.path.exists(voice_profiler_path):
                        try:
                            with open(voice_profiler_path, 'r', encoding='utf-8') as f:
                                profiles_data = json.load(f)
                                for name_key, profile_data in profiles_data.items():
                                    self.voice_profiler.add_profile(name_key, profile_data)
                            self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 로드 ({len(self.voice_profiler.profiles)}명)")
                        except (json.JSONDecodeError, KeyError, TypeError, OSError) as e:  # [V64.P4] OPTIONAL: voice profiler load
                            self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 활성화 (로드 실패: {str(e)[:40]})")
                    else:
                        self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 활성화")

                    # V52.1 자기 성찰 체인
                    self.self_reflector = SelfReflector(
                        api_client=self.sys.api_client,
                        model=_V50_MODULE_MODEL  # [V65] 중앙 상수
                    )
                    self.ui.log(f"   🔄 [V52.1] Self-Reflection Chain 활성화")

                    # V52.3 전문가 혼합
                    self.expert_mixture = ExpertMixture(genre=genre_type)
                    self.ui.log(f"   🎯 [V52.3] Expert Mixture 활성화 ({genre_type})")

                    # V52.4 교차 에이전트 검증
                    self.cross_verifier = CrossAgentVerifier(
                        api_client=self.sys.api_client,
                        model=_V50_MODULE_MODEL  # [V65] 중앙 상수
                    )
                    self.ui.log(f"   🔗 [V52.4] Cross-Agent Verifier 활성화")

                    # V53.1 동적 프롬프트 가중치
                    self.prompt_weighter = DynamicPromptWeighter(failure_learner=self.failure_learner)
                    self.ui.log(f"   ⚖️ [V53.1] Dynamic Prompt Weighter 활성화")

                    # V53.2 사실 검증 체인
                    self.chain_of_verification = ChainOfVerification(
                        api_client=self.sys.api_client,
                        model=_V50_MODULE_MODEL  # [V65] 중앙 상수
                    )
                    self.ui.log(f"   🔍 [V53.2] Chain-of-Verification 활성화")

                    # V53.3 신뢰도 보정
                    self.confidence_calibrator = ConfidenceCalibrator(
                        api_client=self.sys.api_client,
                        use_llm=False  # Python 휴리스틱만 (비용 0)
                    )
                    self.ui.log(f"   📊 [V53.3] Confidence Calibrator 활성화")

                    # V53.4 사전 체크리스트
                    self.pre_director_checklist = PreDirectorChecklist()
                    self.ui.log(f"   ✅ [V53.4] Pre-Director Checklist 활성화")

                    # V53.5 Tree of Thoughts
                    self.tree_of_thoughts = TreeOfThoughts(
                        api_client=self.sys.api_client,
                        model=AIModels.STAGE2_MAIN_MODEL  # [V65] 중앙 상수
                    )
                    self.ui.log(f"   🌳 [V53.5] Tree of Thoughts 활성화 (Gemini 3)")

                    # V53.6 적대적 자기 대결
                    self.adversarial_self_play = AdversarialSelfPlay(
                        api_client=self.sys.api_client,
                        model=_V50_MODULE_MODEL  # [V65] 중앙 상수
                    )
                    self.ui.log(f"   ⚔️ [V53.6] Adversarial Self-Play 활성화")

                    # V53.7 다중 에이전트 토론
                    self.multi_agent_deliberation = MultiAgentDeliberation(
                        api_client=self.sys.api_client,
                        model=_V50_MODULE_MODEL  # [V65] 중앙 상수
                    )
                    self.ui.log(f"   🗣️ [V53.7] Multi-Agent Deliberation 활성화")

                    # ============================================================
                    # [V54] 비용 절감 + 품질 향상 모듈
                    # ============================================================

                    # V54.1 의미론적 캐시
                    self.semantic_cache = SemanticCache(max_size=500)
                    self.ui.log(f"   💾 [V54.1] Semantic Cache 활성화")

                    # V54.2 컨텍스트 압축
                    self.context_compressor = ContextCompressor(
                        target_ratio=0.6,
                        max_field_length=2000
                    )
                    self.ui.log(f"   📦 [V54.2] Context Compressor 활성화")

                    # V54.3 적응형 재시도 관리자
                    self.adaptive_manager = get_adaptive_manager()
                    # [V54.3.1] FailureLearner 연동
                    if self.failure_learner:
                        self.adaptive_manager.connect_failure_learner(self.failure_learner)
                        self.ui.log(f"   🔄 [V54.3] Adaptive Retry Manager 활성화 (FailureLearner 연동)")
                    else:
                        self.ui.log(f"   🔄 [V54.3] Adaptive Retry Manager 활성화")

                    # [V65] TwoPhaseGenerator 삭제 (two_phase_ms/bp/arc — Dead Code)

                    # V54.5 성공 패턴 메모리
                    self.success_patterns = SuccessPatternMemory(
                        project_context=self.current_project,
                        max_patterns=100
                    )
                    self.ui.log(f"   🏆 [V54.5] Success Pattern Memory 활성화")

                    # V55 원고 품질/분량 향상
                    self.manuscript_enhancer = ManuscriptEnhancer(genre=genre_type)
                    self.ui.log(f"   ✨ [V55] Manuscript Enhancer 활성화 (7개 서브모듈)")

                    # V55.2 헌법적 자기검증
                    self.constitutional_checker = ConstitutionalChecker(genre=genre_type)
                    self.ui.log(f"   📜 [V55.2] Constitutional Checker 활성화")

                    # V55.3 원고 템플릿
                    self.writer_template = WriterTemplate(genre=genre_type)
                    self.ui.log(f"   📝 [V55.3] Writer Template 활성화")

                    # V55.3 통과율 모니터
                    project_path = str(self.current_project.paths.root) if self.current_project else "."
                    self.pass_rate_monitor = PassRateMonitor(project_path)
                    self.ui.log(f"   📊 [V55.3] Pass Rate Monitor 활성화")

                    # V60 품질 대시보드
                    from pathlib import Path
                    self.quality_dashboard = QualityDashboard(Path(project_path))
                    self.ui.log(f"   📊 [V60] Quality Dashboard 활성화")

                    self.ui.log(f"   📊 [V50~V60] 서사 품질 모듈 초기화 완료 (장르: {genre_type})")

                    # 기존 에피소드에서 데이터 로드
                    self._load_v50_history()

                except Exception as v50_err:
                    self.ui.log(f"   ⚠️ [V50] 모듈 초기화 실패 (비치명적): {v50_err}")
            else:
                self.ui.log("   ⚠️ [V50] 모듈 미설치 - 기본 모드")

            self.ui.log("✅ [System] 모든 에이전트 안전하게 초기화 완료")
            return True
            
        except Exception as e:
            self.ui.log(f"🚨 [Critical] 에이전트 초기화 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

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
            bible = self.current_project.db.load_anchor("bible") or {}
            bible_root = bible.get('MasterBible', bible)
            genre = self.selected_genre.get('type', '') if self.selected_genre else ''

            name = HUDKeys.get_protagonist_name(bible_root, genre)
            if name and name != '주인공':
                return name

            # 레거시 characters 리스트 폴백
            chars = bible.get('characters', bible.get('등장인물', []))
            if chars and isinstance(chars, list) and len(chars) > 0:
                first_char = chars[0]
                if isinstance(first_char, dict):
                    return first_char.get('name', first_char.get('이름', '주인공'))
                return str(first_char)

            return name  # '주인공' 기본값
        except Exception as e:
            print(f"      ⚠️ [V61.2] 주인공 이름 추출 실패: {e}")
            return '주인공'

    def _fix_entity_registry_protagonist(self, entity_registry: dict, protagonist_name: str = None) -> dict:
        """
        [V62.4] Entity Registry에서 주인공 이름을 락된 이름으로 보정

        StateExtractor LLM이 주인공 이름을 잘못 추출하거나,
        '주인공 제외' 지시에도 불구하고 빠뜨리는 경우 방지.
        주인공이 Registry에 없으면 Director가 비슷한 NPC 이름과 혼동하여 오탐 REJECT 발생.
        """
        if not entity_registry or not protagonist_name or protagonist_name == "주인공":
            return entity_registry

        chars = entity_registry.get('characters', [])
        protag_found = False
        for ch in chars:
            if isinstance(ch, dict) and ch.get('role') in ('주인공', 'protagonist', '주역'):
                if ch.get('name') != protagonist_name:
                    old_name = ch.get('name', '?')
                    ch['name'] = protagonist_name
                    print(f"      🔒 [V62.4] Entity Registry 주인공 보정: {old_name} → {protagonist_name}")
                protag_found = True
                break

        if not protag_found:
            chars.insert(0, {"name": protagonist_name, "role": "주인공", "context": "락 고정"})
            entity_registry['characters'] = chars

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
                genre_label = self.selected_genre['name']
                self.ui.title("V40 SOVEREIGN PRODUCTION", f"Genre: {genre_label} | Project: {self.current_project.name}")
                
                # 2. 상태 체크 (DB Anchors 기반의 무결성 확인)
                # 이 함수는 self.current_project.db의 'bible', 'volumes', 'arcs' 키를 체크해야 함
                status = self.sys.check_v20_readiness() 
                
                # 3. 메뉴 구성 (V41 유동 아크 + 스킵 옵션)
                vol_status = '✅' if status.get('Stage 1 (Volumes)', False) else '⏭️ 스킵가능'
                menu = {
                    "0": f"Stage 0: Bible/역설계/스타일 추출 [{'✅' if status.get('Stage 0 (Bible)', False) else '❌'}]",
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
                    # [V60.95] Stage 4 - Chief Writer 단일화 (V1 레거시 제거)
                    self._stage_4_v2_chief_writer(limit_mode=True)
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
        import sys
        print("\n🛑 [System] 시스템 종료 시퀀스 가동...", flush=True)
        sys.stdout.flush()

        # [V49.3] 비용 추적 리포트 출력 및 저장 (타임아웃 적용)
        # [V49.4 FIX] 전체 메트릭 처리에 타임아웃 적용 (get_metrics_collector뿐 아니라 리포트 생성/저장도)
        def _process_metrics():
            """메트릭 처리 전체를 별도 함수로 분리"""
            collector = get_metrics_collector()
            if collector:
                report = collector.get_summary_report()
                print("\n" + report, flush=True)
                saved_path = collector.save_metrics()
                print(f"📊 [Metrics] 세션 메트릭 저장: {saved_path}", flush=True)

        try:
            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(_process_metrics)
                try:
                    future.result(timeout=5)  # 전체 메트릭 처리에 5초 타임아웃
                except concurrent.futures.TimeoutError:
                    print("⚠️ [Metrics] 메트릭 처리 타임아웃 (건너뜀)", flush=True)
            finally:
                executor.shutdown(wait=False)  # 타임아웃 시 즉시 진행, 스레드 대기 안 함
        except Exception as metrics_err:
            print(f"⚠️ [Metrics] 비용 추적 리포트 생성 실패: {metrics_err}", flush=True)

        # [V51.4] 실패 학습 기록 저장
        if V50_MODULES_AVAILABLE and self.failure_learner and self.current_project:
            try:
                logs_dir = os.path.join("projects", self.current_project.name, "logs")
                os.makedirs(logs_dir, exist_ok=True)
                failure_log_path = os.path.join(logs_dir, "failure_learning.json")
                self.failure_learner.save_to_json(failure_log_path)
                stats = self.failure_learner.get_failure_stats()
                print(f"📚 [V51.4] 실패 학습 기록 저장: {stats['total_failures']}건", flush=True)
            except Exception as fl_err:
                print(f"⚠️ [V51.4] 실패 기록 저장 실패: {fl_err}", flush=True)

        # [V51.5] 캐릭터 음성 프로필 저장
        if V50_MODULES_AVAILABLE and self.character_voice and self.current_project:
            try:
                logs_dir = os.path.join("projects", self.current_project.name, "logs")
                os.makedirs(logs_dir, exist_ok=True)
                voice_log_path = os.path.join(logs_dir, "character_voice.json")
                self.character_voice.save_to_json(voice_log_path)
                print(f"🎭 [V51.5] 캐릭터 음성 저장: {len(self.character_voice.profiles)}명", flush=True)
            except Exception as cv_err:
                print(f"⚠️ [V51.5] 캐릭터 음성 저장 실패: {cv_err}", flush=True)

        # [V51.6] 복선 추적 저장
        if V50_MODULES_AVAILABLE and self.foreshadow_tracker and self.current_project:
            try:
                logs_dir = os.path.join("projects", self.current_project.name, "logs")
                os.makedirs(logs_dir, exist_ok=True)
                foreshadow_log_path = os.path.join(logs_dir, "foreshadow.json")
                self.foreshadow_tracker.save_to_json(foreshadow_log_path)
                stats = self.foreshadow_tracker.get_stats()
                print(f"🔮 [V51.6] 복선 저장: {stats['total']}개 (회수율: {stats['payoff_rate']}%)", flush=True)
            except Exception as fs_err:
                print(f"⚠️ [V51.6] 복선 저장 실패: {fs_err}", flush=True)

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
                    print(f"종료 중 DB 커밋 오류: {e}", flush=True)
                finally:
                    try:
                        db_conn.close()
                        self.ui.log("[System] DB 연결 안전하게 해제됨")
                    except Exception as close_err:
                        print(f"DB close 오류: {close_err}", flush=True)

        print("✅ [System] 종료 완료", flush=True)
            
    def _phase_0_recovery(self):
        print("\n⚙️ Phase 0: S-Grade 데이터 주권 동기화 가동...")

        # [V40] 장르 정보 표시
        if self.selected_genre:
            print(f"📌 현재 장르: {self.selected_genre['name']} ({self.selected_genre['type']})")

        # [V60.95] Stage 0 서브메뉴
        print("\n" + "=" * 50)
        print("  📚 Stage 0 - 프로젝트 설정")
        print("=" * 50)
        print("\n  [1] 기존 방식 - Bible/Treatment 파일 선택")
        if STAGE0_AVAILABLE:
            print("  [2] 🆕 컨셉 → Bible 생성 (AI 확장)")
            print("  [3] 🔄 역설계 - 기존 원고에서 Bible/스타일 추출")
            print("  [4] 📥 Bible JSON 임포트")
            print("  [5] 📈 Block 확장 - 기존 Treatment에 블록 추가")
        print("\n  [0] 취소")

        p0_choice = input("\n  선택 (기본: 1): ").strip()

        if p0_choice == "0":
            print("❌ Stage 0이 취소되었습니다.")
            return
        elif p0_choice == "2" and STAGE0_AVAILABLE:
            self._stage_0_extended(mode=1)  # 컨셉 → Bible
            return
        elif p0_choice == "3" and STAGE0_AVAILABLE:
            self._stage_0_extended(mode=2)  # 역설계
            return
        elif p0_choice == "4" and STAGE0_AVAILABLE:
            self._stage_0_extended(mode=3)  # Bible 임포트
            return
        elif p0_choice == "5" and STAGE0_AVAILABLE:
            self._stage_0_extended(mode=4)  # Block 확장
            return

        # 기존 방식 계속...
        # 1. 파일 선택 (Bible & Treatment)
        bible_file = self._ui_select_bible()
        treatment_file = self._ui_select_treatment()

        if not bible_file or not treatment_file:
            print("❌ 파일 선택이 취소되어 중단합니다.")
            return

        # 1.5. [V60.10] Treatment Block 농축 옵션
        enrich_choice = input("   🔧 [V60.10] Treatment Block 자동 농축을 수행하시겠습니까? (y/N): ").strip().lower()
        if enrich_choice == 'y':
            treatment_file = self._enrich_treatment_blocks(treatment_file)

        # ============================================================
        # [V60.87] 주인공 유형 설정 (Bible에 저장)
        # ============================================================
        print("\n📌 [V60.87] 주인공 기본 설정")

        # 1) 세계관 출신 (현대인/원시인)
        print("   🌍 주인공의 세계관 출신을 선택하세요:")
        print("      [1] 원시인 - 현대 지식/용어 사용 제한 (권장: 무협/판타지)")
        print("      [2] 현대인 - 제약 없음 (권장: 회귀/빙의물)")
        world_choice = input("   선택 (기본: 1): ").strip()
        world_origin = "현대인" if world_choice == "2" else "원시인"

        # 2) 주인공 유형 (빙의자/회귀자/환생자/기타)
        print("   🎭 주인공의 유형을 선택하세요:")
        print("      [1] 회귀자 - 먼 미래에서 과거로 회귀 (기억 보존)")
        print("      [2] 빙의자 - 다른 사람의 몸에 빙의")
        print("      [3] 환생자 - 아기로 다시 태어남")
        print("      [4] 기타 - 특별한 유형 없음")
        type_choice = input("   선택 (기본: 1): ").strip()
        incarnation_types = {"1": "회귀자", "2": "빙의자", "3": "환생자", "4": "기타"}
        incarnation_type = incarnation_types.get(type_choice, "회귀자")

        protagonist_config = {
            "world_origin": world_origin,
            "incarnation_type": incarnation_type
        }
        print(f"   ✅ 설정 완료: {world_origin} / {incarnation_type}")

        # ============================================================
        # [TODO V60.88+] 주인공 유형에 따른 장르 가드 세분화
        # - world_origin == "원시인": 현대어 Guard 강화 (WuxiaGuard 강화 모드)
        # - incarnation_type == "빙의자": 원래 인물의 기억/관계 충돌 검사
        # - incarnation_type == "회귀자": 미래 지식 사용 타당성 검사
        # - incarnation_type == "환생자": 성장 단계별 지식 제한
        # ============================================================

        # 2. [필수] 50개 설계도 DNA 강제 이식 (원고 유무 상관없이 무조건 수행)
        # 이 함수가 실행되면 AI를 안 거치고 50개 블록이 DB에 100% 들어갑니다.
        dna_success = self.current_project.force_sync_v25_dna(bible_file, treatment_file)

        if dna_success:
            # 2.5 [V60.87] 주인공 설정을 Bible에 주입
            try:
                master_bible = self.current_project.master_bible or {}
                bible_root = master_bible.get('MasterBible', master_bible)
                bible_root['protagonist_config'] = protagonist_config
                self.current_project.master_bible = {'MasterBible': bible_root}
                self.current_project.save_v20_anchor('bible', self.current_project.master_bible)
                print(f"   💾 [V60.87] 주인공 설정이 Bible에 저장됨: {protagonist_config}")
            except Exception as pc_err:
                print(f"   ⚠️ [V60.87] 주인공 설정 저장 실패 (비차단): {pc_err}")

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

    def _stage_0_extended(self, mode: int = 0):
        """
        [V60.95] Stage 0 확장 기능
        - 컨셉 입력 → Bible/Treatment 생성 (mode=1)
        - 역설계 → 기존 원고에서 설정 추출 (mode=2)
        - Bible 임포트 → 기존 JSON 불러오기 (mode=3)
        - Block 확장 → 기존 Treatment에 블록 추가 (mode=4)
        - mode=0: 메뉴 표시
        """
        if not STAGE0_AVAILABLE:
            print("❌ Stage 0 모듈이 로드되지 않았습니다.")
            return

        # StageZeroManager 초기화
        project_path = str(self.current_project.paths.root) if self.current_project else None
        stage0_manager = StageZeroManager(project_path=project_path)

        # 장르 정보 전달 (선택된 장르가 있으면)
        if self.selected_genre:
            genre_type = self.selected_genre.get('type', '')
            if genre_type:
                stage0_manager.genre = genre_type.lower()
                stage0_manager.preset_registry = PresetRegistry(base_genre=genre_type.lower())

        # Stage 0 메뉴 표시 (mode=0일 때만)
        if mode == 0:
            choice = stage0_manager.show_menu(is_new_project=True)
        else:
            choice = mode  # 직접 모드 지정

        bible = None
        treatment = None

        if choice == 1:
            # 컨셉 입력 → Bible/Treatment 생성
            bible, treatment, _ = stage0_manager.run_new_project_flow()
        elif choice == 2:
            # 역설계
            bible, episode_bibles, style_guide = stage0_manager.run_reverse_engineering_flow()
            if style_guide:
                print(f"\n📝 스타일 가이드 추출 완료:")
                print(f"   - 톤: {style_guide.tone}")
                print(f"   - 시점: {style_guide.pov}")
                print(f"   - 대화 비율: {style_guide.dialogue_ratio:.0%}")

            # [V60.95] 원고 벡터화 (ChromaDB)
            try:
                from modules.core.stage0 import ReverseExpander
                # stage0_manager 내부의 ReverseExpander 접근 또는 새로 생성
                if hasattr(stage0_manager, '_reverse_expander') and stage0_manager._reverse_expander:
                    vectorize_result = stage0_manager._reverse_expander.persist_to_chromadb(self.current_project)
                    if vectorize_result > 0:
                        print(f"✅ [V60.95] ChromaDB 벡터화 완료: {vectorize_result}개 에피소드")
            except Exception as ve:
                print(f"⚠️ [V60.95] 벡터화 스킵: {str(ve)[:50]}")

            # [V61] SQLite DB 저장 (manuscripts, blueprints stub, arcs stub)
            try:
                if hasattr(stage0_manager, '_reverse_expander') and stage0_manager._reverse_expander:
                    db_result = stage0_manager._reverse_expander.persist_to_db(self.current_project)
                    if db_result:
                        print(f"✅ [V61] DB 저장 완료:")
                        print(f"   - Manuscripts: {db_result.get('manuscripts', 0)}개")
                        print(f"   - State Logs (HUD): {db_result.get('state_logs', 0)}개")
                        print(f"   - Episode Bibles: {db_result.get('episode_bibles', 0)}개")
                        print(f"   - Blueprint stubs: {db_result.get('blueprints', 0)}개")
                        print(f"   - Arc stubs: {db_result.get('arcs', 0)}개")

                    # Stub 요약 정보
                    summary = stage0_manager._reverse_expander.get_stub_summary()
                    if summary:
                        print(f"\n📊 역설계 요약:")
                        print(f"   - 처리된 에피소드: {summary.get('ep_range', 'N/A')} ({summary.get('episodes', 0)}개)")
                        print(f"   - Arc stubs: {summary.get('arc_stub_range', 'N/A')}")
                        print(f"\n🎯 다음 생성 시작점:")
                        print(f"   - Stage 2 (Arc): Arc {summary.get('next_arc', 'N/A')}부터")
                        print(f"   - Stage 3 (Blueprint): ep {summary.get('next_blueprint', 'N/A')}부터")
                        print(f"   - Stage 4 (Manuscript): ep {summary.get('next_episode', 'N/A')}부터")
            except Exception as db_err:
                print(f"⚠️ [V61] DB 저장 스킵: {str(db_err)[:50]}")
        elif choice == 3:
            # Bible 임포트
            bible = stage0_manager.import_bible()
        elif choice == 4:
            # Block 확장
            treatment = self._extend_blocks(stage0_manager)
            if treatment:
                # 1. 확장된 Treatment 파일 저장
                try:
                    treatment_path = self.current_project.paths.root / "treatment_extended.json"
                    with open(treatment_path, 'w', encoding='utf-8') as f:
                        json.dump({"treatments": treatment}, f, ensure_ascii=False, indent=2)
                    print(f"✅ 확장된 Treatment 저장: {treatment_path}")
                    print(f"   총 {len(treatment)} 블록")
                except Exception as e:
                    print(f"❌ Treatment 저장 실패: {e}")

                # 2. [V61] Treatment → plot_roadmap 변환 후 Master Bible에 주입
                try:
                    # [V62.2] plot_roadmap flat 구조 변환 (중복 래핑 제거)
                    refined_roadmap = []
                    for i, block in enumerate(treatment):
                        entry = {"block_no": i + 1}
                        entry.update(block)
                        refined_roadmap.append(entry)

                    # Master Bible 로드
                    master_bible = self.current_project.master_bible or {}
                    bible_root = master_bible.get('MasterBible', master_bible)

                    # plot_roadmap 주입
                    bible_root['plot_roadmap'] = refined_roadmap
                    self.current_project.master_bible = {'MasterBible': bible_root}

                    # DB anchor 저장
                    self.current_project.save_v20_anchor('bible', self.current_project.master_bible)
                    self.current_project._load_from_db()

                    print(f"✅ [V61] plot_roadmap 주입 완료: {len(refined_roadmap)} 블록 → Master Bible")
                    print(f"   이제 Stage 2 (Arc 생성)를 진행할 수 있습니다.")

                except Exception as pr_err:
                    print(f"❌ plot_roadmap 주입 실패: {pr_err}")
                    import traceback
                    traceback.print_exc()

            input("\n[Enter] 메뉴로 돌아가기")
            return
        else:
            print("❌ Stage 0 확장이 취소되었습니다.")
            return

        # 결과물이 있으면 DB에 저장
        if bible:
            try:
                # Bible을 프로젝트에 저장
                self.current_project.master_bible = bible
                self.current_project.save_v20_anchor('bible', bible)
                print("✅ Bible이 DB에 저장되었습니다.")

                # 주인공 설정 추출
                master = bible.get('MasterBible', bible)
                protagonist_config = master.get('protagonist_config', {})
                if protagonist_config:
                    print(f"   💾 주인공 설정: {protagonist_config}")

                # Preset 상태 저장 + SovereignApp에 보관
                if stage0_manager.preset_registry:
                    self.preset_registry = stage0_manager.preset_registry  # [V60.95] 앱 레벨 보관
                    preset_state = stage0_manager.preset_registry.to_json()
                    self.current_project.save_v20_anchor('preset_state', json.loads(preset_state))
                    print(f"   📦 프리셋 상태 저장: {list(stage0_manager.preset_registry.active_presets)}")

                # 스타일 가이드 저장 (있으면)
                if stage0_manager.style_guide:
                    self.current_project.save_v20_anchor('style_guide', stage0_manager.style_guide.to_dict())
                    print("   🎨 스타일 가이드 저장 완료")

            except Exception as e:
                print(f"❌ 저장 중 오류: {e}")

        # Treatment가 있으면 Treatment 파일 생성
        if treatment:
            try:
                treatment_path = self.current_project.paths.root / "treatment_generated.json"
                with open(treatment_path, 'w', encoding='utf-8') as f:
                    json.dump({"treatments": treatment}, f, ensure_ascii=False, indent=2)
                print(f"✅ Treatment 저장: {treatment_path}")
            except Exception as e:
                print(f"❌ Treatment 저장 실패: {e}")

        # 데이터 리로드
        if bible:
            self.current_project._load_from_db()
            print("✨ [Stage 0 Complete] 프로젝트 설정이 완료되었습니다.")

        input("\n[Enter] 메뉴로 돌아가기")

    def _extend_blocks(self, stage0_manager) -> List[Dict[str, Any]]:
        """
        [V61] Block 확장 기능
        기존 Treatment에 블록을 추가
        """
        print("\n" + "=" * 50)
        print("  📈 Block 확장 - 기존 Treatment에 블록 추가")
        print("=" * 50)

        # 1. 기존 Treatment 로드
        existing_treatment = []
        treatment_files = [
            self.current_project.paths.root / "treatment_extended.json",
            self.current_project.paths.root / "treatment_generated.json",
            self.current_project.paths.root / "treatment.json",
        ]

        for tf in treatment_files:
            if tf.exists():
                try:
                    with open(tf, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        existing_treatment = data.get("treatments", [])
                        if existing_treatment:
                            print(f"   📂 기존 Treatment 로드: {tf.name} ({len(existing_treatment)} 블록)")
                            break
                except Exception as e:
                    print(f"   ⚠️ 파일 로드 실패: {tf.name} - {e}")

        if not existing_treatment:
            print("   ❌ 기존 Treatment를 찾을 수 없습니다.")
            print("   먼저 [2] 컨셉 → Bible 생성 또는 [3] 역설계를 실행하세요.")
            return []

        # 2. 확장 설정
        print(f"\n   현재 블록 수: {len(existing_treatment)}")
        print(f"   마지막 블록: {existing_treatment[-1].get('block_id', 'N/A')} - {existing_treatment[-1].get('title', 'N/A')}")

        try:
            extend_count = int(input("\n   추가할 블록 수 (기본: 10): ").strip() or "10")
        except ValueError:
            extend_count = 10

        direction_hint = input("   방향 힌트 (예: '클라이맥스로', '새 빌런 등장', 생략 가능): ").strip()

        # 3. 배치별 확인 콜백
        def confirm_batch(batch):
            print(f"\n   --- 생성된 블록 ({len(batch)}개) ---")
            for b in batch[:3]:  # 미리보기 3개
                print(f"   • {b.get('block_id', 'N/A')}: {b.get('title', 'N/A')}")
            if len(batch) > 3:
                print(f"   ... 외 {len(batch) - 3}개")

            confirm = input("   계속 진행하시겠습니까? (Y/n): ").strip().lower()
            return confirm != 'n'

        # 4. StoryExpander 사용하여 확장
        try:
            from modules.core.stage0.story_expander import StoryExpander
            expander = StoryExpander(genre=stage0_manager.genre)

            print(f"\n   🔄 Block {len(existing_treatment)+1}부터 {extend_count}개 생성 시작...")

            extended_treatment = expander.extend_treatment(
                existing_treatment=existing_treatment,
                extend_count=extend_count,
                direction_hint=direction_hint,
                batch_size=10,
                confirm_callback=confirm_batch
            )

            print(f"\n   ✅ 확장 완료: {len(existing_treatment)} → {len(extended_treatment)} 블록")
            return extended_treatment

        except Exception as e:
            print(f"   ❌ Block 확장 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return existing_treatment

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

            # [V65] retry_with_feedback 래퍼로 밀도 확보 재시도 루프 표준화
            from modules.core.adaptive_retry import retry_with_feedback

            def _vol_attempt_func(attempt, _feedback):
                """[V65] 단일 권 설계 시도 로직"""
                self.ui.log(f"   {Emojis.BRAIN} 제 {vol_idx}권 전략 설계 중... (시도 {attempt+1}/{RetryLimits.DIRECTOR_MAX_ATTEMPTS})")

                # [안전성 패치] Analyst에게 슬라이싱된 데이터와 성경, 그리고 '누적된 앞 권 내용' 주입
                # [V60.83] Stage 1 스피너  [V60.93] 주인공 이름 추출
                stage1_protagonist_name = self._get_protagonist_name()
                with StageSpinner(1, f"제{vol_idx}권 설계"):
                    vol_data = self.agents['analyst'].plan_single_volume_v20(
                        vol_idx,
                        self.current_project.master_bible,
                        treatment_slice,
                        context_accumulator,
                        meta_info,
                        protagonist_name=stage1_protagonist_name  # [V60.93]
                    )
                return vol_data

            def _vol_on_success(vol_data):
                """[V65] 볼륨 설계 성공 판정 — 유효성 + 분량 + 경계 검증"""
                if not vol_data or not isinstance(vol_data, dict):
                    self.ui.log(f"🚨 [Analyst Error] 제 {vol_idx}권 설계 결과가 유효하지 않음: {type(vol_data)}")
                    self._audit_event("analyst_error", "invalid volume data", {
                        "vol_no": vol_idx, "type": str(type(vol_data))
                    })
                    return False

                # V25 품질 기준: 전략 문서가 최소 2,000자 이상
                raw_doc = vol_data.get('strategy_doc', '')
                if isinstance(raw_doc, dict):
                    raw_doc = json.dumps(raw_doc, ensure_ascii=False)
                doc_len = len(raw_doc)
                if doc_len < 2000:
                    self.ui.log(f"   ⚠️ [Low Density] 분량 부족({doc_len}/2000). 다시 설계합니다.")
                    return False

                # [V39 패치 D] Volume 경계 검증 추가
                boundary_check = self._validate_volume_boundaries(vol_data, vol_idx)
                if boundary_check.get("status") == "REJECT":
                    self.ui.log(f"   🚨 [Boundary Violation] {boundary_check.get('reason')}")
                    self.ui.log(f"   📝 수정 요청: {boundary_check.get('feedback')}")
                    self._audit_event("volume_boundary_violation", boundary_check.get("reason"), {
                        "vol_no": vol_idx, "feedback": boundary_check.get("feedback")
                    })
                    return False

                return True

            def _vol_on_failure(vol_data, attempt):
                """[V65] 실패 시 피드백 (로그/감사만, 원래 루프도 피드백 미사용)"""
                return ""

            vol_result, _vol_attempts, vol_passed = retry_with_feedback(
                func=_vol_attempt_func,
                max_attempts=RetryLimits.DIRECTOR_MAX_ATTEMPTS,
                on_success=_vol_on_success,
                on_failure=_vol_on_failure,
                logger=lambda msg: self.ui.log(msg),
                task_name=f"Stage1_Volume_{vol_idx}",
            )

            if not vol_passed:
                self.ui.log(f"❌ [Critical] 제 {vol_idx}권 품질 미달로 공정 중단.")
                return

            # 성공 후처리 — 기존 동작 보존
            vol_data = vol_result
            raw_doc = vol_data.get('strategy_doc', '')
            if isinstance(raw_doc, dict):
                raw_doc = json.dumps(raw_doc, ensure_ascii=False)
            doc_len = len(raw_doc)
            self.ui.log(f"   ✅ [Pass] {vol_idx}권 검수 완료 (분량: {doc_len}자)")
            final_volumes.append(vol_data)

            # [중요] 다음 권 설계를 위해 현재 권의 요약을 누적
            # [V62.8] 최근 3권만 상세 유지, 나머지 1줄 압축
            summary = vol_data.get('strategy_doc', '')[:500]
            context_accumulator += f"\n[제 {vol_idx}권 요약]: {summary}..."
            MAX_CONTEXT_VOLUMES = 3
            if vol_idx > MAX_CONTEXT_VOLUMES:
                # 오래된 권 요약을 1줄로 압축
                acc_lines = context_accumulator.split('\n')
                compressed_lines = []
                kept_recent = 0
                for line in reversed(acc_lines):
                    if line.startswith('[제 ') and '권 요약]' in line:
                        if kept_recent < MAX_CONTEXT_VOLUMES:
                            compressed_lines.insert(0, line)
                            kept_recent += 1
                        else:
                            vol_label = line.split(']:')[0] + ']: (요약 생략)'
                            compressed_lines.insert(0, vol_label)
                    elif line.strip():
                        compressed_lines.insert(0, line)
                context_accumulator = '\n'.join(compressed_lines)

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
        """[V64.P3] Stage 2 Arc 설계 → Stage2Orchestrator 위임"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._stage2_orch.stage_2_arcs_async_logic())
                future.result()
        else:
            asyncio.run(self._stage2_orch.stage_2_arcs_async_logic())


    # -- [V64.P3] Stage 2 helpers -> Stage2Orchestrator delegation stubs ------

    def _normalize_tactical_text(self, text):
        """[V64.P3] -> Stage2Orchestrator"""
        return self._stage2_orch._normalize_tactical_text(text)

    def _is_tactical_doc_duplicate(self, candidate_text, reference_texts, threshold=0.98):
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
    
    def _build_item_acquisition_timeline(self, up_to_ep: int) -> str:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.build_item_acquisition_timeline(up_to_ep)

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
        # [FIX] 안전한 정수 변환 (dict/list/None 등 타입 오류 방지)
        ep_count = refined_arc.get("ep_count") or refined_arc.get("ep_end")
        if not isinstance(ep_count, int):
            try:
                ep_count = int(ep_count) if ep_count and not isinstance(ep_count, (dict, list)) else 5
            except (ValueError, TypeError):
                ep_count = 5
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

    def _build_validation_context(self, ep_num: int, blueprint: dict = None, mode: str = 'MANUSCRIPT', blueprint_text: str = '') -> dict:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.build_validation_context(ep_num, blueprint, mode, blueprint_text)

    # =================================================================
    # [V41] Director Sovereignty 헬퍼 메서드
    # =================================================================

    def _extract_npc_profiles(self, arc_data: dict) -> dict:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.extract_npc_profiles(arc_data)

    def _get_character_traits(self) -> dict:
        """[V64 P2-2] -> PromptBuilder"""
        return self._prompt_builder.get_character_traits()

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

    def _classify_rejection_feedback(self, reason: str, feedback: str, blueprint: dict = None) -> str:
        """[V64 P2-3] -> FeedbackSystem"""
        return self._feedback_system.classify_rejection_feedback(reason, feedback, blueprint)

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
        [V60.80] Stage 3 - Three Phase Blueprint Generator

        3단계 파이프라인: 제약수집 → 앙상블생성 → 통합검증
        - Phase 1: Constraint compilation (Arc 섹션 추출, 연속성, 정지선)
        - Phase 2: Ensemble generation (3개 후보 → 최적 선택)
        - Phase 3: Unified validation (Python + LLM)

        철학: "Arc를 충실히 따르는, 연속성 있는 Blueprint"
        """
        if not self.current_project.arcs:
            self.ui.log(f"{Emojis.ERROR} {ErrorMessages.STAGE_PREREQUISITE_MISSING}")
            return

        # ═══════════════════════════════════════════════════════════════
        # [V60.96] StateTracker 초기화 (Stage 2에서 생성되지 않은 경우)
        # [V60.95] PresetRegistry 연동
        # ═══════════════════════════════════════════════════════════════
        if not hasattr(self, 'state_tracker') or self.state_tracker is None:
            self.state_tracker = StateTracker(preset_registry=self.preset_registry, llm_client=self.sys.api_client)
            all_arcs = self.current_project.db.load_anchor('arcs') or []
            for arc in all_arcs:
                self.state_tracker.extract_npc_deaths_from_arc(arc)
                self.state_tracker.extract_skill_acquisitions_from_arc(arc)
                self.state_tracker.extract_npc_info_from_arc(arc)
                self.state_tracker.extract_resolved_plots_from_arc(arc)  # [V62.7]
            if self.state_tracker.npc_registry:
                dead_count = sum(1 for info in self.state_tracker.npc_registry.values() if info.get("status") == "dead")
                self.ui.log(f"      👤 [V60.96] StateTracker 초기화: NPC {len(self.state_tracker.npc_registry)}명 (사망: {dead_count}명)")

        # ═══════════════════════════════════════════════════════════════
        # 1. 목표 범위 설정
        # ═══════════════════════════════════════════════════════════════
        total_planned_ep = self.current_project.arcs[-1].get('ep_end', 50)

        # [V60.80 FIX] Blueprint 테이블 기준으로 시작점 결정
        existing_bp_max = self.current_project.db.get_latest_blueprint_number()  # 0 if empty

        # [Smart Skip] 기존 원고가 있다면 원고 기준으로도 체크
        existing_ms_max_ep = self._get_max_episode_from_manuscripts()

        # 둘 중 큰 값을 기준으로 (Blueprint나 원고가 있는 화 다음부터)
        production_head = max(existing_bp_max, existing_ms_max_ep)

        if production_head > 0:
            self.ui.log(f"📂 [Detected] Blueprint {existing_bp_max}화, 원고 {existing_ms_max_ep}화까지 발견")
        else:
            self.ui.log(f"📂 [Fresh Start] 기존 데이터 없음 - 1화부터 시작")

        self.ui.log(f"📊 [V60.80] 현재 총 {total_planned_ep}화까지 설계가 가능합니다.")
        target_ep = self._get_int_input(
            f"👉 몇 화까지 설계도를 생성하시겠습니까? (현재 {production_head}화 / 최대 {total_planned_ep}화): ",
            default=total_planned_ep,
            min_val=production_head + 1,
            max_val=total_planned_ep
        )

        # ═══════════════════════════════════════════════════════════════
        # 2. 메인 에피소드 루프
        # ═══════════════════════════════════════════════════════════════
        working_ep = production_head + 1
        success_count = 0
        fail_count = 0
        prev_blueprints = []  # 연속성 검증용

        # 이전 Blueprint들 로드 (최근 5개)
        for prev_ep in range(max(1, working_ep - 5), working_ep):
            prev_bp = self.current_project.get_blueprint(prev_ep)
            if prev_bp:
                prev_blueprints.append(prev_bp)

        self.ui.log(f"\n{'═' * 60}")
        self.ui.log(f"🎯 [V60.80] Three Phase Blueprint Generator 시작")
        self.ui.log(f"   범위: 제{working_ep}화 ~ 제{target_ep}화 ({target_ep - working_ep + 1}개)")
        self.ui.log(f"{'═' * 60}\n")

        while working_ep <= target_ep:
            # ───────────────────────────────────────────────────────────
            # 이미 설계도가 존재하면 스킵
            # ───────────────────────────────────────────────────────────
            if self.current_project.get_blueprint(working_ep):
                self.ui.log(f"   ⏭️  제{working_ep}화 - 기존 설계도 존재, 스킵")
                working_ep += 1
                continue

            # ───────────────────────────────────────────────────────────
            # [V60.83] 직전 화 Blueprint 필수 체크 (연속성 보장)
            # ───────────────────────────────────────────────────────────
            if working_ep > 1:
                prev_bp_check = self.current_project.get_blueprint(working_ep - 1)
                if not prev_bp_check:
                    self.ui.log(f"🚨 [V60.83] 제{working_ep - 1}화 Blueprint 없음! 연속성 보장 불가.")
                    self.ui.log(f"   → 제{working_ep - 1}화를 먼저 생성하세요.")
                    self._audit_event("continuity_block", f"ep_{working_ep}_blocked_no_prev", {
                        "blocked_ep": working_ep,
                        "missing_ep": working_ep - 1
                    })
                    break  # 연속성 깨진 상태로 진행 금지

            # ───────────────────────────────────────────────────────────
            # Arc 컨텍스트 확보
            # ───────────────────────────────────────────────────────────
            arc_idx, arc_data = self._get_arc_context_for_episode(working_ep)
            if arc_idx is None or arc_data is None:
                self.ui.log(f"❌ [V60.80] 제{working_ep}화의 Arc 컨텍스트를 찾을 수 없습니다.")
                break

            ep_start_val = arc_data.get('ep_start')
            if ep_start_val is None or not isinstance(ep_start_val, int):
                self.ui.log(f"⚠️ [Stop] Arc ep_start 누락: arc_idx={arc_idx}")
                self._audit_event("data_missing", "arc ep_start missing", {"arc_idx": arc_idx})
                break

            # Arc 데이터 검증
            arc_data_validated = self._validate_arc_data_fields(arc_data, arc_idx)
            if arc_data_validated:
                arc_data = arc_data_validated

            arc_no = arc_data.get('arc_no', arc_idx + 1)

            # ───────────────────────────────────────────────────────────
            # [V61] Entity Registry 추출 (Stage 3용)
            # [V61.6] Arc 내 캐싱 - 같은 arc_idx면 캐시 재사용 (LLM 80% 절감)
            # ───────────────────────────────────────────────────────────
            if self._entity_cache_arc_idx != arc_idx:  # [V64.P4] __init__에서 선언됨
                # arc_idx가 바뀌었을 때만 새로 추출
                self.ui.log(f"      ⏳ Entity Registry 추출 중... (Arc {arc_idx}, 첫 호출)")
                try:
                    if 'state_extractor' in self.agents and self.current_project.arcs:
                        all_arcs_for_entity = list(self.current_project.arcs)[:arc_idx + 1]
                        if all_arcs_for_entity:
                            state_for_entity = self.agents['state_extractor'].extract_cumulative_state(all_arcs_for_entity)
                            self._cached_entity_registry = state_for_entity.get('entity_registry') if state_for_entity else None
                            if self._cached_entity_registry:
                                # [V62.4] 주인공 이름 보정
                                stage3_protag = self._get_protagonist_name()
                                self._cached_entity_registry = self._fix_entity_registry_protagonist(
                                    self._cached_entity_registry, stage3_protag
                                )
                                total_entities = sum(len(v) for v in self._cached_entity_registry.values() if isinstance(v, list))
                                self.ui.log(f"      📋 [V61] Entity Registry 추출: {total_entities}개 엔티티")
                        else:
                            self._cached_entity_registry = None
                    else:
                        self._cached_entity_registry = None
                    self._entity_cache_arc_idx = arc_idx
                except Exception as entity_err:
                    self.ui.log(f"      ⚠️ [V61] Entity Registry 추출 실패: {str(entity_err)[:50]}")
                    self._cached_entity_registry = None
                    self._entity_cache_arc_idx = arc_idx  # 실패해도 캐시 마킹 (반복 시도 방지)
            else:
                self.ui.log(f"      ♻️ [V61.6] Entity Registry 캐시 재사용 (Arc {arc_idx})")
            entity_registry_for_stage3 = getattr(self, '_cached_entity_registry', None)

            # ───────────────────────────────────────────────────────────
            # 직전 Blueprint 로드 [V61.3 보호]
            # ───────────────────────────────────────────────────────────
            prev_blueprint = None
            try:
                prev_blueprint = self.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None
            except Exception as prev_bp_err:
                import sys
                import traceback
                print(f"🚨 [V61.3] prev_blueprint 로드 크래시: {str(prev_bp_err)[:100]}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                self.ui.log(f"      ⚠️ 직전 Blueprint 로드 실패, None으로 진행")

            # ───────────────────────────────────────────────────────────
            # [V61] 주인공 이름 추출 [V61.3 보호]
            # ───────────────────────────────────────────────────────────
            protagonist_name_for_stage3 = "주인공"  # 기본값
            try:
                protagonist_name_for_stage3 = self._get_protagonist_name()
            except Exception as protag_err:
                import sys
                import traceback
                print(f"🚨 [V61.3] protagonist_name 추출 크래시: {str(protag_err)[:100]}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                self.ui.log(f"      ⚠️ 주인공 이름 추출 실패, 기본값 사용")

            # ───────────────────────────────────────────────────────────
            # [V60.80] Three Phase Blueprint Generation
            # ───────────────────────────────────────────────────────────
            self.ui.log(f"\n   📐 제{working_ep}화 Blueprint 생성 중... (Arc {arc_no}, 주인공: {protagonist_name_for_stage3})")

            try:
                # [V63.3] BlueprintMemory 시맨틱 검색
                _bp_semantic_ctx = ""
                try:
                    if self.blueprint_memory and self.blueprint_memory.initialized and arc_data:
                        _bp_scenario = arc_data.get('tactical_doc', '')[:300]
                        if _bp_scenario:
                            _bp_related = self.blueprint_memory.search_related(
                                _bp_scenario, n_results=3, exclude_eps=[working_ep]
                            )
                            if _bp_related:
                                _bp_semantic_ctx = self.blueprint_memory.generate_context_prompt(_bp_related)
                except Exception:  # [V64.P4] OPTIONAL: blueprint vector search
                    pass

                # [V60.83] Stage 3 스피너
                with StageSpinner(3, f"제{working_ep}화"):
                    # [V60.80] ToT 방식: 3전략 × 3시도 = 최대 9회 생성, Director 최대 3회 판정
                    # [V61] entity_registry 전달하여 NPC 명칭 일관성 검증
                    # [V60.96] state_tracker 전달하여 죽은 NPC 검증
                    blueprint, pipeline_result = self.agents['three_phase_bp'].generate(
                        ep_num=working_ep,
                        arc_data=arc_data,
                        prev_blueprint=prev_blueprint,
                        prev_blueprints=prev_blueprints[-5:] if prev_blueprints else None,
                        max_retries=4,  # [V62.4] 총 5번 시도 (0, 1, 2, 3, 4)
                        director=self.agents['director'],  # 디렉터주권주의 - 최종 판정
                        arc_idx=arc_idx,
                        entity_registry=entity_registry_for_stage3,  # [V61] Entity 일관성 검증
                        protagonist_name=protagonist_name_for_stage3,  # [V61] 주인공 이름 주입
                        state_tracker=getattr(self, 'state_tracker', None),  # [V60.96] 죽은 NPC 검증
                        db=self.current_project.db,  # [V61.6] 연속성 검사 활성화
                        semantic_context=_bp_semantic_ctx  # [V63.3] 유사 블루프린트 참조
                    )

            except Exception as gen_err:
                # [V61.3] stderr로도 출력 (Rich 스피너가 stdout 가림)
                import sys
                import traceback
                print(f"🚨 [V61.3] 제{working_ep}화 Blueprint 생성 크래시: {str(gen_err)[:100]}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()

                self.ui.log(f"❌ [V60.80] 제{working_ep}화 생성 실패: {str(gen_err)[:100]}")
                self._audit_event("blueprint_gen_error", str(gen_err)[:200], {"ep_num": working_ep})
                blueprint = None
                pipeline_result = {"final_verdict": "ERROR", "error": str(gen_err)[:200]}

            # ───────────────────────────────────────────────────────────
            # 결과 처리
            # ───────────────────────────────────────────────────────────
            if blueprint and pipeline_result.get("final_verdict") == "PASS":
                # 무결성 검증 후 저장
                if not self._validate_blueprint_integrity(blueprint):
                    self.ui.log(f"   🚨 [Integrity] 제{working_ep}화 Blueprint 무결성 실패")
                    self._audit_event("integrity_fail", "blueprint integrity check failed", {"ep_num": working_ep})
                    fail_count += 1
                    working_ep += 1
                    continue

                # DB에 저장
                self.current_project.save_episode_blueprint(working_ep, blueprint)
                self._safe_commit()

                # [V63.3] BlueprintMemory 인덱싱
                try:
                    if self.blueprint_memory and self.blueprint_memory.initialized:
                        self.blueprint_memory.index_blueprint(working_ep, blueprint)
                except Exception:  # [V64.P4] OPTIONAL: blueprint indexing
                    pass

                # prev_blueprints 업데이트
                prev_blueprints.append(blueprint)
                if len(prev_blueprints) > 5:
                    prev_blueprints = prev_blueprints[-5:]

                # 메트릭 기록
                self._audit_event("blueprint_success", f"ep_{working_ep}_blueprint_generated", {
                    "ep_num": working_ep,
                    "arc_no": arc_no,
                    "strategy": pipeline_result.get("phases", {}).get("generate", {}).get("selected_strategy", "unknown"),
                    "score": pipeline_result.get("phases", {}).get("generate", {}).get("selected_score", 0)
                })

                self.ui.log(f"   ✅ 제{working_ep}화 Blueprint 저장 완료")
                success_count += 1
                working_ep += 1

            else:
                # 생성 실패
                self.ui.log(f"   ❌ 제{working_ep}화 Blueprint 생성 실패")
                self._audit_event("blueprint_fail", f"ep_{working_ep}_all_retries_exhausted", {
                    "ep_num": working_ep,
                    "final_verdict": pipeline_result.get("final_verdict", "UNKNOWN")
                })
                fail_count += 1

                # 연속 실패 3회 시 중단
                if fail_count >= 3:
                    self.ui.log(f"🛑 [Safety] 연속 {fail_count}회 실패로 공정을 중단합니다.")
                    break

                working_ep += 1

        # ═══════════════════════════════════════════════════════════════
        # 3. 완료 처리
        # ═══════════════════════════════════════════════════════════════
        self._write_audit_summary("stage3_complete")

        # 통계 출력
        self.ui.log(f"\n{'═' * 60}")
        self.ui.log(f"📊 [V60.80] Stage 3 완료 통계")
        self.ui.log(f"   성공: {success_count}개 | 실패: {fail_count}개")
        if hasattr(self.agents.get('three_phase_bp'), 'get_stats'):
            stats = self.agents['three_phase_bp'].get_stats()
            self.ui.log(f"   통과율: {stats.get('pass_rate', 'N/A')}")
        self.ui.log(f"{'═' * 60}\n")

        # Slack 알림
        if success_count > 0:
            try:
                notifier.send_notification(
                    title=f"✅ [V60.80 Blueprint] 설계도 생성 완료",
                    message=f"프로젝트: {self.current_project.name}\n성공: {success_count}개 | 실패: {fail_count}개",
                    key_metrics={"성공": f"{success_count}개", "실패": f"{fail_count}개"}
                )
            except Exception as slack_err:
                self.ui.log(f"⚠️ [Slack] 알림 전송 실패: {str(slack_err)[:50]}")


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
            },
            "4": {
                "name": f"{GenreTypes.get_name(GenreTypes.FANTASY)} (Fantasy)",
                "type": GenreTypes.FANTASY,
                "hud_key": HUDKeys.FANTASY_HUD_ROOT,
                "description": "이세계 배경, 마법/마나 시스템, 종족/길드",
                "critical_keys": ['magic_tier', 'mana', 'spells', 'race', 'blessings', 'level', 'wealth', 'injuries', 'reputation', 'current_objective']
            },
            "5": {
                "name": f"{GenreTypes.get_name(GenreTypes.COMPOSER)} (Composer Fiction)",
                "type": GenreTypes.COMPOSER,
                "hud_key": HUDKeys.COMPOSER_HUD_ROOT,
                "description": "현대 배경, 음악 창작/산업 시스템, 작곡/프로듀싱",
                "critical_keys": ['composition', 'arrangement', 'production', 'reputation', 'wealth', 'mental_state', 'current_objective']
            },
            "6": {
                "name": f"{GenreTypes.get_name(GenreTypes.COOKING)} (Cooking Fiction)",
                "type": GenreTypes.COOKING,
                "hud_key": HUDKeys.COOKING_HUD_ROOT,
                "description": "현대 배경, 셰프 성장/식당 경영 시스템, 요리/미식",
                "critical_keys": ['chef_rank', 'signature_dish', 'culinary_techniques', 'restaurant_tier', 'reputation_score', 'capital', 'current_objective']
            },
            "7": {
                "name": f"{GenreTypes.get_name(GenreTypes.ALT_HISTORY)} (Alt History)",
                "type": GenreTypes.ALT_HISTORY,
                "hud_key": HUDKeys.ALT_HISTORY_HUD_ROOT,
                "description": "조선 시대 배경, 관직/당파/신분 시스템, 궁중 정치",
                "critical_keys": ['social_class', 'court_rank', 'position', 'faction', 'political_influence', 'wealth', 'public_trust', 'current_objective']
            },
            "8": {
                "name": f"{GenreTypes.get_name(GenreTypes.ACTOR)} (Actor Fiction)",
                "type": GenreTypes.ACTOR,
                "hud_key": HUDKeys.ACTOR_HUD_ROOT,
                "description": "현대 배경, 연예계/배우 성장 시스템, 오디션/촬영/시상식",
                "critical_keys": ['acting_skill', 'fame', 'filmography', 'agency', 'fandom', 'scandal_index', 'box_office', 'current_objective']
            },
            "9": {
                "name": f"{GenreTypes.get_name(GenreTypes.SPORTS)} (Sports Fiction)",
                "type": GenreTypes.SPORTS,
                "hud_key": HUDKeys.SPORTS_HUD_ROOT,
                "description": "현대 배경, 선수 성장/팀 스포츠 시스템, 경기/훈련",
                "critical_keys": ['athlete_tier', 'sport_type', 'physical_stats', 'record', 'team', 'ranking', 'reputation', 'current_objective']
            },
            "10": {
                "name": f"{GenreTypes.get_name(GenreTypes.MEDICAL)} (Medical Fiction)",
                "type": GenreTypes.MEDICAL,
                "hud_key": HUDKeys.MEDICAL_HUD_ROOT,
                "description": "현대 배경, 의사 성장/병원 시스템, 수술/진료",
                "critical_keys": ['doctor_rank', 'specialty', 'hospital', 'surgery_count', 'success_rate', 'reputation', 'current_objective']
            }
        }
        
        print(f"\n{Emojis.BOOK} [V40 Multi-Genre Factory] 장르를 선택하십시오:\n")
        for key, genre in genres.items():
            print(f"   {key}. {genre['name']}")
            print(f"      → {genre['description']}\n")
        
        choice = self._get_int_input(
            f"{Emojis.PENCIL} Choice (1.무협 / 2.헌터 / 3.투자 / 4.작곡가 / 5.요리 / 6.대체역사 / 7.배우물 / 8.스포츠 / 9.의학): ",
            default=1,
            min_val=1,
            max_val=9
        )
        
        selected = genres[str(choice)]
        self.ui.log(f"✅ [{selected['name']}] 전문 공정이 선택되었습니다.")
        self.ui.log(f"   📌 HUD 시스템: {selected['type'].upper()}")

        # [V60.95] PresetRegistry 초기화
        if STAGE0_AVAILABLE:
            genre_map = {
                GenreTypes.WUXIA: "wuxia",
                GenreTypes.HUNTER: "hunter",
                GenreTypes.INVESTMENT: "investment",
                GenreTypes.COMPOSER: "composer",
                GenreTypes.COOKING: "cooking",
                GenreTypes.ALT_HISTORY: "alt_history",
                GenreTypes.ACTOR: "actor",
                GenreTypes.SPORTS: "sports",
                GenreTypes.MEDICAL: "medical",
            }
            base_genre = genre_map.get(selected['type'], "wuxia")
            self.preset_registry = PresetRegistry(base_genre=base_genre)
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
            self._safe_commit()
            
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
                            if 'MasterBible' in bible_data:
                                # [V61.2 Fix] 장르별 HUD 탐색
                                genre = self.selected_genre.get('type', '') if self.selected_genre else ''
                                hud_key = HUDKeys.get_hud_root(genre)
                                # 존재하는 HUD 키를 우선 탐색
                                for hk in [hud_key, 'MartialHUD', 'FinanceHUD', 'HunterHUD']:
                                    if hk in bible_data['MasterBible']:
                                        hud_key = hk
                                        break
                                if hud_key in bible_data['MasterBible']:
                                    bible_data['MasterBible'][hud_key].setdefault('Protagonist', {})['actual_truth'] = past_actual
                                self.current_project.db.cursor.execute(
                                    "UPDATE anchors SET data = ? WHERE key = 'bible'",
                                    (json.dumps(bible_data, ensure_ascii=False),)
                                )
                                self.ui.log(f"   📉 [Rollback] HUD를 {target_ep-1}화 시점으로 복구했습니다.")
                                # 메모리에도 반영
                                self.current_project.master_bible = bible_data

            # 2. ✂️ SQL DB 데이터 삭제
            # [FIX] SQL Injection 방지: 화이트리스트로 테이블명 검증
            ALLOWED_EP_TABLES = frozenset([
                'manuscripts', 'blueprints', 'state_logs', 'martial_tracker',
                'sync_status', 'causal_graph'
            ])
            ep_tables = [
                'manuscripts', 'blueprints', 'state_logs', 'martial_tracker',
                'sync_status', 'causal_graph'
            ]

            for t in ep_tables:
                if t not in ALLOWED_EP_TABLES:
                    self.ui.log(f"🚨 [Security] 허용되지 않은 테이블: {t}")
                    continue
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

            # 3.5 [V61] Episode Bibles 롤백 (에피소드별 설정 변화 - 아이템, NPC, 관계 등)
            deleted_bibles = self.current_project.db.delete_episode_bibles_after(target_ep - 1)
            self.ui.log(f"   📖 [Episode Bibles] {deleted_bibles}개 에피소드 설정 변화 삭제 완료")

            # 4. 🔢 ID 카운터 초기화 (sqlite_sequence)
            seq_targets = "('manuscripts', 'blueprints', 'state_logs', 'martial_tracker', 'causal_graph', 'sync_status')"
            self.current_project.db.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN {seq_targets}")
            self.ui.log("   🔢 [Sequence] 테이블 ID 카운터 초기화 완료")

            # 커밋
            self._safe_commit()

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
            # [FIX] SQL Injection 방지: 화이트리스트로 테이블명 검증
            ALLOWED_TABLES = frozenset([
                'manuscripts', 'blueprints', 'state_logs', 'martial_tracker',
                'causal_graph', 'sync_status', 'karma_status'
            ])
            production_tables = [
                'manuscripts', 'blueprints', 'state_logs', 'martial_tracker',
                'causal_graph', 'sync_status', 'karma_status'
            ]

            for t in production_tables:
                if t not in ALLOWED_TABLES:
                    self.ui.log(f"🚨 [Security] 허용되지 않은 테이블: {t}")
                    continue
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

    # =================================================================
    # [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처
    # =================================================================

    # ═══════════════════════════════════════════════════════════════
    # [V63.2] 10화 단위 내러티브 요약 시스템
    # ═══════════════════════════════════════════════════════════════

    def _generate_narrative_summary(self, up_to_ep: int) -> None:
        """
        [V66] 5화 단위 내러티브 요약 생성 및 DB 저장.

        최근 5화 원고를 LLM(gemini-2.5-flash)으로 요약하여
        'narrative_summary_ep_XXX' anchor에 저장.
        이후 생성 시 장기 기억으로 활용.
        """
        import time as _time

        start_ep = max(1, up_to_ep - 4)  # [V66] 10→5화 범위
        self.ui.log(f"   📝 [V66] 내러티브 요약 생성 중 (제{start_ep}~{up_to_ep}화)...")

        # 최근 5화 원고 수집
        manuscripts = self.current_project.db.get_recent_manuscripts(
            before_ep=up_to_ep + 1, limit=5
        )
        if not manuscripts or len(manuscripts) < 2:  # [V66] 최소 2화로 완화
            self.ui.log(f"   ⚠️ 원고 부족 ({len(manuscripts)}화) - 요약 건너뜀")
            return

        # 원고 텍스트 결합 (각 화 앞 500자만 + 뒤 300자)
        combined = []
        for ms in manuscripts:
            ep = ms.get("ep_num", "?")
            content = ms.get("content", "")
            if content:
                excerpt = content[:500] + "\n...(중략)...\n" + content[-300:] if len(content) > 800 else content
                combined.append(f"[제{ep}화]\n{excerpt}")

        combined_text = "\n\n---\n\n".join(combined)

        # LLM 요약 호출
        try:
            from google.genai import types as _types

            prompt = (
                f"다음은 웹소설의 제{start_ep}~{up_to_ep}화 원고 발췌입니다.\n"
                f"500자 이내로 핵심 내러티브를 요약해주세요.\n\n"
                f"반드시 포함할 내용:\n"
                f"1. 주요 사건 (각 화의 핵심 전개)\n"
                f"2. 캐릭터 변화 (관계 변화, 성장, 사망 등)\n"
                f"3. 미해결 갈등/복선 (아직 해결되지 않은 것)\n"
                f"4. 현재 상황 (마지막 화 기준 위치, 상태, 다음 전개 방향)\n\n"
                f"[원고 발췌]\n{combined_text[:8000]}\n\n"
                f"요약 (500자 이내, 한국어):"
            )

            _time.sleep(0.3)
            response = self.sys.api_client.models.generate_content(
                model=_SUMMARY_MODEL,  # [V65] 중앙 상수
                contents=prompt,
                config=_types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                ),
            )

            summary = response.text.strip()
            if summary and len(summary) > 50:
                anchor_key = f"narrative_summary_ep_{up_to_ep:03d}"
                self.current_project.db.save_anchor(anchor_key, {
                    "ep_range": f"{start_ep}-{up_to_ep}",
                    "summary": summary,
                    "ep_count": len(manuscripts),
                })
                self.current_project.db.conn.commit()
                self.ui.log(f"   ✅ [V63.2] 내러티브 요약 저장: {anchor_key} ({len(summary)}자)")
            else:
                self.ui.log(f"   ⚠️ 요약이 너무 짧음 ({len(summary)}자) - 저장 건너뜀")

        except Exception as e:
            self.ui.log(f"   ⚠️ [V63.2] LLM 요약 실패: {str(e)[:60]}")

    def _load_narrative_summaries(self) -> str:
        """
        [V63.2] 저장된 내러티브 요약들을 로드하여 프롬프트 주입용 문자열 반환.
        """
        summaries = []
        for ep_marker in range(5, 500, 5):  # [V66] 10→5화 간격
            anchor_key = f"narrative_summary_ep_{ep_marker:03d}"
            data = self.current_project.db.load_anchor(anchor_key, default=None)
            if data and isinstance(data, dict) and data.get("summary"):
                summaries.append(f"[제{data['ep_range']}화 요약] {data['summary']}")
            else:
                continue  # [V63.3] 빈 구간 건너뛰기 (break→continue, 이후 요약도 로드)

        if summaries:
            return "### 📚 장기 내러티브 요약 (과거 스토리)\n" + "\n\n".join(summaries)
        return ""

    def _stage_4_v2_chief_writer(self, limit_mode: bool = False) -> None:
        """[V64.P3] Stage 4 V2 Chief Writer -> Stage4Orchestrator 위임"""
        return self._stage4_orch.stage_4_v2_chief_writer(limit_mode=limit_mode)


if __name__ == "__main__":
    SovereignApp().boot()