"""
[V49.3] State Tracker Agent - 상태 추적 및 DAG 타임라인 검증
[V60.95] PresetRegistry 연동 - 동적 필드 기반 상태 추적
[V64.P3] Facade 패턴 리팩토링 - NPC/Financial/Plots 서브모듈 분리
[V66.1] F-1 시간선추적 + F-3 regex폴백 + F-8 영구부상 + F-10 사망취소
[V66.1] 동행자 추적 + 약속/맹세 추적 + 주인공 감정 상태 추적

Arc 내 각 회차의 상태를 자동 추적하고
DAG(Directed Acyclic Graph) 형태로 타임라인을 구성하여 검증합니다.

서브모듈:
  - state_tracker_npc.py      → NPC 레지스트리, 사망/무공/관계/부상/이동/영구부상/동행자/주인공감정 추적
  - state_tracker_financial.py → 금융 상태 추적 (투자물)
  - state_tracker_plots.py     → 완결된 플롯 + 엔티티 명칭 일관성 + 시간선 추적 + 약속/맹세 추적
"""

import copy
import logging
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from modules.domain.agents.state_tracker_financial import StateTrackerFinancial

# [V64.P3] 서브모듈 import
from modules.domain.agents.state_tracker_npc import StateTrackerNPC
from modules.domain.agents.state_tracker_plots import StateTrackerPlots

# [V60.95] PresetRegistry 연동
try:
    from modules.core.stage0 import PresetRegistry

    PRESET_AVAILABLE = True
except ImportError:
    PRESET_AVAILABLE = False
    PresetRegistry = None


@dataclass
class EpisodeState:
    """에피소드 단위 상태 스냅샷 [V60.95 확장]"""

    ep_num: int
    # 기본 필드 (하위 호환성)
    location: str = ""
    weapons: list[str] = field(default_factory=list)
    items: list[str] = field(default_factory=list)
    injuries: str = "정상"  # 정상/경상/중상/위독
    internal_energy: int = 100  # 0-100%
    relationships: dict[str, str] = field(default_factory=dict)  # NPC -> 상태

    # [V60.95] 동적 확장 필드 (프리셋 기반)
    extra_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        base = {
            "ep_num": self.ep_num,
            "location": self.location,
            "weapons": self.weapons.copy(),
            "items": self.items.copy(),
            "injuries": self.injuries,
            "internal_energy": self.internal_energy,
            "relationships": self.relationships.copy(),
        }
        # 동적 필드 병합
        base.update(copy.deepcopy(self.extra_fields))
        return base

    def get(self, key: str, default=None):
        """필드 조회 (기본 + 동적)"""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra_fields.get(key, default)

    def set(self, key: str, value):
        """필드 설정 (기본이면 속성, 아니면 동적)"""
        if hasattr(self, key) and key != "extra_fields":
            setattr(self, key, value)
        else:
            self.extra_fields[key] = value


@dataclass
class StateTransition:
    """상태 전이 정보"""

    from_ep: int
    to_ep: int
    changes: dict[str, tuple[any, any]]  # field -> (before, after)
    justification: str = ""
    is_valid: bool = True
    issues: list[str] = field(default_factory=list)


class StateTracker:
    """
    [V49.3] Arc 상태 추적기
    [V60.95] PresetRegistry 연동 - 동적 필드 + 고밀도 추적
    [V64.P3] Facade 패턴 - NPC/Financial/Plots 서브모듈로 분리

    Arc 설계 시 각 회차의 상태를 추적하여 DAG 형태로 관리하고
    상태 불일치(무기 중복 획득, 부상 무시 등)를 사전에 탐지합니다.

    Usage:
        # 기존 방식 (하위 호환)
        tracker = StateTracker()

        # PresetRegistry 연동 (권장)
        from modules.core.stage0 import PresetRegistry
        preset = PresetRegistry(base_genre='wuxia')
        tracker = StateTracker(preset_registry=preset)

        tracker.load_arc_design(arc_tactical_doc)
        issues = tracker.validate_timeline()
    """

    def __init__(self, preset_registry=None, llm_client=None, genre: str = "wuxia") -> None:
        self.states: dict[int, EpisodeState] = {}  # ep_num -> state
        self.transitions: list[StateTransition] = []
        self.global_items: set[str] = set()  # 전체 소지 아이템 추적
        self.acquired_items: dict[str, int] = {}  # item -> 획득 에피소드
        self.consumed_items: dict[str, int] = {}  # item -> 소모 에피소드

        # [V60.94] NPC 상태 추적 (생사, 무장, 수준)
        self.npc_registry: dict[str, dict] = {}  # name -> {프리셋 기반 필드들}
        # [V60.94] 주인공 무공 목록 추적
        self.protagonist_skills: set[str] = set()  # 습득한 무공 목록
        self.skill_acquisitions: dict[str, int] = {}  # skill -> 습득 Arc

        # [V62.7] 완결된 플롯 누적 추적
        self.resolved_plots: list[dict] = []
        self._resolved_plots_max: int = 500  # [TF-B-1] 메모리 누적 상한
        # [V62.7→V64 P2-4] 비-NPC 엔티티 명칭 레지스트리 (LRU, max 500)
        self.entity_name_registry: OrderedDict = OrderedDict()
        self._entity_registry_max_size = 500  # [V66] 200→500 엔티티 망각 방지
        # [V66] 조직/장소 파괴 추적
        self.entity_destructions: list[dict] = []
        # [V66] NPC-NPC 관계 추적 (key: sorted tuple of names)
        self.npc_npc_relationships: dict = {}
        # [V66] 장르별 확장 레지스트리 (필요 시 초기화)
        self.skill_cooldown_registry: dict = {}  # hunter: skill → {cooldown, last_used_ep}
        self.dungeon_clear_registry: dict = {}  # hunter: dungeon_id → {cleared_ep, rank}
        self.spell_repertoire: dict = {}  # fantasy: spell_name → {tier, learned_ep}
        self.blessing_curse_registry: dict = {}  # fantasy: name → {type, source, ep}
        self.filmography_registry: dict = {}  # actor: work_name → {role, year, ep}
        # [V66] 아이템 상태 레지스트리
        self.item_state_registry: dict = {}  # item_name → {description, source, condition, arc_no}
        # [V66] 플롯 서스펜션 추적 (active/in_progress/suspended/resolved)
        self.active_plots: dict = {}  # plot_name → {status, first_arc, last_mention_arc}
        # [V66] NPC 대화 스타일 레지스트리
        self.npc_dialogue_profiles: dict = {}  # npc_name → {speech_level, catchphrase, emotion_baseline}

        # [V66.1] F-1: 작중 시간선 추적 (시간 모순 방지)
        self.in_world_timeline: list = []  # [{arc_no, episode, type, description}]

        # [V66.1] 동행자 추적 (합류/이탈)
        self.current_companions: list = []  # [{name, joined_arc, joined_episode, reason}]

        # [V66.1] 약속/맹세 추적
        self.pending_commitments: list = []  # [{arc_no, episode, parties, description, deadline_hint, status}]

        # [V66.1] 주인공 감정 상태
        self.protagonist_emotion: dict = {"emotion": "평온", "trigger": "", "arc_no": 0}

        # [V63.1] 금융 상태 추적 (투자물)
        self.financial_number_registry: dict[int, dict[str, Any]] = {}
        # arc_no → {exchange_rates: [...], total_assets: [...], leverage: [...], key_transactions: [...]}

        # [V62.5] LLM 클라이언트 (Regex NPC 사망 검증용, Optional)
        self._llm_client = llm_client

        # [Phase 3-5A] NPC 이력 DB (bind_db()로 설정)
        self._db = None
        self._world_state = None  # [TF-35b] bind_world_state() 전 AttributeError 방지

        # [V60.95] PresetRegistry 연동
        self.preset_registry = preset_registry
        self._genre = genre  # [TF-45]
        self._init_tracking_fields()

        # [V64.P3] 서브모듈 초기화
        self._npc = StateTrackerNPC(self)
        self._financial = StateTrackerFinancial(self)
        self._plots = StateTrackerPlots(self)

    def full_extract_from_arcs(self, arcs: list[dict], genre: str = "") -> None:
        """Arc 목록에서 17개 extract 메서드를 순회 호출해 NPC 상태를 구축."""
        for arc in arcs:
            # 핵심 4종: 항상 호출
            self.extract_npc_deaths_from_arc(arc)
            self.extract_skill_acquisitions_from_arc(arc)
            self.extract_npc_info_from_arc(arc, genre=genre)
            self.extract_resolved_plots_from_arc(arc)

            # V66 확장: 실패해도 비차단
            try:
                self.extract_time_markers_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 시간선 추출 실패 (무시): %s", e)
            try:
                self.extract_permanent_injuries_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 신체 변화 추출 실패 (무시): %s", e)
            try:
                self.update_companions_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 동행자 추출 실패 (무시): %s", e)
            try:
                self.extract_commitments_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 약속 추출 실패 (무시): %s", e)
            try:
                self.extract_protagonist_emotion_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 감정 추출 실패 (무시): %s", e)
            try:
                self.extract_item_states_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (major_items): %s", e)
            try:
                self.extract_entity_destructions_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (entity_destructions): %s", e)
            try:
                self.extract_npc_personality_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (npc_personality): %s", e)
            try:
                self.extract_npc_npc_relationships_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (npc_npc_relationships): %s", e)
            try:
                self.extract_npc_dialogue_styles_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (dialogue_profiles): %s", e)
            try:
                self.extract_relationship_changes_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.2] 관계 변화 추출 실패 (무시): %s", e)
            try:
                self.extract_npc_injuries_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.2] NPC 부상 추출 실패 (무시): %s", e)
            try:
                self.extract_npc_movements_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.2] NPC 이동 추출 실패 (무시): %s", e)

            # 투자물: 금융 이벤트 추출
            if genre == "investment":
                self.extract_financial_events_from_arc(arc)

    def _init_tracking_fields(self) -> None:
        """[V60.95] 프리셋 기반 추적 필드 초기화"""
        self.tracking_fields: dict[str, Any] = {}

        if self.preset_registry and PRESET_AVAILABLE:
            # 프리셋에서 필드 가져오기
            active_fields = self.preset_registry.get_active_fields()
            for name, field_def in active_fields.items():
                self.tracking_fields[name] = copy.deepcopy(field_def.default)

            # NPC 필드도 설정 (FieldDefinition → .default 값으로 변환)
            npc_field_defs = self.preset_registry.get_npc_fields()
            self.npc_tracking_fields = {name: copy.deepcopy(fd.default) for name, fd in npc_field_defs.items()}
        else:
            # 기본 필드 (하위 호환성)
            _fallback = {
                "location": "",
                "weapons": [],
                "items": [],
                "injuries": "정상",
                "relationships": {},
            }
            # [TF-45] internal_energy는 무협 전용
            if self._genre in ("wuxia", "무협", ""):
                _fallback["internal_energy"] = 100
            self.tracking_fields = _fallback
            self.npc_tracking_fields = {
                "status": "alive",
                "weapon": "",
                "level": "",
                "death_arc": None,
                "last_arc": 0,
                # [V63] NPC 상세 상태 확장
                "injury": "정상",  # 정상/경상/중상/위독
                "location": "",  # NPC 마지막 위치
                "disposition": "중립",  # 적대/경계/중립/호의/충성
            }

    def get_active_tracking_fields(self) -> list[str]:
        """현재 추적 중인 필드 목록"""
        return list(self.tracking_fields.keys())

    def check_and_expand_genre(self, content: str) -> str | None:
        """
        [V61.3] 콘텐츠에서 새 장르 요소 감지 및 자동 프리셋 확장

        Args:
            content: Arc tactical_doc 또는 원고 텍스트

        Returns:
            새로 활성화된 장르명 또는 None
        """
        if not self.preset_registry or not PRESET_AVAILABLE:
            return None

        # 새 장르 감지
        new_genre = self.preset_registry.detect_new_genre(content)

        if new_genre:
            # 프리셋 활성화
            activated = self.preset_registry.activate_preset(new_genre)
            if activated:
                # 추적 필드 갱신
                self.refresh_tracking_fields()
                logging.info(f"\U0001f3ad [V61.3] 새 장르 감지: {new_genre} → 프리셋 활성화, 추적 필드 확장")
                return new_genre

        return None

    def refresh_tracking_fields(self) -> None:
        """
        [V61.3] 프리셋 변경 후 추적 필드 갱신

        기존 필드는 유지하면서 새 필드만 추가
        """
        if not self.preset_registry or not PRESET_AVAILABLE:
            return

        # 새 필드 가져오기
        active_fields = self.preset_registry.get_active_fields()

        # 기존 필드 유지하면서 새 필드 추가
        for name, field_def in active_fields.items():
            if name not in self.tracking_fields:
                self.tracking_fields[name] = copy.deepcopy(field_def.default)

        # NPC 필드도 갱신 [V61.5] .default 추가 + deepcopy로 mutable 오염 방지
        npc_fields = self.preset_registry.get_npc_fields()
        for name, field_def in npc_fields.items():
            if name not in self.npc_tracking_fields:
                self.npc_tracking_fields[name] = copy.deepcopy(field_def.default)

        # 기존 NPC 레지스트리의 엔트리들에도 새 필드 추가
        for npc_name, npc_data in self.npc_registry.items():
            for name, field_def in npc_fields.items():
                if name not in npc_data:
                    npc_data[name] = copy.deepcopy(field_def.default)

    def get_active_presets(self) -> list[str]:
        """[V61.3] 현재 활성화된 프리셋 목록"""
        if self.preset_registry and PRESET_AVAILABLE:
            return list(self.preset_registry.active_presets)
        return ["common"]

    def create_episode_state(self, ep_num: int, **kwargs) -> EpisodeState:
        """[V60.95] 프리셋 기반 EpisodeState 생성"""
        # 기본 필드
        state = EpisodeState(ep_num=ep_num)

        # 프리셋 기반 동적 필드 채우기
        if self.preset_registry and PRESET_AVAILABLE:
            active_fields = self.preset_registry.get_active_fields()
            for name, field_def in active_fields.items():
                value = kwargs.get(name, field_def.default)
                # 기본 필드면 직접 설정
                if hasattr(state, name) and name != "extra_fields":
                    setattr(state, name, value)
                else:
                    # 동적 필드
                    state.extra_fields[name] = value
        else:
            # 하위 호환: kwargs만 적용
            for key, value in kwargs.items():
                if hasattr(state, key) and key != "extra_fields":
                    setattr(state, key, value)
                else:
                    state.extra_fields[key] = value

        return state

    def create_npc_entry(self, npc_name: str, **kwargs) -> dict[str, Any]:
        """[V60.95] 프리셋 기반 NPC 엔트리 생성"""
        entry = {"name": npc_name}

        if self.preset_registry and PRESET_AVAILABLE:
            npc_fields = self.preset_registry.get_npc_fields()
            for name, field_def in npc_fields.items():
                entry[name] = kwargs.get(name, field_def.default)
        else:
            # 기본 필드
            entry.update(
                {
                    "status": kwargs.get("status", "alive"),
                    "weapon": kwargs.get("weapon", ""),
                    "level": kwargs.get("level", ""),
                    "death_arc": kwargs.get("death_arc"),
                    "last_arc": kwargs.get("last_arc", 0),
                }
            )

        # 추가 kwargs 병합
        for key, value in kwargs.items():
            if key not in entry:
                entry[key] = value

        return entry

    def _parse_internal_energy(self, value) -> int:
        """
        [V49.3 Fix] 내공 수치 파싱 - 한글 서술형 텍스트도 처리

        Args:
            value: 내공 값 (int, str, 또는 서술형 텍스트)

        Returns:
            int: 0-100 범위의 내공 수치
        """
        if isinstance(value, int):
            return max(0, min(100, value))

        if isinstance(value, (float)):
            return max(0, min(100, int(value)))

        if isinstance(value, str):
            # 1. 퍼센트 기호 제거 후 숫자 추출 시도
            clean_value = value.replace("%", "").strip()

            # 2. 순수 숫자인 경우
            if clean_value.isdigit():
                return max(0, min(100, int(clean_value)))

            # 3. 숫자 포함 문자열에서 첫 번째 숫자 추출
            match = re.search(r"(\d+)", clean_value)
            if match:
                return max(0, min(100, int(match.group(1))))

            # 4. 한글 서술형 텍스트 처리 (휴리스틱) - V49.3.1 오탐지 방지
            # 순서 중요: 구체적 패턴 먼저, 일반적 패턴 나중에

            # 매우 낮음 (0-10%)
            very_low_patterns = ["일 할", "일할", "1할", "미만", "영에 가까", "거의 없"]
            if any(k in value for k in very_low_patterns):
                return 5

            # 낮음 (10-30%) - 짧은 서술형에서만 매칭 (오탐지 방지)
            if len(value) <= 10 and re.search(r"(탈진|고갈|소진|바닥|전멸|방전)", value):
                return 10

            # 높음 (80-100%) - 짧은 서술형에서만 매칭
            if len(value) <= 10 and re.search(r"(최대|충만|가득|완전회복|만땅)", value):
                return 100

            # 중간 (40-60%)
            if re.search(r"(절반|반 정도|오 할|오할|5할|50)", value):
                return 50

            # 낮은 편 (20-40%)
            if re.search(r"(삼 할|삼할|3할|30|부족)", value):
                return 30

            # 높은 편 (60-80%)
            if re.search(r"(칠 할|칠할|7할|70|여유)", value):
                return 70

        # 기본값: 중간값 (파싱 실패 시)
        return 50

    def load_arc_design(self, tactical_doc: dict) -> bool:
        """
        Arc 전술 문서에서 상태 정보 추출

        Args:
            tactical_doc: Analyst가 생성한 Arc 전술 문서

        Returns:
            bool: 로드 성공 여부
        """
        try:
            # 상태 제약조건 추출
            state_constraints = tactical_doc.get("state_constraints", {})

            # Arc 시작 상태 설정
            arc_start = state_constraints.get("arc_start_state", {})
            state_constraints.get("arc_end_state", {})

            # 에피소드별 상태 추출 (continuity_checkpoints에서)
            checkpoints = state_constraints.get("continuity_checkpoints", [])

            # 에피소드 분해도에서 상세 정보 추출
            episode_breakdown = tactical_doc.get("episode_breakdown", {})

            # Arc 번호 추출
            arc_no = tactical_doc.get("arc_no", 1)
            _ep_count = int(tactical_doc.get("ep_count", 4) or 4)
            base_ep = tactical_doc.get("ep_start", (arc_no - 1) * _ep_count + 1)

            # 초기 상태 설정 (Arc 시작)
            initial_state = EpisodeState(
                ep_num=base_ep,
                location=arc_start.get("location", ""),
                weapons=arc_start.get("equipment", []).copy() if isinstance(arc_start.get("equipment"), list) else [],
                items=arc_start.get("equipment", []).copy() if isinstance(arc_start.get("equipment"), list) else [],
                injuries=arc_start.get("injuries", "정상"),
                internal_energy=self._parse_internal_energy(arc_start.get("internal_energy", 100)),
            )
            self.states[base_ep] = initial_state

            # 각 에피소드별 상태 파싱
            for i in range(_ep_count):  # Arc당 에피소드 수
                ep_num = base_ep + i
                ep_key = f"ep_{i + 1}"

                if ep_key in episode_breakdown:
                    ep_data = episode_breakdown[ep_key]
                    self._parse_episode_state(ep_num, ep_data, checkpoints)

            # 아이템 획득/소모 추적
            # [BUG-F] protagonist_items 우선 폴백
            items_acquired = state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", [])
            items_consumed = state_constraints.get("items_consumed", [])

            for item in items_acquired:
                item = str(item) if isinstance(item, dict) else item
                if item not in self.acquired_items:
                    # 획득 에피소드 추정 (checkpoint에서)
                    acq_ep = self._find_acquisition_episode(item, checkpoints, base_ep)
                    self.acquired_items[item] = acq_ep

            for item in items_consumed:
                item = str(item) if isinstance(item, dict) else item
                if item not in self.consumed_items:
                    cons_ep = self._find_consumption_episode(item, checkpoints, base_ep)
                    self.consumed_items[item] = cons_ep

            # 상태 전이 생성
            self._build_transitions()

            return True

        except Exception as e:
            logging.warning(f"\u26a0\ufe0f [StateTracker] Arc 설계 로드 실패: {e}")
            return False

    def _parse_episode_state(self, ep_num: int, ep_data: dict, checkpoints: list):
        """에피소드 데이터에서 상태 추출"""
        # 이전 상태 복사
        prev_state = self.states.get(ep_num - 1)
        if prev_state:
            new_state = EpisodeState(
                ep_num=ep_num,
                location=prev_state.location,
                weapons=prev_state.weapons.copy(),
                items=prev_state.items.copy(),
                injuries=prev_state.injuries,
                internal_energy=prev_state.internal_energy,
                relationships=prev_state.relationships.copy(),
            )
        else:
            new_state = EpisodeState(ep_num=ep_num)

        # 에피소드 데이터에서 상태 업데이트
        if isinstance(ep_data, dict):
            # 위치 변경
            if "location" in ep_data:
                new_state.location = ep_data["location"]
            elif "setting" in ep_data:
                new_state.location = ep_data["setting"]

            # 핵심 이벤트에서 상태 변화 추출
            core_events = ep_data.get("core_events", ep_data.get("summary", ""))
            if core_events:
                self._extract_state_from_text(new_state, core_events)

        # checkpoint에서 해당 에피소드 상태 변화 적용
        for checkpoint in checkpoints:
            if (
                f"제{ep_num - (ep_num - 1) // 5 * 5}화:" in checkpoint
                or f"제 {ep_num - (ep_num - 1) // 5 * 5}화:" in checkpoint
            ):
                self._apply_checkpoint(new_state, checkpoint)

        self.states[ep_num] = new_state

    def _extract_state_from_text(self, state: EpisodeState, text: str):
        """텍스트에서 상태 변화 추출"""
        # 부상 패턴
        injury_patterns = {r"중상": "중상", r"부상": "경상", r"회복": "정상", r"치료": "정상", r"위독": "위독"}

        for pattern, injury_state in injury_patterns.items():
            if re.search(pattern, text):
                state.injuries = injury_state

        # 아이템 획득 패턴
        acquisition_patterns = [
            r"([가-힣]+)[을를]?\s*획득",
            r"([가-힣]+)[을를]?\s*얻",
            r"([가-힣]+)[을를]?\s*손에\s*넣",
            r"([가-힣]+검|도|창|궁)[을를]?\s*받",
        ]

        for pattern in acquisition_patterns:
            matches = re.findall(pattern, text)
            for item in matches:
                if len(item) >= 2 and item not in state.items:
                    state.items.append(item)
                    # 무기류 판별
                    if any(weapon_suffix in item for weapon_suffix in ["검", "도", "창", "궁", "장", "봉"]):
                        if item not in state.weapons:
                            state.weapons.append(item)

        # 위치 변경 패턴
        location_patterns = [r"([가-힣]+)[으로에]\s*이동", r"([가-힣]+)[으로에]\s*도착", r"([가-힣]+)[으로에]\s*입장"]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                state.location = match.group(1)
                break

    def _apply_checkpoint(self, state: EpisodeState, checkpoint: str):
        """체크포인트 정보를 상태에 적용"""
        # [상태 변화] 이후 내용 추출
        if "[상태 변화]" in checkpoint:
            change_text = checkpoint.split("[상태 변화]")[-1]
            self._extract_state_from_text(state, change_text)
        else:
            self._extract_state_from_text(state, checkpoint)

    def _find_acquisition_episode(self, item: str, checkpoints: list, base_ep: int) -> int:
        """아이템 획득 에피소드 찾기"""
        for i, checkpoint in enumerate(checkpoints):
            if item in checkpoint and ("획득" in checkpoint or "얻" in checkpoint or "받" in checkpoint):
                # 에피소드 번호 추출
                match = re.search(r"제\s*(\d+)화", checkpoint)
                if match:
                    return base_ep + int(match.group(1)) - 1
        return base_ep  # 기본값: Arc 시작

    def _find_consumption_episode(self, item: str, checkpoints: list, base_ep: int) -> int:
        """아이템 소모 에피소드 찾기"""
        for i, checkpoint in enumerate(checkpoints):
            if item in checkpoint and ("소모" in checkpoint or "사용" in checkpoint or "잃" in checkpoint):
                match = re.search(r"제\s*(\d+)화", checkpoint)
                if match:
                    return base_ep + int(match.group(1)) - 1
        return base_ep + 4  # 기본값: Arc 종료

    def _build_transitions(self) -> None:
        """상태 전이 DAG 구성"""
        self.transitions.clear()

        sorted_eps = sorted(self.states.keys())

        for i in range(len(sorted_eps) - 1):
            from_ep = sorted_eps[i]
            to_ep = sorted_eps[i + 1]

            from_state = self.states[from_ep]
            to_state = self.states[to_ep]

            changes = self._compute_changes(from_state, to_state)

            transition = StateTransition(from_ep=from_ep, to_ep=to_ep, changes=changes)

            self.transitions.append(transition)

    def _compute_changes(self, from_state: EpisodeState, to_state: EpisodeState) -> dict[str, tuple]:
        """두 상태 간의 변화 계산"""
        changes = {}

        if from_state.location != to_state.location:
            changes["location"] = (from_state.location, to_state.location)

        if set(from_state.weapons) != set(to_state.weapons):
            changes["weapons"] = (from_state.weapons.copy(), to_state.weapons.copy())

        if set(from_state.items) != set(to_state.items):
            changes["items"] = (from_state.items.copy(), to_state.items.copy())

        if from_state.injuries != to_state.injuries:
            changes["injuries"] = (from_state.injuries, to_state.injuries)

        if from_state.internal_energy != to_state.internal_energy:
            changes["internal_energy"] = (from_state.internal_energy, to_state.internal_energy)

        return changes

    def validate_timeline(self) -> list[dict]:
        """
        상태 타임라인 검증

        Returns:
            검증 이슈 목록 [{type, severity, description, episodes}]
        """
        issues = []

        # 1. 아이템 중복 획득 검사
        issues.extend(self._check_duplicate_acquisition())

        # 2. 부상 상태 일관성 검사
        issues.extend(self._check_injury_consistency())

        # 3. 위치 순간이동 검사
        issues.extend(self._check_location_teleport())

        # 4. 내공 급변 검사
        issues.extend(self._check_energy_spike())

        # 5. 아이템 사용 전 미획득 검사
        issues.extend(self._check_item_usage_before_acquisition())

        # 6. 무기 상태 일관성 검사
        issues.extend(self._check_weapon_continuity())

        return issues

    def _check_duplicate_acquisition(self) -> list[dict]:
        """아이템 중복 획득 검사"""
        issues = []
        item_first_acquired = {}

        for transition in self.transitions:
            if "items" in transition.changes:
                before, after = transition.changes["items"]
                new_items = set(after) - set(before)

                for item in new_items:
                    if item in item_first_acquired:
                        issues.append(
                            {
                                "type": "duplicate_acquisition",
                                "severity": "critical",
                                "description": f"'{item}' 중복 획득: 제{item_first_acquired[item]}화에서 이미 획득함",
                                "episodes": [item_first_acquired[item], transition.to_ep],
                            }
                        )
                    else:
                        item_first_acquired[item] = transition.to_ep

        return issues

    def _check_injury_consistency(self) -> list[dict]:
        """부상 상태 일관성 검사"""
        issues = []

        injury_severity = {"정상": 0, "경상": 1, "중상": 2, "위독": 3}

        for transition in self.transitions:
            if "injuries" in transition.changes:
                before, after = transition.changes["injuries"]
                before_sev = injury_severity.get(before, 0)
                after_sev = injury_severity.get(after, 0)

                # 급격한 회복 (중상 → 정상) 경고
                if before_sev - after_sev >= 2:
                    issues.append(
                        {
                            "type": "rapid_recovery",
                            "severity": "major",
                            "description": f"부상 급회복: {before} → {after} (치료 과정 필요)",
                            "episodes": [transition.from_ep, transition.to_ep],
                        }
                    )

        return issues

    def _check_location_teleport(self) -> list[dict]:
        """위치 순간이동 검사"""
        issues = []

        # 멀리 떨어진 위치 쌍 정의 (간단한 휴리스틱)
        distant_pairs = [("산", "바다"), ("동굴", "궁전"), ("사막", "설산"), ("지하", "하늘"), ("섬", "대륙")]

        for transition in self.transitions:
            if "location" in transition.changes:
                before, after = transition.changes["location"]

                for loc1, loc2 in distant_pairs:
                    if (loc1 in before and loc2 in after) or (loc2 in before and loc1 in after):
                        issues.append(
                            {
                                "type": "location_teleport",
                                "severity": "minor",
                                "description": f"위치 급변: {before} → {after} (이동 과정 묘사 권장)",
                                "episodes": [transition.from_ep, transition.to_ep],
                            }
                        )
                        break

        return issues

    def _check_energy_spike(self) -> list[dict]:
        """내공 급변 검사"""
        issues = []

        for transition in self.transitions:
            if "internal_energy" in transition.changes:
                before, after = transition.changes["internal_energy"]
                diff = after - before

                # 30% 이상 급격한 변화
                if abs(diff) >= 30:
                    change_type = "급증" if diff > 0 else "급감"
                    issues.append(
                        {
                            "type": "energy_spike",
                            "severity": "minor" if abs(diff) < 50 else "major",
                            "description": f"내공 {change_type}: {before}% → {after}% (설명 필요)",
                            "episodes": [transition.from_ep, transition.to_ep],
                        }
                    )

        return issues

    def _check_item_usage_before_acquisition(self) -> list[dict]:
        """아이템 사용 전 미획득 검사"""
        issues = []

        for item, acq_ep in self.acquired_items.items():
            if item in self.consumed_items:
                cons_ep = self.consumed_items[item]
                if cons_ep < acq_ep:
                    issues.append(
                        {
                            "type": "use_before_acquire",
                            "severity": "critical",
                            "description": f"'{item}' 획득 전 사용: 제{cons_ep}화에서 사용, 제{acq_ep}화에서 획득",
                            "episodes": [cons_ep, acq_ep],
                        }
                    )

        return issues

    def _check_weapon_continuity(self) -> list[dict]:
        """무기 상태 일관성 검사"""
        issues = []

        for transition in self.transitions:
            if "weapons" in transition.changes:
                before, after = transition.changes["weapons"]
                lost_weapons = set(before) - set(after)

                # 무기가 설명 없이 사라진 경우
                for weapon in lost_weapons:
                    issues.append(
                        {
                            "type": "weapon_disappeared",
                            "severity": "major",
                            "description": f"'{weapon}' 설명 없이 소실 (분실/파괴 설명 필요)",
                            "episodes": [transition.from_ep, transition.to_ep],
                        }
                    )

        return issues

    def get_state_at_episode(self, ep_num: int) -> EpisodeState | None:
        """특정 에피소드의 상태 반환"""
        return self.states.get(ep_num)

    def get_timeline_summary(self) -> str:
        """타임라인 요약 문자열 생성"""
        lines = ["\U0001f4ca [StateTracker] 상태 타임라인 요약:\n"]

        for ep_num in sorted(self.states.keys()):
            state = self.states[ep_num]
            lines.append(f"  제{ep_num}화:")
            lines.append(f"    - 위치: {state.location or '미지정'}")
            lines.append(f"    - 무기: {', '.join(state.weapons) if state.weapons else '없음'}")
            lines.append(f"    - 부상: {state.injuries}")
            lines.append(f"    - 내공: {state.internal_energy}%")
            lines.append("")

        return "\n".join(lines)

    def get_dag_visualization(self) -> str:
        """DAG 시각화 문자열 (텍스트 기반)"""
        lines = ["\U0001f4c8 [StateTracker] 상태 전이 DAG:\n"]

        for transition in self.transitions:
            arrow = "──▶"
            if transition.issues:
                arrow = "━━▶ \u26a0\ufe0f"

            change_summary = []
            for field, (before, after) in transition.changes.items():
                if field == "weapons":
                    added = set(after) - set(before)
                    removed = set(before) - set(after)
                    if added:
                        change_summary.append(f"+{', '.join(added)}")
                    if removed:
                        change_summary.append(f"-{', '.join(removed)}")
                elif field == "injuries":
                    change_summary.append(f"부상:{before}→{after}")
                elif field == "location":
                    change_summary.append(f"위치:{after}")

            change_text = ", ".join(change_summary) if change_summary else "변화 없음"
            lines.append(f"  EP{transition.from_ep} {arrow} EP{transition.to_ep}: [{change_text}]")

        return "\n".join(lines)

    def generate_constraint_prompt(self) -> str:
        """Architect/Writer용 상태 제약 프롬프트 생성"""
        lines = ["\U0001f512 [상태 제약 조건]\n"]

        # 현재 소지 아이템
        if self.states:
            latest_ep = max(self.states.keys())
            latest_state = self.states[latest_ep]

            lines.append(f"현재 상태 (제{latest_ep}화 종료 시점):")
            lines.append(f"  - 위치: {latest_state.location or '미지정'}")
            lines.append(f"  - 소지 무기: {', '.join(latest_state.weapons) if latest_state.weapons else '없음'}")
            lines.append(f"  - 소지 아이템: {', '.join(latest_state.items) if latest_state.items else '없음'}")
            lines.append(f"  - 부상 상태: {latest_state.injuries}")
            lines.append(f"  - 내공: {latest_state.internal_energy}%")
            lines.append("")

        # 획득 이력
        if self.acquired_items:
            lines.append("이미 획득한 아이템 (중복 획득 금지):")
            for item, ep in self.acquired_items.items():
                lines.append(f"  - {item} (제{ep}화)")
            lines.append("")

        # 소모 이력
        if self.consumed_items:
            lines.append("이미 소모한 아이템 (재사용 금지):")
            for item, ep in self.consumed_items.items():
                lines.append(f"  - {item} (제{ep}화)")

        return "\n".join(lines)

    def merge_from_previous_arcs(self, prev_tracker: "StateTracker"):
        """이전 Arc의 상태를 현재 tracker에 병합"""
        # 아이템 이력 병합
        for item, ep in prev_tracker.acquired_items.items():
            if item not in self.acquired_items:
                self.acquired_items[item] = ep

        for item, ep in prev_tracker.consumed_items.items():
            if item not in self.consumed_items:
                self.consumed_items[item] = ep

        # 전역 아이템 목록 병합
        self.global_items.update(prev_tracker.global_items)

    # ═══════════════════════════════════════════════════════════════
    # [V64.P3] NPC 서브모듈 위임 스텁
    # ═══════════════════════════════════════════════════════════════

    # [V61.7.1] 장르별 능력 습득 로그 표시 (서브모듈에서 참조)
    _SKILL_LOG_LABEL = StateTrackerNPC._SKILL_LOG_LABEL

    def register_npc_death(self, npc_name: str, death_arc: int, death_context: str = ""):
        return self._npc.register_npc_death(npc_name, death_arc, death_context)

    def register_npc_info(
        self,
        npc_name: str,
        arc_no: int,
        weapon: str = None,
        level: str = None,
        personality_traits: str = None,
        primary_motivation: str = None,
        position: str = None,
    ):
        return self._npc.register_npc_info(
            npc_name,
            arc_no,
            weapon,
            level,
            personality_traits=personality_traits,
            primary_motivation=primary_motivation,
            position=position,
        )

    def check_npc_changes(self, content: str, arc_no: int) -> list[dict]:
        return self._npc.check_npc_changes(content, arc_no)

    def extract_npc_info_from_arc(self, arc: dict, genre: str = "") -> list[dict]:
        return self._npc.extract_npc_info_from_arc(arc, genre=genre)

    def _is_standalone_name(self, name: str, text: str) -> bool:
        return self._npc._is_standalone_name(name, text)

    def check_dead_npc_appearance(self, content: str, arc_no: int) -> list[dict]:
        return self._npc.check_dead_npc_appearance(content, arc_no)

    def register_protagonist_skill(self, skill_name: str, arc_no: int):
        return self._npc.register_protagonist_skill(skill_name, arc_no)

    def check_unlearned_skill_usage(self, content: str, arc_no: int) -> list[dict]:
        return self._npc.check_unlearned_skill_usage(content, arc_no)

    def get_entity_registry(self) -> dict:
        return self._npc.get_entity_registry()

    def merge_npc_registry(self, other: "StateTracker"):
        return self._npc.merge_npc_registry(other)

    def extract_npc_deaths_from_arc(self, arc: dict) -> list[str]:
        return self._npc.extract_npc_deaths_from_arc(arc)

    def extract_skill_acquisitions_from_arc(self, arc: dict) -> list[str]:
        return self._npc.extract_skill_acquisitions_from_arc(arc)

    def extract_relationship_changes_from_arc(self, arc: dict) -> list[dict]:
        return self._npc.extract_relationship_changes_from_arc(arc)

    def extract_npc_injuries_from_arc(self, arc: dict) -> list[dict]:
        return self._npc.extract_npc_injuries_from_arc(arc)

    def extract_npc_movements_from_arc(self, arc: dict) -> list[dict]:
        return self._npc.extract_npc_movements_from_arc(arc)

    def check_dead_npc_in_blueprint(self, blueprint: dict, ep_num: int, arc_no: int = 0) -> list[dict]:
        return self._npc.check_dead_npc_in_blueprint(blueprint, ep_num, arc_no)

    def check_dead_npc_in_manuscript(self, manuscript: str, ep_num: int, arc_no: int = 0) -> list[dict]:
        return self._npc.check_dead_npc_in_manuscript(manuscript, ep_num, arc_no)

    def get_dead_npc_summary(self) -> str:
        return self._npc.get_dead_npc_summary()

    def cleanup_npc_registry_with_llm(self, arc_no: int) -> list[str]:
        """[V69] 5 Arc마다 NPC 레지스트리 일반명사 오탐 LLM 정리 위임."""
        return self._npc.cleanup_npc_registry_with_llm(arc_no)

    # ═══════════════════════════════════════════════════════════════
    # [Phase 3-5A] NPC 이력 DB API
    # ═══════════════════════════════════════════════════════════════

    def bind_db(self, db_manager) -> None:
        """[Phase 3-5A] DB 매니저 바인딩. 호출측(main_a 등)에서 설정."""
        self._db = db_manager

    def bind_world_state(self, world_state_manager) -> None:
        """[TF-36] WorldState 동기화용 바인딩."""
        self._world_state = world_state_manager

    def get_npc_change_history(self, npc_name: str, limit: int = 50) -> list[dict]:
        """[Phase 3-5A] NPC 변경 이력 조회 (최신순)"""
        if self._db and hasattr(self._db, "get_npc_history"):
            return self._db.get_npc_history(npc_name, limit)
        return []

    def get_npc_latest_fields(self, npc_name: str) -> dict:
        """[Phase 3-5A] NPC 필드별 최신 값"""
        if self._db and hasattr(self._db, "get_npc_latest_fields"):
            return self._db.get_npc_latest_fields(npc_name)
        return {}

    # ═══════════════════════════════════════════════════════════════
    # [V64.P3] Financial 서브모듈 위임 스텁
    # ═══════════════════════════════════════════════════════════════

    def extract_financial_events_from_arc(self, arc: dict) -> dict:
        return self._financial.extract_financial_events_from_arc(arc)

    def get_financial_state_summary(self) -> str:
        return self._financial.get_financial_state_summary()

    def export_financial_registry(self) -> dict:
        return self._financial.export_financial_registry()

    def import_financial_registry(self, data: dict):
        return self._financial.import_financial_registry(data)

    # ═══════════════════════════════════════════════════════════════
    # [V64.P3] Plots/Entity 서브모듈 위임 스텁
    # ═══════════════════════════════════════════════════════════════

    def extract_resolved_plots_from_arc(self, arc: dict) -> list[dict]:
        return self._plots.extract_resolved_plots_from_arc(arc)

    def get_resolved_plots_summary(self, max_items: int = 30) -> str:
        return self._plots.get_resolved_plots_summary(max_items=max_items)

    def register_entity_name(self, name: str, entity_type: str, arc_no: int):
        return self._plots.register_entity_name(name, entity_type, arc_no)

    def load_entities_from_entity_registry(self, entity_registry: dict, arc_no: int):
        return self._plots.load_entities_from_entity_registry(entity_registry, arc_no)

    def check_entity_name_consistency(self, content: str, arc_no: int = 0) -> list[dict]:
        return self._plots.check_entity_name_consistency(content, arc_no)

    # [V66] 조직/장소 파괴 추적 위임
    def extract_entity_destructions_from_arc(self, arc: dict) -> list[dict]:
        return self._plots.extract_entity_destructions_from_arc(arc)

    def get_entity_destruction_summary(self) -> str:
        return self._plots.get_entity_destruction_summary()

    def check_destroyed_entity_in_manuscript(self, content: str) -> list[dict]:
        return self._plots.check_destroyed_entity_in_manuscript(content)

    # [V66] NPC 성격/동기 위임
    def extract_npc_personality_from_arc(self, arc: dict) -> list[dict]:
        return self._npc.extract_npc_personality_from_arc(arc)

    def get_npc_personality_summary(self) -> str:
        return self._npc.get_npc_personality_summary()

    # [V66] NPC-NPC 관계 위임
    def extract_npc_npc_relationships_from_arc(self, arc: dict) -> list[dict]:
        return self._npc.extract_npc_npc_relationships_from_arc(arc)

    def get_npc_npc_relationship_summary(self) -> str:
        return self._npc.get_npc_npc_relationship_summary()

    # [V66] 아이템 상태 위임
    def extract_item_states_from_arc(self, arc: dict) -> list[dict]:
        return self._plots.extract_item_states_from_arc(arc)

    def get_item_state_summary(self) -> str:
        return self._plots.get_item_state_summary()

    # [V66] 플롯 서스펜션 위임
    def update_plot_mentions_from_arc(self, arc: dict) -> list[dict]:
        return self._plots.update_plot_mentions_from_arc(arc)

    def check_suspended_plots(self, current_arc_no: int, threshold: int = 3) -> list[dict]:
        return self._plots.check_suspended_plots(current_arc_no, threshold)

    def get_plot_suspension_summary(self, current_arc_no: int) -> str:
        return self._plots.get_plot_suspension_summary(current_arc_no)

    # [V66] NPC 대화 스타일 위임
    def extract_npc_dialogue_styles_from_arc(self, arc: dict) -> list[dict]:
        return self._npc.extract_npc_dialogue_styles_from_arc(arc)

    def get_npc_dialogue_style_summary(self) -> str:
        return self._npc.get_npc_dialogue_style_summary()

    def register_npc_npc_relationship(self, npc1: str, npc2: str, relation: str, arc_no: int):
        return self._npc.register_npc_npc_relationship(npc1, npc2, relation, arc_no)

    def register_npc_dialogue_style(
        self, npc_name: str, speech_level: str = "", catchphrase: str = "", emotion_baseline: str = "", arc_no: int = 0
    ):
        return self._npc.register_npc_dialogue_style(npc_name, speech_level, catchphrase, emotion_baseline, arc_no)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-1: 시간선 추적 위임 (Plots 서브모듈)
    # ═══════════════════════════════════════════════════════════════

    def register_time_marker(self, arc_no: int, episode: int, marker_type: str, description: str):
        return self._plots.register_time_marker(arc_no, episode, marker_type, description)

    def extract_time_markers_from_arc(self, arc_data: dict) -> list[dict]:
        return self._plots.extract_time_markers_from_arc(arc_data)

    def get_time_timeline_summary(self) -> str:
        return self._plots.get_time_timeline_summary()

    def check_time_consistency(self, manuscript: str, current_timeline: list = None) -> list[dict]:
        return self._plots.check_time_consistency(manuscript, current_timeline)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-8: NPC 영구 부상 위임 (NPC 서브모듈)
    # ═══════════════════════════════════════════════════════════════

    def register_permanent_injury(self, name: str, injury_type: str, description: str, arc_no: int):
        return self._npc.register_permanent_injury(name, injury_type, description, arc_no)

    def extract_permanent_injuries_from_arc(self, arc_data: dict) -> list[dict]:
        return self._npc.extract_permanent_injuries_from_arc(arc_data)

    def get_permanent_injury_summary(self) -> str:
        return self._npc.get_permanent_injury_summary()

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-10: NPC 사망 등록 취소 위임 (NPC 서브모듈)
    # ═══════════════════════════════════════════════════════════════

    def revive_npc(self, name: str, reason: str) -> bool:
        return self._npc.revive_npc(name, reason)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] 동행자(Companion) 추적 위임 (NPC 서브모듈)
    # ═══════════════════════════════════════════════════════════════

    def update_companions_from_arc(self, arc_data: dict) -> list[dict]:
        return self._npc.update_companions_from_arc(arc_data)

    def get_companion_summary(self) -> str:
        return self._npc.get_companion_summary()

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] 약속/맹세(Commitment) 추적 위임 (Plots 서브모듈)
    # ═══════════════════════════════════════════════════════════════

    def register_commitment(
        self, arc_no: int, episode: int, parties: list[str], description: str, deadline_hint: str = ""
    ):
        return self._plots.register_commitment(arc_no, episode, parties, description, deadline_hint)

    def extract_commitments_from_arc(self, arc_data: dict) -> list[dict]:
        return self._plots.extract_commitments_from_arc(arc_data)

    def resolve_commitment(self, description: str) -> bool:
        return self._plots.resolve_commitment(description)

    def get_commitment_summary(self) -> str:
        return self._plots.get_commitment_summary()

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] 주인공 감정 상태 추적 위임 (NPC 서브모듈)
    # ═══════════════════════════════════════════════════════════════

    def update_protagonist_emotion(self, arc_no: int, episode: int, emotion: str, trigger: str):
        return self._npc.update_protagonist_emotion(arc_no, episode, emotion, trigger)

    def extract_protagonist_emotion_from_arc(self, arc_data: dict):
        return self._npc.extract_protagonist_emotion_from_arc(arc_data)

    def get_protagonist_emotion_summary(self) -> str:
        return self._npc.get_protagonist_emotion_summary()

    # [V66.2] D-1,2,3: mandatory_context 주입용 summary 위임 스텁
    def get_relationship_changes_summary(self) -> str:
        return self._npc.get_relationship_changes_summary()

    def get_npc_injury_summary(self) -> str:
        return self._npc.get_npc_injury_summary()

    def get_npc_movement_summary(self) -> str:
        return self._npc.get_npc_movement_summary()

    # [V66.2] C-2: 주인공 습득 무공/스킬 요약 위임
    def get_protagonist_skills_summary(self) -> str:
        return self._npc.get_protagonist_skills_summary()

    # ═══════════════════════════════════════════════════════════════
    # [S4-I2] 통합 요약 메서드
    # ═══════════════════════════════════════════════════════════════

    def get_all_summaries(self, *, arc_no: int = 0, genre: str = "") -> dict[str, str]:
        """[S4-I2] 16종 get_XXX_summary() 호출 결과를 dict로 통합 반환.

        빈 문자열인 항목은 포함하되 None은 제외한다.
        stage4_context_builder 등에서 일괄 수집에 사용.

        Args:
            arc_no: 현재 Arc 번호 (plot_suspension_summary에 필요).
            genre: 장르 코드 (``'investment'``이면 financial 요약 포함).

        Returns:
            ``{ summary_name: summary_text }`` 딕셔너리.
        """
        summaries: dict[str, str] = {}

        # 16종 기본 요약
        _methods: list[tuple[str, str]] = [
            ("entity_destruction", "get_entity_destruction_summary"),
            ("resolved_plots", "get_resolved_plots_summary"),
            ("npc_personality", "get_npc_personality_summary"),
            ("npc_npc_relationship", "get_npc_npc_relationship_summary"),
            ("permanent_injury", "get_permanent_injury_summary"),
            ("time_timeline", "get_time_timeline_summary"),
            ("companion", "get_companion_summary"),
            ("commitment", "get_commitment_summary"),
            ("protagonist_emotion", "get_protagonist_emotion_summary"),
            ("item_state", "get_item_state_summary"),
            ("npc_dialogue_style", "get_npc_dialogue_style_summary"),
            ("relationship_changes", "get_relationship_changes_summary"),
            ("npc_injury", "get_npc_injury_summary"),
            ("npc_movement", "get_npc_movement_summary"),
            ("protagonist_skills", "get_protagonist_skills_summary"),
            ("dead_npc", "get_dead_npc_summary"),
        ]

        for key, method_name in _methods:
            try:
                val = getattr(self, method_name)()
                if val is not None:
                    summaries[key] = val
            except Exception as exc:
                logging.warning("[S4-I2] %s() 실패 (무시): %s", method_name, exc)

        # arc_no 필요 메서드
        try:
            val = self.get_plot_suspension_summary(arc_no)
            if val is not None:
                summaries["plot_suspension"] = val
        except Exception as exc:
            logging.warning("[S4-I2] get_plot_suspension_summary() 실패 (무시): %s", exc)

        # 투자물 전용
        if genre == "investment":
            try:
                val = self.get_financial_state_summary()
                if val is not None:
                    summaries["financial_state"] = val
            except Exception as exc:
                logging.warning("[S4-I2] get_financial_state_summary() 실패 (무시): %s", exc)

        return summaries

    # ═══════════════════════════════════════════════════════════════
    # [V66] 멀티-Arc 요약
    # ═══════════════════════════════════════════════════════════════

    def generate_arc_summary(self, arc_no: int, arc: dict = None) -> dict:
        """[V66] Arc 완료 시 자동 요약 생성 -- NPC 관계/세계 상태/플롯 현황.
        [V66.2] F-2: arc dict가 주어지면 state_changes에서 NPC를 우선 추출하여
                     registry 오염에 의존하지 않는 정확한 스냅샷 생성.
        """
        summary = {
            "arc_no": arc_no,
            "npc_status": {},
            "world_changes": [],
            "resolved_plots": [],
            "active_plots": [],
            "destroyed_entities": [],
        }
        # NPC 상태 스냅샷 (최근 10명)
        recent_npcs = {}
        seen_names: set = set()

        # [V66.2] F-2: arc['state_changes']에서 NPC 이름 우선 추출
        if arc and isinstance(arc, dict):
            sc = arc.get("state_changes", {})
            if isinstance(sc, dict):
                # state_changes 내 NPC 이름 수집
                sc_npc_names = []
                for entry in sc.get("relationship_changes", []):
                    if isinstance(entry, dict) and entry.get("npc"):
                        sc_npc_names.append(entry["npc"])
                for entry in sc.get("npc_deaths", []):
                    if isinstance(entry, dict) and entry.get("name"):
                        sc_npc_names.append(entry["name"])
                for entry in sc.get("companion_changes", []):
                    if isinstance(entry, dict) and entry.get("name"):
                        sc_npc_names.append(entry["name"])
                for entry in sc.get("npc_personality_changes", []):
                    if isinstance(entry, dict) and entry.get("name"):
                        sc_npc_names.append(entry["name"])

                # 중복 제거 후 registry 정보로 보강
                for npc_name in dict.fromkeys(sc_npc_names):  # 순서 유지 중복 제거
                    if len(recent_npcs) >= 10:
                        break
                    reg_info = self.npc_registry.get(npc_name, {})
                    recent_npcs[npc_name] = {
                        "status": reg_info.get("status", "alive"),
                        "relation": reg_info.get("relation_to_protag", ""),
                        "personality": reg_info.get("personality_traits", ""),
                        "location": reg_info.get("location", ""),
                    }
                    seen_names.add(npc_name)

        # 기존 npc_registry 루프 (state_changes에서 이미 추가된 이름은 스킵)
        for name, info in self.npc_registry.items():
            if len(recent_npcs) >= 10:
                break
            if name in seen_names:
                continue
            if info.get("last_arc", 0) >= max(1, arc_no - 2):
                recent_npcs[name] = {
                    "status": info.get("status", "alive"),
                    "relation": info.get("relation_to_protag", ""),
                    "personality": info.get("personality_traits", ""),
                    "location": info.get("location", ""),
                }
        summary["npc_status"] = recent_npcs

        # 완결 플롯 (현재 arc)
        for rp in self.resolved_plots:
            if rp.get("arc_no") == arc_no:
                summary["resolved_plots"].append(rp.get("plot", ""))

        # 파괴된 엔티티
        for ed in self.entity_destructions:
            if ed.get("arc_no") == arc_no:
                summary["destroyed_entities"].append(f"{ed.get('name', '')} ({ed.get('type', '')})")

        # 활성 플롯 (있으면)
        if hasattr(self, "active_plots") and self.active_plots:
            for plot_name, info in self.active_plots.items():
                if info.get("status") != "resolved":
                    summary["active_plots"].append(plot_name)

        # NPC-NPC 관계 스냅샷
        npc_relations = []
        for info in self.npc_npc_relationships.values():
            npc_relations.append(f"{info.get('npc1', '')}↔{info.get('npc2', '')}: {info.get('relation', '')}")
        if npc_relations:
            summary["npc_relations"] = npc_relations[:10]

        return summary

    def format_arc_summary_for_prompt(self, arc_summaries: list) -> str:
        """[V66] Arc 요약 목록 -> mandatory_context 주입용 문자열."""
        if not arc_summaries:
            return ""
        lines = ["[V66] 이전 Arc 요약 (서사 연속성 유지 필수):"]
        for s in arc_summaries[-3:]:  # 직전 3개 Arc만
            arc_no = s.get("arc_no", "?")
            lines.append(f"\n  === Arc {arc_no} ===")

            npcs = s.get("npc_status", {})
            if npcs:
                for name, info in list(npcs.items())[:5]:
                    status = info.get("status", "alive")
                    rel = info.get("relation", "")
                    lines.append(f"  NPC {name}: {status}" + (f", 관계={rel}" if rel else ""))

            resolved = s.get("resolved_plots", [])
            if resolved:
                lines.append(f"  완결: {', '.join(resolved[:3])}")

            active = s.get("active_plots", [])
            if active:
                lines.append(f"  진행중: {', '.join(active[:3])}")

            destroyed = s.get("destroyed_entities", [])
            if destroyed:
                lines.append(f"  파괴: {', '.join(destroyed[:3])}")

            npc_rels = s.get("npc_relations", [])
            if npc_rels:
                lines.append(f"  관계: {'; '.join(npc_rels[:3])}")

        result = "\n".join(lines)
        # 3,000자 상한
        if len(result) > 3000:
            result = result[:2997] + "..."
        return result

    # ═══════════════════════════════════════════════════════════════
    # [V64.P3] 통합 추출 메서드 (여러 서브모듈 조합)
    # ═══════════════════════════════════════════════════════════════

    def extract_all_state_changes(self, arc: dict) -> dict:
        """
        [V61] Arc에서 모든 state_changes 추출 (통합 메서드)
        [V63] npc_injuries, npc_movements 추가
        [V63.1] financial_events 추가
        [V66] entity_destructions, npc_personality_changes, npc_npc_relationships 추가
        [V66.1] time_markers, permanent_injuries, companion_changes, commitments, protagonist_emotion 추가

        Returns:
            {
                "npc_deaths": [...],
                "skill_acquisitions": [...],
                "relationship_changes": [...],
                "major_items": [...],
                "resolved_plots": [...],
                "npc_injuries": [...],
                "npc_movements": [...],
                "financial_events": {...},
                "entity_destructions": [...],
                "npc_personality_changes": [...],
                "npc_npc_relationships": [...],
                "time_markers": [...],
                "permanent_injuries": [...],
                "companion_changes": [...],
                "commitments": [...],
                "protagonist_emotion": {...}
            }
        """
        return {
            "npc_deaths": self.extract_npc_deaths_from_arc(arc),
            "skill_acquisitions": self.extract_skill_acquisitions_from_arc(arc),
            "relationship_changes": self.extract_relationship_changes_from_arc(arc),
            "major_items": (arc.get("state_changes") or {}).get("major_items", []),  # [V70] None 방어
            "resolved_plots": self.extract_resolved_plots_from_arc(arc),
            "npc_injuries": self.extract_npc_injuries_from_arc(arc),
            "npc_movements": self.extract_npc_movements_from_arc(arc),
            "financial_events": self.extract_financial_events_from_arc(arc),
            "entity_destructions": self.extract_entity_destructions_from_arc(arc),
            "npc_personality_changes": self.extract_npc_personality_from_arc(arc),
            "npc_npc_relationships": self.extract_npc_npc_relationships_from_arc(arc),
            "time_markers": self.extract_time_markers_from_arc(arc),
            "permanent_injuries": self.extract_permanent_injuries_from_arc(arc),
            "companion_changes": self.update_companions_from_arc(arc),
            "commitments": self.extract_commitments_from_arc(arc),
            "protagonist_emotion": self.extract_protagonist_emotion_from_arc(arc) or {},
        }

    def _populate_genre_registries_from_arc(self, arc: dict):
        """[V66] Arc에서 장르별 레지스트리 데이터 추출 및 저장."""
        state_changes = arc.get("state_changes", {})
        if not isinstance(state_changes, dict):
            return
        arc_no = arc.get("arc_no", 0)

        # Hunter: 던전 클리어 기록
        for item in state_changes.get("major_items", []):
            if isinstance(item, dict) and "던전" in str(item.get("name", "")):
                self.dungeon_clear_registry[item["name"]] = {"cleared_ep": item.get("episode", 0), "arc_no": arc_no}

        # Hunter: 스킬 쿨다운 (skill_acquisitions에서 추출)
        for skill in state_changes.get("skill_acquisitions", []):
            if isinstance(skill, dict) and skill.get("name"):
                self.skill_cooldown_registry[skill["name"]] = {"learned_ep": skill.get("episode", 0), "arc_no": arc_no}

        # Fantasy: 주문 레퍼토리
        for skill in state_changes.get("skill_acquisitions", []):
            if isinstance(skill, dict) and skill.get("name"):
                self.spell_repertoire[skill["name"]] = {
                    "tier": skill.get("tier", ""),
                    "learned_ep": skill.get("episode", 0),
                }


def create_tracker_from_arcs(arcs_data: list[dict]) -> StateTracker:
    """
    여러 Arc 데이터로부터 통합 StateTracker 생성

    Args:
        arcs_data: Arc 전술 문서 목록 (순서대로)

    Returns:
        통합된 StateTracker
    """
    master_tracker = StateTracker()

    for arc_doc in arcs_data:
        arc_tracker = StateTracker()
        if arc_tracker.load_arc_design(arc_doc):
            master_tracker.merge_from_previous_arcs(arc_tracker)
            master_tracker.merge_npc_registry(arc_tracker)  # [V60.94] NPC 레지스트리 병합
            # 상태도 병합
            master_tracker.states.update(arc_tracker.states)
            master_tracker.transitions.extend(arc_tracker.transitions)

    # [Sweep4] cross-arc boundary transitions 재구축
    # extend로 모은 within-arc transitions만으로는 arc 경계(예: ep5→ep6) 전이가 누락됨
    # _build_transitions()가 states 전체를 정렬하여 연속 EP 간 전이를 재생성
    if master_tracker.states:
        master_tracker._build_transitions()

    return master_tracker
