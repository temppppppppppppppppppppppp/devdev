"""
[V54.1] Semantic Cache (의미론적 캐시)
유사한 요청에 대해 캐시된 응답 재사용

핵심: 정확히 같은 요청이 아니어도 의미적으로 유사하면 캐시 활용

원리:
1. 요청의 핵심 특징 추출 (해시 생성)
2. 유사 요청 검색 (임베딩 or 키워드)
3. 캐시 히트 시 저장된 응답 반환
4. 미스 시 새로 생성 후 캐시 저장

비용: $0 (Python 휴리스틱)
효과: API 호출 20-30% 감소

사용:
    cache = SemanticCache(max_size=1000)

    # 캐시 조회
    cached = cache.get(request_type, context_hash)
    if cached:
        return cached

    # 새로 생성 후 저장
    result = generate_new()
    cache.set(request_type, context_hash, result)
"""

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    """캐시 엔트리"""

    key: str
    value: Any
    context_signature: str
    created_at: float
    hit_count: int = 0
    last_hit: float = 0


@dataclass
class CacheStats:
    """캐시 통계"""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    bytes_saved: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


class SemanticCache:
    """의미론적 캐시 시스템"""

    # 캐시 가능한 요청 타입
    CACHEABLE_TYPES = {
        "blueprint_structure",  # 블루프린트 구조 (씬 배치)
        "scene_template",  # 씬 템플릿
        "character_reaction",  # 캐릭터 반응 패턴
        "dialogue_style",  # 대화 스타일
        "description_pattern",  # 묘사 패턴
        "transition_phrase",  # 전환 문구
        "arc_tactical",  # [V60.26] Arc 전술 문서 (유사 상황 재활용)
        "arc_constraint",  # [V60.26] Arc 제약 조건 (Preflight 결과)
    }

    # TTL (초)
    DEFAULT_TTL = 3600 * 24  # 24시간

    def __init__(self, max_size: int = 500, ttl: int = None, similarity_threshold: float = 0.85):
        """
        Args:
            max_size: 최대 캐시 엔트리 수
            ttl: Time-to-live (초)
            similarity_threshold: 유사도 임계값 (0-1)
        """
        self.max_size = max_size
        self.ttl = ttl or self.DEFAULT_TTL
        self.similarity_threshold = similarity_threshold

        # LRU 캐시 (OrderedDict 사용)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 컨텍스트 시그니처 인덱스 (빠른 유사 검색용)
        self._signature_index: dict[str, list[str]] = {}

        # 통계
        self.stats = CacheStats()

        self._lock = threading.Lock()
        self.enabled = True

    def _generate_context_hash(self, context: dict[str, Any]) -> str:
        """컨텍스트에서 해시 생성"""
        # 핵심 필드만 추출
        key_fields = [
            context.get("ep_num", ""),
            context.get("arc_num", ""),
            context.get("scene_type", ""),
            context.get("character", ""),
            context.get("emotion", ""),
            context.get("action_type", ""),
        ]

        # 정렬된 문자열로 변환
        key_string = "|".join(str(f) for f in key_fields if f)

        return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()[:16]

    def _generate_signature(self, context: dict[str, Any]) -> str:
        """컨텍스트 시그니처 생성 (유사도 비교용)"""
        # 의미적으로 중요한 키워드 추출
        keywords = []

        # 씬 타입
        if scene_type := context.get("scene_type"):
            keywords.append(f"scene:{scene_type}")

        # 감정
        if emotion := context.get("emotion"):
            keywords.append(f"emo:{emotion}")

        # 액션 타입
        if action := context.get("action_type"):
            keywords.append(f"act:{action}")

        # 캐릭터 관계
        if relation := context.get("relation"):
            keywords.append(f"rel:{relation}")

        # 장소 타입 (구체적 장소가 아닌 유형)
        if location := context.get("location"):
            loc_type = self._extract_location_type(location)
            keywords.append(f"loc:{loc_type}")

        return "|".join(sorted(keywords))

    def _extract_location_type(self, location: str) -> str:
        """장소에서 유형 추출"""
        location_types = {
            "객잔": "inn",
            "주막": "inn",
            "여관": "inn",
            "산": "mountain",
            "봉": "mountain",
            "령": "mountain",
            "강": "river",
            "호수": "river",
            "계곡": "river",
            "성": "castle",
            "궁": "castle",
            "부": "castle",
            "동굴": "cave",
            "굴": "cave",
            "숲": "forest",
            "림": "forest",
            "마을": "village",
            "촌": "village",
            "도시": "city",
            "성": "city",
        }

        for keyword, loc_type in location_types.items():
            if keyword in location:
                return loc_type

        return "unknown"

    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """두 시그니처의 유사도 계산 (Jaccard)"""
        if not sig1 or not sig2:
            return 0.0

        set1 = set(sig1.split("|"))
        set2 = set(sig2.split("|"))

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def get(self, request_type: str, context: dict[str, Any], exact_match: bool = False) -> Any | None:
        """
        캐시 조회

        Args:
            request_type: 요청 타입
            context: 컨텍스트
            exact_match: True면 정확히 일치하는 것만

        Returns:
            캐시된 값 또는 None
        """
        with self._lock:
            if not self.enabled:
                return None

            self.stats.total_requests += 1

            # 캐시 키 생성
            context_hash = self._generate_context_hash(context)
            cache_key = f"{request_type}:{context_hash}"

            # 정확한 매칭 시도
            if cache_key in self._cache:
                entry = self._cache[cache_key]

                # TTL 체크
                if time.time() - entry.created_at > self.ttl:
                    self._evict(cache_key)
                else:
                    # 히트 업데이트
                    entry.hit_count += 1
                    entry.last_hit = time.time()

                    # LRU 업데이트 (맨 뒤로)
                    self._cache.move_to_end(cache_key)

                    self.stats.cache_hits += 1
                    return entry.value

            # 유사 매칭 시도 (exact_match가 False일 때)
            if not exact_match:
                similar = self._find_similar(request_type, context)
                if similar:
                    self.stats.cache_hits += 1
                    return similar

            self.stats.cache_misses += 1
            return None

    def _find_similar(self, request_type: str, context: dict[str, Any]) -> Any | None:
        """유사한 캐시 엔트리 검색"""
        signature = self._generate_signature(context)

        if not signature:
            return None

        # 같은 request_type의 엔트리들만 검색
        candidates = []
        for key, entry in self._cache.items():
            if key.startswith(f"{request_type}:"):
                similarity = self._calculate_similarity(signature, entry.context_signature)
                if similarity >= self.similarity_threshold:
                    candidates.append((similarity, entry))

        if not candidates:
            return None

        # 가장 유사한 것 반환
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_entry = candidates[0][1]

        # 히트 업데이트
        best_entry.hit_count += 1
        best_entry.last_hit = time.time()

        return best_entry.value

    def set(self, request_type: str, context: dict[str, Any], value: Any, metadata: dict[str, Any] = None) -> str:
        """
        캐시 저장

        Args:
            request_type: 요청 타입
            context: 컨텍스트
            value: 저장할 값
            metadata: 추가 메타데이터

        Returns:
            캐시 키
        """
        with self._lock:
            if not self.enabled:
                return ""

            # 캐시 키 생성
            context_hash = self._generate_context_hash(context)
            cache_key = f"{request_type}:{context_hash}"

            # 시그니처 생성
            signature = self._generate_signature(context)

            # 용량 체크 및 LRU 정리
            while len(self._cache) >= self.max_size:
                self._evict_lru()

            # 엔트리 생성
            entry = CacheEntry(
                key=cache_key,
                value=value,
                context_signature=signature,
                created_at=time.time(),
                hit_count=0,
                last_hit=time.time(),
            )

            # [V70] 기존 엔트리가 있으면 시그니처 인덱스에서 먼저 제거
            if cache_key in self._cache:
                old_entry = self._cache[cache_key]
                if old_entry.context_signature in self._signature_index:
                    sig_list = self._signature_index[old_entry.context_signature]
                    if cache_key in sig_list:
                        sig_list.remove(cache_key)

            self._cache[cache_key] = entry

            # 시그니처 인덱스 업데이트
            if signature:
                if signature not in self._signature_index:
                    self._signature_index[signature] = []
                self._signature_index[signature].append(cache_key)

            return cache_key

    def _evict(self, key: str):
        """특정 키 제거"""
        if key in self._cache:
            entry = self._cache.pop(key)

            # 시그니처 인덱스에서도 제거
            if entry.context_signature in self._signature_index:
                sig_list = self._signature_index[entry.context_signature]
                if key in sig_list:
                    sig_list.remove(key)

    def _evict_lru(self) -> None:
        """LRU 정책으로 가장 오래된 것 제거"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            self._evict(oldest_key)

    def invalidate(self, pattern: str = None):
        """
        캐시 무효화

        Args:
            pattern: 패턴 (없으면 전체 무효화)
        """
        with self._lock:
            if pattern is None:
                self._cache.clear()
                self._signature_index.clear()
            else:
                # 패턴 매칭하는 것들 제거
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_remove:
                    self._evict(key)

    def get_stats(self) -> dict[str, Any]:
        """통계 반환"""
        with self._lock:
            return {
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "hit_rate": f"{self.stats.hit_rate:.1%}",
                "cache_size": len(self._cache),
                "max_size": self.max_size,
            }

    def get_summary(self) -> str:
        """요약 문자열"""
        stats = self.get_stats()
        return (
            f"[V54.1 Semantic Cache]\n"
            f"  히트율: {stats['hit_rate']}\n"
            f"  히트: {stats['cache_hits']} / 요청: {stats['total_requests']}\n"
            f"  캐시: {stats['cache_size']}/{stats['max_size']}"
        )


class BlueprintCache(SemanticCache):
    """블루프린트 전용 캐시"""

    def __init__(self, max_size: int = 100):
        super().__init__(max_size=max_size, similarity_threshold=0.8)

    def cache_scene_structure(self, scene_type: str, emotion_arc: str, structure: dict[str, Any]) -> str:
        """씬 구조 캐시"""
        context = {"scene_type": scene_type, "emotion": emotion_arc}
        return self.set("scene_structure", context, structure)

    def get_scene_structure(self, scene_type: str, emotion_arc: str) -> dict[str, Any] | None:
        """씬 구조 조회"""
        context = {"scene_type": scene_type, "emotion": emotion_arc}
        return self.get("scene_structure", context)


class DescriptionCache(SemanticCache):
    """묘사 패턴 캐시"""

    def __init__(self, max_size: int = 200):
        super().__init__(max_size=max_size, similarity_threshold=0.75)

    def cache_description(self, desc_type: str, subject: str, description: str) -> str:
        """묘사 캐시"""
        context = {"action_type": desc_type, "character": subject}
        return self.set("description", context, description)

    def get_similar_description(self, desc_type: str, subject: str) -> str | None:
        """유사 묘사 조회"""
        context = {"action_type": desc_type, "character": subject}
        return self.get("description", context)
