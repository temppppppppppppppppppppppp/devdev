"""
[V47] TIER 0.5: CONTINUITY Validator
에피소드 간 연속성 검증 (API 호출 불필요 - 순수 Python)

핵심 역할:
1. 아이템 소지 연속성 - 이미 가진 아이템을 다시 획득하러 가는 패턴 감지
2. 무기 소지 연속성 - 들고 있던 무기가 사라지는 문제 감지
3. 부상 상태 연속성 - 부상 상태에서 무리한 행동 감지
4. 위치 연속성 - 순간이동 방지

실행 시점:
- Blueprint 생성 시 (Architect) → 사전 검증
- Manuscript 생성 시 (Director) → 재확인

비용: $0 (LLM 호출 없음)
"""

import logging
import re

from modules.validation.threshold_helper import _threshold  # [Phase 5-B-2c]


class ContinuityValidator:
    """
    TIER 0.5: 에피소드 간 연속성 검증

    BLOCKING보다 먼저 실행되어야 함.
    직전 에피소드 상태와 현재 원고/블루프린트 간 모순 감지.
    """

    def __init__(self, context=None) -> None:
        """
        Args:
            context: ProjectContext 객체 (직전 에피소드 데이터 조회용)
        """
        self.context = context

        # 아이템 획득 패턴 (한국어)
        self.acquire_patterns = [
            r"(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들|획득|챙기|얻|주워\s*들)",
            r"(.+?)(?:을|를)\s*(?:손에\s*넣|가져가|챙겨\s*들)",
            r"(?:녹슨|묵직한|육중한)?\s*(.+?)(?:을|를)\s*(?:집어\s*들|뽑아\s*들)",
        ]

        # 아이템 분실 패턴
        self.lose_patterns = [
            r"(.+?)(?:을|를)\s*(?:잃어버리|놓치|떨어뜨리|버리|내려놓)",
            r"(.+?)(?:이|가)\s*(?:부러지|파손되|사라지)",
        ]

        # 부상 관련 패턴
        self.injury_patterns = [
            r"(?:부상|상처|골절|파열|출혈|중상|경상)",
            r"(?:어깨|팔|다리|등|가슴|복부).*?(?:다치|부상|파열)",
        ]

        # 무리한 행동 패턴 (부상 시 불가능한 행동)
        self.strenuous_patterns = [
            r"(?:휘두르|내리치|베어|찌르|막아내)",
            r"(?:달리|뛰어|도약|점프)",
            r"(?:들어올리|메|짊어지)",
        ]

        # 이동 패턴 (위치 변경 감지용)
        self.location_patterns = [
            r"(?:로|으로)\s*(?:향하|이동하|걸어가|달려가)",
            r"(?:에서|부터)\s*(?:나와|나서|떠나)",
            r"(?:에|로)\s*(?:도착|당도)",
        ]

    def validate(
        self, current_ep: int, manuscript: str, validation_context: dict, prev_hud: dict | None = None
    ) -> dict:
        """
        연속성 검증 실행

        Args:
            current_ep: 현재 에피소드 번호
            manuscript: 현재 원고/블루프린트
            validation_context: 검증 컨텍스트
            prev_hud: 직전 에피소드 HUD (없으면 context에서 조회)

        Returns:
            {
                "tier": "CONTINUITY",
                "passed": True/False,
                "violations": [...],
                "warnings": [...],
                "message": "..."
            }
        """
        violations = []
        warnings = []

        # 1화는 이전 에피소드가 없으므로 스킵
        if current_ep <= 1:
            return {
                "tier": "CONTINUITY",
                "passed": True,
                "violations": [],
                "warnings": [],
                "message": "첫 번째 에피소드 - 연속성 검증 스킵",
            }

        # 직전 에피소드 HUD 가져오기
        if prev_hud is None:
            prev_hud = validation_context.get("prev_hud") or validation_context.get("martial_hud")
        if prev_hud is None:
            prev_hud = self._get_prev_hud(current_ep, validation_context)

        # [P3-01] prev_hud 완전 누락 시 DEGRADED 조기 반환
        # skip_continuity=True (Blueprint 모드)면 PASS, 아니면 fail-closed (TF-15 P0-06)
        if not prev_hud:
            skip = validation_context.get("skip_continuity", False) if isinstance(validation_context, dict) else False
            logging.warning(
                "[CONTINUITY] prev_hud 누락 — HUD 의존 연속성 검증 DEGRADED. "
                "validation_context에 prev_hud를 주입하세요."
            )
            return {
                "tier": "CONTINUITY",
                "passed": bool(skip),
                "score": 1.0 if skip else 0.0,
                "degraded": True,
                "violations": [] if skip else [
                    {
                        "type": "prev_hud_missing",
                        "severity": "BLOCKING",
                        "reason": "prev_hud missing; continuity checks cannot be trusted",
                        "fix_suggestion": "inject prev_hud into validation_context before continuity validation",
                    }
                ],
                "warnings": ["prev_hud 누락으로 연속성 검증 스킵" if skip else "prev_hud 누락으로 연속성 검증 DEGRADED"],
                "message": "prev_hud missing - continuity validation skipped (blueprint mode)" if skip
                           else "prev_hud missing - continuity validation failed (degraded)",
                "violation_count": 0,
                "warning_count": 1,
            }

        # [V66.1] prev_hud 의존 검증 (1~4): [P3-01] prev_hud 없는 경우는 위에서 조기 반환됨
        # 직전 원고 가져오기 (선택적)
        prev_manuscript = self._get_prev_manuscript(current_ep, validation_context)

        # ═══════════════════════════════════════════════════════════════
        # 검증 1: 아이템 소지 연속성
        # ═══════════════════════════════════════════════════════════════
        item_check = self._check_item_continuity(current_ep, manuscript, prev_hud, prev_manuscript)
        if not item_check["passed"]:
            violations.extend(item_check["violations"])
        warnings.extend(item_check.get("warnings", []))

        # ═══════════════════════════════════════════════════════════════
        # 검증 2: 무기 소지 연속성
        # ═══════════════════════════════════════════════════════════════
        weapon_check = self._check_weapon_continuity(current_ep, manuscript, prev_hud, prev_manuscript)
        if not weapon_check["passed"]:
            violations.extend(weapon_check["violations"])
        warnings.extend(weapon_check.get("warnings", []))

        # ═══════════════════════════════════════════════════════════════
        # 검증 3: 부상 상태 연속성
        # ═══════════════════════════════════════════════════════════════
        injury_check = self._check_injury_continuity(current_ep, manuscript, prev_hud, prev_manuscript)
        if not injury_check["passed"]:
            violations.extend(injury_check["violations"])
        warnings.extend(injury_check.get("warnings", []))

        # ═══════════════════════════════════════════════════════════════
        # 검증 4: 위치 연속성 [V66.1] 불가능한 순간이동 BLOCKING 추가
        # ═══════════════════════════════════════════════════════════════
        location_check = self._check_location_continuity(current_ep, manuscript, prev_hud, prev_manuscript)
        if not location_check["passed"]:
            violations.extend(location_check["violations"])
        warnings.extend(location_check.get("warnings", []))

        # ═══════════════════════════════════════════════════════════════
        # 검증 5: [V66.1] NPC 성격 연속성 (MAJOR WARNING)
        # ═══════════════════════════════════════════════════════════════
        personality_check = self._check_personality_continuity(manuscript, validation_context)
        # [V66.2] C-2: 성격 모순 감지 결과를 명확한 경고로 전달
        _personality_violations = personality_check.get("violations", [])
        for _pv in _personality_violations:
            if isinstance(_pv, dict):
                warnings.append(f"[V66.2] 성격 모순 경고: {_pv.get('description', _pv.get('reason', str(_pv)))}")
            else:
                warnings.append(f"[V66.2] 성격 모순 경고: {_pv}")

        # ═══════════════════════════════════════════════════════════════
        # 검증 6: [V66.1] 시간 일관성 (BLOCKING if severe)
        # ═══════════════════════════════════════════════════════════════
        time_check = self._check_time_consistency(manuscript, validation_context)
        if not time_check["passed"]:
            violations.extend(time_check.get("violations", []))
        warnings.extend(time_check.get("warnings", []))

        # 결과 집계
        passed = len(violations) == 0

        if passed:
            message = "연속성 검증 통과"
        else:
            message = f"연속성 위반 {len(violations)}건 감지"

        return {
            "tier": "CONTINUITY",
            "passed": passed,
            "violations": violations,
            "warnings": warnings,
            "message": message,
            "violation_count": len(violations),
            "warning_count": len(warnings),
        }

    def _get_prev_hud(self, current_ep: int, validation_context: dict) -> dict | None:
        """직전 에피소드 HUD 가져오기"""
        # 1. validation_context에서 직접 제공된 경우
        prev_hud = validation_context.get("prev_hud")
        if prev_hud:
            return prev_hud

        # 2. context를 통해 DB에서 조회
        # [P0] manuscripts 테이블에 hud_snapshot 컬럼 없음 — 항상 None 반환
        # 실제 prev_hud는 validation_context["prev_hud"]로 주입해야 함
        if self.context and hasattr(self.context, "db"):
            try:
                prev_ep = current_ep - 1
                manuscript_data = self.context.db.get_manuscript(prev_ep)
                if manuscript_data:
                    hud_snapshot = manuscript_data.get("hud_snapshot")
                    if hud_snapshot:
                        if isinstance(hud_snapshot, str):
                            import json

                            return json.loads(hud_snapshot)
                        return hud_snapshot
            except Exception as e:
                logging.warning(f"⚠️ [CONTINUITY] 직전 HUD 조회 실패: {e}")

        # [TF-XC-04] 현재 HUD를 이전 HUD로 사용하면 false negative 발생
        logging.info("[CONTINUITY] 이전 HUD 조회 불가 — 연속성 검사 스킵")

        return None

    def _get_prev_manuscript(self, current_ep: int, validation_context: dict) -> str | None:
        """직전 에피소드 원고 가져오기"""
        # 1. validation_context에서 제공된 경우
        prev_text = validation_context.get("prev_full_text")
        if prev_text:
            return prev_text

        # 2. history에서 가져오기
        history = validation_context.get("history", [])
        if history and len(history) > 0:
            last_entry = history[-1]
            if isinstance(last_entry, dict):
                return last_entry.get("text", "")
            return str(last_entry)

        # 3. context를 통해 DB에서 조회
        if self.context and hasattr(self.context, "db"):
            try:
                prev_ep = current_ep - 1
                manuscript_data = self.context.db.get_manuscript(prev_ep)
                if manuscript_data:
                    return manuscript_data.get("content", "")
            except Exception as e:
                logging.warning(f"⚠️ [CONTINUITY] 직전 원고 조회 실패: {e}")

        return None

    def _extract_equipment(self, hud: dict) -> set[str]:
        """HUD에서 장비 목록 추출"""
        equipment = set()

        # actual_truth.equipment 경로
        actual_truth = hud.get("actual_truth", {})
        eq_data = actual_truth.get("equipment", hud.get("equipment", []))

        if isinstance(eq_data, list):
            for item in eq_data:
                if isinstance(item, str) and item.strip():
                    equipment.add(item.strip())
                elif isinstance(item, dict):
                    name = item.get("name", item.get("item", ""))
                    if name:
                        equipment.add(name.strip())
        elif isinstance(eq_data, str):
            equipment.add(eq_data.strip())
        elif isinstance(eq_data, dict):
            for key, value in eq_data.items():
                if isinstance(value, str) and value:
                    equipment.add(value.strip())
                elif key and isinstance(key, str):
                    equipment.add(key.strip())

        return equipment

    def _check_item_continuity(
        self, current_ep: int, manuscript: str, prev_hud: dict, prev_manuscript: str | None
    ) -> dict:
        """
        아이템 소지 연속성 검증
        - 이미 소유한 아이템을 다시 획득하러 가는 패턴 감지
        """
        if prev_manuscript is None:
            prev_manuscript = ""
        violations = []
        warnings = []

        # 직전 HUD에서 소유 아이템 추출
        prev_equipment = self._extract_equipment(prev_hud)

        if not prev_equipment:
            return {"passed": True, "violations": [], "warnings": []}

        # 현재 원고에서 획득 패턴 검색
        for pattern in self.acquire_patterns:
            matches = re.findall(pattern, manuscript)
            for item_name in matches:
                item_name = item_name.strip()
                if not item_name:
                    continue

                # 이미 소유한 아이템인지 확인 (부분 매칭)
                for owned_item in prev_equipment:
                    # 핵심 키워드 추출 (예: "녹슨 백근 대도" → "대도", "백근")
                    if self._is_same_item(item_name, owned_item):
                        violations.append(
                            {
                                "type": "duplicate_acquisition",
                                "severity": "CRITICAL",
                                "item": item_name,
                                "owned_item": owned_item,
                                "reason": f"이미 소유한 '{owned_item}'을(를) 다시 획득하려 함",
                                "prev_ep": current_ep - 1,
                                "fix_suggestion": f"'{owned_item}'는 이미 제{current_ep - 1}화에서 획득함. "
                                f"현재 에피소드에서는 소지 상태로 시작해야 함.",
                            }
                        )
                        break

        return {"passed": len(violations) == 0, "violations": violations, "warnings": warnings}

    def _check_weapon_continuity(
        self, current_ep: int, manuscript: str, prev_hud: dict, prev_manuscript: str | None
    ) -> dict:
        """
        무기 소지 연속성 검증
        - 직전 에피소드 끝에서 들고 있던 무기가 현재 에피소드에서 사라지는 문제
        """
        if prev_manuscript is None:
            prev_manuscript = ""
        violations = []
        warnings = []

        # 직전 원고 끝부분에서 무기 소지 상태 확인
        if prev_manuscript:
            # 마지막 500자에서 무기 관련 언급 찾기
            last_part = prev_manuscript[-500:] if len(prev_manuscript) > 500 else prev_manuscript

            # 무기를 들고 있는 패턴
            holding_patterns = [
                r"(.+?)(?:을|를)\s*(?:어깨에\s*메|손에\s*들|쥐)",
                r"(.+?)(?:을|를)\s*(?:끌며|끌고)",
                r"(?:메고|들고|쥐고)\s*(?:있는|있던)\s*(.+?)",
            ]

            held_weapons = set()
            for pattern in holding_patterns:
                matches = re.findall(pattern, last_part)
                for match in matches:
                    if isinstance(match, tuple):
                        for m in match:
                            if m.strip():
                                held_weapons.add(m.strip())
                    elif match.strip():
                        held_weapons.add(match.strip())

            # 현재 원고 첫 500자에서 해당 무기 확인
            if held_weapons:
                first_part = manuscript[:500] if len(manuscript) > 500 else manuscript

                for weapon in held_weapons:
                    # 무기 언급이 있는지 확인
                    if weapon not in first_part:
                        # 핵심 키워드로 재확인
                        keywords = self._extract_keywords(weapon)
                        mentioned = any(kw in first_part for kw in keywords if len(kw) > 1)

                        if not mentioned:
                            # 무기를 다시 획득하러 가는지 확인
                            acquiring = any(re.search(pattern, first_part) for pattern in self.acquire_patterns)

                            if acquiring:
                                violations.append(
                                    {
                                        "type": "weapon_reset",
                                        "severity": "CRITICAL",
                                        "weapon": weapon,
                                        "reason": f"직전 에피소드 끝에서 '{weapon}'을(를) 소지하고 있었으나, "
                                        f"현재 에피소드에서 다시 획득하러 감",
                                        "prev_ep": current_ep - 1,
                                        "fix_suggestion": f"'{weapon}'는 이미 소지 중. "
                                        f"에피소드 시작 시 소지 상태로 묘사해야 함.",
                                    }
                                )

        return {"passed": len(violations) == 0, "violations": violations, "warnings": warnings}

    def _check_injury_continuity(
        self, current_ep: int, manuscript: str, prev_hud: dict, prev_manuscript: str | None
    ) -> dict:
        """
        [V66.1] 부상 상태 연속성 검증 (강화)
        - SEVERE 부상(위독/빈사/중상/골절/파열)에서 회복 묘사 없이 정상 행동 → BLOCKING
        - 경미한 부상에서 무리한 행동 → WARNING (기존)
        """
        if prev_manuscript is None:
            prev_manuscript = ""
        violations = []
        warnings = []

        # 직전 HUD에서 부상 상태 확인
        if not isinstance(prev_hud, dict):  # [V70] str/None 타입 방어
            prev_hud = {}
        actual_truth = prev_hud.get("actual_truth", {})
        condition = actual_truth.get("condition", prev_hud.get("condition", ""))
        condition_str = str(condition)

        # 부상 상태인지 확인
        injury_keywords = ["부상", "상처", "파열", "골절", "중상", "경상", "출혈", "다친"]
        has_injury = any(kw in condition_str for kw in injury_keywords)

        # [V66.1] SEVERE 부상 키워드 (회복 없이 정상 행동 시 BLOCKING)
        severe_keywords = ["위독", "빈사", "중상", "골절", "파열", "의식불명", "혼수"]
        has_severe_injury = any(kw in condition_str for kw in severe_keywords)

        # 직전 원고에서 부상 언급 확인
        if prev_manuscript and not has_injury:
            last_part = prev_manuscript[-1000:] if len(prev_manuscript) > 1000 else prev_manuscript
            for pattern in self.injury_patterns:
                if re.search(pattern, last_part):
                    has_injury = True
                    break
            # [V66.1] 직전 원고에서 SEVERE 부상 감지
            if not has_severe_injury:
                severe_manuscript_patterns = [
                    r"위독",
                    r"빈사",
                    r"의식을?\s*잃",
                    r"혼수",
                    r"골절",
                    r"파열",
                    r"피를\s*토하",
                ]
                for sp in severe_manuscript_patterns:
                    if re.search(sp, last_part):
                        has_severe_injury = True
                        break

        if has_injury:
            # 현재 원고에서 부상 부위 특정
            injury_detail = self._extract_injury_detail(condition_str, prev_manuscript)

            # [V66.1] SEVERE 부상: 회복 묘사 없이 정상 행동 → BLOCKING
            if has_severe_injury:
                recovery_patterns = [
                    r"치료",
                    r"요양",
                    r"회복",
                    r"낫",
                    r"치유",
                    r"약을?\s*먹",
                    r"금창약",
                    r"영약",
                    r"내상.*?회복",
                    r"며칠.*?지나",
                    r"시간이?\s*흘러",
                    r"이튿날",
                    r"의원",
                    r"의술",
                    r"침을?\s*놓",
                ]
                first_500 = manuscript[:500] if len(manuscript) > 500 else manuscript
                has_recovery = any(re.search(rp, first_500) for rp in recovery_patterns)

                # 정상 행동 패턴 (SEVERE 부상과 양립 불가)
                normal_action_patterns = [
                    r"힘차게",
                    r"거침없이",
                    r"가볍게",
                    r"자유롭게",
                    r"아무런?\s*문제.*?없",
                    r"멀쩡",
                    r"성한",
                    r"평소처럼",
                    r"평소와?\s*다름없",
                ]
                acts_normal = any(re.search(np, manuscript) for np in normal_action_patterns)

                if not has_recovery and acts_normal:
                    violations.append(
                        {
                            "type": "severe_injury_ignored",
                            "severity": "BLOCKING",
                            "injury": injury_detail,
                            "reason": f"SEVERE 부상({injury_detail})에서 회복 묘사 없이 정상 행동. "
                            f"치료/요양/시간경과 장면 필수.",
                            "fix_suggestion": "에피소드 초반에 치료/회복 장면을 추가하거나, "
                            "부상 상태를 반영한 행동으로 수정하세요.",
                        }
                    )

            # 부상 부위와 관련된 무리한 행동 검색
            strenuous_actions = []
            for pattern in self.strenuous_patterns:
                matches = re.findall(pattern, manuscript)
                strenuous_actions.extend(matches)

            if strenuous_actions:
                # 정당화 패턴 확인 (역근경, 진기, 내공 등)
                justification_patterns = [
                    r"역근경",
                    r"내공.*?운용",
                    r"진기.*?순환",
                    r"고통.*?억누르",
                    r"이를\s*악물",
                ]

                has_justification = any(re.search(jp, manuscript) for jp in justification_patterns)

                if not has_justification:
                    warnings.append(
                        {
                            "type": "injury_action_mismatch",
                            "severity": "WARNING",
                            "injury": injury_detail,
                            "actions": strenuous_actions[:3],
                            "reason": f"부상 상태({injury_detail})에서 무리한 행동 감지. "
                            f"정당화 묘사 권장 (역근경, 내공 운용 등)",
                            "fix_suggestion": "부상에도 불구하고 행동하는 이유를 내공/정신력 등으로 정당화",
                        }
                    )

        return {
            "passed": len(violations) == 0,  # [V66.1] SEVERE 부상 무시 시 REJECT
            "violations": violations,
            "warnings": warnings,
        }

    # [V66.1] 물리적으로 불가능한 순간이동 쌍 (시간 경과 없이 이동 불가)
    DISTANT_LOCATION_PAIRS = [
        # 무협: 대륙 반대편
        ("하북", "사천"),
        ("하북", "강남"),
        ("산서", "강남"),
        ("산동", "사천"),
        ("중원", "서역"),
        ("강북", "남해"),
        ("요동", "사천"),
        ("요동", "강남"),
        # 헌터: 대도시 간 (순간이동 게이트 없이)
        ("서울", "부산"),
        ("서울", "제주"),
        ("경기", "제주"),
        # 투자: 글로벌
        ("서울", "뉴욕"),
        ("서울", "런던"),
        ("서울", "도쿄"),
    ]

    def _check_location_continuity(
        self, current_ep: int, manuscript: str, prev_hud: dict, prev_manuscript: str | None
    ) -> dict:
        """
        [V66.1] 위치 연속성 검증 (강화)
        - 불가능한 순간이동 (DISTANT_LOCATION_PAIRS) → BLOCKING
        - 일반적인 위치 변화 → WARNING (기존)
        """
        if prev_manuscript is None:
            prev_manuscript = ""
        violations = []
        warnings = []

        # HUD에서 위치 정보 추출 (가장 신뢰할 수 있는 소스)
        if not isinstance(prev_hud, dict):  # [V70] str/None 타입 방어
            prev_hud = {}
        actual_truth = prev_hud.get("actual_truth", {})
        prev_hud_location = actual_truth.get("location", prev_hud.get("location", ""))

        # 직전 원고 끝부분에서 위치 확인
        if prev_manuscript:
            last_part = prev_manuscript[-300:] if len(prev_manuscript) > 300 else prev_manuscript
            first_part = manuscript[:300] if len(manuscript) > 300 else manuscript

            # 직전 위치 키워드
            prev_locations = set()
            location_markers = [
                r"(?:에서|에)\s*(.{2,10}?)(?:에서|에|를|을)",
                r"(.{2,10}?)(?:로|으로)\s*(?:향하|이동|가|걸어)",
            ]

            for pattern in location_markers:
                matches = re.findall(pattern, last_part)
                prev_locations.update(m.strip() for m in matches if m.strip())

            # HUD 위치도 추가
            if prev_hud_location:
                prev_locations.add(prev_hud_location)

            # 현재 위치 키워드
            curr_locations = set()
            for pattern in location_markers:
                matches = re.findall(pattern, first_part)
                curr_locations.update(m.strip() for m in matches if m.strip())

            # 위치 연결 확인 (시간 경과 없이 급격한 위치 변화)
            time_markers = [
                "이튿날",
                "다음날",
                "며칠 후",
                "시간이 지나",
                "해가 지고",
                "날이 밝",
                "몇 달",
                "수일",
                "한 달",
                "보름",
                "열흘",
            ]
            has_time_skip = any(tm in first_part for tm in time_markers)

            if prev_locations and curr_locations and not has_time_skip:
                # [V66.1] 불가능한 순간이동 체크 (DISTANT_LOCATION_PAIRS)
                for prev_loc in prev_locations:
                    for curr_loc in curr_locations:
                        for loc_a, loc_b in self.DISTANT_LOCATION_PAIRS:
                            if (loc_a in prev_loc and loc_b in curr_loc) or (loc_b in prev_loc and loc_a in curr_loc):
                                violations.append(
                                    {
                                        "type": "impossible_teleportation",
                                        "severity": "BLOCKING",
                                        "prev_location": prev_loc,
                                        "curr_location": curr_loc,
                                        "reason": f"불가능한 순간이동: '{prev_loc}' → '{curr_loc}' "
                                        f"(시간 경과 묘사 없이 먼 거리 이동)",
                                        "fix_suggestion": "이동 경위를 묘사하거나, "
                                        "시간 경과 표현(며칠 후, 이튿날 등)을 추가하세요.",
                                    }
                                )
                                break  # 한 쌍만 감지하면 충분
                    if violations:
                        break
                if not violations:
                    # 위치가 완전히 다르면 경고 (기존)
                    overlap = prev_locations & curr_locations
                    if not overlap and len(prev_locations) > 0 and len(curr_locations) > 0:
                        warnings.append(
                            {
                                "type": "location_jump",
                                "severity": "INFO",
                                "prev_locations": list(prev_locations)[:3],
                                "curr_locations": list(curr_locations)[:3],
                                "reason": "위치 변화가 감지됨. 이동 경위 묘사 권장",
                                "fix_suggestion": "이전 위치에서 현재 위치로 이동하는 과정을 간략히 묘사",
                            }
                        )

        return {
            "passed": len(violations) == 0,  # [V66.1] 불가능한 순간이동 시 REJECT
            "violations": violations,
            "warnings": warnings,
        }

    def _is_same_item(self, item1: str, item2: str) -> bool:
        """두 아이템이 같은 것인지 판단 (부분 매칭)"""
        # 정규화
        item1 = item1.strip().lower()
        item2 = item2.strip().lower()

        # 완전 일치
        if item1 == item2:
            return True

        # 한쪽이 다른 쪽을 포함
        if item1 in item2 or item2 in item1:
            return True

        # 핵심 키워드 비교
        keywords1 = self._extract_keywords(item1)
        keywords2 = self._extract_keywords(item2)

        # 2개 이상의 키워드가 일치하면 같은 아이템으로 판단
        common = keywords1 & keywords2
        if len(common) >= 2:
            return True

        # 핵심 단어가 일치하면 같은 아이템
        important_words = ["대도", "검", "창", "도끼", "활", "패", "옥", "환", "단"]
        for word in important_words:
            if word in item1 and word in item2:
                return True

        return False

    def _extract_keywords(self, text: str) -> set[str]:
        """텍스트에서 핵심 키워드 추출"""
        # 한글 단어만 추출
        words = re.findall(r"[가-힣]+", text)
        # 조사/접미사 제거
        stopwords = {"을", "를", "이", "가", "에", "에서", "으로", "로", "의", "한", "된", "인"}
        keywords = {w for w in words if w not in stopwords and len(w) > 1}
        return keywords

    def _extract_injury_detail(self, condition: str, prev_manuscript: str | None) -> str:
        """부상 상세 정보 추출"""
        if "어깨" in condition or (prev_manuscript and "어깨" in prev_manuscript[-500:]):
            return "어깨 부상"
        if "팔" in condition or (prev_manuscript and "팔" in prev_manuscript[-500:]):
            return "팔 부상"
        if "다리" in condition or (prev_manuscript and "다리" in prev_manuscript[-500:]):
            return "다리 부상"
        if "파열" in condition:
            return "근육 파열"
        return "부상 상태"

    # ═══════════════════════════════════════════════════════════════════════
    # [V66.1] NPC 성격 연속성 검증
    # ═══════════════════════════════════════════════════════════════════════

    # 냉혹/잔혹 성격에 모순되는 감정 표현 (NPC 이름 근처에서 검색)
    _COLD_TRAITS = {"냉혹", "잔혹", "무자비", "냉정", "냉담", "비정", "살벌"}
    _COLD_CONTRADICTIONS = {"눈물", "울며", "감동", "미소", "따뜻", "다정", "온화", "부드럽"}

    # 자비/온화 성격에 모순되는 표현
    _KIND_TRAITS = {"자비", "온화", "인자", "자상", "다정", "따뜻", "온유"}
    _KIND_CONTRADICTIONS = {"잔인", "학살", "무자비", "냉혹", "살육", "처형", "도살", "참수"}

    # [Phase 3-5A-2] 성격 급변 감지용 모순쌍
    _CONTRADICTORY_TRAIT_PAIRS = [
        ({"냉혹", "잔혹", "무자비", "냉정"}, {"온화", "자비", "인자", "따뜻"}),
        ({"겁쟁이", "소심", "비겁"}, {"용감", "대담", "무모"}),
        ({"충성", "헌신"}, {"배신", "배반"}),
    ]

    @staticmethod
    def _is_contradictory_trait_change(old: str, new: str) -> bool:
        """[Phase 3-5A-2] 냉혹↔온화, 겁쟁이↔용감 등 극단 반전 감지"""
        for group_a, group_b in ContinuityValidator._CONTRADICTORY_TRAIT_PAIRS:
            old_in_a = any(t in str(old) for t in group_a)
            old_in_b = any(t in str(old) for t in group_b)
            new_in_a = any(t in str(new) for t in group_a)
            new_in_b = any(t in str(new) for t in group_b)
            if (old_in_a and new_in_b) or (old_in_b and new_in_a):
                return True
        return False

    def _check_personality_continuity(self, manuscript: str, validation_context: dict) -> dict:
        """
        [V66.1] NPC 성격 모순 검증
        [Phase 3-5A-2] NPC 이력 기반 성격 급변 감지 추가

        냉혹한 NPC가 따뜻한 감정을 보이거나, 자비로운 NPC가 잔인한 행동을
        하는 경우를 감지. severity: MAJOR (BLOCKING은 아니지만 강한 WARNING).

        Args:
            manuscript: 현재 원고
            validation_context: {
                'npc_personalities': {NPC이름: {"traits": "냉혹한", "motivation": "복수"}},
                'npc_history': {NPC이름: [{"field_name": ..., "old_value": ..., "new_value": ...}, ...]}
            }

        Returns:
            {"passed": True/False, "violations": [...]}
        """
        npc_personalities = validation_context.get("npc_personalities", {})

        if not npc_personalities or not isinstance(npc_personalities, dict):
            return {"passed": True, "violations": []}

        violations = []
        # NPC 이름 근처 탐색 범위 (앞뒤 N자)
        proximity = _threshold("continuity.personality_proximity", 150)

        # [I-02] 성장/변화 키워드 — 근접 윈도우 내 존재 시 MAJOR → MINOR 다운그레이드
        _GROWTH_KEYWORDS = ("변했다", "달라졌다", "처음으로", "비로소", "깨달았다", "결심했다", "각성", "변화")

        for npc_name, personality_data in npc_personalities.items():
            if not npc_name or not isinstance(personality_data, dict):
                continue

            traits_str = str(personality_data.get("traits", ""))
            if not traits_str:
                continue

            # NPC가 원고에 등장하는지 확인
            if npc_name not in manuscript:
                continue

            # 모든 등장 위치 찾기
            npc_positions = []
            start = 0
            while True:
                idx = manuscript.find(npc_name, start)
                if idx == -1:
                    break
                npc_positions.append(idx)
                start = idx + 1

            # 냉혹 계열 NPC → 따뜻한 표현 모순 체크
            has_cold_trait = any(t in traits_str for t in self._COLD_TRAITS)
            if has_cold_trait:
                for pos in npc_positions:
                    context_start = max(0, pos - proximity)
                    context_end = min(len(manuscript), pos + len(npc_name) + proximity)
                    nearby_text = manuscript[context_start:context_end]

                    for contradiction in self._COLD_CONTRADICTIONS:
                        if contradiction in nearby_text:
                            # [I-02] 성장 컨텍스트 감지 → MINOR 다운그레이드
                            has_growth = any(gk in nearby_text for gk in _GROWTH_KEYWORDS)
                            severity = "MINOR" if has_growth else "MAJOR"
                            violations.append(
                                {
                                    "type": "personality_contradiction",
                                    "severity": severity,
                                    "npc": npc_name,
                                    "traits": traits_str,
                                    "contradiction": contradiction,
                                    "growth_context": has_growth,
                                    "reason": f"냉혹한 NPC '{npc_name}'(성격: {traits_str}) 근처에서 "
                                    f"모순 표현 '{contradiction}' 감지"
                                    + (" (성장 컨텍스트 감지)" if has_growth else ""),
                                    "context": nearby_text[:200],
                                    "fix_suggestion": f"'{npc_name}'의 성격({traits_str})에 맞게 "
                                    f"'{contradiction}' 표현을 수정하거나, "
                                    f"성격 변화의 계기를 명시하세요.",
                                }
                            )
                            break  # 한 위치에서 하나만 감지
                    if violations and violations[-1].get("npc") == npc_name:
                        break  # NPC당 하나만 보고

            # 자비 계열 NPC → 잔인한 표현 모순 체크
            has_kind_trait = any(t in traits_str for t in self._KIND_TRAITS)
            if has_kind_trait:
                for pos in npc_positions:
                    context_start = max(0, pos - proximity)
                    context_end = min(len(manuscript), pos + len(npc_name) + proximity)
                    nearby_text = manuscript[context_start:context_end]

                    for contradiction in self._KIND_CONTRADICTIONS:
                        if contradiction in nearby_text:
                            # [I-02] 성장 컨텍스트 감지 → MINOR 다운그레이드
                            has_growth = any(gk in nearby_text for gk in _GROWTH_KEYWORDS)
                            severity = "MINOR" if has_growth else "MAJOR"
                            violations.append(
                                {
                                    "type": "personality_contradiction",
                                    "severity": severity,
                                    "npc": npc_name,
                                    "traits": traits_str,
                                    "contradiction": contradiction,
                                    "growth_context": has_growth,
                                    "reason": f"온화한 NPC '{npc_name}'(성격: {traits_str}) 근처에서 "
                                    f"모순 표현 '{contradiction}' 감지"
                                    + (" (성장 컨텍스트 감지)" if has_growth else ""),
                                    "context": nearby_text[:200],
                                    "fix_suggestion": f"'{npc_name}'의 성격({traits_str})에 맞게 "
                                    f"'{contradiction}' 표현을 수정하거나, "
                                    f"성격 변화의 계기를 명시하세요.",
                                }
                            )
                            break
                    if violations and violations[-1].get("npc") == npc_name:
                        break

        # [Phase 3-5A-2] NPC 이력 기반 성격 급변 감지
        npc_history = validation_context.get("npc_history", {})
        if npc_history and isinstance(npc_history, dict):
            already_reported = {v.get("npc") for v in violations}
            for npc_name, history_entries in npc_history.items():
                if npc_name in already_reported:
                    continue
                if npc_name not in manuscript:
                    continue
                if not isinstance(history_entries, list):
                    continue
                # [G21] personality_traits 변경 이력 필터 — 최신 2개 비교
                personality_changes = [
                    h for h in history_entries if isinstance(h, dict) and h.get("field_name") == "personality_traits"
                ]

                def _safe_int(value) -> int:
                    try:
                        return int(value or 0)
                    except (TypeError, ValueError):
                        return 0

                personality_changes.sort(key=lambda h: (_safe_int(h.get("episode_no")), _safe_int(h.get("id"))))
                if len(personality_changes) >= 2:
                    prev = personality_changes[-2]  # 직전
                    curr = personality_changes[-1]  # 최신
                    old_val = prev.get("new_value", "")
                    new_val = curr.get("new_value", "")
                    if self._is_contradictory_trait_change(old_val, new_val):
                        violations.append(
                            {
                                "type": "personality_sudden_change",
                                "severity": "MAJOR",
                                "npc": npc_name,
                                "old_traits": old_val,
                                "new_traits": new_val,
                                "reason": f"NPC '{npc_name}' 성격 급변: {old_val} → {new_val}",
                                "fix_suggestion": "성격 변화의 계기를 서사에 명시하세요.",
                            }
                        )

        return {"passed": len(violations) == 0, "violations": violations}

    # ═══════════════════════════════════════════════════════════════════════
    # [V66.1] 시간 일관성 검증
    # ═══════════════════════════════════════════════════════════════════════

    def _check_time_consistency(self, manuscript: str, validation_context: dict) -> dict:
        """
        [V66.1] 시간 일관성 검증

        time_warnings(외부 시스템에서 전달)를 분석하여:
        - "중상"/"급속"/"불가능" 포함 시 → BLOCKING (passed=False)
        - 그 외 → WARNING

        Args:
            manuscript: 현재 원고 (미사용, 인터페이스 일관성 유지)
            validation_context: {
                'time_warnings': ["중상에서 급속 회복 - 불가능한 시간 경과", ...]
            }

        Returns:
            {"passed": True/False, "violations": [...], "warnings": [...]}
        """
        time_warnings = validation_context.get("time_warnings", [])

        if not time_warnings or not isinstance(time_warnings, list):
            return {"passed": True, "violations": [], "warnings": []}

        violations = []
        warnings = []

        severe_keywords = ["중상", "급속", "불가능"]

        for warning_item in time_warnings:
            # [V66.2] C-3: time_warnings dict/str 양쪽 처리
            if isinstance(warning_item, dict):
                warning_msg = warning_item.get("description", warning_item.get("message", str(warning_item)))
            elif isinstance(warning_item, str):
                warning_msg = warning_item
            else:
                continue

            is_severe = any(kw in warning_msg for kw in severe_keywords)

            if is_severe:
                violations.append(
                    {
                        "type": "time_inconsistency",
                        "severity": "BLOCKING",
                        "reason": f"시간 일관성 위반 (심각): {warning_msg}",
                        "fix_suggestion": "시간 경과를 현실적으로 조정하거나, "
                        "회복/이동에 필요한 시간 묘사를 추가하세요.",
                    }
                )
            else:
                warnings.append(
                    {
                        "type": "time_inconsistency",
                        "severity": "WARNING",
                        "reason": f"시간 일관성 경고: {warning_msg}",
                        "fix_suggestion": "시간 경과 묘사를 보완하세요.",
                    }
                )

        return {"passed": len(violations) == 0, "violations": violations, "warnings": warnings}

    # ── [D Step 4] 좌절-보상 타이머 (advisory) ──────────────────

    def check_frustration_streak(self, ep_num: int) -> list[str]:
        """최근 에피소드의 좌절 연속 화수를 검사한다.

        Rules:
        - 좌절 N화 연속 (default 3): WARNING "보상 에피소드 권장"
        - 좌절 M화 연속 (default 5): WARNING "대리만족 부재 심각"

        Returns:
            경고 메시지 리스트 (빈 리스트 = 정상)
        """
        db = getattr(self.context, "db", None) if self.context else None
        if not db or not hasattr(db, "get_recent_satisfaction_tags"):
            return []

        warn_threshold = _threshold("satisfaction.frustration_warning_streak", 3)
        crit_threshold = _threshold("satisfaction.frustration_critical_streak", 5)

        try:
            tags = db.get_recent_satisfaction_tags(before_ep=ep_num, lookback=crit_threshold)
        except Exception:
            return []

        if not tags:
            return []

        # 최신→과거 순으로 연속 좌절 카운트
        streak = 0
        for tag in reversed(tags):
            if tag.get("frustration_flag"):
                streak += 1
            else:
                break

        warnings = []
        if streak >= crit_threshold:
            warnings.append(
                f"[Satisfaction] 좌절 {streak}화 연속 — 대리만족 부재 심각. 다음 에피소드에 보상 장면 필수."
            )
        elif streak >= warn_threshold:
            warnings.append(f"[Satisfaction] 좌절 {streak}화 연속 — 보상 에피소드 권장.")
        return warnings
