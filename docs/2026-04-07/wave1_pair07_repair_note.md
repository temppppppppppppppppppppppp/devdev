# Wave 1 — Pair 07 Repair Note

Date: 2026-04-07
Mode: flagged-block sweep (no full-wave surgery)
Pair: `07` `office_checkup_next_day` (`blockguide`, canonical)
TR file mutated: `treatments/07_office_checkup_next_day_tr_block_070_draft.json` (in-place edit)
Source audit: `docs/2026-04-07/10pair_true_benchmark_terminal07_pair07_report.md` (Repair-1/2/3 우선순위)

## Scope

- 본 sweep은 `Block 1, 25, 32, 35, 43, 48, 53, 63, 65, 66` 10개 flagged no-cider 블록만 손댄다.
- 본문 엔진(주인공 무기/관계/적대 구도/사건 순서)은 변경하지 않는다.
- 각 블록의 `content.reward` 필드만 수정하여 same-block receipt 또는 micro-token을 명시 등록하고 `has_cider: true`로 전환한다.
- 다른 필드(context / event_villain / solution / power_shift / capital_delta / relationship_delta / foreshadow / callback / genre_ext / regression_ext)는 모두 무수정 — 본문 엔진 보존.

## Per-Block Patch Summary

Patch 적용 우선순위는 audit report Repair-1(연속 차단) → Repair-2(패배 4종) → Repair-3(quiet 3종) → Repair-X(opening setup `Block 1`)로 적용했다.

| Block | Repair # | 같은 블록에 부착한 receipt 종류 | Receipt 한 줄 요약 | has_cider |
| --- | --- | --- | --- | --- |
| 1 | Repair-X | protection receipt | 시혁이 SCM 비용 절감 보고서 PDF를 자기 개인 메일로 사외 백업 — 회사 결재 시스템 밖에 '한시혁' 작성자란 1부 보존 | true |
| 25 | Repair-3 | weighted reevaluation receipt | 용인 센터 차 안에서 최부장이 시혁에게 첫 외부 발화 인정 ('너 빠지면 우리는 못 한다') | true |
| 32 | Repair-3 | next-card receipt | 같은 회의실에서 서정민이 즉답 동의 + 감사 데이터 요청서 양식 v2 그 자리에서 작성·캐비닛 등재 | true |
| 35 | Repair-3 | authority shift receipt | 같은 밤 시혁이 TF 간사 권한으로 야근 식대 결재 본인 신청 → 박전무 직보 자동 승인 (Lv5 예산 발언권 첫 자기 사용) | true |
| 43 | Repair-2 | next-card receipt | 같은 자리에서 시혁이 본사 공유 폴더의 '그룹 중기 전략 프레임워크' 68페이지 PDF 다운로드 — 본사 언어 원본 사전 1부 손에 쥠 | true |
| 48 | Repair-2 | next-card receipt + ally registration | 출처 위조 카드 온존을 이도현에게 명시 등록 ('아직 안 씁니다. 다음 카드 보고 결정합시다' / 이도현 즉답) | true |
| 53 | Repair-2 | protection receipt + role registration | 삭제 로그가 새로운 형태의 증거로 감사팀 등재 + 시혁 → 감사팀장 '핵심 품의서 아카이브 미러링 처리합시다' / 즉답 '오늘부터' | true |
| 63 | Repair-2 | next-card receipt | 전무실에서 나오는 복도 휴대폰 메모장에 선택지 C 한 줄 첫 등록 ('유통 팀장 + TF 유통 산하 + 전략실 보고 라인 유지') | true |
| 65 | Repair-1 | next-card receipt (paper) | 정밀검사 봉투 옆 책상 위 메모지에 선택지 C 첫 문장 + 제시 순서를 잉크로 등록 ('강민호 먼저, 전무는 그다음') | true |
| 66 | Repair-1 | external access shift + ally reinforcement | 같은 출근길 지하철에서 이도현으로부터 강민호 상무 오전 일정 + 비서실 사전 작업 메시지 도착 — 그룹 전략실 실무 라인이 시혁 쪽으로 한 칸 더 기움 | true |

## Engine Preservation Check

- 각 패치는 `content.reward` 필드만 수정. 다른 어떤 필드도 손대지 않음.
- 사건 순서: 모든 micro-event는 해당 블록 본문이 묘사하는 시간대(같은 날·같은 회의·같은 밤·같은 출근길) 안에서 발생하며 본문 묘사 사건과 시간 순서가 충돌하지 않음.
- 본문 시간이 명시된 곳:
  - `Block 1`: "회의가 끝나자 ... 자리로 돌아와 화면을 끈다" → 백업은 '화면을 끄기 직전' 동일 시점.
  - `Block 25`: "용인 센터를 왕복하는 일상" 2주 윈도우 → 차 안 한 줄은 그 윈도우 내.
  - `Block 32`: "회의가 끝난 뒤 시혁은 TF룸에서 멈춘다 ... 서정민에게 말한다" → 서정민 즉답·양식 v2 작성은 그 발화 직후.
  - `Block 35`: "1주" duration / "2025년 11월 초" → 같은 밤 결재.
  - `Block 43`: "회의가 끝난 뒤 ... 본사 공유 폴더에서 ... 다운로드한다" → 본문 그대로 사용.
  - `Block 48`: solution 시점("아무것도 하지 않는다") 안에서 이도현 단문 메시지.
  - `Block 53`: 본문에 이미 "삭제 로그를 확보하고 감사팀에 넘겼지만" 명시 → 그 직후 감사팀장과 한 마디.
  - `Block 63`: "전무실 ... 시혁이 답한다 '아직 모르겠습니다. 조금만 시간을 주십시오'" → 전무실 나오는 복도 메모.
  - `Block 65`: "결과지를 서랍에 다시 넣는다" → 그 직후 책상 위 메모지.
  - `Block 66`: "지하철에서 내려 그룹 본관으로 걸어가면서" → 지하철 안 메시지.
- 적대 구도·주인공 무기·아크 클라이맥스·승급 사다리 등 모두 무변경.

## Aggregate Effect (post-patch projection)

- 무보상 블록 카운트: **10 → 0** (10건 모두 same-block receipt 부착으로 `has_cider: true` 전환)
- 최장 no-cider drought: **2 → 0** (`Block 65→66` 연속 무보상 streak 해소)
- spec §6 활성 캡 변화:
  - "any no-cider block in the full-block cider scan → YELLOW ceiling": **해제** (사후 재감리 필요)
  - "rewardless pain blocks 2 in a row → GREEN ceiling": 사전부터 미발화, 변동 없음
  - "no-cider drought 6+ blocks → YELLOW ceiling": 사전부터 미발화, 변동 없음
  - "major defeat without next card in same/next block → YELLOW ceiling": 사전부터 미발화, 변동 없음
- spec §5 P1 axis 10 (blockwise cider continuity): 10건 무보상 → 0건 무보상이 되면 spec 정의상 `2`("every block lands a felt receipt") 진입 조건을 충족할 가능성. 단, 일부 패치(`Block 1, 25, 35, 65`)는 micro-token 성격이 강해 "weak bridge-only"로 재판정될 여지가 있어 `1`로 떨어질 수 있음. 정확한 확정은 다음 audit에서 strict 재평가 필요.
- 본 repair note는 effect 시뮬레이션이며 grade 갱신을 자동으로 의미하지 않는다. **정식 등급 갱신은 별도 read-only re-audit에서 확정한다.** spec §6 "any no-cider block" 캡이 0건 달성으로 해제되더라도, 다른 캡 발화 여부와 P1 재채점은 다음 audit의 권한이다.

## Validation

- JSON 무결성 확인: `python -c "import json; d=json.load(open(...)); print(len(d['blocks']))"` → **70 blocks** 유지, 파싱 OK.
- 수정 범위: 10건 reward 필드만. 총 블록 수·블록 ID·다른 필드 모두 보존.
- prior pass의 `Block 43/48/53/63` 지적은 모두 carry-forward되어 본 sweep에서 패치 적용 완료.

## Next Steps (참고)

1. 다음 audit cycle에서 패치된 TR을 spec v1 strict 기준으로 재감리 → P1 axis 10 재채점 + 캡 재평가 → grade 확정.
2. 본 sweep은 read-modify-write 1회 wave. 추가 wave는 audit 결과에 따라 결정.
3. BI/WG 파일은 무수정 (요청 범위 밖).

repair sweep complete; 10 flagged blocks patched in TR; engine and event order preserved
