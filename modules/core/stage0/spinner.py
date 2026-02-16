"""
Spinner & Progress Utils - 화려한 로딩 애니메이션
================================================
Rich 라이브러리 기반 파도치는 색상 + 덮어쓰기 방지
"""

import logging
import sys
import threading
import time
from itertools import cycle
from typing import Optional

# Rich 라이브러리 임포트
try:
    from rich import box
    from rich.color import Color
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
    from rich.style import Style
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 전역 콘솔
console = Console() if RICH_AVAILABLE else None


# ============================================
# 파도치는 그라데이션 색상 생성
# ============================================

WAVE_COLORS = [
    "#5BCEFA",  # 하늘색
    "#55CDFC",
    "#4FC3F7",
    "#42A5F5",
    "#3D9EE0",
    "#2196F3",  # 파랑
    "#1E88E5",
    "#1976D2",
    "#1565C0",
    "#0D47A1",
    "#1565C0",
    "#1976D2",
    "#1E88E5",
    "#2196F3",
    "#3D9EE0",
    "#42A5F5",
    "#4FC3F7",
    "#55CDFC",
]

FIRE_COLORS = [
    "#FFD54F",  # 노랑
    "#FFCA28",
    "#FFC107",
    "#FFB300",
    "#FFA000",
    "#FF8F00",
    "#FF6F00",
    "#F57C00",
    "#EF6C00",
    "#E65100",
    "#FF5722",  # 주황
    "#F4511E",
    "#E64A19",
    "#D84315",
    "#BF360C",
]

PURPLE_WAVE = [
    "#E1BEE7",
    "#CE93D8",
    "#BA68C8",
    "#AB47BC",
    "#9C27B0",
    "#8E24AA",
    "#7B1FA2",
    "#6A1B9A",
    "#4A148C",
    "#6A1B9A",
    "#7B1FA2",
    "#8E24AA",
    "#9C27B0",
    "#AB47BC",
    "#BA68C8",
    "#CE93D8",
]

RAINBOW_COLORS = [
    "#FF6B6B",
    "#FF8E53",
    "#FFCD38",
    "#7BED9F",
    "#70A1FF",
    "#5352ED",
    "#9B59B6",
    "#E056FD",
]


def create_wave_text(text: str, colors: list[str], offset: int = 0) -> Text:
    """파도치는 색상 텍스트 생성"""
    if not RICH_AVAILABLE:
        return text

    result = Text()
    for i, char in enumerate(text):
        color_idx = (i + offset) % len(colors)
        result.append(char, style=Style(color=colors[color_idx]))
    return result


def create_gradient_text(text: str, start_color: str = "#00D4FF", end_color: str = "#FF00FF") -> Text:
    """그라데이션 텍스트"""
    if not RICH_AVAILABLE:
        return text

    result = Text()
    length = len(text)

    # 색상 파싱
    sr, sg, sb = int(start_color[1:3], 16), int(start_color[3:5], 16), int(start_color[5:7], 16)
    er, eg, eb = int(end_color[1:3], 16), int(end_color[3:5], 16), int(end_color[5:7], 16)

    for i, char in enumerate(text):
        ratio = i / max(length - 1, 1)
        r = int(sr + (er - sr) * ratio)
        g = int(sg + (eg - sg) * ratio)
        b = int(sb + (eb - sb) * ratio)
        result.append(char, style=Style(color=f"#{r:02x}{g:02x}{b:02x}"))

    return result


# ============================================
# Rich 기반 화려한 스피너
# ============================================


class Spinner:
    """화려한 파도치는 스피너"""

    STYLES = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["—", "\\", "|", "/"],
        "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "bounce": ["⠁", "⠂", "⠄", "⠂"],
        "grow": ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"],
        "pulse": ["◜", "◠", "◝", "◞", "◡", "◟"],
        "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
        "earth": ["🌍", "🌎", "🌏"],
        "clock": ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"],
        "box": ["◰", "◳", "◲", "◱"],
        "triangle": ["◢", "◣", "◤", "◥"],
        "star": ["✶", "✸", "✹", "✺", "✹", "✸"],
        "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
        "simple": [".", "..", "...", "...."],
        "blocks": ["▖", "▘", "▝", "▗"],
        "meter": ["█", "█", "█", "▓", "▒", "░", "▒", "▓"],
        "wave": ["≋", "≈", "∼", "∽", "∿", "≀", "∿", "∽", "∼", "≈"],
        "sparkle": ["✧", "✦", "★", "✦", "✧", "⋆", "✧", "✦"],
        "fire": ["🔥", "🔥", "💥", "✨", "💫", "⭐", "💫", "✨", "💥"],
        "magic": ["✨", "💫", "⭐", "🌟", "💖", "🌟", "⭐", "💫"],
    }

    COLOR_THEMES = {
        "wave": WAVE_COLORS,
        "fire": FIRE_COLORS,
        "purple": PURPLE_WAVE,
        "rainbow": RAINBOW_COLORS,
    }

    def __init__(
        self, message: str = "처리 중", style: str = "dots", color_theme: str = "wave", use_panel: bool = False
    ):
        self.message = message
        self.frames = self.STYLES.get(style, self.STYLES["dots"])
        self.colors = self.COLOR_THEMES.get(color_theme, WAVE_COLORS)
        self.use_panel = use_panel
        self.running = False
        self.thread = None
        self.start_time = None
        self.wave_offset = 0
        self.live = None

    def _create_display(self, frame: str, elapsed: float) -> Text:
        """화려한 디스플레이 생성"""
        # 파도치는 메시지
        wave_msg = create_wave_text(self.message, self.colors, self.wave_offset)

        # 스피너 아이콘 (그라데이션)
        spinner_color = self.colors[self.wave_offset % len(self.colors)]

        # 조합
        result = Text()
        result.append(f" {frame} ", style=Style(color=spinner_color, bold=True))
        result.append_text(wave_msg)
        result.append(" ", style="dim")
        result.append(f"({elapsed:.1f}s)", style="dim cyan")

        return result

    def _animate_rich(self) -> None:
        """Rich Live를 사용한 애니메이션"""
        spinner = cycle(self.frames)

        with Live(console=console, refresh_per_second=10, transient=True) as live:
            self.live = live
            while self.running:
                elapsed = time.time() - self.start_time
                frame = next(spinner)

                display = self._create_display(frame, elapsed)

                if self.use_panel:
                    live.update(Panel(display, border_style="cyan", box=box.ROUNDED))
                else:
                    live.update(display)

                self.wave_offset += 1
                time.sleep(0.08)

    def _animate_fallback(self) -> None:
        """폴백 애니메이션 (Rich 없을 때)"""
        spinner = cycle(self.frames)
        while self.running:
            elapsed = time.time() - self.start_time
            frame = next(spinner)
            text = f"\r\033[36m{frame}\033[0m {self.message} \033[90m({elapsed:.1f}s)\033[0m"
            sys.stdout.write(text)
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self) -> None:
        """스피너 시작"""
        self.running = True
        self.start_time = time.time()
        self.wave_offset = 0

        if RICH_AVAILABLE:
            self.thread = threading.Thread(target=self._animate_rich)
        else:
            self.thread = threading.Thread(target=self._animate_fallback)

        self.thread.daemon = True
        self.thread.start()

    def stop(self, final_message: str = None):
        """스피너 정지"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)

        elapsed = time.time() - self.start_time if self.start_time else 0

        if RICH_AVAILABLE and final_message:
            # 성공 메시지 (그라데이션)
            success_text = create_gradient_text(final_message, "#00FF88", "#00D4FF")
            console.print("[bold green]✓[/] ", end="")
            console.print(success_text, end="")
            console.print(f" [dim]({elapsed:.1f}s)[/]")
        elif final_message:
            sys.stdout.write("\r" + " " * 80 + "\r")
            logging.info(f"\033[32m✓\033[0m {final_message} \033[90m({elapsed:.1f}s)\033[0m")

        sys.stdout.flush()

    def update(self, message: str):
        """메시지 업데이트"""
        self.message = message

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.stop(f"{self.message} 완료")
        else:
            self.stop()


# ============================================
# 화려한 프로그레스 바
# ============================================


class ProgressBar:
    """파도치는 프로그레스 바"""

    def __init__(self, total: int, message: str = "진행 중", color_theme: str = "wave", show_speed: bool = True):
        self.total = total
        self.current = 0
        self.message = message
        self.colors = Spinner.COLOR_THEMES.get(color_theme, WAVE_COLORS)
        self.start_time = time.time()
        self.show_speed = show_speed
        self.wave_offset = 0

        if RICH_AVAILABLE:
            self.progress = Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[bold]{task.description}"),
                BarColumn(bar_width=40, style="cyan", complete_style="green"),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            )
            self.task_id = None

    def start(self) -> None:
        """프로그레스 시작"""
        if RICH_AVAILABLE:
            self.progress.start()
            self.task_id = self.progress.add_task(self.message, total=self.total)

    def update(self, current: int = None, message: str = None):
        """진행률 업데이트"""
        if current is not None:
            self.current = current
        else:
            self.current += 1

        if message:
            self.message = message

        if RICH_AVAILABLE and self.task_id is not None:
            self.progress.update(self.task_id, completed=self.current, description=self.message)
        else:
            # 폴백
            percent = self.current / self.total if self.total > 0 else 0
            filled = int(30 * percent)
            bar = "█" * filled + "░" * (30 - filled)
            elapsed = time.time() - self.start_time
            text = f"\r\033[36m{bar}\033[0m {percent * 100:5.1f}% | {self.message} \033[90m({elapsed:.1f}s)\033[0m"
            sys.stdout.write(text)
            sys.stdout.flush()

    def finish(self, message: str = "완료"):
        """완료"""
        elapsed = time.time() - self.start_time

        if RICH_AVAILABLE:
            self.progress.stop()
            success_text = create_gradient_text(message, "#00FF88", "#00D4FF")
            console.print("[bold green]✓[/] ", end="")
            console.print(success_text, end="")
            console.print(f" [dim]({elapsed:.1f}s)[/]")
        else:
            sys.stdout.write("\r" + " " * 100 + "\r")
            logging.info(f"\033[32m✓\033[0m {message} \033[90m({elapsed:.1f}s)\033[0m")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.finish()
        elif RICH_AVAILABLE:
            self.progress.stop()


# ============================================
# 단계 표시기 (파도치는 버전)
# ============================================


class PhaseIndicator:
    """화려한 단계 표시기"""

    def __init__(self, phases: list, color_theme: str = "wave"):
        self.phases = phases
        self.current_phase = 0
        self.colors = Spinner.COLOR_THEMES.get(color_theme, WAVE_COLORS)
        self.wave_offset = 0

    def show(self) -> None:
        """전체 단계 표시"""
        if RICH_AVAILABLE:
            console.print()
            for i, phase in enumerate(self.phases):
                if i < self.current_phase:
                    # 완료 (그라데이션)
                    text = create_gradient_text(f"  ✓ {phase}", "#00FF88", "#00D4FF")
                    console.print(text)
                elif i == self.current_phase:
                    # 현재 (파도)
                    wave_text = create_wave_text(f"  ➤ {phase}", self.colors, self.wave_offset)
                    console.print(wave_text, style="bold")
                else:
                    # 대기
                    console.print(f"  [dim]○ {phase}[/]")
            console.print()
        else:
            print()
            for i, phase in enumerate(self.phases):
                if i < self.current_phase:
                    logging.info(f"\033[32m✓\033[0m {phase}")
                elif i == self.current_phase:
                    logging.info(f"\033[36m➤\033[0m \033[1m{phase}\033[0m")
                else:
                    logging.info(f"\033[90m○ {phase}\033[0m")
            print()

        self.wave_offset += 1

    def next(self) -> bool:
        """다음 단계로"""
        self.current_phase += 1
        return self.current_phase < len(self.phases)

    def complete(self) -> None:
        """모든 단계 완료"""
        self.current_phase = len(self.phases)


# ============================================
# 화려한 헤더/메시지 출력
# ============================================


def print_header(title: str, style: str = "double", color_theme: str = "wave"):
    """파도치는 화려한 헤더"""
    colors = Spinner.COLOR_THEMES.get(color_theme, WAVE_COLORS)

    if RICH_AVAILABLE:
        if style == "double":
            # 그라데이션 제목
            title_text = create_gradient_text(title, "#00D4FF", "#FF00FF")
            panel = Panel(title_text, border_style="cyan", box=box.DOUBLE, padding=(0, 2))
            console.print()
            console.print(panel)
        elif style == "wave":
            # 파도치는 제목
            wave_text = create_wave_text(f"  {title}  ", colors, 0)
            panel = Panel(wave_text, border_style="bright_cyan", box=box.ROUNDED, padding=(0, 1))
            console.print()
            console.print(panel)
        elif style == "fire":
            # 불꽃 테마
            fire_text = create_wave_text(f"🔥 {title} 🔥", FIRE_COLORS, 0)
            console.print()
            console.print(fire_text, style="bold")
            console.print()
        elif style == "star":
            console.print()
            console.print(f"[yellow]{'★' * 20}[/]")
            rainbow_title = create_wave_text(f"  {title}", RAINBOW_COLORS, 0)
            console.print(rainbow_title, style="bold")
            console.print(f"[yellow]{'★' * 20}[/]")
        else:
            console.print()
            console.print(f"[bold cyan]{'─' * 60}[/]")
            console.print(f"[bold]{title}[/]")
            console.print(f"[bold cyan]{'─' * 60}[/]")
    else:
        width = 60
        border = "═" * width
        logging.info(f"\n+{border}+")
        logging.info(f"| {title:^{width - 2}} |")
        logging.info(f"+{border}+")


def print_success(message: str):
    """성공 메시지 (그라데이션)"""
    if RICH_AVAILABLE:
        text = create_gradient_text(message, "#00FF88", "#00D4FF")
        console.print("[bold green]✓[/] ", end="")
        console.print(text)
    else:
        logging.info(f"\033[32m✓\033[0m {message}")


def print_error(message: str):
    """에러 메시지"""
    if RICH_AVAILABLE:
        console.print(f"[bold red]✗[/] [red]{message}[/]")
    else:
        logging.info(f"\033[31m✗\033[0m {message}")


def print_warning(message: str):
    """경고 메시지"""
    if RICH_AVAILABLE:
        text = create_wave_text(message, FIRE_COLORS, 0)
        console.print("[bold yellow]![/] ", end="")
        console.print(text)
    else:
        logging.info(f"\033[33m!\033[0m {message}")


def print_info(message: str):
    """정보 메시지 (파도)"""
    if RICH_AVAILABLE:
        text = create_wave_text(message, WAVE_COLORS, 0)
        console.print("[bold cyan]→[/] ", end="")
        console.print(text)
    else:
        logging.info(f"\033[36m→\033[0m {message}")


def print_tip(message: str):
    """팁 메시지"""
    if RICH_AVAILABLE:
        text = create_wave_text(message, PURPLE_WAVE, 0)
        console.print("[bold magenta]💡[/] ", end="")
        console.print(text)
    else:
        logging.info(f"\033[35m💡\033[0m {message}")


def print_stage(stage_num: int, stage_name: str, status: str = "running"):
    """스테이지 헤더 (화려한 버전)"""
    if RICH_AVAILABLE:
        if status == "running":
            title = create_wave_text(f"Stage {stage_num}: {stage_name}", WAVE_COLORS, 0)
            console.print()
            console.print(Panel(title, border_style="cyan", box=box.HEAVY))
        elif status == "complete":
            title = create_gradient_text(f"Stage {stage_num}: {stage_name} ✓", "#00FF88", "#00D4FF")
            console.print(Panel(title, border_style="green", box=box.ROUNDED))
        elif status == "error":
            console.print(Panel(f"[bold red]Stage {stage_num}: {stage_name} ✗[/]", border_style="red", box=box.HEAVY))
    else:
        logging.info(f"\n{'=' * 60}")
        logging.info(f"Stage {stage_num}: {stage_name}")
        logging.info(f"{'=' * 60}")


def print_table(headers: list, rows: list):
    """화려한 테이블"""
    if RICH_AVAILABLE:
        table = Table(box=box.ROUNDED, border_style="cyan")

        for header in headers:
            table.add_column(header, style="bold cyan")

        for i, row in enumerate(rows):
            # 행마다 살짝 다른 색상
            style = "white" if i % 2 == 0 else "bright_white"
            table.add_row(*[str(cell) for cell in row], style=style)

        console.print(table)
    else:
        # 폴백
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        header_line = " │ ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        separator = "─┼─".join("─" * w for w in widths)

        logging.info(f"\033[1m{header_line}\033[0m")
        logging.info(f"\033[90m{separator}\033[0m")

        for row in rows:
            row_line = " │ ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            logging.info(row_line)


# ============================================
# 데코레이터
# ============================================


def with_spinner(message: str = "처리 중", style: str = "dots", color_theme: str = "wave"):
    """스피너 데코레이터"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            spinner = Spinner(message, style, color_theme)
            spinner.start()
            try:
                result = func(*args, **kwargs)
                spinner.stop(f"{message} 완료")
                return result
            except Exception as e:
                spinner.stop()
                print_error(f"{message} 실패: {e}")
                raise

        return wrapper

    return decorator


# ============================================
# 테스트
# ============================================

if __name__ == "__main__":
    logging.info("\n")
    print_header("Spinner & Progress Test", style="wave")

    # 스피너 테스트
    print_info("스피너 테스트 시작...")

    for style, theme in [("dots", "wave"), ("braille", "purple"), ("magic", "rainbow"), ("fire", "fire")]:
        spinner = Spinner(f"{style} + {theme}", style=style, color_theme=theme)
        spinner.start()
        time.sleep(2)
        spinner.stop(f"{style} 스타일 완료!")
        time.sleep(0.3)

    # 프로그레스 바 테스트
    print()
    print_info("프로그레스 바 테스트...")

    with ProgressBar(30, "블록 생성", color_theme="wave") as progress:
        for i in range(30):
            time.sleep(0.05)
            progress.update(message=f"Block {i + 1}/30 생성 중")

    # 단계 표시기 테스트
    print()
    print_info("단계 표시기 테스트...")

    phases = ["컨셉 분석", "Bible 생성", "Treatment 생성", "저장"]
    indicator = PhaseIndicator(phases, color_theme="wave")

    for _ in range(len(phases)):
        indicator.show()
        time.sleep(1)
        indicator.next()

    indicator.show()

    # 메시지 테스트
    print()
    print_header("메시지 스타일", style="star")
    print_success("성공 메시지입니다!")
    print_warning("경고 메시지입니다!")
    print_error("에러 메시지입니다!")
    print_info("정보 메시지입니다!")
    print_tip("IMF 직전에는 달러가 최고!")

    # 테이블 테스트
    print()
    print_header("NPC 목록", style="double")
    print_table(
        ["NPC", "역할", "상태"],
        [
            ["팽조명", "주인공", "활성"],
            ["한영민", "빌런", "활성"],
            ["워렌 버핏", "멘토", "활성"],
        ],
    )

    # 스테이지 헤더 테스트
    print()
    print_stage(0, "Bible Recovery", "running")
    time.sleep(1)
    print_stage(0, "Bible Recovery", "complete")

    print()
    print_success("모든 테스트 완료!")
