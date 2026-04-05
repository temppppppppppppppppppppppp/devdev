"""[LM-B] NPC 속성 드리프트 감지기 — 원고 텍스트 레벨 표류 advisory.

TruthGate(state_updates dict 검사)와 분리된 독립 클래스.
원고 본문에서 NPC가 초기 설정과 다르게 묘사되는 것을 LLM으로 감지.
Advisory-only: Director가 최종 판정.
"""

import json
import logging
import re

from modules.core.constants import smart_truncate

logger = logging.getLogger(__name__)

# 일반 명사 / 호칭 — NPC 이름 매칭에서 제외
_EXCLUDE_WORDS = frozenset(["주인공", "적", "자신", "상대", "아군", "동료", "스승", "제자", "장로", "문주"])
_RELATION_TAG_SPLIT_RE = re.compile(r"\s*/\s*")
_RELATION_TAG_TOKEN_RE = re.compile(r"^[A-Za-z가-힣_]+[+-]{0,1}\d+$")
_RELATION_TAG_WHITESPACE_RE = re.compile(r"\s+")
_RELATION_TAG_PLAIN_HINTS = {
    "오해 대상": {
        "expected_relation_axes": ["오해 대상", "NPC가 주인공을 오해함"],
        "relation_direction": "npc_misunderstands_protag",
        "relation_direction_label": "NPC가 주인공을 오해함",
        "prompt_hint": (
            "방향성 평문 관계 태그; '오해 대상'은 기본적으로 NPC가 주인공을 오해하거나 "
            "잘못 판단하는 관계를 뜻한다. 주인공이 상대를 오해해야 한다는 literal 요구로 해석하지 말라"
        ),
        "semantic_local_fix_hint": (
            "relation_to_protag '오해 대상'은 NPC가 주인공을 오해하는 관계로 해석하고 "
            "canonical direction과 어긋난 관계 표현만 국소 수정한다"
        ),
    }
}


def _normalize_relation_tag_label(raw_value: object) -> str:
    return _RELATION_TAG_WHITESPACE_RE.sub(" ", str(raw_value or "").strip())


def _extract_relation_tag_tokens(raw_value: object) -> list[str]:
    text = _normalize_relation_tag_label(raw_value)
    if not text or "/" not in text:
        return []
    tokens = [token.strip() for token in _RELATION_TAG_SPLIT_RE.split(text) if token.strip()]
    if len(tokens) < 2:
        return []
    if not all(_RELATION_TAG_TOKEN_RE.fullmatch(token) for token in tokens):
        return []
    return tokens


def _build_relation_tag_semantics(raw_value: object) -> dict[str, object]:
    value = _normalize_relation_tag_label(raw_value)
    if not value:
        return {}

    tokens = _extract_relation_tag_tokens(value)
    if tokens:
        return {
            "relation_label_kind": "compressed_axes",
            "expected_relation_label": value,
            "expected_relation_axes": tokens,
            "prompt_hint": (
                "압축 관계 태그; literal 숫자/태그 일치를 요구하지 말고 "
                f"{', '.join(tokens)} 축과 부합하는 관계 프레이밍만 보라"
            ),
            "semantic_local_fix_hint": (
                "relation_to_protag 압축 관계 태그와 어긋난 관계 프레이밍만 국소 수정하고 "
                "literal 숫자/태그 재현은 요구하지 않는다"
            ),
        }

    plain_hint = _RELATION_TAG_PLAIN_HINTS.get(value)
    if not plain_hint:
        return {}

    semantics = dict(plain_hint)
    semantics["relation_label_kind"] = "plain_directional"
    semantics["expected_relation_label"] = value
    semantics["expected_relation_axes"] = list(plain_hint.get("expected_relation_axes") or [])
    return semantics


def _format_relation_attr_value_for_prompt(field: str, raw_value: object) -> str:
    value = _normalize_relation_tag_label(raw_value)
    if str(field or "").strip() != "relation_to_protag":
        return value
    semantics = _build_relation_tag_semantics(value)
    if not semantics:
        return value
    prompt_hint = str(semantics.get("prompt_hint", "") or "").strip()
    if not prompt_hint:
        return value
    return f"{value} [{prompt_hint}]"


def _build_relation_tag_warning_metadata(field: object, expected: object) -> dict[str, object]:
    normalized_field = str(field or "").strip()
    semantics = _build_relation_tag_semantics(expected)
    if normalized_field != "relation_to_protag" or not semantics:
        return {}
    expected_relation_label = str(semantics.get("expected_relation_label", "") or "").strip()
    semantic_local_fix_hint = str(semantics.get("semantic_local_fix_hint", "") or "").strip()
    metadata = {
        "drift_subtype": "relation_tag_semantic",
        "subtype": "relation_tag_semantic",
        "target_kind": "local_phrase",
        "fix_scope": "inplace",
        "local_fixable": True,
        "expected_relation_label": expected_relation_label,
        "expected_relation_axes": list(semantics.get("expected_relation_axes") or []),
        "expected_truth": expected_relation_label,
        "semantic_local_fix_hint": semantic_local_fix_hint,
        "local_fix_hint": semantic_local_fix_hint,
        "relation_label_kind": str(semantics.get("relation_label_kind", "") or "").strip(),
    }
    relation_direction = str(semantics.get("relation_direction", "") or "").strip()
    if relation_direction:
        metadata["relation_direction"] = relation_direction
    relation_direction_label = str(semantics.get("relation_direction_label", "") or "").strip()
    if relation_direction_label:
        metadata["relation_direction_label"] = relation_direction_label
    return metadata


class NpcDriftAdvisor:
    """원고 텍스트에서 NPC 속성 표류를 LLM으로 감지 (advisory only)."""

    def __init__(self, llm_ask=None):
        """
        Args:
            llm_ask: Optional callable(prompt: str) -> str. None이면 검사 스킵.
        """
        self._llm_ask = llm_ask

    def check(self, manuscript, npc_snapshots, *, ep_num=0, max_npcs=8):
        """NPC 속성 표류 검사.

        Args:
            manuscript: 원고 텍스트
            npc_snapshots: {
                npc_name: {
                    "role_at_intro": str,
                    "authoritative_role": str,
                    "first_seen_ep": int,
                    "known_attrs": dict,
                }
            }
            ep_num: 현재 에피소드 번호
            max_npcs: 검사 대상 최대 NPC 수

        Returns:
            list[dict]: [{"npc", "field", "expected", "found_in_ms", "severity", "check"}]
        """
        if not isinstance(manuscript, str) or not manuscript:
            return []
        if not isinstance(npc_snapshots, dict) or not npc_snapshots:
            return []

        appearing = self._find_appearing_npcs(manuscript, npc_snapshots)
        if not appearing:
            return []

        # authoritative_role 또는 known_attrs가 있는 NPC만 검사 대상
        targets = []
        for name in appearing:
            snap = npc_snapshots.get(name, {})
            if snap.get("authoritative_role") or snap.get("role_at_intro") or snap.get("known_attrs"):
                targets.append(name)
            if len(targets) >= max_npcs:
                break

        if not targets:
            return []

        if not self._llm_ask:
            return []

        return self._llm_check_batch(manuscript, npc_snapshots, targets, ep_num)

    def _find_appearing_npcs(self, manuscript, npc_snapshots):
        """원고에 등장하는 스냅샷 NPC를 빈도 내림차순으로 반환."""
        if not isinstance(manuscript, str) or not isinstance(npc_snapshots, dict):
            return []
        counts = {}
        for name in npc_snapshots:
            if not name or len(name) < 2:
                continue
            if name in _EXCLUDE_WORDS:
                continue
            cnt = manuscript.count(name)
            if cnt > 0:
                counts[name] = cnt

        def _sort_key(name):
            snap = npc_snapshots.get(name, {}) if isinstance(npc_snapshots, dict) else {}
            recent_changed_ep = 0
            known_attrs = snap.get("known_attrs", {}) if isinstance(snap, dict) else {}
            if isinstance(known_attrs, dict):
                for value in known_attrs.values():
                    if isinstance(value, dict):
                        try:
                            recent_changed_ep = max(recent_changed_ep, int(value.get("changed_ep", 0) or 0))
                        except (TypeError, ValueError):
                            continue
            return (counts.get(name, 0), recent_changed_ep, int(snap.get("first_seen_ep", 0) or 0))

        return sorted(counts, key=_sort_key, reverse=True)

    def _format_snapshot_for_prompt(self, npc_snapshots, targets):
        """프롬프트용 NPC 스냅샷 텍스트 포맷."""
        lines = []
        for name in targets:
            snap = npc_snapshots.get(name, {})
            parts = [f"이름: {name}"]
            authoritative_role = str(snap.get("authoritative_role", "") or "").strip()
            if authoritative_role:
                parts.append(f"현재기준역할: {authoritative_role}")
            role = str(snap.get("role_at_intro", "") or "").strip()
            if role and role != authoritative_role:
                parts.append(f"초기참고역할: {role}")
            first_ep = snap.get("first_seen_ep", 0)
            if first_ep:
                parts.append(f"첫등장: {first_ep}화")
            known = snap.get("known_attrs", {})
            if known:
                attr_strs = []
                for k, v in list(known.items())[:12]:
                    val = v.get("value", v) if isinstance(v, dict) else str(v)
                    attr_strs.append(f"{k}={_format_relation_attr_value_for_prompt(k, val)}")
                parts.append(f"속성: {', '.join(attr_strs)}")
            lines.append(" / ".join(parts))
        return "\n".join(lines)

    def _llm_check_batch(self, manuscript, npc_snapshots, targets, ep_num):
        """배치 LLM 호출로 NPC 속성 표류 감지."""
        snapshot_text = self._format_snapshot_for_prompt(npc_snapshots, targets)
        ms_snippet = smart_truncate(manuscript or "", max_chars=4000, head_chars=2500)

        prompt = (
            "다음 NPC들의 현재 authoritative 속성과 원고를 비교하여, 설명 없이 속성이 변한 경우만 지적하세요.\n"
            "각 NPC에 현재기준역할이 있으면 그것을 최우선 기준으로 사용하고, "
            "초기참고역할은 현재 기준이 없을 때만 보조 참고하세요.\n"
            "검사 대상: 역할, 관계(relation_to_protag), 무장, 실력, 성격, "
            "부상 상태(injury), 현재 위치(location), 영구 부상(permanent_injuries), "
            "지식시대(knowledge_era), 전문영역(expertise_domain), 비밀 인지(secrets_known), "
            "이중 정체(dual_identity) 등.\n"
            "relation_to_protag가 '집착100/오해-80'처럼 압축 관계 태그로 주어지면 "
            "literal 숫자/태그 재현은 요구하지 말고, 관계 프레이밍이 그 축과 명백히 반대일 때만 표류로 지적하세요.\n"
            "relation_to_protag에 대괄호 의미/방향성 힌트가 붙어 있으면 그 힌트를 authoritative 해석으로 사용하세요.\n"
            "서사적 변화(성장·부상·전직 등 작중 이유가 있는 변화)는 표류가 아닙니다.\n"
            "설명 없이 속성이 바뀐 것만 지적하세요.\n\n"
            f"[NPC authoritative 속성]\n{snapshot_text}\n\n"
            f"[원고 (최대 4000자)]\n{ms_snippet}\n\n"
            "반드시 JSON 배열로만 답하세요. 표류가 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"npc": "이름", "field": "변경된 필드", "expected": "현재 authoritative 값", "found_in_ms": "원고에서 발견된 묘사"}]\n'
        )

        try:
            response = self._llm_ask(prompt)
            if not response:
                return []
            return self._parse_llm_response(response, ep_num)
        except Exception as e:
            logger.warning("[LM-B] NpcDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
            return []

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
            logger.debug("[LM-B] JSON 파싱 실패: %s", text[:100])
            return []

        if not isinstance(parsed, list):
            return []

        results = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            npc = item.get("npc", "")
            if not npc:
                continue
            field = item.get("field", "")
            found = item.get("found_in_ms", "")
            results.append(
                {
                    "npc": npc,
                    "field": field,
                    "expected": item.get("expected", ""),
                    "expected_truth": item.get("expected", ""),
                    "found_in_ms": found,
                    "severity": "MAJOR",
                    "check": "npc_drift",
                    "text": f"[NPC 표류] {npc}: {field} (원고: {found})" if found else f"[NPC 표류] {npc}: {field}",
                }
            )
            metadata = _build_relation_tag_warning_metadata(field, item.get("expected", ""))
            if metadata:
                results[-1].update(metadata)

        return results
