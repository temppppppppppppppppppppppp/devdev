# Codex: 02_chaebol_allowance_zero — 상호 코멘트 오더

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-11
> 목적: Opus와 Codex(또는 다른 LLM 세션)가 **동일 문서 세트를 각자 다른 관점에서 리뷰**하고, 코멘트를 모아 최종 보강안을 도출
> 방식: **방법 1 — 역할별 병렬 리뷰** (3명 동시 투입, 종합 판정)

---

## §0. 리뷰 대상 문서

| # | 문서 | 역할 |
|---|------|------|
| D1 | `docs/blockguide/TF-BH1_block_harness_reinforcement.md` | 규칙 원본 (R27~R33, validate_v3, 출고 게이트) |
| D2 | `docs/blockguide/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md` | 재작업 비교 오더 (§1~§8) |
| D3 | `docs/blockguide/treatment-production-harness-v2.md` | 생산 하네스 본문 |
| D4 | `docs/blockguide/SSOT_blockguide-integrated-order.md` | 통합 오더 SSOT |
| D5 | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | 골든 TR (실측 대조용) |
| D6 | `docs/blockguide/실패작들/02_chaebol_allowance_zero_tr_block_070_draft.json` | 실패 TR (실측 대조용) |

---

## §1. 리뷰어 3명 역할 정의

### 리뷰어 A: Production 감리관

**관점**: "이 오더대로 실제 배치 생산을 시작하면 빠지는 게 있나?"

**검토 축** (8개):
1. **실행 가능성** — D2만 보고 첫 배치(블록 1~3)를 바로 생산할 수 있는가? 빠진 전제 조건은?
2. **배치 순서** — §5의 3→4→3→10×6 구성이 현실적인가? 첫 3블록에서 opponent 3명/weakness 3종을 동시에 투입하면 밀도가 유지되는가?
3. **아크 전환** — 아크 1→2 전환 시 서도윤 퇴장 + 신규 opponent 2명 투입이 자연스러운가? 섹터 전환과 opponent 전환이 동시에 일어나면 생산 난이도가 너무 높지 않은가?
4. **자본금 커브** — §4.1에서 "유지"라 했는데, opponent/weakness/solution을 전면 재설계하면서 기존 자본금 궤적(0→1,320억)을 그대로 따를 수 있는가? 곡선이 opponent 교체와 충돌하는 블록은?
5. **Phase 0 선행 작업량** — §4.2 재설계(opponent 10명+, npc_timeline, sector_roadmap 7섹터)를 Phase 0에서 먼저 완성해야 하는데, 이 선행 작업의 분량이 오더에 명시되어 있는가?
6. **신규 opponent 설계 주체** — 이름/성격/동기/퇴장 조건을 누가 설계하는가? Phase 0에서 미리 확정하는가, 배치 생산 중 즉석 설계하는가?
7. **validate_v3 중간 실행** — 아크 1(10블록) 완성 후 validate_v3를 돌리면, 아직 블록 10개뿐이라 "70블록 고유 opponent ≥8명"(R29)은 구조적으로 FAIL. 이 false-alarm을 어떻게 처리하는가?
8. **배치 실패 시 재작업 범위** — P0 위반으로 같은 배치를 재작업할 때, 이전 배치의 블록은 건드리지 않는 것이 맞는가? 아니면 이전 배치까지 소급 수정이 필요한 경우가 있는가?

**출력 형식**: 코멘트 번호(PA-01~) + 참조 섹션 + 심각도(BLOCKER/MAJOR/MINOR/NOTE) + 설명 + 제안. 최대 10개.

---

### 리뷰어 B: QA 검증자

**관점**: "D1(TF-BH1)과 D2(비교 오더)의 수치가 정말 일치하는가? 논리적 모순은 없는가?"

**검토 축** (8개):
1. **수치 교차 대조** — D2 §1~§2의 모든 수치(F-1~F-5 실측, R27~R33 임계값, validate_v3 결과)가 D1 §0~§2와 **글자 단위로** 일치하는가? 1곳이라도 다르면 어느 쪽이 맞는가?
2. **골든 TR false-FAIL** — D2 §8.2에서 "false-FAIL 0건"이라 했는데, D5(골든 TR)를 validate_v3에 실제로 돌려도 P0 위반 0건이 나오는가? 특히 R30(weakness 3종/아크)에서 골든 TR의 weakness가 비어있을 때 "N/A"로 빠지는 로직이 validate_v3 코드와 일치하는가?
3. **임계값 경계 케이스** — R29 점유율 30%: 골든 02 최대 opponent가 ~33%(D1 §2)라 했는데, 이 수치가 정확한가? 만약 정확히 33%라면 30% 임계값에서 골든 02도 FAIL. D5를 직접 집계해서 확인 필요.
4. **출고 게이트 항목 대조** — D2 §6.1~6.4의 체크 항목이 D1 §8.1~8.4와 **항목 수, 순서, 기준값** 모두 일치하는가?
5. **패턴 ID 일관성** — D2 전체에서 사용된 패턴 ID(Q, Q', R, R', S, T, T', U, Q+T)가 D1 §R33 정의와 빠짐없이 일치하는가? D2에서 D1에 없는 패턴을 추가로 사용하고 있지 않은가?
6. **§3.8 opponent 총괄표 vs §2.1 PASS 기준** — "목표: 고유 opponent ≥10명, 최대 점유율 ≤25%"인데 R29 PASS 기준은 "≥8명, ≤30%". 재작업 목표가 PASS 기준보다 엄격한 건 의도인가, 혼동인가?
7. **§7.1 content 평균 ≥200자** — "최소 PASS 기준"에 content ≥200자(P0 해소)라 했는데, D1 R27은 "200자 미만 = P0, 350자 미만 = P1". 그러면 200자 이상이면 P0만 해소이고 여전히 P1. 이걸 "최소 PASS"로 부르는 게 맞는가?
8. **§5.2 안전 배치 3→4→3 합계** — 3+4+3 = 10 (아크 1). 이후 "10×6"이라 했는데 아크 2~7 = 6아크. 총합 10+60 = 70. 산술은 맞지만, 아크 2~7도 안전 배치(3→4→3)로 시작해야 하지 않는가?

**출력 형식**: 코멘트 번호(QB-01~) + 참조 위치(D1/D2 + 섹션+라인) + 심각도(MISMATCH/WARNING/OK/NOTE) + 설명. 최대 10개.

---

### 리뷰어 C: Writer 관점

**관점**: "이 재설계 방향대로 실제 블록 JSON을 써야 하는 사람(LLM)이 막히는 지점은?"

**검토 축** (8개):
1. **opponent 서사 설계** — §3에서 "신규 opponent (예: 장례식장 지역 이권자)" 등 이름이 예시. 실제 생산 시 이 예시 이름을 그대로 쓰는가, Phase 0에서 확정된 이름을 쓰는가? 예시만 있고 확정 이름이 없으면 생산자가 즉석에서 만들어야 함.
2. **weakness 3종의 서사적 자연스러움** — 아크 1에서 "①운영비 인식 부재 ②외주 단가 불투명 ③의전 인력 이직률 무관심"을 10블록에 분배하면, 블록당 weakness가 바뀌면서 서사 연속성이 깨지지 않는가? 3종을 어떤 비율로 배분하는가 (예: 3-4-3? 균등?)
3. **solution 차별화 vs 캐릭터 일관성** — 70블록 전부 다른 solution을 쓰면 주인공의 전략 스타일이 일관되지 않을 수 있음. "윤재이"라는 캐릭터의 코어 전략 DNA는 무엇이고, 그 위에서 전술 변주를 하는 건지, 아니면 매번 완전히 다른 사람처럼 쓰는 건지?
4. **event_villain 밀도 보강** — 실패 TR의 event_villain은 42~46자(편차 4자). ≥50자로 보강한다 했는데, 실제로 villain 행동/동기/충돌을 50자 안에 담으려면 어떤 구조를 쓰는가? 예시 템플릿이 있으면 생산이 수월함.
5. **reward 필드 55자** — reward가 현재 57자 평균이고 "≥55자"가 최소. 거의 현행 유지인데, reward에 담아야 할 내용(자본 변화? 관계 변화? 감정 변화?)의 우선순위가 있는가?
6. **아크 간 opponent 인수인계** — 아크 1의 신규 opponent(예: 지역 이권자)가 아크 2에서 완전 퇴장하는가? 아니면 일부가 아크 2~3까지 잔류해서 서사 연속성을 유지하는가? §3.8에서 "아크별 1~2명 배정"이라 했는데, 크로스 아크 opponent의 존재 여부가 불명확.
7. **sector_roadmap과 블록 content의 연결** — §4.3에서 sector_roadmap JSON 예시가 있는데, 블록의 `content.context`가 이 roadmap의 `core_conflict`를 반영해야 하는가? 반영한다면 어떤 수준(직접 인용? 영감만?)인가?
8. **서사적 클라이맥스 배치** — 70블록 중 어디가 서사 정점(가장 큰 위기/반전)인가? 실패 TR은 균일하게 밋밋했는데, 재설계에서 "블록 35(병원 방역 중반)에서 반전", "블록 65(가문 역의존 후반)에서 최종 위기" 같은 서사 곡선 지시가 없으면 생산자가 또 균일하게 쓸 위험이 있음.

**출력 형식**: 코멘트 번호(WC-01~) + 참조 섹션 + 심각도(BLOCKER/MAJOR/MINOR/NOTE) + 설명 + 제안. 최대 10개.

---

## §2. 실행 프로토콜

### 2.1 투입 순서

```
1턴: 리뷰어 A, B, C 동시 투입 (병렬)
     ├─ A: D2 + D3 + D4 읽고, 생산 관점 코멘트 ≤10개
     ├─ B: D1 + D2 + D5 + D6 읽고, 수치 대조 코멘트 ≤10개
     └─ C: D2 + D5 + D6 읽고, Writer 관점 코멘트 ≤10개

2턴: 종합 판정
     ├─ 3명의 코멘트를 1곳에 모음
     ├─ 겹치는 지적(2명+) = CONFIRMED → D2 즉시 보강
     ├─ 1명만 지적 = CANDIDATE → 채택/기각 판정
     └─ 최종 보강안 목록 확정

3턴: D2 문서 패치
     └─ CONFIRMED + 채택된 CANDIDATE 반영하여 D2 수정
```

### 2.2 투입 오더 (복사해서 사용)

각 리뷰어에게 아래 프롬프트를 **그대로** 전달:

---

#### 리뷰어 A 프롬프트

```
당신은 Production 감리관이다. Treatment 블록을 실제로 생산하는 현장 책임자 관점에서 리뷰한다.

아래 문서를 읽어라:
- (필수) docs/blockguide/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md
- (참조) docs/blockguide/treatment-production-harness-v2.md
- (참조) docs/blockguide/SSOT_blockguide-integrated-order.md

검토 축 8개:
1. 실행 가능성 — D2만 보고 첫 배치(블록 1~3)를 바로 생산할 수 있는가?
2. 배치 순서 — 3→4→3→10×6이 현실적인가?
3. 아크 전환 — 섹터+opponent 동시 교체의 생산 난이도는?
4. 자본금 커브 — opponent 전면 교체와 자본금 궤적이 충돌하는 블록은?
5. Phase 0 선행 작업량 — 분량 추정이 명시되어 있는가?
6. 신규 opponent 설계 주체 — Phase 0 확정인가 즉석인가?
7. validate_v3 중간 실행 — 10블록 시점에서 R29(70블록 기준) false-alarm 처리는?
8. 배치 실패 시 재작업 범위 — 이전 배치 소급 수정이 필요한 경우는?

출력: PA-01~ 번호 + 섹션 참조 + 심각도(BLOCKER/MAJOR/MINOR/NOTE) + 설명 + 제안.
최대 10개. 근거 없는 추측 금지 — 문서에서 직접 인용하라.
```

---

#### 리뷰어 B 프롬프트

```
당신은 QA 검증자다. 두 문서(D1: TF-BH1, D2: 비교 오더)의 수치 정합성을 글자 단위로 교차 검증한다.

아래 문서를 읽어라:
- (필수) docs/blockguide/TF-BH1_block_harness_reinforcement.md
- (필수) docs/blockguide/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md
- (참조) treatments/02_chaebol_allowance_zero_tr_block_070_draft.json (골든 TR)
- (참조) docs/blockguide/실패작들/02_chaebol_allowance_zero_tr_block_070_draft.json (실패 TR)

검토 축 8개:
1. 수치 교차 대조 — D2의 모든 수치가 D1과 글자 단위로 일치하는가?
2. 골든 TR false-FAIL — validate_v3 코드에서 weakness 비어있을 때 N/A 처리가 실제로 동작하는가?
3. 임계값 경계 — 골든 02 최대 opponent 점유율 ~33%가 정확한가? 30% 임계값과 충돌하지 않는가?
4. 출고 게이트 항목 대조 — D2 §6 vs D1 §8 항목 수/순서/기준값 일치 여부.
5. 패턴 ID 일관성 — D2에서 사용된 패턴 ID가 D1 R33 정의와 전량 일치하는가?
6. 재작업 목표 vs PASS 기준 — ≥10명/≤25%가 의도적 여유인지 혼동인지.
7. content ≥200자 "최소 PASS" — P0 해소지만 P1 잔존. 이를 "최소 PASS"로 부르는 게 정확한가?
8. 안전 배치 구성 — 아크 2~7도 안전 배치가 필요한지 여부.

출력: QB-01~ 번호 + 참조 위치(D1/D2 + 섹션) + 심각도(MISMATCH/WARNING/OK/NOTE) + 설명.
최대 10개. 추측 금지 — 두 문서에서 직접 인용하여 대조하라.
```

---

#### 리뷰어 C 프롬프트

```
당신은 Writer 관점 리뷰어다. 이 재설계 방향대로 실제 블록 JSON을 생산하는 LLM의 관점에서 리뷰한다.

아래 문서를 읽어라:
- (필수) docs/blockguide/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md
- (참조) treatments/02_chaebol_allowance_zero_tr_block_070_draft.json (골든 TR 구조 참조)
- (참조) docs/blockguide/실패작들/02_chaebol_allowance_zero_tr_block_070_draft.json (실패 TR 비교)

검토 축 8개:
1. opponent 서사 설계 — 예시 이름인가 확정 이름인가? 즉석 생성이면 일관성 리스크.
2. weakness 3종 배분 — 10블록에 3종을 어떤 비율로 분배하는가? 서사 연속성은?
3. solution 차별화 vs 캐릭터 일관성 — 주인공 전략 DNA와 전술 변주의 경계는?
4. event_villain 밀도 보강 — 50자 안에 담을 구조/예시 템플릿이 있으면 도움됨.
5. reward 필드 우선순위 — 자본/관계/감정 중 뭘 먼저 쓰는가?
6. 아크 간 opponent 인수인계 — 크로스 아크 opponent 존재 여부가 불명확.
7. sector_roadmap ↔ content 연결 — core_conflict를 블록에 어떻게 반영하는가?
8. 서사 클라이맥스 배치 — 정점/반전 블록 지정 없으면 또 균일하게 쓸 위험.

출력: WC-01~ 번호 + 섹션 참조 + 심각도(BLOCKER/MAJOR/MINOR/NOTE) + 설명 + 제안.
최대 10개. 서사 관점에서 구체적으로 — "다양하게 쓰라"는 수준의 코멘트는 가치 없다.
```

---

## §3. 종합 판정 기준

### 3.1 코멘트 분류

| 분류 | 조건 | 처리 |
|------|------|------|
| **CONFIRMED** | 2명 이상이 동일/유사 지적 | D2 **즉시 보강** |
| **CANDIDATE** | 1명만 지적, BLOCKER/MAJOR 심각도 | 채택/기각 판정 후 보강 여부 결정 |
| **NOTED** | 1명만 지적, MINOR/NOTE 심각도 | 기록만. 차후 참고. |

### 3.2 종합 보고서 형식

```markdown
## 상호 코멘트 종합 보고서

### CONFIRMED (즉시 보강)
| # | 지적 요약 | 지적자 | D2 보강 내용 |
|---|-----------|--------|-------------|

### CANDIDATE (채택/기각)
| # | 지적 요약 | 지적자 | 판정 | 사유 |
|---|-----------|--------|------|------|

### NOTED (기록)
| # | 지적 요약 | 지적자 |
|---|-----------|--------|
```

### 3.3 D2 패치 후 재검증

- 보강된 D2를 validate_v3에 재통과 (골든 TR false-FAIL 0건 유지 확인)
- 보강된 항목이 D1(TF-BH1)과 여전히 정합하는지 B 역할로 1회 재검증
- 최종 판정: **SHIP** (출고 가능) 또는 **REVISE** (추가 라운드 필요)
