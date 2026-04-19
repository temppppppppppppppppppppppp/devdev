# T06: 장르 시스템 무결성

Surveyor: Claude Code (Terminal 6)
Date: 2026-04-19
Scope: 9 활성 장르(무협·헌터·투자·작곡가·요리·대체역사·배우·스포츠·의학) + fantasy(내부 10번째) 시스템 전역 감사 — MEMORY.md 16항목 체크리스트 기반

## 1. Executive Summary

- **성숙도 판정**: **Pre-production** (하위 상한)
- **한줄 요약**: 10개 장르(판타지 포함)의 정적 골격은 **93% 일관**(코드 3층 + YAML + 프롬프트 라이브러리 전량 커버)이나, Guard 깊이·YAML 분량·프롬프트 조직이 **장르별 3배 불균형**이고, 체크리스트 참조 문서가 **실제 코드 구조와 drift**(genre_stage_prompts.py 부재, _SKILL_LOG_LABEL 위치 이동) 상태라 "프로덕션 투입 시 장르 추가 비용" 측면에서 부채가 누적됨.

## 2. 강점 (Strengths)

### 2.1 3층(GenreTypes/HUDKeys/NPCHUDKeys) 완전 정합
- `modules/core/constants.py:47-74` `GenreTypes.all()` → 10장르 반환
- `modules/core/constants.py:418-429` `_GENRE_HUD_MAP` → 10장르 HUD root 매핑 (MartialHUD/HunterHUD/FinanceHUD/ComposerHUD/CookingHUD/JoseonHUD/ActorHUD/SportsHUD/MedicalHUD/FantasyHUD)
- `modules/core/constants.py:552-566` `NPCHUDKeys.get_key()` → 10장르 dispatch
- **누락 없음**: 세 클래스 × 10장르 매트릭스에 공백 제로.

### 2.2 Guard Factory 완전 분기 + 체인 래핑
- `modules/core/genre_guards/__init__.py:22-69` `create_genre_guard()` → 10장르 if/elif, fallback은 `WuxiaGuard` + WARNING 로그
- `base_guard.py:16-199` 공통 추상화 — FORBIDDEN_TERMS, MANDATORY_CONCEPTS, `_is_figurative_use`, `run_deep_validation`, `_load_genre_yaml` 등 공통 API
- 3계층 Guard 체인(base→WorkGuard→StyleGuard)이 옵션 파라미터로 래핑되어 SRP 준수

### 2.3 장르 오염 방지 테스트 다층 배치
- `tests/test_genre_contamination_guardrail.py` — 장르 간 용어 침범 차단
- `tests/test_tf3_tier1_genre_completeness.py` — Tier1 완전성 스위프
- `tests/test_genre_yaml_loading.py`, `test_genre_guards_extended.py`, `test_genre_schema_builder.py` 등 5+ 전용 파일
- Guard 초기화 lane 테스트(alt_history/wuxia lane_c, lane_f) 배치

### 2.4 CONTRASTIVE_EXAMPLES 10장르 전량 보유
- `modules/core/narrative_diversity.py` L40-383에 wuxia/hunter/investment/fantasy/composer/cooking/alt_history/actor/sports/medical 모두 negative/positive 예시 페어 존재

### 2.5 main_a.py 진입 지점 10분기 완전
- `main_a.py:3235-3394` `_build_genre_selection_catalog` → 번호 1~10 전량
- `main_a.py:3422-3432` `_resolve_selected_genre` min=1, max=10 가드
- `main_a.py:3434-3458` `_initialize_selected_genre_preset_registry` → genre_map 10매핑

### 2.6 primitive_forbidden.json 장르별 `apply_level` 정책화
- `modules/core/laws/primitive_forbidden.json:9-62` — full/partial/moderate/none 4단계 정책. wuxia=full, fantasy=partial, alt_history=moderate, 나머지 현대물=none. 명시적 기준 문서화됨.

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. MEMORY.md 체크리스트 ↔ 실제 코드 drift (3항목)
- **파일:라인**: `C:\Users\PC\.claude\projects\C--Users-PC-Desktop----\memory\MEMORY.md` "Genre Addition Integrity Checklist" 섹션
- **증거**:
  - MEMORY 5번 `genre_stage_prompts.py` → **파일 부재** (Glob 결과 0건). 실제 STAGE2/3 프롬프트는 `modules/domain/agents/stage3_prompt_envelope.py`, `three_phase_blueprint_runtime.py`, `state_locked_arc_generator.py`, `modules/core/stage3_orchestrator.py`로 **분산**됨.
  - MEMORY 7번 `strategies/` → **디렉토리 삭제됨** (MEMORY 자체에 "dead code 삭제" 기록 있음에도 체크리스트에 남아있음)
  - MEMORY 12번 `state_tracker.py _SKILL_LOG_LABEL` → 실제로는 `modules/domain/agents/state_tracker_npc.py:185-196`에 위치
- **영향도**: 새 장르 추가 시 개발자가 존재하지 않는 파일을 찾거나, 잘못된 파일을 수정하여 버그 유발. 체크리스트 신뢰도 저하.
- **권장 조치**: MEMORY.md 체크리스트 16항목을 실제 코드 위치로 전수 재매핑 후 업데이트.

### P0-2. Guard 깊이 불균형 (850줄 vs 362줄, 2.4×)
- **파일:라인**:
  - `modules/core/genre_guards/hunter_guard.py` 873줄 (최대)
  - `modules/core/genre_guards/wuxia_guard.py` 683줄
  - `modules/core/genre_guards/investment_guard.py` 723줄
  - `modules/core/genre_guards/fantasy_guard.py` 362줄 (최소)
- **증거**: 파일 크기 편차 `wc -l` 결과. fantasy는 hunter 대비 **41%** 수준.
- **영향도**: 판타지 장르는 wuxia 대비 `check_state_action_consistency`, `check_hierarchy_consistency`, `check_authority_delegation`, `check_unresolved_conflict`, `check_villain_response` 등 V46/V46.1 심층 검증 오버라이드가 **빈약 가능성** → 판타지 원고에서 고구마/무능한 빌런/직위 불일치 탐지 누락 리스크.
- **권장 조치**: fantasy_guard.py, medical_guard.py(475줄), sports_guard.py(462줄), actor_guard.py(470줄) 4개 guard에 대해 base_guard 추상 메서드 오버라이드 커버리지 감사. 최소 v46/v46.1 인터페이스 8개 각각 1줄 이상 구체화.

### P0-3. config/terms/ 디렉토리 8장르 누락
- **파일:라인**: `config/terms/` 디렉토리 — `alt_history.json`, `wuxia.json` 2개만 존재
- **증거**: `ls config/terms/` → 2 files. hunter/investment/composer/cooking/actor/sports/medical/fantasy 부재.
- **영향도**: wuxia/alt_history는 장르 용어 JSON을 별도 관리하는데 다른 8장르는 YAML 내부에 임베드됨 → **이원화된 관리 체계**. 용어 추가 시 어디에 넣어야 하는지 불명확. wuxia에서만 작동하는 term-기반 기능이 다른 장르에서 실패할 수 있음.
- **권장 조치**: 두 가지 중 택1 — (a) 8장르 terms JSON 파일 생성(일관화) 또는 (b) wuxia/alt_history의 terms JSON도 YAML로 흡수하고 `config/terms/` 폐지. 설계 의도가 무엇인지 README 또는 CLAUDE.md에 명시.

### P0-4. detect_new_genre() 호환 불가 리스트 불완전
- **파일:라인**: `modules/core/stage0/preset_registry.py:612-620` `_INCOMPATIBLE` dict
- **증거**: `_INCOMPATIBLE`에 `investment`, `wuxia`, `hunter`만 항목 있음. `fantasy`, `composer`, `cooking`, `alt_history`, `actor`, `sports`, `medical`은 **누락** → 예를 들어 medical 소설에 마법 키워드 3개 이상 섞이면 `fantasy` 장르 오탐 위험.
- **영향도**: 장르 오염 오탐(false genre switch)으로 HUD 구조 파괴 가능.
- **권장 조치**: 10장르 모든 조합에 대해 호환성 매트릭스 정의. 최소 현대물(hunter/composer/cooking/actor/sports/medical) ↔ wuxia/fantasy는 상호 incompatible 처리.

## 4. 개선 권장 (Major Issues) — P1

### P1-1. config/genres/ YAML 분량 2.9× 불균형
- **파일:라인**: `config/genres/*.yaml`
- **수치**: wuxia=237줄, alt_history=146줄, actor=135줄, hunter=122줄, investment=112줄, medical=106줄, sports=104줄, composer=97줄, cooking=93줄, **fantasy=82줄(최소)**
- **영향도**: fantasy 장르는 wuxia의 35% 규칙만 가짐 → 판타지 원고 품질 검증 비대칭. 금기어 목록, 계위 체계, action_limits 섹션이 누락됐을 가능성.
- **권장 조치**: 각 YAML 섹션(forbidden_terms, mandatory_concepts, *_hierarchy, *_action_limits, *_requirements) 존재 여부 매트릭스 생성 후 fantasy 보강. 목표: 100줄 이상.

### P1-2. DEFAULT_PRESET 부재 — 장르 미지정 상황 행동 분기 불명
- **파일:라인**: `modules/core/stage0/preset_registry.py:458-466` `PresetRegistry.__init__`
- **증거**: `base_genre`가 None이거나 `GENRE_PRESETS`에 없으면 **WARNING만 로그**하고 common 프리셋만 활성화. fallback 기본값 없음.
- **영향도**: 장르 미지정 상태로 pipeline 진행 시 scoring/validation에서 무협 하드코딩으로 암묵 fallback되는지, 아니면 null-safe한지 계약이 불분명.
- **권장 조치**: `DEFAULT_FALLBACK_GENRE="wuxia"` 명시 상수화 또는 장르 필수 강제(장르 없으면 fail-fast).

### P1-3. BaseGuard의 `get_authority_hierarchy()`/`get_hostile_action_types()` 기본값이 무협 편향
- **파일:라인**: `modules/core/genre_guards/base_guard.py:586-613`
- **증거**: `get_hostile_action_types()` 기본 리턴이 `["구타", "모욕", "배신", "암살", "독살", "협박", "멸시", "학대"]` — 이는 무협/대체역사 색채. 투자/의학/스포츠에서는 "상장폐지", "오진", "도핑" 등이 적대 행동.
- **영향도**: 장르별 오버라이드 누락 시 base의 무협식 패턴이 투자/의학/스포츠 원고에 오탐 유발.
- **권장 조치**: base_guard의 해당 메서드를 `return []` 중립 기본값으로 변경하고, 각 장르 guard에서 반드시 오버라이드.

### P1-4. preset_registry의 `detect_new_genre` 키워드 개수 비대칭
- **파일:라인**: `modules/core/stage0/preset_registry.py:596-610` `genre_keywords`
- **증거**: 각 장르 8개 키워드. romance(7), politics(7), military(7)는 활성화 안 된 cross-cut 프리셋이나 같은 dict에 혼재.
- **영향도**: 활성 10장르와 cross-cut 3프리셋이 dict 하나에 섞여 있어 의도 파악 어려움. 또한 키워드 8개는 2026년 현대 한국 문학 기준 빈약(특히 composer/actor).
- **권장 조치**: cross-cut 프리셋 키워드를 별도 dict로 분리. 장르별 키워드를 15-20개로 확장.

### P1-5. wuxia_guard 포함 4개 Guard 외 V46.1 인터페이스(권위위임/고구마/빌런반응) 오버라이드 증거 부족
- **파일:라인**: `modules/core/genre_guards/base_guard.py:441-861` (6개 메서드 정의), 각 장르 guard에서의 오버라이드
- **증거**: base_guard 기본값으로만 작동할 경우 스포츠/요리/작곡가 장르에서 "무능한 빌런"/"미해결 고구마" 탐지 불가.
- **권장 조치**: 각 장르 guard에서 최소 `get_villain_response_patterns`, `get_protagonist_victory_patterns`는 장르 특화 오버라이드 제공.

### P1-6. Genre fallback 로그가 silent 위험
- **파일:라인**: `modules/core/genre_guards/__init__.py:57-59`
- **증거**: 미지원 장르 입력 시 `logging.warning` 후 WuxiaGuard 폴백. audit 이벤트 미발행.
- **영향도**: 잘못된 genre_type이 주입되어도 파이프라인은 wuxia로 계속 진행 → 원고 생성 실패 후에야 발견.
- **권장 조치**: `AuditEvents` 상수 추가 (`GENRE_FALLBACK`) 및 audit_logger에 이벤트 발행. production에서는 fail-fast 옵션 제공.

## 5. 개선 검토 (Minor Issues) — P2

### P2-1. GenreTypes.FANTASY 주석이 "V65"인데 전체는 "V40"/"V66" — 버전 태깅 일관성
- `modules/core/constants.py:53` `FANTASY = "fantasy"  # [V65] 판타지`
- 나머지 WUXIA/HUNTER/… 9개는 버전 주석 없음
- 권장: `# [V40]` / `# [V61.9 alt_history]` / `# [V62 actor]` / `# [V62.1 sports, medical]` / `# [V65 fantasy]` 도입 버전 통일 주석

### P2-2. HUDKeys `_ROLE_NAME_BLACKLIST`에 장르별 누락 있음
- `modules/core/constants.py:437-462` — "작곡가", "요리사", "배우", "선수", "의사", "조선인" 등 있지만 "투자자", "헌터", "각성자" 포함 대비 "헌터마스터", "펀드매니저", "트레이더", "명의", "국수", "대감" 등 장르별 typical role noun 누락 가능
- 권장: 장르별 guard와 대조해 blacklist 일관성 점검

### P2-3. 장르 한글명 ↔ 코드 매핑 분산
- 동일한 "무협"↔"wuxia" 매핑이 최소 4곳 존재: `constants.GenreTypes.get_name`, `main_a._build_genre_selection_catalog`, `chief_writer._CW_GENRE_CODE_MAP`, `stage0/__init__.SUPPORTED_GENRES`
- 권장: `GenreTypes.get_name`/`get_code` 한 쌍으로 통합, 나머지는 이를 참조

### P2-4. `style_guard.py`(203줄), `work_guard.py`(1036줄)은 특수 래퍼인데 genre_guards/ 디렉토리에 평행 배치 → 계층 혼동
- 권장: `genre_guards/wrappers/` 하위 디렉토리로 이동 고려

### P2-5. MEMORY.md "analyst_libraries JSON (narrative archetypes)"가 실제로는 10개 파일
- 실제: `config/prompts/analyst_libraries.json` (무협 기본) + `analyst_libraries_{hunter,investment,fantasy,composer,cooking,alt_history,actor,sports,medical}.json` (9개)
- 체크리스트가 "JSON" 단수 → 10파일 구조 명시 업데이트 필요

## 6. 수치 지표 (Metrics)

| 항목 | 값 |
|------|-----|
| 활성 장르 수 | 10 (사용자 인식 9 + 판타지 내부) |
| genre_guards/ 총 라인 수 | 7,777 |
| 장르별 guard 라인 중위값 | 493줄 |
| 장르별 guard 최대/최소 | 873(hunter) / 362(fantasy) — 2.4× |
| config/genres/ YAML 총 라인 | 1,234 |
| YAML 장르별 최대/최소 | 237(wuxia) / 82(fantasy) — 2.9× |
| analyst_libraries JSON 개수 | 10 (base + 9 장르) |
| narrative_archetypes 분포 | 23(cooking) ~ 112(wuxia base) |
| CONTRASTIVE_EXAMPLES 장르 커버 | 10/10 |
| primitive_forbidden.json genre_rules 장르 수 | 10 |
| config/terms/ 파일 수 | 2 (wuxia, alt_history만) |
| main_a.py 장르 선택 분기 | 10 (L3235-3394, min=1 max=10) |
| state_tracker_npc `_SKILL_LOG_LABEL` 장르 키 | 10 (L185-196) |
| HUDKeys `_GENRE_HUD_MAP` 항목 | 10 (L418-429) |
| NPCHUDKeys dispatch 분기 | 10 (L552-566) |
| Preset `_INCOMPATIBLE` 항목 | **3** (investment, wuxia, hunter만) |
| 장르 관련 테스트 파일 (식별됨) | 10+ |

## 7. 성숙도 근거 (Maturity Evidence)

### 왜 Pre-production (Production-ready 아님)
- **Production-ready 요건 결손**:
  - 장르 drift(체크리스트 vs 코드) 자체가 운영 품질 저하 신호
  - `_INCOMPATIBLE` 매트릭스 불완전 → 장르 오탐 방어선 미완성
  - Guard 깊이 2.4× 불균형 → 판타지/스포츠/요리/작곡가 장르에서 원고 품질 검증이 wuxia 대비 비대칭
  - config/terms/ 이원화된 관리 체계 정규화 필요
- **그래도 Pre-production (MVP/POC 아님)**:
  - 10장르 × 3층 구조(GenreTypes/HUDKeys/NPCHUDKeys) 완전 정합
  - 테스트 다층 배치(contamination_guardrail, tier1_completeness, yaml_loading 등)
  - YAML 외부화 완료(`base_guard._load_genre_yaml`)
  - 10장르 × HUDManager 전용 클래스 + factory 분기 + critical_keys 정의 완성
  - 10장르 × narrative archetypes 24+ 개씩 배포 완료

### 왜 MVP보다 상위
- 이미 9개 장르가 프로덕션 원고 생성에 투입됨 (MEMORY.md: "3,170 passed, 0 failed")
- 장르 추가 SOP가 16항목 체크리스트로 문서화됨 (drift는 있으나 체계는 존재)
- 장르별 YAML/Guard/HUD/Prompt가 완전 외부화되어 런타임 스왑 가능

## 8. 권장 로드맵 (Recommendations)

### Phase 1 — 문서 drift 해소 (추정 2시간, 2026-04-22 이전)
1. MEMORY.md 체크리스트 16항목을 실제 코드 위치로 재매핑
   - `genre_stage_prompts.py` 제거 또는 실제 4개 분산 파일로 업데이트
   - `strategies/` 항목 제거 (이미 삭제됨)
   - `state_tracker.py` → `state_tracker_npc.py:185` 수정
   - `analyst_libraries JSON` → `10개 파일 구조` 명시
2. CLAUDE.md/AGENTS.md에 "10장르 × 16 touchpoint" 공식 체크리스트 섹션화

### Phase 2 — 매트릭스 완전화 (추정 6시간)
3. `_INCOMPATIBLE` 매트릭스 10×10 완성 (`preset_registry.py:612`)
4. `config/terms/` 정책 결정 후 8장르 파일 추가 또는 wuxia/alt_history의 JSON 흡수
5. fantasy.yaml 보강 → 최소 100줄 (wuxia 대비 50% 커버리지)
6. 4개 guard(fantasy/sports/actor/medical)에 V46.1 인터페이스 6개 오버라이드 추가

### Phase 3 — 구조 개선 (추정 4시간)
7. `genre_guards/wrappers/` 서브디렉토리 신설 후 style_guard/work_guard 이동
8. `GenreTypes.get_name`/`get_code` SSOT 통합 — 나머지 3곳 참조로 리팩터링
9. `AuditEvents.GENRE_FALLBACK` 추가 + audit_logger 연동
10. base_guard 기본값 `get_hostile_action_types` 중립화

### Phase 4 — 테스트 보강 (추정 3시간)
11. 10×10 장르 cross-contamination 매트릭스 테스트 생성 (현재 일부만 존재)
12. "존재 증명 테스트" 추가: 16 touchpoint × 10 장르 = 160 assertion으로 drift 자동 감시

### 장르 추가 작업량 추정 (새 장르 1개 추가 시)
- 현재: **~16시간** (16 touchpoint × 1시간, 일부는 0.5시간, 일부 2시간)
- Phase 1-4 완료 후: **~8시간** (drift 제거 + SSOT 통합으로 절반 단축 기대)

---

**감사 종합**: 10장르 시스템은 구조적으로는 견고하나 **문서-코드 drift**와 **Guard 깊이 편차**가 부채 형태로 누적 중. P0 4건, P1 6건을 2026-04-30까지 해소하면 Production-ready 상위로 진입 가능.
