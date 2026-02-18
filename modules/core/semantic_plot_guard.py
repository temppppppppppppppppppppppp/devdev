"""
[V63] Semantic Plot Guard — 임베딩 기반 시맨틱 플롯 중복 감지

resolved_plots 임베딩 vs 새 tactical_doc 플롯명 임베딩 비교.
cosine similarity > 0.85 → WARNING 생성.

Usage:
    guard = SemanticPlotGuard(api_key="...")
    guard.index_resolved_plots(resolved_plots)
    warnings = guard.check_new_arc(tactical_doc, new_plot_names)
"""

import logging
import os
import re
import time

try:
    import numpy as np

    _NP_AVAILABLE = True
except ImportError:
    _NP_AVAILABLE = False

try:
    from google import genai

    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


def _cosine_similarity(a: list, b: list) -> float:
    """numpy 없이도 동작하는 코사인 유사도 계산"""
    if _NP_AVAILABLE:
        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        dot = np.dot(va, vb)
        norm = np.linalg.norm(va) * np.linalg.norm(vb)
        return float(dot / norm) if norm > 0 else 0.0
    else:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x**2 for x in a) ** 0.5
        norm_b = sum(x**2 for x in b) ** 0.5
        return dot / (norm_a * norm_b) if (norm_a * norm_b) > 0 else 0.0


class SemanticPlotGuard:
    """
    [V63] 시맨틱 플롯 중복 감지 가드

    기존 resolved_plots를 임베딩하여 저장하고,
    새 Arc의 플롯과 비교하여 유사도가 높은 경우 경고 생성.
    """

    SIMILARITY_THRESHOLD = 0.85
    EMBED_MODEL = "gemini-embedding-001"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._client = None
        self._resolved_embeddings: list[dict] = []  # [{"plot": str, "embedding": list}]
        self._resolved_keywords: list[dict] = []  # [C-1] 키워드 폴백 저장소
        self._init_done = False  # [V64.P4-fix] lazy init 플래그
        self._retry_count = 0
        self._max_retries = 1

        self._try_init_client()
        if not self._client:
            logging.info("ℹ️ [V63] SemanticPlotGuard: API 미사용 — 키워드 폴백 모드")

    def _try_init_client(self) -> None:
        """[V64.P4-fix] Client 초기화 시도 (실패해도 다음 사용 시 재시도)"""
        if self._client or not _GENAI_AVAILABLE or not self._api_key:
            return
        if self._retry_count > self._max_retries:
            return
        try:
            self._client = genai.Client(api_key=self._api_key)
            self._init_done = True
            self._retry_count = 0
        except Exception as e:
            logging.warning(f"⚠️ [V63] SemanticPlotGuard 초기화 실패: {str(e)[:80]}")
            self._client = None
            self._retry_count += 1

    def _embed_text(self, text: str) -> list | None:
        """단일 텍스트를 임베딩 벡터로 변환"""
        # [V64.P4-fix] lazy init: client가 없으면 한 번 더 시도
        if not self._client and self._retry_count <= self._max_retries:
            self._try_init_client()

        if not self._client or not text:
            return None
        try:
            clean = text.replace("\n", " ").strip()[:2000]
            res = self._client.models.embed_content(model=self.EMBED_MODEL, contents=clean)
            time.sleep(0.5)

            if hasattr(res, "embeddings") and res.embeddings:
                return res.embeddings[0].values
            elif hasattr(res, "embedding"):
                return res.embedding.values
        except Exception as e:
            logging.warning(f"⚠️ [V63] SemanticPlotGuard 임베딩 실패: {str(e)[:80]}")
        return None

    def index_resolved_plots(self, resolved_plots: list[dict]) -> int:
        """
        완결된 플롯들을 임베딩하여 인덱스에 저장.

        Args:
            resolved_plots: [{"plot": "인수전 완료", "resolution": "...", ...}, ...]

        Returns:
            성공적으로 인덱싱된 플롯 수
        """
        if not self._client:
            return self._index_keyword_fallback(resolved_plots)

        indexed = 0
        for rp in resolved_plots:
            plot_name = rp.get("plot", "")
            resolution = rp.get("resolution", "")
            text = f"{plot_name}: {resolution}" if resolution else plot_name

            if not text or len(text) < 3:
                continue

            # 이미 인덱싱된 플롯은 스킵
            if any(e["plot"] == plot_name for e in self._resolved_embeddings):
                continue

            emb = self._embed_text(text)
            if emb:
                self._resolved_embeddings.append({"plot": plot_name, "resolution": resolution, "embedding": emb})
                indexed += 1

        if indexed > 0:
            logging.info(
                f"📊 [V63] SemanticPlotGuard: {indexed}개 플롯 인덱싱 완료 (총 {len(self._resolved_embeddings)}개)"
            )
        return indexed

    def check_new_arc(self, tactical_doc: str = "", new_plot_names: list[str] = None) -> list[dict]:
        """
        새 Arc의 내용이 기존 resolved_plots와 시맨틱 중복인지 검사.

        Args:
            tactical_doc: 새 Arc의 tactical_doc 전문
            new_plot_names: 새 Arc에서 추출한 주요 플롯/갈등 이름 목록

        Returns:
            경고 목록: [{"new_plot": str, "similar_to": str, "similarity": float}, ...]
        """
        if tactical_doc and not isinstance(tactical_doc, str):
            tactical_doc = str(tactical_doc)

        if not self._client or not self._resolved_embeddings:
            # [C-1] 키워드 기반 폴백
            if self._resolved_keywords:
                return self._check_keyword_fallback(tactical_doc=tactical_doc, new_plot_names=new_plot_names)
            return []

        warnings = []
        texts_to_check = []

        # 플롯 이름이 주어진 경우
        if new_plot_names:
            texts_to_check.extend([(name, name) for name in new_plot_names if name])

        # tactical_doc에서 핵심 문장 추출 (제목 부분만)
        if tactical_doc and not texts_to_check:
            lines = tactical_doc.split("\n")
            for line in lines[:20]:
                stripped = line.strip()
                if stripped and ("제" in stripped and "화" in stripped):
                    # "제 N화: 제목" 패턴에서 제목 추출
                    parts = stripped.split(":", 1)
                    if len(parts) > 1:
                        texts_to_check.append((parts[1].strip()[:100], stripped[:100]))

        for check_text, display_text in texts_to_check:
            emb = self._embed_text(check_text)
            if not emb:
                continue

            for resolved in self._resolved_embeddings:
                sim = _cosine_similarity(emb, resolved["embedding"])
                if sim >= self.SIMILARITY_THRESHOLD:
                    warnings.append(
                        {"new_plot": display_text, "similar_to": resolved["plot"], "similarity": round(sim, 3)}
                    )

        return warnings

    def format_warnings(self, warnings: list[dict]) -> str:
        """경고를 프롬프트 주입 가능한 문자열로 포맷팅"""
        if not warnings:
            return ""

        lines = ["[V63] ⚠️ 시맨틱 플롯 중복 경고:"]
        for w in warnings:
            lines.append(
                f'  - "{w["new_plot"]}" ↔ 완결된 "{w["similar_to"]}" (유사도 {w["similarity"]:.1%}) → 차별화 필요'
            )
        return "\n".join(lines)

    def _index_keyword_fallback(self, resolved_plots: list[dict]) -> int:
        """[C-1] API 없을 때 키워드 기반 인덱싱."""
        indexed = 0
        for resolved_plot in resolved_plots:
            plot_name = resolved_plot.get("plot", "")
            resolution = resolved_plot.get("resolution", "")
            if not plot_name or len(plot_name) < 2:
                continue
            if any(item["plot"] == plot_name for item in self._resolved_keywords):
                continue

            keywords = self._extract_keywords(f"{plot_name} {resolution}")
            self._resolved_keywords.append(
                {
                    "plot": plot_name,
                    "resolution": resolution,
                    "keywords": keywords,
                }
            )
            indexed += 1

        if indexed > 0:
            logging.info(
                f"📊 [V63] SemanticPlotGuard(키워드): {indexed}개 플롯 인덱싱 완료 (총 {len(self._resolved_keywords)}개)"
            )
        return indexed

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        """[C-1] 텍스트에서 핵심 키워드 추출 (2글자 이상)."""
        words = re.findall(r"[가-힣]{2,}", text) + re.findall(r"[a-zA-Z]{3,}", text)
        stopwords = {"에서", "으로", "하고", "하는", "되는", "있는", "없는", "것이", "위해", "통해", "대한"}
        normalized = set()
        for word in words:
            token = SemanticPlotGuard._normalize_keyword(word)
            if token and token not in stopwords and len(token) >= 2:
                normalized.add(token)
        return normalized

    @staticmethod
    def _normalize_keyword(word: str) -> str:
        """[C-1] 조사/어미를 제거해 비교 가능한 키워드로 정규화."""
        token = word.strip().lower()
        if len(token) < 2:
            return token

        # 2글자 조사/격 조사
        for suffix in ("에서", "으로", "에게", "께서", "부터", "까지", "처럼", "보다"):
            if token.endswith(suffix) and len(token) > len(suffix) + 1:
                token = token[: -len(suffix)]
                break

        # 1글자 조사
        if len(token) >= 3 and token[-1] in "은는이가을를와과의도만":
            token = token[:-1]

        # 흔한 동사/어미 꼬리 제거 (인수하여 -> 인수, 처치했다 -> 처치)
        for ending in ("하였다", "했다", "한다", "하며", "하여", "하고", "됐다", "된다", "됨"):
            if token.endswith(ending) and len(token) > len(ending) + 1:
                token = token[: -len(ending)]
                break

        return token

    def _check_keyword_fallback(self, tactical_doc: str = "", new_plot_names: list[str] = None) -> list[dict]:
        """[C-1] 키워드 기반 중복 검사."""
        if not self._resolved_keywords:
            return []

        warnings = []
        check_texts = []
        if new_plot_names:
            check_texts.extend(new_plot_names)
        if tactical_doc:
            check_texts.append(tactical_doc[:3000])

        combined_text = " ".join(check_texts)
        new_keywords = self._extract_keywords(combined_text)
        if not new_keywords:
            return []

        for resolved in self._resolved_keywords:
            overlap = new_keywords & resolved["keywords"]
            if len(resolved["keywords"]) == 0:
                continue
            ratio = len(overlap) / len(resolved["keywords"])
            if ratio >= 0.5 and len(overlap) >= 2:
                warnings.append(
                    {
                        "new_plot": f"키워드 일치: {', '.join(sorted(overlap)[:5])}",
                        "similar_to": resolved["plot"],
                        "similarity": round(ratio, 3),
                    }
                )

        return warnings
