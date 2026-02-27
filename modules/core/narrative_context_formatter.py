"""[LM-G] NarrativeContextFormatter — 서사 구조 메타데이터 → LLM 컨텍스트 변환.

Stage 2 Arc 설계 시 LLM(Analyst)에게 동기/약속/Arc 스케일 정보를 주입하여
방치 플롯·미이행 약속·스케일 역행을 감지할 수 있도록 한다.

순수 Python 포맷터 — LLM 호출 없음, DB 접근 없음.
"""

import logging

_logger = logging.getLogger(__name__)


class NarrativeContextFormatter:
    """WorldState/StateTracker의 동기/약속/Arc 스케일 → LLM 컨텍스트로 변환."""

    @staticmethod
    def format_motivations(
        active_plots: dict | None,
        npc_motivations: dict | None,
        current_arc_no: int,
    ) -> str:
        """활성 플롯 + NPC 동기 → 포맷 문자열.

        Args:
            active_plots: {plot_name: {status, first_arc, last_mention_arc}} (StateTracker)
            npc_motivations: {npc_name: primary_motivation_str}
            current_arc_no: 현재 Arc 번호

        Returns:
            포맷된 문자열 (빈 데이터면 빈 문자열)
        """
        sections: list[str] = []

        # 활성 플롯
        if active_plots and isinstance(active_plots, dict):
            plot_lines: list[str] = []
            count = 0
            for plot_name, plot_info in active_plots.items():
                if count >= 20:
                    break
                if not isinstance(plot_info, dict):
                    continue
                status = plot_info.get("status", "")
                if status in ("resolved", "완결"):
                    continue
                first_arc = plot_info.get("first_arc", 0)
                last_mention = plot_info.get("last_mention_arc", 0)
                gap = current_arc_no - last_mention if last_mention and current_arc_no else 0
                line = f"- {plot_name} (Arc {first_arc}~, 상태={status or '진행중'})"
                if gap >= 3:
                    line += f" ⚠ {gap}Arc 방치됨"
                plot_lines.append(line)
                count += 1
            if plot_lines:
                sections.append("[진행 중 동기/플롯]\n" + "\n".join(plot_lines))

        # NPC 동기
        if npc_motivations and isinstance(npc_motivations, dict):
            mot_lines: list[str] = []
            count = 0
            for npc_name, motivation in npc_motivations.items():
                if count >= 20:
                    break
                if not motivation or not isinstance(motivation, str):
                    continue
                mot_lines.append(f"- {npc_name}: {motivation}")
                count += 1
            if mot_lines:
                sections.append("[주요 NPC 동기]\n" + "\n".join(mot_lines))

        return "\n\n".join(sections)

    @staticmethod
    def format_promises(
        pending_commitments: list | None,
        current_arc_no: int,
    ) -> str:
        """미이행 약속/서약 → 포맷 문자열.

        Args:
            pending_commitments: [{arc_no, episode, parties, description, deadline_hint, status}]
            current_arc_no: 현재 Arc 번호

        Returns:
            포맷된 문자열 (빈 데이터면 빈 문자열)
        """
        if not pending_commitments or not isinstance(pending_commitments, list):
            return ""

        lines: list[str] = []
        count = 0
        for commit in pending_commitments:
            if count >= 30:
                break
            if not isinstance(commit, dict):
                continue
            status = commit.get("status", "pending")
            if status in ("fulfilled", "이행", "resolved", "완료"):
                continue
            desc = commit.get("description", "")
            if not desc:
                continue
            arc_no = commit.get("arc_no", 0)
            parties = commit.get("parties", "")
            if isinstance(parties, list):
                parties = ", ".join(str(p) for p in parties)
            elapsed = current_arc_no - arc_no if arc_no and current_arc_no else 0
            line = f"- {desc}"
            if parties:
                line += f" (당사자: {parties})"
            if arc_no:
                line += f" [Arc {arc_no}~]"
            if elapsed >= 3:
                line += f" ⚠ 장기 미이행({elapsed}Arc)"
            lines.append(line)
            count += 1

        if not lines:
            return ""
        return "[미이행 약속/서약]\n" + "\n".join(lines)

    @staticmethod
    def format_arc_scales(all_refined_arcs: list | None) -> str:
        """Arc 스케일 진행 요약 → 포맷 문자열.

        Args:
            all_refined_arcs: list of arc dicts (tactical_doc 등 포함)

        Returns:
            포맷된 문자열 (Arc 2개 미만이면 빈 문자열)
        """
        if not all_refined_arcs or not isinstance(all_refined_arcs, list):
            return ""
        if len(all_refined_arcs) < 2:
            return ""

        lines: list[str] = []
        for i, arc in enumerate(all_refined_arcs, 1):
            if not isinstance(arc, dict):
                continue
            # tactical_doc에서 첫 줄 추출
            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):
                # dict인 경우 theme/intensity 키 시도
                theme = tactical.get("theme", "")
                intensity = tactical.get("intensity", "")
                first_line = f"{theme} (강도: {intensity})" if theme else str(tactical)[:80]
            elif isinstance(tactical, str):
                first_line = tactical.split("\n")[0][:80] if tactical else ""
            else:
                first_line = ""
            if first_line:
                lines.append(f"- Arc {i}: {first_line}")

        if not lines:
            return ""
        return "[Arc 스케일 진행]\n" + "\n".join(lines)

    @classmethod
    def format_all(
        cls,
        *,
        active_plots: dict | None,
        npc_motivations: dict | None,
        pending_commitments: list | None,
        all_refined_arcs: list | None,
        current_arc_no: int,
        max_chars: int = 3000,
    ) -> str:
        """3개 섹션 통합 → advisory 헤더 포함 컨텍스트 문자열.

        Returns:
            포맷된 문자열 (모든 섹션 빈 경우 빈 문자열)
        """
        sections: list[str] = []

        mot = cls.format_motivations(active_plots, npc_motivations, current_arc_no)
        if mot:
            sections.append(mot)

        prom = cls.format_promises(pending_commitments, current_arc_no)
        if prom:
            sections.append(prom)

        scales = cls.format_arc_scales(all_refined_arcs)
        if scales:
            sections.append(scales)

        if not sections:
            return ""

        body = "\n\n".join(sections)
        result = "[LM-G 서사 구조 참고 — advisory]\n\n" + body

        if len(result) > max_chars:
            result = result[: max_chars - 10] + "\n...(절삭)"

        return result
