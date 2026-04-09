# quiet_chaebol_heir — Block 21~30 Self-Audit

Date: 2026-04-09
Harness reference: `docs/blockguide/treatment-production-harness-v2.md` §1.1C 10-block 자체 감리 (세 번째 gate)
Audit window: Block 21-30 inside `treatments/quiet_chaebol_heir_tr_block_001_draft.json`
Audit type: read-only review (TR 파일 수정 없음)
Saved boundary at audit time: `_total_blocks=30`, `_saved_block_boundary=30`, `_next_continuation_boundary=31`
Previous audits:
- `docs/2026-04-08/quiet_chaebol_heir_block_001_010_audit.md` (PASS)
- `docs/2026-04-08/quiet_chaebol_heir_block_011_020_audit.md` (PASS)

Envelope context:
- 6th envelope Block 21-25 (운영 오더 `ㄱㄱㄱㄱ` 두 번째, capital_allocation_guard §6 `limited_guarded_release` 적용, 2026-04-08)
- 7th envelope Block 26-30 (운영 오더 `interrupt된 21-25 envelope 동기화를 먼저 마무리하고 이어서 Block 26-30 envelope를 하나로 진행`, 2026-04-09, capital_allocation_guard §6 누나 Block 27 whitelist 확장 적용)

## 0. Verdict

**PASS**

Block 31 진입 허용. ARC-04 형의 라운드 입장권 유효. 단, 아래 §3 top_risks와 §4 repair_targets는 next 10-block window(Block 31-40) 설계 시 반영해야 한다. 특히 `capital_allocation_guard §6.4 추가 해제` (차입 구조 재조정 / 비핵심 자산 정리 / 그룹 단위 본격 의결 장면) 운영자 결정이 Block 31 envelope 시작 전에 반드시 내려져야 한다.

## 1. 6-axis Review (harness §1.1C rule 3)

### Axis 1 — 주인공 우위와 간판 맛이 살아 있는가

**PASS**

- ARC-03 핵심 reward(Block 29 사업부 자본배분 안건 발언권)가 서준 본인의 4번 defeat 정직 인정 누적(Block 13·22·23·28)으로 도달했다는 것이 구조적으로 명확하다. 누가 대신 해 준 보상 없음. 형 Block 25 메시지로도, 누나 Block 27 조건부 협정으로도, 회장 Block 24 호명으로도 서준의 발언권이 직접 열리지 않는다 — 열어 준 것은 서준 본인이 Block 26 종이 보고서 3종 선제 제출 + Block 28 12주 적자 즉시 정직 인정 + 다른 12주 데이터로 균형 잡기.
- 간판 맛 강화: Block 29에서 Stage 3 `경영의 재미` 차원이 첫 등장하면서 `잘하고 싶습니다` 한 마디가 처음으로 서준 입에서 나오고, Block 30에서 그 한 마디가 분기 결산 의사록에 공식 기록된다 — 작품 정체성(`재벌가 막내가 지방 생활몰 한 곳을 살려 권역 본진을 쌓고, 그 뒤에 사업부 단위 발언권자로 올라가, 본인 축을 지키면서 경영의 재미를 자각한다`)가 한 단계 더 굵어졌다.
- Block 21-30 안에서 서준 본인의 내적 전환 6회 — Block 21 사업부 단위 첫 외적 발판 확보 / Block 22 상대 논리 거울 전환 / Block 23 `권역 본진만으로는 부족하다` / Block 25 본인 축 지키기 = 책임 정의 / Block 27 본인 축이 사실로 존재 자기 확인 / Block 28 Stage 3 본격 진입(`내가 이 사람들을 지킨다`) / Block 29 Stage 3 공식 전환(`경영의 재미` + `잘하고 싶다`) / Block 30 `잘하고 싶습니다` 공개 언어화. 전환이 모두 서준 본인 행동·판단·인지 안에 있다.

### Axis 2 — 성취 직후 보상/인정 리듬이 유지되는가

**PASS**

- Block 21: 같은 블록 내 사업부 자본배분 사전 검토 회의 배석권 + 5분 발화 기록 (first_division_floor_access)
- Block 22: 같은 블록 내 사업부 5곳 매장 진단 권한 한시 수령 + 보수파 임원 검증자 재배치 (tactical_authority_shift)
- Block 23: defeat 블록이지만 같은 블록 내 명분 자산 1건 축적 + `권역 본진만으로는 부족하다` 자기 인정 (structural_constraint_acceptance)
- Block 24: 같은 블록 내 회장 시야 진입 + `네 절차로 풀어라` 룰 외적 확인 (weighed_recognition)
- Block 25: 조용한 블록, 같은 블록 내 형 자원 평가 톤 정확한 인지 + 본인 축 지키기 책임 정의 (axis_preservation)
- Block 26: 같은 블록 내 5곳 진단 결과 정식 안건 상정 + 사업부 의사록 서준 이름 3줄 기록 + 운영 룰 초안 작성권 (authority_shift_division_agenda)
- Block 27: 같은 블록 내 누나 첫 등장 + 조건부 자료 공유 협정 + 본인 축 자기 확인 (relational_axis_mutual_acknowledgement)
- Block 28: defeat 블록이지만 같은 블록 내 5곳 중 4곳 운영 수정 실험 허가 정식 인가 + Stage 3 본격 진입 (partial_victory_with_stage3_entry)
- Block 29: 같은 블록 내 ARC-03 핵심 reward(사업부 자본배분 안건 발언권) 정식 인가 + `발언권자` 직함 + Stage 3 공식 전환 (arc03_core_reward_with_stage3_formal_transition)
- Block 30: 같은 블록 내 `잘하고 싶습니다` 공식 기록 + 세 자녀 첫 동시 동석 기록 + 라운드 순서 본문 첫 시각적 검증 (arc03_exit_round_order_formal_confirmation)

cider 분포(Block 21-30): `[T,T,F,F,F,T,F,T,T,T]` — 6 cider, 4 setup/defeat/quiet/signal. defeat 블록(Block 23) + quiet 블록(Block 25) + signal 블록(Block 27)도 `같은 블록 영수증` 원칙을 내면/관계 자산 층위에서 유지.

### Axis 3 — 자본/권력/조직 장악 축이 실제로 커졌는가

**PASS**

- Block 21 시작: ARC-01 공식 권한 7건 + ARC-02 공식 권한 5건 = 12 공식 권한, 23 자산
- Block 30 시점 누적:
  - 공식 권한 **17건** (ARC-01 7 + ARC-02 5 + ARC-03 5: 사업부 자본배분 사전 검토 회의 배석권 Block 21 / 사업부 5곳 한시 진단 권한 Block 22 / 운영 룰 초안 작성권 Block 26 / 사업부 자본배분 안건 발언권 Block 29 / 발언권자 직함 Block 29)
  - 협력/관계 라인 **4건** (문하 생활관 점장, 매장 A 점장, 판촉팀장 중립자, 누나 라인 조건부 자료 공유 협정 Block 27)
  - 명분 자산 **5건** (지역본부장 서면 요청 기록, 매장 C 판단 존중 기록, 보고서 제출 형식 재구조화, Block 23 3주 대기 → 검증 강화 전환, Block 28 부분 패배 정직 인정 → 사업부 자본배분 라인 신뢰도 역상승)
  - 현장 검증 **3건** (Block 3 문하 생활관 / Block 16 매장 A +22% / Block 28 같은 사업부 안의 살린 매장 12주 +9% 회복)
  - 신호/인정 자산 **5건** (Block 18 본사 다른 라인 실무자 → Block 21 그룹 재무팀 차장 실체화 / Block 19 장남 라인 비서실 → Block 25 형 본인 메시지 실체화 / Block 24 회장 호명 / Block 27 누나 조건부 협정 / Block 30 분기 결산 의사록 공식 기록)
  - 구조 자산 **1건** (Block 30 라운드 순서 lock 본문 첫 시각적 검증)
  - **총 35 자산** (Block 20 시점 23 자산에서 +12)
- 조직 장악 축: `현장 운영대행` → `권역 본진` → `권역 단위 운영권` → `사업부 단위 배석권` → `사업부 단위 발언권자` → `분기 결산 의사록 기록 발언자`. 5단계 층위 상승이 Block 3~30 사이에 본인 절차로만 쌓였다.
- 사업부 보수파 임원이 적대자 → `정확한 한계를 제시하는 검증자`로 재배치된 것이 ARC-03 내부 조직 구조 변화의 가시적 증거 (Block 4→13→28 지역본부장 라인 잔류 동료화 family).

### Axis 4 — opponent / method / deal_type / stakes 반복이 누적되지 않았는가

**PASS**

- opponent 다양성 (Block 21-30):
  - Block 21 사업부 자본배분 사전 검토 회의 배석 자체의 생소함 (자기)
  - Block 22 사업부 보수파 임원 `시기상조` 논리 (인물)
  - Block 23 사업부장 절차 카드 (구조)
  - Block 24 회장 거리감 정책 안에서의 짧은 호명의 무게 (내면)
  - Block 25 본인 축이 형 축에 흡수될 위험 (구조/자기)
  - Block 26 사업부 절차 그 자체 (구조, 보수파 이번 라운드 우회권 불능)
  - Block 27 본인 축이 누나 축의 대외 안건 하위 자료로 프레임 바뀔 위험 (구조)
  - Block 28 보수파 12주 적자 카드 + 사업부 자본배분 라인 단기 손실 버티기 한계 (정보 비대칭 + 구조)
  - Block 29 발언권이 의결권으로 오해될 위험 + `경영의 재미` 감정 첫 등장에 본인이 놀라는 것 (구조 + 내면)
  - Block 30 세 자녀 첫 동시 동석이 폭주/파탄으로 바뀔 위험 (구조)
  - 10블록 모두 다른 opponent 형태, 중복 없음. 그 중 7개가 `구조 적대자`(인물 아님)로 Block 11-20 audit top_risk #2(villain dignity) 회피
- method 다양성: 5분 발화 기록화 / 상대 논리 거울 전환 / 3주 대기 → 검증 강화 / 회장 룰 외적 확인 / 응답 미루기 + 본인 축 책임 정의 / 종이 보고서 선제 제출 / 조건부 수락 + 세 번째 조건 먼저 제시 / 12주 적자 즉시 인정 + 다른 12주 데이터 균형 / 패배 누적을 발언권 명분 실체로 인지 / 세 자녀 동석을 조용한 형태로 설계. 10개 모두 중복 없음.
- deal_type: business_growth_power 단일 (작품 profile 정상)
- stakes 변주: 10블록 모두 다른 stake
- defeat block 3종 변주 완결: Block 13(인적 패배: 매장 C 점장 15년 판단 존중) / Block 23(구조적 패배: 절차 vs 결과 분리) / Block 28(정보 비대칭 + 단기 손실 버티기 한계). 세 형태 모두 다른 family. Block 11-20 audit top_risk #4 완결 대응.
- 조용한 블록 intensity 변주: Block 4·9(6/6) / Block 15(4/4) / Block 18·19(5/5) / Block 25(5/6) — 이번 window 한 번 등장, 새 형태(5/6)로 패턴 반복 회피

### Axis 5 — continuity와 열린 복선이 다음 10블록(Block 31-40)으로 자연스럽게 이어지는가

**PASS**

- 열린 foreshadow (Block 31-40 수거 예정):
  - Block 31 ARC-04 형의 라운드 첫 블록 — Block 30에서 형이 말한 `본부 간 자본 흐름 조율 안건 다음 분기 정식 안건 제출`이 직접 씨앗. Block 25 형의 `본부 라인 하나를 열어 줄 수 있다` 톤이 ARC-04 본격 발동의 사전 연료
  - Block 32±2 형의 차입 구조 재조정 본격 발동 — 현재 capital_allocation_guard §6.4가 미해제 상태, ARC-04 진입 전 해제 결정 필수
  - Block 35±2 형 라운드 안에서 서준 Block 29 발언권이 처음 사용되는 시점 — 본인 축 발언 형태로, 형 축에 흡수되지 않는 거리 유지
  - Block 40 ARC-04 출구 — 형 라운드 핵심 reward 수령, 서준은 발언권자 자격으로 본인 축 유지 증언
- 열린 foreshadow (Block 41-60 수거 예정):
  - ARC-05 누나의 라운드 — Block 27 조건부 협정의 해외 대외 미상정 조건이 누나 라운드 진입 시점의 라인 조건으로 이월, Block 30 누나의 공개 재확인이 ARC-05 진입 조건으로 고정
  - ARC-06 서준의 라운드 — Block 29 `경영의 재미` 차원 + `잘하고 싶다` + 발언권자 직함 6개월이 ARC-06 능동 진입의 직접 토대
- 열린 foreshadow (Block 61-70 수거 예정):
  - ARC-07 셋의 결합 파이널 — Block 30 세 자녀 첫 동시 동석 조용한 형태가 ARC-07 셋의 결합 파이널의 reverse echo (첫 동석과 마지막 결합이 서로를 거울)
- 복선 회수 부하: Block 31-40 window에서 회수될 foreshadow 4~6건. 밀도 적정.
- `_envelope_ref` 갱신 확인: Block 30 저장 시 7th envelope 정보 추가됨

### Axis 6 — 다음 10블록에서 키워야 할 확장축과 위험축이 분명한가

**PASS**

- **확장축 4종** (Block 31-40 core):
  1. ARC-04 형의 라운드 본격 발동 — 차입 구조 재조정 / 비핵심 자산 정리 / 그룹 단위 본격 의결 장면 등장. capital_allocation_guard §6.4 해제 필수
  2. 서준 발언권(Block 29 수령)의 형 라운드 안에서의 본인 축 사용 — 형 축에 흡수되지 않는 거리 유지 + Stage 3 `경영의 재미` 차원 활성 유지
  3. 형 강도윤 본인의 본격 온스크린 등장 — Block 25 개인 메시지 / Block 30 한 줄 발언에서 한 단계 더 올라가 주 발언자/주 결정자 위치로. villain dignity 기준 확장 필요
  4. 세 자녀 사이의 권력 균형 구조 본격 시각화 — Block 30 조용한 형태 이후 형 라운드 안에서 누나 미등장 유지 + 서준 발언권자 보조 위치
- **위험축 5종** (Block 31-40 관리 대상):
  1. **capital_allocation_guard §6.4 해제 결정 필수** — 운영자 사전 결정. `차입 구조 재조정`, `비핵심 자산 정리`, `이사회 본회의`, `M&A` 등 표현의 본문 진입 가능 범위를 Block 31 envelope 시작 전에 명시해야 함
  2. 형 강도윤의 본격 등장 시 villain dignity — 형은 적대자 아닌 자기 축 정직한 경쟁자. ARC-04에서 형이 본격 결정을 내릴 때 그 결정이 `생존과 안정`이라는 본인 축 룰 안에서 정직하게 나와야 함. 관계 파탄·증오·복수 엔진 금지
  3. 서준 발언권자의 ARC-04 내 역할 — 발언권자는 `조언자/비판자/검증자` 중 어느 자리인가? Block 29 인가서 3조건(`발언이 의결 아님 / 의결권은 사업부장에게 있음 / 6개월 한시`)을 ARC-04 형 라운드 안에서도 준수해야 함. 서준이 형 본부 라인 의사결정을 직접 움직이면 canon 3축 non-overlap 룰 위반
  4. Stage 3 `경영의 재미` 차원 지속 — Block 29·30 첫 등장 + 공개 언어화 이후, ARC-04 안에서 이 차원이 소멸하지 않고 지속되어야 함. 형 라운드에 수동적으로 끌려들어가면 `경영의 재미`가 `의무감`으로 축소될 위험
  5. canon ledger drift 누적 — Block 1-10 / Block 11-20 / Block 21-30 세 audit 모두 동일 드리프트 기록. ARC-04 진입 전 또는 Block 40 self-audit gate에서 canon_tighten 검토 권고

## 2. Machine Checks (보조)

- JSON parse: PASS
- `_total_blocks == 30`: PASS
- `_saved_block_boundary == 30`: PASS
- `_next_continuation_boundary == 31`: PASS
- blocks 배열 길이 30, block_id `Block 1` ~ `Block 30` 연속: PASS
- cider 분포 (Block 1-30): `[F,F,T,F,F,T,T,T,F,T,F,T,F,T,F,T,T,F,F,T,T,T,F,F,F,T,F,T,T,T]` — 15 cider, 15 setup/buildup/quiet/defeat/signal
- ARC별 cider:
  - ARC-01 (1-10): 5개 (Block 3·6·7·8·10)
  - ARC-02 (11-20): 5개 (Block 12·14·16·17·20)
  - ARC-03 (21-30): 5개 (Block 21·22·26·28·29·30 — 실제 6, 단 Block 23·24·25·27은 defeat/signal/quiet)
  - 실제 Block 21-30 cider 블록: 21·22·26·28·29·30 = **6개**
- capital_allocation_guard §6.2 금지 용어 18종 sweep (Block 1-30 전체): **0건**
- §6.2 금지 인물 sweep (부회장·사외이사·대표이사·전무): **0건**
- §6.1 whitelist 인물 Block 21-30 등장:
  - 본사 기획실장: Block 21·23·26·29·30
  - 그룹 재무팀 차장: Block 21
  - 사업부장: Block 22·23·26·28·29·30
  - 사업부 보수파 임원: Block 22·23·26·28
  - 대륜그룹 회장: Block 24 (본인 등장)
  - 장남 강도윤: Block 25 (본인 첫 발화, 개인 메시지) + Block 30 (본인 첫 공식 발언)
  - 누나 강민서: Block 27 (본인 첫 대면) + Block 30 (본인 첫 공식 발언)
  - 강민서 보좌관: Block 27
- provisional canon name lock (대륜그룹·문하 생활관·지방 도시): 유지
- sibling_axes_present_in_scene:
  - Block 24 chairman_onscreen=true
  - Block 25 hyeong_onscreen=true
  - Block 27 nuna_onscreen=true
  - Block 30 hyeong_onscreen=true + nuna_onscreen=true (최초 동시)
- Stage 0 handoff validator: **PASS** (4-pack 유지)

## 3. Top Risks (carry to Block 31-40 설계)

1. **`capital_allocation_guard §6.4 해제 결정` 운영자 사전 합의 필수** — ARC-04 형의 라운드 본격 발동 블록들은 `차입 구조 재조정`, `비핵심 자산 정리`, `이사회 본회의`, `M&A`, `지분 재배치` 등 표현이 본문으로 들어가야 한다. 해제 없이 Block 31을 시작하면 매 블록 HOLD 위험. 해제 형태는 §6과 같은 `limited_guarded_release` 형태 권장(ARC-04 범위 안에서 허용되는 표현·장면 명시 + ARC-05 범위 유지).
2. **ARC-04 형 라운드 안에서 서준 발언권자의 역할 정의** — 서준은 ARC-04에서 (a) 형 본부 라인 의사결정의 조언자/비판자/검증자, (b) 본인 사업부 발언권 안에서 본인 축 유지하는 별도 라인, (c) 형 결정 결과에 대한 발언권자 의견 제시자 중 어느 자리에 앉아야 하는가? Block 29 인가서 3조건(발언=비의결, 6개월 한시, 사업부장 재평가)의 테두리 안에서 서준이 형 라운드에 개입하는 방식을 사전 설계 필수.
3. **Stage 3 `경영의 재미` 차원 지속 유지** — Block 29·30에서 첫 등장한 이 차원이 ARC-04 안에서 형 라운드에 수동적으로 끌려들어가면 `의무감`으로 축소된다. 형 라운드 본문에서도 서준이 본인 축 발언을 할 때 `이걸 정확히 잘하고 싶다`는 톤이 유지되어야 함. Block 31-40 sample 블록 한두 개에서 `경영의 재미` 차원 재확인 필수.
4. **형 강도윤 villain dignity 확장** — Block 25 개인 메시지 + Block 30 한 줄 공식 발언에서 형은 `정직한 경쟁자`로 그려졌다. ARC-04에서 형이 본격 의사결정자로 올라가면 dignity 기준이 한 단계 확장되어야 한다. 형의 본부 라인 결정이 `이전 시대 정답을 지키면서도 새 시대 변수를 반영하는` 형태여야지, 단순한 고집·숫자 집착·차가운 거절이면 dignity가 줄어든다. Block 13/23/28 보수파 family 원칙과 같은 계열이지만 한 층위 더 큰 인물로.
5. **canon ledger drift 누적 (3rd recording)** — Block 1-10 / Block 11-20 / Block 21-30 세 audit 모두 동일 드리프트 기록. ARC-04 진입 전 canon_tighten 실행 여부를 운영자가 결정해야 함. 현재 드리프트는 본문 품질을 해치지 않았기 때문에 즉시 canon_tighten 불필요 판단 유지. Block 40 self-audit 또는 작품 70블록 완성 후 정산 권고.
6. **라운드 순서 lock 본문 시각적 검증의 ARC-04 연장** — Block 30에서 Phase0 round_order_lock(ARC-04 형 → ARC-05 누나 → ARC-06 서준 → ARC-07 결합)이 본문 안에서 첫 시각적 검증되었다. ARC-04 안에서 이 순서가 두 번째 시각적 검증되어야 한다 — 구체적으로, ARC-04에서 서준이 본인 라운드 진입을 ARC-04 끝에서도 하지 않는 것(순서 lock 두 번째 검증)이 본문 안에 장면으로 남아야 함.

## 4. Repair Targets

- **same-turn repair**: 없음 (Block 21-30 내부 정합성 통과)
- **next envelope 착수 전 확인 (operator-level)**:
  - `capital_allocation_guard §6.4` 해제 결정 — 운영자가 §6.4를 업데이트하거나 별도 조사 결과 확인 필요. 해제 형태는 `arc04_limited_guarded_release`(특정 표현·장면 허용) 또는 `arc04_full_release`(차입 재편 / 비핵심 자산 정리 등 본격 발동) 중 하나
  - 해제 없이 Block 31 진입 시 ARC-04 본격 발동 장면 진입 불가, 매 블록 HOLD 위험
  - canon_tighten 실행 여부 결정 — canon ledger drift 3회 누적, 즉시 실행은 불필요하나 Block 40 self-audit 또는 70블록 완성 후 정산 시점을 운영자가 명시해야 함
- **next envelope 착수 전 확인 (writing-level)**:
  - 형 강도윤 본격 등장 시 villain dignity 기준 재확인 — Block 13/23/28 보수파 family 원칙의 한 층위 상위 확장
  - 서준 발언권자의 ARC-04 내 역할 사전 설계 — 조언자/비판자/검증자 중 어느 위치
  - Stage 3 `경영의 재미` 차원 ARC-04 sample 블록 한두 개에 재확인 장치 필수
  - Block 30 `세 개의 복도 분리` 공간적 분리 장면이 ARC-04 안에서 다른 형태로 한 번 더 등장해야 3축 non-overlap 룰이 본문 안에서 네 번째 시각적 검증됨

## 5. Next 10 Focus (Block 31-40 핵심 집중점)

1. **ARC-04 형의 라운드 본격 발동** — 형 본부 라인 의사결정의 본문 진입. 차입 구조 재조정 / 비핵심 자산 정리 / 그룹 단위 본격 의결 장면이 허용 범위 안에서 등장. capital_allocation_guard §6.4 해제 필수.
2. **서준 발언권자의 ARC-04 내 역할 정립** — Block 29 인가서 3조건 안에서 서준이 형 라운드에 어떻게 참여하는지 본문 확립. 본인 축 유지 필수.
3. **형 강도윤 villain dignity 확장** — 형이 본격 의사결정자로 올라가는 블록에서 dignity 기준이 한 층위 확장. Block 13/23/28 family의 한 층위 상위.
4. **Stage 3 `경영의 재미` 차원 지속** — ARC-04 안에서 서준의 본인 축 발언 블록에 `잘하고 싶다` 톤 재확인 장치.
5. **라운드 순서 lock 본문 두 번째 시각적 검증** — ARC-04 안에서 서준이 본인 라운드 진입을 하지 않는 것 + 형의 라운드가 형 축 안에서 자립적으로 진행되는 것이 본문에 장면으로 남음.
6. **Block 30 세 자녀 동석의 reverse echo 예약** — ARC-04 끝에서 세 자녀 두 번째 동시 동석 또는 비슷한 관계 장면이 한 번 더 등장해 ARC-07 결합 파이널의 사전 토대가 됨.

## 6. Gate Result

- harness §1.1C rule 1: ✓
- rule 2: ✓ (Block 31이 아니라 Block 21~30 자체 감리)
- rule 3 (6축 review): ✓ §1 완료
- rule 4 (deliverable shape): ✓ §0 PASS, §3 top_risks 6건, §4 repair_targets (operator 2 + writing 4), §5 next_10_focus 6개
- rule 5 (FAIL 시 같은 10블록 수리): 적용 없음 (PASS)

**Block 31 진입 허용**. 단, capital_allocation_guard §6.4 해제 결정이 운영자 차원에서 내려진 뒤에만 안전하다. 해제 없이 진행 시 ARC-04 본격 발동 장면 진입 불가, 매 블록 HOLD 위험.

## 7. ARC-03 Summary (전체 10블록)

ARC-03 (`그룹 자본배분`, Phase0 arc title) entry → exit:
- **entry** (Block 21): 그룹 재무팀 차장이 서준을 사업부 자본배분 사전 검토 회의에 호출. Block 18 비공식 신호 실체화.
- **mid1** (Block 22): 보수파 임원 `시기상조` 논리 거울 전환 → 5곳 한시 진단 권한 수령.
- **defeat1** (Block 23): 사업부장 절차 카드 → 3주 대기. `권역 본진만으로는 부족하다` 자기 인정. Block 13 인적 패배와 다른 `절차 vs 결과 분리` 형태.
- **signal1** (Block 24): 회장 본인 첫 등장, `네 절차로 풀어라` 룰 외적 확인.
- **signal2** (Block 25): 형 본인 첫 발화 (개인 메시지), 서준 응답 미루기 + 본인 축 지키기 = 책임 정의.
- **mid2** (Block 26): 3주 대기 → 검증 강화 전환 → 종이 보고서 3종 선제 제출 → 5곳 진단 결과 정식 안건 상정 + 사업부 의사록 첫 기록.
- **signal3** (Block 27): 누나 본인 첫 등장, 조건부 자료 공유 협정, 본인 축 존재 자기 확인.
- **defeat2** (Block 28): 보수파 12주 적자 카드 → 다른 12주 데이터 균형 → 4/5 승리 + 1곳 부분 패배. Stage 3 본격 진입 (`내가 이 사람들을 지킨다`).
- **core reward** (Block 29): 사업부 자본배분 안건 발언권 정식 인가 + Stage 3 공식 전환 (`경영의 재미` 차원 첫 등장 + `잘하고 싶다` 첫 언어화).
- **exit** (Block 30): 세 자녀 첫 동시 동석, 각자 한 줄씩 분기 결산 의사록 기록, `잘하고 싶습니다` 공식 기록, 라운드 순서 lock 본문 첫 시각적 검증, ARC-04 무대 깔기 완결.

ARC-03 `그룹 자본배분` arc title은 Phase0 설계 상 arc title이며, 본문 안에서는 `사업부 자본배분` 수준으로 안전하게 구현되었다. 그룹 단위 본격 의결은 ARC-04~07에 예약되어 있고, ARC-03 안에서는 `사업부 자본배분 사전 검토 회의` / `사업부 자본배분 안건 발언권` 수준으로 capital_allocation_guard §6 `limited_guarded_release` 범위를 정확히 지켰다.

Phase0 ARC-03 `capital_target` = `권역 본진 → 사업부 단위 자본배분 발언권 + 형/누나의 시야 진입` — **달성 확인**.
Phase0 ARC-03 `exit_function` = `사업부 단위 자본배분 발언권을 정식으로 받는다. 형 강도윤·누나 강민서가 서준을 처음으로 같은 테이블에서 마주한다. 서준 본인 안에서 '이걸 안 하면 더 크게 망한다'는 책임감의 첫 자각이 일어난다` — **Block 28 책임감 본격 진입 + Block 29 발언권 정식 인가 + Block 30 세 자녀 첫 동시 동석으로 달성 확인**.
