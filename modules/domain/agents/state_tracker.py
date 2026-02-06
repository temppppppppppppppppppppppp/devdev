"""
[V49.3] State Tracker Agent - 상태 추적 및 DAG 타임라인 검증
[V60.95] PresetRegistry 연동 - 동적 필드 기반 상태 추적

Arc 내 각 회차의 상태를 자동 추적하고
DAG(Directed Acyclic Graph) 형태로 타임라인을 구성하여 검증합니다.
"""

import json
import re
import copy
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict

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
    weapons: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    injuries: str = "정상"  # 정상/경상/중상/위독
    internal_energy: int = 100  # 0-100%
    relationships: Dict[str, str] = field(default_factory=dict)  # NPC -> 상태

    # [V60.95] 동적 확장 필드 (프리셋 기반)
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        base = {
            "ep_num": self.ep_num,
            "location": self.location,
            "weapons": self.weapons.copy(),
            "items": self.items.copy(),
            "injuries": self.injuries,
            "internal_energy": self.internal_energy,
            "relationships": self.relationships.copy()
        }
        # 동적 필드 병합
        base.update(self.extra_fields)
        return base

    def get(self, key: str, default=None):
        """필드 조회 (기본 + 동적)"""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra_fields.get(key, default)

    def set(self, key: str, value):
        """필드 설정 (기본이면 속성, 아니면 동적)"""
        if hasattr(self, key) and key != 'extra_fields':
            setattr(self, key, value)
        else:
            self.extra_fields[key] = value


@dataclass
class StateTransition:
    """상태 전이 정보"""
    from_ep: int
    to_ep: int
    changes: Dict[str, Tuple[any, any]]  # field -> (before, after)
    justification: str = ""
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)


class StateTracker:
    """
    [V49.3] Arc 상태 추적기
    [V60.95] PresetRegistry 연동 - 동적 필드 + 고밀도 추적

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

    def __init__(self, preset_registry=None):
        self.states: Dict[int, EpisodeState] = {}  # ep_num -> state
        self.transitions: List[StateTransition] = []
        self.global_items: Set[str] = set()  # 전체 소지 아이템 추적
        self.acquired_items: Dict[str, int] = {}  # item -> 획득 에피소드
        self.consumed_items: Dict[str, int] = {}  # item -> 소모 에피소드

        # [V60.94] NPC 상태 추적 (생사, 무장, 수준)
        self.npc_registry: Dict[str, Dict] = {}  # name -> {프리셋 기반 필드들}
        # [V60.94] 주인공 무공 목록 추적
        self.protagonist_skills: Set[str] = set()  # 습득한 무공 목록
        self.skill_acquisitions: Dict[str, int] = {}  # skill -> 습득 Arc

        # [V60.95] PresetRegistry 연동
        self.preset_registry = preset_registry
        self._init_tracking_fields()

    def _init_tracking_fields(self):
        """[V60.95] 프리셋 기반 추적 필드 초기화"""
        self.tracking_fields: Dict[str, Any] = {}

        if self.preset_registry and PRESET_AVAILABLE:
            # 프리셋에서 필드 가져오기
            active_fields = self.preset_registry.get_active_fields()
            for name, field_def in active_fields.items():
                self.tracking_fields[name] = copy.deepcopy(field_def.default)

            # NPC 필드도 설정 (FieldDefinition → .default 값으로 변환)
            npc_field_defs = self.preset_registry.get_npc_fields()
            self.npc_tracking_fields = {
                name: copy.deepcopy(fd.default) for name, fd in npc_field_defs.items()
            }
        else:
            # 기본 필드 (하위 호환성)
            self.tracking_fields = {
                "location": "",
                "weapons": [],
                "items": [],
                "injuries": "정상",
                "internal_energy": 100,
                "relationships": {},
            }
            self.npc_tracking_fields = {
                "status": "alive",
                "weapon": "",
                "level": "",
                "death_arc": None,
                "last_arc": 0,
            }

    def get_active_tracking_fields(self) -> List[str]:
        """현재 추적 중인 필드 목록"""
        return list(self.tracking_fields.keys())

    def check_and_expand_genre(self, content: str) -> Optional[str]:
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
                print(f"      🎭 [V61.3] 새 장르 감지: {new_genre} → 프리셋 활성화, 추적 필드 확장")
                return new_genre

        return None

    def refresh_tracking_fields(self):
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

    def get_active_presets(self) -> List[str]:
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
                if hasattr(state, name) and name != 'extra_fields':
                    setattr(state, name, value)
                else:
                    # 동적 필드
                    state.extra_fields[name] = value
        else:
            # 하위 호환: kwargs만 적용
            for key, value in kwargs.items():
                if hasattr(state, key) and key != 'extra_fields':
                    setattr(state, key, value)
                else:
                    state.extra_fields[key] = value

        return state

    def create_npc_entry(self, npc_name: str, **kwargs) -> Dict[str, Any]:
        """[V60.95] 프리셋 기반 NPC 엔트리 생성"""
        entry = {"name": npc_name}

        if self.preset_registry and PRESET_AVAILABLE:
            npc_fields = self.preset_registry.get_npc_fields()
            for name, field_def in npc_fields.items():
                entry[name] = kwargs.get(name, field_def.default)
        else:
            # 기본 필드
            entry.update({
                "status": kwargs.get("status", "alive"),
                "weapon": kwargs.get("weapon", ""),
                "level": kwargs.get("level", ""),
                "death_arc": kwargs.get("death_arc"),
                "last_arc": kwargs.get("last_arc", 0),
            })

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
            clean_value = value.replace('%', '').strip()

            # 2. 순수 숫자인 경우
            if clean_value.isdigit():
                return max(0, min(100, int(clean_value)))

            # 3. 숫자 포함 문자열에서 첫 번째 숫자 추출
            match = re.search(r'(\d+)', clean_value)
            if match:
                return max(0, min(100, int(match.group(1))))

            # 4. 한글 서술형 텍스트 처리 (휴리스틱) - V49.3.1 오탐지 방지
            # 순서 중요: 구체적 패턴 먼저, 일반적 패턴 나중에

            # 매우 낮음 (0-10%)
            very_low_patterns = ['일 할', '일할', '1할', '미만', '영에 가까', '거의 없']
            if any(k in value for k in very_low_patterns):
                return 5

            # 낮음 (10-30%) - 짧은 서술형에서만 매칭 (오탐지 방지)
            if len(value) <= 10 and re.search(r'(탈진|고갈|소진|바닥|전멸|방전)', value):
                return 10

            # 높음 (80-100%) - 짧은 서술형에서만 매칭
            if len(value) <= 10 and re.search(r'(최대|충만|가득|완전회복|만땅)', value):
                return 100

            # 중간 (40-60%)
            if re.search(r'(절반|반 정도|오 할|오할|5할|50)', value):
                return 50

            # 낮은 편 (20-40%)
            if re.search(r'(삼 할|삼할|3할|30|부족)', value):
                return 30

            # 높은 편 (60-80%)
            if re.search(r'(칠 할|칠할|7할|70|여유)', value):
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
            state_constraints = tactical_doc.get('state_constraints', {})

            # Arc 시작 상태 설정
            arc_start = state_constraints.get('arc_start_state', {})
            arc_end = state_constraints.get('arc_end_state', {})

            # 에피소드별 상태 추출 (continuity_checkpoints에서)
            checkpoints = state_constraints.get('continuity_checkpoints', [])

            # 에피소드 분해도에서 상세 정보 추출
            episode_breakdown = tactical_doc.get('episode_breakdown', {})

            # Arc 번호 추출
            arc_no = tactical_doc.get('arc_no', 1)
            base_ep = (arc_no - 1) * 5 + 1  # Arc 1 = EP 1-5, Arc 2 = EP 6-10 ...

            # 초기 상태 설정 (Arc 시작)
            initial_state = EpisodeState(
                ep_num=base_ep,
                location=arc_start.get('location', ''),
                weapons=arc_start.get('equipment', []).copy() if isinstance(arc_start.get('equipment'), list) else [],
                items=arc_start.get('equipment', []).copy() if isinstance(arc_start.get('equipment'), list) else [],
                injuries=arc_start.get('injuries', '정상'),
                internal_energy=self._parse_internal_energy(arc_start.get('internal_energy', 100))
            )
            self.states[base_ep] = initial_state

            # 각 에피소드별 상태 파싱
            for i in range(5):  # Arc당 5개 에피소드
                ep_num = base_ep + i
                ep_key = f"ep_{i+1}"

                if ep_key in episode_breakdown:
                    ep_data = episode_breakdown[ep_key]
                    self._parse_episode_state(ep_num, ep_data, checkpoints)

            # 아이템 획득/소모 추적
            items_acquired = state_constraints.get('items_acquired', [])
            items_consumed = state_constraints.get('items_consumed', [])

            for item in items_acquired:
                if item not in self.acquired_items:
                    # 획득 에피소드 추정 (checkpoint에서)
                    acq_ep = self._find_acquisition_episode(item, checkpoints, base_ep)
                    self.acquired_items[item] = acq_ep

            for item in items_consumed:
                if item not in self.consumed_items:
                    cons_ep = self._find_consumption_episode(item, checkpoints, base_ep)
                    self.consumed_items[item] = cons_ep

            # 상태 전이 생성
            self._build_transitions()

            return True

        except Exception as e:
            print(f"      ⚠️ [StateTracker] Arc 설계 로드 실패: {e}")
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
                relationships=prev_state.relationships.copy()
            )
        else:
            new_state = EpisodeState(ep_num=ep_num)

        # 에피소드 데이터에서 상태 업데이트
        if isinstance(ep_data, dict):
            # 위치 변경
            if 'location' in ep_data:
                new_state.location = ep_data['location']
            elif 'setting' in ep_data:
                new_state.location = ep_data['setting']

            # 핵심 이벤트에서 상태 변화 추출
            core_events = ep_data.get('core_events', ep_data.get('summary', ''))
            if core_events:
                self._extract_state_from_text(new_state, core_events)

        # checkpoint에서 해당 에피소드 상태 변화 적용
        for checkpoint in checkpoints:
            if f"제{ep_num - (ep_num - 1) // 5 * 5}화:" in checkpoint or f"제 {ep_num - (ep_num - 1) // 5 * 5}화:" in checkpoint:
                self._apply_checkpoint(new_state, checkpoint)

        self.states[ep_num] = new_state

    def _extract_state_from_text(self, state: EpisodeState, text: str):
        """텍스트에서 상태 변화 추출"""
        # 부상 패턴
        injury_patterns = {
            r'중상': '중상',
            r'부상': '경상',
            r'회복': '정상',
            r'치료': '정상',
            r'위독': '위독'
        }

        for pattern, injury_state in injury_patterns.items():
            if re.search(pattern, text):
                state.injuries = injury_state

        # 아이템 획득 패턴
        acquisition_patterns = [
            r'([가-힣]+)[을를]?\s*획득',
            r'([가-힣]+)[을를]?\s*얻',
            r'([가-힣]+)[을를]?\s*손에\s*넣',
            r'([가-힣]+검|도|창|궁)[을를]?\s*받'
        ]

        for pattern in acquisition_patterns:
            matches = re.findall(pattern, text)
            for item in matches:
                if len(item) >= 2 and item not in state.items:
                    state.items.append(item)
                    # 무기류 판별
                    if any(weapon_suffix in item for weapon_suffix in ['검', '도', '창', '궁', '장', '봉']):
                        if item not in state.weapons:
                            state.weapons.append(item)

        # 위치 변경 패턴
        location_patterns = [
            r'([가-힣]+)[으로에]\s*이동',
            r'([가-힣]+)[으로에]\s*도착',
            r'([가-힣]+)[으로에]\s*입장'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                state.location = match.group(1)
                break

    def _apply_checkpoint(self, state: EpisodeState, checkpoint: str):
        """체크포인트 정보를 상태에 적용"""
        # [상태 변화] 이후 내용 추출
        if '[상태 변화]' in checkpoint:
            change_text = checkpoint.split('[상태 변화]')[-1]
            self._extract_state_from_text(state, change_text)
        else:
            self._extract_state_from_text(state, checkpoint)

    def _find_acquisition_episode(self, item: str, checkpoints: list, base_ep: int) -> int:
        """아이템 획득 에피소드 찾기"""
        for i, checkpoint in enumerate(checkpoints):
            if item in checkpoint and ('획득' in checkpoint or '얻' in checkpoint or '받' in checkpoint):
                # 에피소드 번호 추출
                match = re.search(r'제\s*(\d+)화', checkpoint)
                if match:
                    return base_ep + int(match.group(1)) - 1
        return base_ep  # 기본값: Arc 시작

    def _find_consumption_episode(self, item: str, checkpoints: list, base_ep: int) -> int:
        """아이템 소모 에피소드 찾기"""
        for i, checkpoint in enumerate(checkpoints):
            if item in checkpoint and ('소모' in checkpoint or '사용' in checkpoint or '잃' in checkpoint):
                match = re.search(r'제\s*(\d+)화', checkpoint)
                if match:
                    return base_ep + int(match.group(1)) - 1
        return base_ep + 4  # 기본값: Arc 종료

    def _build_transitions(self):
        """상태 전이 DAG 구성"""
        self.transitions.clear()

        sorted_eps = sorted(self.states.keys())

        for i in range(len(sorted_eps) - 1):
            from_ep = sorted_eps[i]
            to_ep = sorted_eps[i + 1]

            from_state = self.states[from_ep]
            to_state = self.states[to_ep]

            changes = self._compute_changes(from_state, to_state)

            transition = StateTransition(
                from_ep=from_ep,
                to_ep=to_ep,
                changes=changes
            )

            self.transitions.append(transition)

    def _compute_changes(self, from_state: EpisodeState, to_state: EpisodeState) -> Dict[str, Tuple]:
        """두 상태 간의 변화 계산"""
        changes = {}

        if from_state.location != to_state.location:
            changes['location'] = (from_state.location, to_state.location)

        if set(from_state.weapons) != set(to_state.weapons):
            changes['weapons'] = (from_state.weapons.copy(), to_state.weapons.copy())

        if set(from_state.items) != set(to_state.items):
            changes['items'] = (from_state.items.copy(), to_state.items.copy())

        if from_state.injuries != to_state.injuries:
            changes['injuries'] = (from_state.injuries, to_state.injuries)

        if from_state.internal_energy != to_state.internal_energy:
            changes['internal_energy'] = (from_state.internal_energy, to_state.internal_energy)

        return changes

    def validate_timeline(self) -> List[dict]:
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

    def _check_duplicate_acquisition(self) -> List[dict]:
        """아이템 중복 획득 검사"""
        issues = []
        item_first_acquired = {}

        for transition in self.transitions:
            if 'items' in transition.changes:
                before, after = transition.changes['items']
                new_items = set(after) - set(before)

                for item in new_items:
                    if item in item_first_acquired:
                        issues.append({
                            "type": "duplicate_acquisition",
                            "severity": "critical",
                            "description": f"'{item}' 중복 획득: 제{item_first_acquired[item]}화에서 이미 획득함",
                            "episodes": [item_first_acquired[item], transition.to_ep]
                        })
                    else:
                        item_first_acquired[item] = transition.to_ep

        return issues

    def _check_injury_consistency(self) -> List[dict]:
        """부상 상태 일관성 검사"""
        issues = []

        injury_severity = {'정상': 0, '경상': 1, '중상': 2, '위독': 3}

        for transition in self.transitions:
            if 'injuries' in transition.changes:
                before, after = transition.changes['injuries']
                before_sev = injury_severity.get(before, 0)
                after_sev = injury_severity.get(after, 0)

                # 급격한 회복 (중상 → 정상) 경고
                if before_sev - after_sev >= 2:
                    issues.append({
                        "type": "rapid_recovery",
                        "severity": "major",
                        "description": f"부상 급회복: {before} → {after} (치료 과정 필요)",
                        "episodes": [transition.from_ep, transition.to_ep]
                    })

        return issues

    def _check_location_teleport(self) -> List[dict]:
        """위치 순간이동 검사"""
        issues = []

        # 멀리 떨어진 위치 쌍 정의 (간단한 휴리스틱)
        distant_pairs = [
            ('산', '바다'), ('동굴', '궁전'), ('사막', '설산'),
            ('지하', '하늘'), ('섬', '대륙')
        ]

        for transition in self.transitions:
            if 'location' in transition.changes:
                before, after = transition.changes['location']

                for loc1, loc2 in distant_pairs:
                    if (loc1 in before and loc2 in after) or (loc2 in before and loc1 in after):
                        issues.append({
                            "type": "location_teleport",
                            "severity": "minor",
                            "description": f"위치 급변: {before} → {after} (이동 과정 묘사 권장)",
                            "episodes": [transition.from_ep, transition.to_ep]
                        })
                        break

        return issues

    def _check_energy_spike(self) -> List[dict]:
        """내공 급변 검사"""
        issues = []

        for transition in self.transitions:
            if 'internal_energy' in transition.changes:
                before, after = transition.changes['internal_energy']
                diff = after - before

                # 30% 이상 급격한 변화
                if abs(diff) >= 30:
                    change_type = "급증" if diff > 0 else "급감"
                    issues.append({
                        "type": "energy_spike",
                        "severity": "minor" if abs(diff) < 50 else "major",
                        "description": f"내공 {change_type}: {before}% → {after}% (설명 필요)",
                        "episodes": [transition.from_ep, transition.to_ep]
                    })

        return issues

    def _check_item_usage_before_acquisition(self) -> List[dict]:
        """아이템 사용 전 미획득 검사"""
        issues = []

        for item, acq_ep in self.acquired_items.items():
            if item in self.consumed_items:
                cons_ep = self.consumed_items[item]
                if cons_ep < acq_ep:
                    issues.append({
                        "type": "use_before_acquire",
                        "severity": "critical",
                        "description": f"'{item}' 획득 전 사용: 제{cons_ep}화에서 사용, 제{acq_ep}화에서 획득",
                        "episodes": [cons_ep, acq_ep]
                    })

        return issues

    def _check_weapon_continuity(self) -> List[dict]:
        """무기 상태 일관성 검사"""
        issues = []

        for transition in self.transitions:
            if 'weapons' in transition.changes:
                before, after = transition.changes['weapons']
                lost_weapons = set(before) - set(after)

                # 무기가 설명 없이 사라진 경우
                for weapon in lost_weapons:
                    issues.append({
                        "type": "weapon_disappeared",
                        "severity": "major",
                        "description": f"'{weapon}' 설명 없이 소실 (분실/파괴 설명 필요)",
                        "episodes": [transition.from_ep, transition.to_ep]
                    })

        return issues

    def get_state_at_episode(self, ep_num: int) -> Optional[EpisodeState]:
        """특정 에피소드의 상태 반환"""
        return self.states.get(ep_num)

    def get_timeline_summary(self) -> str:
        """타임라인 요약 문자열 생성"""
        lines = ["📊 [StateTracker] 상태 타임라인 요약:\n"]

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
        lines = ["📈 [StateTracker] 상태 전이 DAG:\n"]

        for transition in self.transitions:
            arrow = "──▶"
            if transition.issues:
                arrow = "━━▶ ⚠️"

            change_summary = []
            for field, (before, after) in transition.changes.items():
                if field == 'weapons':
                    added = set(after) - set(before)
                    removed = set(before) - set(after)
                    if added:
                        change_summary.append(f"+{', '.join(added)}")
                    if removed:
                        change_summary.append(f"-{', '.join(removed)}")
                elif field == 'injuries':
                    change_summary.append(f"부상:{before}→{after}")
                elif field == 'location':
                    change_summary.append(f"위치:{after}")

            change_text = ", ".join(change_summary) if change_summary else "변화 없음"
            lines.append(f"  EP{transition.from_ep} {arrow} EP{transition.to_ep}: [{change_text}]")

        return "\n".join(lines)

    def generate_constraint_prompt(self) -> str:
        """Architect/Writer용 상태 제약 프롬프트 생성"""
        lines = ["🔒 [상태 제약 조건]\n"]

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

    def merge_from_previous_arcs(self, prev_tracker: 'StateTracker'):
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
    # [V60.94] NPC 상태 추적 메서드
    # ═══════════════════════════════════════════════════════════════

    def register_npc_death(self, npc_name: str, death_arc: int, death_context: str = ""):
        """
        [V60.94] NPC 사망 등록

        Args:
            npc_name: NPC 이름
            death_arc: 사망한 Arc 번호
            death_context: 사망 맥락 (선택)
        """
        if npc_name not in self.npc_registry:
            self.npc_registry[npc_name] = {}

        self.npc_registry[npc_name].update({
            "status": "dead",
            "death_arc": death_arc,
            "death_context": death_context
        })
        print(f"      💀 [V60.94] NPC 사망 등록: {npc_name} (Arc {death_arc})")

    def register_npc_info(self, npc_name: str, arc_no: int, weapon: str = None, level: str = None):
        """
        [V60.94] NPC 정보 등록/업데이트

        Args:
            npc_name: NPC 이름
            arc_no: Arc 번호
            weapon: 무장 (선택)
            level: 수준/경지 (선택)
        """
        if npc_name not in self.npc_registry:
            self.npc_registry[npc_name] = {"status": "alive"}

        npc = self.npc_registry[npc_name]
        npc["last_arc"] = arc_no

        if weapon:
            npc["weapon"] = weapon
        if level:
            npc["level"] = level

    def check_npc_changes(self, content: str, arc_no: int) -> List[dict]:
        """
        [V60.95] NPC 무장/수준 변경 검사 - WARNING 대상 (정당화 사유 필요)

        Args:
            content: 검사할 텍스트 (tactical_doc 등)
            arc_no: 현재 Arc 번호

        Returns:
            변경 목록 [{npc_name, change_type, old_value, new_value, severity}]
        """
        warnings = []

        # NPC 무장 패턴
        weapon_patterns = [
            r'([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))[을를으로]?\s*(?:들|휘두르|뽑)',
            r'([가-힣]{2,10})[의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))',
        ]

        # NPC 수준 패턴
        level_patterns = [
            r'([가-힣]{2,10})[이가은는]\s*(절대고수|화경|현경|초절정|일류|이류|삼류)',
            r'(절대고수|화경|현경|초절정|일류)[인의]\s*([가-힣]{2,10})',
        ]

        # 무장 변경 검사
        for pattern in weapon_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                npc_name = match[0] if len(match) > 0 else None
                weapon = match[1] if len(match) > 1 else None

                if npc_name and weapon and npc_name in self.npc_registry:
                    npc = self.npc_registry[npc_name]
                    old_weapon = npc.get("weapon")

                    if old_weapon and old_weapon != weapon:
                        warnings.append({
                            "npc_name": npc_name,
                            "change_type": "weapon",
                            "old_value": old_weapon,
                            "new_value": weapon,
                            "arc_no": arc_no,
                            "severity": "WARNING",
                            "reason": f"Arc {npc.get('last_arc', '?')}에서 '{old_weapon}' 사용 → Arc {arc_no}에서 '{weapon}' 사용"
                        })

        # 수준 변경 검사
        for pattern in level_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 패턴에 따라 순서가 다를 수 있음
                if match[0] in ['절대고수', '화경', '현경', '초절정', '일류', '이류', '삼류']:
                    level, npc_name = match[0], match[1]
                else:
                    npc_name, level = match[0], match[1]

                if npc_name and level and npc_name in self.npc_registry:
                    npc = self.npc_registry[npc_name]
                    old_level = npc.get("level")

                    if old_level and old_level != level:
                        warnings.append({
                            "npc_name": npc_name,
                            "change_type": "level",
                            "old_value": old_level,
                            "new_value": level,
                            "arc_no": arc_no,
                            "severity": "WARNING",
                            "reason": f"Arc {npc.get('last_arc', '?')}에서 '{old_level}' → Arc {arc_no}에서 '{level}'"
                        })

        return warnings

    def extract_npc_info_from_arc(self, arc: dict) -> List[dict]:
        """
        [V60.95] Arc의 tactical_doc에서 NPC 정보(무장, 수준) 추출 및 등록

        Args:
            arc: Arc 데이터

        Returns:
            추출된 NPC 정보 목록
        """
        arc_no = arc.get("arc_no", 0)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        extracted = []

        # NPC 무장 패턴
        weapon_patterns = [
            r'([가-힣]{2,10})[이가은는의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))',
        ]

        # NPC 수준 패턴
        level_patterns = [
            r'([가-힣]{2,10})[이가은는]\s*(절대고수|화경|현경|초절정|일류|이류|삼류)',
            r'(절대고수|화경|현경|초절정|일류)[인의]\s*([가-힣]{2,10})',
        ]

        # 제외할 일반 명사
        exclude_words = ['주인공', '적', '상대', '자신', '그', '그녀', '적수', '상대방']

        for pattern in weapon_patterns:
            matches = re.findall(pattern, tactical)
            for match in matches:
                npc_name, weapon = match[0], match[1]
                if npc_name not in exclude_words and len(npc_name) >= 2:
                    self.register_npc_info(npc_name, arc_no, weapon=weapon)
                    extracted.append({"name": npc_name, "weapon": weapon, "arc": arc_no})

        for pattern in level_patterns:
            matches = re.findall(pattern, tactical)
            for match in matches:
                if match[0] in ['절대고수', '화경', '현경', '초절정', '일류', '이류', '삼류']:
                    level, npc_name = match[0], match[1]
                else:
                    npc_name, level = match[0], match[1]

                if npc_name not in exclude_words and len(npc_name) >= 2:
                    self.register_npc_info(npc_name, arc_no, level=level)
                    extracted.append({"name": npc_name, "level": level, "arc": arc_no})

        return extracted

    def check_dead_npc_appearance(self, content: str, arc_no: int) -> List[dict]:
        """
        [V60.94] 죽은 NPC 등장 검사 - REJECT 대상

        Args:
            content: 검사할 텍스트 (tactical_doc 등)
            arc_no: 현재 Arc 번호

        Returns:
            위반 목록 [{npc_name, death_arc, severity}]
        """
        violations = []

        for npc_name, info in self.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)

                # [V60.97] 타임라인 비교: 사망 이전 Arc에서는 검사 스킵
                if arc_no < death_arc:
                    continue  # 아직 죽지 않은 시점

                # 죽은 NPC 이름이 콘텐츠에 등장하는지 검사
                if npc_name in content:
                    # 회상/과거 언급은 허용 (패턴 검사)
                    flashback_patterns = [
                        f"{npc_name}의 죽음",
                        f"{npc_name}을 떠올",
                        f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}",
                        f"죽은 {npc_name}",
                        f"{npc_name}의 유언",
                        f"{npc_name}의 무덤",
                        f"{npc_name}의 원혼",
                        f"{npc_name}의 유품",
                    ]

                    is_flashback = any(pattern in content for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장으로 간주 (대화, 행동 등)
                        action_patterns = [
                            f"{npc_name}이 ",
                            f"{npc_name}가 ",
                            f"{npc_name}은 ",
                            f"{npc_name}는 ",
                            f'"{npc_name}',  # 대사
                            f"{npc_name}의 검",
                            f"{npc_name}의 공격",
                        ]

                        if any(pattern in content for pattern in action_patterns):
                            violations.append({
                                "npc_name": npc_name,
                                "death_arc": death_arc,
                                "current_arc": arc_no,
                                "severity": "CRITICAL",
                                "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 Arc {arc_no}에서 다시 등장"
                            })

        return violations

    def register_protagonist_skill(self, skill_name: str, arc_no: int):
        """
        [V60.94] 주인공 무공 습득 등록

        Args:
            skill_name: 무공 이름
            arc_no: 습득 Arc 번호
        """
        if skill_name not in self.protagonist_skills:
            self.protagonist_skills.add(skill_name)
            self.skill_acquisitions[skill_name] = arc_no
            print(f"      🥋 [V60.94] 무공 습득 등록: {skill_name} (Arc {arc_no})")

    def check_unlearned_skill_usage(self, content: str, arc_no: int) -> List[dict]:
        """
        [V60.94] 미습득 무공 사용 검사 - 기록용 (REJECT 안 함)

        Args:
            content: 검사할 텍스트
            arc_no: 현재 Arc 번호

        Returns:
            의심 목록 [{skill_name, context}] - 정보 제공용
        """
        suspicious = []

        # 무공 사용 패턴
        skill_patterns = [
            r'([가-힣]{2,10}(?:장|권|법|공|결|식|초))[을를]?\s*(?:시전|펼치|사용|발동)',
            r'([가-힣]{2,10}(?:심법|내공|기공))[으로]?\s*(?:운기|조식)',
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, content)
            for skill in matches:
                if skill and len(skill) >= 2:
                    # 등록된 무공인지 확인
                    if skill not in self.protagonist_skills:
                        # 새로운 무공일 수도 있으므로 INFO 레벨
                        suspicious.append({
                            "skill_name": skill,
                            "arc_no": arc_no,
                            "severity": "INFO",
                            "note": "습득 기록 없음 - 새 무공이거나 숨겨둔 패일 수 있음"
                        })

        return suspicious

    def get_entity_registry(self) -> dict:
        """
        [V60.94] Director/Validator용 Entity Registry 반환

        Returns:
            {
                "dead_npcs": [{name, death_arc}],
                "npc_info": [{name, weapon, level, status}],
                "protagonist_skills": [skill_names],
                "protagonist_items": [item_names]
            }
        """
        dead_npcs = []
        npc_info = []

        for name, info in self.npc_registry.items():
            if info.get("status") == "dead":
                dead_npcs.append({
                    "name": name,
                    "death_arc": info.get("death_arc", 0)
                })
            npc_info.append({
                "name": name,
                "weapon": info.get("weapon", ""),
                "level": info.get("level", ""),
                "status": info.get("status", "alive"),
                "last_arc": info.get("last_arc", 0)
            })

        # 최신 상태의 아이템 목록
        protagonist_items = []
        if self.states:
            latest_ep = max(self.states.keys())
            latest_state = self.states[latest_ep]
            protagonist_items = latest_state.items + latest_state.weapons

        return {
            "dead_npcs": dead_npcs,
            "npc_info": npc_info,
            "protagonist_skills": list(self.protagonist_skills),
            "protagonist_items": protagonist_items
        }

    def merge_npc_registry(self, other: 'StateTracker'):
        """[V60.94] 다른 StateTracker의 NPC 레지스트리 병합"""
        for name, info in other.npc_registry.items():
            if name not in self.npc_registry:
                self.npc_registry[name] = info.copy()
            else:
                # 기존 정보 업데이트 (사망 정보 우선)
                if info.get("status") == "dead":
                    self.npc_registry[name] = info.copy()
                else:
                    self.npc_registry[name].update(info)

        # 무공 목록 병합
        self.protagonist_skills.update(other.protagonist_skills)
        for skill, arc in other.skill_acquisitions.items():
            if skill not in self.skill_acquisitions:
                self.skill_acquisitions[skill] = arc

    def extract_npc_deaths_from_arc(self, arc: dict) -> List[str]:
        """
        [V61] Arc에서 NPC 사망 추출 및 등록
        우선순위: state_changes 필드 > Regex 폴백

        Args:
            arc: Arc 데이터 (state_changes 또는 tactical_doc 포함)

        Returns:
            사망한 NPC 이름 목록
        """
        arc_no = arc.get("arc_no", 0)
        dead_npcs = []

        # [V61] 1순위: state_changes 필드 직접 읽기 (정확도 ~98%)
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            npc_deaths = state_changes.get("npc_deaths", [])
            if isinstance(npc_deaths, list) and npc_deaths:
                for death in npc_deaths:
                    if isinstance(death, dict):
                        npc_name = death.get("name", "")
                        episode = death.get("episode", arc_no)
                        cause = death.get("cause", "state_changes에서 추출")
                        if npc_name and len(npc_name) >= 2:
                            self.register_npc_death(npc_name, arc_no, f"Arc {arc_no} Ep {episode}: {cause}")
                            dead_npcs.append(npc_name)
                    elif isinstance(death, str) and len(death) >= 2:
                        # 단순 문자열 형태도 지원
                        self.register_npc_death(death, arc_no, f"Arc {arc_no} state_changes에서 추출")
                        dead_npcs.append(death)
                if dead_npcs:
                    return list(set(dead_npcs))

        # [V61] 2순위: Regex 폴백 (하위 호환 + 보조)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        death_patterns = [
            r'([가-힣]{2,10})[이가을를]\s*(?:죽이|처단|살해|베어|제거|처형|사살)',
            r'([가-힣]{2,10})[이가은는]\s*(?:죽|사망|전사|명을\s*다|숨을\s*거두|운명)',
            r'([가-힣]{2,10})[의]\s*(?:죽음|최후|사망|전사)',
            r'([가-힣]{2,10})[을를]\s*(?:끝장|마무리|처리)',
        ]

        exclude_words = ['주인공', '적', '상대', '자신', '목숨', '생명', '원수', '원한', '일격', '공격', '반격']
        for pattern in death_patterns:
            matches = re.findall(pattern, tactical)
            for npc_name in matches:
                if npc_name and len(npc_name) >= 2 and npc_name not in exclude_words:
                    self.register_npc_death(npc_name, arc_no, f"Arc {arc_no} tactical_doc Regex 추출")
                    dead_npcs.append(npc_name)

        return list(set(dead_npcs))

    def extract_skill_acquisitions_from_arc(self, arc: dict) -> List[str]:
        """
        [V61] Arc에서 무공/기술 습득 추출 및 등록
        우선순위: state_changes 필드 > Regex 폴백

        Args:
            arc: Arc 데이터

        Returns:
            습득한 무공 이름 목록
        """
        arc_no = arc.get("arc_no", 0)
        learned_skills = []

        # [V61] 1순위: state_changes 필드 직접 읽기 (정확도 ~98%)
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            skill_acq = state_changes.get("skill_acquisitions", [])
            if isinstance(skill_acq, list) and skill_acq:
                for skill in skill_acq:
                    if isinstance(skill, dict):
                        skill_name = skill.get("name", "")
                        episode = skill.get("episode", arc_no)
                        source = skill.get("source", "state_changes에서 추출")
                        if skill_name and len(skill_name) >= 2:
                            self.register_protagonist_skill(skill_name, arc_no)
                            learned_skills.append(skill_name)
                    elif isinstance(skill, str) and len(skill) >= 2:
                        self.register_protagonist_skill(skill, arc_no)
                        learned_skills.append(skill)
                if learned_skills:
                    return list(set(learned_skills))

        # [V61] 2순위: Regex 폴백 (하위 호환 + 보조)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        learn_patterns = [
            r'([가-힣]{2,10}(?:장|권|법|공|결|식|초|심법))[을를]?\s*(?:습득|익히|배우|터득|깨우치|전수받)',
            r'([가-힣]{2,10}(?:장|권|법|공|결|식|초|심법))[의]?\s*(?:오의|진수|비전)[을를]?\s*(?:깨달|얻)',
        ]

        for pattern in learn_patterns:
            matches = re.findall(pattern, tactical)
            for skill_name in matches:
                if skill_name and len(skill_name) >= 2:
                    self.register_protagonist_skill(skill_name, arc_no)
                    learned_skills.append(skill_name)

        return list(set(learned_skills))

    def extract_relationship_changes_from_arc(self, arc: dict) -> List[Dict]:
        """
        [V61] Arc에서 관계 변화 추출 (state_changes 필드 전용)

        Args:
            arc: Arc 데이터

        Returns:
            관계 변화 목록 [{"npc": ..., "from": ..., "to": ..., "episode": ...}]
        """
        arc_no = arc.get("arc_no", 0)
        changes = []

        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            rel_changes = state_changes.get("relationship_changes", [])
            if isinstance(rel_changes, list):
                for change in rel_changes:
                    if isinstance(change, dict):
                        npc = change.get("npc", "")
                        from_rel = change.get("from", "")
                        to_rel = change.get("to", "")
                        episode = change.get("episode", arc_no)
                        if npc and from_rel and to_rel:
                            changes.append({
                                "npc": npc,
                                "from": from_rel,
                                "to": to_rel,
                                "episode": episode,
                                "arc_no": arc_no
                            })
                            # NPC registry에도 반영
                            if npc in self.npc_registry:
                                self.npc_registry[npc]["relation_to_protag"] = to_rel
                                self.npc_registry[npc]["last_arc"] = arc_no

        return changes

    def extract_all_state_changes(self, arc: dict) -> Dict:
        """
        [V61] Arc에서 모든 state_changes 추출 (통합 메서드)

        Returns:
            {
                "npc_deaths": [...],
                "skill_acquisitions": [...],
                "relationship_changes": [...],
                "major_items": [...]
            }
        """
        return {
            "npc_deaths": self.extract_npc_deaths_from_arc(arc),
            "skill_acquisitions": self.extract_skill_acquisitions_from_arc(arc),
            "relationship_changes": self.extract_relationship_changes_from_arc(arc),
            "major_items": arc.get("state_changes", {}).get("major_items", [])
        }

    # ═══════════════════════════════════════════════════════════════
    # [V60.96] Stage 3/4 확장 메서드 (Blueprint/Manuscript 검증)
    # ═══════════════════════════════════════════════════════════════

    def check_dead_npc_in_blueprint(self, blueprint: dict, ep_num: int, arc_no: int = 0) -> List[dict]:
        """
        [V60.96] Blueprint에서 죽은 NPC 등장 검사 - REJECT 대상

        Args:
            blueprint: Blueprint 데이터 (integrated_scenario, scene_breakdown 포함)
            ep_num: 에피소드 번호
            arc_no: [V60.97] Arc 번호 (타임라인 비교용, 0이면 blueprint에서 추출 시도)

        Returns:
            위반 목록 [{npc_name, death_arc, severity, context}]
        """
        violations = []

        # [V60.97] arc_no 추출 (파라미터 우선, 없으면 blueprint에서)
        if arc_no <= 0:
            arc_no = blueprint.get("arc_no", 0)
        if arc_no <= 0:
            # 에피소드 번호로 추정 (보수적: 5화 단위)
            arc_no = (ep_num - 1) // 5 + 1

        # integrated_scenario 추출
        content = blueprint.get("integrated_scenario", "")
        if not isinstance(content, str):
            content = str(content) if content else ""

        # scene_breakdown 추가
        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, dict):
            for scene in scenes.values():
                if isinstance(scene, dict):
                    content += "\n" + scene.get("content", "")
                    content += "\n" + scene.get("summary", "")
                elif isinstance(scene, str):
                    content += "\n" + scene

        # 죽은 NPC 검사
        for npc_name, info in self.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)

                # [V60.97] 타임라인 비교: 사망 이전 Arc에서는 검사 스킵
                if arc_no < death_arc:
                    continue  # 아직 죽지 않은 시점

                if npc_name in content:
                    # 회상/언급 패턴은 허용
                    flashback_patterns = [
                        f"{npc_name}의 죽음", f"{npc_name}을 떠올", f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}", f"죽은 {npc_name}", f"{npc_name}의 유언",
                        f"{npc_name}의 무덤", f"{npc_name}의 원혼", f"{npc_name}의 유품",
                        f"{npc_name}을 추모", f"{npc_name}의 복수"
                    ]
                    is_flashback = any(pattern in content for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장 패턴 검사
                        action_patterns = [
                            f"{npc_name}이 ", f"{npc_name}가 ", f"{npc_name}은 ", f"{npc_name}는 ",
                            f'"{npc_name}', f"{npc_name}와 ", f"{npc_name}과 ",
                            f"{npc_name}의 검", f"{npc_name}의 공격", f"{npc_name}에게"
                        ]
                        if any(pattern in content for pattern in action_patterns):
                            violations.append({
                                "npc_name": npc_name,
                                "death_arc": death_arc,
                                "current_ep": ep_num,
                                "current_arc": arc_no,
                                "severity": "CRITICAL",
                                "context": "blueprint",
                                "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 제{ep_num}화(Arc {arc_no}) Blueprint에서 다시 등장"
                            })

        return violations

    def check_dead_npc_in_manuscript(self, manuscript: str, ep_num: int, arc_no: int = 0) -> List[dict]:
        """
        [V60.96] Manuscript에서 죽은 NPC 등장 검사 - REJECT 대상

        Args:
            manuscript: 원고 텍스트
            ep_num: 에피소드 번호
            arc_no: [V60.97] Arc 번호 (타임라인 비교용, 0이면 ep_num으로 추정)

        Returns:
            위반 목록 [{npc_name, death_arc, severity, context}]
        """
        violations = []

        if not manuscript or not isinstance(manuscript, str):
            return violations

        # [V60.97] arc_no 추정 (파라미터 없으면 에피소드 기준)
        if arc_no <= 0:
            arc_no = (ep_num - 1) // 5 + 1

        for npc_name, info in self.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)

                # [V60.97] 타임라인 비교: 사망 이전 Arc에서는 검사 스킵
                if arc_no < death_arc:
                    continue  # 아직 죽지 않은 시점

                if npc_name in manuscript:
                    # 회상/언급 패턴은 허용 (더 광범위)
                    flashback_patterns = [
                        f"{npc_name}의 죽음", f"{npc_name}을 떠올", f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}", f"죽은 {npc_name}", f"{npc_name}의 유언",
                        f"{npc_name}의 무덤", f"{npc_name}의 원혼", f"{npc_name}의 유품",
                        f"{npc_name}을 추모", f"{npc_name}의 복수", f"{npc_name}의 이름",
                        f"{npc_name}처럼", f"{npc_name}같은", f"과거의 {npc_name}",
                        f"{npc_name}의 기억", f"{npc_name}의 영혼"
                    ]
                    is_flashback = any(pattern in manuscript for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장 패턴 (대화, 행동)
                        action_patterns = [
                            f"{npc_name}이 말", f"{npc_name}가 말", f"{npc_name}이 대답",
                            f"{npc_name}가 대답", f"{npc_name}은 고개", f"{npc_name}는 고개",
                            f'"{npc_name}', f"{npc_name}이 검", f"{npc_name}가 검",
                            f"{npc_name}의 손", f"{npc_name}이 다가", f"{npc_name}가 다가"
                        ]
                        if any(pattern in manuscript for pattern in action_patterns):
                            violations.append({
                                "npc_name": npc_name,
                                "death_arc": death_arc,
                                "current_ep": ep_num,
                                "current_arc": arc_no,
                                "severity": "CRITICAL",
                                "context": "manuscript",
                                "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 제{ep_num}화(Arc {arc_no}) 원고에서 살아있는 것처럼 등장"
                            })

        return violations

    def get_dead_npc_summary(self) -> str:
        """
        [V60.96] 죽은 NPC 목록 요약 (Writer/Architect 프롬프트 주입용)

        Returns:
            죽은 NPC 목록 문자열
        """
        dead_npcs = []
        for name, info in self.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)
                dead_npcs.append(f"  - {name} (Arc {death_arc}에서 사망)")

        if not dead_npcs:
            return ""

        lines = [
            "🚨 [사망 NPC 목록 - 절대 살아있는 것처럼 등장시키지 말 것]",
            *dead_npcs,
            ""
        ]
        return "\n".join(lines)


def create_tracker_from_arcs(arcs_data: List[dict]) -> StateTracker:
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

    return master_tracker
