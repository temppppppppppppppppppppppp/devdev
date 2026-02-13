"""
[V60.80] Chief Writer - Stage 4 앙상블 원고 생성 엔진

Stage 4 "Director 주권주의" 아키텍처의 핵심 생성 에이전트.
3개 후보를 병렬 생성하여 Director에게 제출.

핵심 철학: "Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

[V60.81] Writer 핵심 기능 통합:
- Self-Critique (다중 라운드 자체 검토)
- Leakage 방지 (출력 정제)
- NPC 빈도/장비 추적
- HUD 변화 추세 모니터링
- DNA 모드 (1화 특수 처리)
- Rubric 기반 품질 평가
"""

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared

from .base_agent import BaseAgent

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section, get_primitive_guard

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False

from .chief_writer_prompts import (
    build_chief_writer_main_prompt,
    get_anti_trope_instructions,
    get_common_rules_section,
    get_fix_issues_prompt,
    get_modern_origin_section,
    get_primitive_constraint_fallback,
    get_prompt_template_output,
    get_writing_guidelines_section,
)


class ChiefWriter(BaseAgent):
    """
    [V60.80] Chief Writer - 앙상블 원고 생성 엔진

    특징:
    - 3개 후보 병렬 생성 (균형/서사/긴장감)
    - CoT (Chain of Thought) 기반 전략적 집필
    - Director 피드백 반영 재생성
    """

    # [V61.3] 앙상블 타임아웃 설정 (야간 무인 운영 - 무한 대기 방지)
    ENSEMBLE_TIMEOUT = 600  # 전체 앙상블 타임아웃 (초) - 10분 (thinking 오버헤드 반영)
    SINGLE_CANDIDATE_TIMEOUT = 540  # 개별 후보 타임아웃 (초) - 9분

    # 앙상블 전략 정의
    ENSEMBLE_STRATEGIES = {
        "balanced": {
            "name": "균형 전략",
            "temperature": 0.7,
            "emphasis": "Blueprint 충실 재현",
            "instruction": """
[전략 A: 균형]
- Blueprint의 모든 씬을 균등한 비중으로 반영
- 서사와 액션의 조화로운 배분
- 안정적인 품질 우선
- ⚠️ 반드시 5,000자 이상 작성. 각 씬에 충분한 묘사와 대화를 배분할 것
""",
        },
        "narrative": {
            "name": "서사 강조",
            "temperature": 0.8,
            "emphasis": "심리 묘사 + 관계 발전",
            "instruction": """
[전략 B: 서사 강조]
- 캐릭터 내면 묘사 강화
- 관계 발전과 감정선에 집중
- 대화와 심리 갈등 확대
- ⚠️ 반드시 5,000자 이상 작성. 심리 묘사와 대화를 충분히 확장할 것
""",
        },
        "tension": {
            "name": "긴장감 + 반전 강조",
            "temperature": 0.8,
            "emphasis": "반전 + 클리프행어 + 예측 불가능 전개",
            "instruction": """
[전략 C: 몰입감 극대화]
- 독자 예측을 벗어나는 전개 1개 이상 포함
- 서스펜스와 긴장감 극대화. 정보를 독자에게 천천히 공개하라
- 강렬한 클리프행어 (단순 전투 외: 정보 폭탄, 배신, 반전)
- 캐릭터 간 긴장감 있는 대화 (침묵, 눈빛, 서브텍스트)
- ⚠️ 반드시 5,000자 이상 작성. 긴장 고조와 반전을 충분히 전개할 것
""",
        },
    }

    # [V64.P4] 프롬프트 외부화
    PROMPT_TEMPLATE_OUTPUT = get_prompt_template_output()

    def __init__(self, context, client, model_tier="gemini-3-pro-preview") -> None:
        super().__init__(context, client, model_tier)
        self._agent_name = "ChiefWriter"
        # [V60.82] 배치 캐시 - DB 쿼리 최적화
        self._manuscript_cache = {}  # {ep_num: content}
        self._cache_ep_num = -1  # 캐시 유효성 기준
        # [V65] _emotion_skeleton_cache / _emotion_skeleton_blueprint_hash 삭제 (Emotion Skeleton Dead Code 제거)

    def generate_ensemble(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str = "",
        director_feedback: str = "",
        failure_constraints: str = "",
        # [V60.80 FIX] 미래 침범 방지용 추가 파라미터
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        # [V60.80+] 기존 Writer 핵심 기능 통합
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        # [V60.81] 추가 파라미터
        npc_equipment_summary: str = "",
        intro_dna: str = "CYNICAL",
        # [V60.85] 장르 Guard Purism Prompt
        purism_prompt: str = "",
        # [V60.95] 고밀도 HUD 전달
        state_tracker=None,
        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_text: str = "",
        # [V68] 세계 상태 요약 — 장기연재 모순 방지
        world_state_summary: str = "",
        # [V68] 에피소드 연결고리 — 직전 화에서 이어받아야 할 것
        chain_link_section: str = "",
    ) -> list[dict]:
        """
        3개 후보 원고 병렬 생성

        Args:
            ep_num: 에피소드 번호
            blueprint: Blueprint 데이터
            prev_manuscript: 직전 화 원고
            hud_report: 현재 HUD 상태
            arc_doc: Arc 전술 문서
            master_bible: 마스터 바이블
            style_guide: 플랫폼 스타일 가이드
            director_feedback: Director 피드백 (재시도 시)
            failure_constraints: 실패 학습 제약 (이전 REJECT 패턴)
            purism_prompt: 장르 Guard의 순혈주의 지침 (V60.85)
            prev_manuscripts_text: [V67] 이전 30화 원고 전문 (모순 방지용)
            world_state_summary: [V68] 세계 상태 요약 (장기연재 모순 방지)
            chain_link_section: [V68] 직전 화 연결고리 (다음 화에서 이어받을 것)

        Returns:
            List[Dict]: 3개 후보 원고 [{
                "strategy": str,
                "manuscript": str,
                "title": str,
                "state_updates": dict,
                "metadata": dict
            }]
        """
        # [V60.82] DB 배치 프리페치 - 중복 쿼리 제거
        self._prefetch_manuscripts(ep_num, window=10)

        # 공통 컨텍스트 구성
        common_context = self._build_common_context(
            ep_num=ep_num,
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
            hud_report=hud_report,
            arc_doc=arc_doc,
            master_bible=master_bible,
            style_guide=style_guide,
            director_feedback=director_feedback,
            failure_constraints=failure_constraints,
            # 미래 침범 방지
            current_inventory=current_inventory or [],
            current_martial_arts=current_martial_arts or [],
            dead_npcs=dead_npcs or [],
            item_acquisition_timeline=item_acquisition_timeline,
            # 기존 Writer 핵심 기능
            reference_anchor_prompt=reference_anchor_prompt,
            mandatory_context=mandatory_context,
            anti_trope_prompt=anti_trope_prompt,
            justification_prompt=justification_prompt,
            reflexion_prompt=reflexion_prompt,
            genre_name=genre_name,
            # [V60.81] 추가 파라미터
            npc_equipment_summary=npc_equipment_summary,
            intro_dna=intro_dna,
            # [V60.85] 장르 Guard Purism Prompt
            purism_prompt=purism_prompt,
            # [V60.95] 고밀도 HUD 전달
            state_tracker=state_tracker,
            # [V67] 이전 원고 전문
            prev_manuscripts_text=prev_manuscripts_text,
            # [V68] 세계 상태 요약
            world_state_summary=world_state_summary,
            # [V68] 에피소드 연결고리
            chain_link_section=chain_link_section,
        )

        # [V61.7] 컨텍스트 캐싱 시도 (토큰 비용 50-67% 절감)
        cache_name = None
        try:
            cache_info = self._get_or_create_context_cache(
                cache_type="manuscript",
                content=common_context,
                ttl_seconds=600,  # 10분 (같은 에피소드 재시도 대비)
                project_name=f"ep{ep_num}",
            )
            cache_name = cache_info.get("cache_name")
            if cache_name:
                logging.info(f"📦 [V61.7] 컨텍스트 캐시 활성 (ep{ep_num}, {len(common_context)}자)")
        except Exception as e:  # [V64.P4] OPTIONAL: context caching
            logging.debug(f"[SILENT] context caching: {e}")
            pass  # 캐싱 실패해도 기존 방식으로 진행

        # 병렬 생성
        candidates = []
        strategies = ["balanced", "narrative", "tension"]

        # [V61.3] 전체 병렬 처리 블록을 try-except로 감싸서 급사 방지
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(
                        self._generate_single_candidate,
                        ep_num=ep_num,
                        strategy=strategy,
                        common_context=common_context,
                        hud_report=hud_report,
                        master_bible=master_bible,
                        genre_name=genre_name,
                        cache_name=cache_name,
                    ): strategy
                    for strategy in strategies
                }

                # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy = futures[future]
                        try:
                            # [V61.3] 개별 후보에도 타임아웃 적용
                            result = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
                            if result:
                                candidates.append(result)
                                logging.info(
                                    f"✅ [ChiefWriter] 후보 {strategy} 생성 완료 ({len(result.get('manuscript', ''))}자)"
                                )
                        except FutureTimeoutError:
                            logging.info(f"⏰ [V61.3] 후보 {strategy} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")
                            candidates.append(
                                {
                                    "strategy": strategy,
                                    "manuscript": "",
                                    "title": "",
                                    "state_updates": {},
                                    "metadata": {"error": "타임아웃"},
                                    "error": True,
                                }
                            )
                        except Exception as e:
                            logging.warning(f"⚠️ [ChiefWriter] 후보 {strategy} 생성 실패: {str(e)[:50]}")
                            # 실패한 전략은 빈 결과로 대체
                            candidates.append(
                                {
                                    "strategy": strategy,
                                    "manuscript": "",
                                    "title": "",
                                    "state_updates": {},
                                    "metadata": {"error": str(e)},
                                    "error": True,
                                }
                            )
                except FutureTimeoutError:
                    # 전체 앙상블 타임아웃 - 완료된 후보만 사용
                    logging.info(
                        f"⏰ [V61.3] 원고 앙상블 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
                    )
                except Exception as e:
                    # [V61.3] as_completed 자체 예외 처리
                    logging.info(f"⚠️ [V61.3] 원고 앙상블 루프 예외: {str(e)[:80]}")
        except Exception as e:
            # [V61.3] ThreadPoolExecutor 전체 예외 처리 - 급사 방지
            # stderr로 출력 (Rich 스피너가 stdout 가림)
            import sys
            import traceback

            print(f"      🚨 [V61.3] 원고 병렬 처리 크래시 방지: {str(e)[:100]}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

        # 최소 1개 후보 보장
        valid_candidates = [c for c in candidates if not c.get("error")]
        if not valid_candidates:
            logging.warning("🚨 [ChiefWriter] 모든 후보 생성 실패 - 단일 재시도")
            fallback = self._generate_single_candidate(
                ep_num=ep_num,
                strategy="balanced",
                common_context=common_context,
                hud_report=hud_report,
                master_bible=master_bible,
                genre_name=genre_name,
                cache_name=cache_name,
            )
            if fallback:
                candidates = [fallback]

        # [V66.3] C-4: 모든 후보 생성 실패 시 에러 dict 반환 (빈 배열 방지 → downstream IndexError 크래시 방어)
        if not candidates:
            logging.error("[ChiefWriter] generate_ensemble: 앙상블 + 단일 폴백 모두 실패 — 에러 후보 반환")
            candidates = [
                {
                    "strategy": "error_fallback",
                    "strategy_name": "에러 폴백",
                    "manuscript": "",
                    "title": f"제{ep_num}화 (생성 실패)",
                    "state_updates": {},
                    "metadata": {"error": "모든 후보 생성 실패"},
                    "error": True,
                    "error_message": "모든 후보 생성 실패",
                }
            ]

        return candidates

    def _generate_single_candidate(
        self,
        ep_num: int,
        strategy: str,
        common_context: str,
        hud_report: str = "",
        master_bible: dict = None,
        genre_name: str = "무협",
        cache_name: str = None,
    ) -> dict | None:
        """
        [V60.81] 단일 후보 생성 + Self-Critique + Leakage 방지
        [V61.7] 컨텍스트 캐싱 지원 - 토큰 비용 50-67% 절감

        Args:
            ep_num: 에피소드 번호
            strategy: 전략 이름 (balanced/narrative/tension)
            common_context: 공통 컨텍스트
            hud_report: HUD 상태 (Self-Critique용)
            master_bible: 마스터 바이블 (NPC 정보 추출용)
            genre_name: 장르명
            cache_name: [V61.7] 캐시 이름 (있으면 캐시 사용, 없으면 기존 방식)
        """
        # [V61.3] 전체 메서드를 try-except로 감싸서 worker thread 크래시 방지
        try:
            strategy_config = self.ENSEMBLE_STRATEGIES.get(strategy, self.ENSEMBLE_STRATEGIES["balanced"])

            # [V61.7] 캐시 사용 분기
            if cache_name:
                # 캐시 활성: common_context는 캐시에 있으므로 전략 부분만 전송
                strategy_prompt = f"""{strategy_config["instruction"]}

{self.PROMPT_TEMPLATE_OUTPUT.format(strategy=strategy)}"""

                # 폴백용 전체 프롬프트 (캐시 실패 시)
                full_prompt = f"""{common_context}

{strategy_config["instruction"]}

{self.PROMPT_TEMPLATE_OUTPUT.format(strategy=strategy)}"""

                response = self._ask_with_cached_context(
                    cache_name=cache_name,
                    prompt=strategy_prompt,
                    temperature=strategy_config["temperature"],
                    thinking_level="medium",
                    full_prompt_fallback=full_prompt,
                )
            else:
                # [V60.82] 기존 방식: 전체 프롬프트
                full_prompt = f"""{common_context}

{strategy_config["instruction"]}

{self.PROMPT_TEMPLATE_OUTPUT.format(strategy=strategy)}"""

                response = self.ask(
                    prompt=full_prompt,
                    temperature=strategy_config["temperature"],
                    thinking_level="medium",  # [V61.6] 원고 생성 추론 강화
                )

            # [V60.81] Leakage 방지 적용
            response = self._sanitize_leakage(response)

            data = self._extract_json_robust(response)

            if not data or data.get("parsing_error"):
                return None

            # 원고 추출 (타입 안전성 보장)
            manuscript_content = data.get("content", "")
            if not isinstance(manuscript_content, str):
                # content가 리스트/딕셔너리인 경우 문자열로 변환 시도
                if isinstance(manuscript_content, list):
                    manuscript_content = "\n".join(str(item) for item in manuscript_content)
                else:
                    manuscript_content = str(manuscript_content) if manuscript_content else ""
            manuscript_json = json.dumps(data, ensure_ascii=False)

            # [V60.81] Self-Critique 적용 (NPC 정보 필요)
            npcs = []
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
                assets = bible_root.get("AssetLibrary", {})
                npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])

            critiqued_manuscript = self._apply_self_critique(
                manuscript=manuscript_json, hud_report=hud_report, npcs=npcs, genre_name=genre_name, ep_num=ep_num
            )

            # Self-Critique 결과에서 content 재추출
            try:
                critiqued_data = json.loads(critiqued_manuscript)
                final_content = critiqued_data.get("content", manuscript_content)
                final_title = critiqued_data.get("title", data.get("title", f"제{ep_num}화"))
                final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))
            except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] IMPORTANT: critique parse, safe default
                final_content = manuscript_content
                final_title = data.get("title", f"제{ep_num}화")
                final_state = data.get("state_updates", {})

            return {
                "strategy": strategy,
                "strategy_name": strategy_config["name"],
                "manuscript": final_content,
                "title": final_title,
                "state_updates": final_state,
                "key_scenes_covered": data.get("key_scenes_covered", []),
                "metadata": {
                    "temperature": strategy_config["temperature"],
                    "emphasis": strategy_config["emphasis"],
                    "length": len(final_content),
                    "self_critique_applied": True,
                },
            }

        except Exception as e:
            # [V61.3] stderr로 출력 (Rich 스피너가 stdout 가림)
            import sys
            import traceback

            print(f"      🚨 [V61.3] ChiefWriter _generate_single_candidate 크래시: {str(e)[:80]}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return None

    def _build_common_context(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str,
        director_feedback: str,
        failure_constraints: str,
        # 미래 침범 방지
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        # 기존 Writer 핵심 기능
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        # [V60.81] 추가 파라미터
        npc_equipment_summary: str = "",
        intro_dna: str = "CYNICAL",
        # [V60.85] 장르 Guard Purism Prompt
        purism_prompt: str = "",
        # [V60.95] 고밀도 HUD 전달
        state_tracker=None,
        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_text: str = "",
        # [V68] 세계 상태 요약 — 장기연재 모순 방지
        world_state_summary: str = "",
        # [V68] 에피소드 연결고리 — 직전 화에서 이어받아야 할 것
        chain_link_section: str = "",
    ) -> str:
        """
        [V60.81] 공통 컨텍스트 구성 (CoT 기반 + Writer 핵심 기능 완전 통합)

        추가된 기능:
        - NPC 장비 현황
        - NPC 등장 빈도 경고
        - HUD 변화 추세
        - DNA 모드 (1화 특수)
        - HUD 급변 감지
        - [V60.85] 장르 Guard Purism Prompt 주입
        - [V67] 이전 원고 전문 (모순 방지용 컨텍스트)
        - [V68] 세계 상태 요약 (장기연재 모순 방지)
        """
        current_inventory = current_inventory or []
        current_martial_arts = current_martial_arts or []
        dead_npcs = dead_npcs or []

        # Blueprint에서 씬 정보 추출
        scene_breakdown = ""
        if isinstance(blueprint, dict):
            scenes = blueprint.get("scene_breakdown", {})
            if isinstance(scenes, dict):
                scene_breakdown = json.dumps(scenes, ensure_ascii=False, indent=2)
            integrated = blueprint.get("integrated_scenario", "")
            if integrated:
                scene_breakdown += f"\n\n통합 시나리오:\n{integrated}"

        # 마스터 바이블에서 핵심 정보 추출
        bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
        core_identity = bible_root.get("ProjectData", {}).get("CoreIdentity", {})
        assets = bible_root.get("AssetLibrary", {})

        # [V60.95] 주인공 설정 추출 (원시인/현대인 제약)
        protagonist_config = bible_root.get("protagonist_config", {})
        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "회귀자")

        # [V67.1] 환생 유형별 집필 맥락 주입
        incarnation_context_section = ""
        if incarnation_type == "회귀자":
            incarnation_context_section = """
### [V67.1] 회귀자 집필 가이드
주인공은 미래에서 되돌아온 회귀자입니다.
- 미래의 사건/인물/가격 등을 미리 아는 것이 당연합니다
- 내면 독백에서 "전생에서는...", "원래라면..." 같은 회고가 자연스럽습니다
- 주인공이 역사를 의도적으로 바꾸려는 행동은 핵심 서사입니다
- 단, NPC에게 미래 정보를 직접 말하면 어색합니다 (합리적 이유 필요)
"""
        elif incarnation_type == "빙의자":
            incarnation_context_section = """
### [V67.1] 빙의자 집필 가이드
주인공은 다른 인물의 몸에 빙의한 존재입니다.
- 원래 인물의 기억이 부분적으로 떠오를 수 있습니다
- 원래 인물과 다른 반응/성격을 보이면 주변이 의아해합니다
- "이 몸의 주인은..." 같은 내면 갈등이 자연스럽습니다
"""
        elif incarnation_type == "환생자":
            incarnation_context_section = """
### [V67.1] 환생자 집필 가이드
주인공은 전생의 기억을 가진 환생자입니다.
- 전생의 지식/기술이 단편적으로 떠오를 수 있습니다
- 현생의 몸이 전생의 능력을 완전히 재현하지 못할 수 있습니다
"""

        # [V60.96] 장르 코드 변환 (장르별 금지어 적용)
        genre_code_map = {
            "무협": "wuxia",
            "판타지": "fantasy",
            "헌터물": "hunter",
            "투자물": "investment",
            "배우물": "actor",
            "스포츠": "sports",
            "의학": "medical",
            "요리": "cooking",
            "작곡가": "composer",
            "대체역사": "alt_history",
        }
        genre_code = genre_code_map.get(genre_name, bible_root.get("_genre", "wuxia"))

        # [V60.96] 원시인 모드 제약 섹션 (장르별 JSON 기반 PrimitiveGuard)
        world_origin_constraint_section = ""
        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                # 장르별 JSON 기반 동적 생성
                world_origin_constraint_section = get_primitive_constraint_section(
                    protagonist_config, genre=genre_code, length="build"
                )
            else:
                # [V65] 폴백: 최소한의 경고
                world_origin_constraint_section = get_primitive_constraint_fallback()
        elif world_origin == "현대인":
            world_origin_constraint_section = get_modern_origin_section()  # [V65]

        # [V62.6→V63.2] 직전 원고: 구조화 다이제스트 + 엔딩 2500자 (800→2500 확대)
        prev_ending = prev_manuscript[-2500:] if prev_manuscript else ""
        prev_digest = self._generate_episode_digest(prev_manuscript, ep_num - 1) if prev_manuscript else ""

        # Director 피드백 섹션
        feedback_section = ""
        if director_feedback:
            feedback_section = f"""
### 🚨 [Director 피드백 - 반드시 반영]
{self._escape_braces(director_feedback)}
"""

        # 실패 학습 제약
        constraint_section = ""
        if failure_constraints:
            constraint_section = f"""
### ⚠️ [이전 REJECT 패턴 - 회피 필수]
{self._escape_braces(failure_constraints)}
"""

        # [V60.80 FIX] 미래 침범 방지 섹션
        future_guard_section = self._build_future_guard_section(
            current_inventory=current_inventory,
            current_martial_arts=current_martial_arts,
            dead_npcs=dead_npcs,
            item_acquisition_timeline=item_acquisition_timeline,
        )

        # [V60.81] 과거 침범 방지 섹션
        past_guard_section = self._build_past_guard_section(
            prev_manuscript=prev_manuscript, existing_dead_npcs=dead_npcs
        )

        # [V68] 세계 상태 요약 섹션 (최우선 주입)
        world_state_section = ""
        if world_state_summary:
            world_state_section = f"""
### [V68] 세계 상태 문서 (World State) — 반드시 참조
{self._escape_braces(world_state_summary)}
⚠️ 위 세계 상태와 모순되는 묘사/대화/사건은 절대 금지.
"""

        # [V60.80+] 기존 Writer 핵심 기능 섹션 조립
        writer_core_section = ""
        if world_state_section:
            writer_core_section += f"\n{world_state_section}\n"
        if reference_anchor_prompt:
            writer_core_section += f"\n{reference_anchor_prompt}\n"
        if mandatory_context:
            writer_core_section += f"\n{mandatory_context}\n"
        if anti_trope_prompt:
            writer_core_section += f"\n{anti_trope_prompt}\n"
        if justification_prompt:
            writer_core_section += f"\n{justification_prompt}\n"
        if reflexion_prompt:
            writer_core_section += f"\n{reflexion_prompt}\n"

        # [V60.81] NPC 장비 현황 섹션
        npc_equipment_section = ""
        if not npc_equipment_summary:
            npc_equipment_summary = self._get_npc_equipment_summary(master_bible)
        if npc_equipment_summary and npc_equipment_summary != "NPC 장비 정보 없음":
            npc_equipment_section = f"""
### 🗡️ [V60.81] NPC 현재 장비 현황
{self._escape_braces(npc_equipment_summary)}
⚠️ NPC가 소지한 무기/장비는 반드시 일관되게 묘사하라. 갑자기 없던 무기가 생기거나 사라지면 안 된다.
"""

        # [V60.81] NPC 등장 빈도 경고
        npc_frequency_section = ""
        npc_freq_warning = self._get_npc_frequency_warning(ep_num)
        if npc_freq_warning and npc_freq_warning != "빈도 추적 실패":
            npc_frequency_section = f"""
👥 [Lightweight] 주요 NPC 등장 빈도 (최근 10화):
{npc_freq_warning}
"""

        # [V60.81] HUD 변화 추세
        hud_trend_section = ""
        hud_trend = self._get_hud_trend_safe(ep_num)
        if hud_trend and hud_trend != "HUD 추세 정보 없음":
            hud_trend_section = f"""
📈 [Lightweight] 최근 5화 HUD 변화 추세:
{hud_trend}
⚠️ 갑작스러운 변화가 있다면 반드시 정당화 필요!
"""

        # [V60.81] HUD 급변 감지
        hud_anomaly_section = ""
        hud_anomalies = self._check_hud_anomalies(ep_num)
        if hud_anomalies.get("has_anomalies") and hud_anomalies.get("warning_text"):
            hud_anomaly_section = f"""
{hud_anomalies["warning_text"]}
"""

        # [V60.81] DNA 모드 지시문
        dna_instruction = self._get_dna_instruction(ep_num, intro_dna)

        # [V60.85] 장르 Guard Purism 섹션
        purism_section = ""
        if purism_prompt:
            purism_section = f"""
### 🛡️ [장르 순혈주의 절대 준수]
{self._escape_braces(purism_prompt)}
"""

        # [V60.95] 고밀도 HUD 컨텍스트 구축
        high_density_hud_section = ""
        if state_tracker:
            hd_hud = self._build_hud_context(state_tracker, ep_num)
            if hd_hud:
                high_density_hud_section = f"""
### 📊 [V60.95 고밀도 HUD - 주인공 상세 상태]
{self._escape_braces(hd_hud)}
"""

        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_section = ""
        if prev_manuscripts_text:
            prev_manuscripts_section = f"""

### [V67] 이전 원고 전문 — 진실의 원천 (모순 절대 금지)
아래는 이전에 확정·출판된 원고 전문입니다. 이 내용이 "실제로 일어난 일"입니다.
현재 원고를 작성할 때 아래 사실과 모순되면 안 됩니다.
특히 고유명사(인물, 조직, 장소, 회사명), 수치(금액, 가격, 환율), 상태(부상, 관계, 소지품)가
이전 원고와 달라지면 반드시 작중에서 이유를 명확히 설명해야 합니다.

{self._escape_braces(prev_manuscripts_text[:200000])}
"""

        # [V65] 메인 프롬프트 함수 래핑 호출
        return build_chief_writer_main_prompt(
            ep_num=ep_num,
            dna_instruction=dna_instruction,
            purism_section=purism_section,
            world_origin_constraint_section=world_origin_constraint_section,
            feedback_section=feedback_section,
            constraint_section=constraint_section,
            future_guard_section=future_guard_section,
            past_guard_section=past_guard_section,
            writer_core_section=writer_core_section,
            hud_anomaly_section=hud_anomaly_section,
            scene_breakdown=self._escape_braces(scene_breakdown),
            prev_digest=self._escape_braces(prev_digest),
            prev_ending=self._escape_braces(prev_ending),
            hud_report=self._escape_braces(hud_report),
            high_density_hud_section=high_density_hud_section,
            hud_trend_section=hud_trend_section,
            npc_equipment_section=npc_equipment_section,
            npc_frequency_section=npc_frequency_section,
            arc_doc=self._escape_braces(arc_doc) if arc_doc else "특이사항 없음",
            core_identity_desire=self._escape_braces(str(core_identity.get("desire", ""))),
            style_guide=self._escape_braces(style_guide) if style_guide else "기본 웹소설 문체",
            common_rules=get_common_rules_section(),
            writing_guidelines=get_writing_guidelines_section(),
            prev_manuscripts_section=prev_manuscripts_section,  # [V67]
            incarnation_context_section=incarnation_context_section,  # [V67.1]
            chain_link_section=self._escape_braces(chain_link_section) if chain_link_section else "",  # [V68]
        )

    # ── [V62.6] 에피소드 상태 다이제스트 ──────────────────────────

    def _generate_episode_digest(self, manuscript: str, ep_num: int = 0) -> str:
        """
        [V62.6] Python 기반 에피소드 상태 다이제스트 생성

        이전 에피소드 전체를 분석하여 핵심 상태 정보를 구조화된 텍스트로 반환.
        LLM 호출 없이 regex로 추출 (비용 $0).

        ChiefWriter가 원고 생성 시 prev_manuscript[-2500:]와 함께 사용하여
        이전 에피소드의 컨텍스트 손실 문제를 완화.
        """
        if not manuscript or len(manuscript) < 200:
            return ""

        digest_parts = []

        # 1. NPC 사망
        death_patterns = [
            r"([가-힣]{2,4})[이가은는]\s*(?:죽었다|사망했다|숨을\s*거두|최후를\s*맞|절명)",
            r"([가-힣]{2,4})[의]\s*(?:시신|주검|유해)",
            r"([가-힣]{2,4})[을를]\s*(?:죽였다|베었다|처단했다|살해했다)",
        ]
        dead_npcs = set()
        for pattern in death_patterns:
            for m in re.finditer(pattern, manuscript):
                dead_npcs.add(m.group(1))
        if dead_npcs:
            digest_parts.append(f"사망 NPC: {', '.join(dead_npcs)}")

        # 2. 아이템 획득/상실
        gain_patterns = [
            r"([가-힣]{2,6})[을를]\s*(?:획득|입수|얻었|받았|수령|전수받|건네받)",
        ]
        loss_patterns = [
            r"([가-힣]{2,6})[을를]\s*(?:잃어|버렸|빼앗겼|떨어뜨렸)",
            r"([가-힣]{2,6})[이가]\s*(?:부서졌|파괴되었|산산조각)",
        ]
        gained = set()
        for p in gain_patterns:
            for m in re.finditer(p, manuscript):
                name = m.group(1)
                if len(name) >= 2:
                    gained.add(name)
        lost = set()
        for p in loss_patterns:
            for m in re.finditer(p, manuscript):
                name = m.group(1)
                if len(name) >= 2:
                    lost.add(name)
        if gained:
            digest_parts.append(f"획득 아이템: {', '.join(gained)}")
        if lost:
            digest_parts.append(f"상실 아이템: {', '.join(lost)}")

        # 3. 부상
        injury_patterns = [
            r"(왼팔|오른팔|왼손|오른손|왼다리|오른다리|갈비뼈|어깨)[이가을를에]?\s*"
            r"(?:부러[졌져]|골절|부상|절단|찢[어겼]|관통|으스러)",
            r"(?:중상|내상|중독|출혈)[을를에]?\s*(?:입었|당했|걸렸)",
        ]
        injuries = set()
        for p in injury_patterns:
            for m in re.finditer(p, manuscript):
                injuries.add(m.group(0)[:20])
        if injuries:
            digest_parts.append(f"부상 상태: {', '.join(injuries)}")

        # 4. 위치 (마지막 언급)
        loc_patterns = [
            r"([가-힣]{2,8}(?:산|성|촌|루|각|관|당|원|궁|객잔|주막|동굴|절벽|광장|채|봉))"
            r"[에으로]?\s*(?:도착|돌아|들어|향|당도)",
        ]
        locations = []
        for p in loc_patterns:
            for m in re.finditer(p, manuscript):
                locations.append((m.start(), m.group(1)))
        if locations:
            last_loc = max(locations, key=lambda x: x[0])
            digest_parts.append(f"마지막 위치: {last_loc[1]}")

        # 5. 무공 습득
        skill_patterns = [
            r"([가-힣]{2,8}(?:공|법|결|식|초))[을를]\s*(?:익히|깨달|습득|전수받|터득)",
        ]
        skills = set()
        for p in skill_patterns:
            for m in re.finditer(p, manuscript):
                skills.add(m.group(1))
        if skills:
            digest_parts.append(f"습득 무공: {', '.join(skills)}")

        # 6. NPC 쓰러짐/기절 (사망 미만)
        down_patterns = [
            r"([가-힣]{2,4})[이가은는]\s*(?:쓰러졌|의식을\s*잃|기절했)",
        ]
        downed = set()
        for p in down_patterns:
            for m in re.finditer(p, manuscript):
                name = m.group(1)
                if name not in dead_npcs:
                    downed.add(name)
        if downed:
            digest_parts.append(f"부상/기절 NPC: {', '.join(downed)}")

        # 7. [V63.2] 관계 변화 (동맹/배신/화해)
        relation_patterns = [
            r"([가-힣]{2,4})[과와][의]?\s*(?:동맹|협력|연합)[을를]?\s*(?:맺|결성|체결)",
            r"([가-힣]{2,4})[이가은는]\s*(?:배신|배반|이탈)했",
            r"([가-힣]{2,4})[과와]\s*(?:화해|휴전|협정)[을를]?\s*(?:했|이루|맺)",
            r"([가-힣]{2,4})[이가은는]\s*(?:적이\s*되|원수가\s*되|등을\s*돌)",
        ]
        relation_changes = set()
        for p in relation_patterns:
            for m in re.finditer(p, manuscript):
                relation_changes.add(m.group(0)[:30])
        if relation_changes:
            digest_parts.append(f"관계 변화: {', '.join(relation_changes)}")

        # 8. [V63.2] 미스터리/비밀/복선
        mystery_patterns = [
            r"(?:비밀|정체|진실|음모)[이가을를]\s*(?:밝혀|드러나|알게\s*되)",
            r"(?:수수께끼|의문|미스터리)[이가을를]?\s*(?:남|생겨|던져)",
            r"숨겨진\s*[가-힣]{2,6}[이가을를]?\s*(?:발견|알아)",
        ]
        mysteries = set()
        for p in mystery_patterns:
            for m in re.finditer(p, manuscript):
                mysteries.add(m.group(0)[:30])
        if mysteries:
            digest_parts.append(f"미스터리/복선: {', '.join(mysteries)}")

        # 9. [V63.2] 클리프행어 (마지막 200자에서 추출)
        ending = manuscript[-200:] if len(manuscript) > 200 else manuscript
        cliff_patterns = [
            r"(?:그\s*순간|갑자기|그때)[,\s]",
            r"눈[이가]\s*(?:커졌|번뜩|휘둥)",
            r"(?:불길한|섬뜩한|낯선)\s*(?:기운|예감|느낌)",
            r"(?:정체|그림자|인영)[이가]\s*(?:나타|드러|모습)",
        ]
        cliffhanger_found = False
        for p in cliff_patterns:
            if re.search(p, ending):
                cliffhanger_found = True
                break
        if cliffhanger_found:
            # 마지막 문장 추출
            last_sentences = re.split(r"[.!?]\s*", ending.strip())
            last_sentence = last_sentences[-1] if last_sentences else ""
            if last_sentence and len(last_sentence) > 5:
                digest_parts.append(f'클리프행어: "{last_sentence[:50]}"')

        if not digest_parts:
            return ""

        header = f"[제{ep_num}화 상태 다이제스트]" if ep_num > 0 else "[직전 화 상태 다이제스트]"
        return header + "\n" + "\n".join(f"- {p}" for p in digest_parts)

    def _detect_deaths_from_manuscript(self, prev_manuscript: str) -> list[str]:
        """
        [V60.81] 이전 원고에서 사망 NPC 탐지 (과거 침범 방지)

        ManuscriptValidator와 동일한 로직으로 사망 패턴 감지
        """
        if not prev_manuscript:
            return []

        detected_deaths = set()

        # 사망 패턴 정규식
        death_patterns = [
            r"([가-힣]{2,4})[이가은는]\s*(?:죽었다|사망했다|숨을\s*거두|최후를\s*맞|절명|운명했다|목숨을\s*잃)",
            r"([가-힣]{2,4})[의]\s*(?:시신|주검|유해|사체)",
            r"([가-힣]{2,4})[을를]\s*(?:죽였다|베었다|처단했다|살해했다)",
        ]

        for pattern in death_patterns:
            matches = re.findall(pattern, prev_manuscript)
            detected_deaths.update(matches)

        # 2글자 미만 이름 필터링
        return [name for name in detected_deaths if len(name) >= 2]

    def _detect_past_events_from_manuscript(self, prev_manuscript: str) -> dict:
        """
        [V60.81] 이전 원고에서 중요 과거 사건 탐지 (과거 침범 방지)

        부상, 아이템 획득/손실, 관계 변화 등 추적
        """
        if not prev_manuscript:
            return {"injuries": [], "items_gained": [], "items_lost": [], "relationship_changes": []}

        result = {"injuries": [], "items_gained": [], "items_lost": [], "relationship_changes": []}

        # 1. 부상 패턴 탐지
        injury_patterns = [
            r"([가-힣]+)[이가]\s*(중상|내상|부상|중독)[을를]?\s*(입|당)",
            r"(중상|내상|부상)[을를]\s*입",
        ]
        for pattern in injury_patterns:
            matches = re.findall(pattern, prev_manuscript)
            result["injuries"].extend([m[0] if isinstance(m, tuple) else m for m in matches])

        # 2. 아이템 획득 패턴
        gain_patterns = [
            r"([가-힣]{2,6})[을를]\s*(얻|획득|받|입수)",
            r"([가-힣]{2,6})[이가]\s*손에\s*들어",
        ]
        for pattern in gain_patterns:
            matches = re.findall(pattern, prev_manuscript)
            result["items_gained"].extend([m[0] if isinstance(m, tuple) else m for m in matches])

        # 3. 아이템 손실 패턴
        loss_patterns = [
            r"([가-힣]{2,6})[을를]\s*(잃|빼앗|분실|파괴)",
        ]
        for pattern in loss_patterns:
            matches = re.findall(pattern, prev_manuscript)
            result["items_lost"].extend([m[0] if isinstance(m, tuple) else m for m in matches])

        return result

    def _build_past_guard_section(self, prev_manuscript: str, existing_dead_npcs: list[str] = None) -> str:
        """
        [V60.81] 과거 침범 방지 섹션 구성

        이전 원고 분석 결과를 바탕으로 과거 사건 일관성 강제
        """
        sections = []
        existing_dead_npcs = existing_dead_npcs or []

        # 1. 추가 사망 NPC 탐지
        detected_deaths = self._detect_deaths_from_manuscript(prev_manuscript)
        all_dead_npcs = list(set(existing_dead_npcs + detected_deaths))

        if all_dead_npcs:
            dead_str = ", ".join(all_dead_npcs)  # [V66.1] 상한 제거 - 전체 사망 NPC 표시
            sections.append(f"""
### 🔒 [PAST CONSTRAINT] 사망 NPC - 절대 부활 금지
이미 사망한 인물: {dead_str}

⛔ 위 인물들이 현재 시점에서 대화/행동하면 REJECT
⛔ 회상 장면에서만 언급 가능 (과거형 필수)
⛔ "알고 보니 살아있었다" 전개 금지 (별도 복선 없이)
""")

        # 2. 과거 사건 탐지
        past_events = self._detect_past_events_from_manuscript(prev_manuscript)

        if past_events.get("injuries"):
            injuries = list(set(past_events["injuries"]))[:5]
            sections.append(f"""
### 🔒 [PAST CONSTRAINT] 이전 화 부상 상태
직전 화에서 발생한 부상: {", ".join(injuries)}

⛔ 치료 장면 없이 완치된 것처럼 행동하면 REJECT
⛔ 부상 상태는 전투/행동에 반드시 반영
""")

        if sections:
            return "\n".join(sections)
        else:
            return ""

    def _build_future_guard_section(
        self,
        current_inventory: list[str],
        current_martial_arts: list[str],
        dead_npcs: list[str],
        item_acquisition_timeline: str,
    ) -> str:
        """
        [V60.80 FIX] 미래 침범 방지 섹션 구성

        미래에 획득할 아이템/무공 사용 방지
        죽은 NPC 부활 방지
        """
        sections = []

        # 1. 현재 소지품 제약
        if current_inventory:
            inventory_str = ", ".join(current_inventory[:15])  # 최대 15개
            sections.append(f"""
### 🔒 [HARD CONSTRAINT] 소지품 제약
현재 주인공이 보유한 아이템:
→ {inventory_str}

⛔ 위 목록에 없는 아이템은 절대 사용/언급할 수 없습니다.
⛔ "나중에 얻을 아이템"을 미리 사용하면 즉시 REJECT됩니다.
""")
        else:
            sections.append("""
### 🔒 [HARD CONSTRAINT] 소지품 제약
현재 주인공 소지품: (정보 없음 - HUD 참조)
⛔ HUD에 명시된 장비/아이템만 사용하세요.
""")

        # 2. 현재 무공 제약
        if current_martial_arts:
            martial_str = ", ".join(current_martial_arts[:10])  # 최대 10개
            sections.append(f"""
### 🔒 [HARD CONSTRAINT] 무공 제약
현재 주인공이 습득한 무공:
→ {martial_str}

⛔ 위 목록에 없는 무공은 절대 사용/시전할 수 없습니다.
⛔ 아직 배우지 않은 비급/초식을 사용하면 즉시 REJECT됩니다.
""")

        # 3. 죽은 NPC 목록
        if dead_npcs:
            dead_str = ", ".join(dead_npcs)  # [V66.1] 상한 제거 - 전체 사망 NPC 표시
            sections.append(f"""
### 🔒 [HARD CONSTRAINT] 사망 NPC 목록
다음 인물들은 이미 사망했습니다:
→ {dead_str}

⛔ 위 인물들이 대화하거나 행동하면 즉시 REJECT됩니다.
⛔ 회상/과거 장면에서만 언급 가능합니다. (단, 현재 시점 행동 금지)
""")

        # 4. 아이템 획득 타임라인
        if item_acquisition_timeline:
            sections.append(f"""
### 📅 [참고] 아이템 획득 타임라인
{self._escape_braces(item_acquisition_timeline)}

⛔ 아직 획득하지 않은 아이템을 사용하면 REJECT됩니다.
""")

        if sections:
            return "\n".join(sections)
        else:
            return """
### 🔒 [HARD CONSTRAINT] 미래 침범 방지
⛔ HUD에 명시된 장비/무공만 사용하세요.
⛔ 아직 획득하지 않은 아이템/무공 사용 시 REJECT됩니다.
⛔ 죽은 NPC를 부활시키면 REJECT됩니다.
"""

    def regenerate_with_feedback(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str,
        director_feedback: str,
        previous_attempt: dict,
        attempt_number: int,
        # [V60.80 FIX] 미래 침범 방지용 추가 파라미터
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        # [V60.80+] 기존 Writer 핵심 기능
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        # [V60.81] 추가 파라미터
        npc_equipment_summary: str = "",
        intro_dna: str = "CYNICAL",
        # [V60.85] 장르 Guard Purism Prompt
        purism_prompt: str = "",
        # [V60.95] 고밀도 HUD 전달
        state_tracker=None,
        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_text: str = "",
        # [V68] 세계 상태 요약 — 장기연재 모순 방지
        world_state_summary: str = "",
        # [V68] 에피소드 연결고리 — 직전 화에서 이어받아야 할 것
        chain_link_section: str = "",
    ) -> list[dict]:
        """
        Director 피드백 반영 재생성

        Args:
            ... (기존 파라미터)
            director_feedback: Director의 구체적 피드백
            previous_attempt: 이전 시도 결과
            attempt_number: 현재 시도 번호 (2 또는 3)
            current_inventory: 현재 소지품 목록
            current_martial_arts: 현재 무공 목록
            dead_npcs: 죽은 NPC 목록
            item_acquisition_timeline: 아이템 획득 타임라인
            purism_prompt: 장르 Guard의 순혈주의 지침 (V60.85)
            prev_manuscripts_text: [V67] 이전 30화 원고 전문 (모순 방지용)
            world_state_summary: [V68] 세계 상태 요약 (장기연재 모순 방지)
            chain_link_section: [V68] 직전 화 연결고리 (다음 화에서 이어받을 것)

        Returns:
            List[Dict]: 새로운 3개 후보
        """
        # 피드백 강화
        enhanced_feedback = f"""
[🚨 {attempt_number}차 재시도 - Director 피드백 필수 반영]

{director_feedback}

[이전 시도 분석]
- 선택된 전략: {previous_attempt.get("strategy", "unknown")}
- 문제점: {previous_attempt.get("rejection_reason", "unknown")}

⚠️ 위 피드백을 100% 반영하지 않으면 다시 REJECT됩니다.
"""

        # 실패 학습 제약 구성
        failure_constraints = ""
        if previous_attempt.get("action_items"):
            items = previous_attempt.get("action_items", [])
            failure_constraints = "이전 REJECT 사유:\n" + "\n".join([f"- {item}" for item in items])

        return self.generate_ensemble(
            ep_num=ep_num,
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
            hud_report=hud_report,
            arc_doc=arc_doc,
            master_bible=master_bible,
            style_guide=style_guide,
            director_feedback=enhanced_feedback,
            failure_constraints=failure_constraints,
            # 미래 침범 방지 데이터 전달
            current_inventory=current_inventory,
            current_martial_arts=current_martial_arts,
            dead_npcs=dead_npcs,
            item_acquisition_timeline=item_acquisition_timeline,
            # 기존 Writer 핵심 기능
            reference_anchor_prompt=reference_anchor_prompt,
            mandatory_context=mandatory_context,
            anti_trope_prompt=anti_trope_prompt,
            justification_prompt=justification_prompt,
            reflexion_prompt=reflexion_prompt,
            genre_name=genre_name,
            # [V60.81] 추가 파라미터
            npc_equipment_summary=npc_equipment_summary,
            intro_dna=intro_dna,
            # [V60.85] 장르 Guard Purism Prompt
            purism_prompt=purism_prompt,
            # [V60.95] 고밀도 HUD 전달
            state_tracker=state_tracker,
            # [V67] 이전 원고 전문
            prev_manuscripts_text=prev_manuscripts_text,
            # [V68] 세계 상태 요약
            world_state_summary=world_state_summary,
            # [V68] 에피소드 연결고리
            chain_link_section=chain_link_section,
        )

    # =========================================================================
    # [V60.81] Writer 핵심 기능 통합 - Self-Critique & Quality Assurance
    # =========================================================================

    def _sanitize_leakage(self, text: str) -> str:
        """
        [V60.81] Writer 출력 누수(Leakage) 방지용 사후 필터

        미래 씬 정보, 메타데이터 등 원고에 포함되면 안 되는 정보 제거
        """
        if not text:
            return text

        # 1. JSON 구조적 정제 시도
        try:
            clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
            data = json.loads(clean_text)

            # 금지된 키 리스트 (누수 주범)
            banned_keys = [
                "Beat 3",
                "Beat 4",
                "continuation_text",
                "scene_summary",
                "future_hint",
                "next_episode",
                "spoiler",
            ]

            if isinstance(data, dict):
                for key in banned_keys:
                    if key in data:
                        del data[key]
                return json.dumps(data, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, ValueError) as e:
            logging.debug(f"[V66.3] ChiefWriter JSON 파싱 부분실패: {e}")

        # 2. 텍스트 라인 필터링 (비상 대책)
        filtered_lines = []
        for line in text.splitlines():
            if re.search(r'"(Beat \d+|continuation_text|future_hint)":', line):
                continue
            filtered_lines.append(line)

        text = "\n".join(filtered_lines)

        # 3. 영문 괄호 병기 제거: "윈도우(Windows)" → "윈도우"
        text = re.sub(r"([가-힣]+)\([A-Za-z][A-Za-z\s&\-\'\.,;:0-9]*\)", r"\1", text)

        return text

    def _apply_self_critique(
        self, manuscript: str, hud_report: str, npcs: list, genre_name: str, ep_num: int = None
    ) -> str:
        """
        [V60.81] Self-Critique 다중 라운드 적용

        원고에 Self-Critique를 최대 3회 반복 실행하고, 문제가 있으면 수정 후 반환

        Args:
            manuscript: 원고 (JSON 문자열)
            hud_report: HUD 정보
            npcs: NPC 리스트
            genre_name: 장르
            ep_num: 에피소드 번호

        Returns:
            str: 검토 및 수정된 원고
        """
        encyclopedia = {"npcs": npcs}
        MAX_CRITIQUE_ROUNDS = 3

        current_manuscript = manuscript
        total_issues_fixed = 0

        # [V60.82] 조기 스킵 조건 - Rubric 점수로 사전 평가
        rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
        if rubric_score >= 3.5:
            # 이미 품질 높음 - Self-Critique 스킵
            return current_manuscript

        for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
            critique_result = self._self_critique(current_manuscript, hud_report, encyclopedia, genre_name, ep_num)

            if not critique_result["has_issues"]:
                if round_num > 1:
                    logging.info(f"[ChiefWriter] Self-Critique R{round_num}: 완료 ({total_issues_fixed}건 수정)")
                break

            if critique_result["severity"] == "low":
                break

            # [V60.82] 라운드 중간 Rubric 체크 - 3.5 이상이면 조기 종료
            if round_num > 1:
                mid_score = self._evaluate_with_rubric(current_manuscript, genre_name)
                if mid_score >= 3.5:
                    break

            logging.info(
                f"[ChiefWriter] Self-Critique R{round_num}/{MAX_CRITIQUE_ROUNDS}: {len(critique_result['issues'])}건..."
            )
            current_manuscript = self._fix_manuscript_issues(current_manuscript, critique_result, hud_report)
            total_issues_fixed += len(critique_result["issues"])

        return current_manuscript

    def _self_critique(
        self, manuscript: str, hud_report: str, encyclopedia: dict, genre_name: str, ep_num: int = None
    ) -> dict:
        """
        [V60.81] Writer Self-Critic - 원고 자체 검토

        Returns:
            {
                "has_issues": bool,
                "issues": [...],
                "severity": "low" | "medium" | "high"
            }
        """
        # JSON 파싱
        try:
            data = json.loads(manuscript)
            content = data.get("content", "")
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
            content = manuscript

        issues = []

        # 1. HUD 모순 체크
        hud_issues = self._check_hud_consistency(content, hud_report)
        issues.extend(hud_issues)

        # 2. 클리셰 과다 체크
        cliche_issues = self._check_cliche_overuse(content, genre_name, ep_num)
        issues.extend(cliche_issues)

        # 3. 정당화 부족 체크
        justification_issues = self._check_justification_gaps(content, hud_report)
        issues.extend(justification_issues)

        # 4. NPC 관계 일관성 체크
        npc_issues = self._check_npc_relationship(content, encyclopedia)
        issues.extend(npc_issues)

        # 심각도 판단
        severity = "low"
        if len(issues) >= 3:
            severity = "high"
        elif len(issues) >= 1:
            severity = "medium"

        has_issues = len(issues) > 0

        return {"has_issues": has_issues, "issues": issues, "severity": severity}

    def _check_hud_consistency(self, content: str, hud_report: str) -> list:
        """HUD 모순 체크"""
        issues = []

        weak_keywords = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "빈사"]
        strong_actions = ["일격에", "압도", "박살", "분쇄", "제압", "일도양단"]

        is_weak = any(kw in hud_report for kw in weak_keywords)
        has_strong_action = any(kw in content for kw in strong_actions)

        if is_weak and has_strong_action:
            justification_kws = ["발경", "기혈", "폭발", "전생", "대가", "고통", "각오", "최후"]
            has_justification = any(kw in content for kw in justification_kws)

            if not has_justification:
                issues.append(
                    {
                        "type": "hud_contradiction",
                        "description": "나약한 상태에서 강력한 행동, 정당화 부족",
                        "location": "본문",
                        "severity": "medium",
                    }
                )

        return issues

    def _check_cliche_overuse(self, content: str, genre_name: str, ep_num: int = None) -> list:
        """클리셰 과다 사용 체크"""
        issues = []

        # 최근 빈도 체크
        if ep_num is not None and ep_num > 1:
            recent_counts = self._count_recent_cliches(ep_num, content, window=10)

            overused = [f"'{keyword}' ({count}회)" for keyword, count in recent_counts.items() if count >= 3]

            if overused:
                issues.append(
                    {
                        "type": "cliche_overuse_recent",
                        "description": f"최근 클리셰 과용: {', '.join(overused[:3])}",
                        "location": "최근 10화",
                        "severity": "medium",
                        "recommendation": "다른 표현으로 다양화 필요",
                    }
                )

        # 무협 클리셰 패턴
        if genre_name == "무협":
            cliche_patterns = [
                ("무시", "별 볼일"),
                ("무시", "평범해"),
                ("허름", "행색"),
                ("조롱", "비웃"),
            ]

            cliche_count = 0
            for pattern1, pattern2 in cliche_patterns:
                if pattern1 in content and pattern2 in content:
                    cliche_count += 1

            if cliche_count >= 2:
                issues.append(
                    {
                        "type": "cliche_overuse",
                        "description": f"무협 클리셰 패턴이 {cliche_count}회 반복",
                        "location": "본문",
                        "severity": "low",
                    }
                )

        return issues

    def _check_justification_gaps(self, content: str, hud_report: str) -> list:
        """정당화 누락 체크"""
        issues = []

        constraints = []
        if "나약" in hud_report or "중독" in hud_report:
            constraints.append("physical")
        if "reputation" in hud_report.lower():
            rep_match = re.search(r"reputation[:\s]+(\d+)", hud_report, re.IGNORECASE)
            if rep_match and int(rep_match.group(1)) < 30:
                constraints.append("authority")

        if "physical" in constraints:
            overcome_keywords = ["이루어", "성공", "압도", "제압"]
            has_overcome = any(kw in content for kw in overcome_keywords)

            if has_overcome:
                just_kws = ["때문에", "덕분에", "활용", "방법", "대가"]
                has_just = any(kw in content for kw in just_kws)

                if not has_just:
                    issues.append(
                        {
                            "type": "justification_gap",
                            "description": "제약 극복 장면에 정당화 표현 부족",
                            "location": "본문",
                            "severity": "medium",
                        }
                    )

        return issues

    def _check_npc_relationship(self, content: str, encyclopedia: dict) -> list:
        """NPC 관계 일관성 체크"""
        issues = []

        npcs = encyclopedia.get("npcs", [])

        for npc in npcs:
            if not isinstance(npc, dict):
                continue

            name = npc.get("name", "")
            if not name or name not in content:
                continue

            relationship = npc.get("relationship_state", "중립")

            # 경외 상태인데 무시 표현이 있는가?
            if relationship in ["경외", "충성", "존경"]:
                disrespect_keywords = ["무시", "비웃", "조롱", "업신여"]
                for kw in disrespect_keywords:
                    if kw in content:
                        # NPC가 주인공을 무시하는 맥락인지 확인
                        context_pattern = f"{name}.*{kw}|{kw}.*{name}"
                        if re.search(context_pattern, content):
                            issues.append(
                                {
                                    "type": "npc_relationship_inconsistency",
                                    "description": f"'{name}'은 경외 상태인데 무시/조롱 표현 사용",
                                    "location": "본문",
                                    "severity": "medium",
                                }
                            )
                            break

        return issues

    def _fix_manuscript_issues(self, manuscript: str, critique_result: dict, hud_report: str) -> str:
        """
        [V60.81] 감지된 문제 수정

        LLM을 사용하여 문제점을 수정한 새 원고 반환
        """
        issues = critique_result.get("issues", [])
        if not issues:
            return manuscript

        # 수정 지시 구성
        fix_instructions = []
        for issue in issues[:3]:  # 최대 3개만 수정
            fix_instructions.append(f"- {issue['type']}: {issue['description']}")

        # [V65] 교정 프롬프트 함수 래핑 호출
        prompt = get_fix_issues_prompt(
            fix_instructions_text=chr(10).join(fix_instructions),
            hud_report_escaped=self._escape_braces(hud_report[:500]),
            manuscript_escaped=self._escape_braces(manuscript[:8000]),
        )
        try:
            fixed = self.ask(prompt, temperature=0.5, thinking_level="low")
            fixed = self._sanitize_leakage(fixed)

            # JSON 유효성 검증
            try:
                json.loads(fixed)
                return fixed
            except (json.JSONDecodeError, ValueError, TypeError):
                return manuscript  # 파싱 실패시 원본 유지
        except Exception as e:
            logging.warning(f"⚠️ [ChiefWriter] 수정 실패: {e}")
            return manuscript

    def _evaluate_with_rubric(self, manuscript: str, genre_name: str) -> float:
        """
        [V60.81] Rubric 기반 품질 평가

        Returns:
            float: 품질 점수 (1.0 ~ 4.0)
        """
        try:
            data = json.loads(manuscript)
            content = data.get("content", "")
        except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
            content = manuscript

        if not content or len(content) < 100:
            return 1.0

        scores = []

        # 1. 감정 표현 평가 (Show vs Tell)
        direct_emotions = ["기뻤다", "슬펐다", "화났다", "놀랐다", "두려웠다", "경악했다", "분노했다"]
        direct_count = sum(content.count(e) for e in direct_emotions)
        chars_per_1000 = len(content) / 1000
        direct_rate = direct_count / max(chars_per_1000, 1)

        if direct_rate <= 0.5:
            scores.append(4)
        elif direct_rate <= 1.5:
            scores.append(3)
        elif direct_rate <= 3.0:
            scores.append(2)
        else:
            scores.append(1)

        # 2. 문장 시작 다양성
        sentences = [s.strip() for s in re.split(r"[.!?]", content) if len(s.strip()) > 5]
        if sentences:
            starters = [s[:2] for s in sentences[:20]]
            unique_rate = len(set(starters)) / max(len(starters), 1)
            if unique_rate >= 0.7:
                scores.append(4)
            elif unique_rate >= 0.5:
                scores.append(3)
            elif unique_rate >= 0.3:
                scores.append(2)
            else:
                scores.append(1)
        else:
            scores.append(2)

        # 3. 대화 자연스러움 (대화 비율)
        dialogue_matches = re.findall(r'["\'].*?["\']', content)
        dialogue_chars = sum(len(d) for d in dialogue_matches)
        dialogue_ratio = dialogue_chars / max(len(content), 1)

        if 0.15 <= dialogue_ratio <= 0.40:
            scores.append(4)
        elif 0.10 <= dialogue_ratio <= 0.50:
            scores.append(3)
        elif dialogue_ratio > 0:
            scores.append(2)
        else:
            scores.append(1)

        # 4. 오감 묘사 균형
        sensory_keywords = {
            "visual": ["보였다", "빛", "색", "어둠", "그림자"],
            "auditory": ["소리", "울림", "침묵", "들렸다", "속삭"],
            "tactile": ["차가", "뜨거", "거친", "부드러", "통증"],
            "olfactory": ["냄새", "향기", "악취", "피비린"],
        }
        sensory_counts = {k: sum(content.count(w) for w in words) for k, words in sensory_keywords.items()}
        active_senses = sum(1 for c in sensory_counts.values() if c > 0)

        if active_senses >= 3:
            scores.append(4)
        elif active_senses >= 2:
            scores.append(3)
        elif active_senses >= 1:
            scores.append(2)
        else:
            scores.append(1)

        avg_score = sum(scores) / len(scores) if scores else 2.0
        return round(avg_score, 1)

    # =========================================================================
    # [V60.82] DB 배치 캐시 - 중복 쿼리 제거
    # =========================================================================

    def _prefetch_manuscripts(self, ep_num: int, window: int = 10) -> None:
        """
        [V60.82] 최근 N화 원고를 한 번에 로드하여 캐시

        이후 _get_npc_frequency, _count_recent_cliches, _check_hud_anomalies에서
        DB 직접 조회 대신 캐시 사용
        """
        # 이미 같은 에피소드에 대해 캐시됨
        if self._cache_ep_num == ep_num and self._manuscript_cache:
            return

        self._manuscript_cache = {}
        self._cache_ep_num = ep_num

        try:
            for i in range(max(1, ep_num - window), ep_num):
                try:
                    past_ms = self.context.db.get_manuscript(i)
                    if past_ms:
                        content = past_ms.get("content", "") if isinstance(past_ms, dict) else str(past_ms)
                        # [V70] NOTE: manuscripts 테이블에 hud_snapshot 컬럼 없음 — 항상 {} 반환 (dead code)
                        hud_snapshot = past_ms.get("hud_snapshot", {}) if isinstance(past_ms, dict) else {}
                        self._manuscript_cache[i] = {"content": content, "hud_snapshot": hud_snapshot}
                except (KeyError, TypeError, AttributeError) as e:  # [V64.P4] individual ms load failure
                    continue
        except Exception as e:  # [V64.P4] IMPORTANT: manuscript cache build failure affects continuity checks
            logging.warning(f"⚠️ [V64.P4] 원고 캐시 구축 실패: {str(e)[:60]}")

    def _get_cached_manuscript(self, ep_num: int) -> dict:
        """[V60.82] 캐시에서 원고 조회"""
        return self._manuscript_cache.get(ep_num, {"content": "", "hud_snapshot": {}})

    # =========================================================================
    # [V60.81] NPC/HUD 추적 기능
    # =========================================================================

    def _get_npc_frequency(self, ep_num: int, window: int = 10) -> dict:
        """
        최근 N화에서 주요 NPC 등장 횟수 추적

        Returns:
            dict: {"연홍": 8, "화산장로": 2, ...}
        """
        try:
            master_bible = getattr(self.context, "master_bible", None)
            if not master_bible:
                return {}

            bible_root = master_bible.get("MasterBible", master_bible)
            assets = bible_root.get("AssetLibrary", {})
            key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])

            if not key_npcs:
                return {}

            npc_names = [npc.get("name", "") for npc in key_npcs if isinstance(npc, dict) and npc.get("name")]
            frequency = {name: 0 for name in npc_names}

            # [V60.82] 캐시 사용 (DB 직접 조회 대신)
            for i in range(max(1, ep_num - window), ep_num):
                cached = self._get_cached_manuscript(i)
                content = cached.get("content", "")
                if content:
                    for name in npc_names:
                        if name in content:
                            frequency[name] += 1

            return frequency
        except (AttributeError, KeyError, TypeError):  # [V64.P4] OPTIONAL: NPC frequency tracking
            return {}

    def _get_npc_frequency_warning(self, ep_num: int) -> str:
        """
        NPC 등장 빈도 경고 메시지 생성
        """
        if ep_num < 2:
            return "초반부 - NPC 빈도 추적 없음"

        try:
            npc_freq = self._get_npc_frequency(ep_num, window=10)

            if not npc_freq:
                return "주요 NPC 정보 없음"

            warnings = []
            for name, count in npc_freq.items():
                if count == 0:
                    warnings.append(f"⚠️ {name}: 최근 10화 미등장 → 관계 유지 고려")
                elif count >= 7:
                    warnings.append(f"✅ {name}: 최근 {count}회 등장 → 주연급 일관성 유지")

            if warnings:
                return "\n".join(warnings)
            else:
                return "모든 주요 NPC 적정 빈도 유지 중"

        except (AttributeError, KeyError, TypeError):  # [V64.P4] OPTIONAL: NPC frequency warning
            return "빈도 추적 실패"

    def _count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> dict:
        """
        최근 N화에서 클리셰 빈도 카운트
        """
        cliche_keywords = [
            "피를 토하",
            "기세",
            "살기",
            "냉기",
            "검기",
            "압도",
            "전율",
            "경악",
            "창백",
            "경외",
            "무시",
            "조롱",
            "비웃",
            "허름",
        ]

        counts = {keyword: 0 for keyword in cliche_keywords}

        # [V60.82] 캐시 사용 (DB 직접 조회 대신)
        for i in range(max(1, ep_num - window), ep_num):
            cached = self._get_cached_manuscript(i)
            content = cached.get("content", "")
            if content:
                for keyword in cliche_keywords:
                    counts[keyword] += content.count(keyword)

        # 현재 원고도 체크
        for keyword in cliche_keywords:
            counts[keyword] += manuscript.count(keyword)

        return {k: v for k, v in counts.items() if v > 0}

    def _get_hud_trend_safe(self, ep_num: int) -> str:
        """[V64.P4] 위임 → modules.core.hud_utils.get_hud_trend_safe"""
        return _get_hud_trend_safe_shared(self.context, ep_num)

    def _extract_numeric_value(self, value) -> int:
        """HUD 값에서 숫자 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            match = re.search(r"[+-]?\d+", value)
            if match:
                return int(match.group())
        return 0

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """[V64 P2-7] 위임 → modules.core.hud_utils.build_hud_context (writer variant)"""
        return _build_hud_context_shared(state_tracker, ep_num, variant="writer")

    def _check_hud_anomalies(self, current_ep: int) -> dict:
        """
        [V60.81] HUD 급변 감지 - 내공/경지/부상 상태의 급격한 변화 탐지

        Returns:
            {
                'has_anomalies': bool,
                'anomalies': [...],
                'warning_text': str
            }
        """
        anomalies = []

        if current_ep < 2:
            return {"has_anomalies": False, "anomalies": [], "warning_text": ""}

        try:
            # [V60.82] 캐시 사용 (DB 직접 조회 대신)
            hud_history = []
            for ep in range(max(1, current_ep - 3), current_ep):
                cached = self._get_cached_manuscript(ep)
                hud_snapshot = cached.get("hud_snapshot", {})
                if hud_snapshot:
                    hud_history.append({"ep": ep, "hud": hud_snapshot})

            if not hud_history:
                return {"has_anomalies": False, "anomalies": [], "warning_text": ""}

            latest = hud_history[-1]["hud"] if hud_history else {}

            # 1. 내공 급변 감지
            if len(hud_history) >= 2:
                prev_hud = hud_history[-2]["hud"]

                curr_energy = self._extract_numeric_value(latest.get("internal_energy", 0))
                prev_energy = self._extract_numeric_value(prev_hud.get("internal_energy", 0))

                if curr_energy - prev_energy > 500:
                    anomalies.append(
                        {
                            "type": "내공 급상승",
                            "description": f"직전 화 대비 내공 +{curr_energy - prev_energy} 증가",
                            "recommendation": "점진적 성장 또는 특별한 기연으로 정당화 필요",
                            "severity": "high",
                        }
                    )
                elif curr_energy - prev_energy > 200:
                    anomalies.append(
                        {
                            "type": "내공 빠른 성장",
                            "description": f"직전 화 대비 내공 +{curr_energy - prev_energy} 증가",
                            "recommendation": "수련/깨달음 장면으로 정당화 권장",
                            "severity": "medium",
                        }
                    )

                # 2. 경지 급변 감지
                curr_realm = latest.get("realm", "")
                prev_realm = prev_hud.get("realm", "")

                realm_tiers = ["하수", "삼류", "이류", "일류", "초일류", "절정", "화경", "현경", "귀환"]

                if curr_realm and prev_realm and curr_realm != prev_realm:
                    try:
                        curr_tier = realm_tiers.index(curr_realm) if curr_realm in realm_tiers else -1
                        prev_tier = realm_tiers.index(prev_realm) if prev_realm in realm_tiers else -1

                        if curr_tier - prev_tier >= 2:
                            anomalies.append(
                                {
                                    "type": "경지 급상승",
                                    "description": f"직전 화 대비 경지 2단계 이상 상승 ({prev_realm} → {curr_realm})",
                                    "recommendation": "연속 돌파 장면 또는 특수 기연으로 정당화 필수",
                                    "severity": "critical",
                                }
                            )
                    except ValueError:
                        pass

                # 3. 부상 상태 급변 감지
                curr_injury = str(latest.get("causal_injuries", "")).lower()
                prev_injury = str(prev_hud.get("causal_injuries", "")).lower()

                injury_levels = {"정상": 0, "경상": 1, "중상": 2, "중독": 2, "내상": 2, "빈사": 3, "치명상": 3}

                curr_level = 0
                prev_level = 0
                for injury_name, level in injury_levels.items():
                    if injury_name in curr_injury:
                        curr_level = max(curr_level, level)
                    if injury_name in prev_injury:
                        prev_level = max(prev_level, level)

                if prev_level >= 2 and curr_level == 0:
                    anomalies.append(
                        {
                            "type": "부상 급회복",
                            "description": "직전 화 심각한 부상 → 갑자기 완치",
                            "recommendation": "치료 과정 명시적 묘사 필요",
                            "severity": "high",
                        }
                    )

        except Exception as e:
            return {"has_anomalies": False, "anomalies": [], "error": str(e), "warning_text": ""}

        # 경고 텍스트 생성
        warning_text = ""
        if anomalies:
            warning_parts = ["🚨 [HUD 급변 감지]"]
            for a in anomalies:
                warning_parts.append(f"⚠️ {a['type']}: {a['description']}")
                warning_parts.append(f"   → {a['recommendation']}")
            warning_text = "\n".join(warning_parts)

        return {"has_anomalies": len(anomalies) > 0, "anomalies": anomalies, "warning_text": warning_text}

    def _get_npc_equipment_summary(self, master_bible: dict) -> str:
        """
        [V60.81] NPC 장비 현황 추출

        Returns:
            str: NPC 장비 요약 문자열
        """
        try:
            bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
            assets = bible_root.get("AssetLibrary", {})
            key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])

            npc_equipment_summary = []
            for npc in key_npcs:
                if isinstance(npc, dict):
                    npc_name = npc.get("name") or npc.get("Name", "알 수 없음")
                    npc_hud = npc.get("NPC_Martial_HUD", {})
                    if isinstance(npc_hud, dict):
                        equip = npc_hud.get("equipment", [])
                        if equip:
                            npc_equipment_summary.append(f"- {npc_name}: {equip}")

            if npc_equipment_summary:
                return "\n".join(npc_equipment_summary)
            else:
                return "NPC 장비 정보 없음"
        except (AttributeError, KeyError, TypeError):  # [V64.P4] OPTIONAL: NPC equipment
            return "NPC 장비 정보 로드 실패"

    # =========================================================================
    # [V60.81] DNA 모드 & 1화 특수 처리
    # =========================================================================

    def _get_dna_instruction(self, ep_num: int, intro_dna: str = "CYNICAL") -> str:
        """
        [V60.81] DNA 모드 지시문 생성

        1화는 특수 DNA 적용, 2화부터는 연속성 모드
        """
        if int(ep_num) == 1:
            return f"""
[제1화 특수 DNA 적용]: {intro_dna}
- 주인공의 핵심 동기와 세계관 기초 확립
- 강렬한 첫인상과 핵심 갈등 제시
- 독자 몰입을 위한 훅(Hook) 장면 필수
"""
        else:
            return """
[연속 집필 모드]: 이전 화의 마침표에서 단 1초의 공백 없이 사건을 전진시켜라.
- 직전 화 마지막 장면에서 자연스럽게 연결
- 시간 점프 시 명시적 전환문 필수
"""

    # =========================================================================
    # [V60.81] Context Building (Writer 통합) - 독립 실행용
    # =========================================================================

    def _build_anti_trope_instructions(self, genre_name: str) -> str:
        """
        [V60.81] 반클리셰 명령 생성

        ChiefWriter가 독립적으로 동작할 수 있도록 내장
        [V65] 프롬프트 본문 함수 래핑 호출
        """
        return get_anti_trope_instructions(genre_name=genre_name)

    def _build_mandatory_context(self, current_ep: int) -> str:
        """
        [V60.81] 강제 맥락 주입 - 최근 사건/NPC 상태/HUD 급변 포함

        ChiefWriter가 독립적으로 동작할 수 있도록 내장
        """
        mandatory_parts = ["[MANDATORY CONTEXT - 반드시 인지하고 집필할 것]\n"]

        # HUD 급변 감지
        hud_anomalies = self._check_hud_anomalies(current_ep)
        if hud_anomalies.get("has_anomalies"):
            mandatory_parts.append("\n[HUD ANOMALY WARNING - 급변 감지]\n")
            for anomaly in hud_anomalies.get("anomalies", []):
                mandatory_parts.append(f"- {anomaly['type']}: {anomaly['description']}")
                mandatory_parts.append(f"  -> 권장: {anomaly['recommendation']}\n")

        # 최근 사건 추출
        recent_events = self._extract_recent_events(current_ep, n_episodes=3)

        if recent_events:
            mandatory_parts.append("\n최근 중요 사건 (절대 무시 금지):")
            for event in recent_events:
                mandatory_parts.append(f"- 제{event['ep_num']}화: {event['description']}")
                if event.get("consequence"):
                    mandatory_parts.append(f"  현재 상태: {event['consequence']}")
                mandatory_parts.append("  -> 이 사실을 무시하면 논리 모순 발생\n")

        # NPC 상태 추출
        npc_states = self._extract_npc_last_states(current_ep)

        if npc_states:
            mandatory_parts.append("\nNPC 마지막 관계 상태 (일관성 유지 필수):")
            for npc_name, state_info in npc_states.items():
                mandatory_parts.append(f"- {npc_name}: {state_info['relationship']} (제{state_info['last_ep']}화)")
                mandatory_parts.append("  -> 이 관계가 변경되려면 명시적 사건 필요\n")

        if len(mandatory_parts) == 1:
            mandatory_parts.append("\n(첫 에피소드이거나 강제 맥락 없음)")

        return "\n".join(mandatory_parts)

    def _extract_recent_events(self, current_ep: int, n_episodes: int = 3) -> list:
        """최근 N화의 핵심 사건 추출"""
        events = []

        try:
            for ep in range(max(1, current_ep - n_episodes), current_ep):
                log_data = self.context.db.load_state_log(ep)

                if log_data and isinstance(log_data, dict):
                    summary = log_data.get("summary", "")
                    if summary and len(summary) > 10:
                        events.append({"ep_num": ep, "description": summary[:200], "consequence": ""})

                    data = log_data.get("data", {})
                    if isinstance(data, dict):
                        major_changes = data.get("major_changes", [])
                        if major_changes:
                            for change in major_changes[:2]:
                                if isinstance(change, dict):
                                    events.append(
                                        {
                                            "ep_num": ep,
                                            "description": change.get("event", ""),
                                            "consequence": change.get("consequence", ""),
                                        }
                                    )
        except (AttributeError, KeyError, TypeError) as e:  # [V64.P4] IMPORTANT: plot event extraction
            logging.warning(f"⚠️ [V64.P4] 플롯 이벤트 추출 실패: {str(e)[:60]}")

        return events[-5:] if events else []

    def _extract_npc_last_states(self, current_ep: int) -> dict:
        """등장 NPC의 마지막 상태 추출"""
        npc_states = {}

        try:
            bible = getattr(self.context, "master_bible", {})
            bible_root = bible.get("MasterBible", bible)
            assets = bible_root.get("AssetLibrary", {})
            key_npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])

            for npc in key_npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get("name") or npc.get("Name", "")
                if not name:
                    continue

                relationship = npc.get("relationship_state", "중립")
                last_appearance = npc.get("last_appearance_ep", 0)

                if isinstance(last_appearance, int) and 0 < last_appearance < current_ep:
                    npc_states[name] = {"relationship": relationship, "last_ep": last_appearance}
        except (AttributeError, KeyError, TypeError) as e:  # [V64.P4] IMPORTANT: NPC state extraction
            logging.warning(f"⚠️ [V64.P4] NPC 상태 추출 실패: {str(e)[:60]}")

        return npc_states

    def _build_justification_guidance(self, hud_report: str, genre_name: str) -> str:
        """
        [V60.81] 정당화 패턴 가이드 생성

        현재 HUD 상태를 분석하여 제약 조건을 파악하고,
        해당 제약을 극복할 때 필요한 정당화 패턴을 제시
        """
        guidance_parts = ["[JUSTIFICATION PATTERNS - 제약 극복 시 필수 참고]\n"]
        active_constraints = []

        hud_lower = hud_report.lower()

        # 1. 신체 제약 감지
        physical_constraints = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "기혈역류"]
        if any(constraint in hud_report for constraint in physical_constraints):
            active_constraints.append("physical")
            guidance_parts.append("\n[신체 제약 감지] 현재 주인공은 신체적 약점이 있습니다.")
            guidance_parts.append("강력한 행동 시 반드시 정당화 필요:")
            guidance_parts.append("- 발경/내력 폭발 (대가: 내상)")
            guidance_parts.append("- 특수 환단 복용 (대가: 후유증)")
            guidance_parts.append("- 의지력 각성 (대가: 기절/혼절)")

        # 2. 지위 제약 감지
        low_status_keywords = ["하인", "노예", "평민", "무명", "낭인", "거지", "천민"]
        if any(keyword in hud_report for keyword in low_status_keywords):
            active_constraints.append("authority")
            guidance_parts.append("\n[지위 제약 감지] 현재 주인공은 낮은 명성/지위입니다.")
            guidance_parts.append("명령/지시 행위 시 반드시 정당화 필요:")
            guidance_parts.append("- 신분 증명 (증표, 신물)")
            guidance_parts.append("- 실력 과시 (무력 시위)")
            guidance_parts.append("- 제3자 보증 (귀인의 추천)")

        # 3. 능력 급상승 가능성
        breakthrough_keywords = ["돌파", "깨달음", "체득", "각성", "각오"]
        if any(keyword in hud_report for keyword in breakthrough_keywords):
            active_constraints.append("power_up")
            guidance_parts.append("\n[능력 상승 가능성] 경지 돌파 시 반드시 정당화 필요:")
            guidance_parts.append("- 깨달음의 계기 명시 (사부의 가르침, 생사의 기로)")
            guidance_parts.append("- 체득 과정 묘사 (고통, 황홀경)")
            guidance_parts.append("- 부작용 언급 (기혈 불안정, 적응 기간)")

        if not active_constraints:
            return ""

        guidance_parts.append("\n")
        guidance_parts.append("중요: 위 패턴은 '영감의 원천'입니다.")
        guidance_parts.append("논리 구조를 참고하여 당신만의 창의적인 정당화를 만드십시오.")

        return "\n".join(guidance_parts)

    # [V65] Dead Code 삭제: _self_refine (-85줄), EMOTION_STATES/GENRE_EMOTION_PATTERNS/
    # generate_emotion_skeleton/_analyze_scene_types/build_emotion_prompt_injection/
    # auto_map_emotions_to_manuscript/get_emotion_skeleton_lazy (-320줄),
    # quick_self_check/self_review_and_refine (-197줄)
