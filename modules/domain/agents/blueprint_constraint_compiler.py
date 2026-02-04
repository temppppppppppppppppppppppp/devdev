"""
[V60.80] Blueprint Constraint Compiler
Arc에서 해당 화의 제약 조건을 구조화된 블록으로 컴파일

목적:
- tactical_doc에서 해당 화 섹션 추출
- 이전 Blueprint와의 연속성 정보 수집
- 정지선(다음 화 내용) 설정

출력 형식:
- MUST_FOCUS (이번 화 핵심 내용)
- STOP_LINE (다음 화 내용 - 절대 침범 금지)
- CONTINUITY (이전 화 연속성)
- INHERITED_STATE (계승해야 할 상태)
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple


class BlueprintConstraintCompiler:
    """
    [V60.80] Blueprint 제약 조건 컴파일러

    Arc tactical_doc에서 에피소드별 제약을 추출하고 구조화
    """

    def __init__(self):
        pass

    def compile(
        self,
        arc_data: Dict,
        ep_num: int,
        prev_blueprint: Optional[Dict] = None,
        prev_blueprints: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Blueprint 제약 조건 컴파일

        Args:
            arc_data: 현재 Arc 데이터
            ep_num: 현재 에피소드 번호
            prev_blueprint: 직전 Blueprint (있으면)
            prev_blueprints: 이전 Blueprint 리스트 (연속성 검증용)

        Returns:
            constraint_block: 구조화된 제약 블록
        """
        # Arc 기본 정보
        ep_start = arc_data.get("ep_start", 1)
        ep_count = arc_data.get("ep_count", 5)
        arc_no = arc_data.get("arc_no", 1)

        # 현재 화의 Arc 내 위치
        arc_position = ep_num - ep_start + 1

        # 1. 이번 화 핵심 내용 추출
        must_focus = self._extract_episode_focus(arc_data, ep_num, arc_position)

        # 2. 정지선 설정 (다음 화 내용)
        stop_line = self._extract_stop_line(arc_data, ep_num, arc_position, ep_count)

        # 3. 연속성 정보 수집
        continuity = self._extract_continuity(prev_blueprint, prev_blueprints)

        # 4. 계승 상태 추출
        inherited_state = self._extract_inherited_state(arc_data, prev_blueprint)

        # 5. 제약 블록 생성
        constraint_block = {
            "ep_num": ep_num,
            "arc_no": arc_no,
            "arc_position": f"{arc_position}/{ep_count}",
            "must_focus": must_focus,
            "stop_line": stop_line,
            "continuity": continuity,
            "inherited_state": inherited_state
        }

        return constraint_block

    def compile_to_prompt(self, constraint_block: Dict) -> str:
        """
        제약 블록을 프롬프트 문자열로 변환

        Args:
            constraint_block: compile() 결과

        Returns:
            프롬프트 주입용 문자열
        """
        lines = []

        # 헤더
        lines.append("=" * 60)
        lines.append(f"[V60.80 BLUEPRINT CONSTRAINTS] 제{constraint_block['ep_num']}화")
        lines.append(f"Arc {constraint_block['arc_no']} - 위치: {constraint_block['arc_position']}")
        lines.append("=" * 60)
        lines.append("")

        # MUST FOCUS
        lines.append("### 🎯 MUST_FOCUS (이번 화 핵심 - 반드시 포함)")
        must_focus = constraint_block.get("must_focus", {})
        lines.append(f"내용: {must_focus.get('content', '정보 없음')[:500]}")
        if must_focus.get("key_events"):
            lines.append("핵심 이벤트:")
            for event in must_focus["key_events"][:5]:
                lines.append(f"  - {event}")
        lines.append("")

        # STOP LINE
        lines.append("### 🚨 STOP_LINE (다음 화 내용 - 절대 침범 금지)")
        stop_line = constraint_block.get("stop_line", {})
        if stop_line.get("content"):
            lines.append(f"다음 화 예고: {stop_line['content'][:200]}")
            lines.append("⚠️ 위 내용을 이번 화에서 다루면 즉시 REJECT")
        else:
            lines.append("(Arc 마지막 화 - 정지선 없음)")
        lines.append("")

        # CONTINUITY
        lines.append("### 🔗 CONTINUITY (이전 화 연속성)")
        continuity = constraint_block.get("continuity", {})
        if continuity.get("prev_ending"):
            lines.append(f"직전 화 엔딩: {continuity['prev_ending'][:150]}...")
        if continuity.get("location"):
            lines.append(f"현재 위치: {continuity['location']}")
        if continuity.get("time_context"):
            lines.append(f"시간 맥락: {continuity['time_context']}")
        if continuity.get("ongoing_conflicts"):
            lines.append(f"진행 중 갈등: {', '.join(continuity['ongoing_conflicts'][:3])}")
        lines.append("")

        # INHERITED STATE
        lines.append("### 📦 INHERITED_STATE (계승 상태)")
        inherited = constraint_block.get("inherited_state", {})
        if inherited.get("equipment"):
            lines.append(f"소지품: {inherited['equipment']}")
        if inherited.get("injuries"):
            lines.append(f"부상: {inherited['injuries']}")
        if inherited.get("internal_energy"):
            lines.append(f"내공: {inherited['internal_energy']}")
        if inherited.get("companions"):
            lines.append(f"동행: {', '.join(inherited['companions'])}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _extract_episode_focus(
        self,
        arc_data: Dict,
        ep_num: int,
        arc_position: int
    ) -> Dict:
        """이번 화 핵심 내용 추출"""
        tactical_doc = arc_data.get("tactical_doc", "")

        # 딕셔너리면 문자열로 변환
        if isinstance(tactical_doc, dict):
            tactical_doc = json.dumps(tactical_doc, ensure_ascii=False, indent=2)

        # 해당 화 섹션 추출 패턴
        focus_tag = f"[제 {ep_num}화"
        alt_tag = f"[제{ep_num}화"

        # 정규식으로 해당 화 섹션 추출
        pattern = rf'\[제\s*{ep_num}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)'
        match = re.search(pattern, tactical_doc, re.DOTALL)

        content = ""
        if match:
            content = match.group(1).strip()
        else:
            # 폴백: beat_sequence 사용
            beats = arc_data.get("beat_sequence", [])
            if arc_position - 1 < len(beats):
                content = beats[arc_position - 1]

        # 핵심 이벤트 추출
        key_events = []
        if content:
            # 줄 단위로 이벤트 추출
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    key_events.append(line.lstrip("-•").strip())
                elif len(line) > 10 and len(line) < 100:
                    key_events.append(line)

        return {
            "content": content[:1000] if content else "이번 화 전술 정보 없음",
            "key_events": key_events[:5],
            "arc_position": arc_position
        }

    def _extract_stop_line(
        self,
        arc_data: Dict,
        ep_num: int,
        arc_position: int,
        ep_count: int
    ) -> Dict:
        """정지선 추출 (다음 화 내용)"""
        # Arc 마지막 화면 정지선 없음
        if arc_position >= ep_count:
            return {"content": None, "is_arc_finale": True}

        next_ep = ep_num + 1
        tactical_doc = arc_data.get("tactical_doc", "")

        if isinstance(tactical_doc, dict):
            tactical_doc = json.dumps(tactical_doc, ensure_ascii=False, indent=2)

        # 다음 화 섹션 추출
        pattern = rf'\[제\s*{next_ep}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)'
        match = re.search(pattern, tactical_doc, re.DOTALL)

        content = ""
        if match:
            content = match.group(1).strip()[:300]
        else:
            # 폴백: beat_sequence 사용
            beats = arc_data.get("beat_sequence", [])
            if arc_position < len(beats):
                content = beats[arc_position]  # 다음 비트

        return {
            "content": content if content else None,
            "is_arc_finale": False,
            "next_ep": next_ep
        }

    def _extract_continuity(
        self,
        prev_blueprint: Optional[Dict],
        prev_blueprints: Optional[List[Dict]] = None
    ) -> Dict:
        """연속성 정보 추출"""
        continuity = {
            "prev_ending": None,
            "location": None,
            "time_context": None,
            "ongoing_conflicts": [],
            "active_characters": []
        }

        if not prev_blueprint:
            return continuity

        # 직전 Blueprint에서 추출
        continuity["prev_ending"] = prev_blueprint.get("ending_hook", "")
        continuity["location"] = prev_blueprint.get("end_location",
                                   prev_blueprint.get("location", ""))
        continuity["time_context"] = prev_blueprint.get("time_flow", "")

        # scene_breakdown에서 마지막 씬 정보
        scenes = prev_blueprint.get("scene_breakdown", {})
        if scenes:
            # 마지막 씬 키 찾기
            scene_keys = sorted(scenes.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
            if scene_keys:
                last_scene = scenes.get(scene_keys[-1], {})
                if isinstance(last_scene, dict):
                    continuity["location"] = last_scene.get("location", continuity["location"])

                    # 등장인물 추출
                    chars = last_scene.get("characters", [])
                    if isinstance(chars, list):
                        continuity["active_characters"] = chars[:5]

        # ongoing_conflicts 추출 (여러 Blueprint에서)
        if prev_blueprints:
            conflicts = set()
            for bp in prev_blueprints[-3:]:  # 최근 3개
                bp_conflicts = bp.get("ongoing_conflicts", [])
                if isinstance(bp_conflicts, list):
                    conflicts.update(bp_conflicts[:2])
                # cliffhanger도 갈등으로
                cliffhanger = bp.get("cliffhanger", "")
                if cliffhanger:
                    conflicts.add(cliffhanger[:50])
            continuity["ongoing_conflicts"] = list(conflicts)[:5]

        return continuity

    def _extract_inherited_state(
        self,
        arc_data: Dict,
        prev_blueprint: Optional[Dict]
    ) -> Dict:
        """계승 상태 추출"""
        inherited = {
            "equipment": [],
            "injuries": "없음",
            "internal_energy": "100%",
            "companions": [],
            "mood": "평온"
        }

        # Arc의 joint_docs에서 추출
        joint_docs = arc_data.get("joint_docs", {})
        if joint_docs:
            inventory = joint_docs.get("physical_inventory", [])
            if isinstance(inventory, list):
                inherited["equipment"] = inventory[:10]
            elif isinstance(inventory, str):
                inherited["equipment"] = [i.strip() for i in inventory.split(",")][:10]

        # Arc의 status_shadow에서 추출
        shadow = arc_data.get("status_shadow", {})
        if shadow:
            injuries = shadow.get("expected_injuries", "")
            if injuries:
                inherited["injuries"] = injuries

            energy = shadow.get("internal_energy_loss", "0%")
            if energy:
                try:
                    loss = int(re.search(r'(\d+)', str(energy)).group(1))
                    inherited["internal_energy"] = f"{100 - loss}%"
                except:
                    pass

        # Arc의 state_constraints에서 추출
        state = arc_data.get("state_constraints", {})
        if state:
            arc_start = state.get("arc_start_state", {})
            if arc_start:
                inherited["injuries"] = arc_start.get("injuries", inherited["injuries"])
                if arc_start.get("internal_energy"):
                    inherited["internal_energy"] = f"{arc_start['internal_energy']}%"
                inherited["equipment"] = arc_start.get("equipment", inherited["equipment"])

        # 이전 Blueprint에서 보강
        if prev_blueprint:
            # protagonist_state 확인
            protag = prev_blueprint.get("protagonist_state", {})
            if protag:
                if protag.get("equipment"):
                    inherited["equipment"] = protag["equipment"]
                if protag.get("injuries"):
                    inherited["injuries"] = protag["injuries"]
                if protag.get("companions"):
                    inherited["companions"] = protag["companions"]
                if protag.get("mood"):
                    inherited["mood"] = protag["mood"]

        return inherited


def create_blueprint_constraint_compiler():
    """BlueprintConstraintCompiler 생성 헬퍼"""
    return BlueprintConstraintCompiler()
