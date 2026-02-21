"""[Phase 4B-2] UIService — UI 헬퍼 메서드 서비스

원본: main_a.py:1117-1186, 2752-2790, 3219-3242 (4개 메서드, 132줄)
Protocol: modules/protocols/app_services.py UIServiceProtocol (log/title은 StudioVisualizer 직접)
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

    # ── select_bible ─────────────────────────────────────────────
    def select_bible(self) -> str | None:
        """bible 폴더에서 성경(Lore) JSON 파일 선택. 원본: main_a.py:1117"""
        bible_dir = Path("bible")
        files = sorted(list(bible_dir.glob("*.json")))
        if not files:
            print("❌ bible 폴더에 JSON 파일이 없습니다.")
            return None

        print("\n📚 [Bible Selection] 사용할 성경(Lore)을 선택하십시오:")
        for i, f in enumerate(files, 1):
            print(f"   {i}. {f.name}")

        idx = (self.get_int_input(f"\n👉 Choice (1-{len(files)}): ", default=1, min_val=1, max_val=len(files)) or 1) - 1
        return files[idx].name if 0 <= idx < len(files) else files[0].name

    # ── select_treatment ─────────────────────────────────────────
    def select_treatment(self) -> str | None:
        """treatments 폴더에서 설계도 JSON 선택. 원본: main_a.py:1141"""
        treat_dir = Path("treatments")
        if not treat_dir.exists():
            treat_dir.mkdir(parents=True, exist_ok=True)

        files = sorted(list(treat_dir.glob("*.json")))
        if not files:
            self._ui.log("❌ treatments 폴더에 JSON 파일이 없습니다.")
            return None

        project = self._project_fn()
        print("\n🧬 [Roadmap Selection] V25 상세 설계도(JSON)를 선택하십시오:")
        for i, f in enumerate(files, 1):
            is_current = project and project.treatment_path == f
            print(f"   {i}. {f.name} {'⭐ (Current)' if is_current else ''}")

        try:
            idx = (
                self.get_int_input(
                    f"\n👉 Choice (1-{len(files)}, 미입력 시 1번): ", default=1, min_val=1, max_val=len(files)
                )
                or 1
            ) - 1

            if 0 <= idx < len(files):
                selected_file = files[idx]
                if project:
                    project.treatment_path = selected_file
                self._ui.log(f"✅ 로드맵 선택 완료: {selected_file.name}")
                return selected_file.name
            else:
                return files[0].name if files else None

        except Exception as e:
            self._ui.log(f"⚠️ 선택 중 오류 발생: {e}")
            return files[0].name if files else None

    # ── show_volume_table ────────────────────────────────────────
    def show_volume_table(self, volumes: list[dict[str, Any]]) -> None:
        """권별 전략 설계 테이블 출력. 원본: main_a.py:3219"""
        from rich import box
        from rich.table import Table

        table = Table(title="📊 [V20] 10권 전략 설계 상업성 성적표", box=box.ROUNDED)
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
    ) -> int | None:
        """사용자로부터 정수 입력. 원본: main_a.py:2752"""
        # [TF-CX-RISK-01] 범위 역전 사전 검증
        if min_val is not None and max_val is not None and min_val > max_val:
            self._ui.log(f"⚠️ 입력 범위 오류 (min={min_val} > max={max_val}). 기본값({default})을 반환합니다.")
            return default
        for _ in range(attempts):
            raw = input(prompt).strip()
            if raw == "":
                # [TF-CX-RISK-01] default도 min/max 검증
                if default is not None:
                    if (min_val is not None and default < min_val) or (max_val is not None and default > max_val):
                        self._ui.log(f"⚠️ 기본값 {default}이(가) 범위({min_val}~{max_val})를 벗어났습니다.")
                        continue
                return default
            if not raw.isdigit():
                self._ui.log("⚠️ 숫자만 입력 가능합니다.")
                continue
            value = int(raw)
            if min_val is not None and value < min_val:
                self._ui.log(f"⚠️ 최소값은 {min_val}입니다.")
                continue
            if max_val is not None and value > max_val:
                self._ui.log(f"⚠️ 최대값은 {max_val}입니다.")
                continue
            return value
        return default
