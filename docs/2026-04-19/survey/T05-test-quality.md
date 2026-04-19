# T05: 테스트 스위트 품질 감사

Surveyor: Claude Code (Terminal 5)
Date: 2026-04-19
Scope: `tests/` 디렉토리 424+ 파일 전량 — 구조, 커버리지, 테스트 패턴, 픽스처 설계, 마커 현황, 플레이키 리스크, 비 pytest 아티팩트

## 1. Executive Summary

- 성숙도 판정: **Pre-production (상위 MVP, 프로덕션 접근)**
- 한줄 요약: 규모(6,571개 test, 17,841개 assert)·property 테스트·xfail 제로화 등 **상위 수준의 테스트 기반**을 갖췄으나, 일부 영역(초거대 단일 파일, `tests/`에 혼입된 비 pytest 수동 스크립트, 커밋된 바이너리 artifact)이 **프로덕션 기준에 미달**한다.

## 2. 강점 (Strengths)

### S1. 규모·밀도·다양성이 모두 확보됨
- 448개 test 파일, 6,571개 `def test_` 함수, 17,841개 `assert` (`tests/**/*.py`)
- 분류된 디렉토리 구조: `chaos/`(7) · `e2e/`(10) · `integration/`(2) · `property/`(4) — `tests/README.md:5-14`
- 카테고리별 범위: unit(~423) / integration(2) / e2e(8) / property(4) / chaos(7)
- Hypothesis 사용 48건 (`tests/property/*.py`, `tests/test_*`) — 단순 example-based를 넘어선 property-based 테스트가 정착
- Parametrize 31파일 · MagicMock 205파일 · monkeypatch/patch 92파일

### S2. xfail 제로 정책이 지켜지고 있음
- `@pytest.mark.xfail` 사용 0건 (전역 grep 기준)
- MEMORY.md 에 기록된 "xfail-sweep: 68→0 전량 해소" 정책이 현재 상태로 유지됨
- `skip` 20건·`skipif` 1건은 모두 **조건부(sqlite-vec/genai 선택적 의존성, 실 프로젝트 DB 부재, 금기어 미정의)**로, 무조건 skip은 없음 — `tests/integration/test_pipeline_smoke.py:132`, `tests/test_db_merge.py:42`

### S3. 공용 conftest 설계가 명확함
- `tests/conftest.py:21-254` — 장르별 HUD 샘플(`sample_hud_wuxia`/`sample_hud_hunter`/`sample_hud_investment`), `sample_bible`/`sample_blueprint`/`sample_manuscript`, `mock_api_client`/`mock_db_manager`/`mock_project_context`/`validation_context` 등 작성 의도가 드러나는 12개 공용 픽스처
- E2E 전용 conftest(`tests/e2e/conftest.py:62-174`): 실제 `DBManager(tmp_path)` + MockLLM + `Stage4Context` 수동 조립 — 계층 경계에 맞춘 분리
- Windows FS 락 회피를 위해 conftest temp dir cleanup 에 `gc.collect() + time.sleep(0.1)` 재시도(`tests/conftest.py:28-38`) — 플랫폼 제약을 의식한 설계

### S4. 외부 의존성 없는 mock-first 정책
- `tests/` 전역에서 실 네트워크 호출(`requests.get/post`, `httpx`) **0건**
- `genai.Client(...)` 실 호출은 `monkeypatch.setattr("...vertex_provider.genai.Client", FakeClient)` 패턴으로 전량 대체 — `tests/test_llm_router.py:320,360,378,397,464`

### S5. 에이전트/밸리데이션 핵심 경로가 두터움
- director 계열 17파일, writer 11파일, manager 9파일, chief_writer 9파일
- `modules/validation/*` 참조 49파일, `modules/api/*` 참조 18파일, `db_manager` 참조 63파일
- 거대 파이프라인 단위 테스트: `test_stage4_interview_round.py`(13,014 LOC, 317 test 함수)·`test_stage4_orchestrator.py`(4,835 LOC, 163 test 함수)·`test_stage4_post_processor.py`(3,190 LOC)·`test_stage4_context_builder.py`(2,965 LOC) — Stage4가 실제로 가장 리스크 큰 영역임을 고려하면 규모 자체는 정당

### S6. 메모리 의식 있는 로컬 러너 제공
- `scripts/run_pytest_lowmem.py:18-22` — 12개 단위 샤딩 + 메모리 점유율 기반 pause/resume(pause 90%, resume 82%) — Windows 고메모리 환경에 대응
- `tests/README.md:18-27` 에 공식 실행 가이드 문서화

---

## 3. 개선 필수 (Critical Issues) — P0

### P0-1. `tests/` 아래에 **pytest가 인식하지 못하는 스크립트**가 혼재

파일:
- `tests/stage3_isolated_test/test_stage3_arc3.py:30` — `from dotenv import load_dotenv`
- `tests/stage3_isolated_test/test_stage3_arc3_v2.py`
- `tests/stage3_isolated_test/test_stage3_production.py:182` — `genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))`
- `tests/stage4_v2_test/test_batch_1_to_10.py:72`
- `tests/stage4_v2_test/test_episode_1.py:47`

5개 파일 전부 `def test_` 함수 0개 (`grep -c "def test_"` 검증 완료). 이들은 `if __name__ == "__main__"` 기반 실행 스크립트로, `pyproject.toml:64-68`의 `python_files = ["test_*.py"]` 규칙에 의해 **pytest가 수집만 하고 0 테스트로 처리**한다. 그러나 수집 시 import가 일어나며 `load_dotenv(...)` / 실 API 키 의존 로직이 트리거될 수 있다.

영향도: **높음**
- 수집 단계에서 `SOURCE_PROJECT = PROJECT_ROOT / "projects" / "팽가 망나니 가문 재건"` 같은 **외부 디렉토리 의존**이 있어 CI/깨끗한 체크아웃에서 collection-only 에러가 발생할 여지
- `tests/README.md:31` "Tests must not import from `projects/` or `docs/`" 규칙을 스스로 위반
- 실 Gemini API 호출 코드가 `tests/` 트리에 상주 — 실수로 실행 시 비용/레이트 리밋 리스크

권장 조치:
1. 두 디렉토리를 `scripts/manual_harness/` 또는 `tools/experiments/` 로 이동
2. 또는 `pyproject.toml`에 `norecursedirs = ["tests/stage3_isolated_test", "tests/stage4_v2_test"]` 명시
3. 진짜 테스트로 전환하려면 `def test_*` 함수로 래핑 + `@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="manual")` + `@pytest.mark.manual` 커스텀 마커

### P0-2. `tests/stage4_v2_test/project/` 에 커밋된 바이너리 DB/체험판 데이터

파일:
- `tests/stage4_v2_test/project/project_data.db` (512KB, Binary)
- `tests/stage4_v2_test/project/chroma_db/long_term_anchor.db` (12KB)
- `tests/stage4_v2_test/project/chroma_db/vector_db/chroma.sqlite3` (164KB)
- `tests/stage4_v2_test/results/ep_*.txt` (실 에피소드 산출물)
- `tests/stage4_v2_test/project/plans/{arcs,blueprints}/*.txt` (실 플랜 데이터)
- `tests/stage3_isolated_test/blueprints_*.json`, `production_test_*.json`, `test_result_*.json`, `test_v2_result_*.json`, `progress.log` — 실행 artifact 7건

`git ls-files tests/stage4_v2_test/` 로 확인됨. `tests/stage4_v2_test` 총 1.1MB, `tests/stage3_isolated_test` 437KB.

영향도: **중간~높음**
- 테스트 artifact가 리포지토리 기록에 누적 → git clone/fetch 용량·리베이스 난이도 증가
- 일자 라벨링된 JSON(`blueprints_20260203_183608.json`)은 재현 가능한 테스트 데이터가 아닌 일회성 실행 스냅샷
- `ep_*.txt` 처럼 **원작자의 실제 집필 샘플로 추정되는 텍스트 자산**이 테스트 디렉토리에 존재 — 의도가 불명확

권장 조치:
1. DB/artifact 전량 git 히스토리에서 제거(`git filter-repo` 등) 후 `.gitignore` 확장
2. 고정 씨앗 데이터가 필요하면 `tests/fixtures/` 로 이동 + minimal subset으로 축소
3. `results/` 디렉토리는 테스트 실행 시 `tmp_path` 로 재생성

---

## 4. 개선 권장 (Major Issues) — P1

### P1-1. 초거대 단일 테스트 파일 — 분할 필요
`wc -l tests/test_*.py` 기준 500 LOC 이상이 **53개**, 가장 큰 건:

| LOC | 파일 | 테스트 함수 |
|-----:|------|------:|
| 13,014 | `tests/test_stage4_interview_round.py` | 317 |
| 4,835 | `tests/test_stage4_orchestrator.py` | 163 |
| 3,861 | `tests/test_failure_analyzer.py` | 50 |
| 3,190 | `tests/test_stage4_post_processor.py` | — |
| 2,965 | `tests/test_stage4_context_builder.py` | — |
| 2,955 | `tests/test_blueprint_patch_mode.py` | 86 |
| 2,715 | `tests/test_pass_with_fix.py` | — |
| 2,502 | `tests/test_stage2_preflight.py` | — |

`test_stage4_interview_round.py:13014` 단일 파일에 317개 테스트가 몰려 있어:
- 수정 시 rebase 충돌 핫스폿
- 실패 시 한 슈트 다운이 다량 회귀 가리기 쉬움
- 특정 테스트만 선택 실행할 때 `::`-path 식별 부하
- `scripts/run_pytest_lowmem.py` 의 12-unit 샤딩이 해당 파일을 단일 배치로 묶기 때문에 메모리 피크 제어가 어려움

권장 조치: interview round 하위 단계별(예: round_decision, followup_prompt, escape_hatch, feedback_gate)로 **4~6개 파일로 분할**.

### P1-2. `modules/core/` 내 25% 파일이 테스트 직접 참조 없음

`modules/core/*.py` 165개 중 **41개(24.8%)** 가 `tests/**/*.py` 어디에도 `from modules.core.X` 또는 `import X` 형태로 등장하지 않음 (간접 호출은 있을 수 있음):

대표: `arc_state_utils`, `arc_summary_utils`, `data_collector`, `diversity_sampler`, `dynamic_prompt_weighting`, `episode_state_arbiter`, `error_helper`, `escape_utils`, `expert_mixture`, `jianghu_logic`, `jsonl_io`, `karma_service`, `lore_manager`, `material_db`, `non_wuxia_recovery_policy`, `pre_director_narrative_checker`, `pre_director_style_checker`, `primitive_guard`, `quality_constitution`, `scene_obligation_heuristics`, `stage2_entity_contract`, `stage2_location_contract`, `stage3_envelope_builder`, `stage4_policy_digest`, `stage4_postselect_runtime`, `stage4_retry_runtime`, `tactical_intrusion_contract`, `technique_weaver`, `work_identity_surface`, 외 12건

각각 `modules/` 내부에서는 사용됨(`jianghu_logic`·`escape_utils`·`lore_manager` 각 1회, `jsonl_io` 5회, `arc_state_utils` 2회 등)이므로 dead code는 아니지만 **계약/경계 단위 테스트 부재**.

영향도: 핵심 헬퍼/계약 모듈의 회귀를 파이프라인 테스트에만 의존 → 경계 버그 탐지 지연.

권장 조치: 상기 41개 중 top-10 중요 모듈(`episode_state_arbiter`, `primitive_guard`, `stage2_entity_contract`, `stage2_location_contract`, `stage3_envelope_builder`, `stage4_policy_digest`, `stage4_postselect_runtime`, `stage4_retry_runtime`, `tactical_intrusion_contract`, `quality_constitution`)에 한해 smoke 단위 테스트 추가.

### P1-3. 에이전트 7종이 테스트 직접 참조 없음
`modules/domain/agents/*.py` 기준:
- `analyst_prompts`, `chief_writer_inplace_local_ops`, `stage3_blueprint_patch_ir`, `stage3_prompt_envelope`, `stage3_retry_coordinator`, `stage3_validation_boundary`, `state_tracker_financial`

특히 `state_tracker_financial.py:1-124` 는 `modules/domain/agents/state_tracker.py:37,198` 에서 `StateTrackerFinancial` 를 composite 멤버(`self._financial`)로 보유하나 tests/ 에 **단 한 번도 import 되지 않음**. 투자물 장르 재무 상태 추적의 회귀 가드 전무.

권장 조치:
1. `test_state_tracker_financial.py` 신설 — 자산/현금/주식/연결 갱신 경계 테스트
2. `stage3_validation_boundary` 는 Stage3 가드 직진입점이므로 contract 테스트 필수

### P1-4. 커스텀 마커 미등록 — slow/integration/e2e/chaos 구분 불가
`pyproject.toml:63-68` 에 `markers` 섹션 없음. 전역 grep 결과 `@pytest.mark.{parametrize, skipif}` 외 커스텀 마커는 0종.

영향도:
- 빠른 CI 피드백 루프 구성 불가 — `pytest -m "not slow"` 같은 필터 불가
- e2e/chaos 테스트가 무거움에도 기본 run에서 자동 제외되지 않음
- 현재는 경로 기반(`pytest tests/test_*.py` 과 `pytest tests/e2e/`) 분리에만 의존

권장 조치: `pyproject.toml`에 `markers = ["slow", "chaos", "e2e", "integration", "property", "manual"]` 등록 + 해당 디렉토리 pytestmark 자동 부여.

### P1-5. 픽스처 215개 중 93%가 개별 파일 산포
- 전역/e2e conftest: 16개 공용 픽스처
- 개별 테스트 파일 내 `@pytest.fixture`: **199개** (215 − 16)
- 재사용되는 샘플 데이터(Bible/Blueprint/HUD/MockDirector 등)가 파일마다 중복 선언될 가능성

권장 조치: 주요 테스트 클러스터(director, stage4_orchestrator, chief_writer)별로 하위 `conftest.py` 도입 + factory 패턴(`build_bible(overrides=...)`) 도입.

### P1-6. 실 시간 `time.sleep` 4건 — 플레이키 리스크 (경미)
- `tests/test_api_contract.py:326,541` — TTL=0 approval 만료 검증 `time.sleep(0.01)`
- `tests/test_integrity.py:62` — 동시성 race 유도 `time.sleep(0.001)`
- `tests/test_project_manager_arc_storage.py:59` — mtime delta 확보 `time.sleep(0.02)`
- `tests/conftest.py:29,38,191` — Windows FS cleanup (픽스처 teardown, 테스트 결과와 무관)

영향도: 현재는 수치가 작아 회피 가능하나, 부하 많은 CI에서 `test_api_contract` 만료 경계가 가끔 밀릴 수 있음.

권장 조치: `time.sleep(0.01)` → `freezegun` 또는 `router._clock = lambda: now + 1` 식 주입 가능한 clock으로 리팩터.

---

## 5. 개선 검토 (Minor Issues) — P2

### P2-1. `tests/` 최상위 평탄 구조 — 422개 파일 flat
`find tests -maxdepth 1 -name "test_*.py" | wc -l` = **422**. 장르(wuxia/alt_history/actor/sports/medical/…), 단계(stage2/3/4), 에이전트(director/chief_writer/weaver) 등 도메인이 혼재해 있어 탐색 부하. `tests/stage4/`, `tests/agents/director/` 같은 디렉토리 승격이 장기적으로 유리.

### P2-2. `pytest.ini_options.addopts` 가 `-p no:xdist` 로 병렬 실행 불가
`pyproject.toml:68` — xdist 비활성화. 로컬 lowmem 러너가 대체하지만 CI는 이를 고려해야 함. README(`tests/README.md:33`) 에서 수동 opt-in 가능하다고 언급되나 개발자 진입장벽.

### P2-3. 테스트 로그/출력 스타일만 설정, 실패 디테일은 `--tb=short` 고정
`pyproject.toml:68` — long traceback 이 필요한 대형 픽스처 실패 시 추적 어려움. 환경 변수나 `--tb=auto` 토글 가능하도록.

### P2-4. 테스트 없는 `critic.py`, `base_agent.py` 의존 에이전트들이 많음
`test_base_agent.py`(1,201 LOC)는 강하나, base/critic 변경 시 파생 에이전트 회귀 가드 부재.

### P2-5. `tests/integration/` 에 단 2개 파일만 존재
`test_patch_wiring.py`, `test_pipeline_smoke.py` — integration 레이어가 의도적 최소 구성인지, unit에 흡수되었는지 불분명. README 갱신 필요.

### P2-6. Property 테스트 4개는 하이퍼리티브 영역 대비 작음
DB rollback / budget / validation / rollback 만 property 대상. `state_tracker`·`arc_constraint`·`npc_relationship` 같은 고상태 모듈에 property-based 확장 여지.

### P2-7. `assert` 17,841개 중 `assert expr` 단순 bool 패턴 다수
실패 시 diff 의미가 약함. `assert result == expected`, `assert set(a) == set(b)` 스타일 강화 or `pytest-assume`/`pytest-check` 고려.

---

## 6. 수치 지표 (Metrics)

| 항목 | 값 | 비고 |
|------|------:|------|
| 총 `test_*.py` 파일 수 | 448 | `find tests -name test_*.py` |
| 유효 pytest 파일 수 | 443 | `def test_` 포함 |
| 비 pytest 스크립트 | 5 | `stage3_isolated_test/`, `stage4_v2_test/` |
| `def test_` 함수 수 | 6,571 | — |
| 총 `assert` 수 | 17,841 | — |
| tests/ 총 LOC | 149,255 | |
| modules/ 총 LOC | 197,545 | tests/modules LOC 비율 ≈ 0.76 |
| 500 LOC+ 메가 테스트 파일 | 53 | 1500+ LOC 파일 12개 |
| 최대 단일 파일 | 13,014 LOC / 317 test | `test_stage4_interview_round.py` |
| 전역 `@pytest.fixture` | 215 | 그 중 공용 conftest 16 |
| Mock/MagicMock 사용 파일 | 205 | — |
| `monkeypatch`/`patch` 파일 | 92 | — |
| `hypothesis` 사용 | 48건 | `tests/property/`, 기타 |
| `pytest.mark.parametrize` 파일 | 31 | — |
| `pytest.skip`/`skipif` | 21 | 조건부, 무조건 skip 없음 |
| `pytest.xfail` | 0 | 정책 유지 |
| 커스텀 마커 등록 | 0 | `pyproject.toml` 미등록 |
| 실 `time.sleep` (prod sleep patch 제외) | 4 | conftest teardown 3건 추가 |
| 실 네트워크 호출 (requests/httpx) | 0 | `tests/` 전역 |
| conftest 파일 수 | 2 | `tests/conftest.py`, `tests/e2e/conftest.py` |
| `modules/` 유니크 import | 179 | `from modules.*` 정렬·중복 제거 기준 |
| 테스트 직접 참조 없는 core 파일 | 41 / 165 (24.8%) | maxdepth 1 기준 |
| 테스트 직접 참조 없는 agent 파일 | 7 / 56 (12.5%) | |
| 커밋된 바이너리/데이터 artifact | 9+ | DB 3 + JSON/log 6+ |

## 7. 성숙도 근거 (Maturity Evidence)

**Pre-production 근거** (상위 MVP / production 임박):

1. **테스트 밀도**: LOC 대비 76% — 오픈소스 중대형 프로젝트 평균(40~60%)을 상회
2. **정책 엄격성**: xfail 0건 유지, 무조건 skip 0건, 실 네트워크 호출 0건 — 운영 코드에 준하는 위생
3. **다양성**: unit/integration/e2e/chaos/property 전 계층 존재, Hypothesis·Parametrize·Mock 패턴 균형
4. **플랫폼 의식**: Windows FS락 회피 cleanup, lowmem 러너, `PYTHONIOENCODING=utf-8` 요구 등 실환경 대응

**Production-ready로 판정하지 못하는 이유**:

1. **하드 블로커 2종**: `tests/` 디렉토리에 pytest 스크립트가 아닌 실 API 호출 스크립트(P0-1)와 커밋된 바이너리 DB/실데이터 artifact(P0-2) — 프로덕션 릴리즈 기준 게이트 위반
2. **구조적 부채**: 단일 파일 13K LOC 같은 God test(P1-1)는 CI 유연성과 실패 신호 품질을 훼손
3. **계약/경계 공백**: core 24.8% · agent 12.5% 의 직접 테스트 공백(P1-2/3) — 회귀 그물 완결성 미달
4. **CI 도구 옵션 부재**: 커스텀 마커 미등록(P1-4) · xdist 비활성(P2-2) — 빠른 피드백 루프 구성 어려움

## 8. 권장 로드맵 (Recommendations)

### Phase 1 — 위생 (1~2 스프린트, P0 해소)
1. `tests/stage3_isolated_test/`, `tests/stage4_v2_test/` 전량 `scripts/manual_harness/` 로 이동
   - 또는 `norecursedirs` 에 등재 + pytest 스크립트화
2. 커밋된 DB/artifact/real 에피소드 텍스트 제거 + `.gitignore` 보강 (`tests/**/*.db`, `tests/**/chroma_db/`, `tests/**/results/`, `tests/stage3_isolated_test/*.json`)
3. 실 `.env` 경로(`tests/stage4_v2_test/project/.env`)가 실 API 키를 담지 않는지 재확인 — `.env.example` 로 대체 후 삭제

### Phase 2 — 회귀 그물 보강 (2~4 스프린트, P1-2/3 해소)
4. 최우선 10개 core 모듈(`episode_state_arbiter`, `primitive_guard`, `stage2_entity_contract`, `stage2_location_contract`, `stage3_envelope_builder`, `stage4_policy_digest`, `stage4_postselect_runtime`, `stage4_retry_runtime`, `tactical_intrusion_contract`, `quality_constitution`) 단위 테스트 신설
5. `state_tracker_financial` 포함 에이전트 7종 smoke 테스트 신설
6. 장르 guard 매트릭스 테스트 강화 (현재 sports/alt_history/composer/cooking/medical/actor 각 1~2 테스트만 존재)

### Phase 3 — 구조 리팩터 (3~6 스프린트, P1-1/4/5 해소)
7. `test_stage4_interview_round.py` (13K LOC) → round 단계별 4~6 파일 분할
8. `tests/` → 도메인 서브디렉토리(`tests/stage4/`, `tests/agents/director/`, `tests/validation/`) 로 점진 이관
9. 커스텀 마커 체계 도입 (`slow`, `chaos`, `e2e`, `integration`, `property`, `manual`) + 디렉토리 pytestmark + CI 워크플로 분리

### Phase 4 — 품질·속도 최적화 (선택)
10. `time.sleep` 기반 시간 검증을 주입 가능한 clock으로 치환
11. `hypothesis` 적용을 `state_tracker`/`arc_constraint`/`npc_relationship` 까지 확대
12. `pytest-xdist` 조건부 활성화 (메모리 가이드 병행)
13. coverage.py 정기 측정 + 트렌드 기록 (`coverage xml` → CI 게이트)
