import logging
from collections.abc import Callable

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table


class StudioVisualizer:
    def __init__(self) -> None:
        self.console = Console()
        self.layout = Layout()
        self._operator_event_sink: Callable[[dict], None] | None = None
        self._operator_event_seq = 0

    def make_cockpit_layout(self, ep_num: int, martial_data: str, causal_data: str):
        """화면을 좌/우로 분할하여 정보를 배치합니다."""
        # [🚨 수정] 매 호출마다 레이아웃을 초기화하여 중복 분할 에러 방지
        from rich.layout import Layout  # (필요시 내부 임포트 혹은 상단 확인)

        self.layout = Layout()

        self.layout.split_row(
            Layout(name="main", ratio=2),  # 집필 로그
            Layout(name="side", ratio=1),  # 상태창 및 인과관계
        )

        self.layout["side"].split_column(Layout(name="martial", size=15), Layout(name="causal"))

        # 패널 테두리와 스타일 보강
        self.layout["martial"].update(Panel(martial_data, title=f"⚔️ Martial HUD (Ep. {ep_num})", border_style="cyan"))
        self.layout["causal"].update(Panel(causal_data, title="🔗 Causal Tracker", border_style="yellow"))
        return self.layout

    def title(self, text: str, sub_text: str = "") -> None:
        self.console.clear()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(f"[bold magenta]🎹 {text}[/bold magenta]")
        if sub_text:
            grid.add_row(f"[dim white]{sub_text}[/dim white]")
        self.console.print(Panel(grid, style="magenta", box=box.HEAVY))

    def print_agent(self, agent_name: str, message: str, color: str = "white") -> None:
        """에이전트별 고유 색상 패널 출력"""
        emoji_map = {
            "Analyst": "🧠",
            "Architect": "📐",
            "Writer": "✍️",
            "Editor": "💅",
            "Director": "🎬",
            "Manager": "💼",
            "Weaver": "🕸️",
            "System": "🤖",
        }
        icon = emoji_map.get(agent_name, "🤖")
        self.console.print(Panel(message, title=f"{icon} [bold {color}]{agent_name}[/]", border_style=color))

    def show_status(self, episode: int, module_name: str, seeds_count: int) -> None:
        """HUD 스타일 상태창"""
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Episode", justify="center")
        table.add_column("Current Module", justify="center")
        table.add_column("Active Seeds", justify="center")

        table.add_row(f"[bold yellow]제 {episode} 화[/]", f"[green]{module_name}[/]", f"[red]{seeds_count} 개[/]")
        self.console.print(table)

    def menu(self, items: dict) -> str:
        self.console.print("\n[bold cyan]👇 Select Command:[/]")
        for key, value in items.items():
            self.console.print(f"   [bold yellow]{key}.[/] {value}")
        return self.console.input("\n   👉 [bold]Choice:[/bold] ")

    def set_operator_event_sink(self, sink: Callable[[dict], None] | None) -> None:
        self._operator_event_sink = sink

    def log(self, text: str, **context) -> None:
        message = str(text)
        meta = context.pop("meta", {})
        if not isinstance(meta, dict):
            meta = {"value": meta}
        if context:
            meta = {**meta, **context}
        visible = bool(meta.get("visible", True))
        if visible:
            self.console.print(f"   [dim]{message}[/]")
        logging.getLogger("UI").info(message)  # [TF-26] 파일 듀얼 출력
        if self._operator_event_sink is None:
            return
        self._operator_event_seq += 1
        event = {
            "seq": self._operator_event_seq,
            "level": str(meta.pop("level", "info")),
            "component": str(meta.pop("component", "UI")),
            "stage": meta.pop("stage", None),
            "ep_num": meta.pop("ep_num", None),
            "arc_num": meta.pop("arc_num", None),
            "round_num": meta.pop("round_num", None),
            "attempt_key": meta.pop("attempt_key", None),
            "event_kind": str(meta.pop("event_kind", "log")),
            "render_format": str(meta.pop("render_format", "text")),
            "message": message,
            "visible": bool(meta.pop("visible", True)),
            "selection_value": meta.pop("selection_value", None),
            "prompt_id": meta.pop("prompt_id", None),
            "artifact_path": meta.pop("artifact_path", None),
            "meta": meta or None,
        }
        try:
            self._operator_event_sink(event)
        except Exception as exc:  # pragma: no cover - non-blocking console path
            logging.getLogger("UI").debug("operator event sink failed: %s", exc)

    def menu_block(self, title: str, options: list[str], **context) -> None:
        self.log(
            str(title),
            event_kind="menu",
            render_format="menu",
            **context,
        )
        for option in options:
            self.log(
                str(option),
                event_kind="menu_option",
                render_format="menu",
                **context,
            )

    def prompt(self, prompt_text: str, **context) -> str:
        prompt_context = dict(context)
        prompt_context.setdefault("event_kind", "prompt")
        prompt_context.setdefault("render_format", "prompt")
        self.log(str(prompt_text), **prompt_context)
        response = self.console.input(str(prompt_text))
        response_context = dict(context)
        response_context.setdefault("event_kind", "prompt_response")
        response_context.setdefault("render_format", "input")
        response_context.setdefault("selection_value", response)
        response_context.setdefault("visible", False)
        self.log(str(prompt_text), **response_context)
        return response

    def selection(self, label: str, selection_value, **context) -> None:
        self.log(
            str(label),
            event_kind="selection",
            render_format="selection",
            selection_value=selection_value,
            **context,
        )

    def summary(self, text: str, **context) -> None:
        self.log(
            str(text),
            event_kind="summary",
            render_format="summary",
            **context,
        )

    def spinner(self, text: str):
        """로딩 스피너 컨텍스트 매니저"""
        return self.console.status(f"[bold green]{text}...", spinner="dots")

    def get_progress_bar(self):
        """연속 집필용 프로그레스 바"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
        )
