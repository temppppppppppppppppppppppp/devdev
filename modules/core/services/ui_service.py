"""[Phase 4B-2] UIService — UI helper service

원본: main_a.py:1117-1186, 2752-2790, 3219-3242 (4개 메서드, 132줄)

NOTE:
- 이 구현체는 Bible/Treatment 선택, 정수 입력, 테이블 출력 helper를 담당한다.
- `modules/protocols/app_services.py::UIServiceProtocol`은 `self.ui`의 log/title surface를
  모델링하며, 본 helper service의 conform target이 아니다.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


class UIService:
    """UI 선택/입력/표시 헬퍼 서비스.

    Args:
        ui: StudioVisualizer 인스턴스 (log, console.print 등)
        project_fn: () -> current_project 또는 None (lazy 접근)
    """

    def __init__(
        self,
        ui: Any,
        project_fn: Callable[[], Any],
    ) -> None:
        self._ui = ui
        self._project_fn = project_fn

    def _log(self, text: str, **context) -> None:
        if hasattr(self._ui, "log"):
            self._ui.log(text, component="Stage0UI", stage="stage0", **context)

    def _menu_block(self, title: str, options: list[str], **context) -> None:
        if hasattr(type(self._ui), "menu_block"):
            self._ui.menu_block(title, options, component="Stage0UI", stage="stage0", **context)
            return
        self._log(title, event_kind="menu", render_format="menu", **context)
        for option in options:
            self._log(option, event_kind="menu_option", render_format="menu", **context)

    def _prompt(self, prompt: str, **context) -> str:
        if hasattr(type(self._ui), "prompt"):
            return self._ui.prompt(prompt, component="Stage0UI", stage="stage0", **context)
        self._log(prompt, event_kind="prompt", render_format="prompt", **context)
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt, ValueError):
            return ""

    def _selection(self, label: str, selection_value, **context) -> None:
        if hasattr(type(self._ui), "selection"):
            self._ui.selection(label, selection_value, component="Stage0UI", stage="stage0", **context)
            return
        self._log(
            label,
            event_kind="selection",
            render_format="selection",
            selection_value=selection_value,
            **context,
        )

    # ── select_bible ─────────────────────────────────────────────
    def select_bible(self) -> str | None:
        """bible 폴더에서 성경(Lore) JSON 파일 선택. 원본: main_a.py:1117"""
        bible_dir = Path("bible")
        files = sorted(list(bible_dir.glob("*.json")))
        if not files:
            self._log("❌ bible 폴더에 JSON 파일이 없습니다.")
            return None

        options = [f"{i}. {f.name}" for i, f in enumerate(files, 1)]
        self._menu_block(
            "📚 [Bible Selection] 사용할 성경(Lore)을 선택하십시오:",
            options,
            prompt_id="stage0_select_bible",
        )

        idx = (
            self.get_int_input(
                f"\n👉 Choice (1-{len(files)}): ",
                default=1,
                min_val=1,
                max_val=len(files),
                prompt_id="stage0_select_bible_choice",
            )
            or 1
        ) - 1
        selected = files[idx].name if 0 <= idx < len(files) else files[0].name
        self._selection("Bible 선택", selected, prompt_id="stage0_select_bible")
        return selected

    # ── select_treatment ─────────────────────────────────────────
    def select_treatment(self) -> str | None:
        """treatments 폴더에서 설계도 JSON 선택. 원본: main_a.py:1141"""
        treat_dir = Path("treatments")
        if not treat_dir.exists():
            treat_dir.mkdir(parents=True, exist_ok=True)

        files = sorted(list(treat_dir.glob("*.json")))
        if not files:
            self._log("❌ treatments 폴더에 JSON 파일이 없습니다.")
            return None

        project = self._project_fn()
        options = []
        for i, f in enumerate(files, 1):
            is_current = project and project.treatment_path == f
            options.append(f"{i}. {f.name} {'⭐ (Current)' if is_current else ''}".rstrip())
        self._menu_block(
            "🧬 [Roadmap Selection] V25 상세 설계도(JSON)를 선택하십시오:",
            options,
            prompt_id="stage0_select_treatment",
        )

        try:
            idx = (
                self.get_int_input(
                    f"\n👉 Choice (1-{len(files)}, 미입력 시 1번): ",
                    default=1,
                    min_val=1,
                    max_val=len(files),
                    prompt_id="stage0_select_treatment_choice",
                )
                or 1
            ) - 1

            if 0 <= idx < len(files):
                selected_file = files[idx]
                if project:
                    project.treatment_path = selected_file
                self._selection("로드맵 선택", selected_file.name, prompt_id="stage0_select_treatment")
                self._log(f"✅ 로드맵 선택 완료: {selected_file.name}")
                return selected_file.name
            else:
                return files[0].name if files else None

        except Exception as e:
            self._log(f"⚠️ 선택 중 오류 발생: {e}", level="warning")
            return files[0].name if files else None

    # ── show_volume_table ────────────────────────────────────────
    def _build_volume_table_title(self, volumes: list[dict[str, Any]]) -> str:
        """Use the live volume count when available, otherwise fall back to a neutral label."""
        volume_count = len(volumes)
        if volume_count > 0:
            return f"📊 [V20] {volume_count}권 전략 설계 상업성 성적표"
        return "📊 [V20] 권별 전략 설계 상업성 성적표"

    def show_volume_table(self, volumes: list[dict[str, Any]]) -> None:
        """권별 전략 설계 테이블 출력. 원본: main_a.py:3219"""
        from rich import box
        from rich.table import Table

        table = Table(title=self._build_volume_table_title(volumes), box=box.ROUNDED)
        table.add_column("Vol", justify="center", style="cyan")
        table.add_column("Strategy Title", style="white")
        table.add_column("Cider Score", justify="right", style="bold yellow")
        for v in volumes:
            raw_doc = v.get("strategy_doc", "")
            if isinstance(raw_doc, dict):
                raw_doc = str(raw_doc.get("title", raw_doc.get("summary", str(raw_doc))))
            title = str(raw_doc).split("\n")[0].replace("### ", "")
            cider = v.get("cider_score", "N/A")
            table.add_row(f"제 {v.get('vol_no', '?')} 권", title, str(cider))
        self._ui.console.print(table)

    # ── get_int_input ────────────────────────────────────────────
    def get_int_input(
        self,
        prompt: str,
        default: int | None = None,
        min_val: int | None = None,
        max_val: int | None = None,
        attempts: int = 3,
        prompt_id: str | None = None,
    ) -> int | None:
        """사용자로부터 정수 입력. 원본: main_a.py:2752"""
        # [TF-CX-RISK-01] 범위 역전 사전 검증
        if min_val is not None and max_val is not None and min_val > max_val:
            self._log(f"⚠️ 입력 범위 오류 (min={min_val} > max={max_val}). 기본값({default})을 반환합니다.", level="warning")
            return default
        for _ in range(attempts):
            raw = self._prompt(prompt, prompt_id=prompt_id).strip()
            if raw == "":
                # [TF-CX-RISK-01] default도 min/max 검증
                if default is not None:
                    if (min_val is not None and default < min_val) or (max_val is not None and default > max_val):
                        self._log(f"⚠️ 기본값 {default}이(가) 범위({min_val}~{max_val})를 벗어났습니다.", level="warning")
                        continue
                self._selection(prompt, default, prompt_id=prompt_id, visible=False)
                return default
            if not raw.isdigit():
                self._log("⚠️ 숫자만 입력 가능합니다.", level="warning")
                continue
            value = int(raw)
            if min_val is not None and value < min_val:
                self._log(f"⚠️ 최소값은 {min_val}입니다.", level="warning")
                continue
            if max_val is not None and value > max_val:
                self._log(f"⚠️ 최대값은 {max_val}입니다.", level="warning")
                continue
            self._selection(prompt, value, prompt_id=prompt_id, visible=False)
            return value
        return default
