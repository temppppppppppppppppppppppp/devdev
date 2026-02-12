import json
import logging
import re
from functools import lru_cache
from typing import List, Dict, Optional, Set
import time


class LoreManager:
    """
    [V44] 로어 관리자 (N+1 쿼리 최적화)

    Features:
    - LRU 캐시로 반복 쿼리 최적화
    - DB 레벨 LIKE 쿼리 필터링
    - 컨텍스트 길이 제한 (토큰 절약)
    - 배치 로딩 최적화
    """

    # [V44] 캐시 설정 - 점진적 노화 적용
    CACHE_SOFT_TTL_SECONDS = 300  # 5분: 소프트 TTL (경고 시작)
    CACHE_HARD_TTL_SECONDS = 600  # 10분: 하드 TTL (강제 무효화)
    MAX_CONTEXT_LENGTH = 2000  # 검색에 사용할 최대 컨텍스트 길이
    MAX_LORE_RESULTS = 10  # 최대 반환 로어 수

    def __init__(self, context) -> None:
        self.context = context
        self.db = context.db

        # 페르소나/말투는 성경 JSON의 정수를 그대로 상속
        _mb = self.context.master_bible if hasattr(self.context, 'master_bible') and self.context.master_bible else {}  # [V70] None 방어
        bible = _mb.get('MasterBible', _mb)
        self.assets = bible.get('AssetLibrary', bible.get('asset_library', {}))
        self.persona_desc = self.assets.get('Persona', "")
        self.speech_style = self.assets.get('SpeechStyle', self.assets.get('persona', {}))

        # [V44] 캐시 관리
        self._lore_cache: Dict[str, List[dict]] = {}
        self._cache_timestamp: float = 0
        self._all_lore_cache: Optional[List[dict]] = None
        self._lore_index: Dict[str, dict] = {}  # item_name -> lore 매핑

    def _invalidate_cache_if_stale(self) -> None:
        """[V44] TTL 기반 캐시 무효화 (점진적 노화)"""
        cache_age = time.time() - self._cache_timestamp

        # 하드 TTL 초과: 강제 무효화
        if cache_age > self.CACHE_HARD_TTL_SECONDS:
            self._lore_cache.clear()
            self._all_lore_cache = None
            self._lore_index.clear()
            self._cache_timestamp = time.time()
            return

        # 소프트 TTL 초과: 경고만 (점진적 노화)
        if cache_age > self.CACHE_SOFT_TTL_SECONDS:
            # 첫 경고 후 60초마다 로깅 (스팸 방지)
            if not hasattr(self, '_last_cache_warning') or \
               time.time() - self._last_cache_warning > 60:
                logging.info(f"⏰ [LoreManager] 캐시 노화 중 ({int(cache_age)}초 경과, {int(self.CACHE_HARD_TTL_SECONDS - cache_age)}초 후 갱신)")
                self._last_cache_warning = time.time()

    def refresh_cache(self) -> bool:
        """[V44] 수동 캐시 갱신 (프로액티브 리프레시용)"""
        self._lore_cache.clear()
        self._all_lore_cache = None
        self._lore_index.clear()
        self._cache_timestamp = time.time()
        self._build_lore_index()
        return True

    def _build_lore_index(self) -> None:
        """[V44] 로어 인덱스 구축 (O(1) 조회용)"""
        if self._lore_index:
            return

        all_lore = self._get_all_lore_cached()
        for lore in all_lore:
            item_name = lore.get('item', '')
            if item_name:
                # 정규화된 키로 저장
                normalized = item_name.replace(" ", "").lower()
                self._lore_index[normalized] = lore

    def _get_all_lore_cached(self) -> List[dict]:
        """[V44] 전체 로어 캐시 조회"""
        self._invalidate_cache_if_stale()

        if self._all_lore_cache is None:
            self._all_lore_cache = self.db.get_lore_list_by_category(None) or []
            self._cache_timestamp = time.time()

        return self._all_lore_cache

    def _extract_keywords_from_context(self, context_text: str) -> Set[str]:
        """[V44] 컨텍스트에서 키워드 추출"""
        if not context_text:
            return set()

        # 컨텍스트 길이 제한
        limited_context = context_text[:self.MAX_CONTEXT_LENGTH]

        # 한글 명사/고유명사 패턴 추출 (2-10자)
        korean_words = set(re.findall(r'[가-힣]{2,10}', limited_context))

        # 영문 단어 추출
        english_words = set(re.findall(r'[A-Za-z]{3,}', limited_context))

        return korean_words | english_words

    def get_v20_fact_sheet(self, context_text) -> str:
        """
        [V44] 맥락 매칭 로어 + 상세 페르소나 가이드 결합 (최적화)

        Args:
            context_text: 검색 컨텍스트

        Returns:
            str: FACT SHEET 문자열
        """
        if not context_text:
            return ""

        info = []

        # 1. 페르소나 지침 복구
        if self.persona_desc or self.speech_style:
            if isinstance(self.speech_style, dict):  # [V70] string 타입 방어
                tone = self.speech_style.get('tone', '격조 있는 무인')
                keywords = self.speech_style.get('Keywords', self.speech_style.get('words', []))
                if isinstance(keywords, list):
                    info.append(f"[페르소나 가이드]\n- 성격: {self.persona_desc}\n- 말투 톤: {tone}\n- 핵심 키워드: {', '.join(keywords)}")
                else:
                    info.append(f"[페르소나 가이드]\n- 성격: {self.persona_desc}\n- 말투 톤: {tone}")
            elif self.persona_desc:
                info.append(f"[페르소나 가이드]\n- 성격: {self.persona_desc}")

        # 2. [V44] 최적화된 로어 인출
        matched_lore = self.get_lore_by_keywords(context_text)
        for lore in matched_lore[:self.MAX_LORE_RESULTS]:
            item_name = lore.get('item', '')
            category = lore.get('category', '정보')
            description = lore.get('description', '')
            info.append(f"[{category}: {item_name}] {description}")

        return "\n[V20 절대 준수 FACT SHEET]\n" + "\n".join(info) if info else ""

    def get_lore_by_keywords(self, context_text: str) -> List[dict]:
        """
        [V44] 키워드 기반 로어 검색 (N+1 쿼리 최적화)

        Args:
            context_text: 검색 컨텍스트

        Returns:
            list: 매칭된 로어 목록
        """
        # 인덱스 구축 (최초 1회)
        self._build_lore_index()

        # 컨텍스트에서 키워드 추출
        keywords = self._extract_keywords_from_context(context_text)
        if not keywords:
            return []

        # 캐시 키 생성
        cache_key = hash(frozenset(keywords))
        if cache_key in self._lore_cache:
            return self._lore_cache[cache_key]

        # 키워드 매칭
        matched = []
        context_lower = context_text[:self.MAX_CONTEXT_LENGTH].lower()

        for normalized_name, lore in self._lore_index.items():
            item_name = lore.get('item', '')
            if item_name and item_name.lower() in context_lower:
                matched.append(lore)

        # 결과 캐싱
        self._lore_cache[cache_key] = matched
        return matched

    def get_lore_by_db_search(self, keyword: str) -> List[dict]:
        """
        [V44] DB LIKE 쿼리로 직접 검색

        Args:
            keyword: 검색 키워드

        Returns:
            list: 매칭된 로어 목록
        """
        if not keyword or len(keyword) < 2:
            return []

        try:
            # DB에서 LIKE 쿼리로 직접 필터링
            query = """
                SELECT category, item, description
                FROM encyclopedia  -- [V70] 올바른 테이블명 수정
                WHERE item LIKE ? OR description LIKE ?
                LIMIT ?
            """
            pattern = f"%{keyword}%"
            cursor = self.db.cursor.execute(
                query, (pattern, pattern, self.MAX_LORE_RESULTS)
            )
            results = []
            for row in cursor.fetchall():
                results.append({
                    'category': row[0],
                    'item': row[1],
                    'description': row[2]
                })
            return results
        except Exception:
            # 테이블이 없거나 쿼리 실패 시 폴백
            return self.get_lore_by_keywords(keyword)

    def update_v20_assets(self, new_lore_data) -> None:
        """
        [V44] 정규화 및 길이 비교 기반 DB 일괄 박제

        Args:
            new_lore_data: 새로운 로어 데이터 딕셔너리
        """
        if not new_lore_data:
            return

        # 캐시 무효화 (데이터 변경 시)
        self._invalidate_cache()

        # 현재 DB 상태와 비교하여 중복 방지 및 정보 보강(더 긴 설명 우선)
        current_db_lore = {
            l['item'].replace(" ", "").lower(): l
            for l in self._get_all_lore_cached()
        }
        lore_batch = []
        added_cnt, updated_cnt = 0, 0

        for category, items in new_lore_data.items():
            if not isinstance(items, dict):
                continue
            for name, desc in items.items():
                clean_name = name.replace(" ", "").lower()
                if clean_name in current_db_lore:
                    if len(str(desc)) > len(current_db_lore[clean_name].get('description', '')):
                        lore_batch.append((category, name, desc))
                        updated_cnt += 1
                else:
                    lore_batch.append((category, name, desc))
                    added_cnt += 1

        if lore_batch:
            self.db.update_lore_items_batch(lore_batch)
            # 캐시 재무효화 (DB 업데이트 후)
            self._invalidate_cache()
            logging.info(f"[Librarian] 설정 동기화 완료: 신규 {added_cnt}건 / 보강 {updated_cnt}건")

    def _invalidate_cache(self) -> None:
        """[V44] 캐시 강제 무효화"""
        self._lore_cache.clear()
        self._all_lore_cache = None
        self._lore_index.clear()
        self._cache_timestamp = 0

    def get_cache_stats(self) -> dict:
        """[V44] 캐시 상태 통계 반환"""
        return {
            "cache_entries": len(self._lore_cache),
            "index_entries": len(self._lore_index),
            "all_lore_cached": self._all_lore_cache is not None,
            "cache_age_seconds": time.time() - self._cache_timestamp if self._cache_timestamp > 0 else 0
        }

    def get_persona_prompt(self) -> str:
        """말투 예시(Suffix) 인출"""
        if not isinstance(self.speech_style, dict):  # [V70] string 타입 방어
            return ""
        suffix = self.speech_style.get('Suffix', self.speech_style.get('suffix', []))
        if isinstance(suffix, list) and suffix:
            return f"[🗣️ 말투 예시]: " + " / ".join(suffix)
        return ""

    # =================================================================
    # [V45] 아이템 자동 동기화 시스템
    # =================================================================

    def sync_equipment_to_encyclopedia(self, old_equipment: list, new_equipment: list, ep_num: int) -> dict:
        """
        [V45] HUD equipment 변경 사항을 encyclopedia에 자동 동기화

        Writer가 창작한 새 아이템을 encyclopedia에 등록하여
        다음 에피소드의 BLOCKING 검증에서 정상 인식되도록 함

        Args:
            old_equipment: 이전 HUD의 equipment 목록
            new_equipment: 업데이트된 HUD의 equipment 목록
            ep_num: 현재 에피소드 번호

        Returns:
            dict: {
                'added': [새로 등록된 아이템 목록],
                'already_exists': [이미 존재하던 아이템 목록]
            }
        """
        result = {'added': [], 'already_exists': []}

        # 입력 정규화
        old_set = self._normalize_equipment_list(old_equipment)
        new_set = self._normalize_equipment_list(new_equipment)

        # 새로 추가된 아이템 감지
        newly_added = new_set - old_set

        if not newly_added:
            return result

        # 현재 encyclopedia 상태 조회
        existing_items = {
            lore['item'].strip().lower()
            for lore in self.db.get_lore_list_by_category('item') or []
        }

        # 새 아이템 등록
        for item_name in newly_added:
            normalized_name = item_name.strip().lower()

            if normalized_name in existing_items or not item_name.strip():
                result['already_exists'].append(item_name)
                continue

            # encyclopedia에 등록
            description = f"제{ep_num}화에서 획득한 아이템. (Writer 창작)"
            self.db.update_lore_item('item', item_name.strip(), description)
            result['added'].append(item_name)

            logging.info(f"📦 [Item Sync] 새 아이템 등록: '{item_name}' (Ep.{ep_num})")

        # 캐시 무효화
        if result['added']:
            self._invalidate_cache()

        return result

    def _normalize_equipment_list(self, equipment) -> Set[str]:
        """
        [V45] equipment 데이터를 정규화된 Set으로 변환

        다양한 입력 형식 처리:
        - list: ["검", "갑옷"]
        - str: "검, 갑옷" 또는 "검"
        - dict: {"검": True, "갑옷": True}
        - None: 빈 set
        """
        if equipment is None:
            return set()

        if isinstance(equipment, list):
            return {str(item).strip() for item in equipment if item and str(item).strip()}

        if isinstance(equipment, str):
            # "현상 유지" 같은 특수값 무시
            if equipment.strip() in ['현상 유지', '없음', 'None', '']:
                return set()
            # 쉼표로 구분된 경우
            if ',' in equipment:
                return {item.strip() for item in equipment.split(',') if item.strip()}
            return {equipment.strip()} if equipment.strip() else set()

        if isinstance(equipment, dict):
            return {str(k).strip() for k, v in equipment.items() if k and v and str(k).strip()}

        return set()

    def build_validation_encyclopedia(self) -> dict:
        """
        [V45] BlockingValidator용 encyclopedia 딕셔너리 구성

        Returns:
            dict: {
                'items': [{'name': '검', 'status': 'active', ...}, ...],
                'npcs': [{'name': 'NPC명', 'status': 'alive/dead', ...}, ...],
                'locations': [{'name': '장소명', 'status': 'active/destroyed', ...}, ...]
            }
        """
        encyclopedia = {
            'items': [],
            'npcs': [],
            'locations': []
        }

        # DB에서 카테고리별 로어 조회
        all_lore = self.db.get_lore_list_by_category(None) or []

        for lore in all_lore:
            category = (lore.get('category') or '').lower()
            item_name = lore.get('item', '')
            description = lore.get('description', '')

            if not item_name:
                continue

            entry = {
                'name': item_name,
                'description': description,
                'status': self._extract_status_from_description(description)
            }

            # 카테고리별 분류
            if category in ['item', 'items', '아이템', '무기', '장비']:
                encyclopedia['items'].append(entry)
            elif category in ['npc', 'npcs', '인물', 'character', '캐릭터']:
                entry['aliases'] = self._extract_aliases(description)
                encyclopedia['npcs'].append(entry)
            elif category in ['location', 'locations', '장소', 'place', '지역']:
                encyclopedia['locations'].append(entry)

        return encyclopedia

    def _extract_status_from_description(self, description: str) -> str:
        """[V45] 설명에서 상태 추출 (기본값: active)"""
        if not description:
            return 'active'

        desc_lower = description.lower()

        # 사망/파괴 상태 감지
        death_keywords = ['사망', '죽음', '죽었', '처형', '살해', '전사', 'dead', 'deceased']
        destroy_keywords = ['파괴', '불탔', '무너졌', '소실', 'destroyed', '폐허']

        for kw in death_keywords:
            if kw in desc_lower:
                return 'dead'

        for kw in destroy_keywords:
            if kw in desc_lower:
                return 'destroyed'

        return 'active'

    def _extract_aliases(self, description: str) -> List[str]:
        """[V45] 설명에서 별칭 추출"""
        aliases = []

        # 괄호 안의 별칭 추출: "홍길동 (의적)"
        import re
        alias_matches = re.findall(r'\(([^)]+)\)', description)
        aliases.extend(alias_matches)

        # "별칭: X" 패턴
        alias_pattern = re.search(r'별칭[:\s]+([^\s,\.]+)', description)
        if alias_pattern:
            aliases.append(alias_pattern.group(1))

        return aliases