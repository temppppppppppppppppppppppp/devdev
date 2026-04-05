"""[LM-E] 회상/플래시백 오염 감지기 — 원고 내 회상 장면의 내용 정합성 advisory.

TruthGate recall_patterns(사망 NPC 회상 허용 필터)와 분리된 독립 클래스.
원고 본문의 회상/플래시백 장면이 과거 에피소드 맥락과 모순되는지를 LLM으로 감지.
Advisory-only: Director가 최종 판정.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

MAX_FLASHBACKS = 5
CONTEXT_WINDOW = 200


class FlashbackVerifier:
    """원고 내 회상/플래시백 장면의 내용 오염을 LLM으로 감지 (advisory only)."""

    FLASHBACK_MARKERS = [
        "회상",
        "기억했다",
        "떠올렸다",
        "떠올랐다",
        "눈을 감으면",
        "그 시절",
        "예전에",
        "돌이켜보면",
        "몇 년 전",
        "몇 달 전",
        "그때의",
        "과거의",
        "지난날",
        "옛날에",
    ]

    def __init__(self, llm_ask=None):
        """
        Args:
            llm_ask: Optional callable(prompt: str) -> str. None이면 검사 스킵.
        """
        self._llm_ask = llm_ask

    def check(self, manuscript, *, ep_num=0, reference_context="", manuscript_snippets=""):
        """회상/플래시백 오염 검사.

        Args:
            manuscript: 원고 텍스트
            ep_num: 현재 에피소드 번호
            reference_context: VecMemory에서 검색한 과거 에피소드 맥락 (요약)
            manuscript_snippets: [LM-H] 과거 에피소드 원고 발췌 (원문 대조용)

        Returns:
            list[dict]: [{"marker", "issue", "referenced_context", "severity", "check"}]
        """
        if not manuscript:
            return []

        flashbacks = self.detect_flashbacks(manuscript)
        if not flashbacks:
            return []

        if not self._llm_ask or not reference_context:
            return []

        return self._llm_check(flashbacks, reference_context, ep_num, manuscript_snippets)

    def detect_flashbacks(self, manuscript):
        """원고에서 회상 구간을 추출 (Python 수집만).

        Returns:
            list[dict]: [{"marker": str, "text": str, "position": int}]
        """
        if not manuscript:
            return []

        found = []
        used_ranges = []

        for marker in self.FLASHBACK_MARKERS:
            for match in re.finditer(re.escape(marker), manuscript):
                pos = match.start()

                # 기존 구간과 겹치는지 확인
                overlaps = False
                for start, end in used_ranges:
                    if start <= pos <= end:
                        overlaps = True
                        break
                if overlaps:
                    continue

                # 마커 주변 200자 추출
                ctx_start = max(0, pos - CONTEXT_WINDOW // 2)
                ctx_end = min(len(manuscript), pos + len(marker) + CONTEXT_WINDOW // 2)
                text = manuscript[ctx_start:ctx_end]

                found.append(
                    {
                        "marker": marker,
                        "text": text,
                        "position": pos,
                    }
                )
                used_ranges.append((ctx_start, ctx_end))

                if len(found) >= MAX_FLASHBACKS:
                    return found

        # 위치 순 정렬
        found.sort(key=lambda x: x["position"])
        return found

    def _format_for_llm(self, flashbacks, reference_context, manuscript_snippets=""):
        """회상 구간 + 참조 컨텍스트를 LLM 프롬프트용으로 포맷팅."""
        fb_lines = []
        for i, fb in enumerate(flashbacks, 1):
            fb_lines.append(f"[회상 {i}] 마커: '{fb['marker']}'\n{fb['text']}")
        fb_text = "\n\n".join(fb_lines)

        parts = [f"[원고 회상 장면]\n{fb_text}", f"[과거 에피소드 요약]\n{reference_context}"]
        if manuscript_snippets:
            parts.append(f"[과거 원고 원문 발췌]\n{manuscript_snippets}")
        return "\n\n".join(parts)

    def _llm_check(self, flashbacks, reference_context, ep_num, manuscript_snippets=""):
        """LLM에게 회상 오염 판정을 요청."""
        formatted = self._format_for_llm(flashbacks, reference_context, manuscript_snippets)

        ms_note = ""
        if manuscript_snippets:
            ms_note = "원문 발췌가 제공된 경우, 요약보다 원문을 우선 참조하여 사실 관계를 대조하세요.\n"

        prompt = (
            "다음 원고의 회상/플래시백 장면이 과거 에피소드 맥락과 모순되는 부분을 찾아주세요.\n"
            f"{ms_note}"
            "서사적 의도가 있는 변형(신뢰할 수 없는 화자, 의도적 왜곡 등)은 정상입니다.\n"
            "같은 기기를 다른 표현으로 지칭한 경우(예: 휴대전화/폴더폰, 화면의 버튼/통화 버튼)는 그 자체만으로 모순이 아닙니다.\n"
            "구형 폴더폰도 화면과 물리 버튼을 함께 가질 수 있으므로, '화면의 버튼' 같은 표현만으로 스마트폰·터치스크린으로 과추론하지 마세요.\n"
            "기기 유형이나 물리 구조 변경은 본문에 명시적 근거가 있을 때만 모순으로 판정하세요.\n"
            "가능하면 각 항목에 contradiction_subtype(location/movement/facing/dialogue/timeline/other)를 붙이세요.\n"
            "local_fixable는 회상 장면 내부의 한두 문장 또는 짧은 구절을 고치면 정합성이 회복되는 경우에만 true로 두세요.\n"
            "patch_anchor는 수정 대상 문장을 짧게 가리키는 표현으로, expected_truth는 prior authority가 기대하는 사실을 짧게 적으세요.\n"
            "local_fix_hint는 국소 수정 지시를 한 줄로 적으세요.\n"
            "사실 관계가 틀린 회상만 지적하세요.\n\n"
            f"{formatted}\n\n"
            f"현재 {ep_num}화입니다.\n"
            "반드시 JSON 배열로만 답하세요. 오염이 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"marker": "해당 마커", "issue": "문제 설명", "referenced_context": "근거가 된 과거 맥락 발췌", '
            '"contradiction_subtype": "movement", "local_fixable": true, "patch_anchor": "회상 장면 동선 서술 문장", '
            '"expected_truth": "과거에는 멈추지 않고 현관을 향했다", "local_fix_hint": "회상 장면의 멈춤/동선 묘사를 prior truth에 맞게 국소 수정"}]\n'
        )

        try:
            response = self._llm_ask(prompt)
            if not response:
                return []
            return self._parse_llm_response(response, ep_num)
        except Exception as e:
            logger.warning("[LM-E] FlashbackVerifier LLM 호출 실패 (비치명): %s", str(e)[:80])
            return []

    @staticmethod
    def _normalize_optional_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in {0, 1}:
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "yes", "1"}:
                return True
            if normalized in {"false", "no", "0"}:
                return False
        return None

    @staticmethod
    def _parse_llm_response(response, ep_num=0):
        """LLM 응답에서 JSON 배열 파싱."""
        if not response:
            return []

        text = response.strip()
        # ```json 펜스 처리 — 정규식 기반 (다중 펜스 안전)
        m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if not m:
            m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        text = text.strip()

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.debug("[LM-E] JSON 파싱 실패: %s", text[:100])
            return []

        if not isinstance(parsed, list):
            return []

        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            marker = item.get("marker", "")
            if not marker:
                continue
            issue = item.get("issue", "")
            payload = {
                "marker": marker,
                "issue": issue,
                "referenced_context": item.get("referenced_context", ""),
                "severity": "MAJOR",
                "check": "flashback_contamination",
                "text": f"[회상 오염] '{marker}': {issue}" if issue else f"[회상 오염] '{marker}'",
            }
            contradiction_subtype = str(
                item.get("subtype", item.get("contradiction_subtype", "")) or ""
            ).strip().lower()
            if contradiction_subtype:
                payload["contradiction_subtype"] = contradiction_subtype
                payload["subtype"] = contradiction_subtype
            local_fixable = FlashbackVerifier._normalize_optional_bool(item.get("local_fixable"))
            if local_fixable is not None:
                payload["local_fixable"] = local_fixable
            patch_anchor = str(item.get("patch_anchor", "") or "").strip()
            if patch_anchor:
                payload["patch_anchor"] = patch_anchor
            expected_truth = str(item.get("expected_truth", "") or "").strip()
            if expected_truth:
                payload["expected_truth"] = expected_truth
            local_fix_hint = str(item.get("local_fix_hint", "") or "").strip()
            if local_fix_hint:
                payload["local_fix_hint"] = local_fix_hint
            target_kind = str(item.get("target_kind", "") or "").strip()
            if target_kind in {"local_phrase", "local_sentence"}:
                payload["target_kind"] = target_kind
            results.append(payload)

        return results
