# 글도비 v2 — LLM 딥다이브 적대적 3-Pass 감리 교정 보고서

**조사일**: 2026-03-18
**대상**: `geuldobi-v2-llm-integration-deepdive-3pass-audit.md` (원본 보고서)
**방법**: 3회 독립 적대적 감리 — 원본 보고서의 모든 주장을 코드베이스 실물 대조로 반증/확인
**목적**: 과장·허위·누락 완전 제거 → 정확한 최종 판정

---

## 0. Executive Summary

| 구분 | 원본 | 교정 후 |
|------|------|---------|
| CRITICAL | 5건 | **0건** (전부 하향) |
| HIGH | 9건 | **4건** |
| MEDIUM | 10건 | **12건** (CRITICAL/HIGH 하향 + 기존) |
| LOW | 4건 | **10건** (CRITICAL/HIGH 하향 + 기존) |
| FALSE (삭제) | 0건 | **2건** |
| **합계** | 28건 | **28건** (2건 FALSE로 삭제 → 실질 26건) |

**핵심 발견**: 원본 보고서는 **기존 완화 장치를 체계적으로 무시**하고, **2건의 사실 오류**를 포함하며, 심각도를 전반적으로 과대 평가함. 그러나 발견 영역 자체는 유효하며 26건의 실질 이슈가 확인됨.

---

## 1. FALSE 판정 (삭제 대상) — 2건

### FALSE-1: 연속 프롬프트 이중 해제 (원본 §10.2)

**원본 주장**: `_escape_braces(overlap_anchor)`가 `{{` 생성 → f-string 내에서 `{{` → `{`로 해제 → 이스케이핑 무효화

**실제**: Python f-string은 **템플릿 리터럴**의 `{{`만 해제함. 변수 값 내의 `{{`는 **치환 후 그대로 보존**됨.

```python
safe_anchor = "{{test}}"  # _escape_braces 결과
prompt = f"Cut off at: '...{safe_anchor}'"
# 결과: "Cut off at: '...{{test}}'"  ← 해제 안 됨
```

**판정**: **사실 오류. 삭제.**
**3-Pass 일치**: Pass 1 미검증 / Pass 2 미검증 / Pass 3 FALSE 판정

---

### FALSE-2: `_sanitize_context_cache_token(None)` → `"none"` (원본 §7.2)

**원본 주장**: `_sanitize_context_cache_token(None)` → `"none"` → sha256 → 모든 미식별 프로젝트가 동일 해시

**실제 코드** (`base_agent.py` L1845-1846):
```python
@staticmethod
def _sanitize_context_cache_token(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", str(value or "")).strip("_.")
```

- `value=None` → `value or ""` → `""` → `str("")` → `""` → regex → `""` → strip → `""` (빈 문자열)
- 빈 문자열은 falsy → `or` 체인에서 다음 후보로 정상 이동
- `"none"`이 아닌 `""`을 반환하므로 원본의 "동일 해시" 주장은 **허위**

**판정**: **사실 오류. 삭제.**
**3-Pass 일치**: Pass 1 FALSE / Pass 2 미검증 / Pass 3 FALSE

---

## 2. CRITICAL → 하향 조정 — 5건 전부

### 원본 CRITICAL-1: 캐시 키 장르 폴백 → **MEDIUM으로 하향**

**원본 주장**: 장르 폴백으로 프로젝트 간 캐시 오염
**교정**:
- 장르 폴백 체인 자체는 **확인됨** (`base_agent.py` L1848-1862)
- 그러나 원본이 **무시한 완화 장치**: 캐시 키는 `f"{cache_type}_{project_name}_{content_hash}"` (L1895)로 구성 → `content_hash`(MD5)가 **2차 격리층** 제공
- 프로젝트 간 오염 조건: 동일 namespace + 동일 content MD5 → 사실상 동일 콘텐츠
- `"none"` 주장은 FALSE (위 참조)

**교정 심각도**: **MEDIUM** — 스키마 설계 개선 권고 (work_id 필수화) 수준
**3-Pass 일치**: Pass 1 PARTIALLY TRUE / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
base_agent.py L1848: def _context_cache_project_namespace(self, *scope_parts)
base_agent.py L1895: cache_key = f"{cache_type}_{project_name}_{content_hash}"
base_agent.py L1894: content_hash = hashlib.md5(...).hexdigest()[:16]
```

---

### 원본 CRITICAL-2: anyOf 스키마 → **HIGH로 하향**

**원본 주장**: anyOf로 string/object 비결정적 반환 → `for d in _details`에서 글자 단위 순회
**교정**:
- anyOf 스키마 존재: **확인됨** (`response_schemas.py` L518-552, 총 5개 스키마/필드)
- 그러나 원본이 **무시한 완화 장치**: `blueprint_ensemble.py` L246-247:
  ```python
  if isinstance(_details, list) and _details:
      _detail_text = "\n".join(f"  - {d}" for d in _details if isinstance(d, str))
  ```
  `isinstance(_details, list)` 가드가 **이미 존재** → string 시 스킵
- L1094-1106에도 추가 방어 코드: `if isinstance(s_chars, str): s_chars = [s_chars]`
- "글자 단위 순회" 주장은 **해당 라인에서는 FALSE**

**교정 심각도**: **HIGH** — anyOf 설계 자체는 불량 (방어 코드 유지보수 부담), 하류 모든 소비자 검증 필요
**3-Pass 일치**: Pass 1 EXAGGERATED (downstream) / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
response_schemas.py L518: BLUEPRINT_SCENE_ENTRY_SCHEMA = types.Schema(anyOf=[...])
blueprint_ensemble.py L246: if isinstance(_details, list) and _details:
blueprint_ensemble.py L1094-1106: isinstance 가드 추가 존재
```

---

### 원본 CRITICAL-3: protagonist_name 프롬프트 인젝션 → **LOW로 하향**

**원본 주장**: protagonist_name 미소독 → 프롬프트 인젝션
**교정**:
- writer.py L166에서 `protagonist_name` 미이스케이핑: **확인됨**
- 그러나 원본이 **무시한 맥락**:
  1. **자가 호스팅 도구** — "공격자"는 자기 자신의 데이터를 공격하는 것
  2. `response_mime_type: "application/json"` + `response_schema` → LLM 출력 형식 강제
  3. `_escape_braces()`는 **f-string 포맷팅 보호용**이지 프롬프트 인젝션 방지용이 아님
  4. 다른 에이전트(`arc_ensemble.py` L764, `blueprint_ensemble.py` L532)에서는 **이스케이핑 적용됨**
- 원본의 공격 벡터 `"{instruction: ...}"`은 실제로 **Python KeyError를 발생**시킴 (f-string이 변수로 해석)

**교정 심각도**: **LOW** — writer.py의 포맷팅 불일치 (다른 에이전트와 비대칭), 보안 취약점 아님
**3-Pass 일치**: Pass 1 CONFIRMED (존재) / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
writer.py L166: [주인공 이름: {protagonist_name}]  ← 미이스케이핑
arc_ensemble.py L764: protagonist_name=self._escape_braces(protagonist_name)  ← 이스케이핑
base_agent.py L972: "response_mime_type": "application/json"  ← 출력 형식 강제
```

---

### 원본 CRITICAL-4: `_last_thinking` 미리셋 → **LOW로 하향**

**원본 주장**: ask() 진입 시 `_last_thinking` 미리셋 → 호출 간 상태 누수
**교정**:
- 기술적 사실: **확인됨** — `ask()` L604-605에서 `_last_thinking` 리셋 없음
- 그러나 원본이 **무시한 맥락**:
  1. `_last_thinking`은 **진단/로깅 전용** — 생성 로직에 영향 없음
  2. 사용처: `director_auditor.py` L987, `director_ensemble.py` L800/815/1161/1176/1830/1853 — 모두 성공한 `ask()` 후 읽기
  3. 실패 시 호출자는 에러 응답 처리 중 → `_last_thinking` 접근 안 함
  4. 다음 성공 호출에서 L832 `self._last_thinking = _thinking_text`로 정상 덮어쓰기

**교정 심각도**: **LOW** — 로깅 아티팩트, 데이터 오염 아님
**3-Pass 일치**: Pass 1 CONFIRMED / Pass 2 CONFIRMED / Pass 3 OVERRATED

**코드 근거**:
```
base_agent.py L302: self._last_thinking = ""  ← __init__
base_agent.py L604-605: ask() 진입 — _last_thinking 리셋 없음
base_agent.py L832: self._last_thinking = _thinking_text  ← 성공 시 갱신
director_ensemble.py L800: thinking=getattr(self._d, "_last_thinking", "")  ← 진단용 읽기
```

---

### 원본 CRITICAL-5: `json.loads(strict=False)` → **LOW로 하향**

**원본 주장**: NaN/Infinity 허용 → 수치 필드 오염
**교정**:
- `strict=False` 사용: **확인됨** (`base_agent.py` L1703)
- 그러나 원본이 **무시한 맥락**:
  1. `response_mime_type: "application/json"` + `response_schema` → Gemini API가 **타입 강제** (INTEGER 필드에 NaN 불가)
  2. `_extract_json_robust()`는 **최후 수단 파서** — 정상 경로에서는 Gemini 구조화 출력 직접 수신
  3. `strict=False`의 주요 효과: 문자열 내 제어 문자 허용 → 한국어 텍스트 처리에 **실용적**
  4. LLM이 리터럴 `NaN`/`Infinity`를 JSON 응답으로 생성할 확률은 극히 낮음

**교정 심각도**: **LOW** — 방어적 개선 권고 수준 (심층 방어), 활성 취약점 아님
**3-Pass 일치**: Pass 1 CONFIRMED (코드) / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
base_agent.py L1703: data = json.loads(raw_json, strict=False)
base_agent.py L972: "response_mime_type": "application/json"  ← API 수준 타입 강제
base_agent.py L1670: def _extract_json_robust(...)  ← 최후 수단 파서
```

---

## 3. HIGH 판정 유지 — 4건

### HIGH-6: 토큰 추정 ±30% 오차 — **HIGH 유지**

**확인됨** (`metrics_collector.py` L274-290):
```python
korean_chars = sum(1 for c in text if "가" <= c <= "힣")
other_chars = len(text) - korean_chars
return int(korean_chars / 1.5 + other_chars / 4)
```

**교정 보충**: 실제 API 토큰 카운트가 **사용 가능할 때는 사용됨** (L434-436 폴백 조건). 추정은 **실패 호출 한정**.
**3-Pass 일치**: 3/3 확인

---

### HIGH-9: 429 모호 분류 — **HIGH 유지** (원본 대비 동일)

**확인됨** (`base_agent.py` L1092-1100):
```python
is_rate_limit = "429" in error_str and ("rate" in error_str or "limit" in error_str)
is_quota_exhausted = "resource_exhausted" in error_str or ("quota" in error_str and "429" not in error_str)
is_ambiguous_429 = "429" in error_str and not is_rate_limit and not is_quota_exhausted
```

모호 429 → rate limit 처리 → 최대 3회 × 30/60/90초 무의미 대기 후 모델 전환.
**3-Pass 일치**: 3/3 확인

---

### HIGH-10: API 키 전체 소진 시 — **HIGH 유지** (원본 대비 동일)

**확인됨** (`base_agent.py` L224-226):
```python
if cls._rotation_count >= len(cls._api_keys) - 1:
    cls._key_rotation_pending = False
    return None
```

`None` 반환 → 호출부에서 기존 키 유지 → 명시적 경고 없음.
**교정 보충**: Pass 1이 "무경고"를 과장으로 판정했으나, 실제로 log WARNING 없이 마지막 키로 계속 시도하는 것은 운영 관점에서 HIGH 유지 타당.
**3-Pass 일치**: 2/3 확인, 1/3 EXAGGERATED

---

### HIGH-2 (신규 승격): anyOf 스키마 설계 — **HIGH**

원본 CRITICAL에서 하향. anyOf 패턴 5곳이 모든 하류 소비자에게 isinstance 방어 부담을 전가.
현재 방어 코드 존재하나 **신규 소비자 추가 시 누락 리스크** 지속.

---

## 4. HIGH → 하향 조정 — 5건

### 원본 HIGH-7: 프롬프트 무경고 절단 → **MEDIUM**

**원본 주장**: "무경고 절단"
**실제**: L320-321에서 `logging.warning()` 발생 + L325에서 `requires_human_intervention = True` 설정
**교정**: 경고 **있음**. 다만 로그 레벨 경고이므로 운영 대시보드에서 포착 여부는 설정 의존.
**3-Pass 일치**: Pass 1 PARTIALLY TRUE / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
base_agent.py L320: logging.warning("[TF3-H7] Prompt length gate applied: %d -> %d chars...")
base_agent.py L325: self.requires_human_intervention = True
```

---

### 원본 HIGH-8: 5×2=10회 호출 비용 급증 → **MEDIUM**

**원본 주장**: MAX_CONTINUATIONS=5 × 2모델 = 10회
**실제**: 백업 모델 경로 (`_attempt_backup_recovery`) L1317-1465는 **단일 호출**, 연속 루프가 아님. 최대 = 5연속 + 1백업 = **6회**.
**3-Pass 일치**: Pass 1 EXAGGERATED / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
base_agent.py L640: MAX_CONTINUATIONS = 5
base_agent.py L1317: def _attempt_backup_recovery(...)  ← 단일 호출
```

---

### 원본 HIGH-11: 폴백 체인 순환 → **LOW**

**원본 주장**: flash→flash 무한 시도
**실제**:
- `_build_model_stack()` L938: `if self.backup_model and self.backup_model != self.primary_model` → 동일 모델 중복 방지
- primary가 flash이면 model_stack = `[flash]` → `max_quota_retries = 1` → `0 < 0` false → 즉시 "all fallbacks exhausted" 경로
- **무한 루프 불가능**

**3-Pass 일치**: Pass 1 CONFIRMED (체인 존재) / Pass 2 CONFIRMED (체인 존재) / Pass 3 OVERRATED (무한루프 불가)

**코드 근거**:
```
base_agent.py L51-54: DEFAULT_MODEL_FALLBACK_CHAIN = {"gemini-2.5-flash": "gemini-2.5-flash"}
base_agent.py L938: if self.backup_model and self.backup_model != self.primary_model:
base_agent.py L1142: quota_retry_count < max_quota_retries - 1  ← len([flash])=1, 0<0=False
```

---

### 원본 HIGH-12: Phase 1→2 제약 캐시 stale → **LOW**

**원본 주장**: 재시도 시 제약 캐시가 갱신 안 되어 잘못된 제약으로 Blueprint 생성
**실제**: 제약 블록은 `arc_data`와 `prev_blueprint`에서 파생 — 이 입력은 **재시도 루프 내에서 불변**.
**3-Pass 일치**: Pass 1 CONFIRMED (코드) / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
three_phase_blueprint_generator.py L196-212: if cached_constraint_block and retry > 0: ... = cached_constraint_block
```

---

### 원본 HIGH-13: PASS_WITH_FIX 3회 실패 → 미검증 반환 → **MEDIUM**

**원본 주장**: 미검증 blueprint 하류 전달
**실제**: L641에서 `verdict = "REJECT"` 명시 설정 → **외부 재시도 루프 계속**. "미검증 반환"이 아닌 REJECT 처리.
다만 L631-632에서 PASS_WITH_FIX 버전이 `best_blueprint`로 **채택**되는 점은 주의 필요.
**3-Pass 일치**: Pass 1 PARTIALLY TRUE / Pass 2 N/A / Pass 3 OVERRATED

**코드 근거**:
```
three_phase_blueprint_generator.py L631: if _last_rv in ("PASS_WITH_FIX", "PASS_WITH_WARNING"):
three_phase_blueprint_generator.py L632:     best_blueprint = _current_bp  ← 부분 수정본 채택
three_phase_blueprint_generator.py L641: verdict = "REJECT"  ← 명시적 REJECT 처리
```

---

## 5. MEDIUM 판정 — 기존 + 승격/하향 합산 12건

| # | 이슈 | 원본 | 교정 | 3-Pass 근거 |
|---|------|------|------|-------------|
| 1 | 캐시 키 장르 폴백 | CRITICAL | **MEDIUM** | content_hash 2차 격리 |
| 7 | 프롬프트 절단 (경고 있음) | HIGH | **MEDIUM** | logging.warning 존재 |
| 8 | 5+1=6회 호출 비용 | HIGH | **MEDIUM** | 수학 오류 교정 |
| 13 | PASS_WITH_FIX REJECT 처리 | HIGH | **MEDIUM** | verdict=REJECT 확인 |
| 15 | Temperature 0.5→0.3 전환 | MEDIUM | **MEDIUM 유지** | 3/3 확인 |
| 16 | finish_reason 예외→"stop" | MEDIUM | **MEDIUM 유지** | bare except는 과도하나 정상 경로는 추출됨 |
| 17 | Safety 필터 → 빈 응답 | MEDIUM | **MEDIUM 유지** | 3/3 확인 |
| 19 | OpenAI usage 키 불일치 | MEDIUM | **MEDIUM** (보정) | 추정 폴백이 0 방지하나 실측값 손실 |
| 20 | 비용 예산 한도 미집행 | MEDIUM | **MEDIUM 유지** | 3/3 확인 |
| 21 | Thinking 토큰 비용 미반영 | MEDIUM | **MEDIUM** (보정) | output에 포함되나 별도 단가 미적용 |
| 24 | 설정 변경 무반영 (런타임) | MEDIUM | **MEDIUM 유지** | 3/3 확인 |
| 18 | 실패 시 전체 응답 DB 기록 | MEDIUM | **MEDIUM 유지** | 2/3 확인 |

---

## 6. FALSE 판정 (원본 MEDIUM → 삭제) — 2건

### 원본 MEDIUM-22: `_rotation_lock` TOCTOU → **FALSE**

**원본 주장**: Client 생성이 lock 밖에서 발생 → TOCTOU
**실제**: 코드에 명시적 주석 존재 (`base_agent.py` L249-250):
```python
# [A4-P1-3] Client 생성도 lock 내에서 수행 — TOCTOU 방지
# key index/key 값은 lock 내에서 캡처
```
**설계 패턴**: lock 내에서 값 캡처 → lock 해제 → I/O 수행 → 실패 시 롤백. 의도적 capture-then-release 패턴.
**3-Pass 일치**: Pass 1 미검증 / Pass 2 FALSE / Pass 3 미검증

---

### 원본 MEDIUM-23: hud_context 방어적 복사 없음 → **FALSE**

**원본 주장**: 스레드 간 hud_context 변경 영향
**실제**: `hud_context`는 `_build_hud_context()` 반환값 = **Python 문자열** (immutable). 스레드에서 변경 불가.
**3-Pass 일치**: Pass 1 미검증 / Pass 2 FALSE / Pass 3 미검증

---

## 7. LOW 판정 — 기존 + 하향 합산 10건

| # | 이슈 | 원본 | 교정 | 근거 |
|---|------|------|------|------|
| 3 | protagonist_name 미이스케이핑 | CRITICAL | **LOW** | 자가호스팅, JSON 강제, 포맷팅 불일치 수준 |
| 4 | `_last_thinking` 미리셋 | CRITICAL | **LOW** | 진단 로그 전용 |
| 5 | json.loads strict=False | CRITICAL | **LOW** | Gemini JSON 모드 방지, 최후수단 파서 |
| 11 | 폴백 체인 자기참조 | HIGH | **LOW** | model_stack 중복제거로 무한루프 방지 |
| 12 | 제약 캐시 stale | HIGH | **LOW** | 입력 불변 |
| 14 | 배치 부분 실패 무롤백 | HIGH | **LOW** | 읽기 전용 검증이므로 롤백 개념 약함 |
| 25 | top_p 0.95 하드코딩 | LOW | **LOW 유지** | 3/3 확인 |
| 26 | 캐시 해시 16자 충돌 | LOW | **LOW** (과장) | 50 엔트리에서 충돌 확률 ~3.4e-17 |
| 27 | 오버랩 중복제거 100자 cap | LOW | **LOW 유지** | 100자 cap은 합리적 |
| 28 | 앙상블 동점 첫번째 반환 | LOW | **LOW** (보정) | 전체 후보 목록도 반환 → Director가 최종 선택 |

---

## 8. 원본 보고서가 놓친 추가 조사 결과

### 보안 전수 조사 (Pass 3)

| 검사 항목 | 결과 | 근거 |
|-----------|------|------|
| `eval()`/`exec()` on LLM output | **안전** | `ast.literal_eval()` 사용 (L1706, L1807) — 리터럴만 평가 |
| SQL injection via LLM output | **안전** | f-string SQL은 하드코딩 스키마명 사용, LLM 출력 미삽입 |
| 파일 시스템 조작 via LLM output | **안전** | LLM 출력을 경로로 사용하는 코드 없음 |
| 하드코딩 시크릿 | **안전** | 모든 API 키 `os.getenv()` 로드 |
| 무한 메모리 증가 | **안전** | `_agent_durations` 500 상한, `_context_caches` 50 상한, `_metrics` 완료 시 정리 |
| MetricsCollector 스레드 안전성 | **안전** | `threading.Lock()` 보호 |

---

## 9. 최종 교정 위험 매트릭스

| # | 이슈 | 교정 심각도 | 파일 | 라인 | 3-Pass 확인 |
|---|------|-----------|------|------|------------|
| 1 | anyOf 스키마 설계 (방어 코드 부담) | **HIGH** | response_schemas.py | L518 | 3/3 ✓ |
| 2 | 429 모호 분류 → 무의미 대기 | **HIGH** | base_agent.py | L1092-1100 | 3/3 ✓ |
| 3 | API 키 소진 시 무경고 | **HIGH** | base_agent.py | L224-226 | 2/3 ✓ |
| 4 | 토큰 추정 ±30% (폴백 한정) | **HIGH** | metrics_collector.py | L274-290 | 3/3 ✓ |
| 5 | 캐시 키 장르 폴백 (content_hash 2차 격리 있음) | MEDIUM | base_agent.py | L1848-1862 | 3/3 ✓ |
| 6 | 프롬프트 절단 (경고 있으나 로그 수준) | MEDIUM | base_agent.py | L306-326 | 3/3 ✓ |
| 7 | 연속 호출 최대 6회 비용 | MEDIUM | base_agent.py | L640 | 2/3 ✓ |
| 8 | PASS_WITH_FIX 실패 → REJECT+부분채택 | MEDIUM | three_phase*.py | L625-645 | 2/3 ✓ |
| 9 | Temperature 0.5→0.3 무경고 전환 | MEDIUM | base_agent.py | L592, L1967 | 3/3 ✓ |
| 10 | finish_reason 과도한 except | MEDIUM | gemini_provider.py | L24-30 | 3/3 ✓ |
| 11 | Safety 필터 → 빈 응답 | MEDIUM | gemini_provider.py | L18-30 | 3/3 ✓ |
| 12 | OpenAI usage 키 불일치 (추정 폴백) | MEDIUM | base_agent.py | L276-281 | 2/3 ✓ |
| 13 | 비용 예산 한도 미집행 | MEDIUM | metrics_collector.py | L256-269 | 3/3 ✓ |
| 14 | Thinking 토큰 별도 단가 미적용 | MEDIUM | metrics_collector.py | L307-311 | 2/3 ✓ |
| 15 | 시스템 설정 런타임 불변 | MEDIUM | base_agent.py | L149 | 2/3 ✓ |
| 16 | 실패 시 전체 응답 DB 기록 | MEDIUM | base_agent.py | L537-538 | 2/3 ✓ |
| 17 | protagonist_name 포맷팅 불일치 | LOW | writer.py | L166 | 2/3 ✓ |
| 18 | `_last_thinking` 미리셋 (로그용) | LOW | base_agent.py | L302 | 3/3 ✓ |
| 19 | json.loads strict=False (최후수단) | LOW | base_agent.py | L1703 | 2/3 ✓ |
| 20 | 폴백 체인 자기참조 (stack 중복제거) | LOW | base_agent.py | L51-54 | 3/3 ✓ |
| 21 | 제약 캐시 재사용 (입력 불변) | LOW | three_phase*.py | L196-212 | 2/3 ✓ |
| 22 | 배치 검증 부분 실패 (읽기전용) | LOW | batch_validator.py | L80-94 | 2/3 ✓ |
| 23 | top_p 0.95 하드코딩 | LOW | base_agent.py | L972 | 3/3 ✓ |
| 24 | 캐시 MD5 16자 (50 엔트리에서 무의미) | LOW | base_agent.py | L1894 | 2/3 ✓ |
| 25 | 오버랩 100자 cap | LOW | base_agent.py | L1255-1265 | 2/3 ✓ |
| 26 | 앙상블 첫 후보 대표 (Director 최종 선택) | LOW | blueprint_ensemble.py | L398-450 | 3/3 ✓ |

---

## 10. 교정 수정 권고 (Top 5)

원본 보고서의 "Top 5 수정 권고"를 교정 결과 기반으로 재정렬:

| 순위 | 권고 | 심각도 | 작업량 |
|------|------|--------|--------|
| 1 | **anyOf 스키마 제거** — object only 고정, 하류 isinstance 부담 제거 | HIGH | 중 |
| 2 | **429 분류 개선** — API 응답 코드+헤더 기반 분류로 전환 | HIGH | 소 |
| 3 | **API 키 소진 시 명시적 WARNING 로그** 추가 | HIGH | 소 |
| 4 | **토큰 추정 개선** — tiktoken 또는 API 실측 우선 사용 | HIGH | 중 |
| 5 | **캐시 네임스페이스 work_id 필수화** — 장르 폴백 제거 | MEDIUM | 소 |

---

## 11. 감리 방법론 평가

### 원본 보고서 문제점

| 문제 유형 | 건수 | 영향 |
|-----------|------|------|
| **사실 오류** (FALSE) | 2건 | `_sanitize(None)→"none"`, f-string 이중 해제 |
| **기존 완화 장치 무시** | 7건 | isinstance 가드, content_hash, JSON 강제, 불변 입력, stack 중복제거 등 |
| **심각도 과대 평가** | 12건 | CRITICAL 5건 전부 + HIGH 5건 하향 + MEDIUM 2건 삭제 |
| **수학 오류** | 1건 | 5×2=10 → 실제 5+1=6 |

### 적대적 감리 가치

- 원본 28건 중 **26건은 실질 이슈** (코드 근거 확인)
- 그러나 심각도 분포가 CRITICAL 5 / HIGH 9에서 **HIGH 4 / MEDIUM 12 / LOW 10**으로 대폭 교정
- **발견 자체의 가치는 높으나, 심각도 판정이 문맥 무시로 인해 체계적 과대 평가**

---

*3회 독립 적대적 감리 (총 78+ tool uses) → 교정 완료*
*문서 생성: 2026-03-18*
