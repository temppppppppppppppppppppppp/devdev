"""
[Phase 3] Fine-tuning Automation

Gemini Fine-tuning API 자동화
데이터 수집 → 전처리 → 학습 → 배포 전체 파이프라인
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


class FineTuningManager:
    """
    Fine-tuning 자동화 관리자

    데이터 수집부터 모델 학습까지 전체 파이프라인 자동화
    """

    def __init__(self, project_name: str, base_model: str = "gemini-2.5-pro"):
        """
        Args:
            project_name: 프로젝트 이름
            base_model: 기본 모델명
        """
        self.project_name = project_name
        self.base_model = base_model
        self.training_jobs = []

    def check_readiness(self, data_dir: str) -> dict[str, Any]:
        """
        Fine-tuning 준비 상태 확인

        Args:
            data_dir: 데이터 디렉토리

        Returns:
            준비 상태 dict
        """
        approved_dir = Path(data_dir) / "approved"

        if not approved_dir.exists():
            return {"ready": False, "reason": "No approved data directory found"}

        # 승인된 원고 수 카운트
        approved_files = list(approved_dir.glob("*.json"))
        approved_count = len(approved_files)

        # 최소 100개 필요
        min_required = 100

        readiness = {
            "ready": approved_count >= min_required,
            "approved_count": approved_count,
            "min_required": min_required,
            "data_dir": str(approved_dir),
        }

        if approved_count < min_required:
            readiness["reason"] = (
                f"Insufficient data: {approved_count}/{min_required}. "
                f"Collect {min_required - approved_count} more manuscripts."
            )
        else:
            readiness["message"] = "Ready for fine-tuning!"

        return readiness

    def prepare_training_data(self, data_dir: str, output_file: str = None, max_samples: int = None) -> str:
        """
        학습 데이터 준비

        Args:
            data_dir: 데이터 디렉토리
            output_file: 출력 파일 경로 (선택적)
            max_samples: 최대 샘플 수 (선택적)

        Returns:
            출력 파일 경로
        """
        if output_file is None:
            output_file = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

        approved_dir = Path(data_dir) / "approved"
        approved_files = list(approved_dir.glob("*.json"))

        if max_samples:
            approved_files = approved_files[:max_samples]

        with open(output_file, "w", encoding="utf-8") as out:
            for file in approved_files:
                try:
                    with open(file, encoding="utf-8") as f:
                        data = json.load(f)

                    # Gemini Fine-tuning 포맷
                    training_example = self._create_training_example(data)

                    out.write(json.dumps(training_example, ensure_ascii=False) + "\n")

                except Exception as e:
                    logging.warning(f"Error processing {file.name}: {e}")
                    continue

        logging.info(f"✅ Training data prepared: {output_file}")
        logging.info(f"Total samples: {len(approved_files)}")

        return output_file

    def _create_training_example(self, data: dict) -> dict:
        """학습 예제 생성"""
        context = data.get("validation_context", {})
        blueprint = context.get("blueprint", {})

        # 입력: 설계도 + 품질 기준
        text_input = self._create_training_prompt(blueprint)

        # 출력: 승인된 원고
        output = data.get("manuscript", "")

        return {"text_input": text_input, "output": output}

    def _create_training_prompt(self, blueprint: dict) -> str:
        """학습용 프롬프트 생성"""
        prompt = """다음 설계도에 따라 고품질 웹소설 원고를 작성하십시오.

## 설계도
"""
        prompt += json.dumps(blueprint, ensure_ascii=False, indent=2)

        prompt += """

## 품질 기준
- 분량: 4000자 이상
- 문장 리듬: 변화 있게 (CV 0.3-0.6)
- 어휘 다양성: TTR 0.3 이상
- 오감 묘사: 시각 편중 60% 미만
- Show Don't Tell: 직접 감정 서술 최소화
- 감정 몰입: 독자가 공감할 수 있게
- 상업성: 다음 화를 기대하게 만들기
- 클리셰 회피: 신선한 전개

## 요구사항
위 기준을 모두 만족하는 원고를 작성하십시오:
"""
        return prompt

    def start_fine_tuning_job(
        self, training_file: str, tuned_model_name: str = None, learning_rate: float = 0.001, epochs: int = 3
    ) -> dict[str, Any]:
        """
        Fine-tuning 작업 시작

        Args:
            training_file: 학습 데이터 파일
            tuned_model_name: 튜닝된 모델 이름
            learning_rate: 학습률
            epochs: 에폭 수

        Returns:
            작업 정보 dict
        """
        if tuned_model_name is None:
            tuned_model_name = f"{self.project_name}_finetuned_{datetime.now().strftime('%Y%m%d')}"

        job_info = {
            "job_id": f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "base_model": self.base_model,
            "tuned_model_name": tuned_model_name,
            "training_file": training_file,
            "hyperparameters": {"learning_rate": learning_rate, "epochs": epochs},
            "status": "PREPARING",
            "created_at": datetime.now().isoformat(),
        }

        self.training_jobs.append(job_info)

        logging.info(f"🚀 Fine-tuning job created: {job_info['job_id']}")
        logging.info(f"Base model: {self.base_model}")
        logging.info(f"Tuned model: {tuned_model_name}")
        logging.info(f"Training file: {training_file}")
        logging.info("")
        logging.info("⚠️ IMPORTANT: Gemini Fine-tuning requires API access.")
        logging.info("To start actual training, use Google AI Studio:")
        logging.info("https://aistudio.google.com/app/tuned_models")
        logging.info("")
        logging.info("Upload the training file and configure:")
        logging.info(f"- Base model: {self.base_model}")
        logging.info(f"- Learning rate: {learning_rate}")
        logging.info(f"- Epochs: {epochs}")

        return job_info

    def estimate_cost(self, num_samples: int, epochs: int = 3) -> dict[str, float]:
        """
        Fine-tuning 비용 추정

        Args:
            num_samples: 샘플 수
            epochs: 에폭 수

        Returns:
            비용 추정 dict
        """
        # Gemini Fine-tuning 비용 (2024 기준)
        # 실제 비용은 Google AI Studio에서 확인 필요

        cost_per_1k_samples = 0.5  # 예상 비용 (USD)
        total_training_samples = num_samples * epochs

        estimated_cost = (total_training_samples / 1000) * cost_per_1k_samples

        return {
            "num_samples": num_samples,
            "epochs": epochs,
            "total_training_samples": total_training_samples,
            "estimated_cost_usd": estimated_cost,
            "estimated_cost_krw": estimated_cost * 1300,
            "note": "실제 비용은 Google AI Studio에서 확인하세요",
        }

    def validate_training_data(self, training_file: str) -> dict[str, Any]:
        """
        학습 데이터 유효성 검증

        Args:
            training_file: 학습 데이터 파일

        Returns:
            검증 결과 dict
        """
        issues = []
        samples = []

        try:
            with open(training_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        sample = json.loads(line)

                        # 필수 필드 확인
                        if "text_input" not in sample:
                            issues.append(f"Line {line_num}: Missing 'text_input'")
                        if "output" not in sample:
                            issues.append(f"Line {line_num}: Missing 'output'")

                        # 길이 확인
                        if len(sample.get("output", "")) < 1000:
                            issues.append(f"Line {line_num}: Output too short ({len(sample.get('output', ''))} chars)")

                        samples.append(sample)

                    except json.JSONDecodeError:
                        issues.append(f"Line {line_num}: Invalid JSON")

        except FileNotFoundError:
            return {"valid": False, "error": "File not found"}

        return {
            "valid": len(issues) == 0,
            "num_samples": len(samples),
            "issues": issues,
            "avg_input_length": sum(len(s.get("text_input", "")) for s in samples) / len(samples) if samples else 0,
            "avg_output_length": sum(len(s.get("output", "")) for s in samples) / len(samples) if samples else 0,
        }

    def generate_fine_tuning_report(self, data_dir: str, output_file: str = "finetuning_report.txt") -> str:
        """
        Fine-tuning 준비 리포트 생성

        Args:
            data_dir: 데이터 디렉토리
            output_file: 출력 파일

        Returns:
            리포트 텍스트
        """
        readiness = self.check_readiness(data_dir)

        report = []
        report.append("=" * 80)
        report.append("FINE-TUNING READINESS REPORT")
        report.append("=" * 80)
        report.append(f"Project: {self.project_name}")
        report.append(f"Base Model: {self.base_model}")
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("--- Data Readiness ---")
        report.append(f"Status: {'✅ READY' if readiness['ready'] else '⚠️ NOT READY'}")
        report.append(f"Approved Manuscripts: {readiness['approved_count']}")
        report.append(f"Required Minimum: {readiness['min_required']}")

        if not readiness["ready"]:
            report.append(f"Reason: {readiness['reason']}")
        else:
            report.append(f"Message: {readiness['message']}")

        report.append("")

        # 비용 추정
        if readiness["ready"]:
            cost = self.estimate_cost(readiness["approved_count"])
            report.append("--- Cost Estimation ---")
            report.append(f"Training Samples: {cost['total_training_samples']:,}")
            report.append(f"Estimated Cost: ${cost['estimated_cost_usd']:.2f} USD")
            report.append(f"               ({cost['estimated_cost_krw']:.0f}원)")
            report.append(f"Note: {cost['note']}")
            report.append("")

        # 다음 단계
        report.append("--- Next Steps ---")
        if readiness["ready"]:
            report.append("1. Run: manager.prepare_training_data(data_dir)")
            report.append("2. Validate: manager.validate_training_data(training_file)")
            report.append("3. Upload to Google AI Studio")
            report.append("4. Configure and start training")
            report.append("5. Deploy tuned model")
        else:
            report.append("1. Continue collecting approved manuscripts")
            report.append(f"2. Target: {readiness['min_required']} approved manuscripts")
            report.append("3. Run this report again when ready")

        report.append("=" * 80)

        report_text = "\n".join(report)

        # 파일 저장
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_text)

        return report_text


class FineTuningMonitor:
    """
    Fine-tuning 작업 모니터링

    학습 진행 상황과 성능 추적
    """

    def __init__(self, project_name: str):
        """
        Args:
            project_name: 프로젝트 이름
        """
        self.project_name = project_name
        self.metrics_log = []

    def log_training_metrics(self, epoch: int, loss: float, validation_loss: float = None):
        """학습 메트릭 로그"""
        metric = {
            "epoch": epoch,
            "loss": loss,
            "validation_loss": validation_loss,
            "timestamp": datetime.now().isoformat(),
        }

        self.metrics_log.append(metric)

    def compare_base_vs_tuned(self, base_results: list[dict], tuned_results: list[dict]) -> dict[str, Any]:
        """
        기본 모델 vs 튜닝 모델 성능 비교

        Args:
            base_results: 기본 모델 결과
            tuned_results: 튜닝 모델 결과

        Returns:
            비교 결과 dict
        """
        from modules.core.prompt_optimizer import PromptOptimizer

        optimizer = PromptOptimizer()

        base_analysis = optimizer.analyze_validation_results(base_results)
        tuned_analysis = optimizer.analyze_validation_results(tuned_results)

        comparison = {
            "base_model": {
                "avg_score": base_analysis["avg_score"],
                "pass_rate": base_analysis["pass_rate"],
                "std_dev": base_analysis["std_dev"],
            },
            "tuned_model": {
                "avg_score": tuned_analysis["avg_score"],
                "pass_rate": tuned_analysis["pass_rate"],
                "std_dev": tuned_analysis["std_dev"],
            },
            "improvements": {
                "score_improvement": tuned_analysis["avg_score"] - base_analysis["avg_score"],
                "pass_rate_improvement": tuned_analysis["pass_rate"] - base_analysis["pass_rate"],
                "consistency_improvement": base_analysis["std_dev"] - tuned_analysis["std_dev"],
            },
        }

        # ROI 계산 (간단 버전)
        if comparison["improvements"]["score_improvement"] > 5:
            comparison["roi"] = "HIGH - Fine-tuning significantly improved performance"
        elif comparison["improvements"]["score_improvement"] > 2:
            comparison["roi"] = "MEDIUM - Fine-tuning moderately improved performance"
        else:
            comparison["roi"] = "LOW - Fine-tuning had minimal impact"

        return comparison


# 편의 함수
def quick_finetuning_check(project_name: str, data_dir: str) -> str:
    """
    빠른 Fine-tuning 준비 확인

    Args:
        project_name: 프로젝트 이름
        data_dir: 데이터 디렉토리

    Returns:
        리포트 텍스트
    """
    manager = FineTuningManager(project_name)
    report = manager.generate_fine_tuning_report(data_dir)
    logging.info(report)
    return report
