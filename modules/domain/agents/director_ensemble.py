"""
[V64 P2-1] Director EnsembleSelector — 앙상블 선택 전담 모듈

Director God Object 분해의 세 번째 단계.
Blueprint/Manuscript 후보 비교, 선택, 판정을 담당.
Director reference를 통해 BaseAgent 메서드(ask, _extract_json_robust 등) 접근.
"""

import json
import logging
from modules.core.constants import ManuscriptLimits  # [V64.P4]

# [V64.P4] 프롬프트 외부화 — director_prompts.py에서 import
from .director_prompts import ENSEMBLE_SELECTION_PROMPT


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

    def compare_and_select_blueprint(
        self,
        candidates: list,
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict = None,
        entity_registry: dict = None,
        state_tracker=None
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
                "comparison_notes": ""
            }

        if len(candidates) == 1:
            single_result = self._evaluate_single_blueprint(
                candidates[0], arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
            )
            single_result["selected_index"] = 0
            single_result["selected_blueprint"] = candidates[0] if single_result["decision"] == "PASS" else None
            single_result["comparison_notes"] = "단일 후보"
            return single_result

        logging.info(f"🎭 [Director] {len(candidates)}개 후보 비교 중...")

        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)

        prev_ending = ""
        if prev_blueprint:
            prev_ending = prev_blueprint.get("ending_hook", "")
            prev_location = prev_blueprint.get("end_location", "")
            if prev_location:
                prev_ending = f"위치: {prev_location}, 훅: {prev_ending}"

        candidate_summaries = []
        for idx, bp in enumerate(candidates):
            meta = bp.get("_ensemble_meta", {})
            strategy = meta.get("strategy", f"후보{idx+1}")
            scene_count = meta.get("scene_count", len(bp.get("scene_breakdown", {})))
            length = meta.get("length", len(bp.get("integrated_scenario", "")))

            integrated = bp.get("integrated_scenario", "")
            if not isinstance(integrated, str):
                integrated = str(integrated) if integrated else ""

            summary = f"""
[후보 {idx+1}: {strategy}]
- 씬 개수: {scene_count}개
- 분량: {length}자
- 시작 위치: {bp.get('start_location', '?')}
- 종료 위치: {bp.get('end_location', '?')}
- 시간 흐름: {bp.get('time_flow', '?')}
- 엔딩 훅: {(bp.get('ending_hook') or '?')[:100]}

[시나리오 요약]
{integrated[:1500]}...
"""
            candidate_summaries.append(summary)

        comparison_prompt = f"""[V60.85 Blueprint 비교 선택]

당신은 웹소설 시리즈의 품질 관리 감독입니다.
제{ep_num}화 Blueprint 후보 {len(candidates)}개 중 최적의 것을 선택하고 판정하세요.

### Arc 전술서 (이번 화 기준)
{arc_tactical[:2000]}

### 이전 화 정보
{prev_ending if prev_ending else "(1화 또는 이전 정보 없음)"}

### 후보 목록
{''.join(candidate_summaries)}

### 평가 기준
1. **Arc 준수**: 전술서의 이번 화 내용을 충실히 반영하는가?
2. **연속성**: 이전 화 종료 상태에서 자연스럽게 이어지는가?
3. **서사 밀도**: 씬 구성과 시나리오가 충분히 풍부한가?
4. **다음 화 연결**: 적절한 훅으로 마무리하는가?

### 출력 형식 (JSON)
{{
    "selected_index": 0,  // 0부터 시작, 가장 좋은 후보 번호
    "decision": "PASS" | "REJECT",  // 선택한 후보도 기준 미달이면 REJECT
    "score": 0-100,
    "reason": "선택/판정 이유 (50자 이내)",
    "comparison_notes": "후보별 비교 분석 (각 후보의 장단점)",
    "feedback": "REJECT인 경우 수정 지침"
}}

반드시 유효한 JSON만 출력하세요.
"""

        try:
            response = self._d.ask(comparison_prompt, temperature=0.3, thinking_level="high")
            result = self._d._extract_json_robust(response)

            if not isinstance(result, dict):
                logging.warning(f"⚠️ [Director] 비교 응답 파싱 실패")
                return self._fallback_first_candidate(candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker)

            selected_idx = result.get("selected_index", 0)
            if selected_idx < 0 or selected_idx >= len(candidates):
                selected_idx = 0

            decision = result.get("decision", "PASS")
            score = result.get("score", 70)
            comparison_notes = result.get("comparison_notes", "")
            reason = result.get("reason", "")

            logging.info(f"🎯 [Director] 후보 {selected_idx+1} 선택 ({decision}, 점수: {score})")
            if comparison_notes:
                logging.info(f"📝 비교: {comparison_notes[:150]}{'...' if len(comparison_notes) > 150 else ''}")
            if reason:
                logging.info(f"💡 이유: {reason[:100]}{'...' if len(reason) > 100 else ''}")

            return {
                "decision": decision,
                "selected_index": selected_idx,
                "selected_blueprint": candidates[selected_idx] if decision == "PASS" else None,
                "score": score,
                "reason": result.get("reason", ""),
                "feedback": result.get("feedback", "") if decision == "REJECT" else "",
                "comparison_notes": result.get("comparison_notes", "")
            }

        except Exception as e:
            logging.warning(f"⚠️ [Director] 비교 오류: {str(e)[:50]}")
            return self._fallback_first_candidate(candidates, arc_data, ep_num, prev_blueprint, entity_registry, state_tracker)

    def _evaluate_single_blueprint(
        self,
        blueprint: dict,
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict,
        entity_registry: dict,
        state_tracker
    ) -> dict:
        """단일 Blueprint 평가 (기존 audit_manuscript 간소화 버전)"""
        integrated = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

        arc_tactical = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical, dict):
            arc_tactical = json.dumps(arc_tactical, ensure_ascii=False)

        prev_ending = prev_blueprint.get("ending_hook", "") if prev_blueprint else ""

        arc_no = arc_data.get("arc_no", 0) if arc_data else 0

        if state_tracker:
            dead_violations = state_tracker.check_dead_npc_in_blueprint(blueprint, ep_num, arc_no)
            if dead_violations:
                names = [v["npc_name"] for v in dead_violations]
                return {
                    "decision": "REJECT",
                    "score": 20,
                    "reason": f"죽은 NPC 등장: {', '.join(names)}",
                    "feedback": f"사망한 NPC가 등장합니다: {', '.join(names)}. 회상/언급만 허용됩니다."
                }

        scene_count = len(blueprint.get("scene_breakdown", {}))
        if scene_count < 4:
            return {
                "decision": "REJECT",
                "score": 30,
                "reason": f"씬 개수 부족: {scene_count}개",
                "feedback": "최소 4개 이상의 씬이 필요합니다."
            }

        if len(integrated) < 800:
            return {
                "decision": "REJECT",
                "score": 40,
                "reason": f"분량 부족: {len(integrated)}자",
                "feedback": "시나리오가 800자 이상이어야 합니다."
            }

        return {
            "decision": "PASS",
            "score": 75,
            "reason": "기본 기준 충족",
            "feedback": ""
        }

    def _fallback_first_candidate(
        self,
        candidates: list,
        arc_data: dict,
        ep_num: int,
        prev_blueprint: dict,
        entity_registry: dict,
        state_tracker
    ) -> dict:
        """폴백: 첫 번째 후보 선택 (비교 실패 시)"""
        logging.info(f"⚠️ [Director] 폴백 - 첫 번째 후보 평가")
        result = self._evaluate_single_blueprint(
            candidates[0], arc_data, ep_num, prev_blueprint, entity_registry, state_tracker
        )
        result["selected_index"] = 0
        result["selected_blueprint"] = candidates[0] if result["decision"] == "PASS" else None
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
        story_context: str = ""
    ) -> dict:
        """[V60.80] 3개 후보 중 최선 선택 + PASS/REJECT 판정"""
        while len(candidates) < 3:
            candidates.append({
                "strategy": f"fallback_{len(candidates)}",
                "strategy_name": "폴백",
                "manuscript": "",
                "title": "",
                "state_updates": {}
            })

        while len(validation_results) < 3:
            validation_results.append({
                "warnings": ["후보 없음"],
                "focus_points": ["빈 후보"]
            })

        MIN_MANUSCRIPT_LENGTH = ManuscriptLimits.MIN_LENGTH  # [V64.P4]
        qualified_indices = []
        for idx, c in enumerate(candidates):
            ms_len = len(c.get("manuscript", ""))
            if ms_len >= MIN_MANUSCRIPT_LENGTH:
                qualified_indices.append(idx)

        if not qualified_indices:
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
                    "action_items": ["분량을 5,000자 이상으로 확장하세요", "장면 묘사와 대사를 더 풍부하게"]
                },
                "state_updates": {},
                "action_items": ["분량 확장 필요 - 최소 5,000자"],
                "length_violation": True
            }

        logging.info(f"✅ [V60.97] 분량 통과 후보: {len(qualified_indices)}개 ({[['A','B','C'][i] for i in qualified_indices]})")

        blueprint_str = json.dumps(blueprint, ensure_ascii=False, indent=2) if isinstance(blueprint, dict) else str(blueprint)

        def get_candidate_info(idx) -> dict:
            c = candidates[idx] if idx < len(candidates) else {}
            v = validation_results[idx] if idx < len(validation_results) else {}
            return {
                "strategy": c.get("strategy_name", c.get("strategy", f"후보{idx+1}")),
                "manuscript": c.get("manuscript", "")[:12000],
                "warnings": "\n".join(v.get("warnings", [])) or "(경고 없음)"
            }

        info_a = get_candidate_info(0)
        info_b = get_candidate_info(1)
        info_c = get_candidate_info(2)

        # [V67] 이전 원고 전문 — 30+화 컨텍스트
        _prev_ms_for_director = prev_manuscripts_text if prev_manuscripts_text else "(이전 원고 없음 — 1화)"
        # Gemini 컨텍스트 윈도우가 크므로 넉넉히 전달 (최대 200K자)
        if len(_prev_ms_for_director) > 200000:
            _prev_ms_for_director = _prev_ms_for_director[:200000] + "\n...(이하 생략)"

        prompt = ENSEMBLE_SELECTION_PROMPT.format(
            blueprint=self._d._escape_braces(blueprint_str[:5000]),
            episode_digest=self._d._escape_braces(episode_digest) if episode_digest else "(다이제스트 없음)",
            previous_ending=self._d._escape_braces(previous_ending if previous_ending else ""),
            prev_manuscripts_text=self._d._escape_braces(_prev_ms_for_director),
            story_context=self._d._escape_braces(story_context) if story_context else "(작품 설정 정보 없음)",
            strategy_a=info_a["strategy"],
            manuscript_a=self._d._escape_braces(info_a["manuscript"]),
            warnings_a=self._d._escape_braces(info_a["warnings"]),
            strategy_b=info_b["strategy"],
            manuscript_b=self._d._escape_braces(info_b["manuscript"]),
            warnings_b=self._d._escape_braces(info_b["warnings"]),
            strategy_c=info_c["strategy"],
            manuscript_c=self._d._escape_braces(info_c["manuscript"]),
            warnings_c=self._d._escape_braces(info_c["warnings"])
        )

        # [V67] mandatory_context 확장 — 25,000자 상한 (기존 8,000자)
        if mandatory_context:
            _mc_for_director = mandatory_context[:25000]
            if len(mandatory_context) > 25000:
                _mc_for_director = _mc_for_director[:24950] + "\n...(mandatory_context 25,000자 초과로 일부 생략)"
            prompt += f"""

### 📌 [V67] 필수 컨텍스트 (Python 감지 + StateTracker 상태)
아래는 Python 사전 검증 및 StateTracker에서 수집된 세계 상태입니다.
죽은 NPC, 파괴된 장소/아이템, 시간선, 관계 변화 등이 포함되어 있으므로
원고가 이 사실들과 모순되면 반드시 REJECT하세요.

{self._d._escape_braces(_mc_for_director)}
"""

        response = self._d.ask(prompt, temperature=0.1, thinking_level="high")
        result = self._d._extract_json_robust(response)

        if not result or result.get("parsing_error"):
            logging.warning("⚠️ [Director] 앙상블 선택 파싱 실패 - 첫 번째 후보 기본 선택")
            return {
                "selected": "A",
                "selected_candidate": candidates[0] if candidates else {},
                "verdict": "REJECT",
                "score": 50,
                "feedback": {"issues": ["Director 판정 파싱 실패"]},
                "state_updates": candidates[0].get("state_updates", {}) if candidates else {},
                "action_items": ["재생성 필요"],
                "parsing_error": True
            }

        selected_letter = result.get("selected", "A").upper()
        selected_idx = {"A": 0, "B": 1, "C": 2}.get(selected_letter, 0)

        v60_97_swapped = False
        if selected_idx not in qualified_indices and qualified_indices:
            old_selection = selected_letter
            selected_idx = qualified_indices[0]
            selected_letter = ["A", "B", "C"][selected_idx]
            v60_97_swapped = True
            logging.info(f"⚠️ [V60.97] LLM 선택 {old_selection} → {selected_letter}로 교체 (분량 기준)")

        selected_candidate = candidates[selected_idx] if selected_idx < len(candidates) else candidates[0]

        original_verdict = result.get("verdict", "REJECT")
        score = result.get("score", 50)

        if v60_97_swapped:
            score = 50
            original_verdict = "CONDITIONAL_PASS"

        adaptive_result = self._d.apply_adaptive_decision(
            score=score,
            original_decision=original_verdict,
            arc_pos=arc_pos,
            total_eps=total_eps,
            retry_count=retry_count
        )

        final_verdict = adaptive_result["decision"]
        if final_verdict == "CONDITIONAL_PASS":
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

        return {
            "selected": selected_letter,
            "selected_candidate": selected_candidate,
            "verdict": final_verdict,
            "original_verdict": original_verdict,
            "score": score,
            "score_breakdown": result.get("score_breakdown", {}),
            "selection_reason": result.get("selection_reason", ""),
            "feedback": feedback,
            "state_updates": result.get("state_updates", selected_candidate.get("state_updates", {})),
            "action_items": feedback.get("action_items", []) if isinstance(feedback, dict) else [],
            "other_candidates_notes": result.get("other_candidates_notes", {}),
            "adaptive_threshold": adaptive_result.get("threshold_used", 65),
            "adaptive_reason": adaptive_result.get("reason", "")
        }

    def quick_judge_single(
        self,
        ep_num: int,
        manuscript: str,
        blueprint: dict,
        previous_ending: str,
        retry_count: int = 0
    ) -> dict:
        """[V60.80] 냉동인간 Writer용 간소 검토"""
        if len(manuscript) < 3500:
            return {
                "verdict": "REJECT",
                "score": 20,
                "reason": f"분량 심각 부족: {len(manuscript)}자 (최소 3,500자)"
            }

        prompt = f"""
[Role] 편집장 (Emergency Review)
[Task] 냉동인간 Writer가 생성한 원고를 빠르게 검토하라.

### 원고 (제{ep_num}화)
{self._d._escape_braces(manuscript[:6000])}

### Blueprint 요약
{self._d._escape_braces(str(blueprint)[:1500])}

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
                    "forced": True
                }
            return {
                "verdict": "REJECT",
                "score": 30,
                "reason": "간소 검토 파싱 실패 + 분량 미달"
            }

        return {
            "verdict": result.get("verdict", "REJECT"),
            "score": result.get("score", 50),
            "reason": result.get("reason", ""),
            "critical_issues": result.get("critical_issues", [])
        }
