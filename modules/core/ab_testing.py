"""
[Phase 2] A/B Testing Framework

V0128 vs Legacy 시스템 성능 비교
데이터 기반 의사결정 지원
"""

import json
import logging
import statistics
import time
from datetime import datetime


class ABTestingFramework:
    """
    A/B 테스트 프레임워크

    두 검증 시스템(A: Legacy, B: V0128)을 비교하여 성능 측정
    """

    def __init__(self, project_name: str = "default"):
        """
        Args:
            project_name: 프로젝트 이름 (데이터 저장 시 사용)
        """
        self.project_name = project_name
        self.variant_a_results = []  # Legacy
        self.variant_b_results = []  # V0128
        self.start_time = None
        self.end_time = None

    def run_test(
        self,
        ep_num: int,
        manuscript: str,
        validation_context: dict,
        director_a,  # Legacy Director
        director_b,  # V0128 Director
        v0128_config: dict = None,
    ) -> tuple[dict, dict]:
        """
        A/B 테스트 실행

        동일한 원고를 두 시스템으로 검증하고 결과 비교

        Args:
            ep_num: 에피소드 번호
            manuscript: 원고
            validation_context: 검증 컨텍스트
            director_a: Legacy Director (audit_manuscript)
            director_b: V0128 Director (audit_manuscript_v0128)
            v0128_config: V0128 설정

        Returns:
            (result_a, result_b) 튜플
        """
        if self.start_time is None:
            self.start_time = time.time()

        # Variant A: Legacy 시스템
        start_a = time.time()
        try:
            result_a = director_a.audit_manuscript(
                ep_num=ep_num,
                manuscript=manuscript,
                arc_doc=validation_context.get("arc_doc", ""),
                history_summary=validation_context.get("history_summary", ""),
                prev_full_text=validation_context.get("prev_full_text", ""),
                arc_pos=validation_context.get("arc_pos", 1),
                total_eps=validation_context.get("total_eps", 5),
                target_len=5000,
                retry_count=0,
            )
            time_a = time.time() - start_a
            success_a = True
        except Exception as e:
            result_a = {"error": str(e)}
            time_a = time.time() - start_a
            success_a = False

        # Variant B: V0128 시스템
        start_b = time.time()
        try:
            result_b = director_b.audit_manuscript_v0128(
                ep_num=ep_num,
                manuscript=manuscript,
                validation_context=validation_context,
                config=v0128_config,
                genre="wuxia",
            )
            time_b = time.time() - start_b
            success_b = True
        except Exception as e:
            result_b = {"error": str(e)}
            time_b = time.time() - start_b
            success_b = False

        # 결과 저장
        self.variant_a_results.append(
            {
                "ep_num": ep_num,
                "result": result_a,
                "time": time_a,
                "success": success_a,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.variant_b_results.append(
            {
                "ep_num": ep_num,
                "result": result_b,
                "time": time_b,
                "success": success_b,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return result_a, result_b

    def analyze_results(self) -> dict:
        """
        A/B 테스트 결과 분석

        Returns:
            분석 결과 dict
        """
        if not self.variant_a_results or not self.variant_b_results:
            return {"error": "No results to analyze"}

        self.end_time = time.time()

        analysis = {
            "project": self.project_name,
            "total_tests": len(self.variant_a_results),
            "variant_a": self._analyze_variant(self.variant_a_results, "Legacy"),
            "variant_b": self._analyze_variant(self.variant_b_results, "V0128"),
            "comparison": self._compare_variants(),
            "recommendation": self._generate_recommendation(),
        }

        return analysis

    def _analyze_variant(self, results: list[dict], name: str) -> dict:
        """단일 variant 분석"""
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        failed = total - successful

        # PASS/REJECT 통계
        pass_count = 0
        reject_count = 0
        scores = []

        for r in results:
            # [V44] None/키 안전성 체크
            if r.get("success", False) and r.get("result"):
                decision = r["result"].get("decision", "UNKNOWN")
                if decision == "PASS":
                    pass_count += 1
                elif decision == "REJECT":
                    reject_count += 1

                score = r["result"].get("score", 0)
                if score:
                    scores.append(score)

        # 시간 통계
        times = [r["time"] for r in results]
        avg_time = statistics.mean(times) if times else 0
        median_time = statistics.median(times) if times else 0

        # 점수 통계
        avg_score = statistics.mean(scores) if scores else 0
        median_score = statistics.median(scores) if scores else 0
        std_dev_score = statistics.stdev(scores) if len(scores) > 1 else 0

        return {
            "name": name,
            "total_tests": total,
            "successful": successful,
            "failed": failed,
            "pass_count": pass_count,
            "reject_count": reject_count,
            "pass_rate": pass_count / total if total > 0 else 0,
            "avg_score": avg_score,
            "median_score": median_score,
            "score_std_dev": std_dev_score,
            "avg_time": avg_time,
            "median_time": median_time,
        }

    def _compare_variants(self) -> dict:
        """두 variant 비교 (통계적 유의성 포함)"""
        a_stats = self._analyze_variant(self.variant_a_results, "Legacy")
        b_stats = self._analyze_variant(self.variant_b_results, "V0128")

        # 점수 데이터 추출
        a_scores = []
        b_scores = []
        for r in self.variant_a_results:
            if r["success"]:
                score = r["result"].get("score", 0)
                if score:
                    a_scores.append(score)

        for r in self.variant_b_results:
            if r["success"]:
                score = r["result"].get("score", 0)
                if score:
                    b_scores.append(score)

        # 통계적 유의성 검정 (t-test)
        statistical_significance = self._calculate_statistical_significance(a_scores, b_scores)

        return {
            "pass_rate_improvement": b_stats["pass_rate"] - a_stats["pass_rate"],
            "score_improvement": b_stats["avg_score"] - a_stats["avg_score"],
            "time_difference": b_stats["avg_time"] - a_stats["avg_time"],
            "consistency_improvement": a_stats["score_std_dev"] - b_stats["score_std_dev"],
            "statistical_significance": statistical_significance,
            "winner": self._determine_winner(a_stats, b_stats),
        }

    def _calculate_statistical_significance(self, scores_a: list[float], scores_b: list[float]) -> dict:
        """
        통계적 유의성 계산 (Welch's t-test)

        Returns:
            t-statistic, p-value, 유의성 해석
        """
        if len(scores_a) < 2 or len(scores_b) < 2:
            return {
                "test": "Welch t-test",
                "t_statistic": None,
                "p_value": None,
                "significant": False,
                "interpretation": "샘플 수 부족 (최소 2개 필요)",
                "confidence": "N/A",
            }

        # Welch's t-test (등분산 가정 불필요)
        mean_a = statistics.mean(scores_a)
        mean_b = statistics.mean(scores_b)
        var_a = statistics.variance(scores_a) if len(scores_a) > 1 else 0
        var_b = statistics.variance(scores_b) if len(scores_b) > 1 else 0
        n_a = len(scores_a)
        n_b = len(scores_b)

        # t-statistic 계산
        se = ((var_a / n_a) + (var_b / n_b)) ** 0.5
        if se == 0:
            t_stat = 0
        else:
            t_stat = (mean_b - mean_a) / se

        # 자유도 (Welch-Satterthwaite)
        if var_a == 0 or var_b == 0:
            df = min(n_a, n_b) - 1
        else:
            numerator = ((var_a / n_a) + (var_b / n_b)) ** 2
            denominator = ((var_a / n_a) ** 2 / (n_a - 1)) + ((var_b / n_b) ** 2 / (n_b - 1))
            df = numerator / denominator if denominator > 0 else 1

        # p-value 근사 (간단한 휴리스틱)
        # 정확한 계산은 scipy.stats.t.cdf 사용 필요
        abs_t = abs(t_stat)
        if abs_t < 1.0:
            p_value = 0.35  # 유의하지 않음
        elif abs_t < 1.5:
            p_value = 0.15
        elif abs_t < 2.0:
            p_value = 0.06  # 경계선
        elif abs_t < 2.5:
            p_value = 0.02  # 유의함 (p < 0.05)
        else:
            p_value = 0.01  # 매우 유의함 (p < 0.01)

        # 해석
        if p_value < 0.01:
            interpretation = "매우 유의함 (p < 0.01) - 차이가 통계적으로 매우 확실함"
            confidence = "99%+"
        elif p_value < 0.05:
            interpretation = "유의함 (p < 0.05) - 차이가 통계적으로 유의미함"
            confidence = "95%+"
        elif p_value < 0.10:
            interpretation = "경계선 (0.05 < p < 0.10) - 추가 데이터 수집 권장"
            confidence = "90%+"
        else:
            interpretation = "유의하지 않음 (p >= 0.10) - 우연일 가능성 높음"
            confidence = "<90%"

        return {
            "test": "Welch t-test (approximate)",
            "t_statistic": round(t_stat, 3),
            "p_value": round(p_value, 4),
            "degrees_of_freedom": round(df, 1),
            "significant": p_value < 0.05,
            "interpretation": interpretation,
            "confidence": confidence,
            "note": "정확한 p-value는 scipy 사용 권장",
        }

    def _determine_winner(self, a_stats: dict, b_stats: dict) -> str:
        """승자 결정"""
        score = 0

        # 통과율 비교 (가중치: 40%)
        if b_stats["pass_rate"] > a_stats["pass_rate"]:
            score += 40

        # 평균 점수 비교 (가중치: 30%)
        if b_stats["avg_score"] > a_stats["avg_score"]:
            score += 30

        # 일관성 비교 (가중치: 20%)
        if b_stats["score_std_dev"] < a_stats["score_std_dev"]:
            score += 20

        # 속도 비교 (가중치: 10%)
        if b_stats["avg_time"] < a_stats["avg_time"]:
            score += 10

        if score >= 50:
            return "V0128 (Variant B)"
        elif score <= 30:
            return "Legacy (Variant A)"
        else:
            return "Tie (similar performance)"

    def _generate_recommendation(self) -> str:
        """추천 생성"""
        comparison = self._compare_variants()
        winner = comparison["winner"]

        if "V0128" in winner:
            return (
                f"V0128을 사용하는 것을 권장합니다.\n"
                f"- 통과율 개선: {comparison['pass_rate_improvement']:.1%}\n"
                f"- 점수 개선: {comparison['score_improvement']:.1f}점\n"
                f"- 일관성 개선: {comparison['consistency_improvement']:.1f}점"
            )
        elif "Legacy" in winner:
            return "Legacy 시스템을 유지하는 것을 권장합니다.\nV0128의 성능이 예상보다 낮습니다."
        else:
            return "두 시스템의 성능이 유사합니다.\n비용 대비 효과를 고려하여 선택하십시오."

    def generate_report(self, output_path: str = None) -> str:
        """
        상세 리포트 생성

        Args:
            output_path: 리포트 저장 경로 (선택적)

        Returns:
            리포트 텍스트
        """
        analysis = self.analyze_results()

        report = []
        report.append("=" * 80)
        report.append("A/B TESTING REPORT")
        report.append("=" * 80)
        report.append(f"Project: {analysis['project']}")
        report.append(f"Total Tests: {analysis['total_tests']}")
        report.append("")

        # Variant A
        a = analysis["variant_a"]
        report.append("--- VARIANT A: Legacy System ---")
        report.append(f"Pass Rate: {a['pass_rate']:.1%} ({a['pass_count']}/{a['total_tests']})")
        report.append(f"Average Score: {a['avg_score']:.1f}")
        report.append(f"Score Std Dev: {a['score_std_dev']:.2f}")
        report.append(f"Average Time: {a['avg_time']:.3f}s")
        report.append("")

        # Variant B
        b = analysis["variant_b"]
        report.append("--- VARIANT B: V0128 System ---")
        report.append(f"Pass Rate: {b['pass_rate']:.1%} ({b['pass_count']}/{b['total_tests']})")
        report.append(f"Average Score: {b['avg_score']:.1f}")
        report.append(f"Score Std Dev: {b['score_std_dev']:.2f}")
        report.append(f"Average Time: {b['avg_time']:.3f}s")
        report.append("")

        # Comparison
        comp = analysis["comparison"]
        report.append("--- COMPARISON ---")
        report.append(f"Pass Rate Improvement: {comp['pass_rate_improvement']:.1%}")
        report.append(f"Score Improvement: {comp['score_improvement']:+.1f} points")
        report.append(f"Consistency Improvement: {comp['consistency_improvement']:+.2f}")
        report.append(f"Time Difference: {comp['time_difference']:+.3f}s")
        report.append(f"Winner: {comp['winner']}")
        report.append("")

        # Recommendation
        report.append("--- RECOMMENDATION ---")
        report.append(analysis["recommendation"])
        report.append("=" * 80)

        report_text = "\n".join(report)

        # 파일 저장 (선택적)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            report.append(f"\nReport saved to: {output_path}")

        return report_text

    def save_raw_data(self, output_path: str):
        """원시 데이터 JSON으로 저장"""
        data = {
            "project": self.project_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "variant_a": self.variant_a_results,
            "variant_b": self.variant_b_results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        """테스트 데이터 초기화"""
        self.variant_a_results = []
        self.variant_b_results = []
        self.start_time = None
        self.end_time = None


# 편의 함수
def quick_ab_test(manuscripts: list[dict], director_a, director_b, v0128_config: dict = None) -> str:
    """
    빠른 A/B 테스트

    Args:
        manuscripts: List of {ep_num, manuscript, validation_context}
        director_a: Legacy Director
        director_b: V0128 Director
        v0128_config: V0128 설정

    Returns:
        리포트 텍스트
    """
    framework = ABTestingFramework()

    for ms_data in manuscripts:
        framework.run_test(
            ep_num=ms_data["ep_num"],
            manuscript=ms_data["manuscript"],
            validation_context=ms_data["validation_context"],
            director_a=director_a,
            director_b=director_b,
            v0128_config=v0128_config,
        )

    report = framework.generate_report()
    logging.info(report)

    return report
