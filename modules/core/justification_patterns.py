"""
[Phase 4.1] Justification Pattern Library
정당화 패턴 라이브러리 - Few-Shot Learning 방식으로 AI에게 창의적 정당화 영감 제공

패턴은 "감옥"이 아니라 "영감"
AI는 예시의 논리 구조를 이해하고 새로운 정당화를 무한히 생성할 수 있음
"""


JUSTIFICATION_PATTERNS = {
    "wuxia": {
        "weak_body_strong_action": {
            "description": "나약한 신체로 강력한 행동을 할 때의 정당화 패턴",
            "logic_structure": """
기본 논리: [제약 인정] → [특수 방법 활용] → [대가 명시] → [결과 달성]

핵심 원칙:
1. 제약을 무시하지 않고 정면으로 인정
2. 특수한 기술/지식/조건을 활용
3. 성공의 대가(고통, 위험, 부작용)를 반드시 명시
4. 일시적 성공임을 암시 (지속 불가능)
""",
            "examples": [
                {
                    "situation": "나약한 몸으로 100근 대도 들기",
                    "wrong_approach": "❌ 주인공이 100근 대도를 가볍게 들어올렸다.",
                    "wrong_reason": "제약 무시, 정당화 없음, HUD 모순",
                    "correct_approach": "✅ 전생에 체득한 발경법으로 팔목의 기혈을 순간 폭발시켰다. 뼈마디가 어긋나는 고통이 밀려왔지만, 녹슨 철괴는 지면에서 떨어졌다.",
                    "why_correct": "제약 인정(나약) + 방법(발경법) + 대가(뼈 고통) + 결과(들어올림) = 논리적 정당화",
                    "structure": "[제약 인정: 나약] → [방법: 발경법] → [대가: 뼈 고통] → [결과: 들어올림]"
                },
                {
                    "situation": "내공 고갈 상태에서 살기 방출",
                    "justification": "단전 밑바닥의 마지막 진기를 긁어모아 살기로 뒤틀었다. 입안에서 피 맛이 올라왔지만, 상대의 안색이 창백해지는 것이 보였다.",
                    "structure": "[제약 인정: 내공 고갈] → [방법: 잔여 진기 활용] → [대가: 내상] → [결과: 위압 성공]"
                },
                {
                    "situation": "부상 상태에서 고속 이동",
                    "justification": "찢어진 근육에서 비명이 울려왔지만, 전생에 익힌 경공의 원리로 체중을 분산시켰다. 오래 버틸 수는 없지만, 십여 장은 날 수 있었다.",
                    "structure": "[제약 인정: 부상] → [방법: 경공 원리] → [대가: 시간 제한] → [결과: 단거리 이동]"
                }
            ],
            "creation_guide": """
위 예시들의 '논리 구조'를 참고하여, 현재 상황에 맞는 새로운 정당화를 창의적으로 만드십시오.

필수 포함 요소:
- 제약 인정: "~한 상태였지만"
- 특수 방법: "~을 활용하여"
- 대가 명시: "~라는 고통/위험을 감수하고"
- 결과: "~을 이뤄냈다"

⚠️ 중요: 예시와 똑같은 표현을 쓰지 말고, 예시의 '논리 패턴'만 차용하여 새롭게 창조하십시오.
"""
        },
        "low_status_high_authority": {
            "description": "낮은 지위로 높은 권위를 행사할 때의 정당화 패턴",
            "logic_structure": """
기본 논리: [상황 모순 인정] → [숨겨진 근거 제시] → [상대의 약점/두려움 자극] → [권위 확보]

핵심 원칙:
1. 지위와 권위의 불일치를 독자도 인지하게 함
2. 상징물, 비밀 정보, 배후 세력 등 구체적 근거 제시
3. 상대가 복종할 수밖에 없는 이유 명시
4. 권위는 제한적이고 불안정함을 암시
""",
            "examples": [
                {
                    "situation": "망나니 소가주가 원로 장로들을 압박",
                    "justification": "철혈사자패를 탁자 위에 내려놓았다. 가주만이 쥘 수 있는 증표. 장로들의 안색이 흙빛으로 변했다. 패를 가진 자는 곧 가주를 대리하는 존재였다.",
                    "structure": "[모순: 망나니 vs 장로] → [근거: 사자패] → [효과: 두려움] → [권위 확보]"
                },
                {
                    "situation": "미천한 자가 고관에게 명령",
                    "justification": "품속에서 꺼낸 서찰에는 상서(尙書)의 사인(私印)이 찍혀 있었다. 고관의 얼굴이 창백해졌다. 이 서찰 하나면 그의 목숨은 물론 삼족이 멸할 수 있었다.",
                    "structure": "[모순: 미천 vs 고관] → [근거: 상서 서찰] → [약점: 목숨] → [권위 확보]"
                },
                {
                    "situation": "젊은 고수가 노장을 제압",
                    "justification": "검에서 뿜어져 나온 살기가 노장의 심장을 겨냥했다. 육십 년을 살아온 노장은 안다. 저 살기는 진짜다. 죽음이 두려워 무릎을 꿇었다.",
                    "structure": "[모순: 젊음 vs 노장] → [근거: 살기] → [두려움: 죽음] → [굴복]"
                }
            ],
            "creation_guide": """
현재 장면에서 지위와 권위가 불일치하는 상황을 정당화하십시오.

필수 포함 요소:
- 모순 인정: 독자도 "어?"라고 느낄 불일치 상황
- 구체적 근거: 증표, 서신, 능력, 비밀 정보 등
- 상대의 반응: 두려움, 당혹, 복종의 구체적 묘사
- 권위의 한계: 이 권위가 영원하지 않음을 암시

⚠️ 상대가 복종하는 '이유'가 명확해야 독자가 납득합니다.
"""
        },
        "sudden_power_increase": {
            "description": "갑작스러운 전력 상승의 정당화 패턴",
            "logic_structure": """
기본 논리: [축적된 빌드업] → [트리거 사건] → [돌파 과정] → [새로운 경지]

핵심 원칙:
1. '갑작스러움'이 아니라 '축적의 폭발'임을 강조
2. 명확한 트리거(깨달음, 위기, 각성)
3. 돌파의 고통과 위험 묘사
4. 완벽한 통제는 아직 불가능함을 암시
""",
            "examples": [
                {
                    "situation": "생사의 위기에서 경지 돌파",
                    "justification": "죽음의 문턱에서 전생의 수련과 현생의 고통이 하나로 엮였다. 역천벌체로 단련된 경맥이 폭발적으로 진기를 흡수하기 시작했다. 후천에서 선천으로, 오십 년 걸릴 길을 단 한순간에 뛰어넘었다. 하지만 몸은 이 힘을 감당하지 못하고 있었다.",
                    "structure": "[축적: 전생 수련 + 역천벌체] → [트리거: 생사 위기] → [돌파: 경지 상승] → [한계: 불완전]"
                },
                {
                    "situation": "은사의 유언으로 비기 각성",
                    "justification": "죽어가는 은사가 남긴 마지막 구결이 뇌리를 때렸다. 십 년간 이해하지 못했던 구결의 의미가 비로소 깨달아졌다. 단전이 뜨겁게 끓어오르며 새로운 심법이 각성되었다. 그러나 이 힘은 아직 제어할 수 없었다.",
                    "structure": "[축적: 십 년 수련] → [트리거: 은사 유언] → [깨달음: 심법 각성] → [한계: 미숙한 제어]"
                }
            ],
            "creation_guide": """
급격한 전력 상승을 설득력 있게 정당화하십시오.

필수 포함 요소:
- 빌드업: 이전부터 쌓여왔던 것(수련, 고통, 경험)
- 트리거: 명확한 계기(위기, 깨달음, 각성)
- 과정: 돌파의 순간을 구체적으로 묘사
- 불완전성: 완벽한 통제는 아직 안 됨을 명시

⚠️ "갑자기 강해졌다"가 아니라 "쌓인 것이 터졌다"로 표현하십시오.
"""
        }
    },
    "hunter": {
        "weak_body_strong_action": {
            "description": "각성 등급/마나가 부족한데 강력한 스킬 사용",
            "logic_structure": """
기본 논리: [제약 인정] → [오버로드/희생] → [대가 명시] → [결과 달성]

핵심 원칙:
1. 등급/마나 제한을 정면으로 인정
2. 생명력 소모, 스킬 강제 발동, 아이템 희생 등
3. 역류 피해, 기절, 능력 봉인 등 대가 명시
4. 재사용 불가능 또는 긴 쿨타임 암시
""",
            "examples": [
                {
                    "situation": "C급이 A급 스킬 강제 사용",
                    "justification": "생명력을 마나로 전환하는 금기 기술을 썼다. 마나회로가 불타는 고통이 온몸을 휩쓸었지만, A급 스킬 '뇌신강림'이 발동했다. 이 한 방으로 일주일은 누워있어야 할 것이다.",
                    "structure": "[제약: C급] → [방법: 생명력 전환] → [대가: 회로 손상] → [결과: A급 스킬]"
                },
                {
                    "situation": "마나 고갈 상태에서 방어",
                    "justification": "마나 대신 잠재력을 끌어올렸다. 각성 직후로 되돌아가는 역류가 일어날 수 있지만, 죽는 것보단 낫다. 방어막이 펼쳐졌고, 입에서 피가 쏟아졌다.",
                    "structure": "[제약: 마나 고갈] → [방법: 잠재력 소모] → [대가: 역류 위험] → [결과: 방어 성공]"
                }
            ],
            "creation_guide": """
능력치를 초과하는 행동을 정당화하십시오.

필수 포함 요소:
- 제약 인정: 현재 등급/마나의 명확한 한계
- 희생: 생명력, 잠재력, 아이템 등 무언가를 소모
- 구체적 대가: 역류, 기절, 능력 봉인, 회복 시간
- 일회성: 연속 사용 불가능

⚠️ 게임 시스템처럼 보이지 않게, 고통과 위험을 구체적으로 묘사하십시오.
"""
        },
        "low_rank_high_achievement": {
            "description": "낮은 등급으로 고등급 던전/몬스터 처리",
            "logic_structure": """
기본 논리: [불리함 인정] → [숨겨진 요소 활용] → [기술/전략 강조] → [간신히 성공]

핵심 원칙:
1. 등급 차이의 절대성 인정
2. 히든 스킬, 특수 아이템, 약점 공략 등
3. 힘이 아닌 지능/전략으로 승리
4. 압도적 승리가 아닌 간발의 차 강조
""",
            "examples": [
                {
                    "situation": "C급이 B급 보스 처치",
                    "justification": "정면 승부는 불가능했다. 하지만 게이트 내부의 환경을 이용했다. 천장의 종유석을 떨어뜨려 보스의 동선을 차단하고, 약점인 후방 관절을 집요하게 노렸다. 운이 좋았다. 단 한 번의 실수도 죽음이었을 것이다.",
                    "structure": "[불리: C급 vs B급] → [전략: 환경 이용] → [약점 공략] → [간발의 승리]"
                },
                {
                    "situation": "낮은 등급으로 높은 등급 파티 기여",
                    "justification": "화력은 낮지만, 숨겨진 패시브 '위험 감지'가 발동했다. 함정을 미리 발견해 파티를 구했다. 등급이 전부가 아니라는 것을 증명했다.",
                    "structure": "[불리: 낮은 등급] → [숨김: 특수 능력] → [기여] → [인정]"
                }
            ],
            "creation_guide": """
등급을 초월한 성취를 정당화하십시오.

필수 포함 요소:
- 불리함 인정: 등급 차이는 절대적
- 특수 요소: 숨겨진 능력, 아이템, 지식
- 지능 강조: 힘이 아닌 머리로 승리
- 운의 요소: 완벽한 승리가 아닌 간발의 차

⚠️ 등급 시스템을 무시하면 안 됩니다. 특수한 조건이 있었음을 강조하십시오.
"""
        }
    },
    "investment": {
        "weak_capital_high_return": {
            "description": "적은 자본으로 큰 수익 달성",
            "logic_structure": """
기본 논리: [제약 인정] → [정보 우위 활용] → [위험 감수] → [성공과 한계]

핵심 원칙:
1. 자본의 한계를 명확히 인정
2. 회귀 지식, 내부 정보, 시장 통찰 활용
3. 도박에 가까운 레버리지, 올인 등 위험 명시
4. 재현 불가능, 운이 좋았음을 암시
""",
            "examples": [
                {
                    "situation": "1000만원으로 1억 달성",
                    "justification": "전생에서 이 종목이 3개월 뒤 10배 폭등한다는 것을 알고 있었다. 신용 레버리지를 최대로 끌어올렸다. 청산당하면 빚더미였지만, 회귀자의 지식이 정확했다. 하지만 이런 기회는 두 번 없다.",
                    "structure": "[제약: 1000만] → [정보: 회귀 지식] → [위험: 레버리지] → [성공: 1억, 한계: 재현 불가]"
                },
                {
                    "situation": "무명 투자자가 대어 잡기",
                    "justification": "아무도 모르는 이 회사의 기술이 시장을 바꿀 것을 알았다. 전재산을 걸었다. 2년간 수익 없이 버텼고, 결국 상장 후 100배 수익을 냈다. 이런 집중 투자는 자살 행위에 가깝지만, 미래를 아는 회귀자에겐 가능했다.",
                    "structure": "[제약: 무명] → [정보: 미래 지식] → [위험: 올인] → [성공: 100배, 경고: 위험]"
                }
            ],
            "creation_guide": """
비현실적 수익률을 정당화하십시오.

필수 포함 요소:
- 자본 제약: 적은 돈으로 시작
- 정보 우위: 회귀, 내부자, 통찰력
- 위험 명시: 레버리지, 올인, 청산 위험
- 재현 불가: 이런 기회는 다시 없음

⚠️ 투자 판타지를 쓰되, 현실성을 완전히 무시하면 안 됩니다. 독자가 "이건 회귀니까 가능하구나"라고 납득해야 합니다.
"""
        }
    }
}


def get_justification_guide(genre: str, situation_type: str) -> str:
    """
    정당화 가이드 생성 (Few-Shot Learning 방식)

    Args:
        genre: 장르 ('wuxia', 'hunter', 'investment')
        situation_type: 상황 타입 ('weak_body_strong_action', 'low_status_high_authority', 등)

    Returns:
        str: AI에게 전달할 정당화 가이드 (예시 + 창작 지침)
    """
    pattern = JUSTIFICATION_PATTERNS.get(genre, {}).get(situation_type, {})

    if not pattern:
        return ""

    guide_parts = [
        f"📘 [정당화 가이드 - Phase 5 Contrastive CoT]\n",
        f"상황 유형: {pattern['description']}\n",
        f"\n논리 구조:\n{pattern['logic_structure']}\n",
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        f"대조적 예시 (Contrastive Learning)\n",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ]

    for i, example in enumerate(pattern['examples'], 1):
        guide_parts.append(f"\n[예시 {i}] {example['situation']}\n")

        # [Phase 5.1.3] Contrastive Examples
        if 'wrong_approach' in example:
            guide_parts.append(f"\n{example['wrong_approach']}")
            guide_parts.append(f"문제: {example.get('wrong_reason', '정당화 없음')}\n")

        if 'correct_approach' in example:
            guide_parts.append(f"\n{example['correct_approach']}")
            guide_parts.append(f"이유: {example.get('why_correct', '논리적 정당화')}\n")
        else:
            # 기존 형식 (backward compatibility)
            guide_parts.append(f"→ \"{example['justification']}\"")
            guide_parts.append(f"→ 구조: {example['structure']}\n")

    guide_parts.append(f"\n{pattern['creation_guide']}\n")
    guide_parts.append(
        f"\n🎯 당신의 임무: 위 '잘못된 예시'와 '올바른 예시'의 차이를 명확히 이해하고,\n"
        f"현재 장면에 맞는 완전히 새로운 정당화를 창작하십시오.\n"
        f"\n⚠️ 중요: 올바른 예시처럼 [제약 인정 → 방법 → 대가 → 결과] 구조를 반드시 포함하십시오.\n"
    )

    return "".join(guide_parts)


def get_available_patterns(genre: str) -> list:
    """
    특정 장르에서 사용 가능한 패턴 목록 반환

    Args:
        genre: 장르

    Returns:
        list: 패턴 타입 목록
    """
    return list(JUSTIFICATION_PATTERNS.get(genre, {}).keys())


def get_pattern_description(genre: str, situation_type: str) -> str:
    """
    패턴 설명만 간단히 반환 (Validator 제안용)

    Args:
        genre: 장르
        situation_type: 상황 타입

    Returns:
        str: 패턴 설명
    """
    pattern = JUSTIFICATION_PATTERNS.get(genre, {}).get(situation_type, {})
    return pattern.get('description', '')
