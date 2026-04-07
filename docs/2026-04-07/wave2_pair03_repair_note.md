# Wave2 Pair 03 Repair Note — flagged no-cider sweep

Date: 2026-04-07
Status: applied
Pair: `03` / `chaebol_ent_empire`
Family: `blockguide`
Audit Trigger: `docs/2026-04-07/10pair_true_benchmark_terminal03_pair03_report.md` (§4 Full-Block Cider Scan — no-cider 8블록)
Target File (mutated): `treatments/03_chaebol_ent_empire_tr_block_070_draft.json`
Scope: flagged block sweep only (B4 / B16 / B23 / B28 / B34 / B47 / B55 / B63). 그 외 블록은 손대지 않음.

## Repair Doctrine

- spec `production-pair-benchmark-spec-v1` §2.3: `any block is has_cider:false` → YELLOW ceiling. 하나라도 남아 있으면 ceiling이 풀리지 않으므로 8블록 전수 같은-블록 보강.
- WG `03_chaebol_ent_empire.yaml` custom_rules "반격 예약 없는 손해 금지" + crisis_doctrine "즉시 보상" 직접 준수.
- surgical only: 각 블록의 `content.reward` 필드에만 same-block token/receipt 문장을 1~3개 append. 그 외 필드(capital_before/after, opponent, stakes, power_shift, foreshadow, emotional_beat, success_pattern 등) 건드리지 않음. 자본 수치도 변경하지 않음 — 토큰은 재협상 창·계약 단서·팬 서버·복귀 근거 등 비자본 receipt 쪽으로 설계.
- **B55 / B63**: defeat_mechanic 뼈대 보존이 최우선. 피로스 승리 / 지배권 상실 구조와 자본 손실은 그대로 두고, 같은 블록 안에서 회수되는 micro-card만 추가.

## Per-Block Patch Summary

### Block 4 — 조준된 패배 (`capital_delta: -15억`, defeat)

- 기존: 파일럿 실패 + "첫 의심" 인사이트만
- 추가 same-block 토큰:
  - 오지혁이 그 밤 안에 호텔 부속 소극장 단기 행사 라인 1건 묶어 옴
  - 초반 강이현 VIP 무대를 기억한 소형 스폰서 1곳이 철수 대신 "다음 판 한 번만 더 본다" 유예 메시지 + 2억 규모 후속 단기 부킹 카드 1조각 생존
- WG anchor: custom_rules "반격 예약 없는 손해 금지", crisis_doctrine "즉시 보상"

### Block 16 — 감사실 칼날 (`-58억`, betrayal)

- 기존: 감사실 충격 + 한도윤 정체 폭로
- 추가 same-block 토큰:
  - 서민재가 감사 범위 밖 호텔 공간 바우처 + 외부 공동제작 선지급 라인을 비용 재분류 메모로 살려 내며 데뷔조 연습실 최소 운영 예산 1조각 확보
  - 오지혁이 감사가 훑지 않는 소형 행사 2건 선지급으로 묶어 5억 규모 캐시플로 라인 1조각 착지
- WG anchor: mandatory_scene_engines "위기 선독 후 배치 카드로 최소 피해 통제 → 즉시 다음 입장권 회수"

### Block 23 — 화제는 터졌는데 방송은 막혔다 (`-56억`, frustration)

- 기존: 영상 화제성 + 외부 전쟁 비용 학습
- 추가 same-block 토큰:
  - 최라희가 같은 주에 대학 축제·호텔 라이브·직캠 유통 3건 묶어 비방송 노출 라인 공식화
  - 해외 바이어 1명이 프리데뷔 영상 보고 직접 연락 → 업계전 바깥 첫 접점 카드 1조각이 같은 블록에 태하 손에 쥐어짐
- WG anchor: tracking_slots "인재 포트폴리오 확장", protagonist_weapon "접점 확장"

### Block 28 — 새벽의 숨고르기 (`+3억`, introspection)

- 기존: +3억 + 내부 태도 변화만 (reader-felt 토큰 부재)
- 추가 same-block 토큰:
  - 서민재가 남긴 포맷군 통합 메모 실물 도착 → 태하가 그 자리에서 윤서아·강이현·연습생 라인을 하나의 구조로 묶는 첫 실물 스케치 작성
  - 새벽 동안 호텔 계열 내년 단가 보호 계약 1건 구두 수락 → 다음 분기 운영 하방 같은 블록 안 확정
- WG anchor: mandatory_scene_engines "개별 성공을 묶어 패키지·접점 구조로 확장하는 설계 장면"

### Block 34 — 플랫폼이 문을 닫다 (`-61억`, setback)

- 기존: 손실 + 자체 접점 필요 자각
- 추가 same-block 토큰:
  - 박재인 팬들이 플랫폼 밖 소형 커뮤니티로 자발적 이동 → 첫 자체 팬 서버 1개 등장
  - 최라희가 해당 흐름을 즉시 데이터로 기록 → 세령컬처웍스 자체 접점의 첫 명단으로 등록
  - 하은솔이 플랫폼 제재 밖 광고주 2곳과 직거래 계약 단서 1건 확보 → 팬덤 직결 라인 1조각
- WG anchor: tracking_slots "비대칭 전략이 시장에서 먼저 통하는 증명 누적"

### Block 47 — 위생 논란 (`-136억`, crisis)

- 기존: 브랜드 타격 + 문선우 학습
- 추가 same-block 토큰:
  - 하은솔이 유통 파트너 2곳 잔류 재협상 → 브랜드 완전 철수 차단
  - 문선우 개인 라인 주방 단발 주문 1건이 회수 결정과 별개로 생존 → F&B 복귀선 1조각
  - 회수 대응 과정에서 장부 속 비정상 흐름의 첫 단서 태하 손에 잡힘 → 다음 판 반격 카드 1조각
- WG anchor: crisis_doctrine "최소 피해 + 즉시 다음 입장권"

### Block 55 — 세계를 잡았지만 팀이 갈린다 (`-264억`, pyrrhic_victory)

- defeat_mechanic 뼈대 **보존**. 자본 -264억, 독점 계약 일부 수락, 팀 컨디션 손상 모두 그대로.
- 추가 same-block 토큰 (뼈대 훼손 없이 micro-card만):
  - 마커스 리 계약서 안에서 "6개월 단위 재협상 창" 조항 1개만은 끝까지 지켜냄 → 통제권 완전 상실 차단
  - 강이현이 무대 직후 대기실에서 "어디까지 가든 나는 끝까지 간다" 사적 약속 → 팀 신뢰 1조각
- 문장 끝에 "defeat_mechanic은 그대로지만, 다음 판을 여는 재협상 창 카드와 사람 카드 2조각이 같은 블록 안에서 태하 손에 남는다"로 뼈대 보존 명시.
- BI anchor: CommercialCode.defeat_mechanic "성공의 대가를 미리 읽지 못하면 이긴 순간부터 진다" — 손상 없음.

### Block 63 — 빼앗기는 날 (`-666억`, collapse)

- defeat_mechanic 뼈대 **보존**. 자본 -666억, 지배권 상실, 의장석 밀려남 모두 그대로. 기존의 "장부 카드 손에 있다" 정보형 회수도 유지.
- 추가 same-block 토큰 (뼈대 훼손 없이 micro-shelter만):
  - 이세린이 표결 직전 사외이사 1명으로부터 "태하 복귀 조건부 반대표" 기록을 정식 회의록에 박아 넣음 → 미래 복귀 근거 1조각
  - 태하가 마지막 순간 ORBIT 글로벌 계약 수익 라인 중 1건을 개인 법인으로 보류 → 권력 밖 자산 피난처 1조각
- 최종 상태: "자리는 밀려났지만 장부 카드·복귀 근거·개인 자산 피난처 세 조각이 같은 블록 안에서 태하 손에 쥐어진 상태로 이사회실을 나간다"로 same-block receipt 명시.
- BI/WG anchor: B63 foreshadow "초반에 심어진 위임 계약서 복선이 최악의 형태로 회수된다" 유지, custom_rules "반격 예약 없는 손해 금지"는 이번 보강으로 비로소 충족.

## What Was NOT Touched

- capital_before / capital_after / capital_delta 수치: 전 블록 원본 유지. 토큰은 비자본 receipt 쪽으로 설계되어 FinanceHUD 정합성에 영향 없음.
- B55 / B63의 opponent, power_shift, stakes, success_pattern, execution_doctrine: 모두 원본 유지. defeat_mechanic 뼈대 보존.
- 나머지 62 블록: 손대지 않음 (benchmark scope 밖).
- emotional_beat / tension_level / pov_character / foreshadow_targets: 전 블록 원본 유지.
- BI `bible/03_bi_chaebol_ent_empire.json`, WG `work_guards/03_chaebol_ent_empire.yaml`: 본 wave 작업 범위 밖, 건드리지 않음.

## Post-Repair Cider Scan Expectation

- 기존 no-cider 블록 8개 모두 same-block reader-countable receipt 확보:
  - B4: 단기 부킹 카드 1조각
  - B16: 데뷔조 연습실 운영 예산 + 5억 캐시플로 1조각
  - B23: 비방송 노출 라인 + 해외 바이어 접점 1조각
  - B28: 포맷군 통합 메모 실물 + 내년 단가 보호 계약 1조각
  - B34: 자체 팬 서버 + 자체 접점 명단 + 직거래 단서 1조각
  - B47: 잔류 재협상 + F&B 복귀선 + 반격 단서 1조각
  - B55: 6개월 재협상 창 + 팀 신뢰 약속 1조각 (defeat_mechanic 보존)
  - B63: 복귀 근거 회의록 + 개인 자산 피난처 1조각 (defeat_mechanic 보존)
- 예상 post-repair 상태: no-cider count 0, longest drought 0, §6 cap rule "any no-cider block → YELLOW ceiling" 해제 조건 충족. 재감리 필요.

## Next Step

- `docs/2026-04-07/10pair_true_benchmark_terminal03_pair03_report.md`는 본 repair 이전 상태의 benchmark 결과물이므로, 본 repair 결과를 반영한 재감리(re-run §4 Full-Block Cider Scan + §6 Cap Rules + §7 Provisional Grade)가 필요하다.
- 재감리는 본 repair note 범위 밖. 별도 오더에서 진행.

wave2 pair03 flagged-block repair complete; TR mutated, BI/WG untouched
