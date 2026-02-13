"""
Spinner & Progress Utils - 예쁜 로딩 애니메이션
================================================
"""

import sys
import threading
import time
from itertools import cycle


class Spinner:
    """예쁜 스피너"""

    # 스피너 스타일들
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
    }

    def __init__(self, message: str = "처리 중", style: str = "dots", color: bool = True):
        self.message = message
        self.frames = self.STYLES.get(style, self.STYLES["dots"])
        self.color = color
        self.running = False
        self.thread = None
        self.start_time = None

    def _animate(self):
        """애니메이션 루프"""
        spinner = cycle(self.frames)
        while self.running:
            elapsed = time.time() - self.start_time
            frame = next(spinner)

            if self.color:
                # ANSI 색상: 청록색
                text = f"\r\033[36m{frame}\033[0m {self.message} \033[90m({elapsed:.1f}s)\033[0m"
            else:
                text = f"\r{frame} {self.message} ({elapsed:.1f}s)"

            sys.stdout.write(text)
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        """스피너 시작"""
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, final_message: str = None):
        """스피너 정지"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)

        elapsed = time.time() - self.start_time if self.start_time else 0

        # 줄 지우기
        sys.stdout.write("\r" + " " * 80 + "\r")

        if final_message:
            if self.color:
                print(f"\033[32m✓\033[0m {final_message} \033[90m({elapsed:.1f}s)\033[0m")
            else:
                print(f"[v] {final_message} ({elapsed:.1f}s)")
        sys.stdout.flush()

    def update(self, message: str):
        """메시지 업데이트"""
        self.message = message

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class ProgressBar:
    """진행률 바"""

    def __init__(self, total: int, message: str = "진행 중", width: int = 30, color: bool = True):
        self.total = total
        self.current = 0
        self.message = message
        self.width = width
        self.color = color
        self.start_time = time.time()

    def update(self, current: int = None, message: str = None):
        """진행률 업데이트"""
        if current is not None:
            self.current = current
        else:
            self.current += 1

        if message:
            self.message = message

        percent = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)

        elapsed = time.time() - self.start_time

        if self.color:
            text = f"\r\033[36m{bar}\033[0m {percent * 100:5.1f}% | {self.message} \033[90m({elapsed:.1f}s)\033[0m"
        else:
            text = f"\r[{bar}] {percent * 100:5.1f}% | {self.message} ({elapsed:.1f}s)"

        sys.stdout.write(text)
        sys.stdout.flush()

    def finish(self, message: str = "완료"):
        """완료"""
        elapsed = time.time() - self.start_time
        sys.stdout.write("\r" + " " * 100 + "\r")

        if self.color:
            print(f"\033[32m✓\033[0m {message} \033[90m({elapsed:.1f}s)\033[0m")
        else:
            print(f"[v] {message} ({elapsed:.1f}s)")


class PhaseIndicator:
    """단계 표시기"""

    def __init__(self, phases: list, color: bool = True):
        self.phases = phases
        self.current_phase = 0
        self.color = color

    def show(self):
        """전체 단계 표시"""
        print()
        for i, phase in enumerate(self.phases):
            if i < self.current_phase:
                # 완료
                if self.color:
                    print(f"  \033[32m✓\033[0m {phase}")
                else:
                    print(f"  [v] {phase}")
            elif i == self.current_phase:
                # 현재
                if self.color:
                    print(f"  \033[36m➤\033[0m \033[1m{phase}\033[0m")
                else:
                    print(f"  [>] {phase}")
            else:
                # 대기
                if self.color:
                    print(f"  \033[90m○ {phase}\033[0m")
                else:
                    print(f"  [ ] {phase}")
        print()

    def next(self):
        """다음 단계로"""
        self.current_phase += 1
        return self.current_phase < len(self.phases)

    def complete(self):
        """모든 단계 완료"""
        self.current_phase = len(self.phases)


def print_header(title: str, style: str = "double", color: bool = True):
    """예쁜 헤더 출력"""
    width = 60

    if style == "double":
        border = "═" * width
        if color:
            print(f"\n\033[36m╔{border}╗\033[0m")
            print(f"\033[36m║\033[0m \033[1m{title:^{width - 2}}\033[0m \033[36m║\033[0m")
            print(f"\033[36m╚{border}╝\033[0m")
        else:
            print(f"\n+{border}+")
            print(f"| {title:^{width - 2}} |")
            print(f"+{border}+")

    elif style == "simple":
        border = "─" * width
        if color:
            print(f"\n\033[90m{border}\033[0m")
            print(f"\033[1m{title}\033[0m")
            print(f"\033[90m{border}\033[0m")
        else:
            print(f"\n{border}")
            print(title)
            print(border)

    elif style == "star":
        if color:
            print(f"\n\033[33m{'★' * 20}\033[0m")
            print(f"\033[1m  {title}\033[0m")
            print(f"\033[33m{'★' * 20}\033[0m")
        else:
            print(f"\n{'*' * 40}")
            print(f"  {title}")
            print(f"{'*' * 40}")


def print_success(message: str, color: bool = True):
    """성공 메시지"""
    if color:
        print(f"\033[32m✓\033[0m {message}")
    else:
        print(f"[v] {message}")


def print_error(message: str, color: bool = True):
    """에러 메시지"""
    if color:
        print(f"\033[31m✗\033[0m {message}")
    else:
        print(f"[X] {message}")


def print_warning(message: str, color: bool = True):
    """경고 메시지"""
    if color:
        print(f"\033[33m!\033[0m {message}")
    else:
        print(f"[!] {message}")


def print_info(message: str, color: bool = True):
    """정보 메시지"""
    if color:
        print(f"\033[36m→\033[0m {message}")
    else:
        print(f"[>] {message}")


def print_tip(message: str, color: bool = True):
    """팁 메시지"""
    if color:
        print(f"\033[35m💡\033[0m {message}")
    else:
        print(f"[Tip] {message}")


def print_table(headers: list, rows: list, color: bool = True):
    """간단한 테이블 출력"""
    # 열 너비 계산
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # 헤더
    header_line = " │ ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator = "─┼─".join("─" * w for w in widths)

    if color:
        print(f"\033[1m{header_line}\033[0m")
        print(f"\033[90m{separator}\033[0m")
    else:
        print(header_line)
        print(separator)

    # 행
    for row in rows:
        row_line = " │ ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(row_line)


# 편의 함수들
def with_spinner(message: str = "처리 중", style: str = "dots"):
    """스피너 데코레이터"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            spinner = Spinner(message, style)
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


# 테스트
if __name__ == "__main__":
    print("\n=== Spinner 스타일 테스트 ===\n")

    for style in ["dots", "braille", "pulse", "grow", "moon"]:
        spinner = Spinner(f"{style} 스타일", style=style)
        spinner.start()
        time.sleep(2)
        spinner.stop(f"{style} 완료!")

    print("\n=== Progress Bar 테스트 ===\n")

    progress = ProgressBar(20, "블록 생성")
    for i in range(20):
        time.sleep(0.1)
        progress.update(message=f"Block {i + 1}/20")
    progress.finish("블록 생성 완료!")

    print("\n=== Phase Indicator 테스트 ===\n")

    phases = ["컨셉 분석", "Bible 생성", "Treatment 생성", "저장"]
    indicator = PhaseIndicator(phases)

    for _ in range(len(phases)):
        indicator.show()
        time.sleep(1)
        indicator.next()

    indicator.show()

    print("\n=== 메시지 테스트 ===\n")

    print_header("Story Expander v3", style="double")
    print_success("분석 완료!")
    print_warning("API 호출 중...")
    print_error("연결 실패")
    print_info("다음 단계로 이동")
    print_tip("IMF 직전에는 달러가 최고!")

    print("\n=== 테이블 테스트 ===\n")

    print_table(
        ["NPC", "역할", "실존 모티브"],
        [
            ["한영민", "메인 빌런", "-"],
            ["워렌 버핏", "멘토", "Warren Buffett"],
            ["손정의", "파트너", "Masayoshi Son"],
        ],
    )
