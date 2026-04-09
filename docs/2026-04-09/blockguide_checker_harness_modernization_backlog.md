# Blockguide — Checker / Harness Modernization Backlog

Date: 2026-04-09
Status: **BACKLOG** (옵션 C, 후속 governance 오더 대기)
Scope: **blockguide family 전체** (family-wide governance)
Priority: **Medium-High** (서사 품질에 영향 없지만 출고 게이트 정상화에 필요)
Triggering evidence: `jangyeongshil_industrial_revolution` Phase 3 automated check 결과 (baseline 1053 flags, 85% systemic drift)
Related docs:
- `docs/2026-04-09/jangyeongshil_industrial_revolution_phase3_policy_note.md` (정책 결정 근거)
- `docs/2026-04-09/jangyeongshil_industrial_revolution_phase3_waiver.md` (work-level waiver, 옵션 A 부분)
- `docs/blockguide/treatment-production-harness-v2.md` (수정 대상)
- `scripts/tr_batch_harness.py` (수정 대상)

## 0. 배경

`jangyeongshil_industrial_revolution` work의 Phase 3 automated check 실행 결과, 70블록 TR에 1053 flag가 보고됨. 이 중 약 85%가 다음 두 가지 유형:

1. **Checker 규칙 vs SSOT 미스매치**: `althistory_possession` 장르는 narrative capital을 SSOT에서 허용 (harness §0B)하지만 체커의 CAP 규칙은 numeric parser 기대. `deal_type` genre-fixed 값을 Pattern E 균등 분배 감지가 오탐.
2. **Authoring Convention vs harness §0A.14**: 70블록 전체가 prose 안에 "Block N" 참조로 서사 그래프를 기록해왔으나, harness §0A.14는 전용 구조 필드(`foreshadow_targets`/`callback_sources`)만 허용.

이 두 유형은 개별 work 단위 수리로는 해결되지 않음 (다른 blockguide works에도 동일 발생 가능성 높음). **governance-level (체커 + harness) 수정**으로만 근본 해결 가능.

본 백로그는 그 modernization 작업의 범위를 명시한다.

## 1. 백로그 항목 목록

### BL-1: `tr_batch_harness.py` — CAP 규칙 장르 인식

**현 상태**: `CAP-001/002/003` 규칙이 `capital_before`/`capital_after`를 numeric parser로 파싱 시도. narrative 문자열은 전량 FAIL.
**문제**: harness §0B "capital = 호환 지표 (돈·권한·관계·라이선스)"와 체커 구현 불일치. `althistory_possession` 장르는 narrative capital이 정상.
**수정 방향**:
1. 블록의 `genre_ext.type` 또는 pitch family에서 장르 프로파일 판별
2. `business_growth_profile`/`investment_market_profile` 등 numeric-capital 장르는 기존 parser 유지
3. `althistory_possession`/`medical_professional_profile`/`urban_power_profile` 등 narrative-capital 허용 장르는 **단조 변화 검사**만 수행 (capital 텍스트 길이 또는 권한 키워드 수가 monotonic increase/reasonable transition)
4. 또는 narrative-capital 장르 전체에 대해 CAP-001/002/003을 P2 권장 수준으로 downgrade

**영향**:
- `jangyeongshil_industrial_revolution`: -209 P0 flags
- 기타 `althistory_*` / `urban_power_*` / `medical_*` works: 유사 효과 기대

**효과 우선순위**: **High** (P0 flag 209건 직접 해소)

### BL-2: `tr_batch_harness.py` — DEAL-001 genre-fixed 예외

**현 상태**: `DEAL-001` 규칙이 `deal_type`이 3블록 내 재등장 시 flag (Pattern E "5종 × 14회 균등 분배" 감지의 단순화).
**문제**: harness §0D 장르 프로파일 운용표 — `deal_type`은 pitch family 고정값. `althistory_possession` 등 단일 deal_type family는 모든 블록 동일 = 정상.
**수정 방향**:
1. pitch family에서 `deal_type` 고정 여부 판별
2. 고정 family의 `deal_type`은 Pattern E 검사 대상에서 제외
3. 또는 `genre_ext.type`이 family-fixed `deal_type`을 명시한 경우 해당 값만 제외

**영향**:
- `jangyeongshil_industrial_revolution`: -69 P1 flags
- 기타 family-fixed deal_type works: 유사 효과

**효과 우선순위**: **Medium** (P1 flag 69건 해소, 서사 품질 영향 0)

### BL-3: `tr_batch_harness.py` + harness §0A.14 — META-001 구조 필드 부재 시 downgrade

**현 상태**: `META-001` 규칙은 자연어 필드에서 "Block N" prose 참조를 전량 P0 FAIL로 플래그.
**문제**: harness §0A.14 원칙("전용 구조 필드 `foreshadow_targets`/`callback_sources`에만 적는다")은 합리적이지만, **현존 70블록 draft들은 전부 prose 참조로 작성됨**. retroactive 적용은 mass rewrite.
**수정 방향** (세 가지 옵션):

**옵션 BL-3a**: 단계적 적용 — 구조 필드가 **부재한** 레거시 TR은 prose Block 참조를 P2 권장 수준으로 downgrade. 구조 필드가 부착된 블록만 P0 엄격 적용.
- 장점: 현존 draft 자동 해소 + 신규 작성 시 구조 필드 도입 권장
- 단점: 영구 이중 표준 (legacy는 prose, 신규는 구조 필드) → 일관성 약화

**옵션 BL-3b**: 자동 마이그레이션 도구 — `scripts/migrate_prose_to_structured_refs.py` 신규 작성. prose의 "Block N" 참조를 scan해서 `foreshadow_targets`/`callback_sources` 구조 필드로 **병행 부착** (prose는 보존). 부착 완료 TR은 META-001 P0 통과.
- 장점: 레거시 TR 자동 수리 가능 + prose 서사 연결 조직 보존
- 단점: 스크립트 작성 + TR 스키마 병행 확장

**옵션 BL-3c**: harness §0A.14 문구 완화 — "prose Block 참조는 구조 필드 존재 여부와 무관하게 허용, 단 구조 필드가 있으면 우선 사용" 방향으로 규칙 자체 갱신.
- 장점: 가장 간단, 즉시 전체 해소
- 단점: 저지능 LLM 모델 (Gemini Flash 등)이 prose 참조만 보고 서사 그래프를 재구성하는 부담 (§0A.14 도입 원래 의도 약화)

**권장**: **옵션 BL-3b (자동 마이그레이션 도구)** — 가장 낮은 서사 영향 + 높은 정합성

**영향**:
- `jangyeongshil_industrial_revolution`: -292 P0 flags (META-001) + 부수 LANG-001 감소
- 기타 blockguide works: 동일 수준 해소 기대 (모든 works가 유사 pattern 사용 추정)

**효과 우선순위**: **High** (P0 flag 292건 직접 해소, 그 외 LANG-001 다수)

### BL-4: `tr_batch_harness.py` — REL-001 요약 스타일 허용

**현 상태**: `REL-001` 규칙이 `relationship_delta[target].before`와 직전 블록의 `after`의 **verbatim** 문자열 일치를 요구.
**문제**: 본 project의 authoring style은 "before"를 요약문으로 씀 (예: "Block 60 각성의 즉각 운영 변환 수신자"). verbatim cascade로 재작성하는 것은 수천 건 편집이며 서사 품질 변화 없음.
**수정 방향**:
1. `relationship_delta` 엔트리에 `anchor_before` / `anchor_after` 구조 필드 추가 지원 (harness §0A.14와 유사 구조)
2. `anchor_*` 필드가 있으면 `anchor_before == prev.anchor_after` verbatim 검사 (엄격)
3. `anchor_*` 필드가 없으면 `before` / `after`는 요약 스타일로 간주하고 **token overlap 임계 검사** (예: ≥3 token 공유)
4. 또는 summarized `before` 허용 플래그를 block-level 또는 work-level 설정으로 도입

**영향**:
- `jangyeongshil_industrial_revolution`: -130 REL-001 flags (일부는 P0)
- 기타 blockguide works: 동일 수준 해소 기대

**효과 우선순위**: **Medium-High**

### BL-5: `tr_batch_harness.py` — LANG-001 enum 필드 제외

**현 상태**: `LANG-001` 규칙이 모든 필드에 대해 한국어 비율 임계를 적용. `receipt_type: "authority_receipt"` 등 영문 enum 고정값도 flag.
**문제**: harness §0G가 정의한 enum 영문값을 LANG 검사 대상에 포함시키는 것은 false positive.
**수정 방향**:
1. LANG-001 검사 대상에서 다음 필드 제외:
   - `genre_ext.block_cider.receipt_type` (harness §0G 정의 enum)
   - `genre_ext.deal_type` (harness §0D 정의 enum)
   - `emotional_beat.type` (emotional beat enum)
   - `pov_character` 필드의 메타 주석 부분 (Phase0 에필로그 지정 등)
2. 또는 필드 화이트리스트 방식으로 검사 대상 축소

**영향**:
- `jangyeongshil_industrial_revolution`: -140~200 P1 flags (정확 수치는 재측정)
- 기타 blockguide works: 동일 수준

**효과 우선순위**: **Medium**

### BL-6: `scripts/block_continuity_checker.py` — 파일명 하드코딩 제거

**현 상태**: 파일명을 `{work_id}_tr_block_070_draft.json` 형식으로 하드코딩 (또는 `_total_blocks` 기반 regenerate). 이 work처럼 `_tr_block_025_draft.json` 그대로 유지 중인 경우 실행 차단.
**문제**: 파일명 rename이 의도적으로 금지된 상태(live_status 가드)에서 이 스크립트를 돌릴 방법 없음.
**수정 방향**:
1. `--file` / `--path` CLI 인자 추가하여 명시적 파일 경로 오버라이드 지원
2. 또는 work_id + family로 live_status.md를 읽어 actual file path를 동적 해결
3. 또는 `treatments/` 디렉토리에서 해당 work_id로 시작하는 가장 최근 `*_tr_block_*_draft.json` 파일 자동 탐색

**영향**: `block_continuity_checker.py`가 이 work와 유사한 상태의 다른 works에도 실행 가능해짐. 다만 이 체커가 별도로 flagging하는 것은 `tr_batch_harness.py` 와 중복될 가능성 있음 (추가 가치 평가 필요)

**효과 우선순위**: **Low-Medium** (실행 차단 해소는 가치 있으나 duplicate 가능)

### BL-7: harness §6 / §7 — Phase 4 3-Pass 감리 + 출고 게이트 전용 자동화 스크립트

**현 상태**: `docs/blockguide/treatment-production-harness-v2.md` §6 (3-Pass 감리) + §7 (P0/P1/P2 출고 게이트)는 procedure만 정의. 전용 통합 자동화 스크립트는 존재하지 않음.
**문제**: Phase 4 + 출고 게이트를 통과시키려면 매번 수동 LLM 호출 + 수동 체커 실행 + 수동 결과 해석이 필요함.
**수정 방향**:
1. `scripts/tr_phase4_3pass_audit.py` 신규 — Phase 4 3-Pass 감리를 CLI로 실행 가능하게 래핑
2. `scripts/tr_release_gate.py` 신규 — P0/P1/P2 게이트 판정 + `PASS`/`FAIL` 종합 리포트 생성
3. `scripts/process_and_audit_tr_bi_loop.py` 의 현재 고장 상태(다른 works 전수 실패로 진입 차단) 복구

**영향**: 향후 모든 blockguide works의 Phase 4 + 출고 게이트 자동화 가능

**효과 우선순위**: **Medium** (자동화 개선, 이 work 단독에는 즉시 효과 없음)

## 2. 우선순위 매트릭스

| 항목 | 영향 범위 | 즉시 효과 (이 work) | 구현 복잡도 | 우선순위 |
|---|---|---|---|---|
| BL-1 CAP 장르 인식 | family-wide | -209 P0 | Medium | **High** |
| BL-2 DEAL-001 예외 | family-wide | -69 P1 | Low | **Medium** |
| BL-3 META-001 downgrade (3b 마이그레이션) | family-wide | -292 P0 + 부수 LANG-001 | High | **High** |
| BL-4 REL-001 요약 허용 | family-wide | -130 REL | Medium-High | **Medium-High** |
| BL-5 LANG-001 enum 제외 | family-wide | -140~200 P1 | Low | **Medium** |
| BL-6 파일명 하드코딩 제거 | 개별 works | 실행 차단 해소 | Low | **Low-Medium** |
| BL-7 Phase 4/출고 게이트 자동화 | family-wide | 자동화 | High | **Medium** |

## 3. 추정 종합 효과 (전체 구현 시)

옵션 BL-1 + BL-2 + BL-3b + BL-4 + BL-5 전부 구현 완료 후 `jangyeongshil_industrial_revolution` 재체크 예상 결과:
- P0: 631 → **~0~10** (META-001 292 + CAP 209 + 잔여 REL의 P0 부분 해소)
- P1: 413 → **~10~30** (DEAL 69 + REL 나머지 + LANG enum 제외로 대폭 감소)
- P2: 9 → **~4~8** (LOC-001 운영 거점 반복과 FS-003은 별도)
- **총 1053 → ~20~50**, threshold 이하로 진입 가능 추정

이 효과는 **다른 blockguide works에도 동일 수준으로 적용**될 것으로 예상됨 (동일 authoring convention + 동일 장르 SSOT 정의 사용).

## 4. 실행 전 사전 확인 사항

본 백로그를 실제 governance 오더로 승격하기 전 확인이 필요한 사항:

1. **다른 blockguide works의 Phase 3 check 결과** — 이 work와 동일 패턴인지 샘플 확인 (예: `chaebol_allowance_zero`, `wuxia_heavenly_physician`). 만약 다른 결과라면 해결 방향이 달라질 수 있음
2. **이전에 출고 게이트를 정면 통과한 work가 있는가?** — 있다면 해당 work의 TR 구조 분석이 answer key
3. **harness §0A.14 규칙 추가 시점** — 이 work TR 작성 시점보다 후에 추가되었다면 retroactive 미적용 정당성 강화
4. **SSOT 오너 / harness maintainer 승인** — 본 백로그의 BL-3c 처럼 harness 문구 변경 제안은 governance level 합의 필요
5. **`scripts/tr_batch_harness.py` 의 규칙 단위 테스트 커버리지** — 수정 시 회귀 방지

## 5. 이 백로그의 위상

- **BACKLOG**: 즉시 실행 가능 상태가 아님. 사용자가 별도 governance 오더로 승격해야 착수
- **scope 경계**: 본 백로그는 `jangyeongshil_industrial_revolution` 개별 work 작업 범위 밖. governance 오더 전용
- **work-level waiver와 상호 보완**: 현재 `jangyeongshil_industrial_revolution` 은 `phase3_waiver.md` 로 BI 인계 진입 가능. 본 백로그의 BL-1/BL-3b/BL-4 등이 구현되면 waiver 범위 축소 또는 완전 해제 가능
- **삭제 금지**: governance 오더 대기 증거 보존
- **업데이트 규칙**: 다른 blockguide works에서 유사 Phase 3 check 결과가 나오면 본 백로그의 영향 범위 추정치를 업데이트

## 6. 다음 단계 경로

- (이 work의 경우) `phase3_waiver.md` 활성 상태 → `bi_refresh` envelope 진행 가능 → BI 감리 → 출고
- (family 전체의 경우) 본 백로그를 governance 오더로 승격 → BL-1/BL-2/BL-3b/BL-4/BL-5 순차 구현 → 전체 blockguide works에 체커 재실행 → waiver 점진 해제
- 두 경로는 **병렬 진행 가능** (이 work BI 진행과 family-level governance 수정은 독립)
