# shipbuilding_ocean_heir Blocks 001-010 Audit

Date: 2026-05-01
Work: `shipbuilding_ocean_heir`
Family: `blockguide`
Source TR: `treatments/shipbuilding_ocean_heir_tr_block_010_draft.json`
Phase0: `treatments/phase0/shipbuilding_ocean_heir_phase0_design.json`
Work Guard: `work_guards/shipbuilding_ocean_heir.yaml`

## Verdict

PASS.

Blocks 001-010 are accepted as the opening ten-block window. The next production unit is `Block 011`, not BI. BI remains blocked until a complete source TR and source TR handoff gate exist.

## User Correction Applied

The current operating interpretation is:

- `1 TR block = 2~6 serialized episodes`
- each block must contain at least one secondary incident beyond the main incident
- protagonist decisions must be self-interested and efficiency-driven
- kindness or evil is secondary; concrete gain, authority, access, risk control, and future leverage are primary

## Pass 1: Episode-Bundle Density

PASS.

All ten blocks include `genre_ext.episode_bundle_density.primary_incident` and `secondary_incident`.

- B001: 수주 발표 제동 + 해운 계열 추가 선박 확보안
- B002: 후판 조항 proof + 엔진 납기 콜 회의 연결
- B003: 조선소 capacity proof + 기자재 협력사 납기 확약 지연
- B004: 보증 조건표 proof + 은행 한도 확인 전화
- B005: 선주 옵션 계약 재협상 + 언론 수주설/해운 장기 용선 압박
- B006: 수정 계약안 승인 + 은행 보증 한도 갱신안
- B007: 해운 장기 용선 보류 + 단기 고운임 화물 계약 제안
- B008: 엔진/기자재 경쟁입찰권 + 외부 기자재사 확정 납기 견적
- B009: 채권단 질의 대응권 + 경제지 최대 수주 축소 루머
- B010: 해외 조선소 M&A veto권 + 현지 법무법인 환경 규제 메일

This is dense enough to treat each block as an episode bundle rather than a single episode beat.

## Pass 2: Self-Interest / Efficiency

PASS.

Seo-jun is not framed as saving the group out of goodness. The repeated decision logic is:

- avoid reliving liquidation cleanup
- convert proof into authority
- reduce future cash-flow exposure
- keep upside only when downside is contractually capped
- make every next board pass through his risk table

No block closes on charity, sentiment, or praise-only reward.

## Pass 3: Same-Block Cider / Receipt

PASS.

All blocks have `genre_ext.block_cider.has_cider = true`, `pain_only_exit = false`, and a named receipt.

Receipt ladder:

- B001: 원본 계약서 확인 발언권
- B002: 계약조건 재검토 7일 권한
- B003: 생산 원자료 접근권
- B004: 선박금융 보증 검토 배석권
- B005: 조건부 수주 재협상 기준표
- B006: 선박금융 리스크 TF장
- B007: 해운 운임 검토권과 장기 용선 보류권
- B008: 엔진/기자재 경쟁입찰권
- B009: 채권단 질의 대응 회의 입장권
- B010: 해외 조선소 M&A 실사 참여권과 조건부 veto권

## Pass 4: Continuity

PASS.

`scripts/block_continuity_checker.py --work-id shipbuilding_ocean_heir --family blockguide` returned CLEAN.

Manual spot-check also found:

- block count: 10
- capital/authority ladder continuity: OK
- replacement character: 0
- triple-question placeholder: 0

## Pass 5: Next-Step Gate

PASS with boundary.

The next required unit is:

`Block 011: 선박금융의 목줄`

Block 011 should open ARC-02 and must keep the faster pacing rule:

- primary incident: 보증 분리 협상 table opens with a bank/covenant pressure
- secondary incident: one contract, bank memo, shipowner callback, or internal finance leak complicates the scene
- Seo-jun's self-interest: he wants bank-facing authority and direct access to covenant language, not moral approval
- same-block receipt: bank-meeting observer/speaking slot or covenant memo access

## Final Note

Do not enter BI yet. Current TR is a 10-block partial draft. Continue sequential TR production from Block 011 under the same blockguide production cap.

## 2026-05-01 Density Repair Addendum

PASS.

Before final source TR handoff, Blocks 001-010 were repaired for the fast-pacing `2-6 episode bundle` density gate.

- target: remove thin opening bundles under 650 core chars
- repaired blocks: 001-010
- post-repair minimum bundle core chars: 668
- post-repair thin bundle count under 650 chars: 0
- repair principle: preserve existing capital ladder, then add operational pressure, secondary incidents, concrete receipts, and Seo-jun's self-interested efficiency logic inside the same block

The opening ten-block audit remains PASS after repair.
