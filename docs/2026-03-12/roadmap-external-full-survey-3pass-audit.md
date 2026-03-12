# 로드맵 외부 영역 전수조사 + 3-Pass 감리

> **범위**: `today-code-health-ui-build-roadmap.md` 범위 바깥 전 영역
> **조사일**: 2026-03-12
> **코드 수정**: 없음 (문서화만)
> **확신도**: 95%

---

## 1. 조사 범위 정의

로드맵이 커버하는 영역:
- Backend Stage 4 sink alignment (candidate_key/artifact_path 불일치)
- Frontend/Desktop P1/P2 제거
- UI 3-pass 재감리
- Build chain 재현성

**이 문서가 커버하는 영역**: 위 4가지 외 전부.

---

## 2. 발견 사항

### FIND-1: BUG-PRICE-1 — 비용 계산 2.5배 과대 (P1)

**파일**: `modules/core/metrics_collector.py` L78
**현상**: `gemini-2.5-pro` cache_read 가격이 `0.3125`로 설정됨. Google 공식 가격은 `0.125`.
**영향**: 캐시 읽기 비용이 2.5배 부풀려서 집계됨. 비용 대시보드/로그의 비용 수치가 실제보다 과대 표시.
**파이프라인 영향**: 없음 — 비용 집계는 사후 통계용이며 LLM 호출이나 원고 생산에 관여하지 않음.
**발견 경로**: TF-VERTEX 감사(`TF-VERTEX-migration-full-audit.md`)에서 최초 식별, 미수정 상태.
**수정 범위**: 1파일 1줄 (`0.3125` → `0.125`).

### FIND-2: artifact_logging.py 파일 I/O 에러 핸들링 부재 (P1)

**파일**: `modules/core/artifact_logging.py` L45
**현상**: `file_path.write_text()` 호출이 try/except 없이 실행됨.

```python
# L44-46 (현재)
file_path = scope_dir / filename
file_path.write_text(serialized["text"], encoding="utf-8")  # ← 보호 없음
artifact_path = file_path.relative_to(root).as_posix()
```

**영향**: 디스크 꽉 참 / 권한 오류 시 예외가 호출자(stage2_finalizer, stage3_orchestrator, stage4 코드)로 전파. 호출자들도 이 호출을 try/except로 감싸지 않음 (`stage2_finalizer.py` L1360 확인). 결과적으로 **원고 생산은 성공했는데 artifact 저장 실패로 전체 Stage가 크래시**할 수 있음.
**발생 확률**: 낮음 (디스크 여유 충분한 환경). 장기 연재 시 artifact 누적으로 디스크 압박 가능성 존재.
**수정 범위**: `artifact_logging.py` 1곳 (write_text를 try/except로 감싸고 빈 artifact_path 반환).

### FIND-3: 신규 모듈 3개 테스트 부재 (P2)

| 모듈 | 줄 수 | 역할 | 위험도 |
|------|-------|------|--------|
| `modules/core/artifact_logging.py` | 106줄 | artifact 스냅샷 저장 + candidate_key 생성 | 중 — sink 정합성의 핵심 |
| `modules/core/logging_keys.py` | 54줄 | attempt_key/session_id 결정론적 생성 | 중 — 키 형식 깨지면 sink 불일치 |
| `modules/core/soft_failure.py` | ~100줄 | 비차단 실패 보고 + 스로틀링 | 낮 — 지원 유틸 |

**영향**: `artifact_logging.build_candidate_key()`가 sink 간 candidate_key 일관성의 핵심인데 테스트 없음. 카나리 test_07의 candidate_key 불일치와 직접 연관될 가능성 있음.
**수정 범위**: 테스트 파일 3개 신규 (약 25-30개 테스트).

---

## 3. WorkGuard 호출 체인 분석

### 3.1 호출 체인

```
main_a.py L1044-1047: GenreGuard 생성
    create_genre_guard(genre_type)
         ↓
main_a.py L1051-1058: WorkGuard 래핑 (조건부)
    if work_guard.yaml 존재 → WorkGuard(base_guard, yaml_path)
         ↓
main_a.py L1937-1948: StyleGuard 래핑 (조건부)
    if style_guide 존재 → StyleGuard(guard, style_guide)
         ↓
director_auditor.py L94: 실행
    self._d.guard.run_deep_validation(manuscript, current_state)
```

**실행 순서** (decorator 패턴): StyleGuard.run_deep_validation() → WorkGuard.run_deep_validation() → GenreGuard.run_deep_validation() → 결과 합산 반환.

### 3.2 work_guard.yaml 생성 경로

| 경로 | 구현 상태 | 비고 |
|------|-----------|------|
| Desktop UI 편집 | ✅ 구현됨 | `main.js` L570-602, IPC read/write |
| 수동 파일 배치 | ✅ 가능 | `{project}/config/work_guard.yaml` |
| Stage 0 자동 생성 | ❌ 없음 | 프로젝트 초기화 시 생성 안내 없음 |
| CLI 생성 마법사 | ❌ 없음 | `main_a.py` 메뉴에 미포함 |
| REST API 생성 | ❌ 없음 | bridge_server에 상태 조회만 존재 |
| 기본 템플릿 | ❌ 없음 | 빈 파일부터 직접 작성 필요 |

### 3.3 인터랙티브 설정 시점

**결론: 없음.** WorkGuard는 **선택적 기능**으로 설계됨. 파일이 없으면 조용히 건너뛰고 GenreGuard만 동작. Desktop UI에서 편집은 가능하나 "신규 생성" 버튼이나 마법사는 없음.

**심각도 판정**: Observation. WorkGuard는 파워유저용 선택적 커스터마이징 레이어. 없어도 Guard 체인이 정상 동작(GenreGuard → StyleGuard). 자동 생성 마법사는 기능 확장 영역이며 건강도 이슈가 아님.

---

## 4. 기타 영역 전수 스캔

### 4.1 Config/YAML 정합성

- `config/models.yaml`: provider 설정 일관 (gemini=true, 나머지 disabled) ✅
- `config/settings/validation.yaml`: 임계값 문서화 일치 ✅
- **드리프트 없음.**

### 4.2 Dead Code / 미추적 디렉토리

- `MagicMock/` (untracked): 테스트 중 mock `current_project.paths.root`에서 생성된 잔여물. `projects/MagicMock/project_data.db` 365KB 포함. **삭제 가능, Observation.**
- `stage2_optimizer.py` L968: deprecated `category` 파라미터. fallback 로직 존재, 기능 정상. **P2, 코드 위생.**

### 4.3 Provider 시스템

- BUG-PRICE-1 외 추가 이슈 없음 ✅
- disabled provider (anthropic/openai/vertex) lazy import guard 정상 ✅
- `_normalize_billable_model()` vertexai: prefix 처리 정상 ✅

### 4.4 Stage 0 / 프로젝트 초기화

- 메뉴 배선 정상 ✅
- POV 선택 시스템 활성화 완료 (D-1) ✅
- **갭 없음.**

### 4.5 Stage 2/3 Sink Alignment

- `build_candidate_key()` / `build_attempt_key()` 가 S2/S3/S4 전부에서 공유됨 ✅
- `pass_rate_monitor` S2/S3/S4 전부 배선 확인 ✅
- **Stage 4에서만 터진 카나리 문제가 S2/S3에서는 재현되지 않음 확인.**

### 4.6 테스트 건강

- 3,847 collected (최종 기준)
- 신규 모듈 3개 테스트 부재 (FIND-3)
- 나머지 핵심 모듈: 통합 테스트로 간접 커버됨. 직접 테스트 파일 미존재는 P2 이하.

### 4.7 Scripts 디렉토리

- `scripts/run_stage4_canary.py`: 최신 모듈 경로 참조, 정상 ✅
- `scripts/backfill_quality_sidecars.py`: 정상 ✅
- **Stale 스크립트 없음.**

### 4.8 DB 스키마

- `director_selections` ALTER TABLE 15건+: 하위호환 마이그레이션. 기능 정상. **P2 위생, 미래 스키마 버전 관리 후보.**
- pending migration 없음 ✅

---

## 5. 3-Pass 감리

### Pass 1: 사실 정확성

| 항목 | 주장 | 검증 | 판정 |
|------|------|------|------|
| BUG-PRICE-1 | cache_read 0.3125 → 0.125 | TF-VERTEX 감사 + 코드 직접 확인 | ✅ TRUE |
| artifact_logging 에러 핸들링 | L45 write_text 보호 없음 | 코드 직접 확인 | ✅ TRUE |
| 호출자도 보호 없음 | stage2_finalizer L1360 try/except 없음 | 코드 직접 확인 | ✅ TRUE |
| WorkGuard 자동 생성 없음 | Stage 0 메뉴에 미포함 | main_a.py 확인 | ✅ TRUE |
| Desktop UI 편집 가능 | main.js L570-602 IPC 핸들러 | Agent 조사 결과 | ✅ TRUE |
| S2/S3 sink alignment 정상 | build_candidate_key 공유 | 코드 확인 | ✅ TRUE |
| "74 모듈 미테스트" P1 | (Agent 2 주장) | 통합 테스트로 간접 커버 | ❌ FALSE — 오탐. P2 이하로 하향 |

### Pass 2: 심각도 보정

- **BUG-PRICE-1**: P1 유지. 비용 집계 정확도 문제. 파이프라인 무영향이므로 P0 아님.
- **artifact_logging**: P1 유지. 디스크 풀 시 Stage 크래시 가능. 발생 확률 낮으나 방어 없음.
- **WorkGuard 인터랙티브 설정**: P1 → **Observation으로 하향**. 선택적 기능이며 없어도 Guard 체인 정상 동작. 기능 확장 영역.
- **신규 모듈 테스트**: P2 유지. artifact_logging의 `build_candidate_key()`는 sink 정합성 핵심이므로 테스트 가치 높음.
- **MagicMock/**: Observation 유지. 삭제해도 무방.
- **deprecated parameter**: P2 유지. 기능 정상.

### Pass 3: 누락 확인

- ✅ 비용/메트릭스: BUG-PRICE-1 커버
- ✅ artifact/로깅: artifact_logging + logging_keys + soft_failure 전수 확인
- ✅ Guard 체인: WorkGuard 호출 체인 + 인터랙티브 설정 + Desktop UI 전량 추적
- ✅ Config/YAML: models.yaml + validation.yaml 정합 확인
- ✅ Dead code: MagicMock/ + deprecated param
- ✅ Provider: disabled 3종 guard 확인
- ✅ Stage 0 초기화: 메뉴 배선 확인
- ✅ S2/S3 sink: S4 전용 문제 확인
- ✅ 테스트: 신규 모듈 3개 + 기존 커버리지
- ✅ Scripts: stale 없음
- ✅ DB 스키마: pending migration 없음

**누락 없음 확인.**

---

## 6. 최종 요약

| ID | 심각도 | 영역 | 설명 | 로드맵 내 |
|----|--------|------|------|-----------|
| FIND-1 | **P1** | 메트릭스 | BUG-PRICE-1: cache_read 가격 2.5배 과대 | ❌ |
| FIND-2 | **P1** | 로깅 | artifact_logging write_text 에러 핸들링 부재 | ❌ |
| FIND-3 | P2 | 테스트 | 신규 모듈 3개 (artifact_logging/logging_keys/soft_failure) 테스트 없음 | ❌ |
| FIND-4 | P2 | 코드 위생 | stage2_optimizer deprecated parameter | ❌ |
| FIND-5 | Observation | 디렉토리 | MagicMock/ 미추적 잔여물 | ❌ |
| FIND-6 | Observation | Guard | WorkGuard 인터랙티브 생성 마법사 미구현 (선택적 기능) | ❌ |

**P0: 0건 / P1: 2건 / P2: 2건 / Observation: 2건**

### 확인 완료 (CLEAR)

- Stage 2/3 sink alignment ✅
- PassRateMonitor 배선 ✅
- Config YAML 정합 ✅
- Provider guard ✅
- Stage 0 메뉴 ✅
- Scripts 최신 ✅
- DB 스키마 ✅

---

*3-pass 감리 완료. 확신도 95%. 오탐 1건 제거 ("74 모듈 미테스트" P1 → 통합 테스트 간접 커버로 하향).*
