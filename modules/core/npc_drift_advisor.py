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
            npc_snapshots: {npc_name: {"role_at_intro": str, "first_seen_ep": int, "known_attrs": dict}}
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

        # role_at_intro 또는 known_attrs가 있는 NPC만 검사 대상
        targets = []
        for name in appearing:
            snap = npc_snapshots.get(name, {})
            if snap.get("role_at_intro") or snap.get("known_attrs"):
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
            role = snap.get("role_at_intro", "")
            if role:
                parts.append(f"최초역할: {role}")
            first_ep = snap.get("first_seen_ep", 0)
            if first_ep:
                parts.append(f"첫등장: {first_ep}화")
            known = snap.get("known_attrs", {})
            if known:
                attr_strs = []
                for k, v in list(known.items())[:12]:
                    val = v.get("value", v) if isinstance(v, dict) else str(v)
                    attr_strs.append(f"{k}={val}")
                parts.append(f"속성: {', '.join(attr_strs)}")
            lines.append(" / ".join(parts))
        return "\n".join(lines)

    def _llm_check_batch(self, manuscript, npc_snapshots, targets, ep_num):
        """배치 LLM 호출로 NPC 속성 표류 감지."""
        snapshot_text = self._format_snapshot_for_prompt(npc_snapshots, targets)
        ms_snippet = smart_truncate(manuscript or "", max_chars=4000, head_chars=2500)

        prompt = (
            "다음 NPC들의 초기 속성과 원고를 비교하여, 설명 없이 속성이 변한 경우만 지적하세요.\n"
            "검사 대상: 역할, 관계(relation_to_protag), 무장, 실력, 성격, "
            "부상 상태(injury), 현재 위치(location), 영구 부상(permanent_injuries), "
            "지식시대(knowledge_era), 전문영역(expertise_domain), 비밀 인지(secrets_known), "
            "이중 정체(dual_identity) 등.\n"
            "서사적 변화(성장·부상·전직 등 작중 이유가 있는 변화)는 표류가 아닙니다.\n"
            "설명 없이 속성이 바뀐 것만 지적하세요.\n\n"
            f"[NPC 초기 속성]\n{snapshot_text}\n\n"
            f"[원고 (최대 4000자)]\n{ms_snippet}\n\n"
            "반드시 JSON 배열로만 답하세요. 표류가 없으면 빈 배열 []을 반환하세요.\n"
            '형식: [{"npc": "이름", "field": "변경된 필드", "expected": "초기값", "found_in_ms": "원고에서 발견된 묘사"}]\n'
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
                    "found_in_ms": found,
                    "severity": "MAJOR",
                    "check": "npc_drift",
                    "text": f"[NPC 표류] {npc}: {field} (원고: {found})" if found else f"[NPC 표류] {npc}: {field}",
                }
            )

        return results
