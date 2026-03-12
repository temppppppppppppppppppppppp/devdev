# `chaebol_allowance_zero` 실제 재실행 품질 비교

## Scope

- 목적: 하네스 본문 패치 이후 실제 생성 경로를 다시 돌려, 실패본 대비 품질이 얼마나 개선되었는지와 남은 결함이 무엇인지 확인한다.
- 원칙: canonical 산출물은 수정하지 않고 임시 경로에서만 재실행한다.
- 임시 경로:
  - `C:\Users\Public\Documents\ESTsoft\CreatorTemp\codex_chaebol_allowance_zero_rerun`

## Inputs

- 실패 TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- 기존 재시도 TR: `treatments/chaebol_allowance_zero_tr_block_070_draft.json`
- 임시 재실행 TR: `CreatorTemp/.../treatments/chaebol_allowance_zero_tr_block_070_draft.json`
- 실패 BI: `bible/02_bi_chaebol_allowance_zero.json`
- 기존 재시도 BI: `bible/0_bi_chaebol_allowance_zero.json`
- 임시 재실행 BI:
  - 공용 빌더 재실행: 실패
  - 레거시 전용 빌더 재실행본: `CreatorTemp/.../bible/0_bi_chaebol_allowance_zero_legacy_rerun.json`

## Findings

1. 실패본 대비 품질 개선은 실제로 존재한다.
   - 실패 TR 대비 기존 재시도 TR과 임시 재실행 TR 모두 opponent 다양성, weakness 다양성, 본문 밀도에서 큰 폭으로 개선되었다.

2. 하네스 문서 패치가 현재 생성 스크립트 출력에 직접 반영되지는 않았다.
   - 현재 생성 스크립트들은 `docs/blockguide/*.md`를 읽지 않는다.
   - 따라서 이번 실제 재실행은 "보강된 하네스의 효과 측정"이 아니라 "현재 스크립트 스택이 내놓는 결과 재측정"에 가깝다.

3. 기존 재시도 TR과 이번 임시 재실행 TR은 동일하지 않다.
   - 제목 시퀀스는 70/70 동일하다.
   - block hash는 70/70 전부 다르다.
   - opponent 슬롯은 67/70 동일, weakness 슬롯은 64/70 동일이다.
   - 즉 구조는 거의 같은데 문장과 일부 배치가 달라진다. 재현성은 완전 고정 상태가 아니다.

4. 현재 공용 BI 빌더는 최신 Phase 0 최소 계약과 드리프트가 있다.
   - `scripts/build_bi_from_phase0_and_tr.py`는 `partner_location_sector_distribution`를 강제한다.
   - 현재 canonical `chaebol_allowance_zero_phase0_design.json`에는 이 필드가 없다.
   - 따라서 공용 BI 빌더로는 실제 end-to-end 재실행이 막힌다.

5. BI 5-pass는 여전히 source TR 품질을 충분히 구분하지 못한다.
   - 실패 BI, 기존 재시도 BI, 임시 재실행 BI가 모두 5-pass `PASS`였다.
   - 실패 BI도 자기 source TR과 sync만 맞으면 통과한다는 뜻이다.
   - 이는 하네스 문서 보강과 별개로 `scripts/audit_bi_5pass.py` 자체가 아직 source TR density/repetition gate를 강제하지 않는다는 의미다.

## TR Comparison

| Metric | 실패 TR | 기존 재시도 TR | 임시 재실행 TR | 해석 |
|---|---:|---:|---:|---|
| `validate_treatment_structure` | PASS | PASS | PASS | 구조만 보면 셋 다 통과 |
| 블록 수 | 70 | 70 | 70 | 형식 완료 |
| `opponent_unique` | 4 | 31 | 28 | 실패본 대비 대폭 개선, 재실행은 기존 재시도보다 소폭 후퇴 |
| `weakness_unique` | 7 | 70 | 70 | 실패본 대비 대폭 개선 |
| `deal_unique` | 70 | 70 | 70 | 형식상 다양성 유지 |
| `method_unique` | 70 | 70 | 70 | 형식상 다양성 유지 |
| `avg_bundle_chars` | 321.29 | 972.93 | 979.53 | 실패본 대비 약 3.0배 |
| `avg_solution_chars` | 86.50 | 265.01 | 264.74 | 실패본 대비 약 3.1배 |
| top opponent share | 41.4% | 24.3% | 24.3% | 독점 opponent 완화 |
| 10블록 구간 opponent unique | `[2,2,2,2,2,2,3]` | `[8,6,5,5,5,6,5]` | `[5,6,5,5,5,6,5]` | 초반 다양성은 기존 재시도본이 더 좋음 |
| one-sentence-like solution blocks | 70 | 3 | 0 | 실패본은 사실상 전 블록 단문 템플릿 |
| top solution tail-20 repetition | 14 | 57 | 62 | 실패본보다 길이는 늘었지만 cadence 반복은 여전히 심함 |
| UTF-8 이상 | 없음 | 없음 | 없음 | 인코딩 이상 없음 |

## TR Interpretation

- 실패본의 핵심 결함이었던 `2인 rotation`, `weakness 복붙`, `짧은 solution`, `낮은 bundle density`는 실제로 해소되었다.
- 다만 현재 재실행 TR은 기존 재시도 TR보다 낫다고 보기 어렵다.
- 오히려 다음 항목은 퇴보했다.
  - `opponent_unique`: `31 -> 28`
  - 초반 10블록 diversity: `8 -> 5`
  - tail-20 cadence repetition: `57 -> 62`
- 즉 현재 자동 생성기는 실패본을 벗어날 정도의 품질은 내지만, 이미 존재하는 재시도본을 다시 넘어서지는 못했다.

## TR Reproducibility Check

- 기존 재시도 TR과 임시 재실행 TR 비교:
  - 동일 title sequence: `True`
  - 동일 block hash 개수: `0 / 70`
  - 동일 opponent 슬롯: `67 / 70`
  - 동일 weakness 슬롯: `64 / 70`
- 해석:
  - 생성 골격은 매우 비슷하다.
  - 그러나 문장과 일부 배치가 전 블록에 걸쳐 다르다.
  - 현재 스택은 "대체로 비슷한 draft"는 재생산하지만 "완전히 같은 golden draft"를 재생산하지는 못한다.

## BI Comparison

| Metric | 실패 BI | 기존 재시도 BI | 임시 재실행 BI(legacy) | 해석 |
|---|---:|---:|---:|---|
| 5-pass 결과 | PASS | PASS | PASS | 현재 BI audit는 셋을 모두 통과시킴 |
| `plot_roadmap_len` | 70 | 70 | 70 | 모두 충족 |
| title sequence match with source TR | True | True | True | 모두 충족 |
| roadmap hash match with source TR | True | True | True | 모두 충족 |
| `portfolio_history_len` | 8 | 8 | 8 | 체크포인트형 HUD |
| `portfolio_history` sync | True | True | True | source TR과 동기화 |
| final assets | `1320억` | `1318억` | `1320억` | TR 자본 곡선 반영 |
| UTF-8 이상 | 없음 | 없음 | 없음 | 인코딩 이상 없음 |

## BI Interpretation

- BI는 현재도 "source TR을 잘 요약하면 통과"하는 구조다.
- 그래서 실패 BI도 PASS, 개선 BI도 PASS다.
- 즉 BI layer는 품질 분기점이 아니라 sync layer로 작동하고 있다.
- 이번 실험에서도 BI보다 TR이 실제 품질 차이를 만든다.

## BI Build Path Finding

### 1. 공용 빌더 상태

- `scripts/build_bi_from_phase0_and_tr.py`로 실제 재실행을 시도했다.
- 결과: 실패
- 실패 원인:
  - `Phase0 design missing field: partner_location_sector_distribution`

### 2. 의미

- 하네스 문서에서는 이미 Phase 0 최소 계약이 작아졌다.
- 하지만 공용 BI 빌더는 구 계약을 여전히 강제한다.
- 즉 문서와 생성 코드가 아직 정렬되지 않았다.

### 3. 우회 실행

- 실제 chaebol 전용 레거시 빌더 `build_chaebol_allowance_zero_assets.py`의 `build_phase0()` + `build_bible()`로 임시 BI 재실행본을 만들었다.
- 이 경로는 성공했다.
- 다만 이는 "최신 공용 스택" 검증이 아니라 "레거시 개별 자산 생성기" 검증이다.

## Improvement Points

1. 생성 스크립트가 새 하네스 규칙을 실제로 읽게 해야 한다.
   - 지금은 문서만 친절해졌고 생성기는 그대로다.
   - `pattern feedback`, `arc allocation`, `weakness pool`, `Gemini-safe batch size`를 생성 입력으로 연결해야 한다.

2. `generate_chaebol_allowance_zero_retry.py`에 tail cadence 억제 규칙을 넣어야 한다.
   - 현재 `top solution tail-20 repetition`이 `57`, 재실행은 `62`다.
   - 실패본의 짧은 단문 템플릿과는 다른 종류지만, 여전히 강한 cadence 반복이다.

3. 초반 10블록 opponent 다양성 유지 로직이 필요하다.
   - 기존 재시도본은 초반 10블록 `8명`
   - 임시 재실행본은 초반 10블록 `5명`
   - 초반 훅 구간 diversity가 자동 재실행에서 다시 줄었다.

4. 공용 BI 빌더를 최신 Phase 0 계약에 맞춰야 한다.
   - `partner_location_sector_distribution`, `capital_curve`, `defeat_blocks` 구 필드 강제를 완화하거나 adapter를 넣어야 한다.

5. `scripts/audit_bi_5pass.py`를 source TR quality gate와 연결해야 한다.
   - 실패 BI도 PASS하는 한, BI audit는 품질 감별기가 아니다.
   - 최소한 source TR의 `avg_bundle_chars`, repetition fail, density fail 결과를 재인용해야 한다.

6. golden draft 재현성 기준을 따로 세워야 한다.
   - 지금은 같은 title sequence와 거의 같은 opponent 분포를 재생산해도, block hash는 `0 / 70` 동일이다.
   - "동일성"과 "품질 허용 오차"를 분리 정의할 필요가 있다.

## Final Verdict

- 실패본 대비 개선은 `실제`로 확인됐다.
- 다만 이번 하네스 패치가 자동 생성 품질을 직접 끌어올렸다고 보기는 어렵다.
- 이유는 현재 생성 스크립트와 BI audit가 아직 새 하네스 계약을 소비하지 않기 때문이다.
- 현재 상태를 한 줄로 정리하면:
  - `실패본 -> 재시도본`: 분명한 개선
  - `기존 재시도본 -> 실제 재실행본`: 대등하거나 일부 퇴보
  - `문서 보강 -> 자동 생성 품질 상승`: 아직 미연동
