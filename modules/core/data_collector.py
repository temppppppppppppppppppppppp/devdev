"""
[Phase 2] Data Collection System

Fine-tuning 및 RLHF를 위한 데이터 수집
고품질 원고와 검증 결과를 체계적으로 저장
"""

import hashlib
import json
import logging
import os
import re
import threading
from datetime import datetime


class DataCollector:
    """
    Fine-tuning 데이터 수집기

    승인된 원고, 거부된 원고, 검증 결과를 저장하여
    향후 모델 학습에 활용
    """

    def __init__(self, project_name: str, output_dir: str = "datasets"):
        """
        Args:
            project_name: 프로젝트 이름
            output_dir: 데이터 저장 디렉토리
        """
        # 🔒 Path Traversal 방지 - project_name 검증
        safe_project_name = re.sub(r"[^a-zA-Z0-9_\-가-힣]", "", project_name)
        if not safe_project_name or safe_project_name != project_name:
            raise ValueError(
                f"[SECURITY] Invalid project name: '{project_name}'. "
                f"Only alphanumeric, underscore, hyphen, and Korean characters allowed."
            )

        self.project_name = safe_project_name
        self.output_dir = output_dir
        self.project_dir = os.path.join(output_dir, project_name)

        # 🔒 Path Traversal 방지 - 실제 경로 검증
        real_project_dir = os.path.realpath(self.project_dir)
        real_output_dir = os.path.realpath(output_dir)
        if not real_project_dir.startswith(real_output_dir):
            raise ValueError(
                f"[SECURITY] Path traversal detected: project_name='{project_name}'. "
                f"Resolved path '{real_project_dir}' escapes output directory '{real_output_dir}'."
            )

        # Thread-safe file operations
        self._lock = threading.Lock()

        # [V44] 시퀀스 카운터 (UUID 충돌 방지 추가 보호)
        self._sequence_counter = 0

        # 디렉토리 생성
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "approved"), exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "rejected"), exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "training_pairs"), exist_ok=True)

        # 통계
        self.stats = {"approved_count": 0, "rejected_count": 0, "total_collected": 0}

    def collect_validation_result(
        self, ep_num: int, manuscript: str, validation_result: dict, validation_context: dict = None
    ):
        """
        검증 결과 수집

        Args:
            ep_num: 에피소드 번호
            manuscript: 원고 텍스트
            validation_result: 검증 결과 dict
            validation_context: 검증 컨텍스트 (선택적)
        """
        decision = validation_result.get("final_decision", validation_result.get("decision", "UNKNOWN"))

        data = {
            "ep_num": ep_num,
            "manuscript": manuscript,
            "manuscript_length": len(manuscript),
            "manuscript_hash": self._hash_text(manuscript),
            "validation_result": validation_result,
            "validation_context": validation_context,
            "timestamp": datetime.now().isoformat(),
            "project": self.project_name,
        }

        # PASS/REJECT에 따라 분류 저장
        if decision in ["PASS", "CONDITIONAL_PASS"]:
            self._save_approved(ep_num, data)
            self.stats["approved_count"] += 1
        elif decision == "REJECT":
            self._save_rejected(ep_num, data)
            self.stats["rejected_count"] += 1

        self.stats["total_collected"] += 1

    def _save_approved(self, ep_num: int, data: dict):
        """
        승인된 원고 저장 (Thread-safe, 버전 관리 포함)

        🔒 Race Condition 완전 해결: 항상 고유 파일명 사용
        """
        with self._lock:  # 🔒 Critical section
            # 🔒 Race Condition 방지: 밀리초 + 시퀀스 + UUID로 고유 파일명 생성
            import uuid

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # ms
            self._sequence_counter += 1
            unique_id = f"{self._sequence_counter:04d}_{uuid.uuid4().hex[:8]}"

            # 항상 버전 관리된 파일명 사용 (TOCTOU 취약점 완전 제거)
            versioned_filename = f"ep_{ep_num:03d}_approved_{timestamp}_{unique_id}.json"
            filepath = os.path.join(self.project_dir, "approved", versioned_filename)

            # Atomic write (임시 파일 → rename)
            # [V44] temp_filepath를 try 밖에서 정의하여 finally에서 안전하게 접근
            temp_filepath = filepath + ".tmp"
            try:
                with open(temp_filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Atomic rename (Windows: 기존 파일 삭제 후)
                if os.name == "nt" and os.path.exists(filepath):
                    os.remove(filepath)
                os.rename(temp_filepath, filepath)

            except OSError as e:
                logging.warning(f"[WARNING] 파일 저장 실패 ({filepath}): {e}")
                # 임시 파일 정리
                if os.path.exists(temp_filepath):
                    try:
                        os.remove(temp_filepath)
                    except OSError as cleanup_err:
                        logging.warning(f"[DEBUG] 임시 파일 정리 실패: {cleanup_err}")
                raise

    def _save_rejected(self, ep_num: int, data: dict):
        """
        거부된 원고 저장 (Thread-safe, 버전 관리 포함)

        🔒 Race Condition 완전 해결: 항상 고유 파일명 사용
        """
        with self._lock:  # 🔒 Critical section
            # 🔒 Race Condition 방지: 밀리초 + 시퀀스 + UUID로 고유 파일명 생성
            import uuid

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # ms
            self._sequence_counter += 1
            unique_id = f"{self._sequence_counter:04d}_{uuid.uuid4().hex[:8]}"

            # 항상 버전 관리된 파일명 사용 (TOCTOU 취약점 완전 제거)
            versioned_filename = f"ep_{ep_num:03d}_rejected_{timestamp}_{unique_id}.json"
            filepath = os.path.join(self.project_dir, "rejected", versioned_filename)

            # Atomic write (임시 파일 → rename)
            # [V44] temp_filepath를 try 밖에서 정의하여 finally에서 안전하게 접근
            temp_filepath = filepath + ".tmp"
            try:
                with open(temp_filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Atomic rename (Windows: 기존 파일 삭제 후)
                if os.name == "nt" and os.path.exists(filepath):
                    os.remove(filepath)
                os.rename(temp_filepath, filepath)

            except OSError as e:
                logging.warning(f"[WARNING] 파일 저장 실패 ({filepath}): {e}")
                # 임시 파일 정리
                if os.path.exists(temp_filepath):
                    try:
                        os.remove(temp_filepath)
                    except OSError as cleanup_err:
                        logging.warning(f"[DEBUG] 임시 파일 정리 실패: {cleanup_err}")
                raise

    def create_training_pair(self, ep_num: int, bad_manuscript: str, good_manuscript: str, feedback: str):
        """
        Fine-tuning용 학습 쌍 생성

        Args:
            ep_num: 에피소드 번호
            bad_manuscript: 거부된 원고 (Before)
            good_manuscript: 승인된 원고 (After)
            feedback: 개선 피드백
        """
        pair = {
            "ep_num": ep_num,
            "before": bad_manuscript,
            "after": good_manuscript,
            "feedback": feedback,
            "improvement": {
                "length_change": len(good_manuscript) - len(bad_manuscript),
                "before_hash": self._hash_text(bad_manuscript),
                "after_hash": self._hash_text(good_manuscript),
            },
            "timestamp": datetime.now().isoformat(),
        }

        filename = f"pair_ep_{ep_num:03d}.json"
        filepath = os.path.join(self.project_dir, "training_pairs", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(pair, f, indent=2, ensure_ascii=False)

    def export_for_finetuning(self, output_file: str = None) -> str:
        """
        Fine-tuning용 JSONL 포맷으로 export

        Gemini Fine-tuning API 호환 포맷

        Args:
            output_file: 출력 파일 경로 (선택적)

        Returns:
            출력 파일 경로
        """
        if output_file is None:
            output_file = os.path.join(
                self.project_dir, f"finetuning_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            )

        # 승인된 원고 로드
        approved_dir = os.path.join(self.project_dir, "approved")
        approved_files = [f for f in os.listdir(approved_dir) if f.endswith(".json")]

        with open(output_file, "w", encoding="utf-8") as out:
            for filename in approved_files:
                filepath = os.path.join(approved_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)

                # Gemini Fine-tuning 포맷
                training_example = {"text_input": self._create_training_prompt(data), "output": data["manuscript"]}

                out.write(json.dumps(training_example, ensure_ascii=False) + "\n")

        return output_file

    def _create_training_prompt(self, data: dict) -> str:
        """
        학습용 프롬프트 생성

        Args:
            data: 원고 데이터

        Returns:
            프롬프트 문자열
        """
        context = data.get("validation_context", {})
        blueprint = context.get("blueprint", {})

        prompt = f"""다음 설계도에 따라 고품질 웹소설 원고를 작성하십시오.

## 설계도
{json.dumps(blueprint, ensure_ascii=False, indent=2)}

## 품질 기준
- 분량: 4000자 이상
- 문장 리듬: 변화 있게
- 어휘 다양성: TTR 0.3 이상
- 감정 몰입: 독자가 공감할 수 있게
- 상업성: 다음 화를 기대하게 만들기

## 요구사항
원고를 작성하십시오:
"""
        return prompt

    def _hash_text(self, text: str) -> str:
        """텍스트 해시 생성 (중복 체크용)"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]

    def get_statistics(self) -> dict:
        """수집 통계 반환"""
        return {
            "project": self.project_name,
            "approved_count": self.stats["approved_count"],
            "rejected_count": self.stats["rejected_count"],
            "total_collected": self.stats["total_collected"],
            "approval_rate": (
                self.stats["approved_count"] / self.stats["total_collected"] if self.stats["total_collected"] > 0 else 0
            ),
        }

    def generate_report(self) -> str:
        """수집 리포트 생성"""
        stats = self.get_statistics()

        report = []
        report.append("=" * 60)
        report.append("DATA COLLECTION REPORT")
        report.append("=" * 60)
        report.append(f"Project: {stats['project']}")
        report.append(f"Total Collected: {stats['total_collected']}")
        report.append(f"Approved: {stats['approved_count']}")
        report.append(f"Rejected: {stats['rejected_count']}")
        report.append(f"Approval Rate: {stats['approval_rate']:.1%}")
        report.append("")
        report.append(f"Data Directory: {self.project_dir}")
        report.append("=" * 60)

        return "\n".join(report)


class RLHFCollector:
    """
    RLHF (Reinforcement Learning from Human Feedback) 데이터 수집기

    인간 편집자의 피드백을 수집하여 보상 모델 학습
    """

    def __init__(self, project_name: str, output_dir: str = "rlhf_data"):
        """
        Args:
            project_name: 프로젝트 이름
            output_dir: 데이터 저장 디렉토리
        """
        # 🔒 Path Traversal 방지 - project_name 검증
        safe_project_name = re.sub(r"[^a-zA-Z0-9_\-가-힣]", "", project_name)
        if not safe_project_name or safe_project_name != project_name:
            raise ValueError(
                f"[SECURITY] Invalid project name: '{project_name}'. "
                f"Only alphanumeric, underscore, hyphen, and Korean characters allowed."
            )

        self.project_name = safe_project_name
        self.output_dir = output_dir
        self.project_dir = os.path.join(output_dir, project_name)

        # 🔒 Path Traversal 방지 - 실제 경로 검증
        real_project_dir = os.path.realpath(self.project_dir)
        real_output_dir = os.path.realpath(output_dir)
        if not real_project_dir.startswith(real_output_dir):
            raise ValueError(
                f"[SECURITY] Path traversal detected: project_name='{project_name}'. "
                f"Resolved path '{real_project_dir}' escapes output directory '{real_output_dir}'."
            )

        os.makedirs(self.project_dir, exist_ok=True)

        self.feedback_log = []

    def collect_feedback(
        self,
        ep_num: int,
        manuscript: str,
        ai_score: int,
        human_score: int,
        human_feedback: str,
        human_decision: str,  # "APPROVE" | "REJECT" | "REVISE"
    ):
        """
        인간 편집자 피드백 수집

        Args:
            ep_num: 에피소드 번호
            manuscript: 원고
            ai_score: AI 평가 점수
            human_score: 인간 평가 점수
            human_feedback: 인간 피드백
            human_decision: 인간 판정
        """
        feedback = {
            "ep_num": ep_num,
            "manuscript_hash": hashlib.md5(manuscript.encode("utf-8")).hexdigest()[:16],
            "ai_score": ai_score,
            "human_score": human_score,
            "score_difference": human_score - ai_score,
            "human_feedback": human_feedback,
            "human_decision": human_decision,
            "timestamp": datetime.now().isoformat(),
        }

        self.feedback_log.append(feedback)

        # 즉시 저장
        filename = f"feedback_ep_{ep_num:03d}.json"
        filepath = os.path.join(self.project_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(feedback, f, indent=2, ensure_ascii=False)

    def export_for_rlhf(self, output_file: str = None) -> str:
        """
        RLHF 학습용 데이터 export

        Args:
            output_file: 출력 파일 경로

        Returns:
            출력 파일 경로
        """
        if output_file is None:
            output_file = os.path.join(self.project_dir, f"rlhf_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")

        with open(output_file, "w", encoding="utf-8") as out:
            for feedback in self.feedback_log:
                out.write(json.dumps(feedback, ensure_ascii=False) + "\n")

        return output_file

    def analyze_disagreement(self) -> dict:
        """
        AI와 인간의 의견 불일치 분석

        Returns:
            분석 결과 dict
        """
        if not self.feedback_log:
            return {"error": "No feedback collected"}

        score_diffs = [f["score_difference"] for f in self.feedback_log]
        avg_diff = sum(score_diffs) / len(score_diffs)

        # AI가 과대평가한 경우
        overestimated = [f for f in self.feedback_log if f["score_difference"] < -10]

        # AI가 과소평가한 경우
        underestimated = [f for f in self.feedback_log if f["score_difference"] > 10]

        return {
            "total_feedback": len(self.feedback_log),
            "avg_score_difference": avg_diff,
            "overestimated_count": len(overestimated),
            "underestimated_count": len(underestimated),
            "agreement_rate": (
                len([f for f in self.feedback_log if abs(f["score_difference"]) <= 10]) / len(self.feedback_log)
            ),
        }


# 편의 함수
def auto_collect_from_validation(
    collector: DataCollector, ep_num: int, manuscript: str, validation_result: dict, validation_context: dict = None
):
    """
    검증 결과를 자동으로 수집

    Args:
        collector: DataCollector instance
        ep_num: 에피소드 번호
        manuscript: 원고
        validation_result: 검증 결과
        validation_context: 검증 컨텍스트
    """
    collector.collect_validation_result(
        ep_num=ep_num, manuscript=manuscript, validation_result=validation_result, validation_context=validation_context
    )
