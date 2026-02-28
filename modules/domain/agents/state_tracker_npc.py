"""
[V64.P3] StateTracker NPC Sub-module
NPC 레지스트리 관리, 사망 추적, 무공/스킬 추적, 관계 변화, 부상/이동 추적.
[V66.1] F-3 regex 폴백 확충 + F-8 영구 부상 추적 + F-10 사망 등록 취소.

StateTracker에서 NPC 관련 메서드만 분리.
모든 공유 상태는 self.tracker를 통해 접근.
"""

import json
import logging
import re
import time

# ═══════════════════════════════════════════════════════════════
# [V66.1] C-2: Module-level compiled regex patterns
#  메서드 내부 re.compile 호출을 모듈 상수로 이동 (~25ms/Arc 절감)
# ═══════════════════════════════════════════════════════════════

# --- _regex_extract_relationship_changes ---
_RE_REL_ARROW = re.compile(
    r"([가-힣]{2,10})[이가은는의]\s*(?:관계)?\s*(?:가\s*)?"
    r"(적대?|중립|아군|동맹|호의|충성|적)[에서으로]*\s*[→에서]+\s*"
    r"(적대?|중립|아군|동맹|호의|충성|적)"
)
_RE_REL_RECONCILE = re.compile(r"([가-힣]{2,10})[와과]\s*(?:화해|동맹|협력)")
_RE_REL_BETRAY = re.compile(r"([가-힣]{2,10})[이가에][게의]?\s*(?:배신|배반|뒤통수)")

# --- _regex_extract_npc_injuries ---
_RE_INJURY_DIRECT = re.compile(r"([가-힣]{2,10})[이가은는]\s*(중상|경상|위독|부상)[을를에]?\s*(?:입|당)")
_RE_INJURY_BODY = re.compile(r"([가-힣]{2,10})[의]\s*(?:팔|다리|눈|몸)[이가]\s*(?:잘리|부러|찢어|관통)")
_RE_INJURY_REVERSE = re.compile(r"(중상|위독)[을를에]?\s*(?:입[은힌]|당[한])\s*([가-힣]{2,10})")

# --- _regex_extract_npc_movements ---
_RE_MOVE_FROM_TO = re.compile(
    r"([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10})[에서을를]\s*"
    r"(?:떠나|출발).{0,20}?([가-힣]{2,10})[으로에]\s*(?:이동|향|도착|떠나)"
)
_RE_MOVE_TO = re.compile(r"([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10})[으로에]\s*(?:이동|향|도착|떠나)")
_RE_MOVE_LEAVE = re.compile(r"([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10})[을를]\s*(?:떠나|탈출|벗어나)")

# --- _regex_extract_companion_changes ---
_RE_COMP_JOIN = [
    re.compile(r"([가-힣]{2,10})[이가은는]\s*(?:합류|동행|일행에\s*가담|함께\s*(?:가|떠나|동행))"),
    re.compile(r"([가-힣]{2,10})[와과]\s*(?:동행|합류|함께)"),
    re.compile(r"([가-힣]{2,10})[을를]\s*(?:일행에\s*받아들|동료로\s*받아들|데리고)"),
]
_RE_COMP_LEAVE = [
    re.compile(r"([가-힣]{2,10})[이가은는]\s*(?:떠나|이탈|일행에서\s*빠지|헤어지|작별|결별)"),
    re.compile(r"([가-힣]{2,10})[와과]\s*(?:헤어지|작별|이별)"),
    re.compile(r"([가-힣]{2,10})[이가은는]\s*(?:홀로|혼자)\s*(?:떠나|길을\s*가)"),
]

# --- extract_permanent_injuries_from_arc ---
_RE_PERM_AMPUTATION = [
    re.compile(
        r"([가-힣]{2,10})[의]\s*(왼팔|오른팔|왼쪽\s*팔|오른쪽\s*팔|팔|왼다리|오른다리|다리)[이가을를]\s*(?:잘리|절단|끊어|잃)"
    ),
    re.compile(r"([가-힣]{2,10})[이가은는]\s*(팔|다리|손|손가락|발)[을를]?\s*(?:잃|잘리|절단)"),
]
_RE_PERM_BLINDNESS = [
    re.compile(r"([가-힣]{2,10})[의]\s*(왼쪽\s*)?눈[이가을를]\s*(?:멀|잃|찔리|관통)"),
    re.compile(r"([가-힣]{2,10})[이가은는]\s*(?:실명|눈을\s*잃)"),
]
_RE_PERM_SCAR = [
    re.compile(r"([가-힣]{2,10})[의에]\s*(?:얼굴|등|가슴|몸)[에]?\s*(?:큰\s*)?(?:흉터|상처자국|화상)"),
]


# ═══════════════════════════════════════════════════════════════
# NPC 사망 추출 시 제외할 일반 명사 (고유명사 오탐 방지)
# ═══════════════════════════════════════════════════════════════
_NPC_DEATH_EXCLUDE_WORDS = frozenset(
    [
        # 기존 exclude_words
        "주인공",
        "적",
        "상대",
        "자신",
        "목숨",
        "생명",
        "원수",
        "원한",
        "일격",
        "공격",
        "반격",
        # 관용 표현 오탐 방지 ("세상을 떠나다", "인생이 끝나다" 등)
        "세상",
        "세계",
        "인생",
        "시간",
        "사람",
        "인간",
        "모든",
        "누군가",
        "그녀",
        "그것",
        "소문",
        "소식",
        "이야기",
        "사건",
        "사태",
        "상황",
        "현실",
        "미래",
        "과거",
        # 추상 명사 / 비고유명사
        "조직",
        "세력",
        "집단",
        "단체",
        "국가",
        "나라",
        "도시",
        "마을",
        "회사",
        "기업",
        "시장",
        "경제",
        "투자",
        "금융",
        "주식",
        "자본",
        "이름",
        "칭호",
        "부상",
        "전투",
        "데이터",
        "후원자",
        "몬스터",
        "적들",
        "그들",
        "아군",
        "동맹",
        "원래",
    ]
)


class StateTrackerNPC:
    """[V64.P3] NPC 관련 메서드 서브모듈"""

    # [V61.7.1] 장르별 능력 습득 로그 표시
    _SKILL_LOG_LABEL = {
        "wuxia": ("\U0001f94b", "무공 습득"),
        "hunter": ("\u2694\ufe0f", "스킬 습득"),
        "investment": ("\U0001f4c8", "핵심 지식 등록"),
        "fantasy": ("\u2728", "마법 습득"),
        "composer": ("\U0001f3b5", "작곡 기법 습득"),
        "cooking": ("\U0001f468\u200d\U0001f373", "조리법 습득"),
        "alt_history": ("\U0001f4dc", "국정 역량 습득"),
        "actor": ("\U0001f3ac", "연기 습득"),
        "sports": ("\U0001f3c5", "기술 습득"),
        "medical": ("\U0001f52c", "의술 습득"),
    }

    def __init__(self, tracker) -> None:
        self.tracker = tracker  # back-reference to main StateTracker

    # ═══════════════════════════════════════════════════════════════
    # [Phase 3-5A] NPC 변경 이력 기록 헬퍼
    # ═══════════════════════════════════════════════════════════════

    def _record_change(
        self,
        npc_name: str,
        arc_no: int,
        field_name: str,
        old_value: str,
        new_value: str,
        source: str = "arc_extraction",
        episode_no: int = 0,
    ) -> None:
        """[Phase 3-5A] DB에 NPC 변경 이력 기록. 실패 시 비차단."""
        try:
            db = getattr(self.tracker, "_db", None)
            if db and hasattr(db, "insert_npc_change"):
                db.insert_npc_change(
                    npc_name,
                    episode_no,
                    arc_no,
                    field_name,
                    str(old_value or ""),
                    str(new_value or ""),
                    source,
                )
        except Exception as e:
            logging.warning(f"[Phase 3-5A] NPC 이력 기록 실패 (비차단): {e}")

    # ═══════════════════════════════════════════════════════════════
    # NPC 등록/정보
    # ═══════════════════════════════════════════════════════════════

    def register_npc_death(self, npc_name: str, death_arc: int, death_context: str = "", episode_no: int = 0):
        """
        [V60.94] NPC 사망 등록

        Args:
            npc_name: NPC 이름
            death_arc: 사망한 Arc 번호
            death_context: 사망 맥락 (선택)
        """
        # [Phase 3-5A] 변경 전 상태 캡처
        old_status = self.tracker.npc_registry.get(npc_name, {}).get("status", "alive")

        if npc_name not in self.tracker.npc_registry:
            self.tracker.npc_registry[npc_name] = {}

        self.tracker.npc_registry[npc_name].update(
            {"status": "dead", "death_arc": death_arc, "death_context": death_context}
        )
        logging.info(f"\U0001f480 [V60.94] NPC 사망 등록: {npc_name} (Arc {death_arc})")

        # [Phase 3-5A] 이력 기록
        self._record_change(npc_name, death_arc, "status", old_status, "dead", episode_no=episode_no)

    def register_npc_info(
        self,
        npc_name: str,
        arc_no: int,
        weapon: str = None,
        level: str = None,
        personality_traits: str = None,
        primary_motivation: str = None,
        episode_no: int = 0,
    ):
        """
        [V60.94] NPC 정보 등록/업데이트
        [V66] personality_traits, primary_motivation 추가

        Args:
            npc_name: NPC 이름
            arc_no: Arc 번호
            weapon: 무장 (선택)
            level: 수준/경지 (선택)
            personality_traits: [V66] 성격 특성 (선택)
            primary_motivation: [V66] 주요 동기 (선택)
        """
        if npc_name not in self.tracker.npc_registry:
            self.tracker.npc_registry[npc_name] = {"status": "alive"}

        npc = self.tracker.npc_registry[npc_name]
        npc["last_arc"] = arc_no

        # [Phase 3-5A] 각 필드 변경 시 이력 기록 (값이 다를 때만)
        if weapon:
            old = npc.get("weapon", "")
            if old != weapon:
                self._record_change(npc_name, arc_no, "weapon", old, weapon, episode_no=episode_no)
            npc["weapon"] = weapon
        if level:
            old = npc.get("level", "")
            if old != level:
                self._record_change(npc_name, arc_no, "level", old, level, episode_no=episode_no)
            npc["level"] = level
        if personality_traits:
            old = npc.get("personality_traits", "")
            if old != personality_traits:
                self._record_change(
                    npc_name, arc_no, "personality_traits", old, personality_traits, episode_no=episode_no
                )
            npc["personality_traits"] = personality_traits
        if primary_motivation:
            old = npc.get("primary_motivation", "")
            if old != primary_motivation:
                self._record_change(
                    npc_name, arc_no, "primary_motivation", old, primary_motivation, episode_no=episode_no
                )
            npc["primary_motivation"] = primary_motivation

    def check_npc_changes(self, content: str, arc_no: int) -> list[dict]:
        """
        [V60.95] NPC 무장/수준 변경 검사 - WARNING 대상 (정당화 사유 필요)

        Args:
            content: 검사할 텍스트 (tactical_doc 등)
            arc_no: 현재 Arc 번호

        Returns:
            변경 목록 [{npc_name, change_type, old_value, new_value, severity}]
        """
        warnings = []

        # NPC 무장 패턴
        weapon_patterns = [
            r"([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))[을를으로]?\s*(?:들|휘두르|뽑)",
            r"([가-힣]{2,10})[의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))",
        ]

        # NPC 수준 패턴
        level_patterns = [
            r"([가-힣]{2,10})[이가은는]\s*(절대고수|화경|현경|초절정|일류|이류|삼류)",
            r"(절대고수|화경|현경|초절정|일류)[인의]\s*([가-힣]{2,10})",
        ]

        # 무장 변경 검사
        for pattern in weapon_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                npc_name = match[0] if len(match) > 0 else None
                weapon = match[1] if len(match) > 1 else None

                if npc_name and weapon and npc_name in self.tracker.npc_registry:
                    npc = self.tracker.npc_registry[npc_name]
                    old_weapon = npc.get("weapon")

                    if old_weapon and old_weapon != weapon:
                        warnings.append(
                            {
                                "npc_name": npc_name,
                                "change_type": "weapon",
                                "old_value": old_weapon,
                                "new_value": weapon,
                                "arc_no": arc_no,
                                "severity": "WARNING",
                                "reason": f"Arc {npc.get('last_arc', '?')}에서 '{old_weapon}' 사용 → Arc {arc_no}에서 '{weapon}' 사용",
                            }
                        )

        # 수준 변경 검사
        for pattern in level_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 패턴에 따라 순서가 다를 수 있음
                if match[0] in ["절대고수", "화경", "현경", "초절정", "일류", "이류", "삼류"]:
                    level, npc_name = match[0], match[1]
                else:
                    npc_name, level = match[0], match[1]

                if npc_name and level and npc_name in self.tracker.npc_registry:
                    npc = self.tracker.npc_registry[npc_name]
                    old_level = npc.get("level")

                    if old_level and old_level != level:
                        warnings.append(
                            {
                                "npc_name": npc_name,
                                "change_type": "level",
                                "old_value": old_level,
                                "new_value": level,
                                "arc_no": arc_no,
                                "severity": "WARNING",
                                "reason": f"Arc {npc.get('last_arc', '?')}에서 '{old_level}' → Arc {arc_no}에서 '{level}'",
                            }
                        )

        return warnings

    def extract_npc_info_from_arc(self, arc: dict, genre: str = "") -> list[dict]:
        """
        [V60.95] Arc의 tactical_doc에서 NPC 정보(무장, 수준) 추출 및 등록
        [V66.2] F-1: 비무협 장르에서 weapon/level regex 오탐 방지 — genre 가드 추가

        Args:
            arc: Arc 데이터
            genre: 장르 타입 ('wuxia', 'hunter', 'investment', 'fantasy' 등).
                   'wuxia'가 아니면 무장/수준 regex를 스킵하고 빈 리스트를 반환.

        Returns:
            추출된 NPC 정보 목록
        """
        # [V66.2] F-1: 비무협 장르에서는 무기/경지 regex가 일반 명사를 오탐하므로 스킵
        if genre and genre != "wuxia":
            return []

        arc_no = arc.get("arc_no", 0)
        ep_start = arc.get("ep_start", 0)  # 롤백 시 episode_no 기준 삭제를 위해
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        extracted = []

        # NPC 무장 패턴
        weapon_patterns = [
            r"([가-힣]{2,10})[이가은는의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))",
        ]

        # NPC 수준 패턴
        level_patterns = [
            r"([가-힣]{2,10})[이가은는]\s*(절대고수|화경|현경|초절정|일류|이류|삼류)",
            r"(절대고수|화경|현경|초절정|일류)[인의]\s*([가-힣]{2,10})",
        ]

        # 제외할 일반 명사
        exclude_words = ["주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"]

        for pattern in weapon_patterns:
            matches = re.findall(pattern, tactical)
            for match in matches:
                npc_name, weapon = match[0], match[1]
                if npc_name not in exclude_words and len(npc_name) >= 2:
                    self.register_npc_info(npc_name, arc_no, weapon=weapon, episode_no=ep_start)
                    extracted.append({"name": npc_name, "weapon": weapon, "arc": arc_no})

        for pattern in level_patterns:
            matches = re.findall(pattern, tactical)
            for match in matches:
                if match[0] in ["절대고수", "화경", "현경", "초절정", "일류", "이류", "삼류"]:
                    level, npc_name = match[0], match[1]
                else:
                    npc_name, level = match[0], match[1]

                if npc_name not in exclude_words and len(npc_name) >= 2:
                    self.register_npc_info(npc_name, arc_no, level=level, episode_no=ep_start)
                    extracted.append({"name": npc_name, "level": level, "arc": arc_no})

        return extracted

    # ═══════════════════════════════════════════════════════════════
    # 이름 경계 검증 + 죽은 NPC 등장 검사
    # ═══════════════════════════════════════════════════════════════

    def _is_standalone_name(self, name: str, text: str) -> bool:
        """[V63.4] 한글 단어 경계 검증 — 이름 앞뒤에 한글이 붙어있으면 오탐"""
        idx = 0
        while idx <= len(text) - len(name):
            pos = text.find(name, idx)
            if pos == -1:
                return False
            before = text[pos - 1] if pos > 0 else ""
            after_pos = pos + len(name)
            after = text[after_pos] if after_pos < len(text) else ""
            # [V63.4 P0] 앞쪽 한글 경계 검사
            if before and "\uac00" <= before <= "\ud7a3":
                idx = pos + 1
                continue  # 앞에 한글 붙어있으면 오탐
            # [V63.4 P0] 뒤쪽 한글 경계 검사 — "강철"이 "강철무"에 매칭 방지
            if after and "\uac00" <= after <= "\ud7a3":
                # 뒤에 조사/어미가 올 수 있으므로, 일반 한글 글자만 차단
                # 조사 패턴: 이/가/은/는/을/를/의/와/과/에/도/로/라/며 등
                ALLOWED_PARTICLES = set("이가은는을를의와과에도로서라며면고께한")
                if after not in ALLOWED_PARTICLES:
                    idx = pos + 1
                    continue  # 뒤에 일반 한글 붙어있으면 오탐
            return True  # 독립 매칭 확인
        return False

    def check_dead_npc_appearance(self, content: str, arc_no: int) -> list[dict]:
        """
        [V60.94] 죽은 NPC 등장 검사 - REJECT 대상

        Args:
            content: 검사할 텍스트 (tactical_doc 등)
            arc_no: 현재 Arc 번호

        Returns:
            위반 목록 [{npc_name, death_arc, severity}]
        """
        violations = []

        for npc_name, info in self.tracker.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)

                # [V60.97] 타임라인 비교: 사망 이전 Arc에서는 검사 스킵
                if arc_no < death_arc:
                    continue  # 아직 죽지 않은 시점

                # [V63.4] 단어 경계 검증으로 오탐 방지 (e.g. "박정" → "박정적인")
                if self._is_standalone_name(npc_name, content):
                    # 회상/과거 언급은 허용 (패턴 검사)
                    flashback_patterns = [
                        f"{npc_name}의 죽음",
                        f"{npc_name}을 떠올",
                        f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}",
                        f"죽은 {npc_name}",
                        f"{npc_name}의 유언",
                        f"{npc_name}의 무덤",
                        f"{npc_name}의 원혼",
                        f"{npc_name}의 유품",
                    ]

                    is_flashback = any(pattern in content for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장으로 간주 (대화, 행동 등)
                        action_patterns = [
                            f"{npc_name}이 ",
                            f"{npc_name}가 ",
                            f"{npc_name}은 ",
                            f"{npc_name}는 ",
                            f'"{npc_name}',  # 대사
                            f"{npc_name}의 검",
                            f"{npc_name}의 공격",
                        ]

                        if any(pattern in content for pattern in action_patterns):
                            violations.append(
                                {
                                    "npc_name": npc_name,
                                    "death_arc": death_arc,
                                    "current_arc": arc_no,
                                    "severity": "CRITICAL",
                                    "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 Arc {arc_no}에서 다시 등장",
                                }
                            )

        return violations

    # ═══════════════════════════════════════════════════════════════
    # 주인공 무공/스킬 추적
    # ═══════════════════════════════════════════════════════════════

    def register_protagonist_skill(self, skill_name: str, arc_no: int):
        """
        [V60.94] 주인공 능력 습득 등록 (장르별 로그 표시)

        Args:
            skill_name: 능력 이름
            arc_no: 습득 Arc 번호
        """
        if skill_name not in self.tracker.protagonist_skills:
            self.tracker.protagonist_skills.add(skill_name)
            self.tracker.skill_acquisitions[skill_name] = arc_no
            genre = getattr(self.tracker.preset_registry, "base_genre", "") or ""
            emoji, label = self._SKILL_LOG_LABEL.get(genre, ("\U0001f94b", "능력 습득"))
            logging.info(f"{emoji} [V60.94] {label}: {skill_name} (Arc {arc_no})")

    def check_unlearned_skill_usage(self, content: str, arc_no: int) -> list[dict]:
        """
        [V60.94] 미습득 무공 사용 검사 - 기록용 (REJECT 안 함)

        Args:
            content: 검사할 텍스트
            arc_no: 현재 Arc 번호

        Returns:
            의심 목록 [{skill_name, context}] - 정보 제공용
        """
        suspicious = []

        # 무공 사용 패턴
        skill_patterns = [
            r"([가-힣]{2,10}(?:장|권|법|공|결|식|초))[을를]?\s*(?:시전|펼치|사용|발동)",
            r"([가-힣]{2,10}(?:심법|내공|기공))[으로]?\s*(?:운기|조식)",
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, content)
            for skill in matches:
                if skill and len(skill) >= 2:
                    # 등록된 무공인지 확인
                    if skill not in self.tracker.protagonist_skills:
                        # 새로운 무공일 수도 있으므로 INFO 레벨
                        suspicious.append(
                            {
                                "skill_name": skill,
                                "arc_no": arc_no,
                                "severity": "INFO",
                                "note": "습득 기록 없음 - 새 무공이거나 숨겨둔 패일 수 있음",
                            }
                        )

        return suspicious

    def get_entity_registry(self) -> dict:
        """
        [V60.94] Director/Validator용 Entity Registry 반환

        Returns:
            {
                "dead_npcs": [{name, death_arc}],
                "npc_info": [{name, weapon, level, status}],
                "protagonist_skills": [skill_names],
                "protagonist_items": [item_names]
            }
        """
        dead_npcs = []
        npc_info = []

        for name, info in self.tracker.npc_registry.items():
            if info.get("status") == "dead":
                dead_npcs.append({"name": name, "death_arc": info.get("death_arc", 0)})
            npc_info.append(
                {
                    "name": name,
                    "weapon": info.get("weapon", ""),
                    "level": info.get("level", ""),
                    "status": info.get("status", "alive"),
                    "last_arc": info.get("last_arc", 0),
                }
            )

        # 최신 상태의 아이템 목록
        protagonist_items = []
        if self.tracker.states:
            latest_ep = max(self.tracker.states.keys())
            latest_state = self.tracker.states[latest_ep]
            protagonist_items = latest_state.items + latest_state.weapons

        return {
            "dead_npcs": dead_npcs,
            "npc_info": npc_info,
            "protagonist_skills": list(self.tracker.protagonist_skills),
            "protagonist_items": protagonist_items,
        }

    def merge_npc_registry(self, other: "StateTracker"):
        """[V60.94] 다른 StateTracker의 NPC 레지스트리 병합"""
        for name, info in other.npc_registry.items():
            if name not in self.tracker.npc_registry:
                self.tracker.npc_registry[name] = info.copy()
            else:
                # [V63.4 P0] 사망 정보 보호: 이미 dead인 NPC는 비사망 업데이트로 덮어쓰기 차단
                existing = self.tracker.npc_registry[name]
                if existing.get("status") == "dead" and info.get("status") != "dead":
                    continue  # 사망 상태 보존
                elif info.get("status") == "dead":
                    # [Sweep42] 기존 속성 보존 후 사망 정보 병합 (full overwrite → filtered merge)
                    filtered = {k: v for k, v in info.items() if v not in ("", None, [], {}) and v is not False}
                    existing.update(filtered)
                else:
                    # [Sweep34] 빈값으로 기존 속성이 덮어쓰기 되는 문제 방지
                    # [Sweep64] 0/False도 기존 값 덮어쓰기 방지 (last_arc=0 회귀 등)
                    filtered = {
                        k: v
                        for k, v in info.items()
                        if v not in ("", None, [], {})
                        and v is not False
                        and not (isinstance(v, int) and v == 0 and k in existing and existing[k])
                    }
                    existing.update(filtered)  # [G12] 필터링 결과를 기존 데이터에 병합

        # 무공 목록 병합
        self.tracker.protagonist_skills.update(other.protagonist_skills)
        for skill, arc in other.skill_acquisitions.items():
            if skill not in self.tracker.skill_acquisitions:
                self.tracker.skill_acquisitions[skill] = arc

    # ═══════════════════════════════════════════════════════════════
    # state_changes 추출 (NPC 사망, 무공, 관계, 부상, 이동)
    # ═══════════════════════════════════════════════════════════════

    def extract_npc_deaths_from_arc(self, arc: dict) -> list[str]:
        """
        [V61] Arc에서 NPC 사망 추출 및 등록
        우선순위: state_changes 필드 > Regex 폴백

        Args:
            arc: Arc 데이터 (state_changes 또는 tactical_doc 포함)

        Returns:
            사망한 NPC 이름 목록
        """
        arc_no = arc.get("arc_no", 0)
        ep_start = arc.get("ep_start", 0)  # 롤백 시 episode_no 기준 삭제를 위해
        dead_npcs = []

        # [V61] 1순위: state_changes 필드 직접 읽기
        # [V70.1] 일반 명사 exclude + LLM 검증 추가 (기존 regex 경로와 동일 수준)
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            npc_deaths = state_changes.get("npc_deaths", [])
            if isinstance(npc_deaths, list) and npc_deaths:
                _sc_candidates = []
                for death in npc_deaths:
                    if isinstance(death, dict):
                        npc_name = death.get("name", "")
                    elif isinstance(death, str):
                        npc_name = death
                    else:
                        continue
                    if npc_name and len(npc_name) >= 2 and npc_name not in _NPC_DEATH_EXCLUDE_WORDS:
                        _sc_candidates.append((npc_name, death))
                # LLM 검증 (regex 경로와 동일 수준 적용)
                if _sc_candidates:
                    _names_only = [c[0] for c in _sc_candidates]
                    _tactical = arc.get("tactical_doc", "")
                    if isinstance(_tactical, dict):
                        _tactical = "\n".join(str(v) for v in _tactical.values() if v)
                    _verified = self._verify_npc_names_llm(_names_only, _tactical, arc_no)
                    for npc_name, death_data in _sc_candidates:
                        if npc_name not in _verified:
                            logging.info(f"🔍 [V70.1] NPC 사망 후보 '{npc_name}' LLM 검증 탈락 (state_changes 경로)")
                            continue
                        if isinstance(death_data, dict):
                            episode = death_data.get("episode", arc_no)
                            cause = death_data.get("cause", "state_changes에서 추출")
                        else:
                            episode = arc_no
                            cause = "state_changes에서 추출"
                        self.register_npc_death(
                            npc_name, arc_no, f"Arc {arc_no} Ep {episode}: {cause}", episode_no=ep_start
                        )
                        dead_npcs.append(npc_name)
                if dead_npcs:
                    return list(set(dead_npcs))

        # [V61] 2순위: Regex 폴백 (하위 호환 + 보조)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        death_patterns = [
            r"([가-힣]{2,10})[이가을를]\s*(?:죽이|처단|살해|베어|제거|처형|사살)",
            r"([가-힣]{2,10})[이가은는]\s*(?:죽|사망|전사|명을\s*다|숨을\s*거두|운명)",
            r"([가-힣]{2,10})[의]\s*(?:죽음|최후|사망|전사)",
            r"([가-힣]{2,10})[을를]\s*(?:끝장|마무리|처리)",
        ]

        exclude_words = _NPC_DEATH_EXCLUDE_WORDS

        regex_candidates = []
        for pattern in death_patterns:
            matches = re.findall(pattern, tactical)
            for npc_name in matches:
                if npc_name and len(npc_name) >= 2 and npc_name not in exclude_words:
                    regex_candidates.append(npc_name)
        regex_candidates = list(set(regex_candidates))

        # [V62.5] LLM 검증: regex 후보가 실제 인물 이름인지 확인
        if regex_candidates:
            verified = self._verify_npc_names_llm(regex_candidates, tactical, arc_no)
            for npc_name in verified:
                self.register_npc_death(
                    npc_name, arc_no, f"Arc {arc_no} tactical_doc Regex+LLM검증", episode_no=ep_start
                )
                dead_npcs.append(npc_name)

        return list(set(dead_npcs))

    def _verify_npc_names_llm(self, candidates: list[str], context: str, arc_no: int) -> list[str]:
        """
        [V62.5] LLM으로 regex 추출 NPC 이름 후보 검증
        일반 명사(데이터, 후원자, 시장 등) 오탐을 필터링한다.
        LLM 없으면 원본 반환 (하위 호환).
        """
        if not self.tracker._llm_client or not candidates:
            return candidates

        try:
            from google.genai import types as _types

            prompt = (
                f"다음은 소설 텍스트에서 regex로 추출한 'NPC 사망 후보' 목록입니다.\n"
                f"후보: {json.dumps(candidates, ensure_ascii=False)}\n\n"
                f"원문 (Arc {arc_no}):\n{context[:3000]}\n\n"
                f"위 후보 중 실제 작중 등장인물 이름(고유명사)이면서 "
                f"해당 Arc에서 실제로 죽거나 처단당한 캐릭터만 JSON 배열로 반환하세요.\n"
                f"일반 명사(데이터, 후원자, 시장, 사태, 세력, 조직, 몬스터 등)는 반드시 제외.\n"
                f"해당하는 인물이 없으면 빈 배열 []을 반환하세요."
            )
            # [V63.3] 중복 딜레이 제거 (직접 API 호출이므로 최소 지연만)
            time.sleep(0.1)
            response = self.tracker._llm_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=_types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=256,
                    response_mime_type="application/json",
                ),
            )
            try:  # [V70] response.text ValueError 방어
                _resp_text = response.text
            except (ValueError, AttributeError):
                _resp_text = None
            if not _resp_text:
                logging.warning("[XC-002] NPC LLM 검증 응답 없음 → fail-closed: []")
                return []
            result = json.loads(_resp_text)
            if isinstance(result, list):
                verified = [name for name in result if isinstance(name, str) and name in candidates]
                filtered = set(candidates) - set(verified)
                if filtered:
                    logging.info(f"\U0001f50d [V62.5] NPC 오탐 필터링: {filtered} (LLM 검증으로 제외)")
                return verified
        except Exception as e:
            logging.warning("[XC-002] NPC LLM 검증 예외 → fail-closed: %s", str(e)[:60])
            return []

    def extract_skill_acquisitions_from_arc(self, arc: dict) -> list[str]:
        """
        [V61] Arc에서 무공/기술 습득 추출 및 등록
        우선순위: state_changes 필드 > Regex 폴백

        Args:
            arc: Arc 데이터

        Returns:
            습득한 무공 이름 목록
        """
        arc_no = arc.get("arc_no", 0)
        learned_skills = []

        # [V61] 1순위: state_changes 필드 직접 읽기 (정확도 ~98%)
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            skill_acq = state_changes.get("skill_acquisitions", [])
            if isinstance(skill_acq, list) and skill_acq:
                for skill in skill_acq:
                    if isinstance(skill, dict):
                        skill_name = skill.get("name", "")
                        skill.get("episode", arc_no)
                        skill.get("source", "state_changes에서 추출")
                        if skill_name and len(skill_name) >= 2:
                            self.register_protagonist_skill(skill_name, arc_no)
                            learned_skills.append(skill_name)
                    elif isinstance(skill, str) and len(skill) >= 2:
                        self.register_protagonist_skill(skill, arc_no)
                        learned_skills.append(skill)
                if learned_skills:
                    return list(set(learned_skills))

        # [V61] 2순위: Regex 폴백 (하위 호환 + 보조)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        learn_patterns = [
            r"([가-힣]{2,10}(?:장|권|법|공|결|식|초|심법))[을를]?\s*(?:습득|익히|배우|터득|깨우치|전수받)",
            r"([가-힣]{2,10}(?:장|권|법|공|결|식|초|심법))[의]?\s*(?:오의|진수|비전)[을를]?\s*(?:깨달|얻)",
        ]

        for pattern in learn_patterns:
            matches = re.findall(pattern, tactical)
            for skill_name in matches:
                if skill_name and len(skill_name) >= 2:
                    self.register_protagonist_skill(skill_name, arc_no)
                    learned_skills.append(skill_name)

        return list(set(learned_skills))

    def extract_relationship_changes_from_arc(self, arc: dict) -> list[dict]:
        """
        [V61] Arc에서 관계 변화 추출
        [V66.1] F-3: state_changes가 비어있으면 regex 폴백 사용.

        Args:
            arc: Arc 데이터

        Returns:
            관계 변화 목록 [{"npc": ..., "from": ..., "to": ..., "episode": ...}]
        """
        arc_no = arc.get("arc_no", 0)
        changes = []

        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            rel_changes = state_changes.get("relationship_changes", [])
            if isinstance(rel_changes, list):
                for change in rel_changes:
                    if isinstance(change, dict):
                        npc = change.get("npc", "")
                        from_rel = change.get("from", "")
                        to_rel = change.get("to", "")
                        episode = change.get("episode", arc_no)
                        if npc and from_rel and to_rel:
                            changes.append(
                                {"npc": npc, "from": from_rel, "to": to_rel, "episode": episode, "arc_no": arc_no}
                            )
                            # NPC registry에도 반영
                            if npc in self.tracker.npc_registry:
                                self.tracker.npc_registry[npc]["relation_to_protag"] = to_rel
                                self.tracker.npc_registry[npc]["last_arc"] = arc_no
                            self._record_change(
                                npc, arc_no, "relation_to_protag", from_rel, to_rel, "arc_relationship", episode
                            )

        # [V66.1] F-3: regex 폴백
        if not changes:
            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):
                tactical = "\n".join(str(v) for v in tactical.values() if v)
            if tactical:
                regex_changes = self._regex_extract_relationship_changes(tactical)
                for rc in regex_changes:
                    rc["arc_no"] = arc_no
                    changes.append(rc)
                    # NPC registry 반영
                    npc = rc.get("npc", "")
                    to_rel = rc.get("to", "")
                    if npc and npc in self.tracker.npc_registry and to_rel:
                        _old_rel = self.tracker.npc_registry[npc].get("relation_to_protag", "")
                        self.tracker.npc_registry[npc]["relation_to_protag"] = to_rel
                        self.tracker.npc_registry[npc]["last_arc"] = arc_no
                        self._record_change(
                            npc, arc_no, "relation_to_protag", _old_rel, to_rel, "arc_relationship_regex"
                        )

        return changes

    def extract_npc_injuries_from_arc(self, arc: dict) -> list[dict]:
        """
        [V63] Arc에서 NPC 부상 상태 추출 및 레지스트리 반영.
        [V66.1] F-3: state_changes가 비어있으면 regex 폴백 사용.
        """
        arc_no = arc.get("arc_no", 0)
        injuries = []
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            npc_injuries = state_changes.get("npc_injuries", [])
            if isinstance(npc_injuries, list):
                for entry in npc_injuries:
                    if isinstance(entry, dict):
                        npc_name = entry.get("name", "")
                        state = entry.get("state", "")
                        if npc_name and state:
                            injuries.append(
                                {
                                    "name": npc_name,
                                    "episode": entry.get("episode", arc_no),
                                    "state": state,
                                    "cause": entry.get("cause", ""),
                                    "arc_no": arc_no,
                                }
                            )
                            # NPC registry 반영
                            _old_injury = (
                                self.tracker.npc_registry[npc_name].get("injury", "")
                                if npc_name in self.tracker.npc_registry
                                else ""
                            )
                            if npc_name in self.tracker.npc_registry:
                                self.tracker.npc_registry[npc_name]["injury"] = state
                                self.tracker.npc_registry[npc_name]["last_arc"] = arc_no
                            self._record_change(
                                npc_name,
                                arc_no,
                                "injury",
                                _old_injury,
                                state,
                                "arc_injury",
                                entry.get("episode", arc_no),
                            )

        # [V66.1] F-3: regex 폴백
        if not injuries:
            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):
                tactical = "\n".join(str(v) for v in tactical.values() if v)
            if tactical:
                regex_injuries = self._regex_extract_npc_injuries(tactical)
                for ri in regex_injuries:
                    ri["arc_no"] = arc_no
                    injuries.append(ri)
                    npc_name = ri.get("name", "")
                    state = ri.get("state", "")
                    if npc_name and npc_name in self.tracker.npc_registry and state:
                        _old_injury = self.tracker.npc_registry[npc_name].get("injury", "")
                        self.tracker.npc_registry[npc_name]["injury"] = state
                        self.tracker.npc_registry[npc_name]["last_arc"] = arc_no
                        self._record_change(npc_name, arc_no, "injury", _old_injury, state, "arc_injury_regex")

        return injuries

    def extract_npc_movements_from_arc(self, arc: dict) -> list[dict]:
        """
        [V63] Arc에서 NPC 이동 추출 및 레지스트리 반영.
        [V66.1] F-3: state_changes가 비어있으면 regex 폴백 사용.
        """
        arc_no = arc.get("arc_no", 0)
        movements = []
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            npc_movements = state_changes.get("npc_movements", [])
            if isinstance(npc_movements, list):
                for entry in npc_movements:
                    if isinstance(entry, dict):
                        npc_name = entry.get("name", "")
                        to_loc = entry.get("to", "")
                        if npc_name and to_loc:
                            movements.append(
                                {
                                    "name": npc_name,
                                    "episode": entry.get("episode", arc_no),
                                    "from": entry.get("from", ""),
                                    "to": to_loc,
                                    "arc_no": arc_no,
                                }
                            )
                            # NPC registry 반영
                            _old_loc = entry.get("from", "")
                            if npc_name in self.tracker.npc_registry:
                                if not _old_loc:
                                    _old_loc = self.tracker.npc_registry[npc_name].get("location", "")
                                self.tracker.npc_registry[npc_name]["location"] = to_loc
                                self.tracker.npc_registry[npc_name]["last_arc"] = arc_no
                            self._record_change(
                                npc_name,
                                arc_no,
                                "location",
                                _old_loc,
                                to_loc,
                                "arc_movement",
                                entry.get("episode", arc_no),
                            )

        # [V66.1] F-3: regex 폴백
        if not movements:
            tactical = arc.get("tactical_doc", "")
            if isinstance(tactical, dict):
                tactical = "\n".join(str(v) for v in tactical.values() if v)
            if tactical:
                regex_movements = self._regex_extract_npc_movements(tactical)
                for rm in regex_movements:
                    rm["arc_no"] = arc_no
                    movements.append(rm)
                    npc_name = rm.get("name", "")
                    to_loc = rm.get("to", "")
                    if npc_name and npc_name in self.tracker.npc_registry and to_loc:
                        _old_loc = self.tracker.npc_registry[npc_name].get("location", "")
                        self.tracker.npc_registry[npc_name]["location"] = to_loc
                        self.tracker.npc_registry[npc_name]["last_arc"] = arc_no
                        self._record_change(npc_name, arc_no, "location", _old_loc, to_loc, "arc_movement_regex")

        return movements

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-3: Regex 폴백 메서드 (relationship, injury, movement)
    # ═══════════════════════════════════════════════════════════════

    def _regex_extract_relationship_changes(self, tactical_doc: str) -> list[dict]:
        """
        [V66.1] F-3: tactical_doc에서 관계 변화를 regex로 추출.
        state_changes.relationship_changes가 비어있을 때 폴백으로 사용.

        Patterns: "NPC가 적대→동맹", "NPC와 화해", "NPC에게 배신당"
        """
        if not tactical_doc:
            return []

        changes = []
        seen = set()
        exclude_words = {"주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"}

        # "NPC가 적→동맹" / "NPC의 관계가 적대에서 아군으로"
        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_REL_ARROW.finditer(tactical_doc):
            npc = match.group(1).strip()
            from_rel = match.group(2).strip()
            to_rel = match.group(3).strip()
            if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                seen.add(npc)
                changes.append({"npc": npc, "from": from_rel, "to": to_rel, "episode": 0})

        # "NPC와 화해", "NPC에게 배신당"
        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_REL_RECONCILE.finditer(tactical_doc):
            npc = match.group(1).strip()
            if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                seen.add(npc)
                changes.append({"npc": npc, "from": "적대", "to": "동맹", "episode": 0})

        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_REL_BETRAY.finditer(tactical_doc):
            npc = match.group(1).strip()
            if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                seen.add(npc)
                changes.append({"npc": npc, "from": "아군", "to": "적대", "episode": 0})

        return changes

    def _regex_extract_npc_injuries(self, tactical_doc: str) -> list[dict]:
        """
        [V66.1] F-3: tactical_doc에서 NPC 부상을 regex로 추출.
        state_changes.npc_injuries가 비어있을 때 폴백으로 사용.

        Patterns: "NPC가 부상", "NPC가 중상", "NPC의 팔이 잘"
        """
        if not tactical_doc:
            return []

        injuries = []
        seen = set()
        exclude_words = {"주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"}

        # [V66.1] C-2: module-level compiled patterns
        injury_patterns = [
            (_RE_INJURY_DIRECT, None),
            (_RE_INJURY_BODY, "중상"),
            (_RE_INJURY_REVERSE, None),
        ]

        for pattern, default_state in injury_patterns:
            for match in pattern.finditer(tactical_doc):
                groups = match.groups()
                if len(groups) >= 2:
                    # 패턴에 따라 NPC 이름과 부상 상태 위치가 다름
                    if groups[0] in ("중상", "경상", "위독", "부상"):
                        state = groups[0]
                        npc_name = groups[1]
                    else:
                        npc_name = groups[0]
                        state = default_state or groups[1]
                elif len(groups) == 1 and default_state:
                    npc_name = groups[0]
                    state = default_state
                else:
                    continue

                npc_name = npc_name.strip()
                # 부상→경상 변환
                if state == "부상":
                    state = "경상"

                if npc_name not in exclude_words and len(npc_name) >= 2 and npc_name not in seen:
                    seen.add(npc_name)
                    injuries.append(
                        {"name": npc_name, "episode": 0, "state": state, "cause": "tactical_doc regex 추출"}
                    )

        return injuries

    def _regex_extract_npc_movements(self, tactical_doc: str) -> list[dict]:
        """
        [V66.1] F-3: tactical_doc에서 NPC 이동을 regex로 추출.
        state_changes.npc_movements가 비어있을 때 폴백으로 사용.

        Patterns: "NPC가 X에서 Y로 이동", "NPC가 X를 떠나"
        """
        if not tactical_doc:
            return []

        movements = []
        seen = set()
        exclude_words = {"주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"}

        # "NPC가 X에서 Y로 이동/향하다"
        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_MOVE_FROM_TO.finditer(tactical_doc):
            npc = match.group(1).strip()
            from_loc = match.group(2).strip()
            to_loc = match.group(3).strip()
            if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                seen.add(npc)
                movements.append({"name": npc, "episode": 0, "from": from_loc, "to": to_loc})

        # "NPC가 X로 이동/향하다/도착"
        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_MOVE_TO.finditer(tactical_doc):
            npc = match.group(1).strip()
            to_loc = match.group(2).strip()
            if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                seen.add(npc)
                movements.append({"name": npc, "episode": 0, "from": "", "to": to_loc})

        # "NPC가 X를 떠나다"
        # [V66.1] C-2: module-level compiled pattern
        for match in _RE_MOVE_LEAVE.finditer(tactical_doc):
            npc = match.group(1).strip()
            from_loc = match.group(2).strip()
            if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                seen.add(npc)
                movements.append({"name": npc, "episode": 0, "from": from_loc, "to": ""})

        return movements

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-8: NPC 영구 부상 (절단, 실명, 흉터 등) 추적
    # ═══════════════════════════════════════════════════════════════

    def register_permanent_injury(self, name: str, injury_type: str, description: str, arc_no: int):
        """
        [V66.1] NPC 영구 부상 등록.

        Args:
            name: NPC 이름
            injury_type: "amputation" | "blindness" | "scar" | "disfigurement"
            description: 설명 (예: "왼팔 절단", "왼쪽 눈 실명")
            arc_no: 발생 Arc 번호
        """
        if not name or len(name) < 2:
            return
        if injury_type not in ("amputation", "blindness", "scar", "disfigurement"):
            injury_type = "disfigurement"  # 기본값

        if name not in self.tracker.npc_registry:
            self.tracker.npc_registry[name] = {"status": "alive"}

        npc = self.tracker.npc_registry[name]
        if "permanent_injuries" not in npc:
            npc["permanent_injuries"] = []

        # 중복 방지: 같은 description + arc_no
        for existing in npc["permanent_injuries"]:
            if existing.get("description") == description and existing.get("arc_no") == arc_no:
                return

        npc["permanent_injuries"].append(
            {
                "type": injury_type,
                "description": description,
                "arc_no": arc_no,
            }
        )
        npc["last_arc"] = arc_no
        self._record_change(name, arc_no, "permanent_injuries", "", f"{injury_type}: {description}", "permanent_injury")
        logging.info(f"[V66.1] NPC 영구 부상 등록: {name} - {description} (Arc {arc_no})")

    def extract_permanent_injuries_from_arc(self, arc_data: dict) -> list[dict]:
        """
        [V66.1] Arc에서 영구 부상 추출 및 등록.
        우선순위: state_changes["permanent_injuries"] > regex 폴백.

        Args:
            arc_data: Arc 데이터

        Returns:
            영구 부상 목록
        """
        arc_no = arc_data.get("arc_no", 0)
        results = []

        # 1순위: state_changes.permanent_injuries
        state_changes = arc_data.get("state_changes", {})
        if isinstance(state_changes, dict):
            perm_injuries = state_changes.get("permanent_injuries", [])
            if isinstance(perm_injuries, list) and perm_injuries:
                for pi in perm_injuries:
                    if isinstance(pi, dict) and pi.get("name"):
                        name = str(pi["name"])
                        i_type = str(pi.get("type", "disfigurement"))
                        desc = str(pi.get("description", ""))
                        episode = pi.get("episode", arc_no)
                        if name and len(name) >= 2 and desc:
                            self.register_permanent_injury(name, i_type, desc, arc_no)
                            results.append(
                                {
                                    "name": name,
                                    "type": i_type,
                                    "description": desc,
                                    "episode": episode,
                                    "arc_no": arc_no,
                                }
                            )
                if results:
                    return results

        # 2순위: regex 폴백
        tactical = arc_data.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        if not tactical:
            return results

        exclude_words = {"주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"}
        seen = set()

        # [V66.1] C-2: module-level compiled patterns
        amputation_patterns = _RE_PERM_AMPUTATION
        blindness_patterns = _RE_PERM_BLINDNESS
        scar_patterns = _RE_PERM_SCAR

        for pattern in amputation_patterns:
            for match in pattern.finditer(tactical):
                npc = match.group(1).strip()
                body_part = match.group(2).strip()
                if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                    seen.add(npc)
                    desc = f"{body_part} 절단"
                    self.register_permanent_injury(npc, "amputation", desc, arc_no)
                    results.append(
                        {"name": npc, "type": "amputation", "description": desc, "episode": 0, "arc_no": arc_no}
                    )

        for pattern in blindness_patterns:
            for match in pattern.finditer(tactical):
                npc = match.group(1).strip()
                if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                    seen.add(npc)
                    desc = "실명"
                    self.register_permanent_injury(npc, "blindness", desc, arc_no)
                    results.append(
                        {"name": npc, "type": "blindness", "description": desc, "episode": 0, "arc_no": arc_no}
                    )

        for pattern in scar_patterns:
            for match in pattern.finditer(tactical):
                npc = match.group(1).strip()
                if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                    seen.add(npc)
                    desc = "영구 흉터"
                    self.register_permanent_injury(npc, "scar", desc, arc_no)
                    results.append({"name": npc, "type": "scar", "description": desc, "episode": 0, "arc_no": arc_no})

        return results

    def get_permanent_injury_summary(self) -> str:
        """
        [V66.1] NPC 영구 부상 목록 -> 프롬프트 주입용 문자열.
        잘린 팔로 양손 무기를 쓰는 등의 모순 방지.

        Returns:
            포맷된 영구 부상 요약 문자열
        """
        lines = []
        for name, info in self.tracker.npc_registry.items():
            perm_injuries = info.get("permanent_injuries", [])
            if perm_injuries:
                for pi in perm_injuries:
                    desc = pi.get("description", "")
                    arc = pi.get("arc_no", "?")
                    lines.append(f"  - {name}: {desc} (Arc {arc})")

        if not lines:
            return ""

        header = "[V66.1] NPC 영구 부상 - 회복 불가, 묘사 시 반드시 반영:"
        return header + "\n" + "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] F-10: NPC 사망 등록 취소 메커니즘
    # ═══════════════════════════════════════════════════════════════

    def revive_npc(self, name: str, reason: str) -> bool:
        """
        [V66.1] NPC 사망 등록 취소 (false positive 수정용).
        명시적 호출로만 동작하며, 자동 호출되지 않음.

        Args:
            name: 부활시킬 NPC 이름
            reason: 부활 사유 (예: "오탐지", "회상에서 추출된 이름")

        Returns:
            True: 성공적으로 부활, False: NPC 미등록 또는 이미 alive
        """
        if name not in self.tracker.npc_registry:
            logging.warning(f"[V66.1] NPC 부활 실패: '{name}' 레지스트리에 미등록")
            return False

        npc = self.tracker.npc_registry[name]
        if npc.get("status") != "dead":
            logging.info(f"[V66.1] NPC 부활 불필요: '{name}' 이미 alive 상태")
            return False

        # 사망 정보 백업 후 제거
        old_death_arc = npc.get("death_arc")
        old_death_context = npc.get("death_context", "")

        npc["status"] = "alive"
        npc.pop("death_arc", None)
        npc.pop("death_context", None)

        # 부활 이력 기록
        if "revive_history" not in npc:
            npc["revive_history"] = []
        npc["revive_history"].append(
            {
                "reason": reason,
                "previous_death_arc": old_death_arc,
                "previous_death_context": old_death_context,
            }
        )

        logging.info(f"[V66.1] NPC 사망 취소: '{name}' (사유: {reason}, 이전 사망 Arc: {old_death_arc})")
        return True

    # ═══════════════════════════════════════════════════════════════
    # Stage 3/4: Blueprint/Manuscript 내 죽은 NPC 검사
    # ═══════════════════════════════════════════════════════════════

    def check_dead_npc_in_blueprint(self, blueprint: dict, ep_num: int, arc_no: int = 0) -> list[dict]:
        """
        [V60.96] Blueprint에서 죽은 NPC 등장 검사 - REJECT 대상

        Args:
            blueprint: Blueprint 데이터 (integrated_scenario, scene_breakdown 포함)
            ep_num: 에피소드 번호
            arc_no: [V60.97] Arc 번호 (타임라인 비교용, 0이면 blueprint에서 추출 시도)

        Returns:
            위반 목록 [{npc_name, death_arc, severity, context}]
        """
        violations = []

        # [V60.97] arc_no 추출 (파라미터 우선, 없으면 blueprint에서)
        if arc_no <= 0:
            arc_no = blueprint.get("arc_no", 0)
        if arc_no <= 0:
            # 에피소드 번호로 추정 (보수적: 5화 단위)
            arc_no = (ep_num - 1) // 5 + 1

        # integrated_scenario 추출
        content = blueprint.get("integrated_scenario", "")
        if not isinstance(content, str):
            content = str(content) if content else ""

        # scene_breakdown 추가
        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, list):  # [V70] list 타입 대응
            for scene in scenes:
                if isinstance(scene, dict):
                    content += "\n" + scene.get("content", "")
                    content += "\n" + scene.get("summary", "")
                elif isinstance(scene, str):
                    content += "\n" + scene
        elif isinstance(scenes, dict):
            for scene in scenes.values():
                if isinstance(scene, dict):
                    content += "\n" + scene.get("content", "")
                    content += "\n" + scene.get("summary", "")
                elif isinstance(scene, str):
                    content += "\n" + scene

        # 죽은 NPC 검사
        for npc_name, info in self.tracker.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)

                # [V60.97] 타임라인 비교: 사망 이전 Arc에서는 검사 스킵
                if arc_no < death_arc:
                    continue  # 아직 죽지 않은 시점

                # [V63.4] 단어 경계 검증으로 오탐 방지
                if self._is_standalone_name(npc_name, content):
                    # 회상/언급 패턴은 허용
                    flashback_patterns = [
                        f"{npc_name}의 죽음",
                        f"{npc_name}을 떠올",
                        f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}",
                        f"죽은 {npc_name}",
                        f"{npc_name}의 유언",
                        f"{npc_name}의 무덤",
                        f"{npc_name}의 원혼",
                        f"{npc_name}의 유품",
                        f"{npc_name}을 추모",
                        f"{npc_name}의 복수",
                    ]
                    is_flashback = any(pattern in content for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장 패턴 검사
                        action_patterns = [
                            f"{npc_name}이 ",
                            f"{npc_name}가 ",
                            f"{npc_name}은 ",
                            f"{npc_name}는 ",
                            f'"{npc_name}',
                            f"{npc_name}와 ",
                            f"{npc_name}과 ",
                            f"{npc_name}의 검",
                            f"{npc_name}의 공격",
                            f"{npc_name}에게",
                        ]
                        if any(pattern in content for pattern in action_patterns):
                            violations.append(
                                {
                                    "npc_name": npc_name,
                                    "death_arc": death_arc,
                                    "current_ep": ep_num,
                                    "current_arc": arc_no,
                                    "severity": "CRITICAL",
                                    "context": "blueprint",
                                    "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 제{ep_num}화(Arc {arc_no}) Blueprint에서 다시 등장",
                                }
                            )

        return violations

    def check_dead_npc_in_manuscript(self, manuscript: str, ep_num: int, arc_no: int = 0) -> list[dict]:
        """
        [V60.96] Manuscript에서 죽은 NPC 등장 검사 - REJECT 대상

        Args:
            manuscript: 원고 텍스트
            ep_num: 에피소드 번호
            arc_no: [V60.97] Arc 번호 (타임라인 비교용, 0이면 ep_num으로 추정)

        Returns:
            위반 목록 [{npc_name, death_arc, severity, context}]
        """
        violations = []

        if not manuscript or not isinstance(manuscript, str):
            return violations

        # [V60.97] arc_no 추정 (파라미터 없으면 에피소드 기준)
        if arc_no <= 0:
            arc_no = (ep_num - 1) // 5 + 1

        for npc_name, info in self.tracker.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)

                # [V60.97] 타임라인 비교: 사망 이전 Arc에서는 검사 스킵
                if arc_no < death_arc:
                    continue  # 아직 죽지 않은 시점

                # [V63.4] 단어 경계 검증으로 오탐 방지
                if self._is_standalone_name(npc_name, manuscript):
                    # 회상/언급 패턴은 허용 (더 광범위)
                    flashback_patterns = [
                        f"{npc_name}의 죽음",
                        f"{npc_name}을 떠올",
                        f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}",
                        f"죽은 {npc_name}",
                        f"{npc_name}의 유언",
                        f"{npc_name}의 무덤",
                        f"{npc_name}의 원혼",
                        f"{npc_name}의 유품",
                        f"{npc_name}을 추모",
                        f"{npc_name}의 복수",
                        f"{npc_name}의 이름",
                        f"{npc_name}처럼",
                        f"{npc_name}같은",
                        f"과거의 {npc_name}",
                        f"{npc_name}의 기억",
                        f"{npc_name}의 영혼",
                    ]
                    is_flashback = any(pattern in manuscript for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장 패턴 (대화, 행동)
                        action_patterns = [
                            f"{npc_name}이 말",
                            f"{npc_name}가 말",
                            f"{npc_name}이 대답",
                            f"{npc_name}가 대답",
                            f"{npc_name}은 고개",
                            f"{npc_name}는 고개",
                            f'"{npc_name}',
                            f"{npc_name}이 검",
                            f"{npc_name}가 검",
                            f"{npc_name}의 손",
                            f"{npc_name}이 다가",
                            f"{npc_name}가 다가",
                        ]
                        if any(pattern in manuscript for pattern in action_patterns):
                            violations.append(
                                {
                                    "npc_name": npc_name,
                                    "death_arc": death_arc,
                                    "current_ep": ep_num,
                                    "current_arc": arc_no,
                                    "severity": "CRITICAL",
                                    "context": "manuscript",
                                    "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 제{ep_num}화(Arc {arc_no}) 원고에서 살아있는 것처럼 등장",
                                }
                            )

        return violations

    def get_dead_npc_summary(self) -> str:
        """
        [V60.96] 죽은 NPC 목록 요약 (Writer/Architect 프롬프트 주입용)

        Returns:
            죽은 NPC 목록 문자열
        """
        dead_npcs = []
        for name, info in self.tracker.npc_registry.items():
            if info.get("status") == "dead":
                death_arc = info.get("death_arc", 0)
                dead_npcs.append(f"  - {name} (Arc {death_arc}에서 사망)")

        if not dead_npcs:
            return ""

        lines = ["\U0001f6a8 [사망 NPC 목록 - 절대 살아있는 것처럼 등장시키지 말 것]", *dead_npcs, ""]
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] NPC 성격/동기 baseline
    # ═══════════════════════════════════════════════════════════════

    def extract_npc_personality_from_arc(self, arc: dict) -> list[dict]:
        """[V66] Arc에서 npc_personality_changes 추출 및 NPC 레지스트리 업데이트."""
        arc_no = arc.get("arc_no", 0)
        ep_start = arc.get("ep_start", 0)
        results = []

        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            changes = state_changes.get("npc_personality_changes", [])
            if isinstance(changes, list):
                for pc in changes:
                    if isinstance(pc, dict) and pc.get("name"):
                        name = str(pc["name"])
                        traits = str(pc.get("traits", ""))
                        motivation = str(pc.get("motivation", ""))
                        self.register_npc_info(
                            name, arc_no, personality_traits=traits, primary_motivation=motivation, episode_no=ep_start
                        )
                        results.append({"name": name, "traits": traits, "motivation": motivation, "arc_no": arc_no})
        return results

    def get_npc_personality_summary(self) -> str:
        """[V66] NPC 성격/동기 목록 → 프롬프트 주입용 문자열."""
        lines = []
        for name, info in self.tracker.npc_registry.items():
            traits = info.get("personality_traits", "")
            motivation = info.get("primary_motivation", "")
            if traits or motivation:
                parts = [f"  - {name}:"]
                if traits:
                    parts.append(f"성격={traits}")
                if motivation:
                    parts.append(f"동기={motivation}")
                lines.append(" ".join(parts))

        if not lines:
            return ""
        return "[V66] NPC 성격/동기 (급변 금지):\n" + "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] NPC-NPC 관계 추적
    # ═══════════════════════════════════════════════════════════════

    def extract_npc_npc_relationships_from_arc(self, arc: dict) -> list[dict]:
        """[V66] Arc에서 npc_npc_relationships 추출 및 레지스트리 업데이트."""
        arc_no = arc.get("arc_no", 0)
        results = []

        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            rels = state_changes.get("npc_npc_relationships", [])
            if isinstance(rels, list):
                for r in rels:
                    if isinstance(r, dict) and r.get("npc1") and r.get("npc2"):
                        npc1 = str(r["npc1"])
                        npc2 = str(r["npc2"])
                        relation = str(r.get("relation", ""))
                        self.register_npc_npc_relationship(npc1, npc2, relation, arc_no)
                        results.append({"npc1": npc1, "npc2": npc2, "relation": relation, "arc_no": arc_no})
        return results

    def register_npc_npc_relationship(self, npc1: str, npc2: str, relation: str, arc_no: int):
        """[V66] NPC 간 관계 등록. key=정렬된 (name1, name2) 튜플. 이력 보존."""
        key = tuple(sorted([npc1, npc2]))
        existing = self.tracker.npc_npc_relationships.get(key)
        new_entry = {"npc1": key[0], "npc2": key[1], "relation": relation, "arc_no": arc_no}
        # 이력 보존: prev_relation 필드로 이전 관계 기록
        if existing and existing.get("relation") != relation:
            new_entry["prev_relation"] = existing.get("relation", "")
            new_entry["prev_arc"] = existing.get("arc_no", 0)
        self.tracker.npc_npc_relationships[key] = new_entry
        # 최근 50쌍 한도 [V66 확장: 20→50]
        if len(self.tracker.npc_npc_relationships) > 50:
            oldest_key = next(iter(self.tracker.npc_npc_relationships))
            del self.tracker.npc_npc_relationships[oldest_key]
        # [Graph-Layer] DB 영속화 (메모리 50쌍 한도와 별개로 무제한)
        _db = getattr(self.tracker, "_db", None)
        if _db:
            try:
                _ep = getattr(self.tracker, "current_ep", 0) or 0
                _db.upsert_npc_relationship_edge(key[0], key[1], relation, arc_no, _ep)
            except Exception as _e:
                logging.debug("[StateTrackerNPC] npc_rel DB sync 실패 (비치명): %s", _e)

    def get_npc_npc_relationship_summary(self) -> str:
        """[V66] NPC-NPC 관계 목록 → 프롬프트 주입용 문자열."""
        if not self.tracker.npc_npc_relationships:
            return ""
        lines = ["[V66] NPC 간 관계 (변경 시 명시적 사유 필요):"]
        for info in self.tracker.npc_npc_relationships.values():
            lines.append(
                f"  - {info['npc1']} ↔ {info['npc2']}: {info.get('relation', '?')} (Arc {info.get('arc_no', '?')})"
            )
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] NPC 대화 스타일 레지스트리
    # ═══════════════════════════════════════════════════════════════

    def register_npc_dialogue_style(
        self, npc_name: str, speech_level: str = "", catchphrase: str = "", emotion_baseline: str = "", arc_no: int = 0
    ):
        """[V66] NPC 대화 스타일 등록."""
        if not npc_name:
            return
        existing = self.tracker.npc_dialogue_profiles.get(npc_name, {})
        entry = {
            "speech_level": speech_level or existing.get("speech_level", ""),
            "catchphrase": catchphrase or existing.get("catchphrase", ""),
            "emotion_baseline": emotion_baseline or existing.get("emotion_baseline", ""),
            "arc_no": arc_no,
        }
        self.tracker.npc_dialogue_profiles[npc_name] = entry

    def extract_npc_dialogue_styles_from_arc(self, arc: dict) -> list[dict]:
        """[V66] Arc의 state_changes에서 npc_personality_changes 기반 대화 스타일 추출."""
        arc_no = arc.get("arc_no", 0)
        results = []
        state_changes = arc.get("state_changes", {})
        if not isinstance(state_changes, dict):
            return results

        # [V70] 1순위: npc_dialogue_profiles 명시적 프로필 (LLM 직접 출력)
        _seen_names = set()
        dialogue_profiles = state_changes.get("npc_dialogue_profiles", [])
        if isinstance(dialogue_profiles, list):
            for dp in dialogue_profiles:
                if isinstance(dp, dict) and dp.get("name"):
                    name = str(dp["name"])
                    _seen_names.add(name)
                    self.register_npc_dialogue_style(
                        name,
                        speech_level=str(dp.get("speech_style", "")),
                        catchphrase=str(dp.get("catchphrase", "")),
                        arc_no=arc_no,
                    )
                    results.append({"name": name, "speech": dp.get("speech_style", ""), "emotion": ""})

        # 2순위: npc_personality_changes에서 대화 스타일 추론 (명시적 프로필 없는 NPC만)
        personality_changes = state_changes.get("npc_personality_changes", [])
        if isinstance(personality_changes, list):
            for pc in personality_changes:
                if isinstance(pc, dict) and pc.get("name"):
                    name = str(pc["name"])
                    if name in _seen_names:  # [V70] 명시적 프로필 우선
                        continue
                    traits = str(pc.get("traits", ""))
                    str(pc.get("motivation", ""))
                    # 성격에서 말투 추론
                    speech = ""
                    if any(k in traits for k in ["냉혹", "살벌", "무뚝뚝", "차가운"]):
                        speech = "극존칭_회피/짧은문장"
                    elif any(k in traits for k in ["쾌활", "활발", "수다", "장난"]):
                        speech = "비격식/긴문장"
                    elif any(k in traits for k in ["학자", "현인", "지식", "박식"]):
                        speech = "격식/고어체"
                    # 감정 기저선 추론
                    emotion = ""
                    if any(k in traits for k in ["냉혹", "무감", "차가운"]):
                        emotion = "무감정"
                    elif any(k in traits for k in ["분노", "복수"]):
                        emotion = "분노기저"
                    elif any(k in traits for k in ["쾌활", "밝은"]):
                        emotion = "긍정기저"

                    if speech or emotion:
                        self.register_npc_dialogue_style(
                            name,
                            speech_level=speech,
                            emotion_baseline=emotion,
                            arc_no=arc_no,
                        )
                        results.append({"name": name, "speech": speech, "emotion": emotion})
        return results

    def get_npc_dialogue_style_summary(self) -> str:
        """[V66] NPC 대화 스타일 -> 프롬프트 주입용 문자열."""
        if not self.tracker.npc_dialogue_profiles:
            return ""
        lines = ["[V66] NPC 대화 스타일 (말투 일관성 유지 필수):"]
        for name, info in self.tracker.npc_dialogue_profiles.items():
            parts = [f"  - {name}:"]
            if info.get("speech_level"):
                parts.append(f"말투={info['speech_level']}")
            if info.get("emotion_baseline"):
                parts.append(f"감정={info['emotion_baseline']}")
            if info.get("catchphrase"):
                parts.append(f'캐치프레이즈="{info["catchphrase"]}"')
            if len(parts) > 1:
                lines.append(" ".join(parts))
        if len(lines) <= 1:
            return ""
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] 동행자(Companion) 추적
    # ═══════════════════════════════════════════════════════════════

    def update_companions_from_arc(self, arc_data: dict) -> list[dict]:
        """
        [V66.1] Arc에서 동행자 변동 추출 및 current_companions 갱신.
        우선순위: state_changes["companion_changes"] > regex 폴백.

        Args:
            arc_data: Arc 데이터 (state_changes 또는 tactical_doc 포함)

        Returns:
            동행자 변동 목록 [{"name": ..., "action": "join|leave", ...}]
        """
        arc_no = arc_data.get("arc_no", 0)
        results = []

        # 1순위: state_changes.companion_changes 필드 직접 읽기
        state_changes = arc_data.get("state_changes", {})
        if isinstance(state_changes, dict):
            companion_changes = state_changes.get("companion_changes", [])
            if isinstance(companion_changes, list) and companion_changes:
                for cc in companion_changes:
                    if isinstance(cc, dict) and cc.get("name"):
                        name = str(cc["name"])
                        action = str(cc.get("action", "join"))
                        episode = cc.get("episode", arc_no)
                        reason = str(cc.get("reason", ""))
                        if name and len(name) >= 2:
                            self._apply_companion_change(name, action, arc_no, episode, reason)
                            results.append(
                                {"name": name, "action": action, "episode": episode, "reason": reason, "arc_no": arc_no}
                            )
                if results:
                    return results

        # 2순위: regex 폴백
        tactical = arc_data.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        if tactical:
            regex_changes = self._regex_extract_companion_changes(tactical)
            for rc in regex_changes:
                rc["arc_no"] = arc_no
                self._apply_companion_change(
                    rc["name"], rc["action"], arc_no, rc.get("episode", 0), rc.get("reason", "tactical_doc regex 추출")
                )
                results.append(rc)

        return results

    def _apply_companion_change(self, name: str, action: str, arc_no: int, episode: int = 0, reason: str = ""):
        """[V66.1] 동행자 상태 적용 (join/leave)."""
        companions = self.tracker.current_companions
        if action == "join":
            if not any(c.get("name") == name for c in companions):
                companions.append({"name": name, "joined_arc": arc_no, "joined_episode": episode, "reason": reason})
                logging.info(f"[V66.1] 동행자 합류: {name} (Arc {arc_no})")
        elif action == "leave":
            self.tracker.current_companions = [c for c in companions if c.get("name") != name]
            logging.info(f"[V66.1] 동행자 이탈: {name} (Arc {arc_no}, 사유: {reason})")

    def _regex_extract_companion_changes(self, tactical_doc: str) -> list[dict]:
        """
        [V66.1] tactical_doc에서 동행자 합류/이탈을 regex로 추출.
        state_changes.companion_changes가 비어있을 때 폴백으로 사용.

        Patterns: "NPC가 합류", "NPC와 동행", "NPC가 떠나", "NPC와 헤어지",
                  "NPC가 일행에서 빠지"
        """
        if not tactical_doc:
            return []

        changes = []
        seen = set()
        exclude_words = {"주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"}

        # [V66.1] C-2: module-level compiled patterns
        join_patterns = _RE_COMP_JOIN
        leave_patterns = _RE_COMP_LEAVE

        for pattern in join_patterns:
            for match in pattern.finditer(tactical_doc):
                npc = match.group(1).strip()
                if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                    seen.add(npc)
                    changes.append({"name": npc, "action": "join", "episode": 0, "reason": "tactical_doc regex 추출"})

        for pattern in leave_patterns:
            for match in pattern.finditer(tactical_doc):
                npc = match.group(1).strip()
                if npc not in exclude_words and len(npc) >= 2 and npc not in seen:
                    seen.add(npc)
                    changes.append({"name": npc, "action": "leave", "episode": 0, "reason": "tactical_doc regex 추출"})

        return changes

    def get_companion_summary(self) -> str:
        """
        [V66.1] 현재 동행자 목록 -> mandatory_context 주입용 문자열.
        동행자가 설명 없이 사라지거나 이미 떠난 동행자가 재등장하는 것 방지.

        Returns:
            포맷된 동행자 요약 문자열
        """
        if not self.tracker.current_companions:
            return ""

        names = [c.get("name", "?") for c in self.tracker.current_companions]
        header = f"[V66.1] 현재 동행자: {', '.join(names)}"
        lines = [header, "  (동행자 이탈/합류 시 반드시 명시적 사유 필요)"]
        for c in self.tracker.current_companions:
            name = c.get("name", "?")
            arc = c.get("joined_arc", "?")
            reason = c.get("reason", "")
            detail = f"  - {name} (Arc {arc}부터 동행"
            if reason:
                detail += f", 사유: {reason}"
            detail += ")"
            lines.append(detail)
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66.1] 주인공 감정 상태 추적
    # ═══════════════════════════════════════════════════════════════

    def update_protagonist_emotion(self, arc_no: int, episode: int, emotion: str, trigger: str):
        """
        [V66.1] 주인공 감정 상태 갱신.

        Args:
            arc_no: Arc 번호
            episode: 에피소드 번호
            emotion: 감정 상태 (예: "비통", "분노", "환희", "평온")
            trigger: 감정 유발 원인 (예: "부모 사망", "복수 성공")
        """
        if not emotion:
            return
        self.tracker.protagonist_emotion = {
            "emotion": emotion,
            "trigger": trigger,
            "arc_no": arc_no,
            "episode": episode,
        }
        logging.info(f"[V66.1] 주인공 감정 갱신: {emotion} (사유: {trigger}, Arc {arc_no} Ep{episode})")

    def extract_protagonist_emotion_from_arc(self, arc_data: dict) -> dict | None:
        """
        [V66.1] Arc에서 주인공 감정 상태 추출 및 갱신.
        우선순위: state_changes["protagonist_emotion"] > regex 폴백.

        Args:
            arc_data: Arc 데이터

        Returns:
            감정 정보 dict 또는 None
        """
        arc_no = arc_data.get("arc_no", 0)

        # 1순위: state_changes.protagonist_emotion 필드
        state_changes = arc_data.get("state_changes", {})
        if isinstance(state_changes, dict):
            pe = state_changes.get("protagonist_emotion", {})
            if isinstance(pe, list) and pe:  # [V70] list 타입 대응 (CLAUDE.md 스키마)
                pe = pe[0] if isinstance(pe[0], dict) else {}
            if isinstance(pe, dict) and pe.get("emotion"):
                emotion = str(pe["emotion"])
                trigger = str(pe.get("trigger", ""))
                episode = pe.get("episode", arc_no)
                self.update_protagonist_emotion(arc_no, episode, emotion, trigger)
                return {"emotion": emotion, "trigger": trigger, "episode": episode, "arc_no": arc_no}

        # 2순위: regex 폴백 (강한 감정 표현만)
        tactical = arc_data.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        if not tactical:
            return None

        # 강한 감정 패턴: 주인공 + 감정 표현
        emotion_map = {
            "분노": "분노",
            "격노": "분노",
            "격분": "분노",
            "비통": "비통",
            "슬픔": "비통",
            "통곡": "비통",
            "비탄": "비통",
            "절망": "절망",
            "좌절": "절망",
            "환희": "환희",
            "기쁨": "환희",
            "감격": "환희",
            "환호": "환희",
            "감동": "감동",
            "공포": "공포",
            "두려움": "공포",
            "경악": "공포",
            "결의": "결의",
            "각오": "결의",
            "결심": "결의",
        }

        # "주인공이 분노" / "비통에 잠기" / "격노하며" 패턴
        for keyword, normalized in emotion_map.items():
            # 주인공 관련 감정 패턴
            pattern = re.compile(
                r"(?:주인공|{name})[이가은는의]?\s*.{{0,20}}?{kw}".format(
                    name=re.escape("주인공"), kw=re.escape(keyword)
                )
            )
            if pattern.search(tactical):
                # trigger 추출 시도: 감정 주변 컨텍스트
                trigger_match = re.search(re.escape(keyword) + r".{0,30}?(?:에|으로|때문|인해)", tactical)
                trigger_text = trigger_match.group(0)[:30] if trigger_match else ""
                self.update_protagonist_emotion(arc_no, arc_no, normalized, trigger_text)
                return {"emotion": normalized, "trigger": trigger_text, "episode": arc_no, "arc_no": arc_no}

        return None

    def get_protagonist_emotion_summary(self) -> str:
        """
        [V66.1] 주인공 감정 상태 -> mandatory_context 주입용 문자열.
        감정의 급격한 전환 없이 자연스러운 전이를 유도.

        Returns:
            포맷된 감정 상태 요약 문자열
        """
        pe = self.tracker.protagonist_emotion
        if not pe or pe.get("emotion") == "평온" and not pe.get("trigger"):
            return ""

        emotion = pe.get("emotion", "평온")
        trigger = pe.get("trigger", "")
        arc_no = pe.get("arc_no", 0)

        lines = [
            f"[V66.1] 주인공 현재 감정: {emotion} (Arc {arc_no})",
        ]
        if trigger:
            lines.append(f"  원인: {trigger}")
        lines.append("  (감정 급변 금지 -- 전이 과정을 자연스럽게 묘사할 것)")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66.2] D-1,2,3: mandatory_context 주입용 summary 메서드
    # ═══════════════════════════════════════════════════════════════

    def get_relationship_changes_summary(self) -> str:
        """[V66.2] D-1: NPC-주인공 관계 현황 요약 -- mandatory_context 주입용."""
        lines = []
        for npc_name, npc_info in self.tracker.npc_registry.items():
            if npc_info.get("status") == "dead":
                continue
            rel = npc_info.get("relation_to_protag")
            if rel:
                lines.append(f"  - {npc_name}: {rel}")
        if not lines:
            return ""
        return "[V66.2] NPC-주인공 관계 현황 (관계 급변 금지):\n" + "\n".join(lines[:30])

    def get_npc_injury_summary(self) -> str:
        """[V66.2] D-2: NPC 부상 현황 요약 -- mandatory_context 주입용."""
        lines = []
        for npc_name, npc_info in self.tracker.npc_registry.items():
            injury = npc_info.get("injury")
            if injury and injury != "정상" and npc_info.get("status") == "alive":
                lines.append(f"  - {npc_name}: {injury}")
        if not lines:
            return ""
        return "[V66.2] NPC 부상 현황 (미치료 시 유지 필수):\n" + "\n".join(lines[:20])

    def get_npc_movement_summary(self) -> str:
        """[V66.2] D-3: NPC 위치 현황 요약 -- mandatory_context 주입용."""
        lines = []
        for npc_name, npc_info in self.tracker.npc_registry.items():
            loc = npc_info.get("location")
            if loc and npc_info.get("status") == "alive":
                lines.append(f"  - {npc_name}: {loc}")
        if not lines:
            return ""
        return "[V66.2] NPC 위치 현황 (위치 모순 금지):\n" + "\n".join(lines[:30])

    def get_protagonist_skills_summary(self) -> str:
        """
        [V66.2] C-2: 주인공 습득 무공/스킬 요약 -- mandatory_context 주입용.
        skill_acquisitions (Dict[skill_name, arc_no])에서 요약 생성.
        빈 리스트일 때 빈 문자열 반환 (mandatory_context에 빈 섹션 방지).
        """
        if not self.tracker.skill_acquisitions:
            return ""
        genre = getattr(self.tracker.preset_registry, "base_genre", "") or ""
        _, label = self._SKILL_LOG_LABEL.get(genre, ("\U0001f94b", "능력 습득"))
        lines = []
        for skill_name, arc_no in self.tracker.skill_acquisitions.items():
            lines.append(f"  - {skill_name} (Arc {arc_no})")
        header = f"[V66.2] 주인공 {label} 목록 (미습득 무공 사용 금지):"
        return header + "\n" + "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V69] NPC 레지스트리 LLM 정리
    # ═══════════════════════════════════════════════════════════════

    def cleanup_npc_registry_with_llm(self, arc_no: int) -> list[str]:
        """[V69] 5 Arc마다 npc_registry에서 일반명사 오탐을 LLM으로 정리.
        flash 모델 1회 호출. 실패 시 비차단.

        Args:
            arc_no: 현재 Arc 번호

        Returns:
            삭제된 이름 목록 (실패 시 빈 리스트)
        """
        try:
            # alive 상태인 NPC 이름 목록 추출 (dead는 건드리지 않음)
            alive_names = [name for name, info in self.tracker.npc_registry.items() if info.get("status") == "alive"]

            # 이름이 5개 미만이면 스킵 (정리 불필요)
            if len(alive_names) < 5:
                return []

            # LLM 클라이언트 확인
            if not self.tracker._llm_client:
                return []

            from google.genai import types as _types

            prompt = (
                f"다음은 소설의 NPC 레지스트리에서 '생존(alive)' 상태로 등록된 이름 목록입니다.\n"
                f"이름 목록: {json.dumps(alive_names, ensure_ascii=False)}\n\n"
                f"위 목록에서 실제 소설 등장인물 이름(고유명사)이 아닌 "
                f"일반 명사/단어를 골라주세요.\n"
                f"예: '선언', '미래', '저택', '사태', '세력', '후원자' 등은 일반 명사이므로 제거 대상입니다.\n"
                f"해당하는 단어가 없으면 빈 배열을 반환하세요.\n"
                f'JSON 형식: {{"remove": ["일반명사1", "일반명사2"]}}'
            )

            time.sleep(0.1)
            response = self.tracker._llm_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=_types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=512,
                    response_mime_type="application/json",
                ),
            )

            try:  # [V70] response.text ValueError 방어
                _resp_text = response.text
            except (ValueError, AttributeError):
                _resp_text = None
            if not _resp_text:
                logging.info("⚠️ [V69] NPC 정리 LLM 응답 비어있음, 건너뜀")
                return []
            result = json.loads(_resp_text)
            remove_list = []
            if isinstance(result, dict):
                remove_list = result.get("remove", [])
            elif isinstance(result, list):
                remove_list = result

            # remove 목록에 있는 이름을 npc_registry에서 삭제
            removed = []
            for name in remove_list:
                if isinstance(name, str) and name in self.tracker.npc_registry:
                    # alive 상태인 것만 삭제 (이중 확인)
                    if self.tracker.npc_registry[name].get("status") == "alive":
                        del self.tracker.npc_registry[name]
                        removed.append(name)

            if removed:
                logging.info(
                    f"      \U0001f9f9 [V69] NPC 레지스트리 LLM 정리 (Arc {arc_no}): "
                    f"{len(removed)}개 오탐 제거 - {removed}"
                )

            return removed

        except Exception as e:
            logging.warning(f"\u26a0\ufe0f [V69] NPC 레지스트리 LLM 정리 실패 (비차단): {str(e)[:80]}")
            return []
