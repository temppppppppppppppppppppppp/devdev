"""
Stage 0 Module - 프로젝트 초기화 및 역설계
==========================================
main_a.py에서 분리된 Stage 0 전용 모듈
"""

# utf8-hygiene: allow-file legacy stage0 UI strings remain mojibake outside the current refactor tranche
import logging

from modules.core.constants import GenreTypes

from .preset_registry import FieldDefinition, PresetRegistry
from .reverse_expander import ReverseExpander
from .story_expander import StoryExpander, StoryExpanderBibleGenerationError
from .style_extractor import StyleExtractor, StyleGuide

# 스피너 유틸리티
try:
    from .spinner import (
        PhaseIndicator,
        ProgressBar,
        Spinner,
        print_error,
        print_header,
        print_info,
        print_success,
        print_warning,
    )

    SPINNER_AVAILABLE = True
except ImportError:
    SPINNER_AVAILABLE = False

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.core.project_support import (
    EXTERNAL_POV_INSERT_POLICY_OPTIONS,
    INCARNATION_TYPE_OPTIONS,
    POV_OPTIONS,
    WORLD_ORIGIN_OPTIONS,
    default_external_pov_insert_policy,
    normalize_external_pov_insert_policy,
    resolve_external_pov_insert_policy_choice,
    resolve_indexed_menu_choice,
)
from modules.core.stage0_handoff import build_plot_roadmap_from_treatment, ensure_plot_roadmap


class StageZeroManager:
    """
    Stage 0 통합 관리자
    - 신규 프로젝트: 장르 선택 → 컨셉 입력 → Bible/Treatment 생성
    - 역설계: 기존 원고 → Bible + 회차별 상태 + 스타일 가이드 추출
    - Bible 임포트: 기존 JSON 불러오기
    """

    # 지원 장르 (GenreTypes.all()과 동기화)
    SUPPORTED_GENRES = {
        "wuxia": "무협",
        "hunter": "헌터물/던전물",
        "investment": "투자물/재벌물",
        "fantasy": "판타지",
        "composer": "작곡가물",
        "cooking": "요리물",
        "alt_history": "대체역사",
        "actor": "배우물/연예계",
        "sports": "스포츠물",
        "medical": "의학물/닥터물",
    }

    # 주인공 설정 옵션
    WORLD_ORIGIN_OPTIONS = list(WORLD_ORIGIN_OPTIONS)
    INCARNATION_TYPES = list(INCARNATION_TYPE_OPTIONS)
    POV_OPTIONS = list(POV_OPTIONS)
    WORK_GUARD_LIBRARY_ROOT = Path("work_guards")
    EXTERNAL_POV_INSERT_POLICY_OPTIONS = list(EXTERNAL_POV_INSERT_POLICY_OPTIONS)

    def __init__(self, project_path: str = None, llm_client=None, ui=None):
        self.project_path = project_path
        self.client = llm_client
        self.ui = ui

        # 결과물
        self.genre: str = ""
        self.preset_registry: PresetRegistry | None = None
        self.bible: dict[str, Any] = {}
        self.treatment: list[dict[str, Any]] = []
        self.episode_bibles: list[dict[str, Any]] = []
        self.style_guide: StyleGuide | None = None
        self.protagonist_config: dict[str, Any] = {}

    def _ui_log(self, text: str, **context) -> None:
        message = str(text)
        if hasattr(type(self.ui), "log"):
            self.ui.log(message, component="Stage0", stage="stage0", **context)
            return
        logging.getLogger("Stage0").info(message)
        sys.stdout.write(f"{message}\n")

    def _ui_menu(self, title: str, options: list[str], **context) -> None:
        if hasattr(type(self.ui), "menu_block"):
            self.ui.menu_block(title, options, component="Stage0", stage="stage0", **context)
            return
        self._ui_log(title, event_kind="menu", render_format="menu", **context)
        for option in options:
            self._ui_log(option, event_kind="menu_option", render_format="menu", **context)

    def _ui_prompt(self, prompt_text: str, **context) -> str:
        if hasattr(type(self.ui), "prompt"):
            return self.ui.prompt(prompt_text, component="Stage0", stage="stage0", **context)
        logging.getLogger("Stage0").info(prompt_text)
        try:
            return input(prompt_text)
        except (EOFError, KeyboardInterrupt, ValueError):
            return ""

    def _ui_selection(self, label: str, selection_value, **context) -> None:
        if hasattr(type(self.ui), "selection"):
            self.ui.selection(label, selection_value, component="Stage0", stage="stage0", **context)
            return
        self._ui_log(
            label,
            event_kind="selection",
            render_format="selection",
            selection_value=selection_value,
            **context,
        )

    def _project_work_guard_path(self) -> Path | None:
        if not self.project_path:
            return None
        return Path(self.project_path) / "config" / "work_guard.yaml"

    def _list_work_guard_templates(self) -> list[Path]:
        roots: list[Path] = []
        if self.genre:
            roots.append(self.WORK_GUARD_LIBRARY_ROOT / self.genre)
        roots.append(self.WORK_GUARD_LIBRARY_ROOT)

        candidates: dict[str, Path] = {}
        for root in roots:
            if not root.exists():
                continue
            for pattern in ("*.yaml", "*.yml"):
                for path in sorted(root.glob(pattern)):
                    candidates[str(path.resolve())] = path
        return sorted(candidates.values(), key=lambda item: str(item).lower())

    def _build_default_work_guard_yaml(self) -> str:
        work_type = self.genre or "custom"
        tracking_slots = {
            "investment": ["지분 구조 변화", "현금흐름 압박", "시장 심리 변화"],
            "wuxia": ["문파 위상 변화", "무공 성장 축", "원한/은원 추적"],
            "hunter": ["파티 전력 변화", "게이트 위협 축", "자원/장비 확보"],
        }.get(work_type, ["작품 핵심 갈등", "관계 변화", "추적 슬롯"])
        scene_engines = {
            "investment": ["협상", "실사", "IR/브리핑"],
            "wuxia": ["비무", "수련", "문파 정치"],
            "hunter": ["공략", "브리핑", "전리품 정산"],
        }.get(work_type, ["핵심 장면 엔진"])

        slot_lines = "\n".join(f"    - {slot}" for slot in tracking_slots)
        engine_lines = "\n".join(f"    - {engine}" for engine in scene_engines)
        return (
            "work_identity:\n"
            '  work_id: ""\n'
            '  family: ""\n'
            f"  work_type: {work_type}\n"
            '  one_line_truth: ""\n'
            "  mandatory_lexicon: []\n"
            "  forbidden_flattenings: []\n"
            "  tracking_slots:\n"
            f"{slot_lines}\n"
            "  mandatory_scene_engines:\n"
            f"{engine_lines}\n"
            "  registry_profiles: []\n"
            "  role_fit_constraints: []\n"
        )

    def manage_work_guard(self) -> None:
        project_guard_path = self._project_work_guard_path()
        if project_guard_path is None:
            self._ui_log("[!] 프로젝트 경로가 없어 Work Guard를 관리할 수 없습니다.", level="warning")
            return

        self._ui_menu(
            "작품가드 설정 (선택)",
            [
                "[1] 라이브러리에서 가져오기",
                "[2] 기본 템플릿으로 초기화",
                "[3] 현재 프로젝트 작품가드 미리보기",
                "[4] 현재 프로젝트 작품가드 삭제",
                "[0] 돌아가기",
            ],
            prompt_id="stage0_work_guard_menu",
        )

        try:
            choice = self._ui_prompt("\n  선택: ", prompt_id="stage0_work_guard_choice").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            choice = "0"

        if choice == "0":
            return

        project_guard_path.parent.mkdir(parents=True, exist_ok=True)

        if choice == "1":
            templates = self._list_work_guard_templates()
            if not templates:
                self._ui_log(
                    "[!] 가져올 작품가드 템플릿이 없습니다. work_guards/ 아래에 YAML을 두세요.", level="warning"
                )
                return
            self._ui_menu(
                "사용 가능한 템플릿:",
                [f"[{idx}] {template.as_posix()}" for idx, template in enumerate(templates, 1)],
                prompt_id="stage0_work_guard_template_menu",
            )
            try:
                template_choice = int(
                    self._ui_prompt("\n  가져올 번호: ", prompt_id="stage0_work_guard_template_choice").strip()
                )
                selected = templates[template_choice - 1]
            except (ValueError, IndexError, EOFError, KeyboardInterrupt):
                self._ui_log("[!] 잘못된 선택입니다.", level="warning")
                return
            project_guard_path.write_text(selected.read_text(encoding="utf-8"), encoding="utf-8")
            self._ui_selection(
                "작품가드 템플릿", selected.as_posix(), prompt_id="stage0_work_guard_template_choice", visible=False
            )
            self._ui_log(f"[v] 작품가드 가져오기 완료: {selected} -> {project_guard_path}")
            return

        if choice == "2":
            project_guard_path.write_text(self._build_default_work_guard_yaml(), encoding="utf-8")
            self._ui_log(f"[v] 기본 작품가드 초기화 완료: {project_guard_path}")
            return

        if choice == "3":
            from modules.core.project_support import load_work_guard_summary

            summary = load_work_guard_summary(Path(self.project_path))
            if not summary.get("work_guard_exists"):
                self._ui_log("[*] 현재 프로젝트에는 작품가드가 없습니다. baseline 경로로 진행 중입니다.")
                return
            self._ui_log(f"- 경로: {project_guard_path}", event_kind="summary", render_format="summary")
            self._ui_log(
                f"- work_type: {summary.get('work_type', '') or '(미지정)'}",
                event_kind="summary",
                render_format="summary",
            )
            self._ui_log(
                f"- tracking_slots: {summary.get('tracking_slots', 0)}", event_kind="summary", render_format="summary"
            )
            self._ui_log(
                f"- registry_profiles: {summary.get('registry_profiles', 0)}",
                event_kind="summary",
                render_format="summary",
            )
            self._ui_log(
                f"- role_fit_constraints: {summary.get('role_fit_constraints', 0)}",
                event_kind="summary",
                render_format="summary",
            )
            return

        if choice == "4":
            if project_guard_path.exists():
                project_guard_path.unlink()
                self._ui_log(f"[v] 작품가드 삭제 완료: {project_guard_path}")
            else:
                self._ui_log("[*] 삭제할 작품가드가 없습니다.")
            return

        self._ui_log("[!] 잘못된 선택입니다.", level="warning")

    # ============================================
    # 메뉴 시스템
    # ============================================

    def show_menu(self, is_new_project: bool = True) -> int:
        """Stage 0 메인 메뉴 표시"""
        if is_new_project:
            options = [
                "[1] 컨셉 입력 → Bible + Treatment 생성",
                "[2] 역설계 → 기존 원고에서 설정 추출",
                "[3] Bible 임포트 → 기존 JSON 불러오기",
                "[4] 스타일 레퍼런스 분석 → 참조 원고에서 문체 DNA 추출",
                "[5] 작품가드 설정 (선택)",
                "[0] 취소",
            ]
        else:
            options = [
                "[1] Bible 재생성/수정",
                "[2] 역설계 추가 (원고 추가 분석)",
                "[3] 스타일 가이드 재추출",
                "[4] 프리셋 관리",
                "[5] 스타일 레퍼런스 분석 → 참조 원고에서 문체 DNA 추출",
                "[6] 작품가드 설정 (선택)",
                "[0] 메인 메뉴로",
            ]
        self._ui_menu("Stage 0 - 프로젝트 설정", options, prompt_id="stage0_main_menu")

        try:
            choice = self._ui_prompt("\n  선택: ", prompt_id="stage0_main_menu_choice").strip()
            self._ui_selection("Stage 0 메인 메뉴", choice, prompt_id="stage0_main_menu_choice", visible=False)
            return int(choice) if choice.isdigit() else -1
        except (ValueError, EOFError):
            return -1

    def show_genre_menu(self) -> str:
        """장르 선택 메뉴"""
        genres = list(self.SUPPORTED_GENRES.items())
        options = [f"[{i}] {name} ({code})" for i, (code, name) in enumerate(genres, 1)]
        options.append("[0] 자동 감지")
        self._ui_menu("장르 선택", options, prompt_id="stage0_genre_menu")

        try:
            choice = self._ui_prompt("\n  선택: ", prompt_id="stage0_genre_choice").strip()
            if choice == "0":
                self._ui_selection("장르 선택", "auto", prompt_id="stage0_genre_choice", visible=False)
                return ""  # 자동 감지
            idx = int(choice) - 1
            if 0 <= idx < len(genres):
                self._ui_selection("장르 선택", genres[idx][0], prompt_id="stage0_genre_choice", visible=False)
                return genres[idx][0]
        except (ValueError, IndexError, EOFError):
            pass
        return ""

    def show_protagonist_config_menu(self) -> dict[str, str]:
        """주인공 설정 메뉴"""
        config = {}

        # 세계관 출신
        self._ui_menu(
            "주인공 기본 설정 / 세계관 출신",
            [f"[{i}] {opt}" for i, opt in enumerate(self.WORLD_ORIGIN_OPTIONS, 1)],
            prompt_id="stage0_world_origin_menu",
        )
        try:
            raw_choice = self._ui_prompt("    선택: ", prompt_id="stage0_world_origin_choice").strip()
        except (ValueError, IndexError, EOFError):
            raw_choice = ""
        config["world_origin"] = resolve_indexed_menu_choice(
            tuple(self.WORLD_ORIGIN_OPTIONS),
            raw_choice,
            default="현대인",
        )
        self._ui_selection("세계관 출신", config["world_origin"], prompt_id="stage0_world_origin_choice", visible=False)

        # 회귀/빙의 타입
        self._ui_menu(
            "주인공 기본 설정 / 캐릭터 타입",
            [f"[{i}] {opt}" for i, opt in enumerate(self.INCARNATION_TYPES, 1)],
            prompt_id="stage0_incarnation_menu",
        )
        try:
            raw_choice = self._ui_prompt("    선택: ", prompt_id="stage0_incarnation_choice").strip()
        except (ValueError, IndexError, EOFError):
            raw_choice = ""
        config["incarnation_type"] = resolve_indexed_menu_choice(
            tuple(self.INCARNATION_TYPES),
            raw_choice,
            default="일반",
        )
        self._ui_selection(
            "캐릭터 타입", config["incarnation_type"], prompt_id="stage0_incarnation_choice", visible=False
        )

        # [D-1] 시점(POV) 선택
        self._ui_menu(
            "주인공 기본 설정 / 시점(POV)",
            [f"[{i}] {opt}" for i, opt in enumerate(self.POV_OPTIONS, 1)],
            prompt_id="stage0_pov_menu",
        )
        try:
            raw_choice = self._ui_prompt("    선택: ", prompt_id="stage0_pov_choice").strip()
        except (ValueError, IndexError, EOFError):
            raw_choice = ""
        config["pov"] = resolve_indexed_menu_choice(
            tuple(self.POV_OPTIONS),
            raw_choice,
            default="3인칭",
        )
        self._ui_selection("시점(POV)", config["pov"], prompt_id="stage0_pov_choice", visible=False)

        default_policy = default_external_pov_insert_policy(config.get("pov", ""), genre=self.genre)
        default_index = 1
        options = []
        for i, opt in enumerate(self.EXTERNAL_POV_INSERT_POLICY_OPTIONS, 1):
            if opt == default_policy:
                default_index = i
            options.append(f"[{i}] {opt}")
        self._ui_menu("주인공 기본 설정 / 외부 시점 삽입 정책", options, prompt_id="stage0_external_pov_menu")
        try:
            raw_choice = self._ui_prompt(
                f"    선택 (기본: {default_index}): ",
                prompt_id="stage0_external_pov_choice",
            ).strip()
        except (ValueError, IndexError, EOFError):
            raw_choice = ""
        config["external_pov_insert_policy"] = resolve_external_pov_insert_policy_choice(
            raw_choice,
            primary_pov=config.get("pov", ""),
            genre=self.genre,
        )
        self._ui_selection(
            "외부 시점 삽입 정책",
            config["external_pov_insert_policy"],
            prompt_id="stage0_external_pov_choice",
            visible=False,
        )

        return config

    # ============================================
    # 신규 프로젝트 플로우
    # ============================================

    def run_new_project_flow(self) -> tuple[dict, list, StyleGuide | None]:
        """신규 프로젝트 전체 플로우"""
        # 1. 장르 선택
        self.genre = self.show_genre_menu()
        if not self.genre:
            self._ui_log("[*] 컨셉에서 장르 자동 감지 예정")

        # 2. 주인공 설정
        self.protagonist_config = self.show_protagonist_config_menu()

        # 3. 컨셉 입력
        self._ui_menu(
            "스토리 컨셉 입력 (여러 줄 가능, 빈 줄로 종료)",
            ["빈 줄을 입력하면 종료됩니다."],
            prompt_id="stage0_concept_intro",
        )
        lines = []
        try:
            while True:
                line = self._ui_prompt("", prompt_id="stage0_concept_line")
                if not line:
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt, ValueError):
            pass
        concept = "\n".join(lines)

        if not concept.strip():
            self._ui_log("[!] 컨셉이 입력되지 않았습니다.", level="warning")
            return {}, [], None

        # 4. 생성
        return self.generate_from_concept(concept)

    @staticmethod
    def _build_plot_roadmap_from_treatment(treatment: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        return build_plot_roadmap_from_treatment(treatment)

    @classmethod
    def _ensure_plot_roadmap(cls, bible: dict[str, Any], treatment: list[dict[str, Any]] | None) -> int:
        status = ensure_plot_roadmap(None, bible, treatment)
        if status.warnings:
            logging.warning(
                "[Stage0:HandoffContract] plot_roadmap not Stage 2 ready (%s): %s",
                status.source,
                "; ".join(status.warnings[:5]),
            )
        return len(status.roadmap)

    def _review_stage0_candidate(
        self,
        expander: StoryExpander,
        *,
        bible: dict[str, Any],
        treatment: list[dict[str, Any]],
        attempt: int,
        max_attempts: int,
    ) -> dict[str, Any]:
        review = expander.review_stage0_candidate(
            bible=bible,
            treatment=treatment,
            review_mode="fresh",
            attempt=attempt,
            max_attempts=max_attempts,
        )
        decision = str(review.get("decision", "REJECT") or "REJECT").upper()
        operator_message = str(review.get("operator_message", "") or review.get("reason", "") or "").strip()
        if operator_message:
            self._ui_log(
                f"[Stage0 Gate] {decision}: {operator_message}",
                event_kind="summary",
                render_format="summary",
            )
        else:
            self._ui_log(f"[Stage0 Gate] {decision}", event_kind="summary", render_format="summary")
        return review

    def generate_from_concept(self, concept: str) -> tuple[dict, list, StyleGuide | None]:
        """컨셉에서 Bible + Treatment 생성"""
        expander = StoryExpander(genre=self.genre, llm_client=self.client)

        # 분석
        self._ui_log("[*] 컨셉 분석 중...", event_kind="summary", render_format="summary")
        expander.analyze_concept(concept)

        # 장르 업데이트
        if not self.genre:
            self.genre = expander.genre
            self._ui_log(f"[v] 감지된 장르: {self.genre}", event_kind="summary", render_format="summary")

        # 프리셋 초기화
        self.preset_registry = expander.preset_registry

        review_max_attempts = getattr(expander, "_STAGE0_REVIEW_MAX_ATTEMPTS", 2)
        accepted_review: dict[str, Any] | None = None

        for attempt in range(1, review_max_attempts + 1):
            self._ui_log("[*] Bible generation in progress...", event_kind="summary", render_format="summary")
            try:
                self.bible = expander.generate_bible(self.protagonist_config)
            except StoryExpanderBibleGenerationError as exc:
                logging.warning("[Stage0] Bible generation failed: %s", exc)
                self._ui_log(
                    f"[!] Bible 생성 실패: {exc}",
                    level="warning",
                    event_kind="summary",
                    render_format="summary",
                )
                self.bible = {}
                self.treatment = []
                return {}, [], None

            if not self.bible or not isinstance(self.bible, dict) or not self.bible.get("MasterBible"):
                logging.warning("[Stage0] Bible generation failed; aborting before treatment generation")
                return {}, [], None

            self._ui_log("[*] Treatment generation in progress...", event_kind="summary", render_format="summary")
            self.treatment = expander.generate_treatment(60)
            self._ensure_plot_roadmap(self.bible, self.treatment)

            review = self._review_stage0_candidate(
                expander,
                bible=self.bible,
                treatment=self.treatment,
                attempt=attempt,
                max_attempts=review_max_attempts,
            )
            decision = str(review.get("decision", "REJECT") or "REJECT").upper()
            if decision == "PASS":
                accepted_review = review
                break
            if decision == "RETRY" and attempt < review_max_attempts:
                self._ui_log(
                    f"[Stage0 Gate] retrying candidate generation ({attempt}/{review_max_attempts})",
                    event_kind="summary",
                    render_format="summary",
                )
                continue
            self._ui_log(
                "[Stage0 Gate] stop-save: Stage 0 candidate did not clear the bounded review gate.",
                level="warning",
                event_kind="summary",
                render_format="summary",
            )
            return {}, [], None

        if accepted_review:
            self.bible["_stage0_review"] = accepted_review

        if self.project_path:
            output_dir = Path(self.project_path) / "stage0_output"
            expander.save_all(str(output_dir))
            self._ui_log(f"[v] Save complete: {output_dir}", event_kind="summary", render_format="summary")

        return self.bible, self.treatment, None

    # ============================================
    # 역설계 플로우
    # ============================================

    def run_reverse_engineering_flow(self, input_path: str = None) -> tuple[dict, list, StyleGuide | None]:
        """역설계 플로우"""
        # 입력 경로
        if not input_path:
            self._ui_log("원고 경로 입력 (파일 또는 폴더):", event_kind="prompt", render_format="prompt")
            try:
                input_path = self._ui_prompt("  > ", prompt_id="stage0_reverse_path").strip()
            except (EOFError, KeyboardInterrupt, ValueError):
                input_path = ""

        if not input_path or not Path(input_path).exists():
            self._ui_log("[!] 유효하지 않은 경로입니다.", level="warning")
            return {}, [], None

        # 장르 (선택사항)
        genre = self.show_genre_menu()

        # 역설계 실행
        expander = ReverseExpander(llm_client=self.client)
        output_dir = str(Path(self.project_path) / "stage0_output") if self.project_path else None

        try:
            self.bible, self.episode_bibles, self.style_guide = expander.run(
                input_path=input_path, output_dir=output_dir or ".", genre=genre if genre else None
            )
        except ReverseExpander.DraftEncodingError as exc:
            logging.warning("[Stage0] 역설계 입력 인코딩 오류: %s", exc)
            self._ui_log(f"[!] 인코딩 오류로 역설계를 중단합니다: {exc}", level="warning")
            return {}, [], None

        self.genre = expander.preset_registry.base_genre if expander.preset_registry else ""
        self.preset_registry = expander.preset_registry

        # [V60.95] ReverseExpander 보관 (벡터화용)
        self._reverse_expander = expander

        return self.bible, self.episode_bibles, self.style_guide

    # ============================================
    # Bible 임포트
    # ============================================

    def import_bible(self, bible_path: str = None) -> dict[str, Any]:
        """기존 Bible JSON 임포트"""
        if not bible_path:
            self._ui_log("Bible JSON 경로 입력:", event_kind="prompt", render_format="prompt")
            try:
                bible_path = self._ui_prompt("  > ", prompt_id="stage0_bible_import_path").strip()
            except (EOFError, KeyboardInterrupt, ValueError):
                bible_path = ""

        path = Path(bible_path)
        if not path.exists() or path.suffix.lower() != ".json":
            self._ui_log("[!] 유효하지 않은 JSON 파일입니다.", level="warning")
            return {}

        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)

            # [G3] 빈/손상 데이터로 기존 bible 덮어쓰기 방지
            if not loaded or not isinstance(loaded, dict):
                logging.warning("[!] Bible JSON이 비어있거나 유효하지 않습니다.")
                return {}

            self.bible = loaded

            # 장르 추출
            self.genre = self.bible.get("_genre", "")
            if not self.genre:
                master = self.bible.get("MasterBible", {})
                self.genre = master.get("_genre", "")
            if not self.genre:
                self.genre = self.show_genre_menu()  # [P1-A3-7] 존재하는 메서드로 교체

            # 프리셋 초기화
            self.preset_registry = PresetRegistry(base_genre=self.genre)

            self._ui_log(f"[v] Bible 임포트 완료 (장르: {self.genre})", event_kind="summary", render_format="summary")
            return self.bible

        except Exception as e:
            logging.warning(f"[!] 임포트 실패: {e}")
            return {}

    # ============================================
    # 프리셋 관리
    # ============================================

    def manage_presets(self) -> None:
        """프리셋 관리 메뉴"""
        if not self.preset_registry:
            self.preset_registry = PresetRegistry(base_genre=self.genre)

        while True:
            available = [g for g in PresetRegistry.GENRE_PRESETS.keys() if g not in self.preset_registry.active_presets]
            active = [g for g in self.preset_registry.active_presets if g != "common"]
            options = [f"현재 활성: {list(self.preset_registry.active_presets)}", "사용 가능한 프리셋:"]
            options.extend(f"[{i}] + {g}" for i, g in enumerate(available, 1))
            options.extend(f"[{i}] - {g}" for i, g in enumerate(active, len(available) + 1))
            options.append("[0] 돌아가기")
            self._ui_menu("프리셋 관리", options, prompt_id="stage0_preset_menu")

            try:
                raw_choice = self._ui_prompt("\n    선택: ", prompt_id="stage0_preset_choice").strip()
                choice = int(raw_choice)
                if choice == 0:
                    break
                elif choice <= len(available):
                    preset = available[choice - 1]
                    self.preset_registry.activate_preset(preset)
                    self._ui_selection("프리셋 활성화", preset, prompt_id="stage0_preset_choice", visible=False)
                    self._ui_log(f"[v] {preset} 활성화")
                else:
                    idx = choice - len(available) - 1
                    if 0 <= idx < len(active):
                        preset = active[idx]
                        self.preset_registry.deactivate_preset(preset)
                        self._ui_selection("프리셋 비활성화", preset, prompt_id="stage0_preset_choice", visible=False)
                        self._ui_log(f"[v] {preset} 비활성화")
            except (ValueError, IndexError, EOFError):
                pass

    # ============================================
    # 스타일 레퍼런스 분석
    # ============================================

    def _resolve_reference_analysis_genre(self, genre: str | None) -> str | None:
        if genre:
            return genre
        if self.genre:
            return self.genre
        resolved_genre = self.show_genre_menu()
        if resolved_genre:
            return resolved_genre
        self._ui_log("[!] 장르가 지정되지 않았습니다.", level="warning")
        return None

    def _confirm_reference_analysis_start(self) -> bool:
        try:
            confirm = (
                self._ui_prompt(
                    "\n  분석을 시작하시겠습니까? (y/n): ",
                    prompt_id="stage0_style_analysis_confirm",
                )
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt, ValueError):
            confirm = "n"
        return confirm == "y"

    def _resolve_reference_analysis_cache_mode(self, cache_mode: str | None) -> str:
        """Resolve the effective cache mode for style-reference analysis."""
        if cache_mode is None:
            self._ui_menu(
                "스타일 캐시 모드",
                [
                    "[1] 캐시 사용 (기본)",
                    "[2] 참조 원고 기준 재분석",
                    "[3] 장르 캐시 초기화 후 재분석",
                ],
                prompt_id="stage0_style_cache_menu",
            )
            try:
                cache_choice = (
                    self._ui_prompt("\n  선택 (기본: 1): ", prompt_id="stage0_style_cache_choice").strip()
                    or "1"
                )
            except (EOFError, KeyboardInterrupt, ValueError):
                cache_choice = "1"
            resolved_cache_mode = {"1": "use", "2": "refresh", "3": "reset"}.get(cache_choice, "use")
        else:
            resolved_cache_mode = cache_mode if cache_mode in {"use", "refresh", "reset"} else "use"
        cache_mode_label_map = {
            "use": "캐시 사용",
            "refresh": "캐시 무시 후 재분석",
            "reset": "캐시 초기화 후 재분석",
        }
        self._ui_log(
            f"[*] 스타일 캐시 모드: {cache_mode_label_map.get(resolved_cache_mode, '캐시 사용')}",
            event_kind="summary",
            render_format="summary",
        )
        return resolved_cache_mode

    def _load_reference_analysis_payload(self, genre: str) -> tuple[dict[str, Any], Path, dict[str, list[str]]] | None:
        prepared_refs = StyleExtractor.prepare_reference_manuscripts(genre)
        ref_base = Path(prepared_refs["ref_dir"])
        if prepared_refs["status"] == "packaged_sync":
            source_dir = prepared_refs.get("source_dir")
            self._ui_log(
                f"[*] 투자물 레퍼런스 초기화: 패키지 기본 레퍼런스를 작업 디렉터리로 동기화했습니다 ({source_dir} -> {ref_base})",
                event_kind="summary",
                render_format="summary",
            )
        ref_data = prepared_refs["works"]
        if not ref_data:
            self._ui_log(f"[!] 레퍼런스 원고가 없습니다: {ref_base}/", level="warning")
            self._ui_log(f"디렉터리 구조: config/style_references/{genre}/작품명/0001.txt", level="warning")
            if genre == "investment":
                self._ui_log(
                    "[!] 투자물 스타일 레퍼런스를 찾지 못했습니다. 작업 디렉터리 config/style_references/investment 또는 패키지 설치본을 확인하세요.",
                    level="warning",
                )
            return None
        return prepared_refs, ref_base, ref_data

    def _log_reference_analysis_catalog(self, ref_data: dict[str, list[str]]) -> None:
        total_eps = sum(len(eps) for eps in ref_data.values())
        works = list(ref_data.keys())
        self._ui_log(
            f"[*] 레퍼런스 로드 완료: {len(works)}개 작품, {total_eps}개 에피소드",
            event_kind="summary",
            render_format="summary",
        )
        for work_name in works:
            self._ui_log(
                f"- {work_name}: {len(ref_data[work_name])}개",
                event_kind="summary",
                render_format="summary",
            )

    def _extract_reference_style_guide(self, *, genre: str, cache_mode: str) -> tuple[StyleGuide | None, StyleExtractor]:
        extractor = StyleExtractor(llm_client=self.client, genre=genre)
        extractor.progress_callback = lambda message, **meta: self._ui_log(
            message,
            event_kind="summary",
            render_format="summary",
            meta=meta,
        )
        self._ui_log(
            "[*] 문체 DNA 추출 중... (참조 원고 분석 - 시간 소요)",
            event_kind="summary",
            render_format="summary",
        )
        selected_primary_pov = ""
        external_pov_insert_policy = ""
        if isinstance(self.protagonist_config, dict):
            selected_primary_pov = str(self.protagonist_config.get("pov", "") or "").strip()
            external_pov_insert_policy = str(
                self.protagonist_config.get("external_pov_insert_policy", "") or ""
            ).strip()
        style_guide = extractor.extract_from_references(
            genre,
            cache_mode=cache_mode,
            selected_primary_pov=selected_primary_pov,
            external_pov_insert_policy=external_pov_insert_policy,
        )
        return style_guide, extractor

    def _persist_reference_style_guide(self, style_guide: StyleGuide) -> None:
        if not self.project_path:
            return
        output_dir = Path(self.project_path) / "stage0_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        try:  # [TF-11-08] OSError 방어로 스타일 저장 실패 시 비정상 종료를 막는다.
            with open(output_dir / "style_guide.json", "w", encoding="utf-8") as f:
                f.write(style_guide.to_json())
            self._ui_log(
                f"- 저장: {output_dir / 'style_guide.json'}",
                event_kind="summary",
                render_format="summary",
            )
        except OSError as exc:
            import logging as _log

            _log.warning("[Stage0] style_guide.json 저장 실패 (계속 진행): %s", exc)

    def _log_reference_analysis_result(self, *, style_guide: StyleGuide, extractor: StyleExtractor) -> None:
        cache_status_map = {
            "hit": "캐시 사용",
            "refresh": "참조 원고 기준 재분석",
            "reset": "캐시 초기화 후 재분석",
            "miss": "캐시 미스 후 재분석",
        }
        self._ui_log(
            f"[v] 문체 DNA 추출 완료 (v{style_guide.analysis_version})",
            event_kind="summary",
            render_format="summary",
        )
        self._ui_log(
            f"- 캐시 상태: {cache_status_map.get(extractor.last_cache_status, '알 수 없음')}",
            event_kind="summary",
            render_format="summary",
        )
        self._ui_log(
            f"- 참조 원고: {style_guide.source_episode_count}개 / {style_guide.source_char_count:,}자",
            event_kind="summary",
            render_format="summary",
        )
        self._ui_log(
            f"- 참조 작품: {', '.join(style_guide.reference_works or [])}",
            event_kind="summary",
            render_format="summary",
        )
        self._ui_log(
            f"- 모범 문단: {len(style_guide.exemplary_passages or [])}개",
            event_kind="summary",
            render_format="summary",
        )
        self._ui_log(
            f"- Anti-AI 패턴: {len(style_guide.anti_ai_patterns or [])}개",
            event_kind="summary",
            render_format="summary",
        )
        self._persist_reference_style_guide(style_guide)

    def run_reference_analysis(self, genre: str = None, cache_mode: str | None = None) -> StyleGuide | None:
        """config/style_references/{genre}/ 폴더의 참조 원고를 분석하여 StyleGuide 생성"""
        resolved_genre = self._resolve_reference_analysis_genre(genre)
        if not resolved_genre:
            return None

        payload = self._load_reference_analysis_payload(resolved_genre)
        if payload is None:
            return None
        _, _, ref_data = payload
        self._log_reference_analysis_catalog(ref_data)

        if not self._confirm_reference_analysis_start():
            return None

        resolved_cache_mode = self._resolve_reference_analysis_cache_mode(cache_mode)
        self.style_guide, extractor = self._extract_reference_style_guide(
            genre=resolved_genre,
            cache_mode=resolved_cache_mode,
        )
        self.genre = resolved_genre

        if self.style_guide:
            self._log_reference_analysis_result(style_guide=self.style_guide, extractor=extractor)

        return self.style_guide

    # ============================================
    # 유틸리티
    # ============================================

    def get_active_schema(self) -> str:
        """현재 활성 스키마를 프롬프트용 문자열로 반환"""
        if self.preset_registry:
            return self.preset_registry.get_schema_for_prompt()
        return ""

    def get_style_prompt(self) -> str:
        """스타일 가이드를 프롬프트용 문자열로 반환"""
        if self.style_guide:
            return self.style_guide.to_prompt()
        return ""

    def save_state(self, output_dir: str):
        """현재 상태 저장"""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        state = {
            "_saved_at": datetime.now().isoformat(),
            "genre": self.genre,
            "protagonist_config": self.protagonist_config,
        }

        with open(out / "stage0_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        if self.bible:
            with open(out / "bible.json", "w", encoding="utf-8") as f:
                json.dump(self.bible, f, ensure_ascii=False, indent=2)

        if self.treatment:
            with open(out / "treatment.json", "w", encoding="utf-8") as f:
                json.dump(self.treatment, f, ensure_ascii=False, indent=2)

        if self.episode_bibles:
            with open(out / "episode_bibles.json", "w", encoding="utf-8") as f:
                json.dump(self.episode_bibles, f, ensure_ascii=False, indent=2)

        if self.preset_registry:
            with open(out / "preset_state.json", "w", encoding="utf-8") as f:
                f.write(self.preset_registry.to_json())

        if self.style_guide:
            with open(out / "style_guide.json", "w", encoding="utf-8") as f:
                f.write(self.style_guide.to_json())

        self._ui_log(f"[v] 상태 저장: {out}", event_kind="summary", render_format="summary")

    @classmethod
    def load_state(cls, project_path: str, llm_client=None) -> "StageZeroManager":
        """저장된 상태 로드"""
        manager = cls(project_path=project_path, llm_client=llm_client)
        out = Path(project_path) / "stage0_output"

        # state 로드
        state_file = out / "stage0_state.json"
        if state_file.exists():
            try:
                with open(state_file, encoding="utf-8") as f:
                    state = json.load(f)
                manager.genre = state.get("genre", "")
                manager.protagonist_config = state.get("protagonist_config", {})
            except (json.JSONDecodeError, OSError) as e:
                logging.warning("[Stage0] state 로드 실패: %s", e)

        # bible 로드
        bible_file = out / "bible.json"
        if bible_file.exists():
            try:
                with open(bible_file, encoding="utf-8") as f:
                    manager.bible = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logging.warning("[Stage0] bible 로드 실패: %s", e)

        # treatment 로드
        treatment_file = out / "treatment.json"
        if treatment_file.exists():
            try:
                with open(treatment_file, encoding="utf-8") as f:
                    manager.treatment = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logging.warning("[Stage0] treatment 로드 실패: %s", e)

        # episode_bibles 로드
        ep_bibles_file = out / "episode_bibles.json"
        if ep_bibles_file.exists():
            try:
                with open(ep_bibles_file, encoding="utf-8") as f:
                    manager.episode_bibles = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logging.warning("[Stage0] episode_bibles 로드 실패: %s", e)

        # preset 로드
        preset_file = out / "preset_state.json"
        if preset_file.exists():
            try:
                with open(preset_file, encoding="utf-8") as f:
                    manager.preset_registry = PresetRegistry.from_json(f.read())
            except (json.JSONDecodeError, OSError, ValueError) as e:
                logging.warning("[Stage0] preset 로드 실패: %s", e)
                manager.preset_registry = PresetRegistry(base_genre=manager.genre)
        else:
            manager.preset_registry = PresetRegistry(base_genre=manager.genre)

        # style guide 로드
        style_file = out / "style_guide.json"
        if style_file.exists():
            try:
                with open(style_file, encoding="utf-8") as f:
                    manager.style_guide = StyleGuide.from_dict(json.load(f))
            except (json.JSONDecodeError, OSError) as e:
                logging.warning("[Stage0] style_guide 로드 실패: %s", e)

        return manager


# 편의 함수
def create_stage_zero(project_path: str = None, llm_client=None) -> StageZeroManager:
    """StageZeroManager 인스턴스 생성 헬퍼"""
    return StageZeroManager(project_path=project_path, llm_client=llm_client)


__all__ = [
    "StageZeroManager",
    "PresetRegistry",
    "FieldDefinition",
    "StyleExtractor",
    "StyleGuide",
    "StoryExpander",
    "ReverseExpander",
    "create_stage_zero",
    "SPINNER_AVAILABLE",
]
# [P2] 스피너 유틸리티는 조건부 import이므로 존재할 때만 __all__에 추가
if SPINNER_AVAILABLE:
    __all__ += ["Spinner", "ProgressBar", "PhaseIndicator"]
