"""[TF-45] Genre Schema Builder — 장르별 프롬프트 스키마 자동 생성.

Central Schema Builder: HUD get_critical_keys() 기반으로 장르별 프롬프트
스키마를 자동 생성한다. 무협(wuxia) 경로는 기존 하드코딩 텍스트를 100% 보존하고,
비무협 경로만 새 스키마를 동적 생성한다.

순수 Python 모듈 — LLM/DB 의존 없음.
"""


def is_wuxia(genre: str) -> bool:
    """장르가 무협(wuxia)인지 판별."""
    return genre in ("wuxia", "무협", "")


# ---------------------------------------------------------------------------
# Genre Labels (한국어)
# ---------------------------------------------------------------------------
_GENRE_LABELS: dict[str, str] = {
    "hunter": "헌터",
    "investment": "투자",
    "composer": "작곡가",
    "cooking": "요리",
    "alt_history": "대체역사",
    "actor": "배우",
    "sports": "스포츠",
    "medical": "의학",
    "fantasy": "판타지",
}


def get_genre_label(genre: str) -> str:
    """장르 한국어 라벨 반환. 무협이면 '무협'."""
    if is_wuxia(genre):
        return "무협"
    return _GENRE_LABELS.get(genre, genre)


# ---------------------------------------------------------------------------
# Item suffixes (SSOT)
# ---------------------------------------------------------------------------
_ITEM_SUFFIX_MAP: dict[str, list[str]] = {
    "_common": ["패", "권", "인장", "서", "부"],
    "wuxia": ["도", "검", "창", "봉", "궁", "갑", "환", "단", "경", "비급", "책", "도끼", "낫", "곤", "편"],
    "investment": [
        "통장",
        "계약서",
        "인감",
        "증명서",
        "면허",
        "허가증",
        "보고서",
        "카드",
        "워크스테이션",
        "노트북",
        "폰",
        "수표",
        "어음",
        "주권",
        "채권",
        "명함",
    ],
    "hunter": ["검", "도", "창", "활", "방패", "갑옷", "포션", "스크롤", "문장", "배지", "카드"],
    "fantasy": ["검", "도", "창", "지팡이", "로브", "반지", "목걸이", "오브", "스크롤", "포션", "열쇠"],
    "cooking": ["칼", "팬", "냄비", "도마", "레시피", "재료", "향신료", "식재료"],
    "medical": ["메스", "청진기", "차트", "처방전", "의료기", "약"],
    "sports": ["유니폼", "트로피", "메달", "배트", "글러브", "라켓", "공", "헬멧"],
    "actor": ["대본", "의상", "소품", "카메라", "마이크", "조명"],
    "alt_history": ["문서", "지도", "무기", "서신", "칙령", "조약"],
    "composer": ["악보", "악기", "바이올린", "피아노", "기타", "드럼", "마이크"],
}

_ITEM_GENRE_ALIASES: dict[str, str] = {
    "무협": "wuxia",
    "투자": "investment",
    "헌터": "hunter",
    "판타지": "fantasy",
    "요리": "cooking",
    "의학": "medical",
    "스포츠": "sports",
    "배우": "actor",
    "대체역사": "alt_history",
    "작곡가": "composer",
}


def _normalize_item_genre_key(genre: str) -> str:
    """아이템 접미사 조회용 장르 키 정규화."""
    if not genre:
        return ""
    key = str(genre).strip().lower().replace("-", "_").replace(" ", "_")
    if key in _ITEM_SUFFIX_MAP:
        return key
    return _ITEM_GENRE_ALIASES.get(str(genre).strip(), key)


def _load_suffix_data() -> dict[str, list[str]]:
    """YAML에서 접미사 데이터 로드. 실패 시 하드코딩 폴백."""
    from pathlib import Path

    import yaml

    yaml_path = Path(__file__).resolve().parents[2] / "config" / "settings" / "item_suffixes.yaml"
    if yaml_path.exists():
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "_common" in data:
                return data
        except Exception:
            pass
    return _ITEM_SUFFIX_MAP


def get_item_suffixes(genre: str = "") -> list[str]:
    """장르별 아이템 접미사 리스트 반환.

    YAML(config/settings/item_suffixes.yaml) 우선 로드, 실패 시 하드코딩 폴백.
    미지 장르(또는 빈 문자열)는 전체 장르 union을 반환한다.
    """
    data = _load_suffix_data()
    common = list(data.get("_common", []))
    genre_key = _normalize_item_genre_key(genre)
    specific = list(data.get(genre_key, [])) if genre_key else []

    if not specific:
        specific = []
        for key, values in data.items():
            if key == "_common":
                continue
            specific.extend(values)

    merged = common + specific
    unique: list[str] = []
    seen = set()
    for token in merged:
        item = str(token).strip()
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


# ---------------------------------------------------------------------------
# Field descriptions per (genre, key) — 비무협 전용
# ---------------------------------------------------------------------------
_GENRE_KEY_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "hunter": {
        "awakening_rank": "각성 등급 (예: F급, S급)",
        "mana": "마나 수치 (숫자)",
        "skills": "보유 스킬 목록 (배열)",
        "wealth": "현재 자산",
        "reputation": "명성/평판",
        "injuries": "부상 상태",
        "guild": "소속 길드",
        "level": "레벨 (숫자)",
    },
    "investment": {
        "capital": "현재 자본금 (숫자)",
        "total_assets": "총자산 (숫자)",
        "stocks": "보유 주식/포트폴리오 (배열)",
        "reputation": "시장 평판",
        "connections": "인맥/네트워크",
        "market_insight": "시장 통찰력",
        "status": "현재 상태",
    },
    "composer": {
        "composition": "작곡력 수치",
        "arrangement": "편곡력 수치",
        "production": "프로듀싱 역량",
        "reputation": "업계 명성",
        "wealth": "현재 자산",
        "mental_state": "정신 상태",
        "current_objective": "현재 목표",
    },
    "cooking": {
        "chef_rank": "셰프 등급",
        "signature_dish": "대표 요리",
        "culinary_techniques": "조리 기법 목록 (배열)",
        "restaurant_tier": "식당 등급",
        "reputation_score": "평판 점수 (숫자)",
        "capital": "운영 자금 (숫자)",
        "current_objective": "현재 목표",
    },
    "alt_history": {
        "social_class": "신분/계급",
        "court_rank": "품계/관품",
        "position": "관직/직위",
        "faction": "당파/붕당",
        "political_influence": "정치적 영향력",
        "wealth": "재산",
        "public_trust": "민심/공신력",
        "current_objective": "현재 목표",
    },
    "actor": {
        "acting_skill": "연기력 수치",
        "fame": "인지도/명성",
        "filmography": "출연작 목록 (배열)",
        "agency": "소속사",
        "fandom": "팬덤 규모",
        "scandal_index": "스캔들 지수 (숫자)",
        "box_office": "흥행 성적",
        "current_objective": "현재 목표",
    },
    "sports": {
        "athlete_tier": "선수 등급",
        "sport_type": "종목",
        "physical_stats": "신체 능력치",
        "record": "전적/기록",
        "team": "소속팀",
        "ranking": "랭킹/순위",
        "reputation": "명성",
        "current_objective": "현재 목표",
    },
    "medical": {
        "doctor_rank": "의사 직급",
        "specialty": "전공과",
        "hospital": "소속 병원",
        "surgery_count": "수술 횟수 (숫자)",
        "success_rate": "성공률 (숫자%)",
        "reputation": "명성",
        "current_objective": "현재 목표",
    },
    "fantasy": {
        "magic_tier": "마법 등급",
        "mana": "마나 수치 (숫자)",
        "spells": "주문 목록 (배열)",
        "race": "종족",
        "level": "레벨 (숫자)",
        "equipment": "장비 목록 (배열)",
        "wealth": "현재 자산",
        "injuries": "부상 상태",
        "reputation": "명성",
        "current_objective": "현재 목표",
    },
}

# NPC HUD 스키마 — 비무협 장르별
_GENRE_NPC_HUD_FIELDS: dict[str, dict[str, str]] = {
    "hunter": {
        "rank": "각성 등급",
        "main_skill": "주력 스킬",
        "level": "레벨",
        "current_status": "현재 상태(부상 등)",
        "equipment": "현재 소지 장비 목록 (배열)",
    },
    "investment": {
        "position": "직위/역할",
        "influence": "시장 영향력",
        "current_status": "현재 상태",
        "specialty": "전문 분야",
    },
    "composer": {
        "role": "업계 역할",
        "skill_level": "음악적 역량",
        "current_status": "현재 상태",
        "specialty": "전문 장르/악기",
    },
    "cooking": {
        "chef_rank": "셰프 등급",
        "specialty": "전문 요리",
        "current_status": "현재 상태",
        "restaurant": "소속 식당",
    },
    "alt_history": {
        "court_rank": "품계",
        "faction": "당파",
        "current_status": "현재 상태",
        "influence": "영향력",
    },
    "actor": {
        "fame_level": "인지도 등급",
        "role_type": "배역 유형",
        "current_status": "현재 상태",
        "agency": "소속사",
    },
    "sports": {
        "athlete_tier": "선수 등급",
        "position": "포지션",
        "current_status": "현재 상태(부상 등)",
        "team": "소속팀",
    },
    "medical": {
        "doctor_rank": "직급",
        "specialty": "전공과",
        "current_status": "현재 상태",
        "hospital": "소속 병원",
    },
    "fantasy": {
        "magic_tier": "마법 등급",
        "main_spell": "주력 마법",
        "level": "레벨",
        "current_status": "현재 상태(부상 등)",
        "equipment": "현재 소지 장비 목록 (배열)",
    },
}


def _get_descriptions(genre: str, critical_keys: list[str]) -> list[tuple[str, str]]:
    """(key, 한국어설명) 쌍 목록 반환."""
    descs = _GENRE_KEY_DESCRIPTIONS.get(genre, {})
    result = []
    for key in critical_keys:
        desc = descs.get(key, key)
        result.append((key, desc))
    return result


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------


def build_actual_truth_schema(genre: str, critical_keys: list[str]) -> str:
    """Manager용 actual_truth JSON 스키마 블록 생성 (비무협 전용)."""
    if is_wuxia(genre):
        return ""  # 무협은 기존 상수 사용
    pairs = _get_descriptions(genre, critical_keys)
    lines = ['      "actual_truth": {']
    for i, (key, desc) in enumerate(pairs):
        comma = "," if i < len(pairs) - 1 else ""
        lines.append(f'        "{key}": "{desc}"{comma}')
    # 공통 필드
    lines.append('        ,"current_objective": "현재 목표",')
    lines.append('        "equipment": ["현재 소지품 전체 목록을 배열로 기입"],')
    lines.append('        "reputation": "평판/명성",')
    lines.append('        "wealth": "현재 자산"')
    lines.append("      }")
    return "\n".join(lines)


def build_state_updates_schema(genre: str, critical_keys: list[str]) -> str:
    """ChiefWriter용 state_updates JSON 스키마 블록 생성."""
    if is_wuxia(genre):
        return (
            '      "state_updates": {{\n'
            '          "internal_energy": "현재 내공 % (0-100)",\n'
            '          "realm": "경지명 또는 현상 유지",\n'
            '          "causal_injuries": "부상 상태",\n'
            '          "wealth": "현재 총 자산",\n'
            '          "misunderstanding": 0-100,\n'
            '          "obsession": 0-100,\n'
            '          "equipment": ["소지품 목록"],\n'
            '          "martial_arts": ["무공 목록"]\n'
            "      }}"
        )
    pairs = _get_descriptions(genre, critical_keys)
    lines = ['      "state_updates": {{']
    for key, desc in pairs:
        lines.append(f'          "{key}": "{desc}",')
    lines.append('          "equipment": ["소지품 목록"]')
    lines.append("      }}")
    return "\n".join(lines)


def build_state_constraints_schema(genre: str, critical_keys: list[str]) -> str:
    """Ensemble용 state_constraints 내 에너지/상태 필드 (비무협은 장르별 키)."""
    if is_wuxia(genre):
        return '"internal_energy": 내공_퍼센트'
    # 비무협: 첫 번째 critical_key 중 수치형 필드 사용
    _numeric_candidates = [
        k
        for k in critical_keys
        if k
        in (
            "mana",
            "capital",
            "total_assets",
            "level",
            "surgery_count",
            "success_rate",
            "reputation_score",
            "magic_tier",
            "athlete_tier",
        )
    ]
    if _numeric_candidates:
        key = _numeric_candidates[0]
        desc = _GENRE_KEY_DESCRIPTIONS.get(genre, {}).get(key, key)
        return f'"{key}": "{desc}"'
    return '"status": "현재 상태"'


def build_status_shadow_schema(genre: str, critical_keys: list[str]) -> str:
    """Analyst/Ensemble용 status_shadow JSON 스키마 블록 생성."""
    if is_wuxia(genre):
        return (
            '      "status_shadow": {{\n'
            '          "internal_energy_loss": "예상 소모량(%)",\n'
            '          "expected_injuries": "부상 예상 부위 및 정도",\n'
            '          "item_consumption": ["사용한 소모성 아이템 목록"]\n'
            "      }}"
        )
    label = get_genre_label(genre)
    lines = ['      "status_shadow": {{']
    lines.append(f'          "key_stat_change": "{label} 핵심 수치 변동 요약",')
    lines.append('          "expected_injuries": "부상/상태 변화 예상 (정신적 피로는 일상 휴식으로 자연 회복 가능)",')
    lines.append('          "item_consumption": ["사용/소모된 아이템 목록"]')
    lines.append("      }}")
    return "\n".join(lines)


def build_npc_hud_schema(genre: str) -> str:
    """Manager용 NPC HUD JSON 스키마 블록 생성."""
    if is_wuxia(genre):
        return ""  # 무협은 기존 NPC_Martial_HUD 상수 사용
    fields = _GENRE_NPC_HUD_FIELDS.get(
        genre,
        {
            "role": "역할",
            "current_status": "현재 상태",
        },
    )
    label = get_genre_label(genre)
    lines = [f'        "NPC_{label}_HUD": {{{{']
    items = list(fields.items())
    for i, (key, desc) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        lines.append(f'          "{key}": "{desc}"{comma}')
    lines.append("        }}")
    return "\n".join(lines)


def build_manager_genre_instructions(genre: str, critical_keys: list[str]) -> str:
    """Manager 프롬프트용 장르별 지시문 (비무협 전용)."""
    if is_wuxia(genre):
        return ""  # 무협은 기존 상수 사용
    label = get_genre_label(genre)
    pairs = _get_descriptions(genre, critical_keys)
    key_list = ", ".join(f"{key}({desc})" for key, desc in pairs)
    return f"""1. **{label} 핵심 지표 정산**:
   - 이 장르의 핵심 추적 키: {key_list}
   - 변화가 있다면 반드시 `actual_truth` 내부에 반영하되, 수치형 데이터는 이전 상태를 계승하여 누적하라.
2. **로어 및 인과관계 기록**:
   - 신규 설정은 `new_lore`에, 사건의 인과는 `causal_links`에 담아라.
3. 원고에서 핵심 지표에 영향을 주는 사건이 등장했는데 HUD 수치를 갱신하지 않는 것은 치명적인 직무유기다.
4. 이전 상태(current_state_json)와 비교하여 1이라도 변화가 있다면 반드시 actual_truth의 수치를 수정하라.
5. 이 장르는 '내공(internal_energy)', '무공(martial_arts)', '경지(realm)', '진기성질(qi_nature)' 등 무협 전용 필드를 사용하지 않는다. 절대 생성하지 마라."""


def get_genre_role_title(genre: str) -> str:
    """Analyst 볼륨 전략가 역할명."""
    if is_wuxia(genre):
        return "무협 대서사 전략가"
    label = get_genre_label(genre)
    return f"{label} 대서사 전략가"
