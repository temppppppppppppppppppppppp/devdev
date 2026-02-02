"""
[V49.3] State Tracker Agent - 상태 추적 및 DAG 타임라인 검증

Arc 내 각 회차의 상태(무기, 부상, 위치)를 자동 추적하고
DAG(Directed Acyclic Graph) 형태로 타임라인을 구성하여 검증합니다.
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class EpisodeState:
    """에피소드 단위 상태 스냅샷"""
    ep_num: int
    location: str = ""
    weapons: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    injuries: str = "정상"  # 정상/경상/중상/위독
    internal_energy: int = 100  # 0-100%
    relationships: Dict[str, str] = field(default_factory=dict)  # NPC -> 상태

    def to_dict(self) -> dict:
        return {
            "ep_num": self.ep_num,
            "location": self.location,
            "weapons": self.weapons.copy(),
            "items": self.items.copy(),
            "injuries": self.injuries,
            "internal_energy": self.internal_energy,
            "relationships": self.relationships.copy()
        }


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

    Arc 설계 시 각 회차의 상태를 추적하여 DAG 형태로 관리하고
    상태 불일치(무기 중복 획득, 부상 무시 등)를 사전에 탐지합니다.

    Usage:
        tracker = StateTracker()
        tracker.load_arc_design(arc_tactical_doc)
        issues = tracker.validate_timeline()
        if issues:
            # 상태 불일치 발견 - 재설계 필요
    """

    def __init__(self):
        self.states: Dict[int, EpisodeState] = {}  # ep_num -> state
        self.transitions: List[StateTransition] = []
        self.global_items: Set[str] = set()  # 전체 소지 아이템 추적
        self.acquired_items: Dict[str, int] = {}  # item -> 획득 에피소드
        self.consumed_items: Dict[str, int] = {}  # item -> 소모 에피소드

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

            # 낮음 (10-30%) - 단독 단어로만 매칭 (오탐지 방지)
            if re.search(r'(탈진|고갈|소진|바닥|전멸|방전)', value):
                return 10

            # 높음 (80-100%) - 단독 단어로만 매칭
            if re.search(r'(최대|충만|가득|완전회복|만땅)', value):
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
            # 상태도 병합
            master_tracker.states.update(arc_tracker.states)
            master_tracker.transitions.extend(arc_tracker.transitions)

    return master_tracker
