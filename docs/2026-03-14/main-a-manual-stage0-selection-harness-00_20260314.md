<!-- [참고자료] -->
# `main_a.py` Manual Stage 0 Selection Harness - `00_20260314`

Created: 2026-03-14
Last Re-Audited: 2026-03-14
Status: `captured-from-terminal-log`
Scope: system-track manual runtime replay
Source: pasted interactive terminal log captured during `python main_a.py`

## 1. Purpose

- Preserve the exact operator choices used in the observed `main_a.py` manual run.
- Make the run replayable without relying on memory.
- Separate:
  - raw numeric inputs actually typed during the captured run
  - stable semantic targets that should be chosen even if list ordering changes later

## 2. Run Summary

Observed high-level flow:

1. launch `python main_a.py`
2. choose genre `투자`
3. choose project `00_20260314`
4. run `Stage 0 -> 기존 방식 - Bible/Treatment 파일 선택`
5. set protagonist config
6. return to main menu
7. run `Stage 0 -> 스타일 레퍼런스 분석`
8. choose style cache mode `캐시 사용`

## 3. Replay Notes

This harness preserves both:

- `raw_input`: what was actually typed in the captured session
- `semantic_target`: what the choice meant

Important:

- project list order can change
- Bible list order can change
- roadmap list order can change

Future replay should prefer `semantic_target` over raw ordinal numbers when list ordering differs.

## 4. Captured Operator Transcript

| Step | Screen | Raw Input | Semantic Target | Notes |
| --- | --- | --- | --- | --- |
| 1 | Genre selector | `3` | `투자 (Investment Fiction)` | genre preset = `investment` |
| 2 | prompt | `Enter` | `프로젝트 선택으로 이동` | literal enter press |
| 3 | Project selector | `1` | `00_20260314` | index-sensitive |
| 4 | Main menu | `0` | `Stage 0` | first Stage 0 entry |
| 5 | Stage 0 submenu | `1` | `기존 방식 - Bible/Treatment 파일 선택` | existing file path mode |
| 6 | Bible selection | `1` | `01_bi_투자물_골든_카나리아 테스트.json` | index-sensitive |
| 7 | Roadmap selection | `1` | `01_tr_투자물_골든_카나리아 테스트.json` | index-sensitive |
| 8 | Treatment block condensation | `n` | `자동 농축 미수행` | explicit opt-out |
| 9 | Protagonist world origin | `2` | `원시인` | saved to Bible |
| 10 | Protagonist incarnation type | `1` | `회귀자` | saved to Bible |
| 11 | POV selection | `4` | `혼합` | saved to Bible |
| 12 | External POV insert policy | `3` | `적극 허용` | saved to Bible |
| 13 | prompt | `Enter` | `메뉴로 돌아가기` | after Stage 0 file-selection flow |
| 14 | Main menu | `0` | `Stage 0` | second Stage 0 entry |
| 15 | Stage 0 submenu | `6` | `스타일 레퍼런스 분석` | style extraction path |
| 16 | Start analysis confirmation | `y` | `분석 시작` | confirmed |
| 17 | Style cache mode | `1` | `캐시 사용 (기본)` | cache reuse path |
| 18 | prompt | `Enter` | `메뉴로 돌아가기` | after style extraction |
| 19 | prompt | `Enter` | `메뉴로 돌아가기` | second return prompt seen in log |

## 5. Replay-Friendly Raw Input Sequence

Use this only when the displayed list ordering still matches the captured session:

```text
3
<ENTER>
1
0
1
1
1
n
2
1
4
3
<ENTER>
0
6
y
1
<ENTER>
<ENTER>
```

## 6. Stable Semantic Replay Sequence

Use this when list ordering may have changed:

1. select genre: `투자 (Investment Fiction)`
2. continue to project selection
3. select project: `00_20260314`
4. main menu -> `Stage 0`
5. Stage 0 submenu -> `기존 방식 - Bible/Treatment 파일 선택`
6. choose Bible file: `01_bi_투자물_골든_카나리아 테스트.json`
7. choose roadmap file: `01_tr_투자물_골든_카나리아 테스트.json`
8. answer `no` to Treatment Block auto-condense
9. protagonist config:
   - world origin = `원시인`
   - incarnation type = `회귀자`
   - pov = `혼합`
   - external POV insert policy = `적극 허용`
10. return to main menu
11. main menu -> `Stage 0`
12. Stage 0 submenu -> `스타일 레퍼런스 분석`
13. confirm analysis start = `yes`
14. style cache mode = `캐시 사용`
15. return to main menu

## 7. Observed Side Effects

Observed from the captured log:

- project genre info saved as `투자 (Investment Fiction)`
- selected roadmap:
  - `01_tr_투자물_골든_카나리아 테스트.json`
- protagonist config saved:
  - `world_origin = 원시인`
  - `incarnation_type = 회귀자`
  - `pov = 혼합`
  - `external_pov_insert_policy = 적극 허용`
- style guide output saved at:
  - `projects/00_20260314/stage0_output/style_guide.json`
- style guide also saved into DB anchor:
  - `style_guide`

## 8. Harness Interpretation Boundary

This document is a manual operator harness, not an auto-captured event log.

It can reliably preserve:

- the observed choice sequence
- the semantic meaning of each choice
- the expected side effects visible in the terminal log

It does not guarantee:

- that future menu ordering remains identical
- that future Bible/roadmap file numbering remains identical
- that the same cache state or analysis duration will recur

## 9. Recommended Next Upgrade

If this should become stronger runtime evidence rather than a manual note, the next step is:

- persist Stage 0 operator prompts and selections as structured session events
- store both `display_index` and `resolved_target_label`
- make replay possible without relying on terminal capture
