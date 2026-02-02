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
from rich.console import Console
from rich.status import Status

# [V60.47] 전역 Rich 콘솔 (스피너용)
rich_console = Console()
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
from modules.core.narrative_diversity import NarrativeDiversityEngine  # [V48] 서사 다양성 엔진
from modules.core.metrics_collector import get_metrics_collector  # [V49.3] 비용 추적 시스템
from modules.core.constraint_db import ConstraintDB  # [V49.4] Pre-Generation Constraint DB

# [V50] 서사 품질 향상 모듈
try:
    from modules.core.tension_curve import TensionCurveManager  # [V50.1] 긴장감 곡선 관리
    from modules.core.dialogue_engine import DialogueQualityEngine  # [V50.2] 대화 DNA 엔진
    from modules.core.subplot_weaver import SubplotWeaver  # [V50.3] 서브플롯 관리
    from modules.core.reader_simulator import ReaderSimulator  # [V50.4] 가상 독자 시뮬레이션
    from modules.core.pacing_analyzer import PacingAnalyzer  # [V51.1] 호흡 분석기
    from modules.core.quality_amplifier import QualityAmplifier  # [V51.2] 품질 증폭기
    from modules.core.agent_intelligence import AgentIntelligence, AgentType  # [V51.3] 에이전트 지능 향상
    from modules.core.failure_learning import FailureLearner  # [V51.4] 실패 학습 시스템
    from modules.core.character_voice import CharacterVoiceTracker  # [V51.5] 캐릭터 음성 추적
    from modules.core.foreshadow_tracker import ForeshadowTracker, ForeshadowCategory  # [V51.6] 복선 추적
    from modules.core.emotion_tracker import EmotionArcTracker  # [V60.26] 감정선 추적
    from modules.core.power_scaling import PowerScalingTracker  # [V60.26] 파워 스케일링 추적
    from modules.core.state_delta_tracker import StateDeltaTracker  # [V60.26] 상태 변화 추적
    from modules.core.semantic_item_registry import SemanticItemRegistry  # [V60.26] 의미적 아이템 레지스트리
    from modules.core.character_voice_profiler import CharacterVoiceProfiler  # [V60.26] 캐릭터 음성 프로파일러 (V58)
    from modules.core.self_reflection import SelfReflector, ReflectionTarget  # [V52.1] 자기 성찰
    from modules.core.expert_mixture import ExpertMixture, SceneType  # [V52.3] 전문가 혼합
    from modules.core.cross_agent_verifier import CrossAgentVerifier, ComplianceLevel  # [V52.4] 교차 검증
    from modules.core.dynamic_prompt_weighting import DynamicPromptWeighter, PromptCategory  # [V53.1] 동적 프롬프트 가중치
    from modules.core.chain_of_verification import ChainOfVerification, VerificationSeverity  # [V53.2] 사실 검증 체인
    from modules.core.confidence_calibration import ConfidenceCalibrator, ConfidenceLevel  # [V53.3] 신뢰도 보정
    from modules.core.pre_director_checklist import PreDirectorChecklist, CheckSeverity  # [V53.4] 사전 체크리스트
    from modules.core.tree_of_thoughts import TreeOfThoughts  # [V53.5] Tree of Thoughts
    from modules.core.adversarial_self_play import AdversarialSelfPlay  # [V53.6] 적대적 자기 대결
    from modules.core.multi_agent_deliberation import MultiAgentDeliberation, AgentRole  # [V53.7] 다중 에이전트 토론
    # [V54] 비용 절감 + 품질 향상 모듈
    from modules.core.semantic_cache import SemanticCache, BlueprintCache  # [V54.1] 의미론적 캐시
    from modules.core.context_compression import ContextCompressor  # [V54.2] 컨텍스트 압축
    from modules.core.adaptive_retry import AdaptiveRetryManager, get_adaptive_manager  # [V54.3] 적응형 재시도
    from modules.core.two_phase_generator import TwoPhaseManuscriptGenerator, TwoPhaseBlueprintGenerator, TwoPhaseArcGenerator  # [V54.4] 2단계 생성
    from modules.core.blueprint_memory import SuccessPatternMemory  # [V54.5] 성공 패턴 메모리
    from modules.core.manuscript_enhancer import ManuscriptEnhancer  # [V55] 원고 품질/분량 향상
    from modules.core.constitutional_checker import ConstitutionalChecker  # [V55.2] 헌법적 자기검증
    from modules.core.writer_template import WriterTemplate  # [V55.3] 원고 템플릿
    from modules.core.pass_rate_monitor import PassRateMonitor, get_monitor  # [V55.3] 통과율 모니터
    from modules.core.quality_dashboard import QualityDashboard, get_dashboard  # [V60] 품질 대시보드
    from modules.core.stage2_optimizer import Stage2Optimizer, create_stage2_optimizer  # [V60.25] Stage 2 최적화
    V50_MODULES_AVAILABLE = True
except ImportError as e:
    V50_MODULES_AVAILABLE = False
    print(f"⚠️ [V50] 일부 모듈 미설치: {e}")

import random
from google.genai import types
import asyncio

# [V60.2] 사전 컴파일된 수여물 패턴 (성능 최적화)
GRANT_PATTERNS_COMPILED = [
    (re.compile(r'([가-힣]+패)[를을]?\s*(?:하사|수여|받|얻)'), '패'),  # ~패
    (re.compile(r'([가-힣]+권)[를을]?\s*(?:위임|부여|받|얻|하사)'), '권'),  # ~권
    (re.compile(r'([가-힣]+직|[가-힣]+장)[에으로]?\s*(?:임명|취임|올|받)'), '직위'),  # 직위/직장
    (re.compile(r'((?:[가-힣]+\s*)?인장)[를을]?\s*(?:받|하사|수여)'), '인장'),  # 인장 (공백 허용)
]

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
        self.diversity_engine = None  # [V48] 서사 다양성 엔진
        self.stage_rejection_history = []  # [V60.3] Stage간 REJECT 히스토리 전달

        # [V50] 서사 품질 향상 모듈
        self.tension_manager = None    # [V50.1] 긴장감 곡선 관리
        self.dialogue_engine = None    # [V50.2] 대화 DNA 엔진
        self.subplot_weaver = None     # [V50.3] 서브플롯 관리
        self.reader_simulator = None   # [V50.4] 가상 독자 시뮬레이션
        self.pacing_analyzer = None    # [V51.1] 호흡 분석기
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
        self.two_phase_ms = None        # [V54.4] 2단계 원고 생성
        self.two_phase_bp = None        # [V54.4.1] 2단계 블루프린트 생성
        self.two_phase_arc = None       # [V55.1] 2단계 Arc 생성
        self.success_patterns = None    # [V54.5] 성공 패턴 메모리
        self.manuscript_enhancer = None # [V55] 원고 품질/분량 향상
        self.constitutional_checker = None  # [V55.2] 헌법적 자기검증
        self.writer_template = None         # [V55.3] 원고 템플릿
        self.pass_rate_monitor = None       # [V55.3] 통과율 모니터
        self.quality_dashboard = None       # [V60] 품질 대시보드

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

    def _build_structured_feedback(self, decision: str, reason: str, violations: list = None,
                                      severity: str = "MEDIUM", fix_instructions: str = "") -> dict:
        """
        [V60.3] 구조화된 피드백 생성

        Args:
            decision: PASS/REJECT/CONDITIONAL_PASS
            reason: REJECT 사유
            violations: 위반 항목 리스트
            severity: CRITICAL/MAJOR/MINOR
            fix_instructions: 수정 지시

        Returns:
            dict: 구조화된 피드백 객체
        """
        return {
            'decision': decision,
            'reason': reason[:300] if reason else '',
            'violations': violations or [],
            'severity': severity,
            'fix_instructions': fix_instructions[:500] if fix_instructions else '',
            'priority_order': self._get_violation_priority(violations or [])
        }

    def _get_violation_priority(self, violations: list) -> list:
        """위반 항목 우선순위 정렬"""
        priority_map = {
            'duplicate_acquisition': 1,
            'timeline_error': 2,
            'continuity': 3,
            'scope_overflow': 4,
            'blueprint_mismatch': 5,
            'relationship_jump': 6,
            'unknown': 10
        }
        sorted_violations = sorted(
            violations,
            key=lambda v: priority_map.get(v.get('type', 'unknown'), 10)
        )
        return [v.get('type', 'unknown') for v in sorted_violations]

    def _format_feedback_for_prompt(self, structured_feedback: dict) -> str:
        """구조화된 피드백을 프롬프트용 문자열로 변환"""
        if not structured_feedback or structured_feedback.get('decision') == 'PASS':
            return ""

        parts = [
            f"🚨 [{structured_feedback.get('severity', 'MEDIUM')}] {structured_feedback.get('decision', 'REJECT')}",
            f"사유: {structured_feedback.get('reason', '')}",
        ]

        priority_order = structured_feedback.get('priority_order', [])
        if priority_order:
            parts.append(f"우선 수정: {' → '.join(priority_order[:3])}")

        if structured_feedback.get('fix_instructions'):
            parts.append(f"수정 지시: {structured_feedback.get('fix_instructions')}")

        return "\n".join(parts)

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

    def _quantify_reject_feedback(
        self,
        reason: str,
        content_length: int,
        audit_result: dict
    ) -> list:
        """
        [V60.6] REJECT 사유를 구체적 수치로 정량화

        "분량 부족" → "대화 300자 추가 필요" 수준으로 변환.

        Args:
            reason: REJECT 사유
            content_length: 현재 원고 길이
            audit_result: Director 결과 (score_breakdown 등)

        Returns:
            list: 정량화된 action_items
        """
        quantified = []

        # 1. 분량 정량화
        if '분량' in reason or content_length < 4500:
            target_length = 5000
            shortage = max(0, target_length - content_length)

            if shortage > 0:
                # 부족분 배분 가이드
                dialogue_add = int(shortage * 0.35)  # 35%는 대화
                desc_add = int(shortage * 0.40)  # 40%는 묘사
                action_add = int(shortage * 0.25)  # 25%는 액션

                quantified.append({
                    'type': 'QUANTIFIED',
                    'description': f'정확한 분량 보충: 총 {shortage}자 추가 필요',
                    'severity': 'HIGH' if shortage > 500 else 'MEDIUM',
                    'suggestion': f'대화 +{dialogue_add}자 | 묘사 +{desc_add}자 | 액션 +{action_add}자'
                })

        # 2. 대화 비율 정량화
        score_breakdown = audit_result.get('score_breakdown', {})
        if '대화' in reason or '건조' in reason:
            # 현재 대화 비율 추정 (15% 미만으로 가정)
            current_dialogue_chars = int(content_length * 0.15)  # 추정치
            target_dialogue_chars = int(content_length * 0.30)  # 목표 30%
            dialogue_needed = target_dialogue_chars - current_dialogue_chars

            if dialogue_needed > 100:
                # 대화 개수로 변환 (평균 대화 50자 가정)
                dialogue_count_needed = dialogue_needed // 50

                quantified.append({
                    'type': 'QUANTIFIED',
                    'description': f'대화 분량 부족: {dialogue_needed}자 추가 필요',
                    'severity': 'HIGH' if dialogue_needed > 500 else 'MEDIUM',
                    'suggestion': f'대화 {dialogue_count_needed}~{dialogue_count_needed + 2}개 추가 (조연 리액션, 내면 독백 포함)'
                })

        # 3. 씬 밀도 정량화
        if '밀도' in reason or '후반부' in reason or '요약' in reason:
            # 후반부 분량 계산 (이상적: 전체의 50%)
            target_latter_half = content_length // 2
            estimated_latter_half = int(content_length * 0.35)  # 추정 35% (문제 상황)
            latter_shortage = target_latter_half - estimated_latter_half

            if latter_shortage > 300:
                quantified.append({
                    'type': 'QUANTIFIED',
                    'description': f'후반부 분량 부족: Scene 5-6에 {latter_shortage}자 추가 필요',
                    'severity': 'HIGH',
                    'suggestion': f'Scene 5에 +{latter_shortage // 2}자, Scene 6에 +{latter_shortage // 2}자 배분'
                })

        # 4. 씬 반영 정량화
        if '씬' in reason or '장면' in reason or '누락' in reason:
            quantified.append({
                'type': 'QUANTIFIED',
                'description': '씬 반영 부족: Blueprint의 모든 씬 균등 반영 필요',
                'severity': 'HIGH',
                'suggestion': '각 씬당 최소 700자 확보 (6개 씬 × 700자 = 4,200자 베이스라인)'
            })

        # 5. 감각 묘사 정량화
        if '묘사' in reason or '건조' in reason:
            # 이상적: 1000자당 3-5개 감각 묘사
            target_sensory = (content_length // 1000) * 4
            estimated_sensory = (content_length // 1000) * 1  # 추정 (문제 상황)
            sensory_needed = target_sensory - estimated_sensory

            if sensory_needed > 0:
                quantified.append({
                    'type': 'QUANTIFIED',
                    'description': f'감각 묘사 부족: {sensory_needed}개 추가 권장',
                    'severity': 'MEDIUM',
                    'suggestion': '시각/청각/촉각/후각 중 2가지 이상 혼합하여 장면당 1-2개 추가'
                })

        # 6. 액션 밀도 정량화
        if '액션' in reason or '긴장' in reason:
            quantified.append({
                'type': 'QUANTIFIED',
                'description': '액션 밀도 부족: 동작 묘사 강화 필요',
                'severity': 'MEDIUM',
                'suggestion': '무술 장면은 3박자 이상 교환(공격-방어-반격) 묘사. 최소 500자/액션씬'
            })

        return quantified

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
        """
        [V60.5] 3회차 이상 재시도 시 프롬프트 간소화

        핵심 피드백만 남기고 부가 정보 제거하여 토큰 효율화 및 집중도 향상.

        Args:
            enhanced_feedback: 현재까지 누적된 피드백
            core_feedback: REJECT 시 받은 핵심 피드백
            attempt: 재시도 횟수

        Returns:
            str: 간소화된 피드백
        """
        lines = [
            f"🎯 [V60.5 간소화 모드 - {attempt + 1}회차 재시도]",
            "⚠️ 이전 시도들이 실패했습니다. 아래 핵심 지시에만 집중하세요.",
            ""
        ]

        # 핵심 REJECT 사유만 추출
        if core_feedback:
            # 핵심 키워드 추출
            critical_issues = []
            if '분량' in core_feedback or '자' in core_feedback:
                critical_issues.append("📏 분량: 4,500자 이상 확보")
            if '폭주' in core_feedback:
                critical_issues.append("🔄 서사 폭주 금지: 사건을 더 잘게 쪼개라")
            if '정체' in core_feedback:
                critical_issues.append("🔄 서사 정체 금지: 반복 대신 전진하라")
            if '씬' in core_feedback or '장면' in core_feedback:
                critical_issues.append("🎬 모든 씬 반영: Blueprint 씬을 빠짐없이 포함")
            if '설정' in core_feedback or '무공' in core_feedback:
                critical_issues.append("⚙️ 설정 준수: 미습득 무공 사용 금지")
            if '밀도' in core_feedback or '균등' in core_feedback:
                critical_issues.append("📊 밀도 균등: 앞뒤 분량 균형 맞추기")

            if not critical_issues:
                # 기본 핵심 지시
                critical_issues = [
                    "📏 분량 4,500자 이상",
                    "🎬 6개 씬 모두 반영",
                    "⚙️ Hard Constraints 준수"
                ]

            lines.append("**핵심 수정 사항:**")
            for issue in critical_issues[:5]:  # 최대 5개
                lines.append(f"  {issue}")

        lines.append("")
        lines.append("💡 다른 부가 지시는 무시하고 위 핵심 사항만 해결하세요.")

        # 재시도 기준 완화 정보 추가
        lines.append("")
        lines.append("✅ PASS 가능 조건 (3회차+):")
        lines.append("  - 3~4개 씬만 있어도 OK (밀도 유지 시)")
        lines.append("  - 분량 4,000자 이상이면 통과 가능")
        lines.append("  - Hard Constraints만 지키면 승인")

        return "\n".join(lines)

    def _build_strong_kind_feedback(self, violations: list, attempt: int, protagonist_name: str = "주인공") -> str:
        """
        [V60.21] 극도로 집중된 피드백 생성

        원칙:
        1. XML 우선순위 태그 사용 (LLM이 무시 못함)
        2. 500자 이내로 압축
        3. 단 하나의 핵심 문제만 지적
        4. 직접 명령형 ("DO THIS")

        Args:
            violations: 위반 사항 리스트
            attempt: 재시도 횟수
            protagonist_name: 주인공 이름

        Returns:
            str: 극도로 집중된 피드백
        """
        if not violations:
            return ""

        # 가장 중요한 위반 하나만 선택
        v = violations[0]
        v_type = v.get('type', 'unknown')
        item_name = v.get('item_or_subject', '')

        # 위반 유형별 한 줄 명령
        if v_type == 'duplicate_acquisition':
            core_fix = f"'{item_name}' 획득 장면 삭제. 이미 소유 중이므로 '꺼내서 사용'으로 변경."
        elif v_type == 'state_discontinuity':
            core_fix = "직전 Arc 종료 상태(내공/부상)를 그대로 이어서 시작."
        elif v_type == 'premature_possession':
            core_fix = f"'{item_name}' 언급 삭제. 아직 획득 안 한 아이템."
        elif 'protagonist' in v_type.lower():
            core_fix = f"주인공 이름을 '{protagonist_name}'으로 통일."
        else:
            core_fix = v.get('description', '위반사항 수정')[:80]

        # [V60.21] XML 우선순위 태그로 감싸기 - LLM이 무시 못함
        feedback = f"""
<CRITICAL_INSTRUCTION priority="HIGHEST">
[재시도 {attempt + 1}회차] 아래 1개만 수정하면 PASS

🔴 수정 필수: {core_fix}
🔒 주인공: {protagonist_name} (변경 금지)

다른 건 그대로 두고, 위 사항만 고치세요.
</CRITICAL_INSTRUCTION>
"""
        return feedback.strip()

    def _build_focused_context(self, violations: list, prev_arcs: list, protagonist_name: str) -> str:
        """
        [V60.21] 집중된 컨텍스트 생성 - 정보 과부하 방지

        모든 맥락을 주지 말고, 핵심만 전달.
        """
        if not prev_arcs:
            return ""

        last_arc = prev_arcs[-1]
        arc_end = last_arc.get('state_constraints', {}).get('arc_end_state', {})
        joint = last_arc.get('joint_docs', {})

        # 핵심 상태만 추출 (3줄)
        energy = arc_end.get('internal_energy', '?')
        injury = arc_end.get('injuries', '없음')
        inventory = joint.get('physical_inventory', [])
        if isinstance(inventory, list):
            inventory = ', '.join(inventory[:3])

        return f"""
<PREVIOUS_STATE>
내공: {energy}% | 부상: {injury} | 소지품: {inventory}
→ 이 상태로 시작해야 함
</PREVIOUS_STATE>
""".strip()

    def _build_strong_kind_feedback_legacy(self, violations: list, attempt: int, protagonist_name: str = "주인공") -> str:
        """
        [V60.19 LEGACY] 기존 상세 피드백 (백업용)
        """
        lines = [
            "",
            "█" * 60,
            "█  🚨 [V60.19] 필수 수정 사항 - 이것만 고치면 통과!  🚨  █",
            "█" * 60,
            "",
            f"📍 현재 {attempt + 1}회차 재시도입니다.",
            f"📍 아래 사항만 수정하면 바로 PASS됩니다!",
            "",
        ]

        # 위반 유형별 친절한 수정 가이드
        for i, v in enumerate(violations[:3], 1):
            v_type = v.get('type', 'unknown')
            v_desc = v.get('description', '')[:150]
            item_name = v.get('item_or_subject', '')

            lines.append(f"━━━ 수정 {i} ━━━")

            if v_type == 'duplicate_acquisition':
                lines.extend([
                    f"❌ 문제: '{item_name}'을(를) 다시 획득하려 함",
                    f"✅ 해결: 이미 갖고 있으니 '사용'만 하세요!",
                ])
            elif v_type == 'state_discontinuity':
                lines.extend([
                    f"❌ 문제: 상태가 갑자기 바뀜 - {v_desc[:80]}",
                    f"✅ 해결: 직전 Arc 종료 상태를 그대로 이어가세요!",
                ])
            elif v_type == 'premature_possession':
                lines.extend([
                    f"❌ 문제: 획득 안 한 '{item_name}'을(를) 이미 갖고 있음",
                    f"✅ 해결: 이 아이템을 삭제하거나 획득 장면을 추가하세요!",
                ])
            elif 'protagonist' in v_type.lower() or '주인공' in v_desc:
                lines.extend([
                    f"❌ 문제: 주인공 이름이 잘못됨",
                    f"✅ 해결: 반드시 '{protagonist_name}'만 사용하세요!",
                ])
            else:
                lines.extend([
                    f"❌ 문제: {v_desc[:100]}",
                    f"✅ 해결: 위 내용을 수정해주세요.",
                ])

            lines.append("")

        lines.extend([
            "█" * 60,
            f"█  위 {len(violations[:3])}가지만 고치면 PASS! 화이팅! 💪  █",
            "█" * 60,
            "",
        ])

        return "\n".join(lines)

    def _build_minimal_arc_context(self, prev_arcs: list, protagonist_name: str) -> str:
        """
        [V60.21] 최소 Arc 컨텍스트 생성 - 재시도 시 사용

        재시도할 때는 LLM이 이미 규칙을 알고 있음.
        핵심 정보만 전달: 이전 Arc 종료 상태 + 소지품 목록

        Args:
            prev_arcs: 이전 Arc 리스트
            protagonist_name: 주인공 이름

        Returns:
            str: 최소화된 컨텍스트 (1000자 이내 목표)
        """
        if not prev_arcs:
            return f"<CONTEXT>\n주인공: {protagonist_name}\n서사 시작점 (첫 Arc)\n</CONTEXT>"

        last_arc = prev_arcs[-1]
        arc_no = last_arc.get('arc_no', '?')

        # 핵심 상태 추출
        state = last_arc.get('state_constraints', {})
        arc_end = state.get('arc_end_state', {})
        joint = last_arc.get('joint_docs', {})
        shadow = last_arc.get('status_shadow', {})

        # 내공 (arc_end_state 우선, 없으면 shadow에서 계산)
        energy = arc_end.get('internal_energy')
        if energy is None:
            loss = shadow.get('internal_energy_loss', '0%')
            try:
                loss_val = int(str(loss).replace('%', '').strip())
                energy = max(0, 100 - loss_val)
            except:
                energy = '?'

        # 부상
        injury = arc_end.get('injuries') or shadow.get('expected_injuries', '없음')

        # 위치
        location = arc_end.get('location') or joint.get('final_location', '?')

        # 소지품 (3개까지만)
        inventory = arc_end.get('equipment') or joint.get('physical_inventory', [])
        if isinstance(inventory, str):
            inventory = [i.strip() for i in inventory.split(',') if i.strip()]
        if isinstance(inventory, list):
            inventory = inventory[:5]  # 최대 5개
            inventory_str = ', '.join(inventory) if inventory else '없음'
        else:
            inventory_str = str(inventory)[:100]

        # XML 태그로 감싸기 (LLM이 중요하게 인식)
        return f"""<CONTEXT priority="HIGH">
주인공: {protagonist_name} (절대 변경 금지)

[Arc {arc_no} 종료 → 다음 Arc 시작 조건]
내공: {energy}%
부상: {injury}
위치: {location}
소지품: {inventory_str}

→ 위 상태 그대로 시작해야 함
→ 이미 가진 아이템 다시 획득 금지
</CONTEXT>"""

    def _generate_arc_position_guide(self, arc_pos: int, total_eps: int) -> str:
        """
        [V60.5] 아크 위치 기반 기대치 가이드 생성

        아크 내 위치에 따라 서사 밀도 기대치를 차등 적용:
        - 초반 (1화, 20%): 도입부, 설정 전개, 긴장감 시작
        - 중반 (40-60%): 갈등 고조, 사건 전개
        - 후반 (80-100%): 클라이맥스, 해결의 실마리, 강력한 엔딩

        Args:
            arc_pos: 현재 아크 내 위치 (1-based)
            total_eps: 아크 총 화수

        Returns:
            str: 위치 기반 가이드
        """
        if total_eps <= 0:
            return ""

        position_ratio = arc_pos / total_eps

        lines = ["[V60.5 아크 위치 기반 가이드]"]

        if arc_pos == 1:
            # 첫 화
            lines.append(f"📍 현재 위치: 아크 제1화 (도입부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 새로운 사건/갈등의 시작점 설정")
            lines.append("  - 주인공의 목표와 장애물 명확히 제시")
            lines.append("  - 독자의 기대감 구축 (급한 해결 금지)")
            lines.append("")
            lines.append("⚠️ 주의: 도입부에서 사건을 해결하면 서사 폭주. 설정과 긴장감 구축에 집중.")

        elif position_ratio <= 0.4:
            # 초반 (20-40%)
            lines.append(f"📍 현재 위치: 아크 {arc_pos}/{total_eps}화 (전개부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 갈등의 심화와 장애물 추가")
            lines.append("  - 캐릭터 관계 발전")
            lines.append("  - 복선 심기")
            lines.append("")
            lines.append("⚠️ 주의: 아직 클라이맥스 아님. 긴장감을 쌓아가는 단계.")

        elif position_ratio <= 0.7:
            # 중반 (40-70%)
            lines.append(f"📍 현재 위치: 아크 {arc_pos}/{total_eps}화 (상승부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 갈등 최고조로 끌어올리기")
            lines.append("  - 주인공의 시련과 성장 묘사")
            lines.append("  - 반전 또는 새로운 정보 공개")
            lines.append("")
            lines.append("💡 서사 밀도가 가장 높아야 하는 구간. 사건을 풍부하게 전개하라.")

        elif arc_pos == total_eps:
            # 마지막 화
            lines.append(f"📍 현재 위치: 아크 마지막 화 (절정/결말)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 이 아크의 핵심 갈등 해결")
            lines.append("  - 카타르시스 제공")
            lines.append("  - 다음 아크로 이어지는 강력한 클리프행어")
            lines.append("")
            lines.append("🔥 High Impact Zone: 클라이맥스 밀도를 최대로. 감정적 절정 필수.")

        else:
            # 후반 (70-90%)
            lines.append(f"📍 현재 위치: 아크 {arc_pos}/{total_eps}화 (절정부)")
            lines.append("")
            lines.append("🎯 이 화의 역할:")
            lines.append("  - 클라이맥스 직전 긴장감 극대화")
            lines.append("  - 주인공의 결정적 행동 또는 선택")
            lines.append("  - 절벽걸기로 다음 화 기대감 극대화")
            lines.append("")
            lines.append("🔥 High Impact Zone 진입. 감정선과 액션 밀도를 높여라.")

        return "\n".join(lines)

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
        except Exception:
            return base_keywords

    # ═══════════════════════════════════════════════════════════════════════════
    # [V60.8] Writer 사전 가이드 시스템 - Director REJECT 방지
    # ═══════════════════════════════════════════════════════════════════════════

    def _generate_high_impact_zone_guide(self, blueprint: dict, target_len: int = 5000) -> str:
        """
        [V60.8-1] High Impact Zone 분량 가이드 생성

        Scene 5-6(클라이맥스)가 Scene 1-4보다 밀도가 높도록 구체적 분량 지시
        """
        if not blueprint or not isinstance(blueprint, dict):
            return ""

        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not scene_breakdown:
            return ""

        total_scenes = len(scene_breakdown)
        if total_scenes < 4:
            return ""

        # 씬별 목표 분량 계산 (후반부 가중치 1.3배)
        # 예: 6개 씬, 5000자 목표 → 전반부 3씬 = 2000자, 후반부 3씬 = 3000자
        front_ratio = 0.4  # 전반부 40%
        back_ratio = 0.6   # 후반부 60% (클라이맥스 강조)

        mid_point = total_scenes // 2
        front_scenes = list(scene_breakdown.keys())[:mid_point]
        back_scenes = list(scene_breakdown.keys())[mid_point:]

        front_total = int(target_len * front_ratio)
        back_total = int(target_len * back_ratio)

        front_per_scene = front_total // len(front_scenes) if front_scenes else 0
        back_per_scene = back_total // len(back_scenes) if back_scenes else 0

        lines = [
            "",
            "=" * 50,
            "[V60.8 High Impact Zone 분량 가이드]",
            "=" * 50,
            f"총 목표 분량: {target_len}자",
            "",
            "📍 전반부 (도입/전개):",
        ]

        for scene_key in front_scenes:
            scene_data = scene_breakdown.get(scene_key, {})
            scene_title = scene_data.get('title', scene_key) if isinstance(scene_data, dict) else scene_key
            lines.append(f"  - {scene_key}: 약 {front_per_scene}자 ('{scene_title[:20]}...')")

        lines.append("")
        lines.append("🔥 후반부 (클라이맥스/결말) - 반드시 상세하게!")

        for scene_key in back_scenes:
            scene_data = scene_breakdown.get(scene_key, {})
            scene_title = scene_data.get('title', scene_key) if isinstance(scene_data, dict) else scene_key
            lines.append(f"  - {scene_key}: 최소 {back_per_scene}자 이상 ('{scene_title[:20]}...')")

        lines.extend([
            "",
            "⚠️ 경고: 후반부가 전반부보다 요약되면 REJECT됩니다!",
            "=" * 50,
            ""
        ])

        return "\n".join(lines)

    def _generate_npc_relationship_justification(self, blueprint: dict) -> str:
        """
        [V60.8-2] NPC 관계 단계별 정당화 가이드 생성

        relationship_changes에서 2단계 이상 점프 감지 시 정당화 단계 제시
        """
        if not blueprint or not isinstance(blueprint, dict):
            return ""

        relationship_changes = blueprint.get('relationship_changes', [])
        if not relationship_changes:
            return ""

        # 관계 상태 우선순위 (숫자가 높을수록 긍정적)
        STATE_PRIORITY = {
            "멸시": 0, "적대": 1, "무시": 2, "의심": 3, "경계": 4,
            "중립": 5, "호기심": 6, "경외": 7, "호감": 8, "충성": 9, "추종": 10
        }

        # 전환에 필요한 정당화 패턴
        JUSTIFICATION_PATTERNS = {
            (0, 7): ["압도적 무력 시연", "목숨 구해줌", "적을 처단"],
            (0, 9): ["목숨을 걸고 지켜줌 + 압도적 실력 증명"],
            (2, 7): ["예상 밖의 실력 증명", "지혜로운 문제 해결"],
            (2, 9): ["여러 차례 실력 증명 + 품성 확인"],
            (3, 7): ["의심이 경외로 바뀌는 결정적 사건 필요"],
            (4, 9): ["신뢰 회복 사건 + 능력 증명"],
        }

        jump_guides = []

        for change in relationship_changes:
            if not isinstance(change, dict):
                continue

            target = change.get('target', '알수없음')
            from_state = change.get('from', '')
            to_state = change.get('to', '')

            from_priority = STATE_PRIORITY.get(from_state, 5)
            to_priority = STATE_PRIORITY.get(to_state, 5)
            jump_size = to_priority - from_priority

            # 2단계 이상 점프 감지
            if jump_size >= 2:
                # 중간 단계 제안
                intermediate_states = []
                for state, priority in sorted(STATE_PRIORITY.items(), key=lambda x: x[1]):
                    if from_priority < priority < to_priority:
                        intermediate_states.append(state)

                # 정당화 패턴 찾기
                key = (from_priority, to_priority)
                justifications = JUSTIFICATION_PATTERNS.get(key, ["강력한 서사적 근거 필요"])

                guide = [
                    f"",
                    f"📌 '{target}' 관계 전환: {from_state} → {to_state} ({jump_size}단계 점프)",
                    f"   ⚠️ 급격한 전환은 REJECT 사유입니다!",
                    f"",
                    f"   권장 단계적 전환:",
                ]

                if intermediate_states:
                    for i, state in enumerate(intermediate_states[:2]):
                        guide.append(f"     {i+1}. {from_state} → {state}: [정당화 이유 작성]")
                    guide.append(f"     {len(intermediate_states[:2])+1}. {intermediate_states[-1] if intermediate_states else from_state} → {to_state}: [정당화 이유 작성]")
                else:
                    guide.append(f"     1. {from_state} → {to_state}: [강력한 정당화 필요]")

                guide.append(f"")
                guide.append(f"   정당화 예시: {', '.join(justifications)}")

                jump_guides.append("\n".join(guide))

        if not jump_guides:
            return ""

        header = [
            "",
            "=" * 50,
            "[V60.8 NPC 관계 전환 정당화 가이드]",
            "=" * 50,
        ]

        footer = [
            "",
            "=" * 50,
            ""
        ]

        return "\n".join(header + jump_guides + footer)

    def _generate_item_acquisition_timeline(self, blueprint: dict, episode_bibles: list = None) -> str:
        """
        [V60.8-3] 아이템/무공 획득 시점 명시화

        현재 소지 아이템과 습득 무공의 획득 시점(화 번호)을 명시적으로 전달
        """
        lines = []

        # Blueprint에서 현재 소지품 추출
        current_inventory = []
        current_skills = []

        if blueprint and isinstance(blueprint, dict):
            protagonist_state = blueprint.get('protagonist_state', {})
            if isinstance(protagonist_state, dict):
                current_inventory = protagonist_state.get('inventory', [])
                current_skills = protagonist_state.get('skills', []) or protagonist_state.get('martial_arts', [])

        # Episode Bible에서 획득 시점 추출
        item_timeline = {}
        skill_timeline = {}

        if episode_bibles:
            for eb in episode_bibles:
                if not isinstance(eb, dict):
                    continue
                ep_num = eb.get('ep_num', 0)
                new_items = eb.get('new_items', [])
                if isinstance(new_items, list):
                    for item in new_items:
                        item_name = item.get('name', item) if isinstance(item, dict) else str(item)
                        if item_name and item_name not in item_timeline:
                            item_timeline[item_name] = ep_num

        if not current_inventory and not current_skills:
            return ""

        lines = [
            "",
            "=" * 50,
            "[V60.8 아이템/무공 획득 타임라인]",
            "=" * 50,
        ]

        if current_inventory:
            lines.append("")
            lines.append("📦 현재 소지 아이템:")
            for item in current_inventory[:10]:  # 최대 10개
                item_name = item.get('name', item) if isinstance(item, dict) else str(item)
                acquired_ep = item_timeline.get(item_name, "?")
                lines.append(f"  - {item_name} (제{acquired_ep}화 획득)")
            lines.append("")
            lines.append("⚠️ 위 아이템 외의 것을 사용하면 REJECT됩니다!")

        if current_skills:
            lines.append("")
            lines.append("⚔️ 습득 무공:")
            for skill in current_skills[:10]:
                skill_name = skill.get('name', skill) if isinstance(skill, dict) else str(skill)
                acquired_ep = skill_timeline.get(skill_name, "기본")
                lines.append(f"  - {skill_name} (제{acquired_ep}화 습득)")
            lines.append("")
            lines.append("⚠️ 미습득 무공/비급 사용은 REJECT됩니다!")

        lines.extend([
            "",
            "=" * 50,
            ""
        ])

        return "\n".join(lines)

    def _generate_temporal_spatial_guide(self, blueprint: dict, prev_manuscript: str = "") -> str:
        """
        [V60.8-4] 시간/공간 연속성 가이드

        이전 화 끝 시점(시간, 장소)을 명시적으로 전달
        """
        lines = []

        # Blueprint에서 시간/공간 정보 추출
        time_flow = ""
        start_location = ""

        if blueprint and isinstance(blueprint, dict):
            time_flow = blueprint.get('time_flow', '')
            start_location = blueprint.get('start_location', '') or blueprint.get('location', '')

        # 이전 원고에서 마지막 시간/장소 추출 (정규식 기반)
        prev_time = ""
        prev_location = ""

        if prev_manuscript:
            import re
            # 시간 패턴 추출
            time_patterns = [
                r'(다음\s*날|그날\s*밤|새벽|아침|정오|저녁|밤|자정|해질\s*무렵)',
                r'(\d+일\s*후|\d+일\s*뒤|며칠\s*후|한\s*달\s*후)',
            ]
            for pattern in time_patterns:
                matches = re.findall(pattern, prev_manuscript[-2000:])
                if matches:
                    prev_time = matches[-1] if isinstance(matches[-1], str) else matches[-1][0]
                    break

            # 장소 패턴 추출
            location_patterns = [
                r'(객잔|주막|산장|동굴|광장|저택|성문|시장|숲|산|강가|절벽|무림맹|사파)',
            ]
            for pattern in location_patterns:
                matches = re.findall(pattern, prev_manuscript[-2000:])
                if matches:
                    prev_location = matches[-1]
                    break

        if not (time_flow or prev_time or prev_location or start_location):
            return ""

        lines = [
            "",
            "=" * 50,
            "[V60.8 시간/공간 연속성 가이드]",
            "=" * 50,
        ]

        if prev_time or prev_location:
            lines.append("")
            lines.append("📍 이전 화 마지막 상황:")
            if prev_time:
                lines.append(f"  - 시간: {prev_time}")
            if prev_location:
                lines.append(f"  - 장소: {prev_location}")

        if time_flow or start_location:
            lines.append("")
            lines.append("📍 현재 화 시작 상황:")
            if time_flow:
                lines.append(f"  - 시간 흐름: {time_flow}")
            if start_location:
                lines.append(f"  - 시작 장소: {start_location}")

        lines.extend([
            "",
            "⚠️ 시간/공간 연속성 주의사항:",
            "  - 순간이동 금지 (장소 이동 시 이동 과정 묘사)",
            "  - 시간 역행 금지 (이전 화보다 과거 시점 불가)",
            "  - 같은 날 과다 이벤트 주의 (하루에 대형 사건 2개 이상 지양)",
            "",
            "=" * 50,
            ""
        ])

        return "\n".join(lines)

    def _generate_cliche_avoidance_guide(self, cliche_check_result: dict = None) -> str:
        """
        [V60.8-5] 클리셰 회피 가이드

        클리셰 밀도 초과 시 구체적 회피 대안 제시
        """
        # 기본 클리셰 회피 패턴 (Pre-Director Checklist와 연동)
        CLICHE_ALTERNATIVES = {
            "눈이 번쩍": ["시야가 환해지며", "정신이 맑아지며", "깨달음이 스쳤다"],
            "몸이 굳어": ["움직임이 멈추며", "발이 땅에 박힌 듯", "숨이 멎는 듯"],
            "심장이 멎": ["가슴이 조여들며", "피가 얼어붙는 듯한", "등줄기에 한기가"],
            "피가 끓어": ["분노가 차올랐다", "억누른 감정이 폭발", "참았던 것이 터졌다"],
            "입꼬리가 올라": ["미소를 머금었다", "만족한 표정", "흐뭇함이 번졌다"],
            "전율이": ["몸이 떨렸다", "긴장이 흘렀다", "압도당하는 느낌"],
            "살기가": ["위협적인 기운", "날카로운 눈빛", "공격 의지가"],
            "기세가": ["분위기가 압도", "존재감이 팽창", "무게감이 실렸다"],
        }

        lines = [
            "",
            "=" * 50,
            "[V60.8 클리셰 회피 가이드]",
            "=" * 50,
            "",
            "🚫 과다 사용 금지 표현 (1000자당 3회 미만 유지):",
            ""
        ]

        # 클리셰 대안 제시
        for cliche, alternatives in list(CLICHE_ALTERNATIVES.items())[:8]:
            lines.append(f"  '{cliche}' → {', '.join(alternatives[:2])}")

        lines.extend([
            "",
            "💡 클리셰 회피 원칙:",
            "  1. 감정을 직접 서술하지 말고 행동/반응으로 보여주기",
            "  2. 동일 표현 연속 사용 금지 (최소 500자 간격)",
            "  3. 신체 반응 묘사 다양화 (심장/눈/피 외에 다른 부위)",
            "",
            "=" * 50,
            ""
        ])

        return "\n".join(lines)

    def _generate_writer_guidance_v60_8(
        self,
        blueprint: dict,
        prev_manuscript: str = "",
        episode_bibles: list = None,
        cliche_check_result: dict = None,
        target_len: int = 5000
    ) -> str:
        """
        [V60.8] Writer 사전 가이드 통합 생성

        5개 가이드를 통합하여 Writer에게 전달:
        1. High Impact Zone 분량 가이드
        2. NPC 관계 정당화 가이드
        3. 아이템/무공 타임라인
        4. 시간/공간 연속성 가이드
        5. 클리셰 회피 가이드
        """
        guides = []

        # 1. High Impact Zone 분량 가이드
        hiz_guide = self._generate_high_impact_zone_guide(blueprint, target_len)
        if hiz_guide:
            guides.append(hiz_guide)

        # 2. NPC 관계 정당화 가이드
        relationship_guide = self._generate_npc_relationship_justification(blueprint)
        if relationship_guide:
            guides.append(relationship_guide)

        # 3. 아이템/무공 타임라인
        item_guide = self._generate_item_acquisition_timeline(blueprint, episode_bibles)
        if item_guide:
            guides.append(item_guide)

        # 4. 시간/공간 연속성 가이드
        temporal_guide = self._generate_temporal_spatial_guide(blueprint, prev_manuscript)
        if temporal_guide:
            guides.append(temporal_guide)

        # 5. 클리셰 회피 가이드 (첫 시도에만)
        cliche_guide = self._generate_cliche_avoidance_guide(cliche_check_result)
        if cliche_guide:
            guides.append(cliche_guide)

        if not guides:
            return ""

        return "\n".join(guides)

    # ═══════════════════════════════════════════════════════════════════════════
    # [V60.9] Analyst/Architect 피드백 시스템 - Stage 2/3 PASS율 향상
    # ═══════════════════════════════════════════════════════════════════════════

    def _generate_structured_arc_feedback(
        self,
        continuity_result: dict,
        prev_arcs: list = None,
        arc_no: int = 1
    ) -> str:
        """
        [V60.9-1] Arc 검증 결과를 구조화된 Analyst 피드백으로 변환

        ContinuityInspector.inspect_arc() 결과를 행동 지시로 변환
        """
        if not continuity_result:
            return ""

        violations = continuity_result.get('violations', [])
        if not violations:
            return ""

        lines = [
            "",
            "=" * 60,
            f"[V60.9 Arc {arc_no} 검증 결과 - 필수 수정 사항]",
            "=" * 60,
        ]

        # 위반 유형별 분류
        item_violations = []
        npc_violations = []
        state_violations = []
        timeline_violations = []

        for v in violations:
            v_type = v.get('type', 'unknown')
            v_desc = v.get('description', '')
            v_item = v.get('item_or_subject', '')
            v_loc = v.get('location', '')

            violation_entry = {
                'type': v_type,
                'desc': v_desc[:150],
                'item': v_item,
                'location': v_loc
            }

            if 'item' in v_type.lower() or 'acquisition' in v_type.lower():
                item_violations.append(violation_entry)
            elif 'npc' in v_type.lower() or 'relationship' in v_type.lower():
                npc_violations.append(violation_entry)
            elif 'state' in v_type.lower() or 'injury' in v_type.lower():
                state_violations.append(violation_entry)
            else:
                timeline_violations.append(violation_entry)

        # 아이템 관련 위반
        if item_violations:
            lines.append("")
            lines.append("📦 [아이템 타임라인 오류]")
            for v in item_violations[:3]:
                lines.append(f"  ❌ {v['item'] or '알수없음'}: {v['desc']}")
                if v['location']:
                    lines.append(f"     → 문제 위치: {v['location']}")
            lines.append("")
            lines.append("  💡 수정 방법:")
            lines.append("     - 이미 획득한 아이템을 다시 획득하는 장면 삭제")
            lines.append("     - 대신 '소지 중' 상태로 시작하여 '사용' 장면으로 대체")

        # NPC 관련 위반
        if npc_violations:
            lines.append("")
            lines.append("👤 [NPC/관계 오류]")
            for v in npc_violations[:3]:
                lines.append(f"  ❌ {v['item'] or '알수없음'}: {v['desc']}")
            lines.append("")
            lines.append("  💡 수정 방법:")
            lines.append("     - 사망한 NPC 재등장 삭제")
            lines.append("     - 관계 급변 시 중간 단계 추가 (멸시→의심→경외)")

        # 상태 관련 위반
        if state_violations:
            lines.append("")
            lines.append("💊 [상태 연속성 오류]")
            for v in state_violations[:3]:
                lines.append(f"  ❌ {v['desc']}")
            lines.append("")
            lines.append("  💡 수정 방법:")
            lines.append("     - 부상 상태 유지 (즉시 완치 금지)")
            lines.append("     - 내공 회복에 최소 2-3화 필요")

        # 기타 타임라인 위반
        if timeline_violations:
            lines.append("")
            lines.append("⏱️ [타임라인 오류]")
            for v in timeline_violations[:3]:
                lines.append(f"  ❌ {v['desc']}")

        # 이전 Arc 상태 요약
        if prev_arcs:
            last_arc = prev_arcs[-1] if prev_arcs else {}
            joint_docs = last_arc.get('joint_docs', {})
            if joint_docs:
                lines.append("")
                lines.append("=" * 60)
                lines.append(f"[직전 Arc 확정 상태 - 반드시 계승]")
                lines.append("=" * 60)
                lines.append(f"  📍 위치: {joint_docs.get('final_location', '미정')}")
                lines.append(f"  📦 소지품: {joint_docs.get('physical_inventory', '미정')}")
                if joint_docs.get('world_joint'):
                    lines.append(f"  🌍 세계 상태: {joint_docs.get('world_joint', '')[:100]}")

        lines.extend([
            "",
            "=" * 60,
            ""
        ])

        return "\n".join(lines)

    def _generate_structured_blueprint_feedback(
        self,
        director_result: dict,
        blueprint: dict = None,
        retry_count: int = 0
    ) -> str:
        """
        [V60.9-2] Blueprint 검증 결과를 구조화된 Architect 피드백으로 변환

        Director score_breakdown을 구체적 행동 지시로 변환
        """
        if not director_result:
            return ""

        score_breakdown = director_result.get('score_breakdown', {})
        if not score_breakdown:
            return ""

        lines = [
            "",
            "=" * 60,
            f"[V60.9 Blueprint 검증 결과 - 우선순위별 수정 지침]",
            "=" * 60,
        ]

        # 점수 분석
        issues = []

        # 설정 일관성
        setting_score = score_breakdown.get('setting_consistency', 100)
        if setting_score < 15:
            issues.append({
                'priority': 'CRITICAL',
                'area': '설정 일관성',
                'score': setting_score,
                'action': '미습득 무공/미획득 아이템 사용 장면 삭제. HUD 확인 필수.'
            })
        elif setting_score < 18:
            issues.append({
                'priority': 'HIGH',
                'area': '설정 일관성',
                'score': setting_score,
                'action': '직전 화 상태와 불일치하는 설정 수정'
            })

        # 장면 구성
        scene_score = score_breakdown.get('scene_composition', 100)
        if scene_score < 10:
            issues.append({
                'priority': 'CRITICAL',
                'area': '장면 구성',
                'score': scene_score,
                'action': f'장면 수 부족. 최소 5개 이상 설계 필요.'
            })
        elif scene_score < 15:
            issues.append({
                'priority': 'HIGH',
                'area': '장면 구성',
                'score': scene_score,
                'action': '장면 밀도 불균형. 각 씬 분량을 균등하게 조정.'
            })

        # 서사 흐름
        flow_score = score_breakdown.get('narrative_flow', 100)
        if flow_score < 10:
            issues.append({
                'priority': 'CRITICAL',
                'area': '서사 흐름',
                'score': flow_score,
                'action': '서사 폭주/정체 감지. 사건 분배 재조정 필요.'
            })
        elif flow_score < 15:
            issues.append({
                'priority': 'HIGH',
                'area': '서사 흐름',
                'score': flow_score,
                'action': '같은 장소 3씬 이상 연속 금지. 위치 변화 추가.'
            })

        # 분량
        length_score = score_breakdown.get('length_fulfillment', 100)
        if length_score < 10:
            issues.append({
                'priority': 'CRITICAL',
                'area': '분량',
                'score': length_score,
                'action': '설계 분량 절대 부족. 각 씬 목표 분량 명시.'
            })

        # 우선순위 정렬
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
        issues.sort(key=lambda x: priority_order.get(x['priority'], 3))

        if issues:
            lines.append("")
            for i, issue in enumerate(issues[:5], 1):
                priority_emoji = "🔴" if issue['priority'] == 'CRITICAL' else "🟠"
                lines.append(f"{i}. {priority_emoji} [{issue['priority']}] {issue['area']} ({issue['score']}점)")
                lines.append(f"   → 조치: {issue['action']}")
                lines.append("")
        else:
            lines.append("")
            lines.append("✅ 주요 문제 없음. 세부 품질 개선 집중.")

        # 재시도 횟수별 가이드
        lines.append("=" * 60)
        if retry_count == 0:
            lines.append("[첫 시도] 완벽한 설계를 목표로 하되, 위 이슈 우선 해결")
        elif retry_count == 1:
            lines.append("[2차 시도] CRITICAL/HIGH 이슈만 집중 해결")
        else:
            lines.append(f"[{retry_count + 1}차 시도] 최소 기준 충족에 집중 (CRITICAL만 해결)")

        lines.extend([
            "=" * 60,
            ""
        ])

        return "\n".join(lines)

    def _generate_reverse_feedback_stage4_to_3(
        self,
        writer_reject_reason: str,
        pre_checklist_result: dict = None
    ) -> str:
        """
        [V60.9-3] Stage 4→3 역방향 피드백

        Writer REJECT 시 다음 회차 Architect에게 전달할 피드백
        """
        if not writer_reject_reason:
            return ""

        lines = [
            "",
            "=" * 50,
            "[V60.9 이전 원고 REJECT 피드백 - Blueprint 설계 참고]",
            "=" * 50,
        ]

        # REJECT 사유 분석
        reason_lower = writer_reject_reason.lower()

        if '후반' in reason_lower or '요약' in reason_lower or '밀도' in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 후반부 밀도 부족")
            lines.append("   → 이번 Blueprint: Scene 5-6에 더 많은 이벤트 배치")
            lines.append("   → 각 씬 목표 분량을 명시적으로 설정")

        if '분량' in reason_lower or '짧' in reason_lower or '부족' in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 전체 분량 부족")
            lines.append("   → 이번 Blueprint: 씬 수 6개 이상 확보")
            lines.append("   → 각 씬에 세부 비트 2-3개 추가")

        if '설정' in reason_lower or '모순' in reason_lower or '일관' in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 설정 모순")
            lines.append("   → 이번 Blueprint: HUD/직전 화 상태 명시적 기재")
            lines.append("   → 사용 가능한 아이템/무공 목록 포함")

        if '대화' in reason_lower or '지문' in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 대화/지문 비율 불균형")
            lines.append("   → 이번 Blueprint: 각 씬에 대화 장면 최소 1개 포함")

        # Pre-checklist 결과 반영
        if pre_checklist_result:
            failed_checks = [c for c in pre_checklist_result.get('items', [])
                           if not c.get('passed', True)]
            if failed_checks:
                lines.append("")
                lines.append("📋 Pre-Checklist 실패 항목:")
                for check in failed_checks[:3]:
                    lines.append(f"   - {check.get('name', 'unknown')}: {check.get('message', '')[:50]}")

        lines.extend([
            "",
            "=" * 50,
            ""
        ])

        return "\n".join(lines)

    def _generate_reverse_feedback_stage3_to_2(
        self,
        architect_failures: list = None,
        arc_no: int = 1
    ) -> str:
        """
        [V60.9-4] Stage 3→2 역방향 피드백

        Architect 3회 이상 실패 시 Analyst에게 Arc 수정 필요 정보 전달
        """
        if not architect_failures or len(architect_failures) < 3:
            return ""

        lines = [
            "",
            "=" * 50,
            f"[V60.9 Arc {arc_no} Blueprint 설계 반복 실패 - Arc 재검토 필요]",
            "=" * 50,
            "",
            f"⚠️ Blueprint 설계가 {len(architect_failures)}회 연속 실패했습니다.",
            "   Arc 수준에서 구조적 문제가 있을 수 있습니다.",
            "",
        ]

        # 실패 패턴 분석
        failure_reasons = {}
        for failure in architect_failures:
            reason = failure.get('reason', 'unknown')
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        if failure_reasons:
            lines.append("📊 반복된 실패 사유:")
            for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1])[:3]:
                lines.append(f"   - {reason}: {count}회")

        lines.extend([
            "",
            "💡 Arc 수정 권장 사항:",
            "   1. 아이템/NPC 배치 시점 재검토",
            "   2. 씬 간 의존성 단순화",
            "   3. 핵심 갈등 요소 명확화",
            "",
            "=" * 50,
            ""
        ])

        return "\n".join(lines)

    def _generate_arc_context_v60(
        self,
        all_refined_arcs: list,
        current_arc_no: int = None
    ) -> str:
        """
        [V60.10] StateExtractor를 활용한 Arc 컨텍스트 생성

        이전 Arc들의 상태를 구조화하여 추출하고,
        다음 Arc 설계 시 명확한 제약으로 주입

        Args:
            all_refined_arcs: 이전에 완료된 Arc 리스트
            current_arc_no: 현재 설계 중인 Arc 번호

        Returns:
            구조화된 제약 프롬프트 문자열
        """
        if not all_refined_arcs:
            return "서사 시작점"

        try:
            # StateExtractor 사용 시도
            state_extractor = self.agents.get('state_extractor')
            if state_extractor:
                # 누적 상태 추출
                cumulative_state = state_extractor.extract_cumulative_state(all_refined_arcs)
                # 제약 프롬프트 생성
                constraint_prompt = state_extractor.generate_constraint_prompt(cumulative_state)

                self._audit_event("v60_10_state_extracted", "StateExtractor generated context", {
                    "arc_count": len(all_refined_arcs),
                    "items_tracked": len(cumulative_state.get('inventory', {}).get('current_items', []))
                })

                return constraint_prompt

        except Exception as se_err:
            self._audit_event("v60_10_state_extractor_error", "StateExtractor failed, using fallback", {
                "error": str(se_err)[:100]
            })
            self.ui.log(f"      ⚠️ [V60.10] StateExtractor 실패, Python 폴백 사용: {str(se_err)[:50]}")

        # 폴백: 기존 Python 기반 추출
        return self._generate_arc_context_fallback(all_refined_arcs)

    def _generate_arc_context_fallback(self, all_refined_arcs: list) -> str:
        """[V60.10] StateExtractor 실패 시 Python 기반 폴백"""
        import re

        last_arc = all_refined_arcs[-1]
        joint_docs = last_arc.get('joint_docs', {})
        status_shadow = last_arc.get('status_shadow', {})
        # [V60.13 FIX] arc_end_state 우선 사용
        state_constraints = last_arc.get('state_constraints', {})
        arc_end_state = state_constraints.get('arc_end_state', {})

        # 전체 Arc에서 획득한 아이템 목록 수집
        all_acquired_items = []
        all_grants_received = []

        for prev_arc in all_refined_arcs:
            # state_constraints에서 획득 아이템 추출
            state_constraints = prev_arc.get('state_constraints', {})
            items_acquired = state_constraints.get('items_acquired', [])
            if items_acquired:
                for item in items_acquired:
                    if item and item not in all_acquired_items:
                        all_acquired_items.append(f"Arc{prev_arc.get('arc_no')}: {item}")

            # joint_docs.physical_inventory에서 추가 추출
            prev_joint = prev_arc.get('joint_docs', {})
            prev_inventory = prev_joint.get('physical_inventory', [])
            if isinstance(prev_inventory, list):
                for item in prev_inventory:
                    item_names_only = [x.split(': ', 1)[-1] if ': ' in x else x for x in all_acquired_items]
                    if item and item not in item_names_only:
                        all_acquired_items.append(f"Arc{prev_arc.get('arc_no')}: {item}")
            elif isinstance(prev_inventory, str) and prev_inventory:
                item_names_only = [x.split(': ', 1)[-1] if ': ' in x else x for x in all_acquired_items]
                if prev_inventory not in item_names_only:
                    all_acquired_items.append(f"Arc{prev_arc.get('arc_no')}: {prev_inventory}")

            # tactical_doc에서 수여물 패턴 추출
            tactical = prev_arc.get('tactical_doc', '')
            for pattern_compiled, suffix in GRANT_PATTERNS_COMPILED:
                matches = pattern_compiled.findall(tactical)
                for match in matches:
                    grant_item = match if isinstance(match, str) else match[0] if match else None
                    if grant_item and grant_item not in str(all_grants_received):
                        all_grants_received.append(f"Arc{prev_arc.get('arc_no')}: {grant_item}")

        # 내공 누적 계산
        korean_hal = {'일': 10, '이': 20, '삼': 30, '사': 40, '오': 50, '육': 60, '칠': 70, '팔': 80, '구': 90}
        korean_pun = {'일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9}

        total_energy_consumed = 0
        energy_history = []

        for prev_arc in all_refined_arcs:
            prev_status = prev_arc.get('status_shadow', {})
            energy_loss_str = str(prev_status.get('internal_energy_loss', '0%'))

            match = re.search(r'(\d+)%', energy_loss_str)
            if match:
                loss = int(match.group(1))
                total_energy_consumed += loss
                energy_history.append(f"Arc{prev_arc.get('arc_no')}: -{loss}%")
            else:
                loss = 0
                for k, v in korean_hal.items():
                    if f'{k}할' in energy_loss_str or f'{k} 할' in energy_loss_str:
                        loss += v
                        break
                for k, v in korean_pun.items():
                    if f'{k}푼' in energy_loss_str or f'{k} 푼' in energy_loss_str:
                        loss += v
                        break
                if loss > 0:
                    total_energy_consumed += loss
                    energy_history.append(f"Arc{prev_arc.get('arc_no')}: -{loss}%")

        # [V60.13 FIX] arc_end_state에서 정확한 최종 값 추출
        final_energy = arc_end_state.get('internal_energy')
        if final_energy is None:
            # 폴백: 누적 소모량 계산 (하위 호환)
            final_energy = max(0, 100 - total_energy_consumed)

        # [V60.23] 내공 바닥 방지 - 숫자로 변환 후 최소값 보장
        try:
            final_energy = int(str(final_energy).replace('%', '').strip())
        except (ValueError, TypeError):
            final_energy = 50  # 파싱 실패 시 기본값

        # 살아있는 무협 주인공 최소 내공 10% (폐인/사망 아닌 이상)
        if final_energy < 10:
            final_energy = max(10, final_energy)  # 최소 10%

        final_injuries = arc_end_state.get('injuries') or status_shadow.get('expected_injuries', '없음')
        final_location = arc_end_state.get('location') or joint_docs.get('final_location', '알 수 없음')
        final_equipment = arc_end_state.get('equipment') or joint_docs.get('physical_inventory', '알 수 없음')

        acquired_items_str = "\n   ".join(all_acquired_items) if all_acquired_items else "없음"
        grants_str = "\n   ".join(all_grants_received) if all_grants_received else "없음"
        energy_history_str = " → ".join(energy_history) if energy_history else "소모 없음"

        return (
            f"[직전 아크 {last_arc.get('arc_no')} 결말 상태]:\n"
            f"══════════════════════════════════════\n"
            f"🔴🔴🔴 [필수 계승 - 다음 Arc 시작 조건] 🔴🔴🔴\n"
            f"[⚡ 최종 내공]: {final_energy}% ← 다음 Arc는 이 값으로 시작해야 함\n"
            f"[💔 최종 부상]: {final_injuries} ← 이 상태로 시작해야 함\n"
            f"[🗺️ 최종 위치]: {final_location}\n"
            f"[📦 최종 소지품]: {final_equipment}\n"
            f"══════════════════════════════════════\n"
            f"[🌍 세계 변화]: {joint_docs.get('world_joint', '알 수 없음')}\n"
            f"[🧪 소모 아이템]: {status_shadow.get('item_consumption', '없음')}\n"
            f"[📊 내공 소모 이력]: {energy_history_str}\n"
            f"══════════════════════════════════════\n"
            f"🚨🚨🚨 [중복 획득 절대 금지 목록] 🚨🚨🚨\n"
            f"아래 아이템들은 이미 이전 Arc에서 획득 완료되었습니다.\n"
            f"다시 획득하러 가거나, 다시 수여받는 설정은 CRITICAL 위반입니다:\n"
            f"   {acquired_items_str}\n"
            f"══════════════════════════════════════\n"
            f"🏅 [이미 수여받은 권한/패]:\n"
            f"   {grants_str}\n"
            f"══════════════════════════════════════\n"
            f"[📜 핵심 전술 요약]: {last_arc.get('tactical_doc', '')[:600]}...\n"
            f"══════════════════════════════════════\n"
            f"🚨 [CONTINUITY LOCK] 위 상태는 절대 무시하거나 리셋할 수 없습니다. "
            f"현재 아크는 위 종료 시점에서 단 1초의 공백 없이 이어져야 합니다."
        )

    def _get_adaptive_feedback_intensity(self, retry_count: int, stage: int = 4) -> dict:
        """
        [V60.9-5] 적응형 피드백 강도 조절

        재시도 횟수에 따라 피드백 상세도와 PASS 기준 동적 조절
        """
        if stage == 2:  # Analyst (Arc 설계)
            if retry_count == 0:
                return {
                    'pass_threshold': 70,
                    'feedback_level': 'detailed',  # 상세한 예시 포함
                    'strictness': 'high',
                    'guidance': '완벽한 Arc 설계를 목표로 합니다. 모든 제약 조건을 준수하세요.'
                }
            elif retry_count == 1:
                return {
                    'pass_threshold': 65,
                    'feedback_level': 'focused',  # 핵심 이슈만
                    'strictness': 'medium',
                    'guidance': 'CRITICAL 이슈만 해결하세요. 부가적 품질은 차후 개선.'
                }
            else:
                return {
                    'pass_threshold': 55,
                    'feedback_level': 'minimal',  # 최소 기준만
                    'strictness': 'low',
                    'guidance': '최소 기준 충족에 집중하세요. 아이템/NPC 타임라인만 정확히.'
                }

        elif stage == 3:  # Architect (Blueprint 설계)
            if retry_count == 0:
                return {
                    'pass_threshold': 70,
                    'feedback_level': 'detailed',
                    'strictness': 'high',
                    'guidance': '6개 이상의 균형 잡힌 씬을 설계하세요.'
                }
            elif retry_count == 1:
                return {
                    'pass_threshold': 60,
                    'feedback_level': 'focused',
                    'strictness': 'medium',
                    'guidance': '핵심 씬 5개 확보, 설정 일관성 유지에 집중.'
                }
            else:
                return {
                    'pass_threshold': 50,
                    'feedback_level': 'minimal',
                    'strictness': 'low',
                    'guidance': '최소 4개 씬, 기본 연속성만 확보하세요.'
                }

        else:  # Stage 4 (Writer)
            if retry_count == 0:
                return {
                    'pass_threshold': 70,
                    'feedback_level': 'detailed',
                    'strictness': 'high',
                    'guidance': '5000자 이상, 균형 잡힌 씬 분배를 목표로.'
                }
            elif retry_count == 1:
                return {
                    'pass_threshold': 65,
                    'feedback_level': 'focused',
                    'strictness': 'medium',
                    'guidance': '4500자 이상, 핵심 씬 반영에 집중.'
                }
            else:
                return {
                    'pass_threshold': 55,
                    'feedback_level': 'minimal',
                    'strictness': 'low',
                    'guidance': '4000자 최소 기준, Blueprint 핵심만 반영.'
                }

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
            enricher = BlockEnricher(self.current_project, self.sys.api_client, model_tier="gemini-3-flash-preview")

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

            # 5. 주인공 이름 추출 (Bible에서)
            protagonist_name = "주인공"
            try:
                bible_path = Path("bibles")
                bible_files = list(bible_path.glob("*.json"))
                if bible_files:
                    with open(bible_files[0], 'r', encoding='utf-8') as f:
                        bible_data = json.load(f)
                    bible_root = bible_data.get('MasterBible', bible_data)
                    hud = bible_root.get('MartialHUD', {})
                    protag = hud.get('Protagonist', {})
                    actual = protag.get('actual_truth', {})
                    protagonist_name = actual.get('name', '주인공')
            except Exception:
                pass

            # 6. 장르 확인
            genre = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'

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

            # 결과 정리 (enrichment_metadata 제거)
            enriched_blocks = []
            for i, block in enumerate(enriched_blocks_raw):
                if block is None:
                    enriched_blocks.append(treatment_blocks[i])
                elif isinstance(block, dict):
                    clean_block = {
                        "block_id": block.get("block_id", f"Block {i+1}"),
                        "title": block.get("title", ""),
                        "content": block.get("content", {})
                    }
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
            
            default_model = "gemini-3-pro-preview"  # [V60.24] 모든 에이전트 기본값 Gemini 3
            
            self.agents = {
                'analyst': Analyst(self.current_project, self.sys.api_client, model_tier=models.get("analyst", default_model)),
                'architect': Architect(self.current_project, self.sys.api_client, model_tier=models.get("architect", default_model)),
                'writer': Writer(self.current_project, self.sys.api_client, model_tier=models.get("writer", default_model)),
                'director': Director(self.current_project, self.sys.api_client, model_tier=models.get("director", default_model)),
                'manager': Manager(self.current_project, self.sys.api_client, model_tier=models.get("manager", default_model)),
                # [V45 Fix] weaver는 manager가 아닌 weaver 모델 사용 (fallback: manager)
                'weaver': Weaver(self.current_project, self.sys.api_client, model_tier=models.get("weaver", models.get("manager", default_model))),
                # [V48.1] ContinuityInspector - Director 산하 연속성 검증 에이전트 (2.5-pro 모델, 전체 BP 분석)
                'continuity_inspector': ContinuityInspector(self.current_project, self.sys.api_client, model_tier="gemini-3-pro-preview"),  # [V60.13] 생성 티어와 동급
                # [V52.2] Critic - 원고 비평 에이전트 (빠른 모델 사용)
                'critic': Critic(self.current_project, self.sys.api_client, model_tier="gemini-2.0-flash"),
                # [V60.10] StateExtractor - 상태 추출 에이전트 (빠른 모델로 구조화된 상태 추출)
                'state_extractor': StateExtractor(self.current_project, self.sys.api_client, model_tier="gemini-3-flash-preview"),  # [V60.24] Flash (추출용)
                # [V60.11] ArcEnsembleGenerator - Arc 앙상블 생성기 (3개 후보 병렬 생성)
                'arc_ensemble': ArcEnsembleGenerator(self.current_project, self.sys.api_client, model_tier="gemini-3-pro-preview"),  # [V60.24] Gemini 3
                # [V60.12] FourPhaseArcGenerator - 4단계 Arc 생성 파이프라인 (초기 통과율 극대화)
                'four_phase': FourPhaseArcGenerator(self.current_project, self.sys.api_client, model_tier="gemini-3-pro-preview"),  # [V60.24] Gemini 3
                # [V60.14] StateLockedArcGenerator - 상태 잠금 Arc 생성기 (구조적 모순 불가)
                'state_locked': StateLockedArcGenerator(self.current_project, self.sys.api_client, model_tier="gemini-3-pro-preview"),  # [V60.24] Gemini 3
                # [V60.12] PreflightChecker - 생성 전 완벽 분석
                'preflight': PreflightChecker(self.current_project, self.sys.api_client, model_tier="gemini-3-flash-preview"),  # [V60.24] Flash (분석용)
                # [V60.12] ArcCritic - Arc 즉시 비평
                'arc_critic': ArcCritic(self.current_project, self.sys.api_client, model_tier="gemini-3-pro-preview"),  # [V60.24] Gemini 3
                # [V60.12] ConsensusValidator - 3-LLM 합의 검증
                'consensus': ConsensusValidator(self.current_project, self.sys.api_client, model_tier="gemini-3-pro-preview"),  # [V60.24] Gemini 3
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
                model_tier="gemini-3-flash-preview"  # 경량 모델 사용
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
            except Exception:
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

                    # V50.1 긴장감 곡선 관리자
                    self.tension_manager = TensionCurveManager()

                    # V50.2 대화 DNA 엔진
                    self.dialogue_engine = DialogueQualityEngine()

                    # V50.3 서브플롯 관리자
                    self.subplot_weaver = SubplotWeaver()

                    # V50.4 독자 시뮬레이터
                    self.reader_simulator = ReaderSimulator()

                    # V51.1 호흡 분석기
                    self.pacing_analyzer = PacingAnalyzer()

                    # V51.2 품질 증폭기
                    self.quality_amplifier = QualityAmplifier()

                    # V51.3 에이전트 지능 향상
                    self.agent_intelligence = AgentIntelligence(genre=genre_type)

                    # V51.4 실패 학습 시스템
                    self.failure_learner = FailureLearner()
                    # 프로젝트별 실패 기록 로드 시도
                    failure_log_path = os.path.join(
                        "projects", name, "logs", "failure_learning.json"
                    )
                    if os.path.exists(failure_log_path):
                        self.failure_learner.load_from_json(failure_log_path)
                        self.ui.log(f"   📚 [V51.4] 실패 기록 {len(self.failure_learner.records)}건 로드")

                    # V51.5 캐릭터 음성 추적
                    self.character_voice = CharacterVoiceTracker()
                    voice_log_path = os.path.join(
                        "projects", name, "logs", "character_voice.json"
                    )
                    if os.path.exists(voice_log_path):
                        self.character_voice.load_from_json(voice_log_path)
                        self.ui.log(f"   🎭 [V51.5] 캐릭터 음성 {len(self.character_voice.profiles)}명 로드")

                    # V51.6 복선 추적
                    self.foreshadow_tracker = ForeshadowTracker()
                    foreshadow_log_path = os.path.join(
                        "projects", name, "logs", "foreshadow.json"
                    )
                    if os.path.exists(foreshadow_log_path):
                        self.foreshadow_tracker.load_from_json(foreshadow_log_path)
                        stats = self.foreshadow_tracker.get_stats()
                        self.ui.log(f"   🔮 [V51.6] 복선 {stats['total']}개 로드 (활성: {stats['active']}, 회수율: {stats['payoff_rate']}%)")

                    # ============================================================
                    # [V60.26] 품질 향상 모듈 (미사용 → 활성화)
                    # ============================================================

                    # V60.26-1 감정선 추적
                    self.emotion_tracker = EmotionArcTracker(self.current_project)
                    emotion_log_path = os.path.join("projects", name, "logs", "emotion_arc.json")
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
                    voice_profiler_path = os.path.join("projects", name, "logs", "voice_profiles.json")
                    if os.path.exists(voice_profiler_path):
                        try:
                            with open(voice_profiler_path, 'r', encoding='utf-8') as f:
                                profiles_data = json.load(f)
                                for name_key, profile_data in profiles_data.items():
                                    self.voice_profiler.add_profile(name_key, profile_data)
                            self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 로드 ({len(self.voice_profiler.profiles)}명)")
                        except Exception:
                            self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 활성화")
                    else:
                        self.ui.log(f"   🎭 [V60.26] 캐릭터 음성 프로파일러 활성화")

                    # V52.1 자기 성찰 체인
                    self.self_reflector = SelfReflector(
                        api_client=self.sys.api_client,
                        model="gemini-2.0-flash"  # 빠른 모델 사용
                    )
                    self.ui.log(f"   🔄 [V52.1] Self-Reflection Chain 활성화")

                    # V52.3 전문가 혼합
                    self.expert_mixture = ExpertMixture(genre=genre_type)
                    self.ui.log(f"   🎯 [V52.3] Expert Mixture 활성화 ({genre_type})")

                    # V52.4 교차 에이전트 검증
                    self.cross_verifier = CrossAgentVerifier(
                        api_client=self.sys.api_client,
                        model="gemini-2.0-flash"  # 빠른 모델 사용
                    )
                    self.ui.log(f"   🔗 [V52.4] Cross-Agent Verifier 활성화")

                    # V53.1 동적 프롬프트 가중치
                    self.prompt_weighter = DynamicPromptWeighter(failure_learner=self.failure_learner)
                    self.ui.log(f"   ⚖️ [V53.1] Dynamic Prompt Weighter 활성화")

                    # V53.2 사실 검증 체인
                    self.chain_of_verification = ChainOfVerification(
                        api_client=self.sys.api_client,
                        model="gemini-2.0-flash"
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
                        model="gemini-3-pro-preview"  # [V60.24] Stage 2 Gemini 3
                    )
                    self.ui.log(f"   🌳 [V53.5] Tree of Thoughts 활성화 (Gemini 3)")

                    # V53.6 적대적 자기 대결
                    self.adversarial_self_play = AdversarialSelfPlay(
                        api_client=self.sys.api_client,
                        model="gemini-2.0-flash"
                    )
                    self.ui.log(f"   ⚔️ [V53.6] Adversarial Self-Play 활성화")

                    # V53.7 다중 에이전트 토론
                    self.multi_agent_deliberation = MultiAgentDeliberation(
                        api_client=self.sys.api_client,
                        model="gemini-2.0-flash"
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

                    # V54.4 2단계 원고 생성
                    self.two_phase_ms = TwoPhaseManuscriptGenerator(
                        client=self.sys.api_client,
                        model="gemini-2.0-flash"
                    )
                    self.ui.log(f"   ✌️ [V54.4] Two-Phase Manuscript Generator 활성화")

                    # V54.4.1 2단계 블루프린트 생성
                    self.two_phase_bp = TwoPhaseBlueprintGenerator(
                        client=self.sys.api_client,
                        model="gemini-2.5-flash"
                    )
                    self.ui.log(f"   📐 [V54.4.1] Two-Phase Blueprint Generator 활성화")

                    # V55.1+V60.10 2단계 Arc 생성 (Stage 2 전용, StateExtractor 통합)
                    self.two_phase_arc = TwoPhaseArcGenerator(
                        client=self.sys.api_client,
                        model="gemini-3-pro-preview",  # [V60.24] Stage 2 Gemini 3
                        state_extractor=self.agents.get('state_extractor')  # [V60.10] StateExtractor 통합
                    )
                    self.ui.log(f"   🏗️ [V55.1+V60.10] Two-Phase Arc Generator 활성화 (Gemini 3, StateExtractor 통합)")

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
        [V50] 기존 에피소드 데이터를 V50 모듈에 로드

        - 긴장도 기록: 기존 블루프린트에서 tension_level 추출
        - 대화 DNA: 기존 원고에서 캐릭터 대사 학습
        - 서브플롯: 기존 아크에서 서브플롯 정보 추출
        """
        if not V50_MODULES_AVAILABLE:
            return

        try:
            # 1. 기존 원고에서 긴장도/대사 학습
            manuscripts = self.current_project.db.get_all_manuscripts() or []
            for ms in manuscripts[-10:]:  # 최근 10개만 로드 (성능)
                ep_num = ms.get('ep_num', 0)
                text = ms.get('text', '')

                if text and self.dialogue_engine:
                    # 주인공 대사 학습 (간단 추출)
                    protagonist_name = self._get_protagonist_name()
                    if protagonist_name:
                        self.dialogue_engine.learn_character(protagonist_name, text)

            # 2. 블루프린트에서 긴장도 기록
            blueprints = self.current_project.db.get_all_blueprints() or []
            for bp in blueprints[-20:]:  # 최근 20개
                ep_num = bp.get('ep_num', 0)
                data = bp.get('data', {})
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        continue

                tension_level = data.get('tension_level', data.get('긴장도', 5))
                if self.tension_manager and ep_num > 0:
                    self.tension_manager.record_tension(
                        episode=ep_num,
                        level=tension_level if isinstance(tension_level, int) else 5,
                        description=data.get('cliffhanger', '')
                    )

            # 3. 아크에서 서브플롯 추출
            arcs_data = self.current_project.db.load_anchor("arcs") or []
            for arc in arcs_data[-5:]:  # 최근 5개 아크
                subplots = arc.get('subplots', arc.get('서브플롯', []))
                if isinstance(subplots, list) and self.subplot_weaver:
                    for sp in subplots:
                        if isinstance(sp, dict):
                            self.subplot_weaver.register_subplot(
                                name=sp.get('name', sp.get('제목', 'unknown')),
                                subplot_type=sp.get('type', 'character'),
                                description=sp.get('description', sp.get('설명', ''))
                            )

            loaded_count = len(manuscripts[-10:]) + len(blueprints[-20:])
            if loaded_count > 0:
                self.ui.log(f"   📚 [V50] 히스토리 로드: 원고 {len(manuscripts[-10:])}개, BP {len(blueprints[-20:])}개")

        except Exception as e:
            self.ui.log(f"   ⚠️ [V50] 히스토리 로드 실패 (비치명적): {e}")

    def _get_protagonist_name(self) -> str:
        """주인공 이름 추출 (bible에서)"""
        try:
            bible = self.current_project.db.load_anchor("bible") or {}
            chars = bible.get('characters', bible.get('등장인물', []))
            if chars and isinstance(chars, list) and len(chars) > 0:
                first_char = chars[0]
                if isinstance(first_char, dict):
                    return first_char.get('name', first_char.get('이름', '주인공'))
                return str(first_char)
            return '주인공'
        except:
            return '주인공'

    def _process_v50_post_episode(self, ep_num: int, manuscript: str, blueprint: dict) -> None:
        """
        [V50] 에피소드 완료 후 서사 품질 피드백 처리

        - V50.1 긴장도 기록 및 곡선 분석
        - V50.2 대사 DNA 학습
        - V50.3 서브플롯 업데이트
        - V50.4 독자 시뮬레이션 피드백
        """
        if not V50_MODULES_AVAILABLE:
            return

        feedback_summary = []

        # V50.1: 긴장도 기록
        if self.tension_manager:
            try:
                tension_level = blueprint.get('tension_level', blueprint.get('긴장도', 5))
                if isinstance(tension_level, str):
                    tension_level = 5
                cliffhanger = blueprint.get('cliffhanger', '')

                self.tension_manager.record_tension(
                    episode=ep_num,
                    level=tension_level,
                    description=cliffhanger
                )

                # 아크 경계에서 곡선 분석
                if ep_num % 5 == 0:  # 매 5화마다 (아크 끝)
                    arc_num = ep_num // 5
                    curve_analysis = self.tension_manager.validate_arc_curve(arc_num)
                    if curve_analysis.get('warnings'):
                        for w in curve_analysis['warnings'][:2]:
                            feedback_summary.append(f"긴장곡선: {w}")
            except Exception as t_err:
                self.ui.log(f"      ⚠️ [V50.1] 긴장도 기록 실패: {t_err}")

        # V50.2: 대사 DNA 학습
        if self.dialogue_engine:
            try:
                protagonist = self._get_protagonist_name()
                self.dialogue_engine.learn_character(protagonist, manuscript)
            except Exception as d_err:
                self.ui.log(f"      ⚠️ [V50.2] 대사 학습 실패: {d_err}")

        # V50.3: 서브플롯 업데이트
        if self.subplot_weaver:
            try:
                # 서브플롯 진행 상태 업데이트
                neglected = self.subplot_weaver.get_neglected_subplots(threshold_episodes=3)
                if neglected:
                    for sp in neglected[:2]:
                        feedback_summary.append(f"서브플롯 방치: '{sp.name}' ({sp.episodes_since_update}화 방치)")
            except Exception as s_err:
                self.ui.log(f"      ⚠️ [V50.3] 서브플롯 분석 실패: {s_err}")

        # V50.4: 독자 시뮬레이션
        if self.reader_simulator:
            try:
                sim_results = self.reader_simulator.simulate_all_readers(manuscript)
                avg_score = sum(r.engagement_score for r in sim_results) / len(sim_results) if sim_results else 0

                # 문제 지점 피드백
                for result in sim_results:
                    if result.drop_flags:
                        for flag in result.drop_flags[:1]:  # 독자당 1개만
                            feedback_summary.append(f"독자({result.reader_type.value}): {flag}")

                if avg_score < 70:
                    feedback_summary.append(f"독자 평균 점수: {avg_score:.0f}/100 (경고)")
                else:
                    self.ui.log(f"      📖 [V50.4] 독자 평균 점수: {avg_score:.0f}/100")

            except Exception as r_err:
                self.ui.log(f"      ⚠️ [V50.4] 독자 시뮬레이션 실패: {r_err}")

        # V51.1: 호흡 분석 (LLM 비용 0원)
        if self.pacing_analyzer:
            try:
                pacing = self.pacing_analyzer.analyze(manuscript)
                if pacing.pacing_score < 70:
                    feedback_summary.append(f"호흡 점수: {pacing.pacing_score}/100")
                    for issue in pacing.issues[:2]:
                        feedback_summary.append(f"호흡: {issue}")
                else:
                    self.ui.log(f"      📝 [V51.1] 호흡 점수: {pacing.pacing_score}/100 (대화:{pacing.dialogue_ratio:.0%})")
            except Exception as p_err:
                self.ui.log(f"      ⚠️ [V51.1] 호흡 분석 실패: {p_err}")

        # V51.5: 캐릭터 음성 분석
        if self.character_voice:
            try:
                voice_result = self.character_voice.analyze_manuscript(ep_num, manuscript)
                if voice_result.get('characters_analyzed', 0) > 0:
                    self.ui.log(f"      🎭 [V51.5] 캐릭터 {voice_result['characters_analyzed']}명, 대사 {voice_result['total_dialogues']}개 분석")
            except Exception as cv_err:
                self.ui.log(f"      ⚠️ [V51.5] 캐릭터 음성 분석 실패: {cv_err}")

        # 피드백 요약 출력
        if feedback_summary:
            self.ui.log(f"      📊 [V50] 서사 품질 피드백 {len(feedback_summary)}건:")
            for fb in feedback_summary[:5]:  # 최대 5개
                self.ui.log(f"         └ {fb}")

            # 오디트 이벤트 기록
            self._audit_event("v50_feedback", "narrative quality feedback", {
                "ep_num": ep_num,
                "feedback_count": len(feedback_summary),
                "items": feedback_summary[:5]
            })

    def _generate_v50_writer_prompt(self, ep_num: int, blueprint: dict) -> str:
        """
        [V50] Writer를 위한 서사 품질 프롬프트 생성

        - V50.1: 긴장도 가이드
        - V50.2: 대사 DNA 가이드
        - V50.3: 서브플롯 리마인더
        """
        if not V50_MODULES_AVAILABLE:
            return ""

        prompts = []

        # V50.1: 긴장도 가이드
        if self.tension_manager:
            try:
                suggestion = self.tension_manager.suggest_next_tension(ep_num)
                if suggestion.get('suggestion'):
                    prompts.append(f"[V50 긴장도 가이드]\n{suggestion['suggestion']}")
            except Exception:
                pass

        # V50.2: 대사 DNA 가이드
        if self.dialogue_engine:
            try:
                protagonist = self._get_protagonist_name()
                dialogue_prompt = self.dialogue_engine.generate_dialogue_prompt(protagonist)
                if dialogue_prompt:
                    prompts.append(f"[V50 대사 가이드]\n{dialogue_prompt}")
            except Exception:
                pass

        # V50.3: 서브플롯 리마인더
        if self.subplot_weaver:
            try:
                neglected = self.subplot_weaver.get_neglected_subplots(threshold_episodes=3)
                if neglected:
                    reminders = []
                    for sp in neglected[:2]:
                        beat = self.subplot_weaver.suggest_subplot_beat(sp.name)
                        if beat:
                            reminders.append(f"- '{sp.name}': {beat}")
                    if reminders:
                        prompts.append(f"[V50 서브플롯 리마인더]\n다음 서브플롯을 진행시켜주세요:\n" + "\n".join(reminders))
            except Exception:
                pass

        # V51.1: 호흡 가이드 (이전 분석 기반)
        if self.pacing_analyzer and self.pacing_analyzer.history:
            try:
                pacing_prompt = self.pacing_analyzer.generate_pacing_prompt()
                if pacing_prompt:
                    prompts.append(pacing_prompt)
            except Exception:
                pass

        # V51.5: 캐릭터 음성 가이드
        if self.character_voice and self.character_voice.profiles:
            try:
                voice_prompt = self.character_voice.get_writer_injection()
                if voice_prompt:
                    prompts.append(voice_prompt)
            except Exception:
                pass

        # V51.6: 복선 관리 가이드
        if self.foreshadow_tracker:
            try:
                foreshadow_prompt = self.foreshadow_tracker.generate_writer_prompt(ep_num)
                if foreshadow_prompt:
                    prompts.append(foreshadow_prompt)
            except Exception:
                pass

        # V52.3: 씬별 전문가 가이드
        if self.expert_mixture and blueprint:
            try:
                expert_prompt = self.expert_mixture.generate_writer_injection(blueprint)
                if expert_prompt:
                    prompts.append(expert_prompt)
            except Exception:
                pass

        # [V60.5] 자가 진단 체크리스트 주입
        try:
            self_diagnosis = self._generate_self_diagnosis_checklist(blueprint)
            if self_diagnosis:
                prompts.append(self_diagnosis)
        except Exception:
            pass

        if prompts:
            return "\n\n".join(prompts)
        return ""

    def _generate_self_diagnosis_checklist(self, blueprint: dict) -> str:
        """
        [V60.5] Writer 자가 진단 체크리스트 생성

        Blueprint 정보를 기반으로 맞춤형 체크리스트 생성
        """
        lines = [
            "[V60.5 자가 진단 체크리스트 - 제출 전 필수 확인]",
            "원고 제출 전 아래 항목을 스스로 점검하라:",
            ""
        ]

        # Blueprint 기반 씬 정보 추출
        scene_count = 6
        if blueprint and isinstance(blueprint, dict):
            scene_breakdown = blueprint.get('scene_breakdown', {})
            scene_count = len(scene_breakdown) if scene_breakdown else 6

        lines.append(f"📏 분량: 4,500자 이상 목표 (4,000자 미만 = 즉시 REJECT)")
        lines.append(f"🎬 장면: {scene_count}개 씬 모두 균등 반영 (앞만 상세하고 뒤 요약 금지)")
        lines.append(f"🔄 흐름: 서사 폭주(1~2장면에 해결) 또는 정체(3장면+ 반복) 금지")
        lines.append(f"⚙️ 설정: 미습득 무공 사용 금지, 핵심 인물 이름 유지")
        lines.append(f"✍️ 문체: 대화 4개+, 감각 묘사 포함, 시점 전환 활용")
        lines.append("")
        lines.append("⚠️ 3개 이상 미충족 시 REJECT 확률 80%")

        return "\n".join(lines)

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

        # [V49.4] Pre-Generation Constraint DB 초기화
        constraint_db = ConstraintDB(self.current_project)
        self.ui.log(f"🔒 [V49.4] ConstraintDB 초기화 완료 (기존 Arc: {len(constraint_db.arc_states)}개)")

        # 2. 배치(Batch) 처리 루프 시작
        for batch_start in range(done_count, target_limit, 5):
            batch_end = min(batch_start + 5, target_limit)
            batch_start_count = len(all_refined_arcs)  # 배치 시작 시 Arc 개수 추적
            self.ui.log(f"📦 [Batch] {batch_start + 1}~{batch_end}번 구간 욕망 수혈 공정 가동...")

            # [V60.10] 수혈 맥락 준비 - StateExtractor 활용
            last_refined_context = self._generate_arc_context_v60(all_refined_arcs, batch_start + 1)
            if all_refined_arcs:
                self.ui.log(f"      🧠 [V60.10] StateExtractor: {len(all_refined_arcs)}개 Arc 상태 추출 완료")

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

            # [V60.45] while 루프로 변경 - "다시 하기" 지원
            idx = 0
            while idx < len(enriched_batch):
                enriched_block = enriched_batch[idx]
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

                # [V49.4] Pre-Generation Constraint 생성
                constraint_block = constraint_db.generate_constraint_block(global_arc_no)
                if constraint_block:
                    self.ui.log(f"      🔒 [V49.4] Arc {global_arc_no} 제약 조건 주입됨")

                # [V60.11] ConstraintCompiler로 구조화된 체크리스트 생성
                if hasattr(self, 'constraint_compiler') and all_refined_arcs:
                    try:
                        # StateExtractor 결과 가져오기 (있으면)
                        state_result = None
                        if 'state_extractor' in self.agents:
                            try:
                                state_result = self.agents['state_extractor'].extract_cumulative_state(all_refined_arcs)
                            except Exception:
                                pass

                        compiled_constraints = self.constraint_compiler.compile(all_refined_arcs, state_result)
                        constraint_block = compiled_constraints + "\n\n" + (constraint_block or "")
                        self.ui.log(f"      📋 [V60.11] ConstraintCompiler 체크리스트 생성 완료")
                    except Exception as cc_err:
                        self._audit_event("v60_11_constraint_compiler_error", str(cc_err)[:100])

                # [V60.45] while 루프로 변경 - "다시 하기" 지원
                attempt = 0
                max_attempts = RetryLimits.ANALYST_MAX_ATTEMPTS
                while attempt < max_attempts:
                    # [V60.43] 검증 통과 추적 플래그 초기화
                    draft_validator_passed = False
                    consensus_passed = False

                    # [V55.4] 3회 실패 후 10초 대기 → 4회차 최종 시도
                    if attempt == 3:
                        self.ui.log(f"   ⏸️ [V55.4] 3회 실패. 10초 대기 후 4회차 최종 시도...")
                        self._audit_event("stage2_cooldown", "3 rejects, waiting 10s before final attempt", {
                            "arc_no": global_arc_no,
                            "attempt": attempt
                        })
                        time.sleep(10)  # 10초 대기 (API 안정화)
                        current_feedback = f"[🚨 최종 시도] 이전 3회 모두 실패. Arc 설계의 근본적 문제 해결 필요.\n{current_feedback}"

                    # [V60.10] 이전 시도 REJECT 패턴 분석 (2회차 이상 시 적용)
                    if attempt >= 1 and self.stage_rejection_history:
                        arc_rejections = [r for r in self.stage_rejection_history
                                         if r.get('stage') == 2 and r.get('arc_no') == global_arc_no]
                        if arc_rejections:
                            pattern_analysis = self._analyze_rejection_pattern_v60(arc_rejections, global_arc_no)
                            if pattern_analysis:
                                current_feedback = pattern_analysis + "\n" + current_feedback
                                self.ui.log(f"      🔍 [V60.10] REJECT 패턴 분석 주입 ({len(arc_rejections)}건)")

                    self.ui.log(f"   {Emojis.BRAIN} [Arc {global_arc_no}] 전술 설계 중 (시도 {attempt+1}/{RetryLimits.ANALYST_MAX_ATTEMPTS})...")

                    recent_patterns = [
                        a.get('hybrid_composition', {}).get('primary')
                        for a in all_refined_arcs
                        if a.get('hybrid_composition', {}).get('primary')
                    ]

                    # [V49.4] 제약 블록을 prev_arc_context에 주입
                    enhanced_context = last_refined_context
                    if constraint_block:
                        enhanced_context = constraint_block + "\n" + last_refined_context

                    # [V60.25] Stage 2 Optimizer 주입
                    if hasattr(self, 'stage2_optimizer') and self.stage2_optimizer:
                        try:
                            optimizer_prompt = self.stage2_optimizer.generate_optimized_prompt(
                                prev_arcs=all_refined_arcs,
                                protagonist_name=protagonist_name or "주인공",
                                include_examples=(attempt == 0)  # 첫 시도에서만 예시 포함
                            )
                            enhanced_context = optimizer_prompt + "\n\n" + enhanced_context
                            if attempt == 0:
                                self.ui.log(f"      ⚡ [V60.25] Stage 2 Optimizer 프롬프트 주입 완료")
                        except Exception as opt_err:
                            self._audit_event("v60_25_optimizer_error", str(opt_err)[:100])

                    # [V60.21] Focus Mode: 재시도 시 컨텍스트 최소화
                    # 첫 시도: 모든 주입 적용
                    # 재시도: 피드백 + 이전 상태만 (LLM이 이미 규칙을 알고 있음)
                    is_retry = attempt > 0 and current_feedback

                    # [V51] Analyst 지능 향상 주입 - 첫 시도에서만!
                    v51_analyst_injection = ""
                    if V50_MODULES_AVAILABLE and not is_retry:  # [V60.21] 재시도 시 스킵
                        try:
                            # V51.2 품질 제약 주입
                            if self.quality_amplifier:
                                analyst_constraints = self.quality_amplifier.generate_analyst_constraints(
                                    arc_num=global_arc_no,
                                    prev_arcs=all_refined_arcs
                                )
                                v51_analyst_injection += analyst_constraints + "\n\n"

                            # V51.3 지능 향상 주입 (Few-Shot + Anti-Pattern)
                            if self.agent_intelligence:
                                intel_prompt = self.agent_intelligence.get_analyst_enhancement(
                                    arc_num=global_arc_no,
                                    prev_arcs=all_refined_arcs
                                )
                                v51_analyst_injection += intel_prompt + "\n\n"

                            # V51.4 실패 학습 제약 주입
                            if self.failure_learner:
                                learned_constraints = self.failure_learner.generate_constraint_prompt(stage=2)
                                if learned_constraints:
                                    v51_analyst_injection += learned_constraints

                            # V55.2 Constitutional Self-Check 주입
                            if self.constitutional_checker:
                                constitutional_prompt = self.constitutional_checker.get_full_injection(
                                    stage=2,
                                    context={
                                        'prev_arcs': all_refined_arcs,
                                        'feedback': current_feedback
                                    }
                                )
                                v51_analyst_injection = constitutional_prompt + "\n\n" + v51_analyst_injection

                            if v51_analyst_injection:
                                enhanced_context = v51_analyst_injection + "\n\n" + enhanced_context
                                self.ui.log(f"      🧠 [V51+V55.2] Analyst 지능 향상 + Constitutional 주입 완료")
                        except Exception as v51_err:
                            self.ui.log(f"      ⚠️ [V51] Analyst 향상 실패: {v51_err}")

                    # [V60.21] Focus Mode: 재시도 시 컨텍스트 대폭 축소
                    if is_retry:
                        # 재시도: 피드백 + 이전 Arc 최소 정보만!
                        # LLM은 이미 규칙을 알고 있음 → 핵심만 전달
                        minimal_prev_context = self._build_minimal_arc_context(all_refined_arcs, protagonist_name or "주인공")
                        enhanced_context = f"{current_feedback}\n\n{minimal_prev_context}"
                        context_size = len(enhanced_context)
                        self.ui.log(f"      📢 [V60.21] Focus Mode 활성화 - 컨텍스트 {context_size}자 (최소화)")

                    # [V60.9] Stage 3→2 역방향 피드백 주입 (동일 Arc에서 Blueprint 3회 이상 실패 시)
                    try:
                        if self.stage_rejection_history:
                            # 이 Arc에서 발생한 Stage 3 실패 목록
                            arc_stage3_failures = [r for r in self.stage_rejection_history
                                                   if r.get('stage') == 3 and r.get('arc_no') == global_arc_no]
                            if len(arc_stage3_failures) >= 3:
                                # 3회 이상 실패 시 역방향 피드백 생성
                                reverse_feedback_3to2 = self._generate_reverse_feedback_stage3_to_2(
                                    architect_failures=arc_stage3_failures,
                                    arc_no=global_arc_no
                                )
                                if reverse_feedback_3to2:
                                    stage3_warning = f"\n\n🔄 [V60.9 Stage 3→2 역방향 피드백]\n"
                                    stage3_warning += f"이 Arc(#{global_arc_no})에서 Blueprint 설계가 {len(arc_stage3_failures)}회 실패했습니다.\n"
                                    stage3_warning += f"Arc 구조 자체에 문제가 있을 수 있습니다.\n\n"
                                    stage3_warning += f"[Blueprint 실패 패턴 분석]\n{reverse_feedback_3to2}\n"
                                    enhanced_context = stage3_warning + "\n" + enhanced_context
                                    self.ui.log(f"      🔄 [V60.9] Stage 3→2 역방향 피드백 주입 ({len(arc_stage3_failures)}회 실패 기반)")
                    except Exception as rf32_err:
                        self._audit_event("v60_9_stage3to2_error", "stage 3→2 reverse feedback failed", {"error": str(rf32_err)[:100]})

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.36] Analyst 강화 - Director 검수 통과를 위한 무장
                    # 1. Preflight: 이전 Arc 완전 분석 (무기 #1)
                    # 2. ConstraintCompiler: 제약 명확화 (무기 #2)
                    # 3. DraftValidator: 즉시 사전 검증 (무기 #3)
                    # 4. Consensus: 최종 검증
                    # 5. attempt >= 2: ToT/TwoPhase 필살기
                    # ═══════════════════════════════════════════════════════════════

                    refined_arc = None
                    generation_method = "analyst"
                    analyst_weapons = {}  # Analyst에게 제공할 무기들

                    print(f"\n      {'='*60}")
                    print(f"      [V60.36] Arc {global_arc_no} 생성 시작 (attempt {attempt + 1})")
                    print(f"      {'='*60}")

                    # ─────────────────────────────────────────────────────────────
                    # [무기 #1] Preflight 분석 - 이전 Arc 상태 완전 파악
                    # ─────────────────────────────────────────────────────────────
                    preflight_injection = ""
                    if 'preflight' in self.agents and all_refined_arcs:
                        try:
                            print(f"      🔍 [무기 #1] Preflight 분석 시작...")
                            # [V60.47] LLM 호출 중 스피너 표시
                            with rich_console.status(f"[bold green]🔍 Preflight 분석 중...[/]", spinner="dots"):
                                preflight_result = self.agents['preflight'].analyze(all_refined_arcs)
                            if preflight_result:
                                preflight_injection = self.agents['preflight'].generate_analyst_injection(preflight_result)
                                analyst_weapons['preflight'] = preflight_result
                                print(f"      ✅ [Preflight] 분석 완료:")
                                print(f"         - 아이템 타임라인: {len(preflight_result.get('item_timeline', []))}개")
                                print(f"         - 금지 사항: {len(preflight_result.get('absolute_prohibitions', []))}개")
                                print(f"         - 관계 맵: {len(preflight_result.get('relationship_map', {}))}명")
                        except Exception as pf_err:
                            print(f"      ⚠️ [Preflight] 스킵: {str(pf_err)[:50]}")

                    # ─────────────────────────────────────────────────────────────
                    # [무기 #2] ConstraintCompiler - 명확한 제약 체크리스트
                    # ─────────────────────────────────────────────────────────────
                    constraint_block = ""
                    if hasattr(self, 'constraint_compiler') and all_refined_arcs:
                        try:
                            print(f"      📋 [무기 #2] ConstraintCompiler 컴파일 중...")
                            state_result = None
                            if 'state_extractor' in self.agents:
                                state_result = self.agents['state_extractor'].extract_cumulative_state(all_refined_arcs)
                            constraint_block = self.constraint_compiler.compile(all_refined_arcs, state_result)
                            analyst_weapons['constraints'] = constraint_block
                            print(f"      ✅ [Constraints] 제약 블록 생성 완료 ({len(constraint_block)}자)")
                        except Exception as cc_err:
                            print(f"      ⚠️ [Constraints] 스킵: {str(cc_err)[:50]}")

                    # ─────────────────────────────────────────────────────────────
                    # [attempt >= 2] 필살기: ToT / TwoPhase
                    # ─────────────────────────────────────────────────────────────
                    if attempt >= 2:
                        print(f"      🔥 [필살기] attempt {attempt + 1} - 서브 에이전트 투입!")

                        # ToT 우선
                        if V50_MODULES_AVAILABLE and self.tree_of_thoughts:
                            try:
                                print(f"      🌳 [ToT] Tree of Thoughts 발동...")
                                tot_result = self.tree_of_thoughts.explore_arc(
                                    arc_no=global_arc_no,
                                    vol_strategy=current_vol_strategy.get('strategy_doc', ''),
                                    curr_block=enriched_block,
                                    prev_arc_context=enhanced_context + "\n" + constraint_block,
                                    assets=bible_root.get('AssetLibrary', {}),
                                    feedback=current_feedback,
                                    num_branches=3,
                                    depth=2,
                                    protagonist_name=protagonist_name or "주인공"
                                )
                                if tot_result and isinstance(tot_result, dict):
                                    refined_arc = tot_result
                                    generation_method = "tot"
                                    print(f"      ✅ [ToT] 성공!")
                            except Exception as tot_err:
                                print(f"      ❌ [ToT] 실패: {str(tot_err)[:80]}")

                        # ToT 실패 시 TwoPhase
                        if refined_arc is None and V50_MODULES_AVAILABLE and self.two_phase_arc:
                            try:
                                print(f"      🏗️ [TwoPhase] 2단계 생성 시도...")
                                two_phase_result = self.two_phase_arc.generate(
                                    arc_no=global_arc_no,
                                    vol_strategy=current_vol_strategy.get('strategy_doc', ''),
                                    curr_block=enriched_block,
                                    prev_arc_context=enhanced_context,
                                    assets=bible_root.get('AssetLibrary', {}),
                                    constraints=current_feedback + "\n" + constraint_block,
                                    prev_arcs=all_refined_arcs,
                                    protagonist_name=protagonist_name or "주인공"
                                )
                                if two_phase_result and isinstance(two_phase_result, dict):
                                    refined_arc = two_phase_result
                                    generation_method = "two_phase"
                                    print(f"      ✅ [TwoPhase] 성공!")
                            except Exception as tp_err:
                                print(f"      ❌ [TwoPhase] 실패: {str(tp_err)[:80]}")

                    # ─────────────────────────────────────────────────────────────
                    # [핵심] Analyst 호출 - 무장된 상태로 Arc 설계
                    # ─────────────────────────────────────────────────────────────
                    if refined_arc is None:
                        try:
                            print(f"      🎯 [Analyst] Arc {global_arc_no} 설계 시작...")

                            # 강화된 컨텍스트 구성
                            enhanced_arc_context = enhanced_context
                            if preflight_injection:
                                enhanced_arc_context = preflight_injection + "\n\n" + enhanced_arc_context
                            if constraint_block:
                                enhanced_arc_context = constraint_block + "\n\n" + enhanced_arc_context

                            print(f"         - 컨텍스트 크기: {len(enhanced_arc_context)}자")
                            print(f"         - 피드백: {current_feedback[:100] if current_feedback else '없음'}...")

                            # [V60.47] LLM 호출 중 스피너 표시
                            with rich_console.status(f"[bold cyan]🤖 Arc {global_arc_no} LLM 생성 중...[/]", spinner="dots"):
                                refined_arc = self.agents['analyst'].plan_single_arc_v20(
                                    arc_no=global_arc_no,
                                    vol_strategy=current_vol_strategy.get('strategy_doc', ''),
                                    prev_block=None,
                                    curr_block=enriched_block,
                                    next_block=None,
                                    ep_start=current_ep_start,
                                    prev_arc_context=enhanced_arc_context,  # 강화된 컨텍스트
                                    assets=bible_root.get('AssetLibrary', {}),
                                    full_roadmap=full_roadmap_str,
                                    assigned_seeds=[],
                                    feedback=current_feedback,
                                    recent_patterns=recent_patterns,
                                    protagonist_name=protagonist_name or "주인공"
                                )
                            generation_method = "analyst"
                            print(f"      ✅ [Analyst] Arc 생성 완료!")

                            # 결과 요약 출력
                            if refined_arc:
                                print(f"         - tactical_doc: {len(refined_arc.get('tactical_doc', ''))}자")
                                print(f"         - ep_count: {refined_arc.get('ep_count', '?')}화")
                                print(f"         - items_acquired: {refined_arc.get('state_constraints', {}).get('items_acquired', [])}")
                        except Exception as analyst_err:
                            print(f"      ❌ [Analyst] 에러: {str(analyst_err)[:100]}")
                            self._audit_event("analyst_error", "plan_single_arc_v20 failed", {
                                "arc_no": global_arc_no,
                                "error": str(analyst_err)
                            })
                            current_feedback = f"Analyst 엔진 오류: {str(analyst_err)[:100]}. 안정적인 JSON 출력을 확보하라."
                            continue

                    # ─────────────────────────────────────────────────────────────
                    # [무기 #3] DraftValidator - 즉시 사전 검증 (LLM 비용 0원)
                    # ─────────────────────────────────────────────────────────────
                    if refined_arc and hasattr(self, 'arc_draft_validator') and self.arc_draft_validator:
                        try:
                            print(f"      🔬 [무기 #3] DraftValidator 사전 검증...")
                            draft_result = self.arc_draft_validator.validate(
                                arc=refined_arc,
                                prev_arcs=all_refined_arcs
                            )
                            if not draft_result.get('valid', True):
                                issues = draft_result.get('issues', [])
                                print(f"      ❌ [DraftValidator] {len(issues)}개 이슈 발견:")
                                for issue in issues[:3]:
                                    severity = issue.get('severity', 'UNKNOWN')
                                    msg = issue.get('message', str(issue))
                                    print(f"         - [{severity}] {msg[:80]}")

                                # CRITICAL 있으면 즉시 재시도
                                critical_issues = [i for i in issues if i.get('severity') == 'CRITICAL']
                                if critical_issues:
                                    print(f"      🔄 [DraftValidator] CRITICAL 발견 - 재시도 유도")
                                    current_feedback = "DraftValidator 검증 실패: " + "; ".join([i.get('message', '')[:50] for i in critical_issues[:2]])
                                    refined_arc = None
                                    continue
                                else:
                                    print(f"      ⚠️ [DraftValidator] WARNING만 있음 - 계속 진행")
                                    draft_validator_passed = True  # [V60.43] WARNING만 있어도 통과 처리
                            else:
                                print(f"      ✅ [DraftValidator] 사전 검증 통과!")
                                draft_validator_passed = True  # [V60.43] 추적 플래그
                        except Exception as dv_err:
                            print(f"      ⚠️ [DraftValidator] 스킵: {str(dv_err)[:50]}")

                    # ─────────────────────────────────────────────────────────────
                    # [V60.36] SelfReflector: Analyst 자기 비판
                    # ─────────────────────────────────────────────────────────────
                    if V50_MODULES_AVAILABLE and self.self_reflector and refined_arc and generation_method == "analyst":
                        try:
                            print(f"      🪞 [SelfReflector] Analyst 자기 비판 시작...")
                            arc_str = json.dumps(refined_arc, ensure_ascii=False, indent=2)
                            context_str = f"Arc {global_arc_no} 설계. 피드백: {current_feedback or '없음'}"

                            reflection_result = self.self_reflector.reflect_and_improve(
                                output=arc_str,
                                context=context_str,
                                target=ReflectionTarget.ANALYST,
                                force=False
                            )

                            if reflection_result and reflection_result.improved != arc_str:
                                try:
                                    improved_arc = json.loads(reflection_result.improved)
                                    refined_arc = improved_arc
                                    print(f"      ✅ [SelfReflector] 자기 개선 완료 (점수: {getattr(reflection_result, 'improvement_score', '?')})")
                                except json.JSONDecodeError:
                                    print(f"      ⚠️ [SelfReflector] 개선 결과 파싱 실패, 원본 유지")
                            else:
                                print(f"      ℹ️ [SelfReflector] 개선 불필요")
                        except Exception as sr_err:
                            print(f"      ⚠️ [SelfReflector] 스킵: {str(sr_err)[:50]}")

                    # ─────────────────────────────────────────────────────────────
                    # [V60.36] Consensus 검증 - 3-LLM 합의
                    # ─────────────────────────────────────────────────────────────
                    if refined_arc and 'consensus' in self.agents:
                        try:
                            print(f"      🗳️ [Consensus] 3-LLM 합의 검증 시작...")
                            # [V60.47] LLM 호출 중 스피너 표시
                            with rich_console.status(f"[bold magenta]🗳️ Consensus 3-LLM 검증 중...[/]", spinner="dots"):
                                consensus_verdict, consensus_result = self.agents['consensus'].validate_with_consensus(
                                    arc=refined_arc,
                                    prev_arcs=all_refined_arcs,
                                    constraints=""
                                )

                            vote_summary = consensus_result.get("vote_summary", {})
                            print(f"         - 투표 결과: PASS {vote_summary.get('pass', 0)} / REJECT {vote_summary.get('reject', 0)}")

                            if consensus_verdict == "REJECT":
                                critical_issues = consensus_result.get("critical_issues", [])
                                all_issues = consensus_result.get("all_issues", [])
                                print(f"      ❌ [Consensus] REJECT!")
                                print(f"         - CRITICAL: {len(critical_issues)}개")
                                print(f"         - 전체 이슈: {len(all_issues)}개")
                                for ci in critical_issues[:3]:
                                    print(f"         🚨 [{ci.get('category', '?')}] {ci.get('issue', '?')[:80]}")

                                # 피드백으로 변환하여 재시도
                                feedback_parts = [f"[{ci.get('category')}] {ci.get('issue')}" for ci in critical_issues[:3]]
                                current_feedback = "Consensus 검증 실패: " + "; ".join(feedback_parts)
                                refined_arc = None
                                print(f"      🔄 재시도 피드백: {current_feedback[:100]}...")
                                continue
                            else:
                                print(f"      ✅ [Consensus] PASS!")
                                consensus_passed = True  # [V60.43] 추적 플래그
                                passed_checks = consensus_result.get("passed_checks", [])
                                if passed_checks:
                                    print(f"         - 통과 항목: {passed_checks[:3]}")
                        except Exception as cv_err:
                            print(f"      ⚠️ [Consensus] 검증 스킵: {str(cv_err)[:50]}")

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

                    # ⚡ [V60.25] Auto-Corrector - 자동 수정 가능한 오류 먼저 수정
                    if hasattr(self, 'stage2_optimizer') and self.stage2_optimizer:
                        try:
                            refined_arc, corrections = self.stage2_optimizer.post_process_arc(
                                arc=refined_arc,
                                prev_arcs=all_refined_arcs
                            )
                            if corrections:
                                self._audit_event("v60_25_auto_correct", "arc auto-corrected", {
                                    "arc_no": global_arc_no,
                                    "corrections": corrections[:5]
                                })
                        except Exception as ac_err:
                            self._audit_event("v60_25_auto_correct_error", str(ac_err)[:100])

                    # 🔒 [V49.4] Pre-Validation: ConstraintDB로 즉시 검증 (무료)
                    pre_validation = constraint_db.validate_arc_design(refined_arc)
                    if not pre_validation['valid']:
                        self.ui.log(f"      🔒 [V49.4 Pre-Check] 제약 위반 감지!")
                        for v in pre_validation['violations'][:2]:
                            self.ui.log(f"         {v}")
                        self._audit_event("constraint_violation", "pre-generation constraint violated", {
                            "arc_no": global_arc_no,
                            "violations": pre_validation['violations'][:3]
                        })
                        # 위반 내용을 피드백에 포함하여 재생성 유도
                        violation_summary = "; ".join(pre_validation['violations'][:2])
                        current_feedback = f"[제약 위반] {violation_summary}. 이미 획득한 아이템을 다시 획득하지 마십시오."
                        continue

                    # 경고만 있는 경우 로그 출력
                    if pre_validation['warnings']:
                        for w in pre_validation['warnings'][:2]:
                            self.ui.log(f"      ⚠️ [V49.4 Warning] {w}")

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
                            refined_arc = None  # [V60.10 Fix] 다음 시도에서 Analyst 재호출 보장
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

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.11] Arc Draft 빠른 사전 검증 (Python 기반, LLM 비용 0원)
                    # ContinuityInspector 호출 전 명백한 오류 필터링
                    # ═══════════════════════════════════════════════════════════════
                    if hasattr(self, 'arc_draft_validator'):
                        draft_result = self.arc_draft_validator.validate(
                            arc=refined_arc,
                            prev_arcs=all_refined_arcs,
                            constraint_block=constraint_block or ""
                        )

                        if not draft_result["valid"]:
                            self.ui.log(f"      🚨 [V60.11 DraftValidator] 사전 검증 실패 (점수: {draft_result['score']})")
                            for issue in draft_result["critical_issues"][:3]:
                                self.ui.log(f"         ❌ {issue}")

                            self._audit_event("draft_validation_reject", "draft validation failed", {
                                "arc_no": global_arc_no,
                                "score": draft_result["score"],
                                "critical_count": len(draft_result["critical_issues"])
                            })

                            # ═══════════════════════════════════════════════════════════════
                            # [V60.42] ArcCorrector - MAJOR만 있을 때 부분 수정 시도
                            # ═══════════════════════════════════════════════════════════════
                            # 이슈 분류: CRITICAL vs MAJOR
                            all_issues = draft_result.get("issues", [])
                            critical_only = [i for i in all_issues if i.get("severity") == "CRITICAL"]
                            major_only = [i for i in all_issues if i.get("severity") in ["MAJOR", "WARNING"]]

                            # CRITICAL이 없고 MAJOR만 있으면 ArcCorrector 시도
                            if not critical_only and major_only and hasattr(self, 'arc_corrector') and self.use_arc_corrector:
                                self.ui.log(f"      🔧 [V60.42] CRITICAL 없음, MAJOR {len(major_only)}개 - ArcCorrector 부분 수정 시도")

                                try:
                                    # 수정 가능 여부 확인 (반환값: bool, correctable_list, uncorrectable_list)
                                    can_correct, correctable_issues, uncorrectable_issues = self.arc_corrector.can_correct(major_only)

                                    if can_correct:
                                        corrected_arc, correction_log = self.arc_corrector.correct(
                                            arc=refined_arc,
                                            issues=major_only,
                                            prev_arcs=all_refined_arcs
                                        )

                                        if corrected_arc and correction_log.get("success"):
                                            # 수정 성공 - 수정된 Arc로 교체
                                            refined_arc = corrected_arc
                                            corrections_made = correction_log.get('corrections_made', [])
                                            corrections_failed = correction_log.get('corrections_failed', [])
                                            self.ui.log(f"      ✅ [V60.42] ArcCorrector 수정 완료 ({len(corrections_made)}개 수정)")
                                            for fix in corrections_made[:3]:
                                                fix_summary = fix.get('change_summary', fix.get('issue', '')[:50])
                                                self.ui.log(f"         🔨 {fix_summary}")

                                            self._audit_event("arc_corrector_success", "arc partially corrected", {
                                                "arc_no": global_arc_no,
                                                "corrections": len(corrections_made),
                                                "failed": len(corrections_failed)
                                            })

                                            # 수정 후 재검증
                                            revalidation = self.arc_draft_validator.validate(
                                                arc=refined_arc,
                                                prev_arcs=all_refined_arcs,
                                                constraint_block=constraint_block or ""
                                            )

                                            if revalidation["valid"]:
                                                self.ui.log(f"      ✅ [V60.42] 수정 후 재검증 통과 (점수: {revalidation['score']})")
                                                # 계속 진행 (continue 안 함)
                                            else:
                                                self.ui.log(f"      ⚠️ [V60.42] 수정 후에도 검증 실패 - 재생성 필요")
                                                issues_str = "\n".join([f"- {i}" for i in revalidation["critical_issues"][:3]])
                                                current_feedback = f"[ArcCorrector 수정 후에도 실패]\n{issues_str}"
                                                refined_arc = None
                                                continue
                                        else:
                                            # 수정 실패 - 재생성
                                            reason = correction_log.get('reason', '알 수 없음')
                                            self.ui.log(f"      ⚠️ [V60.42] ArcCorrector 수정 실패: {reason}")
                                            self._audit_event("arc_corrector_fail", reason, {
                                                "arc_no": global_arc_no
                                            })
                                            # 피드백으로 재시도
                                            issues_str = "\n".join([f"- {i.get('message', str(i))}" for i in major_only[:3]])
                                            current_feedback = f"[V60.42 수정 불가]\n{issues_str}\n재설계 필요."
                                            refined_arc = None
                                            continue
                                    else:
                                        # 수정 불가 (CRITICAL 포함 등)
                                        uncorr_msgs = [i.get('message', '')[:30] for i in uncorrectable_issues[:2]]
                                        self.ui.log(f"      ⚠️ [V60.42] 수정 불가: {', '.join(uncorr_msgs)}")
                                        issues_str = "\n".join([f"- {i.get('message', str(i))}" for i in major_only[:3]])
                                        current_feedback = f"[수정 불가]\n{issues_str}"
                                        refined_arc = None
                                        continue

                                except Exception as corr_err:
                                    self.ui.log(f"      ⚠️ [V60.42] ArcCorrector 오류: {str(corr_err)[:50]}")
                                    self._audit_event("arc_corrector_error", str(corr_err)[:100])
                                    # 오류 시 기존 로직으로 재시도
                                    issues_str = "\n".join([f"- {i}" for i in draft_result["critical_issues"][:5]])
                                    current_feedback = f"[V60.11 검증 실패 + Corrector 오류]\n{issues_str}"
                                    refined_arc = None
                                    continue
                            else:
                                # CRITICAL이 있거나 ArcCorrector 비활성화 - 기존 로직대로 재시도
                                issues_str = "\n".join([f"- {i}" for i in draft_result["critical_issues"][:5]])
                                current_feedback = (
                                    f"[V60.11 DraftValidator 사전 검증 실패]\n"
                                    f"점수: {draft_result['score']}/100\n"
                                    f"문제점:\n{issues_str}\n\n"
                                    f"위 문제를 해결하고 다시 설계하세요."
                                )
                                refined_arc = None
                                continue
                        else:
                            self.ui.log(f"      ✅ [V60.11 DraftValidator] 사전 검증 통과 (점수: {draft_result['score']})")
                            if draft_result["warnings"]:
                                for w in draft_result["warnings"][:2]:
                                    self.ui.log(f"         ⚠️ {w}")

                    # ═══════════════════════════════════════════════════════════════
                    # [V49 NEW] Arc 수준 연속성 검증 - Director 검증 전에 실행
                    # ═══════════════════════════════════════════════════════════════
                    if 'continuity_inspector' in self.agents:
                        self.ui.log(f"      🔍 [V49] Arc {global_arc_no} 연속성 검증 중...")

                        # enriched_block의 joint_docs, status_shadow를 refined_arc에 미리 주입
                        refined_arc['joint_docs'] = enriched_block.get('joint_docs', {})
                        refined_arc['status_shadow'] = enriched_block.get('status_shadow', {})

                        # [V60.47] LLM 호출 중 스피너 표시
                        with rich_console.status(f"[bold yellow]🔍 Arc {global_arc_no} 연속성 검증 중...[/]", spinner="dots"):
                            continuity_result = self.agents['continuity_inspector'].inspect_arc(
                                current_arc=refined_arc,
                                prev_arcs=all_refined_arcs
                            )
                        
                        if continuity_result.get('decision') == 'REJECT':
                            severity = continuity_result.get('severity', 'UNKNOWN')
                            fix_instructions = continuity_result.get('fix_instructions', '')
                            violations = continuity_result.get('violations', [])

                            self.ui.log(f"      🚨 [V49 REJECT] Arc 연속성 위반 감지 (심각도: {severity})")
                            for v in violations[:3]:  # 최대 3개만 로그
                                self.ui.log(f"         - {v.get('type', 'unknown')}: {v.get('description', '')[:100]}")

                            self._audit_event("arc_continuity_reject", "continuity violation detected", {
                                "arc_no": global_arc_no,
                                "severity": severity,
                                "violations_count": len(violations)
                            })

                            # [V51.4] 실패 기록
                            if V50_MODULES_AVAILABLE and self.failure_learner:
                                for v in violations[:3]:
                                    self.failure_learner.record_failure(
                                        stage=2,
                                        episode=current_ep_start,
                                        arc=global_arc_no,
                                        reason=f"{v.get('type', 'unknown')}: {v.get('description', '')[:150]}",
                                        details={"severity": severity, "violation": v}
                                    )

                            # [V60.2] PassRateMonitor: ContinuityInspector REJECT 기록
                            if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                try:
                                    self.pass_rate_monitor.record_attempt(
                                        stage=2,
                                        episode=global_arc_no,
                                        arc=global_arc_no,
                                        attempt_num=attempt + 1,
                                        success=False,
                                        reject_reason=f"ContinuityInspector: {severity} - {violations[0].get('type', '') if violations else 'unknown'}",
                                        generation_method=generation_method
                                    )
                                except Exception:
                                    pass

                            # [V60.25] Stage2Optimizer: 실패 기록 및 집중 피드백 생성
                            if hasattr(self, 'stage2_optimizer') and self.stage2_optimizer:
                                try:
                                    # 실패 패턴 기록 (세션 내 학습)
                                    for v in violations[:3]:
                                        self.stage2_optimizer.failure_memory.record_failure(
                                            arc_no=global_arc_no,
                                            failure_type=v.get('type', 'unknown'),
                                            details=v.get('description', '')[:200]
                                        )
                                except Exception as e:
                                    self.ui.log(f"      ⚠️ [V60.25] 실패 기록 오류 (무시): {str(e)[:50]}")

                            # [V49.6] 구체적인 위반 내용을 피드백에 포함
                            violation_details = []
                            banned_items = []  # 획득 금지 아이템 목록

                            for v in violations[:3]:
                                v_type = v.get('type', 'unknown')
                                v_desc = v.get('description', '')[:200]
                                violation_details.append(f"[{v_type}] {v_desc}")

                                # 중복 획득 위반인 경우 아이템 이름 추출
                                if v_type == 'duplicate_acquisition':
                                    item_name = v.get('item_or_subject', '')
                                    if item_name:
                                        banned_items.append(item_name)

                            detailed_feedback = "\n".join(violation_details)

                            # [V49.7] 획득 금지 목록 생성 (duplicate_acquisition 위반 시)
                            banned_items_warning = ""
                            if banned_items:
                                banned_list = ", ".join(banned_items)
                                banned_items_warning = (
                                    f"\n\n🚫🚫🚫 [획득 금지 아이템 - 절대 준수] 🚫🚫🚫\n"
                                    f"다음 아이템들은 이미 이전 Arc에서 획득했습니다:\n"
                                    f"  → {banned_list}\n\n"
                                    f"[필수 조치]\n"
                                    f"1. 위 아이템을 '획득'하는 장면을 설계하지 마세요.\n"
                                    f"2. 대신 '이미 소지 중'인 상태로 시작하여 '사용'하세요.\n"
                                    f"3. 예: '허리에 찬 백근 대도를 뽑아 들었다' (O)\n"
                                    f"4. 예: '백근 대도를 새로 획득했다' (X - REJECT됨)"
                                )

                            # 이전 Arc 상태 정보 재주입 (Analyst가 참조할 수 있도록)
                            prev_state_reminder = ""
                            if all_refined_arcs:
                                last = all_refined_arcs[-1]
                                last_joint = last.get('joint_docs', {})
                                last_status = last.get('status_shadow', {})
                                prev_state_reminder = (
                                    f"\n\n📌 [직전 Arc {last.get('arc_no', '?')} 확정 상태 - 반드시 계승할 것]:\n"
                                    f"- 위치: {last_joint.get('final_location', '?')}\n"
                                    f"- 소지품: {last_joint.get('physical_inventory', '?')}\n"
                                    f"- 내공 소모: {last_status.get('internal_energy_loss', '?')}\n"
                                    f"- 부상: {last_status.get('expected_injuries', '?')}"
                                )

                            # [V60.9] 구조화된 Arc 피드백 추가
                            structured_arc_feedback = self._generate_structured_arc_feedback(
                                continuity_result=continuity_result,
                                prev_arcs=all_refined_arcs,
                                arc_no=global_arc_no
                            )

                            # [V60.9] 적응형 피드백 강도
                            adaptive_intensity = self._get_adaptive_feedback_intensity(attempt, stage=2)
                            intensity_guide = f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"

                            # [V60.21] 극도로 집중된 피드백 생성 - 정보 과부하 방지!
                            strong_kind_feedback = self._build_strong_kind_feedback(
                                violations=violations,
                                attempt=attempt,
                                protagonist_name=protagonist_name or "주인공"
                            )

                            # [V60.21] 집중된 이전 상태 요약
                            focused_context = self._build_focused_context(
                                violations=violations,
                                prev_arcs=all_refined_arcs,
                                protagonist_name=protagonist_name or "주인공"
                            )

                            # [V60.21] 피드백 = 핵심 지시 + 상태 요약만! (500자 이내)
                            # 기존의 8개 컴포넌트 → 2개로 압축
                            current_feedback = f"{strong_kind_feedback}\n\n{focused_context}"

                            # 로그에 피드백 크기 표시 (디버깅용)
                            feedback_size = len(current_feedback)
                            self.ui.log(f"      📋 [V60.21] 집중 피드백 주입 ({feedback_size}자, 목표: <500자)")
                            refined_arc = None  # [V60.10 Fix] 다음 시도에서 Analyst 재호출 보장
                            attempt += 1  # [V60.51 Fix] ContinuityInspector REJECT 시에도 카운터 증가
                            continue
                        else:
                            # ═══════════════════════════════════════════════════════════════
                            # [V49.2] Joint Docs 자동 수정 반영
                            # ═══════════════════════════════════════════════════════════════
                            corrected_joint_docs = continuity_result.get('corrected_joint_docs')
                            if corrected_joint_docs:
                                refined_arc['joint_docs'] = corrected_joint_docs
                                enriched_block['joint_docs'] = corrected_joint_docs
                                self.ui.log(f"      🔧 [V49.2] joint_docs 자동 수정 반영됨")

                            # [V60.13] Arc Start State 자동 수정 반영
                            corrected_state = continuity_result.get('corrected_state_constraints')
                            if corrected_state:
                                refined_arc['state_constraints'] = corrected_state
                                self.ui.log(f"      🔧 [V60.13] state_constraints 자동 수정 반영됨")

                            warnings = continuity_result.get('warnings', [])
                            if warnings:
                                self.ui.log(f"      ⚠️ [V49] Arc 연속성 경고 {len(warnings)}개 (PASS)")
                            else:
                                self.ui.log(f"      ✅ [V49] Arc 연속성 검증 통과")

                            # [V60.25] Stage2Optimizer: ContinuityInspector PASS 시 성공 예시 저장
                            if hasattr(self, 'stage2_optimizer') and self.stage2_optimizer:
                                try:
                                    self.stage2_optimizer.example_manager.add_successful_arc(
                                        arc=refined_arc,
                                        arc_no=global_arc_no
                                    )
                                    self.ui.log(f"      📚 [V60.25] 성공 Arc 예시 저장됨")
                                except Exception:
                                    pass

                    audit = self.agents['director'].audit_strategic_plan(
                        refined_arc,
                        last_refined_context,
                        curr_block=enriched_block,
                        protagonist_name=protagonist_name  # V42 LOCK
                    )

                    # ═══════════════════════════════════════════════════════════════
                    # [V60.43] API 할당량 오류 시 폴백 로직
                    # DraftValidator와 Consensus가 이미 통과했다면, Director의
                    # Self-Consistency 점수가 할당량 오류로 인해 0인 경우 PASS로 오버라이드
                    # ═══════════════════════════════════════════════════════════════
                    if audit.get('decision') == 'REJECT' and draft_validator_passed and consensus_passed:
                        self_consistency = audit.get('self_consistency', {})
                        scores = self_consistency.get('scores', [])
                        # [V60.43] API 할당량 오류 판단 조건:
                        # 1. 모든 점수가 50 (기본값) - API 실패로 기본값 반환
                        # 2. 점수 중 0인 것이 과반수
                        # 3. 점수 표준편차가 0 (모두 동일) + 평균 <= 50
                        all_default_50 = len(scores) >= 2 and all(s == 50 for s in scores)
                        zero_count = sum(1 for s in scores if s == 0)
                        many_zeros = len(scores) >= 2 and zero_count >= len(scores) // 2
                        is_quota_failure = all_default_50 or many_zeros

                        if is_quota_failure:
                            self.ui.log(f"      ⚠️ [V60.43] API 할당량 오류 감지 (score=0이 {zero_count}/{len(scores)}개)")
                            self.ui.log(f"      ✅ [V60.43] DraftValidator + Consensus 통과로 PASS 오버라이드")
                            audit['decision'] = 'PASS'
                            audit['v60_43_override'] = True
                            audit['original_decision'] = 'REJECT'
                            audit['override_reason'] = 'api_quota_exhausted_fallback'
                            self._audit_event("v60_43_quota_override", "Arc accepted due to quota exhaustion", {
                                "arc_no": global_arc_no,
                                "scores": scores,
                                "zero_count": zero_count
                            })

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

                        # [V49.6 NEW] physical_inventory가 비어있으면 이전 Arc 소지품 계승
                        curr_joint = refined_arc.get('joint_docs', {})
                        curr_inventory = curr_joint.get('physical_inventory', [])
                        if not curr_inventory or curr_inventory == [] or curr_inventory == "[]":
                            if all_refined_arcs:
                                # 이전 Arc의 소지품 계승
                                prev_joint = all_refined_arcs[-1].get('joint_docs', {})
                                prev_inventory = prev_joint.get('physical_inventory', [])
                                if prev_inventory and prev_inventory != [] and prev_inventory != "[]":
                                    # 이번 Arc에서 소모된 아이템 제외
                                    curr_status = refined_arc.get('status_shadow', {})
                                    consumed = curr_status.get('item_consumption', [])
                                    if isinstance(consumed, str):
                                        consumed = [consumed] if consumed else []

                                    # 이번 Arc에서 새로 획득한 아이템 추가
                                    state_constraints = refined_arc.get('state_constraints', {})
                                    acquired = state_constraints.get('items_acquired', [])
                                    if isinstance(acquired, str):
                                        acquired = [acquired] if acquired else []

                                    # 계승 로직: 이전 소지품 - 소모 + 획득
                                    if isinstance(prev_inventory, list):
                                        inherited = [item for item in prev_inventory if item not in consumed]
                                        inherited.extend(acquired)
                                        refined_arc['joint_docs']['physical_inventory'] = inherited
                                        self.ui.log(f"      🔄 [V49.6] physical_inventory 이전 Arc에서 계승: {inherited[:3]}{'...' if len(inherited) > 3 else ''}")

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
                            refined_arc = None  # [V60.10 Fix] 다음 시도에서 Analyst 재호출 보장
                            attempt += 1  # [V60.51 Fix] 검증 실패 시에도 카운터 증가
                            continue

                        # 🧱 [Integrity Gate] 필수 키 검증 통과 시에만 저장
                        if not self._validate_arc_integrity(refined_arc):
                            current_feedback = "필수 키가 누락된 전술 설계입니다. 형식을 완전한 JSON으로 다시 출력하십시오."
                            refined_arc = None  # [V60.10 Fix] 다음 시도에서 Analyst 재호출 보장
                            attempt += 1  # [V60.51 Fix] 검증 실패 시에도 카운터 증가
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
                            attempt += 1  # [V60.51 Fix] DB 저장 실패 시에도 카운터 증가
                            continue

                        # [V49.4] ConstraintDB 업데이트 (다음 Arc 설계 시 참조)
                        constraint_db.update_arc_state(refined_arc)
                        self.ui.log(f"      🔒 [V49.4] ConstraintDB 업데이트 완료 (총 {len(constraint_db.arc_states)}개 Arc)")

                        # [V60.10] Arc 성공 후 종료 상태 갱신 - StateExtractor 활용
                        last_refined_context = self._generate_arc_context_v60(all_refined_arcs, global_arc_no + 1)
                        current_ep_start = refined_arc['ep_end'] + 1
                        passed = True

                        # [V55.3] PassRateMonitor: Stage 2 성공 기록
                        if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                            try:
                                self.pass_rate_monitor.record_attempt(
                                    stage=2,
                                    episode=global_arc_no,  # Arc 번호를 episode로 사용
                                    arc=global_arc_no,
                                    attempt_num=attempt + 1,
                                    success=True,
                                    generation_method=generation_method
                                )
                            except Exception:
                                pass

                        # [V60.2] QualityDashboard: Stage 2 Arc 품질 기록
                        if V50_MODULES_AVAILABLE and self.quality_dashboard:
                            try:
                                self.quality_dashboard.record_validation(
                                    ep_num=global_arc_no,
                                    result={
                                        'decision': 'PASS',
                                        'score': audit.get('score', 80),
                                        'violations': [],
                                        'warnings': []
                                    },
                                    stage=2
                                )
                            except Exception:
                                pass

                        # [V60.25] Stage2Optimizer: Director PASS 시 세션 실패 메모리 초기화
                        if hasattr(self, 'stage2_optimizer') and self.stage2_optimizer:
                            try:
                                # 현재 Arc 실패 기록 초기화 (성공했으므로)
                                self.stage2_optimizer.failure_memory.clear_arc_failures(global_arc_no)
                                self.ui.log(f"      ✨ [V60.25] Arc {global_arc_no} 최종 성공 - 실패 메모리 클리어")
                            except Exception:
                                pass

                        break
                    else:
                        # [V60.9] Director REJECT 시 구조화된 피드백 생성
                        base_feedback = audit.get('re_slice_instruction', '밀도 보강 필요')

                        # 적응형 피드백 강도
                        adaptive_intensity = self._get_adaptive_feedback_intensity(attempt, stage=2)
                        intensity_guide = f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"

                        current_feedback = f"{base_feedback}{intensity_guide}"
                        refined_arc = None  # [V60.10 Fix] 다음 시도에서 Analyst 재호출 보장
                        self.ui.log(f"      🎬 [Reject] {audit.get('reason')}")
                        self.ui.log(f"      📋 [V60.9] 적응형 피드백 (기준: {adaptive_intensity['pass_threshold']}점)")

                        # [V55.3] PassRateMonitor: Stage 2 실패 기록
                        if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                            try:
                                self.pass_rate_monitor.record_attempt(
                                    stage=2,
                                    episode=global_arc_no,
                                    arc=global_arc_no,
                                    attempt_num=attempt + 1,
                                    success=False,
                                    reject_reason=str(audit.get('reason', ''))[:100],
                                    generation_method=generation_method
                                )
                            except Exception:
                                pass

                        # [V60.2] QualityDashboard: Stage 2 Arc REJECT 기록
                        if V50_MODULES_AVAILABLE and self.quality_dashboard:
                            try:
                                self.quality_dashboard.record_validation(
                                    ep_num=global_arc_no,
                                    result={
                                        'decision': 'REJECT',
                                        'score': audit.get('score', 0),
                                        'violations': [{'type': 'director_reject', 'description': str(audit.get('reason', ''))[:200]}],
                                        'warnings': []
                                    },
                                    stage=2
                                )
                            except Exception:
                                pass

                        # [V60.3] Stage간 REJECT 히스토리 기록
                        self.stage_rejection_history.append({
                            'stage': 2,
                            'arc_no': global_arc_no,
                            'reason': str(audit.get('reason', ''))[:200],
                            'attempt': attempt + 1
                        })

                        # [V60.25] Stage2Optimizer: Director REJECT 시 실패 기록
                        if hasattr(self, 'stage2_optimizer') and self.stage2_optimizer:
                            try:
                                self.stage2_optimizer.failure_memory.record_failure(
                                    arc_no=global_arc_no,
                                    failure_type='director_reject',
                                    details=str(audit.get('reason', ''))[:200]
                                )
                            except Exception:
                                pass

                    # [V60.45] while 루프 카운터 증가
                    attempt += 1

                if not passed:
                    self.ui.log(f"🚨 [Critical] Arc {global_arc_no} 최종 설계 실패.")
                    self._audit_event("arc_design_failed", "max retries exhausted", {
                        "arc_no": global_arc_no,
                        "batch_start": batch_start,
                        "batch_end": batch_end
                    })

                    # [V60.46] 실패 리포트 생성 및 출력
                    failure_report_path = self.project_path / "logs" / f"arc_{global_arc_no}_failure_report.txt"
                    failure_report_path.parent.mkdir(parents=True, exist_ok=True)

                    # REJECT 히스토리 수집
                    arc_rejects = [r for r in self.stage_rejection_history
                                   if r.get('stage') == 2 and r.get('arc_no') == global_arc_no]

                    # 현재 제약 조건 수집
                    current_constraints = constraint_db.generate_constraint_block(global_arc_no) if constraint_db else "N/A"

                    # 이전 Arc 아이템 목록
                    prev_items = []
                    for prev_arc in all_refined_arcs:
                        items = prev_arc.get('state_constraints', {}).get('items_acquired', [])
                        if items:
                            prev_items.extend(items if isinstance(items, list) else [items])

                    # 실패 리포트 작성
                    report_lines = [
                        f"{'='*60}",
                        f"Arc {global_arc_no} 실패 리포트",
                        f"{'='*60}",
                        f"",
                        f"[REJECT 히스토리]",
                    ]
                    for i, rej in enumerate(arc_rejects, 1):
                        report_lines.append(f"  시도 {rej.get('attempt', i)}: {rej.get('reason', 'N/A')}")

                    report_lines.extend([
                        f"",
                        f"[이전 Arc에서 이미 획득한 아이템 - 중복 획득 금지]",
                    ])
                    for item in prev_items:
                        report_lines.append(f"  ❌ {item}")

                    report_lines.extend([
                        f"",
                        f"[현재 제약 조건]",
                        str(current_constraints)[:2000] if current_constraints else "없음",
                        f"",
                        f"[마지막 생성된 Arc 데이터]",
                    ])
                    if refined_arc:
                        report_lines.append(f"  tactical_doc 길이: {len(refined_arc.get('tactical_doc', ''))}자")
                        report_lines.append(f"  items_acquired: {refined_arc.get('state_constraints', {}).get('items_acquired', [])}")

                    report_content = "\n".join(report_lines)

                    # 파일 저장
                    with open(failure_report_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)

                    # 콘솔 출력
                    print(f"\n{'='*60}")
                    print(f"📋 [V60.46] Arc {global_arc_no} 실패 분석 리포트")
                    print(f"{'='*60}")
                    print(f"\n🔴 REJECT 사유 ({len(arc_rejects)}회):")
                    for rej in arc_rejects[-3:]:  # 최근 3개만 출력
                        print(f"   - {rej.get('reason', 'N/A')[:100]}")
                    print(f"\n🚫 중복 획득 금지 아이템 ({len(prev_items)}개):")
                    for item in prev_items[:5]:  # 최대 5개만 출력
                        print(f"   - {item}")
                    if len(prev_items) > 5:
                        print(f"   ... 외 {len(prev_items) - 5}개")
                    print(f"\n📁 전체 리포트: {failure_report_path}")
                    print(f"{'='*60}\n")

                    # [V43 패치] 진행 상황 보존 및 사용자 선택 제공
                    if all_refined_arcs:
                        self.ui.log(f"💾 [Auto-Save] 현재까지 {len(all_refined_arcs)}개 Arc 저장 완료.")

                    # [V60.45] 다시 하기 옵션 + [V60.46] 수동 편집 옵션
                    while True:
                        print("   [1] 건너뛰고 계속")
                        print("   [2] 중단")
                        print("   [3] 다시 하기 (자동)")
                        print("   [4] 수동 개입 (리포트 확인 후 재시도)")
                        user_choice = input("   선택 (기본: 2): ").strip()

                        if user_choice == '1':
                            # 건너뛰기 선택 시 다음 Arc를 위한 context 업데이트
                            self.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                            current_ep_start += 5  # 기본 회차 증가
                            break
                        elif user_choice == '3':
                            # 다시 하기 - 현재 Arc를 처음부터 재시도
                            self.ui.log(f"🔄 Arc {global_arc_no} 다시 시도합니다...")
                            attempt = 0
                            passed = False
                            current_feedback = ""
                            constraint_block = constraint_db.generate_constraint_block(global_arc_no)
                            break
                        elif user_choice == '4':
                            # 수동 개입 - 리포트 확인 후 사용자가 준비되면 재시도
                            print(f"\n   📝 리포트 파일을 확인하세요: {failure_report_path}")
                            print(f"   💡 문제가 된 아이템이나 표현을 확인 후, 아래 옵션을 선택하세요.")
                            manual_input = input("   준비되면 [Enter]로 재시도, 'skip'으로 건너뛰기, 'quit'으로 중단: ").strip().lower()
                            if manual_input == 'skip':
                                self.ui.log(f"⏭️ Arc {global_arc_no}을 건너뛰고 계속합니다.")
                                current_ep_start += 5
                                break
                            elif manual_input == 'quit':
                                self.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                                return
                            else:
                                # 수동 확인 후 재시도
                                self.ui.log(f"🔄 Arc {global_arc_no} 수동 확인 후 재시도...")
                                attempt = 0
                                passed = False
                                current_feedback = f"[사용자 수동 확인 완료] 이전 Arc에서 획득한 아이템: {', '.join(prev_items[:5])} 등 {len(prev_items)}개. 이 아이템들은 절대 다시 획득하면 안 됩니다!"
                                constraint_block = constraint_db.generate_constraint_block(global_arc_no)
                                break
                        else:
                            self.ui.log("⏹️ 사용자 요청으로 공정을 중단합니다.")
                            return

                    # 다시 하기 선택 시 while idx 루프 처음부터 (idx 유지)
                    if user_choice == '3':
                        continue  # idx 증가 없이 같은 Arc 다시 시도

                # [V60.45] 정상 처리 완료 또는 건너뛰기 - 다음 Arc로
                idx += 1

            self.ui.log(f"✅ 배치({batch_start+1}~{batch_end}) 욕망 엔진 이식 및 용접 완료.")

            # [V40] Slack 알림 전송 (Arc 설계 완료) - 실패해도 계속 진행
            try:
                batch_results_count = len(all_refined_arcs) - batch_start_count  # 실제 생성된 Arc 개수
                notifier.send_notification(
                    title=f"✅ [Arc] 제 {batch_start+1}~{batch_end}번 아크 설계 완료",
                    message=f"프로젝트: {self.current_project.name}\n설계된 아크 수: {batch_results_count}개",
                    key_metrics={"완료 구간": f"{batch_start+1} ~ {batch_end} Arc", "생성 수": batch_results_count}
                )
            except Exception as slack_err:
                self.ui.log(f"⚠️ [Slack] 알림 전송 실패 (무시하고 계속): {slack_err}")

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
        """
        [V60.15] Stage2: 진짜 서사 구조 분석 기반 Flow Guard

        기존 문제점:
        - 임베딩 유사도는 "문체가 비슷한가"만 봄
        - "싸움→도주→협상"도 문체가 비슷하면 정체로 오탐

        V60.15 개선:
        - LLM이 행위/장소/결과를 추출
        - 연속 3개 동일하면 진짜 정체
        - 문체 유사도는 무시
        """
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

        # 2) [V60.15] 진짜 서사 구조 분석 (LLM 기반)
        try:
            from modules.core.narrative_structure_analyzer import NarrativeStructureAnalyzer

            analyzer = NarrativeStructureAnalyzer(
                client=self.sys.api_client,
                model="gemini-2.5-flash"  # 저렴하게
            )

            result = analyzer.analyze(beats[:5])

            if result.get("status") == "STAGNATION":
                stagnation_type = result.get("stagnation_type", "unknown")
                pattern = result.get("pattern", "")
                recommendation = result.get("recommendation", "")

                print(f"      🔍 [V60.15] 진짜 서사 정체 감지: {stagnation_type}")
                print(f"         패턴: {pattern}")

                return {
                    "status": "REJECT",
                    "reason": f"서사 정체 감지: {stagnation_type} 반복 ({pattern})",
                    "feedback": recommendation
                }

            if result.get("status") == "WARNING":
                warning_type = result.get("warning_type", "")
                pattern = result.get("pattern", "")
                print(f"      ⚠️ [V60.15] 서사 경고: {warning_type} - {pattern}")
                # WARNING은 PASS하되 로그 출력

            # PASS - 다양성 점수 출력
            diversity = result.get("diversity_score", 1.0)
            if diversity < 0.6:
                print(f"      📊 [V60.15] 서사 다양성: {diversity:.0%} (개선 권장)")

            return {"status": "PASS", "diversity_score": diversity}

        except ImportError:
            # 분석기 없으면 기존 방식으로 폴백
            print(f"      ⚠️ [V60.15] NarrativeStructureAnalyzer 로드 실패, 폴백")
            return self._stage2_flow_guard_legacy(normalized)
        except Exception as e:
            # 오류 시 PASS (비차단)
            print(f"      ⚠️ [V60.15] 서사 분석 오류 (비차단): {e}")
            return {"status": "PASS", "fallback": True}

    def _stage2_flow_guard_legacy(self, normalized):
        """[V60.15] 레거시 Flow Guard (폴백용)"""
        def jaccard(a, b):
            sa, sb = set(a.split()), set(b.split())
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        stagnation_hits = 0
        for i in range(1, len(normalized)):
            sim = jaccard(normalized[i - 1], normalized[i])
            if sim >= 0.85:  # 레거시는 더 엄격하게
                stagnation_hits += 1

        if stagnation_hits >= 3:
            return {
                "status": "REJECT",
                "reason": "서사 정체 감지: 유사 비트가 연속 반복",
                "feedback": "연속 회차의 사건/공간/행동을 분리하여 변주하라."
            }

        return {"status": "PASS"}

    def _check_semantic_similarity(self, beats: list, pairs: list) -> int:
        """
        [V49.3] 임베딩 기반 시맨틱 유사도 검사

        Jaccard로 애매한 구간(0.5~0.75)에서 실제 의미적 유사도를 확인합니다.
        비용 최적화: 필요한 쌍에 대해서만 임베딩 호출

        Args:
            beats: 정규화된 비트 리스트
            pairs: [(idx1, idx2, jaccard_sim), ...] 애매한 쌍 리스트

        Returns:
            int: 시맨틱 유사도가 높은 쌍의 수
        """
        try:
            import numpy as np
            from modules.core.memory_engine import GoogleEmbeddingFunction

            # API 클라이언트 확인
            if not hasattr(self, 'sys') or not hasattr(self.sys, 'api_client'):
                return 0

            api_key = os.getenv("GOOGLE_API_KEY", "")
            if not api_key:
                return 0

            embed_func = GoogleEmbeddingFunction(api_key)

            semantic_hits = 0
            for idx1, idx2, jaccard_sim in pairs:
                try:
                    # 두 비트의 임베딩 생성
                    embeddings = embed_func([beats[idx1], beats[idx2]])

                    if len(embeddings) == 2:
                        # 코사인 유사도 계산
                        vec1 = np.array(embeddings[0])
                        vec2 = np.array(embeddings[1])
                        cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

                        # [V60.15] 시맨틱 유사도 임계값 완화 (0.85 → 0.93)
                        # 첫 Arc에서 비슷한 톤은 자연스러움
                        if cosine_sim >= 0.93:
                            print(f"         ⚠️ [V49.3] 시맨틱 정체 감지: Beat {idx1+1} ↔ Beat {idx2+1} (cosine={cosine_sim:.2f})")
                            semantic_hits += 1

                except Exception as pair_err:
                    # 개별 쌍 오류는 무시하고 계속
                    pass

            return semantic_hits

        except ImportError:
            # numpy나 memory_engine 임포트 실패 시 0 반환
            return 0
        except Exception as e:
            # 전체 오류 시 0 반환 (비차단)
            print(f"         ⚠️ [V49.3] 시맨틱 분석 오류 (비차단): {e}")
            return 0

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
        """
        [V45] BlockingValidator용 validation_context 구성

        Args:
            ep_num: 에피소드 번호
            blueprint: 설계도 (선택)
            mode: 'MANUSCRIPT' 또는 'BLUEPRINT'
            blueprint_text: [V49] Blueprint 원본 텍스트 (씬 범위 체크용)

        Returns:
            dict: {
                'encyclopedia': {'items': [...], 'npcs': [...], 'locations': [...]},
                'martial_hud': {...},
                'blueprint': {...},
                'blueprint_text': str,  # [V49] 원본 텍스트
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
            'blueprint_text': blueprint_text,  # [V49] 씬 범위 초과 체크용
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

    def _classify_rejection_feedback(self, reason: str, feedback: str, blueprint: dict = None) -> str:
        """
        [V56] REJECT 피드백 분류 및 구조화

        REJECT 사유를 분류하고 더 구체적인 수정 가이드를 생성합니다.

        Args:
            reason: Director의 REJECT 사유
            feedback: Director의 피드백
            blueprint: 현재 Blueprint (씬 정보 추출용)

        Returns:
            구조화된 피드백 문자열
        """
        reason_lower = reason.lower() if reason else ""
        feedback_lower = feedback.lower() if feedback else ""

        classified_parts = [f"\n[🚨 V56 STRUCTURED REJECTION FEEDBACK]"]

        # 1. 분량 관련
        if any(kw in reason_lower for kw in ["분량", "length", "자", "미달", "부족"]):
            classified_parts.append("📏 [분량 문제]")
            classified_parts.append("   - 원고 분량이 목표에 미달합니다.")
            classified_parts.append("   - 각 씬의 묘사를 더 풍부하게 작성하세요.")
            classified_parts.append("   - 대화 장면, 감각 묘사, 내면 서술을 추가하세요.")

        # 2. 씬 누락
        elif any(kw in reason_lower for kw in ["씬", "scene", "누락", "missing"]):
            classified_parts.append("📋 [씬 누락]")
            if blueprint:
                scene_breakdown = blueprint.get("scene_breakdown", {})
                scene_names = list(scene_breakdown.keys())[:6]
                classified_parts.append(f"   - Blueprint 필수 씬: {', '.join(scene_names)}")
            classified_parts.append("   - 모든 씬을 순서대로 빠짐없이 작성하세요.")

        # 3. 연속성 오류
        elif any(kw in reason_lower for kw in ["연속", "continuity", "이전", "직전"]):
            classified_parts.append("🔗 [연속성 오류]")
            classified_parts.append("   - 직전 화와의 연결이 부자연스럽습니다.")
            classified_parts.append("   - 직전 화 마지막 상황에서 자연스럽게 이어지도록 수정하세요.")

        # 4. 아이템 오류
        elif any(kw in reason_lower for kw in ["아이템", "item", "소지", "미획득"]):
            classified_parts.append("🎒 [아이템 오류]")
            classified_parts.append("   - 소지하지 않은 아이템을 사용했거나, 소지품 연속성 오류입니다.")
            classified_parts.append("   - 현재 소지품 목록을 확인하고 해당 아이템만 사용하세요.")

        # 5. 관계 급변
        elif any(kw in reason_lower for kw in ["관계", "relationship", "급변", "jump"]):
            classified_parts.append("👥 [관계 급변]")
            classified_parts.append("   - NPC 관계가 너무 급격하게 변화했습니다.")
            classified_parts.append("   - 무시→의심→경외→충성 단계를 자연스럽게 거치세요.")

        # 6. Show Don't Tell
        elif any(kw in reason_lower for kw in ["show", "tell", "감정", "서술"]):
            classified_parts.append("✍️ [Show Don't Tell 위반]")
            classified_parts.append("   - 직접 감정 서술이 과다합니다.")
            classified_parts.append("   - '분노했다' 대신 '주먹을 꽉 쥐었다' 같이 행동으로 보여주세요.")

        # 7. 기타
        else:
            classified_parts.append("⚠️ [기타 문제]")
            classified_parts.append(f"   - 사유: {reason[:200]}")

        # 원본 피드백 추가
        if feedback:
            classified_parts.append(f"\n📝 [Director 원본 피드백]")
            classified_parts.append(f"   {feedback[:500]}")

        return "\n".join(classified_parts)

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

        # [V48] 서사 다양성 엔진 초기화
        self._init_diversity_engine(window_size=10)

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
                # 🛡️ [V55.4] 2단계 모델 업그레이드 (비용 효율화)
                if reject_count == 0 and enrichment_level == 0:
                    # 1차 시도: Tier 1 (gemini-2.5-pro) - 첫 시도부터 pro 사용
                    current_model = AIModels.TIER_1_ARCHITECT
                else:
                    # 2차+ 시도: Tier 2 (gemini-3-pro-preview) - reject 시 최고 모델
                    current_model = AIModels.TIER_2_ARCHITECT
                    self.ui.log(f"🚀 [V55.4] 아키텍트 최고 모델 격상: {current_model}")

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
                # [V60.3] 정지선 위반 사전 경고 주입
                stopline_warning = ""
                if next_beat:
                    stopline_warning = (
                        f"\n🚨🚨🚨 [정지선 경고 - 절대 준수] 🚨🚨🚨\n"
                        f"다음 화 내용: 「{next_beat}」\n"
                        f"→ 위 내용은 이번 화에서 절대 다루지 마세요.\n"
                        f"→ 이번 화는 「{focus_tag}」 범위 내에서만 설계하세요.\n"
                        f"→ 정지선을 넘으면 즉시 REJECT됩니다.\n"
                        f"🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨\n"
                    )

                # [V48] 서사 다양성 엔진 프롬프트 주입
                diversity_injection = ""
                if self.diversity_engine and reject_count == 0:
                    diversity_injection = self.diversity_engine.get_architect_injection()

                # [V51] Architect 지능 향상 주입
                v51_architect_injection = ""
                if V50_MODULES_AVAILABLE and reject_count == 0:  # 첫 시도에서만 주입
                    try:
                        # 직전 화 블루프린트 가져오기
                        prev_blueprint = self.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None

                        # V51.2 품질 제약 주입
                        if self.quality_amplifier:
                            architect_constraints = self.quality_amplifier.generate_architect_constraints(
                                ep_num=working_ep,
                                arc_data=arc_data,
                                prev_blueprint=prev_blueprint
                            )
                            v51_architect_injection += architect_constraints + "\n\n"

                        # V51.3 지능 향상 주입 (Few-Shot + Anti-Pattern + 위치 가이드)
                        if self.agent_intelligence:
                            intel_prompt = self.agent_intelligence.get_architect_enhancement(
                                ep_num=working_ep,
                                arc_data=arc_data,
                                prev_blueprint=prev_blueprint
                            )
                            v51_architect_injection += intel_prompt + "\n\n"

                        # V51.4 실패 학습 제약 주입
                        if self.failure_learner:
                            learned_constraints = self.failure_learner.generate_constraint_prompt(stage=3)
                            if learned_constraints:
                                v51_architect_injection += learned_constraints + "\n\n"

                        # [V60.3] Stage 2 REJECT 히스토리 참조
                        if self.stage_rejection_history:
                            stage2_rejects = [r for r in self.stage_rejection_history if r.get('stage') == 2 and r.get('arc_no') == arc_no]
                            if stage2_rejects:
                                reject_warning = "\n⚠️ [이전 Stage 2 REJECT 이력]\n"
                                for rej in stage2_rejects[-3:]:  # 최근 3개
                                    reject_warning += f"  - Arc {rej.get('arc_no')}: {rej.get('reason', '')[:100]}\n"
                                reject_warning += "→ 위 원인을 이번 Blueprint 설계에서 반복하지 마세요.\n"
                                v51_architect_injection += reject_warning + "\n"

                        # [V60.9] Stage 4→3 역방향 피드백 주입 (직전 에피소드의 Writer REJECT로부터 학습)
                        if self.stage_rejection_history:
                            # 직전 에피소드(working_ep - 1)의 Stage 4 REJECT 이력 확인
                            stage4_rejects = [r for r in self.stage_rejection_history
                                              if r.get('stage') == 4 and r.get('ep_num') == working_ep - 1]
                            if stage4_rejects:
                                latest_reject = stage4_rejects[-1]  # 가장 최근 REJECT
                                reverse_guidance = latest_reject.get('reverse_guidance', '')
                                if reverse_guidance:
                                    stage4_warning = f"\n🔄 [V60.9 Stage 4→3 역방향 피드백]\n"
                                    stage4_warning += f"직전 화(제{working_ep - 1}화)에서 Writer가 REJECT된 원인 분석:\n"
                                    stage4_warning += f"  → 원인: {latest_reject.get('reason', '')[:150]}\n"
                                    stage4_warning += f"\n이번 Blueprint에 반영할 구조적 개선:\n{reverse_guidance}\n"
                                    v51_architect_injection += stage4_warning + "\n"
                                    self.ui.log(f"      🔄 [V60.9] Stage 4→3 역방향 피드백 주입 (직전 화 Writer REJECT 기반)")

                        # V51.6 복선 관리 주입
                        if self.foreshadow_tracker:
                            foreshadow_prompt = self.foreshadow_tracker.generate_architect_prompt(working_ep)
                            if foreshadow_prompt:
                                v51_architect_injection += foreshadow_prompt

                        # V55.2 Constitutional Self-Check 주입
                        if self.constitutional_checker:
                            constitutional_prompt = self.constitutional_checker.get_full_injection(
                                stage=3,
                                context={
                                    'prev_blueprint': prev_blueprint,
                                    'arc_data': arc_data,
                                    'feedback': blueprint_feedback if 'blueprint_feedback' in dir() else ""
                                }
                            )
                            v51_architect_injection = constitutional_prompt + "\n\n" + v51_architect_injection

                        # [V60.3] 정지선 경고 추가
                        if stopline_warning:
                            v51_architect_injection = stopline_warning + v51_architect_injection

                        if v51_architect_injection:
                            self.ui.log(f"      🧠 [V51+V55.2+V60.3] Architect 지능 향상 + 정지선 경고 주입 완료")
                    except Exception as v51_err:
                        self.ui.log(f"      ⚠️ [V51] Architect 향상 실패: {v51_err}")

                # [안전성 패치] Architect 호출 및 예외 처리
                try:
                    # [V54.1] Semantic Cache: 유사 블루프린트 캐시 확인
                    cached_blueprint = None
                    cache_structure_hint = ""
                    if V50_MODULES_AVAILABLE and self.semantic_cache and reject_count == 0:
                        try:
                            cache_context = {
                                "ep_num": working_ep,
                                "arc_num": arc_no,
                                "scene_type": arc_data.get('hybrid_composition', {}).get('primary', '') if arc_data else ''
                            }
                            cached_blueprint = self.semantic_cache.get("blueprint_structure", cache_context)
                            if cached_blueprint and isinstance(cached_blueprint, dict):
                                # 캐시된 구조를 힌트로 활용
                                cached_scenes = cached_blueprint.get('scene_breakdown', {})
                                cached_hook = cached_blueprint.get('ending_hook', '')
                                if cached_scenes:
                                    cache_structure_hint = f"\n[V54.1 Cache Hint] 유사 성공 사례 구조:\n- 씬 수: {len(cached_scenes)}개\n- 엔딩훅 유형: {cached_hook[:50]}..."
                                    self.ui.log(f"   💾 [V54.1] 캐시 히트! 구조 힌트 주입 (씬 {len(cached_scenes)}개)")
                        except Exception as cache_err:
                            self._audit_event("v54_cache_error", "semantic cache lookup failed", {"error": str(cache_err)[:100]})

                    # [V54.5] 성공 패턴 가이드 (Architect용)
                    architect_pattern_guide = ""
                    if V50_MODULES_AVAILABLE and self.success_patterns and reject_count == 0:
                        try:
                            architect_pattern_guide = self.success_patterns.get_guidance_from_patterns(
                                content_type="blueprint",
                                target_context={
                                    "ep_num": working_ep,
                                    "arc_num": arc_no if arc_no else 0
                                }
                            )
                            if architect_pattern_guide:
                                self.ui.log(f"   🏆 [V54.5] Architect 성공 패턴 가이드 주입")
                        except Exception as pattern_err:
                            self._audit_event("v54_pattern_error", "architect pattern guide failed", {"error": str(pattern_err)[:100]})

                    # [V48] Diversity Sampling: 첫 시도에서만 3개 후보 생성
                    use_diversity_sampling = (self.diversity_engine and reject_count == 0 and enrichment_level == 0)

                    def architect_generator():
                        """블루프린트 단일 생성 함수"""
                        # V54.1 캐시 힌트 + V54.5 성공 패턴 가이드 주입
                        full_narrative = str(self.current_project.get_causal_history_summary()) + f"\n{enrichment_directive}\n{diversity_injection}\n{v51_architect_injection}"
                        if cache_structure_hint:
                            full_narrative += f"\n{cache_structure_hint}"
                        if architect_pattern_guide:
                            full_narrative += f"\n\n{architect_pattern_guide}"
                        full_narrative += f"\n\n[🚨 Retry Feedback]: {retry_feedback}"

                        return self.agents['architect'].design_v20_breakdown(
                            ep_num=working_ep,
                            arc_pos=arc_pos,
                            arc_tactical_doc=focus_package,
                            martial_hud=self.sys.hud.get_structured_hud(),
                            encyclopedia=self.sys.lore.db.get_lore_list_by_category(None),
                            narrative_context=full_narrative,
                            tactical_references=tactical_references,
                            style_guide=self.current_project.selected_tone.get('guide', '표준 웹소설 연출'),
                            prev_ms_ending=prev_ms_ending,
                            surgery_intel=self.current_project.get_surgery_intelligence(limit=3),
                            enrichment_level=enrichment_level
                        )

                    # [V55.3] 블루프린트 생성 방법 추적
                    blueprint_generation_method = "architect"  # 기본값

                    # [V54.4.1] Two-Phase Blueprint: 첫 번째 재시도에서 발동 (reject_count == 1)
                    if V50_MODULES_AVAILABLE and self.two_phase_bp and reject_count == 1:
                        self.ui.log(f"📐 [V54.4.1] Two-Phase Blueprint 필살기 발동! (시도 {reject_count + 1}회차)")
                        try:
                            # tactical_doc 추출
                            tactical_doc_text = ""
                            if arc_data:
                                tactical_doc_text = arc_data.get('tactical_doc', '')
                                if not tactical_doc_text and focus_package:
                                    tactical_doc_text = focus_package

                            # Two-Phase 블루프린트 생성
                            two_phase_result = self.two_phase_bp.generate(
                                ep_num=working_ep,
                                arc_num=arc_num,
                                volume_num=volume_num,
                                tactical_doc=tactical_doc_text,
                                prev_blueprint=self.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None,
                                context={
                                    "narrative_context": full_narrative[:2000] if full_narrative else "",
                                    "prev_ms_ending": prev_ms_ending[:1000] if prev_ms_ending else ""
                                },
                                constraints=retry_feedback  # 이전 REJECT 이유를 제약 조건으로 전달
                            )

                            if two_phase_result:
                                blueprint_candidate = two_phase_result
                                blueprint_generation_method = "two_phase"
                                self.ui.log(f"   ✅ [V54.4.1] Two-Phase 블루프린트 생성 완료")
                                self._audit_event("two_phase_blueprint", "blueprint generated via two-phase", {
                                    "ep_num": working_ep,
                                    "reject_count": reject_count,
                                    "scene_count": len(two_phase_result.get('scene_breakdown', {}))
                                })
                            else:
                                self.ui.log(f"   ⚠️ [V54.4.1] Two-Phase 실패, 기본 생성기 사용")
                                blueprint_candidate = architect_generator()
                        except Exception as tp_err:
                            self.ui.log(f"   ⚠️ [V54.4.1] Two-Phase 오류: {tp_err}")
                            self._audit_event("two_phase_blueprint_error", "two-phase generation failed", {
                                "ep_num": working_ep,
                                "error": str(tp_err)
                            })
                            blueprint_candidate = architect_generator()

                    # [V53.5] Tree of Thoughts: 마지막 시도에서 필살기로 발동 (reject_count >= 2)
                    elif V50_MODULES_AVAILABLE and self.tree_of_thoughts and reject_count >= 2:
                        self.ui.log(f"🔥 [V53.5] Tree of Thoughts 필살기 발동! (시도 {reject_count + 1}회차)")
                        try:
                            tot_result = self.tree_of_thoughts.explore_blueprint(
                                ep_num=working_ep,
                                arc_data=arc_data,
                                prev_blueprint=self.current_project.get_blueprint(working_ep - 1) if working_ep > 1 else None,
                                generator_fn=architect_generator,
                                n_branches=4  # V55.2: 4분기 확장
                            )
                            blueprint_candidate = tot_result.best_path.output
                            if isinstance(blueprint_candidate, str):
                                try:
                                    blueprint_candidate = json.loads(blueprint_candidate)
                                except:
                                    pass  # 이미 dict이면 그대로
                            blueprint_generation_method = "tot"
                            self.ui.log(f"   🌳 [V53.5] ToT 완료: 최고 경로 '{tot_result.best_path.approach}' ({tot_result.best_path.score}점)")
                            self._audit_event("tree_of_thoughts_ultimate", "blueprint tot as last resort", {
                                "ep_num": working_ep,
                                "reject_count": reject_count,
                                "best_score": tot_result.best_path.score,
                                "paths_explored": len(tot_result.paths)
                            })
                        except Exception as tot_err:
                            self.ui.log(f"   ⚠️ [V53.5] ToT 필살기 실패, 기본 생성기 사용: {tot_err}")
                            blueprint_candidate = architect_generator()
                    elif use_diversity_sampling:
                        self.ui.log(f"🎲 [V48 Diversity] 블루프린트 3개 후보 생성 중...")
                        blueprint_candidate, diversity_meta = self.diversity_engine.generate_diverse_blueprint(
                            generator_fn=architect_generator,
                            n_samples=3
                        )
                        blueprint_generation_method = "diversity"
                        if diversity_meta.get('selected_score'):
                            self.ui.log(f"   ✨ 선택된 블루프린트 다양성 점수: {diversity_meta['selected_score'].get('total', 0):.1f}")
                        self._audit_event("diversity_sampling", "blueprint diversity sampling", {
                            "ep_num": working_ep,
                            "n_samples": diversity_meta.get('n_samples', 0),
                            "selected_score": diversity_meta.get('selected_score', {}).get('total', 0)
                        })
                    else:
                        blueprint_candidate = architect_generator()

                except Exception as architect_err:
                    self.ui.log(f"🚨 [Architect Error] 제 {working_ep}화 설계 중 에러: {architect_err}")
                    self._audit_event("architect_error", "design_v20_breakdown failed", {
                        "ep_num": working_ep,
                        "error": str(architect_err)
                    })
                    retry_feedback = f"Architect 엔진 오류: {str(architect_err)[:100]}. 안정적인 JSON 출력을 확보하라."
                    reject_count += 1
                    continue

                # [V52.1] Self-Reflection: 첫 시도에서만 Architect 자기 성찰 적용
                if V50_MODULES_AVAILABLE and self.self_reflector and reject_count == 0 and blueprint_candidate:
                    try:
                        bp_text = blueprint_candidate.get('integrated_scenario', '')
                        if bp_text and len(bp_text) > 500:
                            arc_context = json.dumps(arc_data.get('tactical_doc', '')[:2000], ensure_ascii=False) if arc_data else ""
                            reflection_result = self.self_reflector.reflect_and_improve(
                                output=bp_text,
                                context=arc_context,
                                target=ReflectionTarget.ARCHITECT
                            )
                            if reflection_result.improvement_score > 0:
                                blueprint_candidate['integrated_scenario'] = reflection_result.improved
                                self.ui.log(f"   🔄 [V52.1] Architect Self-Reflection: {len(reflection_result.changes_made)}개 이슈 자체 수정")
                                self._audit_event("self_reflection", "architect self-improved", {
                                    "ep_num": working_ep,
                                    "changes": reflection_result.changes_made,
                                    "score": reflection_result.improvement_score
                                })
                    except Exception as sr_err:
                        self.ui.log(f"   ⚠️ [V52.1] Architect Self-Reflection 실패 (비치명적): {sr_err}")

                # [V52.4] Cross-Agent Verification: Architect → Arc 설계 준수 검증
                if V50_MODULES_AVAILABLE and self.cross_verifier and blueprint_candidate and reject_count == 0:
                    try:
                        compliance_result = self.cross_verifier.verify_architect_compliance(
                            blueprint=blueprint_candidate,
                            arc_design=arc_data,
                            use_llm=True
                        )

                        if compliance_result.level == ComplianceLevel.VIOLATION:
                            self.ui.log(f"   🚨 [V52.4] Arc 설계 준수 위반 감지 (점수: {compliance_result.score:.0%})")
                            for v in compliance_result.violations[:2]:
                                self.ui.log(f"      - {v.get('item', '')}: {v.get('reason', '')[:60]}...")

                            self._audit_event("cross_agent_reject", "architect arc compliance violation", {
                                "ep_num": working_ep,
                                "score": compliance_result.score,
                                "violations": len(compliance_result.violations)
                            })

                            # 실패 기록
                            if self.failure_learner:
                                self.failure_learner.record_failure(
                                    stage=3,
                                    episode=working_ep,
                                    arc=arc_data.get('arc_no', 0),
                                    reason=f"Arc 준수 위반: {compliance_result.details[:100]}",
                                    details={"violations": compliance_result.violations}
                                )

                            retry_feedback = self.cross_verifier.generate_feedback(compliance_result, "architect")
                            reject_count += 1
                            continue
                        elif compliance_result.level == ComplianceLevel.PARTIAL:
                            self.ui.log(f"   ⚠️ [V52.4] Arc 설계 부분 준수 (점수: {compliance_result.score:.0%}, 계속 진행)")
                        else:
                            self.ui.log(f"   ✅ [V52.4] Arc 설계 완전 준수 확인")
                    except Exception as cv_err:
                        self.ui.log(f"   ⚠️ [V52.4] Cross-Agent 검증 실패 (비치명적): {cv_err}")

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
                        # ═══════════════════════════════════════════════════════════════
                        # [V48.1] ContinuityInspector: Director 호출 전 연속성 검증 (전체 BP)
                        # ═══════════════════════════════════════════════════════════════
                        continuity_passed = True
                        try:
                            # [V48.1] 전체 블루프린트 조회 (1화부터 현재 직전까지)
                            prev_blueprints = self.agents['continuity_inspector'].get_prev_blueprints(
                                current_ep=working_ep, window=None  # None = 전체 조회
                            )
                            
                            if prev_blueprints:
                                self.ui.log(f"   🔗 [V48.1] 연속성 검증 중... (제1화~제{working_ep-1}화, 총 {len(prev_blueprints)}화 전체 분석)")
                                
                                continuity_result = self.agents['continuity_inspector'].inspect(
                                    current_ep=working_ep,
                                    current_blueprint=blueprint_candidate,
                                    prev_blueprints=prev_blueprints
                                )
                                
                                if continuity_result.get('decision') == 'REJECT':
                                    severity = continuity_result.get('severity', 'UNKNOWN')
                                    violations = continuity_result.get('violations', [])
                                    fix_instructions = continuity_result.get('fix_instructions', '')
                                    
                                    self.ui.log(f"   🚨 [V48 CONTINUITY REJECT] 연속성 위반 감지 ({severity})")
                                    for v in violations[:3]:
                                        self.ui.log(f"      - {v.get('type', '')}: {v.get('description', '')[:80]}...")
                                    
                                    self._audit_event("continuity_reject", "blueprint continuity violation", {
                                        "ep_num": working_ep,
                                        "severity": severity,
                                        "violations": len(violations)
                                    })

                                    # [V51.4] 실패 기록
                                    if V50_MODULES_AVAILABLE and self.failure_learner:
                                        for v in violations[:3]:
                                            self.failure_learner.record_failure(
                                                stage=3,
                                                episode=working_ep,
                                                arc=arc_data.get('arc_no', 0),
                                                reason=f"Blueprint: {v.get('type', 'unknown')}: {v.get('description', '')[:150]}",
                                                details={"severity": severity}
                                            )

                                    retry_feedback = f"[연속성 위반] {fix_instructions}"
                                    reject_count += 1
                                    continuity_passed = False
                                else:
                                    # PASS 또는 경고만 있는 경우
                                    warnings = continuity_result.get('warnings', [])
                                    if warnings:
                                        self.ui.log(f"   ⚠️ [V48] 연속성 경고 {len(warnings)}건 (계속 진행)")
                                    else:
                                        self.ui.log(f"   ✅ [V48] 연속성 검증 통과")
                        except Exception as continuity_err:
                            self.ui.log(f"   ⚠️ [V48] ContinuityInspector 오류: {continuity_err}")
                            self._audit_event("continuity_error", "continuity inspection failed", {
                                "ep_num": working_ep,
                                "error": str(continuity_err)
                            })
                            # 연속성 검증 실패해도 Director로 계속 진행
                        
                        if not continuity_passed:
                            continue  # 연속성 위반 시 재시도

                        # ═══════════════════════════════════════════════════════════════
                        # [V60.3] Stage 3 Pre-Director Checklist (Director 호출 전 빠른 체크)
                        # ═══════════════════════════════════════════════════════════════
                        if V50_MODULES_AVAILABLE and self.pre_director_checklist:
                            try:
                                bp_checklist_result = self.pre_director_checklist.check(
                                    content=raw_content,
                                    content_type="blueprint",
                                    context={
                                        "arc_data": arc_data,
                                        "prev_blueprint": prev_blueprint
                                    }
                                )

                                if not bp_checklist_result.passed:
                                    self.ui.log(f"   ❌ [V60.3] Blueprint Pre-Check 실패: {bp_checklist_result.summary}")
                                    for reason in bp_checklist_result.blocking_reasons[:2]:
                                        self.ui.log(f"      - {reason}")

                                    self._audit_event("pre_director_blueprint_fail", "blueprint pre-checklist failed", {
                                        "ep_num": working_ep,
                                        "fail_count": bp_checklist_result.fail_count
                                    })

                                    # 피드백 추가 후 재생성
                                    retry_feedback = self.pre_director_checklist.get_feedback(bp_checklist_result)
                                    reject_count += 1
                                    continue  # Architect 재생성

                                elif bp_checklist_result.warning_count > 0:
                                    self.ui.log(f"   ⚠️ [V60.3] Blueprint Pre-Check 경고 {bp_checklist_result.warning_count}건 (진행)")
                                else:
                                    self.ui.log(f"   ✅ [V60.3] Blueprint Pre-Check 통과")

                            except Exception as bp_checklist_err:
                                self.ui.log(f"   ⚠️ [V60.3] Blueprint Pre-Checklist 실패 (비치명적): {bp_checklist_err}")

                        # ═══════════════════════════════════════════════════════════════
                        # [안전성 패치] Director 호출 예외 처리
                        # ═══════════════════════════════════════════════════════════════
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

                            # [V54.1] 캐시 저장 + [V54.5] 성공 패턴 기록
                            if V50_MODULES_AVAILABLE:
                                try:
                                    # 캐시 저장
                                    if self.semantic_cache:
                                        cache_ctx = {
                                            "ep_num": working_ep,
                                            "arc_num": arc_no,
                                            "scene_type": blueprint.get('hybrid_composition', {}).get('primary', '') if isinstance(blueprint, dict) else ''
                                        }
                                        self.semantic_cache.set("blueprint_structure", cache_ctx, blueprint)

                                    # 성공 패턴 기록
                                    if self.success_patterns:
                                        self.success_patterns.record_success(
                                            content_type="blueprint",
                                            content=blueprint,
                                            context={"ep_num": working_ep, "arc_num": arc_no if arc_no else 0},
                                            score=blueprint_audit.get('score', 80)
                                        )
                                except Exception as sp_err:
                                    self._audit_event("v54_success_pattern_error", "blueprint success pattern recording failed", {"error": str(sp_err)[:50]})

                            # [V55.3] PassRateMonitor: Stage 3 성공 기록
                            if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                try:
                                    # 모델 티어 계산 (1=flash, 2=pro, 3=preview)
                                    _tier = 2 if 'preview' in current_model else 1  # V55.4: 2단계 (1=2.5-pro, 2=3-pro-preview)
                                    self.pass_rate_monitor.record_attempt(
                                        stage=3,
                                        episode=working_ep,
                                        arc=arc_no if arc_no else 0,
                                        attempt_num=reject_count + 1,
                                        success=True,
                                        generation_method=blueprint_generation_method,
                                        model_tier=_tier
                                    )
                                except Exception:
                                    pass

                            # [V60.2] QualityDashboard: Stage 3 Blueprint PASS 기록
                            if V50_MODULES_AVAILABLE and self.quality_dashboard:
                                try:
                                    self.quality_dashboard.record_validation(
                                        ep_num=working_ep,
                                        result={
                                            'decision': 'PASS',
                                            'score': blueprint_audit.get('score', 80),
                                            'violations': [],
                                            'warnings': []
                                        },
                                        stage=3
                                    )
                                except Exception:
                                    pass

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
                            critical_keywords = self._get_dynamic_critical_keywords()  # [V60.3] 동적 생성
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

                                    # [V54.5] 성공 패턴 기록 (품질 경고 포함 통과)
                                    if V50_MODULES_AVAILABLE and self.success_patterns:
                                        try:
                                            self.success_patterns.record_success(
                                                content_type="blueprint",
                                                content=blueprint,
                                                context={"ep_num": working_ep, "arc_num": arc_no if arc_no else 0},
                                                score=score  # 경고 포함이므로 실제 점수 사용
                                            )
                                        except Exception as sp_err:
                                            self._audit_event("v54_success_pattern_error", "blueprint success pattern recording failed (warning)", {"error": str(sp_err)[:50]})

                                    # [V55.3] PassRateMonitor: Stage 3 조건부 성공 기록
                                    if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                        try:
                                            _tier = 2 if 'preview' in current_model else 1  # V55.4: 2단계 (1=2.5-pro, 2=3-pro-preview)
                                            self.pass_rate_monitor.record_attempt(
                                                stage=3,
                                                episode=working_ep,
                                                arc=arc_no if arc_no else 0,
                                                attempt_num=reject_count + 1,
                                                success=True,
                                                generation_method=blueprint_generation_method,
                                                model_tier=_tier
                                            )
                                        except Exception:
                                            pass

                                    # [V60.2] QualityDashboard: Stage 3 Blueprint 조건부 PASS 기록
                                    if V50_MODULES_AVAILABLE and self.quality_dashboard:
                                        try:
                                            self.quality_dashboard.record_validation(
                                                ep_num=working_ep,
                                                result={
                                                    'decision': 'CONDITIONAL_PASS',
                                                    'score': score,
                                                    'violations': [],
                                                    'warnings': [{'type': 'quality_warning', 'description': reason[:100]}]
                                                },
                                                stage=3
                                            )
                                        except Exception:
                                            pass

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

                            # [V60.9] 구조화된 Blueprint 피드백 생성
                            structured_bp_feedback = self._generate_structured_blueprint_feedback(
                                director_result=audit_result,
                                blueprint=bp,
                                retry_count=reject_count
                            )

                            # [V60.9] 적응형 피드백 강도
                            adaptive_intensity = self._get_adaptive_feedback_intensity(reject_count, stage=3)
                            intensity_guide = f"\n\n[V60.9 재시도 가이드 ({reject_count + 1}회차)]\n{adaptive_intensity['guidance']}"

                            retry_feedback = f"이전 설계 거절 사유: {reason} -> {feedback}{structured_bp_feedback}{intensity_guide}"
                            reject_count += 1
                            self.ui.log(f"   📋 [V60.9] 구조화된 Blueprint 피드백 주입 (기준: {adaptive_intensity['pass_threshold']}점)")

                            # [V55.3] PassRateMonitor: Stage 3 실패 기록
                            if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                try:
                                    _tier = 2 if 'preview' in current_model else 1  # V55.4: 2단계 (1=2.5-pro, 2=3-pro-preview)
                                    self.pass_rate_monitor.record_attempt(
                                        stage=3,
                                        episode=working_ep,
                                        arc=arc_no if arc_no else 0,
                                        attempt_num=reject_count,
                                        success=False,
                                        reject_reason=reason[:100],
                                        generation_method=blueprint_generation_method,
                                        model_tier=_tier
                                    )
                                except Exception:
                                    pass

                            # [V60.2] QualityDashboard: Stage 3 Blueprint REJECT 기록
                            if V50_MODULES_AVAILABLE and self.quality_dashboard:
                                try:
                                    self.quality_dashboard.record_validation(
                                        ep_num=working_ep,
                                        result={
                                            'decision': 'REJECT',
                                            'score': score,
                                            'violations': [{'type': 'director_reject', 'description': reason[:200]}],
                                            'warnings': []
                                        },
                                        stage=3
                                    )
                                except Exception:
                                    pass

                            # [V60.9] Stage 3→2 역방향 피드백 기록 (3회 이상 실패 시 Arc 재설계에 활용)
                            try:
                                self.stage_rejection_history.append({
                                    'stage': 3,
                                    'ep_num': working_ep,
                                    'arc_no': arc_no if arc_no else 0,
                                    'reason': reason[:200],
                                    'feedback': feedback[:200] if feedback else '',
                                    'reject_count': reject_count,
                                    'score': score,
                                    'timestamp': datetime.now().isoformat()
                                })
                                # 3회 이상 실패 시 경고 로그
                                if reject_count >= 3:
                                    self.ui.log(f"   ⚠️ [V60.9] Stage 3 실패 {reject_count}회 - Arc 재설계 피드백 축적 중")
                            except Exception as s3_track_err:
                                self._audit_event("v60_9_stage3_track_error", "stage 3 reject tracking failed", {"error": str(s3_track_err)[:100]})

                            # [V60.2] FailureLearner: Stage 3 실패 기록 추가
                            if V50_MODULES_AVAILABLE and self.failure_learner:
                                try:
                                    self.failure_learner.record_failure(
                                        stage=3,
                                        episode=working_ep,
                                        arc=arc_no if arc_no else 0,
                                        reason=f"Director REJECT: {reason[:150]}",
                                        details={"score": score, "feedback": feedback[:200]}
                                    )
                                except Exception:
                                    pass
                else:
                    self.ui.log("   🚨 [Structure Error] JSON 파싱 실패 또는 필드 누락.")
                    retry_feedback = "반드시 'integrated_scenario' 필드를 포함한 유효한 JSON으로 응답하라."
                    reject_count += 1
                    time.sleep(1)

                # [V55.4] 3회 실패 후 10초 대기 → 4회차 최종 시도
                if reject_count == 3:
                    self.ui.log(f"⏸️ [V55.4] 3회 실패. 10초 대기 후 4회차 최종 시도...")
                    self._audit_event("stage3_cooldown", "3 rejects, waiting 10s before final attempt", {
                        "ep_num": working_ep,
                        "reject_count": reject_count
                    })
                    time.sleep(10)  # 10초 대기 (API 안정화, 컨텍스트 리셋 효과)

                    # 4회차 최종 시도를 위해 카운트 증가하지 않고 continue
                    # (다음 루프에서 reject_count=3 상태로 최고 모델 + ToT로 시도)
                    retry_feedback = f"[🚨 최종 시도] 이전 3회 모두 실패. 구조적 문제를 근본적으로 해결하라.\n{retry_feedback}"
                    reject_count += 1  # 4로 증가
                    continue

                # 6. ####== [V35.5 Pro: 다층적 역전파 자율 수술 시스템]
                if reject_count >= 4:
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
        
        # [V40] Slack 알림 전송 (Blueprint 설계 완료 - 전체 루프 종료 후) - 실패해도 계속 진행
        if working_ep > production_head:
            completed_count = working_ep - production_head
            try:
                notifier.send_notification(
                    title=f"✅ [Blueprint] 제 {production_head}~{working_ep-1}화 설계도 생성 완료",
                    message=f"프로젝트: {self.current_project.name}\n생성된 화수: {completed_count}화",
                    key_metrics={"완료 구간": f"{production_head} ~ {working_ep-1}화", "총 생성": f"{completed_count}개"}
                )
            except Exception as slack_err:
                self.ui.log(f"⚠️ [Slack] 알림 전송 실패 (무시하고 계속): {slack_err}")


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

        # [V48] 서사 다양성 엔진 초기화 (Stage 3에서 안 했으면 여기서)
        if not self.diversity_engine:
            self._init_diversity_engine(window_size=10)

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
                        # [V60] 재시도 실패 시 강제 사용을 위한 마지막 원고 저장
                        self._v60_last_manuscript = None
                        self._v60_force_passed = False

                        for audit_attempt in range(RetryLimits.WRITER_MAX_ATTEMPTS):
                            writer_state_updates = {}  # [V41] 초기화 (정의되지 않은 참조 방지)

                            # 🔒 [V40 Fix] Stage 4에서는 모델 변경 없이 gemini-3-pro-preview 고정 사용
                            from modules.core.constants import AIModels
                            current_writer_model = AIModels.STAGE4_FIXED_WRITER_MODEL

                            # [V55.4] 3회 실패 후 10초 대기 → 4회차 최종 시도
                            if audit_attempt == 3:
                                self.ui.log(f"⏸️ [V55.4] 3회 실패. 10초 대기 후 4회차 최종 시도...")
                                self._audit_event("stage4_cooldown", "3 rejects, waiting 10s before final attempt", {
                                    "ep_num": next_ep,
                                    "audit_attempt": audit_attempt
                                })
                                time.sleep(10)  # 10초 대기 (API 안정화)
                                current_feedback = f"[🚨 최종 시도] 이전 3회 모두 실패. 근본적 문제 해결 필요.\n{current_feedback}"

                            # 재시도 시에도 동일 모델 유지 (로그만 출력)
                            elif audit_attempt > 0:
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

                            # [V48] 서사 다양성 엔진 주입 (Pattern Tracking + Contrastive CoT)
                            diversity_writer_injection = ""
                            use_writer_diversity_sampling = False
                            if self.diversity_engine and audit_attempt == 0:
                                diversity_writer_injection = self.diversity_engine.get_writer_injection()
                                should_sample, sample_reason = self.diversity_engine.should_use_diversity_sampling_for_writer()
                                if should_sample:
                                    use_writer_diversity_sampling = True
                                    self.ui.log(f"🎲 [V48 Diversity] Writer Sampling 활성화: {sample_reason}")

                            # 피드백에 다양성 지침 추가
                            enhanced_feedback = current_feedback
                            if diversity_writer_injection:
                                enhanced_feedback = f"{current_feedback}\n\n{diversity_writer_injection}"

                            # [V60.3] 재시도별 유연한 기준 안내
                            if audit_attempt > 0:
                                retry_guidance = (
                                    f"\n\n📊 [V60 재시도 기준 안내 - {audit_attempt + 1}회차]\n"
                                )
                                if audit_attempt == 1:
                                    retry_guidance += (
                                        "- Director 기준이 약간 완화됩니다.\n"
                                        "- 5개 씬 이상 반영이면 PASS 가능.\n"
                                        "- 핵심 80% 반영 + Hard Constraints 준수 시 승인."
                                    )
                                elif audit_attempt >= 2:
                                    retry_guidance += (
                                        "- Director 기준이 관대해집니다.\n"
                                        "- 3~4개 씬만 있어도 밀도가 충분하면 PASS.\n"
                                        "- 치명적 오류(Hard Constraints)만 없으면 승인 가능.\n"
                                        "- 분량 4,000자만 넘으면 통과 가능성 높음."
                                    )
                                enhanced_feedback = f"{enhanced_feedback}\n{retry_guidance}"

                            # [V60.5] 3회차 이상 재시도 시 프롬프트 간소화
                            use_simplified_prompt = audit_attempt >= 2
                            if use_simplified_prompt:
                                self.ui.log(f"   🎯 [V60.5] 프롬프트 간소화 모드 (핵심만 전달)")
                                # 핵심 피드백만 남기고 부가 정보 제거
                                enhanced_feedback = self._simplify_prompt_for_retry(
                                    enhanced_feedback, current_feedback, audit_attempt
                                )

                            # [V50] 서사 품질 모듈 주입
                            v50_injection = ""
                            if V50_MODULES_AVAILABLE and audit_attempt == 0:
                                v50_injection = self._generate_v50_writer_prompt(next_ep, blueprint)
                                if v50_injection:
                                    enhanced_feedback = f"{enhanced_feedback}\n\n{v50_injection}"

                            # [V60.5] 빈번 REJECT 사유 사전 경고
                            if V50_MODULES_AVAILABLE and self.quality_dashboard and audit_attempt == 0:
                                try:
                                    reject_warning = self.quality_dashboard.get_frequent_reject_warning(stage=4)
                                    if reject_warning:
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{reject_warning}"
                                        self.ui.log(f"   ⚠️ [V60.5] 빈번 REJECT 패턴 경고 주입")
                                except Exception:
                                    pass

                            # [V60.5] 아크 위치 기반 기대치 가이드
                            if audit_attempt == 0:
                                arc_position_guide = self._generate_arc_position_guide(
                                    arc_pos, total_ep_in_arc
                                )
                                if arc_position_guide:
                                    enhanced_feedback = f"{enhanced_feedback}\n\n{arc_position_guide}"

                            # [V51.2] 품질 증폭기 - 제약 조건 주입
                            if V50_MODULES_AVAILABLE and self.quality_amplifier:
                                try:
                                    # 직전 화 아이템 추출
                                    prev_items = self.quality_amplifier.extract_items_from_manuscript(prev_text) if prev_text else []

                                    # 제약 조건 생성
                                    quality_constraints = self.quality_amplifier.generate_writer_constraints(
                                        ep_num=next_ep,
                                        blueprint=blueprint,
                                        prev_manuscript=prev_text,
                                        prev_items=prev_items
                                    )
                                    if quality_constraints:
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{quality_constraints}"

                                    # 첫 시도에만 로그
                                    if audit_attempt == 0:
                                        self.ui.log(f"   🎯 [V51.2] 품질 제약 {len(prev_items)}개 아이템 추적 중")
                                except Exception as qa_err:
                                    pass  # 비치명적 오류 무시

                            # [V51.3] 에이전트 지능 향상 - Few-Shot + Anti-Pattern
                            if V50_MODULES_AVAILABLE and self.agent_intelligence and audit_attempt == 0:
                                try:
                                    intel_prompt = self.agent_intelligence.get_writer_enhancement(
                                        ep_num=next_ep,
                                        blueprint=blueprint,
                                        prev_manuscript=prev_text
                                    )
                                    if intel_prompt:
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{intel_prompt}"
                                        self.ui.log(f"   🧠 [V51.3] 지능 향상 프롬프트 주입")
                                except Exception as ia_err:
                                    self._audit_event("v51_module_error", "intelligence amplifier failed", {"module": "V51.3", "error": str(ia_err)[:50]})

                            # [V51.4] 실패 학습 제약 주입 - [V60.3] 모든 재시도에 누적 적용
                            if V50_MODULES_AVAILABLE and self.failure_learner:
                                try:
                                    # 재시도 횟수에 따라 제약 강도 증가
                                    learned_constraints = self.failure_learner.generate_constraint_prompt(
                                        stage=4,
                                        severity_filter="CRITICAL" if audit_attempt >= 2 else None  # 3회차부터는 CRITICAL만
                                    )
                                    if learned_constraints:
                                        # 재시도 시 강조 표시 추가
                                        if audit_attempt > 0:
                                            learned_constraints = f"🚨 [재시도 {audit_attempt + 1}회차 - 필수 준수]\n{learned_constraints}"
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{learned_constraints}"
                                        self.ui.log(f"   📚 [V51.4] 실패 학습 제약 주입 (시도 {audit_attempt + 1}회)")
                                except Exception as fl_err:
                                    self._audit_event("v51_module_error", "failure learner constraint injection failed", {"module": "V51.4", "error": str(fl_err)[:50]})

                            # [V60.4] 점수 추이 기반 피드백 주입
                            if V50_MODULES_AVAILABLE and self.quality_dashboard:
                                try:
                                    trend_injection = self.quality_dashboard.get_trend_injection(stage=4)
                                    if trend_injection:
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{trend_injection}"
                                        trend_analysis = self.quality_dashboard.analyze_score_trend(stage=4)
                                        if trend_analysis.get('trend') == 'declining':
                                            self.ui.log(f"   📉 [V60.4] 점수 하락 추세 경고 (최근 평균: {trend_analysis.get('recent_avg')}점)")
                                        elif trend_analysis.get('trend') == 'improving':
                                            self.ui.log(f"   📈 [V60.4] 점수 상승 추세 (최근 평균: {trend_analysis.get('recent_avg')}점)")
                                except Exception as trend_err:
                                    self._audit_event("v60_trend_error", "trend injection failed", {"error": str(trend_err)[:50]})

                            # [V60.5] PASS 확률 예측 사전 경고 (첫 시도 시)
                            if V50_MODULES_AVAILABLE and self.quality_dashboard and audit_attempt == 0:
                                try:
                                    # 과거 데이터 기반 예측 (현재 메트릭 없이)
                                    pass_prediction = self.quality_dashboard.predict_pass_probability(stage=4)
                                    if pass_prediction.get('probability', 100) < 50:
                                        pass_warning = self.quality_dashboard.get_pass_prediction_warning(stage=4)
                                        if pass_warning:
                                            enhanced_feedback = f"{enhanced_feedback}\n\n{pass_warning}"
                                            self.ui.log(f"   ⚠️ [V60.5] PASS 확률 예측: {pass_prediction.get('probability', 0):.0f}%")
                                except Exception:
                                    pass

                            # [V53.1] 동적 프롬프트 가중치 주입
                            if V50_MODULES_AVAILABLE and self.prompt_weighter and audit_attempt == 0:
                                try:
                                    weighted_prompt = self.prompt_weighter.get_weighted_prompt(
                                        agent_type="writer",
                                        stage=4,
                                        top_n=3
                                    )
                                    if weighted_prompt:
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{weighted_prompt}"
                                        self.ui.log(f"   ⚖️ [V53.1] 동적 프롬프트 가중치 주입")
                                except Exception as pw_err:
                                    self._audit_event("v53_module_error", "prompt weighter injection failed", {"module": "V53.1", "error": str(pw_err)[:50]})

                            # [V54.5 → V60.4] 성공 패턴 가이드 주입 (재시도에서도 활용)
                            if V50_MODULES_AVAILABLE and self.success_patterns:
                                try:
                                    # [V60.4] 재시도 시 rejection context 포함
                                    target_context = {
                                        "ep_num": next_ep,
                                        "arc_num": arc_no if arc_no else 0
                                    }

                                    if audit_attempt > 0 and current_feedback:
                                        # 재시도 시: REJECT 사유 기반 패턴 검색
                                        target_context["rejection_context"] = current_feedback[:500]
                                        target_context["retry_mode"] = True

                                    pattern_guidance = self.success_patterns.get_guidance_from_patterns(
                                        content_type="manuscript",
                                        target_context=target_context
                                    )
                                    if pattern_guidance:
                                        if audit_attempt > 0:
                                            enhanced_feedback = f"{enhanced_feedback}\n\n[🏆 V60.4 성공 패턴 (REJECT 개선용)]\n{pattern_guidance}"
                                            self.ui.log(f"   🏆 [V60.4] 재시도 맞춤 성공 패턴 주입 (attempt {audit_attempt + 1})")
                                        else:
                                            enhanced_feedback = f"{enhanced_feedback}\n\n{pattern_guidance}"
                                            self.ui.log(f"   🏆 [V54.5] 성공 패턴 가이드 주입")
                                    # [V60.6] 성공 원고 스타일 주입 (첫 시도에서만)
                                    if audit_attempt == 0 and hasattr(self.success_patterns, 'generate_style_injection'):
                                        style_injection = self.success_patterns.generate_style_injection(n_samples=5)
                                        if style_injection:
                                            enhanced_feedback = f"{enhanced_feedback}\n\n{style_injection}"
                                            self.ui.log(f"   ✨ [V60.6] 성공 원고 스타일 가이드 주입")

                                except Exception as pattern_err:
                                    self._audit_event("v54_pattern_error", "writer pattern guide failed", {"error": str(pattern_err)[:100]})

                            # [V60.8] Writer 사전 가이드 통합 주입 (Director REJECT 방지)
                            if audit_attempt == 0:
                                try:
                                    # Episode Bible 조회 (아이템 획득 시점용)
                                    episode_bibles = []
                                    if hasattr(self.current_project, 'db') and self.current_project.db:
                                        try:
                                            episode_bibles = self.current_project.db.get_all_episode_bibles()
                                        except Exception:
                                            pass

                                    v60_8_guidance = self._generate_writer_guidance_v60_8(
                                        blueprint=blueprint,
                                        prev_manuscript=prev_text if prev_text else "",
                                        episode_bibles=episode_bibles,
                                        target_len=target_ep_len
                                    )
                                    if v60_8_guidance:
                                        enhanced_feedback = f"{enhanced_feedback}\n\n{v60_8_guidance}"
                                        self.ui.log(f"   📋 [V60.8] Writer 사전 가이드 5종 주입 완료")
                                except Exception as v60_8_err:
                                    self._audit_event("v60_8_guidance_error", "writer guidance failed", {"error": str(v60_8_err)[:100]})

                            # [V55.2] Constitutional Self-Check 주입
                            if V50_MODULES_AVAILABLE and self.constitutional_checker and audit_attempt == 0:
                                try:
                                    # 현재 소지품 추출
                                    current_inventory = []
                                    if blueprint and isinstance(blueprint, dict):
                                        # Blueprint에서 소지품 정보 추출 시도
                                        state = blueprint.get('protagonist_state', {})
                                        if isinstance(state, dict):
                                            current_inventory = state.get('inventory', [])

                                    constitutional_prompt = self.constitutional_checker.get_full_injection(
                                        stage=4,
                                        context={
                                            'blueprint': blueprint,
                                            'prev_manuscript': prev_text[-1000:] if prev_text else "",
                                            'inventory': current_inventory,
                                            'feedback': enhanced_feedback
                                        }
                                    )
                                    enhanced_feedback = f"{constitutional_prompt}\n\n{enhanced_feedback}"
                                    self.ui.log(f"   📜 [V55.2] Constitutional Self-Check 주입 완료")
                                except Exception as const_err:
                                    self._audit_event("v55_constitutional_error", "writer constitutional injection failed", {"error": str(const_err)[:100]})

                            # [V55.3] Writer Template 주입 (모든 시도에 적용 - 구조 가이드 지속)
                            if V50_MODULES_AVAILABLE and self.writer_template:
                                try:
                                    ms_template = self.writer_template.generate_template(
                                        blueprint=blueprint,
                                        prev_ending=prev_text[-500:] if prev_text else "",
                                        inventory=current_inventory
                                    )
                                    template_injection = self.writer_template.generate_prompt_injection(ms_template)

                                    # [V56] 강화된 Blueprint 구조 강제 주입
                                    scene_count = ms_template.total_scenes
                                    total_min = ms_template.total_min_chars
                                    total_max = ms_template.total_max_chars
                                    closing_hook = ms_template.closing_hook

                                    structure_enforcement = f"""
[V56 MANDATORY STRUCTURE ENFORCEMENT]
제{working_ep}화는 다음 구조를 절대 변경하면 안 됩니다:

1. 씬 개수: 정확히 {scene_count}개 (추가/삭제 금지)
2. 분량 목표: {total_min}~{total_max}자 (미달/초과 시 REJECT)
3. 클리프행어: 반드시 다음 내용으로 마무리
   → "{closing_hook[:100]}..."

4. 소지품 제약: 다음 아이템만 사용 가능
   → {', '.join(current_inventory[:5]) if current_inventory else '없음'}

위반 시 Director가 100% REJECT합니다. 각 씬을 순서대로 빠짐없이 작성하세요.
"""
                                    enhanced_feedback = f"{structure_enforcement}\n\n{template_injection}\n\n{enhanced_feedback}"
                                    self.ui.log(f"   📝 [V56] Writer Template + 구조 강제 주입 ({scene_count}개 씬)")
                                except Exception as wt_err:
                                    self._audit_event("v55_template_error", "writer template injection failed", {"error": str(wt_err)[:100]})

                            # [V54.2] 컨텍스트 압축 (토큰 절감)
                            compressed_context = None
                            compressed_prev_text = prev_text  # 기본값
                            if V50_MODULES_AVAILABLE and self.context_compressor:
                                try:
                                    raw_context = {
                                        "blueprint": blueprint,
                                        "prev_text": prev_text[-3000:] if prev_text else "",
                                        "arc_data": arc_data
                                    }
                                    compression_result = self.context_compressor.compress(
                                        context=raw_context,
                                        target_type="manuscript",
                                        max_chars=6000
                                    )
                                    compressed_context = compression_result.compressed
                                    # 압축된 prev_text 추출
                                    if compressed_context and 'prev_text' in compressed_context:
                                        compressed_prev_text = compressed_context.get('prev_text', prev_text[-2000:] if prev_text else "")
                                    if compression_result.compression_ratio < 0.8:
                                        self.ui.log(f"   📦 [V54.2] 컨텍스트 압축: {compression_result.compression_ratio:.0%} ({compression_result.original_size}→{compression_result.compressed_size}자)")
                                        # 압축 정보를 피드백에 추가
                                        enhanced_feedback = f"{enhanced_feedback}\n\n[V54.2 Context Summary] 핵심 컨텍스트 {compression_result.compressed_size}자로 압축됨"
                                except Exception as compress_err:
                                    self._audit_event("v54_compress_error", "context compression failed", {"error": str(compress_err)[:100]})

                            # [V55] 원고 품질/분량 향상 피드백 주입
                            if V50_MODULES_AVAILABLE and self.manuscript_enhancer and audit_attempt == 0:
                                try:
                                    # 이전 원고 분석하여 개선점 도출
                                    if prev_text and len(prev_text) > 1000:
                                        v55_result = self.manuscript_enhancer.analyze(
                                            manuscript=prev_text[-5000:],  # 이전 원고 마지막 부분
                                            current_ep=next_ep
                                        )
                                        if v55_result.total_feedback:
                                            # 분량 향상 관련 피드백만 추출하여 주입
                                            v55_injection = f"[V55 품질/분량 향상 지침]\n이전 원고 분석 결과:\n"
                                            if v55_result.priority_fixes:
                                                v55_injection += "우선 개선: " + ", ".join(v55_result.priority_fixes[:3])
                                            if v55_result.subtext_ratio > 0.3:
                                                v55_injection += f"\n→ 직접 서술을 묘사로 변환하세요 (현재 {v55_result.subtext_ratio:.0%})"
                                            if v55_result.page_turner_score < 60:
                                                v55_injection += f"\n→ 문단 끝에 훅을 추가하세요 (현재 {v55_result.page_turner_score:.0f}점)"
                                            enhanced_feedback = f"{enhanced_feedback}\n\n{v55_injection}"
                                            self.ui.log(f"   ✨ [V55] 품질/분량 향상 피드백 주입 (이슈 {len(v55_result.priority_fixes)}개)")
                                except Exception as v55_err:
                                    self._audit_event("v55_enhancer_error", "manuscript enhancer failed", {"error": str(v55_err)[:100]})

                            # 💡 Writer 집필 호출 (예외 처리 추가)
                            try:
                                def writer_generator():
                                    """원고 단일 생성 함수"""
                                    # V54.2: 압축된 이전 원고 사용 (토큰 절감)
                                    effective_prev_text = compressed_prev_text if compressed_prev_text else prev_text
                                    return self.agents['writer'].write_v20_manuscript(
                                        ep_num=next_ep, breakdown_doc=enriched_breakdown,
                                        master_bible=self.current_project.master_bible,
                                        hud_report=hud_report, purism_prompt=purism,
                                        style_mode=selected_style["guide"], intro_dna=getattr(self.current_project, 'intro_dna', 'CYNICAL'),
                                        feedback=enhanced_feedback, prev_full_manuscript=effective_prev_text,
                                        arc_doc={
                                                "MUST_FOCUS_ON": focus_tag,
                                                "FULL_ARC_MAP": arc_tactical,
                                                "PATTERN_PROFILE": arc_data.get('hybrid_composition', {}),
                                                "PATTERN_MIXING_LOGIC": arc_data.get('hybrid_composition', {}).get('mixing_logic', '')
                                            },
                                        tactical_references=tactical_refs
                                    )

                                # [V55.3] 원고 생성 방법 추적
                                manuscript_generation_method = "writer"  # 기본값

                                # [V54.4] Two-Phase 원고 생성 (3회차+ 시도에서 발동)
                                if V50_MODULES_AVAILABLE and self.two_phase_ms and audit_attempt >= 2:
                                    self.ui.log(f"   ✌️ [V54.4] Two-Phase 원고 생성 발동 (시도 {audit_attempt + 1}회차)")
                                    try:
                                        # V54.2 압축 컨텍스트 활용
                                        tp_context = compressed_context if compressed_context else {
                                            "ep_num": next_ep,
                                            "arc_data": arc_data,
                                            "hud": hud_report
                                        }
                                        tp_prev = compressed_prev_text[-2000:] if compressed_prev_text else ""

                                        two_phase_result = self.two_phase_ms.generate(
                                            blueprint=blueprint,
                                            prev_ending=tp_prev,
                                            context=tp_context,
                                            style_guide=selected_style.get("guide", "")
                                        )
                                        if two_phase_result and len(two_phase_result) > 3000:
                                            writer_res = {
                                                "title": f"제 {next_ep} 화",
                                                "content": two_phase_result
                                            }
                                            manuscript_generation_method = "two_phase"
                                            self.ui.log(f"   ✅ [V54.4] Two-Phase 완료 ({len(two_phase_result)}자)")
                                            self._audit_event("two_phase_generation", "manuscript two-phase as retry", {
                                                "ep_num": next_ep,
                                                "audit_attempt": audit_attempt,
                                                "length": len(two_phase_result)
                                            })
                                        else:
                                            self.ui.log(f"   ⚠️ [V54.4] Two-Phase 결과 부족, 기본 생성기 사용")
                                            writer_res = writer_generator()
                                    except Exception as tp_err:
                                        self.ui.log(f"   ⚠️ [V54.4] Two-Phase 실패, 기본 생성기 사용: {tp_err}")
                                        self._audit_event("two_phase_manuscript_error", "manuscript two-phase failed", {
                                            "ep_num": next_ep,
                                            "audit_attempt": audit_attempt,
                                            "error": str(tp_err)[:100]
                                        })
                                        writer_res = writer_generator()
                                # [V60.6] Beat 단위 분할 생성 (후반부 요약 문제 시 2회차에서 발동)
                                elif audit_attempt == 1 and current_feedback and any(kw in current_feedback for kw in ['후반부', '밀도 불균형', '요약됨', 'Scene 5', 'Scene 6']):
                                    self.ui.log(f"   🎯 [V60.6] Beat 단위 분할 생성 발동 (후반부 품질 문제 감지)")
                                    try:
                                        if hasattr(self.agents['writer'], 'write_manuscript_by_beats'):
                                            beat_result = self.agents['writer'].write_manuscript_by_beats(
                                                ep_num=next_ep,
                                                blueprint=blueprint,
                                                master_bible=self.current_project.master_bible,
                                                hud_report=hud_report,
                                                style_guide=selected_style.get("guide", ""),
                                                feedback=enhanced_feedback,
                                                prev_manuscript=prev_text[-2000:] if prev_text else ""
                                            )
                                            if beat_result and beat_result.get('content') and len(beat_result.get('content', '')) > 3500:
                                                writer_res = beat_result
                                                manuscript_generation_method = "beat_split"
                                                phase_lens = beat_result.get('phase_lengths', [0, 0])
                                                self.ui.log(f"   ✅ [V60.6] Beat 분할 완료 (전반: {phase_lens[0]}자, 후반: {phase_lens[1]}자)")
                                                self._audit_event("beat_split_generation", "manuscript beat-split", {
                                                    "ep_num": next_ep,
                                                    "phase_lengths": phase_lens
                                                })
                                            else:
                                                self.ui.log(f"   ⚠️ [V60.6] Beat 분할 결과 부족, 기본 생성기 사용")
                                                writer_res = writer_generator()
                                        else:
                                            writer_res = writer_generator()
                                    except Exception as beat_err:
                                        self.ui.log(f"   ⚠️ [V60.6] Beat 분할 실패, 기본 생성기 사용: {beat_err}")
                                        writer_res = writer_generator()

                                elif use_writer_diversity_sampling:
                                    self.ui.log(f"   🎲 원고 3개 후보 생성 중... (패턴 반복 감지)")
                                    writer_res, diversity_meta = self.diversity_engine.generate_diverse_manuscript(
                                        generator_fn=writer_generator,
                                        n_samples=3,
                                        force=True
                                    )
                                    manuscript_generation_method = "diversity"
                                    if diversity_meta.get('selected_score'):
                                        self.ui.log(f"   ✨ 선택된 원고 다양성 점수: {diversity_meta['selected_score'].get('total', 0):.1f}")
                                    self._audit_event("writer_diversity_sampling", "manuscript diversity sampling", {
                                        "ep_num": next_ep,
                                        "n_samples": diversity_meta.get('n_samples', 0),
                                        "selected_score": diversity_meta.get('selected_score', {}).get('total', 0)
                                    })
                                else:
                                    writer_res = writer_generator()

                                # [V60] HUD 급변 감지 결과 로깅
                                if hasattr(self.agents['writer'], 'last_hud_anomalies'):
                                    hud_anomalies = self.agents['writer'].last_hud_anomalies
                                    if hud_anomalies and hud_anomalies.get('has_anomalies'):
                                        self._audit_event("hud_anomaly_detected", "HUD sudden change detected", {
                                            "ep_num": next_ep,
                                            "anomaly_count": len(hud_anomalies.get('anomalies', [])),
                                            "anomalies": [
                                                {"type": a.get('type'), "severity": a.get('severity', 'medium')}
                                                for a in hud_anomalies.get('anomalies', [])[:5]
                                            ]
                                        })
                                        self.ui.log(f"   ⚠️ [V60] HUD 급변 {len(hud_anomalies.get('anomalies', []))}건 감지됨")

                                        # [V60.1] QualityDashboard에 HUD 급변 기록
                                        if self.quality_dashboard:
                                            self.quality_dashboard.record_hud_anomaly(next_ep, hud_anomalies.get('anomalies', []))

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

                                # [V60] 마지막 원고 저장 (재시도 실패 시 강제 사용용)
                                self._v60_last_manuscript = {
                                    'content': temp_content,
                                    'title': temp_title,
                                    'attempt': audit_attempt + 1
                                }

                                # [V52.1] Self-Reflection: 첫 시도에서만 자기 성찰 적용
                                if V50_MODULES_AVAILABLE and self.self_reflector and audit_attempt == 0:
                                    try:
                                        bp_context = json.dumps(blueprint, ensure_ascii=False)[:2000] if blueprint else ""
                                        reflection_result = self.self_reflector.reflect_and_improve(
                                            output=temp_content,
                                            context=bp_context,
                                            target=ReflectionTarget.WRITER
                                        )
                                        if reflection_result.improvement_score > 0:
                                            temp_content = reflection_result.improved
                                            self.ui.log(f"   🔄 [V52.1] Self-Reflection: {len(reflection_result.changes_made)}개 이슈 자체 수정")
                                            self._audit_event("self_reflection", "writer self-improved", {
                                                "ep_num": next_ep,
                                                "changes": reflection_result.changes_made,
                                                "score": reflection_result.improvement_score
                                            })
                                    except Exception as sr_err:
                                        self.ui.log(f"   ⚠️ [V52.1] Self-Reflection 실패 (비치명적): {sr_err}")

                                # [V60.6] Writer 자가 수정 루프 (첫 시도에서만)
                                if audit_attempt == 0 and hasattr(self.agents['writer'], 'quick_self_check'):
                                    try:
                                        # 빠른 자가 점검 (LLM 없이)
                                        quick_check = self.agents['writer'].quick_self_check(temp_content, blueprint)

                                        if quick_check.get('needs_llm_review') and len(quick_check.get('quick_issues', [])) >= 2:
                                            self.ui.log(f"   🔄 [V60.6] 자가 점검 이슈 발견: {len(quick_check['quick_issues'])}건")
                                            for issue in quick_check['quick_issues'][:2]:
                                                self.ui.log(f"      - {issue}")

                                            # LLM 기반 자가 수정 (비용 최적화: 이슈 2개 이상일 때만)
                                            self_review_result = self.agents['writer'].self_review_and_refine(
                                                manuscript=temp_content,
                                                blueprint=blueprint,
                                                checklist_feedback="",
                                                max_refinements=1
                                            )

                                            if self_review_result.get('refinement_count', 0) > 0:
                                                refined = self_review_result.get('refined_manuscript', '')
                                                if refined and len(refined) >= len(temp_content) * 0.9:
                                                    temp_content = refined
                                                    self.ui.log(f"   ✅ [V60.6] 자가 수정 완료: {len(self_review_result.get('changes_made', []))}개 이슈 해결")
                                                    self._audit_event("writer_self_review", "writer self-refined", {
                                                        "ep_num": next_ep,
                                                        "changes": self_review_result.get('changes_made', [])[:5],
                                                        "refinement_count": self_review_result.get('refinement_count', 0)
                                                    })
                                            elif self_review_result.get('self_review_passed'):
                                                self.ui.log(f"   ✅ [V60.6] 자가 검토 통과 (수정 불필요)")
                                        else:
                                            self.ui.log(f"   ✅ [V60.6] 빠른 자가 점검 통과")

                                    except Exception as sr_err:
                                        self.ui.log(f"   ⚠️ [V60.6] 자가 수정 실패 (비치명적): {str(sr_err)[:50]}")

                                # [V53.3] Confidence Calibration - 신뢰도 평가
                                if V50_MODULES_AVAILABLE and self.confidence_calibrator:
                                    try:
                                        confidence_result = self.confidence_calibrator.assess(
                                            content=temp_content,
                                            content_type="manuscript",
                                            context={"blueprint": blueprint, "prev_manuscript": prev_text}
                                        )
                                        self.ui.log(f"   📊 [V53.3] 신뢰도: {confidence_result.score}/100 ({confidence_result.level.value})")

                                        if confidence_result.concerns:
                                            for concern in confidence_result.concerns[:2]:
                                                self.ui.log(f"      ⚠️ {concern}")

                                        # 신뢰도가 낮으면 추가 검증 권장 로그
                                        if confidence_result.needs_extra_verification:
                                            self.ui.log(f"   🔍 [V53.3] 추가 검증 권장 (신뢰도 낮음)")

                                        self._audit_event("confidence_calibration", "manuscript confidence assessed", {
                                            "ep_num": next_ep,
                                            "score": confidence_result.score,
                                            "level": confidence_result.level.value,
                                            "recommendation": confidence_result.recommendation
                                        })
                                    except Exception as cc_err:
                                        self.ui.log(f"   ⚠️ [V53.3] Confidence Calibration 실패 (비치명적): {cc_err}")

                                # [V53.2] Chain-of-Verification - 사실 검증
                                if V50_MODULES_AVAILABLE and self.chain_of_verification and audit_attempt == 0:
                                    try:
                                        cov_context = {
                                            "prev_manuscript": prev_text,
                                            "blueprint": blueprint,
                                            "hud": hud_report
                                        }
                                        cov_result = self.chain_of_verification.verify(
                                            generated_content=temp_content,
                                            context=cov_context,
                                            content_type="manuscript"
                                        )

                                        if cov_result.should_regenerate:
                                            self.ui.log(f"   🚨 [V53.2] CoVe 치명적 모순 발견 ({cov_result.severity.value})")
                                            for issue in cov_result.issues[:2]:
                                                self.ui.log(f"      - [{issue.category}] {issue.description[:60]}...")

                                            self._audit_event("cove_reject", "chain of verification failed", {
                                                "ep_num": next_ep,
                                                "severity": cov_result.severity.value,
                                                "issues": len(cov_result.issues)
                                            })

                                            current_feedback = self.chain_of_verification.generate_feedback(cov_result)
                                            continue  # Writer 재생성

                                        elif not cov_result.passed:
                                            self.ui.log(f"   ⚠️ [V53.2] CoVe 경고: {cov_result.summary[:50]}... (진행)")
                                        else:
                                            self.ui.log(f"   ✅ [V53.2] CoVe 사실 검증 통과")

                                    except Exception as cov_err:
                                        self.ui.log(f"   ⚠️ [V53.2] Chain-of-Verification 실패 (비치명적): {cov_err}")

                                # [V55.3] WriterTemplate 검증: 템플릿 준수 여부 확인
                                if V50_MODULES_AVAILABLE and self.writer_template and blueprint:
                                    try:
                                        # 템플릿 재생성 (검증용)
                                        validation_template = self.writer_template.generate_template(
                                            blueprint=blueprint,
                                            prev_ending=prev_text[-500:] if prev_text else "",
                                            inventory=current_inventory
                                        )
                                        template_validation = self.writer_template.validate_against_template(
                                            manuscript=temp_content,
                                            template=validation_template
                                        )

                                        if not template_validation.get('passed'):
                                            issues = template_validation.get('issues', [])
                                            if issues:
                                                self.ui.log(f"   ⚠️ [V55.3] Template 검증 경고: {issues[0]}")
                                                # REJECT하지 않고 경고만 출력 (Director가 최종 판단)
                                                self._audit_event("template_validation_warning", "writer template validation warning", {
                                                    "ep_num": next_ep,
                                                    "issues": issues[:2],
                                                    "scene_coverage": template_validation.get('scene_coverage', 'N/A')
                                                })
                                        else:
                                            self.ui.log(f"   ✅ [V55.3] Template 검증 통과 ({template_validation.get('scene_coverage', 'N/A')})")
                                    except Exception as tv_err:
                                        self.ui.log(f"   ⚠️ [V55.3] Template 검증 실패 (비치명적): {tv_err}")

                                # [V52.4] Cross-Agent Verification: Writer → Blueprint 준수 검증
                                if V50_MODULES_AVAILABLE and self.cross_verifier and audit_attempt == 0:
                                    try:
                                        compliance_result = self.cross_verifier.verify_writer_compliance(
                                            manuscript=temp_content,
                                            blueprint=blueprint,
                                            use_llm=True
                                        )

                                        if compliance_result.level == ComplianceLevel.VIOLATION:
                                            self.ui.log(f"   🚨 [V52.4] Blueprint 준수 위반 (점수: {compliance_result.score:.0%})")
                                            for v in compliance_result.violations[:2]:
                                                self.ui.log(f"      - {v.get('item', '')}: {v.get('reason', '')[:60]}...")

                                            self._audit_event("cross_agent_reject", "writer blueprint compliance violation", {
                                                "ep_num": next_ep,
                                                "score": compliance_result.score,
                                                "violations": len(compliance_result.violations)
                                            })

                                            # 실패 기록
                                            if self.failure_learner:
                                                self.failure_learner.record_failure(
                                                    stage=4,
                                                    episode=next_ep,
                                                    arc=arc_data.get('arc_no', 0),
                                                    reason=f"Blueprint 준수 위반: {compliance_result.details[:100]}",
                                                    details={"violations": compliance_result.violations}
                                                )

                                            current_feedback = self.cross_verifier.generate_feedback(compliance_result, "writer")
                                            continue  # Writer 재생성
                                        elif compliance_result.level == ComplianceLevel.PARTIAL:
                                            self.ui.log(f"   ⚠️ [V52.4] Blueprint 부분 준수 (점수: {compliance_result.score:.0%}, 계속 진행)")
                                        else:
                                            self.ui.log(f"   ✅ [V52.4] Blueprint 완전 준수 확인")
                                    except Exception as cv_err:
                                        self.ui.log(f"   ⚠️ [V52.4] Cross-Agent 검증 실패 (비치명적): {cv_err}")

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

                                # ═══════════════════════════════════════════════════════════════
                                # [V49.1] ContinuityInspector: 원고 연속성 검증
                                # ═══════════════════════════════════════════════════════════════
                                continuity_passed = True
                                if 'continuity_inspector' in self.agents:
                                    try:
                                        self.ui.layout["main"].update(Panel(f"🔍 Stage 4.4: 연속성 검증 중...", title="ContinuityInspector"))
                                        
                                        # 이전 원고 조회 (최근 5화)
                                        prev_manuscripts = self.agents['continuity_inspector'].get_prev_manuscripts(
                                            current_ep=next_ep, window=5
                                        )
                                        
                                        # Blueprint 조회
                                        current_blueprint = self.current_project.get_blueprint(next_ep) or {}

                                        # [V60] Blueprint 완전성 사전 검증 (Python, LLM 비용 $0)
                                        bp_completeness = self.agents['director']._validate_blueprint_completeness_v60(
                                            manuscript=temp_content,
                                            blueprint=current_blueprint
                                        )

                                        # [V60.1] QualityDashboard에 Blueprint 커버리지 기록
                                        if self.quality_dashboard:
                                            self.quality_dashboard.record_blueprint_coverage(next_ep, bp_completeness)

                                        if not bp_completeness.get('valid', True):
                                            # 70% 미만 커버리지 → 즉시 REJECT (LLM 호출 절감)
                                            continuity_passed = False
                                            scene_coverage = bp_completeness.get('scene_coverage', 0)
                                            missing = bp_completeness.get('missing_scenes', [])

                                            self.ui.log(f"🚨 [V60] Blueprint 반영률 부족: {scene_coverage:.1f}% (최소 70% 필요)")
                                            if missing:
                                                self.ui.log(f"   누락 씬: {[m.get('scene') for m in missing[:3]]}")

                                            audit_feedback = bp_completeness.get('feedback', '')
                                            self._audit_event("blueprint_coverage_reject", "manuscript blueprint coverage low", {
                                                "ep_num": next_ep,
                                                "coverage": scene_coverage,
                                                "expected": bp_completeness.get('expected_scenes'),
                                                "reflected": bp_completeness.get('reflected_scenes'),
                                                "missing": [m.get('scene') for m in missing[:5]]
                                            })

                                            # 재시도 루프로 돌아감
                                            if audit_attempt < 2:
                                                self.ui.log(f"🔄 [V60] Blueprint 반영 부족으로 재생성 ({audit_attempt + 1}회차)")
                                                continue
                                            else:
                                                self.ui.log(f"⚠️ [V60] 재시도 한도 초과, 경고와 함께 진행")

                                        # 원고 연속성 검증
                                        manuscript_continuity = self.agents['continuity_inspector'].inspect_manuscript(
                                            current_ep=next_ep,
                                            manuscript=temp_content,
                                            blueprint=current_blueprint,
                                            prev_manuscripts=prev_manuscripts
                                        )
                                        
                                        if manuscript_continuity.get('decision') == 'REJECT':
                                            continuity_passed = False
                                            severity = manuscript_continuity.get('severity', 'UNKNOWN')
                                            fix_instructions = manuscript_continuity.get('fix_instructions', '')
                                            violations = manuscript_continuity.get('violations', [])
                                            
                                            self.ui.log(f"🚨 [ContinuityInspector] 연속성 위반 감지 (심각도: {severity})")
                                            for v in violations[:3]:  # 최대 3개만 표시
                                                self.ui.log(f"   ⚠️ {v.get('type', 'unknown')}: {v.get('description', '')[:100]}")
                                            
                                            # 피드백 반영
                                            audit_feedback = f"[V49.1 연속성 위반]\n{fix_instructions}"
                                            
                                            self._audit_event("continuity_reject", "manuscript continuity failed", {
                                                "ep_num": next_ep,
                                                "severity": severity,
                                                "violations": [v.get('type') for v in violations]
                                            })

                                            # [V51.4] 실패 기록
                                            if V50_MODULES_AVAILABLE and self.failure_learner:
                                                for v in violations[:3]:
                                                    self.failure_learner.record_failure(
                                                        stage=4,
                                                        episode=next_ep,
                                                        arc=arc_data.get('arc_no', 0),
                                                        reason=f"Manuscript: {v.get('type', 'unknown')}: {v.get('description', '')[:150]}",
                                                        details={"severity": severity}
                                                    )
                                        else:
                                            warnings = manuscript_continuity.get('warnings', [])
                                            if warnings:
                                                self.ui.log(f"⚠️ [ContinuityInspector] 경고 {len(warnings)}건 (PASS 처리)")
                                            else:
                                                self.ui.log(f"✅ [ContinuityInspector] 연속성 검증 통과")
                                            
                                    except Exception as ci_err:
                                        self.ui.log(f"⚠️ [ContinuityInspector] 원고 검증 중 오류 (비치명적): {ci_err}")
                                        # 오류 시 통과 처리 (프로세스 중단 방지)
                                        continuity_passed = True
                                
                                # 연속성 위반 시 Writer 재생성 (재시도 횟수 고려)
                                if not continuity_passed:
                                    if audit_attempt < 2:  # 2회까지만 연속성 이유로 재시도
                                        self.ui.log(f"🔄 [V49.1] 연속성 위반으로 원고 재생성 ({audit_attempt + 1}회차)")
                                        continue  # while 루프 다시
                                    else:
                                        self.ui.log(f"⚠️ [V49.1] 연속성 경고 있지만 재시도 횟수 초과로 진행")

                                # [V52.2] Critic 리뷰 (Director 전 1차 필터)
                                critic_feedback = ""
                                if 'critic' in self.agents and audit_attempt == 0:
                                    try:
                                        self.ui.log(f"   👹 [V52.2] Critic 심층 리뷰 중...")
                                        genre_type = self.selected_genre.get('type', 'wuxia') if self.selected_genre else 'wuxia'

                                        critic_result = self.agents['critic'].hybrid_review(
                                            manuscript=temp_content,
                                            blueprint=blueprint,
                                            ep_num=next_ep,
                                            genre=genre_type,
                                            prev_manuscript=prev_text,
                                            hud_report=hud_report,
                                            use_llm=True  # LLM 심층 리뷰 활성화
                                        )

                                        recommendation = critic_result.get('recommendation', 'PASS')
                                        overall_score = critic_result.get('overall_score', 7)

                                        self.ui.log(f"   👹 [V52.2] Critic 결과: {overall_score}/10, 권장={recommendation}")

                                        if recommendation == 'MAJOR_REVISE':
                                            # 심각한 문제 발견 - 피드백과 함께 재생성
                                            critic_feedback = self.agents['critic'].generate_revision_feedback(critic_result)
                                            self.ui.log(f"   🔄 [V52.2] 주요 수정 필요, Writer 재생성...")
                                            current_feedback = critic_feedback
                                            self._audit_event("critic_major_revise", "critic requested major revision", {
                                                "ep_num": next_ep,
                                                "score": overall_score
                                            })
                                            continue  # Writer 재생성

                                        elif recommendation == 'REVISE':
                                            # 경미한 문제 - 피드백 기록만 하고 진행
                                            critic_feedback = self.agents['critic'].generate_revision_feedback(critic_result)
                                            self.ui.log(f"   ⚠️ [V52.2] 경미한 수정 권장 (진행)")

                                    except Exception as critic_err:
                                        self.ui.log(f"   ⚠️ [V52.2] Critic 리뷰 실패 (비치명적): {critic_err}")

                                # [V53.6] Adversarial Self-Play - 필살기 1단계 (3회차+ 시도에서 발동)
                                if V50_MODULES_AVAILABLE and self.adversarial_self_play and audit_attempt >= 2:
                                    try:
                                        self.ui.log(f"   🔥 [V53.6] Adversarial Self-Play 필살기 발동! (시도 {audit_attempt + 1}회차)")
                                        asp_result = self.adversarial_self_play.generate_with_adversary(
                                            initial_content=temp_content,
                                            content_type="manuscript",
                                            context={"blueprint": blueprint, "prev_manuscript": prev_text}
                                        )

                                        if asp_result.improvement_delta > 0:
                                            temp_content = asp_result.final_output
                                            self.ui.log(f"   ⚔️ [V53.6] ASP 완료: +{asp_result.improvement_delta}점 향상 ({asp_result.rounds}라운드)")
                                        else:
                                            self.ui.log(f"   ⚔️ [V53.6] ASP 완료: 원본 유지 (이미 양호)")

                                        self._audit_event("adversarial_self_play_ultimate", "asp as last resort", {
                                            "ep_num": next_ep,
                                            "audit_attempt": audit_attempt,
                                            "improvement": asp_result.improvement_delta,
                                            "rounds": asp_result.rounds,
                                            "final_decision": asp_result.adversary_feedback.decision
                                        })
                                    except Exception as asp_err:
                                        self.ui.log(f"   ⚠️ [V53.6] Adversarial Self-Play 실패 (비치명적): {asp_err}")

                                # [V53.7] Multi-Agent Deliberation - 필살기 2단계 (3회차+ 시도에서 발동)
                                if V50_MODULES_AVAILABLE and self.multi_agent_deliberation and audit_attempt >= 2:
                                    try:
                                        self.ui.log(f"   🔥 [V53.7] Multi-Agent Deliberation 필살기 발동!")
                                        mad_result = self.multi_agent_deliberation.deliberate(
                                            content=temp_content,
                                            content_type="manuscript",
                                            context={"blueprint": blueprint, "arc_data": arc_data}
                                        )

                                        if mad_result.consensus_reached:
                                            if mad_result.consensus_output != temp_content:
                                                temp_content = mad_result.consensus_output
                                                self.ui.log(f"   🗣️ [V53.7] 3자 토론 합의: {mad_result.consensus_score}점, 수정 반영")
                                            else:
                                                self.ui.log(f"   🗣️ [V53.7] 3자 토론 합의: {mad_result.consensus_score}점, 원본 유지")
                                        else:
                                            self.ui.log(f"   ⚠️ [V53.7] 토론 합의 미달: {mad_result.consensus_score}점")
                                            if mad_result.action_items:
                                                for item in mad_result.action_items[:2]:
                                                    self.ui.log(f"      - {item}")

                                        self._audit_event("multi_agent_deliberation_ultimate", "mad as last resort", {
                                            "ep_num": next_ep,
                                            "audit_attempt": audit_attempt,
                                            "consensus_reached": mad_result.consensus_reached,
                                            "consensus_score": mad_result.consensus_score
                                        })
                                    except Exception as mad_err:
                                        self.ui.log(f"   ⚠️ [V53.7] Multi-Agent Deliberation 실패 (비치명적): {mad_err}")

                                # [V53.4] Pre-Director Checklist (Director 호출 전 빠른 체크)
                                if V50_MODULES_AVAILABLE and self.pre_director_checklist:
                                    try:
                                        checklist_result = self.pre_director_checklist.check(
                                            content=temp_content,
                                            content_type="manuscript",
                                            context={
                                                "blueprint": blueprint,
                                                "prev_manuscript": prev_text
                                            }
                                        )

                                        if not checklist_result.passed:
                                            self.ui.log(f"   ❌ [V53.4] Pre-Director 체크 실패: {checklist_result.summary}")
                                            for reason in checklist_result.blocking_reasons[:2]:
                                                self.ui.log(f"      - {reason}")

                                            self._audit_event("pre_director_fail", "pre-director checklist failed", {
                                                "ep_num": next_ep,
                                                "fail_count": checklist_result.fail_count
                                            })

                                            # 피드백 추가 후 재생성
                                            current_feedback = self.pre_director_checklist.get_feedback(checklist_result)
                                            continue  # Writer 재생성

                                        elif checklist_result.warning_count > 0:
                                            self.ui.log(f"   ⚠️ [V53.4] Pre-Director 경고 {checklist_result.warning_count}건 (진행)")
                                        else:
                                            self.ui.log(f"   ✅ [V53.4] Pre-Director 체크 통과")

                                        # [V60.5] 현재 메트릭 기반 PASS 확률 예측
                                        if self.quality_dashboard:
                                            try:
                                                # 대화 비율 계산
                                                import re as re_pass
                                                dialogue_matches = re_pass.findall(r'"[^"]+?"', temp_content)
                                                dialogue_chars = sum(len(m) for m in dialogue_matches)
                                                dialogue_ratio = dialogue_chars / len(temp_content) if temp_content else 0

                                                # 씬 반영률 추정 (pre-checklist 결과에서)
                                                scene_coverage = 0.5  # 기본값
                                                for item in checklist_result.items:
                                                    if '반영' in item.name and item.message:
                                                        import re as re_cov
                                                        cov_match = re_cov.search(r'(\d+)%', item.message)
                                                        if cov_match:
                                                            scene_coverage = int(cov_match.group(1)) / 100

                                                current_metrics = {
                                                    'length': len(temp_content),
                                                    'dialogue_ratio': dialogue_ratio,
                                                    'scene_coverage': scene_coverage,
                                                    'pre_checklist_fails': checklist_result.fail_count,
                                                    'pre_checklist_warnings': checklist_result.warning_count
                                                }

                                                pass_prediction = self.quality_dashboard.predict_pass_probability(
                                                    stage=4, current_metrics=current_metrics
                                                )

                                                prob = pass_prediction.get('probability', 50)
                                                if prob < 40:
                                                    self.ui.log(f"   🚨 [V60.5] PASS 확률 예측: {prob:.0f}% (위험)")
                                                    # 낮은 확률 시 경고 요인 로그
                                                    for factor in pass_prediction.get('factors', [])[:2]:
                                                        if factor.get('weight', 0) < 0:
                                                            self.ui.log(f"      - {factor.get('name')}: {factor.get('impact')}")
                                                elif prob < 60:
                                                    self.ui.log(f"   ⚠️ [V60.5] PASS 확률 예측: {prob:.0f}% (보통)")
                                                else:
                                                    self.ui.log(f"   ✅ [V60.5] PASS 확률 예측: {prob:.0f}% (양호)")

                                            except Exception:
                                                pass  # 비치명적 오류 무시

                                    except Exception as checklist_err:
                                        self.ui.log(f"   ⚠️ [V53.4] Pre-Director Checklist 실패 (비치명적): {checklist_err}")

                                # 🎬 Director 최종 원고 정밀 검수 (예외 처리 추가)
                                self.ui.layout["main"].update(Panel(f"🎬 Stage 4.5: 편집장 원고 정밀 검수 중...", title="Director"))
                                try:
                                    # [V49] Blueprint 텍스트 파일 읽기 (씬 범위 초과 체크용)
                                    blueprint_text = ''
                                    try:
                                        bp_file = self.current_project.paths.root / 'plans' / 'blueprints' / f'blueprint_{next_ep:04d}.txt'
                                        if bp_file.exists():
                                            blueprint_text = bp_file.read_text(encoding='utf-8')
                                    except Exception as bp_err:
                                        self.ui.log(f"⚠️ [V49] Blueprint 텍스트 로드 실패 (비치명적): {bp_err}")
                                    
                                    # [V45] validation_context 구성 (V0128 검증용)
                                    validation_context = self._build_validation_context(
                                        ep_num=next_ep,
                                        blueprint=self.current_project.get_blueprint(next_ep),
                                        mode='MANUSCRIPT',
                                        blueprint_text=blueprint_text  # [V49] 씬 범위 체크용
                                    )
                                    audit_res = self.agents['director'].audit_manuscript(
                                        ep_num=next_ep, manuscript=temp_content, arc_doc=arc_tactical,
                                        history_summary=causal_summary, prev_full_text=prev_text,
                                        arc_pos=arc_pos, total_eps=total_ep_in_arc,
                                        target_len=5000,
                                        retry_count=audit_attempt,  # [V40.3 추가] 재시도 횟수 전달
                                        validation_context=validation_context  # [V45] V0128 검증용
                                    )

                                    # [V60.3] Director 결과 풍부화 (action_items, 에러 카테고리)
                                    audit_res = self._enrich_director_result(
                                        audit_res, stage=4, content_length=len(temp_content)
                                    )

                                    # [V60.3] action_items 로그 출력
                                    if audit_res.get('action_items'):
                                        for item in audit_res['action_items'][:2]:  # 최대 2개
                                            self.ui.log(f"   📋 [{item.get('severity', 'MEDIUM')}] {item.get('description', '')[:50]}")
                                            if item.get('suggestion'):
                                                self.ui.log(f"      → {item.get('suggestion', '')[:80]}")

                                    # [V60.1] QualityDashboard에 검증 결과 기록
                                    if self.quality_dashboard:
                                        self.quality_dashboard.record_validation(next_ep, audit_res, stage=4)

                                    # [V60.6] 적응형 PASS 기준선 적용
                                    if hasattr(self.agents['director'], 'apply_adaptive_decision'):
                                        try:
                                            original_decision = audit_res.get('decision', 'REJECT')
                                            original_score = audit_res.get('score', 0)

                                            adaptive_result = self.agents['director'].apply_adaptive_decision(
                                                score=original_score,
                                                original_decision=original_decision,
                                                arc_pos=arc_pos,
                                                total_eps=total_ep_in_arc,
                                                retry_count=audit_attempt
                                            )

                                            if adaptive_result.get('adjusted'):
                                                new_decision = adaptive_result.get('decision', original_decision)
                                                threshold = adaptive_result.get('threshold_used', 65)
                                                reason = adaptive_result.get('reason', '')

                                                self.ui.log(f"   📊 [V60.6] 적응형 기준 적용: {original_decision} → {new_decision}")
                                                self.ui.log(f"      기준점: {threshold}점 ({reason})")

                                                # CONDITIONAL_PASS는 PASS로 처리하되 경고 로그
                                                if new_decision == 'CONDITIONAL_PASS':
                                                    audit_res['decision'] = 'PASS'
                                                    audit_res['conditional_pass'] = True
                                                    audit_res['adaptive_threshold'] = threshold
                                                    self.ui.log(f"   ⚠️ [V60.6] 조건부 통과 (적응형 기준)")

                                                self._audit_event("adaptive_threshold_applied", "adaptive pass threshold", {
                                                    "ep_num": next_ep,
                                                    "original_decision": original_decision,
                                                    "new_decision": new_decision,
                                                    "score": original_score,
                                                    "threshold": threshold,
                                                    "reason": reason
                                                })
                                        except Exception as at_err:
                                            self.ui.log(f"   ⚠️ [V60.6] 적응형 기준 적용 실패 (비치명적): {str(at_err)[:50]}")

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

                                    # [Phase 5.2.3] Self-Refine 조건 확인 및 실행
                                    v0128_result = audit_res.get('v0128_full_result', {})
                                    if v0128_result.get('refine_recommended', False):
                                        refine_reason = v0128_result.get('refine_reason', '')
                                        self.ui.log(f"✨ [Self-Refine] 품질 정제 시작 ({refine_reason})")
                                        try:
                                            # Self-Refine은 JSON을 기대하므로 writer_data를 JSON으로 변환
                                            manuscript_json = json.dumps({
                                                'title': temp_title,
                                                'content': temp_content,
                                                'state_updates': writer_state_updates
                                            }, ensure_ascii=False)

                                            # Self-Refine은 JSON 문자열을 반환하므로 파싱 필요
                                            refined_json = self.agents['writer']._self_refine(
                                                manuscript=manuscript_json,
                                                target_areas=['emotion', 'prose', 'cliffhanger', 'sensory']
                                            )

                                            # JSON 파싱하여 content 추출
                                            refined_data = self.agents['writer']._extract_json_robust(refined_json) if isinstance(refined_json, str) else refined_json

                                            if refined_data and isinstance(refined_data, dict):
                                                refined_content = refined_data.get('content', '')

                                                # 품질 체크: 길이가 원본의 80% 이상인지
                                                if refined_content and len(refined_content) > len(temp_content) * 0.8:
                                                    temp_content = refined_content
                                                    # title도 업데이트 (있으면)
                                                    if refined_data.get('title'):
                                                        temp_title = refined_data['title']

                                                    self.ui.log(f"✅ [Self-Refine] 품질 정제 완료 (길이: {len(refined_content)}자)")
                                                    self._audit_event("self_refine_success", "manuscript refined", {
                                                        "ep_num": next_ep,
                                                        "reason": refine_reason,
                                                        "length_change": len(refined_content) - len(temp_content)
                                                    })
                                                else:
                                                    self.ui.log(f"⚠️ [Self-Refine] 결과 품질 미달 (길이: {len(refined_content)}자), 원본 유지")
                                            else:
                                                self.ui.log(f"⚠️ [Self-Refine] JSON 파싱 실패, 원본 유지")
                                        except Exception as refine_err:
                                            self.ui.log(f"⚠️ [Self-Refine] 오류 발생, 원본 유지: {refine_err}")
                                            import traceback
                                            traceback.print_exc()

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

                                    # [V54.5] 성공 패턴 기록
                                    if V50_MODULES_AVAILABLE and self.success_patterns:
                                        try:
                                            self.success_patterns.record_success(
                                                content_type="manuscript",
                                                content={"text": temp_content, "title": temp_title},
                                                context={
                                                    "ep_num": next_ep,
                                                    "arc_num": arc_no if arc_no else 0
                                                },
                                                score=audit_res.get('score', 80)
                                            )
                                        except Exception as sp_err:
                                            self._audit_event("v54_success_pattern_error", "manuscript success pattern recording failed", {"error": str(sp_err)[:50]})

                                    # [V55.3] PassRateMonitor: Stage 4 성공 기록
                                    if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                        try:
                                            # Stage 4는 gemini-3-pro-preview 고정 (tier 3)
                                            self.pass_rate_monitor.record_attempt(
                                                stage=4,
                                                episode=next_ep,
                                                arc=arc_no if arc_no else 0,
                                                attempt_num=audit_attempt + 1,
                                                success=True,
                                                generation_method=manuscript_generation_method,
                                                model_tier=3
                                            )
                                        except Exception:
                                            pass

                                    break
                                else:
                                    reason = audit_res.get('reason', '품질 미달')
                                    feedback = audit_res.get('feedback', '상세 묘사 부족')
                                    score = audit_res.get('score', 0)

                                    # [V40.2 User Request] 2번 재시도 후에는 심각한 문제가 아니면 수용
                                    if audit_attempt >= 2:
                                        # 심각한 문제 체크 (서사 폭주, 서사 정체, 모순)
                                        critical_keywords = self._get_dynamic_critical_keywords()  # [V60.3] 동적 생성
                                        is_critical = any(kw in reason for kw in critical_keywords) or score < 20

                                        if is_critical:
                                            # 심각한 문제는 계속 거부
                                            self.ui.log(f"🚨 [Critical Issue] {reason} - 심각한 문제로 계속 재시도합니다.")
                                            self._audit_event("critical_issue", "serious problem in manuscript", {
                                                "ep_num": next_ep,
                                                "reason": reason,
                                                "score": score
                                            })
                                            # [V56] 구조화된 CRITICAL 피드백 생성
                                            current_feedback = f"\n[🚨 CRITICAL ISSUE]\n{self._classify_rejection_feedback(reason, feedback, blueprint)}"

                                            # [V60.4] CRITICAL 경로에서도 action_items 주입
                                            action_items = audit_res.get('action_items', [])
                                            if action_items:
                                                action_items_text = "\n\n[📋 V60.4 CRITICAL 개선 지침]\n"
                                                for idx, item in enumerate(action_items[:3], 1):
                                                    severity = item.get('severity', 'CRITICAL')
                                                    desc = item.get('description', '')
                                                    suggestion = item.get('suggestion', '')
                                                    action_items_text += f"  {idx}. [🔥{severity}] {desc}\n"
                                                    if suggestion:
                                                        action_items_text += f"     → 필수 해결: {suggestion}\n"
                                                current_feedback = f"{current_feedback}{action_items_text}"

                                            # [V60.9] CRITICAL 경로 적응형 피드백 강도 (더 엄격함)
                                            adaptive_intensity = self._get_adaptive_feedback_intensity(audit_attempt, stage=4)
                                            # CRITICAL 경로는 pass_threshold를 80점으로 상향 조정
                                            critical_intensity_guide = (
                                                f"\n\n[V60.9 CRITICAL 재시도 가이드 ({audit_attempt + 1}회차)]\n"
                                                f"⚠️ CRITICAL 이슈로 인해 더 엄격한 기준이 적용됩니다.\n"
                                                f"- 최소 PASS 기준: 80점 이상\n"
                                                f"- 핵심 수정 사항만 집중 (다른 부분은 절대 건드리지 마세요)\n"
                                                f"- 원고 분량은 현재 분량을 유지하세요"
                                            )
                                            current_feedback = f"{current_feedback}{critical_intensity_guide}"
                                            self.ui.log(f"   📋 [V60.9] CRITICAL 적응형 피드백 주입 (엄격 기준: 80점)")
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

                                            # [V55.3] PassRateMonitor: Stage 4 조건부 성공 기록
                                            if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                                try:
                                                    self.pass_rate_monitor.record_attempt(
                                                        stage=4,
                                                        episode=next_ep,
                                                        arc=arc_no if arc_no else 0,
                                                        attempt_num=audit_attempt + 1,
                                                        success=True,
                                                        generation_method=manuscript_generation_method,
                                                        model_tier=3
                                                    )
                                                except Exception:
                                                    pass

                                            break
                                    else:
                                        # 일반 거부 (2번 미만)
                                        self.ui.log(f"🚨 [Director 반려] 사유: {reason}")

                                        # [V60.6] 부분 수정 시도 (2회차 시, 특정 씬 문제일 때)
                                        if audit_attempt == 1 and hasattr(self.agents['writer'], 'identify_problem_scenes'):
                                            try:
                                                problem_scenes = self.agents['writer'].identify_problem_scenes(
                                                    manuscript=temp_content,
                                                    blueprint=blueprint,
                                                    reject_reason=reason
                                                )

                                                # 문제 씬이 2개 이하이고 CRITICAL이 아니면 부분 수정 시도
                                                critical_problems = [p for p in problem_scenes if p.get('severity') == 'CRITICAL']
                                                if problem_scenes and len(problem_scenes) <= 3 and len(critical_problems) <= 1:
                                                    self.ui.log(f"   🔧 [V60.6] 부분 수정 시도: {len(problem_scenes)}개 문제 씬 감지")
                                                    for prob in problem_scenes[:2]:
                                                        self.ui.log(f"      - {prob.get('scene_key')}: {prob.get('issue')} ({prob.get('severity')})")

                                                    partial_result = self.agents['writer'].partial_rewrite(
                                                        manuscript=temp_content,
                                                        blueprint=blueprint,
                                                        problem_scenes=problem_scenes,
                                                        max_scenes_to_rewrite=2
                                                    )

                                                    if partial_result and partial_result.get('content'):
                                                        rewritten = partial_result.get('rewritten_scenes', [])
                                                        self.ui.log(f"   ✅ [V60.6] 부분 수정 완료: {', '.join(rewritten)}")
                                                        temp_content = partial_result['content']
                                                        manuscript_generation_method = "partial_rewrite"

                                                        self._audit_event("partial_rewrite", "manuscript partial rewrite", {
                                                            "ep_num": next_ep,
                                                            "rewritten_scenes": rewritten,
                                                            "original_issues": [p.get('issue') for p in problem_scenes[:3]]
                                                        })

                                                        # 부분 수정 후 Pre-Director Checklist 재실행
                                                        continue  # 다음 루프에서 다시 Director 검증
                                            except Exception as pr_err:
                                                self.ui.log(f"   ⚠️ [V60.6] 부분 수정 실패: {str(pr_err)[:50]}")

                                        # [V56] 구조화된 피드백 생성
                                        current_feedback = self._classify_rejection_feedback(reason, feedback, blueprint)

                                        # [V60.4] action_items를 Writer 프롬프트에 주입
                                        action_items = audit_res.get('action_items', [])
                                        if action_items:
                                            action_items_text = "\n\n[📋 V60.4 구체적 개선 지침 (action_items)]\n"
                                            for idx, item in enumerate(action_items[:3], 1):  # 최대 3개
                                                severity = item.get('severity', 'MEDIUM')
                                                desc = item.get('description', '')
                                                suggestion = item.get('suggestion', '')
                                                action_items_text += f"  {idx}. [{severity}] {desc}\n"
                                                if suggestion:
                                                    action_items_text += f"     → 해결책: {suggestion}\n"
                                            current_feedback = f"{current_feedback}{action_items_text}"
                                            self.ui.log(f"   📋 [V60.4] {len(action_items)}개 action_items Writer에 주입")

                                        # [V60.9] 적응형 피드백 강도 (Stage 4)
                                        adaptive_intensity = self._get_adaptive_feedback_intensity(audit_attempt, stage=4)
                                        intensity_guide = f"\n\n[V60.9 재시도 가이드 ({audit_attempt + 1}회차)]\n{adaptive_intensity['guidance']}"
                                        current_feedback = f"{current_feedback}{intensity_guide}"
                                        self.ui.log(f"   📋 [V60.9] 적응형 피드백 강도 주입 (기준: {adaptive_intensity['pass_threshold']}점)")

                                        # [V55.3] PassRateMonitor: Stage 4 실패 기록
                                        if V50_MODULES_AVAILABLE and self.pass_rate_monitor:
                                            try:
                                                self.pass_rate_monitor.record_attempt(
                                                    stage=4,
                                                    episode=next_ep,
                                                    arc=arc_no if arc_no else 0,
                                                    attempt_num=audit_attempt + 1,
                                                    success=False,
                                                    reject_reason=reason[:100],
                                                    generation_method=manuscript_generation_method,
                                                    model_tier=3
                                                )
                                            except Exception:
                                                pass

                                        # [V60.9] Stage 4→3 역방향 피드백 기록 (다음 에피소드 Blueprint에 전달)
                                        try:
                                            pre_checklist_result = pre_director_result if 'pre_director_result' in dir() else {}
                                            reverse_feedback_4to3 = self._generate_reverse_feedback_stage4_to_3(
                                                writer_reject_reason=reason,
                                                pre_checklist_result=pre_checklist_result
                                            )
                                            self.stage_rejection_history.append({
                                                'stage': 4,
                                                'ep_num': next_ep,
                                                'arc_no': arc_no if arc_no else 0,
                                                'reason': reason[:200],
                                                'feedback': feedback[:200] if feedback else '',
                                                'reverse_guidance': reverse_feedback_4to3,
                                                'timestamp': datetime.now().isoformat()
                                            })
                                            self.ui.log(f"   📝 [V60.9] Stage 4 REJECT 역방향 피드백 저장 (다음 화 Blueprint용)")
                                        except Exception as rf_err:
                                            self._audit_event("v60_9_reverse_feedback_error", "stage 4 reverse feedback failed", {"error": str(rf_err)[:100]})

                                        # [V55] 반려된 원고 분석하여 구체적 개선 피드백 생성
                                        if V50_MODULES_AVAILABLE and self.manuscript_enhancer and temp_content:
                                            try:
                                                v55_reject_analysis = self.manuscript_enhancer.analyze(
                                                    manuscript=temp_content,
                                                    current_ep=next_ep
                                                )
                                                if v55_reject_analysis.priority_fixes:
                                                    v55_fixes = "\n[V55 구체적 개선 지침]\n" + "\n".join(
                                                        f"  - {fix}" for fix in v55_reject_analysis.priority_fixes[:4]
                                                    )
                                                    current_feedback = f"{current_feedback}{v55_fixes}"
                                                    self.ui.log(f"   ✨ [V55] 반려 원고 분석: {len(v55_reject_analysis.priority_fixes)}개 개선점 식별")
                                            except Exception:
                                                pass

                                        # [V54.3] 실패 기록 및 적응형 재시도 지침 생성
                                        if V50_MODULES_AVAILABLE and self.adaptive_manager:
                                            try:
                                                error_type = self.adaptive_manager.record_failure(
                                                    ep_num=next_ep,
                                                    agent="writer",
                                                    error_info={
                                                        "message": reason,
                                                        "reason": feedback,
                                                        "score": score
                                                    },
                                                    attempt=audit_attempt
                                                )
                                                # 다음 시도를 위한 적응형 지침 주입
                                                adaptive_guidance = self.adaptive_manager.get_injection_prompt(
                                                    ep_num=next_ep,
                                                    agent="writer",
                                                    current_attempt=audit_attempt + 1
                                                )
                                                if adaptive_guidance:
                                                    current_feedback = f"{current_feedback}\n{adaptive_guidance}"
                                                    self.ui.log(f"   🔄 [V54.3] 적응형 재시도 지침 주입")
                                            except Exception as ar_err:
                                                self._audit_event("v54_adaptive_retry_error", "adaptive retry guidance failed", {"error": str(ar_err)[:50]})
                            else:
                                self.ui.log(f"🚨 [Structure Error] Writer JSON 파싱 실패")
                                current_feedback = "\n[🚨 System Error]: JSON 규격을 엄수하여 다시 집필하라."

                        # ═══════════════════════════════════════════════════════════════
                        # [V60] 재시도 제한 후 강제 진행 로직
                        # ═══════════════════════════════════════════════════════════════
                        if not final_pure_content:
                            # 마지막으로 생성된 원고가 있으면 경고와 함께 강제 사용
                            if hasattr(self, '_v60_last_manuscript') and self._v60_last_manuscript:
                                self.ui.log(f"⚠️ [V60 FORCE PASS] 제 {next_ep}화 모든 재시도 실패. 마지막 원고를 경고와 함께 강제 수용합니다.")
                                self._audit_event("stage4_force_pass", f"EP{next_ep} force passed after max retries", {
                                    "ep_num": next_ep,
                                    "retry_count": RetryLimits.WRITER_MAX_ATTEMPTS,
                                    "reason": "max_retries_exceeded"
                                })

                                final_pure_content = self._v60_last_manuscript.get('content', '')
                                final_ep_title = self._v60_last_manuscript.get('title', f'제 {next_ep}화')

                                # 강제 통과 경고를 원고 상단에 주입
                                force_pass_warning = f"""
[⚠️ V60 강제 통과 경고]
이 원고는 {RetryLimits.WRITER_MAX_ATTEMPTS}회 검증 모두 실패 후 강제 수용되었습니다.
품질 문제가 있을 수 있으니 수동 검토가 권장됩니다.
{"=" * 50}

"""
                                final_pure_content = force_pass_warning + final_pure_content

                                # 경고 플래그 설정
                                self._v60_force_passed = True
                            else:
                                self.ui.log(f"❌ [Critical] 제 {next_ep}화 집필 최종 실패. 유효한 원고 없음.")
                                return 
                    



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
                            
                            # [V49 FIX] prev_actual이 비어있으면 Bible의 현재 HUD 상태를 fallback으로 사용
                            if not prev_actual and hasattr(self.sys, 'hud') and self.sys.hud:
                                try:
                                    bible_hud = self.sys.hud.pro_data
                                    if bible_hud and isinstance(bible_hud, dict):
                                        prev_actual = bible_hud.copy()
                                        self.ui.log(f"🔄 [V49] prev_actual 비어있음 → Bible HUD fallback 사용 (키 개수: {len(prev_actual)})")
                                except Exception as e:
                                    self.ui.log(f"⚠️ [V49] Bible HUD fallback 실패: {e}")

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

                                # ═══════════════════════════════════════════════════════════════
                                # [V60.26] 품질 추적 모듈 통합 (감정/파워/상태)
                                # ═══════════════════════════════════════════════════════════════
                                if V50_MODULES_AVAILABLE:
                                    try:
                                        # V60.26-1 감정선 추적 (self.emotion_tracker 사용)
                                        if self.emotion_tracker:
                                            emotion_state, intensity = self.emotion_tracker.analyze_manuscript_emotion(final_pure_content)
                                            if emotion_state in EmotionArcTracker.EMOTION_STATES:
                                                self.emotion_tracker.add_episode_emotion(next_ep, emotion_state, intensity)
                                                self.emotion_tracker.save_to_db(self.current_project.db)
                                                self.ui.log(f"      💓 [V60.26] 감정: {emotion_state} (강도: {intensity:.2f})")

                                                # 감정 정체 경고
                                                is_monotonous, recommendation = self.emotion_tracker.check_monotony(last_n_episodes=5)
                                                if is_monotonous:
                                                    self.ui.log(f"      ⚠️ [V60.26] 감정 정체 감지 - 다음 화에서 변화 필요")

                                        # V60.26-2 파워 스케일링 검증
                                        if self.power_scaling and current_hud:
                                            # HUD에서 파워 추출 시도
                                            power_value = current_hud.get('무력', current_hud.get('combat_power', 0))
                                            if isinstance(power_value, str):
                                                power_match = re.search(r'\d+', str(power_value))
                                                power_value = int(power_match.group()) if power_match else 0

                                            if power_value > 0:
                                                protagonist = protagonist_name or "주인공"
                                                validation = self.power_scaling.validate_growth(
                                                    protagonist, arc=arc_no, new_power=power_value
                                                )
                                                if not validation.get('valid', True):
                                                    self.ui.log(f"      ⚠️ [V60.26] 파워 급등: {validation.get('message', '')}")
                                                else:
                                                    self.power_scaling.set_power(protagonist, arc=arc_no, power=power_value)

                                        # V60.26-3 상태 변화 추적 (에피소드별 내공 변화 추적)
                                        if self.state_delta_tracker and current_hud:
                                            try:
                                                energy = current_hud.get('내공', current_hud.get('internal_energy', 100))
                                                if isinstance(energy, str):
                                                    energy_match = re.search(r'\d+', str(energy))
                                                    energy = int(energy_match.group()) if energy_match else 100

                                                # 이전 에너지와 비교하여 델타 계산
                                                prev_energy = self.state_delta_tracker.get_current_energy()
                                                delta = energy - prev_energy

                                                if delta != 0:
                                                    reason = "전투/수련" if delta < 0 else "휴식/회복"
                                                    result = self.state_delta_tracker.apply_energy_delta(
                                                        arc=arc_no, episode=next_ep,
                                                        delta=delta, reason=reason
                                                    )
                                                    if result.get('warning'):
                                                        self.ui.log(f"      ⚠️ [V60.26] 내공 변화 경고: {result['warning']}")
                                            except Exception:
                                                pass  # 비치명적

                                        # V60.26-5 캐릭터 음성 프로파일 추출
                                        if self.voice_profiler and final_pure_content:
                                            try:
                                                # 주인공 음성 프로파일 추출/업데이트
                                                protag = protagonist_name or "주인공"
                                                profile = self.voice_profiler.extract_profile_from_text(protag, final_pure_content)
                                                if profile and profile.sample_dialogues:
                                                    self.ui.log(f"      🎭 [V60.26] 음성 프로파일 추출: {protag} (대사 {len(profile.sample_dialogues)}개)")
                                            except Exception:
                                                pass  # 비치명적

                                    except Exception as v60_26_err:
                                        self.ui.log(f"      ⚠️ [V60.26] 품질 추적 오류 (비치명적): {str(v60_26_err)[:50]}")

                                # ═══════════════════════════════════════════════════════════════
                                # [V50] 서사 품질 향상 모듈 피드백
                                # ═══════════════════════════════════════════════════════════════
                                if V50_MODULES_AVAILABLE:
                                    try:
                                        self._process_v50_post_episode(next_ep, final_pure_content, blueprint)
                                    except Exception as v50_err:
                                        self.ui.log(f"      ⚠️ [V50] 서사 품질 분석 실패 (비치명적): {v50_err}")

                                    # [V55.3] PassRateMonitor 저장 및 경고 체크 (에피소드 완료 시)
                                    if self.pass_rate_monitor:
                                        try:
                                            self.pass_rate_monitor.save()
                                            # 10회차마다 통과율 경고 체크
                                            if next_ep % 10 == 0:
                                                alerts = self.pass_rate_monitor.check_alerts(window=20)
                                                for alert in alerts:
                                                    self.ui.log(f"   {alert}")
                                        except Exception:
                                            pass

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
if __name__ == "__main__":
    SovereignApp().boot()