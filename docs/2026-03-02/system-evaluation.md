# 글도비 시스템 종합 평가 (2026-03-02)

## 정량 지표

| 지표 | 값 | 평가 |
|------|------|------|
| 소스 코드 | 207파일, 107K줄 | 중대형 |
| 테스트 | 191파일, 3,040개 (48K줄) | 소스 대비 우수 |
| Ruff / bare except | 0 / 0 | 깨끗 |
| 50줄+ 함수 | 508개 | 심각 |
| `except Exception` | 707건 (구체 except 310건, 비율 7:3) | broad 과다 |
| `print()` 호출 | 192건 | 관측성 부채 |
| logging 호출 | 1,406건 | warning 남용 |
| core→domain 역참조 | 5건 (lazy import) | DI 무력화 |
| TODO/FIXME | 8건 | 양호 |

---

## 강점

### 1. 테스트 규율
- 196개 소스 파일 대비 191개 테스트 파일, 3,040개 전량 green
- 리팩토링(B-1 시리즈 8단계 분할)이 가능했던 근본 이유
- 프로젝트 생명줄

### 2. 분할 리팩토링 성과
- stage4_orchestrator: 2,481→883줄 (-64%)
- chief_writer: 2,255→854줄 (-62%)
- stage2_orchestrator: 2,639→907줄 (-66%)
- 대부분 프로젝트가 "나중에"에서 끝나는데, 여기는 실행 완료

### 3. Advisory 체인 설계
- TruthGate → NpcDrift → NumericDrift → Flashback → InfoParadox → RelationshipDrift
- 각각 독립 모듈, 실패 격리, Director에 advisory만 전달
- "판단은 LLM이" 대원칙을 체인 레벨에서 준수

### 4. Guard 확장 패턴
- 13개 Guard가 동일 인터페이스, 9개 장르가 동일 패턴으로 추가
- 16항목 체크리스트 문서화

### 5. DI/Protocol 기반
- Stage2/3/4 Context 클래스, 15개 Protocol 정의
- 완벽하진 않지만 뼈대 존재

---

## 구조적 문제

### 1. 거대 함수 = 미완성 분할
- ~~`stage4_interview_round.run()`: 1,649줄~~ → **686줄 (-58%)** ✅ B-1-3b 완료 (5개 private 메서드 추출)
- `stage4_post_processor.process_pass_result()`: 814줄
- `stage2_validation_pipeline.run_validation()`: 694줄
- `stage2_orchestrator.finalizer()`: 612줄
- `base_agent.ask()`: 559줄

**진단**: B-1 시리즈로 파일은 분할했지만, 서브모듈 내부 `run()` 함수가 분할 전 크기를 그대로 가져갔음. B-1-3b로 최대 함수(interview_round.run)를 686줄로 축소 완료. 나머지 4개 600~800줄 함수가 다음 대상.

### 2. 파라미터 폭발
- `Stage2Context.__init__()`: 48개 인자
- `generate_ensemble()`: 30개
- `patch_with_feedback()`: 29개
- `build_common_context()`: 28개

**진단**: DI Context를 도입했지만, 거대한 God Object를 데이터클래스 하나로 포장한 것에 가까움. 48개 필드 중 어떤 메서드가 어떤 필드를 쓰는지 추적 불가.

### 3. 에러 핸들링 = 복원력 극장
- `except Exception`: 707건 (70%)
- 구체 예외 catch: 310건 (30%)

```python
# 지배적 패턴:
try:
    _something_important()
except Exception as e:
    logging.warning(f"[Tag] 실패 (비치명): {e}")
```

**진단**: 어떤 컴포넌트가 죽어도 시스템이 돌아가는 *것처럼* 보임. 실제로는 advisory 누락, 검증 생략, 불완전 컨텍스트가 Director에 전달됨. "비치명" 태그를 붙여도 그 warning을 보는 사람이 없으면 품질 저하.

### 4. 관측성이 print() 레벨
- 192개 `print()` — 필터링·레벨·구조화 불가
- `logging.warning()`을 INFO 용도로 남용 ("🏆 후보 비교:" 등)
- PerfTimer는 ad-hoc — 중앙 대시보드 없음
- "에피소드당 평균 PASS율", "LLM 호출 평균 지연" 같은 질문에 답 불가

### 5. ~~core→domain 역참조가 DI 무력화~~ → 의도적 설계 (해결 불필요)

**[TF-26 재검증] 전 5건이 함수 내부 lazy import — 순환 참조 방지 의도적 설계.**

```
core/stage4_orchestrator.py  L977-978  → ChiefWriter, ManuscriptValidator  (순환 참조 해소)
core/stage2_orchestrator.py  L101      → StateTracker                      (순환 참조 해소)
core/stage3_orchestrator.py  L208      → StateTracker                      (lazy init, 앱 시작 시 미존재 가능)
core/reference_anchor.py     L102      → BaseAgent                         (임시 에이전트 생성, 예외적 경로)
```

파일 상단 import 시 `core ↔ domain` 순환 발생. 함수 내부 lazy import로 해결된 상태.
DI 컨테이너로 완전 제거 가능하나 현재 패턴으로 충분히 동작하며 **개선 ROI 없음**.

---

## 메타 패턴: 전수조사 트레드밀

```
1차 전수조사 → P0  7건 + P1 17건
2차 전수조사 → P0 10건 + P1 34건
3차 전수조사 → P0 19건 + P1 17건
4차 전수조사 → P0 10건 + P1 18건
5차 전수조사 → P0  7건 + P1 12건
```

5차까지 해도 P0이 계속 나옴. 107K줄 + 707개 broad except 구조에서는 전수조사를 몇 번 해도 새로운 결함이 나옴.

**사이클**: broad except → 버그 은폐 → 간헐적 품질 저하 → 전수조사 → 패치 → 새 기능 추가 (broad except 포함) → 반복

---

## 한 줄 요약

> 테스트와 분할 규율은 상위권이지만, 거대 함수·broad except·print 관측성이라는 3대 구조 부채가 전수조사 트레드밀의 근본 원인이다.

---

## 개선 우선순위 (ROI 순)

1. ~~**거대 함수 2차 분할**: `interview_round.run()` 1,649줄~~ ✅ **B-1-3b 완료** — 686줄로 축소, 5개 메서드 추출 (`_run_advisory_chain`, `_build_cv_context`, `_generate_candidates`, `_process_verdict`, `_handle_reject`). 다음 대상: `process_pass_result()` 814줄, `run_validation()` 694줄.
2. **broad except 정밀화**: 707건 중 advisory 체인(~40건)부터 구체 예외로 전환. `except (json.JSONDecodeError, TimeoutError, ConnectionError)` 등. *(부분 진행: Debt Audit에서 bare except 22건→debug화, TF-16에서 fail-closed 38건, TF-20에서 NPC fail-closed 등 기존 패치 존재)*
3. **structured logging**: print() 제거 → logging 레벨 정상화 (WARNING은 실제 경고만). *(부분 진행: E-1 Silent Pass 16건 보강, 3-Obs Step 1+2 PerfTimer 계측, D2 Memory Observability 경로별 계측, V76 episode_production.jsonl + runtime_audit.jsonl + quality_metrics.jsonl + session_logger 구축 완료. 단, print() 298건·logging.warning 710건(INFO 용도 남용)은 미해결)*

---

## 현재 수치 (B-1-3b 이후)

| 지표 | 이전 | 현재 | 변화 |
|------|------|------|------|
| `interview_round.run()` | 1,649줄 | 686줄 | **-58%** |
| print() 호출 | 192건 | 298건 | +106 (기능 추가 영향) |
| logging 호출 | 1,406건 | 1,411건 | +5 |
| logging.warning | ~700건 | 710건 | INFO 남용 미해결 |
| logging.debug | ~100건 | 119건 | Debt Audit 22건 전환 포함 |
| 구조화 로그 | 0종 | 5종 | episode_production/runtime_audit/quality_metrics/pass_rate_monitor/session JSONL |

---

## 다음 우선순위 제안 (ROI 순)

### Tier 1 — 실전 품질 직결

| # | 작업 | 예상 효과 | 난이도 |
|---|------|----------|--------|
| 1 | **실전 테스트 런** | 실제 에피소드 5~10화 생성, 체감 품질 확인 + 새 버그 발견 | 낮음 |
| 2 | **logging.warning 정상화** | 710건 중 INFO 용도 남용 ~400건 → `logging.info` 전환. 실제 WARNING만 남기면 운영 시 경고 탐지 가능 | 낮음 |
| 3 | **나머지 거대 함수 분할** | `process_pass_result()` 814줄, `run_validation()` 694줄, `finalizer()` 612줄 — B-1-3b 동일 패턴 적용 | 중간 |

### Tier 2 — 구조 부채 감소

| # | 작업 | 예상 효과 | 난이도 |
|---|------|----------|--------|
| 4 | **broad except 구체화 (advisory 체인)** | advisory 40건 → `except (TimeoutError, json.JSONDecodeError, ConnectionError)`. 버그 은폐 차단 | 중간 |
| 5 | **print() → logging 전환** | 298건 중 Stage4 경로(~80건)부터. 필터링·레벨 제어 가능 | 중간 |
| ~~6~~ | ~~core→domain 역참조 제거~~ | **의도적 lazy import (순환 참조 방지) — 해결 불필요** | — |

### Tier 3 — 장기 개선

| # | 작업 | 예상 효과 | 난이도 |
|---|------|----------|--------|
| 7 | **파라미터 축소** | Stage2Context 48필드 → 도메인별 sub-context 분리 | 높음 |
| 8 | **중앙 대시보드** | 5종 JSONL 로그 → 에피소드 PASS율/LLM 지연/비용 시각화 | 높음 |

---

## TF-26 종합 감사 결과 (2026-03-02)

### 감사 범위 (6축)
1. 코드 품질 (TODO/FIXME)
2. 에러 처리 (bare except / silent swallow)
3. SSOT / 매직넘버
4. 테스트 커버리지
5. Dead code
6. LLM 파싱

### 수정 완료 항목
- **작업 1 (Director SSOT)**: `director.py` 4개 상수 → `_threshold()` YAML 참조. `validation.yaml` 3개 값을 코드 실사용값으로 통일 (동작 변경 0).
- **작업 2 (Dead code)**: `config/rules/loot.json`, `config/paths.json` 삭제. `continuity_validator.py` hud_snapshot DB 조회 dead code 제거.
- **작업 3 (로깅 강화)**: `except Exception: pass` 9건 → `logging.debug/warning` 전환 (9파일).
- **작업 4 (타임아웃 YAML)**: `system.yaml` `ensemble_timeouts` 섹션 추가. 5개 클래스 하드코딩 → YAML 참조 + fallback.

### 오탐 확인 — 재감사 불필요
- dead module 3개: 전부 main_a.py 사용 중 (data_collector, pass_rate_monitor, quality_dashboard)
- 미사용 함수 26개: 전부 사용 확인
- PATCH_MODE 프롬프트 3건: YAML 정상 등록 (chief_writer/arc_generator/blueprint_generator.yaml)
- P0 로직 3건: 의도적 설계 (arc_idx cache, _stage3_meta, blueprint None)
- 타임아웃 불일치: 의도적 per-component 설정 (Stage4 600s, Director 투표 90-150s)

### 관찰 유지 항목
- 에러 처리 silent swallow 38건 중 29건: 의도적 패턴 (이차 예외 방지 11건, graceful fallback 13건, 성능 계측 5건)
- 테스트 커버리지 갭: 대형 오케스트레이션 모듈 7개 부족
- stage2_optimizer 테스트 1개만 (관찰)
