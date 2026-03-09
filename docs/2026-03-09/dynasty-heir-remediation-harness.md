# 왕조의 후계자 빙의 Treatment 개선 하네스

> 인코딩: UTF-8  
> 작성일: 2026-03-09  
> 대상: `treatments/dynasty_heir_possession_tr_block_070_draft.json`  
> 목적: 재감리 결과(P0/P1/P2)를 반영한 전용 개선 하네스 정의

---

## 1. 적용 범위

- 파일 단위: `dynasty_heir_possession_tr_block_070_draft.json` 70블록
- 파이프라인 단위: `tools/treatment_builder.py` 기반 생성/보정/감리 전 과정
- 우선순위:
1. P0 구조 모순 제거
2. P1 서사 모순 제거
3. P2 품질 개선

---

## 2. 재감리 결함 요약

### P0

1. `regression_ext.regression_type = "빙의"`인데 `is_regressor = false` 전량 고정

### P1

1. `relationship_delta.before/after` 영문 고정 문장
2. `foreshadow/callback` 영문 기계 템플릿 + 실질 회수 단절
3. 페이즈 내 NPC 관계 정체(`before == after` 반복)
4. `context/event_villain/solution` 섹터명 치환형 순환
5. `leverage_used` 4종 고정
6. `location` 10개 정확 주기 순환
7. `execution_doctrine` 전량 동일

### P2

1. 코드형 식별자 스타일(`*_plan_01`, `*_type_1`, `*_B01`)
2. `reward` 영문
3. 섹터 8종 완전 균등 로테이션
4. `global_partner` 단일 고정

---

## 3. 즉시 교정 하네스 (Draft Hotfix)

### 3.1 P0 강제 규칙

1. `regression_type`가 `빙의` 또는 `회귀`면 `is_regressor = true` 강제
2. `timeline_knowledge`, `butterfly_effect`, `death_flag`가 존재하는데 `is_regressor = false`면 오류
3. 위 규칙 위반 시 블록 단위가 아니라 파일 전체 REJECT

### 3.2 언어/형식 강제 규칙

1. 아래 필드는 한국어 비율 80% 미만이면 위반
- `relationship_delta.before/after`
- `foreshadow[]`
- `callback[]`
- `content.reward`
- `genre_ext.method`
- `genre_ext.success_pattern`
- `regression_ext.regression_hint.slip_up`

2. 코드형 토큰 금지(정규식 검출)
- `_B\d{2,}`
- `_plan_\d+`
- `_type_\d+`
- `anomaly_\d+`
- `protocol_\d+`

3. 영어 문장 고정 템플릿 금지
- `Deferred setup for Block`
- `carry-over was converted into leverage`
- `Capital moved from`

### 3.3 NPC 관계 규칙

1. `relationship_delta.before(N) == relationship_delta.after(N-1)` NPC별 강제
2. 동일 NPC의 `before == after`가 2블록 연속 발생하면 위반
3. 페이즈(10블록) 내 관계 상태가 단일 문장으로 4회 이상 반복되면 위반
4. 전체 70블록 기준 최소 8명 NPC 유지

### 3.4 복선/회수 규칙

1. `foreshadow` 항목마다 `payoff_block`을 명시적으로 매핑
2. `payoff_block`의 `callback`에 seed 사건 키워드 1개 이상 포함
3. 시드 후 10블록 이상 지연 회수 복선 최소 5개
4. 매핑 실패 복선 1개라도 있으면 P1 위반

### 3.5 다양성 규칙

1. `location`:
- 전체 8개 이상
- 동일 장소가 3블록 이내 재등장 금지
- 10블록 정확 주기 반복 검출 시 위반

2. `leverage_used`:
- 블록당 최소 1개 신규 항목
- 동일 4항목 세트가 3회 이상 반복되면 위반

3. `global_partner.name`:
- 전체 최소 3개
- 동일 파트너 연속 8블록 초과 금지

4. `business_sector`:
- 8종 완전 균등(편차 0) 분포는 오히려 경고
- 허용 분포 편차: 최대/최소 비율 1.8 이하

---

## 4. 생성기 하네스 보강 (Builder-Level)

### 4.1 Phase 0 추가 필수

아래 아크 시트를 먼저 생성한다.

1. 적대자 전환 계획(최소 3세력, 전환 블록 포함)
2. NPC 등퇴장 계획(최소 8명, 관계 전환 이벤트 포함)
3. 복선-회수 맵(시드/힌트/회수 블록)
4. 패배 블록 계획(최소 7개)
5. 파트너/장소/섹터 분포 계획

### 4.2 Phase 1 프롬프트 금지 조건

1. 섹터명만 바꾼 문장 재사용 금지
2. 직전 블록 callback 문장 패턴 복붙 금지
3. 페이즈 내 `before == after` 관계 고정 금지
4. 10블록 주기 완전 반복 구조 금지

### 4.3 Phase 2 메타 채움

`prev_blocks[-5:]` 컨텍스트를 주입해 다음을 강제한다.

1. `capital_before = prev.capital_after`
2. `relationship_delta.before = prev.after`
3. `callback`은 `foreshadow_map`의 예정 회수 항목만 사용

---

## 5. 자동 검증 스펙 (Python)

```python
def validate_dynasty_heir(blocks: list[dict]) -> list[dict]:
    """
    반환 형식:
    [{"block": 12, "severity": "P1", "rule": "REL-FROZEN", "msg": "..."}]
    """
```

### 5.1 필수 검증 규칙

1. `REG-001` (P0): regression_type/is_regressor 정합
2. `LANG-001` (P1): 한국어 비율 검사
3. `TPL-001` (P1): 금지 템플릿 문자열 검사
4. `CODE-001` (P2): 코드형 토큰 검사
5. `REL-001` (P0): NPC before/after 연속성
6. `REL-002` (P1): 관계 동결 검사
7. `FS-001` (P1): foreshadow-payoff 매핑 검사
8. `LOC-001` (P1): 위치 단주기 반복 검사
9. `LEV-001` (P1): leverage_used 고정 세트 반복 검사
10. `GP-001` (P2): 글로벌 파트너 다양성 검사

### 5.2 반복 탐지 규칙

문장 유사도(코사인 또는 n-gram Jaccard)로 아래를 검출한다.

1. `context/event_villain/solution` 유사도 0.92 이상 3회 초과
2. 같은 문장에서 `business_sector` 토큰만 치환된 패턴

---

## 6. 3-Pass 재감리 절차

### 1차(전수)

1. 자동 검증 규칙 전부 실행
2. P0/P1/P2 분류표 생성
3. 위반 블록 인덱스 확정

### 2차(오탐 제거)

1. 장기 복선으로 의도된 지연인지 검토
2. 의도적 저강도 블록(quiet block) 유지 여부 검토
3. 규칙 완화 사유를 코멘트로 기록

### 3차(최종 확정)

1. 확정 위반만 수정 반영
2. 수정 후 자동검증 재실행
3. 통과 리포트 생성

---

## 7. 출고 게이트 (합격 조건)

### P0 게이트

- `REG-001`, `REL-001`, 자본 연속성 위반 0건

### P1 게이트

- 영문 템플릿 0건
- 복선 미회수 0건
- 관계 동결(연속 2회 이상) 0건
- 위치 단주기 반복 0건

### P2 게이트

- 코드형 토큰 0건
- reward 영문화 0건
- global_partner 최소 3개

---

## 8. 리포트 출력 형식

`treatments/audit_reports/dynasty_heir_remediation_report.md`

```markdown
# Dynasty Heir Remediation Report

## Summary
- P0: 0
- P1: 0
- P2: 0

## Fixed Issues
| rule | count_before | count_after |
|------|--------------|-------------|
| REG-001 | 70 | 0 |
| LANG-001 | 70 | 0 |
...
```

---

## 9. 즉시 실행 권고

1. 현재 드래프트에 `REG-001`, `LANG-001`, `FS-001` 먼저 적용
2. 이후 `TPL-001`, `REL-002`, `LOC-001` 적용
3. 마지막으로 `GP-001`, `CODE-001`로 품질 정리

