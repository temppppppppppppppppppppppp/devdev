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
import re
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, List, Optional, Tuple
from .base_agent import BaseAgent

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_guard, get_primitive_constraint_section
    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


class ChiefWriter(BaseAgent):
    """
    [V60.80] Chief Writer - 앙상블 원고 생성 엔진

    특징:
    - 3개 후보 병렬 생성 (균형/서사/긴장감)
    - CoT (Chain of Thought) 기반 전략적 집필
    - Director 피드백 반영 재생성
    """

    # [V61.3] 앙상블 타임아웃 설정 (야간 무인 운영 - 무한 대기 방지)
    ENSEMBLE_TIMEOUT = 600       # 전체 앙상블 타임아웃 (초) - 10분 (thinking 오버헤드 반영)
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
"""
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
"""
        },
        "tension": {
            "name": "긴장감 강조",
            "temperature": 0.75,
            "emphasis": "액션 + 클리프행어 강화",
            "instruction": """
[전략 C: 긴장감 강조]
- 액션/전투 씬 밀도 강화
- 서스펜스와 긴장감 극대화
- 강렬한 클리프행어 엔딩
- ⚠️ 반드시 5,000자 이상 작성. 액션 묘사와 긴장 고조를 충분히 전개할 것
"""
        }
    }

    # [V60.82] 프롬프트 템플릿 상수 (프리컴파일)
    PROMPT_TEMPLATE_OUTPUT = """
### 📌 출력 형식 (Strict JSON)
{{
    "title": "에피소드 제목 (한글만)",
    "content": "5,000자 이상의 소설 본문 (줄바꿈은 \\n)",
    "state_updates": {{
        "internal_energy": "현재 내공 % (0-100)",
        "realm": "경지명 또는 현상 유지",
        "causal_injuries": "부상 상태",
        "wealth": "현재 총 자산",
        "misunderstanding": 0-100,
        "obsession": 0-100,
        "equipment": ["소지품 목록"],
        "martial_arts": ["무공 목록"]
    }},
    "writing_strategy": "{strategy}",
    "key_scenes_covered": ["반영한 씬 목록"]
}}
"""

    def __init__(self, context, client, model_tier="gemini-3-pro-preview"):
        super().__init__(context, client, model_tier)
        self._agent_name = "ChiefWriter"
        # [V60.82] 배치 캐시 - DB 쿼리 최적화
        self._manuscript_cache = {}  # {ep_num: content}
        self._cache_ep_num = -1  # 캐시 유효성 기준
        # [V60.82] 감정 스켈레톤 지연 로딩
        self._emotion_skeleton_cache = None
        self._emotion_skeleton_blueprint_hash = None

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
        current_inventory: List[str] = None,
        current_martial_arts: List[str] = None,
        dead_npcs: List[str] = None,
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
        state_tracker=None
    ) -> List[Dict]:
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
            state_tracker=state_tracker
        )

        # [V61.7] 컨텍스트 캐싱 시도 (토큰 비용 50-67% 절감)
        cache_name = None
        try:
            cache_info = self._get_or_create_context_cache(
                cache_type="manuscript",
                content=common_context,
                ttl_seconds=600,  # 10분 (같은 에피소드 재시도 대비)
                project_name=f"ep{ep_num}"
            )
            cache_name = cache_info.get("cache_name")
            if cache_name:
                print(f"      📦 [V61.7] 컨텍스트 캐시 활성 (ep{ep_num}, {len(common_context)}자)")
        except Exception:
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
                        cache_name=cache_name
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
                                print(f"      ✅ [ChiefWriter] 후보 {strategy} 생성 완료 ({len(result.get('manuscript', ''))}자)")
                        except FutureTimeoutError:
                            print(f"      ⏰ [V61.3] 후보 {strategy} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")
                            candidates.append({
                                "strategy": strategy,
                                "manuscript": "",
                                "title": "",
                                "state_updates": {},
                                "metadata": {"error": "타임아웃"},
                                "error": True
                            })
                        except Exception as e:
                            print(f"      ⚠️ [ChiefWriter] 후보 {strategy} 생성 실패: {str(e)[:50]}")
                            # 실패한 전략은 빈 결과로 대체
                            candidates.append({
                                "strategy": strategy,
                                "manuscript": "",
                                "title": "",
                                "state_updates": {},
                                "metadata": {"error": str(e)},
                                "error": True
                            })
                except FutureTimeoutError:
                    # 전체 앙상블 타임아웃 - 완료된 후보만 사용
                    print(f"      ⏰ [V61.3] 원고 앙상블 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용")
                except Exception as e:
                    # [V61.3] as_completed 자체 예외 처리
                    print(f"      ⚠️ [V61.3] 원고 앙상블 루프 예외: {str(e)[:80]}")
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
            print("      🚨 [ChiefWriter] 모든 후보 생성 실패 - 단일 재시도")
            fallback = self._generate_single_candidate(
                ep_num=ep_num,
                strategy="balanced",
                common_context=common_context,
                hud_report=hud_report,
                master_bible=master_bible,
                genre_name=genre_name,
                cache_name=cache_name
            )
            if fallback:
                candidates = [fallback]

        return candidates

    def _generate_single_candidate(
        self,
        ep_num: int,
        strategy: str,
        common_context: str,
        hud_report: str = "",
        master_bible: dict = None,
        genre_name: str = "무협",
        cache_name: str = None
    ) -> Optional[Dict]:
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
                    full_prompt_fallback=full_prompt
                )
            else:
                # [V60.82] 기존 방식: 전체 프롬프트
                full_prompt = f"""{common_context}

{strategy_config["instruction"]}

{self.PROMPT_TEMPLATE_OUTPUT.format(strategy=strategy)}"""

                response = self.ask(
                    prompt=full_prompt,
                    temperature=strategy_config["temperature"],
                    thinking_level="medium"  # [V61.6] 원고 생성 추론 강화
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
                bible_root = master_bible.get('MasterBible', master_bible) if isinstance(master_bible, dict) else {}
                assets = bible_root.get('AssetLibrary', {})
                npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            critiqued_manuscript = self._apply_self_critique(
                manuscript=manuscript_json,
                hud_report=hud_report,
                npcs=npcs,
                genre_name=genre_name,
                ep_num=ep_num
            )

            # Self-Critique 결과에서 content 재추출
            try:
                critiqued_data = json.loads(critiqued_manuscript)
                final_content = critiqued_data.get("content", manuscript_content)
                final_title = critiqued_data.get("title", data.get("title", f"제{ep_num}화"))
                final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))
            except Exception:
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
                    "self_critique_applied": True
                }
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
        current_inventory: List[str] = None,
        current_martial_arts: List[str] = None,
        dead_npcs: List[str] = None,
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
        state_tracker=None
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
        bible_root = master_bible.get('MasterBible', master_bible) if isinstance(master_bible, dict) else {}
        core_identity = bible_root.get('ProjectData', {}).get('CoreIdentity', {})
        assets = bible_root.get('AssetLibrary', {})

        # [V60.95] 주인공 설정 추출 (원시인/현대인 제약)
        protagonist_config = bible_root.get('protagonist_config', {})
        world_origin = protagonist_config.get('world_origin', '원시인')
        incarnation_type = protagonist_config.get('incarnation_type', '회귀자')

        # [V60.96] 장르 코드 변환 (장르별 금지어 적용)
        genre_code_map = {"무협": "wuxia", "판타지": "fantasy", "헌터물": "hunter", "투자물": "investment", "배우물": "actor", "스포츠": "sports", "의학": "medical", "요리": "cooking", "작곡가": "composer", "대체역사": "alt_history"}
        genre_code = genre_code_map.get(genre_name, bible_root.get('_genre', 'wuxia'))

        # [V60.96] 원시인 모드 제약 섹션 (장르별 JSON 기반 PrimitiveGuard)
        world_origin_constraint_section = ""
        if world_origin == '원시인':
            if PRIMITIVE_GUARD_AVAILABLE:
                # 장르별 JSON 기반 동적 생성
                world_origin_constraint_section = get_primitive_constraint_section(
                    protagonist_config, genre=genre_code, length="build"
                )
            else:
                # 폴백: 최소한의 경고
                world_origin_constraint_section = """
### 🚨 [원시인 모드] 현대 용어 절대 금지!
❌ 금지: 헬스장, 바벨, 병원, 학교, 시스템, 스트레스, 축구, 자동차
✅ 대체: 무관, 석추, 의원, 서당, 체계, 심기, 격구, 마차
⚠️ 회귀자라도 현대 용어 사용 불가!
"""
        elif world_origin == '현대인':
            world_origin_constraint_section = """
### ✅ [현대인 모드] 현대 지식 활용 가능
주인공은 현대 세계 출신으로 현대 지식을 내적 독백에서 활용 가능합니다.
단, 대화에서 현대 용어 남발은 자제하고 세계관에 맞게 표현하세요.
"""

        # 직전 원고 엔딩 (마지막 1500자)
        prev_ending = prev_manuscript[-1500:] if prev_manuscript else ""

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
            item_acquisition_timeline=item_acquisition_timeline
        )

        # [V60.81] 과거 침범 방지 섹션
        past_guard_section = self._build_past_guard_section(
            prev_manuscript=prev_manuscript,
            existing_dead_npcs=dead_npcs
        )

        # [V60.80+] 기존 Writer 핵심 기능 섹션 조립
        writer_core_section = ""
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
        if hud_anomalies.get('has_anomalies') and hud_anomalies.get('warning_text'):
            hud_anomaly_section = f"""
{hud_anomalies['warning_text']}
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

        return f"""
[Role] 웹소설 1타 작가 (Chief Writer)
[Task] 제{ep_num}화 원고를 Blueprint 기반으로 집필하라.

### 핵심 철학
"Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

{dna_instruction}

{purism_section}

{world_origin_constraint_section}

{feedback_section}
{constraint_section}

{future_guard_section}

{past_guard_section}

{writer_core_section}

{hud_anomaly_section}

### 📋 [STEP 1: Blueprint 분석]
아래 Blueprint의 모든 씬을 파악하고, 누락 없이 반영하라.

{self._escape_braces(scene_breakdown)}

### 📋 [STEP 2: 연속성 확인]
직전 화 엔딩에서 자연스럽게 이어져야 한다.

[직전 화 마지막 장면]
...{self._escape_braces(prev_ending)}

### 📋 [STEP 3: 현재 상태 반영]
{self._escape_braces(hud_report)}

{high_density_hud_section}

{hud_trend_section}

⚠️ 필수 준수:
- 현재 경지/내공 범위 내에서만 무공 사용
- 부상 상태는 전투/행동에 반영
- 소지품/자금 상태 일관성 유지

{npc_equipment_section}

{npc_frequency_section}

### 📋 [STEP 4: Arc 전술 참조]
{self._escape_braces(arc_doc) if arc_doc else "특이사항 없음"}

### 📋 [STEP 5: 세계관 설정]
- 주인공 동기: {self._escape_braces(str(core_identity.get('desire', '')))}

### 📋 [STEP 6: 문체 DNA 가이드 - 위반 시 AI티 판정]
{self._escape_braces(style_guide) if style_guide else "기본 웹소설 문체"}

### 🔥 변환 원칙 (Common Rules) - 위반 시 AI티 판정
1. 감정어 삭제 → 행동 변환: '화가 났다', '슬펐다', '당황했다' 같은 추상적 감정 단어를 금지한다. 대신 미세한 표정 변화, 손짓, 호흡, 시선 처리, 주변 사물과의 상호작용으로 감정을 유추하게 만들어라. (예: "그는 초조해했다" → "그는 마른입술을 혀로 훑으며 펜을 톡, 톡, 책상에 두드렸다.")
2. 감각적 묘사 강화 (오감 활용): 상황을 설명하지 말고, 독자가 그 현장에 있는 것처럼 느끼게 해라. 소리(청각), 냄새(후각), 질감(촉각)을 문장에 녹여내라.
3. 요약된 대화의 장면화: "그들은 협상에 대해 길게 논쟁했다"처럼 요약된 서술을 금지한다. 날 선 티키타카(대화)가 오가는 실제 장면으로 풀어 써라.
4. 문장 밀도 조절: 무의미한 미사여구로 문장 길이를 늘리지 마라. 불필요한 접속사와 수식어는 쳐내고, '동사(Action)' 위주로 문장을 짧고 힘 있게 끊어쳐라.

### 📌 집필 지침 (위반 시 즉시 REJECT)
1. ⚠️ 분량: 반드시 5,000자 이상. 4,999자 이하는 무조건 REJECT. 부족하면 장면 묘사, 인물 심리, 대화를 확장하라
2. 모든 씬을 균등한 비중으로 전개 - 각 씬 최소 1,000자 이상
3. 후반부 급전개/요약 절대 금지 - 마지막 씬도 앞 씬과 동일한 밀도로 작성
4. 클리프행어 엔딩 필수
5. 죽은 NPC 부활, 미습득 무공 사용 절대 금지
6. 영문 병기 금지 - "윈도우(Windows)", "검(Sword)" 같은 한글(English) 표기 금지. 한글만 사용
"""

    def _detect_deaths_from_manuscript(self, prev_manuscript: str) -> List[str]:
        """
        [V60.81] 이전 원고에서 사망 NPC 탐지 (과거 침범 방지)

        ManuscriptValidator와 동일한 로직으로 사망 패턴 감지
        """
        if not prev_manuscript:
            return []

        detected_deaths = set()

        # 사망 패턴 정규식
        death_patterns = [
            r'([가-힣]{2,4})[이가은는]\s*(?:죽었다|사망했다|숨을\s*거두|최후를\s*맞|절명|운명했다|목숨을\s*잃)',
            r'([가-힣]{2,4})[의]\s*(?:시신|주검|유해|사체)',
            r'([가-힣]{2,4})[을를]\s*(?:죽였다|베었다|처단했다|살해했다)',
        ]

        for pattern in death_patterns:
            matches = re.findall(pattern, prev_manuscript)
            detected_deaths.update(matches)

        # 2글자 미만 이름 필터링
        return [name for name in detected_deaths if len(name) >= 2]

    def _detect_past_events_from_manuscript(self, prev_manuscript: str) -> Dict:
        """
        [V60.81] 이전 원고에서 중요 과거 사건 탐지 (과거 침범 방지)

        부상, 아이템 획득/손실, 관계 변화 등 추적
        """
        if not prev_manuscript:
            return {'injuries': [], 'items_gained': [], 'items_lost': [], 'relationship_changes': []}

        result = {
            'injuries': [],
            'items_gained': [],
            'items_lost': [],
            'relationship_changes': []
        }

        # 1. 부상 패턴 탐지
        injury_patterns = [
            r'([가-힣]+)[이가]\s*(중상|내상|부상|중독)[을를]?\s*(입|당)',
            r'(중상|내상|부상)[을를]\s*입',
        ]
        for pattern in injury_patterns:
            matches = re.findall(pattern, prev_manuscript)
            result['injuries'].extend([m[0] if isinstance(m, tuple) else m for m in matches])

        # 2. 아이템 획득 패턴
        gain_patterns = [
            r'([가-힣]{2,6})[을를]\s*(얻|획득|받|입수)',
            r'([가-힣]{2,6})[이가]\s*손에\s*들어',
        ]
        for pattern in gain_patterns:
            matches = re.findall(pattern, prev_manuscript)
            result['items_gained'].extend([m[0] if isinstance(m, tuple) else m for m in matches])

        # 3. 아이템 손실 패턴
        loss_patterns = [
            r'([가-힣]{2,6})[을를]\s*(잃|빼앗|분실|파괴)',
        ]
        for pattern in loss_patterns:
            matches = re.findall(pattern, prev_manuscript)
            result['items_lost'].extend([m[0] if isinstance(m, tuple) else m for m in matches])

        return result

    def _build_past_guard_section(self, prev_manuscript: str, existing_dead_npcs: List[str] = None) -> str:
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
            dead_str = ", ".join(all_dead_npcs[:15])
            sections.append(f"""
### 🔒 [PAST CONSTRAINT] 사망 NPC - 절대 부활 금지
이미 사망한 인물: {dead_str}

⛔ 위 인물들이 현재 시점에서 대화/행동하면 REJECT
⛔ 회상 장면에서만 언급 가능 (과거형 필수)
⛔ "알고 보니 살아있었다" 전개 금지 (별도 복선 없이)
""")

        # 2. 과거 사건 탐지
        past_events = self._detect_past_events_from_manuscript(prev_manuscript)

        if past_events.get('injuries'):
            injuries = list(set(past_events['injuries']))[:5]
            sections.append(f"""
### 🔒 [PAST CONSTRAINT] 이전 화 부상 상태
직전 화에서 발생한 부상: {', '.join(injuries)}

⛔ 치료 장면 없이 완치된 것처럼 행동하면 REJECT
⛔ 부상 상태는 전투/행동에 반드시 반영
""")

        if sections:
            return "\n".join(sections)
        else:
            return ""

    def _build_future_guard_section(
        self,
        current_inventory: List[str],
        current_martial_arts: List[str],
        dead_npcs: List[str],
        item_acquisition_timeline: str
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
            dead_str = ", ".join(dead_npcs[:10])  # 최대 10개
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
        previous_attempt: Dict,
        attempt_number: int,
        # [V60.80 FIX] 미래 침범 방지용 추가 파라미터
        current_inventory: List[str] = None,
        current_martial_arts: List[str] = None,
        dead_npcs: List[str] = None,
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
        state_tracker=None
    ) -> List[Dict]:
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

        Returns:
            List[Dict]: 새로운 3개 후보
        """
        # 피드백 강화
        enhanced_feedback = f"""
[🚨 {attempt_number}차 재시도 - Director 피드백 필수 반영]

{director_feedback}

[이전 시도 분석]
- 선택된 전략: {previous_attempt.get('strategy', 'unknown')}
- 문제점: {previous_attempt.get('rejection_reason', 'unknown')}

⚠️ 위 피드백을 100% 반영하지 않으면 다시 REJECT됩니다.
"""

        # 실패 학습 제약 구성
        failure_constraints = ""
        if previous_attempt.get('action_items'):
            items = previous_attempt.get('action_items', [])
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
            state_tracker=state_tracker
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
            banned_keys = ["Beat 3", "Beat 4", "continuation_text", "scene_summary",
                          "future_hint", "next_episode", "spoiler"]

            if isinstance(data, dict):
                for key in banned_keys:
                    if key in data:
                        del data[key]
                return json.dumps(data, ensure_ascii=False, indent=4)
        except (json.JSONDecodeError, ValueError):
            pass

        # 2. 텍스트 라인 필터링 (비상 대책)
        filtered_lines = []
        for line in text.splitlines():
            if re.search(r'"(Beat \d+|continuation_text|future_hint)":', line):
                continue
            filtered_lines.append(line)

        text = "\n".join(filtered_lines)

        # 3. 영문 괄호 병기 제거: "윈도우(Windows)" → "윈도우"
        text = re.sub(r'([가-힣]+)\([A-Za-z][A-Za-z\s&\-\'\.,;:0-9]*\)', r'\1', text)

        return text

    def _apply_self_critique(
        self,
        manuscript: str,
        hud_report: str,
        npcs: list,
        genre_name: str,
        ep_num: int = None
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
        encyclopedia = {'npcs': npcs}
        MAX_CRITIQUE_ROUNDS = 3

        current_manuscript = manuscript
        total_issues_fixed = 0

        # [V60.82] 조기 스킵 조건 - Rubric 점수로 사전 평가
        rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
        if rubric_score >= 3.5:
            # 이미 품질 높음 - Self-Critique 스킵
            return current_manuscript

        for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
            critique_result = self._self_critique(
                current_manuscript, hud_report, encyclopedia, genre_name, ep_num
            )

            if not critique_result['has_issues']:
                if round_num > 1:
                    print(f"      [ChiefWriter] Self-Critique R{round_num}: 완료 ({total_issues_fixed}건 수정)")
                break

            if critique_result['severity'] == 'low':
                break

            # [V60.82] 라운드 중간 Rubric 체크 - 3.5 이상이면 조기 종료
            if round_num > 1:
                mid_score = self._evaluate_with_rubric(current_manuscript, genre_name)
                if mid_score >= 3.5:
                    break

            print(f"      [ChiefWriter] Self-Critique R{round_num}/{MAX_CRITIQUE_ROUNDS}: {len(critique_result['issues'])}건...")
            current_manuscript = self._fix_manuscript_issues(
                current_manuscript, critique_result, hud_report
            )
            total_issues_fixed += len(critique_result['issues'])

        return current_manuscript

    def _self_critique(
        self,
        manuscript: str,
        hud_report: str,
        encyclopedia: dict,
        genre_name: str,
        ep_num: int = None
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
            content = data.get('content', '')
        except Exception:
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

        return {
            "has_issues": has_issues,
            "issues": issues,
            "severity": severity
        }

    def _check_hud_consistency(self, content: str, hud_report: str) -> list:
        """HUD 모순 체크"""
        issues = []

        weak_keywords = ['나약', '중독', '부상', '중상', '쇠약', '기력고갈', '빈사']
        strong_actions = ['일격에', '압도', '박살', '분쇄', '제압', '일도양단']

        is_weak = any(kw in hud_report for kw in weak_keywords)
        has_strong_action = any(kw in content for kw in strong_actions)

        if is_weak and has_strong_action:
            justification_kws = ['발경', '기혈', '폭발', '전생', '대가', '고통', '각오', '최후']
            has_justification = any(kw in content for kw in justification_kws)

            if not has_justification:
                issues.append({
                    "type": "hud_contradiction",
                    "description": "나약한 상태에서 강력한 행동, 정당화 부족",
                    "location": "본문",
                    "severity": "medium"
                })

        return issues

    def _check_cliche_overuse(self, content: str, genre_name: str, ep_num: int = None) -> list:
        """클리셰 과다 사용 체크"""
        issues = []

        # 최근 빈도 체크
        if ep_num is not None and ep_num > 1:
            recent_counts = self._count_recent_cliches(ep_num, content, window=10)

            overused = [
                f"'{keyword}' ({count}회)"
                for keyword, count in recent_counts.items()
                if count >= 3
            ]

            if overused:
                issues.append({
                    "type": "cliche_overuse_recent",
                    "description": f"최근 클리셰 과용: {', '.join(overused[:3])}",
                    "location": "최근 10화",
                    "severity": "medium",
                    "recommendation": "다른 표현으로 다양화 필요"
                })

        # 무협 클리셰 패턴
        if genre_name == '무협':
            cliche_patterns = [
                ('무시', '별 볼일'),
                ('무시', '평범해'),
                ('허름', '행색'),
                ('조롱', '비웃'),
            ]

            cliche_count = 0
            for pattern1, pattern2 in cliche_patterns:
                if pattern1 in content and pattern2 in content:
                    cliche_count += 1

            if cliche_count >= 2:
                issues.append({
                    "type": "cliche_overuse",
                    "description": f"무협 클리셰 패턴이 {cliche_count}회 반복",
                    "location": "본문",
                    "severity": "low"
                })

        return issues

    def _check_justification_gaps(self, content: str, hud_report: str) -> list:
        """정당화 누락 체크"""
        issues = []

        constraints = []
        if '나약' in hud_report or '중독' in hud_report:
            constraints.append('physical')
        if 'reputation' in hud_report.lower():
            rep_match = re.search(r'reputation[:\s]+(\d+)', hud_report, re.IGNORECASE)
            if rep_match and int(rep_match.group(1)) < 30:
                constraints.append('authority')

        if 'physical' in constraints:
            overcome_keywords = ['이루어', '성공', '압도', '제압']
            has_overcome = any(kw in content for kw in overcome_keywords)

            if has_overcome:
                just_kws = ['때문에', '덕분에', '활용', '방법', '대가']
                has_just = any(kw in content for kw in just_kws)

                if not has_just:
                    issues.append({
                        "type": "justification_gap",
                        "description": "제약 극복 장면에 정당화 표현 부족",
                        "location": "본문",
                        "severity": "medium"
                    })

        return issues

    def _check_npc_relationship(self, content: str, encyclopedia: dict) -> list:
        """NPC 관계 일관성 체크"""
        issues = []

        npcs = encyclopedia.get('npcs', [])

        for npc in npcs:
            if not isinstance(npc, dict):
                continue

            name = npc.get('name', '')
            if not name or name not in content:
                continue

            relationship = npc.get('relationship_state', '중립')

            # 경외 상태인데 무시 표현이 있는가?
            if relationship in ['경외', '충성', '존경']:
                disrespect_keywords = ['무시', '비웃', '조롱', '업신여']
                for kw in disrespect_keywords:
                    if kw in content:
                        # NPC가 주인공을 무시하는 맥락인지 확인
                        context_pattern = f"{name}.*{kw}|{kw}.*{name}"
                        if re.search(context_pattern, content):
                            issues.append({
                                "type": "npc_relationship_inconsistency",
                                "description": f"'{name}'은 경외 상태인데 무시/조롱 표현 사용",
                                "location": "본문",
                                "severity": "medium"
                            })
                            break

        return issues

    def _fix_manuscript_issues(
        self,
        manuscript: str,
        critique_result: dict,
        hud_report: str
    ) -> str:
        """
        [V60.81] 감지된 문제 수정

        LLM을 사용하여 문제점을 수정한 새 원고 반환
        """
        issues = critique_result.get('issues', [])
        if not issues:
            return manuscript

        # 수정 지시 구성
        fix_instructions = []
        for issue in issues[:3]:  # 최대 3개만 수정
            fix_instructions.append(f"- {issue['type']}: {issue['description']}")

        prompt = f"""
[Role] 원고 교정 전문가
[Task] 아래 원고에서 발견된 문제를 수정하라.

### 발견된 문제
{chr(10).join(fix_instructions)}

### 현재 HUD 상태 (참고)
{self._escape_braces(hud_report[:500])}

### 수정 대상 원고
{self._escape_braces(manuscript[:8000])}

### 출력 형식
수정된 JSON 원고만 출력하라. 설명 없이 JSON만.
"""
        try:
            fixed = self.ask(prompt, temperature=0.5, thinking_level="low")
            fixed = self._sanitize_leakage(fixed)

            # JSON 유효성 검증
            try:
                json.loads(fixed)
                return fixed
            except:
                return manuscript  # 파싱 실패시 원본 유지
        except Exception as e:
            print(f"      ⚠️ [ChiefWriter] 수정 실패: {e}")
            return manuscript

    def _evaluate_with_rubric(self, manuscript: str, genre_name: str) -> float:
        """
        [V60.81] Rubric 기반 품질 평가

        Returns:
            float: 품질 점수 (1.0 ~ 4.0)
        """
        try:
            data = json.loads(manuscript)
            content = data.get('content', '')
        except Exception:
            content = manuscript

        if not content or len(content) < 100:
            return 1.0

        scores = []

        # 1. 감정 표현 평가 (Show vs Tell)
        direct_emotions = ['기뻤다', '슬펐다', '화났다', '놀랐다', '두려웠다', '경악했다', '분노했다']
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
        sentences = [s.strip() for s in re.split(r'[.!?]', content) if len(s.strip()) > 5]
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
            'visual': ['보였다', '빛', '색', '어둠', '그림자'],
            'auditory': ['소리', '울림', '침묵', '들렸다', '속삭'],
            'tactile': ['차가', '뜨거', '거친', '부드러', '통증'],
            'olfactory': ['냄새', '향기', '악취', '피비린']
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
                        content = past_ms.get('content', '') if isinstance(past_ms, dict) else str(past_ms)
                        hud_snapshot = past_ms.get('hud_snapshot', {}) if isinstance(past_ms, dict) else {}
                        self._manuscript_cache[i] = {
                            'content': content,
                            'hud_snapshot': hud_snapshot
                        }
                except Exception:
                    continue
        except Exception:
            pass

    def _get_cached_manuscript(self, ep_num: int) -> dict:
        """[V60.82] 캐시에서 원고 조회"""
        return self._manuscript_cache.get(ep_num, {'content': '', 'hud_snapshot': {}})

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
            master_bible = getattr(self.context, 'master_bible', None)
            if not master_bible:
                return {}

            bible_root = master_bible.get('MasterBible', master_bible)
            assets = bible_root.get('AssetLibrary', {})
            key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            if not key_npcs:
                return {}

            npc_names = [npc.get('name', '') for npc in key_npcs if isinstance(npc, dict) and npc.get('name')]
            frequency = {name: 0 for name in npc_names}

            # [V60.82] 캐시 사용 (DB 직접 조회 대신)
            for i in range(max(1, ep_num - window), ep_num):
                cached = self._get_cached_manuscript(i)
                content = cached.get('content', '')
                if content:
                    for name in npc_names:
                        if name in content:
                            frequency[name] += 1

            return frequency
        except Exception:
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

        except Exception:
            return "빈도 추적 실패"

    def _count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> dict:
        """
        최근 N화에서 클리셰 빈도 카운트
        """
        cliche_keywords = [
            "피를 토하", "기세", "살기", "냉기", "검기",
            "압도", "전율", "경악", "창백", "경외",
            "무시", "조롱", "비웃", "허름"
        ]

        counts = {keyword: 0 for keyword in cliche_keywords}

        # [V60.82] 캐시 사용 (DB 직접 조회 대신)
        for i in range(max(1, ep_num - window), ep_num):
            cached = self._get_cached_manuscript(i)
            content = cached.get('content', '')
            if content:
                for keyword in cliche_keywords:
                    counts[keyword] += content.count(keyword)

        # 현재 원고도 체크
        for keyword in cliche_keywords:
            counts[keyword] += manuscript.count(keyword)

        return {k: v for k, v in counts.items() if v > 0}

    def _get_hud_trend_safe(self, ep_num: int) -> str:
        """
        HUD 추세 안전 호출
        """
        try:
            if hasattr(self.context, 'sys') and hasattr(self.context.sys, 'hud'):
                return self.context.sys.hud.get_hud_trend(ep_num, window=5)
            elif hasattr(self.context, 'martial'):
                return self.context.martial.get_hud_trend(ep_num, window=5)
            else:
                return "HUD 추세 정보 없음"
        except Exception:
            return "안정적"

    def _extract_numeric_value(self, value) -> int:
        """HUD 값에서 숫자 추출"""
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            match = re.search(r'[+-]?\d+', value)
            if match:
                return int(match.group())
        return 0

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """
        [V60.95] StateTracker에서 고밀도 HUD 컨텍스트 구축

        PresetRegistry 기반 17+ 필드를 프롬프트에 주입
        NPC 레지스트리 정보도 포함

        Args:
            state_tracker: StateTracker 인스턴스
            ep_num: 현재 에피소드 번호

        Returns:
            str: 프롬프트용 HUD 컨텍스트
        """
        if not state_tracker:
            return ""

        lines = []

        # 1. 주인공 상태 (고밀도 필드)
        try:
            # 직전 에피소드 상태 가져오기
            prev_state = None
            if ep_num > 1 and hasattr(state_tracker, 'episode_states'):
                prev_state = state_tracker.episode_states.get(ep_num - 1)

            if prev_state:
                state_dict = prev_state.to_dict() if hasattr(prev_state, 'to_dict') else {}

                lines.append("[주인공 현재 상태 - 고밀도]")

                # 핵심 필드 (항상 표시)
                core_fields = ['location', 'internal_energy', 'injuries']
                for field in core_fields:
                    if field in state_dict:
                        lines.append(f"  - {field}: {state_dict[field]}")

                # 확장 필드 (있으면 표시)
                extended_fields = [
                    ('realm', '경지'), ('reputation', '평판'), ('mental_state', '정신상태'),
                    ('faction', '소속'), ('rank', '지위'), ('gold', '재화'),
                    ('awakening_grade', '각성등급'), ('gate_clearance', '클리어 게이트'),
                    ('net_worth', '자산'), ('market_reputation', '시장평판'),
                    ('mana', '마나'), ('skills', '스킬'), ('titles', '칭호')
                ]

                for field, display in extended_fields:
                    if field in state_dict and state_dict[field]:
                        value = state_dict[field]
                        # 리스트는 쉼표로 연결
                        if isinstance(value, list):
                            value = ', '.join(str(v) for v in value[:5])  # 최대 5개
                        lines.append(f"  - {display}: {value}")

                # 소지품
                items = state_dict.get('items', [])
                weapons = state_dict.get('weapons', [])
                if items or weapons:
                    all_items = weapons + items
                    lines.append(f"  - 소지품: {', '.join(str(i) for i in all_items[:8])}")

                # 관계
                relationships = state_dict.get('relationships', {})
                if relationships:
                    rel_str = ', '.join(f"{k}:{v}" for k, v in list(relationships.items())[:5])
                    lines.append(f"  - 관계: {rel_str}")

        except Exception as e:
            lines.append(f"  (상태 로드 오류: {str(e)[:30]})")

        # 2. NPC 레지스트리 (살아있는 주요 NPC)
        try:
            if hasattr(state_tracker, 'npc_registry') and state_tracker.npc_registry:
                alive_npcs = [
                    (name, info) for name, info in state_tracker.npc_registry.items()
                    if info.get('status') != 'dead'
                ][:10]  # 최대 10명

                if alive_npcs:
                    lines.append("")
                    lines.append("[등장 가능 NPC]")
                    for name, info in alive_npcs:
                        role = info.get('role', '')
                        relationship = info.get('relationship', '')
                        faction = info.get('faction', '')

                        npc_desc = f"  - {name}"
                        details = []
                        if role:
                            details.append(role)
                        if faction:
                            details.append(faction)
                        if relationship:
                            details.append(f"관계:{relationship}")
                        if details:
                            npc_desc += f" ({', '.join(details)})"
                        lines.append(npc_desc)

                # 사망 NPC 경고
                dead_npcs = [
                    name for name, info in state_tracker.npc_registry.items()
                    if info.get('status') == 'dead'
                ]
                if dead_npcs:
                    lines.append("")
                    lines.append(f"⚠️ [사망 NPC - 등장 금지]: {', '.join(dead_npcs[:5])}")

        except Exception:
            pass  # NPC 로드 실패 시 무시

        return "\n".join(lines) if lines else ""

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
            return {'has_anomalies': False, 'anomalies': [], 'warning_text': ''}

        try:
            # [V60.82] 캐시 사용 (DB 직접 조회 대신)
            hud_history = []
            for ep in range(max(1, current_ep - 3), current_ep):
                cached = self._get_cached_manuscript(ep)
                hud_snapshot = cached.get('hud_snapshot', {})
                if hud_snapshot:
                    hud_history.append({'ep': ep, 'hud': hud_snapshot})

            if not hud_history:
                return {'has_anomalies': False, 'anomalies': [], 'warning_text': ''}

            latest = hud_history[-1]['hud'] if hud_history else {}

            # 1. 내공 급변 감지
            if len(hud_history) >= 2:
                prev_hud = hud_history[-2]['hud']

                curr_energy = self._extract_numeric_value(latest.get('internal_energy', 0))
                prev_energy = self._extract_numeric_value(prev_hud.get('internal_energy', 0))

                if curr_energy - prev_energy > 500:
                    anomalies.append({
                        'type': '내공 급상승',
                        'description': f'직전 화 대비 내공 +{curr_energy - prev_energy} 증가',
                        'recommendation': '점진적 성장 또는 특별한 기연으로 정당화 필요',
                        'severity': 'high'
                    })
                elif curr_energy - prev_energy > 200:
                    anomalies.append({
                        'type': '내공 빠른 성장',
                        'description': f'직전 화 대비 내공 +{curr_energy - prev_energy} 증가',
                        'recommendation': '수련/깨달음 장면으로 정당화 권장',
                        'severity': 'medium'
                    })

                # 2. 경지 급변 감지
                curr_realm = latest.get('realm', '')
                prev_realm = prev_hud.get('realm', '')

                realm_tiers = ['하수', '삼류', '이류', '일류', '초일류', '절정', '화경', '현경', '귀환']

                if curr_realm and prev_realm and curr_realm != prev_realm:
                    try:
                        curr_tier = realm_tiers.index(curr_realm) if curr_realm in realm_tiers else -1
                        prev_tier = realm_tiers.index(prev_realm) if prev_realm in realm_tiers else -1

                        if curr_tier - prev_tier >= 2:
                            anomalies.append({
                                'type': '경지 급상승',
                                'description': f'직전 화 대비 경지 2단계 이상 상승 ({prev_realm} → {curr_realm})',
                                'recommendation': '연속 돌파 장면 또는 특수 기연으로 정당화 필수',
                                'severity': 'critical'
                            })
                    except ValueError:
                        pass

                # 3. 부상 상태 급변 감지
                curr_injury = str(latest.get('causal_injuries', '')).lower()
                prev_injury = str(prev_hud.get('causal_injuries', '')).lower()

                injury_levels = {'정상': 0, '경상': 1, '중상': 2, '중독': 2, '내상': 2, '빈사': 3, '치명상': 3}

                curr_level = 0
                prev_level = 0
                for injury_name, level in injury_levels.items():
                    if injury_name in curr_injury:
                        curr_level = max(curr_level, level)
                    if injury_name in prev_injury:
                        prev_level = max(prev_level, level)

                if prev_level >= 2 and curr_level == 0:
                    anomalies.append({
                        'type': '부상 급회복',
                        'description': f'직전 화 심각한 부상 → 갑자기 완치',
                        'recommendation': '치료 과정 명시적 묘사 필요',
                        'severity': 'high'
                    })

        except Exception as e:
            return {'has_anomalies': False, 'anomalies': [], 'error': str(e), 'warning_text': ''}

        # 경고 텍스트 생성
        warning_text = ""
        if anomalies:
            warning_parts = ["🚨 [HUD 급변 감지]"]
            for a in anomalies:
                warning_parts.append(f"⚠️ {a['type']}: {a['description']}")
                warning_parts.append(f"   → {a['recommendation']}")
            warning_text = "\n".join(warning_parts)

        return {
            'has_anomalies': len(anomalies) > 0,
            'anomalies': anomalies,
            'warning_text': warning_text
        }

    def _get_npc_equipment_summary(self, master_bible: dict) -> str:
        """
        [V60.81] NPC 장비 현황 추출

        Returns:
            str: NPC 장비 요약 문자열
        """
        try:
            bible_root = master_bible.get('MasterBible', master_bible) if isinstance(master_bible, dict) else {}
            assets = bible_root.get('AssetLibrary', {})
            key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            npc_equipment_summary = []
            for npc in key_npcs:
                if isinstance(npc, dict):
                    npc_name = npc.get('name') or npc.get('Name', '알 수 없음')
                    npc_hud = npc.get('NPC_Martial_HUD', {})
                    if isinstance(npc_hud, dict):
                        equip = npc_hud.get('equipment', [])
                        if equip:
                            npc_equipment_summary.append(f"- {npc_name}: {equip}")

            if npc_equipment_summary:
                return "\n".join(npc_equipment_summary)
            else:
                return "NPC 장비 정보 없음"
        except Exception:
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
        """
        return f"""
[ANTI-TROPE PROTOCOL - 장르 관습 재정의]

이 작품은 일반적인 {genre_name}물과 다릅니다. 다음 클리셰는 절대 사용하지 마십시오:

1. "약해 보이는 주인공" 클리셰 금지
   - X "허름한 행색", "평범해 보이는", "별 볼일 없어 보이는"
   - O 주인공의 실제 HUD 상태를 직접 반영
   - O "증표를 본 순간 안색이 창백해졌다" (데이터 기반 묘사)

2. "무시-사이다" 공식 과다 사용 금지
   - X 매 에피소드마다 무시당하고 압도하는 반복
   - O 주인공의 명성/권위가 증가하면 무시는 감소해야 함
   - O 무시가 필요하면 반드시 알리바이 (정보 차단, 변장 등)

3. "조연의 영구 생존" 클리셰 금지
   - X 모욕한 하인이 아무 처벌 없이 계속 등장
   - O 모욕/배신한 조연은 반드시 청산 (처단/퇴장/굴복)

4. "순간 회복" 클리셰 금지
   - X 전투 중 부상 -> 다음 장면에서 멀쩡함 (설명 없이)
   - O 부상은 지속적으로 영향 주거나, 치료 과정 명시

5. "NPC의 기억상실" 클리셰 금지
   - X 이전 화에서 경외했던 NPC가 이번 화에서 다시 무시
   - O 관계는 단방향 발전 (무시->경외는 가능, 경외->무시는 정당화 필요)

[당신이 쓰려는 문장이 위 클리셰에 해당하는가? YES -> 다시 쓰십시오]
"""

    def _build_mandatory_context(self, current_ep: int) -> str:
        """
        [V60.81] 강제 맥락 주입 - 최근 사건/NPC 상태/HUD 급변 포함

        ChiefWriter가 독립적으로 동작할 수 있도록 내장
        """
        mandatory_parts = ["[MANDATORY CONTEXT - 반드시 인지하고 집필할 것]\n"]

        # HUD 급변 감지
        hud_anomalies = self._check_hud_anomalies(current_ep)
        if hud_anomalies.get('has_anomalies'):
            mandatory_parts.append("\n[HUD ANOMALY WARNING - 급변 감지]\n")
            for anomaly in hud_anomalies.get('anomalies', []):
                mandatory_parts.append(f"- {anomaly['type']}: {anomaly['description']}")
                mandatory_parts.append(f"  -> 권장: {anomaly['recommendation']}\n")

        # 최근 사건 추출
        recent_events = self._extract_recent_events(current_ep, n_episodes=3)

        if recent_events:
            mandatory_parts.append("\n최근 중요 사건 (절대 무시 금지):")
            for event in recent_events:
                mandatory_parts.append(f"- 제{event['ep_num']}화: {event['description']}")
                if event.get('consequence'):
                    mandatory_parts.append(f"  현재 상태: {event['consequence']}")
                mandatory_parts.append(f"  -> 이 사실을 무시하면 논리 모순 발생\n")

        # NPC 상태 추출
        npc_states = self._extract_npc_last_states(current_ep)

        if npc_states:
            mandatory_parts.append("\nNPC 마지막 관계 상태 (일관성 유지 필수):")
            for npc_name, state_info in npc_states.items():
                mandatory_parts.append(f"- {npc_name}: {state_info['relationship']} (제{state_info['last_ep']}화)")
                mandatory_parts.append(f"  -> 이 관계가 변경되려면 명시적 사건 필요\n")

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
                    summary = log_data.get('summary', '')
                    if summary and len(summary) > 10:
                        events.append({
                            'ep_num': ep,
                            'description': summary[:200],
                            'consequence': ''
                        })

                    data = log_data.get('data', {})
                    if isinstance(data, dict):
                        major_changes = data.get('major_changes', [])
                        if major_changes:
                            for change in major_changes[:2]:
                                if isinstance(change, dict):
                                    events.append({
                                        'ep_num': ep,
                                        'description': change.get('event', ''),
                                        'consequence': change.get('consequence', '')
                                    })
        except Exception as e:
            pass

        return events[-5:] if events else []

    def _extract_npc_last_states(self, current_ep: int) -> dict:
        """등장 NPC의 마지막 상태 추출"""
        npc_states = {}

        try:
            bible = getattr(self.context, 'master_bible', {})
            bible_root = bible.get('MasterBible', bible)
            assets = bible_root.get('AssetLibrary', {})
            key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

            for npc in key_npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get('name') or npc.get('Name', '')
                if not name:
                    continue

                relationship = npc.get('relationship_state', '중립')
                last_appearance = npc.get('last_appearance_ep', 0)

                if isinstance(last_appearance, int) and 0 < last_appearance < current_ep:
                    npc_states[name] = {
                        'relationship': relationship,
                        'last_ep': last_appearance
                    }
        except Exception as e:
            pass

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
        physical_constraints = ['나약', '중독', '부상', '중상', '쇠약', '기력고갈', '기혈역류']
        if any(constraint in hud_report for constraint in physical_constraints):
            active_constraints.append('physical')
            guidance_parts.append("\n[신체 제약 감지] 현재 주인공은 신체적 약점이 있습니다.")
            guidance_parts.append("강력한 행동 시 반드시 정당화 필요:")
            guidance_parts.append("- 발경/내력 폭발 (대가: 내상)")
            guidance_parts.append("- 특수 환단 복용 (대가: 후유증)")
            guidance_parts.append("- 의지력 각성 (대가: 기절/혼절)")

        # 2. 지위 제약 감지
        low_status_keywords = ['하인', '노예', '평민', '무명', '낭인', '거지', '천민']
        if any(keyword in hud_report for keyword in low_status_keywords):
            active_constraints.append('authority')
            guidance_parts.append("\n[지위 제약 감지] 현재 주인공은 낮은 명성/지위입니다.")
            guidance_parts.append("명령/지시 행위 시 반드시 정당화 필요:")
            guidance_parts.append("- 신분 증명 (증표, 신물)")
            guidance_parts.append("- 실력 과시 (무력 시위)")
            guidance_parts.append("- 제3자 보증 (귀인의 추천)")

        # 3. 능력 급상승 가능성
        breakthrough_keywords = ['돌파', '깨달음', '체득', '각성', '각오']
        if any(keyword in hud_report for keyword in breakthrough_keywords):
            active_constraints.append('power_up')
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

    # =========================================================================
    # [V60.81] Self-Refine 품질 정제 시스템 (Writer 통합)
    # =========================================================================

    def _self_refine(self, manuscript: str, target_areas: list = None) -> str:
        """
        [V60.81] Self-Refine: 품질 정제

        88-90점대 아쉬운 점수거나 중요 화일 때 호출
        문학적 품질 향상 (감정선, 문장력, 절벽걸기 등)

        Args:
            manuscript: 원고 (JSON 문자열)
            target_areas: 개선 영역 리스트 ['emotion', 'prose', 'cliffhanger', 'sensory']

        Returns:
            str: 정제된 원고 (JSON)
        """
        if target_areas is None:
            target_areas = ['emotion', 'prose', 'cliffhanger']

        area_instructions = {
            'emotion': """
[감정선 강화]
- 주인공의 내면 독백 추가 (감정의 깊이)
- 미묘한 감정 변화 묘사 (분노 → 냉소 → 결의)
- 감정과 행동의 연결 (왜 그렇게 행동하는가?)
""",
            'prose': """
[문장력 향상]
- 반복 표현 다양화
- 비유/은유 추가 (시적 표현)
- 리듬감 있는 문장 구성 (짧-짧-긴 패턴)
""",
            'cliffhanger': """
[절벽걸기 강화]
- 마지막 문장을 강렬하게
- 미해결 긴장감 조성
- 독자가 다음 화를 궁금해하게 만들기
""",
            'sensory': """
[오감 묘사 강화]
- 시각적 묘사 (색, 형태, 움직임)
- 청각적 묘사 (소리, 침묵)
- 촉각/후각 추가 (질감, 냄새)
"""
        }

        selected_instructions = "\n".join([
            area_instructions.get(area, '')
            for area in target_areas
        ])

        refine_prompt = f"""
[Self-Refine: 문학적 품질 향상]

[원본 원고]
{self._escape_braces(manuscript[:8000])}

[개선 영역]
{selected_instructions}

[지침]
위 원고를 아래 기준으로 정제하십시오:
1. 스토리/설정은 절대 변경 금지
2. 위 개선 영역의 표현만 향상
3. 전체 길이는 유지 (±10%)
4. JSON 형식 유지

중요:
- "정제"이지 "재작성"이 아닙니다
- 기존 문장의 70%는 유지하고 30%만 향상
- 과도한 수식어 추가는 금물

출력: 정제된 원고 (JSON 형식만)
"""

        try:
            refined = self.ask(refine_prompt, temperature=0.7)
            refined = self._sanitize_leakage(refined)
            # JSON 유효성 검증
            try:
                json.loads(refined)
                return refined
            except:
                return manuscript
        except Exception as e:
            print(f"      ⚠️ [ChiefWriter Self-Refine] 정제 실패: {e}")
            return manuscript

    # =========================================================================
    # [V60.81] V59 감정선 스켈레톤 시스템 (Writer 통합)
    # =========================================================================

    # 감정 상태 정의
    EMOTION_STATES = {
        '평온': {'intensity': 0, 'valence': 0},
        '불안': {'intensity': 2, 'valence': -1},
        '긴장': {'intensity': 3, 'valence': -1},
        '분노': {'intensity': 4, 'valence': -2},
        '공포': {'intensity': 4, 'valence': -2},
        '절망': {'intensity': 5, 'valence': -3},
        '기대': {'intensity': 2, 'valence': 1},
        '희열': {'intensity': 4, 'valence': 2},
        '통쾌': {'intensity': 5, 'valence': 3},
        '감동': {'intensity': 4, 'valence': 2},
        '슬픔': {'intensity': 3, 'valence': -2},
        '결의': {'intensity': 4, 'valence': 1},
    }

    # 장르별 권장 감정 흐름 패턴
    GENRE_EMOTION_PATTERNS = {
        'wuxia': {
            'standard': ['평온', '긴장', '분노', '결의', '통쾌'],
            'training': ['평온', '불안', '긴장', '절망', '결의', '희열'],
            'revenge': ['슬픔', '분노', '결의', '긴장', '통쾌'],
            'crisis': ['평온', '불안', '공포', '절망', '결의'],
        },
        'hunter': {
            'dungeon': ['긴장', '불안', '공포', '결의', '통쾌'],
            'awakening': ['평온', '기대', '긴장', '희열'],
            'boss_fight': ['긴장', '분노', '절망', '결의', '통쾌'],
            'growth': ['평온', '기대', '긴장', '희열', '결의'],
        },
        'investment': {
            'opportunity': ['평온', '기대', '긴장', '희열'],
            'crisis': ['긴장', '불안', '공포', '절망', '결의'],
            'victory': ['긴장', '불안', '결의', '통쾌', '감동'],
            'betrayal': ['평온', '불안', '분노', '결의'],
        },
        'sports': {
            'match': ['긴장', '불안', '결의', '분노', '통쾌'],
            'training': ['평온', '고통', '절망', '결의', '희열'],
            'rivalry': ['긴장', '분노', '결의', '긴장', '통쾌'],
            'injury': ['충격', '절망', '슬픔', '결의', '희열'],
        },
        'medical': {
            'surgery': ['긴장', '불안', '결의', '공포', '안도'],
            'diagnosis': ['평온', '긴장', '불안', '결의'],
            'crisis': ['긴장', '공포', '절망', '결의', '안도'],
            'growth': ['평온', '불안', '결의', '희열'],
        },
    }

    def get_emotion_skeleton_lazy(self, blueprint: dict, genre: str = 'wuxia') -> dict:
        """
        [V60.82] 감정선 스켈레톤 지연 로딩 래퍼

        같은 Blueprint에 대해 중복 생성 방지
        """
        # Blueprint 해시 계산 (간단히 scene_breakdown 키 기반)
        bp_hash = hash(frozenset(blueprint.get('scene_breakdown', {}).keys()))

        if self._emotion_skeleton_cache and self._emotion_skeleton_blueprint_hash == bp_hash:
            return self._emotion_skeleton_cache

        # 캐시 미스 - 새로 생성
        self._emotion_skeleton_cache = self.generate_emotion_skeleton(blueprint, genre)
        self._emotion_skeleton_blueprint_hash = bp_hash
        return self._emotion_skeleton_cache

    def generate_emotion_skeleton(self, blueprint: dict, genre: str = 'wuxia') -> dict:
        """
        [V60.81] 감정선 스켈레톤 생성 - Blueprint 기반으로 씬별 감정 흐름 설계
        """
        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not scene_breakdown:
            return {'scenes': [], 'overall_arc': 'unknown', 'error': 'No scene breakdown'}

        # 1. 씬 유형 분석
        scene_types = self._analyze_scene_types(scene_breakdown, genre)

        # 2. 적합한 감정 패턴 선택
        pattern_name, pattern = self._select_emotion_pattern(scene_types, genre)

        # 3. 씬별 감정 배치
        scenes = []
        num_scenes = len(scene_breakdown)
        pattern_length = len(pattern)

        for i, (scene_name, scene_desc) in enumerate(scene_breakdown.items()):
            pattern_idx = int(i * pattern_length / num_scenes) if num_scenes > 0 else 0
            pattern_idx = min(pattern_idx, pattern_length - 1)

            emotion = pattern[pattern_idx]
            emotion_data = self.EMOTION_STATES.get(emotion, {'intensity': 2, 'valence': 0})

            next_idx = min(pattern_idx + 1, pattern_length - 1)
            target_emotion = pattern[next_idx] if next_idx != pattern_idx else None

            scenes.append({
                'scene_id': i + 1,
                'scene_name': scene_name,
                'emotion': emotion,
                'intensity': emotion_data['intensity'],
                'valence': emotion_data['valence'],
                'target_emotion': target_emotion,
                'description': str(scene_desc)[:100] if scene_desc else ''
            })

        # 4. 클라이맥스 씬 식별
        climax_scene = max(scenes, key=lambda x: x['intensity'])['scene_id'] if scenes else 1

        # 5. 전체 아크 유형 판단
        overall_arc = self._determine_arc_type(scenes)

        return {
            'scenes': scenes,
            'overall_arc': overall_arc,
            'climax_scene': climax_scene,
            'recommended_pattern': pattern_name,
            'pattern_emotions': pattern
        }

    def _analyze_scene_types(self, scene_breakdown: dict, genre: str) -> list:
        """씬 유형 분석"""
        scene_types = []

        type_keywords = {
            'wuxia': {
                'battle': ['전투', '대결', '격돌', '검', '공격', '방어'],
                'training': ['수련', '연마', '깨달음', '돌파', '경지'],
                'dialogue': ['대화', '협상', '설득', '정보'],
                'discovery': ['발견', '비밀', '진실', '단서'],
                'revenge': ['복수', '원수', '청산', '응징'],
            },
            'hunter': {
                'battle': ['전투', '몬스터', '보스', '스킬', '공격'],
                'growth': ['레벨업', '성장', '각성', '스킬 획득'],
                'dungeon': ['던전', '게이트', '탐색', '클리어'],
                'social': ['길드', '동료', '대화', '협력'],
            },
            'investment': {
                'analysis': ['분석', '차트', '데이터', '연구'],
                'trade': ['매수', '매도', '거래', '투자'],
                'crisis': ['폭락', '위기', '손실', '공황'],
                'victory': ['수익', '성공', '대박', '승리'],
            },
            'sports': {
                'match': ['경기', '시합', '대결', '승부', '결승'],
                'training': ['훈련', '연습', '트레이닝', '체력'],
                'rivalry': ['라이벌', '경쟁', '도전', '설욕'],
                'injury': ['부상', '재활', '회복', '수술'],
            },
            'medical': {
                'surgery': ['수술', '집도', '절개', '봉합', '시술'],
                'diagnosis': ['진단', '검사', '판독', '소견'],
                'crisis': ['응급', '위급', '코드블루', '심정지'],
                'growth': ['연수', '수련', '연구', '논문'],
            },
        }

        genre_keywords = type_keywords.get(genre, type_keywords['wuxia'])

        for scene_name, scene_desc in scene_breakdown.items():
            full_text = f"{scene_name} {scene_desc}".lower()
            detected_type = 'unknown'

            for scene_type, keywords in genre_keywords.items():
                if any(kw in full_text for kw in keywords):
                    detected_type = scene_type
                    break

            scene_types.append(detected_type)

        return scene_types

    def _select_emotion_pattern(self, scene_types: list, genre: str) -> tuple:
        """적합한 감정 패턴 선택"""
        patterns = self.GENRE_EMOTION_PATTERNS.get(genre, self.GENRE_EMOTION_PATTERNS['wuxia'])

        type_counts = {}
        for t in scene_types:
            type_counts[t] = type_counts.get(t, 0) + 1

        dominant_type = max(type_counts, key=type_counts.get) if type_counts else 'standard'

        if dominant_type in patterns:
            return dominant_type, patterns[dominant_type]
        else:
            default_key = list(patterns.keys())[0]
            return default_key, patterns[default_key]

    def _determine_arc_type(self, scenes: list) -> str:
        """전체 감정 아크 유형 판단"""
        if not scenes:
            return 'unknown'

        intensities = [s['intensity'] for s in scenes]

        first_half = sum(intensities[:len(intensities)//2]) / max(len(intensities)//2, 1)
        second_half = sum(intensities[len(intensities)//2:]) / max(len(intensities) - len(intensities)//2, 1)

        if second_half > first_half + 1:
            return '상승형'
        elif first_half > second_half + 1:
            return '하강형'
        else:
            return '균형형'

    def build_emotion_prompt_injection(self, emotion_skeleton: dict) -> str:
        """
        [V60.81] 감정 스켈레톤을 프롬프트에 주입할 형태로 변환
        """
        if not emotion_skeleton or not emotion_skeleton.get('scenes'):
            return ""

        lines = [
            "\n[V59 EMOTION SKELETON - 감정선 가이드]\n",
            f"전체 아크: {emotion_skeleton.get('overall_arc', '균형형')}",
            f"클라이맥스: 씬 {emotion_skeleton.get('climax_scene', '?')}",
            f"추천 패턴: {emotion_skeleton.get('recommended_pattern', 'standard')}\n",
            "씬별 감정 흐름:"
        ]

        for scene in emotion_skeleton.get('scenes', []):
            emotion = scene.get('emotion', '평온')
            intensity = scene.get('intensity', 2)
            target = scene.get('target_emotion')

            intensity_bar = '*' * intensity + '-' * (5 - intensity)
            target_str = f" -> {target}" if target and target != emotion else ""
            lines.append(f"  씬{scene['scene_id']}: {emotion} [{intensity_bar}]{target_str}")

        lines.append("\n지침:")
        lines.append("- 각 씬에서 지정된 감정을 독자가 느끼도록 묘사하라")
        lines.append("- 감정 전환(->)이 있는 씬은 그 과정을 자연스럽게 표현하라")
        lines.append("- 클라이맥스 씬에서 감정 강도를 최대로 끌어올려라")
        lines.append("- 감정 직접 서술('슬펐다') 대신 행동/묘사로 전달하라")

        return "\n".join(lines)

    def auto_map_emotions_to_manuscript(self, manuscript: str, emotion_skeleton: dict) -> dict:
        """
        [V60.81] 원고에서 감정 표현 자동 매핑 및 평가
        """
        try:
            data = json.loads(manuscript)
            content = data.get('content', '')
        except Exception:
            content = manuscript

        if not content or not emotion_skeleton.get('scenes'):
            return {'alignment_score': 0, 'error': 'No content or skeleton'}

        emotion_keywords = {
            '평온': ['평화', '고요', '잔잔', '평온', '안정'],
            '불안': ['불안', '초조', '두근', '떨리', '긴장'],
            '긴장': ['긴장', '살기', '위압', '팽팽', '숨막'],
            '분노': ['분노', '화가', '격분', '치밀', '울분'],
            '공포': ['공포', '두려움', '소름', '전율', '무섭'],
            '절망': ['절망', '무력', '좌절', '막막', '암담'],
            '기대': ['기대', '설렘', '희망', '기다'],
            '희열': ['희열', '환희', '황홀', '짜릿', '쾌감'],
            '통쾌': ['통쾌', '시원', '후련', '사이다', '속시원'],
            '감동': ['감동', '뭉클', '눈물', '감격'],
            '슬픔': ['슬픔', '비통', '눈물', '안타', '서러'],
            '결의': ['결의', '각오', '다짐', '결심', '굳건'],
        }

        num_scenes = len(emotion_skeleton['scenes'])
        chunk_size = len(content) // max(num_scenes, 1)

        scene_analysis = []
        matched_count = 0

        for i, scene_info in enumerate(emotion_skeleton['scenes']):
            start = i * chunk_size
            end = start + chunk_size if i < num_scenes - 1 else len(content)
            scene_text = content[start:end]

            expected_emotion = scene_info['emotion']
            expected_keywords = emotion_keywords.get(expected_emotion, [])

            found_keywords = [kw for kw in expected_keywords if kw in scene_text]
            is_matched = len(found_keywords) > 0

            if is_matched:
                matched_count += 1

            detected_emotions = []
            for emotion, keywords in emotion_keywords.items():
                if any(kw in scene_text for kw in keywords):
                    detected_emotions.append(emotion)

            scene_analysis.append({
                'scene_id': scene_info['scene_id'],
                'expected': expected_emotion,
                'detected': detected_emotions,
                'matched': is_matched,
                'found_keywords': found_keywords
            })

        alignment_score = (matched_count / max(num_scenes, 1)) * 100

        missing_emotions = [s['expected'] for s in scene_analysis if not s['matched']]

        suggestions = []
        for s in scene_analysis:
            if not s['matched']:
                suggestions.append(
                    f"씬{s['scene_id']}: '{s['expected']}' 감정 표현 추가 필요"
                )

        return {
            'alignment_score': round(alignment_score, 1),
            'scene_analysis': scene_analysis,
            'missing_emotions': missing_emotions,
            'suggestions': suggestions[:5],
            'matched_scenes': matched_count,
            'total_scenes': num_scenes
        }

    # =========================================================================
    # [V60.81] Quick Self Check (Python-only 품질 검사)
    # =========================================================================

    def quick_self_check(self, manuscript: str, blueprint: dict) -> dict:
        """
        [V60.81] 빠른 자가 점검 (LLM 없이 Python만)

        LLM 호출 없이 기본적인 품질 지표를 체크.

        Returns:
            {
                'needs_llm_review': bool,
                'quick_issues': list,
                'scores': dict
            }
        """
        issues = []
        scores = {}

        # JSON에서 content 추출
        try:
            data = json.loads(manuscript)
            content = data.get('content', manuscript)
        except:
            content = manuscript

        # 1. 분량 체크
        length = len(content)
        scores['length'] = length
        if length < 4000:
            issues.append(f"분량 부족: {length}자 (최소 5000자)")
        elif length < 4500:
            issues.append(f"분량 경계: {length}자 (목표 5000자)")

        # 2. 대화 비율 체크
        dialogue_matches = re.findall(r'"[^"]+?"', content)
        dialogue_chars = sum(len(m) for m in dialogue_matches)
        dialogue_ratio = dialogue_chars / length if length > 0 else 0
        scores['dialogue_ratio'] = dialogue_ratio

        if dialogue_ratio < 0.15:
            issues.append(f"대화 부족: {dialogue_ratio:.0%}")
        elif dialogue_ratio > 0.50:
            issues.append(f"대화 과다: {dialogue_ratio:.0%}")

        # 3. 씬 반영 체크
        scene_breakdown = blueprint.get('scene_breakdown', {}) if blueprint else {}
        if scene_breakdown:
            reflected = 0
            for scene_key, scene_data in scene_breakdown.items():
                if isinstance(scene_data, dict):
                    desc = scene_data.get('description', '') or scene_data.get('title', '')
                else:
                    desc = str(scene_data)

                keywords = re.findall(r'[\w가-힣]{2,}', desc)[:5]
                if any(kw in content for kw in keywords):
                    reflected += 1

            coverage = reflected / len(scene_breakdown) if scene_breakdown else 0
            scores['scene_coverage'] = coverage

            if coverage < 0.5:
                issues.append(f"씬 반영 부족: {coverage:.0%}")

        # 4. 문장 시작어 반복 체크
        sentences = re.split(r'[.?!]\s*', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        consecutive_same = 0
        max_consecutive = 0
        for i in range(1, len(sentences)):
            if len(sentences[i]) >= 2 and len(sentences[i-1]) >= 2:
                if sentences[i][:2] == sentences[i-1][:2]:
                    consecutive_same += 1
                    max_consecutive = max(max_consecutive, consecutive_same)
                else:
                    consecutive_same = 0

        if max_consecutive >= 4:
            issues.append(f"문장 시작어 {max_consecutive}회 연속 반복")

        # 5. 후반부 분량 체크
        if length > 3000:
            first_half = content[:length // 2]
            second_half = content[length // 2:]
            if len(second_half) < len(first_half) * 0.7:
                issues.append("후반부 분량 부족 (급하게 요약됨)")

        return {
            'needs_llm_review': len(issues) >= 2,
            'quick_issues': issues,
            'scores': scores
        }

    # =========================================================================
    # [V60.81] Self-Review and Refine (자가 수정 루프)
    # =========================================================================

    def self_review_and_refine(
        self,
        manuscript: str,
        blueprint: dict,
        checklist_feedback: str = "",
        max_refinements: int = 1
    ) -> dict:
        """
        [V60.81] Writer 자가 수정 루프

        생성된 원고를 자가 검토하여 수정본 생성.
        Director 호출 전 품질 향상 목적.

        Returns:
            {
                'refined_manuscript': str,
                'changes_made': list,
                'refinement_count': int,
                'self_review_passed': bool
            }
        """
        result = {
            'refined_manuscript': manuscript,
            'changes_made': [],
            'refinement_count': 0,
            'self_review_passed': False
        }

        # JSON에서 content 추출
        try:
            data = json.loads(manuscript)
            content = data.get('content', manuscript)
        except:
            content = manuscript

        if not content or len(content) < 1000:
            return result

        scene_breakdown = blueprint.get('scene_breakdown', {}) if blueprint else {}
        scene_list = list(scene_breakdown.keys()) if scene_breakdown else []

        review_prompt = f"""당신은 소설 원고를 검토하는 편집자입니다.

아래 원고를 검토하고 문제점을 수정한 개선본을 작성하세요.

## 검토 기준
1. **분량**: 5,000자 이상이어야 함 (현재: {len(content)}자)
2. **씬 반영**: Blueprint의 모든 씬이 반영되어야 함 ({len(scene_list)}개 씬)
3. **대화/묘사 균형**: 대화 25-40%, 묘사/서술 60-75%
4. **문장 다양성**: 연속으로 같은 단어로 시작하는 문장 금지
5. **클리셰 회피**: 진부한 표현 최소화
6. **후반부 완성도**: 클라이맥스가 급하게 요약되지 않아야 함

{f"## 사전 체크리스트 피드백{chr(10)}{self._escape_braces(checklist_feedback)}" if checklist_feedback else ""}

## 원본 원고
{self._escape_braces(manuscript[:8000])}

## 출력 형식 (JSON)
{{
    "needs_refinement": true/false,
    "issues_found": ["이슈1", "이슈2"],
    "refined_manuscript": "수정된 원고 전문 (JSON 형태 그대로)"
}}

문제가 없으면 needs_refinement: false, 문제가 있으면 수정 후 반환.
"""

        current_manuscript = manuscript

        for i in range(max_refinements):
            try:
                response = self.ask(
                    review_prompt if i == 0 else review_prompt.replace(manuscript, current_manuscript),
                    temperature=0.3,
                    thinking_level="low"  # [V61.6] 자체 리뷰 추론 강화
                )

                if not response:
                    break

                review_result = self._extract_json_robust(response)

                if not review_result:
                    break

                needs_refinement = review_result.get('needs_refinement', False)
                issues = review_result.get('issues_found', [])
                refined = review_result.get('refined_manuscript', '')

                if not needs_refinement:
                    result['self_review_passed'] = True
                    break

                if refined and len(str(refined)) >= len(str(current_manuscript)) * 0.8:
                    result['changes_made'].extend(issues)
                    current_manuscript = refined if isinstance(refined, str) else json.dumps(refined, ensure_ascii=False)
                    result['refinement_count'] += 1

                    if len(issues) <= 1:
                        result['self_review_passed'] = True

            except Exception as e:
                print(f"      ⚠️ [ChiefWriter Self-Review] 실패: {e}")
                break

        result['refined_manuscript'] = current_manuscript
        return result
