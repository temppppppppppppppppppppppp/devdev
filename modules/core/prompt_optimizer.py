"""
[Phase 3] Automated Prompt Optimization

성능 데이터를 분석하여 프롬프트를 자동으로 개선
메타-학습 기반 프롬프트 진화
"""

import os
import statistics
from datetime import datetime
from typing import Any


class PromptOptimizer:
    """
    프롬프트 자동 최적화 시스템

    성능 데이터를 분석하여 프롬프트의 효과적인 부분을 식별하고
    자동으로 개선된 프롬프트를 생성
    """

    def __init__(self, project_name: str = "default"):
        """
        Args:
            project_name: 프로젝트 이름
        """
        self.project_name = project_name
        self.optimization_history = []
        self.best_prompts = {}

    def analyze_validation_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        검증 결과 분석

        Args:
            results: 검증 결과 리스트

        Returns:
            분석 결과 dict
        """
        if not results:
            return {"error": "No results to analyze"}

        # 점수 통계
        scores = [r.get("total_score", 0) for r in results]
        avg_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0

        # 통과율
        pass_count = sum(1 for r in results if r.get("decision") in ["PASS", "CONDITIONAL_PASS"])
        pass_rate = pass_count / len(results)

        # 세부 점수 분석
        category_scores = self._analyze_category_scores(results)

        # 약점 식별
        weaknesses = self._identify_weaknesses(category_scores)

        return {
            "total_evaluations": len(results),
            "avg_score": avg_score,
            "median_score": median_score,
            "std_dev": std_dev,
            "pass_rate": pass_rate,
            "category_scores": category_scores,
            "weaknesses": weaknesses,
        }

    def _analyze_category_scores(self, results: list[dict]) -> dict[str, float]:
        """카테고리별 평균 점수 분석"""
        categories = [
            "character_consistency",
            "emotion_arc",
            "dialogue_quality",
            "commercial_appeal",
            "pattern_diversity",
        ]

        category_scores = {}

        for category in categories:
            scores = []
            for r in results:
                breakdown = r.get("scoring_result", {}).get("breakdown", {})
                if category in breakdown:
                    score = breakdown[category].get("score", 0)
                    max_score = breakdown[category].get("max", 100)
                    percentage = (score / max_score * 100) if max_score > 0 else 0
                    scores.append(percentage)

            if scores:
                category_scores[category] = statistics.mean(scores)

        return category_scores

    def _identify_weaknesses(
        self, category_scores: dict[str, float], threshold: float = 70.0
    ) -> list[tuple[str, float]]:
        """약점 카테고리 식별"""
        weaknesses = []

        for category, score in category_scores.items():
            if score < threshold:
                weaknesses.append((category, score))

        # 점수가 낮은 순으로 정렬
        weaknesses.sort(key=lambda x: x[1])

        return weaknesses

    def generate_improved_prompt(
        self, original_prompt: str, weaknesses: list[tuple[str, float]], analysis: dict[str, Any]
    ) -> str:
        """
        개선된 프롬프트 생성

        Args:
            original_prompt: 원본 프롬프트
            weaknesses: 약점 리스트 [(category, score), ...]
            analysis: 분석 결과

        Returns:
            개선된 프롬프트
        """
        if not weaknesses:
            return original_prompt

        # 개선 지시사항 생성
        improvements = []

        for category, score in weaknesses[:3]:  # 상위 3개 약점
            improvement = self._generate_improvement_for_category(category, score)
            improvements.append(improvement)

        # 프롬프트에 개선사항 추가
        improved_prompt = original_prompt + "\n\n"
        improved_prompt += "### [📈 Performance-Optimized Focus Areas]\n\n"
        improved_prompt += "최근 분석 결과, 아래 항목들을 특히 주의하여 평가하십시오:\n\n"

        for i, improvement in enumerate(improvements, 1):
            improved_prompt += f"{i}. {improvement}\n"

        improved_prompt += f"\n현재 평균 점수: {analysis.get('avg_score', 0):.1f}점\n"
        improved_prompt += f"목표: {analysis.get('avg_score', 0) + 5:.1f}점 이상\n"

        return improved_prompt

    def _generate_improvement_for_category(self, category: str, current_score: float) -> str:
        """카테고리별 개선 지시사항 생성"""
        improvements = {
            "character_consistency": (
                f"**캐릭터 일관성** (현재 {current_score:.1f}%): "
                "등장인물의 행동이 설정된 성격/능력과 일치하는지 더욱 엄격히 검증하십시오. "
                "설정 모순이 발견되면 점수를 대폭 감점하십시오."
            ),
            "emotion_arc": (
                f"**감정선** (현재 {current_score:.1f}%): "
                "감정 변화의 자연스러움과 독자 공감도를 높게 평가하십시오. "
                "급격한 감정 전환이나 설득력 없는 감정 묘사는 감점하십시오."
            ),
            "dialogue_quality": (
                f"**대화 품질** (현재 {current_score:.1f}%): "
                "대사가 캐릭터 특성을 반영하고 서사 전개에 기여하는지 중점적으로 평가하십시오. "
                "설명적 대사나 캐릭터성 없는 대사는 감점하십시오."
            ),
            "commercial_appeal": (
                f"**상업성** (현재 {current_score:.1f}%): "
                "독자를 끌어당기는 요소와 다음 화 기대감을 엄격히 평가하십시오. "
                "절벽걸기, 반전, 카타르시스 등이 부족하면 감점하십시오."
            ),
            "pattern_diversity": (
                f"**패턴 다양성** (현재 {current_score:.1f}%): "
                "클리셰와 반복 패턴을 더욱 엄격히 감지하십시오. "
                "신선하지 않은 전개는 과감히 감점하십시오."
            ),
        }

        return improvements.get(category, f"{category} 개선 필요 (현재 {current_score:.1f}%)")

    def optimize_prompt_iteratively(
        self, original_prompt: str, validation_results: list[dict], target_score: float = 80.0, max_iterations: int = 5
    ) -> tuple[str, list[dict]]:
        """
        반복적 프롬프트 최적화

        Args:
            original_prompt: 원본 프롬프트
            validation_results: 검증 결과
            target_score: 목표 점수
            max_iterations: 최대 반복 횟수

        Returns:
            (최적 프롬프트, 최적화 히스토리)
        """
        current_prompt = original_prompt
        history = []

        for iteration in range(max_iterations):
            # 분석
            analysis = self.analyze_validation_results(validation_results)

            # 목표 달성 시 종료
            if analysis["avg_score"] >= target_score:
                break

            # 약점 식별
            weaknesses = analysis["weaknesses"]

            if not weaknesses:
                break

            # 프롬프트 개선
            improved_prompt = self.generate_improved_prompt(current_prompt, weaknesses, analysis)

            # 히스토리 기록
            history.append(
                {
                    "iteration": iteration + 1,
                    "avg_score": analysis["avg_score"],
                    "weaknesses": weaknesses,
                    "prompt": improved_prompt,
                }
            )

            current_prompt = improved_prompt

        return current_prompt, history

    def save_optimized_prompt(self, prompt: str, prompt_name: str, output_dir: str = "optimized_prompts"):
        """최적화된 프롬프트 저장"""
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{prompt_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prompt)

        return filepath

    def compare_prompts(
        self, prompt_a: str, prompt_b: str, results_a: list[dict], results_b: list[dict]
    ) -> dict[str, Any]:
        """
        두 프롬프트 성능 비교

        Args:
            prompt_a: 프롬프트 A
            prompt_b: 프롬프트 B
            results_a: A의 검증 결과
            results_b: B의 검증 결과

        Returns:
            비교 결과 dict
        """
        analysis_a = self.analyze_validation_results(results_a)
        analysis_b = self.analyze_validation_results(results_b)

        comparison = {
            "prompt_a": {
                "avg_score": analysis_a["avg_score"],
                "pass_rate": analysis_a["pass_rate"],
                "std_dev": analysis_a["std_dev"],
            },
            "prompt_b": {
                "avg_score": analysis_b["avg_score"],
                "pass_rate": analysis_b["pass_rate"],
                "std_dev": analysis_b["std_dev"],
            },
            "improvements": {
                "score_diff": analysis_b["avg_score"] - analysis_a["avg_score"],
                "pass_rate_diff": analysis_b["pass_rate"] - analysis_a["pass_rate"],
                "consistency_improvement": analysis_a["std_dev"] - analysis_b["std_dev"],
            },
        }

        # 승자 결정
        if comparison["improvements"]["score_diff"] > 0:
            comparison["winner"] = "Prompt B"
        elif comparison["improvements"]["score_diff"] < 0:
            comparison["winner"] = "Prompt A"
        else:
            comparison["winner"] = "Tie"

        return comparison

    def generate_report(self, analysis: dict[str, Any]) -> str:
        """분석 리포트 생성"""
        report = []
        report.append("=" * 60)
        report.append("PROMPT OPTIMIZATION ANALYSIS")
        report.append("=" * 60)
        report.append(f"Total Evaluations: {analysis['total_evaluations']}")
        report.append(f"Average Score: {analysis['avg_score']:.1f}")
        report.append(f"Median Score: {analysis['median_score']:.1f}")
        report.append(f"Std Dev: {analysis['std_dev']:.2f}")
        report.append(f"Pass Rate: {analysis['pass_rate']:.1%}")
        report.append("")

        # 카테고리별 점수
        report.append("--- Category Scores ---")
        for category, score in analysis["category_scores"].items():
            report.append(f"{category}: {score:.1f}%")
        report.append("")

        # 약점
        if analysis["weaknesses"]:
            report.append("--- Identified Weaknesses ---")
            for category, score in analysis["weaknesses"]:
                report.append(f"⚠️ {category}: {score:.1f}%")
        else:
            report.append("✅ No significant weaknesses detected")

        report.append("=" * 60)

        return "\n".join(report)


class MetaLearner:
    """
    메타-학습 시스템

    여러 프롬프트 변형의 성능을 학습하여
    최적의 프롬프트 패턴을 발견
    """

    def __init__(self) -> None:
        """Initialize meta-learner"""
        self.prompt_variants = []
        self.performance_data = []

    def register_variant(self, variant_name: str, prompt: str, results: list[dict]):
        """프롬프트 변형 등록"""
        optimizer = PromptOptimizer()
        analysis = optimizer.analyze_validation_results(results)

        self.prompt_variants.append({"name": variant_name, "prompt": prompt, "performance": analysis})

    def identify_best_patterns(self) -> dict[str, Any]:
        """최고 성능 패턴 식별"""
        if not self.prompt_variants:
            return {"error": "No variants registered"}

        # 성능 순으로 정렬
        sorted_variants = sorted(self.prompt_variants, key=lambda x: x["performance"]["avg_score"], reverse=True)

        best = sorted_variants[0]
        worst = sorted_variants[-1]

        return {
            "best_variant": best["name"],
            "best_score": best["performance"]["avg_score"],
            "worst_variant": worst["name"],
            "worst_score": worst["performance"]["avg_score"],
            "improvement": best["performance"]["avg_score"] - worst["performance"]["avg_score"],
            "all_variants": sorted_variants,
        }

    def synthesize_optimal_prompt(self) -> str:
        """최적 프롬프트 합성"""
        patterns = self.identify_best_patterns()

        if "error" in patterns:
            return ""

        best_variant = patterns["all_variants"][0]

        return best_variant["prompt"]


# 편의 함수
def quick_optimize(prompt: str, validation_results: list[dict], prompt_name: str = "optimized") -> tuple[str, str]:
    """
    빠른 프롬프트 최적화

    Args:
        prompt: 원본 프롬프트
        validation_results: 검증 결과
        prompt_name: 프롬프트 이름

    Returns:
        (최적화된 프롬프트, 리포트)
    """
    optimizer = PromptOptimizer()

    # 분석
    analysis = optimizer.analyze_validation_results(validation_results)

    # 개선
    improved_prompt = optimizer.generate_improved_prompt(prompt, analysis["weaknesses"], analysis)

    # 저장
    optimizer.save_optimized_prompt(improved_prompt, prompt_name)

    # 리포트
    report = optimizer.generate_report(analysis)

    return improved_prompt, report
