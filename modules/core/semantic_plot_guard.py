"""
[V63] Semantic Plot Guard — ChromaDB 임베딩 기반 시맨틱 플롯 중복 감지

resolved_plots 임베딩 vs 새 tactical_doc 플롯명 임베딩 비교.
cosine similarity > 0.85 → WARNING 생성.

Usage:
    guard = SemanticPlotGuard(api_key="...")
    guard.index_resolved_plots(resolved_plots)
    warnings = guard.check_new_arc(tactical_doc, new_plot_names)
"""

import time
import logging
import os
from typing import List, Dict, Optional

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
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
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
        self._resolved_embeddings: List[Dict] = []  # [{"plot": str, "embedding": list}]

        if _GENAI_AVAILABLE and self._api_key:
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception:
                self._client = None

    def _embed_text(self, text: str) -> Optional[list]:
        """단일 텍스트를 임베딩 벡터로 변환"""
        if not self._client or not text:
            return None
        try:
            clean = text.replace("\n", " ").strip()[:2000]
            res = self._client.models.embed_content(
                model=self.EMBED_MODEL,
                contents=clean
            )
            time.sleep(0.5)

            if hasattr(res, 'embeddings') and res.embeddings:
                return res.embeddings[0].values
            elif hasattr(res, 'embedding'):
                return res.embedding.values
        except Exception as e:
            logging.warning(f"⚠️ [V63] SemanticPlotGuard 임베딩 실패: {str(e)[:80]}")
        return None

    def index_resolved_plots(self, resolved_plots: List[Dict]) -> int:
        """
        완결된 플롯들을 임베딩하여 인덱스에 저장.

        Args:
            resolved_plots: [{"plot": "인수전 완료", "resolution": "...", ...}, ...]

        Returns:
            성공적으로 인덱싱된 플롯 수
        """
        if not self._client:
            return 0

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
                self._resolved_embeddings.append({
                    "plot": plot_name,
                    "resolution": resolution,
                    "embedding": emb
                })
                indexed += 1

        if indexed > 0:
            logging.info(f"📊 [V63] SemanticPlotGuard: {indexed}개 플롯 인덱싱 완료 (총 {len(self._resolved_embeddings)}개)")
        return indexed

    def check_new_arc(self, tactical_doc: str = "", new_plot_names: List[str] = None) -> List[Dict]:
        """
        새 Arc의 내용이 기존 resolved_plots와 시맨틱 중복인지 검사.

        Args:
            tactical_doc: 새 Arc의 tactical_doc 전문
            new_plot_names: 새 Arc에서 추출한 주요 플롯/갈등 이름 목록

        Returns:
            경고 목록: [{"new_plot": str, "similar_to": str, "similarity": float}, ...]
        """
        if not self._client or not self._resolved_embeddings:
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
                    warnings.append({
                        "new_plot": display_text,
                        "similar_to": resolved["plot"],
                        "similarity": round(sim, 3)
                    })

        return warnings

    def format_warnings(self, warnings: List[Dict]) -> str:
        """경고를 프롬프트 주입 가능한 문자열로 포맷팅"""
        if not warnings:
            return ""

        lines = ["[V63] ⚠️ 시맨틱 플롯 중복 경고:"]
        for w in warnings:
            lines.append(
                f"  - \"{w['new_plot']}\" ↔ 완결된 \"{w['similar_to']}\" "
                f"(유사도 {w['similarity']:.1%}) → 차별화 필요"
            )
        return "\n".join(lines)
