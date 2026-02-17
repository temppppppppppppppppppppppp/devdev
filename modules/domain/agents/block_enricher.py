"""
V60.10 Block Enricher Agent
Treatment Block 자동 농축 에이전트

Purpose:
- 정보량이 부족한 Block을 Arc 설계 전에 자동 농축
- Block 1 수준의 품질로 모든 Block을 표준화
- 인접 Block과의 인과 연결 보장
"""

import json
import re

from .base_agent import BaseAgent

# ═══════════════════════════════════════════════════════════════════════════
# ENRICHMENT PROMPT
# ═══════════════════════════════════════════════════════════════════════════

BLOCK_ENRICHMENT_PROMPT = """
[Role] Treatment Block 농축 전문가 (Block Enrichment Specialist)
[Task] 정보량이 부족한 Block을 고품질 기준(Reference Block)에 맞춰 농축하라.

### [🚨 SYSTEM RESTRICTION: JSON ONLY]
1. 답변의 첫 글자는 반드시 {{, 마지막 글자는 반드시 }}
2. 설명, 인사말, 서문 절대 금지
3. 오직 유효한 JSON만 출력

### [📐 품질 기준 - Reference Block]
아래 Block이 "이상적인 정보 밀도"의 기준이다. 이 수준으로 농축하라:
```
{reference_block}
```

### [🎯 농축 대상 Block]
```
{current_block}
```

### [📚 컨텍스트]
- 이전 Block (상태 계승 필수): {prev_block}
- 다음 Block (미래 정보 오염 금지): {next_block}
- 주인공 이름: {protagonist_name}
- 장르: {genre}

### [🔧 농축 필수 항목]

1. **context 확장** (최소 200자):
   - 시간: 이전 Block으로부터 며칠 후인지 명시
   - 공간: 구체적 지명 (예: "남문 밖 천금루", "가문 서쪽 별채")
   - 상태: 주인공의 현재 내공/부상/소지품 상태
   - 감각: 장소의 냄새, 소리, 온도 묘사

2. **event_villain 확장** (최소 150자):
   - NPC 이름: 최소 2명의 구체적 이름 (예: "심복 유삼", "도박장주 마오")
   - 세력: 적의 규모와 구성 (예: "수하 30여 명, 그중 고수 3명")
   - 수법: 구체적 위협/계략 (예: "지하 금고에 황금 오천 냥 은닉")
   - 동기: 왜 이 행동을 하는지

3. **solution 확장** (최소 150자):
   - 전술: 주인공의 구체적 접근법
   - 물리적 묘사: 무공/동작의 세부 (예: "도의 무게로 문짝을 박살")
   - 제약: 현재 상태에서의 한계 (예: "내공 삼할 상태라 연속 세 초식이 한계")
   - 돌파: 어떻게 제약을 극복하는지

4. **reward 확장** (최소 100자):
   - 물질: 구체적 금액/아이템 (예: "황금 삼천 냥", "철갑 30벌")
   - 관계: NPC 반응 변화 (예: "사병 50명이 '경외'로 전환")
   - 상태: 주인공 상태 변화 (예: "내공 일할 소모, 좌측 어깨 경미한 타박")
   - 복선: 다음 Block으로 이어질 요소

### [🚫 금지 사항]
1. 다음 Block의 내용을 미리 언급하지 마라
2. 이전 Block에서 아직 없는 아이템/능력을 사용하지 마라
3. Reference Block의 고유명사를 그대로 복사하지 마라 (참고만 할 것)
4. 원본 Block의 핵심 사건을 변경하지 마라 (디테일만 추가)

### [📤 Output Format]
{{
    "block_id": "{block_id}",
    "title": "원본 유지 또는 소폭 개선",
    "content": {{
        "context": "농축된 context (200자+)",
        "event_villain": "농축된 event_villain (150자+)",
        "solution": "농축된 solution (150자+)",
        "reward": "농축된 reward (100자+)"
    }},
    "enrichment_metadata": {{
        "added_npcs": ["추가된 NPC 이름들"],
        "added_locations": ["추가된 장소명들"],
        "added_numbers": ["추가된 수치들 (금액, 수량 등)"],
        "time_from_prev": "이전 Block으로부터 경과 시간",
        "state_inheritance": "이전 Block에서 계승한 상태"
    }}
}}
"""


ENRICHMENT_VALIDATION_PROMPT = """
[Role] Block 농축 검증관 (Enrichment Validator)
[Task] 농축된 Block이 원본의 의도를 훼손하지 않았는지 검증하라.

### [원본 Block]
{original_block}

### [농축된 Block]
{enriched_block}

### [이전 Block]
{prev_block}

### [다음 Block]
{next_block}

### [검증 항목]
1. **의도 보존**: 원본의 핵심 사건이 유지되었는가?
2. **인과 연결**: 이전 Block의 결과가 반영되었는가?
3. **미래 오염 없음**: 다음 Block의 내용이 미리 노출되지 않았는가?
4. **수치 합리성**: 추가된 금액/수량이 서사적으로 적절한가?
5. **NPC 일관성**: 추가된 NPC가 기존 설정과 충돌하지 않는가?

### [Output Format - JSON Only]
{{
    "validation_result": "PASS" 또는 "FAIL",
    "issues": ["발견된 문제점들"],
    "suggestions": ["개선 제안"],
    "confidence_score": 0.0~1.0
}}
"""


DIRECTOR_BLOCK_AUDIT_PROMPT = """
[Role] 서사 품질 감독관 (Director - Block Quality Auditor)
[Task] 농축된 Block이 Arc 설계에 사용하기에 충분한 품질인지 심사하라.

### [🚨 SYSTEM RESTRICTION: JSON ONLY]
답변의 첫 글자는 반드시 {{, 마지막 글자는 반드시 }}

### [농축된 Block]
{enriched_block}

### [이전 Block] (인과 계승 확인용)
{prev_block}

### [다음 Block] (미래 오염 확인용)
{next_block}

### [원본 Block] (의도 보존 확인용)
{original_block}

### [심사 기준 - 모두 통과해야 PASS]

1. **핵심 사건 보존** (30점)
   - 원본의 context/event_villain/solution/reward 핵심이 유지되었는가?
   - 농축 과정에서 원작자의 의도가 왜곡되지 않았는가?

2. **인과 연결성** (25점)
   - 이전 Block의 결과(reward)가 현재 Block의 전제로 반영되었는가?
   - 시간 흐름이 명시되었는가? (예: "3일 후", "다음 날")
   - 상태 계승이 명시되었는가? (부상, 내공, 소지품)

3. **미래 정보 차단** (25점)
   - 다음 Block의 고유명사나 사건이 미리 언급되지 않았는가?
   - 아직 만나지 않은 NPC나 얻지 않은 아이템이 등장하지 않았는가?

4. **수치 일관성** (10점)
   - 금액/수량/내공 수치가 합리적인가?
   - 이전 Block의 수치와 충돌하지 않는가?

5. **NPC/장소 구체성** (10점)
   - 구체적인 NPC 이름이 추가되었는가?
   - 구체적인 장소명이 추가되었는가?

### [Output Format - JSON Only]
{{
    "decision": "PASS" 또는 "REJECT",
    "total_score": 0-100,
    "score_breakdown": {{
        "core_preservation": 0-30,
        "causal_connection": 0-25,
        "future_block": 0-25,
        "numeric_consistency": 0-10,
        "specificity": 0-10
    }},
    "critical_issues": ["치명적 문제 (있으면 무조건 REJECT)"],
    "warnings": ["경고 (PASS 가능하지만 개선 권장)"],
    "feedback": "수정 지시 (REJECT 시)"
}}
"""


class BlockEnricher(BaseAgent):
    """
    V60.10 Treatment Block 농축 에이전트

    Features:
    - Block 1을 품질 기준으로 사용
    - 인접 Block 참조하여 인과 연결
    - 자동 검증으로 품질 보장
    """

    def __init__(self, context, client, model_tier: str = None):
        """
        BlockEnricher 초기화

        Args:
            context: ProjectContext (프로젝트 컨텍스트)
            client: genai.Client (API 클라이언트)
            model_tier: 사용할 모델 (V60.24: Flash - 농축용)
        """
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정: gemini-3-flash → gemini-2.5-flash)

    def analyze_block_density(self, block: dict) -> dict:
        """
        Block의 정보량을 분석하여 농축 필요 여부 판단

        Returns:
            {
                "needs_enrichment": bool,
                "density_score": float (0-1),
                "missing_elements": list,
                "word_count": int
            }
        """
        content = block.get("content", {})
        if isinstance(content, str):
            # content가 문자열인 경우
            total_text = content
        else:
            # content가 dict인 경우
            total_text = " ".join(
                [
                    str(content.get("context", "")),
                    str(content.get("event_villain", "")),
                    str(content.get("solution", "")),
                    str(content.get("reward", "")),
                ]
            )

        word_count = len(total_text)

        # 필수 요소 체크
        missing = []

        # 구체적 금액/수량 체크
        if not re.search(r"[0-9천백만억]+\s*(냥|냥|개|명|벌|자루|알)", total_text):
            missing.append("specific_numbers")

        # 구체적 NPC 이름 체크 (따옴표로 감싸진 이름)
        if not re.search(r"['\"][\w가-힣]+['\"]|[\w가-힣]{2,4}(이|가|을|를|에게|의)", total_text):
            # 더 관대한 체크 - 한글 이름 패턴
            npc_pattern = re.search(r"(심복|부하|수하|적|도박장주|두목|대장)\s*[\w가-힣]{2,4}", total_text)
            if not npc_pattern:
                missing.append("npc_names")

        # 구체적 장소명 체크
        if not re.search(r"['\"][\w가-힣]+[루당각전관문원]|[\w가-힣]+\s*(안|밖|앞|뒤|옆)", total_text):
            missing.append("location_names")

        # 시간 정보 체크
        if not re.search(r"\d+\s*(일|시간|각|경|달|년)|다음\s*날|그\s*날|며칠|사흘|이틀|하루", total_text):
            missing.append("time_info")

        # 상태 정보 체크
        if not re.search(r"(내공|기력|부상|상처|회복).*(할|푼|%|퍼센트)", total_text):
            missing.append("state_info")

        # 밀도 점수 계산
        density_score = min(1.0, word_count / 500)  # 500자 기준
        element_score = (5 - len(missing)) / 5
        final_score = (density_score * 0.4) + (element_score * 0.6)

        return {
            "needs_enrichment": final_score < 0.7 or len(missing) >= 2,
            "density_score": round(final_score, 2),
            "missing_elements": missing,
            "word_count": word_count,
            "content_breakdown": {  # [V70] content가 str이면 dict.get() 불가 → 분기
                "context": len(str(content.get("context", ""))) if isinstance(content, dict) else len(content),
                "event_villain": len(str(content.get("event_villain", ""))) if isinstance(content, dict) else 0,
                "solution": len(str(content.get("solution", ""))) if isinstance(content, dict) else 0,
                "reward": len(str(content.get("reward", ""))) if isinstance(content, dict) else 0,
            },
        }

    def enrich_block(
        self,
        current_block: dict,
        reference_block: dict,
        prev_block: dict | None = None,
        next_block: dict | None = None,
        protagonist_name: str = "주인공",
        genre: str = "wuxia",
    ) -> dict:
        """
        Block을 Reference Block 수준으로 농축

        Args:
            current_block: 농축할 Block
            reference_block: 품질 기준 Block (보통 Block 1)
            prev_block: 이전 Block (상태 계승용)
            next_block: 다음 Block (미래 오염 방지용)
            protagonist_name: 주인공 이름
            genre: 장르

        Returns:
            농축된 Block dict
        """
        # 농축 필요 여부 먼저 체크
        density_analysis = self.analyze_block_density(current_block)

        if not density_analysis["needs_enrichment"]:
            return {
                "enriched": False,
                "reason": "이미 충분한 정보량",
                "density_score": density_analysis["density_score"],
                "block": current_block,
            }

        # 프롬프트 구성
        prompt = BLOCK_ENRICHMENT_PROMPT.format(
            reference_block=json.dumps(reference_block, ensure_ascii=False, indent=2),
            current_block=json.dumps(current_block, ensure_ascii=False, indent=2),
            prev_block=json.dumps(prev_block, ensure_ascii=False, indent=2) if prev_block else "없음 (첫 번째 Block)",
            next_block=json.dumps(next_block, ensure_ascii=False, indent=2) if next_block else "없음 (마지막 Block)",
            block_id=current_block.get("block_id", "Unknown"),
            protagonist_name=protagonist_name,
            genre=genre,
        )

        # LLM 호출
        try:
            result = self.ask(prompt, temperature=0.7)

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70] json.loads → robust parser

            # 검증
            validation = self._validate_enrichment(
                original=current_block, enriched=result, prev_block=prev_block, next_block=next_block
            )

            if validation.get("validation_result") == "FAIL":
                # 1차 검증 실패 → 원본 보존 패치 모드
                _original_text = json.dumps(result, ensure_ascii=False, indent=2)[:20000]
                retry_prompt = (
                    prompt + f"\n\n[🔧 패치 모드: 이전 농축 결과 원본 보존 + 지적사항만 수정]"
                    f"\n## 이전 농축 결과\n{_original_text}"
                    f"\n\n## 검증 실패 피드백\n{json.dumps(validation.get('issues', []), ensure_ascii=False)}"
                    f"\n\n⚠️ 전면 재농축하지 마세요. 지적된 부분만 수정하세요."
                )
                result = self.ask(retry_prompt, temperature=0.5)
                if isinstance(result, str):
                    result = self._extract_json_robust(result)  # [V70]
                # 재검증
                validation = self._validate_enrichment(
                    original=current_block, enriched=result, prev_block=prev_block, next_block=next_block
                )

            # [V60.10] Director 품질 심사 (2차 검증)
            director_audit = self._director_audit_block(
                original=current_block, enriched=result, prev_block=prev_block, next_block=next_block
            )

            if director_audit.get("decision") == "REJECT":
                # Director REJECT → 원본 보존 패치 모드
                feedback = director_audit.get("feedback", "품질 미달")
                critical_issues = director_audit.get("critical_issues", [])
                _original_text = json.dumps(result, ensure_ascii=False, indent=2)[:20000]

                retry_prompt = (
                    prompt
                    + f"""

[🔧 패치 모드: 이전 농축 결과 원본 보존 + Director 지적사항만 수정]

## 이전 농축 결과
{_original_text}

## Director 심사 REJECT
점수: {director_audit.get("total_score", 0)}/100
치명적 문제: {json.dumps(critical_issues, ensure_ascii=False)}
수정 지시: {feedback}

⚠️ 전면 재농축하지 마세요. 지적된 부분만 수정하세요.
"""
                )
                result = self.ask(retry_prompt, temperature=0.4)
                if isinstance(result, str):
                    result = self._extract_json_robust(result)  # [V70]

                # 재심사
                director_audit = self._director_audit_block(
                    original=current_block, enriched=result, prev_block=prev_block, next_block=next_block
                )

            return {
                "enriched": True,
                "original_density": density_analysis["density_score"],
                "missing_elements": density_analysis["missing_elements"],
                "block": result,
                "validation": validation,
                "director_audit": director_audit,
            }

        except Exception as e:
            return {"enriched": False, "reason": f"농축 실패: {str(e)}", "block": current_block}

    def _validate_enrichment(
        self, original: dict, enriched: dict, prev_block: dict | None, next_block: dict | None
    ) -> dict:
        """농축 결과 1차 검증 (Self-Check)"""

        prompt = ENRICHMENT_VALIDATION_PROMPT.format(
            original_block=json.dumps(original, ensure_ascii=False, indent=2),
            enriched_block=json.dumps(enriched, ensure_ascii=False, indent=2),
            prev_block=json.dumps(prev_block, ensure_ascii=False, indent=2) if prev_block else "없음",
            next_block=json.dumps(next_block, ensure_ascii=False, indent=2) if next_block else "없음",
        )

        try:
            # [V60.24] Flash (빠른 검증용)
            original_model = self.primary_model
            try:  # [V70] 예외 시 primary_model 복원 보장 (레이스 컨디션 방지)
                self.primary_model = "gemini-3-flash-preview"
                result = self.ask(prompt, temperature=0.3)
            finally:
                self.primary_model = original_model

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70] json.loads → robust parser

            return result

        except Exception as e:
            return {
                "validation_result": "PASS",  # 검증 실패 시 일단 통과
                "issues": [f"검증 오류: {str(e)}"],
                "confidence_score": 0.5,
            }

    def _director_audit_block(
        self, original: dict, enriched: dict, prev_block: dict | None, next_block: dict | None
    ) -> dict:
        """
        [V60.10] Director 품질 심사

        농축된 Block이 Arc 설계에 사용하기 적합한지 Director가 심사합니다.
        70점 이상이면 PASS, 미만이면 REJECT.
        """

        prompt = DIRECTOR_BLOCK_AUDIT_PROMPT.format(
            original_block=json.dumps(original, ensure_ascii=False, indent=2),
            enriched_block=json.dumps(enriched, ensure_ascii=False, indent=2),
            prev_block=json.dumps(prev_block, ensure_ascii=False, indent=2) if prev_block else "없음 (첫 번째 Block)",
            next_block=json.dumps(next_block, ensure_ascii=False, indent=2) if next_block else "없음 (마지막 Block)",
        )

        try:
            # [V60.24] Flash (빠른 심사용)
            original_model = self.primary_model
            try:  # [V70] 예외 시 primary_model 복원 보장
                self.primary_model = "gemini-3-flash-preview"
                result = self.ask(prompt, temperature=0.3)
            finally:
                self.primary_model = original_model

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70] json.loads → robust parser

            # 점수 기반 PASS/REJECT 결정
            total_score = result.get("total_score", 0)
            if total_score >= 70:
                result["decision"] = "PASS"
            else:
                result["decision"] = "REJECT"

            return result

        except Exception as e:
            return {
                "decision": "PASS",  # 심사 실패 시 일단 통과 (Block 자체 문제 아님)
                "total_score": 70,
                "error": str(e),
                "critical_issues": [],
                "warnings": [f"Director 심사 오류: {str(e)}"],
            }

    def enrich_all_blocks(
        self,
        treatment_blocks: list,
        protagonist_name: str = "주인공",
        genre: str = "wuxia",
        reference_block_index: int = 0,
    ) -> dict:
        """
        전체 Treatment를 일괄 농축

        Args:
            treatment_blocks: 전체 Block 리스트
            protagonist_name: 주인공 이름
            genre: 장르
            reference_block_index: 품질 기준 Block 인덱스 (기본 0 = Block 1)

        Returns:
            {
                "enriched_blocks": list,
                "statistics": {
                    "total": int,
                    "enriched_count": int,
                    "skipped_count": int,
                    "failed_count": int
                }
            }
        """
        reference_block = treatment_blocks[reference_block_index]
        enriched_blocks = []
        stats = {"total": len(treatment_blocks), "enriched_count": 0, "skipped_count": 0, "failed_count": 0}

        for i, block in enumerate(treatment_blocks):
            # Reference block은 그대로 유지
            if i == reference_block_index:
                enriched_blocks.append(block)
                stats["skipped_count"] += 1
                continue

            prev_block = treatment_blocks[i - 1] if i > 0 else None
            next_block = treatment_blocks[i + 1] if i < len(treatment_blocks) - 1 else None

            result = self.enrich_block(
                current_block=block,
                reference_block=reference_block,
                prev_block=prev_block,
                next_block=next_block,
                protagonist_name=protagonist_name,
                genre=genre,
            )

            if result.get("enriched"):
                enriched_blocks.append(result["block"])
                stats["enriched_count"] += 1
            elif result.get("reason") == "이미 충분한 정보량":
                enriched_blocks.append(block)
                stats["skipped_count"] += 1
            else:
                enriched_blocks.append(block)  # 실패 시 원본 유지
                stats["failed_count"] += 1

        return {"enriched_blocks": enriched_blocks, "statistics": stats}

    # ═══════════════════════════════════════════════════════════════════════════
    # [V60.10] 병렬 농축 + 인과 검증
    # ═══════════════════════════════════════════════════════════════════════════

    def enrich_all_blocks_parallel(
        self,
        treatment_blocks: list,
        protagonist_name: str = "주인공",
        genre: str = "wuxia",
        reference_block_index: int = 0,
        batch_size: int = 5,
        ui=None,
    ) -> dict:
        """
        [V60.10] 병렬 농축 + 인과 검증 + 문제 Block 재농축

        Flow:
        1. 배치 단위 병렬 농축 (Rate Limit 회피)
        2. 전체 인과 에러 검증 (LLM 일괄)
        3. 문제 Block만 재농축 (농축된 prev_block 참조)
        """
        import concurrent.futures

        reference_block = treatment_blocks[reference_block_index]
        enriched_blocks = [None] * len(treatment_blocks)
        enriched_blocks[reference_block_index] = treatment_blocks[reference_block_index]

        stats = {
            "total": len(treatment_blocks),
            "enriched_count": 0,
            "skipped_count": 1,  # reference block
            "failed_count": 0,
            "causal_fixes": 0,
        }

        # 농축 대상 인덱스 수집
        enrich_targets = []
        for i, block in enumerate(treatment_blocks):
            if i == reference_block_index:
                continue
            analysis = self.analyze_block_density(block)
            if analysis["needs_enrichment"]:
                enrich_targets.append(i)
            else:
                enriched_blocks[i] = block
                stats["skipped_count"] += 1

        if ui:
            ui.log(f"   📊 병렬 농축 대상: {len(enrich_targets)}개 (배치 크기: {batch_size})")

        # ─────────────────────────────────────────────────────────────────────
        # Phase 1: 배치 병렬 농축
        # ─────────────────────────────────────────────────────────────────────
        def enrich_single(idx) -> tuple:
            block = treatment_blocks[idx]
            prev_block = treatment_blocks[idx - 1] if idx > 0 else None
            next_block = treatment_blocks[idx + 1] if idx < len(treatment_blocks) - 1 else None

            result = self.enrich_block(
                current_block=block,
                reference_block=reference_block,
                prev_block=prev_block,
                next_block=next_block,
                protagonist_name=protagonist_name,
                genre=genre,
            )
            return idx, result

        # 배치 단위로 병렬 처리
        for batch_start in range(0, len(enrich_targets), batch_size):
            batch = enrich_targets[batch_start : batch_start + batch_size]
            if ui:
                ui.log(f"   🔄 배치 {batch_start // batch_size + 1}: Block {batch[0] + 1}~{batch[-1] + 1} 처리 중...")

            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = {executor.submit(enrich_single, idx): idx for idx in batch}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        idx, result = future.result()
                        if result.get("enriched") and result.get("block"):
                            enriched_blocks[idx] = result["block"]
                            stats["enriched_count"] += 1
                        else:
                            enriched_blocks[idx] = treatment_blocks[idx]
                            stats["failed_count"] += 1
                    except Exception as e:
                        idx = futures[future]
                        enriched_blocks[idx] = treatment_blocks[idx]
                        stats["failed_count"] += 1
                        if ui:
                            ui.log(f"      ⚠️ Block {idx + 1} 농축 실패: {str(e)[:30]}")

            # [V66.1] Rate Limit 딜레이 제거 (BaseAgent.API_DELAY에서 이미 적용)

        # ─────────────────────────────────────────────────────────────────────
        # Phase 2: 인과 에러 검증
        # ─────────────────────────────────────────────────────────────────────
        if ui:
            ui.log("   🔍 인과 에러 검증 중...")

        causal_issues = self._check_causal_errors(enriched_blocks)

        if causal_issues:
            if ui:
                ui.log(f"   ⚠️ 인과 에러 {len(causal_issues)}건 발견 → 재농축 시작")

            # ─────────────────────────────────────────────────────────────────
            # Phase 3: 문제 Block 재농축 (농축된 prev_block 참조)
            # ─────────────────────────────────────────────────────────────────
            for issue in causal_issues:
                idx = issue.get("block_index") if isinstance(issue, dict) else None
                if idx is None or idx <= 0 or idx >= len(enriched_blocks):
                    continue

                issue_text = issue.get("issue", "인과 에러") if isinstance(issue, dict) else str(issue)
                if ui:
                    ui.log(f"      🔧 Block {idx + 1} 재농축 (사유: {str(issue_text)[:30]}...)")

                # 농축된 prev_block 참조 (None이면 원본 사용)
                enriched_prev = enriched_blocks[idx - 1]
                if enriched_prev is None:
                    enriched_prev = treatment_blocks[idx - 1]
                next_block = treatment_blocks[idx + 1] if idx < len(treatment_blocks) - 1 else None

                # 재농축 프롬프트에 인과 에러 피드백 포함
                result = self._re_enrich_with_causal_fix(
                    current_block=treatment_blocks[idx],
                    enriched_prev_block=enriched_prev,
                    next_block=next_block,
                    reference_block=reference_block,
                    causal_issue=issue_text,
                    protagonist_name=protagonist_name,
                    genre=genre,
                )

                if result.get("enriched") and result.get("block"):
                    enriched_blocks[idx] = result["block"]
                    stats["causal_fixes"] += 1
        else:
            if ui:
                ui.log("   ✅ 인과 에러 없음")

        return {
            "enriched_blocks": enriched_blocks,
            "statistics": stats,
            "causal_issues_found": len(causal_issues) if causal_issues else 0,
        }

    def _check_causal_errors(self, enriched_blocks: list) -> list:
        """
        [V60.10] 전체 농축 Block의 인과 에러 일괄 검증

        Returns:
            [{"block_index": int, "issue": str}, ...]
        """
        # Block 요약 생성 (전체를 LLM에 보내기엔 너무 크므로 요약)
        block_summaries = []
        for i, block in enumerate(enriched_blocks):
            if block is None:
                continue
            content = block.get("content", {})
            if isinstance(content, dict):
                reward = content.get("reward", "")[:100]
                context = content.get("context", "")[:100]
            else:
                reward = ""
                context = str(content)[:100]
            block_summaries.append(
                {
                    "block_id": block.get("block_id", f"Block {i + 1}"),
                    "index": i,
                    "context_snippet": context,
                    "reward_snippet": reward,
                }
            )

        prompt = f"""[Role] 인과 연속성 검증관
[Task] 아래 Block들의 인과 연결을 검증하고, 문제가 있는 Block을 찾아라.

### [Block 요약]
{json.dumps(block_summaries, ensure_ascii=False, indent=2)}

### [검증 항목]
1. Block N의 reward에서 획득한 것이 Block N+1의 context에 언급/반영되는가?
2. 시간 흐름이 자연스러운가? (역행 없음)
3. 상태 계승이 되는가? (부상, 소지품 등)

### [Output Format - JSON Only]
{{
    "has_issues": true/false,
    "issues": [
        {{"block_index": N, "issue": "문제 설명"}},
        ...
    ]
}}

인과 에러가 없으면 "issues": []로 반환.
"""

        try:
            # [V60.24] Flash (빠른 검증용)
            original_model = self.primary_model
            try:  # [V70] 예외 시 primary_model 복원 보장
                self.primary_model = "gemini-3-flash-preview"
                result = self.ask(prompt, temperature=0.2)
            finally:
                self.primary_model = original_model

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70] json.loads → robust parser

            return result.get("issues", [])

        except Exception as e:
            return []  # 검증 실패 시 빈 리스트 (에러 없음 처리)

    def _re_enrich_with_causal_fix(
        self,
        current_block: dict,
        enriched_prev_block: dict,
        next_block: dict | None,
        reference_block: dict,
        causal_issue: str,
        protagonist_name: str,
        genre: str,
    ) -> dict:
        """
        [V60.10] 인과 에러 수정을 위한 재농축

        농축된 prev_block을 참조하여 인과 연결을 보장.
        """
        # prev_block의 reward 추출 (None 방어)
        if enriched_prev_block is None:
            prev_content = {}
        else:
            prev_content = enriched_prev_block.get("content", {}) if isinstance(enriched_prev_block, dict) else {}
        if isinstance(prev_content, dict):
            prev_reward = prev_content.get("reward", "정보 없음")
        else:
            prev_reward = str(prev_content)[-200:]

        prompt = f"""[Role] 인과 수정 전문가
[Task] 아래 Block을 재농축하되, 이전 Block과의 인과 연결을 반드시 보장하라.

### [🚨 인과 에러 수정 필수]
발견된 문제: {causal_issue}

### [🔗 이전 Block의 결과 - 반드시 계승]
{prev_reward}

### [📐 품질 기준]
{json.dumps(reference_block, ensure_ascii=False)[:500]}

### [🎯 재농축 대상]
{json.dumps(current_block, ensure_ascii=False, indent=2)}

### [📚 다음 Block] (미래 오염 금지)
{json.dumps(next_block, ensure_ascii=False)[:300] if next_block else "없음"}

### [🔧 필수 수정사항]
1. context 시작부에 이전 Block의 결과(획득물, 상태변화)를 자연스럽게 언급
2. 시간 흐름 명시 (예: "3일 후", "다음 날 아침")
3. 상태 계승 (부상, 내공, 소지품)

### [Output Format - JSON Only]
{{
    "block_id": "{current_block.get("block_id", "Unknown")}",
    "title": "제목",
    "content": {{
        "context": "인과 연결된 context",
        "event_villain": "...",
        "solution": "...",
        "reward": "..."
    }}
}}
"""

        try:
            result = self.ask(prompt, temperature=0.5)

            if isinstance(result, str):
                result = self._extract_json_robust(result)  # [V70]

            return {"enriched": True, "block": result, "causal_fixed": True}

        except Exception as e:
            return {"enriched": False, "reason": f"재농축 실패: {str(e)}", "block": current_block}
