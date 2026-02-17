"""
[V64 P2-3] FeedbackSystem — SovereignApp 피드백 생성 로직 캡슐화

SovereignApp에서 분리된 15개 피드백 생성 메서드.
모든 메서드가 순수 함수(Pure Function) — app 참조 불필요.

카테고리:
- 구조화 피드백 (3개): build_structured_feedback, get_violation_priority, format_feedback_for_prompt
- 정량화/강화 (5개): quantify_reject_feedback, build_strong_kind_feedback, build_focused_context,
                      build_strong_kind_feedback_legacy, build_minimal_arc_context
- Stage별 피드백 (2개): generate_structured_arc_feedback, generate_structured_blueprint_feedback
- 역방향 피드백 (2개): generate_reverse_feedback_stage4_to_3, generate_reverse_feedback_stage3_to_2
- 적응형 (2개): get_adaptive_feedback_intensity, classify_rejection_feedback
- 재시도 (1개): simplify_prompt_for_retry
"""

from modules.core.constants import ManuscriptLimits  # [V64.P4]


class FeedbackSystem:
    """
    [V64 P2-3] SovereignApp의 피드백 생성 로직 캡슐화

    모든 메서드가 순수 함수 — 인스턴스 상태 없음.
    """

    # ═══════════════════════════════════════════════════════════════════════
    # 구조화 피드백
    # ═══════════════════════════════════════════════════════════════════════

    def build_structured_feedback(
        self, decision: str, reason: str, violations: list = None, severity: str = "MEDIUM", fix_instructions: str = ""
    ) -> dict:
        """[V60.3] 구조화된 피드백 생성"""
        return {
            "decision": decision,
            "reason": reason[:300] if reason else "",
            "violations": violations or [],
            "severity": severity,
            "fix_instructions": fix_instructions[:500] if fix_instructions else "",
            "priority_order": self.get_violation_priority(violations or []),
        }

    def get_violation_priority(self, violations: list) -> list:
        """위반 항목 우선순위 정렬"""
        priority_map = {
            "duplicate_acquisition": 1,
            "timeline_error": 2,
            "continuity": 3,
            "scope_overflow": 4,
            "blueprint_mismatch": 5,
            "relationship_jump": 6,
            "unknown": 10,
        }
        sorted_violations = sorted(violations, key=lambda v: priority_map.get(v.get("type", "unknown"), 10))
        return [v.get("type", "unknown") for v in sorted_violations]

    def format_feedback_for_prompt(self, structured_feedback: dict) -> str:
        """구조화된 피드백을 프롬프트용 문자열로 변환"""
        if not structured_feedback or structured_feedback.get("decision") == "PASS":
            return ""

        parts = [
            f"🚨 [{structured_feedback.get('severity', 'MEDIUM')}] {structured_feedback.get('decision', 'REJECT')}",
            f"사유: {structured_feedback.get('reason', '')}",
        ]

        priority_order = structured_feedback.get("priority_order", [])
        if priority_order:
            parts.append(f"우선 수정: {' → '.join(priority_order[:3])}")

        if structured_feedback.get("fix_instructions"):
            parts.append(f"수정 지시: {structured_feedback.get('fix_instructions')}")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════════════
    # 정량화 / 강화
    # ═══════════════════════════════════════════════════════════════════════

    def quantify_reject_feedback(self, reason: str, content_length: int, audit_result: dict) -> list:
        """
        [V60.6] REJECT 사유를 구체적 수치로 정량화

        "분량 부족" → "대화 300자 추가 필요" 수준으로 변환.
        """
        quantified = []

        # 1. 분량 정량화
        if "분량" in reason or content_length < ManuscriptLimits.WARNING_LENGTH:  # [V64.P4]
            target_length = ManuscriptLimits.TARGET_LENGTH  # [V64.P4]
            shortage = max(0, target_length - content_length)

            if shortage > 0:
                dialogue_add = int(shortage * 0.35)
                desc_add = int(shortage * 0.40)
                action_add = int(shortage * 0.25)

                quantified.append(
                    {
                        "type": "QUANTIFIED",
                        "description": f"정확한 분량 보충: 총 {shortage}자 추가 필요",
                        "severity": "HIGH" if shortage > 500 else "MEDIUM",
                        "suggestion": f"대화 +{dialogue_add}자 | 묘사 +{desc_add}자 | 액션 +{action_add}자",
                    }
                )

        # 2. 대화 비율 정량화
        score_breakdown = audit_result.get("score_breakdown", {})
        if "대화" in reason or "건조" in reason:
            current_dialogue_chars = int(content_length * 0.15)
            target_dialogue_chars = int(content_length * 0.30)
            dialogue_needed = target_dialogue_chars - current_dialogue_chars

            if dialogue_needed > 100:
                dialogue_count_needed = dialogue_needed // 50
                quantified.append(
                    {
                        "type": "QUANTIFIED",
                        "description": f"대화 분량 부족: {dialogue_needed}자 추가 필요",
                        "severity": "HIGH" if dialogue_needed > 500 else "MEDIUM",
                        "suggestion": f"대화 {dialogue_count_needed}~{dialogue_count_needed + 2}개 추가 (조연 리액션, 내면 독백 포함)",
                    }
                )

        # 3. 씬 밀도 정량화
        if "밀도" in reason or "후반부" in reason or "요약" in reason:
            target_latter_half = content_length // 2
            estimated_latter_half = int(content_length * 0.35)
            latter_shortage = target_latter_half - estimated_latter_half

            if latter_shortage > 300:
                quantified.append(
                    {
                        "type": "QUANTIFIED",
                        "description": f"후반부 분량 부족: Scene 5-6에 {latter_shortage}자 추가 필요",
                        "severity": "HIGH",
                        "suggestion": f"Scene 5에 +{latter_shortage // 2}자, Scene 6에 +{latter_shortage // 2}자 배분",
                    }
                )

        # 4. 씬 반영 정량화
        if "씬" in reason or "장면" in reason or "누락" in reason:
            quantified.append(
                {
                    "type": "QUANTIFIED",
                    "description": "씬 반영 부족: Blueprint의 모든 씬 균등 반영 필요",
                    "severity": "HIGH",
                    "suggestion": "각 씬당 최소 700자 확보 (6개 씬 × 700자 = 4,200자 베이스라인)",
                }
            )

        # 5. 감각 묘사 정량화
        if "묘사" in reason or "건조" in reason:
            target_sensory = (content_length // 1000) * 4
            estimated_sensory = (content_length // 1000) * 1
            sensory_needed = target_sensory - estimated_sensory

            if sensory_needed > 0:
                quantified.append(
                    {
                        "type": "QUANTIFIED",
                        "description": f"감각 묘사 부족: {sensory_needed}개 추가 권장",
                        "severity": "MEDIUM",
                        "suggestion": "시각/청각/촉각/후각 중 2가지 이상 혼합하여 장면당 1-2개 추가",
                    }
                )

        # 6. 액션 밀도 정량화
        if "액션" in reason or "긴장" in reason:
            quantified.append(
                {
                    "type": "QUANTIFIED",
                    "description": "액션 밀도 부족: 동작 묘사 강화 필요",
                    "severity": "MEDIUM",
                    "suggestion": "무술 장면은 3박자 이상 교환(공격-방어-반격) 묘사. 최소 500자/액션씬",
                }
            )

        return quantified

    def build_strong_kind_feedback(self, violations: list, attempt: int, protagonist_name: str = "주인공") -> str:
        """
        [V60.21] 극도로 집중된 피드백 생성

        원칙: XML 우선순위 태그, 500자 이내, 단 하나의 핵심 문제, 직접 명령형
        """
        if not violations:
            return ""

        v = violations[0]
        v_type = v.get("type", "unknown")
        item_name = v.get("item_or_subject", "")

        if v_type == "duplicate_acquisition":
            core_fix = f"'{item_name}' 획득 장면 삭제. 이미 소유 중이므로 '꺼내서 사용'으로 변경."
        elif v_type == "state_discontinuity":
            core_fix = "직전 Arc 종료 상태(내공/부상)를 그대로 이어서 시작."
        elif v_type == "premature_possession":
            core_fix = f"'{item_name}' 언급 삭제. 아직 획득 안 한 아이템."
        elif "protagonist" in v_type.lower():
            core_fix = f"주인공 이름을 '{protagonist_name}'으로 통일."
        else:
            core_fix = v.get("description", "위반사항 수정")[:80]

        feedback = f"""
<CRITICAL_INSTRUCTION priority="HIGHEST">
[재시도 {attempt + 1}회차] 아래 1개만 수정하면 PASS

🔴 수정 필수: {core_fix}
🔒 주인공: {protagonist_name} (변경 금지)

다른 건 그대로 두고, 위 사항만 고치세요.
</CRITICAL_INSTRUCTION>
"""
        return feedback.strip()

    def build_focused_context(self, violations: list, prev_arcs: list, protagonist_name: str) -> str:
        """[V60.21] 집중된 컨텍스트 생성 - 정보 과부하 방지"""
        if not prev_arcs:
            return ""

        last_arc = prev_arcs[-1]
        arc_end = last_arc.get("state_constraints", {}).get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})

        energy = arc_end.get("internal_energy", "?")
        injury = arc_end.get("injuries", "없음")
        inventory = joint.get("physical_inventory", [])
        if isinstance(inventory, list):
            inventory = ", ".join(inventory[:3])

        return f"""
<PREVIOUS_STATE>
내공: {energy}% | 부상: {injury} | 소지품: {inventory}
→ 이 상태로 시작해야 함
</PREVIOUS_STATE>
""".strip()

    def build_strong_kind_feedback_legacy(
        self, violations: list, attempt: int, protagonist_name: str = "주인공"
    ) -> str:
        """[V60.19 LEGACY] 기존 상세 피드백 (백업용)"""
        lines = [
            "",
            "█" * 60,
            "█  🚨 [V60.19] 필수 수정 사항 - 이것만 고치면 통과!  🚨  █",
            "█" * 60,
            "",
            f"📍 현재 {attempt + 1}회차 재시도입니다.",
            "📍 아래 사항만 수정하면 바로 PASS됩니다!",
            "",
        ]

        for i, v in enumerate(violations[:3], 1):
            v_type = v.get("type", "unknown")
            v_desc = v.get("description", "")[:150]
            item_name = v.get("item_or_subject", "")

            lines.append(f"━━━ 수정 {i} ━━━")

            if v_type == "duplicate_acquisition":
                lines.extend(
                    [
                        f"❌ 문제: '{item_name}'을(를) 다시 획득하려 함",
                        "✅ 해결: 이미 갖고 있으니 '사용'만 하세요!",
                    ]
                )
            elif v_type == "state_discontinuity":
                lines.extend(
                    [
                        f"❌ 문제: 상태가 갑자기 바뀜 - {v_desc[:80]}",
                        "✅ 해결: 직전 Arc 종료 상태를 그대로 이어가세요!",
                    ]
                )
            elif v_type == "premature_possession":
                lines.extend(
                    [
                        f"❌ 문제: 획득 안 한 '{item_name}'을(를) 이미 갖고 있음",
                        "✅ 해결: 이 아이템을 삭제하거나 획득 장면을 추가하세요!",
                    ]
                )
            elif "protagonist" in v_type.lower() or "주인공" in v_desc:
                lines.extend(
                    [
                        "❌ 문제: 주인공 이름이 잘못됨",
                        f"✅ 해결: 반드시 '{protagonist_name}'만 사용하세요!",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"❌ 문제: {v_desc[:100]}",
                        "✅ 해결: 위 내용을 수정해주세요.",
                    ]
                )

            lines.append("")

        lines.extend(
            [
                "█" * 60,
                f"█  위 {len(violations[:3])}가지만 고치면 PASS! 화이팅! 💪  █",
                "█" * 60,
                "",
            ]
        )

        return "\n".join(lines)

    def build_minimal_arc_context(self, prev_arcs: list, protagonist_name: str) -> str:
        """[V60.21] 최소 Arc 컨텍스트 생성 - 재시도 시 사용"""
        if not prev_arcs:
            return f"<CONTEXT>\n주인공: {protagonist_name}\n서사 시작점 (첫 Arc)\n</CONTEXT>"

        last_arc = prev_arcs[-1]
        arc_no = last_arc.get("arc_no", "?")

        state = last_arc.get("state_constraints", {})
        arc_end = state.get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})
        shadow = last_arc.get("status_shadow", {})

        energy = arc_end.get("internal_energy")
        if energy is None:
            loss = shadow.get("internal_energy_loss", "0%")
            try:
                loss_val = int(str(loss).replace("%", "").strip())
                energy = max(0, 100 - loss_val)
            except (ValueError, TypeError):
                energy = "?"

        injury = arc_end.get("injuries") or shadow.get("expected_injuries", "없음")
        location = arc_end.get("location") or joint.get("final_location", "?")

        inventory = arc_end.get("equipment") or joint.get("physical_inventory", [])
        if isinstance(inventory, str):
            inventory = [i.strip() for i in inventory.split(",") if i.strip()]
        if isinstance(inventory, list):
            inventory = inventory[:5]
            inventory_str = ", ".join(inventory) if inventory else "없음"
        else:
            inventory_str = str(inventory)[:100]

        return f"""<CONTEXT priority="HIGH">
주인공: {protagonist_name} (절대 변경 금지)

[Arc {arc_no} 종료 → 다음 Arc 시작 조건]
내공: {energy}%
부상: {injury}
위치: {location}
소지품: {inventory_str}

→ 위 상태 그대로 시작해야 함
→ 이미 가진 아이템 다시 획득 금지
</CONTEXT>"""

    # ═══════════════════════════════════════════════════════════════════════
    # Stage별 피드백
    # ═══════════════════════════════════════════════════════════════════════

    def generate_structured_arc_feedback(self, continuity_result: dict, prev_arcs: list = None, arc_no: int = 1) -> str:
        """[V60.9-1] Arc 검증 결과를 구조화된 Analyst 피드백으로 변환"""
        if not continuity_result:
            return ""

        violations = continuity_result.get("violations", [])
        if not violations:
            return ""

        lines = [
            "",
            "=" * 60,
            f"[V60.9 Arc {arc_no} 검증 결과 - 필수 수정 사항]",
            "=" * 60,
        ]

        item_violations = []
        npc_violations = []
        state_violations = []
        timeline_violations = []

        for v in violations:
            v_type = v.get("type", "unknown")
            v_desc = v.get("description", "")
            v_item = v.get("item_or_subject", "")
            v_loc = v.get("location", "")

            violation_entry = {"type": v_type, "desc": v_desc[:150], "item": v_item, "location": v_loc}

            if "item" in v_type.lower() or "acquisition" in v_type.lower():
                item_violations.append(violation_entry)
            elif "npc" in v_type.lower() or "relationship" in v_type.lower():
                npc_violations.append(violation_entry)
            elif "state" in v_type.lower() or "injury" in v_type.lower():
                state_violations.append(violation_entry)
            else:
                timeline_violations.append(violation_entry)

        if item_violations:
            lines.append("")
            lines.append("📦 [아이템 타임라인 오류]")
            for v in item_violations[:3]:
                lines.append(f"  ❌ {v['item'] or '알수없음'}: {v['desc']}")
                if v["location"]:
                    lines.append(f"     → 문제 위치: {v['location']}")
            lines.append("")
            lines.append("  💡 수정 방법:")
            lines.append("     - 이미 획득한 아이템을 다시 획득하는 장면 삭제")
            lines.append("     - 대신 '소지 중' 상태로 시작하여 '사용' 장면으로 대체")

        if npc_violations:
            lines.append("")
            lines.append("👤 [NPC/관계 오류]")
            for v in npc_violations[:3]:
                lines.append(f"  ❌ {v['item'] or '알수없음'}: {v['desc']}")
            lines.append("")
            lines.append("  💡 수정 방법:")
            lines.append("     - 사망한 NPC 재등장 삭제")
            lines.append("     - 관계 급변 시 중간 단계 추가 (멸시→의심→경외)")

        if state_violations:
            lines.append("")
            lines.append("💊 [상태 연속성 오류]")
            for v in state_violations[:3]:
                lines.append(f"  ❌ {v['desc']}")
            lines.append("")
            lines.append("  💡 수정 방법:")
            lines.append("     - 부상 상태 유지 (즉시 완치 금지)")
            lines.append("     - 내공 회복에 최소 2-3화 필요")

        if timeline_violations:
            lines.append("")
            lines.append("⏱️ [타임라인 오류]")
            for v in timeline_violations[:3]:
                lines.append(f"  ❌ {v['desc']}")

        if prev_arcs:
            last_arc = prev_arcs[-1] if prev_arcs else {}
            joint_docs = last_arc.get("joint_docs", {})
            if joint_docs:
                lines.append("")
                lines.append("=" * 60)
                lines.append("[직전 Arc 확정 상태 - 반드시 계승]")
                lines.append("=" * 60)
                lines.append(f"  📍 위치: {joint_docs.get('final_location', '미정')}")
                lines.append(f"  📦 소지품: {joint_docs.get('physical_inventory', '미정')}")
                if joint_docs.get("world_joint"):
                    lines.append(f"  🌍 세계 상태: {joint_docs.get('world_joint', '')[:100]}")

        lines.extend(["", "=" * 60, ""])
        return "\n".join(lines)

    def generate_structured_blueprint_feedback(
        self, director_result: dict, blueprint: dict = None, retry_count: int = 0
    ) -> str:
        """[V60.9-2] Blueprint 검증 결과를 구조화된 Architect 피드백으로 변환"""
        if not director_result:
            return ""

        score_breakdown = director_result.get("score_breakdown", {})
        if not score_breakdown:
            return ""

        lines = [
            "",
            "=" * 60,
            "[V60.9 Blueprint 검증 결과 - 우선순위별 수정 지침]",
            "=" * 60,
        ]

        issues = []

        setting_score = score_breakdown.get("setting_consistency", 100)
        if setting_score < 15:
            issues.append(
                {
                    "priority": "CRITICAL",
                    "area": "설정 일관성",
                    "score": setting_score,
                    "action": "미습득 무공/미획득 아이템 사용 장면 삭제. HUD 확인 필수.",
                }
            )
        elif setting_score < 18:
            issues.append(
                {
                    "priority": "HIGH",
                    "area": "설정 일관성",
                    "score": setting_score,
                    "action": "직전 화 상태와 불일치하는 설정 수정",
                }
            )

        scene_score = score_breakdown.get("scene_composition", 100)
        if scene_score < 10:
            issues.append(
                {
                    "priority": "CRITICAL",
                    "area": "장면 구성",
                    "score": scene_score,
                    "action": "장면 수 부족. 최소 5개 이상 설계 필요.",
                }
            )
        elif scene_score < 15:
            issues.append(
                {
                    "priority": "HIGH",
                    "area": "장면 구성",
                    "score": scene_score,
                    "action": "장면 밀도 불균형. 각 씬 분량을 균등하게 조정.",
                }
            )

        flow_score = score_breakdown.get("narrative_flow", 100)
        if flow_score < 10:
            issues.append(
                {
                    "priority": "CRITICAL",
                    "area": "서사 흐름",
                    "score": flow_score,
                    "action": "서사 폭주/정체 감지. 사건 분배 재조정 필요.",
                }
            )
        elif flow_score < 15:
            issues.append(
                {
                    "priority": "HIGH",
                    "area": "서사 흐름",
                    "score": flow_score,
                    "action": "같은 장소 3씬 이상 연속 금지. 위치 변화 추가.",
                }
            )

        length_score = score_breakdown.get("length_fulfillment", 100)
        if length_score < 10:
            issues.append(
                {
                    "priority": "CRITICAL",
                    "area": "분량",
                    "score": length_score,
                    "action": "설계 분량 절대 부족. 각 씬 목표 분량 명시.",
                }
            )

        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        issues.sort(key=lambda x: priority_order.get(x["priority"], 3))

        if issues:
            lines.append("")
            for i, issue in enumerate(issues[:5], 1):
                priority_emoji = "🔴" if issue["priority"] == "CRITICAL" else "🟠"
                lines.append(f"{i}. {priority_emoji} [{issue['priority']}] {issue['area']} ({issue['score']}점)")
                lines.append(f"   → 조치: {issue['action']}")
                lines.append("")
        else:
            lines.append("")
            lines.append("✅ 주요 문제 없음. 세부 품질 개선 집중.")

        lines.append("=" * 60)
        if retry_count == 0:
            lines.append("[첫 시도] 완벽한 설계를 목표로 하되, 위 이슈 우선 해결")
        elif retry_count == 1:
            lines.append("[2차 시도] CRITICAL/HIGH 이슈만 집중 해결")
        else:
            lines.append(f"[{retry_count + 1}차 시도] 최소 기준 충족에 집중 (CRITICAL만 해결)")

        lines.extend(["=" * 60, ""])
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    # 역방향 피드백
    # ═══════════════════════════════════════════════════════════════════════

    def generate_reverse_feedback_stage4_to_3(
        self, writer_reject_reason: str, pre_checklist_result: dict = None
    ) -> str:
        """[V60.9-3] Stage 4→3 역방향 피드백"""
        if not writer_reject_reason:
            return ""

        lines = [
            "",
            "=" * 50,
            "[V60.9 이전 원고 REJECT 피드백 - Blueprint 설계 참고]",
            "=" * 50,
        ]

        reason_lower = writer_reject_reason.lower()

        if "후반" in reason_lower or "요약" in reason_lower or "밀도" in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 후반부 밀도 부족")
            lines.append("   → 이번 Blueprint: Scene 5-6에 더 많은 이벤트 배치")
            lines.append("   → 각 씬 목표 분량을 명시적으로 설정")

        if "분량" in reason_lower or "짧" in reason_lower or "부족" in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 전체 분량 부족")
            lines.append("   → 이번 Blueprint: 씬 수 6개 이상 확보")
            lines.append("   → 각 씬에 세부 비트 2-3개 추가")

        if "설정" in reason_lower or "모순" in reason_lower or "일관" in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 설정 모순")
            lines.append("   → 이번 Blueprint: HUD/직전 화 상태 명시적 기재")
            lines.append("   → 사용 가능한 아이템/무공 목록 포함")

        if "대화" in reason_lower or "지문" in reason_lower:
            lines.append("")
            lines.append("⚠️ 이전 원고 문제: 대화/지문 비율 불균형")
            lines.append("   → 이번 Blueprint: 각 씬에 대화 장면 최소 1개 포함")

        if pre_checklist_result:
            failed_checks = [c for c in pre_checklist_result.get("items", []) if not c.get("passed", True)]
            if failed_checks:
                lines.append("")
                lines.append("📋 Pre-Checklist 실패 항목:")
                for check in failed_checks[:3]:
                    lines.append(f"   - {check.get('name', 'unknown')}: {check.get('message', '')[:50]}")

        lines.extend(["", "=" * 50, ""])
        return "\n".join(lines)

    def generate_reverse_feedback_stage3_to_2(self, architect_failures: list = None, arc_no: int = 1) -> str:
        """[V60.9-4] Stage 3→2 역방향 피드백"""
        if not architect_failures or len(architect_failures) < 3:
            return ""

        lines = [
            "",
            "=" * 50,
            f"[V60.9 Arc {arc_no} Blueprint 설계 반복 실패 - Arc 재검토 필요]",
            "=" * 50,
            "",
            f"⚠️ Blueprint 설계가 {len(architect_failures)}회 연속 실패했습니다.",
            "   Arc 수준에서 구조적 문제가 있을 수 있습니다.",
            "",
        ]

        failure_reasons = {}
        for failure in architect_failures:
            reason = failure.get("reason", "unknown")
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        if failure_reasons:
            lines.append("📊 반복된 실패 사유:")
            for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1])[:3]:
                lines.append(f"   - {reason}: {count}회")

        lines.extend(
            [
                "",
                "💡 Arc 수정 권장 사항:",
                "   1. 아이템/NPC 배치 시점 재검토",
                "   2. 씬 간 의존성 단순화",
                "   3. 핵심 갈등 요소 명확화",
                "",
                "=" * 50,
                "",
            ]
        )

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    # 적응형 / 분류
    # ═══════════════════════════════════════════════════════════════════════

    def get_adaptive_feedback_intensity(self, retry_count: int, stage: int = 4) -> dict:
        """[V60.9-5] 적응형 피드백 강도 조절"""
        if stage == 2:
            if retry_count == 0:
                return {
                    "pass_threshold": 70,
                    "feedback_level": "detailed",
                    "strictness": "high",
                    "guidance": "완벽한 Arc 설계를 목표로 합니다. 모든 제약 조건을 준수하세요.",
                }
            elif retry_count == 1:
                return {
                    "pass_threshold": 65,
                    "feedback_level": "focused",
                    "strictness": "medium",
                    "guidance": "CRITICAL 이슈만 해결하세요. 부가적 품질은 차후 개선.",
                }
            else:
                return {
                    "pass_threshold": 55,
                    "feedback_level": "minimal",
                    "strictness": "low",
                    "guidance": "최소 기준 충족에 집중하세요. 아이템/NPC 타임라인만 정확히.",
                }

        elif stage == 3:
            if retry_count == 0:
                return {
                    "pass_threshold": 70,
                    "feedback_level": "detailed",
                    "strictness": "high",
                    "guidance": "6개 이상의 균형 잡힌 씬을 설계하세요.",
                }
            elif retry_count == 1:
                return {
                    "pass_threshold": 60,
                    "feedback_level": "focused",
                    "strictness": "medium",
                    "guidance": "핵심 씬 5개 확보, 설정 일관성 유지에 집중.",
                }
            else:
                return {
                    "pass_threshold": 50,
                    "feedback_level": "minimal",
                    "strictness": "low",
                    "guidance": "최소 4개 씬, 기본 연속성만 확보하세요.",
                }

        else:  # Stage 4
            if retry_count == 0:
                return {
                    "pass_threshold": 70,
                    "feedback_level": "detailed",
                    "strictness": "high",
                    "guidance": f"{ManuscriptLimits.TARGET_LENGTH}자 이상, 균형 잡힌 씬 분배를 목표로.",
                }
            elif retry_count == 1:
                return {
                    "pass_threshold": 65,
                    "feedback_level": "focused",
                    "strictness": "medium",
                    "guidance": f"{ManuscriptLimits.WARNING_LENGTH}자 이상, 핵심 씬 반영에 집중.",
                }
            else:
                return {
                    "pass_threshold": 55,
                    "feedback_level": "minimal",
                    "strictness": "low",
                    "guidance": f"{ManuscriptLimits.MIN_LENGTH}자 최소 기준, Blueprint 핵심만 반영.",
                }

    def classify_rejection_feedback(self, reason: str, feedback: str, blueprint: dict = None) -> str:
        """[V56] REJECT 피드백 분류 및 구조화"""
        reason_lower = reason.lower() if reason else ""
        feedback_lower = feedback.lower() if feedback else ""

        classified_parts = ["\n[🚨 V56 STRUCTURED REJECTION FEEDBACK]"]

        if any(kw in reason_lower for kw in ["분량", "length", "자", "미달", "부족"]):
            classified_parts.append("📏 [분량 문제]")
            classified_parts.append("   - 원고 분량이 목표에 미달합니다.")
            classified_parts.append("   - 각 씬의 묘사를 더 풍부하게 작성하세요.")
            classified_parts.append("   - 대화 장면, 감각 묘사, 내면 서술을 추가하세요.")

        elif any(kw in reason_lower for kw in ["씬", "scene", "누락", "missing"]):
            classified_parts.append("📋 [씬 누락]")
            if blueprint:
                scene_breakdown = blueprint.get("scene_breakdown", {})
                scene_names = list(scene_breakdown.keys())[:6]
                classified_parts.append(f"   - Blueprint 필수 씬: {', '.join(scene_names)}")
            classified_parts.append("   - 모든 씬을 순서대로 빠짐없이 작성하세요.")

        elif any(kw in reason_lower for kw in ["연속", "continuity", "이전", "직전"]):
            classified_parts.append("🔗 [연속성 오류]")
            classified_parts.append("   - 직전 화와의 연결이 부자연스럽습니다.")
            classified_parts.append("   - 직전 화 마지막 상황에서 자연스럽게 이어지도록 수정하세요.")

        elif any(kw in reason_lower for kw in ["아이템", "item", "소지", "미획득"]):
            classified_parts.append("🎒 [아이템 오류]")
            classified_parts.append("   - 소지하지 않은 아이템을 사용했거나, 소지품 연속성 오류입니다.")
            classified_parts.append("   - 현재 소지품 목록을 확인하고 해당 아이템만 사용하세요.")

        elif any(kw in reason_lower for kw in ["관계", "relationship", "급변", "jump"]):
            classified_parts.append("👥 [관계 급변]")
            classified_parts.append("   - NPC 관계가 너무 급격하게 변화했습니다.")
            classified_parts.append("   - 무시→의심→경외→충성 단계를 자연스럽게 거치세요.")

        elif any(kw in reason_lower for kw in ["show", "tell", "감정", "서술"]):
            classified_parts.append("✍️ [Show Don't Tell 위반]")
            classified_parts.append("   - 직접 감정 서술이 과다합니다.")
            classified_parts.append("   - '분노했다' 대신 '주먹을 꽉 쥐었다' 같이 행동으로 보여주세요.")

        else:
            classified_parts.append("⚠️ [기타 문제]")
            classified_parts.append(f"   - 사유: {reason[:200]}")

        if feedback:
            classified_parts.append("\n📝 [Director 원본 피드백]")
            classified_parts.append(f"   {feedback[:500]}")

        return "\n".join(classified_parts)

    # ═══════════════════════════════════════════════════════════════════════
    # 재시도
    # ═══════════════════════════════════════════════════════════════════════

    def simplify_prompt_for_retry(self, enhanced_feedback: str, core_feedback: str, attempt: int) -> str:
        """[V60.5] 3회차 이상 재시도 시 프롬프트 간소화"""
        lines = [
            f"🎯 [V60.5 간소화 모드 - {attempt + 1}회차 재시도]",
            "⚠️ 이전 시도들이 실패했습니다. 아래 핵심 지시에만 집중하세요.",
            "",
        ]

        if core_feedback:
            critical_issues = []
            if "분량" in core_feedback or "자" in core_feedback:
                critical_issues.append("📏 분량: 4,500자 이상 확보")
            if "폭주" in core_feedback:
                critical_issues.append("🔄 서사 폭주 금지: 사건을 더 잘게 쪼개라")
            if "정체" in core_feedback:
                critical_issues.append("🔄 서사 정체 금지: 반복 대신 전진하라")
            if "씬" in core_feedback or "장면" in core_feedback:
                critical_issues.append("🎬 모든 씬 반영: Blueprint 씬을 빠짐없이 포함")
            if "설정" in core_feedback or "무공" in core_feedback:
                critical_issues.append("⚙️ 설정 준수: 미습득 무공 사용 금지")
            if "밀도" in core_feedback or "균등" in core_feedback:
                critical_issues.append("📊 밀도 균등: 앞뒤 분량 균형 맞추기")

            if not critical_issues:
                critical_issues = ["📏 분량 4,500자 이상", "🎬 6개 씬 모두 반영", "⚙️ Hard Constraints 준수"]

            lines.append("**핵심 수정 사항:**")
            for issue in critical_issues[:5]:
                lines.append(f"  {issue}")

        lines.append("")
        lines.append("💡 다른 부가 지시는 무시하고 위 핵심 사항만 해결하세요.")

        lines.append("")
        lines.append("✅ PASS 가능 조건 (3회차+):")
        lines.append("  - 3~4개 씬만 있어도 OK (밀도 유지 시)")
        lines.append("  - 분량 4,000자 이상이면 통과 가능")
        lines.append("  - Hard Constraints만 지키면 승인")

        return "\n".join(lines)
