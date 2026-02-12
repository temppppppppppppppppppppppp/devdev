from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.layout import Layout
from rich import box
import time
from rich.live import Live

class StudioVisualizer:
    def __init__(self) -> None:
        self.console = Console()
        self.layout = Layout()    

    def make_cockpit_layout(self, ep_num: int, martial_data: str, causal_data: str):
            """화면을 좌/우로 분할하여 정보를 배치합니다."""
            # [🚨 수정] 매 호출마다 레이아웃을 초기화하여 중복 분할 에러 방지
            from rich.layout import Layout # (필요시 내부 임포트 혹은 상단 확인)
            self.layout = Layout() 
            
            self.layout.split_row(
                Layout(name="main", ratio=2), # 집필 로그
                Layout(name="side", ratio=1)  # 상태창 및 인과관계
            )
            
            self.layout["side"].split_column(
                Layout(name="martial", size=15),
                Layout(name="causal")
            )
            
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
            "Analyst": "🧠", "Architect": "📐", "Writer": "✍️",
            "Editor": "💅", "Director": "🎬", "Manager": "💼",
            "Weaver": "🕸️", "System": "🤖"
        }
        icon = emoji_map.get(agent_name, "🤖")
        self.console.print(Panel(message, title=f"{icon} [bold {color}]{agent_name}[/]", border_style=color))

    def show_status(self, episode: int, module_name: str, seeds_count: int) -> None:
        """HUD 스타일 상태창"""
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Episode", justify="center")
        table.add_column("Current Module", justify="center")
        table.add_column("Active Seeds", justify="center")
        
        table.add_row(
            f"[bold yellow]제 {episode} 화[/]", 
            f"[green]{module_name}[/]", 
            f"[red]{seeds_count} 개[/]"
        )
        self.console.print(table)

    def menu(self, items: dict) -> str:
        self.console.print("\n[bold cyan]👇 Select Command:[/]")
        for key, value in items.items():
            self.console.print(f"   [bold yellow]{key}.[/] {value}")
        return self.console.input("\n   👉 [bold]Choice:[/bold] ")

    def log(self, text: str) -> None:
        self.console.print(f"   [dim]{text}[/]")

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
            console=self.console
        )