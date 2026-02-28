"""
[V64 P2-1] Director EnsembleSelector — 앙상블 선택 전담 모듈

Director God Object 분해의 세 번째 단계.
Blueprint/Manuscript 후보 비교, 선택, 판정을 담당.
Director reference를 통해 BaseAgent 메서드(ask, _extract_json_robust 등) 접근.
"""

import json
import logging

from modules.core.constants import ManuscriptLimits, smart_truncate  # [V64.P4]
from modules.core.prompt_loader import PromptLoader
from modules.core.tactical_utils import extract_episode_tactical
from modules.validation.threshold_helper import _threshold


def _safe_int(value, default=0):
    """LLM 반환값을 안전하게 int로 변환한다."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class DirectorEnsembleSelector:
    """
    [V64 P2-1] Director에서 분리된 앙상블 선택 모듈

    담당:
    - compare_and_select_blueprint(): Blueprint 후보 비교 선택
    - select_and_judge_ensemble(): 3개 원고 후보 선택 + PASS/REJECT
    - quick_judge_single(): 냉동인간 Writer용 간소 검토
    """

    def __init__(self, director) -> None:
        """
        Args:
            director: Director 인스턴스 (BaseAgent 상속, ask/extract/escape 접근용)
        """
        self._d = director
        self._prompt_loader = PromptLoader()

    def compare_and_select_blueprint(
        self,
        candidates: list,
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict = None,
        entity_registry: dict = None,
        state_tracker=None,
    ) -> dict:
        """[V60.85] 여러 Blueprint 후보 중 최적 선택 + PASS/REJECT 판정"""
        if not candidates:
            return {
                "decision": "REJECT",
                "selected_index": -1,
                "selected_blueprint": None,
                "score": 0,
                "reason": "후보 없음",
                "feedback": "Blueprint 후보가 없습니다.",
                "comparison_notes": "",
            }

        if len(candidates) == 1:
            single_result = self._evaluate_single_blueprint(
                candidates[0], arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
            )
            single_result["selected_index"] = 0
            single_result["selected_blueprint"] = candidates[0]
            single_result["comparison_notes"] = "단일 후보"
            return single_result

        logging.info(f"🎭 [Director] {len(candidates)}개 후보 비교 중...")

        # [TTE] 에피소드별 지능 추출 + 안전캡 6000 (기존 2000×3)
        arc_tactical_ep = extract_episode_tactical(
            arc_data.get("tactical_doc", ""),
            ep_num,
            episode_details=arc_data.get("episode_details"),
        )[:6000]

        prev_ending = ""
        if prev_blueprint:
            prev_ending = prev_blueprint.get("ending_hook", "")
            prev_location = prev_blueprint.get("end_location", "")
            if prev_location:
                prev_ending = f"위치: {prev_location}, 훅: {prev_ending}"

        candidate_summaries = []
        for idx, bp in enumerate(candidates):
            meta = bp.get("_ensemble_meta", {})
            strategy = meta.get("strategy", f"후보{idx + 1}")
            scene_count = meta.get("scene_count", len(bp.get("scene_breakdown", {})))
            length = meta.get("length", len(bp.get("integrated_scenario", "")))

            integrated = bp.get("integrated_scenario", "")
            if not isinstance(integrated, str):
                integrated = str(integrated) if integrated else ""

            summary = f"""
[후보 {idx + 1}: {strategy}]
- 씬 개수: {scene_count}개
- 분량: {length}자
- 시작 위치: {bp.get("start_location", "?")}
- 종료 위치: {bp.get("end_location", "?")}
- 시간 흐름: {bp.get("time_flow", "?")}
- 엔딩 훅: {str(bp.get("ending_hook") or "?")[:100]}

[시나리오 전문]
{integrated}
"""
            candidate_summaries.append(summary)

        comparison_prompt = f"""[Blueprint 비교 선택 + 일관성·모순 판정]

당신은 웹소설 시리즈의 품질 관리 감독입니다.
제{ep_num}화 Blueprint 후보 {len(candidates)}개를 **각각 절대 기준으로 독립 평가**한 뒤, 최적 후보를 선택하고 최종 판정하세요.

### Arc 전술서 (이번 화 기준)
{arc_tactical_ep}

### 이전 화 정보
{prev_ending if prev_ending else "(1화 또는 이전 정보 없음)"}

### 후보 목록
{"".join(candidate_summaries)}

### 🔍 일관성·모순 체크 항목 (각 후보를 아래 항목으로 반드시 검사)
1. **사망·부재 NPC 활동**: 이전 화에서 사망하거나 퇴장한 NPC가 활동하는가?
2. **수치·사실 모순**: 금액, 지분율, 날짜, 회사명, 직함 등 확립된 수치·사실과 충돌하는가?
3. **인물 관계·설정 모순**: 기존에 확립된 인물 관계, 직함, 성격과 다른가?
4. **장소·시간 모순**: 이전 화 종료 위치·상황과 공간적·시간적으로 불가능한 변화가 있는가?
5. **내부 모순**: 시나리오 내 앞뒤 내용이 서로 충돌하는가? (한 씬에서 A를 했는데 다음 씬에서 A를 안 한 것처럼 묘사 등)

### 🚨 즉시 REJECT 조건 (하나라도 해당 시 해당 후보 탈락)
- 모순 체크 항목에서 **명백한 모순이 1건 이상** 발견됨
- Arc 전술서에서 지정한 핵심 사건이 **단 하나도** 반영되지 않음
- 이전 화 종료 위치·상황과 **공간적·시간적 모순** 발생
- 통합 시나리오 **1000자 미만** (서사 밀도 부족)
- 엔딩 훅 **누락** 또는 내용 없음

### 📊 점수 기준 (절대 평가 — 상대 비교 아님)
- **90~100**: 모순 없음 + Arc 핵심 사건 전부 반영 + 연속성 완벽 + 강한 훅
- **80~89**: 모순 없음 + Arc 주요 사건 반영 + 연속성 양호 + 훅 존재
- **70~79**: 경미한 모순 의심 1건 또는 Arc 사건 일부 누락 또는 연속성 어색
- **60~69**: 모순 2건 이상 또는 Arc 사건 절반 이상 누락
- **60 미만**: 반드시 REJECT

⚠️ **핵심 원칙**: 3개 후보 중 상대적으로 가장 낫더라도, **절대 점수 80점 미만이면 REJECT**하세요.

### 평가 기준 (가중치)
1. **일관성·모순 없음** (40%): 확립된 사실·수치·관계·설정과 모순이 없는가?
2. **Arc 준수** (35%): 전술서의 이번 화 핵심 사건을 충실히 반영하는가?
3. **연속성** (15%): 이전 화 종료 상태에서 자연스럽게 이어지는가?
4. **다음 화 연결** (10%): 적절한 훅으로 마무리하는가?

### 출력 형식 (JSON)
{{
    "selected_index": 0,
    "decision": "PASS" | "REJECT",
    "fix_scope": "inplace" | "partial" | "full",
    "score": 0-100,
    "contradictions": ["모순 설명 (구체적 — 어떤 사실과 무엇이 충돌하는지)", ...],  // 없으면 빈 배열
    "reason": "선택/판정 이유 (50자 이내)",
    "comparison_notes": "후보별 비교 분석 (각 후보의 장단점)",
    "feedback": "REJECT인 경우 구체적 수정 지침"
}}

[TF-23] fix_scope: REJECT 시 수정 범위 판단. inplace=국소수정, partial=일부씬재작성, full=전면재설계. PASS 시 "inplace".

반드시 유효한 JSON만 출력하세요.
"""

        try:
            response = self._d.ask(comparison_prompt, temperature=0.3, thinking_level="high")
            result = self._d._extract_json_robust(response)

            if not isinstance(result, dict):
                logging.warning("⚠️ [Director] 비교 응답 파싱 실패")
                return self._fallback_first_candidate(
                    candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
                )

            selected_idx = _safe_int(result.get("selected_index", 0), 0)
            if selected_idx < 0 or selected_idx >= len(candidates):
                selected_idx = 0

            decision = result.get("decision", "PASS")
            score = _safe_int(result.get("score", 70), 70)
            comparison_notes = str(result.get("comparison_notes", ""))
            reason = str(result.get("reason", ""))
            contradictions = result.get("contradictions", [])
            if not isinstance(contradictions, list):
                contradictions = []

            logging.info(f"🎯 [Director] 후보 {selected_idx + 1} 선택 ({decision}, 점수: {score})")
            if contradictions:
                logging.warning(f"🚨 [Director] 모순 {len(contradictions)}건 발견:")
                for c in contradictions[:5]:
                    logging.warning(f"   ▸ {str(c)[:120]}")
            else:
                logging.info("✅ [Director] 모순·일관성 이상 없음")
            if comparison_notes:
                logging.info(f"📝 비교: {comparison_notes[:150]}{'...' if len(comparison_notes) > 150 else ''}")
            if reason:
                logging.info(f"💡 이유: {reason[:100]}{'...' if len(reason) > 100 else ''}")

            print(f"\n{'=' * 60}")
            print(f"  [Stage3 Director] Blueprint {decision} (점수: {score})")
            print(f"  선택: 후보 {selected_idx + 1}")
            if reason:
                print(f"  사유: {reason[:200]}")
            if comparison_notes:
                print(f"  비교: {comparison_notes[:200]}")
            if contradictions:
                for c in contradictions[:3]:
                    print(f"  모순: {str(c)[:150]}")
            _bp_feedback = result.get("feedback", "")
            if decision == "REJECT" and _bp_feedback:
                print(f"  피드백: {str(_bp_feedback)[:200]}")
            print(f"{'=' * 60}\n")

            return {
                "decision": decision,
                "selected_index": selected_idx,
                "selected_blueprint": candidates[selected_idx],
                "score": score,
                "contradictions": contradictions,
                "reason": result.get("reason", ""),
                "feedback": result.get("feedback", "") if decision == "REJECT" else "",
                "comparison_notes": result.get("comparison_notes", ""),
                "fix_scope": result.get("fix_scope", ""),  # [TF-23] Director 판단 수정 범위
            }

        except Exception as e:
            logging.warning(f"⚠️ [Director] 비교 오류: {str(e)[:50]}")
            return self._fallback_first_candidate(
                candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
            )

    def _evaluate_single_blueprint(
        self, blueprint: dict, arc_data: dict, ep_num: int, prev_blueprint: dict, entity_registry: dict, state_tracker
    ) -> dict:
        """단일 Blueprint 평가 (기존 audit_manuscript 간소화 버전)"""
        integrated = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)

        arc_no = arc_data.get("arc_no", 0) if arc_data else 0

        if state_tracker:
            dead_violations = state_tracker.check_dead_npc_in_blueprint(blueprint, ep_num, arc_no)
            if dead_violations:
                names = [v["npc_name"] for v in dead_violations]
                return {
                    "decision": "REJECT",
                    "score": 20,
                    "reason": f"죽은 NPC 등장: {', '.join(names)}",
                    "feedback": f"사망한 NPC가 등장합니다: {', '.join(names)}. 회상/언급만 허용됩니다.",
                }

        _sb = blueprint.get("scene_breakdown", {})
        scene_count = len(_sb) if isinstance(_sb, dict | list) else 0  # [TF-R2-S3-01]
        if scene_count < 4:
            return {
                "decision": "REJECT",
                "score": 30,
                "reason": f"씬 개수 부족: {scene_count}개",
                "feedback": "최소 4개 이상의 씬이 필요합니다.",
            }

        if len(integrated) < 800:
            return {
                "decision": "REJECT",
                "score": 40,
                "reason": f"분량 부족: {len(integrated)}자",
                "feedback": "시나리오가 800자 이상이어야 합니다.",
            }

        return {"decision": "PASS", "score": 75, "reason": "기본 기준 충족", "feedback": ""}

    def _fallback_first_candidate(
        self, candidates: list, arc_data: dict, ep_num: int, prev_blueprint: dict, entity_registry: dict, state_tracker
    ) -> dict:
        """폴백: 첫 번째 후보 선택 (비교 실패 시)"""
        logging.warning("⚠️ [Director] 폴백 - 첫 번째 후보 평가")
        result = self._evaluate_single_blueprint(
            candidates[0], arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
        )
        result["selected_index"] = 0
        result["selected_blueprint"] = candidates[0]
        result["comparison_notes"] = "폴백 선택 (비교 실패)"
        return result

    def select_and_judge_ensemble(
        self,
        ep_num: int,
        candidates: list,
        validation_results: list,
        blueprint: dict,
        previous_ending: str,
        arc_pos: int = 1,
        total_eps: int = 5,
        retry_count: int = 0,
        episode_digest: str = "",
        mandatory_context: str = "",
        prev_manuscripts_text: str = "",
        story_context: str = "",
    ) -> dict:
        """[V60.80] 3개 후보 중 최선 선택 + PASS/REJECT 판정"""
        # [Sweep46] 호출자 리스트 변이 방지 — 복사본 사용
        candidates = list(candidates)
        while len(candidates) < 3:
            candidates.append(
                {
                    "strategy": f"fallback_{len(candidates)}",
                    "strategy_name": "폴백",
                    "manuscript": "",
                    "title": "",
                    "state_updates": {},
                }
            )

        # [Sweep59] 호출자 리스트 변이 방지 — 복사본 사용 (candidates와 동일 패턴)
        validation_results = list(validation_results)
        while len(validation_results) < 3:
            validation_results.append({"warnings": ["후보 없음"], "focus_points": ["빈 후보"]})

        MIN_MANUSCRIPT_LENGTH = ManuscriptLimits.MIN_LENGTH  # [V64.P4]
        qualified_indices = []
        for idx, c in enumerate(candidates):
            ms_len = len(c.get("manuscript") or "")
            if ms_len >= MIN_MANUSCRIPT_LENGTH:
                qualified_indices.append(idx)

        if not qualified_indices:
            if not candidates:
                logging.warning("🚨 [V60.97] 빈 후보 리스트 — REJECT 반환")
                return {
                    "selected": "A",
                    "selected_candidate": {"manuscript": "", "error": True},
                    "verdict": "REJECT",
                    "score": 0,
                    "feedback": {
                        "issues": ["빈 후보 리스트: 앙상블 생성 실패"],
                        "action_items": ["원고 생성 과정을 확인하세요"],
                    },
                }
            lengths = [len(c.get("manuscript", "")) for c in candidates]
            best_idx = lengths.index(max(lengths))
            logging.warning(f"🚨 [V60.97] 모든 후보 분량 미달 (최대: {max(lengths)}자 < {MIN_MANUSCRIPT_LENGTH}자)")
            return {
                "selected": ["A", "B", "C"][best_idx],
                "selected_candidate": candidates[best_idx],
                "verdict": "REJECT",
                "score": 30,
                "feedback": {
                    "issues": [f"모든 후보 분량 미달: {lengths}자 (최소 {MIN_MANUSCRIPT_LENGTH}자 필요)"],
                    "action_items": ["분량을 5,000자 이상으로 확장하세요", "장면 묘사와 대사를 더 풍부하게"],
                },
                "state_updates": candidates[best_idx].get("state_updates", {}),
                "action_items": ["분량 확장 필요 - 최소 5,000자"],
                "length_violation": True,
            }

        logging.info(
            f"✅ [V60.97] 분량 통과 후보: {len(qualified_indices)}개 "
            f"({[chr(65 + i) if i < len(candidates) else f'#{i}' for i in qualified_indices]})"
        )

        blueprint_str = (
            json.dumps(blueprint, ensure_ascii=False, indent=2) if isinstance(blueprint, dict) else str(blueprint)
        )

        def get_candidate_info(idx) -> dict:
            c = candidates[idx] if idx < len(candidates) else {}
            v = validation_results[idx] if idx < len(validation_results) else {}
            return {
                "strategy": c.get("strategy_name", c.get("strategy", f"후보{idx + 1}")),
                "manuscript": c.get("manuscript", ""),
                "warnings": "\n".join(v.get("warnings", [])) or "(경고 없음)",
            }

        info_a = get_candidate_info(0)
        info_b = get_candidate_info(1)
        info_c = get_candidate_info(2)

        # [V67] 이전 원고 전문 — 30+화 컨텍스트
        _prev_ms_for_director = prev_manuscripts_text if prev_manuscripts_text else "(이전 원고 없음 — 1화)"
        _prev_ms_for_director = smart_truncate(_prev_ms_for_director)

        # [1M-CTX Phase2] stable/variable 분리 — Director 컨텍스트 캐싱
        _blueprint_esc = self._d._escape_braces(blueprint_str)  # [1M-CTX] 슬라이스 제거 — 전체 게이트(700K) 위임
        _digest_esc = self._d._escape_braces(episode_digest) if episode_digest else "(다이제스트 없음)"
        _ending_esc = self._d._escape_braces(previous_ending if previous_ending else "")
        _prev_ms_esc = self._d._escape_braces(_prev_ms_for_director)
        _story_esc = self._d._escape_braces(story_context) if story_context else "(작품 설정 정보 없음)"

        stable_context = self._prompt_loader.load(
            "director",
            "ENSEMBLE_STABLE_CONTEXT",
            blueprint=_blueprint_esc,
            episode_digest=_digest_esc,
            previous_ending=_ending_esc,
            prev_manuscripts_text=_prev_ms_esc,
            story_context=_story_esc,
        )
        variable_prompt = (
            self._prompt_loader.load(
                "director",
                "ENSEMBLE_VARIABLE_PROMPT",
                strategy_a=info_a["strategy"],
                manuscript_a=self._d._escape_braces(info_a["manuscript"]),
                warnings_a=self._d._escape_braces(info_a["warnings"]),
                strategy_b=info_b["strategy"],
                manuscript_b=self._d._escape_braces(info_b["manuscript"]),
                warnings_b=self._d._escape_braces(info_b["warnings"]),
                strategy_c=info_c["strategy"],
                manuscript_c=self._d._escape_braces(info_c["manuscript"]),
                warnings_c=self._d._escape_braces(info_c["warnings"]),
            )
            if stable_context
            else None
        )

        # mandatory_context 블록 생성 (stable/legacy 양쪽 공통)
        _mc_block = ""
        if mandatory_context:
            _dir_mc_max = _threshold("context.director_mandatory_max", 40000)
            _mc_for_director = mandatory_context[:_dir_mc_max]
            if len(mandatory_context) > _dir_mc_max:
                _mc_for_director = (
                    _mc_for_director[: _dir_mc_max - 50]
                    + f"\n...(mandatory_context {_dir_mc_max:,}자 초과로 일부 생략)"
                )
            _mc_block = f"""

### 📌 [V67] 필수 컨텍스트 (Python 감지 + StateTracker 상태)
아래는 Python 사전 검증 및 StateTracker에서 수집된 세계 상태입니다.
죽은 NPC, 파괴된 장소/아이템, 시간선, 관계 변화 등이 포함되어 있으므로
원고가 이 사실들과 모순되면 반드시 REJECT하세요.

{self._d._escape_braces(_mc_for_director)}
"""

        if not stable_context or not variable_prompt:
            # Fallback: split 프롬프트 없음 → legacy 단일 프롬프트 사용
            prompt = self._prompt_loader.load(
                "director",
                "ENSEMBLE_SELECTION_PROMPT",
                blueprint=_blueprint_esc,
                episode_digest=_digest_esc,
                previous_ending=_ending_esc,
                prev_manuscripts_text=_prev_ms_esc,
                story_context=_story_esc,
                strategy_a=info_a["strategy"],
                manuscript_a=self._d._escape_braces(info_a["manuscript"]),
                warnings_a=self._d._escape_braces(info_a["warnings"]),
                strategy_b=info_b["strategy"],
                manuscript_b=self._d._escape_braces(info_b["manuscript"]),
                warnings_b=self._d._escape_braces(info_b["warnings"]),
                strategy_c=info_c["strategy"],
                manuscript_c=self._d._escape_braces(info_c["manuscript"]),
                warnings_c=self._d._escape_braces(info_c["warnings"]),
            )
            if not prompt:
                logging.warning("[Director] ENSEMBLE_SELECTION_PROMPT not found in prompt loader")
                return {
                    "selected": "A",
                    "selected_candidate": candidates[0] if candidates else {},
                    "verdict": "REJECT",
                    "score": 50,
                    "feedback": {"issues": ["Prompt loading failed: ENSEMBLE_SELECTION_PROMPT"]},
                    "state_updates": (candidates[0].get("state_updates") or {})
                    if candidates
                    else {},  # [TF-R4] LLM null 방어
                    "action_items": ["프롬프트 로더 설정 확인 필요"],
                    "prompt_error": True,
                }
            prompt += _mc_block
            try:
                response = self._d.ask(prompt, temperature=0.1, thinking_level="high")
            except Exception as _ask_err:
                logging.warning("[Director] select_and_judge_ensemble ask() 실패: %s", _ask_err)
                response = ""
        else:
            # [1M-CTX] Caching path — stable context (prev_manuscripts ~180K자) 캐시
            variable_prompt += _mc_block
            # [TF-A] full_fallback 선제 절삭 — variable_prompt 보호
            # _apply_prompt_size_gate()는 단순 head 절삭이므로, 미리 stable_context를 줄여
            # full_fallback이 게이트 이내가 되도록 보장 (variable이 tail에서 잘리는 것 방지)
            _gate = int(getattr(self._d, "MAX_CONTEXT_CHARS", None) or 700_000)
            _stable_budget = max(0, _gate - len(variable_prompt) - 2)
            _stable_for_fallback = (
                stable_context[:_stable_budget] if len(stable_context) > _stable_budget else stable_context
            )
            full_fallback = _stable_for_fallback + "\n\n" + variable_prompt

            cache_name = None
            try:
                cache_info = self._d._get_or_create_context_cache(
                    cache_type="director_ensemble",
                    content=stable_context,
                    ttl_seconds=600,
                    project_name=f"ep{ep_num}",
                )
                cache_name = cache_info.get("cache_name")
                _was_cached = cache_info.get("cached", False)
                logging.info(
                    f"📦 [Director-CACHE] {'HIT' if _was_cached else 'MISS(신규)'}: "
                    f"stable={len(stable_context):,}자, variable={len(variable_prompt):,}자"
                )
            except Exception as _cache_err:
                logging.debug(f"[SILENT] director context caching: {_cache_err}")

            try:
                if cache_name:
                    logging.info(f"✅ [Director] 캐시 경로: variable_prompt만 전송 ({len(variable_prompt):,}자)")
                    response = self._d._ask_with_cached_context(
                        cache_name=cache_name,
                        prompt=variable_prompt,
                        temperature=0.1,
                        thinking_level="high",
                        full_prompt_fallback=full_fallback,
                    )
                else:
                    logging.info(f"⚠️ [Director] fallback 경로: full_fallback 전송 ({len(full_fallback):,}자)")
                    response = self._d.ask(full_fallback, temperature=0.1, thinking_level="high")
            except Exception as _ask_err:
                logging.warning("[Director] select_and_judge_ensemble ask() 실패: %s", _ask_err)
                response = ""
        result = self._d._extract_json_robust(response)

        if not result or result.get("parsing_error"):
            logging.warning("⚠️ [Director] 앙상블 선택 파싱 실패 - 첫 번째 후보 기본 선택")
            return {
                "selected": "A",
                "selected_candidate": candidates[0] if candidates else {},
                "verdict": "REJECT",
                "score": 0,  # [P0-3] 파싱 실패 시 적응형 승격 방지
                "feedback": {"issues": ["Director 판정 파싱 실패"]},
                "state_updates": (candidates[0].get("state_updates") or {})
                if candidates
                else {},  # [TF-R4] LLM null 방어
                "action_items": ["재생성 필요"],
                "parsing_error": True,
            }

        selected_letter = str(result.get("selected", "A")).strip().upper()
        selected_idx = {"A": 0, "B": 1, "C": 2}.get(selected_letter, 0)

        v60_97_swapped = False
        if selected_idx not in qualified_indices and qualified_indices:
            old_selection = selected_letter
            selected_idx = max(qualified_indices, key=lambda i: len(candidates[i].get("manuscript", "")))
            selected_letter = ["A", "B", "C"][selected_idx]
            v60_97_swapped = True
            logging.warning(f"⚠️ [V60.97] LLM 선택 {old_selection} → {selected_letter}로 교체 (분량 기준)")

        selected_candidate = candidates[selected_idx] if selected_idx < len(candidates) else candidates[0]

        original_verdict = result.get("verdict", "REJECT")
        score = _safe_int(result.get("score", 50), 50)
        _pre_firewall_score = score  # [TF-24] 기본값 초기화 (firewall 미작동 시에도 안전)

        if v60_97_swapped:
            score = 50
            original_verdict = "CONDITIONAL_PASS"

        # ── [V75-C] Contradiction Firewall ──────────────────────────
        # NOTE: v60_97_swapped 뒤에 배치 — 방화벽이 swap 승격보다 우선
        _contradiction_check = result.get("contradiction_check", {})
        if isinstance(_contradiction_check, dict):
            _found = _contradiction_check.get("found_contradictions", [])
            if isinstance(_found, list) and _found:
                _critical_count = sum(
                    1 for c in _found if isinstance(c, dict) and str(c.get("severity", "")).upper() == "CRITICAL"
                )
                _major_count = sum(
                    1 for c in _found if isinstance(c, dict) and str(c.get("severity", "")).upper() == "MAJOR"
                )
                _firewall_triggered = False
                if _critical_count >= 1:
                    _firewall_triggered = True
                    logging.warning(f"🚨 [V75-C] Contradiction Firewall: CRITICAL {_critical_count}건 → REJECT 강제")
                elif _major_count >= 2:
                    _firewall_triggered = True
                    logging.warning(f"🚨 [V75-C] Contradiction Firewall: MAJOR {_major_count}건 → REJECT 강제")
                if _firewall_triggered:
                    original_verdict = "REJECT"
                    _pre_firewall_score = score  # [TF-22b] 패치 모드용 원본 점수 보존
                    score = min(score, 44)  # adaptive floor=45 미만 → 승격 불가
                    for _c in _found[:5]:
                        if isinstance(_c, dict):
                            logging.warning(
                                f"   ▸ [{_c.get('severity', '?')}] {str(_c.get('type', ''))}: "
                                f"{str(_c.get('current_violation', ''))[:100]}"
                            )

        adaptive_result = self._d.apply_adaptive_decision(
            score=score,
            original_decision=original_verdict,
            arc_pos=arc_pos,
            total_eps=total_eps,
            retry_count=retry_count,
        )

        final_verdict = adaptive_result["decision"]
        if final_verdict == "CONDITIONAL_PASS":
            if original_verdict == "REJECT":
                # [TF-22b] 디렉터 주권: Director REJECT는 Python이 뒤집지 않음
                final_verdict = "REJECT"
            elif adaptive_result.get("adjusted") and original_verdict == "PASS":
                # [Sweep59] 적응형 하향 조정 (PASS+저점수→REJECT)
                final_verdict = "REJECT"
            elif v60_97_swapped:
                final_verdict = "REJECT"  # 스왑된 후보는 REJECT (적응형이 별도로 승격하지 않는 한)
            else:
                final_verdict = "PASS"

        feedback = result.get("feedback", {})
        if isinstance(feedback, str):
            feedback = {"issues": [feedback]}

        # [V67.2] 자유 형식 리뷰 → feedback에 병합
        _open_review = result.get("open_review", "")
        if _open_review and _open_review not in ("특이사항 없음", "없음", ""):
            if isinstance(feedback, dict):
                _existing_issues = feedback.get("issues", [])
                _existing_issues.append(f"[자유 리뷰] {_open_review}")
                feedback["issues"] = _existing_issues

        # --- Director 판정 상세 출력 ---
        print(f"\n{'=' * 60}")
        print(f"  [Stage4 Director] 원고 앙상블 판정: {final_verdict} (점수: {score})")
        print(f"  선택: 후보 {selected_letter} | 원래 판정: {original_verdict}")
        _sel_reason = result.get("selection_reason", "")
        if _sel_reason:
            print(f"  선택 사유: {str(_sel_reason)[:200]}")
        _sb = result.get("score_breakdown", {})
        if _sb:
            _sb_str = ", ".join(f"{k}={v}" for k, v in _sb.items() if isinstance(v, int | float))
            if _sb_str:
                print(f"  점수 분해: {_sb_str}")
        _issues = feedback.get("issues", []) if isinstance(feedback, dict) else []
        if _issues:
            for _iss in _issues[:5]:
                print(f"  이슈: {str(_iss)[:150]}")
        if _open_review and _open_review not in ("특이사항 없음", "없음", ""):
            print(f"  자유 리뷰: {_open_review[:200]}")
        if adaptive_result.get("reason"):
            print(f"  적응형: {adaptive_result['reason']}")
        print(f"{'=' * 60}\n")

        return {
            "selected": selected_letter,
            "selected_candidate": selected_candidate,
            "verdict": final_verdict,
            "original_verdict": original_verdict,
            "score": score,
            "pre_firewall_score": _pre_firewall_score,  # [TF-22b] 패치 모드용
            "score_breakdown": result.get("score_breakdown", {}),
            "selection_reason": result.get("selection_reason", ""),
            "feedback": feedback,
            "state_updates": result.get("state_updates")
            or selected_candidate.get("state_updates")
            or {},  # [TF-R4] LLM null 방어
            "action_items": feedback.get("action_items", []) if isinstance(feedback, dict) else [],
            "other_candidates_notes": result.get("other_candidates_notes", {}),
            "adaptive_threshold": adaptive_result.get("threshold_used", 65),
            "adaptive_reason": adaptive_result.get("reason", ""),
            "error_category": result.get("error_category", ""),  # [V75-B] LOGIC_ERROR 전파
            "fix_scope": result.get("fix_scope", ""),  # [TF-23] Director 판단 수정 범위
        }

    def quick_judge_single(
        self, ep_num: int, manuscript: str, blueprint: dict, previous_ending: str, retry_count: int = 0
    ) -> dict:
        """[V60.80] 냉동인간 Writer용 간소 검토"""
        if len(manuscript) < 3500:
            return {"verdict": "REJECT", "score": 20, "reason": f"분량 심각 부족: {len(manuscript)}자 (최소 3,500자)"}

        prompt = f"""
[Role] 편집장 (Emergency Review)
[Task] 냉동인간 Writer가 생성한 원고를 빠르게 검토하라.

### 원고 (제{ep_num}화)
{self._d._escape_braces(manuscript[:6000])}

### Blueprint 요약
{self._d._escape_braces(str(blueprint)[:5000])}

### 판정 기준 (완화됨)
1. 분량 3,500자 이상: OK
2. 치명적 설정 오류 없음: OK
3. 최소한의 서사 진행: OK

[Output Format] JSON Only
{{
    "verdict": "PASS" 또는 "REJECT",
    "score": 0-100,
    "reason": "판정 사유",
    "critical_issues": ["치명적 문제 (있을 경우)"]
}}
"""

        response = self._d.ask(prompt, temperature=0.1)
        result = self._d._extract_json_robust(response)

        if not result or result.get("parsing_error"):
            if len(manuscript) >= 3500:
                return {
                    "verdict": "REJECT",
                    "score": 45,
                    "reason": "간소 검토 파싱 실패 - 분량 충족이나 품질 검증 불가로 REJECT",
                    "forced": True,
                }
            return {"verdict": "REJECT", "score": 30, "reason": "간소 검토 파싱 실패 + 분량 미달"}

        # [G5] critical_issues가 list가 아닐 수 있음 (LLM 응답 안전성)
        _issues = result.get("critical_issues", [])
        if not isinstance(_issues, list):
            _issues = [_issues] if _issues else []

        return {
            "verdict": result.get("verdict", "REJECT"),
            "score": result.get("score", 50),
            "reason": result.get("reason", ""),
            "critical_issues": _issues,
        }
