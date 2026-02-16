"""
[V44] 진행상황 관리자

Rich 기반 진행 표시 및 상태 시각화
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class StageInfo:
    """스테이지 정보"""

    name: str
    description: str
    total_items: int = 0
    completed_items: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str = "pending"  # pending, in_progress, completed, failed


@dataclass
class EpisodeProgress:
    """에피소드 진행 정보"""

    ep_num: int
    stage: str
    status: str = "pending"
    start_time: datetime | None = None
    end_time: datetime | None = None
    retries: int = 0
    error: str | None = None


class ProgressManager:
    """
    [V44] 진행상황 관리자

    Features:
    - Rich progress bar 통합
    - 스테이지별 진행률 추적
    - 예상 소요 시간 계산
    - 실시간 상태 표시
    """

    # 스테이지 정의
    STAGES = {
        "phase0": StageInfo("Phase 0", "Bible Recovery & DNA Sync"),
        "stage1": StageInfo("Stage 1", "Volume Strategy (10권)"),
        "stage2": StageInfo("Stage 2", "Arc Tactical Design (50 arcs)"),
        "stage3": StageInfo("Stage 3", "Episode Blueprinting"),
        "stage4": StageInfo("Stage 4", "Sovereign Production"),
    }

    def __init__(self, console: Optional["Console"] = None):
        """
        초기화

        Args:
            console: Rich Console 인스턴스 (없으면 새로 생성)
        """
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.stages: dict[str, StageInfo] = {k: StageInfo(v.name, v.description) for k, v in self.STAGES.items()}
        self.current_stage: str | None = None
        self.episode_history: list[EpisodeProgress] = []
        self._progress: Progress | None = None
        self._task_ids: dict[str, TaskID] = {}

        # 성능 통계
        self._stage_durations: dict[str, list[float]] = {}

    def start_stage(self, stage_key: str, total_items: int = 0):
        """
        스테이지 시작

        Args:
            stage_key: 스테이지 키 (phase0, stage1, ...)
            total_items: 총 처리할 항목 수
        """
        if stage_key not in self.stages:
            return

        stage = self.stages[stage_key]
        stage.status = "in_progress"
        stage.start_time = datetime.now()
        stage.total_items = total_items
        stage.completed_items = 0
        self.current_stage = stage_key

        self._print_stage_header(stage)

    def update_stage(self, stage_key: str, completed: int = None, increment: int = 1):
        """
        스테이지 진행률 업데이트

        Args:
            stage_key: 스테이지 키
            completed: 완료 항목 수 (직접 설정)
            increment: 증가량 (completed가 None일 때)
        """
        if stage_key not in self.stages:
            return

        stage = self.stages[stage_key]
        if completed is not None:
            stage.completed_items = completed
        else:
            stage.completed_items += increment

        self._update_progress_bar(stage_key)

    def complete_stage(self, stage_key: str, success: bool = True):
        """
        스테이지 완료

        Args:
            stage_key: 스테이지 키
            success: 성공 여부
        """
        if stage_key not in self.stages:
            return

        stage = self.stages[stage_key]
        stage.status = "completed" if success else "failed"
        stage.end_time = datetime.now()

        # 소요 시간 기록
        if stage.start_time:
            duration = (stage.end_time - stage.start_time).total_seconds()
            if stage_key not in self._stage_durations:
                self._stage_durations[stage_key] = []
            self._stage_durations[stage_key].append(duration)

        self._print_stage_completion(stage, success)

    def start_episode(self, ep_num: int, stage: str):
        """에피소드 처리 시작"""
        progress = EpisodeProgress(ep_num=ep_num, stage=stage, status="in_progress", start_time=datetime.now())
        self.episode_history.append(progress)
        return progress

    def complete_episode(self, ep_num: int, success: bool = True, error: str = None):
        """에피소드 처리 완료"""
        for progress in reversed(self.episode_history):
            if progress.ep_num == ep_num and progress.status == "in_progress":
                progress.status = "completed" if success else "failed"
                progress.end_time = datetime.now()
                progress.error = error
                break

    def get_estimated_time(self, stage_key: str, remaining_items: int) -> timedelta | None:
        """
        예상 남은 시간 계산

        Args:
            stage_key: 스테이지 키
            remaining_items: 남은 항목 수

        Returns:
            timedelta: 예상 남은 시간
        """
        if stage_key not in self._stage_durations:
            return None

        durations = self._stage_durations[stage_key]
        if not durations:
            return None

        # 평균 소요 시간 기반 추정
        avg_duration = sum(durations) / len(durations)
        estimated_seconds = avg_duration * remaining_items

        return timedelta(seconds=estimated_seconds)

    def _print_stage_header(self, stage: StageInfo):
        """스테이지 시작 헤더 출력"""
        if not RICH_AVAILABLE or not self.console:
            logging.info(f"\n{'=' * 60}")
            logging.info(f"{stage.name}: {stage.description}")
            logging.info(f"{'=' * 60}\n")
            return

        header = Panel(f"[bold]{stage.description}[/bold]", title=f"[cyan]{stage.name}[/cyan]", border_style="cyan")
        self.console.print(header)

    def _print_stage_completion(self, stage: StageInfo, success: bool):
        """스테이지 완료 메시지 출력"""
        duration = ""
        if stage.start_time and stage.end_time:
            delta = stage.end_time - stage.start_time
            duration = f" ({self._format_duration(delta)})"

        status_icon = "[OK]" if success else "[FAIL]"

        if not RICH_AVAILABLE or not self.console:
            logging.info(f"\n{status_icon} {stage.name} 완료{duration}")
            return

        color = "green" if success else "red"
        self.console.print(f"[{color}]{status_icon}[/{color}] {stage.name} 완료{duration}")

    def _update_progress_bar(self, stage_key: str):
        """진행률 바 업데이트 (Rich 사용 시)"""
        stage = self.stages.get(stage_key)
        if not stage or stage.total_items == 0:
            return

        percent = (stage.completed_items / stage.total_items) * 100

        if not RICH_AVAILABLE or not self.console:
            bar_width = 40
            filled = int(bar_width * stage.completed_items / stage.total_items)
            bar = "#" * filled + "-" * (bar_width - filled)
            logging.info(f"\r[{bar}] {percent:.1f}% ({stage.completed_items}/{stage.total_items})", end="")
            if stage.completed_items >= stage.total_items:
                logging.info()
            return

        # Rich 진행률 표시는 Live context에서 사용하는 것이 좋음
        # 여기서는 간단한 출력으로 대체
        self.console.print(f"  [{stage.completed_items}/{stage.total_items}] {percent:.1f}%", end="\r")

    def _format_duration(self, delta: timedelta) -> str:
        """시간 포맷팅"""
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초"

    def print_summary(self) -> None:
        """전체 진행 요약 출력"""
        if not RICH_AVAILABLE or not self.console:
            self._print_summary_text()
            return

        self._print_summary_rich()

    def _print_summary_text(self) -> None:
        """텍스트 기반 요약 출력"""
        logging.info("\n" + "=" * 60)
        logging.info("진행 요약")
        logging.info("=" * 60)

        for key, stage in self.stages.items():
            status_icon = {"pending": "[ ]", "in_progress": "[~]", "completed": "[O]", "failed": "[X]"}.get(
                stage.status, "[?]"
            )

            duration = ""
            if stage.start_time and stage.end_time:
                delta = stage.end_time - stage.start_time
                duration = f" - {self._format_duration(delta)}"

            logging.info(f"{status_icon} {stage.name}: {stage.description}{duration}")

        logging.info("=" * 60)

    def _print_summary_rich(self) -> None:
        """Rich 기반 요약 출력"""
        table = Table(title="진행 요약", show_header=True)
        table.add_column("스테이지", style="cyan")
        table.add_column("설명")
        table.add_column("상태", justify="center")
        table.add_column("소요시간", justify="right")

        for key, stage in self.stages.items():
            status_style = {
                "pending": "[dim]대기[/dim]",
                "in_progress": "[yellow]진행중[/yellow]",
                "completed": "[green]완료[/green]",
                "failed": "[red]실패[/red]",
            }.get(stage.status, "알 수 없음")

            duration = "-"
            if stage.start_time and stage.end_time:
                delta = stage.end_time - stage.start_time
                duration = self._format_duration(delta)

            table.add_row(stage.name, stage.description, status_style, duration)

        self.console.print(table)

    def get_stats(self) -> dict[str, Any]:
        """통계 정보 반환"""
        total_episodes = len(self.episode_history)
        successful = sum(1 for e in self.episode_history if e.status == "completed")
        failed = sum(1 for e in self.episode_history if e.status == "failed")
        total_retries = sum(e.retries for e in self.episode_history)

        return {
            "total_episodes": total_episodes,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_episodes * 100) if total_episodes > 0 else 0,
            "total_retries": total_retries,
            "stage_durations": self._stage_durations,
        }


# 전역 인스턴스
_progress_manager: ProgressManager | None = None


def get_progress_manager() -> ProgressManager:
    """전역 진행상황 관리자 반환"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager


def start_stage(stage_key: str, total_items: int = 0):
    """스테이지 시작 (단축형)"""
    get_progress_manager().start_stage(stage_key, total_items)


def update_stage(stage_key: str, completed: int = None, increment: int = 1):
    """스테이지 업데이트 (단축형)"""
    get_progress_manager().update_stage(stage_key, completed, increment)


def complete_stage(stage_key: str, success: bool = True):
    """스테이지 완료 (단축형)"""
    get_progress_manager().complete_stage(stage_key, success)


def print_summary() -> None:
    """요약 출력 (단축형)"""
    get_progress_manager().print_summary()
