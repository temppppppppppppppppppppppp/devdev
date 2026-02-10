"""
[V64.P3] StateTracker NPC Sub-module
NPC 레지스트리 관리, 사망 추적, 무공/스킬 추적, 관계 변화, 부상/이동 추적.

StateTracker에서 NPC 관련 메서드만 분리.
모든 공유 상태는 self.tracker를 통해 접근.
"""

import json
import re
import time
from typing import Dict, List, Optional, Any


class StateTrackerNPC:
    """[V64.P3] NPC 관련 메서드 서브모듈"""

    # [V61.7.1] 장르별 능력 습득 로그 표시
    _SKILL_LOG_LABEL = {
        'wuxia': ('\U0001f94b', '무공 습득'),
        'hunter': ('\u2694\ufe0f', '스킬 습득'),
        'investment': ('\U0001f4c8', '핵심 지식 등록'),
        'fantasy': ('\u2728', '마법 습득'),
        'cooking': ('\U0001f468\u200d\U0001f373', '조리법 습득'),
        'actor': ('\U0001f3ac', '연기 습득'),
        'sports': ('\U0001f3c5', '기술 습득'),
        'medical': ('\U0001f52c', '의술 습득'),
    }

    def __init__(self, tracker):
        self.tracker = tracker  # back-reference to main StateTracker

    # ═══════════════════════════════════════════════════════════════
    # NPC 등록/정보
    # ═══════════════════════════════════════════════════════════════

    def register_npc_death(self, npc_name: str, death_arc: int, death_context: str = ""):
        """
        [V60.94] NPC 사망 등록

        Args:
            npc_name: NPC 이름
            death_arc: 사망한 Arc 번호
            death_context: 사망 맥락 (선택)
        """
        if npc_name not in self.tracker.npc_registry:
            self.tracker.npc_registry[npc_name] = {}

        self.tracker.npc_registry[npc_name].update({
            "status": "dead",
            "death_arc": death_arc,
            "death_context": death_context
        })
        print(f"      \U0001f480 [V60.94] NPC 사망 등록: {npc_name} (Arc {death_arc})")

    def register_npc_info(self, npc_name: str, arc_no: int, weapon: str = None, level: str = None,
                          personality_traits: str = None, primary_motivation: str = None):
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

        if weapon:
            npc["weapon"] = weapon
        if level:
            npc["level"] = level
        if personality_traits:
            npc["personality_traits"] = personality_traits
        if primary_motivation:
            npc["primary_motivation"] = primary_motivation

    def check_npc_changes(self, content: str, arc_no: int) -> List[dict]:
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
            r'([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))[을를으로]?\s*(?:들|휘두르|뽑)',
            r'([가-힣]{2,10})[의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))',
        ]

        # NPC 수준 패턴
        level_patterns = [
            r'([가-힣]{2,10})[이가은는]\s*(절대고수|화경|현경|초절정|일류|이류|삼류)',
            r'(절대고수|화경|현경|초절정|일류)[인의]\s*([가-힣]{2,10})',
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
                        warnings.append({
                            "npc_name": npc_name,
                            "change_type": "weapon",
                            "old_value": old_weapon,
                            "new_value": weapon,
                            "arc_no": arc_no,
                            "severity": "WARNING",
                            "reason": f"Arc {npc.get('last_arc', '?')}에서 '{old_weapon}' 사용 → Arc {arc_no}에서 '{weapon}' 사용"
                        })

        # 수준 변경 검사
        for pattern in level_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 패턴에 따라 순서가 다를 수 있음
                if match[0] in ['절대고수', '화경', '현경', '초절정', '일류', '이류', '삼류']:
                    level, npc_name = match[0], match[1]
                else:
                    npc_name, level = match[0], match[1]

                if npc_name and level and npc_name in self.tracker.npc_registry:
                    npc = self.tracker.npc_registry[npc_name]
                    old_level = npc.get("level")

                    if old_level and old_level != level:
                        warnings.append({
                            "npc_name": npc_name,
                            "change_type": "level",
                            "old_value": old_level,
                            "new_value": level,
                            "arc_no": arc_no,
                            "severity": "WARNING",
                            "reason": f"Arc {npc.get('last_arc', '?')}에서 '{old_level}' → Arc {arc_no}에서 '{level}'"
                        })

        return warnings

    def extract_npc_info_from_arc(self, arc: dict) -> List[dict]:
        """
        [V60.95] Arc의 tactical_doc에서 NPC 정보(무장, 수준) 추출 및 등록

        Args:
            arc: Arc 데이터

        Returns:
            추출된 NPC 정보 목록
        """
        arc_no = arc.get("arc_no", 0)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        extracted = []

        # NPC 무장 패턴
        weapon_patterns = [
            r'([가-힣]{2,10})[이가은는의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))',
        ]

        # NPC 수준 패턴
        level_patterns = [
            r'([가-힣]{2,10})[이가은는]\s*(절대고수|화경|현경|초절정|일류|이류|삼류)',
            r'(절대고수|화경|현경|초절정|일류)[인의]\s*([가-힣]{2,10})',
        ]

        # 제외할 일반 명사
        exclude_words = ['주인공', '적', '상대', '자신', '그', '그녀', '적수', '상대방']

        for pattern in weapon_patterns:
            matches = re.findall(pattern, tactical)
            for match in matches:
                npc_name, weapon = match[0], match[1]
                if npc_name not in exclude_words and len(npc_name) >= 2:
                    self.register_npc_info(npc_name, arc_no, weapon=weapon)
                    extracted.append({"name": npc_name, "weapon": weapon, "arc": arc_no})

        for pattern in level_patterns:
            matches = re.findall(pattern, tactical)
            for match in matches:
                if match[0] in ['절대고수', '화경', '현경', '초절정', '일류', '이류', '삼류']:
                    level, npc_name = match[0], match[1]
                else:
                    npc_name, level = match[0], match[1]

                if npc_name not in exclude_words and len(npc_name) >= 2:
                    self.register_npc_info(npc_name, arc_no, level=level)
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
            before = text[pos - 1] if pos > 0 else ''
            after_pos = pos + len(name)
            after = text[after_pos] if after_pos < len(text) else ''
            # [V63.4 P0] 앞쪽 한글 경계 검사
            if before and '\uAC00' <= before <= '\uD7A3':
                idx = pos + 1
                continue  # 앞에 한글 붙어있으면 오탐
            # [V63.4 P0] 뒤쪽 한글 경계 검사 — "강철"이 "강철무"에 매칭 방지
            if after and '\uAC00' <= after <= '\uD7A3':
                # 뒤에 조사/어미가 올 수 있으므로, 일반 한글 글자만 차단
                # 조사 패턴: 이/가/은/는/을/를/의/와/과/에/도/로/라/며 등
                ALLOWED_PARTICLES = set('이가은는을를의와과에도로서라며면고께한')
                if after not in ALLOWED_PARTICLES:
                    idx = pos + 1
                    continue  # 뒤에 일반 한글 붙어있으면 오탐
            return True  # 독립 매칭 확인
        return False

    def check_dead_npc_appearance(self, content: str, arc_no: int) -> List[dict]:
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
                            violations.append({
                                "npc_name": npc_name,
                                "death_arc": death_arc,
                                "current_arc": arc_no,
                                "severity": "CRITICAL",
                                "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 Arc {arc_no}에서 다시 등장"
                            })

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
            genre = getattr(self.tracker.preset_registry, 'base_genre', '') or ''
            emoji, label = self._SKILL_LOG_LABEL.get(genre, ('\U0001f94b', '능력 습득'))
            print(f"      {emoji} [V60.94] {label}: {skill_name} (Arc {arc_no})")

    def check_unlearned_skill_usage(self, content: str, arc_no: int) -> List[dict]:
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
            r'([가-힣]{2,10}(?:장|권|법|공|결|식|초))[을를]?\s*(?:시전|펼치|사용|발동)',
            r'([가-힣]{2,10}(?:심법|내공|기공))[으로]?\s*(?:운기|조식)',
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, content)
            for skill in matches:
                if skill and len(skill) >= 2:
                    # 등록된 무공인지 확인
                    if skill not in self.tracker.protagonist_skills:
                        # 새로운 무공일 수도 있으므로 INFO 레벨
                        suspicious.append({
                            "skill_name": skill,
                            "arc_no": arc_no,
                            "severity": "INFO",
                            "note": "습득 기록 없음 - 새 무공이거나 숨겨둔 패일 수 있음"
                        })

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
                dead_npcs.append({
                    "name": name,
                    "death_arc": info.get("death_arc", 0)
                })
            npc_info.append({
                "name": name,
                "weapon": info.get("weapon", ""),
                "level": info.get("level", ""),
                "status": info.get("status", "alive"),
                "last_arc": info.get("last_arc", 0)
            })

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
            "protagonist_items": protagonist_items
        }

    def merge_npc_registry(self, other: 'StateTracker'):
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
                    self.tracker.npc_registry[name] = info.copy()
                else:
                    existing.update(info)

        # 무공 목록 병합
        self.tracker.protagonist_skills.update(other.protagonist_skills)
        for skill, arc in other.skill_acquisitions.items():
            if skill not in self.tracker.skill_acquisitions:
                self.tracker.skill_acquisitions[skill] = arc

    # ═══════════════════════════════════════════════════════════════
    # state_changes 추출 (NPC 사망, 무공, 관계, 부상, 이동)
    # ═══════════════════════════════════════════════════════════════

    def extract_npc_deaths_from_arc(self, arc: dict) -> List[str]:
        """
        [V61] Arc에서 NPC 사망 추출 및 등록
        우선순위: state_changes 필드 > Regex 폴백

        Args:
            arc: Arc 데이터 (state_changes 또는 tactical_doc 포함)

        Returns:
            사망한 NPC 이름 목록
        """
        arc_no = arc.get("arc_no", 0)
        dead_npcs = []

        # [V61] 1순위: state_changes 필드 직접 읽기 (정확도 ~98%)
        state_changes = arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            npc_deaths = state_changes.get("npc_deaths", [])
            if isinstance(npc_deaths, list) and npc_deaths:
                for death in npc_deaths:
                    if isinstance(death, dict):
                        npc_name = death.get("name", "")
                        episode = death.get("episode", arc_no)
                        cause = death.get("cause", "state_changes에서 추출")
                        if npc_name and len(npc_name) >= 2:
                            self.register_npc_death(npc_name, arc_no, f"Arc {arc_no} Ep {episode}: {cause}")
                            dead_npcs.append(npc_name)
                    elif isinstance(death, str) and len(death) >= 2:
                        # 단순 문자열 형태도 지원
                        self.register_npc_death(death, arc_no, f"Arc {arc_no} state_changes에서 추출")
                        dead_npcs.append(death)
                if dead_npcs:
                    return list(set(dead_npcs))

        # [V61] 2순위: Regex 폴백 (하위 호환 + 보조)
        tactical = arc.get("tactical_doc", "")
        if isinstance(tactical, dict):
            tactical = "\n".join(str(v) for v in tactical.values() if v)

        death_patterns = [
            r'([가-힣]{2,10})[이가을를]\s*(?:죽이|처단|살해|베어|제거|처형|사살)',
            r'([가-힣]{2,10})[이가은는]\s*(?:죽|사망|전사|명을\s*다|숨을\s*거두|운명)',
            r'([가-힣]{2,10})[의]\s*(?:죽음|최후|사망|전사)',
            r'([가-힣]{2,10})[을를]\s*(?:끝장|마무리|처리)',
        ]

        exclude_words = ['주인공', '적', '상대', '자신', '목숨', '생명', '원수', '원한', '일격', '공격', '반격']

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
                self.register_npc_death(npc_name, arc_no, f"Arc {arc_no} tactical_doc Regex+LLM검증")
                dead_npcs.append(npc_name)

        return list(set(dead_npcs))

    def _verify_npc_names_llm(self, candidates: List[str], context: str, arc_no: int) -> List[str]:
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
            result = json.loads(response.text)
            if isinstance(result, list):
                verified = [name for name in result if isinstance(name, str) and name in candidates]
                filtered = set(candidates) - set(verified)
                if filtered:
                    print(f"      \U0001f50d [V62.5] NPC 오탐 필터링: {filtered} (LLM 검증으로 제외)")
                return verified
        except Exception as e:
            print(f"      \u26a0\ufe0f [V62.5] NPC LLM 검증 실패, regex 결과 그대로 사용: {str(e)[:60]}")

        return candidates

    def extract_skill_acquisitions_from_arc(self, arc: dict) -> List[str]:
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
                        episode = skill.get("episode", arc_no)
                        source = skill.get("source", "state_changes에서 추출")
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
            r'([가-힣]{2,10}(?:장|권|법|공|결|식|초|심법))[을를]?\s*(?:습득|익히|배우|터득|깨우치|전수받)',
            r'([가-힣]{2,10}(?:장|권|법|공|결|식|초|심법))[의]?\s*(?:오의|진수|비전)[을를]?\s*(?:깨달|얻)',
        ]

        for pattern in learn_patterns:
            matches = re.findall(pattern, tactical)
            for skill_name in matches:
                if skill_name and len(skill_name) >= 2:
                    self.register_protagonist_skill(skill_name, arc_no)
                    learned_skills.append(skill_name)

        return list(set(learned_skills))

    def extract_relationship_changes_from_arc(self, arc: dict) -> List[Dict]:
        """
        [V61] Arc에서 관계 변화 추출 (state_changes 필드 전용)

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
                            changes.append({
                                "npc": npc,
                                "from": from_rel,
                                "to": to_rel,
                                "episode": episode,
                                "arc_no": arc_no
                            })
                            # NPC registry에도 반영
                            if npc in self.tracker.npc_registry:
                                self.tracker.npc_registry[npc]["relation_to_protag"] = to_rel
                                self.tracker.npc_registry[npc]["last_arc"] = arc_no

        return changes

    def extract_npc_injuries_from_arc(self, arc: dict) -> List[Dict]:
        """
        [V63] Arc에서 NPC 부상 상태 추출 및 레지스트리 반영.
        state_changes.npc_injuries 필드에서 직접 읽기.
        새 필드가 없으면 빈 리스트 반환 (하위 호환).
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
                            injuries.append({
                                "name": npc_name,
                                "episode": entry.get("episode", arc_no),
                                "state": state,
                                "cause": entry.get("cause", ""),
                                "arc_no": arc_no
                            })
                            # NPC registry 반영
                            if npc_name in self.tracker.npc_registry:
                                self.tracker.npc_registry[npc_name]["injury"] = state
                                self.tracker.npc_registry[npc_name]["last_arc"] = arc_no
        return injuries

    def extract_npc_movements_from_arc(self, arc: dict) -> List[Dict]:
        """
        [V63] Arc에서 NPC 이동 추출 및 레지스트리 반영.
        state_changes.npc_movements 필드에서 직접 읽기.
        새 필드가 없으면 빈 리스트 반환 (하위 호환).
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
                            movements.append({
                                "name": npc_name,
                                "episode": entry.get("episode", arc_no),
                                "from": entry.get("from", ""),
                                "to": to_loc,
                                "arc_no": arc_no
                            })
                            # NPC registry 반영
                            if npc_name in self.tracker.npc_registry:
                                self.tracker.npc_registry[npc_name]["location"] = to_loc
                                self.tracker.npc_registry[npc_name]["last_arc"] = arc_no
        return movements

    # ═══════════════════════════════════════════════════════════════
    # Stage 3/4: Blueprint/Manuscript 내 죽은 NPC 검사
    # ═══════════════════════════════════════════════════════════════

    def check_dead_npc_in_blueprint(self, blueprint: dict, ep_num: int, arc_no: int = 0) -> List[dict]:
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
        if isinstance(scenes, dict):
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
                        f"{npc_name}의 죽음", f"{npc_name}을 떠올", f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}", f"죽은 {npc_name}", f"{npc_name}의 유언",
                        f"{npc_name}의 무덤", f"{npc_name}의 원혼", f"{npc_name}의 유품",
                        f"{npc_name}을 추모", f"{npc_name}의 복수"
                    ]
                    is_flashback = any(pattern in content for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장 패턴 검사
                        action_patterns = [
                            f"{npc_name}이 ", f"{npc_name}가 ", f"{npc_name}은 ", f"{npc_name}는 ",
                            f'"{npc_name}', f"{npc_name}와 ", f"{npc_name}과 ",
                            f"{npc_name}의 검", f"{npc_name}의 공격", f"{npc_name}에게"
                        ]
                        if any(pattern in content for pattern in action_patterns):
                            violations.append({
                                "npc_name": npc_name,
                                "death_arc": death_arc,
                                "current_ep": ep_num,
                                "current_arc": arc_no,
                                "severity": "CRITICAL",
                                "context": "blueprint",
                                "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 제{ep_num}화(Arc {arc_no}) Blueprint에서 다시 등장"
                            })

        return violations

    def check_dead_npc_in_manuscript(self, manuscript: str, ep_num: int, arc_no: int = 0) -> List[dict]:
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
                        f"{npc_name}의 죽음", f"{npc_name}을 떠올", f"{npc_name}를 떠올",
                        f"고인이 된 {npc_name}", f"죽은 {npc_name}", f"{npc_name}의 유언",
                        f"{npc_name}의 무덤", f"{npc_name}의 원혼", f"{npc_name}의 유품",
                        f"{npc_name}을 추모", f"{npc_name}의 복수", f"{npc_name}의 이름",
                        f"{npc_name}처럼", f"{npc_name}같은", f"과거의 {npc_name}",
                        f"{npc_name}의 기억", f"{npc_name}의 영혼"
                    ]
                    is_flashback = any(pattern in manuscript for pattern in flashback_patterns)

                    if not is_flashback:
                        # 실제 등장 패턴 (대화, 행동)
                        action_patterns = [
                            f"{npc_name}이 말", f"{npc_name}가 말", f"{npc_name}이 대답",
                            f"{npc_name}가 대답", f"{npc_name}은 고개", f"{npc_name}는 고개",
                            f'"{npc_name}', f"{npc_name}이 검", f"{npc_name}가 검",
                            f"{npc_name}의 손", f"{npc_name}이 다가", f"{npc_name}가 다가"
                        ]
                        if any(pattern in manuscript for pattern in action_patterns):
                            violations.append({
                                "npc_name": npc_name,
                                "death_arc": death_arc,
                                "current_ep": ep_num,
                                "current_arc": arc_no,
                                "severity": "CRITICAL",
                                "context": "manuscript",
                                "reason": f"Arc {death_arc}에서 사망한 '{npc_name}'이 제{ep_num}화(Arc {arc_no}) 원고에서 살아있는 것처럼 등장"
                            })

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

        lines = [
            "\U0001f6a8 [사망 NPC 목록 - 절대 살아있는 것처럼 등장시키지 말 것]",
            *dead_npcs,
            ""
        ]
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # [V66] NPC 성격/동기 baseline
    # ═══════════════════════════════════════════════════════════════

    def extract_npc_personality_from_arc(self, arc: dict) -> List[Dict]:
        """[V66] Arc에서 npc_personality_changes 추출 및 NPC 레지스트리 업데이트."""
        arc_no = arc.get("arc_no", 0)
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
                            name, arc_no,
                            personality_traits=traits,
                            primary_motivation=motivation
                        )
                        results.append({
                            "name": name, "traits": traits,
                            "motivation": motivation, "arc_no": arc_no
                        })
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

    def extract_npc_npc_relationships_from_arc(self, arc: dict) -> List[Dict]:
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
                        results.append({
                            "npc1": npc1, "npc2": npc2,
                            "relation": relation, "arc_no": arc_no
                        })
        return results

    def register_npc_npc_relationship(self, npc1: str, npc2: str, relation: str, arc_no: int):
        """[V66] NPC 간 관계 등록. key=정렬된 (name1, name2) 튜플. 이력 보존."""
        key = tuple(sorted([npc1, npc2]))
        existing = self.tracker.npc_npc_relationships.get(key)
        new_entry = {
            "npc1": key[0], "npc2": key[1],
            "relation": relation, "arc_no": arc_no
        }
        # 이력 보존: prev_relation 필드로 이전 관계 기록
        if existing and existing.get("relation") != relation:
            new_entry["prev_relation"] = existing.get("relation", "")
            new_entry["prev_arc"] = existing.get("arc_no", 0)
        self.tracker.npc_npc_relationships[key] = new_entry
        # 최근 50쌍 한도 [V66 확장: 20→50]
        if len(self.tracker.npc_npc_relationships) > 50:
            oldest_key = next(iter(self.tracker.npc_npc_relationships))
            del self.tracker.npc_npc_relationships[oldest_key]

    def get_npc_npc_relationship_summary(self) -> str:
        """[V66] NPC-NPC 관계 목록 → 프롬프트 주입용 문자열."""
        if not self.tracker.npc_npc_relationships:
            return ""
        lines = ["[V66] NPC 간 관계 (변경 시 명시적 사유 필요):"]
        for info in self.tracker.npc_npc_relationships.values():
            lines.append(
                f"  - {info['npc1']} ↔ {info['npc2']}: "
                f"{info.get('relation', '?')} (Arc {info.get('arc_no', '?')})"
            )
        return "\n".join(lines)
