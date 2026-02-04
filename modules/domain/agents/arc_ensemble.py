"""
[V60.11] Arc Ensemble Generator
병렬로 다수 Arc 후보를 생성하고 최적 후보를 선택

Strategy:
1. 3개의 서로 다른 전략으로 Arc 후보 생성 (병렬)
2. 각 후보를 빠르게 검증 (Python 기반)
3. 점수가 가장 높은 후보 선택
4. 모든 후보가 실패하면 피드백 통합하여 재생성

Cost: ~3x single generation (but higher pass rate)
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_agent import BaseAgent
from modules.core.constants import Stage2Limits


# 다양한 생성 전략
GENERATION_STRATEGIES = [
    {
        "name": "conservative",
        "temperature": 0.3,
        "focus": "안정성과 연속성 우선. 이전 Arc 상태를 정확히 계승하고, 새로운 요소는 최소화.",
        "style": "기존 설정 활용 중심"
    },
    {
        "name": "balanced",
        "temperature": 0.5,
        "focus": "연속성과 새로움의 균형. 이전 상태를 계승하면서 적절한 새 갈등 도입.",
        "style": "균형 잡힌 전개"
    },
    {
        "name": "creative",
        "temperature": 0.7,
        "focus": "서사적 흥미 우선. 연속성을 유지하면서 예상치 못한 전개 시도.",
        "style": "창의적 전개"
    }
]


ENSEMBLE_ARC_PROMPT = """
[V60.11 ENSEMBLE ARC GENERATOR - {strategy_name} 전략]

##############################################################
# 🔒 [V60.18] 주인공 정보 - 반드시 이 이름을 사용!
##############################################################
주인공 이름: {protagonist_name}
→ tactical_doc에서 반드시 '{protagonist_name}'을 사용하세요!
→ 다른 이름(이현, 강민수 등)은 절대 사용 금지!
##############################################################

##############################################################
# 🚨🚨🚨 [V60.13] 최우선 금지 사항 - 위반 시 즉시 REJECT 🚨🚨🚨
##############################################################
{prohibition_summary}
##############################################################

### 생성 전략
{strategy_focus}
스타일: {strategy_style}

### [🚨 ABSOLUTE CONSTRAINTS - 위반 시 0점]

████████████████████████████████████████████████████████████████████████████████
█   🚨 [V60.38] tactical_doc 분량 필수 - 위반 시 즉시 REJECT                   █
█   ⚠️ 총 분량: 최소 (ep_count × 500)자 이상                                   █
█   ⚠️ 1,500자 미만 = CRITICAL REJECT (시스템 자동 거부)                        █
████████████████████████████████████████████████████████████████████████████████

⚠️ CRITICAL: tactical_doc 내용과 state_constraints는 반드시 일치해야 합니다!
- 이전 Arc 종료 시 내공이 70%이면, tactical_doc에서도 "내공 70%" 또는 "7할의 내공"으로 표현
- "2할" "20%" 같은 다른 수치 사용 금지
- 부상 상태도 state_constraints.arc_start_state와 동일하게 표현

{constraint_block}

### [이전 Arc 상태 - 반드시 계승]
{prev_arc_context}

### [현재 블록 DNA]
{curr_block}

### [Volume 전략]
{vol_strategy}

### [AssetLibrary]
{assets}

### [피드백 (있다면)]
{feedback}

### [V60.40] 화간 상태 체크포인트 필수
각 화는 반드시 시작 상태와 종료 상태를 명시하라:
- 시작 상태: 위치, 내공%, 부상, 소지품 (이전 화 종료 상태와 동일)
- 종료 상태: 위치, 내공%, 부상, 획득/소모 아이템

### [Output JSON Schema]
{{
    "arc_no": {arc_no},
    "ep_count": "3~7 중 사건 밀도에 맞게 결정",
    "ep_start": {ep_start},
    "ep_end": {ep_end},
    "title": "Arc 제목",
    "tactical_doc": "[V60.40] 각 화마다 시작/종료 상태 체크포인트 필수. 화당 500자 이상. '제 N화:' 형식으로 화별 명확 구분",
    "beat_sequence": ["제 N화: 핵심 비트", ...],
    "hybrid_composition": {{
        "primary": "주 서사 패턴",
        "secondary": ["부 패턴"],
        "mixing_logic": "패턴 조합 전략"
    }},
    "state_constraints": {{
        "arc_start_state": {{
            "location": "시작 위치 (이전 Arc 종료 위치와 동일해야 함)",
            "equipment": ["소지품 (이전 Arc 종료 시 소지품과 동일)"],
            "injuries": "부상 상태 (이전 Arc 부상 계승)",
            "internal_energy": 내공_퍼센트
        }},
        "arc_end_state": {{
            "location": "종료 위치",
            "equipment": ["종료 시 소지품"],
            "injuries": "종료 시 부상",
            "internal_energy": 내공_퍼센트
        }},
        "items_acquired": ["새로 획득 아이템 (이전에 없던 것만)"],
        "items_consumed": ["소모 아이템"],
        "grants_received": ["수여받은 것"]
    }},
    "joint_docs": {{
        "final_location": "Arc 종료 시 정확한 위치",
        "physical_inventory": ["종료 시 소지품 전체 목록"],
        "world_joint": "다음 Arc가 계승할 세계 변화"
    }},
    "status_shadow": {{
        "internal_energy_loss": "N%",
        "expected_injuries": "부상 상태",
        "item_consumption": ["소모된 아이템"]
    }}
}}

반드시 유효한 JSON만 출력하세요.
"""


class ArcEnsembleGenerator(BaseAgent):
    """
    [V60.11] Arc Ensemble Generator

    병렬로 3개 Arc 후보 생성 후 최적 선택
    """

    def __init__(self, context, client, model_tier: str = "gemini-3-pro-preview"):
        # [V60.24] Gemini 3로 변경 - 최고 품질의 Arc 생성
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정: gemini-3 → gemini-2.5-pro)
        self.strategies = GENERATION_STRATEGIES
        self.max_workers = 3

    def generate_ensemble(
        self,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: Dict,
        prev_arc_context: str,
        constraint_block: str,
        assets: Dict = None,
        feedback: str = "",
        protagonist_name: str = "주인공"  # [V60.18] 주인공 이름 (필수!)
    ) -> Tuple[Optional[Dict], List[Dict]]:
        """
        앙상블 Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            vol_strategy: Volume 전략
            curr_block: 현재 블록 DNA
            prev_arc_context: 이전 Arc 맥락
            constraint_block: 제약 조건 블록
            assets: AssetLibrary
            feedback: 이전 피드백
            protagonist_name: [V60.18] 주인공 이름 (환각 방지)

        Returns:
            (best_arc, all_candidates) - 최적 Arc와 모든 후보 리스트
        """
        # [V60.73] ep_count 기반 ep_end 계산 (기존 고정값 +4 오류 수정)
        ep_count = curr_block.get("ep_count", 5) if isinstance(curr_block, dict) else 5
        ep_end = ep_start + ep_count - 1
        candidates = []

        # 병렬 생성
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for strategy in self.strategies:
                future = executor.submit(
                    self._generate_single,
                    arc_no=arc_no,
                    ep_start=ep_start,
                    ep_end=ep_end,
                    vol_strategy=vol_strategy,
                    curr_block=curr_block,
                    prev_arc_context=prev_arc_context,
                    constraint_block=constraint_block,
                    assets=assets,
                    feedback=feedback,
                    strategy=strategy,
                    protagonist_name=protagonist_name  # [V60.18]
                )
                futures[future] = strategy["name"]

            for future in as_completed(futures):
                strategy_name = futures[future]
                try:
                    result = future.result()
                    if result:
                        result["_strategy"] = strategy_name
                        candidates.append(result)
                except Exception as e:
                    print(f"      ⚠️ [Ensemble] {strategy_name} 전략 실패: {str(e)[:50]}")

        if not candidates:
            return None, []

        # [V60.73] tactical_doc 최소 길이 필터 (가변 페이싱: 화당 500자)
        min_tactical_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE  # 3화=1500자, 5화=2500자, 7화=3500자
        valid_candidates = []
        for candidate in candidates:
            # [V60.74] tactical_doc 타입 안전 변환 (dict/list 처리)
            tactical = candidate.get("tactical_doc", "")
            tactical = self._safe_tactical_str(tactical)
            candidate["tactical_doc"] = tactical  # 변환된 값으로 업데이트
            tactical_len = len(tactical)
            if tactical_len >= min_tactical_length:
                valid_candidates.append(candidate)
            else:
                print(f"      ⚠️ [Ensemble] {candidate.get('_strategy', '?')} 제외: tactical_doc {tactical_len}자 < {min_tactical_length}자 (ep_count={ep_count})")

        # [V60.74] 유효한 후보가 없으면 최장 후보 선택 + 경고 레벨 판단
        if not valid_candidates:
            def safe_tactical_len(x):
                t = x.get("tactical_doc", "")
                return len(t) if isinstance(t, str) else len(str(t)) if t else 0

            candidates.sort(key=safe_tactical_len, reverse=True)
            longest = candidates[0]
            longest_len = safe_tactical_len(longest)
            min_required = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE

            # 권장값의 60% 미만이면 경고 레벨 높임
            if longest_len < min_required * 0.6:
                print(f"      🚨 [Ensemble] 모든 후보 심각한 분량 부족: {longest_len}자 < {int(min_required * 0.6)}자 (권장의 60%)")
                print(f"         → Critic/Consensus에서 REJECT 가능성 높음")
            else:
                print(f"      ⚠️ [Ensemble] 모든 후보 분량 미달, 최대 분량 후보 선택: {longest_len}자")

            valid_candidates = candidates[:1]

        # 후보 평가 및 선택
        scored_candidates = []
        for candidate in valid_candidates:
            score, issues = self._evaluate_candidate(candidate, prev_arc_context, constraint_block)
            candidate["_score"] = score
            candidate["_issues"] = issues
            scored_candidates.append(candidate)

        # 점수순 정렬
        scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)

        best = scored_candidates[0]
        # [V60.37] 타입 안전성
        best_tactical = best.get("tactical_doc", "")
        tactical_len = len(best_tactical) if isinstance(best_tactical, str) else len(str(best_tactical)) if best_tactical else 0
        print(f"      🏆 [Ensemble] 최적 후보 선택: {best.get('_strategy')} (점수: {best.get('_score', 0)}, tactical: {tactical_len}자)")

        # [V60.74] 메타데이터 보존 (디버깅용) - _ensemble_meta에 저장
        ensemble_meta = {
            "best_strategy": best.get("_strategy", "unknown"),
            "best_score": best.get("_score", 0),
            "all_scores": [(c.get("_strategy", "?"), c.get("_score", 0)) for c in scored_candidates],
            "total_candidates": len(scored_candidates)
        }
        best["_ensemble_meta"] = ensemble_meta

        # 메타데이터 제거 후 반환 (단, _ensemble_meta는 유지)
        for c in scored_candidates:
            c.pop("_strategy", None)
            c.pop("_score", None)
            c.pop("_issues", None)

        return best, scored_candidates

    def _generate_single(
        self,
        arc_no: int,
        ep_start: int,
        ep_end: int,
        vol_strategy: str,
        curr_block: Dict,
        prev_arc_context: str,
        constraint_block: str,
        assets: Dict,
        feedback: str,
        strategy: Dict,
        protagonist_name: str = "주인공"  # [V60.18]
    ) -> Optional[Dict]:
        """단일 전략으로 Arc 생성"""
        try:
            # [V60.13] 최우선 금지 요약 생성 - 프롬프트 최상단에 배치
            prohibition_summary = self._generate_prohibition_summary(prev_arc_context, constraint_block)

            prompt = ENSEMBLE_ARC_PROMPT.format(
                strategy_name=strategy["name"].upper(),
                strategy_focus=strategy["focus"],
                strategy_style=strategy["style"],
                prohibition_summary=prohibition_summary,
                protagonist_name=protagonist_name,  # [V60.18]
                constraint_block=self._escape_braces(constraint_block or "(없음)"),
                prev_arc_context=self._escape_braces(prev_arc_context or "시작점"),
                curr_block=self._escape_braces(json.dumps(curr_block, ensure_ascii=False)[:3000] if curr_block else "{}"),
                vol_strategy=self._escape_braces(vol_strategy[:2000] if vol_strategy else "(없음)"),
                assets=self._escape_braces(json.dumps(assets, ensure_ascii=False)[:2000] if assets else "{}"),
                feedback=self._escape_braces(feedback[:1500] if feedback else "(없음)"),
                arc_no=arc_no,
                ep_start=ep_start,
                ep_end=ep_end
            )

            # [V60.27] Thinking Level "high" 적용 - Arc 생성 품질 향상
            result = self.ask(prompt, temperature=strategy["temperature"], thinking_level="high")

            if isinstance(result, str):
                result = json.loads(result)

            # 필수 필드 보장
            result = self._ensure_required_fields(result, arc_no, ep_start, ep_end)

            return result

        except Exception as e:
            print(f"      ⚠️ [Ensemble] {strategy['name']} 생성 오류: {str(e)[:50]}")
            return None

    def _evaluate_candidate(
        self,
        candidate: Dict,
        prev_arc_context: str,
        constraint_block: str
    ) -> Tuple[int, List[str]]:
        """
        후보 평가 (100점 만점)

        평가 기준:
        - 필수 필드 완성도 (20점)
        - 제약 조건 준수 (30점)
        - 연속성 (25점)
        - tactical_doc 품질 (25점)
        """
        score = 100
        issues = []

        # 1. 필수 필드 완성도 (20점)
        required_fields = ["arc_no", "ep_count", "tactical_doc", "joint_docs", "state_constraints"]
        for field in required_fields:
            if field not in candidate or not candidate[field]:
                score -= 4
                issues.append(f"필수 필드 누락: {field}")

        # 2. 제약 조건 준수 (30점)
        if constraint_block:
            # 획득 금지 아이템 검사
            items_acquired = candidate.get("state_constraints", {}).get("items_acquired", [])
            tactical = candidate.get("tactical_doc", "")
            # [V60.37] 타입 안전성
            if not isinstance(tactical, str):
                tactical = str(tactical) if tactical else ""

            # 금지 아이템 패턴 추출
            forbidden_items = re.findall(r'❌\s*([가-힣\w]+)', constraint_block)
            for item in forbidden_items:
                if item in str(items_acquired) or f"획득" in tactical and item in tactical:
                    score -= 15
                    issues.append(f"금지 아이템 획득 시도: {item}")

        # 3. 연속성 (25점)
        if prev_arc_context and prev_arc_context != "서사 시작점":
            # 시작 위치 검사
            start_state = candidate.get("state_constraints", {}).get("arc_start_state", {})
            if "위치" in prev_arc_context:
                prev_loc_match = re.search(r'위치[:\]]\s*([가-힣\w\s]+)', prev_arc_context)
                if prev_loc_match:
                    prev_loc = prev_loc_match.group(1).strip()[:20]
                    curr_loc = start_state.get("location", "")
                    if prev_loc and curr_loc and prev_loc not in curr_loc and curr_loc not in prev_loc:
                        score -= 10
                        issues.append(f"시작 위치 불일치: 이전={prev_loc}, 현재={curr_loc}")

            # 소지품 계승 검사
            if "소지품" in prev_arc_context:
                prev_inv_match = re.search(r'소지품[:\]]\s*([^\n]+)', prev_arc_context)
                if prev_inv_match:
                    prev_inv = prev_inv_match.group(1).strip()
                    curr_equip = start_state.get("equipment", [])
                    # 주요 아이템이 계승되었는지 간단히 체크
                    key_items = re.findall(r'([가-힣]+(?:도|검|창|궁|패|인장))', prev_inv)
                    for item in key_items[:3]:  # 최대 3개만 검사
                        if item not in str(curr_equip):
                            score -= 5
                            issues.append(f"소지품 미계승: {item}")

        # 4. tactical_doc 품질 (25점) - [V60.73] 가변 페이싱 기준 (화당 500자)
        tactical = candidate.get("tactical_doc", "")
        # [V60.37] 타입 안전성
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""
        ep_count = candidate.get("ep_count", 5)
        min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE  # 3화=1500자, 5화=2500자, 7화=3500자
        recommended_length = ep_count * 600  # 권장: 화당 600자
        if len(tactical) < min_length:
            score -= 40  # 최소 기준 미달은 사실상 실격
            issues.append(f"[CRITICAL] tactical_doc 분량 심각 부족: {len(tactical)}자 (최소 {min_length}자, ep_count={ep_count})")
        elif len(tactical) < recommended_length:
            score -= 10
            issues.append(f"tactical_doc 분량 미흡: {len(tactical)}자 (권장 {recommended_length}자)")
        elif len(tactical) < ep_count * 700:
            score -= 5
            issues.append(f"tactical_doc 분량 보통: {len(tactical)}자")

        # 화수별 구분 검사
        ep_count = candidate.get("ep_count", 5)
        ep_mentions = len(re.findall(r'제\s*\d+\s*화', tactical))
        if ep_mentions < ep_count:
            score -= 5
            issues.append(f"화수 구분 부족: {ep_mentions}/{ep_count}")

        return max(0, score), issues

    def _ensure_required_fields(self, result: Dict, arc_no: int, ep_start: int, ep_end: int) -> Dict:
        """필수 필드 보장"""
        if "arc_no" not in result:
            result["arc_no"] = arc_no
        if "ep_start" not in result:
            result["ep_start"] = ep_start
        if "ep_end" not in result:
            result["ep_end"] = ep_end
        if "ep_count" not in result:
            result["ep_count"] = ep_end - ep_start + 1

        if "state_constraints" not in result:
            result["state_constraints"] = {
                "arc_start_state": {"location": "이전 Arc 종료 위치", "equipment": []},
                "arc_end_state": {"location": "알 수 없음", "equipment": []},
                "items_acquired": [],
                "items_consumed": []
            }

        if "joint_docs" not in result:
            result["joint_docs"] = {
                "final_location": "알 수 없음",
                "physical_inventory": [],
                "world_joint": ""
            }

        if "status_shadow" not in result:
            result["status_shadow"] = {
                "internal_energy_loss": "0%",
                "expected_injuries": "없음",
                "item_consumption": []
            }

        return result

    def _safe_tactical_str(self, tactical) -> str:
        """
        [V60.74] tactical_doc을 안전하게 문자열로 변환

        Args:
            tactical: str, dict, list, None 등 다양한 타입

        Returns:
            str: 변환된 문자열
        """
        if isinstance(tactical, str):
            return tactical
        if tactical is None:
            return ""
        if isinstance(tactical, dict):
            # dict라면 값들을 조인 (content, text 등 우선 시도)
            if "content" in tactical:
                return str(tactical["content"])
            if "text" in tactical:
                return str(tactical["text"])
            # 그 외에는 모든 값 조인
            return "\n".join(str(v) for v in tactical.values() if v)
        if isinstance(tactical, list):
            return "\n".join(str(item) for item in tactical if item)
        # 기타 타입
        return str(tactical)

    def _generate_prohibition_summary(self, prev_arc_context: str, constraint_block: str) -> str:
        """
        [V60.13] 최우선 금지 사항 요약 생성

        프롬프트 최상단에 배치하여 LLM이 절대 무시할 수 없도록 함
        """
        lines = []

        # 1. 시작 상태 추출 (prev_arc_context에서)
        if prev_arc_context:
            # 내공 추출
            import re
            energy_match = re.search(r'내공[:\s]*(\d+)%', prev_arc_context)
            if energy_match:
                lines.append(f"✅ 시작 내공: {energy_match.group(1)}% (이 수치로 시작해야 함!)")

            # 부상 추출
            injury_patterns = ['완치', '없음', '중상', '경상', '부상']
            for pattern in injury_patterns:
                if pattern in prev_arc_context:
                    if pattern in ['완치', '없음']:
                        lines.append(f"✅ 시작 부상: 없음 (건강한 상태로 시작!)")
                    else:
                        lines.append(f"✅ 시작 부상: {pattern} (이 상태로 시작!)")
                    break

        # 2. 금지 아이템 추출 (constraint_block에서)
        if constraint_block:
            # ❌ 패턴 추출
            forbidden = re.findall(r'❌\s*([^\n❌]+)', constraint_block)
            if forbidden:
                lines.append("")
                lines.append("🚫 절대 다시 획득/수여 금지:")
                for item in forbidden[:10]:  # 최대 10개
                    clean_item = item.strip()[:50]
                    if clean_item:
                        lines.append(f"   ❌ {clean_item}")

        # 3. 기본 경고
        if not lines:
            lines.append("(금지 사항 없음 - 첫 Arc)")

        return "\n".join(lines)

    def _escape_braces(self, text: str) -> str:
        """중괄호 이스케이프"""
        if not isinstance(text, str):
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")


def create_ensemble_generator(context, client, model_tier: str = "gemini-3-pro-preview"):
    """[V60.24] ArcEnsembleGenerator 생성 헬퍼 - Gemini 3 사용"""
    return ArcEnsembleGenerator(context, client, model_tier)
