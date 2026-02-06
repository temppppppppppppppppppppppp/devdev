"""
Stage 0 Module - 프로젝트 초기화 및 역설계
==========================================
main_a.py에서 분리된 Stage 0 전용 모듈
"""

from .preset_registry import PresetRegistry, FieldDefinition
from .style_extractor import StyleExtractor, StyleGuide
from .story_expander import StoryExpander
from .reverse_expander import ReverseExpander

# 스피너 유틸리티
try:
    from .spinner import Spinner, ProgressBar, PhaseIndicator, print_header, print_success, print_error, print_info, print_warning
    SPINNER_AVAILABLE = True
except ImportError:
    SPINNER_AVAILABLE = False

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime


class StageZeroManager:
    """
    Stage 0 통합 관리자
    - 신규 프로젝트: 장르 선택 → 컨셉 입력 → Bible/Treatment 생성
    - 역설계: 기존 원고 → Bible + 회차별 상태 + 스타일 가이드 추출
    - Bible 임포트: 기존 JSON 불러오기
    """

    # 지원 장르 (preset_registry.GENRE_PRESETS와 동기화)
    SUPPORTED_GENRES = {
        "investment": "투자물/재벌물",
        "wuxia": "무협",
        "hunter": "헌터물/던전물",
        "composer": "작곡가물",
        "cooking": "요리물",
        "fantasy": "판타지",
        "romance": "로맨스",
        "politics": "정치물",
        "military": "군사/전쟁물",
        "sports": "스포츠물",
        "medical": "의학물/닥터물",
    }

    # 주인공 설정 옵션
    WORLD_ORIGIN_OPTIONS = ["현대인", "원시인"]
    INCARNATION_TYPES = ["회귀자", "빙의자", "환생자", "일반"]

    def __init__(self, project_path: str = None, llm_client=None):
        self.project_path = project_path
        self.client = llm_client

        # 결과물
        self.genre: str = ""
        self.preset_registry: Optional[PresetRegistry] = None
        self.bible: Dict[str, Any] = {}
        self.treatment: List[Dict[str, Any]] = []
        self.episode_bibles: List[Dict[str, Any]] = []
        self.style_guide: Optional[StyleGuide] = None
        self.protagonist_config: Dict[str, Any] = {}

    # ============================================
    # 메뉴 시스템
    # ============================================

    def show_menu(self, is_new_project: bool = True) -> int:
        """Stage 0 메인 메뉴 표시"""
        print("\n" + "=" * 50)
        print("  Stage 0 - 프로젝트 설정")
        print("=" * 50)

        if is_new_project:
            print("\n  [1] 컨셉 입력 → Bible + Treatment 생성")
            print("  [2] 역설계 → 기존 원고에서 설정 추출")
            print("  [3] Bible 임포트 → 기존 JSON 불러오기")
            print("  [4] 스타일 레퍼런스 분석 → 참조 원고에서 문체 DNA 추출")
            print("\n  [0] 취소")
        else:
            print("\n  [1] Bible 재생성/수정")
            print("  [2] 역설계 추가 (원고 추가 분석)")
            print("  [3] 스타일 가이드 재추출")
            print("  [4] 프리셋 관리")
            print("  [5] 스타일 레퍼런스 분석 → 참조 원고에서 문체 DNA 추출")
            print("\n  [0] 메인 메뉴로")

        try:
            choice = input("\n  선택: ").strip()
            return int(choice) if choice.isdigit() else -1
        except (ValueError, EOFError):
            return -1

    def show_genre_menu(self) -> str:
        """장르 선택 메뉴"""
        print("\n" + "-" * 40)
        print("  장르 선택")
        print("-" * 40)

        genres = list(self.SUPPORTED_GENRES.items())
        for i, (code, name) in enumerate(genres, 1):
            print(f"  [{i}] {name} ({code})")
        print(f"\n  [0] 자동 감지")

        try:
            choice = input("\n  선택: ").strip()
            if choice == "0":
                return ""  # 자동 감지
            idx = int(choice) - 1
            if 0 <= idx < len(genres):
                return genres[idx][0]
        except (ValueError, IndexError, EOFError):
            pass
        return ""

    def show_protagonist_config_menu(self) -> Dict[str, str]:
        """주인공 설정 메뉴"""
        config = {}

        print("\n" + "-" * 40)
        print("  주인공 기본 설정")
        print("-" * 40)

        # 세계관 출신
        print("\n  [세계관 출신]")
        for i, opt in enumerate(self.WORLD_ORIGIN_OPTIONS, 1):
            print(f"    [{i}] {opt}")
        try:
            choice = int(input("    선택: ").strip()) - 1
            if 0 <= choice < len(self.WORLD_ORIGIN_OPTIONS):
                config["world_origin"] = self.WORLD_ORIGIN_OPTIONS[choice]
            else:
                config["world_origin"] = "현대인"
        except (ValueError, IndexError, EOFError):
            config["world_origin"] = "현대인"

        # 회귀/빙의 타입
        print("\n  [캐릭터 타입]")
        for i, opt in enumerate(self.INCARNATION_TYPES, 1):
            print(f"    [{i}] {opt}")
        try:
            choice = int(input("    선택: ").strip()) - 1
            if 0 <= choice < len(self.INCARNATION_TYPES):
                config["incarnation_type"] = self.INCARNATION_TYPES[choice]
            else:
                config["incarnation_type"] = "일반"
        except (ValueError, IndexError, EOFError):
            config["incarnation_type"] = "일반"

        return config

    # ============================================
    # 신규 프로젝트 플로우
    # ============================================

    def run_new_project_flow(self) -> Tuple[Dict, List, Optional[StyleGuide]]:
        """신규 프로젝트 전체 플로우"""
        # 1. 장르 선택
        self.genre = self.show_genre_menu()
        if not self.genre:
            print("  [*] 컨셉에서 장르 자동 감지 예정")

        # 2. 주인공 설정
        self.protagonist_config = self.show_protagonist_config_menu()

        # 3. 컨셉 입력
        print("\n" + "-" * 40)
        print("  스토리 컨셉 입력 (여러 줄 가능, 빈 줄로 종료)")
        print("-" * 40)
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        concept = "\n".join(lines)

        if not concept.strip():
            print("  [!] 컨셉이 입력되지 않았습니다.")
            return {}, [], None

        # 4. 생성
        return self.generate_from_concept(concept)

    def generate_from_concept(self, concept: str) -> Tuple[Dict, List, Optional[StyleGuide]]:
        """컨셉에서 Bible + Treatment 생성"""
        expander = StoryExpander(genre=self.genre, llm_client=self.client)

        # 분석
        print("\n  [*] 컨셉 분석 중...")
        expander.analyze_concept(concept)

        # 장르 업데이트
        if not self.genre:
            self.genre = expander.genre
            print(f"  [v] 감지된 장르: {self.genre}")

        # 프리셋 초기화
        self.preset_registry = expander.preset_registry

        # Bible 생성
        print("  [*] Bible 생성 중...")
        self.bible = expander.generate_bible(self.protagonist_config)

        # Treatment 생성
        print("  [*] Treatment 생성 중...")
        self.treatment = expander.generate_treatment(60)

        # 저장
        if self.project_path:
            output_dir = Path(self.project_path) / "stage0_output"
            expander.save_all(str(output_dir))
            print(f"  [v] 저장 완료: {output_dir}")

        return self.bible, self.treatment, None

    # ============================================
    # 역설계 플로우
    # ============================================

    def run_reverse_engineering_flow(self, input_path: str = None) -> Tuple[Dict, List, StyleGuide]:
        """역설계 플로우"""
        # 입력 경로
        if not input_path:
            print("\n  원고 경로 입력 (파일 또는 폴더):")
            input_path = input("  > ").strip()

        if not input_path or not Path(input_path).exists():
            print("  [!] 유효하지 않은 경로입니다.")
            return {}, [], None

        # 장르 (선택사항)
        genre = self.show_genre_menu()

        # 역설계 실행
        expander = ReverseExpander(llm_client=self.client)
        output_dir = str(Path(self.project_path) / "stage0_output") if self.project_path else None

        self.bible, self.episode_bibles, self.style_guide = expander.run(
            input_path=input_path,
            output_dir=output_dir or ".",
            genre=genre if genre else None
        )

        self.genre = expander.preset_registry.base_genre if expander.preset_registry else ""
        self.preset_registry = expander.preset_registry

        # [V60.95] ReverseExpander 보관 (ChromaDB 벡터화용)
        self._reverse_expander = expander

        return self.bible, self.episode_bibles, self.style_guide

    # ============================================
    # Bible 임포트
    # ============================================

    def import_bible(self, bible_path: str = None) -> Dict[str, Any]:
        """기존 Bible JSON 임포트"""
        if not bible_path:
            print("\n  Bible JSON 경로 입력:")
            bible_path = input("  > ").strip()

        path = Path(bible_path)
        if not path.exists() or path.suffix.lower() != ".json":
            print("  [!] 유효하지 않은 JSON 파일입니다.")
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.bible = json.load(f)

            # 장르 추출
            self.genre = self.bible.get("_genre", "")
            if not self.genre:
                master = self.bible.get("MasterBible", {})
                self.genre = master.get("_genre", "investment")

            # 프리셋 초기화
            self.preset_registry = PresetRegistry(base_genre=self.genre)

            print(f"  [v] Bible 임포트 완료 (장르: {self.genre})")
            return self.bible

        except Exception as e:
            print(f"  [!] 임포트 실패: {e}")
            return {}

    # ============================================
    # 프리셋 관리
    # ============================================

    def manage_presets(self):
        """프리셋 관리 메뉴"""
        if not self.preset_registry:
            self.preset_registry = PresetRegistry(base_genre=self.genre)

        while True:
            print("\n" + "-" * 40)
            print("  프리셋 관리")
            print("-" * 40)
            print(f"\n  현재 활성: {list(self.preset_registry.active_presets)}")
            print("\n  사용 가능한 프리셋:")

            available = [g for g in PresetRegistry.GENRE_PRESETS.keys()
                         if g not in self.preset_registry.active_presets]
            for i, g in enumerate(available, 1):
                print(f"    [{i}] + {g}")

            active = [g for g in self.preset_registry.active_presets if g != "common"]
            for i, g in enumerate(active, len(available) + 1):
                print(f"    [{i}] - {g}")

            print("\n    [0] 돌아가기")

            try:
                choice = int(input("\n    선택: ").strip())
                if choice == 0:
                    break
                elif choice <= len(available):
                    preset = available[choice - 1]
                    self.preset_registry.activate_preset(preset)
                    print(f"    [v] {preset} 활성화")
                else:
                    idx = choice - len(available) - 1
                    if 0 <= idx < len(active):
                        preset = active[idx]
                        self.preset_registry.deactivate_preset(preset)
                        print(f"    [v] {preset} 비활성화")
            except (ValueError, IndexError, EOFError):
                pass

    # ============================================
    # 스타일 레퍼런스 분석
    # ============================================

    def run_reference_analysis(self, genre: str = None) -> Optional[StyleGuide]:
        """config/style_references/{genre}/ 폴더의 참조 원고를 분석하여 StyleGuide 생성"""
        # 장르 결정
        if not genre:
            genre = self.genre
        if not genre:
            genre = self.show_genre_menu()
        if not genre:
            print("  [!] 장르가 지정되지 않았습니다.")
            return None

        # 레퍼런스 로드
        ref_data = StyleExtractor.load_reference_manuscripts(genre)
        if not ref_data:
            ref_base = Path("config/style_references") / genre
            print(f"  [!] 레퍼런스 원고가 없습니다: {ref_base}/")
            print(f"      폴더 구조: config/style_references/{genre}/작품명/0001.txt")
            return None

        total_eps = sum(len(eps) for eps in ref_data.values())
        works = list(ref_data.keys())
        print(f"\n  [*] 레퍼런스 로드 완료: {len(works)}개 작품, {total_eps}개 에피소드")
        for w in works:
            print(f"      - {w}: {len(ref_data[w])}편")

        confirm = input("\n  분석을 시작하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            return None

        # 분석 실행
        extractor = StyleExtractor(llm_client=self.client)
        print("\n  [*] 문체 DNA 추출 중... (대량 원고 분석 - 시간 소요)")
        self.style_guide = extractor.extract_from_references(ref_data, genre=genre)
        self.genre = genre

        if self.style_guide:
            print(f"\n  [v] 문체 DNA 추출 완료 (v{self.style_guide.analysis_version})")
            print(f"      - 분석 원고: {self.style_guide.source_episode_count}편 / {self.style_guide.source_char_count:,}자")
            print(f"      - 참조 작품: {', '.join(self.style_guide.reference_works or [])}")
            print(f"      - 모범 문단: {len(self.style_guide.exemplary_passages or [])}개")
            print(f"      - AI 금지 패턴: {len(self.style_guide.anti_ai_patterns or [])}개")

            # 저장
            if self.project_path:
                output_dir = Path(self.project_path) / "stage0_output"
                output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_dir / "style_guide.json", 'w', encoding='utf-8') as f:
                    f.write(self.style_guide.to_json())
                print(f"      - 저장: {output_dir / 'style_guide.json'}")

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

        with open(out / "stage0_state.json", 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        if self.bible:
            with open(out / "bible.json", 'w', encoding='utf-8') as f:
                json.dump(self.bible, f, ensure_ascii=False, indent=2)

        if self.treatment:
            with open(out / "treatment.json", 'w', encoding='utf-8') as f:
                json.dump(self.treatment, f, ensure_ascii=False, indent=2)

        if self.episode_bibles:
            with open(out / "episode_bibles.json", 'w', encoding='utf-8') as f:
                json.dump(self.episode_bibles, f, ensure_ascii=False, indent=2)

        if self.preset_registry:
            with open(out / "preset_state.json", 'w', encoding='utf-8') as f:
                f.write(self.preset_registry.to_json())

        if self.style_guide:
            with open(out / "style_guide.json", 'w', encoding='utf-8') as f:
                f.write(self.style_guide.to_json())

        print(f"  [v] 상태 저장: {out}")

    @classmethod
    def load_state(cls, project_path: str, llm_client=None) -> "StageZeroManager":
        """저장된 상태 로드"""
        manager = cls(project_path=project_path, llm_client=llm_client)
        out = Path(project_path) / "stage0_output"

        # state 로드
        state_file = out / "stage0_state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            manager.genre = state.get("genre", "")
            manager.protagonist_config = state.get("protagonist_config", {})

        # bible 로드
        bible_file = out / "bible.json"
        if bible_file.exists():
            with open(bible_file, 'r', encoding='utf-8') as f:
                manager.bible = json.load(f)

        # treatment 로드
        treatment_file = out / "treatment.json"
        if treatment_file.exists():
            with open(treatment_file, 'r', encoding='utf-8') as f:
                manager.treatment = json.load(f)

        # episode_bibles 로드
        ep_bibles_file = out / "episode_bibles.json"
        if ep_bibles_file.exists():
            with open(ep_bibles_file, 'r', encoding='utf-8') as f:
                manager.episode_bibles = json.load(f)

        # preset 로드
        preset_file = out / "preset_state.json"
        if preset_file.exists():
            with open(preset_file, 'r', encoding='utf-8') as f:
                manager.preset_registry = PresetRegistry.from_json(f.read())
        else:
            manager.preset_registry = PresetRegistry(base_genre=manager.genre)

        # style guide 로드
        style_file = out / "style_guide.json"
        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                manager.style_guide = StyleGuide.from_dict(json.load(f))

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
    # 스피너 유틸리티
    "Spinner",
    "ProgressBar",
    "PhaseIndicator",
    "SPINNER_AVAILABLE",
]
