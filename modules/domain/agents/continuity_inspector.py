"""
[V64.P3] Continuity Inspector — Facade (God Object 분해 후)

[V49] 원래 역할:
1. 이전 블루프린트/Arc 전체 분석
2. 아이템/패 획득 타임라인 추적
3. 캐릭터 상태 흐름 검증
4. 모순 감지 시 구체적 수정 지시 제공
5. [V61 NEW] Entity 명칭 일관성 검증

[V64.P3] 구조:
- continuity_arc.py       → ContinuityArcValidator (Arc 수준 검증)
- continuity_blueprint.py → ContinuityBlueprintValidator (Blueprint 수준 검증)
- continuity_manuscript.py → ContinuityManuscriptValidator (원고 수준 검증)
- continuity_tracker.py   → ContinuityTrackerIntegration (V49.7 트래커)

실행 시점:
- [V49 NEW] Stage 2에서 Analyst가 Arc 설계 후 - Arc 간 연속성 + 단일 Arc 내 모순 검증
- Stage 3에서 Architect가 블루프린트 생성 후 - 에피소드 연속성 검증
- [V61 NEW] Stage 4에서 원고 검증 시 - Entity 명칭 일관성 검증
- Director 검증 전에 실행
- REJECT 시 재생성 (모순 지점 피드백 포함)

비용: ~$0.01/에피소드 (flash 모델 사용)
"""

import logging
import re
from typing import Any

from .base_agent import BaseAgent

# [V64.P3] 서브모듈 임포트
from .continuity_arc import ContinuityArcValidator
from .continuity_blueprint import ContinuityBlueprintValidator
from .continuity_manuscript import ContinuityManuscriptValidator
from .continuity_tracker import ContinuityTrackerIntegration


class ContinuityInspector(BaseAgent):
    """
    [V49] 연속성 검증 전문 에이전트 (Director 산하)

    [V64.P3] God Object 분해 — Facade 패턴
    모든 공개 메서드는 유지하되, 구현은 4개 서브모듈에 위임.
    외부 코드(main_a.py 등)는 변경 불요.

    서브모듈:
    - self._arc       : ContinuityArcValidator       (Arc 수준 검증)
    - self._blueprint : ContinuityBlueprintValidator  (Blueprint 수준 검증)
    - self._manuscript: ContinuityManuscriptValidator  (원고 수준 검증)
    - self._tracker   : ContinuityTrackerIntegration   (V49.7 트래커)

    공유 유틸리티 (서브모듈이 self._ci.xxx로 접근):
    - acquire_patterns, grant_patterns, possession_patterns, usage_patterns, distribution_patterns
    - _is_same_item(), _is_distributed_item(), _filter_distributed_items()
    - _extract_acquisitions(), _extract_grants(), _extract_key_sentences()
    - _format_entity_registry()

    [V61 Update]
    - [NEW] entity_registry 파라미터: 모든 inspect 메서드에 추가
    - Entity 명칭 일관성 검증: 캐릭터, 조직, 장소, 물품, 기술명 일관성 체크
    - entity_consistency 출력 필드 추가
    """

    def __init__(self, context, client, model_tier=None) -> None:
        """
        [V62.5] gemini-2.5-pro로 다운그레이드 (검증 작업 - 3-pro 쿼터 절감)
        Args:
            context: ProjectContext 객체
            client: Gemini API 클라이언트
            model_tier: 사용할 모델 (V62.5: gemini-2.5-pro)
        """
        super().__init__(context, client, model_tier)

        # =================================================================
        # 공유 패턴 (서브모듈이 self._ci.xxx_patterns로 접근)
        # =================================================================

        # 아이템 획득 패턴 (한국어) - [V49.4 FIX] 더 엄격한 패턴
        # [V60.53] "집어 들", "뽑아 들" 제거 - 사용과 획득 혼동 방지
        self.acquire_patterns = [
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:획득|챙기|얻|주워\s*들|가져)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:손에\s*넣|가져가|챙겨\s*들)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:발견|찾아)",
            # [V60.53] 명시적 획득만 인정
            r"(?:새로운?|처음으로?)\s*['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:얻|획득|손에\s*넣)",
        ]

        # [V60.53] 사용/꺼내기 패턴 - 이미 가진 것을 쓰는 행동 (획득 아님)
        self.usage_patterns = [
            r"(?:다시|이미|자신의|허리춤의|품속의|등에\s*멘)\s*['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:다시\s*)?(?:세우|휘두르|내리치|찔러|베|쥐)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:뽑아\s*들|집어\s*들|꺼내\s*들)",
            r"(?:허리춤|품속|등|어깨)(?:에서|의)\s*['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)",
        ]

        # 수여/하사 패턴 (범용) - [V49.4 FIX] 더 엄격한 패턴
        self.grant_patterns = [
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:하사|수여|내리|던져\s*주|건네)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:풀어|떼어)\s*(?:던지|주)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:위임|부여|임명)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,20}권)['\"]?.*?(?:위임|부여|하사)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,20}패)['\"]?.*?(?:하사|수여|던지)",
        ]

        # 소지/사용 패턴
        self.possession_patterns = [
            r"품속.*?(.+?)(?:이|가)\s*(?:있|자리)",
            r"(.+?)(?:을|를)\s*(?:들어\s*보이|꺼내|쥐)",
            r"(?:쥔|든|멘)\s*(.+?)",
        ]

        # [V49.2] 복장/의복 패턴
        self.attire_patterns = [
            r"(?:비단|명주|무명|삼베|가죽|철갑|갑옷)\s*(?:옷|의|포|복|갑)",
            r"(?:화려한|허름한|낡은|깨끗한|더러운|피묻은|찢어진)\s*(?:옷|의|포|복|차림)",
            r"(?:옷|의복|복장|차림)(?:이|을|를)\s*(?:갈아입|바꾸|벗)",
        ]

        # [V49.2] 부상/상태 패턴
        self.injury_patterns = [
            r"(?:부상|상처|파열|골절|출혈|기절|내상|중상|경상)",
            r"(?:어깨|팔|다리|허리|등|가슴|복부|머리).*?(?:부상|상처|다치)",
            r"(?:피가|피를)\s*(?:흘|뿜|쏟)",
        ]

        # [V49.6] 분배/지급 제외 패턴
        self.distribution_patterns = [
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:나눠\s*주|지급|분배|하사하|배분)",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?[이가]?\s*(?:실린|담긴)\s*(?:수레|마차|짐|보따리)",
            r"(?:병사|무사|사병|부하)들?(?:에게|한테).*?['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?",
            r"['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?(?:을|를)\s*(?:내려\s*보내|전달하|건네주)",
            r"(?:막사|연무장|무기고).*?(?:도착|배달|전달).*?['\"]?([가-힣a-zA-Z0-9]{2,25})['\"]?",
        ]

        # =================================================================
        # [V64.P3] 서브모듈 초기화
        # =================================================================
        self._arc = ContinuityArcValidator(self)
        self._blueprint = ContinuityBlueprintValidator(self)
        self._manuscript = ContinuityManuscriptValidator(self)
        self._tracker = ContinuityTrackerIntegration(self)

        # [V49.7] 품질 향상 트래커 초기화 (서브모듈에 위임)
        self._tracker.init_trackers()

    # =================================================================
    # 공유 유틸리티 (서브모듈이 self._ci.xxx()로 접근)
    # =================================================================

    def _format_entity_registry(self, entity_registry: dict) -> str:
        """
        [V61] Entity Registry를 LLM용 포맷으로 변환

        Args:
            entity_registry: {characters:[], organizations:[], locations:[], objects:[], concepts:[]}

        Returns:
            포맷된 문자열 (Entity Registry가 없으면 "(등록된 Entity 없음)" 반환)
        """
        if not entity_registry:
            return "(등록된 Entity 없음 - 이전 에피소드/Arc에서 추출된 Entity가 없습니다)"

        lines = []
        categories = [
            ("characters", "캐릭터"),
            ("organizations", "조직/문파"),
            ("locations", "장소"),
            ("objects", "물품/아이템"),
            ("concepts", "기술/개념"),
        ]

        has_any = False
        for key, label in categories:
            items = entity_registry.get(key, [])
            if items:
                has_any = True
                formatted_items = []
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("canonical_name", str(item)))
                        aliases = item.get("aliases", [])
                        first_ep = item.get("first_appearance", item.get("first_ep", "?"))
                        if aliases:
                            formatted_items.append(f"{name} (별칭: {', '.join(aliases)}, 첫등장: ep{first_ep})")
                        else:
                            formatted_items.append(f"{name} (첫등장: ep{first_ep})")
                    else:
                        formatted_items.append(str(item))
                lines.append(f"[{label}] {', '.join(formatted_items)}")

        if not has_any:
            return "(등록된 Entity 없음)"

        return "\n".join(lines)

    def _extract_acquisitions(self, scenario: str) -> list[str]:
        """시나리오에서 획득 아이템 추출"""
        items = []
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, scenario)
            for item in matches:
                item = item.strip()
                if item and 2 <= len(item) <= 20:
                    items.append(item)
        return list(set(items))[:5]

    def _extract_grants(self, scenario: str) -> list[str]:
        """시나리오에서 수여물 추출"""
        grants = []
        for pattern in self.grant_patterns:
            matches = re.findall(pattern, scenario)
            for grant in matches:
                grant = grant.strip() if isinstance(grant, str) else str(grant)
                if grant and 2 <= len(grant) <= 20:
                    grants.append(grant)
        return list(set(grants))[:3]

    def _extract_key_sentences(self, scenario: str) -> str:
        """시나리오에서 연속성 관련 핵심 문장 추출"""
        key_patterns = [
            r"[^.。!?]*(?:획득|집어\s*들|뽑아\s*들|챙기|얻)[^.。!?]*[.。!?]",
            r"[^.。!?]*(?:하사|수여|위임|부여)[^.。!?]*[.。!?]",
            r"[^.。!?]*(?:부상|상처|파열|회복)[^.。!?]*[.。!?]",
            r"[^.。!?]*(?:품속|손에|어깨에|허리에)[^.。!?]*[.。!?]",
            r"[^.。!?]*(?:하사|수여|위임|부여|임명)[^.。!?]*[.。!?]",
        ]

        key_sentences = set()
        for pattern in key_patterns:
            matches = re.findall(pattern, scenario)
            for match in matches:
                if len(match.strip()) > 10:
                    key_sentences.add(match.strip())

        sorted_sentences = sorted(
            key_sentences, key=lambda s: scenario.find(s) if scenario.find(s) >= 0 else len(scenario)
        )

        result = " ... ".join(sorted_sentences[:10])

        if len(result) < 500:
            result = scenario[:800] + " ... [중략] ... " + scenario[-500:]

        return result

    def _is_same_item(self, item1: str, item2: str) -> bool:
        """
        [V60.55] 두 아이템이 같은 것인지 판단 - 초보수적 접근
        100% 확실한 경우만 True, 조금이라도 다르면 False
        """
        item1_clean = item1.strip()
        item2_clean = item2.strip()

        item1_normalized = "".join(item1_clean.lower().split())
        item2_normalized = "".join(item2_clean.lower().split())

        if item1_normalized == item2_normalized:
            logging.info(f" [_is_same_item] 정확 매칭: '{item1_clean}' == '{item2_clean}'")
            return True

        logging.info(f" [_is_same_item] 다른 아이템: '{item1_clean}' != '{item2_clean}'")
        return False

    def _is_distributed_item(self, item: str, context: str) -> bool:
        """
        [V49.6] 아이템이 타인에게 분배/지급된 것인지 판단
        """
        if not item or not context:
            return False

        item_pos = context.find(item)
        if item_pos == -1:
            return False

        start = max(0, item_pos - 100)
        end = min(len(context), item_pos + len(item) + 100)
        local_context = context[start:end]

        distribution_keywords = [
            "지급",
            "분배",
            "나눠",
            "배분",
            "내려 보내",
            "하사하",
            "수레",
            "마차",
            "도착",
            "배달",
            "전달",
            "병사들",
            "무사들",
            "사병들",
            "부하들",
            "병사에게",
            "무사에게",
            "사병에게",
            "부하에게",
            "막사 앞",
            "연무장에",
            "도착한다",
            "실린",
        ]

        for keyword in distribution_keywords:
            if keyword in local_context:
                return True

        for pattern in self.distribution_patterns:
            matches = re.findall(pattern, local_context)
            for match in matches:
                if self._is_same_item(item, match):
                    return True

        return False

    def _filter_distributed_items(self, items: list[str], context: str) -> list[str]:
        """
        [V49.6] 분배된 아이템을 필터링
        """
        if not items or not context:
            return items

        filtered = []
        for item in items:
            if not self._is_distributed_item(item, context):
                filtered.append(item)

        return filtered

    # =================================================================
    # [V64.P3] 위임 스텁 — Blueprint 수준 검증
    # =================================================================

    def inspect(
        self,
        current_ep: int,
        current_blueprint: dict,
        prev_blueprints: list[dict],
        hud_history: list[dict] = None,
        entity_registry: dict = None,
    ) -> dict:
        """블루프린트 연속성 검증 실행 → ContinuityBlueprintValidator에 위임"""
        return self._blueprint.inspect(
            current_ep, current_blueprint, prev_blueprints, hud_history=hud_history, entity_registry=entity_registry
        )

    def _python_precheck(self, current_ep: int, current_scenario: str, prev_blueprints: list[dict]) -> dict:
        """Python 기반 사전 검증 → ContinuityBlueprintValidator에 위임"""
        return self._blueprint._python_precheck(current_ep, current_scenario, prev_blueprints)

    def _format_prev_blueprints(self, prev_blueprints: list[dict]) -> str:
        """이전 블루프린트 포맷팅 → ContinuityBlueprintValidator에 위임"""
        return self._blueprint._format_prev_blueprints(prev_blueprints)

    def _format_timeline(self, items: list[tuple]) -> str:
        """타임라인 포맷팅 → ContinuityBlueprintValidator에 위임"""
        return self._blueprint._format_timeline(items)

    def _generate_fix_instructions(self, violations: list[dict]) -> str:
        """수정 지시 생성 → ContinuityBlueprintValidator에 위임"""
        return self._blueprint._generate_fix_instructions(violations)

    def get_prev_blueprints(self, current_ep: int, window: int = None) -> list[dict]:
        """DB에서 이전 블루프린트 조회 → ContinuityBlueprintValidator에 위임"""
        return self._blueprint.get_prev_blueprints(current_ep, window=window)

    # =================================================================
    # [V64.P3] 위임 스텁 — Arc 수준 검증
    # =================================================================

    def inspect_arc(self, current_arc: dict, prev_arcs: list[dict], entity_registry: dict = None) -> dict:
        """Arc 수준 연속성 검증 → ContinuityArcValidator에 위임"""
        return self._arc.inspect_arc(current_arc, prev_arcs, entity_registry=entity_registry)

    def _inspect_intra_arc_only(self, current_arc: dict) -> dict:
        """단일 Arc 내 모순 검증 → ContinuityArcValidator에 위임"""
        return self._arc._inspect_intra_arc_only(current_arc)

    def _extract_accurate_joint_docs(
        self, tactical_doc: str, arc_no: int, ep_end: int, original_joint_docs: dict
    ) -> dict | None:
        """Joint Docs 자동 추출 → ContinuityArcValidator에 위임"""
        return self._arc._extract_accurate_joint_docs(tactical_doc, arc_no, ep_end, original_joint_docs)

    def _extract_last_episode_content(self, tactical_doc: str, ep_end: int) -> str:
        """마지막 화 내용 추출 — [TTE] 공유 유틸 위임"""
        from modules.core.tactical_utils import extract_episode_tactical

        return extract_episode_tactical(tactical_doc, ep_end, fallback_full=False)

    def _arc_python_precheck(self, current_arc: dict, prev_arcs: list[dict]) -> dict:
        """Arc Python 사전 검증 → ContinuityArcValidator에 위임"""
        return self._arc._arc_python_precheck(current_arc, prev_arcs)

    def _check_intra_arc_consistency(self, arc: dict) -> list[dict]:
        """단일 Arc 내 모순 검증 → ContinuityArcValidator에 위임"""
        return self._arc._check_intra_arc_consistency(arc)

    def _format_prev_arcs(self, prev_arcs: list[dict]) -> str:
        """이전 Arc 포맷팅 → ContinuityArcValidator에 위임"""
        return self._arc._format_prev_arcs(prev_arcs)

    def _format_arc_timeline(self, items: list[tuple]) -> str:
        """Arc 타임라인 포맷팅 → ContinuityArcValidator에 위임"""
        return self._arc._format_arc_timeline(items)

    def _generate_arc_fix_instructions(self, violations: list[dict]) -> str:
        """Arc 위반 수정 지시 생성 → ContinuityArcValidator에 위임"""
        return self._arc._generate_arc_fix_instructions(violations)

    # =================================================================
    # [V64.P3] 위임 스텁 — 원고(Manuscript) 수준 검증
    # =================================================================

    def inspect_manuscript(
        self,
        current_ep: int,
        manuscript: str,
        blueprint: dict,
        prev_manuscripts: list[dict],
        hud_history: list[dict] = None,
        entity_registry: dict = None,
    ) -> dict:
        """원고 연속성 검증 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript.inspect_manuscript(
            current_ep,
            manuscript,
            blueprint,
            prev_manuscripts,
            hud_history=hud_history,
            entity_registry=entity_registry,
        )

    def inspect_manuscript_v59(
        self,
        current_ep: int,
        manuscript: str,
        blueprint: dict,
        prev_manuscripts: list[dict],
        hud_history: list[dict] = None,
    ) -> dict:
        """[V59] 강화된 원고 검증 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript.inspect_manuscript_v59(
            current_ep, manuscript, blueprint, prev_manuscripts, hud_history=hud_history
        )

    def get_prev_manuscripts(self, current_ep: int, window: int = 5) -> list[dict]:
        """DB에서 이전 원고 조회 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript.get_prev_manuscripts(current_ep, window=window)

    def _manuscript_python_precheck(
        self, current_ep: int, manuscript: str, prev_manuscripts: list[dict], blueprint: dict
    ) -> dict:
        """원고 Python 사전 검증 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._manuscript_python_precheck(current_ep, manuscript, prev_manuscripts, blueprint)

    def _check_relationship_jump(self, prev_manuscripts: list[dict], manuscript: str) -> list[dict]:
        """관계 급변 탐지 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._check_relationship_jump(prev_manuscripts, manuscript)

    def _check_villain_intelligence(self, prev_manuscripts: list[dict], manuscript: str) -> list[dict]:
        """악역 지능 보호 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._check_villain_intelligence(prev_manuscripts, manuscript)

    def _check_time_flow(self, prev_manuscripts: list[dict], manuscript: str) -> list[dict]:
        """시간 흐름 검증 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._check_time_flow(prev_manuscripts, manuscript)

    def _check_reader_immersion(self, prev_manuscripts: list[dict], manuscript: str, current_ep: int) -> list[dict]:
        """독자 몰입도 예측 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._check_reader_immersion(prev_manuscripts, manuscript, current_ep)

    def _check_skill_timeline(self, current_ep: int, manuscript: str, prev_manuscripts: list[dict]) -> dict:
        """[V59] 스킬 타임라인 검증 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._check_skill_timeline(current_ep, manuscript, prev_manuscripts)

    def _is_same_skill(self, skill1: str, skill2: str) -> bool:
        """두 스킬 동일성 판단 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._is_same_skill(skill1, skill2)

    def _track_relationship_history(self, current_ep: int, manuscript: str, prev_manuscripts: list[dict]) -> dict:
        """[V59] 관계 히스토리 추적 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._track_relationship_history(current_ep, manuscript, prev_manuscripts)

    def _check_blueprint_only(self, current_ep: int, manuscript: str, blueprint: dict) -> dict:
        """Blueprint 준수만 체크 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._check_blueprint_only(current_ep, manuscript, blueprint)

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> list[str]:
        """핵심 키워드 추출 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._extract_keywords(text, max_keywords=max_keywords)

    def _format_prev_manuscripts(self, prev_manuscripts: list[dict]) -> str:
        """이전 원고 포맷팅 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._format_prev_manuscripts(prev_manuscripts)

    def _generate_manuscript_fix_instructions(self, violations: list[dict]) -> str:
        """원고 수정 지시 생성 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._generate_manuscript_fix_instructions(violations)

    def _generate_v59_fix_instructions(self, violations: list[dict]) -> str:
        """[V59] 수정 지시 생성 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._generate_v59_fix_instructions(violations)

    def _is_item_acquired(self, item: str, acquired_items: set[str]) -> bool:
        """아이템 획득 여부 확인 → ContinuityManuscriptValidator에 위임"""
        return self._manuscript._is_item_acquired(item, acquired_items)

    # =================================================================
    # [V64.P3] 위임 스텁 — V49.7 트래커
    # =================================================================

    def _init_v49_7_trackers(self) -> None:
        """[V49.7] 트래커 초기화 → ContinuityTrackerIntegration에 위임"""
        self._tracker.init_trackers()

    def _get_protagonist_name(self) -> str:
        """주인공 이름 추출 → ContinuityTrackerIntegration에 위임"""
        return self._tracker._get_protagonist_name()

    def _validate_with_v49_7_trackers(
        self, arc: int, episode: int, content: str, content_type: str = "blueprint"
    ) -> dict[str, Any]:
        """[V49.7] 트래커 기반 검증 → ContinuityTrackerIntegration에 위임"""
        return self._tracker.validate_with_trackers(arc, episode, content, content_type=content_type)

    def _check_relationship_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """관계 전이 검증 → ContinuityTrackerIntegration에 위임"""
        return self._tracker._check_relationship_with_tracker(arc, episode, content)

    def _check_power_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """파워 스케일링 검증 → ContinuityTrackerIntegration에 위임"""
        return self._tracker._check_power_with_tracker(arc, episode, content)

    def _check_foreshadowing_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """복선 상태 검증 → ContinuityTrackerIntegration에 위임"""
        return self._tracker._check_foreshadowing_with_tracker(arc, episode, content)

    def _check_state_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """내공/부상 상태 검증 → ContinuityTrackerIntegration에 위임"""
        return self._tracker._check_state_with_tracker(arc, episode, content)

    def load_trackers_from_db(self, arcs_data: list[dict] = None) -> dict[str, int]:
        """[V49.7] DB에서 트래커 상태 로드 → ContinuityTrackerIntegration에 위임"""
        return self._tracker.load_trackers_from_db(arcs_data=arcs_data)
