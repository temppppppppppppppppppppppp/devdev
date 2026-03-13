# Treatment 배치 하네스 운영 문서

작성일: 2026-03-09  
대상: `treatments/*.json` 로 들어갈 block 포함 TR JSON 생산  
목적: 장문 가이드의 규칙을 실제 운영 절차로 압축하고, 저지능 모델도 따라올 수 있는 배치 하네스를 고정한다.

## 1. 이 문서가 추가로 필요한 이유

`docs/2026-03-09/treatment-block-production-guide.md`는 규칙이 충분히 많고 정확하지만, 실제 작업자가 바로 실행하기에는 너무 길다.  
또한 현재 코드 기준으로는 아래 문제가 있다.

- `tools/treatment_builder.py`는 60블록 기준의 구형 설계다.
- Phase 2와 Phase 3가 분리되어 있어서, 생성 시점에 자본/NPC/복선 연속성이 강제되지 않는다.
- `scripts/repair_tr_korean_utf8.py`는 복구용 스크립트이지 생산용 하네스가 아니다.
  - 템플릿 회전, 동일 leverage 세트, 고정 callback 패턴을 대량 주입하기 쉽다.
  - 새 생산 파이프라인의 기본 생성기로 사용하면 안 된다.

결론: 새 생산은 `한 번에 많이 생성`이 아니라 `작게 생성하고 Python이 강제`하는 방식으로 고정해야 한다.

## 2. 공식 생산 단위

기본 단위는 배치다.

- 저지능 모델 (`flash`급): 3블록
- 중간 이상 모델 (`pro`, `sonnet`): 5블록까지 가능
- 10블록 이상은 고지능 모델 + 수동 감리 전제일 때만 허용

절대 금지:

- 70블록 단일 호출
- 생성과 검증을 한 번에 요구하는 호출
- 모델이 `capital_before`, `relationship_delta.before`를 임의 작성하게 방치하는 것

## 3. 생산 원칙

이번 문서 기준의 권한 분리는 아래와 같다.

- 모델 책임
  - 사건, 갈등, 해결, 감정 비트, 복선 설치/회수의 서사 작성
  - 각 블록 간 차별화
- Python 책임
  - `block_id` 정렬
  - `capital_before = 직전 capital_after`
  - `capital_delta = after - before`
  - `profit_loss` 갱신
  - `relationship_delta.before = 직전 after`
  - 회귀/빙의 작품의 `is_regressor = true`
- 작업자 책임
  - 배치 목표(title) 확인
  - 후보 JSON만 따로 저장
  - `check` 통과 전 merge 금지

## 4. 이번에 추가한 하네스

새 CLI:

- `scripts/tr_batch_harness.py`

서브커맨드:

- `prompt`
  - 직전 블록 요약, NPC 추적표, OPEN 복선 원장, 배치 목표를 묶어서 프롬프트 파일을 만든다.
- `check`
  - 후보 JSON 배치를 검사하고, 안전한 항목만 자동 보정한다.
- `merge`
  - `check`를 다시 수행한 뒤 draft에 병합한다.

핵심 차별점:

- 모델은 배치 단위 창작만 한다.
- Python은 수치/연속성만 강제한다.
- BI를 넣더라도 title 중심으로만 쓰고, 기존 defective content를 그대로 베끼지 않게 막는다.

## 5. 권장 파일 흐름

예시 작품: `dynasty_heir_possession`

1. 프롬프트 생성

```powershell
python -X utf8 scripts/tr_batch_harness.py prompt `
  --roadmap bible\a_재벌가빙의후승계전_bi.json `
  --start 1 `
  --batch-size 3 `
  --mode flash `
  --output docs\2026-03-09\dynasty_heir_batch_001_prompt.md
```

2. 모델 호출

- 위 프롬프트를 저지능 모델에 넣는다.
- 모델 출력 중 `사전 선언`, `차이 행렬`, `복선 원장`은 사람이 검토용으로 보고,
  실제 저장 파일에는 `JSON 배열`만 남긴다.

3. 후보 검사

```powershell
python -X utf8 scripts/tr_batch_harness.py check `
  --candidate treatments\dynasty_heir_batch_001_candidate.json `
  --roadmap bible\a_재벌가빙의후승계전_bi.json `
  --start 1 `
  --batch-size 3 `
  --autofix `
  --fixed-output treatments\dynasty_heir_batch_001_fixed.json `
  --report treatments\audit_reports\dynasty_heir_batch_001_check.md
```

4. draft 병합

```powershell
python -X utf8 scripts/tr_batch_harness.py merge `
  --draft treatments\dynasty_heir_possession_tr_block_070_draft.json `
  --candidate treatments\dynasty_heir_batch_001_fixed.json `
  --roadmap bible\a_재벌가빙의후승계전_bi.json `
  --start 1 `
  --batch-size 3 `
  --report treatments\audit_reports\dynasty_heir_batch_001_merge.md
```

5. 다음 배치 반복

- `--start 4`, `--start 7`, `--start 10` 식으로 순차 진행한다.
- draft가 없는 신작은 `start 1`부터 시작한다.

## 6. `check`가 강제하는 핵심 규칙

P0:

- `block_id` 순서
- `capital_before` 연속성
- `capital_delta` 계산 일치
- `regression_type in {빙의, 회귀} -> is_regressor = true`
- `relationship_delta.before` 이월

P1:

- roadmap title 불일치
- 한국어 비율 부족
- 영문/기계 템플릿
- 기계식 callback
- `emotional_beat.type` 연속 반복
- `deal_type` 최근 3블록 재등장
- 관계 변화 없음
- 명시된 복선 목표 블록에서 callback 회수 실패

P2:

- 코드형 값 (`plan_01`, `type_1`, `_B01`)
- `location` 최근 15블록 재등장
- `leverage_used` 동일 세트 3회 이상
- OPEN 복선 10개 초과
- 배치 전부 상승만 존재

## 7. `autofix`로 고쳐도 되는 항목과 안 되는 항목

자동 보정 허용:

- `block_id`
- `genre_ext.capital_before`
- `genre_ext.capital_delta`
- `genre_ext.profit_loss`
- `relationship_delta.before`
- `regression_ext.is_regressor`

자동 보정 금지:

- `content.*`
- `stakes`
- `foreshadow`
- `callback`
- `deal_type`
- `location`
- `leverage_used`
- `method`, `success_pattern`, `execution_doctrine`

이 구분이 중요한 이유는, 수치/연속성은 기계적으로 맞출 수 있지만 서사 필드는 모델이 다시 써야 하기 때문이다.

## 8. 저지능 모델 운용 규약

저지능 모델에는 아래만 고정한다.

- 배치 3블록
- 사전 선언 3항목
- JSON
- 차이 행렬
- 복선 원장 업데이트

작업자가 지켜야 할 추가 규칙:

- 모델에게 기존 70블록 전체 JSON을 넣지 말 것
- 직전 3블록 + NPC 추적표 + OPEN 복선만 줄 것
- `roadmap`를 넣더라도 title만 기준점으로 삼을 것
- 후보 저장 파일에는 자연어 설명을 남기지 말고 JSON만 남길 것

## 9. 기존 가이드와의 관계

우선순위는 아래 순서다.

1. `docs/2026-03-09/treatment-block-production-guide.md`
2. 이 운영 문서
3. `scripts/tr_batch_harness.py`의 실제 검사 결과

해석 원칙:

- 장문 가이드는 설계 원칙의 원본이다.
- 이 문서는 실무 절차로 압축한 것이다.
- 실제 merge 가능 여부는 하네스 검사 결과를 최종 기준으로 삼는다.

## 10. 실무 판단

새 production 루프는 `수동 감리 + 저지능 모델`을 버리는 방향이 아니라,  
저지능 모델도 배치 단위로 묶어서 써먹을 수 있게 만드는 방향으로 가야 한다.

즉, 목표는 “좋은 모델만 쓰면 된다”가 아니라 아래다.

- 작은 배치
- 강한 입력 형식
- Python 연속성 강제
- merge 전 게이트

이 4개가 지켜지면 `treatments/` 아래 TR JSON의 품질은 지금보다 훨씬 안정적으로 관리할 수 있다.
