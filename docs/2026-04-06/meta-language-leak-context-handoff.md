# Meta Language Leak Context Handoff

- Date: 2026-04-06
- Status: active context note
- Scope: TR / BI harness interpretation and operator-facing policy
- Type: context-only handoff

## 1. Why This Exists

최근 `TR` draft와 `BI` downstream에서 아래 종류의 메타 언어가 자연어 필드 안으로 스며드는 문제가 반복적으로 관측됐다.

- `Block 4의 손실선 선언`
- `ARC-01 - 원자재로 첫 증명을 만들고 ...`
- `Phase 1에서 얻은 카드`
- `Stage 3에서 회수될 복선`

이 표현들은 감리용 메타 앵커로는 편하지만, downstream으로 복사될 경우 다음 같은 오염을 만들 수 있다.

- Stage 2 -> 3 -> 4를 거치며 메타 문구가 살아남음
- 작중 인물이나 내레이터가 `Block 3`, `ARC-01` 같은 말을 하는 메타 침식
- `foreshadow/callback` 설명이 자연어가 아니라 내부 구조 설명문으로 굳어짐
- `section_rotation`이 사람이 읽는 구간 제목이 아니라 기계용 ID처럼 남음

핵심 문제는 단순 미관이 아니라, **메타가 서사 안으로 내려와 작중 언어를 오염시키는 것**이다.

## 2. Decision

이번 wave의 결정은 하나다.

**메타는 전용 구조 필드에서만 허용하고, 사람이 읽는 자연어 필드는 전부 자연어로 유지한다.**

즉,

- 기계가 읽는 구조 정보
- 사람이 읽는 서사 정보

를 분리한다.

## 3. Allowed vs Forbidden

### 3.1 Allowed

아래는 기계용 구조 필드로 본다.

- `block_id`
- `arc_id`
- `arc_no`
- `phase_no`
- `stage_no`
- `foreshadow_targets`
- `callback_sources`

여기에는 번호/구조 정보가 들어가도 된다.

### 3.2 Forbidden

아래는 자연어 또는 라벨 필드로 본다.

- `content.*`
- `stakes`
- `power_shift.*`
- `relationship_delta.before/after`
- `genre_ext.method`
- `genre_ext.success_pattern`
- `foreshadow`
- `callback`
- `section_rotation`
- `arc_section`
- `phase`
- `phase_label`

이 영역에는 `Block / ARC / Phase / Stage`류 번호 메타가 들어가면 안 된다.

## 4. Meta Taxonomy

이번에 차단 대상으로 보는 최소 메타 lexicon은 아래다.

- `Block 3`
- `B12`
- `블록 7`
- `ARC-01`
- `Arc 2`
- `아크 3`
- `Phase 1`
- `페이즈 2`
- `Stage 4`
- `스테이지 3`

운영 메타(`PASS/HOLD/REJECT`, `WG-V2`, `TR/BI/canon`)는 우선 문서 규칙으로만 다루고, validator는 위 4계열을 먼저 강하게 집행한다.

## 5. Natural-Language Replacement Rule

메타를 완전히 지우는 게 목적이 아니다.

메타를 **자연어 + 구조 필드**로 분리하는 게 목적이다.

### 5.1 Good

```json
"foreshadow": [
  "보험 인상률, 스크랩률, 슬롯 취소율의 세 신호가 하나의 손실선으로 모이기 시작한다."
],
"foreshadow_targets": [4, 9]
```

```json
"section_rotation": "원자재로 첫 증명을 만들고 금융위기 숏을 준비하다"
```

### 5.2 Bad

```json
"foreshadow": [
  "trigger set A가 Block 4의 손실선 선언과 Block 9의 적중으로 이어진다."
]
```

```json
"section_rotation": "ARC-01 - 원자재로 첫 증명을 만들고 금융위기 숏을 준비하다"
```

## 6. Why Label Fields Are Also Blocked

`section_rotation`, `arc_section`, `phase` 같은 필드는 기계용 ID처럼 보이기 쉽지만, 실제 운영상으로는 사람이 읽는 라벨이다.

따라서:

- 존재해야 한다
- 하지만 값은 자연어여야 한다

즉 `label present`와 `label clean`은 다른 문제다.

이 구분이 없으면 `section_rotation_present = true`인데도 실제 값은 `ARC-01 - ...`처럼 메타가 남아 있는 상태를 놓치게 된다.

## 7. Downstream Risk This Rule Is Preventing

가장 중요한 우려는 아래 같은 메타 침식이다.

- `BLOCK 3에서 얻은 물건으로...`
- `내가 Block 14에서 말한 내용을 기억하십니까?`
- `ARC-02에서 시작된 복수선이 이제 회수된다`

이건 감리용 텍스트가 작중 언어로 오염된 상태다.

이번 규칙은 정확히 이 위험을 막기 위해 들어갔다.

## 8. Default Operating Choice

기본 선택은 아래다.

1. 메타는 전용 구조 필드에서만 허용
2. 자연어/라벨 필드는 자연어만 허용
3. 기존 live/archive 파일 대량 백필은 이번 wave 범위 밖
4. 기존 draft는 새 감리 기준에서 적발되게 둠
5. 자동 치환/자동 수선은 후속 파스로 분리

즉 이번 wave는 **차단 규칙 정규화**가 목적이지, **기존 자산 청소**가 목적이 아니다.

## 9. New Audit Interpretation

새 감리에서는 두 종류를 구분해 본다.

- `diegetic_meta_ref_*`
  - 서사/자연어 필드의 메타 누수
- `label_meta_ref_*`
  - `section_rotation`류 라벨 필드의 메타 누수

의미는 다르지만 둘 다 실패 사유가 될 수 있다.

## 10. Non-Goals

이번 문맥 문서는 아래를 다루지 않는다.

- 기존 draft 자동 정리 파스
- 메타 표현의 자동 자연어 치환
- TR/BI 전체 재생성
- stage runtime consumer의 별도 sanitizer 설계

그건 다음 wave로 분리한다.

## 11. Operator Summary

운영자가 기억할 한 줄 요약은 이거다.

**번호 메타는 구조 필드로 보내고, 사람이 읽는 필드에는 자연어만 남긴다.**

다시 말해:

- `foreshadow` / `callback` = 뜻
- `foreshadow_targets` / `callback_sources` = 번호
- `section_rotation` = 자연어 제목
- `Block / ARC / Phase / Stage` = 인간용 서사 필드에 금지
