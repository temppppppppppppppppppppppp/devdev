"""
[V60.12] Negative Example Injector
실패 사례 기반 Few-Shot 학습 - "하지 말아야 할 것" 명시

목적:
- 과거 REJECT 사례를 분석하여 동일 실수 방지
- Contrastive Learning으로 LLM이 경계해야 할 패턴 학습
- 초기 통과율 극대화

비용: $0 (프롬프트 주입만)
"""

import threading

# [V60.74] 스레드 안전성을 위한 Lock
_rejection_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════
# 장르 공통 실패 사례 (4 카테고리 — 장르 무관)
# ═══════════════════════════════════════════════════════════════
_COMMON_EXAMPLES = {
    "duplicate_acquisition": {
        "description": "이미 획득한 아이템 재획득",
        "bad_examples": [
            {
                "context": "Arc 1에서 핵심 아이템을 획득한 상태",
                "mistake": "Arc 2의 protagonist_items(legacy alias: items_acquired)에 동일 아이템 포함",
                "why_wrong": "이미 획득한 아이템을 다시 획득할 수 없음",
                "correct": "protagonist_items에서 기존 아이템 제외. arc_end_state.equipment는 종료 시 전체 소지품 기준으로 유지",
            },
            {
                "context": "Arc 2에서 특별한 지위/칭호를 수여받은 상태",
                "mistake": "Arc 3에서 동일 지위/칭호를 다시 수여받는 장면",
                "why_wrong": "이미 수여받은 것을 다시 수여받을 수 없음",
                "correct": "기존 지위를 '활용'하는 장면으로 변경",
            },
        ],
    },
    "location_teleport": {
        "description": "위치 순간이동",
        "bad_examples": [
            {
                "context": "Arc 1 종료 시 A 지역에 있음",
                "mistake": "Arc 2 시작 위치가 전혀 다른 B 지역",
                "why_wrong": "이전 Arc 종료 위치에서 시작해야 함",
                "correct": "arc_start_state.location = 이전 종료 위치로 시작, 이동 장면 포함",
            }
        ],
    },
    "joint_docs_mismatch": {
        "description": "joint_docs와 tactical_doc 불일치",
        "bad_examples": [
            {
                "context": "tactical_doc 마지막 화에서 새 지역으로 이동",
                "mistake": "joint_docs.final_location이 이전 위치 그대로",
                "why_wrong": "joint_docs는 tactical_doc 마지막 상태를 정확히 반영해야 함",
                "correct": "joint_docs.final_location = tactical_doc 마지막 위치",
            },
            {
                "context": "tactical_doc에서 소모품 사용",
                "mistake": "joint_docs.physical_inventory에 여전히 소모품 포함",
                "why_wrong": "소모된 아이템은 소지품에서 제외",
                "correct": "physical_inventory에서 소모품 제거, items_consumed에 추가",
            },
        ],
    },
    "tactical_doc_quality": {
        "description": "tactical_doc 품질 문제",
        "bad_examples": [
            {
                "context": "Arc tactical_doc 작성",
                "mistake": "1500자 분량의 간략한 요약만 작성",
                "why_wrong": "tactical_doc은 최소 3000자 이상의 상세 시나리오 필요",
                "correct": "각 화별 800자 이상, 총 4000자 이상의 구체적 장면 묘사",
            },
            {
                "context": "5개 화 구성 Arc",
                "mistake": "화 구분 없이 하나의 흐름으로 작성",
                "why_wrong": "'제 N화' 형식으로 명확히 구분 필요",
                "correct": "'제 1화: ...', '제 2화: ...' 형식으로 5개 화 명확 구분",
            },
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# 장르별 오버라이드 (state_discontinuity + power_inflation)
# ═══════════════════════════════════════════════════════════════
_GENRE_OVERRIDES = {
    "wuxia": {
        "state_discontinuity": {
            "description": "상태 불연속 (무협)",
            "bad_examples": [
                {
                    "context": "Arc 1 종료 시 왼팔 중상, 내공 60%",
                    "mistake": "Arc 2 시작에서 부상 언급 없이 정상 활동",
                    "why_wrong": "중상은 회복 과정 없이 사라지지 않음",
                    "correct": "Arc 2 초반에 치료 장면 포함 또는 부상 상태로 행동 제한",
                },
                {
                    "context": "Arc 2에서 내공 30% 손실",
                    "mistake": "Arc 3 시작에서 내공 100%",
                    "why_wrong": "내공은 수련/회복 과정 없이 회복되지 않음",
                    "correct": "Arc 3 초반 내공 회복 수련 장면 포함",
                },
            ],
        },
        "power_inflation": {
            "description": "파워 인플레이션 (무협)",
            "bad_examples": [
                {
                    "context": "주인공 삼류 수준에서 시작",
                    "mistake": "Arc 1에서 바로 일류 경지 도달",
                    "why_wrong": "한 Arc에서 2단계 이상 성장은 비현실적",
                    "correct": "Arc 1: 삼류→이류, Arc 2: 이류→일류 점진적 성장",
                }
            ],
        },
    },
    "hunter": {
        "state_discontinuity": {
            "description": "상태 불연속 (헌터)",
            "bad_examples": [
                {
                    "context": "Arc 1 종료 시 마나 30%, HP 위험",
                    "mistake": "Arc 2 시작에서 마나/HP 만충 상태",
                    "why_wrong": "던전 귀환 후 회복 시간이 필요함",
                    "correct": "Arc 2 초반에 회복/치료 장면 포함",
                },
                {
                    "context": "각성 스킬 사용 후 반동",
                    "mistake": "다음 Arc에서 반동 언급 없이 정상 활동",
                    "why_wrong": "각성 반동은 회복 없이 사라지지 않음",
                    "correct": "반동 회복 과정 또는 행동 제한 묘사",
                },
            ],
        },
        "power_inflation": {
            "description": "파워 인플레이션 (헌터)",
            "bad_examples": [
                {
                    "context": "주인공 E등급 헌터",
                    "mistake": "Arc 1에서 바로 S등급 도달",
                    "why_wrong": "한 Arc에서 3등급 이상 점프는 비현실적",
                    "correct": "Arc 1: E→D, Arc 2: D→C 점진적 각성",
                }
            ],
        },
    },
    "investment": {
        "state_discontinuity": {
            "description": "상태 불연속 (투자)",
            "bad_examples": [
                {
                    "context": "Arc 1 종료 시 자금 30% 손실, 신용등급 하락",
                    "mistake": "Arc 2 시작에서 자금 완전 회복",
                    "why_wrong": "투자 손실은 회수 과정 없이 복원되지 않음",
                    "correct": "Arc 2 초반에 자금 조달/회수 과정 포함",
                },
                {
                    "context": "주인공이 특정 종목에 올인한 상태",
                    "mistake": "다음 Arc에서 해당 포지션 언급 없음",
                    "why_wrong": "미청산 포지션은 자동으로 사라지지 않음",
                    "correct": "기존 포지션 정리 또는 유지 상태 명시",
                },
            ],
        },
        "power_inflation": {
            "description": "파워 인플레이션 (투자)",
            "bad_examples": [
                {
                    "context": "주인공 초기 자금 1000만원",
                    "mistake": "Arc 1에서 바로 100억 달성",
                    "why_wrong": "한 Arc에서 1000배 수익은 비현실적",
                    "correct": "Arc 1: 1000만→5000만, Arc 2: 5000만→2억 단계적 성장",
                }
            ],
        },
    },
    "fantasy": {
        "state_discontinuity": {
            "description": "상태 불연속 (판타지)",
            "bad_examples": [
                {
                    "context": "Arc 1 종료 시 마나 고갈, 축복 소진",
                    "mistake": "Arc 2 시작에서 마나/축복 완전 회복",
                    "why_wrong": "마나 고갈과 축복 소진은 회복 과정 필요",
                    "correct": "Arc 2 초반에 명상/기도/휴식 회복 장면 포함",
                },
                {
                    "context": "Arc 2에서 HP 위험, 저주 상태",
                    "mistake": "Arc 3 시작에서 저주 언급 없이 정상 상태",
                    "why_wrong": "저주는 해제 과정 없이 사라지지 않음",
                    "correct": "저주 해제 퀘스트 또는 상태이상 유지 묘사",
                },
            ],
        },
        "power_inflation": {
            "description": "파워 인플레이션 (판타지)",
            "bad_examples": [
                {
                    "context": "주인공 1레벨 견습 마법사",
                    "mistake": "Arc 1에서 바로 대마법사 도달",
                    "why_wrong": "한 Arc에서 급격한 레벨업은 비현실적",
                    "correct": "Arc 1: 견습→초급, Arc 2: 초급→중급 점진적 성장",
                }
            ],
        },
    },
    "_default": {
        "state_discontinuity": {
            "description": "상태 불연속",
            "bad_examples": [
                {
                    "context": "Arc 종료 시 주인공이 불리한 상태",
                    "mistake": "다음 Arc 시작에서 불리한 상태 언급 없이 정상 활동",
                    "why_wrong": "이전 Arc의 결과는 다음 Arc에 자연스럽게 이어져야 함",
                    "correct": "다음 Arc 초반에 회복/해결 과정 포함",
                },
            ],
        },
        "power_inflation": {
            "description": "파워 인플레이션",
            "bad_examples": [
                {
                    "context": "주인공이 초보 수준에서 시작",
                    "mistake": "한 Arc에서 최고 수준에 도달",
                    "why_wrong": "급격한 성장은 독자의 몰입을 깨뜨림",
                    "correct": "Arc별 한 단계씩 점진적 성장",
                }
            ],
        },
    },
}


class NegativeExampleInjector:
    """
    [V60.12] Negative Example Injector

    실패 사례 기반 프롬프트 강화
    """

    def __init__(self, genre: str = "wuxia"):
        self.genre = genre
        self.examples_library = self._load_examples_library(genre)
        self.rejection_history: list[dict] = []

    def _load_examples_library(self, genre: str) -> dict:
        """장르별 실패 사례 라이브러리 로드 — COMMON + genre override merge"""
        overrides = _GENRE_OVERRIDES.get(genre, _GENRE_OVERRIDES["_default"])
        return {**_COMMON_EXAMPLES, **overrides}

    def record_rejection(self, arc: dict, rejection_reason: str, category: str):
        """REJECT 사례 기록 - [V60.74] 스레드 안전"""
        state_constraints = arc.get("state_constraints", {})
        protagonist_items = state_constraints.get("protagonist_items")
        if protagonist_items is None:
            protagonist_items = state_constraints.get("items_acquired", [])
        with _rejection_lock:
            self.rejection_history.append(
                {
                    "arc_no": arc.get("arc_no", "?"),
                    "reason": rejection_reason,
                    "category": category,
                    "protagonist_items": protagonist_items,
                    "items_acquired": state_constraints.get("items_acquired", []),
                    "grants_received": state_constraints.get("grants_received", []),
                    "timestamp": "now",
                }
            )

            # 최근 20개만 유지
            if len(self.rejection_history) > 20:
                self.rejection_history = self.rejection_history[-20:]

    def generate_injection(self, context: dict = None) -> str:
        """Analyst 프롬프트에 주입할 실패 사례 텍스트 생성"""
        lines = [
            "",
            "\u2554" + "\u2550" * 70 + "\u2557",
            "\u2551"
            + " [V60.12 NEGATIVE EXAMPLES - \uc808\ub300 \ud558\uc9c0 \ub9d0\uc544\uc57c \ud560 \uac83] ".center(70)
            + "\u2551",
            "\u255a" + "\u2550" * 70 + "\u255d",
            "",
            "\ub2e4\uc74c\uc740 \uacfc\uac70\uc5d0 REJECT\ub41c \uc2e4\ud328 \uc0ac\ub840\uc785\ub2c8\ub2e4.",
            "\ub3d9\uc77c\ud55c \uc2e4\uc218\ub97c \ubc18\ubcf5\ud558\uc9c0 \ub9c8\uc138\uc694!",
            "",
        ]

        # [TF-S2-05] 최근 REJECT 히스토리 스냅샷 (스레드 안전)
        with _rejection_lock:
            _history_snapshot = list(self.rejection_history[-5:])

        if _history_snapshot:
            lines.append("\u2501\u2501\u2501 \ucd5c\uadfc REJECT \uc0ac\ub840 \u2501\u2501\u2501")
            for rej in _history_snapshot:
                lines.append(f"\u274c Arc {rej['arc_no']}: {rej['reason']}")
            lines.append("")

        # 기본 실패 사례 라이브러리
        lines.append("\u2501\u2501\u2501 \uc77c\ubc18\uc801\uc778 \uc2e4\ud328 \ud328\ud134 \u2501\u2501\u2501")
        lines.append("")

        # 상황에 맞는 사례 선택
        relevant_categories = self._select_relevant_categories(context)

        for category in relevant_categories[:4]:  # 최대 4개 카테고리
            cat_data = self.examples_library.get(category, {})
            if not cat_data:
                continue

            lines.append(f"\u25b6 {cat_data.get('description', category)}")
            lines.append("")

            for ex in cat_data.get("bad_examples", [])[:2]:  # 카테고리당 최대 2개
                lines.append(f"  \uc0c1\ud669: {ex.get('context', '')}")
                lines.append(f"  \u274c \uc798\ubabb\ub41c \uc608: {ex.get('mistake', '')}")
                lines.append(f"  \u2192 \uc65c \ud2c0\ub838\ub098: {ex.get('why_wrong', '')}")
                lines.append(f"  \u2705 \uc62c\ubc14\ub978 \uc608: {ex.get('correct', '')}")
                lines.append("")

        # 최종 경고
        lines.append("\u2501" * 60)
        lines.append(
            "\u26a0\ufe0f \uc704 \uc2e4\ud328 \uc0ac\ub840\ub97c \uc808\ub300 \ubc18\ubcf5\ud558\uc9c0 \ub9c8\uc138\uc694!"
        )
        lines.append(
            "\u26a0\ufe0f \ud2b9\ud788 '\uc774\ubbf8 \ud68d\ub4dd\ud55c \uc544\uc774\ud15c \uc7ac\ud68d\ub4dd'\uc740 \uc989\uc2dc REJECT\ub429\ub2c8\ub2e4!"
        )
        lines.append("")

        return "\n".join(lines)

    def _select_relevant_categories(self, context: dict = None) -> list[str]:
        """상황에 맞는 카테고리 선택"""
        # 기본 우선순위
        priority = [
            "duplicate_acquisition",
            "location_teleport",
            "state_discontinuity",
            "joint_docs_mismatch",
            "tactical_doc_quality",
            "power_inflation",
        ]

        # [TF-S2-05] 최근 REJECT 히스토리 스냅샷 (스레드 안전)
        with _rejection_lock:
            recent_categories = [r.get("category") for r in self.rejection_history[-5:]]
        for cat in recent_categories:
            if cat in priority:
                priority.remove(cat)
                priority.insert(0, cat)  # 최근 실패한 카테고리 우선

        return priority

    def generate_self_check_prompt(self) -> str:
        """생성 후 자가 검증 프롬프트"""
        return """
### [V60.12 자가 검증 체크리스트 - 제출 전 필수 확인]

다음 항목을 모두 확인하고 "예"로 답할 수 있어야 합니다:

□ protagonist_items(legacy alias: items_acquired)에 이전 Arc에서 이미 획득한 아이템이 없는가?
□ grants_received에 이전 Arc에서 이미 수여받은 것이 없는가?
□ arc_start_state.location이 이전 Arc의 final_location과 일치하는가?
□ 이전 Arc의 불리한 상태(부상/자원 손실 등)가 적절히 계승되었는가?
□ tactical_doc이 3000자 이상인가?
□ tactical_doc에 '제 N화' 형식으로 화가 구분되어 있는가?
□ joint_docs.final_location이 tactical_doc 마지막 화 종료 위치와 일치하는가?
□ joint_docs.physical_inventory에 소모된 아이템이 제외되어 있는가?

위 항목 중 하나라도 "아니오"면 수정 후 제출하세요!
"""

    def get_targeted_warning(self, issue_type: str) -> str:
        """특정 이슈에 대한 타겟 경고 생성"""
        warnings = {
            "duplicate_acquisition": """
⚠️ [중복 획득 경고]
이전 Arc에서 이미 획득한 아이템을 다시 획득하려 합니다!
→ protagonist_items(legacy alias: items_acquired) 목록에서 해당 아이템을 제거하세요.
→ 대신 '새로운' 아이템을 획득하거나, 기존 아이템을 '활용'하는 장면으로 변경하세요.
""",
            "location_mismatch": """
⚠️ [위치 불일치 경고]
Arc 시작 위치가 이전 Arc 종료 위치와 다릅니다!
→ arc_start_state.location을 이전 Arc의 final_location과 동일하게 수정하세요.
→ 위치 이동이 필요하면 Arc 초반에 이동 장면을 포함하세요.
""",
            "state_discontinuity": """
⚠️ [상태 불연속 경고]
이전 Arc의 상태가 무시되었습니다!
→ 부상/자원 손실이 있었다면 회복 과정을 포함하거나 상태 제한을 적용하세요.
→ 이전 Arc 종료 상태를 자연스럽게 이어가세요.
""",
            "joint_docs_mismatch": """
⚠️ [Joint Docs 불일치 경고]
joint_docs가 tactical_doc 내용과 일치하지 않습니다!
→ final_location을 tactical_doc 마지막 화 종료 위치로 수정하세요.
→ physical_inventory를 정확히 업데이트하세요.
""",
        }
        return warnings.get(issue_type, "⚠️ 제약 조건을 다시 확인하세요.")


def create_negative_example_injector(genre: str = "wuxia") -> NegativeExampleInjector:
    """NegativeExampleInjector 생성 헬퍼"""
    return NegativeExampleInjector(genre)
