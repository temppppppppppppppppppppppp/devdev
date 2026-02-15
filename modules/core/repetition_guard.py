"""
[V40 Premium] 반복 구문 실시간 차단 시스템

AI가 동일한 표현을 과도하게 반복하는 것을 방지합니다.
최근 N화의 3-gram을 분석하여 금지 구문 목록을 생성하고,
새 원고에서 위반 사항을 검출합니다.
"""

import hashlib
import re
from collections import Counter


class RepetitionGuard:
    """
    반복 구문 차단 시스템

    Attributes:
        window_size: 분석할 이전 에피소드 수 (기본 5화)
        threshold: 동일 n-gram이 이 횟수 이상 나오면 차단 (기본 3회)
        banned_phrases: 금지 구문 집합
    """

    def __init__(self, window_size: int = 5, threshold: int = 3) -> None:
        """
        Args:
            window_size: 분석할 이전 에피소드 수
            threshold: 동일 n-gram이 이 횟수 이상 나오면 차단
        """
        self.window_size = window_size
        self.threshold = threshold
        self.banned_phrases = set()

    def build_banned_list(self, previous_manuscripts: list) -> set:
        """
        이전 원고들에서 과다 반복 구문 추출

        Args:
            previous_manuscripts: List of manuscript contents (최근 N화)

        Returns:
            Set of banned phrases
        """
        if not previous_manuscripts:
            return set()

        # 전체 텍스트 병합 (None 및 비문자열 필터링)
        filtered = [ms for ms in previous_manuscripts[-self.window_size :] if ms and isinstance(ms, str)]
        combined = "\n".join(filtered) if filtered else ""

        # 필터링 후 데이터가 없으면 빈 set 반환
        if not combined:
            return set()

        # 3-gram 추출 (한글/영문 단어 기준)
        words = re.findall(r"[\w가-힣]+", combined)

        if len(words) < 3:
            return set()

        trigrams = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]

        # 빈도 계산
        counter = Counter(trigrams)

        # threshold 이상 반복된 것들을 금지 목록에 추가
        # 단, 5자 이상의 의미 있는 구문만 (조사 조합 제외)
        self.banned_phrases = {
            phrase for phrase, count in counter.items() if count >= self.threshold and len(phrase) > 5
        }

        return self.banned_phrases

    def scan_manuscript(self, new_manuscript: str) -> tuple:
        """
        새 원고에서 금지 구문 스캔

        Args:
            new_manuscript: 검사할 원고 텍스트

        Returns:
            Tuple (violations: list, clean_score: float)
            - violations: 위반 구문 리스트
            - clean_score: 클린 점수 (0.0 - 1.0)
        """
        if not self.banned_phrases:
            return ([], 1.0)

        # 원고에서 3-gram 추출
        words = re.findall(r"[\w가-힣]+", new_manuscript)

        if len(words) < 3:
            return ([], 1.0)

        trigrams = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]

        violations = []
        seen_violations = set()  # 중복 보고 방지

        for i, trigram in enumerate(trigrams):
            if trigram in self.banned_phrases and trigram not in seen_violations:
                # 위반 문맥 추출 (앞뒤 5단어)
                context_start = max(0, i - 5)
                context_end = min(len(words), i + 8)
                context = " ".join(words[context_start:context_end])

                violations.append(
                    {
                        "phrase": trigram,
                        "position": i,
                        "context": f"...{context}...",
                        "frequency": self.threshold,  # 이전 화에서 몇 번 나왔는지
                    }
                )

                seen_violations.add(trigram)

        # 클린 점수 계산 (0.0 - 1.0)
        # 위반이 많을수록 점수 낮아짐
        if trigrams:
            clean_score = 1.0 - (len(violations) / len(trigrams))
            clean_score = max(0.0, min(1.0, clean_score))  # 0-1 범위 보장
        else:
            clean_score = 1.0

        return (violations, clean_score)

    def generate_correction_prompt(self, violations: list) -> str:
        """
        Director에게 전달할 교정 프롬프트 생성

        Args:
            violations: scan_manuscript()에서 반환된 위반 리스트

        Returns:
            교정 프롬프트 문자열
        """
        if not violations:
            return ""

        # 상위 5개만 보고 (너무 많으면 프롬프트 길어짐)
        top_violations = violations[:5]

        violation_report = "\n".join(
            [f'- "{v["phrase"]}" (위치: {v["position"]}, 문맥: {v["context"]})' for v in top_violations]
        )

        prompt = f"""
[🚨 REPETITION ALERT - 반복 구문 과다 사용]
아래 구문들은 최근 {self.window_size}화에서 {self.threshold}회 이상 반복 사용되었습니다.
새로운 표현으로 대체하십시오.

검출된 반복 구문 ({len(violations)}개):
{violation_report}

[교정 지침]
1. 동일한 의미를 전달하되, 다른 어휘와 구문을 사용하십시오.
2. 예시:
   - "차가운 눈빛을 보냈다" → "냉소를 머금었다" / "얼음장 같은 시선을 던졌다" / "서리 낀 눈빛으로 쳐다봤다"
   - "힘을 집중시켰다" → "기운을 모았다" / "내공을 한 곳에 응축했다" / "진기를 끌어올렸다"
3. 단순 유의어 교체가 아니라, 문장 구조 자체를 바꾸는 것을 권장합니다.

[중요]
반복 구문을 피하되, 설정과 사건의 핵심 내용은 반드시 유지하십시오.
"""

        return prompt

    def get_statistics(self) -> dict:
        """
        현재 금지 구문 통계 반환

        Returns:
            Dict with statistics
        """
        return {
            "total_banned_phrases": len(self.banned_phrases),
            "window_size": self.window_size,
            "threshold": self.threshold,
            "sample_phrases": list(self.banned_phrases)[:10] if self.banned_phrases else [],
        }

    # ── [Phase 3-B] 크로스 에피소드 문장 핑거프린팅 ──────────────

    # 한국어 종결어미 + 문장부호 기반 분리 패턴
    _SENTENCE_SPLIT_RE = re.compile(
        r"(?<=[다요죠함임음됨었았겠습니까])[.!?]\s+"
        r"|(?<=[.!?])\s+"
        r"|\n+"
    )

    @staticmethod
    def extract_sentence_fingerprints(
        manuscript: str,
        min_length: int = 15,
    ) -> list:
        """원고에서 정규화 문장 핑거프린트를 추출한다.

        Args:
            manuscript: 원고 전문
            min_length: 이 미만 글자수 문장은 제외

        Returns:
            [(sha256_hex, preview_50chars), ...] — 중복 제거됨
        """
        if not manuscript or not isinstance(manuscript, str):
            return []

        raw_sentences = RepetitionGuard._SENTENCE_SPLIT_RE.split(manuscript)

        seen_hashes = set()
        results = []
        for sent in raw_sentences:
            normalized = re.sub(r"\s+", " ", sent).strip()
            if len(normalized) < min_length:
                continue
            h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                preview = normalized[:50]
                results.append((h, preview))
        return results
