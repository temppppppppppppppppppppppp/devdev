# Treatment 블록 생산 하네스 v2 (통합 실전판)

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-09
> 근거: `treatment-block-production-guide.md` + `dynasty-heir-remediation-harness.md` + 8작품 560블록 전수 감사
> 목적: **모든 지능 수준의 모델이 골든루트급 Treatment JSON을 생산**할 수 있는 완전한 하네스
> 출력: `treatments/{작품명}_tr_block_070_draft.json`
> 선행 문서: `blockguide-integrated-order.md`

---

## 0A. 초저지능 LLM용 빠른 시작

이 문서는 **`Phase 0`가 이미 있는 상태에서 TR을 생산할 때만** 쓴다.
사용자가 작품명, `work_id`, 짧은 기획안, `다음 스텝`만 던져도 아래 순서를 먼저 수행한다.

1. `blockguide-integrated-order.md`를 **UTF-8로 먼저 읽는다.**
2. `treatment-planning-harness.md`를 다시 확인해 지금이 기획 단계인지 생산 단계인지 판단한다.
3. 이 문서를 **UTF-8로 다시 읽는다.**
4. `treatments/{work_id}_phase0_design.json`과 직전 `candidate/fixed/draft`를 재오픈한다.
5. `Phase 0`가 없으면 이 문서를 실행하지 말고 planning 단계로 되돌린다.
6. 생산 단계가 맞으면 기본 배치를 **가장 작은 안전 단위**로 잡는다.
   - 확신이 낮으면 3블록
   - 중간 수준이면 5블록
   - 충분히 안정적일 때만 10블록
7. 각 배치에서 해야 할 일은 항상 같다.
   - 사전 선언
   - 블록 생성
   - 절대 금지 규칙 자가 점검
   - Python 교정/검증
   - 위반 시 같은 배치만 재생성
8. `70블록 draft`가 완성되면 바로 BI를 상상하지 말고, 먼저 감리와 출고 게이트를 통과시킨다.
9. 감리 통과 뒤에는 `bi-production-harness-v1.md`로 인계한다.

금지:

- `Phase 0` 없이 블록부터 쓰기
- 안정성 확인 없이 10블록, 20블록을 한꺼번에 밀어붙이기
- 감리 전 `draft`를 완성본으로 선언하기
- 기억에 의존해 직전 배치 상태를 재구성하기

## 0. 왜 이 문서가 필요한가

### 0.1 근본 원인

기존 `treatment_builder.py`의 3-Phase 구조는 다음 3가지 구조적 결함을 갖는다:

1. **Phase 1에서 60블록 일괄 생성** → LLM이 "안전한 패턴"으로 수렴 (균등 분배, 템플릿 복붙)
2. **Phase 3 메타데이터가 블록 간 독립** → NPC 관계 리셋, 자본 불연속
3. **검증 루프 부재** → 생성 후 정합성 미검사

**결과**: 8작품 전량에서 동일한 8대 결함 패턴 100% 공유.

### 0.2 8대 결함 (1세대: Pattern A~H)

| ID | 패턴 | 8작품 공유율 | 심각도 |
|----|------|-------------|--------|
| A | capital_before ≠ prev capital_after (68/70) | 100% | P0 |
| B | NPC 2명 고정, before 매 블록 리셋 | 100% | P0 |
| C | 적대자 단일 고정 (70블록 동일) | 100% | P1 |
| D | emotional_beat 4종×3강도 수학적 순환 | 100% | P1 |
| E | deal_type 5종×14회 균등 분배 | 100% | P1 |
| F | duration 전량 "7일" 고정 | 100% | P2 |
| G | solution/callback/success_pattern 템플릿 반복 | 100% | P1 |
| H | 빙의 death_flag/slip_up 전량 동일 | 100% (빙의) | P1 |

### 0.3 2세대 결함 (Pattern I~P) — dynasty_heir 심층 평가 기반

1세대 해결 후에도 "정교한 템플릿 반복"이 나타남:

| ID | 패턴 | 심각도 |
|----|------|--------|
| I | 영문 혼용 (relationship_delta/foreshadow/callback/reward) | P1 |
| J | 코드형 값 (method="execution_plan_01", death_flag="systemic_risk_type_1") | P2 |
| K | 10문장 로테이션 (섹터명만 교체하며 순환) | P1 |
| L | leverage_used 70블록 전량 동일 4항목 고정 | P1 |
| M | is_regressor=false인데 regression_type="빙의" (논리 모순) | P0 |
| N | 복선-회수 단절 (foreshadow 지목 블록에서 callback 회수 안 함) | P1 |
| O | 페이즈 내 NPC 동결 (2명×10블록, before=after) | P1 |
| P | 장소 10곳 10블록 주기 정확 순환 | P2 |

---

## 1. 생산 아키텍처: 5-Phase + 3-Pass 감리

```
Phase 0: 대단원 아크 설계 ─────────────────────── 1회 LLM
  ↓ (서사 골격: 적대자 변천, NPC 타임라인, 자본 곡선, 복선 맵)
Phase 1: 대단원별 블록 생성 ────────────────────── N회 LLM
  ↓ (10블록 또는 3블록 배치, 사전 선언 + Anti-Shortcut)
Phase 2: Python 자동 교정 ─────────────────────── 0회 LLM
  ↓ (자본 연속성, NPC before 이월, delta 재계산)
Phase 3: Python 자동 검증 + LLM 재생성 ─────────── 위반 블록만
  ↓ (A~P 16개 패턴 탐지, 위반 블록만 재생성)
Phase 4: 3-Pass 감리 ──────────────────────────── 3회 LLM
  (1차 전수 → 2차 오탐 제거 → 3차 최종 확정)
```

### 1.1 대화형 순차 진행 프로토콜 (`다음 스텝` 루프)

실전에서는 사용자가 긴 운영 지시 대신 `다음 스텝`만 반복하는 경우가 많다.
이 하네스는 그 상황을 **정상 경로**로 간주한다.

운영 규칙:

1. `다음 스텝`은 “직전 산출물이 끝났으니 **다음 필수 출력 단위 1개를 계속 생성하라**”는 승인으로 해석한다.
2. 한 턴에 전진하는 단위는 반드시 1개다.
   - Phase 0 시트 1묶음
   - Block 1~10, 11~20 같은 10블록 배치 1개
   - 검수/merge 1회
   - TR 완료 후 BI handoff 1회
3. 사용자가 새 방향을 주지 않으면, 이미 확정된 Phase 0와 직전 배치를 기준으로 **다음 미완료 구간**으로 이동한다.
4. `70블록 draft`가 끝난 뒤 사용자가 다시 `다음 스텝`을 입력하면,
   기본 동작은 `검수 → BI 하네스 인계`다.
5. 이 프로토콜에서는 “질문부터 하기”가 아니라 “다음 단위를 실제로 생성하기”가 기본값이다.

권장 진행표:

| 사용자 입력 | 기본 행동 | 산출물 |
| ----------- | --------- | ------ |
| `다음 스텝` (기획 직후) | Phase 0 JSON 또는 1대단원 상세 스타트 작성 | Phase 0 설계 시트 |
| `다음 스텝` (생산 시작) | 다음 10블록 배치 생성 | `batch_00N_candidate.json` |
| `다음 스텝` (배치 완료 후) | 다음 10블록 배치 생성 | 다음 candidate/fixed |
| `다음 스텝` (61~70 완료 후) | 전량 merge/최종 draft 정리 | `tr_block_070_draft.json` |
| `다음 스텝` (draft 확정 후) | BI 하네스로 handoff | `0_bi_{work_id}.json` 또는 BI 감리 |

정지 조건:

- 사용자가 명시적으로 방향을 바꾸는 경우
- 필수 SSOT(`Phase 0`, 직전 `draft`)가 없거나 손상된 경우
- 감리에서 P0가 떠서 다음 배치로 넘어갈 수 없는 경우

### 1.2 Auto-Run 모드 (기본값)

생산 단계는 기본적으로 `다음 스텝` 입력 없이도 스스로 다음 배치로 이동한다.
사용자가 중간 검토를 명시하지 않는 한, Phase 0와 직전 draft를 기준으로 다음 미완료 단위로 계속 전진한다.

핵심 규칙:

1. auto-run은 기본값이다. 사용자가 검토/중단/수정 대기를 명시한 경우에만 멈춘다.
2. 진행 단위는 그대로 유지한다.
   - Phase 0 시트 1묶음
   - 10블록 배치 1개
   - 검수/merge 1회
   - BI handoff 1회
3. 각 단위 종료 시 반드시 아래 3개를 확인한다.
   - 산출물 파일 생성 완료
   - 직전 감리 또는 검증 통과
   - 다음 단위에 필요한 SSOT 존재
4. 1~3이 모두 참이면 사용자 입력 없이 다음 단위로 진행한다.
5. 1개라도 거짓이면 즉시 정지하고 실패 지점을 보고한다.
6. 컨텍스트 compaction이 발생해도 auto-run 기본값은 유지된다. 이 경우 `Phase 0`, 직전 `draft`, 직전 감리 결과를 다시 열어 확인한 뒤 자동 재개한다.
7. candidate/fixed/draft/check/merge 산출물과 모든 감리 보고서는 **UTF-8 only**로 저장한다. 한글 오염은 P0다.

권장 auto-run 순서:

`Phase 0 확정 → batch_001~007 생성 → fixed/merge → tr_block_070_draft 확정 → 검수 → BI 하네스 인계`

강제 정지 게이트:

- P0 위반 발생
- candidate/fixed/draft 간 title 또는 capital 연속성 불일치
- UTF-8 파싱 실패
- `???`, `�`, 인코딩 오염 탐지
- 사용자가 검토/수정/중단을 명시
- 정리 삭제처럼 되돌리기 어려운 후처리가 필요한 경우

### 1.3 `docs/blockguide` 강제 읽기 순서

이 폴더에는 역할이 다른 하네스가 3개 있다.
저지능 LLM일수록 **읽기 순서**를 강제로 고정해야 한다.

1. `blockguide-integrated-order.md`
2. `treatment-planning-harness.md`
3. 현재 문서 `treatment-production-harness-v2.md`
4. `bi-production-harness-v1.md`는 **TR handoff 규칙 확인용으로만** 미리 읽고, 실제 실행은 TR 완료 뒤에 한다.

운영 규칙:

1. 사용자가 특정 작품 기획안, `work_id`, `Phase 0`, `draft`, `다음 스텝` 중 하나만 줘도 위 4개를 먼저 UTF-8로 다시 연다.
2. 파일 존재 여부로 현재 단계를 판정한다.
   - `phase0_design` 없음 → planning 단계
   - `phase0_design` 있음, `tr_block_070_draft` 없음 → production 단계
   - `tr_block_070_draft` 있음 → BI 또는 감리 단계
3. 현재 단계가 production이 아니면 이 문서 내용을 중간에 끼워 넣지 않는다.
4. 읽기 순서를 건너뛰고 기억으로 작업하면 무효로 본다.

### 1.4 초세분화 실행 루틴 (저지능 LLM 기본값)

아래 14단계는 느리지만 실패율이 가장 낮다.
확신이 낮으면 이 루틴을 기본값으로 사용한다.

1. `Phase 0`와 직전 `draft/candidate/fixed`를 UTF-8로 재오픈한다.
2. 이번 턴 범위를 `Block N~M` 형태로 한 번만 정한다.
3. 범위가 모호하면 3블록으로 줄인다.
4. 이번 범위에서 회수해야 할 복선, 이어받아야 할 자본, 유지해야 할 NPC 상태를 먼저 적는다.
5. 각 블록의 사전 선언을 먼저 쓴다.
6. 그다음 JSON 블록을 생성한다.
7. 생성 직후 `절대 금지` 26개를 자가 점검한다.
8. 자가 점검에서 하나라도 걸리면 같은 범위를 즉시 다시 쓴다.
9. 통과본만 UTF-8로 저장한다.
10. Python 자동 교정을 실행한다.
11. Python 자동 검증을 실행한다.
12. 실패 시 다음 범위로 넘어가지 말고 **같은 범위만 재생성**한다.
13. 통과 시에만 merge 또는 다음 범위로 이동한다.
14. 턴 종료 시 아래 4줄을 남긴다.
    - 이번에 끝난 범위
    - 열린 복선 수
    - 다음 범위
    - 멈춤 사유 또는 계속 가능 여부

안전 모드 기본값:

- 모델 성능이 애매하면 3블록 단위
- 문장 반복이 보이면 즉시 3블록 단위로 강등
- 새 대단원 첫 배치는 무조건 작은 단위로 시작

### 1.5 모델별 배치 크기

| 항목 | Opus/Sonnet | Gemini Pro | Gemini Flash |
|------|-------------|------------|--------------|
| Phase 1 배치 | 10블록 | 5블록 | **3블록** |
| 사전 선언 항목 | 5개 전부 | 5개 전부 | **3개 필수** (1,4,5) |
| 차이 행렬 | 10블록 후 1회 | 5블록마다 1회 | **3블록마다 1회** |
| 복선 원장 상한 | 무제한 | 최대 15개 | **최대 10개** |
| 불안정 시 안전 모드 | **3블록으로 즉시 강등** | **3블록으로 즉시 강등** | **1~3블록 유지** |

---

## 2. Phase 0: 대단원 아크 설계 (가장 중요)

70블록 생성 **전에** 서사 골격을 확정한다. 이 단계 없이는 LLM이 무한 균등 반복으로 수렴한다.

### 2.0A 재료 은행 입력 규약 (강력 권장)

`test_material/material_bank.db`는 **연속성 엔진이 아니라 재료 은행**으로만 사용한다.

- 사용 대상: `material_bank_events`, `material_bank_npcs`, `material_bank_crises`,
  `material_bank_sector_chains`, `material_bank_market_data`
- 금지 대상: raw 테이블 전체 주입, `material_bank_exclusions`에 걸린 행, 연도별 자본 시뮬레이션(`X2`)을 단일 사건처럼 사용하는 것
- 용도:
  - Phase 0: 적대자/산업/위기/NPC 후보 확장
  - Phase 1: 배치별 사건 후보와 장소·섹터 다양화
  - Phase 2~4: 사용 금지. 연속성은 Python 교정/검증이 담당

조회 예시:

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --sectors "조선/해운,금융/은행" `
  --year-start 2006 `
  --year-end 2012 `
  --keyword "서브프라임,조선" `
  --limit-events 12 `
  --limit-npcs 8 `
  --limit-crises 6 `
  --limit-sector-chains 6 `
  --limit-market-data 12
```

이 번들 결과만 Phase 0/1 프롬프트에 넣는다. DB 전체를 직접 넣지 않는다.

### 2.1 Phase 0 프롬프트

```
당신은 웹소설 시놉시스 설계 전문가입니다.

[Bible 컨텍스트 — 세계관, 주인공, 장르 설정 전문]

아래 규격으로 7개 대단원(각 10블록)의 서사 골격을 설계하세요.

## 필수 설계 항목

### 1. 적대자 변천사 (최소 3세력)
- 대단원 1~2: 초기 적대자 (예: 내부 반대파)
- 대단원 3~4: 중기 적대자 (예: 경쟁사 연합)
- 대단원 5~7: 최종 적대자 (예: 글로벌 세력)
- 각 적대자의 등장/퇴장/약점 변화 명시

### 2. NPC 등퇴장 타임라인 (최소 8명)
- 대단원별 신규 NPC 1~2명 추가
- 기존 NPC 관계 변화 마일스톤 (협력→갈등→화해 등)
- NPC 이탈/배신/사망 이벤트 배치

### 3. 자본 성장 곡선 (변동 필수)
- 초반(1~20): 급성장 구간 (20~40% 변동)
- 중반(21~40): 위기 구간 (성장 둔화/일시 하락 포함)
- 후반(41~60): 재도약 구간 (변동폭 줄어듦)
- 최종(61~70): 안정화 또는 최종 승부
- 최소 3개 블록에서 자본 감소 필수 (패배/손실)

### 4. 감정 곡선 설계
- 대단원별 emotional_beat 분포 설계
- 10블록 내에서 최소 5종 이상의 beat type 사용
- intensity 1~10 전 구간 활용 (저조한 구간 필수)
- "조용한 블록" 최소 5개 배치 (tension 4~6, intensity 3~5)

### 5. 복선 장기 아크 (최소 5개)
- 10블록 이상 지연 회수되는 장기 복선 배치
- 각 복선의 심기 블록, 힌트 블록, 회수 블록 명시

### 6. 패배/좌절 블록 (최소 7개)
- 70블록 중 최소 10%는 주인공이 실질적으로 지는 블록
- success_pattern이 "실패"/"부분 성공"/"피로스 승리"인 블록 배치

## 출력 형식
JSON — 대단원 7개, 각 대단원에 10블록 슬롯 개요
```

### 2.2 Phase 0 보조 시트 (Phase 0 출력에 포함)

Phase 0 완료 시 아래 5개 시트를 함께 출력한다:

1. **적대자 전환 계획** — 최소 3세력, 전환 블록 포함
2. **NPC 등퇴장 계획** — 최소 8명, 관계 전환 이벤트 포함
3. **복선-회수 맵** — 시드/힌트/회수 블록
4. **패배 블록 계획** — 최소 7개
5. **파트너/장소/섹터 분포 계획**

---

## 3. Phase 1: 블록 생성 (Anti-Shortcut Harness)

### 3.1 생성 프롬프트 구조

```
당신은 웹소설 treatment 블록 생성 전문가입니다.

[Phase 0 전체 아크 설계]

## 직전 상태
- 마지막 자본: {prev_capital_after}
- 활성 NPC: {active_npcs_with_relations}
- 활성 적대자: {current_opponent}
- 미회수 복선: {open_foreshadows}
- 마지막 감정: {last_emotional_beat}
- 마지막 위치: {last_location}

## 이번 배치 목표 (Phase 0에서 설계한 것)
- 목표 자본 범위: {target_capital_range}
- 등장 예정 NPC: {new_npcs}
- 적대자 변화: {opponent_change}
- 회수 예정 복선: {foreshadows_to_resolve}
- 패배 블록 위치: {defeat_block_positions}
```

### 3.2 절대 금지 규칙 (프롬프트 하단에 필수 삽입)

```
## 절대 금지 — 이 규칙을 어기면 전량 재생성

=== 1세대 금지 (Pattern A~H 차단) ===
1. 성장률 3블록 이상 동일 값 금지 (±2%p 이상 변동 필수)
2. emotional_beat.type 2블록 연속 동일 금지
3. emotional_beat.intensity 3블록 연속 동일 값 금지
4. relationship_delta.before가 직전 블록의 after와 다르면 금지
5. callback이 "직전 블록의 X 성과가..." 패턴 2회 이상 금지
6. success_pattern 동일 표현 3회 이상 반복 금지
7. opponent.weakness_exploited 동일 표현 3회 이상 금지
8. deal_type 동일 값 3블록 이내 재등장 금지
9. location 동일 장소 3블록 이내 재등장 금지
10. duration 전량 동일 값 금지 (블록별 서사 규모에 맞게 3일~3개월)

=== 2세대 금지 (Pattern I~P 차단) ===
11. 영어 문장 금지: relationship_delta, foreshadow, callback, reward, stakes는
    반드시 한국어로 작성하라. 영어 1문장이라도 있으면 재작성.
12. 코드 식별자 금지: method, death_flag.avoided, slip_up, success_pattern,
    weakness_exploited에 "type_1", "plan_01", "anomaly_02" 같은
    코드/번호 접미사 금지. 서사적 한국어 문장으로 서술하라.
    - ❌ "systemic_risk_type_1"
    - ✅ "유동성 경색으로 인한 그룹 전체 연쇄 부도 위기"
13. 문장 템플릿 재사용 금지: solution/context/event_villain/stakes에서
    "섹터명만 교체"한 동일 구조 문장을 2회 이상 사용하면 재작성.
14. leverage_used 고정 금지: 동일 4항목 세트 3회 이상 반복 금지.
    블록별 최소 2항목은 고유해야 한다.
15. is_regressor 정합성: regression_type이 "빙의" 또는 "회귀"이면
    is_regressor=true 필수.
16. 복선 실제 회수 의무: foreshadow에서 "Block N" 지목 시,
    해당 Block N의 callback에 명시적으로 회수 문장 포함 필수.
17. 페이즈 내 NPC 변화 의무: 동일 NPC가 5블록 이상 등장하면,
    before≠after인 블록이 최소 3개 있어야 한다.
18. 장소 순환 주기 최소 15블록: 동일 장소가 15블록 이내에 재등장하면 위반.
19. global_partner 분화 의무: 70블록에 최소 3개 해외 파트너 등장.
20. execution_doctrine 진화 의무: 20블록 이상 동일 문장이면 재작성.
21. `reward` 재진술 금지: `context`를 시제만 바꿔 반복하거나 같은 문장을 축약하는 수준이면 무효.
    `reward`에는 반드시 "새로 생긴 결과/손실/지배력 변화"가 1개 이상 포함되어야 한다.
22. `relationship_delta.after` 복제 금지: 동일 문장이 다른 블록/다른 NPC에 3회 이상 반복되면 재작성.
23. 대단원 슬롯 반복 금지: 10블록 패턴을 다음 대단원에서 같은 순서로 재사용하면 무효.
    특히 `deal_type`, `method`, `success_pattern` 3종이 같은 인덱스에서 반복되면 재작성.
24. skeleton draft 금지: Phase 0의 block slot 문장을 `context/reward`에 얕게 풀어쓴 수준이면 무효.
    블록마다 최소 1개의 "구체 장면", 1개의 "구체 손익/권력 변화"가 새로 생겨야 한다.
25. 복선 저밀도 금지: 10블록 배치에서 `foreshadow + callback` 합계가 8 미만이면 재설계.
26. 저밀도 관계망 금지: 10블록 배치 평균 `relationship_delta` 대상 수가 2 미만이면 재설계.
```

### 3.3 사전 선언 프로토콜 (블록마다 JSON 앞에 필수)

#### 전체 버전 (Opus/Sonnet/Gemini Pro — 5항목)

```
각 블록마다 JSON 출력 직전에 아래 5개 항목을 자연어로 서술하라.
사전 선언 없이 JSON을 출력하면 무효 처리된다.

1. **이전 블록 잔향**: 직전 블록에서 무슨 일이 일어났는가?
   주인공의 감정 상태, 관계 변화, 자본은 얼마였나?
2. **이번 블록의 고유 사건**: 이전/이후 블록에서 절대 반복되지 않는
   고유 이벤트를 1문장으로 서술하라.
3. **차별화 증명**: 직전 블록과 아래 5필드가 어떻게 다른지 명시:
   - emotional_beat.type: [직전] → [이번]
   - deal_type: [직전] → [이번]
   - opponent 또는 weakness: [직전] → [이번]
   - location: [직전] → [이번]
   - duration: [직전] → [이번]
   5개 중 3개 이상이 직전과 동일하면 해당 블록을 다시 구상하라.
4. **자본 계산 과정**: capital_before = [직전 capital_after] = [숫자].
   변동 근거 = [서사적 근거]. capital_after = [계산식].
5. **NPC 관계 이월**: 각 NPC의 before를 직전 블록 after에서 복사.
   새 NPC면 "신규" 명시.
```

#### 축소 버전 (Gemini Flash — 3항목)

```
각 블록마다 JSON 앞에 필수:

1. **직전 상태 인용**: 직전 블록의 capital_after, emotional_beat,
   각 NPC의 after 텍스트를 그대로 복사하라.
2. **자본 계산**: capital_before = [직전 capital_after].
   변동 근거 = [1문장]. capital_after = [계산식].
3. **차별화 1줄**: 직전 블록과 이번 블록의 가장 큰 차이를 1문장으로 서술.
```

### 3.4 차이 행렬 (배치 완료 후 필수 출력)

블록 배치 생성 완료 후, 차이 행렬을 출력하고 자가 검증 수행:

```
| Block | beat_type | intensity | tension | deal_type | opponent | location | duration | capital_delta | 성장률 | success |
|-------|-----------|-----------|---------|-----------|----------|----------|----------|---------------|--------|---------|

### 자가 검증 (행렬 출력 후 수행)
1. beat_type 열에 2연속 동일 값? → 수정
2. intensity 열에 3연속 동일 값? → 수정
3. deal_type 열에 3블록 이내 동일 값? → 수정
4. opponent 열이 전부 동일? → 최소 2개 분화
5. location 열에 3블록 이내 동일 값? → 수정
6. duration 열이 전부 동일? → 최소 3종 분화
7. 성장률 열에 3연속 ±1%p 이내? → 수정
8. success 열이 전부 동일? → 최소 2개 "실패"/"부분성공"
9. capital_delta 전부 양수? → 최소 1개 음수 필수
10. "이 블록들이 전부 같은 이야기처럼 보이는가?" → 보이면 재설계
11. relationship_delta/foreshadow/callback에 영어 문장? → 한국어로 교체
12. method/death_flag/slip_up에 코드 접미사? → 서사 문장으로 교체
13. solution/event_villain에서 "섹터명만 다르고 나머지 동일"? → 재작성
14. leverage_used가 3블록 이상 동일 세트? → 최소 2항목 교체
15. callback이 전부 "carry-over" 패턴? → 구체적 사건 참조로 교체
16. reward가 context 반복 요약처럼 보이는가? → 실제 결과, 손실, 계약 변화로 교체
17. relationship_delta.after가 같은 문장으로 여러 NPC/여러 블록에 복붙됐는가? → 관계별로 차별화
18. 이번 10블록의 deal_type/method 순서가 다음 10블록에도 그대로 재사용될 것 같은가? → 순서 자체를 재설계
19. foreshadow + callback 합계가 10블록에 8개 미만인가? → 복선 밀도 보강
20. 평균 핵심 서술 길이가 지나치게 짧아 skeleton처럼 보이는가? → 장면과 결과를 추가
```

### 3.5 대단원 종료 시 필수 보조 출력 (4종)

#### A. NPC 추적표

```
| NPC 이름 | 등장 블록 | 마지막 활동 | 현재 관계 (= 다음 블록 before) | 다음 예정 |
|----------|-----------|-------------|-------------------------------|-----------|

검증:
- 활성 NPC ≤ 2명 → 다음 대단원에서 최소 2명 추가
- 10블록 동안 NPC 변동 0건 → 재설계
- "현재 관계" 열에 동일 문장 2명+ → 차별화
```

#### B. 복선 원장

```
| # | 복선 내용 | 심기 블록 | 목표 회수 블록 | 실제 회수 블록 | 상태 |
|---|-----------|-----------|---------------|---------------|------|

검증:
- OPEN 복선 20개+ 누적 → 5개 이상 이번 대단원에서 회수
- 심기 후 20블록+ 미회수 → 즉시 회수 또는 "폐기"
- 장기 복선(간격 10블록+) 5개 미만 → 추가
```

**Gemini Flash 축소판** — OPEN 복선 최대 10개, 3블록마다 출력:

```
| # | 내용 (20자 이내) | 심기 | 회수 예정 | 상태 |
```

#### C. 자본 곡선 ASCII

```
Block N+1:  ████████████ 1,150억 (-4.5%)
Block N+2:  █████████████ 1,230억 (+7.0%)
...

검증:
- 10블록 연속 상승 → 최소 1블록 하락
- 성장률 5블록+ ±2%p 평탄 → 변동폭 확대
- 최종 자본이 Phase 0 목표 ±20% 이탈 → 조정
```

#### D. 적대자 상태 (20블록마다)

```
현재 적대자: [이름]
- 활동 기간: Block X~Y (Z블록)
- 실질적 타격 횟수: N회
- 약점 노출 종류: N종 (3종 이하 → 추가 필요)

### 20블록 초과 시 필수 조치 (택 1)
□ 적대자 분열    □ 적대자 교체
□ 적대자 진화    □ 적대자 동맹
```

---

## 4. Phase 2: Python 자동 교정 (LLM 불신 영역)

LLM 출력을 **신뢰하지 않는** 필드들을 Python이 강제 교정한다.
이 단계는 LLM 호출 0회.

```python
def auto_correct(blocks: list[dict], npc_tracker: dict) -> list[dict]:
    """
    LLM 출력에서 절대적으로 보장해야 하는 수치/연속성을 Python이 강제 교정.
    - capital_before = prev.capital_after
    - capital_delta = capital_after - capital_before (재계산)
    - relationship_delta.before = prev.after (NPC별)
    - pov_character 일관성 강제
    - is_regressor 정합성 강제 (빙의/회귀 → true)
    """
    for i, block in enumerate(blocks):
        ge = block.setdefault("genre_ext", {})

        # --- 자본 연속성 ---
        if i > 0:
            prev_after = blocks[i-1]["genre_ext"]["capital_after"]
            ge["capital_before"] = prev_after

            before_val = parse_capital(prev_after)
            after_val = parse_capital(ge.get("capital_after", "0"))
            ge["capital_delta"] = format_capital_delta(after_val - before_val)

        # --- NPC before 이월 ---
        for rd in block.get("relationship_delta", []):
            target = rd.get("target", "")
            if target in npc_tracker:
                rd["before"] = npc_tracker[target]
            # tracker 갱신
            npc_tracker[target] = rd.get("after", rd.get("before", ""))

        # --- pov_character 일관성 ---
        if i > 0 and block.get("pov_character") != blocks[0].get("pov_character"):
            block["pov_character"] = blocks[0]["pov_character"]

        # --- is_regressor 정합성 (P0-M) ---
        reg = block.get("regression_ext", {})
        if reg.get("regression_type") in ("빙의", "회귀"):
            reg["is_regressor"] = True

    return blocks


def parse_capital(text: str) -> float:
    """한국어 자본 파싱: '1조 2,000억' → 12000 (억 단위)"""
    import re
    if not text or text in ("0", "해당 없음"):
        return 0.0
    text = text.replace(",", "").replace(" ", "")

    total = 0.0
    # 조
    m = re.search(r'(\d+(?:\.\d+)?)\s*조', text)
    if m:
        total += float(m.group(1)) * 10000
    # 억
    m = re.search(r'(\d+(?:\.\d+)?)\s*억', text)
    if m:
        total += float(m.group(1))
    # 만
    m = re.search(r'(\d+(?:\.\d+)?)\s*만', text)
    if m:
        total += float(m.group(1)) * 0.0001

    # 순수 숫자 (단위 없음) — 억 단위로 가정
    if total == 0:
        m = re.search(r'[\d.]+', text)
        if m:
            total = float(m.group())

    return total


def format_capital_delta(delta_eok: float) -> str:
    """억 단위 delta를 한국어로 포맷: -800 → '-800억', 12000 → '+1조 2,000억'"""
    sign = "+" if delta_eok >= 0 else ""
    abs_val = abs(delta_eok)
    if abs_val >= 10000:
        jo = int(abs_val // 10000)
        eok = abs_val % 10000
        if eok > 0:
            return f"{sign}{'-' if delta_eok < 0 else ''}{jo}조 {int(eok):,}억"
        return f"{sign}{'-' if delta_eok < 0 else ''}{jo}조"
    return f"{sign}{int(delta_eok):,}억"
```

### 4.1 Gemini 전용: 자본 표기 통일

Gemini는 "1조 2,000억 + 800억 = ?" 같은 혼합 산술에서 오류 빈발.

**대책: 생성 시 억 단위 정수로 통일, 완료 후 Python 변환**

프롬프트에 삽입:
```
## 자본 표기 규칙 (Gemini 전용)
모든 자본을 "억" 단위 정수로 표기하라. 조/만 혼용 금지.
- ✅ capital_before: "12000억"
- ❌ capital_before: "1조 2,000억"
- ❌ capital_before: "1.2조"

생성 완료 후 Python이 "12000억" → "1조 2,000억"으로 자동 변환함.
```

### 4.2 Autofix 허용/금지 경계

Phase 2 자동 교정은 수치·연속성만 다룬다. 서사 필드는 Python이 수정하지 않고 LLM 재작성 대상으로 남겨 둔다.

#### 자동 보정 허용

| 필드 | 교정 방식 |
|------|-----------|
| `block_id` | 배치 순서에 맞게 재정렬 |
| `genre_ext.capital_before` | 직전 블록의 `capital_after`로 강제 |
| `genre_ext.capital_delta` | `capital_after - capital_before`로 재계산 |
| `genre_ext.profit_loss` | 재계산된 delta와 일치하도록 갱신 |
| `relationship_delta.before` | 동일 NPC의 직전 `after` 값으로 이월 |
| `regression_ext.is_regressor` | `regression_type in {빙의, 회귀}`이면 `true`로 강제 |

#### 자동 보정 금지

| 필드 | 금지 이유 |
|------|-----------|
| `content.*` | 사건, 적대 행동, 해결, 보상은 서사 재작성 대상 |
| `stakes` | 손실 규모와 긴장도는 문맥 의존적 |
| `foreshadow` | 장기 복선 구조 판단이 필요 |
| `callback` | 구체 사건 회수 문장을 다시 써야 함 |
| `deal_type` | 배치 차별화와 거래 구조 설계에 직접 영향 |
| `location` | 순환 패턴 회피와 장면 설계가 함께 필요 |
| `leverage_used` | 반복 여부만으로 대체 항목을 결정할 수 없음 |
| `genre_ext.method` | 전략 서술은 모델이 다시 써야 함 |
| `genre_ext.success_pattern` | 결과 패턴은 블록 서사와 함께 재설계해야 함 |
| `regression_ext.execution_doctrine` | 회귀/빙의 전략 문장은 기계적 치환 대상이 아님 |

이 경계의 목적은 정합성은 기계적으로 강제하고, 서사 품질은 모델이 다시 책임지게 분리하는 데 있다.

---

## 5. Phase 3: Python 자동 검증

### 5.1 1세대 결함 탐지 (Pattern A~H)

```python
def validate_v1(blocks: list[dict]) -> list[dict]:
    """1세대 8대 결함 패턴 자동 탐지. 위반 목록 반환."""
    violations = []

    for i in range(1, len(blocks)):
        prev, curr = blocks[i-1], blocks[i]

        # Pattern A: 자본 연속성
        prev_after = parse_capital(prev["genre_ext"]["capital_after"])
        curr_before = parse_capital(curr["genre_ext"]["capital_before"])
        if abs(prev_after - curr_before) > 0.01:
            violations.append({
                "block": i+1, "pattern": "A", "severity": "P0",
                "msg": f"capital_before({curr_before}) != prev capital_after({prev_after})",
                "auto_fix": True
            })

        # Pattern B: NPC before 리셋
        if i > 1:
            prev_rd = {rd["target"]: rd["after"] for rd in prev.get("relationship_delta", [])}
            for rd in curr.get("relationship_delta", []):
                if rd["target"] in prev_rd and rd["before"] != prev_rd[rd["target"]]:
                    violations.append({
                        "block": i+1, "pattern": "B", "severity": "P0",
                        "msg": f"NPC {rd['target']} before 리셋",
                        "auto_fix": True
                    })

        # Pattern D: emotional_beat 연속
        if i >= 2:
            types_3 = [blocks[j]["emotional_beat"]["type"] for j in range(i-2, i+1)]
            if len(set(types_3)) == 1:
                violations.append({
                    "block": i+1, "pattern": "D", "severity": "P1",
                    "msg": f"beat.type 3연속 동일: {types_3[0]}"
                })
            ints_3 = [blocks[j]["emotional_beat"]["intensity"] for j in range(i-2, i+1)]
            if len(set(ints_3)) == 1:
                violations.append({
                    "block": i+1, "pattern": "D", "severity": "P1",
                    "msg": f"beat.intensity 3연속 동일: {ints_3[0]}"
                })

        # Pattern E: deal_type 근접 반복
        if i >= 2:
            deals = [blocks[j]["genre_ext"].get("deal_type", "") for j in range(i-2, i+1)]
            if deals[0] == deals[2] and deals[0]:
                violations.append({
                    "block": i+1, "pattern": "E", "severity": "P1",
                    "msg": f"deal_type 3블록 이내 재등장: {deals[0]}"
                })

        # Pattern G: callback 템플릿
        for cb in curr.get("callback", []):
            if isinstance(cb, str) and "성과가 이번" in cb and "전환의 발판" in cb:
                violations.append({
                    "block": i+1, "pattern": "G", "severity": "P1",
                    "msg": "callback 템플릿 반복 (X 성과가 Y 전환의 발판)"
                })

    # Pattern C: 적대자 단일 고정
    opponents = set()
    for b in blocks:
        opp = b.get("genre_ext", {}).get("opponent", {})
        opponents.add(opp.get("name", "") if isinstance(opp, dict) else str(opp))
    if len(opponents) <= 1:
        violations.append({"block": "전체", "pattern": "C", "severity": "P1",
                          "msg": f"적대자 단일 고정: {opponents}"})

    # Pattern F: duration 전량 동일
    durations = set(b.get("time_span", {}).get("duration", "") for b in blocks)
    if len(durations) <= 1:
        violations.append({"block": "전체", "pattern": "F", "severity": "P2",
                          "msg": f"duration 전량 동일: {durations}"})

    # Pattern G: success_pattern 반복
    sp_counts: dict[str, int] = {}
    for b in blocks:
        sp = b.get("genre_ext", {}).get("success_pattern", "")
        if sp:
            sp_counts[sp] = sp_counts.get(sp, 0) + 1
    for sp, cnt in sp_counts.items():
        if cnt >= 3:
            violations.append({"block": "전체", "pattern": "G-success", "severity": "P1",
                              "msg": f"success_pattern '{sp[:40]}...' {cnt}회 반복"})

    # 성장률 5블록 연속 동일
    growth_rates = []
    for b in blocks:
        ge = b.get("genre_ext", {})
        before = parse_capital(ge.get("capital_before", "0"))
        after = parse_capital(ge.get("capital_after", "0"))
        growth_rates.append(round((after - before) / before * 100, 1) if before > 0 else 0.0)
    for i in range(len(growth_rates) - 4):
        if len(set(growth_rates[i:i+5])) == 1:
            violations.append({"block": f"{i+1}~{i+5}", "pattern": "A-growth", "severity": "P0",
                              "msg": f"성장률 5블록 연속 고정: {growth_rates[i]}%"})
            break

    # 패배 블록 부재
    defeat_count = sum(1 for b in blocks if parse_capital(b.get("genre_ext", {}).get("capital_delta", "+0")) < 0)
    if defeat_count < 3:
        violations.append({"block": "전체", "pattern": "DEFEAT", "severity": "P1",
                          "msg": f"패배/손실 블록 {defeat_count}개 (최소 7개 권장)"})

    return violations
```

### 5.2 2세대 결함 탐지 (Pattern I~P)

```python
import re
from collections import Counter

ENGLISH_RE = re.compile(r'[A-Za-z]{5,}')
CODE_RE = re.compile(r'(?:_\d+|type_\d|plan_\d|anomaly_\d|protocol_\d|_B\d)')
BANNED_TEMPLATES = [
    "Deferred setup for Block",
    "carry-over was converted into leverage",
    "Capital moved from",
]


def validate_v2(blocks: list[dict]) -> list[dict]:
    """2세대 결함 패턴 탐지 (I~P)."""
    violations = []

    for i, b in enumerate(blocks):
        # Pattern I: 영문 혼용
        for rd in b.get("relationship_delta", []):
            for field in ("before", "after"):
                if ENGLISH_RE.search(rd.get(field, "")):
                    violations.append({"block": i+1, "pattern": "I", "severity": "P1",
                                      "msg": f"relationship_delta.{field} 영문 포함"})
                    break
        for fs in b.get("foreshadow", []):
            if ENGLISH_RE.search(fs):
                violations.append({"block": i+1, "pattern": "I", "severity": "P1",
                                  "msg": f"foreshadow 영문: '{fs[:40]}...'"})
        for cb in b.get("callback", []):
            if ENGLISH_RE.search(cb):
                violations.append({"block": i+1, "pattern": "I", "severity": "P1",
                                  "msg": f"callback 영문: '{cb[:40]}...'"})
        reward = b.get("content", {}).get("reward", "")
        if ENGLISH_RE.search(reward):
            violations.append({"block": i+1, "pattern": "I", "severity": "P1",
                              "msg": f"reward 영문: '{reward[:40]}...'"})
        # 금지 템플릿
        for tmpl in BANNED_TEMPLATES:
            for field_val in [reward] + b.get("foreshadow", []) + b.get("callback", []):
                if tmpl in str(field_val):
                    violations.append({"block": i+1, "pattern": "I-TPL", "severity": "P1",
                                      "msg": f"금지 템플릿: '{tmpl}'"})

        # Pattern J: 코드형 값
        code_fields = [
            (b.get("genre_ext", {}), "method"),
            (b.get("genre_ext", {}), "success_pattern"),
            (b.get("regression_ext", {}), "execution_doctrine"),
        ]
        code_nested = [
            ("genre_ext.opponent", b.get("genre_ext", {}).get("opponent", {}), "weakness_exploited"),
            ("regression_ext.death_flag", b.get("regression_ext", {}).get("death_flag", {}), "avoided"),
            ("regression_ext.death_flag", b.get("regression_ext", {}).get("death_flag", {}), "method"),
            ("regression_ext.regression_hint", b.get("regression_ext", {}).get("regression_hint", {}), "slip_up"),
        ]
        for parent, key in code_fields:
            val = parent.get(key, "") if isinstance(parent, dict) else ""
            if CODE_RE.search(str(val)):
                violations.append({"block": i+1, "pattern": "J", "severity": "P2",
                                  "msg": f"{key} 코드형 값: '{str(val)[:40]}'"})
        for path, parent, key in code_nested:
            val = parent.get(key, "") if isinstance(parent, dict) else ""
            if CODE_RE.search(str(val)):
                violations.append({"block": i+1, "pattern": "J", "severity": "P2",
                                  "msg": f"{path}.{key} 코드형 값: '{str(val)[:40]}'"})

    # Pattern K: 문장 템플릿 로테이션 (자카드 기반)
    def _mask_sector(text: str) -> str:
        for s in ["지주구조", "금융", "반도체", "에너지", "물류",
                   "바이오", "유통", "플랫폼", "인프라", "미디어"]:
            text = text.replace(s, "SECTOR")
        return text

    def _trigram_jaccard(a: str, b: str) -> float:
        if len(a) < 3 or len(b) < 3:
            return 0.0
        sa = {a[j:j+3] for j in range(len(a)-2)}
        sb = {b[j:j+3] for j in range(len(b)-2)}
        inter = len(sa & sb)
        union = len(sa | sb)
        return inter / union if union else 0.0

    for fp in ["content.context", "content.event_villain", "content.solution", "stakes"]:
        texts = []
        for b in blocks:
            parts = fp.split(".")
            val = b
            for p in parts:
                val = val.get(p, "") if isinstance(val, dict) else ""
            texts.append(_mask_sector(str(val)))
        similar = sum(1 for i in range(len(texts))
                      for j in range(i+1, min(i+6, len(texts)))
                      if _trigram_jaccard(texts[i], texts[j]) > 0.5)
        if similar > len(blocks) * 0.3:
            violations.append({"block": "전체", "pattern": "K", "severity": "P1",
                              "msg": f"{fp} 템플릿 로테이션: 유사 쌍 {similar}개"})

    # Pattern L: leverage_used 고정
    lev_sets = [tuple(sorted(b.get("genre_ext", {}).get("leverage_used", [])))
                for b in blocks if isinstance(b.get("genre_ext", {}).get("leverage_used"), list)]
    for lev_set, cnt in Counter(lev_sets).items():
        if cnt >= 3:
            violations.append({"block": "전체", "pattern": "L", "severity": "P1",
                              "msg": f"leverage_used 동일 세트 {cnt}회 반복"})

    # Pattern M: is_regressor 정합
    for i, b in enumerate(blocks):
        reg = b.get("regression_ext", {})
        if (reg.get("regression_type") in ("빙의", "회귀")
                and reg.get("is_regressor") is False):
            violations.append({"block": i+1, "pattern": "M", "severity": "P0",
                              "msg": f"is_regressor=false but regression_type='{reg['regression_type']}'"})
            break

    # Pattern N: 복선-회수 단절
    BLOCK_REF_RE = re.compile(r'Block\s*(\d+)', re.IGNORECASE)
    plant_targets: dict[int, list[str]] = {}
    for i, b in enumerate(blocks):
        for fs in b.get("foreshadow", []):
            for m in BLOCK_REF_RE.finditer(fs):
                plant_targets.setdefault(int(m.group(1)), []).append(fs)
    disconnected = 0
    for target, foreshadows in plant_targets.items():
        if 1 <= target <= len(blocks):
            tb = blocks[target - 1]
            cbs = tb.get("callback", [])
            resolved = any(
                len(set(fs.split()) & set(cb.split())) >= 3
                for cb in cbs for fs in foreshadows
            )
            if not resolved:
                disconnected += 1
    if plant_targets and disconnected > len(plant_targets) * 0.5:
        violations.append({"block": "전체", "pattern": "N", "severity": "P1",
                          "msg": f"복선-회수 단절: {disconnected}/{len(plant_targets)}"})

    # Pattern O: 페이즈 내 NPC 동결
    for ps in range(0, len(blocks), 10):
        pe = min(ps + 10, len(blocks))
        frozen: dict[str, int] = {}
        for b in blocks[ps:pe]:
            for rd in b.get("relationship_delta", []):
                if rd.get("before", "") == rd.get("after", ""):
                    frozen[rd["target"]] = frozen.get(rd["target"], 0) + 1
        for name, cnt in frozen.items():
            if cnt >= 7:
                violations.append({"block": f"{ps+1}~{pe}", "pattern": "O", "severity": "P1",
                                  "msg": f"NPC '{name}' 페이즈 내 {cnt}블록 동결"})

    # Pattern P: 장소 15블록 이내 재등장
    locations = [b.get("location", {}).get("place", "") for b in blocks]
    for i in range(len(locations)):
        for j in range(i+1, min(i+15, len(locations))):
            if locations[i] and locations[i] == locations[j]:
                violations.append({"block": f"{i+1},{j+1}", "pattern": "P", "severity": "P2",
                                  "msg": f"장소 '{locations[i]}' {j-i}블록 만에 재등장"})
                break

    return violations


def validate_all(blocks: list[dict]) -> list[dict]:
    """v1 + v2 통합 검증"""
    return validate_v1(blocks) + validate_v2(blocks)
```

---

## 6. Phase 4: 3-Pass 감리

### 6.1 1차 감리 (전수조사)

Python 자동 검증(§5) + LLM 6개 검사 항목 × 70블록:
- 수치 연속성
- 시간 연속성
- 인물 연속성
- 서사 연속성
- 장르 정합성
- 빙의/회귀 정합성

### 6.2 2차 감리 (오탐 제거)

1차 결과 재검토:
- 장기 복선으로 의도된 지연 → FP
- 의도적 저강도 블록(quiet block) → FP
- 규칙 완화 사유를 코멘트로 기록

### 6.3 3차 감리 (최종 확정)

- 확정 위반만 수정 반영
- 수정 후 자동검증 재실행
- 통과 리포트 생성

---

## 7. 출고 게이트 (합격 조건)

### 7.0 생산 밀도 게이트 (실전용 필수)

정합성이 맞아도 아래 기준을 못 넘기면 `production_ready = false`로 본다.
이 경우 결과물은 draft가 아니라 **skeleton draft**로 분류하며, 출고 전 재생성이 원칙이다.

- 핵심 서술 평균 길이 (`context + event_villain + solution + reward + stakes`) 350자 이상
- `foreshadow` 평균 0.8개 이상
- `callback` 평균 0.8개 이상
- `relationship_delta` 평균 대상 수 2.0 이상
- `deal_type` 최대 반복 4회 이하
- `method` 최대 반복 4회 이하
- `reward` 재진술 패턴 0건
- 대단원 간 `deal_type/method` 순서 반복 0건

해석:

- 위 기준을 못 넘기면 "JSON은 맞지만 실제 생산용으론 저밀도"로 판정한다.
- 이 경우 패치보다 **Phase 0 유지 + TR 전면 재생성**이 우선이다.

### P0 게이트 (자동화 — 1건이라도 있으면 출고 불가)

- Pattern A: 자본 연속성 위반 0건
- Pattern B: NPC before 리셋 위반 0건
- Pattern M: is_regressor 정합 위반 0건
- 시간 역행 0건
- pov_character 불일치 0건

### P1 게이트 (감리 확인 — 각 0건)

- 영문 템플릿 0건
- 복선 미회수율 50% 미만
- 관계 동결(연속 7블록+) 0건
- 적대자 3세력 이상
- NPC 8명 이상
- 패배 블록 7개 이상
- emotional_beat 6종 이상
- callback 구체적 사건 참조 (기계 패턴 0건)
- deal_type 10종 이상
- leverage_used 동일 세트 3회 미만
- reward 재진술 0건
- relationship_delta 복제 문장 0건
- 대단원 슬롯 반복 0건

### P2 게이트 (권장)

- 코드형 토큰 0건
- reward 한국어
- duration 3종 이상
- location 8곳 이상, 15블록 이내 재등장 0건
- global_partner 3곳 이상
- 핵심 서술 평균 길이 400자 이상
- foreshadow 평균 1.0 이상
- callback 평균 1.0 이상

---

## 8. Gemini 실전 운용 플로우

### 8.1 핵심 원칙

1. **LLM은 창작만, Python은 수치/연속성 강제** — 대원칙 1과 동일 사상
2. **생성/검증/수정 3단 분리 호출** — 한 번에 시키면 Gemini가 검증을 건너뜀
3. **Python이 최종 교정권** — capital_before, NPC before, delta는 LLM 출력을 덮어씀

### 8.2 호출 시퀀스 (3블록 배치 기준)

```
[호출 1] 생성
  입력: 직전 3블록 JSON + NPC 추적표 + 복선 원장 + 배치 목표 + material bundle(선택)
  출력: 블록 3개 JSON + 사전 선언 3항목

[Python] 자동 교정
  - capital_before = prev.capital_after (강제)
  - NPC before = prev.after (강제)
  - delta 재계산

[호출 2] 검증 (분리 호출)
  입력: 교정된 3블록
  출력: 차이 행렬 + 자가 검증 15문항 답변

[Python] 자동 검증
  - validate_all() 실행

[호출 3] 수정 (위반 시만)
  입력: 위반 블록 + 위반 사유
  출력: 수정된 블록 1개

[Python] 복선 원장 + NPC 추적표 갱신
```

### 8.3 저지능 모델 추가 규약

Gemini Flash급 저지능 모델은 `§8.2` 호출 시퀀스 외에도 아래 제한을 고정한다.

1. 배치 크기는 3블록으로 고정한다. 5블록 이상 확장은 금지한다.
2. 입력 컨텍스트는 직전 3블록 JSON, NPC 추적표, OPEN 복선 원장, 배치 목표로 제한한다. 70블록 전체 JSON 주입은 금지한다.
3. `roadmap` 또는 BI를 넣더라도 title만 고정점으로 사용한다. 기존 defective content를 그대로 베끼지 않는다.
4. 후보 저장 파일에는 JSON 배열만 남긴다. 사전 선언, 차이 행렬, 자연어 설명은 저장 대상이 아니다.

### 8.4 Python 오케스트레이터

```python
def generate_treatment_gemini(bible: dict, arc_design: dict,
                              total_blocks: int = 70,
                              batch_size: int = 3) -> list[dict]:
    """Gemini Flash/Pro용 treatment 생성 오케스트레이터"""
    blocks: list[dict] = []
    npc_tracker: dict[str, str] = {}
    foreshadow_ledger: list[dict] = []

    for batch_start in range(0, total_blocks, batch_size):
        batch_end = min(batch_start + batch_size, total_blocks)

        # === 호출 1: 생성 ===
        prev_ctx = format_prev_blocks(blocks[-3:])
        npc_table = format_npc_tracker(npc_tracker)
        fs_table = format_foreshadow_ledger(foreshadow_ledger)
        goals = extract_batch_goals(arc_design, batch_start, batch_end)

        new_blocks = call_gemini_generate(
            prev_ctx, npc_table, fs_table, goals,
            batch_start + 1, batch_end
        )

        # === Python 자동 교정 ===
        for j, block in enumerate(new_blocks):
            idx = batch_start + j
            ge = block.setdefault("genre_ext", {})

            # 자본 연속성
            if idx > 0:
                prev_after = blocks[-1]["genre_ext"]["capital_after"]
                ge["capital_before"] = prev_after
                bv = parse_capital(prev_after)
                av = parse_capital(ge.get("capital_after", "0"))
                ge["capital_delta"] = format_capital_delta(av - bv)

            # NPC before 이월
            for rd in block.get("relationship_delta", []):
                if rd["target"] in npc_tracker:
                    rd["before"] = npc_tracker[rd["target"]]

            blocks.append(block)

            # NPC tracker 갱신
            for rd in block.get("relationship_delta", []):
                npc_tracker[rd["target"]] = rd["after"]

        # === 호출 2: 검증 (분리 호출) ===
        llm_violations = call_gemini_validate(new_blocks)

        # === Python 자동 검증 ===
        py_violations = validate_all(blocks[batch_start:batch_end])

        # === 호출 3: 수정 (위반 시만) ===
        all_viols = merge_violations(llm_violations, py_violations)
        for v in all_viols:
            if not v.get("auto_fix"):
                fixed = call_gemini_fix(blocks[v["block"] - 1], v)
                blocks[v["block"] - 1] = fixed

        # 복선 원장 갱신
        update_foreshadow_ledger(foreshadow_ledger, new_blocks, batch_start)

    return blocks
```

### 8.5 CLI 하네스 실행

실전 운영은 `scripts/tr_batch_harness.py`의 `prompt`, `check`, `merge` 서브커맨드로 고정한다.

- `prompt`: 직전 블록 요약, NPC 추적표, OPEN 복선 원장, 배치 목표를 묶은 프롬프트 번들 생성
- `check`: 후보 배치 검사, 안전한 정합성 필드만 자동 보정, 리포트 생성
- `merge`: `check`를 다시 수행한 뒤 통과 배치를 draft에 병합

권장 순서:

1. `prompt`로 배치 프롬프트 파일 생성
2. 모델 출력에서 JSON 배열만 후보 파일로 저장
3. `check --autofix`로 정합성 보정 및 검사 리포트 생성
4. `merge`로 통과 배치를 draft에 반영

#### PowerShell 예시 1: 신작 배치 프롬프트 생성

```powershell
python -X utf8 scripts/tr_batch_harness.py prompt `
  --roadmap bible\a_재벌가빙의후승계전_bi.json `
  --start 1 `
  --batch-size 3 `
  --mode flash `
  --output docs\2026-03-09\dynasty_heir_batch_001_prompt.md
```

#### PowerShell 예시 2: 기존 draft 기준 다음 배치 프롬프트 생성

```powershell
python -X utf8 scripts/tr_batch_harness.py prompt `
  --draft treatments\dynasty_heir_possession_tr_block_070_draft.json `
  --roadmap bible\a_재벌가빙의후승계전_bi.json `
  --start 4 `
  --batch-size 3 `
  --mode flash `
  --output docs\2026-03-09\dynasty_heir_batch_002_prompt.md
```

#### PowerShell 예시 3: 후보 배치 검사 및 자동 보정

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

#### PowerShell 예시 4: draft 병합

```powershell
python -X utf8 scripts/tr_batch_harness.py merge `
  --draft treatments\dynasty_heir_possession_tr_block_070_draft.json `
  --candidate treatments\dynasty_heir_batch_001_fixed.json `
  --roadmap bible\a_재벌가빙의후승계전_bi.json `
  --start 1 `
  --batch-size 3 `
  --report treatments\audit_reports\dynasty_heir_batch_001_merge.md
```

---

## 9. 골든 블록 레퍼런스

### 9.1 좋은 블록 (이것을 목표로 삼아라)

```json
{
  "block_id": "Block 23",
  "title": "우한의 겨울 — 공급망 붕괴",
  "content": {
    "context": "2020년 1월, 중국 우한발 팬데믹이 전 세계 공급망을 마비시켰다. 한도준의 물류 자회사 3개 중 2개가 항만 봉쇄로 화물을 받지 못하는 상황.",
    "event_villain": "글로벌 물류 연합이 한도준의 독점 노선을 빼앗으려 각국 정부에 로비. 내부 배신자 최부장이 경쟁사에 노선 데이터 유출. 자금 조달선마저 은행들이 회수 통보.",
    "solution": "팬데믹을 예견하고 선제 확보한 방역 물자를 동남아 4개국에 무상 제공하여 정치적 우군을 만듦. 최부장의 유출은 미끼 데이터. 은행 자금 회수는 자체 유동성으로 버텼지만 순손실 800억 감수.",
    "reward": "물류 노선 3개 중 2개를 사수했지만 1개는 경쟁사에 넘어감. 자본 1.2조에서 1.12조로 감소. 동남아 정부와의 신뢰로 향후 독점 입찰 자격 확보."
  },
  "stakes": "물류 자회사 전량 상실 시 핵심 사업 기반 붕괴. 은행 자금 회수가 연쇄되면 유동성 위기로 전체 그룹 매각 위험",
  "tension_level": 9,
  "power_shift": {
    "protagonist": "순손실 800억 감수하며 전략적 후퇴 단행. 단기 패배를 인정했지만 장기 포석.",
    "antagonist": "글로벌 물류 연합이 노선 1개를 탈취하며 첫 실질적 승리. 내부 배신자 최부장은 미끼에 걸려 신뢰 상실."
  },
  "relationship_delta": [
    {
      "target": "박재현 CFO",
      "before": "팬데믹 대비 자금 운용에 대해 '과잉 방어'라며 불만을 표출하던 상태",
      "after": "유동성 위기를 자체 자금으로 넘기자 판단력을 인정. '다음엔 미리 알려달라'며 신뢰 회복 조짐"
    },
    {
      "target": "최부장 (내부 배신자)",
      "before": "5년간 신뢰받던 물류 담당 임원",
      "after": "미끼 데이터 유출이 밝혀져 경영진에서 퇴출. 양쪽 모두에서 버림받는 처지"
    },
    {
      "target": "닌 쏜차이 (태국 교통부 차관)",
      "before": "'외국 자본의 침략자'로 경계하던 관료",
      "after": "방역 물자 제공에 감사하며 물류 입찰에서 우호적 입장으로 전환"
    }
  ],
  "foreshadow": [
    "동남아 정부와의 신뢰가 Block 31에서 독점 입찰 수주로 연결될 것",
    "최부장의 퇴출 소식을 들은 다른 임원 중 한 명이 동요하기 시작할 것 (Block 26)"
  ],
  "callback": [
    "Block 15에서 '최부장에게 너무 많은 권한을 줬다'고 독백한 것이 이번 배신으로 현실화",
    "Block 18에서 선제 확보한 방역 물자 500억 분이 이번 위기의 핵심 카드로 활용"
  ],
  "emotional_beat": { "type": "pyrrhic_victory", "intensity": 7 },
  "genre_ext": {
    "capital_before": "1조 2,000억",
    "capital_after": "1조 1,200억",
    "capital_delta": "-800억",
    "method": "전략적 후퇴 — 단기 손실 감수 + 정치적 신뢰 자산 확보",
    "deal_type": "정부 간 물자 공여 계약",
    "leverage_used": ["선제 확보 방역 물자", "미끼 데이터 역이용", "동남아 정치 네트워크"],
    "opponent": {
      "name": "글로벌 물류 연합 (DHL-Maersk 컨소시엄)",
      "weakness_exploited": "현지 정부와의 관계 부재 — 자본력만으로 노선 확보 시도"
    },
    "success_pattern": "노선 3개 중 1개를 잃은 피로스 승리"
  }
}
```

**좋은 이유**: capital_delta 마이너스(패배), NPC 3명(1명 퇴출), callback 구체적 블록 참조, foreshadow 장기(8~10블록 후), duration "6주", 전 필드 한국어, 코드 식별자 0건.

### 9.2 나쁜 블록 (이것을 피하라)

```json
{
  "content": {
    "context": "한도준은 물류 분야에서 새로운 기회를 포착했다.",
    "event_villain": "경쟁 물류 연합이 확장을 저지하기 위해 조달 계약을 방해했다.",
    "solution": "물류 수익구조 정비 + 계약 단계화를 통해 위기를 극복하고 전략 제휴를 체결했다.",
    "reward": "Capital moved from 2,848억 to 3,161억 (+313억)."
  },
  "relationship_delta": [
    { "target": "이은호", "before": "Cooperation remained limited.", "after": "Moved to coordination." },
    { "target": "한지민", "before": "Cooperation remained limited.", "after": "Moved to coordination." }
  ],
  "foreshadow": ["다음 블록에서는 에너지관리 관련 변수가 발생할 것이다."],
  "callback": ["직전 블록의 전력망 성과가 이번 물류 전환의 발판이 되었다."]
}
```

**나쁜 이유**: reward 영문, NPC 2명 고정+before 리셋, callback 기계 패턴, foreshadow 즉시 소비, context 추상적, solution 템플릿.

---

## 10. 필드별 품질 기준 총정리

### 10.1 P0 필드 (자동화 필수 — 위반 시 파이프라인 오류)

| 필드 | 규칙 |
|------|------|
| `genre_ext.capital_before` | N블록 = N-1블록의 capital_after |
| `genre_ext.capital_delta` | capital_after - capital_before 정합 |
| `genre_ext.capital_after` | 성장률 5블록 연속 동일 금지 |
| 자본 감소 | 70블록 중 최소 3블록은 delta < 0 |
| `pov_character` | 전 블록 일관 |
| `time_span.in_story_time` | 순방향 진행 (역행 0건) |
| `regression_ext.is_regressor` | 빙의/회귀 → true |
| `relationship_delta.before(N)` | = N-1블록의 해당 NPC after |

### 10.2 P1 필드 (감리 확인)

| 필드 | 규칙 |
|------|------|
| `emotional_beat.type` | 2블록 연속 동일 금지, 전체 6종+ |
| `emotional_beat.intensity` | 3블록 연속 동일 금지, 1~10 전구간 |
| `opponent.name` | 70블록에 최소 3세력 |
| NPC 수 | 전체 최소 8명 |
| `foreshadow` | 장기 복선 5개+ (10블록+ 지연) |
| `callback` | 구체적 사건/블록 참조 (템플릿 금지) |
| `deal_type` | 3블록 이내 재등장 금지, 10종+ |
| `success_pattern` | 4종+ (실패/부분성공/피로스 포함), 동일 3회 금지 |
| `leverage_used` | 동일 세트 3회 미만, 블록별 최소 2항목 고유 |
| 패배 블록 | 최소 7개 |
| 영문 0건 | relationship_delta/foreshadow/callback/reward/stakes 전부 한국어 |
| 코드 식별자 0건 | method/death_flag/slip_up/success_pattern/weakness_exploited |
| 템플릿 로테이션 | 자카드 유사도 50%+ 쌍이 30% 미만 |
| `execution_doctrine` | 20블록 이상 동일 문장 금지 (빙의/회귀) |

### 10.3 P2 필드 (권장)

| 필드 | 규칙 |
|------|------|
| `time_span.duration` | 블록별 차별화 (3일~3개월), 전량 동일 금지 |
| `location` | 8곳+, 15블록 이내 재등장 금지 |
| `method` | 블록별 고유 전략 서술 |
| `risk_level` | "저"~"극고" 전구간 활용 |
| `global_partner` | 70블록에 최소 3곳 |
| (빙의) `death_flag` | 대단원별 다른 위기 유형 |
| (빙의) `slip_up` | 10종+, 에스컬레이션 |

---

## 11. 감정 비트 확장 목록 (20종+)

기존 4종(`resolve/pressure/breakthrough/victory`) 순환을 탈피:

| 유형 | 설명 | intensity |
|------|------|-----------|
| `triumph` | 완전한 승리 | 8~10 |
| `pyrrhic_victory` | 대가를 치른 승리 | 5~7 |
| `defeat` | 실질적 패배 | 2~4 |
| `betrayal` | 배신당함 | 7~9 |
| `revelation` | 중대한 사실 발견 | 6~9 |
| `sacrifice` | 희생적 선택 | 5~8 |
| `isolation` | 고립/고독 | 3~5 |
| `reconciliation` | 화해/관계 회복 | 5~7 |
| `escalation` | 위기 고조 | 7~9 |
| `respite` | 숨고르기/평화 | 2~4 |
| `moral_dilemma` | 윤리적 갈등 | 6~8 |
| `confrontation` | 정면 대결 | 8~10 |
| `realization` | 깨달음/자기성찰 | 4~6 |
| `humiliation` | 굴욕 | 3~6 |
| `alliance` | 새로운 동맹 | 5~7 |
| `deception` | 속임수 성공/발각 | 6~8 |
| `transformation` | 캐릭터 변화 | 5~8 |
| `countdown` | 시간 제한 긴장 | 8~10 |
| `aftermath` | 사건 후유증 | 3~5 |
| `foreshadowing` | 불길한 전조 | 4~6 |
| `rebirth` | 회귀/재시작 | 7~9 |

---

## 12. 투자물 거래 유형 확장 (15종+)

| 유형 | 적합 자본 규모 |
|------|--------------|
| 주식 장외 매입 | 50억~500억 |
| 적대적 M&A | 1,000억+ |
| 우호적 M&A | 500억+ |
| 조인트 벤처 | 100억~5,000억 |
| 컨소시엄 입찰 | 5,000억+ |
| 부실 자산 인수 | 100억~3,000억 |
| IPO/공모 | 1,000억+ |
| 사모펀드 조성 | 500억~1조 |
| 기술 라이선싱 | 50억~500억 |
| 정부 특허권/허가 | 상황별 |
| 공급망 수직 통합 | 300억~5,000억 |
| 자산유동화(ABS) | 500억+ |
| 크로스보더 스왑 | 1,000억+ |
| 전환사채(CB) 발행 | 200억~2,000억 |
| 워런트 행사 | 상황별 |

---

## 13. 파이프라인 소비 지점 정합 맵

Treatment 필드가 파이프라인 어디서 소비되는지. 이 필드가 부실하면 해당 검사에서 경고/REJECT.

| Treatment 필드 | 소비 지점 | 검사 내용 |
|----------------|-----------|-----------|
| `genre_ext.capital_*` | `_format_block_numeric_targets()` → CW self-critique | 블록 목표 자본 달성 여부 |
| `genre_ext.capital_*` | `_check_arc_vs_block_targets()` (NS-3-B) | Arc 결과 vs Treatment ±30% 괴리 |
| `genre_ext.*` | `_build_block_event_guard()` | 블록 경계 이벤트 침범 방지 |
| `content.event_villain` | Arc → Blueprint → 원고 | 빌런 행동의 서사적 기반 |
| `content.solution` | Arc → Blueprint → 원고 | 해결 방식의 서사적 기반 |
| `emotional_beat` | Director 심사 (NC-3 체크리스트) | 감정선 자연스러움 평가 |
| `relationship_delta` | NPC 연속성 검사 | NPC 관계 변화 추적 |
| `time_span` | Timeline 연속성 (NS-4) | 시간 역행/압축 감지 |
| `foreshadow/callback` | Arc 복선 관리 | 복선 심기/회수 추적 |
| `regression_ext` | 빙의/회귀 정합성 검사 | 회귀자 설정 일관성 |

---

## 14. 종합 프롬프트 템플릿 (복사-붙여넣기용)

### 14.1 Opus/Sonnet 전체 버전

```
═══════════════════════════════════════════════════
  ANTI-SHORTCUT HARNESS — 아래를 건너뛰면 전량 무효
═══════════════════════════════════════════════════

당신은 지금부터 매 블록마다 "사전 선언 → JSON → 차이 행렬" 순서로 출력한다.
순서가 틀리면 전량 재작업이다. 지름길은 없다.

[STEP 1] 사전 선언 5항목 (§3.3) — 블록마다 필수
[STEP 2] 블록 JSON 출력
[STEP 3] 10블록 완료 후 차이 행렬 (§3.4) + 자가 검증 15문항 답변
[STEP 4] NPC 추적표 (§3.5-A) — 대단원 종료 시
[STEP 5] 복선 원장 (§3.5-B) — 대단원 종료 시
[STEP 6] 자본 곡선 ASCII (§3.5-C) — 대단원 종료 시
[STEP 7] 적대자 상태 (§3.5-D) — 20블록마다

하나라도 빠지면:
→ "HARNESS VIOLATION: [누락 항목]" 을 출력하고 해당 구간을 재작성하라.
→ 절대로 무시하고 다음 블록으로 넘어가지 마라.

이 하네스의 목적: 당신이 "핵심만 읽고 나머지를 복붙"하는 것을 물리적으로
불가능하게 만드는 것이다.
═══════════════════════════════════════════════════
```

### 14.2 Gemini Flash 축소 버전

```
═══════════════════════════════════════════════════
  TREATMENT BLOCK 생성 (Gemini Flash/Pro 전용)
═══════════════════════════════════════════════════

당신은 웹소설 treatment 블록을 3개씩 생성한다.
반드시 아래 순서를 지켜라. 순서를 어기면 전량 무효.

[A] 컨텍스트 수신
  - 직전 3블록 JSON (제공됨)
  - NPC 추적표 (제공됨)
  - 복선 원장 (제공됨)
  - 이번 배치 목표 (대단원 아크에서 발췌)

[B] 사전 선언 3항목 (블록마다)
  1. 직전 상태 인용 (capital_after, beat, NPC after 복사)
  2. 자본 계산 (before = 직전 after, 변동 근거, after = 계산식)
  3. 차별화 1줄

[C] 블록 JSON 출력 (3개)

[D] 차이 행렬 + 자가 검증 (3블록 분량)

[E] 복선 원장 업데이트

## 자본 규칙
- 전부 "억" 단위 정수 (조/만 금지)
- capital_before = 직전 capital_after (예외 없음)

## 절대 금지
- beat_type 2연속 동일
- deal_type 3블록 이내 재등장
- 성장률 3연속 동일 (±2%p 이상 변동)
- NPC before ≠ 직전 after
- callback "성과가...발판" 패턴
- duration 전부 동일
- 영어 문장 금지 (전 필드 한국어)
- 코드 식별자 금지 (_01, type_N 등)

## 하네스 위반 시
→ "VIOLATION: [항목]" 출력 후 해당 블록 재작성
→ 절대로 무시하고 다음으로 넘어가지 마라
═══════════════════════════════════════════════════
```

---

## 15. 실행 순서 요약

```
0. `docs/blockguide/blockguide-integrated-order.md`를 UTF-8로 읽고 현재 단계를 판정
   ↓
1. Bible/기획안/Phase 0 존재 여부 확인
   → planning 단계면 `treatment-planning-harness.md`로 복귀
   ↓
2. Phase 0: 대단원 아크 설계 (§2)
   → 적대자 변천, NPC 타임라인, 자본 곡선, 복선 맵, 패배 계획
   ↓
3. 생산 시작 전 직전 SSOT 재오픈
   → `phase0_design` + 직전 `candidate/fixed/draft`
   ↓
4. Phase 1: 배치 생성 (§3)
   → 기본은 작은 안전 단위
   → 사전 선언 + 절대 금지 규칙 + Anti-Shortcut Harness
   ↓
5. 생성 직후 자가 점검
   → `절대 금지` 26개를 먼저 눈으로 점검
   ↓
6. Phase 2: Python 자동 교정 (§4)
   → 자본/NPC/pov/is_regressor 강제 교정
   ↓
7. Phase 3: Python 자동 검증 + 위반 블록 재생성 (§5)
   → validate_v1() + validate_v2() = 16개 패턴
   → 위반 블록만 LLM 재생성
   ↓
8. 통과한 배치만 merge
   → 실패 배치는 같은 범위만 재생성
   ↓
9. Phase 4: 3-Pass 감리 (§6)
   → 1차 전수 → 2차 오탐 제거 → 3차 최종 확정
   ↓
10. 출고 게이트 통과 (§7)
    → P0 0건, P1 0건, P2 권장 충족
    ↓
11. `production_ready = true` 확인
    → 밀도 게이트 실패 시 skeleton draft로 분류하고 재생성
    ↓
12. treatments/{작품명}_tr_block_070_draft.json 저장
    ↓
13. 사용자가 `다음 스텝` 입력 시 `bi-production-harness-v1.md`로 인계
```

---

*이 문서는 `treatment-block-production-guide.md`(8작품 560블록 전수 감사) + `dynasty-heir-remediation-harness.md`(dynasty_heir 심층 평가) + `tr-bi-loop-audit-report.md`(자동 감사 결과)를 통합한 실전 운용 하네스입니다.*
