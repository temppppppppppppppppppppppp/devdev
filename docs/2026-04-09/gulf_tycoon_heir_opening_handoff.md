# gulf_tycoon_heir opening handoff

Date: 2026-04-09
Work ID: `gulf_tycoon_heir`
Title: `알고 보니 내 아버지가 걸프 대부호였다`
Purpose: `Opus-safe continuation handoff for ARC-01 opening`

## 1. Read Order

1. `docs/2026-04-09/gulf_tycoon_heir_live_status.md`
2. `material_ssot/20_pitch/canon/gulf_tycoon_heir.md`
3. `treatments/phase0/gulf_tycoon_heir_phase0_design.json`
4. `treatments/phase0/gulf_tycoon_heir_phase0_prompt_roadmap.json`
5. `treatments/gulf_tycoon_heir_tr_block_001_draft.json`

## 2. Saved Boundary

- current saved boundary: `Block 5`
- next legal continuation: `Block 6`
- next allowed range for one continuation order: `Block 6-10 only`
- stop at: `Block 10`
- after stop: run `Block 1-10 self-audit`

## 3. What Is Already Fixed

- `Block 1 검은 봉투`
  - setup lock: 한국에서 개고생하던 태하 앞에 하산이 직접 찾아온다
  - receipt: `guest-heir` 임시 배지 + 혈통 확인 청문 입장권
- `Block 2 혈통 확인`
  - receipt: K-Transit 7 `90일 임시 운영권` + limited protection
- `Block 3 동결 계좌`
  - receipt: cargo seizure 회피 + `emergency signatory override`
- `Block 4 빈 창고`
  - receipt: first free-zone cash line
- `Block 5 우회 선적`
  - receipt: `direct report line` + `board observer seat`

These five are current truth. Do not rewrite them unless a concrete schema or consistency issue is found.

## 4. Immediate Target Blocks

- `Block 6 서명권`
  - function lock: 은행 롤오버와 항만 슬롯 연장을 동시에 성사시켜 다음 자산 인수전 입장권을 연다
  - receipt target: `next_gate_opening`
- `Block 7 가짜 어음`
  - function lock: old-guard가 fake paper와 split invoice로 태하를 역으로 엮어 넣으려 한다
  - `defeat block` lock
- `Block 8 현금흐름표`
  - function lock: cash conversion cycle과 누수 지도를 다시 그려 K-Transit 7의 진짜 목줄을 정리한다
  - `quiet block` lock
- `Block 9 항만 슬롯`
  - function lock: 칼리즈 포트 슬롯을 고정시키며 port corridor의 첫 실권을 잡는다
- `Block 10 가족회의`
  - function lock: family meeting에서 태하가 temporary heir가 아니라 inside operator라는 사실을 공식화한다
  - ARC-01 exit lock

## 5. Opening Doctrine

- Block 1 is setup only. Opening rescue does not start there.
- Block 1 must include `한국 back-office 개고생 -> 하산 직접 방문` before the move into the family office battlefield.
- Opening cider ledger is already satisfied by Block 2-5 and must stay intact.
- The opening engine is:
  - family return -> operating right
  - operating right -> first proof
  - proof -> first cash line
  - cash line -> board access
  - board access -> rollover + port gate opening
- Do not turn this into harem, luxury-tour, or exotic-display fiction.
- Do not turn siblings into simple villains.
- Do not use free money or automatic inheritance as the solution.
- If a prompt/check/merge harness needs roadmap input, use `treatments/phase0/gulf_tycoon_heir_phase0_prompt_roadmap.json`, not the root Phase0 file directly.

## 6. Character Guardrails

- 윤태하 is not a chosen prince. He is a systems operator.
- 하산 is not a soft father figure. He gives conditions, not comfort.
- 파이살 is not a villain. He is a warm brother trapped inside his own asset and people line.
- 라일라 is not a cold rival princess. She respects receipts and cannot spend treasury trust casually.
- 사미르 is not sentimental. He trusts covenants, numbers, and proof.
- old-guard line is not cartoon evil. They defend their seat by permits, invoices, brokers, board rhythm, and timing.

## 7. Copy-Paste Order

```text
gulf_tycoon_heir / 알고 보니 내 아버지가 걸프 대부호였다

current truth first:
- docs/2026-04-09/gulf_tycoon_heir_live_status.md
- docs/2026-04-09/gulf_tycoon_heir_opening_handoff.md
- material_ssot/20_pitch/canon/gulf_tycoon_heir.md
- treatments/phase0/gulf_tycoon_heir_phase0_design.json
- treatments/phase0/gulf_tycoon_heir_phase0_prompt_roadmap.json
- treatments/gulf_tycoon_heir_tr_block_001_draft.json

order:
- tr_continue only
- preserve saved Block 1-5 exactly
- append Block 6-10 only
- Block 7 is the locked defeat block
- Block 8 is the locked quiet block
- stop at Block 10
- then run Block 1-10 self-audit
- do not start BI or work_guard
- do not widen past the 5-block continuation cap
```

## 8. Prepared Prompt Bundle

- preferred low-intelligence prompt bundle:
  - `docs/2026-04-09/gulf_tycoon_heir_tr_prompt_006_010.txt`
- this prompt bundle was generated from:
  - `treatments/gulf_tycoon_heir_tr_block_001_draft.json`
  - `treatments/phase0/gulf_tycoon_heir_phase0_prompt_roadmap.json`
- use the prepared prompt bundle as-is when a downstream model is prone to drifting from `Block 6-10` boundaries
