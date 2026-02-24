"""
[V64 P2-1] Director ContinuityValidator — 연속성 검증 전담 모듈

Director God Object 분해의 네 번째 단계.
Entity 일관성, 원고 역사 충돌 검사, Blueprint/Manuscript 연속성 검증 담당.
"""

import json
import logging

from modules.core.constants import ContextLimits, smart_truncate
from modules.core.prompt_loader import PromptLoader


class DirectorContinuityValidator:
    """
    [V64 P2-1] Director에서 분리된 연속성 검증 모듈

    담당:
    - validate_entity_consistency(): Entity 명칭 일관성 LLM 검증
    - _format_entity_registry_for_director(): Entity Registry 포맷 변환
    - _validate_blueprint_completeness_v60(): Blueprint 완전성 검증 (Python)
    - check_manuscript_history_conflicts(): 원고 역사 충돌 검사 (LLM)
    - check_manuscript_history_with_cache(): 캐시 기반 원고 충돌 검사 (LLM)
    - check_blueprint_continuity_with_cache(): Blueprint 연속성 검증 (Python + 캐싱)
    - check_manuscript_continuity_with_cache(): Manuscript 연속성 검증 (LLM + 캐싱)
    """

    def __init__(self, director) -> None:
        """
        Args:
            director: Director 인스턴스 (BaseAgent 메서드 접근용)
        """
        self._d = director
        self._prompt_loader = PromptLoader()

        # [V61.5] 캐시 연속성 검사 — ep_num 기반 갱신
        self._cached_blueprint_ep = None
        self._cached_manuscript_ep = None
        # DI 후보: _cached_recent_blueprints (getattr fallback, L602)
        # DI 후보: _cached_context_text_manuscript (getattr fallback, L715)
        # DI 후보: _manuscript_cache_name (getattr fallback, L716)

    def validate_entity_consistency(
        self, content: str, entity_registry: dict, content_type: str = "manuscript"
    ) -> dict:
        """
        [V61] Entity 명칭 일관성 검증 - Director의 최종 방어선

        Args:
            content: 검증 대상 텍스트 (원고, 블루프린트, Arc 전술서 등)
            entity_registry: Entity Registry dict {characters:[], organizations:[], locations:[], objects:[], concepts:[]}
            content_type: "manuscript", "blueprint", "arc" 중 하나

        Returns:
            {
                "decision": "PASS" | "WARNING" | "REJECT",
                "mismatches": [...],
                "fix_instructions": "수정 지시"
            }
        """
        if not self._d.entity_consistency_enabled:
            return {"decision": "PASS", "mismatches": [], "fix_instructions": ""}

        if not entity_registry or not content:
            return {"decision": "PASS", "mismatches": [], "fix_instructions": ""}

        # Entity Registry 포맷팅
        registry_str = self._format_entity_registry_for_director(entity_registry)
        if registry_str == "(등록된 Entity 없음)":
            return {"decision": "PASS", "mismatches": [], "fix_instructions": ""}

        # LLM 기반 검증 프롬프트
        prompt = f"""[Role] Entity 명칭 일관성 최종 검증관 (Director's Final Defense)
[Task] 주어진 {content_type}에서 Entity Registry에 등록된 명칭과 다른 표기가 사용되었는지 검사하라.

### Entity Registry (정식 명칭 목록)
{self._d._escape_braces(registry_str)}

### 검증 대상 ({content_type})
{self._d._escape_braces(content[:5000])}

### 검증 기준
⚠️ 중요: 이름이 비슷해도 **다른 인물**이면 불일치가 아니다! (예: '김성태'와 '김태민'은 성만 같은 별개 인물)
   Registry에 등록된 모든 인물을 먼저 파악하고, role이 "주인공"인 인물은 절대 다른 NPC와 혼동하지 마라.

1. **캐릭터명**: 등록된 이름 외의 다른 표기 사용 시 WARNING
   - 예: '팽무진'이 등록되었는데 '무진', '주인공'으로 표기
   - 별칭(aliases)은 허용
   - ❌ 절대 금지: 성이 같다는 이유로 다른 인물을 동일인으로 판단
2. **조직/문파명**: 등록된 명칭과 다른 표기 사용 시 WARNING
   - 예: '철혈문'이 등록되었는데 '철혈파'로 표기
3. **장소명**: 동일 장소가 다른 명칭으로 표기 시 MINOR
4. **물품명**: 등록된 무기/아이템이 다른 이름으로 표기 시 MAJOR
   - 예: '백근도'가 등록되었는데 '거구도'로 표기
5. **기술/무공명**: 등록된 기술이 다른 이름으로 표기 시 MAJOR
   - 예: '이화접목'이 등록되었는데 '중검무봉'으로 표기

### 판정 기준
- REJECT: CRITICAL 1개 이상 또는 MAJOR 3개 이상
- WARNING: MAJOR 1-2개 또는 MINOR 다수
- PASS: 문제 없음 또는 MINOR 소수

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "WARNING" 또는 "REJECT",
    "mismatches": [
        {{
            "category": "character | organization | location | object | concept",
            "registered_name": "등록된 정식 명칭",
            "found_variant": "발견된 변형 명칭",
            "severity": "CRITICAL | MAJOR | MINOR",
            "context": "발견된 문맥 일부 (50자 이내)"
        }}
    ],
    "fix_instructions": "수정 지시 (REJECT/WARNING 시 필수)"
}}"""

        try:
            response = self._d.ask(prompt, temperature=0.1, thinking_level="low")
            result = self._d._extract_json_robust(response)

            if not isinstance(result, dict) or result.get("parsing_error"):
                return {"decision": "PASS", "mismatches": [], "fix_instructions": "", "parsing_error": True}

            # 결과 로깅
            mismatches = result.get("mismatches", [])
            if mismatches:
                decision = result.get("decision", "WARNING")
                logging.warning(f"⚠️ [V61] Entity 일관성 검증: {decision} ({len(mismatches)}개 불일치)")
                for m in mismatches[:3]:
                    logging.info(
                        f"- [{m.get('category', '?')}] {m.get('registered_name', '?')} → {m.get('found_variant', '?')}"
                    )

            return result

        except Exception as e:
            logging.warning(f"⚠️ [C-3] Entity 일관성 검증 실패 (UNKNOWN 반환): {e}")
            return {"decision": "UNKNOWN", "mismatches": [], "fix_instructions": "", "error": str(e)}

    def _format_entity_registry_for_director(self, entity_registry: dict) -> str:
        """[V61] Entity Registry를 Director용 포맷으로 변환"""
        if not entity_registry:
            return "(등록된 Entity 없음)"

        lines = []
        categories = [
            ("characters", "캐릭터"),
            ("organizations", "조직/문파"),
            ("locations", "장소"),
            ("objects", "물품/아이템"),
            ("concepts", "기술/개념"),
        ]

        has_any = False
        for key, label in categories:
            items = entity_registry.get(key, [])
            if items:
                has_any = True
                formatted_items = []
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("canonical_name", str(item)))
                        aliases = item.get("aliases", [])
                        if aliases:
                            formatted_items.append(f"{name} (별칭: {', '.join(aliases)})")
                        else:
                            formatted_items.append(name)
                    else:
                        formatted_items.append(str(item))
                lines.append(f"[{label}] {', '.join(formatted_items)}")

        if not has_any:
            return "(등록된 Entity 없음)"

        return "\n".join(lines)

    def _validate_blueprint_completeness_v60(self, manuscript: str, blueprint: dict) -> dict:
        """
        [V60] Blueprint 완전성 검증 - 원고가 설계 씬을 충분히 반영했는지 확인

        Args:
            manuscript: 검증 대상 원고
            blueprint: Blueprint 데이터

        Returns:
            {
                "valid": bool,
                "scene_coverage": float (0-100%),
                "expected_scenes": int,
                "reflected_scenes": int,
                "missing_scenes": list,
                "warnings": list,
                "reason": str,
                "feedback": str,
                "score": int
            }
        """
        import re

        if not blueprint or not isinstance(blueprint, dict):
            return {
                "valid": True,
                "scene_coverage": 100,
                "expected_scenes": 0,
                "reflected_scenes": 0,
                "missing_scenes": [],
                "warnings": [],
                "reason": "",
                "feedback": "",
                "score": 100,
            }

        warnings = []
        missing_scenes = []

        # 1. Blueprint에서 씬 정보 추출
        scene_breakdown = blueprint.get("scene_breakdown", {})
        integrated_scenario = blueprint.get("integrated_scenario", "")

        # scene_breakdown이 dict인 경우 씬 개수 계산
        if isinstance(scene_breakdown, dict):
            scene_keys = [k for k in scene_breakdown.keys() if k.startswith("scene") or k.startswith("Scene")]
            expected_scenes = len(scene_keys)

            # 각 씬의 핵심 키워드 추출
            scene_keywords = {}
            for scene_key in scene_keys:
                scene_content = scene_breakdown.get(scene_key, "")
                if isinstance(scene_content, str):
                    # 씬 타입 추출 ([Core], [Buffer], [Cliffhanger] 등)
                    type_match = re.search(r"\[(Core|Buffer|Cliffhanger|Climax)\]", scene_content, re.IGNORECASE)
                    scene_type = type_match.group(1) if type_match else "Unknown"

                    # 핵심 키워드 추출 (명사/동사 중심)
                    keywords = re.findall(r"[가-힣]{2,5}(?:하다|되다|이다)?", scene_content)
                    # 상위 5개 키워드만 사용
                    scene_keywords[scene_key] = {
                        "type": scene_type,
                        "keywords": keywords[:5] if keywords else [],
                        "content_sample": scene_content[:100],
                    }
        elif isinstance(scene_breakdown, list):
            expected_scenes = len(scene_breakdown)
            scene_keywords = {
                f"scene_{i + 1}": {"type": "Unknown", "keywords": [], "content_sample": str(item)[:100]}
                for i, item in enumerate(scene_breakdown)
            }
        else:
            # scene_breakdown이 없으면 integrated_scenario에서 추정
            scene_markers = re.findall(
                r"\[(?:Core|Buffer|Cliffhanger|Scene)\s*\d*\]", integrated_scenario, re.IGNORECASE
            )
            expected_scenes = len(scene_markers) if scene_markers else 6  # 기본 6개
            scene_keywords = {}

        if expected_scenes == 0:
            expected_scenes = 6  # 기본값

        # 2. 원고에서 씬 반영 여부 확인
        reflected_count = 0

        for scene_key, scene_info in scene_keywords.items():
            keywords = scene_info.get("keywords", [])
            scene_type = scene_info.get("type", "Unknown")

            # 키워드 매칭
            matched_keywords = 0
            for keyword in keywords:
                if keyword in manuscript:
                    matched_keywords += 1

            # 키워드의 50% 이상 매칭되면 반영된 것으로 판단
            if len(keywords) == 0 or matched_keywords >= len(keywords) * 0.5:
                reflected_count += 1
            else:
                missing_scenes.append(
                    {
                        "scene": scene_key,
                        "type": scene_type,
                        "missing_keywords": [k for k in keywords if k not in manuscript][:3],
                        "sample": scene_info.get("content_sample", "")[:50],
                    }
                )

        # 키워드가 없는 경우 길이 기반 추정
        if not scene_keywords:
            # 원고 길이 기반으로 씬 반영 추정
            min_chars_per_scene = 600  # 씬당 최소 600자
            estimated_scenes = len(manuscript) // min_chars_per_scene
            reflected_count = min(estimated_scenes, expected_scenes)

        # 3. 커버리지 계산
        scene_coverage = (reflected_count / expected_scenes * 100) if expected_scenes > 0 else 100

        # 4. 판정 [V60.24] 기준 완화
        MIN_COVERAGE = 65  # [V60.24] 최소 65% 반영 필요 (70→65)

        if scene_coverage < MIN_COVERAGE:
            return {
                "valid": False,
                "scene_coverage": round(scene_coverage, 1),
                "expected_scenes": expected_scenes,
                "reflected_scenes": reflected_count,
                "missing_scenes": missing_scenes,
                "warnings": warnings,
                "reason": f"Blueprint 반영률 부족: {reflected_count}/{expected_scenes} 씬 ({scene_coverage:.1f}%)",
                "feedback": f"설계된 {expected_scenes}개 씬 중 {reflected_count}개만 반영됨. 누락된 씬을 추가하세요: {[m['scene'] for m in missing_scenes[:3]]}",
                "score": int(scene_coverage * 0.5),
            }

        # [V60.24] 75% 미만이면 경고 (80→75)
        if scene_coverage < 75:
            warnings.append(f"씬 반영률 {scene_coverage:.1f}% (권장: 75% 이상)")

        # Cliffhanger 씬 검증
        has_cliffhanger = any(
            "cliffhanger" in str(scene_info.get("type", "")).lower() for scene_info in scene_keywords.values()
        )
        if has_cliffhanger:
            # 원고 마지막 500자에서 긴장감 키워드 확인
            ending = manuscript[-500:] if len(manuscript) >= 500 else manuscript
            tension_keywords = ["그때", "순간", "갑자기", "돌연", "하지만", "그러나", "예상치 못한", "충격", "긴장"]
            has_tension = any(kw in ending for kw in tension_keywords)
            if not has_tension:
                warnings.append("Cliffhanger 엔딩 긴장감 부족 - 마지막 장면에 서스펜스 요소 추가 권장")

        return {
            "valid": True,
            "scene_coverage": round(scene_coverage, 1),
            "expected_scenes": expected_scenes,
            "reflected_scenes": reflected_count,
            "missing_scenes": missing_scenes,
            "warnings": warnings,
            "reason": "",
            "feedback": "",
            "score": 100 - len(warnings) * 5,
        }

    def check_manuscript_history_conflicts(
        self,
        ep_num: int,
        current_manuscript: str,
        manuscript_history: list,
        use_summary: bool = True,
        story_context: str = "",
        memory_context: str = "",
    ) -> dict:
        """
        [V67.1] 현재 원고가 이전 원고들과 충돌하는지 검사 (story_context 추가)

        Args:
            ep_num: 현재 회차 번호
            current_manuscript: 현재 원고 전문
            manuscript_history: 이전 원고 리스트 [{"ep_num": 1, "text": "...", "summary": "..."}, ...]
            use_summary: True면 요약본 사용, False면 전문 사용 (토큰 절약)

        Returns:
            {
                "decision": "PASS" | "CONFLICT",
                "conflicts": [...],
                "summary": "..."
            }
        """
        if not self._d.manuscript_history_check_enabled:
            return {"decision": "PASS", "conflicts": [], "summary": "충돌 검사 비활성화"}

        if not manuscript_history:
            return {"decision": "PASS", "conflicts": [], "summary": "이전 원고 없음"}

        # [V67] 설정 기반 참조 화수 사용
        recent_history = manuscript_history[-self._d.history_check_max_episodes :]

        # [V67] 역사 텍스트 구성 — 전문 사용 (요약 대신)
        history_parts = []
        for h in recent_history:
            h_ep = h.get("ep_num", "?")
            if use_summary:
                h_text = h.get("summary", "") or h.get("text", "")[:500]
            else:
                h_text = h.get("text", "") or h.get("summary", "")
            if h_text:
                history_parts.append(f"[제{h_ep}화]\n{h_text}")

        history_text = "\n\n---\n\n".join(history_parts)

        history_text = smart_truncate(history_text)

        # [V67.1] 프롬프트 구성 (story_context 추가)
        prompt = self._prompt_loader.load(
            "director",
            "MANUSCRIPT_HISTORY_CONFLICT_PROMPT",
            ep_num=ep_num,
            manuscript_history=self._d._escape_braces(history_text),
            current_manuscript=self._d._escape_braces(current_manuscript),
            story_context=self._d._escape_braces(story_context) if story_context else "(작품 설정 정보 없음)",
        )
        if prompt and memory_context:
            prompt += f"\n\n### 🔍 [SC-5] 벡터 메모리 참고 — 과거 에피소드 관련 컨텍스트\n{memory_context}"
        if not prompt:
            return {
                "decision": "REJECT",
                "conflicts": [{"severity": "CRITICAL", "description": "프롬프트 로드 실패 — fail-closed"}],
                "summary": "Prompt loading failed: MANUSCRIPT_HISTORY_CONFLICT_PROMPT",
                "prompt_error": True,
            }

        try:
            response = self._d.ask(prompt, temperature=0.1, thinking_level="medium")
            result = self._d._extract_json_robust(response)

            if not result or result.get("parsing_error"):
                return {
                    "decision": "REJECT",
                    "conflicts": [{"severity": "CRITICAL", "description": "응답 파싱 실패 — fail-closed"}],
                    "summary": "충돌 검사 응답 파싱 실패 — fail-closed",
                    "parsing_error": True,
                }

            decision = result.get("decision", "PASS")
            conflicts = result.get("conflicts", [])

            # CRITICAL 충돌이 있으면 CONFLICT, 아니면 경고만
            critical_count = sum(1 for c in conflicts if isinstance(c, dict) and c.get("severity") == "CRITICAL")

            if decision == "CONFLICT" and critical_count > 0:
                return {
                    "decision": "CONFLICT",
                    "conflicts": conflicts,
                    "summary": result.get("summary", ""),
                    "critical_count": critical_count,
                }
            else:
                # MAJOR/MINOR는 경고만 (비차단)
                return {
                    "decision": "PASS",
                    "conflicts": conflicts,
                    "summary": result.get("summary", ""),
                    "warnings_only": True,
                }

        except Exception as e:
            logging.warning("[P0-2] check_manuscript_history_conflicts 예외 — fail-closed: %s", e)
            return {
                "decision": "REJECT",
                "conflicts": [{"severity": "CRITICAL", "description": "충돌 검사 예외 — fail-closed"}],
                "summary": f"충돌 검사 중 오류 발생 — fail-closed: {str(e)[:100]}",
                "error": str(e),
            }

    def check_manuscript_history_with_cache(self, ep_num: int, current_manuscript: str) -> dict:
        """
        [V60.88] 캐시된 원고를 활용한 충돌 검사

        캐시가 있으면 캐시 참조로 LLM 호출 (토큰 비용 절감),
        캐시가 없으면 기존 방식 (축약된 역사 사용).

        Args:
            ep_num: 현재 회차 번호
            current_manuscript: 현재 원고 전문

        Returns:
            충돌 검사 결과 dict
        """
        if not self._d.manuscript_history_check_enabled:
            return {"decision": "PASS", "conflicts": [], "summary": "충돌 검사 비활성화"}

        if not self._d._caching.manuscript_cache_name:
            return {"decision": "PASS", "conflicts": [], "summary": "캐시 미생성 - 스킵"}

        try:
            from google.genai import types

            prompt = f"""[V60.88 원고 충돌 검사]

### 📋 검사 대상: 제{ep_num}화 신규 원고

### 현재 원고 (제{ep_num}화)
{self._d._escape_braces(current_manuscript[:12000])}

### 🔍 검사 지시
위 신규 원고가 캐시에 저장된 이전 원고들 (제1화~제{ep_num - 1}화)과 충돌하는지 검사하세요.

[Output Format] JSON Only
{{
    "decision": "PASS" 또는 "CONFLICT",
    "conflicts": [
        {{
            "type": "death|item|relationship|timeline|geography",
            "severity": "CRITICAL|MAJOR|MINOR",
            "description": "충돌 설명",
            "evidence_ep": 충돌하는 이전 회차 번호,
            "evidence_text": "이전 원고의 관련 문장"
        }}
    ],
    "summary": "검사 결과 요약"
}}
"""

            response = self._d.client.models.generate_content(
                model=self._d.primary_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    cached_content=self._d._caching.manuscript_cache_name,
                    temperature=0.1,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                ),
            )

            # [V70] response.text가 ValueError 발생 가능 (safety filter, 빈 응답)
            try:
                _resp_text = response.text
            except (ValueError, AttributeError):
                _resp_text = None
            if not _resp_text:
                return {
                    "decision": "REJECT",
                    "conflicts": [{"severity": "CRITICAL", "description": "캐시 검사 응답 비어있음 — fail-closed"}],
                    "summary": "캐시 검사 응답 비어있음 — fail-closed",
                    "parsing_error": True,
                }

            result = self._d._extract_json_robust(_resp_text)

            if not result or result.get("parsing_error"):
                return {
                    "decision": "REJECT",
                    "conflicts": [{"severity": "CRITICAL", "description": "캐시 검사 응답 파싱 실패 — fail-closed"}],
                    "summary": "캐시 검사 응답 파싱 실패 — fail-closed",
                    "parsing_error": True,
                }

            decision = result.get("decision", "PASS")
            conflicts = result.get("conflicts", [])
            critical_count = sum(1 for c in conflicts if isinstance(c, dict) and c.get("severity") == "CRITICAL")

            if decision == "CONFLICT" and critical_count > 0:
                return {
                    "decision": "CONFLICT",
                    "conflicts": conflicts,
                    "summary": result.get("summary", ""),
                    "critical_count": critical_count,
                    "cache_used": True,
                }
            else:
                return {
                    "decision": "PASS",
                    "conflicts": conflicts,
                    "summary": result.get("summary", ""),
                    "warnings_only": True,
                    "cache_used": True,
                }

        except Exception as e:
            # [V63.4 P0] 캐시 실패 시 폴백 트리거 보장
            logging.warning(f"⚠️ [V60.88] 캐시 검사 오류 → 폴백 경로 전환: {e}")
            return {
                "decision": "SKIP",
                "conflicts": [],
                "summary": f"캐시 검사 실패 → 기존 방식 폴백 필요: {str(e)}",
                "error": str(e),
                "needs_fallback": True,
            }

    def check_blueprint_continuity_with_cache(self, new_blueprint: dict, ep_num: int, db=None, limit: int = 30) -> dict:
        """
        [V61.5] 이전 Blueprint 컨텍스트 캐싱 기반 연속성 검증

        최근 N화의 Blueprint를 캐싱하고, 새 Blueprint와의 연속성을 검증한다.
        위치, 시점, 상태 불일치를 감지한다.

        Args:
            new_blueprint: 새로 생성된 Blueprint
            ep_num: 현재 에피소드 번호
            db: DBManager 인스턴스
            limit: 최근 몇 화까지 참조할지

        Returns:
            {
                "decision": "PASS" | "WARNING" | "REJECT",
                "issues": [...],
                "feedback": str
            }
        """
        if not db or ep_num <= 1:
            return {"decision": "PASS", "issues": [], "feedback": ""}

        try:
            project_name = getattr(self._d.context, "project_name", "") if hasattr(self._d, "context") else ""

            if self._cached_blueprint_ep != ep_num:
                recent_blueprints = db.get_recent_blueprints(ep_num, limit=limit)
                if not recent_blueprints:
                    return {"decision": "PASS", "issues": [], "feedback": "이전 Blueprint 없음"}

                context_text = self._d.merge_contexts_for_caching(recent_blueprints, item_type="blueprint")
                cache_result = self._d._get_or_create_context_cache(
                    cache_type="blueprint", content=context_text, ttl_seconds=1800, project_name=project_name
                )
                self._cached_blueprint_ep = ep_num
                self._cached_recent_blueprints = recent_blueprints
                logging.info(f"📦 [V61.5] Blueprint 캐시 갱신 (ep={ep_num})")
            else:
                recent_blueprints = getattr(self, "_cached_recent_blueprints", [])
                cache_result = {"cached": True}
                logging.info(f"♻️ [V61.5] Blueprint 캐시 재사용 (ep={ep_num})")

            # 직전 Blueprint 정보 추출
            prev_bp = recent_blueprints[-1] if recent_blueprints else {}
            prev_data = prev_bp.get("data", {})
            if isinstance(prev_data, str):
                try:
                    prev_data = json.loads(prev_data)
                except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] JSON parse with safe default
                    prev_data = {}

            prev_end_location = prev_data.get("end_location", "")

            # 새 Blueprint 정보 추출
            new_start_location = new_blueprint.get("start_location", "")

            # Python 기반 빠른 체크 (LLM 호출 없이)
            issues = []

            # 위치 불연속 체크
            if prev_end_location and new_start_location:
                if prev_end_location not in new_start_location and new_start_location not in prev_end_location:
                    issues.append(
                        {
                            "type": "location_discontinuity",
                            "severity": "MAJOR",
                            "message": f"위치 불연속: 이전 종료 '{prev_end_location}' → 현재 시작 '{new_start_location}'",
                            "prev_value": prev_end_location,
                            "new_value": new_start_location,
                        }
                    )

            # 결정 로직
            major_count = sum(1 for i in issues if i.get("severity") == "MAJOR")
            critical_count = sum(1 for i in issues if i.get("severity") == "CRITICAL")

            if critical_count > 0:
                decision = "REJECT"
            elif major_count >= 1:
                decision = "WARNING"
            else:
                decision = "PASS"

            feedback = ""
            if issues:
                feedback = "[V61.5 연속성 검증]\n"
                for issue in issues[:3]:
                    feedback += f"- [{issue['severity']}] {issue['message']}\n"

            return {
                "decision": decision,
                "issues": issues,
                "feedback": feedback,
                "cache_used": cache_result.get("cached", False),
            }

        except Exception as e:
            logging.warning(f"⚠️ [C-3] Blueprint 연속성 검증 오류 (UNKNOWN 반환): {str(e)[:50]}")
            return {"decision": "UNKNOWN", "issues": [], "feedback": "", "error": str(e)}

    def check_manuscript_continuity_with_cache(
        self,
        new_manuscript: str,
        ep_num: int,
        db=None,
        limit: int = 30,
        story_context: str = "",
        memory_context: str = "",
    ) -> dict:
        """
        [V61.5] 이전 Manuscript 컨텍스트 캐싱 기반 연속성 검증

        최근 N화의 원고를 캐싱하고, 새 원고와의 충돌을 LLM으로 검증한다.
        기존 check_manuscript_history_conflicts와 유사하지만 캐싱을 활용한다.

        Args:
            new_manuscript: 새로 생성된 원고 텍스트
            ep_num: 현재 에피소드 번호
            db: DBManager 인스턴스
            limit: 최근 몇 화까지 참조할지

        Returns:
            {
                "decision": "PASS" | "CONFLICT",
                "conflicts": [...],
                "summary": str
            }
        """
        if not db or ep_num <= 1:
            return {"decision": "PASS", "conflicts": [], "summary": ""}

        try:
            project_name = getattr(self._d.context, "project_name", "") if hasattr(self._d, "context") else ""

            if self._cached_manuscript_ep != ep_num:
                recent_manuscripts = db.get_recent_manuscripts(ep_num, limit=limit)
                if not recent_manuscripts:
                    return {"decision": "PASS", "conflicts": [], "summary": "이전 원고 없음"}

                context_text = self._d.merge_contexts_for_caching(recent_manuscripts, item_type="manuscript")
                cache_result = self._d._get_or_create_context_cache(
                    cache_type="manuscript", content=context_text, ttl_seconds=1800, project_name=project_name
                )
                self._cached_manuscript_ep = ep_num
                self._cached_context_text_manuscript = context_text
                self._manuscript_cache_name = cache_result.get("cache_name")
                logging.info(f"📦 [V61.5] Manuscript 캐시 갱신 (ep={ep_num})")
            else:
                context_text = getattr(self, "_cached_context_text_manuscript", "")
                cache_result = {"cached": True, "cache_name": getattr(self, "_manuscript_cache_name", None)}
                logging.info(f"♻️ [V61.5] Manuscript 캐시 재사용 (ep={ep_num})")

            # 캐시가 있으면 캐시 기반 질의, 없으면 일반 질의
            # [V67.1] story_context 추가
            prompt = self._prompt_loader.load(
                "director",
                "MANUSCRIPT_HISTORY_CONFLICT_PROMPT",
                ep_num=ep_num,
                manuscript_history="(캐시된 컨텍스트 참조)"
                if cache_result.get("cache_name")
                else self._d._escape_braces(context_text[: ContextLimits.MAX_CONTEXT_CHARS]),
                current_manuscript=self._d._escape_braces(new_manuscript),  # [V70] 중괄호 이스케이프
                story_context=self._d._escape_braces(story_context) if story_context else "(작품 설정 정보 없음)",
            )
            if prompt and memory_context:
                prompt += f"\n\n### 🔍 [SC-5] 벡터 메모리 참고 — 과거 에피소드 관련 컨텍스트\n{memory_context}"
            if not prompt:
                return {
                    "decision": "REJECT",
                    "conflicts": [{"severity": "CRITICAL", "description": "프롬프트 로드 실패 — fail-closed"}],
                    "summary": "Prompt loading failed: MANUSCRIPT_HISTORY_CONFLICT_PROMPT",
                    "prompt_error": True,
                }

            if cache_result.get("cache_name"):
                response = self._d._ask_with_cached_context(cache_result["cache_name"], prompt, temperature=0.1)
            else:
                response = self._d.ask(prompt, temperature=0.1, thinking_level="low")

            result = self._d._extract_json_robust(response)
            if not isinstance(result, dict):
                return {
                    "decision": "REJECT",
                    "conflicts": [{"severity": "CRITICAL", "description": "응답 파싱 실패 — fail-closed"}],
                    "summary": "파싱 오류 — fail-closed",
                    "parsing_error": True,
                }

            # [Sweep59] 자매 메서드와 동일한 CRITICAL 필터 적용
            decision = result.get("decision", "PASS")
            conflicts = result.get("conflicts", [])
            critical_count = sum(1 for c in conflicts if isinstance(c, dict) and c.get("severity") == "CRITICAL")

            if decision == "CONFLICT" and critical_count > 0:
                return {
                    "decision": "CONFLICT",
                    "conflicts": conflicts,
                    "summary": result.get("summary", ""),
                    "critical_count": critical_count,
                    "cache_used": cache_result.get("cached", False),
                }
            else:
                return {
                    "decision": "PASS",
                    "conflicts": conflicts,
                    "summary": result.get("summary", ""),
                    "warnings_only": True,
                    "cache_used": cache_result.get("cached", False),
                }

        except Exception as e:
            logging.warning(f"⚠️ [C-3] Manuscript 연속성 검증 오류 (UNKNOWN 반환): {str(e)[:50]}")
            return {"decision": "UNKNOWN", "conflicts": [], "summary": "", "error": str(e)}
