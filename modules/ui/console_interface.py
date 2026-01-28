import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

class ConsoleInterface:
    def __init__(self, studio_system):
        self.system = studio_system
        self.console = Console()
        self.project_name = studio_system.project_name

    def clear(self):
        """터미널 화면을 깨끗하게 지웁니다."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_dashboard(self):
        """[FIX] 누락되었던 메인 대시보드를 출력합니다."""
        self.clear()
        self.console.print(Panel(
            f"[bold gold1]🏭 Novel Studio v2.0[/] | [bold cyan]Project: {self.project_name}[/]",
            subtitle="Powered by 100 Billion Developer Logic",
            box=box.DOUBLE,
            style="white on black"
        ))
        self.console.print("\n[bold green]Welcome, CEO! Your AI Novel Factory is ready to produce.[/]\n")

    def ask_choice(self, question, choices):
        """사용자에게 선택지를 물어보고 입력을 받습니다."""
        return Prompt.ask(f"[bold yellow]{question}[/]", choices=choices, default=choices[0])

    def select_treatment(self, genre_name):
        """장르 폴더 내의 뼈대(Treatment) 리스트를 보여주고 선택받습니다."""
        path = Path("config") / "treatments" / genre_name.lower()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            return None

        files = [f.stem for f in path.glob("*.txt")]
        if not files:
            self.console.print(f"      ⚠️ No .txt modules found in config/treatments/{genre_name.lower()}/")
            return None

        table = Table(title=f"📜 [bold cyan]{genre_name.upper()}[/] Skeleton Library", box=box.ROUNDED)
        table.add_column("No", style="dim", width=4)
        table.add_column("Module Name", style="white")
        
        for i, name in enumerate(files):
            table.add_row(str(i+1), name)
        
        self.console.print(table)
        sel = Prompt.ask("Select Module Number", choices=[str(i+1) for i in range(len(files))], default="1")
        return files[int(sel)-1]

    def print_success(self, msg): self.console.print(f"✅ [bold green]{msg}[/]")
    def print_info(self, msg): self.console.print(f"ℹ️  [bold blue]{msg}[/]")
    def print_error(self, msg): self.console.print(f"❌ [bold red]{msg}[/]")
