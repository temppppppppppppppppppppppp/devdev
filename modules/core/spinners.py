"""
[V65] Spinner 유틸리티 및 공유 전역 상수 — 순환 참조 해소용 모듈

stage2_orchestrator / stage4_orchestrator가 main_a.py를 역참조하던
순환 의존을 끊기 위해, 공통으로 필요한 객체를 이곳에 모읍니다.

포함 항목:
- rich_console : 전역 Rich Console 인스턴스
- FancySpinner : Claude Code 스타일 스피너
- StageSpinner : Stage별 테마 스피너 (파도치는 그라데이션)
- V50_MODULES_AVAILABLE : V50 서사 품질 모듈 로드 여부 (main_a.py가 설정)
- STAGE0_AVAILABLE      : Stage 0 모듈 로드 여부 (main_a.py가 설정)
"""

import threading
import time

from rich.console import Console
from rich.live import Live
from rich.text import Text

# ─────────────────────────────────────────────────────────────────────
# [V60.47] 전역 Rich 콘솔 (스피너용)
# ─────────────────────────────────────────────────────────────────────
rich_console = Console()

# ─────────────────────────────────────────────────────────────────────
# [V65] 모듈 가용성 플래그 — main_a.py 초기화 시 올바른 값으로 설정됨
# ─────────────────────────────────────────────────────────────────────
V50_MODULES_AVAILABLE: bool = False
STAGE0_AVAILABLE: bool = False


# ─────────────────────────────────────────────────────────────────────
# [V60.75] 멋진 스피너 클래스
# ─────────────────────────────────────────────────────────────────────
class FancySpinner:
    """Claude Code 스타일 스피너 - 전체 시간 + 현재 작업 시간 표시"""

    _session_start = None  # 세션 시작 시간 (클래스 변수)

    def __init__(self, task_name: str, console: Console = None):
        self.task_name = task_name
        self.console = console or rich_console
        self.task_start = None
        self.live = None
        self._stop_event = threading.Event()
        self._thread = None

        # 세션 시작 시간 초기화 (최초 1회)
        if FancySpinner._session_start is None:
            FancySpinner._session_start = time.time()

    def _format_time(self, seconds: float) -> str:
        """시간을 m s 또는 s 형식으로 포맷"""
        if seconds >= 60:
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m}m {s}s"
        return f"{int(seconds)}s"

    def _render(self) -> str:
        """스피너 텍스트 렌더링"""
        now = time.time()
        session_elapsed = now - FancySpinner._session_start
        task_elapsed = now - self.task_start if self.task_start else 0

        return (
            f"[bold orange1]✽[/] [orange1]{self.task_name}[/] "
            f"[dim](전체: {self._format_time(session_elapsed)} · "
            f"현재: {self._format_time(task_elapsed)})[/]"
        )

    def _update_loop(self) -> None:
        """백그라운드에서 Live 업데이트"""
        while not self._stop_event.is_set():
            if self.live:
                self.live.update(self._render())
            time.sleep(0.5)

    def __enter__(self):
        self.task_start = time.time()
        self.live = Live(self._render(), console=self.console, refresh_per_second=2, transient=True)
        self.live.__enter__()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)
        return False


# ─────────────────────────────────────────────────────────────────────
# [V60.83] Stage별 테마 스피너 (파도치는 색상)
# ─────────────────────────────────────────────────────────────────────
class StageSpinner:
    """
    각 Stage별 고유 테마를 가진 스피너 (파도치는 그라데이션)

    Stage 0: 📚 Bible/Setup - 책/설정 테마 (purple wave)
    Stage 1: 📜 Volume Strategy - 고대 두루마리 테마 (gold wave)
    Stage 2: ⚔️ Arc Design - 전투/전략 테마 (red wave)
    Stage 3: 📐 Blueprint - 설계도 테마 (cyan wave)
    Stage 4: ✍️ Manuscript - 집필 테마 (green wave)
    """

    # 파도치는 색상 팔레트
    WAVE_PALETTES = {
        "purple": ["#E1BEE7", "#CE93D8", "#BA68C8", "#AB47BC", "#9C27B0", "#8E24AA", "#7B1FA2", "#6A1B9A"],
        "gold": ["#FFF8E1", "#FFECB3", "#FFE082", "#FFD54F", "#FFCA28", "#FFC107", "#FFB300", "#FFA000"],
        "red": ["#FFCDD2", "#EF9A9A", "#E57373", "#EF5350", "#F44336", "#E53935", "#D32F2F", "#C62828"],
        "cyan": ["#E0F7FA", "#B2EBF2", "#80DEEA", "#4DD0E1", "#26C6DA", "#00BCD4", "#00ACC1", "#0097A7"],
        "green": ["#E8F5E9", "#C8E6C9", "#A5D6A7", "#81C784", "#66BB6A", "#4CAF50", "#43A047", "#388E3C"],
    }

    STAGE_THEMES = {
        0: {
            "name": "Bible & Setup",
            "base_color": "magenta",
            "wave_palette": "purple",
            "frames": ["📚", "📖", "🔮", "✨", "💫", "🌟"],
            "verbs": ["Bible 로딩 중", "설정 추출 중", "스타일 분석 중", "프리셋 활성화 중", "DNA 동기화 중"],
        },
        1: {
            "name": "Volume Strategy",
            "base_color": "yellow",
            "wave_palette": "gold",
            "frames": ["📜", "📖", "📚", "📖", "✨", "💫"],
            "verbs": ["두루마리 펼치는 중", "대서사시 구상 중", "권별 전략 수립 중", "운명의 실 엮는 중"],
        },
        2: {
            "name": "Arc Design",
            "base_color": "red",
            "wave_palette": "red",
            "frames": ["⚔️", "🗡️", "🛡️", "⚔️", "💥", "🔥"],
            "verbs": ["전술 설계 중", "Arc 용접 중", "인과율 계산 중", "욕망 주입 중", "서사 단조 중"],
        },
        3: {
            "name": "Blueprint",
            "base_color": "cyan",
            "wave_palette": "cyan",
            "frames": ["📐", "📏", "🔧", "⚙️", "💎", "🌊"],
            "verbs": ["설계도 제도 중", "씬 배치 중", "연속성 체크 중", "정밀 조립 중", "밀도 계산 중"],
        },
        4: {
            "name": "Manuscript",
            "base_color": "green",
            "wave_palette": "green",
            "frames": ["✍️", "🖋️", "📝", "✒️", "💚", "🌿"],
            "verbs": ["원고 집필 중", "문장 조탁 중", "서사 직조 중", "영혼 불어넣는 중", "독자 마법 걸기 중"],
        },
    }

    _session_start = None

    def __init__(self, stage: int, task_detail: str = "", console: Console = None):
        self.stage = stage
        self.task_detail = task_detail
        self.theme = self.STAGE_THEMES.get(stage, self.STAGE_THEMES[1])
        self.wave_palette = self.WAVE_PALETTES.get(self.theme.get("wave_palette", "cyan"), self.WAVE_PALETTES["cyan"])
        self.console = console or rich_console
        self.task_start = None
        self.live = None
        self._stop_event = threading.Event()
        self._thread = None
        self._frame_idx = 0
        self._verb_idx = 0
        self._wave_offset = 0

        if StageSpinner._session_start is None:
            StageSpinner._session_start = time.time()

    def _format_time(self, seconds: float) -> str:
        if seconds >= 60:
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m}m {s}s"
        return f"{int(seconds)}s"

    def _wave_text(self, text: str) -> Text:
        """파도치는 색상 텍스트 생성"""
        result = Text()
        for i, char in enumerate(text):
            color_idx = (i + self._wave_offset) % len(self.wave_palette)
            result.append(char, style=f"{self.wave_palette[color_idx]}")
        return result

    def _render(self) -> Text:
        now = time.time()
        now - StageSpinner._session_start
        task_elapsed = now - self.task_start if self.task_start else 0

        # [V61.2] 클로드 스타일 미니멀 스피너
        # 펄스 도트 애니메이션
        pulse_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        pulse = pulse_frames[self._frame_idx % len(pulse_frames)]

        # 색상 그라데이션 펄스 (밝기 변화)
        color_cycle = [
            "#6366f1",  # indigo
            "#818cf8",  # lighter
            "#a5b4fc",  # lightest
            "#818cf8",  # lighter
            "#6366f1",  # indigo
            "#4f46e5",  # darker
            "#4338ca",  # darkest
            "#4f46e5",  # darker
        ]
        current_color = color_cycle[self._wave_offset % len(color_cycle)]

        detail = self.task_detail if self.task_detail else self.theme["verbs"][0]

        # 심플한 구성: [펄스] 작업내용 · 시간
        result = Text()
        result.append(f" {pulse} ", style=f"bold {current_color}")
        result.append(f"{detail}", style=f"{current_color}")
        result.append("  ", style="dim")
        result.append(f"{self._format_time(task_elapsed)}", style="dim #888888")

        self._wave_offset += 1
        return result

    def _update_loop(self) -> None:
        tick = 0
        while not self._stop_event.is_set():
            if self.live:
                self.live.update(self._render())
            time.sleep(0.3)
            tick += 1
            if tick % 2 == 0:
                self._frame_idx += 1
            if tick % 8 == 0:
                self._verb_idx += 1

    def __enter__(self):
        self.task_start = time.time()
        # [V61.2] 스피너 가시성 개선:
        # - redirect_stdout/stderr: print()가 스피너 위에 표시됨
        # - transient=True: 완료 후 깔끔하게 사라짐
        self.live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=4,
            transient=True,
            redirect_stdout=True,
            redirect_stderr=True,
        )
        self.live.__enter__()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)
        return False

    def update_detail(self, new_detail: str):
        """작업 상세 정보 업데이트"""
        self.task_detail = new_detail
