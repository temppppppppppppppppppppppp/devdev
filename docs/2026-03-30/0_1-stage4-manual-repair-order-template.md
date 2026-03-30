# 0_1 Stage 4 Manual Repair Order Template

Date: 2026-03-30
Status: ready-to-send
Project: `0_1`
Purpose: Stage 4 결과 감리 후 `P1` 원고 수동 보정이 필요할 때 바로 던질 오더 템플릿

## 1. Use Cases

이 템플릿은 아래 상황에서만 쓴다.

- Stage 4 run 완료 후
- `P1 fix-needed` episode가 특정됨
- 코드 수정이나 재실행보다 `authoritative manual repair`가 더 빠를 때

쓰지 말아야 할 때:

- run 아직 진행 중
- root cause code fix가 먼저 필요한 blocker
- 전체 regeneration이 더 맞는 구조 붕괴

## 2. Filled Prompt Template

```text
글도비 시스템 오더. 이번 턴은 `0_1` Stage 4 manuscript의 `manual authoritative repair`만 수행하라. 코드 수정 금지, Stage 4 재실행 금지, canary 실행 금지. 원고/DB authoritative patch -> export sync -> read-back 검증만 하고 멈춘다.

대상 프로젝트:
- `C:\Users\User\Desktop\글도비\projects\0_1`

근거 문서:
- `{AUDIT_DOC_PATH}`

수정 대상 episode:
- `{EP_LIST}`

원칙:
- primary source는 `project_data.db` 안의 manuscript payload다
- txt export만 고치지 말고 DB를 먼저 고쳐라
- 이번 턴은 지정된 episode만 수정
- regeneration 금지
- 코드 수정 금지
- 문장 polish 금지
- narrative 뜻을 바꾸지 말고 factual/continuity drift만 patch

P1 수정 항목:
{PATCH_ITEMS}

저장 순서:
1. `project_data.db` manuscript payload 수정
2. `drafts/ep_XXXX.txt` export 재반영
3. DB / txt read-back 정합 검증

필수 검증:
1. drift 잔존 0건
2. blueprint / arc truth와 충돌 없음
3. DB read-back == txt export
4. 지정 episode 외 비영향

출력 형식:
1. Patch summary
2. DB read-back anchors
3. TXT read-back anchors
4. Remaining watchlist
5. Final verdict
- `READY FOR NEXT STEP`
- 이유 5줄 이내

중요:
- 이번 턴은 지정 episode manual repair만
- regeneration 금지
- 코드 수정 금지
- Stage 4 재실행 금지
- 보고 후 멈춤
```

## 3. Patch Item Snippets

아래는 자주 쓰는 snippet이다.

### Numeric / Currency Drift

```text
- EP{N}: KRW-authoritative canon과 충돌하는 USD/금액 drift 제거
- blueprint/arc/hud truth 기준 수치로 통일
- 상품 가격표시와 capital/deployment 수치를 구분해서 보정
```

### Timeline Drift

```text
- EP{N}: manuscript opening / body / ending timeline을 arc truth 기준 월/주/일로 통일
- integrated beat는 유지하고 시간 점프만 보정
```

### Identity / Naming Drift

```text
- EP{N}: broker / institution / contract-month naming을 upstream truth 기준으로 통일
- 동일 entity의 별칭 drift만 제거하고 plot role은 유지
```

### Relationship Regression

```text
- EP{N}: relationship state가 직전 episode 종료 상태보다 뒤로 후퇴한 표현 제거
- dialogue/inner monologue에서 from_state regression만 보정
```

### Missing Beat / Empty Coverage

```text
- EP{N}: Stage 3 blueprint의 핵심 scene obligation이 원고에서 누락된 구간만 최소 보강
- 새 사건 발명 금지, 기존 beat 복원만 수행
```

## 4. Recommended Repair Mode Map

- 숫자/통화 단위 drift
  - 기본 `local/manual patch`
- timeline month/week drift
  - 기본 `local/manual patch`
- naming drift
  - 기본 `local/manual patch`
- scene beat 누락
  - 작으면 `manual patch`
  - 구조가 크면 `bounded regeneration` 검토
- 전체 continuity 붕괴
  - `manual repair` 대신 `regeneration` 쪽 검토

## 5. Pre-Send Fill Checklist

오더 던지기 전에 아래를 채운다.

- `{AUDIT_DOC_PATH}` 입력
- `{EP_LIST}` 입력
- `{PATCH_ITEMS}`를 episode별로 구체화
- `P1`만 남겼는지 확인
- `P2` watchlist를 같이 고치려는 과잉 범위 제거

## 6. 3-Pass Audit

### Pass 1

- prompt가 DB-first authoritative repair 원칙을 지키는지 확인

### Pass 2

- patch items가 regeneration scope로 부풀지 않았는지 확인

### Pass 3

- output 형식과 검증 항목이 실제 read-back 중심인지 확인

Final judgment:

- Stage 4 P1 수동 보정용 템플릿으로 충분
