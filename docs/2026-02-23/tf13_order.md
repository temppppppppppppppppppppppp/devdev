# TF-13 Codex 실행 오더 — 프롬프트 정합성 감사

---

## ★ CODEX 환경 규칙 (최우선)

1. **인코딩**: findings 파일 작성 시 UTF-8만 사용. 한글 깨짐 방지를 위해 Write 도구로 파일을 쓸 때 BOM 없는 UTF-8로 작성한다.
2. **자동 검색 도구 금지**: `grep`, `rg`, `find`, `ag`, `ripgrep` 등 셸 자동 검색 도구를 절대 사용하지 않는다. 파일 내용 확인은 **오직 Read 도구**로만 수행한다.
3. **컨텍스트 컴팩트 시 중단 금지**: 컨텍스트 컴팩트가 발생해도 **감사를 중단하지 않는다**. findings.md의 "현재 위치"를 읽고, 미완료 Round부터 이어서 끝까지 완료한다. Round A부터 재시작하면 안 된다.
4. **토큰 절약**: 파일 내용을 findings에 통째로 복사하지 않는다. `파일:줄번호 + 핵심 스니펫(1~3줄) + 등급 + 한 줄 설명`만 기록한다.

---

## 너의 임무

글도비 프로젝트의 **프롬프트 정합성**을 감사한다.
YAML 7개 파일 × 76개 변수가 실제 코드에서 올바르게 주입되는지,
미치환 변수가 LLM에 유출되는 경로가 있는지 판정한다.

**코드 수정 없음. Read-only 감사.**

---

## 시작 전 필수

1. **이 문서 전체를 읽어라**
2. **`docs/2026-02-23/tf13_findings.md`를 읽어라** → "현재 위치" 확인

---

## 절대 수칙

1. **모든 판정은 Read 도구로 파일을 직접 읽은 후 수행한다**
2. **발견 즉시 tf13_findings.md에 기록한다**
3. **각 Round 완료 즉시 "현재 위치" 업데이트**
4. **코드를 수정하지 않는다**

---

## 컨텍스트 컴팩트 복구

1. `docs/2026-02-23/tf13_order.md` 재독
2. `docs/2026-02-23/tf13_findings.md` 재독 → "현재 위치" 확인
3. 다음 미완료 Round부터 즉시 재개

---

## Round 순서

```
Round A → B → C → D → 완료
```

---

## Round A: analyst.yaml (7개 프롬프트)

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `config/prompts/analyst.yaml` | 프롬프트 템플릿 + 변수 |
| `modules/domain/agents/analyst.py` | .load() 호출 시 kwargs |
| `modules/domain/agents/analyst_prompt_api.py` | 프롬프트 API 래퍼 |
| `modules/domain/agents/analyst_prompts.py` | 하드코딩 상수 (폴백) |

### 체크리스트

- [ ] YAML 7개 프롬프트의 변수 목록 추출
- [ ] 각 변수가 .load() 호출 시 kwargs로 주입되는지 추적
- [ ] 미주입 변수 식별 (SafeDict가 "{변수명}" 형태로 보존 → LLM 유출 가능)
- [ ] FALLBACK_CONSTANTS 커버리지 (모든 키가 폴백을 가지는가)
- [ ] analyst_prompts.py의 하드코딩 상수 vs YAML의 중복/불일치

---

## Round B: chief_writer.yaml + director.yaml (10개 프롬프트)

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `config/prompts/chief_writer.yaml` | CW 프롬프트 6개 |
| `config/prompts/director.yaml` | Director 프롬프트 4개 |
| `modules/domain/agents/chief_writer.py` | CW .load() 호출 |
| `modules/domain/agents/director.py` | Director .load() 호출 |
| `modules/domain/agents/director_continuity.py` | Director 연속성 |

### 체크리스트

- [ ] chief_writer 6개 프롬프트 변수 주입 경로 추적
- [ ] director 4개 프롬프트 변수 주입 경로 추적
- [ ] {manuscript}, {blueprint}, {feedback} 직렬화 포맷 일관성
- [ ] PATCH_MODE_PROMPT 변수 주입 완전성

---

## Round C: ensemble.yaml + arc/blueprint generator (4개 프롬프트)

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `config/prompts/ensemble.yaml` | 앙상블 프롬프트 2개 |
| `config/prompts/arc_generator.yaml` | Arc 패치 프롬프트 1개 |
| `config/prompts/blueprint_generator.yaml` | Blueprint 패치 프롬프트 1개 |
| `modules/domain/agents/arc_ensemble.py` | 앙상블 .load() 호출 |
| `modules/domain/agents/blueprint_ensemble.py` | Blueprint .load() 호출 |

### 체크리스트

- [ ] 앙상블 전략 변수 ({strategy_a/b/c}, {strategy_directive}) 주입 경로
- [ ] ARC_PATCH_MODE_PROMPT 변수 완전성
- [ ] BLUEPRINT_PATCH_MODE_PROMPT 변수 완전성

---

## Round D: SafeDict + PromptLoader 메커니즘

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/prompt_loader.py` | SafeDict, 캐싱, 폴백 로직 |
| `modules/core/prompt_builder.py` | 프롬프트 조립 |
| `config/prompts/emotion_tracker.yaml` | 감정 추적 프롬프트 2개 |

### 체크리스트

- [ ] SafeDict가 미존재 변수를 "{변수명}" 형태로 보존하는지 확인
- [ ] PromptLoader 싱글톤 캐시가 장르 전환 시 오염되지 않는지
- [ ] invalidate_cache() 호출 시점 적절성
- [ ] prompt_builder.py의 프롬프트 조립 로직과 YAML 로더의 상호작용
- [ ] emotion_tracker.yaml 2개 프롬프트 변수 주입 확인

---

## 완료 기준

- tf13_findings.md "현재 위치" = Round D 완료
- 모든 YAML 변수에 대해 주입 여부 판정 완료
- 발견 건수 집계

---

지금 바로 `docs/2026-02-23/tf13_findings.md`를 읽는 것부터 시작하라.
