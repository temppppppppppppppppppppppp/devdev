"""
Story Expander - 컨셉 → Bible + Treatment 생성
==============================================
블록 연구소 story_expander.py에서 핵심 로직 이동
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.core.constants import AIModels, GenreTypes, smart_truncate
from modules.core.google_client_factory import build_google_genai_client
from modules.core.llm_generate import generate_content_via_router
from modules.core.stage0_handoff import ensure_plot_roadmap

from .preset_registry import PresetRegistry

# 스피너 import (실패해도 동작)
try:
    from .spinner import PhaseIndicator, Spinner, print_header, print_success

    SPINNER_AVAILABLE = True
except ImportError:
    SPINNER_AVAILABLE = False


class StoryExpanderBibleGenerationError(RuntimeError):
    """Raised when Stage 0 Bible generation cannot satisfy the minimal contract."""


class StoryExpander:
    """스토리 확장기 - 컨셉 → Bible + Treatment"""

    BibleGenerationError = StoryExpanderBibleGenerationError
    _CONCEPT_PROMPT_MAX = 12000
    _CONCEPT_PROMPT_HEAD = 7000
    _STAGE0_REVIEW_MAX_ATTEMPTS = 2
    _STAGE0_REVIEW_WINDOW = 3

    def __init__(self, genre: str = None, llm_client=None):
        self.genre = genre
        self.client = llm_client
        self.preset_registry: PresetRegistry | None = None

        self.concept: str = ""
        self.extracted: dict[str, Any] = {}
        self.bible: dict[str, Any] = {}
        self.treatment: list[dict[str, Any]] = []

    def _init_llm(self) -> None:
        """LLM 초기화"""
        if self.client:
            return
        try:
            self.client = build_google_genai_client()
        except (ImportError, ValueError, RuntimeError) as _e:  # [V64.P4] LLM client init failure
            logging.warning("[StoryExpander] LLM 초기화 실패 (비차단): %s", _e)

    _FALLBACK_MODELS = [AIModels.SUMMARY_MODEL, AIModels.V50_MODULE_MODEL]

    # [S0-I3] 재시도 가능한 에러 패턴 (rate limit / 일시적 네트워크 오류)
    _RETRYABLE_PATTERNS = ("429", "rate limit", "resource exhausted", "quota", "503", "500", "unavailable", "timeout")
    _MAX_RETRIES = 3
    _BASE_DELAY = 2.0  # 초

    def _call_llm(self, prompt: str, temperature: float = 0.85, max_tokens: int = 8192) -> str:
        """LLM 호출 (2-모델 폴백 + 지수 백오프 재시도)"""
        self._init_llm()
        if not self.client:
            return ""
        from google.genai import types

        for model in self._FALLBACK_MODELS:
            for attempt in range(self._MAX_RETRIES):
                try:
                    response = generate_content_via_router(
                        client=self.client,
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        ),
                    )
                    return response.text or ""
                except Exception as e:
                    err_lower = str(e).lower()
                    is_retryable = any(p in err_lower for p in self._RETRYABLE_PATTERNS)

                    if is_retryable and attempt < self._MAX_RETRIES - 1:
                        delay = self._BASE_DELAY * (2**attempt)
                        logging.warning(
                            f"[S0-I3] {model} 일시적 오류 (attempt {attempt + 1}/{self._MAX_RETRIES}), "
                            f"{delay:.1f}초 후 재시도: {e}"
                        )
                        time.sleep(delay)
                        continue

                    logging.warning(f"[X] {model} LLM 오류: {e}")
                    break  # 비재시도 에러 → 다음 모델로 폴백
        return ""

    def _parse_json(self, text: str) -> Any:
        """JSON 파싱"""
        if not text:
            return None
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, ValueError, IndexError):  # [V64.P4] JSON parse failure
            return None

    def _get_concept_prompt_text(self, *, max_chars: int | None = None, head_chars: int | None = None) -> str:
        """Keep more concept detail while staying inside a bounded prompt budget."""
        max_chars = max_chars or self._CONCEPT_PROMPT_MAX
        head_chars = head_chars or self._CONCEPT_PROMPT_HEAD
        return smart_truncate(self.concept or "", max_chars=max_chars, head_chars=head_chars)

    def _build_story_brief(self) -> str:
        """Compact brief reused by Stage 0 generation prompts."""
        extracted = self.extracted if isinstance(self.extracted, dict) else {}
        parts: list[str] = []

        concept_text = self._get_concept_prompt_text()
        if concept_text:
            parts.append(f"컨셉: {concept_text}")
        if self.genre:
            parts.append(f"장르: {self.genre}")

        themes = [str(item).strip() for item in (extracted.get("themes") or []) if str(item).strip()]
        if themes:
            parts.append(f"테마: {', '.join(themes[:4])}")

        tone = str(extracted.get("tone", "") or "").strip()
        if tone:
            parts.append(f"톤: {tone}")

        world_laws = [str(item).strip() for item in (extracted.get("world_laws") or []) if str(item).strip()]
        if world_laws:
            parts.append("세계 법칙: " + "; ".join(world_laws[:3]))

        return "\n".join(parts).strip()

    @staticmethod
    def _preview_blocks(blocks: list[dict[str, Any]] | None, *, limit: int = 3) -> list[dict[str, str]]:
        if not isinstance(blocks, list):
            return []
        previews: list[dict[str, str]] = []
        for block in blocks[-limit:]:
            if not isinstance(block, dict):
                continue
            content = block.get("content", {})
            reward = ""
            if isinstance(content, dict):
                reward = str(content.get("reward", "") or "").strip()
            previews.append(
                {
                    "block_id": str(block.get("block_id", "") or "").strip(),
                    "title": str(block.get("title", "") or "").strip(),
                    "reward": reward[:160],
                }
            )
        return previews

    def _collect_stage0_review_facts(
        self,
        *,
        bible: dict[str, Any],
        treatment: list[dict[str, Any]],
        review_mode: str,
        prior_treatment: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        status = ensure_plot_roadmap(None, bible, treatment)
        master = bible.get("MasterBible", bible) if isinstance(bible, dict) else {}
        core_identity = (
            (((master.get("ProjectData") or {}).get("CoreIdentity")) or {}) if isinstance(master, dict) else {}
        )
        world_state = (master.get("WorldState") or {}) if isinstance(master, dict) else {}
        key_npcs = (((master.get("AssetLibrary") or {}).get("KeyNPCs")) or []) if isinstance(master, dict) else []
        world_laws = (master.get("WorldLaws") or []) if isinstance(master, dict) else []
        completeness_warnings = list(bible.get("_completeness_warnings") or []) if isinstance(bible, dict) else []

        prior_blocks = prior_treatment if isinstance(prior_treatment, list) else []
        new_blocks = (
            treatment[len(prior_blocks) :] if prior_blocks and len(treatment) >= len(prior_blocks) else treatment
        )

        return {
            "review_mode": review_mode,
            "bible_completeness": {
                "warning_count": len(completeness_warnings),
                "warnings": completeness_warnings[:8],
                "has_core_identity": bool(core_identity),
                "key_npc_count": len(key_npcs) if isinstance(key_npcs, list) else 0,
                "world_law_count": len(world_laws) if isinstance(world_laws, list) else 0,
                "has_current_era": bool(str(world_state.get("CurrentEra", "") or "").strip()),
            },
            "plot_roadmap": {
                "entry_count": len(status.roadmap),
                "source": status.source,
                "ready": status.ready,
                "warnings": status.warnings[:8],
            },
            "continuity_handoff": {
                "window_size": self._STAGE0_REVIEW_WINDOW,
                "prior_tail": self._preview_blocks(prior_blocks, limit=self._STAGE0_REVIEW_WINDOW),
                "candidate_head": self._preview_blocks(
                    new_blocks[: self._STAGE0_REVIEW_WINDOW], limit=self._STAGE0_REVIEW_WINDOW
                ),
                "candidate_tail": self._preview_blocks(new_blocks, limit=self._STAGE0_REVIEW_WINDOW),
                "candidate_new_block_count": len(new_blocks) if isinstance(new_blocks, list) else 0,
            },
        }

    @staticmethod
    def _fallback_stage0_review(facts: dict[str, Any], *, attempt: int, max_attempts: int) -> dict[str, Any]:
        completeness = facts.get("bible_completeness", {}) if isinstance(facts, dict) else {}
        roadmap = facts.get("plot_roadmap", {}) if isinstance(facts, dict) else {}
        blocking_issues: list[str] = []
        warning_count = int(completeness.get("warning_count", 0) or 0)

        if not bool(roadmap.get("ready")):
            blocking_issues.extend(list(roadmap.get("warnings") or []))
        if warning_count >= 2:
            blocking_issues.extend(list(completeness.get("warnings") or [])[:4])

        if not blocking_issues:
            return {
                "decision": "PASS",
                "reason": "Deterministic Stage 0 facts stayed above the bounded floor.",
                "operator_message": "Fallback gate passed with deterministic evidence only.",
                "issues": [],
            }

        decision = "RETRY" if attempt < max_attempts else "REJECT"
        return {
            "decision": decision,
            "reason": "Deterministic Stage 0 facts remained below the bounded floor.",
            "operator_message": "Fallback gate escalated Stage 0 because the LLM review was unavailable.",
            "issues": blocking_issues[:8],
        }

    def review_stage0_candidate(
        self,
        *,
        bible: dict[str, Any],
        treatment: list[dict[str, Any]],
        review_mode: str,
        attempt: int,
        max_attempts: int,
        prior_treatment: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        facts = self._collect_stage0_review_facts(
            bible=bible,
            treatment=treatment,
            review_mode=review_mode,
            prior_treatment=prior_treatment,
        )

        prompt = f"""Review this Stage 0 candidate for save/handoff.
Python only collected deterministic facts. Judge only from those facts.

Decision rules:
- PASS: safe to save and hand off to the next stage.
- RETRY: recoverable by regenerating the candidate.
- REJECT: do not save or hand off this candidate.
- Prefer RETRY over REJECT unless this is the final bounded attempt or the structure is clearly unusable.

Current attempt: {attempt} / {max_attempts}

Facts:
{json.dumps(facts, ensure_ascii=False, indent=2)}

Return JSON:
{{
  "decision": "PASS|RETRY|REJECT",
  "reason": "short reason",
  "operator_message": "one-line message for the operator",
  "issues": ["issue 1", "issue 2"]
}}
"""
        raw = self._call_llm(prompt, temperature=0.1, max_tokens=1200)
        parsed = self._parse_json(raw)
        if not isinstance(parsed, dict):
            return self._fallback_stage0_review(facts, attempt=attempt, max_attempts=max_attempts)

        decision = str(parsed.get("decision", "") or "").upper()
        if decision not in {"PASS", "RETRY", "REJECT"}:
            return self._fallback_stage0_review(facts, attempt=attempt, max_attempts=max_attempts)
        parsed["decision"] = decision
        parsed["issues"] = [str(issue).strip() for issue in (parsed.get("issues") or []) if str(issue).strip()]
        parsed.setdefault("reason", "")
        parsed.setdefault("operator_message", parsed.get("reason", ""))
        return parsed

    # ============================================
    # Phase 1: 컨셉 분석
    # ============================================

    def analyze_concept(self, concept: str) -> dict[str, Any]:
        """컨셉 분석 및 핵심 요소 추출"""
        self.concept = concept

        prompt = f"""다음 스토리 컨셉을 분석해서 핵심 요소를 추출하세요.

## 컨셉
{concept}

## 출력 (JSON)
```json
{{
  "title_suggestions": ["제목1", "제목2", "제목3"],
  "protagonist": {{
    "background": "배경",
    "unique_edge": "강점/치트키",
    "main_goal": "최종 목표",
    "starting_condition": "시작 상태"
  }},
  "timeline": {{
    "start_era": "시작 시점",
    "story_span": "스토리 기간"
  }},
  "suggested_genre": "{"/".join(GenreTypes.all())}",
  "themes": ["테마1", "테마2"],
  "tone": "작품 톤",
  "world_laws": ["이 세계의 절대 법칙1", "절대 법칙2"]
}}
```
"""
        parsed = self._parse_json(self._call_llm(prompt))
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}
        self.extracted = parsed if isinstance(parsed, dict) else {}

        # 장르 설정
        if not self.genre:
            self.genre = self.extracted.get("suggested_genre", "investment")

        # 프리셋 초기화
        self.preset_registry = PresetRegistry(base_genre=self.genre)

        return self.extracted

    # ============================================
    # Phase 2: Bible 생성
    # ============================================

    def generate_bible(self, protagonist_config: dict[str, Any] = None) -> dict[str, Any]:
        """Bible 생성"""
        self.bible = {}
        if not self.extracted:  # [P1-A3-6] extracted None/빈값 방어
            self.extracted = {}
        proto = self.extracted.get("protagonist", {})

        # 주인공 상세 생성
        protagonist = self._generate_protagonist_detail()

        # [TF-S01-04] protagonist 빈값 검증 게이트
        if not protagonist or not isinstance(protagonist, dict) or "name" not in protagonist:
            message = "protagonist generation failed"
            logging.error("[StoryExpander] LLM 실패: %s", message)
            raise StoryExpanderBibleGenerationError(message)

        # NPC 생성
        npcs = self._generate_npcs()

        # [TF-S01-04] NPC 빈값 방어
        if not npcs:
            logging.warning("[StoryExpander] NPC 생성 실패 — 빈 목록으로 진행")
            npcs = []

        # 초기 HUD
        hud_input = {
            "name": protagonist.get("name", "주인공"),
            "age": protagonist.get("age", 25),
            **(protagonist_config or {}),
            **proto,
        }
        hud = self.preset_registry.build_initial_hud(hud_input)

        self.bible = {
            "_schema_version": "2.0",
            "_genre": self.genre,
            "_source": "story_expander",
            "_generated_at": datetime.now().isoformat(),
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {
                        "title": (self.extracted.get("title_suggestions") or ["무제"])[0],  # [V70] 빈 리스트 방어
                        "grand_objective": proto.get("main_goal", ""),
                        "logline": f"{proto.get('background', '')} - {proto.get('main_goal', '')}",
                    },
                    "CoreIdentity": protagonist.get("core", {}),
                },
                "protagonist_config": protagonist_config or {},
                "InitialHUD": hud,
                "WorldLaws": self.extracted.get("world_laws", []),
                "WorldState": {
                    "CurrentEra": self.extracted.get("timeline", {}).get("start_era", ""),
                },
                "AssetLibrary": {
                    "KeyNPCs": npcs,
                },
            },
        }

        master_bible = self.bible.get("MasterBible", {})
        project_data = master_bible.get("ProjectData", {}) if isinstance(master_bible, dict) else {}
        core_identity = project_data.get("CoreIdentity", {}) if isinstance(project_data, dict) else {}
        if not isinstance(core_identity, dict) or not core_identity:
            self.bible = {}
            message = "MasterBible.ProjectData.CoreIdentity missing or empty"
            logging.error("[Stage0:BibleGate] Bible contract failure: %s", message)
            raise StoryExpanderBibleGenerationError(message)

        # [SubstrateGate] Bible bounded completeness check — Python은 fact 수집만
        _cw: list[str] = []
        _mb = self.bible.get("MasterBible", {})
        _ci = _mb.get("ProjectData", {}).get("CoreIdentity", {})
        _npcs = _mb.get("AssetLibrary", {}).get("KeyNPCs", [])
        _wl = _mb.get("WorldLaws", [])
        _persona = protagonist.get("persona", "") if isinstance(protagonist, dict) else ""
        _background = protagonist.get("background", "") if isinstance(protagonist, dict) else ""
        if not _ci:
            _cw.append("protagonist CoreIdentity 빈 dict")
        elif not (_ci.get("persona") or _ci.get("background") or _persona or _background):
            _cw.append("protagonist persona/background 모두 누락")
        if len(_npcs) < 2:
            _cw.append(f"KeyNPCs {len(_npcs)}명 — 최소 2명 권장")
        if not _wl:
            _cw.append("WorldLaws 빈 목록")
        if not _mb.get("WorldState", {}).get("CurrentEra"):
            _cw.append("WorldState.CurrentEra 빈 값")
        if _cw:
            logging.warning("[Stage0:BibleGate] 완전성 경고: %s", "; ".join(_cw))
            self.bible["_completeness_warnings"] = _cw

        return self.bible

    def _generate_protagonist_detail(self) -> dict[str, Any]:
        """주인공 상세"""
        proto = self.extracted.get("protagonist", {})

        prompt = f"""주인공 상세 설정을 생성하세요.

## 기본 정보
{json.dumps(proto, ensure_ascii=False)}

JSON:
```json
{{
  "name": "이름",
  "age": 나이,
  "core": {{"protagonist": "이름", "edge": "강점", "desire": "욕망", "crisis": "위기"}},
  "persona": "성격",
  "speech": {{"tone": "말투"}}
}}
```
"""
        result = self._parse_json(self._call_llm(prompt))
        if isinstance(result, list):
            result = result[0] if result and isinstance(result[0], dict) else None
        return result if isinstance(result, dict) else {}

    def _generate_npcs(self) -> list[dict[str, Any]]:
        """NPC 생성"""
        prompt = f"""다음 컨셉에 맞는 NPC 8명을 생성하세요.

{self._build_story_brief()}

JSON:
```json
[{{"name": "이름", "role": "역할", "desc": "설명"}}]
```
"""
        result = self._parse_json(self._call_llm(prompt))
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []

    # ============================================
    # Phase 3: Treatment 생성
    # ============================================

    def generate_treatment(self, block_count: int = 60) -> list[dict[str, Any]]:
        """Treatment 생성"""
        # 스켈레톤 생성
        skeleton = self._generate_skeleton(block_count)

        # 상세 생성
        self.treatment = self._generate_details(skeleton)

        return self.treatment

    def extend_treatment(
        self,
        existing_treatment: list[dict[str, Any]],
        extend_count: int = 10,
        direction_hint: str = "",
        batch_size: int = 10,
        confirm_callback=None,
    ) -> list[dict[str, Any]]:
        """
        기존 Treatment 확장 (Block 연장)

        Args:
            existing_treatment: 기존 블록 리스트
            extend_count: 추가할 블록 수 (기본 10)
            direction_hint: 방향 힌트 ("클라이맥스로", "새 빌런 등장" 등)
            batch_size: 배치 크기 (기본 10)
            confirm_callback: 배치별 확인 콜백 (batch) -> bool

        Returns:
            확장된 전체 treatment 리스트
        """
        self.treatment = existing_treatment.copy()
        start_block = len(existing_treatment) + 1

        # 최근 5개 블록 컨텍스트
        recent_blocks = existing_treatment[-5:] if len(existing_treatment) >= 5 else existing_treatment
        recent_context = "\n".join(
            [
                f"- Block {b.get('block_id', i + 1)}: {b.get('title') or ''} - {((b.get('content') or {}).get('context') or '')[:100] if isinstance(b.get('content'), dict) else str(b.get('content') or '')[:100]}"  # [V70] content str 방어 + None 가드
                for i, b in enumerate(recent_blocks)
            ]
        )

        extended = []
        remaining = extend_count
        current_block = start_block

        while remaining > 0:
            batch_count = min(batch_size, remaining)

            # 배치 생성
            new_blocks = self._generate_extension_batch(
                start_block=current_block,
                count=batch_count,
                recent_context=recent_context,
                direction_hint=direction_hint,
            )

            if not new_blocks:
                logging.warning(f"[!] Block {current_block}~{current_block + batch_count - 1} 생성 실패")
                break

            # 확인 콜백
            if confirm_callback:
                if not confirm_callback(new_blocks):
                    logging.info("[*] 사용자가 중단함")
                    break

            extended.extend(new_blocks)
            self.treatment.extend(new_blocks)

            # 다음 배치를 위한 컨텍스트 업데이트
            recent_context = "\n".join(
                [
                    f"- Block {b.get('block_id', '')}: {b.get('title') or ''} - {((b.get('content') or {}).get('context') or '')[:100] if isinstance(b.get('content'), dict) else str(b.get('content') or '')[:100]}"  # [V70] content str 방어 + None 가드
                    for b in new_blocks[-5:]
                ]
            )

            current_block += batch_count
            remaining -= batch_count

            logging.info(
                f"[v] Block {current_block - batch_count}~{current_block - 1} 생성 완료 ({len(extended)}/{extend_count})"
            )

        return self.treatment

    def _generate_extension_batch(
        self, start_block: int, count: int, recent_context: str, direction_hint: str
    ) -> list[dict[str, Any]]:
        """확장 배치 생성"""
        hint_section = f"\n## 방향 힌트\n{direction_hint}" if direction_hint else ""

        prompt = f"""기존 스토리를 이어서 Block {start_block}~{start_block + count - 1}을 생성하세요.

## 장르
{self.genre}

## 최근 블록 흐름
{recent_context}
{hint_section}

## 요구사항
- 기존 흐름을 자연스럽게 계승
- 각 블록에 새로운 갈등/해결 요소 포함
- 캐릭터 성장과 스토리 진행을 균형있게

## 출력 (JSON)
```json
[{{
  "block_id": "Block {start_block}",
  "title": "블록 제목",
  "content": {{
    "context": "배경 설명",
    "event_villain": "갈등/적대 요소",
    "solution": "해결 방향",
    "reward": "결과/보상"
  }}
}}]
```

정확히 {count}개 블록을 출력하세요.
"""
        result = self._parse_json(self._call_llm(prompt, max_tokens=12000))

        if not result or not isinstance(result, list):
            return []

        # block_id 정규화
        for i, block in enumerate(result):
            expected_id = f"Block {start_block + i}"
            if block.get("block_id") != expected_id:
                block["block_id"] = expected_id

        return result

    def _generate_skeleton(self, count: int) -> list[dict[str, Any]]:
        """블록 스켈레톤 (20블록 배치)"""
        batch_size = 20
        all_blocks: list[dict[str, Any]] = []
        prev_titles: list[str] = []

        for start in range(1, count + 1, batch_size):
            end = min(start + batch_size - 1, count)
            batch_count = end - start + 1

            continuity = ""
            if prev_titles:
                recent = prev_titles[-5:]
                continuity = "\n## 이전 블록 (연결성 유지)\n" + "\n".join(f"- {t}" for t in recent)

            prompt = f"""웹소설 Block {start}~{end} ({batch_count}개)의 뼈대를 생성하세요.

{self._build_story_brief()}
{continuity}

JSON:
```json
[{{"block_id": "Block {start}", "title": "제목", "summary": "요약"}}]
```

정확히 {batch_count}개 출력.
"""
            result = self._parse_json(self._call_llm(prompt, max_tokens=8192)) or []
            if isinstance(result, dict):
                result = [result]
            if not result:
                logging.warning(f"[StoryExpander] _generate_skeleton: Block {start}~{end} LLM 응답 비어있음")
            all_blocks.extend(result)
            prev_titles.extend(b.get("title", "") for b in result)

        return all_blocks

    def _generate_details(self, skeleton: list[dict]) -> list[dict[str, Any]]:
        """블록 상세"""
        detailed = []
        batch_size = 10

        for i in range(0, len(skeleton), batch_size):
            batch = skeleton[i : i + batch_size]
            skeleton_text = "\n".join(
                [f"- {b.get('block_id', f'block_{i + j}')}: {b.get('title', '제목 없음')}" for j, b in enumerate(batch)]
            )  # [V70] 인덱스 수정 (i는 이미 배치 시작)
            story_brief = self._build_story_brief()

            # [SubstrateGate] cross-batch continuity for details
            _continuity_ctx = ""
            if detailed:
                continuity_lines: list[str] = []
                for prev in detailed[-self._STAGE0_REVIEW_WINDOW :]:
                    if not isinstance(prev, dict):
                        continue
                    prev_id = prev.get("block_id", "?")
                    prev_title = prev.get("title", "?")
                    prev_content = prev.get("content", {})
                    prev_reward = ""
                    if isinstance(prev_content, dict):
                        prev_reward = str(prev_content.get("reward", "") or "").strip()
                    line = f"- {prev_id}: {prev_title}"
                    if prev_reward:
                        line += f" | result: {prev_reward[:100]}"
                    continuity_lines.append(line)
                if continuity_lines:
                    _continuity_ctx = "\n## Recent accepted blocks (continuity carry-over)\n" + "\n".join(
                        continuity_lines
                    )

            prompt = f"""블록 상세:

{story_brief}
{_continuity_ctx}

{skeleton_text}

JSON:
```json
[{{
  "block_id": "Block N",
  "title": "제목",
  "content": {{
    "context": "배경",
    "event_villain": "갈등",
    "solution": "해결",
    "reward": "결과"
  }}
}}]
```
"""
            result = self._parse_json(self._call_llm(prompt)) or []
            # [G24] dict 반환 시 list로 래핑 (extend는 iterable of items 기대)
            if isinstance(result, dict):
                result = [result]
            detailed.extend(result if result else batch)

        return detailed

    # ============================================
    # 저장
    # ============================================

    def save_all(self, output_dir: str):
        """저장"""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        with open(out / "bible.json", "w", encoding="utf-8") as f:
            json.dump(self.bible, f, ensure_ascii=False, indent=2)

        treatment_out = {"_genre": self.genre, "total_blocks": len(self.treatment), "treatments": self.treatment}
        with open(out / "treatment.json", "w", encoding="utf-8") as f:
            json.dump(treatment_out, f, ensure_ascii=False, indent=2)

        if self.preset_registry:
            with open(out / "preset_state.json", "w", encoding="utf-8") as f:
                f.write(self.preset_registry.to_json())

    # ============================================
    # 통합 실행
    # ============================================

    def run(self, concept: str, output_dir: str, protagonist_config: dict = None) -> tuple[dict, list]:
        """전체 파이프라인"""
        if SPINNER_AVAILABLE:
            print_header("Story Expander", style="double")
            phases = ["컨셉 분석", "Bible 생성", "Treatment 생성", "저장"]
            indicator = PhaseIndicator(phases)
            indicator.show()

            # Phase 1: 컨셉 분석
            with Spinner("컨셉 분석 중", style="braille"):
                self.analyze_concept(concept)
            print_success(f"컨셉 분석 완료 (장르: {self.genre})")
            indicator.next()
            indicator.show()

            # Phase 2: Bible 생성
            with Spinner("Bible 생성 중", style="dots"):
                try:
                    self.generate_bible(protagonist_config)
                except StoryExpanderBibleGenerationError as exc:
                    logging.warning("[StoryExpander] generate_bible() 실패: %s", exc)
                    self.treatment = []
                    return {}, []
            if not self.bible:
                logging.warning("[StoryExpander] generate_bible() 결과가 비어있음 — 조기 반환")
                return self.bible, self.treatment
            print_success("Bible 생성 완료")
            indicator.next()
            indicator.show()

            # Phase 3: Treatment 생성
            with Spinner("Treatment 생성 중 (60 블록)", style="grow"):
                self.generate_treatment()
            print_success(f"Treatment 생성 완료 ({len(self.treatment)} 블록)")
            indicator.next()
            indicator.show()

            # Phase 4: 저장
            with Spinner("저장 중", style="pulse"):
                self.save_all(output_dir)
            print_success(f"저장 완료: {output_dir}")
            indicator.complete()
            indicator.show()

            print_header("완료!", style="simple")
        else:
            # 스피너 없는 폴백
            logging.info("[*] 컨셉 분석...")
            self.analyze_concept(concept)

            logging.info("[*] Bible 생성...")
            try:
                self.generate_bible(protagonist_config)
            except StoryExpanderBibleGenerationError as exc:
                logging.warning("[StoryExpander] generate_bible() 실패: %s", exc)
                self.treatment = []
                return {}, []
            if not self.bible:
                logging.warning("[StoryExpander] generate_bible() 결과가 비어있음 — 조기 반환")
                return self.bible, self.treatment

            logging.info("[*] Treatment 생성...")
            self.generate_treatment()

            logging.info("[*] 저장...")
            self.save_all(output_dir)

            logging.info("[v] 완료!")

        return self.bible, self.treatment
