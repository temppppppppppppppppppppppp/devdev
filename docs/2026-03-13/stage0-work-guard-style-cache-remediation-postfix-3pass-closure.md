# Stage 0 작품가드 · 스타일캐시 보강 Post-Fix 3PASS Closure

> 작성일: 2026-03-13
> 상태: closed
> 기준 SSOT: `docs/2026-03-13/stage0-work-guard-style-cache-remediation-execution-ssot.md`
> 범위: 투자물 공용 스타일 캐시 삭제, Stage 0 작품가드 선택형 진입점 추가, 스타일 캐시 use/refresh/reset 및 메타 기반 무효화 보강

---

## 0. 최종 결론

이번 수정 범위는 `closed`로 판정한다.

- `config/style_references/investment/style_guide.json`은 삭제되어 다음 투자물 Stage 0 스타일 분석 시 공용 캐시 재사용이 아니라 재분석으로 시작한다.
- Stage 0에는 `작품가드 설정(선택)` 진입점이 추가되었고, 작품가드는 여전히 `optional baseline`으로 유지된다.
- 스타일 레퍼런스 분석은 `캐시 사용 / 캐시 무시 재분석 / 캐시 삭제 후 재분석` 3모드를 지원하고, 캐시 무효화는 단순 `mtime`이 아니라 메타 비교로 강화되었다.
- post-fix 3PASS와 추가 재감리 후 retained `P0 / P1 / P2`는 없다.

최종 확신도는 `95%`다.

---

## 1. 실행 결과

### 1.1 투자물 공용 스타일 캐시 삭제

- 삭제 대상: `config/style_references/investment/style_guide.json`
- 현재 상태: 파일 부재 확인
- 의미:
  - 다음 투자물 Stage 0 분석은 기존 투자물 공용 캐시 hit로 시작하지 않는다.
  - `cache_mode=use`여도 shared cache가 없으므로 cold/miss 재분석 경로를 탄다.

### 1.2 작품가드 선택형 진입점 추가

- Stage 0 신규 메뉴:
  - 신규 프로젝트 메뉴: `5. 작품가드 설정 (선택)`
  - 기존 Stage 0 확장 메뉴: `7. 작품가드 설정 (선택)`
  - 내부 extended mode: `6`
- 지원 동작:
  - `work_guards/` 라이브러리에서 YAML import
  - `{project}/config/work_guard.yaml` 기본 템플릿 초기화
  - 현재 프로젝트 작품가드 미리보기
  - 현재 프로젝트 작품가드 삭제
- 정책:
  - 작품가드는 필수 준비물이 아니다.
  - 작품가드가 없는 프로젝트도 정상 baseline으로 Stage 0~4를 진행해야 한다.
  - 런타임 소비 경로는 계속 `{project}/config/work_guard.yaml` 하나로 유지된다.

### 1.3 스타일 캐시 모드 및 무효화 강화

- `StyleExtractor.extract_from_references()`는 `cache_mode`를 지원한다.
  - `use`
  - `refresh`
  - `reset`
- 캐시 파일은 raw guide가 아니라 아래 구조로 저장된다.
  - `_cache_meta`
  - `style_guide`
- 무효화 기준:
  - `analysis_version`
  - `model_id`
  - `sampling_policy`
  - `prompt_contract_hash`
  - `reference_manifest_hash`
- legacy cache payload는 stale로 간주하고 재분석한다.

---

## 2. 3PASS 감리

### Pass 1. 구현 범위 점검

확인 항목:

- Stage 0 진입점이 실제로 추가됐는지
- 작품가드가 optional baseline으로 유지되는지
- 스타일 캐시가 use/refresh/reset로 분리됐는지
- 캐시 무효화가 단순 `mtime` 의존에서 벗어났는지

판정:

- 범위 적합
- 런타임 소비 경로를 흔들지 않고 Stage 0 입력 타이밍만 보강한 점이 SSOT와 일치

### Pass 2. 회귀 및 인접 영향 점검

실행한 검증:

- `python -m py_compile modules/core/stage0/__init__.py modules/core/stage0/style_extractor.py modules/core/stage01_helpers.py`
- `pytest -q tests/test_stage0_work_guard_style_cache.py tests/test_stage01_helpers.py`
  - `37 passed`
- `pytest -q tests/test_work_guard.py tests/test_project_support.py tests/test_bridge_quality_summary.py tests/test_quality_sidecar_bootstrap.py`
  - `44 passed`

판정:

- Stage 0 전용 보강 회귀 통과
- 작품가드 런타임 소비 및 project support 인접 회귀도 통과

### Pass 3. 정리 감리

감리 중 실제로 발견해 대응한 항목:

- `style_extractor.py`에 과거 `mtime` 기반 설명과 dead helper 흔적이 남아 있었음
- 해당 helper 제거 및 docstring/설명 정합화 후 focused regression 재실행

최종 판정:

- 구현 clean
- 문서/코드/테스트 정합성 확보

---

## 3. 추가 재감리

`95%`까지 올리기 위해 아래를 추가 확인했다.

- 투자물 공용 캐시 파일 부재 여부
- 수정 파일 UTF-8 직접 판독 가능 여부
- `docs/stage_map/stage0.md`와 구현 간 메뉴/정책 동기화 여부
- 작품가드 라이브러리 소스 폴더 존재 여부

재감리 결과:

- `config/style_references/investment/style_guide.json` 삭제 상태 확인
- 주요 수정 파일 UTF-8 판독 정상
- Stage 0 문서와 구현 메뉴 번호 일치
- `work_guards/README.md`, `work_guards/investment/default_work_guard.yaml` 존재 확인

---

## 4. 최종 Findings

### Closed

- 작품가드 입력 타이밍 부재
- 작품가드가 필수 준비물처럼 읽히는 모호성
- 스타일 캐시 재분석/재사용 규칙 불명확성
- 투자물 공용 캐시를 명시적으로 비우고 재분석할 수 없는 상태

### Observation

- 이번 수정은 Stage 0 진입점과 캐시 정책 보강까지다.
- 실제 투자물 프로젝트에서 Stage 0를 다시 실행해 새 `style_guide.json`이 생성되는 런타임 증거는 아직 별도다.
- 따라서 남은 불확실성은 `runtime-only`이며, 코드/테스트/문서 기준 blocker는 아니다.

---

## 5. 확신도 Ledger

- `70`: SSOT 범위 구현 완료
- `+10`: Stage 0 메뉴/작품가드/캐시 모드 코드 경로 확인
- `+5`: 투자물 shared cache 삭제 상태 확인
- `+5`: Stage 0 focused regression `37 passed`
- `+3`: 인접 runtime support regression `44 passed`
- `+2`: 추가 재감리에서 dead helper/doc drift 정리 완료

최종 확신도: `95%`

---

## 6. 다음 액션

권장 다음 단계는 하나다.

- 투자물 프로젝트에서 Stage 0 스타일 분석을 한 번 실행해 새 shared cache 및 `{project}/stage0_output/style_guide.json`이 의도대로 재생성되는지 확인

이 확인은 런타임 증거 보강용이며, 현재 수정분 closure의 blocker는 아니다.
