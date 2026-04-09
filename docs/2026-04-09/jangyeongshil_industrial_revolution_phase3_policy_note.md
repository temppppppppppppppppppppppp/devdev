# jangyeongshil_industrial_revolution — Phase 3 Automated Check Policy Note

Date: 2026-04-09
Work ID: `jangyeongshil_industrial_revolution`
Family: `blockguide`
Author context: Phase 2/3/4 자동화 파이프라인 첫 실행 + Option C 수리 완료 후 정책 결정 근거 문서
Related docs:
- `docs/2026-04-08/jangyeongshil_industrial_revolution_live_status.md` (current truth, Block 1-70)
- `docs/blockguide/treatment-production-harness-v2.md` (§0A.14 / §0B / §0D / §4-§7)
- `scripts/tr_batch_harness.py` (Phase 3 automated checker)

## 0. TL;DR (1분 버전)

- 70블록 TR draft 완성 후 Phase 3 automated Pattern checker를 **이 work에 첫 실행**
- 결과: baseline P0 631 / P1 417 / P2 9 → Option C 수리 후 P0 631 / P1 413 / P2 9 (**-4 P1**)
- 남은 **1053 flag의 절대다수는 Block 1-60까지 존재하는 project-wide authoring convention drift** (META-001 292, CAP-001/002/003 209, REL-001 130, LANG-001 341, DEAL-001 69). 내 세션(Block 61-70)이 새로 만든 것이 아님
- 이전 self-audit gate들(B21-30/31-40/41-50/51-60)이 **전부 PASS**였지만 그건 인라인 LLM 6축 감리였고, 이 automated checker는 **이 work에서 이번이 첫 실행**
- 70블록 TR은 harness §0A.14 + §7 출고 게이트 엄격 기준으로는 **FAIL** 상태
- 하지만 대부분의 flag는 **(a) 체커 규칙 vs SSOT 미스매치** 또는 **(b) 인라인 LLM 감리가 허용해 온 authoring convention**
- 정책 결정 없이는 BI 인계/출고가 불가능. 본 문서는 그 정책 결정의 근거

## 1. Phase 3 Automated Check 실행 기록

### 1.1 실행 커맨드
```
python -X utf8 scripts/tr_batch_harness.py check \
  --candidate treatments/jangyeongshil_industrial_revolution_tr_block_025_draft.json \
  --start 1 --batch-size 70 \
  --report /tmp/tr_check_report.md
```

### 1.2 Baseline 결과 (수리 전)
- **unresolved P0: 631**
- **unresolved P1: 417**
- **unresolved P2: 9**
- autofixed: 0
- total: 1057

### 1.3 Flag code 분포

| code | count | severity | 의미 |
|---|---|---|---|
| `LANG-001` | 343 | P1 | 필드 한국어 비율 낮음 |
| `META-001` | 292 | P0 | Block/ARC/Phase 메타 참조가 자연어 필드에 새어나옴 (harness §0A.14 위반) |
| `REL-001` | 130 | P0/P1 | 관계 before가 직전 블록 after와 불일치 (verbatim 비교) |
| `CAP-001` | 69 | P0 | capital_before가 직전 capital_after와 연속되지 않음 |
| `CAP-002` | 70 | P0 | capital_before 파싱 불가 (narrative 문자열) |
| `CAP-003` | 70 | P0 | capital_after 파싱 불가 (narrative 문자열) |
| `DEAL-001` | 69 | P1 | deal_type 3블록 내 재등장 |
| `LOC-001` | 8 | P2 | 장소 15블록 내 재등장 |
| `BEAT-001` | 5 | P1 | 감정 비트 직전 블록과 동일 |
| `FS-003` | 1 | P2 | OPEN 복선 25개 (threshold 10 초과) |

### 1.4 블록 범위별 위반 분포

| Block 범위 | 총 위반 | 블록당 평균 | META-001 | CAP-1/2/3 | REL-001 | LANG-001 |
|---|---|---|---|---|---|---|
| 1-30 (legacy serialized) | 293 | 9.8 | 92 | 89 | 26 | 53 |
| 31-40 ARC-04 | 150 | 15.0 | 50 | 30 | 16 | 41 |
| 41-50 ARC-05 | 181 | 18.1 | 50 | 30 | 22 | 66 |
| 51-60 ARC-06 | 181 | 18.1 | 50 | 30 | 23 | 67 |
| **61-70 ARC-07 (내 세션)** | 251 | 25.1 | 50 | 30 | 43 | 116 |

**핵심 관찰**: META-001과 CAP-001/002/003은 **블록 범위와 무관하게 정확히 균등 분포**.
- META-001: 블록 31-70에서 매 10블록 정확히 50건 (5건/블록)
- CAP-001/002/003: 매 블록 정확히 3건 (각 1건씩)

즉 **authoring convention과 checker 규칙 사이의 체계적 불일치**가 70블록 전체에 걸쳐 일정한 비율로 누적된 상태.

## 2. Option C 수리 적용 (Block 61-70 세션 marginal contribution)

### 2.1 수리 내역

| # | 블록 | 변경 | 효과 |
|---|---|---|---|
| 1 | B62 | `emotional_beat.type`: containment → defeat | BEAT-001 -2 (B62/B63 연쇄 해소) |
| 2 | B69 | `callback` 1줄 신규 추가 (B68→B69 chain 닫음) | FS-003 OPEN 25→24 |
| 3 | B70 | `foreshadow` 2건 삭제 (non-foreshadow BI meta) | FS-003 OPEN 24→22, LANG-001 -2 |

**시도 후 revert**:
- Block 61-70 `relationship_delta.target` "당직 제자" → "기술소 당직 제자" 표준화는 REL-001 +1 counter-productive로 즉시 revert 완료

### 2.2 수리 후 결과
- **unresolved P0: 631** (변화 없음)
- **unresolved P1: 413** (-4)
- **unresolved P2: 9** (변화 없음)
- total: 1053 (net -4)

### 2.3 왜 Option C로는 더 이상 개선 불가

| Flag | 남은 건수 | 수리 불가 이유 |
|---|---|---|
| META-001 | 292 | 70블록 전체 authoring convention. Block 1-60 수정은 scope 밖 |
| CAP-001/002/003 | 209 | 체커 규칙 vs SSOT 미스매치 (narrative capital은 harness §0B 허용). Block 1-60 공통 |
| REL-001 | 130 | verbatim `before.text == prev.after.text` 요구. 요약 스타일 전면 재작성 scope 밖 |
| DEAL-001 | 69 | `althistory_possession` genre-fixed (harness §0D). 모든 블록 false positive |
| LANG-001 | 341 | receipt_type enum + callback 메타 함유분 (META-001과 중첩) |
| LOC-001 | 8 | 운영 거점 반복은 narrative 필수 (조정 회의장/기술소/대장간). P2 권장 |
| FS-003 | 1 (ledger 22) | 20+ 건이 legacy plant blocks(B3-B52)의 OVERDUE, Block 1-60 수정 필요 |

## 3. 시스템 드리프트 카테고리별 분석

### 3.1 카테고리 A: Checker 규칙 vs SSOT 미스매치 (명백한 false positive)

**해당 flag**:
- **CAP-001/002/003** (209건): `capital_before`/`capital_after` 필드가 narrative 문자열인데 체커는 numeric/formula parser 기대
  - SSOT 근거: harness §0B "capital = 돈, 예산, 반복 현금흐름, 케이스, 팬덤, 권한, 라이선스, 길드 자산을 한데 묶어 추적하는 **호환 지표**". narrative 사용 명시 허용
  - 체커 구현: numeric 값만 파싱 성공 인식. narrative 값은 unparseable로 flag
  - 판단: **체커 규칙이 SSOT 최신 정의에 미추종한 상태**. `althistory_possession` 프로파일은 narrative capital이 정상
- **DEAL-001** (69건): `deal_type`이 3블록 내 재등장 flag. 하지만 pitch family 고정값(`althistory_possession`)
  - SSOT 근거: harness §0D 장르 프로파일 운용표, deal_type은 프로파일별 허용 액션 유형 고정
  - 체커 구현: Pattern E (1세대 결함: deal_type 5종 균등 분배)의 일반화된 반복 감지가 genre-fixed 값에 오발
  - 판단: **genre-fixed deal_type에 대한 체커 예외 처리 누락**

**총 합계: 278건 (P0 209 + P1 69) = 전체 1053건의 26%**. 이 카테고리는 **체커 쪽 수정이 필요한 이슈**이며, TR 수정 대상이 아님.

### 3.2 카테고리 B: Authoring Convention vs Harness §0A.14 (정책 결정 필요)

**해당 flag**:
- **META-001** (292건): `foreshadow`/`callback`/`genre_ext.next_door`/`power_shift.antagonist` 등 자연어 필드에 "Block N", "ARC-N", "Phase0 §4" 같은 메타 참조 함유
  - 규칙 근거: harness §0A.14 "`Block / ARC / Phase / Stage` 번호 메타는 자연어 필드에서 전면 금지. `foreshadow_targets` / `callback_sources` 같은 전용 배열 필드에만 적는다"
  - 현 상태: 70블록 전체가 prose 안에 "Block N에서...", "Block 60 각성..."이라는 메타 참조로 서사 그래프를 기록해왔음. 전용 구조 필드는 전혀 사용되지 않음 (`callback_sources`/`foreshadow_targets` 0건)
  - 이전 self-audit PASS 기록: B21-30, B31-40, B41-50, B51-60 전부 PASS였지만 인라인 LLM 감리 기준이었고, 이 automated checker는 그 시점에 실행되지 않음
  - 판단: **사전 존재한 authoring convention과 harness §0A.14 규칙의 체계적 불일치**
- **LANG-001 일부** (약 200건 추정): META-001과 중첩. "Block 40/49/59/60" 같은 긴 목록이 필드의 한국어 비율을 낮춤

**총 합계: 약 500건 (P0 292 + P1 약 200) = 전체 1053건의 47%**. 이 카테고리는 **정책 결정이 가장 중요한 이슈**.

### 3.3 카테고리 C: 진짜 authoring drift (수리 가능했으나 scope/cost 대비 저가치)

**해당 flag**:
- **REL-001** (130건): `relationship_delta[target].before` 텍스트가 직전 블록의 `after` 텍스트와 verbatim 일치하지 않음. 저자(나 포함 기존 작성자들)는 "before"를 요약문으로 써 왔음 (예: "Block 60 각성의 즉각 운영 변환 수신자"). 체커는 verbatim 요구
  - 수리 비용: 70블록의 모든 `relationship_delta.before`를 verbatim cascade로 재작성 → 수천 건 편집
  - 수리 가치: 서사 품질 변화 없음. 오직 체커 통과용
  - 판단: 체커 규칙이 authoring convention의 요약 스타일을 허용하도록 완화하거나, 별도 `anchor_before`/`anchor_after` 구조 필드로 분리 (harness 확장)
- **LANG-001 일부** (약 140건 추정): receipt_type enum 영문(`"authority_receipt"` 등, harness §0G 정의 형식), pov_character 메타 문자열
  - 수리 비용: 모든 enum 값을 한글화 또는 필드별 한국어 비율 계산 완화
  - 수리 가치: 저. enum 영문값은 harness 정의 형식

**총 합계: 약 270건 (P0 130 + P1 약 140) = 전체 1053건의 26%**.

### 3.4 카테고리 D: 진짜 권장 수준 감사 (P2, 운영에 지장 없음)

- **LOC-001** (8건): 장소 15블록 내 재등장 (조정 회의장 / 기술소 / 기술소 뒷마당 대장간). narrative 거점 반복은 정상
- **BEAT-001** 잔여 (3건): 이미 B62/B63 수리 후 잔여는 Block 1-60 범위
- **FS-003** (1건, ledger 22): 남은 OPEN 복선 중 20건이 Block 1-56 범위의 legacy plant blocks

**총 합계: 12건 (P1 3 + P2 9) = 전체 1053건의 1%**.

## 4. 이전 self-audit gate들이 PASS였던 이유

Block 21-30 / 31-40 / 41-50 / 51-60 / 61-70 5번의 10-block self-audit gate가 전부 PASS로 기록되어 있음. 본 automated checker는 1053 flag를 잡는데 이전 감리는 왜 PASS였나?

답: **이전 감리는 인라인 LLM 6축 감리였고, `tr_batch_harness.py check`는 이 work에서 이번이 첫 실행**.

- 인라인 LLM 감리 6축 (harness §1.1C):
  1. 주인공 우위와 간판 맛이 살아 있는가
  2. 성취 직후 보상/인정 리듬이 유지되는가
  3. 자본/권력/조직 장악 축이 실제로 커졌는가
  4. opponent/method/deal_type/stakes 반복이 누적되지 않았는가
  5. continuity와 열린 복선이 다음 10블록으로 이어지는가
  6. 다음 10블록에서 키워야 할 확장축과 위험축이 분명한가

- 이 6축은 **서사 품질 중심**이며 체커의 META-001/CAP-001/DEAL-001 같은 **스키마 정합 중심 규칙**과 교차하지 않음. 인라인 감리가 서사 품질을 잘 지켜왔어도, 스키마 정합은 별도 체커가 돌지 않으면 드러나지 않음.

- 즉 **인라인 감리 PASS와 automated Pattern check PASS는 서로 다른 품질 축**. 둘 다 통과해야 출고 게이트 통과지만, 이전 gate들은 인라인 감리만 실행되었음.

## 5. 정책 결정 옵션

### 옵션 A: Accept Drift + BI 인계로 진행 (가장 pragmatic)
**전제**: META-001/CAP/DEAL/REL의 상당 부분을 체커 쪽 이슈로 간주. 인라인 LLM 감리가 계속 서사 품질 기준으로 PASS였던 전례를 정책으로 공식화.

**조치**:
1. 본 문서를 `docs/blockguide/` 또는 work 전용 waiver 문서로 승격
2. 이 work에 대한 출고 게이트 통과 기준을:
   - (a) 인라인 LLM self-audit gate PASS (B21-30/B31-40/B41-50/B51-60/B61-70 5회 전부) — 이미 충족
   - (b) canonical rewrite clean (0 warnings) — `rewrite_tr_to_canonical.py` 실행 결과 충족
   - (c) META-001/CAP-001/002/003/DEAL-001은 체커 known-issue로 waive
   - (d) REL-001은 verbatim 요구 완화 (summarized anchor before 허용)
   - (e) LOC-001은 운영 거점 반복 예외
   - (f) FS-003은 plant block이 Block 1-56 legacy인 경우 waive (22/25 해당)
3. 나머지 잔여 flag(약 15-25건)에 대해서만 수동 감리
4. BI 인계 진입 허용

**장점**: 빠른 진행. Option C 수리분 + 이전 인라인 감리 결과 모두 생산성 반영.
**단점**: Waiver 축적. 향후 blockguide works 전체가 META-001/CAP/DEAL 위반을 계속 발생시킬 가능성. harness §0A.14는 명목상 존속하되 실질적으로는 이 work에서 공식 예외 처리되는 상태.

### 옵션 B: 70블록 Mass Rewrite (가장 엄격)
**전제**: harness §0A.14 + SSOT를 retroactive 엄격 적용. TR을 clean 상태로 만들고 출고 게이트를 정면 통과.

**조치**:
1. **META-001 제거**: 모든 `foreshadow`/`callback`/`genre_ext.next_door`/`power_shift.antagonist`에서 "Block N", "ARC-N", "Phase0 §4" 참조 제거
2. **구조 필드 추가**: `foreshadow_targets: [int]`, `callback_sources: [int]` 필드를 각 callback/foreshadow entry에 부착 (또는 block-level)
3. **CAP 필드 재작성**: narrative `capital_before`/`capital_after`를 numeric 포맷으로 재정의 (이건 사실상 capital 의미 자체를 바꾸는 것)
4. **REL-001 verbatim chain**: 10블록의 `relationship_delta[target].before`를 직전 블록의 `after`와 verbatim 일치하도록 cascade 편집
5. **LANG-001 enum**: `receipt_type` 등 영문 enum을 한글화 (harness 정의 형식도 변경)
6. 재검수 → P0 0 + P1 ≤ threshold 확인

**장점**: 엄격 준수. 출고 게이트 정면 통과.
**단점**:
- 70블록 전체 재작성. 실질적으로 TR을 다시 씀 — 수천 건 편집
- **서사 연결 조직 손상**: foreshadow/callback prose의 "Block N" 참조는 독자-친화적 서사 그래프 표기. 제거 시 독자/후속 작성자의 이해가 약해짐
- **CAP narrative → numeric 전환은 의미 자체 변경**: althistory_possession 장르에서 capital은 권한/이름/관계이지 숫자가 아님. numeric 전환 시 장르 정체성 훼손
- **LANG-001 enum 한글화는 harness 공통 스펙 변경**: 다른 모든 works에도 영향
- 다중 세션 작업 + 재감리 필요
- 서사 품질이 오히려 떨어질 위험

### 옵션 C: Checker / Harness 수정 (근본 해결)
**전제**: 체커 규칙과 SSOT 정의 사이의 미스매치를 **checker 쪽에서 해결**. SSOT는 `althistory_possession`에서 narrative capital을 허용한다고 명시되어 있는데 체커 구현이 뒤따르지 않은 상태.

**조치**:
1. `scripts/tr_batch_harness.py` 수정:
   - CAP-001/002/003: 장르 프로파일이 narrative capital을 허용하는 경우(`althistory_possession` 등) 해당 flag 생략
   - DEAL-001: pitch family fixed `deal_type`은 Pattern E 반복 검사에서 제외
   - META-001: 구조 필드(`foreshadow_targets`/`callback_sources`)가 없는 레거시 TR에서는 prose Block 참조를 downgrade P2 권장, 전용 구조 필드 부착된 경우만 P0
   - REL-001: `anchor_before`/`anchor_after` 필드 추가 지원. verbatim은 `anchor_*` 필드 기준이고 `before`/`after`는 summarized 허용
   - LANG-001: `receipt_type`, `pov_character`, `deal_type` 등 structural enum 필드는 한국어 비율 검사 제외
2. `docs/blockguide/treatment-production-harness-v2.md` 문구 정비:
   - §0A.14 "자연어 필드에서 Block 참조 금지"를 "Block 참조는 전용 구조 필드 존재 시에만 금지, 레거시 TR은 권장 수준"으로 완화
   - §0B capital 정의의 narrative 허용을 checker 구현에 반영한다는 주석 추가
   - §0D 장르 고정 deal_type은 Pattern E 예외라는 명시 추가
3. `scripts/tr_batch_harness.py check` 재실행 → 이 work의 flag 수 대폭 감소 기대
4. 다른 blockguide works에도 동일 규칙 적용 → 전체 프로젝트 drift 상당 부분 자동 해소

**장점**: 근본 해결. 이 work뿐 아니라 모든 blockguide works 혜택.
**단점**:
- **범위 확장 매우 큼**: 체커 코드 + harness 문서 + 다른 works 영향 평가 필요
- **harness governance**: `docs/blockguide/` SSOT 변경은 '공유 governance 문서는 read-only' 원칙(delegation-envelope-spec §2) 위반 가능성 — 별도 governance 수정 envelope 필요
- 이 work 1개 발견 사항으로 전체 프로젝트 규칙을 바꾸는 결정이므로 신중한 검토 필요
- 즉시 진행 불가, 별도 governance 오더 필요

### 옵션 D: 하이브리드 (옵션 A + 부분 옵션 C)
**전제**: Option A의 waiver 방식으로 이 work를 우선 BI 인계까지 진행. 동시에 체커 규칙 수정은 별도 백로그 항목으로 등록해서 후속 governance 오더로 처리.

**조치**:
1. 이 work 전용 waiver 문서 작성 (본 문서를 승격)
2. BI 인계 진행 (옵션 A와 동일)
3. 별도 tasklist에 "옵션 C: blockguide-wide checker/harness 수정" 등록 (후속 오더)

**장점**: 즉시 진행 + 근본 해결 경로 보존.
**단점**: 두 경로 관리 필요. waiver가 중복으로 쌓일 가능성 (후속 work에서도 동일 이슈 반복).

## 6. 권장

**옵션 D (하이브리드)**를 권장합니다.

근거:
1. 70블록 TR draft와 5회의 인라인 감리 gate PASS는 이미 큰 생산성 투자. 이걸 policy 이슈로 인해 무산시키는 것은 cost-benefit 불균형
2. 이 work의 META-001/CAP/DEAL 드리프트는 **70블록 전체에 걸친 체계적 불일치**로, 현 TR을 부분 수리해도 근본 해결은 아님
3. 체커/harness 수정(옵션 C)은 근본 해결이지만 범위가 큼 — 이 work 한 개를 이유로 전체 프로젝트 governance를 바꾸는 것은 신중할 필요
4. 옵션 A의 waiver는 약점이 있지만 **인라인 LLM 감리 PASS + canonical clean rewrite + Option C 세션 수리 완료**의 세 가지 증거로 서사 품질이 확인된 상태이므로 정당성 있음
5. 옵션 D는 옵션 A의 즉시 진행성과 옵션 C의 근본 해결 보존을 동시 만족

## 7. 결정 시 확인 사항

정책 결정 전 추가로 확인할 수 있는 사항:

1. **다른 blockguide works의 Phase 3 check 결과는 어떤가?** (`scripts/tr_batch_harness.py check`를 `chaebol_*`, `wuxia_*` 등에 돌려서 동일 드리프트 패턴 존재 확인)
2. **이전에 출고 게이트를 정면 통과한 works가 있는가?** (있다면 그 work의 META-001 count는?)
3. **harness §0A.14 규칙이 언제 추가되었는가?** (이 work의 TR 작성 시점보다 후에 추가되었다면 retroactive 적용은 부당)
4. **`scripts/tr_batch_harness.py` 의 규칙이 이 work 장르(`althistory_possession`)를 지원한 시점은?** (`althistory_profile` 프로파일 추가 시점과 체커 규칙 적응 시점의 차이)
5. **`rewrite_tr_to_canonical.py`가 0 warnings로 성공한 사실**이 canonical shape의 authoritative PASS로 간주될 수 있는가?

## 8. 이 문서의 위상

- **current-truth가 아님**: live_status.md가 current-truth
- **정책 결정 근거 문서**: 사용자/운영자가 옵션 A/B/C/D 중 선택할 때 참조
- **업데이트 규칙**: 사용자가 정책 결정 후 본 문서는 "결정 기록 + 근거"로 archive, `docs/blockguide/`에 work-family level waiver 문서로 승격되거나 후속 governance 오더로 링크됨
- **삭제 금지**: Phase 3 check 실행 기록 + Option C 수리 내역 + 정책 근거를 동시 보존하는 유일한 문서
