"""
Reverse Expander - 진정한 역설계
================================
기존 원고 → Bible + 회차별 상태 + 스타일 가이드 추출
Arc/Blueprint는 스킵, 원고 직접 참조 방식
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.core.constants import AIModels, GenreTypes, VolumeSettings

from .preset_registry import PresetRegistry
from .style_extractor import StyleExtractor, StyleGuide

# 스피너 import (실패해도 동작)
try:
    from .spinner import ProgressBar, Spinner, print_header, print_info, print_success

    SPINNER_AVAILABLE = True
except ImportError:
    SPINNER_AVAILABLE = False


class ReverseExpander:
    """역설계 - 기존 원고에서 설정 추출"""

    def __init__(self, project_context=None, llm_client=None) -> None:
        self.project = project_context
        self.client = llm_client
        self.preset_registry: PresetRegistry | None = None
        self.style_guide: StyleGuide | None = None

        self.raw_drafts: list[dict[str, Any]] = []  # {ep_num, title, content}
        self.bible: dict[str, Any] = {}
        self.episode_bibles: list[dict[str, Any]] = []  # 회차별 상태

    def _init_llm(self) -> None:
        """LLM 클라이언트 초기화"""
        if self.client:
            return
        try:
            from google import genai

            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
        except Exception:
            pass

    _FALLBACK_MODELS = [AIModels.SUMMARY_MODEL, AIModels.V50_MODULE_MODEL]

    # [S0-N-P1-2] 재시도 가능한 에러 패턴 (StoryExpander S0-I3과 동일)
    _RETRYABLE_PATTERNS = ("429", "rate limit", "resource exhausted", "quota", "503", "500", "unavailable", "timeout")
    _MAX_RETRIES = 3
    _BASE_DELAY = 2.0  # 초

    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 8192) -> str:
        """LLM 호출 (2-모델 폴백 + 지수 백오프 재시도)"""
        self._init_llm()
        if not self.client:
            return ""
        from google.genai import types

        for model in self._FALLBACK_MODELS:
            for attempt in range(self._MAX_RETRIES):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        ),
                    )
                    return response.text
                except Exception as e:
                    err_lower = str(e).lower()
                    is_retryable = any(p in err_lower for p in self._RETRYABLE_PATTERNS)

                    if is_retryable and attempt < self._MAX_RETRIES - 1:
                        delay = self._BASE_DELAY * (2**attempt)
                        logging.warning(
                            f"[S0-N-P1-2] {model} 일시적 오류 (attempt {attempt + 1}/{self._MAX_RETRIES}), "
                            f"{delay:.1f}초 후 재시도: {e}"
                        )
                        import time

                        time.sleep(delay)
                        continue

                    logging.warning(f"[X] {model} LLM 오류: {e}")
                    break  # 비재시도 에러 → 다음 모델로 폴백
        return ""

    def _parse_json(self, text: str) -> dict | list | None:
        """JSON 파싱 — dict 또는 list 모두 보존

        [G23] list가 반환될 때 첫 dict만 추출하면 데이터 소실.
        호출부에서 isinstance 체크로 타입 분기.
        """
        if not text:
            return None
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            parsed = json.loads(json_str.strip())
            if isinstance(parsed, dict | list):
                return parsed
            return None
        except Exception:
            return None

    # ============================================
    # Phase 1: 원고 로드 및 파싱
    # ============================================

    def load_drafts_from_file(self, file_path: str) -> int:
        """단일 파일에서 에피소드들 로드"""
        path = Path(file_path)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            # [TF-R3-S0-01] cp949/euc-kr 등 비-UTF-8 파일 폴백
            logging.warning(f"[!] UTF-8 인코딩 실패, cp949로 재시도: {file_path}")
            try:
                with open(path, encoding="cp949") as f:
                    text = f.read()
            except UnicodeDecodeError:
                logging.warning(f"[!] cp949도 실패, errors='replace'로 최종 폴백: {file_path}")
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()

        # ⓚ 제N화 패턴으로 분리
        pattern = r"ⓚ\s*제(\d+)화[.\s]*([^\n]*)"
        matches = list(re.finditer(pattern, text))

        for i, match in enumerate(matches):
            ep_num = int(match.group(1))
            title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            self.raw_drafts.append({"ep_num": ep_num, "title": title, "content": content})

        return len(self.raw_drafts)

    def load_drafts_from_folder(self, folder_path: str) -> int:
        """
        폴더에서 에피소드들 로드
        지원 패턴: ep_0001.txt, 0001.txt, 1.txt 등 (숫자 포함 txt 파일)
        자동 감지: source_drafts, drafts 하위 폴더 우선 탐색
        """
        folder = Path(folder_path)

        # source_drafts 또는 drafts 하위 폴더 자동 감지
        for subdir in ["source_drafts", "drafts"]:
            sub_path = folder / subdir
            if sub_path.exists() and sub_path.is_dir():
                # 하위 폴더에 txt 파일이 있으면 그 폴더 사용
                if list(sub_path.glob("*.txt")):
                    folder = sub_path
                    logging.info(f"📂 자동 감지: {subdir}/ 폴더 사용")
                    break

        # 모든 txt 파일 수집
        all_txt = list(folder.glob("*.txt"))

        # 숫자 추출하여 정렬
        numbered_files = []
        for f in all_txt:
            # ep_0001, 0001, 1 등 다양한 패턴에서 숫자 추출
            match = re.search(r"(\d+)", f.stem)  # 확장자 제외한 파일명에서 숫자 찾기
            if match:
                ep_num = int(match.group(1))
                numbered_files.append((ep_num, f))

        # 에피소드 번호순 정렬
        numbered_files.sort(key=lambda x: x[0])

        for ep_num, f in numbered_files:
            try:
                with open(f, encoding="utf-8") as fp:
                    content = fp.read()
            except UnicodeDecodeError:
                # [TF-R3-S0-03] cp949 폴백 (load_drafts_from_file과 동일 패턴)
                logging.warning(f"[!] UTF-8 실패, cp949 재시도: {f}")
                try:
                    with open(f, encoding="cp949") as fp:
                        content = fp.read()
                except UnicodeDecodeError:
                    logging.warning(f"[!] cp949도 실패, errors='replace'로 최종 폴백: {f}")
                    with open(f, encoding="utf-8", errors="replace") as fp:
                        content = fp.read()
            self.raw_drafts.append({"ep_num": ep_num, "title": f"제{ep_num}화", "content": content})

        return len(self.raw_drafts)

    # ============================================
    # Phase 2: 장르 감지 및 프리셋 초기화
    # ============================================

    def detect_genre(self) -> str:
        """장르 자동 감지"""
        sample = "\n".join([d["content"][:1000] for d in self.raw_drafts[:3]])

        genre_lines = "\n".join(f"- {g}: {GenreTypes.get_name(g)}" for g in GenreTypes.all())
        prompt = f"""다음 원고의 장르를 판별하세요.

## 원고 샘플
{sample[:3000]}

## 가능한 장르
{genre_lines}

## 출력 (JSON)
```json
{{"genre": "장르", "confidence": 0.0-1.0}}
```
"""
        result = self._parse_json(self._call_llm(prompt, temperature=0.3))
        return result.get("genre", GenreTypes.INVESTMENT) if isinstance(result, dict) else GenreTypes.INVESTMENT

    def init_preset(self, genre: str):
        """프리셋 레지스트리 초기화"""
        self.preset_registry = PresetRegistry(base_genre=genre)

    # ============================================
    # Phase 3: Bible 추출
    # ============================================

    def extract_bible(self) -> dict[str, Any]:
        """마스터 Bible 추출"""
        sample_text = "\n\n---\n\n".join(
            [f"[{d['ep_num']}화: {d['title']}]\n{d['content'][:4000]}" for d in self.raw_drafts[:3]]
        )

        # 주인공 추출
        protagonist = self._extract_protagonist(sample_text)

        # NPC 추출
        npcs = self._extract_npcs(sample_text)

        # 세계관 추출
        world_state = self._extract_world_state(sample_text)

        # 초기 HUD
        hud = self.preset_registry.build_initial_hud(protagonist) if self.preset_registry else {}

        self.bible = {
            "_schema_version": "2.0",
            "_genre": self.preset_registry.base_genre if self.preset_registry else "unknown",
            "_source": "reverse_expander",
            "_episode_count": len(self.raw_drafts),
            "_generated_at": datetime.now().isoformat(),
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {
                        "title": self._extract_title(),
                        "total_episodes": len(self.raw_drafts),
                    },
                    "CoreIdentity": protagonist.get("core", {}),
                },
                "protagonist_config": protagonist.get("config", {}),
                "InitialHUD": hud,
                "WorldState": world_state,
                "AssetLibrary": {
                    "KeyNPCs": npcs,
                },
            },
        }

        return self.bible

    def _extract_title(self) -> str:
        """제목 추출"""
        if self.raw_drafts:
            # 첫 화 제목에서 추측
            return self.raw_drafts[0].get("title", "무제")
        return "무제"

    def _extract_protagonist(self, sample: str) -> dict[str, Any]:
        """주인공 정보 추출"""
        prompt = f"""다음 원고에서 주인공 정보를 추출하세요.

{sample[:4000]}

JSON:
```json
{{
  "name": "이름",
  "age": 나이,
  "core": {{"protagonist": "이름", "edge": "강점", "desire": "욕망", "crisis": "위기"}},
  "config": {{"world_origin": "현대인/원시인", "incarnation_type": "회귀자/빙의자/일반"}}
}}
```
"""
        # [TF-R4-S0-01] list 반환 방어 (_extract_npcs 동일 패턴)
        result = self._parse_json(self._call_llm(prompt))
        if isinstance(result, list):
            result = result[0] if result and isinstance(result[0], dict) else None
        return result if isinstance(result, dict) else {}

    def _extract_npcs(self, sample: str) -> list[dict[str, Any]]:
        """NPC 추출"""
        prompt = f"""다음 원고에서 등장인물을 추출하세요.

{sample[:5000]}

JSON:
```json
[{{"name": "이름", "role": "역할", "relationship": "주인공과의 관계"}}]
```
"""
        result = self._parse_json(self._call_llm(prompt))
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]  # [TF-R3-S0-04] 단일 NPC dict → list 래핑
        return []

    def _extract_world_state(self, sample: str) -> dict[str, Any]:
        """세계관 추출"""
        prompt = f"""다음 원고에서 세계관/배경을 추출하세요.

{sample[:3000]}

JSON:
```json
{{"era": "시대", "location": "장소", "setting": "세계관 설명"}}
```
"""
        # [TF-R4-S0-02] list 반환 방어 (_extract_npcs 동일 패턴)
        result = self._parse_json(self._call_llm(prompt))
        if isinstance(result, list):
            result = result[0] if result and isinstance(result[0], dict) else None
        return result if isinstance(result, dict) else {}

    # ============================================
    # Phase 4: 회차별 상태 추출
    # ============================================

    def _extract_single_episode_bible(self, draft: dict, prev_state: dict, schema: str) -> dict[str, Any]:
        """단일 에피소드 상태 추출 (공통 로직)"""
        prompt = f"""이 에피소드 끝 시점의 주인공 상태를 추출하세요.

## 에피소드 {draft["ep_num"]}화
{draft["content"][:6000]}

## 이전 상태
{json.dumps(prev_state.get("hud_snapshot", {}), ensure_ascii=False)[:1000]}

{schema}

JSON:
```json
{{
  "ep_num": {draft["ep_num"]},
  "hud_snapshot": {{필드들}},
  "changes": ["이번 화에서 변한 것들"],
  "new_npcs": ["새로 등장한 인물"],
  "key_events": ["핵심 사건"]
}}
```
"""
        result = self._parse_json(self._call_llm(prompt, temperature=0.5))
        # [G23] list 반환 시 첫 dict 추출
        if isinstance(result, list):
            result = result[0] if result and isinstance(result[0], dict) else None

        if result and isinstance(result, dict):
            # HUD 정규화
            if self.preset_registry and "hud_snapshot" in result:
                result["hud_snapshot"] = self.preset_registry.normalize_hud(result["hud_snapshot"])
            return result

        return {"ep_num": draft["ep_num"], "hud_snapshot": {}, "changes": [], "new_npcs": [], "key_events": []}

    _BATCH_SIZE = 5  # [S0-I4] 배치 크기
    _MAX_WORKERS = 3  # [S0-I4] API rate limit 고려

    def extract_episode_bibles(self) -> list[dict[str, Any]]:
        """회차별 상태 변화 추출 — [G-2] prev_state 의존성 보장을 위한 배치 내 순차 처리."""
        self.episode_bibles = []
        schema = self.preset_registry.get_schema_for_prompt() if self.preset_registry else ""

        drafts = self.raw_drafts
        total = len(drafts)
        for batch_start in range(0, total, self._BATCH_SIZE):
            batch = drafts[batch_start : batch_start + self._BATCH_SIZE]
            logging.info(f"[G-2] 배치 순차 추출 시작: {batch[0]['ep_num']}~{batch[-1]['ep_num']}화 ({len(batch)}건)")
            for draft in batch:
                prev_state = self.episode_bibles[-1] if self.episode_bibles else {}
                ep_num = draft.get("ep_num", 0)
                try:
                    extracted = self._extract_single_episode_bible(draft, prev_state, schema)
                except Exception as exc:
                    logging.warning(f"[G-2] 제{ep_num}화 순차 추출 실패: {exc}")
                    extracted = {
                        "ep_num": ep_num,
                        "hud_snapshot": {},
                        "changes": [],
                        "new_npcs": [],
                        "key_events": [],
                    }
                self.episode_bibles.append(extracted)

        logging.info(f"[G-2] 전체 배치 순차 추출 완료: {len(self.episode_bibles)}건")
        return self.episode_bibles

    # ============================================
    # Phase 5: 스타일 가이드 추출
    # ============================================

    def extract_style_guide(self) -> StyleGuide:
        """스타일 가이드 추출"""
        extractor = StyleExtractor(llm_client=self.client)
        drafts_text = [d["content"] for d in self.raw_drafts]
        self.style_guide = extractor.extract_from_drafts(drafts_text)
        return self.style_guide

    # ============================================
    # Phase 6: 저장
    # ============================================

    def save_all(self, output_dir: str):
        """전체 저장"""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Bible
        with open(out / "bible.json", "w", encoding="utf-8") as f:
            # [DB-Eff-P4] export 전용: DB anchors 테이블이 primary source.
            # stage0_output/*.json은 편집/참조용 사본.
            json.dump(self.bible, f, ensure_ascii=False, indent=2)

        # Episode Bibles
        with open(out / "episode_bibles.json", "w", encoding="utf-8") as f:
            # [DB-Eff-P4] export 전용: DB anchors 테이블이 primary source.
            # stage0_output/*.json은 편집/참조용 사본.
            json.dump(self.episode_bibles, f, ensure_ascii=False, indent=2)

        # Style Guide
        if self.style_guide:
            with open(out / "style_guide.json", "w", encoding="utf-8") as f:
                f.write(self.style_guide.to_json())

        # Preset Registry 상태
        if self.preset_registry:
            with open(out / "preset_state.json", "w", encoding="utf-8") as f:
                f.write(self.preset_registry.to_json())

        logging.info(f"[v] 저장 완료: {out}")

    # ============================================
    # Phase 7: 벡터화 저장 (VecMemory)
    # ============================================

    def persist_to_vectordb(self, project_context=None, memory=None) -> int:
        """[Phase 4D-4] 원고를 벡터 DB에 저장 (VecMemory).

        Args:
            project_context: ProjectContext 인스턴스
            memory: 외부 주입 VecMemory 인스턴스 (없으면 자체 생성)

        Returns:
            int: 저장 성공한 에피소드 수
        """
        if not self.raw_drafts:
            logging.info("[!] 저장할 원고가 없습니다. load_drafts_*를 먼저 호출하세요.")
            return 0

        ctx = project_context or self.project
        if not ctx:
            logging.info("[!] project_context가 필요합니다.")
            return 0

        # 메모리 엔진 결정: 외부 주입 → VecMemory 자체 생성
        if memory is None:
            try:
                import os

                from modules.core.vec_memory import VecMemory

                if hasattr(ctx, "db") and ctx.db and hasattr(ctx.db, "conn") and ctx.db.conn:
                    memory = VecMemory(
                        api_key=os.getenv("GOOGLE_API_KEY", ""),
                        conn=ctx.db.conn,
                        lock=getattr(ctx.db, "_lock", None),
                    )
                else:
                    vec_db_path = ctx.paths.memory / "vec_memory.db"
                    ctx.paths.memory.mkdir(parents=True, exist_ok=True)
                    memory = VecMemory(db_path=vec_db_path, api_key=os.getenv("GOOGLE_API_KEY", ""))
            except Exception as e:
                logging.warning(f"[!] VecMemory 초기화 실패: {e}")
                return 0

        if not memory.is_operational():
            logging.info("[!] 벡터 메모리가 비활성 상태입니다.")
            return 0

        success_count = 0
        total = len(self.raw_drafts)

        logging.info(f"[*] 벡터화 시작 ({total}개 에피소드)...")

        for i, draft in enumerate(self.raw_drafts):
            ep_num = draft.get("ep_num", i + 1)
            title = draft.get("title", f"제{ep_num}화")
            content = draft.get("content", "")

            if not content:
                logging.info(f"[skip] 제{ep_num}화: 내용 없음")
                continue

            causal_links = {
                "title": title,
                "source": "reverse_expander",
                "char_count": len(content),
            }

            _eb_map = {eb.get("ep_num"): eb for eb in self.episode_bibles} if self.episode_bibles else {}
            ep_bible = _eb_map.get(ep_num, {})  # [TF-R2-S01-01] 인덱스 대신 ep_num 키 사용
            if ep_bible:
                causal_links["new_npcs"] = ep_bible.get("new_npcs", [])
                causal_links["new_items"] = ep_bible.get("new_items", [])
                causal_links["location_change"] = ep_bible.get("location_change", "")

            try:
                result = memory.memorize_v20_episode(
                    ep_num=ep_num,
                    text=content,
                    summary=title[:500],
                    causal_links=causal_links,
                )
                if result:
                    success_count += 1
                    if (i + 1) % 10 == 0 or (i + 1) == total:
                        logging.info(f"[{i + 1}/{total}] 벡터화 진행 중...")
            except Exception as e:
                logging.warning(f"[X] 제{ep_num}화 벡터화 실패: {str(e)[:50]}")

        logging.info(f"[v] 벡터화 완료: {success_count}/{total}개")
        return success_count

    # ============================================
    # 통합 실행
    # ============================================

    def run(self, input_path: str, output_dir: str, genre: str = None) -> tuple[dict, list, StyleGuide | None]:
        """전체 역설계 파이프라인"""
        if SPINNER_AVAILABLE:
            print_header("Reverse Engineering", style="double")

            # 1. 로드
            with Spinner("원고 로드 중", style="dots"):
                path = Path(input_path)
                if path.is_file():
                    count = self.load_drafts_from_file(str(path))
                else:
                    count = self.load_drafts_from_folder(str(path))
            print_success(f"{count}개 에피소드 로드")

            # 2. 장르 감지
            with Spinner("장르 감지 중", style="braille"):
                if not genre:
                    genre = self.detect_genre()
                self.init_preset(genre)
            print_success(f"장르: {genre}")

            # 3. Bible 추출
            with Spinner("Bible 추출 중", style="pulse"):
                self.extract_bible()
            print_success("Bible 추출 완료")

            # 4. 회차별 상태 추출 (ProgressBar)
            print_info(f"회차별 상태 추출 ({len(self.raw_drafts)}개 에피소드)")
            self._extract_episode_bibles_with_progress()

            # 5. 스타일 가이드 추출
            with Spinner("스타일 가이드 추출 중", style="star"):
                self.extract_style_guide()
            print_success("스타일 가이드 추출 완료")

            # 6. 저장
            with Spinner("저장 중", style="grow"):
                self.save_all(output_dir)

            print_header("역설계 완료!", style="simple")
        else:
            # 스피너 없는 폴백
            logging.info("\n[*] 역설계 시작")

            path = Path(input_path)
            if path.is_file():
                count = self.load_drafts_from_file(str(path))
            else:
                count = self.load_drafts_from_folder(str(path))
            logging.info(f"[v] {count}개 에피소드 로드")

            if not genre:
                genre = self.detect_genre()
            logging.info(f"[v] 장르: {genre}")
            self.init_preset(genre)

            logging.info("[*] Bible 추출...")
            self.extract_bible()

            logging.info("[*] 회차별 상태 추출...")
            self.extract_episode_bibles()

            logging.info("[*] 스타일 가이드 추출...")
            self.extract_style_guide()

            self.save_all(output_dir)

            logging.info("\n[v] 역설계 완료!")

        if self.style_guide is None:
            logging.warning("[ReverseExpander] 스타일 가이드 추출 실패 — None 반환")

        return self.bible, self.episode_bibles, self.style_guide

    def _extract_episode_bibles_with_progress(self) -> None:
        """스피너와 함께 회차별 상태 추출 — [G-2] 배치 내 순차 처리."""
        self.episode_bibles = []
        schema = self.preset_registry.get_schema_for_prompt() if self.preset_registry else ""

        drafts = self.raw_drafts
        total = len(drafts)
        progress = ProgressBar(total, "회차별 상태 추출")
        progress.start()

        for batch_start in range(0, total, self._BATCH_SIZE):
            batch = drafts[batch_start : batch_start + self._BATCH_SIZE]
            progress.update(message=f"배치 {batch[0]['ep_num']}~{batch[-1]['ep_num']}화 순차 처리 중")
            for draft in batch:
                prev_state = self.episode_bibles[-1] if self.episode_bibles else {}
                ep_num = draft.get("ep_num", 0)
                try:
                    extracted = self._extract_single_episode_bible(draft, prev_state, schema)
                except Exception as exc:
                    logging.warning(f"[G-2] 제{ep_num}화 순차 추출 실패: {exc}")
                    extracted = {
                        "ep_num": ep_num,
                        "hud_snapshot": {},
                        "changes": [],
                        "new_npcs": [],
                        "key_events": [],
                    }
                self.episode_bibles.append(extracted)

        progress.finish(f"회차별 상태 추출 완료 ({len(self.episode_bibles)}개)")

    # ============================================
    # Phase 8: DB 저장 및 Stub 생성
    # ============================================

    def persist_to_db(self, project_context=None) -> dict[str, int]:
        """
        [V61] 역설계 결과를 DB에 저장
        - manuscripts 테이블에 원고 저장
        - blueprints 테이블에 stub 저장
        - arcs anchor에 stub 저장

        Args:
            project_context: ProjectContext 인스턴스

        Returns:
            {"manuscripts": N, "blueprints": N, "arcs": N}
        """
        ctx = project_context or self.project
        if not ctx:
            logging.info("[!] project_context가 필요합니다.")
            return {"manuscripts": 0, "blueprints": 0, "arcs": 0}

        # [TF7-P2-01] 원자적 트랜잭션: 모든 _save_* 완료 후 단일 커밋
        try:
            ctx.db.begin()
            result = {
                "manuscripts": self._save_manuscripts_to_db(ctx),
                "state_logs": self._save_state_logs_to_db(ctx),  # hud_snapshot 저장
                "episode_bibles": self._save_episode_bibles_to_db(ctx),
                "blueprints": self._save_blueprint_stubs(ctx),
                "arcs": self._save_arc_stubs(ctx),
            }

            # [V61.1] Arc stub 보강 (episode_bibles 데이터로 state_changes, joint_docs 채우기)
            enriched = self._enrich_arc_stubs_from_episode_bibles(ctx)
            result["arc_enriched"] = enriched

            ctx.db.commit()
        except Exception as _tx_err:
            logging.warning(f"[!] persist_to_db 트랜잭션 실패, 롤백: {_tx_err}")
            try:
                ctx.db.rollback()
            except Exception:
                pass
            result = {
                "manuscripts": 0,
                "state_logs": 0,
                "episode_bibles": 0,
                "blueprints": 0,
                "arcs": 0,
                "arc_enriched": 0,
            }

        logging.info(f"[v] DB 저장 완료: {result}")
        return result

    def _save_manuscripts_to_db(self, ctx) -> int:
        """원고를 manuscripts 테이블에 저장"""
        if not self.raw_drafts:
            return 0

        count = 0
        for draft in self.raw_drafts:
            ep_num = draft.get("ep_num")
            title = draft.get("title", f"제{ep_num}화")
            content = draft.get("content", "")

            if not content:
                continue

            try:
                # DBManager.save_manuscript() 사용
                ctx.db.save_manuscript(ep_num, title, content)
                count += 1
            except Exception as e:
                logging.warning(f"[!] 원고 저장 실패 (ep_{ep_num}): {e}")

        return count

    def _save_state_logs_to_db(self, ctx) -> int:
        """
        역설계 hud_snapshot을 DB state_logs 테이블에 저장
        Stage 4에서 get_latest_state(), load_state_log()로 참조
        """
        if not self.episode_bibles:
            return 0

        count = 0
        for ep_bible in self.episode_bibles:
            ep_num = ep_bible.get("ep_num")
            hud_snapshot = ep_bible.get("hud_snapshot", {})

            if not ep_num or not hud_snapshot:
                continue

            # state_log 데이터 구성 (Stage 4 형식과 호환)
            state_data = {
                "hud_snapshot": hud_snapshot,
                "actual_truth": hud_snapshot,  # Stage 4에서 actual_truth로 참조
                "_source": "reverse_engineered",
                "ep_num": ep_num,
            }

            # 요약 생성
            summary_parts = []
            if hud_snapshot.get("location"):
                summary_parts.append(f"위치: {hud_snapshot['location']}")
            if hud_snapshot.get("current_objective"):
                summary_parts.append(f"목표: {hud_snapshot['current_objective'][:50]}")
            summary = " / ".join(summary_parts) if summary_parts else f"제{ep_num}화 상태"

            try:
                ctx.db.save_state_log_with_summary(ep_num, state_data, summary)
                count += 1
            except Exception as e:
                logging.warning(f"[!] State Log 저장 실패 (ep_{ep_num}): {e}")

        return count

    def _save_episode_bibles_to_db(self, ctx) -> int:
        """
        역설계 episode_bibles를 DB episode_bibles 테이블에 저장
        스키마 변환: 역설계 형식 → Stage 4 형식
        """
        if not self.episode_bibles:
            return 0

        count = 0
        for ep_bible in self.episode_bibles:
            ep_num = ep_bible.get("ep_num")
            if not ep_num:
                continue

            # 스키마 변환
            hud = ep_bible.get("hud_snapshot", {})
            ep_bible.get("changes", [])
            key_events = ep_bible.get("key_events", [])
            new_npcs_raw = ep_bible.get("new_npcs", [])

            # new_npcs 정규화 (문자열 리스트로)
            new_npcs = []
            for npc in new_npcs_raw:
                if isinstance(npc, dict):
                    new_npcs.append(npc.get("name", str(npc)))
                else:
                    new_npcs.append(str(npc))

            # state_changes: hud_snapshot에서 주요 상태 추출
            state_changes = {}
            if hud:
                # 투자물 관련 필드
                if hud.get("capital"):
                    state_changes["capital"] = hud.get("capital")
                if hud.get("portfolio"):
                    state_changes["portfolio"] = hud.get("portfolio")
                # 일반 필드
                if hud.get("location"):
                    state_changes["location"] = hud.get("location")
                if hud.get("injuries") and hud.get("injuries") != "정상":
                    state_changes["injuries"] = hud.get("injuries")
                if hud.get("current_objective"):
                    state_changes["current_objective"] = hud.get("current_objective")

            # relationship_changes: hud의 relationships에서 추출
            relationship_changes = []
            relationships = hud.get("relationships", {})
            if isinstance(relationships, dict):
                for target, desc in relationships.items():
                    relationship_changes.append({"target": target, "to": desc, "justification": "역설계 추출"})

            # reveals: key_events를 reveals로 매핑
            reveals = key_events if isinstance(key_events, list) else []

            # DB 스키마에 맞는 bible_delta 구성
            bible_delta = {
                "new_items": [],  # 역설계에서 아이템 추출 없음
                "lost_items": [],
                "new_npcs": new_npcs,
                "npc_deaths": [],
                "relationship_changes": relationship_changes,
                "state_changes": state_changes,
                "time_passed": "",
                "reveals": reveals,
                "causal_links": [],
                "karma_matrix": [],
                "knowledge_map": {},
            }

            try:
                ctx.db.save_episode_bible(ep_num, bible_delta)
                count += 1
            except Exception as e:
                logging.warning(f"[!] Episode Bible DB 저장 실패 (ep_{ep_num}): {e}")

        return count

    def _save_blueprint_stubs(self, ctx) -> int:
        """Blueprint stub을 blueprints 테이블에 저장"""
        if not self.raw_drafts:
            return 0

        count = 0
        for i, draft in enumerate(self.raw_drafts):
            ep_num = draft.get("ep_num")

            # episode_bibles에서 정보 가져오기
            ep_bible = {}
            if self.episode_bibles and i < len(self.episode_bibles):
                ep_bible = self.episode_bibles[i]

            # Blueprint stub 생성
            stub = {
                "_stub": True,
                "_source": "reverse_engineered",
                "ep_num": ep_num,
                "title": draft.get("title", f"제{ep_num}화"),
                "arc_no": (ep_num - 1) // VolumeSettings.EPISODES_PER_ARC + 1,
                "scenes": [],  # 빈 씬 (stub이므로)
                "key_events": ep_bible.get("key_events", []),
                "hud_snapshot": ep_bible.get("hud_snapshot", {}),
                "new_npcs": ep_bible.get("new_npcs", []),
                "changes": ep_bible.get("changes", []),
            }

            try:
                # blueprints 테이블에 저장
                ctx.db.save_blueprint(ep_num, stub)
                count += 1
            except Exception as e:
                logging.warning(f"[!] Blueprint stub 저장 실패 (ep_{ep_num}): {e}")

        return count

    def _save_arc_stubs(self, ctx) -> int:
        """Arc stub을 arcs anchor에 저장"""
        if not self.raw_drafts:
            return 0

        # 에피소드 범위로 Arc 계산
        ep_nums = sorted([d["ep_num"] for d in self.raw_drafts])
        max_ep = max(ep_nums)
        epa = VolumeSettings.EPISODES_PER_ARC
        arc_count = (max_ep - 1) // epa + 1

        arc_stubs = []
        for arc_no in range(1, arc_count + 1):
            ep_start = (arc_no - 1) * epa + 1
            ep_end = min(arc_no * epa, max_ep)

            # 해당 Arc의 에피소드들
            arc_episodes = [d for d in self.raw_drafts if ep_start <= d["ep_num"] <= ep_end]
            if not arc_episodes:
                continue

            # Arc 내 key_events 수집
            arc_events = []
            _eb_map = {eb.get("ep_num"): eb for eb in self.episode_bibles} if self.episode_bibles else {}
            for ep in arc_episodes:
                _ep_bible = _eb_map.get(ep["ep_num"], {})
                arc_events.extend(_ep_bible.get("key_events", []))

            stub = {
                "_stub": True,
                "_source": "reverse_engineered",
                "arc_no": arc_no,
                "volume_no": (arc_no - 1) // VolumeSettings.ARCS_PER_VOLUME + 1,
                "ep_start": ep_start,
                "ep_end": ep_end,
                "tactical_doc": f"[역설계] Arc {arc_no}: 제{ep_start}화~제{ep_end}화 (원고 존재)",
                "key_events": arc_events[:10],  # 최대 10개
                "joint_docs": {},
                "state_changes": {},
            }
            arc_stubs.append(stub)

        # arcs anchor에 저장
        try:
            existing_arcs = ctx.db.load_anchor("arcs") or []
            if isinstance(existing_arcs, dict):
                existing_arcs = list(existing_arcs.values())

            # 기존 Arc와 병합 (stub은 뒤에 추가하거나 덮어쓰기)
            existing_arc_nums = {a.get("arc_no") for a in existing_arcs if a.get("arc_no")}
            for stub in arc_stubs:
                if stub["arc_no"] not in existing_arc_nums:
                    existing_arcs.append(stub)

            # arc_no 순으로 정렬
            existing_arcs.sort(key=lambda x: x.get("arc_no", 0))

            ctx.db.save_anchor("arcs", existing_arcs)

            return len(arc_stubs)
        except Exception as e:
            logging.warning(f"[!] Arc stub 저장 실패: {e}")
            return 0

    def _enrich_arc_stubs_from_episode_bibles(self, ctx) -> int:
        """
        [V61.1] Arc stub을 episode_bibles 데이터로 보강

        Stage 2/3에서 StateTracker가 Arc의 state_changes를 읽으므로,
        역설계 stub에도 episode_bibles에서 추출한 데이터를 채워야 함.

        보강 항목:
        - state_changes: npc_deaths, relationship_changes 등
        - joint_docs: 마지막 에피소드의 위치/자산/목표
        - tactical_doc: reveals 기반 요약
        - introduced_npcs: 해당 Arc에서 등장한 NPC 목록

        Returns:
            보강된 Arc 수
        """
        if not self.episode_bibles:
            return 0

        try:
            # arcs anchor 로드
            arcs = ctx.db.load_anchor("arcs") or []
            if not arcs:
                return 0

            # episode_bibles를 ep_num 기준 dict로 변환
            ep_bibles_map = {}
            for eb in self.episode_bibles:
                ep_num = eb.get("ep_num")
                if ep_num:
                    ep_bibles_map[ep_num] = eb

            enriched_count = 0

            for arc in arcs:
                if not arc.get("_stub"):
                    continue

                arc_no = arc.get("arc_no", 0)
                ep_start = arc.get("ep_start", 1)
                ep_end = arc.get("ep_end", 5)

                # 해당 Arc 범위의 episode_bibles 집계
                agg_npcs = []
                agg_deaths = []
                agg_relationships = []
                agg_reveals = []
                last_hud = {}

                for ep in range(ep_start, ep_end + 1):
                    eb = ep_bibles_map.get(ep, {})
                    if not eb:
                        continue

                    hud = eb.get("hud_snapshot", {})

                    # NPC 수집
                    for npc in eb.get("new_npcs", []):
                        if npc and npc not in agg_npcs:
                            if isinstance(npc, dict):
                                agg_npcs.append(npc.get("name", str(npc)))
                            else:
                                agg_npcs.append(str(npc))

                    # 사망 수집 (episode_bibles의 npc_deaths는 보통 비어있지만 있으면 수집)
                    for death in eb.get("npc_deaths", []):
                        if death and death not in agg_deaths:
                            agg_deaths.append(death)

                    # 관계 변화 (hud의 relationships에서)
                    relationships = hud.get("relationships", {})
                    if isinstance(relationships, dict):
                        for target, desc in relationships.items():
                            # 기존 관계 덮어쓰기 (최신 상태 유지)
                            found = False
                            for i, existing in enumerate(agg_relationships):
                                if existing.get("npc") == target:
                                    agg_relationships[i] = {
                                        "npc": target,
                                        "from": "?",
                                        "to": desc[:100] if isinstance(desc, str) else str(desc)[:100],
                                        "episode": ep,
                                    }
                                    found = True
                                    break
                            if not found and len(agg_relationships) < 15:
                                agg_relationships.append(
                                    {
                                        "npc": target,
                                        "from": "?",
                                        "to": desc[:100] if isinstance(desc, str) else str(desc)[:100],
                                        "episode": ep,
                                    }
                                )

                    # reveals/key_events 수집
                    for reveal in eb.get("key_events", []):
                        if reveal and reveal not in agg_reveals:
                            agg_reveals.append(reveal)

                    # 마지막 HUD 유지
                    if hud:
                        last_hud = hud

                # Arc stub 업데이트
                arc["state_changes"] = {
                    "npc_deaths": [{"name": d, "episode": ep_end, "cause": "역설계 추출"} for d in agg_deaths]
                    if agg_deaths
                    else [],
                    "skill_acquisitions": [],  # 투자물 등 비무협 장르는 비워둠
                    "relationship_changes": agg_relationships[:10],  # 상위 10개
                    "major_items": [],
                }

                # joint_docs: 마지막 에피소드 상태
                arc["joint_docs"] = {
                    "location": last_hud.get("location", ""),
                    "capital": last_hud.get("capital", ""),
                    "portfolio": last_hud.get("portfolio", []),
                    "current_objective": last_hud.get("current_objective", ""),
                    "injuries": last_hud.get("injuries", "정상"),
                }

                # tactical_doc 보강 (reveals 기반)
                if agg_reveals:
                    reveals_summary = "; ".join(agg_reveals[:5])
                    arc["tactical_doc"] = f"[역설계] Arc {arc_no} (ep {ep_start}~{ep_end}): {reveals_summary[:300]}"

                # 새 NPC 목록
                arc["introduced_npcs"] = agg_npcs[:20]

                enriched_count += 1
                logging.info(f"[v] Arc {arc_no} 보강: rels={len(agg_relationships[:10])}, npcs={len(agg_npcs[:20])}")

            # 저장
            ctx.db.save_anchor("arcs", arcs)
            ctx.db.conn.commit()

            return enriched_count

        except Exception as e:
            logging.warning(f"[!] Arc stub 보강 실패: {e}")
            return 0

    def get_stub_summary(self) -> dict[str, Any]:
        """stub 생성 요약 정보"""
        if not self.raw_drafts:
            return {}

        ep_nums = sorted([d["ep_num"] for d in self.raw_drafts])
        max_ep = max(ep_nums)
        min_ep = min(ep_nums)

        # Arc 계산
        arc_count = (max_ep - 1) // VolumeSettings.EPISODES_PER_ARC + 1

        return {
            "episodes": len(self.raw_drafts),
            "ep_range": f"{min_ep}~{max_ep}",
            "arc_stubs": arc_count,
            "arc_stub_range": f"Arc 1~{arc_count}",
            "blueprint_stubs": len(self.raw_drafts),
            "next_episode": max_ep + 1,
            "next_blueprint": max_ep + 1,
            "next_arc": arc_count + 1,
        }
