# Codex Order: Feature Activation Audit (TF 병렬 운영판)

> 목적: 기능 활성화 실태를 로그/JSONL 기준으로 감사하고, 숫자 사실만 보고한다.
> 출력(고정): `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/feature-activation-audit-result.md`
> 분석 방식: Python `open()` + 문자열 처리만 사용한다.
> 자동 검색 도구 금지: `rg`, `grep`, `fgrep`, `findstr`, `Select-String`.

---

## 0) 강제 제약 (반드시 준수)

- 절대 금지 #1: 코드 수정, 설정 변경, 파일 삭제, 파일 이동, 파일명 변경.
- 절대 금지 #2: 분석 대상 원본 파일(`projects/000000/logs/*`) 내용 변경.
- 누락 파일은 `파일 없음`으로 기록하고 다음 단계로 진행.
- JSON 파싱 실패 라인은 건너뛰고 실패 건수만 집계.
- 결론 섹션은 숫자 기반 사실만 작성한다. 의견/추정/개선 제안/리팩터링 제안 금지.

---

## 1) TF 구성 (메인 + 서브 에이전트 병렬)

- Main Agent (총괄)
  - 오더 준수 검증, 서브 태스크 병렬 실행, 최종 보고서 병합.
  - 최종 문서에서 수치 충돌/중복 제거.
- Sub-Agent A (Advisory/VecMemory)
  - 세션 로그 8개에서 advisory 발화/미발화 및 VecMemory 히트율 집계.
- Sub-Agent B (합격률/시도 통계)
  - `episode_production.jsonl`, `quality_metrics.jsonl`에서 1차 시도 기준 통계 집계.
- Sub-Agent C (Director 호출 구조)
  - 세션 로그 8개에서 Director `prompt_len`/`response_len` 분포 집계.

병렬 원칙:
- A/B/C는 서로 독립 계산 후 Main Agent가 결과만 병합한다.
- 자동화 검색 커맨드 없이 파일을 순차 읽기(`open`, `readline`/반복)로 처리한다.

---

## 2) 분석 대상 파일

세션 로그:
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_133915.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_142438.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_144516.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_144702.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_145148.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_150048.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_150114.log`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/session_20260303_151852.log`

메트릭 파일:
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/episode_production.jsonl`
- `C:/Users/wjjo/Desktop/글도비/projects/000000/logs/quality_metrics.jsonl`

---

## 3) Sub-Agent A 작업: Advisory Chain + VecMemory

### 3-1. Advisory 발화 탐지

각 세션 로그를 줄 단위로 읽고 아래 패턴의 포함 여부를 집계한다.

| 모듈 | 발화 탐지 문자열 | 비고 |
|---|---|---|
| FlashbackVerifier | `FlashbackVerifier->Director` | 포함 시 발화 1건 |
| NpcDriftAdvisor | `NpcDriftAdvisor->Director` | 포함 시 발화 1건 |
| InfoParadoxChecker | `InfoParadoxChecker->Director` | 포함 시 발화 1건 |
| TruthGate | `TruthGate->Director` | 포함 시 발화 1건 |
| RelationshipDriftAdvisor | `RelationshipDrift` 또는 `RelDrift` + `Director` 동시 포함 | 동시 포함 줄만 발화 |
| LongTermRepetitionAdvisor | `LongTermRep` 또는 `장기 반복` + `Director` 동시 포함 | 동시 포함 줄만 발화 |
| NumericDriftAdvisor | `NumericDrift` 또는 `수치 추적` + `Director` 동시 포함 | 동시 포함 줄만 발화 |

### 3-2. NpcDriftAdvisor LLM 호출 추정

- `NpcDriftAdvisor` 포함 줄의 총건수 = 총 호출 추정.
- `NpcDriftAdvisor->Director` 포함 줄의 건수 = 실제 발화 건수.
- `(총 호출 추정) - (실제 발화)` = 발화 없이 소모된 호출 추정.

### 3-3. VecMemory 히트율

`[VecMem]` 포함 줄만 대상으로:
- `hits=0` 이면 미스.
- `hits=<숫자>`에서 숫자 1 이상이면 히트.
- `hits=0` 줄의 `q='...'`에서 앞 15자 추출해 쿼리 타입 집계.

---

## 4) Sub-Agent B 작업: 합격률 통계

### 4-1. 키 자동 탐색 규칙 (필드명이 다를 때)

각 JSON 레코드에서 아래 후보 키를 우선순위 순서로 탐색한다.
- 에피소드 번호: `ep_num` → `episode` → `episode_number`
- 판정: `verdict` → `result` → `decision`
- 점수: `score`
- 시도 회차: `attempt` → `round` (없으면 기본값 1)

탐색 규칙:
- 후보 키가 존재하고 값이 비어있지 않으면 채택.
- 전부 없으면 해당 레코드를 `필드 누락`으로 집계하고 제외.
- 어떤 키를 채택했는지 최종 보고서에 `실제 사용 키`로 기록.

### 4-2. 집계 규칙

`episode_production.jsonl`:
- 줄 단위 JSON 파싱.
- 1차 시도 기준만 사용 (시도 키의 최소값을 1차로 간주. 예: `round=0`부터 시작하면 `0`이 1차).
- PASS, PASS_WITH_FIX = 합격 / REJECT = 불합격.
- 전체 1차 합격률(%).
- 구간별 합격률: 1~10, 11~20, 21~25.
- 실패(불합격) 최다 에피소드 상위 3개.

`quality_metrics.jsonl`:
- 줄 단위 JSON 파싱.
- score 분포(최소/최대/평균, 필요 시 구간별 빈도) 추가 기록.

---

## 5) Sub-Agent C 작업: Director 호출 구조

세션 로그에서:
- `call_start agent=Director` 포함 줄의 `prompt_len=<숫자>` 추출.
- `call_success agent=Director` 포함 줄의 `response_len=<숫자>` 추출.

분류:
- `< 1000`: 매우 짧음
- `1000~4999`: 소형
- `5000~19999`: 중형
- `>= 20000`: 대형(full fallback 가능성)

추가 집계:
- `response_len=2` 건수 별도 집계.
- 가능하면 동일 에피소드/근접 시점 기준으로 start-success를 매칭하고, 매칭 실패 건수도 기록.

---

## 6) 최종 출력 포맷 (고정)

아래 경로에만 작성:
- `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/feature-activation-audit-result.md`

문서 구조:

```markdown
# Feature Activation Audit 결과

> 분석일: 2026-03-04
> 대상: projects/000000, 세션 로그 8개

## 1. Advisory Chain 활성화 현황

| 모듈 | 발화 건수 | 호출/추정 | 비고 |
|---|---:|---:|---|

## 2. VecMemory 히트율

| 쿼리 타입(앞 15자) | 히트 | 미스 | 히트율 |
|---|---:|---:|---:|

## 3. 합격률 통계 (1차 시도 기준)

| 구간 | 1차 합격률 |
|---|---:|
| 1~10 | N% |
| 11~20 | N% |
| 21~25 | N% |

실패 최다 에피소드 TOP3: ...
실제 사용 키: episode=..., verdict=..., attempt=...

## 4. Director 호출 분포

| prompt_len 구간 | 건수 | response_len=2 건수 |
|---|---:|---:|

## 5. 결론 (숫자 기반 사실만)

- 발화 0건 모듈: ...
- VecMemory 히트율 최저 쿼리 타입: ...
- response_len=2 비율 최고 구간: ...
- JSON 파싱 실패: N건 / 필드 누락: N건 / 매칭 실패: N건
```

---

## 7) 오더 준수 체크리스트

- [ ] 원본 코드/설정/로그 파일 수정 없음
- [ ] 자동 검색 커맨드(`rg`/`grep`/`fgrep` 등) 사용 없음
- [ ] Python `open()` + 문자열 처리 기반 분석 수행
- [ ] 키 자동 탐색 및 누락 처리 기록
- [ ] 결론 섹션에 의견/개선안 없음
- [ ] 출력 파일 경로 고정 준수
