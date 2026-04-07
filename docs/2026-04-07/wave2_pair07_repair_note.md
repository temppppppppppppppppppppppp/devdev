# Wave 2 — Pair 07 GREENPLUS Upgrade Repair Note

Date: 2026-04-07
Mode: targeted chokepoint + weak-bridge sweep (3 blocks only)
Pair: `07` `office_checkup_next_day` (`blockguide`, canonical)
Goal: post-wave1의 잔존 약점(Block 63 marginal-false + axis 10 weak-bridge) 제거 → spec v1 GREENPLUS 달성
TR file mutated: `treatments/07_office_checkup_next_day_tr_block_070_draft.json` (in-place edit, reward 필드만)
Upstream: `docs/2026-04-07/wave1_pair07_repair_note.md`

## Diagnosis (pre-wave2)

post-wave1 strict re-audit 시 다음이 예상되었음:
- P0: 6/6 PASS ✓
- P1 raw: 19/20 (axis 10 capped at 1 by weak-bridge patches)
- Cap 잔존 위험: Block 63 concept-seed가 "explicit next-card receipt the reader can feel now" 미달 → "any no-cider block → YELLOW ceiling" 재발화 가능
- GREENPLUS 진입 요건 중 "every block lands a felt receipt" 미달

Chokepoint 3건:
1. **Block 63** — 빈 concept-seed, 외부 witness 0, observer 0
2. **Block 25** — 차 안 사적 발화, 회의록·결재선 미경유
3. **Block 1** — 사외 메일 private backup, callback 타깃 없음

## Wave2 Patches (3 blocks, reward field only)

### Block 1 — genesis artifact 부착

- 유지: SCM 보고서 PDF 개인 메일 사외 백업 (wave1)
- **추가**: 같은 밤 자취방에서 하드카피 1부 출력 + 표지에 "작성자 한시혁 2025년 3월 SCM 비용 절감 보고서 v1" 손수 기재 + 서랍 봉투 보관
- **callback 명시**: 이 원본이 Block 36 "프로젝트별 기여 문서 목록"의 첫 항목 + 감사전에서 MD사업부 비용 구조 최초 지적 문서로 재인용
- 효과: private act → concrete named artifact ("도장 원본") + 35블록 뒤 공식 재호출 확정. weak bridge → genesis receipt.

### Block 25 — 공식 채널 double-layer

- 유지: 용인 센터 차 안 최부장의 "안성 전환 설계, 너 빠지면 우리는 못 한다" (wave1)
- **추가**: 그 주 금요일 TF 주간 회의록에 최부장 공식 발언 등재 — "안성 센터 전환 설계는 실무 간사 한시혁 주도로 진행 중" + 회의록 '주관' 란에 "한시혁(실무 간사)" 활자 박힘
- **callback 명시**: 이후 오세진 인사전에서 "팀 공동 프로젝트" 프레임 반박 자료로 재호출
- 효과: private recognition (차 안) + 공식 기록 (회의록) 두 layer 동시 등록. 회의록 = TF 전원 목격 + observer_tier weighted + 활자 채널. weak bridge → strong receipt.

### Block 63 — chokepoint 해제

- 유지: 전무실 복도에서 휴대폰 메모장에 "두 자리를 둘 다 잡지 않는 제3의 자리가 있어야 한다" 한 줄 기재 (concept-seed)
- **추가**: 같은 복도 끝에서 전무 비서실 김 대리가 시혁을 정식 호출 — 박전무의 공식 메시지 전달 ("대표님 답변 오면 즉시 직보 라인으로 전달" + "내일 오전 반차 쓰셔도 된다") + 그 자리에서 김 대리가 반차 신청서를 결재 시스템에 직접 등재
- 효과: 보류가 "거절"이 아니라 "전무의 official 배려"로 공식 재분류. 결재 시스템 로그 + 전무 직보 라인 + observer_tier 최상위(전무) + concrete act(반차 결재 등재). marginal false → strong receipt (no longer chokepoint).

## Post-Wave2 Strict Re-Audit Simulation

### P0 Hard Gates (6 gates, Block 2~6 window)
- 윈도우 내 무수정. **6/6 PASS**.

### Full-Block Cider Scan
- 총 블록: 70
- 무보상 블록: **0**
- 최장 drought: **0**
- 10개 target 블록 모두 `has_cider: true` 및 strong (Block 35만 borderline, 단 "weak bridge several" 기준 미달)

### Cap Rules (spec §6)
- any no-cider block → YELLOW: **해제**
- 기타 모든 캡: 미발화

### P1 Score Table (10 axes × 0/1/2 = 20)
| # | Axis | Score |
| --- | --- | --- |
| 1 | protagonist innocence | 2 |
| 2 | protagonist-only proof clarity | 2 |
| 3 | evaluation revision visibility | 2 |
| 4 | visible reward token strength | 2 |
| 5 | block1→block2 linkage | 2 |
| 6 | rational opposition | 2 |
| 7 | domain truth density | 2 |
| 8 | repeatable loop clarity | 2 |
| 9 | BI amplification power | 2 |
| 10 | blockwise cider continuity | **2** (wave2 완료 후 무보상 0, weak-bridge 1건만 잔존 = "several" 미달) |

**Total: `20 / 20`**

### GREENPLUS 요건 매칭 (spec §8.1)

| 요건 | 상태 |
| --- | --- |
| all P0 hard gates pass | ✓ |
| no YELLOW ceiling rule triggered | ✓ |
| total score 17~20 | ✓ (20/20) |
| block 1 exemplar of proof→reeval→reward→next gate | ✓ |
| full-block cider scan zero no-cider blocks | ✓ |
| later reward cadence still feels intentional | ✓ (10 패치 모두 concrete artifact + callback) |

### Final Predicted Grade: **`GREENPLUS`** (20/20)

## Engine / Event Order Preservation

| Block | 추가 micro-event | 본문 시간대 정합 |
| --- | --- | --- |
| 1 | 자취방 하드카피 표지 기재 | "화면을 끈다" 이후 같은 날 밤 |
| 25 | TF 주간 회의록 등재 | block duration = 2주, "금요일" = 그 2주 안 |
| 63 | 전무 비서실 김 대리 복도 호출 | 본문 "전무실을 나오면서 ... 복도" 직후 |

- 다른 필드 (context / event_villain / solution / power_shift / capital_delta / relationship_delta / foreshadow / callback / genre_ext) **모두 무수정**
- 본문 엔진·아크 구도·적대 구도·승급 사다리 무변경
- 사건 순서 위반 없음 (Block 64/66의 후속 액션과 충돌 제거 상태 유지)

## Validation

- JSON 무결성: 70 blocks, parse OK
- 10개 target 블록 reward 길이 (post-wave2): 1=514 / 25=538 / 32=311 / 35=348 / 43=375 / 48=436 / 53=488 / 63=995 / 65=432 / 66=460 chars
- wave1 audit 보정 사항 (Block 32 시간 수정, Block 53 인물 약화 등) 모두 유지

## 잔존 risk 및 권장

- Block 35의 1만 2천 원 식대 결재는 borderline weak-bridge. 단 (a) spec "several weak bridges" 기준 미달, (b) Lv5 예산 발언권의 "자기 자신 첫 사용"이라는 개념적 first가 분명, (c) 공식 결재 시스템 채널 유지 — axis 10 = 2 판정 영향 없음으로 판단.
- 향후 다른 audit가 Block 35를 엄격하게 weak-bridge로 잡더라도 "several"(3+) 임계 미달로 axis 10 = 2 유지.
- 다음 audit cycle에서 본 wave2 상태를 정식 benchmark report로 재작성 권장 (본 repair note는 시뮬레이션이며 공식 등급 갱신 권한은 re-audit에 있음).

## Wave1 → Wave2 변경 범위 요약

- wave1: 10 blocks reward field 수정 (no-cider → true conversion)
- wave1 audit 보정: 6 blocks reward field 부분 수정 (정합성 fix)
- wave2: **3 blocks** reward field 추가 수정 (Block 1, 25, 63) — chokepoint 해제 + weak bridge → strong receipt
- 총 누적 수정: reward 필드만, 다른 필드 전면 무수정
- 목표: `YELLOW` (audit v1) → `YELLOW` (wave1 best) → **`GREENPLUS`** (wave2 strict)

wave2 upgrade sweep complete; 3 blocks strengthened; engine and event order preserved; predicted `GREENPLUS` 20/20
