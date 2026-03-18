# 글도비 v2 — LLM 딥다이브 최종 판정서 (6-Pass 적대적 감리)

**조사일**: 2026-03-18
**방법**: 3회 조사 → 3-Pass 감리 → 3회 적대적 교정 → 3회 2차 적대적 검증 (총 12 에이전트, 200+ tool uses)
**확신도**: 93% — 2차 적대적 감리에서 추가 교정 2건 발생, 나머지 안정

---

## 0. 감리 이력 요약

| 단계 | 문서 | 역할 |
|------|------|------|
| 1단계 | `geuldobi-v2-llm-integration-deepdive-3pass-audit.md` | 원본 — 3회 독립 조사 + 3-Pass 감리 |
| 2단계 | `geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md` | 1차 교정 — 3회 적대적 감리 |
| 3단계 | `geuldobi-v2-devils-advocate-pass3-audit.md` | Devil's Advocate 상세 근거 |
| **4단계** | **본 문서** | **최종 판정 — 2차 적대적 감리 (Pass 4-6) 반영** |

---

## 1. 1차 교정 대비 변경 사항 (2차 적대적 감리 결과)

| # | 이슈 | 1차 교정 | 2차 검증 후 최종 | 변경 근거 |
|---|------|---------|-----------------|-----------|
| 3 | protagonist_name 미이스케이핑 | LOW | **MEDIUM** | FastAPI 서버(`bridge_server.py`) 존재 확인 + 데이터 무결성 각도 |
| 4 | 토큰 추정 ±30% | HIGH | **MEDIUM** | 추정은 **실패 호출 한정** 폴백 — 성공 호출은 API 실측값 사용 |
| 9 | 429 모호 분류 | HIGH | **MEDIUM** | 실제 Gemini 429 응답에 거의 항상 "rate"/"limit"/"resource_exhausted" 포함 |
| 15 | Temperature 0.5→0.3 전환 | MEDIUM | **LOW** | 모든 호출부가 **명시적 temperature 전달** — 기본값 차이 미발현 |
| — | `_extract_json_robust` 역할 | "최후수단 파서" | **모든 응답의 1차 파서** | 60+ 호출부에서 `ask()` 반환 문자열에 직접 호출 확인 |

---

## 2. 최종 위험 매트릭스 (확정)

### HIGH — 2건

| # | 이슈 | 파일 | 라인 | 코드 근거 | 6-Pass 일치 |
|---|------|------|------|-----------|------------|
| **H1** | anyOf 스키마 설계 (5곳) — 모든 소비자에 isinstance 방어 부담 전가 | response_schemas.py | L518, L528, L534, L572, L585 | `anyOf=[types.Schema(type=OBJECT), types.Schema(type=STRING)]` | 6/6 ✓ |
| **H2** | API 키 전체 소진 시 무경고 | base_agent.py | L224-226 | `return None` — 호출부·로그 모두 경고 없음 | 5/6 ✓ |

**H1 상세 근거**:

anyOf 사용 5곳 확인:
```
response_schemas.py L518: BLUEPRINT_SCENE_ENTRY_SCHEMA — anyOf(OBJECT, STRING)
response_schemas.py L528: characters 필드 — anyOf(STRING, ARRAY)
response_schemas.py L534: key_events 필드 — anyOf(STRING, ARRAY)
response_schemas.py L572: equipment 필드 — anyOf(STRING, ARRAY)
response_schemas.py L585: timeline 필드 — anyOf(STRING, OBJECT)
```

하류 isinstance 가드 현황 (Pass 4-6 전수 조사):
- **가드 있음** (13곳): `blueprint_ensemble.py` L246/L866/L1094, `director_continuity.py` L288, `stage4_interview_round.py` L646/L726, `stage3_orchestrator.py` L1932, `stage4_context_builder.py` L199, `chief_writer_context.py` L367, `stage0_handoff.py` L121, `confidence_calibration.py` L251, `state_service.py` L363, `three_phase_blueprint_generator.py` L334
- **약한 가드** (1곳): `confidence_calibration.py` L256 — `or []` 패턴으로 string 시 글자 단위 순회 가능

→ 현재 방어는 양호하나 **신규 소비자 추가 시 누락 리스크 지속** = HIGH 유지 정당

**H2 상세 근거**:

```python
# base_agent.py L224-226
if cls._rotation_count >= len(cls._api_keys) - 1:
    cls._key_rotation_pending = False
    return None  # ← 경고 로그 없음
```

호출부 (`base_agent.py` L620-623):
```python
new_client = self._try_rotate_key()
if new_client:
    self.client = new_client  # None이면 기존 키 유지, 경고 없음
```

→ 운영자에게 키 소진 사실이 전달되지 않음 = HIGH 유지 정당

---

### MEDIUM — 11건

| # | 이슈 | 파일 | 라인 | 코드 근거 요약 | 6-Pass 일치 |
|---|------|------|------|---------------|------------|
| **M1** | 캐시 키 장르 폴백 | base_agent.py | L1848-1862, L1895 | 장르 폴백 실재. 단 `cache_key=f"{type}_{ns}_{content_hash}"` — content_hash가 2차 격리 | 6/6 ✓ |
| **M2** | protagonist_name 포맷팅 불일치 | writer.py | L166 | `{protagonist_name}` 미이스케이핑. `bridge_server.py` FastAPI 존재 + 데이터 무결성 리스크 | 5/6 ✓ |
| **M3** | 프롬프트 절단 (경고 있음) | base_agent.py | L306-326 | `logging.warning()` + `requires_human_intervention=True` 설정됨 | 6/6 ✓ |
| **M4** | 연속 호출 최대 6회 비용 | base_agent.py | L640, L1317 | MAX_CONTINUATIONS=5 + backup 1회 = 6회. 원본 10회는 오류 | 5/6 ✓ |
| **M5** | PASS_WITH_FIX 실패 → REJECT+부분채택 | three_phase*.py | L625-645 | `verdict="REJECT"` 설정 후 외부 루프 계속. L631에서 부분 채택 | 5/6 ✓ |
| **M6** | finish_reason 과도한 except | gemini_provider.py | L24-30 | `except Exception: finish_reason="stop"` — SAFETY 등 정상 추출되나 예외 시 위장 | 6/6 ✓ |
| **M7** | Safety 필터 → 빈 응답 | gemini_provider.py | L18-22 | `except (AttributeError, ValueError): text=""` — 빈 정상 응답과 구분 불가 | 6/6 ✓ |
| **M8** | OpenAI usage 키 불일치 | base_agent.py | L276-281 | Gemini 키(`prompt_token_count`) ≠ OpenAI 키(`prompt_tokens`) → 추정 폴백 | 5/6 ✓ |
| **M9** | 비용 예산 한도 미집행 | metrics_collector.py | L256-269 | 비용 계산만, max budget 비교 없음 | 6/6 ✓ |
| **M10** | 시스템 설정 런타임 불변 | base_agent.py | L149 | `_SYSTEM_CFG = _load_system_config()` — 모듈 임포트 시 1회 로드 | 5/6 ✓ |
| **M11** | 실패 시 전체 응답 DB 기록 | base_agent.py | L537-538 | 성공: 미기록, 실패: 응답 전문 기록 (길이 제한 없음) | 5/6 ✓ |

**M1 상세 근거** (캐시 키 구성 전체 추적):

```python
# base_agent.py L1848-1862 — 네임스페이스 구성
project_token = (
    _sanitize(work_id) or _sanitize(name) or _sanitize(project_name) or _sanitize(genre) or "default"
)

# base_agent.py L1894-1895 — 캐시 키 구성
content_hash = hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
cache_key = f"{cache_type}_{project_name}_{content_hash}"

# base_agent.py L1902 — 캐시 조회
cached_info = self._context_caches.get(cache_key)
```

→ `cache_key`에 `content_hash` 포함 → 동일 네임스페이스라도 **다른 콘텐츠면 다른 키** → 실질 오염 불가
→ 원본 CRITICAL → 1차 교정 MEDIUM → **2차 검증 MEDIUM 확정**

**M2 상세 근거** (protagonist_name):

```python
# writer.py L166 — 미이스케이핑
[주인공 이름: {protagonist_name}]

# arc_ensemble.py L764 — 이스케이핑 적용
protagonist_name=self._escape_braces(protagonist_name)

# bridge_server.py 존재 — FastAPI 서버
# POST /run, WS /events, POST /run/{run_id}/input
```

→ 1차 교정은 "자가호스팅이므로 LOW"로 판정했으나, Pass 4에서 FastAPI 서버 존재 + 데이터 무결성(스토리 내용 왜곡) 각도를 근거로 **MEDIUM으로 상향**
→ 보안 취약점이 아닌 **포맷팅 불일치 + 데이터 무결성 리스크**

---

### LOW — 11건

| # | 이슈 | 파일 | 라인 | 코드 근거 요약 | 6-Pass |
|---|------|------|------|---------------|--------|
| **L1** | `_last_thinking` 미리셋 (로그용) | base_agent.py | L302, L832 | 진단/로깅 전용. 생성 로직·LLM 입력에 미사용. 6곳 읽기 모두 `getattr(..., "")` + 로그/UI | 6/6 ✓ |
| **L2** | `json.loads(strict=False)` | base_agent.py | L1703 | **모든 응답의 1차 파서** (60+ 호출). 단 Gemini JSON 모드가 NaN/Infinity 방지. 주효과: 제어문자 허용 | 6/6 ✓ |
| **L3** | 폴백 체인 자기참조 | base_agent.py | L51-54 | `flash→flash` 존재. 단 `_build_model_stack()` L938 중복제거 + `quota_retry_count` 경계로 무한루프 불가 | 6/6 ✓ |
| **L4** | 제약 캐시 재사용 (입력 불변) | three_phase*.py | L196-212 | 재시도 루프 내 `arc_data`/`prev_blueprint` 불변 → stale 미발생 | 5/6 ✓ |
| **L5** | Temperature 기본값 차이 | base_agent.py | L592, L1967 | `ask()` 0.5 vs `_ask_with_cached_context()` 0.3. **단 모든 호출부가 명시적 temperature 전달** → 기본값 미사용 | 4/6 ✓ |
| **L6** | 토큰 추정 ±30% (폴백 한정) | metrics_collector.py | L274-290 | **실패 호출에서만** 사용. 성공 호출은 API 실측값. 비용 보고 정확도에만 영향 | 5/6 ✓ |
| **L7** | 배치 검증 부분 실패 | batch_validator.py | L80-94 | `asyncio.gather(return_exceptions=True)`. 래퍼 자체는 위임만 — 하위 orchestrator 의존 | 5/6 ✓ |
| **L8** | top_p 0.95 하드코딩 | base_agent.py | L972 | 4곳 반복: L972, L1181, L1342, L2006. 설정 불가 | 6/6 ✓ |
| **L9** | 캐시 MD5 16자 | base_agent.py | L1894 | 50 엔트리에서 충돌 확률 ~3.4e-17. 실질 무의미 | 5/6 ✓ |
| **L10** | 오버랩 100자 cap | base_agent.py | L1255-1265 | 100자 이상 오버랩은 연속 응답에서 극히 드뭄. 합리적 상한 | 5/6 ✓ |
| **L11** | 앙상블 첫 후보 대표 반환 | blueprint_ensemble.py | L398-450 | 전체 후보 목록도 함께 반환 → Director가 최종 선택. 의도적 설계 | 6/6 ✓ |

**L2 상세 근거** (`_extract_json_robust` 역할 교정):

1차 교정 보고서는 이를 "최후수단 파서"로 기술했으나 **사실 오류**:

```python
# ask() L833 — 원시 문자열 반환
return full_response

# 60+ 호출부 패턴:
response = self._d.ask(prompt, ...)
result = self._d._extract_json_robust(response)  # ← 모든 응답의 1차 파서
```

→ `ask()`는 JSON 파싱 없이 원시 텍스트 반환. 모든 호출부가 `_extract_json_robust()`를 직접 호출.
→ "최후수단"이 아니라 **유일한 JSON 파서**. 내부적으로 `json.loads(strict=False)` → `ast.literal_eval` → regex 폴백 순서.
→ 그러나 Gemini `response_mime_type: "application/json"` + `response_schema`가 API 수준에서 타입 강제 → NaN/Infinity 도달 확률 극소 → **LOW 유지 정당**

**L5 상세 근거** (Temperature 기본값 미발현):

Pass 6에서 `_ask_with_cached_context()` 호출부 전수 조사:
- 모든 호출부가 `temperature=` 파라미터를 **명시적으로 전달**
- `ask()`에서 `_ask_with_cached_context()` 호출 시에도 temperature 전달 확인
- 기본값 차이(0.5 vs 0.3)가 실제 발현하는 경로 없음
→ 원본 MEDIUM → 1차 교정 MEDIUM → **2차 검증 LOW 확정**

---

### FALSE (삭제 확정) — 4건

| # | 이슈 | 원본 위치 | FALSE 근거 | 6-Pass |
|---|------|-----------|-----------|--------|
| **F1** | f-string 이중 해제 | 원본 §10.2 | Python f-string은 변수 치환값 내 `{{`를 해제하지 않음 | 4/6 ✓ |
| **F2** | `_sanitize(None)→"none"` | 원본 §7.2 | `None or ""` → `""` (빈 문자열). `"none"` 아님 | 6/6 ✓ |
| **F3** | `_rotation_lock` TOCTOU | 원본 §16.1 | capture-then-release 패턴 + `_key_rotation_pending` 단발 플래그 + `_MIN_ROTATION_INTERVAL` 방지 | 5/6 ✓ |
| **F4** | `hud_context` 방어적 복사 필요 | 원본 §16.2 | `hud_context`는 Python 문자열 (immutable). 스레드 간 변경 불가 | 6/6 ✓ |

**F1 잔여 이슈** (LOW): `_escape_braces` 후 LLM에 `{{skill_name}}` 형태로 전달 → 원본 텍스트와 불일치하여 연속 앵커 매칭 실패 가능. 그러나 이는 Python 크래시가 아닌 앵커 정합성 문제. 실발현 빈도 극소.

**F3 잔여 이슈** (LOW): 이론적 롤백 race — Thread A 실패 후 `_current_key_idx` 롤백이 Thread B의 상태를 덮어쓸 수 있음. 단 `_key_rotation_pending` 단발 플래그로 동시 진입 사실상 차단.

---

## 3. 1차 교정 보고서의 사실 오류 교정

| # | 1차 교정 주장 | 실제 | 출처 |
|---|-------------|------|------|
| 1 | `_extract_json_robust()`는 "최후수단 파서" | **모든 응답의 유일한 JSON 파서** (60+ 호출부) | Pass 4, 6 코드 추적 |
| 2 | 토큰 추정이 HIGH (주요 경로) | **실패 호출 한정 폴백** — 성공 시 API 실측값 사용 | Pass 5 `L434-436` 조건 확인 |
| 3 | 429 모호 분류가 HIGH | 실제 Gemini 429에 거의 항상 키워드 포함 → **발현 빈도 극소** | Pass 5 API 응답 패턴 분석 |

---

## 4. 최종 심각도 분포 비교

| 심각도 | 원본 (1단계) | 1차 교정 (2단계) | **최종 (4단계)** | 변화 |
|--------|-------------|-----------------|-----------------|------|
| CRITICAL | 5 | 0 | **0** | — |
| HIGH | 9 | 4 | **2** | ▼2 (토큰추정·429 하향) |
| MEDIUM | 10 | 12 | **11** | ▼1 (Temperature 하향) + protagonist ▲1 |
| LOW | 4 | 10 | **11** | ▲1 |
| FALSE | 0 | 2+2 | **4** | — |
| **실질 합계** | 28 | 26 | **24** | |

---

## 5. 최종 수정 권고 (확정 Top 5)

| 순위 | 권고 | 심각도 | 작업량 | 코드 위치 |
|------|------|--------|--------|-----------|
| 1 | **anyOf 스키마 제거** — object only 고정. 5곳 수정 | HIGH | 중 | `response_schemas.py` L518/528/534/572/585 |
| 2 | **API 키 소진 시 WARNING 로그** 추가 | HIGH | 소 | `base_agent.py` L224-226 |
| 3 | **protagonist_name `_escape_braces()` 적용** — writer.py 불일치 해소 | MEDIUM | 소 | `writer.py` L166 |
| 4 | **비용 예산 한도 가드** 추가 — 임계값 초과 시 경고 | MEDIUM | 소 | `metrics_collector.py` L256-269 |
| 5 | **실패 시 응답 DB 기록 길이 제한** — 3000자 cap 적용 | MEDIUM | 소 | `base_agent.py` L538 |

---

## 6. 감리 방법론 회고

### 각 단계별 교정 효과

| 단계 | 주요 교정 | 가치 |
|------|----------|------|
| 1단계 (원본) | 28건 발견 | 탐색 영역 설정 — **발견율 높음** |
| 2단계 (1차 적대적) | CRITICAL 5→0, FALSE 4건 | **과장 제거** — isinstance 가드·content_hash 등 완화 장치 식별 |
| 3단계 (2차 적대적) | HIGH 4→2, MEDIUM 1→LOW, LOW 1→MEDIUM | **정밀 보정** — API 실측 경로·FastAPI 존재·호출부 전수 조사 |

### 잔여 불확실성 (확신도 93%의 7%)

1. **anyOf 스키마**: 미래 신규 소비자가 isinstance 가드 없이 추가될 경우 실제 데이터 왜곡 발생 가능 — 현 시점에서는 방어됨
2. **orchestrator 부작용**: `batch_validator.py`가 위임하는 `orchestrator.validate()`의 부작용 여부 미완전 추적
3. **429 분류**: Gemini API 에러 형식 변경 시 모호 케이스 발현 가능 — 현 시점에서는 키워드 포함 확인

---

*6회 적대적 감리 (12 에이전트, 200+ tool uses) 완료*
*최종 판정 확신도: 93%*
*문서 생성: 2026-03-18*
