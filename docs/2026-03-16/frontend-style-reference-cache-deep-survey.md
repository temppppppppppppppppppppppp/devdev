Date: 2026-03-16
Status: final
Topic: frontend-style-reference-cache-deep-survey
Scope: packaged desktop frontend plus Stage 0 style-reference-analysis and style-cache flow
Live Evidence Genre Anchor: investment (`project=00`, workspace `C:\Users\wjjo\Documents\글도비`)
Excluded: code changes, remediation execution SSOT, non-live genre behavior claims beyond inspected code

Commit State:
- Baseline Commit: `5a0177666e6877070d726d983d3c3e1d03e812d2`
- Baseline Dirty Summary: `dirty: tracked frontend/stage0 surfaces already modified in workspace; additional docs/log drift present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

**Findings**
1. Medium: Stage 0 스타일 레퍼런스 분석은 데스크탑 UI에서 완전 수동 프롬프트가 아니라, 프런트가 확인 프롬프트와 캐시 선택을 사전 확정하는 half-automated flow다. [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L5850), [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L6785), [modules/api/process_runner.py](/c:/Users/wjjo/Desktop/글도비/modules/api/process_runner.py#L682)
   Evidence: `_collectInputs()`가 항상 `stage0_style_cache_mode`를 넣고, `_build_stdin_sequence()`는 subkey `6`일 때 `y`와 cache choice를 stdin에 선주입한다. 그래서 엔진 로그에는 `분석을 시작하시겠습니까?`, `스타일 캐시 모드` 프롬프트가 보이지만, 실제 사용자는 추가 선택 없이 바로 진행된 것처럼 체감한다.
2. Medium: 스타일 캐시는 프로젝트별이 아니라 workspace-global per-genre 캐시다. [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L1005), [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L1028), [modules/core/stage0/__init__.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/__init__.py#L762), [modules/core/stage01_helpers.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L585)
   Evidence: current cache file lives at `Documents\글도비\config\style_references\investment\style_guide.json`, while the run also writes project-local `projects\00\stage0_output\style_guide.json` and DB anchor `anchors.style_guide`. The inspected run logged `장르 캐시 재사용`, the global cache mtime stayed `16:41:39`, and the project-local output was freshly written at `16:45:29`.
3. Medium: Cache invalidation watches a broader manifest than the actual analysis inputs. [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L300), [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L353), [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L377)
   Evidence: live investment ref dir contains root-level `0_합본_원본_backup.txt` and `style_seeds_final.txt` plus nested `참조작품1\0_합본.txt`. `_reference_manifest()` hashes all `*.txt` recursively, but `_load_reference_manuscripts_from_dir()` only loads child directories as works. The inspected run loaded `1개 작품, 1개 에피소드`, so root-level backup/seed txt changes can trigger conservative cache misses without changing the actual loaded work set.
4. Medium: Frontend support state for Style is file-based, not anchor-based. [modules/core/project_support.py](/c:/Users/wjjo/Desktop/글도비/modules/core/project_support.py#L276), [modules/api/bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py#L397), [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L4119)
   Evidence: `inspect_project_support_assets()` reads only `project_dir/stage0_output/style_guide.json` to decide `style_guide.ready`, tone, and pov. It does not consult the workspace-global cache file and does not consult `anchors.style_guide`. In the inspected project `00`, all three exist, so UI is coherent today; if the project-local file were missing while the DB anchor remained present, the support chip would degrade to pending.
5. Low: Stage 0 스타일 레퍼런스 분석 deliberately disables the normal boot stdout suppression, so the frontend log shows the full CLI boot/menu stream. [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L6598), [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L5890)
   Evidence: `_handleStdoutLine()` suppresses boot stdout unless `_shouldRevealBootStdout()` returns true; that helper returns true for Stage 0 subkey `6`. This matches the observed desktop log where genre selector, project selector, main menu, Stage 0 submenu, and cache menu are all rendered.
6. Low: Investment has a bounded packaged-to-workspace reference self-heal; other genres do not share that special-case bootstrap in the inspected code. [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L321), [modules/core/stage0/__init__.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/__init__.py#L649)
   Evidence: `prepare_reference_manuscripts()` only performs `packaged_sync` when `genre == "investment"` and packaged refs exist. Current live run did not need that path because workspace refs already existed, but the exception remains part of the active runtime contract.
7. Positive: The inspected style-analysis path is fully durable for downstream runtime use. [modules/core/stage01_helpers.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L585), [modules/core/project_support.py](/c:/Users/wjjo/Desktop/글도비/modules/core/project_support.py#L276)
   Evidence: current project `00` has `stage0_output/style_guide.json`, `anchors.style_guide`, and downstream Stage 3/4 logs explicitly loading and applying the guide (`톤: 진지`, `시점: 혼합`, `style_guide_extracted_pov=1인칭`, `effective_pov=혼합`).

**Pass 1 Inventory**
- Frontend entrypoints:
  - Stage 0 subkey `6` button and inline cache selector in [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L2846)
  - input collection in [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L5850)
  - pre-run cache log injection in [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L6930)
  - boot stdout reveal in [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L6598)
  - artifact ladder render in [geuldobi-desktop/src/index.html](/c:/Users/wjjo/Desktop/글도비/geuldobi-desktop/src/index.html#L4119)
- Bridge / runner surfaces:
  - cache mode value mapping in [modules/api/process_runner.py](/c:/Users/wjjo/Desktop/글도비/modules/api/process_runner.py#L114)
  - stdin boot sequence in [modules/api/process_runner.py](/c:/Users/wjjo/Desktop/글도비/modules/api/process_runner.py#L682)
  - artifact ladder payload in [modules/api/bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py#L397)
- Engine / Stage 0 surfaces:
  - operator flow in [modules/core/stage0/__init__.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/__init__.py#L637)
  - workspace-global cache + manifest logic in [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L321) and [modules/core/stage0/style_extractor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0/style_extractor.py#L1005)
  - project-local file readiness in [modules/core/project_support.py](/c:/Users/wjjo/Desktop/글도비/modules/core/project_support.py#L276)
  - DB anchor save in [modules/core/stage01_helpers.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L585)

**Pass 2 Semantic Classification**
- Frontend-controlled configuration:
  - inline selector expresses operator intent before run
  - renderer logs the selected cache mode before bridge `/run`
- Process-runner contract:
  - style-analysis path is not a plain prompt-driven interactive mode
  - runner preanswers confirm/cache prompts if the frontend provided a cache mode
- Engine-local cache semantics:
  - cache file is global to `workspace/config/style_references/<genre>/style_guide.json`
  - project-specific durable copies are emitted after analysis into `stage0_output` and `anchors.style_guide`
- UI observability:
  - style-analysis uniquely reveals boot stdout to expose progress
  - artifact ladder support chip reflects `stage0_output/style_guide.json`, not the global cache and not the DB anchor
- Bootstrap exception:
  - investment can self-heal packaged refs into workspace when missing

**Side-Effect Map**
- File writes:
  - global cache file: `config/style_references/investment/style_guide.json`
  - project-local artifact: `projects/<name>/stage0_output/style_guide.json`
  - no rollback file on `refresh`; `reset` explicitly unlinks the global cache before recompute
- DB writes:
  - `anchors.style_guide` saved after successful Stage 0 subkey `6`
  - `ui_events` table grows as part of broader runtime logging; inspected DB copy had `ui_events=581`
- JSONL / log / audit sinks:
  - `logs/control-plane-provenance.jsonl` records the Stage 0 subkey `6` run
  - `projects/00/logs/session_20260316_164527.log` records prompt progression, cache status, and anchor save
  - no style-analysis-specific soft failures were observed; current `soft_failures.jsonl` tail shows unrelated Stage 4 sink-alignment warnings only
- Console / UI output:
  - renderer prefaces the run with `[System] 스타일 캐시 모드: ...`
  - engine emits its own cache menu / result summaries
  - because boot suppression is disabled for this path, the operator sees verbose CLI bootstrap text
- Rollback / retry / recovery:
  - `cache_mode=use` returns hit only if cache meta matches
  - `cache_mode=refresh` skips hit path but retains file until rewritten
  - `cache_mode=reset` deletes the genre cache file first
- Cache / global state:
  - `StyleExtractor.last_cache_status` transitions through `hit`, `refresh`, `reset`, `miss`
  - cache reuse is scoped by genre + prompt contract hash + model id + manifest hash + protagonist POV contract
- Config / env / bootstrap fallback:
  - if workspace refs are absent and genre is investment, packaged refs may be copied into workspace first
  - non-investment genres do not have the same self-heal in the inspected code

**Non-Goals**
- This survey does not propose remediation steps.
- This survey does not override the active temp execution queue.
- This survey does not claim live validation for non-investment genres.

**Open Questions**
- None that block the survey itself. The code/evidence picture for the inspected surface is coherent above 95%.
- If a later task wants remediation, the main design choices to revisit are:
  - whether subkey `6` should remain half-automated
  - whether cache invalidation should hash only actually loaded works
  - whether the style-ready chip should consult DB anchor fallback
