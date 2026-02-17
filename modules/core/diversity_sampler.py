"""
[V48 Premium] Diversity Sampling 시스템

3개 후보를 생성하고 가장 다양한 것을 선택하는 앙상블 기법

적용 위치:
- Stage 3 (Architect): 항상 활성화
- Stage 4 (Writer): Pattern Tracker가 플래그할 때만 활성화
"""

import logging
import re
from collections.abc import Callable


class DiversitySampler:
    """
    Diversity Sampling: 여러 후보 중 가장 다양한 것 선택

    다양성 측정 기준:
    1. 어휘 다양성 (TTR - Type-Token Ratio)
    2. 문장 구조 다양성 (문장 길이 분포)
    3. 키워드 유사도 (자카드 거리)
    4. n-gram 중복률 (기존 원고와의 유사도)
    """

    def __init__(self, reference_texts: list[str] = None):
        """
        Args:
            reference_texts: 비교 기준이 되는 기존 원고들 (최근 N화)
        """
        self.reference_texts = reference_texts or []
        self.reference_ngrams = self._build_reference_ngrams()

    def _build_reference_ngrams(self) -> set:
        """기존 원고에서 3-gram 추출"""
        if not self.reference_texts:
            return set()

        combined = "\n".join(self.reference_texts)
        words = re.findall(r"[\w가-힣]+", combined)

        if len(words) < 3:
            return set()

        return set(" ".join(words[i : i + 3]) for i in range(len(words) - 2))

    def sample_and_select(
        self, generator_fn: Callable[[], str], n_samples: int = 3, context: dict = None
    ) -> tuple[str, dict]:
        """
        N개 샘플 생성 후 가장 다양한 것 선택

        Args:
            generator_fn: 텍스트 생성 함수 (호출 시마다 새 결과 반환)
            n_samples: 생성할 샘플 수 (기본 3)
            context: 추가 컨텍스트 정보

        Returns:
            (선택된 텍스트, 메타데이터)
        """
        samples = []
        sample_scores = []

        logging.info(f"[DiversitySampler] {n_samples}개 샘플 생성 중...")

        for i in range(n_samples):
            try:
                sample = generator_fn()
                if sample and isinstance(sample, str):
                    # [V70] 점수 계산 성공 후 append (desync 방지)
                    score = self._calculate_diversity_score(sample)
                    samples.append(sample)
                    sample_scores.append(score)
                    logging.info(f"- 샘플 {i + 1}: 다양성 점수 {score['total']:.2f}")

            except Exception as e:
                logging.warning(f"- 샘플 {i + 1} 생성 실패: {e}")
                continue

        if not samples:
            return "", {"error": "no_samples_generated"}  # [V70] None → "" (callers expect str)

        # 최고 다양성 점수 선택
        best_idx = max(range(len(sample_scores)), key=lambda i: sample_scores[i]["total"])
        selected = samples[best_idx]
        selected_score = sample_scores[best_idx]

        logging.info(f"[DiversitySampler] 샘플 {best_idx + 1} 선택 (점수: {selected_score['total']:.2f})")

        return selected, {
            "selected_index": best_idx,
            "selected_score": selected_score,
            "all_scores": sample_scores,
            "n_samples": len(samples),
        }

    def sample_blueprints(self, generator_fn: Callable[[], dict], n_samples: int = 3) -> tuple[dict, dict]:
        """
        블루프린트 전용 샘플링 (JSON 구조)

        Args:
            generator_fn: 블루프린트 생성 함수
            n_samples: 생성할 샘플 수

        Returns:
            (선택된 블루프린트, 메타데이터)
        """
        samples = []
        sample_scores = []

        logging.info(f"[DiversitySampler] 블루프린트 {n_samples}개 샘플 생성 중...")

        for i in range(n_samples):
            try:
                sample = generator_fn()
                if sample and isinstance(sample, dict):
                    # [V70] 점수 계산 성공 후 append (desync 방지)
                    score = self._calculate_blueprint_diversity(sample)
                    samples.append(sample)
                    sample_scores.append(score)
                    logging.info(f"- 블루프린트 {i + 1}: 다양성 점수 {score['total']:.2f}")

            except Exception as e:
                logging.warning(f"- 블루프린트 {i + 1} 생성 실패: {e}")
                continue

        if not samples:
            return {}, {"error": "no_blueprints_generated"}  # [V70] None → {} (callers expect dict)

        # 최고 다양성 점수 선택
        best_idx = max(range(len(sample_scores)), key=lambda i: sample_scores[i]["total"])
        selected = samples[best_idx]
        selected_score = sample_scores[best_idx]

        logging.info(f"[DiversitySampler] 블루프린트 {best_idx + 1} 선택 (점수: {selected_score['total']:.2f})")

        return selected, {
            "selected_index": best_idx,
            "selected_score": selected_score,
            "all_scores": sample_scores,
            "n_samples": len(samples),
        }

    def _calculate_diversity_score(self, text: str) -> dict:
        """
        텍스트 다양성 점수 계산 (0-100)

        Components:
        - TTR (Type-Token Ratio): 어휘 다양성 (30%)
        - Sentence Variety: 문장 구조 다양성 (25%)
        - Novelty: 기존 원고 대비 신선도 (30%)
        - Structure: 구조적 다양성 (15%)
        """
        scores = {}

        # 1. TTR (Type-Token Ratio) - 30%
        words = re.findall(r"[\w가-힣]+", text)
        if len(words) > 0:
            # 긴 텍스트는 샘플링 (1000단어)
            sample_words = words[:1000] if len(words) > 1000 else words
            unique_words = set(sample_words)
            ttr = len(unique_words) / len(sample_words)
            # TTR 0.3-0.7 범위를 0-100으로 스케일링
            scores["ttr"] = min(100, max(0, (ttr - 0.3) / 0.4 * 100))
        else:
            scores["ttr"] = 0

        # 2. Sentence Variety - 25%
        sentences = re.split(r"[.!?]\s*", text)
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) >= 3:
            lengths = [len(s) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            # 문장 길이 변동계수 (CV)
            if avg_len > 0:
                variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
                std_dev = variance**0.5
                cv = std_dev / avg_len
                # CV 0.3-0.6이 이상적
                if cv < 0.3:
                    scores["sentence_variety"] = cv / 0.3 * 70
                elif cv <= 0.6:
                    scores["sentence_variety"] = 70 + (cv - 0.3) / 0.3 * 30
                else:
                    scores["sentence_variety"] = max(50, 100 - (cv - 0.6) * 100)
            else:
                scores["sentence_variety"] = 50
        else:
            scores["sentence_variety"] = 50

        # 3. Novelty (기존 원고 대비 신선도) - 30%
        if self.reference_ngrams:
            text_words = re.findall(r"[\w가-힣]+", text)
            if len(text_words) >= 3:
                text_ngrams = set(" ".join(text_words[i : i + 3]) for i in range(len(text_words) - 2))
                overlap = len(text_ngrams & self.reference_ngrams)
                total = len(text_ngrams) if text_ngrams else 1
                novelty_ratio = 1 - (overlap / total)
                scores["novelty"] = novelty_ratio * 100
            else:
                scores["novelty"] = 50
        else:
            scores["novelty"] = 70  # 참조 없으면 기본값

        # 4. Structure Variety - 15%
        # 문장 시작 패턴 다양성
        starters = [(w[0] if (w := s.split()) else "") for s in sentences if s.strip()]
        if starters:
            unique_starters = len(set(starters))
            total_starters = len(starters)
            starter_diversity = unique_starters / total_starters if total_starters > 0 else 0
            scores["structure"] = starter_diversity * 100
        else:
            scores["structure"] = 50

        # 가중 평균 계산
        weights = {"ttr": 0.30, "sentence_variety": 0.25, "novelty": 0.30, "structure": 0.15}
        total = sum(scores[k] * weights[k] for k in weights)

        return {
            "ttr": scores["ttr"],
            "sentence_variety": scores["sentence_variety"],
            "novelty": scores["novelty"],
            "structure": scores["structure"],
            "total": total,
        }

    def _calculate_blueprint_diversity(self, blueprint: dict) -> dict:
        """
        블루프린트 다양성 점수 계산

        Components:
        - Scene Type Variety: Core/Buffer 균형 (35%)
        - Content Novelty: 씬 내용 다양성 (35%)
        - Structure: 구조적 다양성 (30%)
        """
        scores = {}

        scene_breakdown = blueprint.get("scene_breakdown", {})
        integrated = blueprint.get("integrated_scenario", "")

        # 1. Scene Type Variety - 35%
        if isinstance(scene_breakdown, dict):
            types = {"Core": 0, "Buffer": 0, "Cliffhanger": 0}
            for scene_content in scene_breakdown.values():
                if isinstance(scene_content, str):
                    if "[Core]" in scene_content:
                        types["Core"] += 1
                    elif "[Buffer]" in scene_content:
                        types["Buffer"] += 1
                    elif "[Cliffhanger]" in scene_content:
                        types["Cliffhanger"] += 1

            total_typed = sum(types.values())
            if total_typed > 0:
                # 이상적 비율: Core 2-3, Buffer 2-3, Cliffhanger 1
                core_ratio = types["Core"] / total_typed
                buffer_ratio = types["Buffer"] / total_typed
                # 0.3-0.5 범위가 이상적
                balance = 1 - abs(core_ratio - 0.4) - abs(buffer_ratio - 0.4)
                scores["scene_type"] = max(0, balance * 100)
            else:
                scores["scene_type"] = 50
        else:
            scores["scene_type"] = 50

        # 2. Content Novelty - 35%
        if integrated:
            score_detail = self._calculate_diversity_score(integrated)
            scores["content_novelty"] = score_detail["novelty"]
        else:
            scores["content_novelty"] = 50

        # 3. Structure Diversity - 30%
        if isinstance(scene_breakdown, dict) and len(scene_breakdown) >= 4:
            # 각 씬 길이 분포
            scene_lengths = [len(str(v)) for v in scene_breakdown.values()]
            avg = sum(scene_lengths) / len(scene_lengths) if scene_lengths else 1
            variance = sum((l - avg) ** 2 for l in scene_lengths) / len(scene_lengths) if scene_lengths else 0
            cv = (variance**0.5) / avg if avg > 0 else 0

            # 적당한 변동 (CV 0.2-0.5)이 좋음
            if 0.2 <= cv <= 0.5:
                scores["structure"] = 80 + (0.5 - abs(cv - 0.35)) * 100
            else:
                scores["structure"] = max(30, 80 - abs(cv - 0.35) * 100)
        else:
            scores["structure"] = 50

        # 가중 평균
        weights = {"scene_type": 0.35, "content_novelty": 0.35, "structure": 0.30}
        total = sum(scores.get(k, 50) * weights[k] for k in weights)

        return {
            "scene_type": scores.get("scene_type", 50),
            "content_novelty": scores.get("content_novelty", 50),
            "structure": scores.get("structure", 50),
            "total": total,
        }

    def compare_candidates(self, candidates: list[str]) -> list[dict]:
        """
        여러 후보 텍스트 비교 분석

        Args:
            candidates: 비교할 텍스트 리스트

        Returns:
            각 후보의 점수 및 순위
        """
        results = []

        for i, text in enumerate(candidates):
            score = self._calculate_diversity_score(text)
            results.append(
                {
                    "index": i,
                    "score": score,
                    "rank": 0,  # 나중에 설정
                }
            )

        # 순위 설정
        results.sort(key=lambda x: x["score"]["total"], reverse=True)
        for rank, item in enumerate(results, 1):
            item["rank"] = rank

        return results


class ConditionalDiversitySampler:
    """
    [V57] 조건부 Diversity Sampling

    Pattern Tracker와 연동하여 필요시에만 활성화
    패턴 심각도에 따라 동적으로 샘플 수 조정
    """

    def __init__(self, pattern_tracker=None, reference_texts: list[str] = None):
        """
        Args:
            pattern_tracker: PatternTracker 인스턴스
            reference_texts: 비교 기준 원고
        """
        self.pattern_tracker = pattern_tracker
        self.sampler = DiversitySampler(reference_texts)
        self.is_forced = False  # 강제 활성화 플래그

    def should_sample(self) -> tuple[bool, str]:
        """
        Diversity Sampling 활성화 여부 판단

        Returns:
            (활성화 여부, 이유)
        """
        if self.is_forced:
            return True, "강제 활성화됨"

        if self.pattern_tracker is None:
            return False, "PatternTracker 없음"

        return self.pattern_tracker.should_activate_diversity_sampling()

    def _calculate_dynamic_samples(self, base_samples: int = 3) -> tuple[int, str]:
        """
        [V57] 패턴 심각도에 따른 동적 샘플 수 계산

        심각도 레벨:
        - NONE (0): 샘플링 비활성화 → 1개
        - LOW (1): 경미한 반복 → 2개
        - MEDIUM (2): 중간 반복 → 3개 (기본)
        - HIGH (3): 심각한 반복 → 4개
        - CRITICAL (4): 위험 수준 → 5개

        Returns:
            (샘플 수, 심각도 레벨 설명)
        """
        if self.pattern_tracker is None:
            return base_samples, "MEDIUM (기본값)"

        # PatternTracker에서 심각도 수준 조회
        severity = self._get_pattern_severity()

        severity_to_samples = {
            "NONE": (1, "NONE - 단일 생성"),
            "LOW": (2, "LOW - 경미한 반복"),
            "MEDIUM": (3, "MEDIUM - 중간 반복"),
            "HIGH": (4, "HIGH - 심각한 반복"),
            "CRITICAL": (5, "CRITICAL - 위험 수준"),
        }

        return severity_to_samples.get(severity, (base_samples, "MEDIUM (기본값)"))

    def _get_pattern_severity(self) -> str:
        """
        [V57] PatternTracker에서 패턴 심각도 레벨 조회

        반환 레벨:
        - NONE: 패턴 없음
        - LOW: 1-2개 패턴 감지
        - MEDIUM: 3-4개 패턴 감지
        - HIGH: 5-6개 패턴 감지
        - CRITICAL: 7개 이상 패턴 감지
        """
        if self.pattern_tracker is None:
            return "MEDIUM"

        try:
            # PatternTracker의 분석 결과 조회
            if hasattr(self.pattern_tracker, "get_severity_level"):
                return self.pattern_tracker.get_severity_level()

            if hasattr(self.pattern_tracker, "pattern_flags"):
                flags = self.pattern_tracker.pattern_flags
                count = sum(1 for v in flags.values() if v)

                if count == 0:
                    return "NONE"
                elif count <= 2:
                    return "LOW"
                elif count <= 4:
                    return "MEDIUM"
                elif count <= 6:
                    return "HIGH"
                else:
                    return "CRITICAL"

            # should_activate 결과로 대체
            should_activate, reason = self.pattern_tracker.should_activate_diversity_sampling()
            if not should_activate:
                return "NONE"
            elif "심각" in reason or "위험" in reason or "반복" in reason:
                return "HIGH"
            else:
                return "MEDIUM"

        except Exception:
            return "MEDIUM"

    def sample_or_single(
        self,
        generator_fn: Callable,
        n_samples: int = 3,
        force: bool = False,
        use_dynamic_samples: bool = True,  # [V57] 동적 샘플링 활성화
    ) -> tuple[any, dict]:
        """
        [V57] 조건에 따라 샘플링 또는 단일 생성

        Args:
            generator_fn: 생성 함수
            n_samples: 기본 샘플 수 (동적 샘플링 비활성화 시 사용)
            force: 강제 활성화
            use_dynamic_samples: [V57] 패턴 심각도 기반 동적 샘플링 활성화

        Returns:
            (결과, 메타데이터)
        """
        should_sample, reason = self.should_sample()

        if force or should_sample:
            # [V57] 동적 샘플 수 계산
            if use_dynamic_samples:
                actual_samples, severity_desc = self._calculate_dynamic_samples(n_samples)
                logging.info(f"[ConditionalSampler] Diversity Sampling 활성화: {reason}")
                logging.info(f"[V57] 동적 샘플 수: {actual_samples}개 ({severity_desc})")
            else:
                actual_samples = n_samples
                logging.info(f"[ConditionalSampler] Diversity Sampling 활성화: {reason}")

            return self.sampler.sample_and_select(generator_fn, actual_samples)
        else:
            logging.info(f"[ConditionalSampler] 단일 생성 모드: {reason}")
            result = generator_fn()
            return result, {"mode": "single", "reason": reason}

    def sample_blueprint_or_single(
        self,
        generator_fn: Callable,
        n_samples: int = 3,
        force: bool = True,  # Stage 3는 기본 활성화
        use_dynamic_samples: bool = True,  # [V57] 동적 샘플링 활성화
    ) -> tuple[dict, dict]:
        """
        [V57] 블루프린트 조건부 샘플링

        Stage 3 (Architect)는 기본적으로 force=True
        패턴 심각도에 따라 동적으로 샘플 수 조정
        """
        # [V57] 동적 샘플 수 계산
        if use_dynamic_samples and (force or self.should_sample()[0]):
            actual_samples, severity_desc = self._calculate_dynamic_samples(n_samples)
        else:
            actual_samples = n_samples
            severity_desc = "고정"

        if force:
            logging.info("[ConditionalSampler] Blueprint Diversity Sampling (Stage 3 기본)")
            logging.info(f"[V57] 동적 샘플 수: {actual_samples}개 ({severity_desc})")
            return self.sampler.sample_blueprints(generator_fn, actual_samples)
        else:
            should_sample, reason = self.should_sample()
            if should_sample:
                logging.info(f"[ConditionalSampler] Blueprint Diversity Sampling 활성화: {reason}")
                logging.info(f"[V57] 동적 샘플 수: {actual_samples}개 ({severity_desc})")
                return self.sampler.sample_blueprints(generator_fn, actual_samples)
            else:
                result = generator_fn()
                return result, {"mode": "single", "reason": reason}
