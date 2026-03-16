<!-- [완료] -->
# Investment EPUB Gemini Corpus Execution SSOT

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/investment-epub-gemini-corpus-execution-ssot.md`
Temp Mirror Path: `docs/temp/investment-epub-gemini-corpus-execution-ssot.md`
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, docs/report_investment_epub_pipeline.md, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/report_investment_epub_pipeline.md`
Evidence Artifacts: `embedded in docs/report_investment_epub_pipeline.md via 2026-03-14 NAS rescan and legacy script inspection; no separate evidence files saved`
Side-Effect Coverage: covered
Confidence Target: 95%
Current Confidence: 96%
Live Workspace Revalidation: 2026-03-14 PASS
Revalidated Confidence: 96%

## 1. Intent

- Realize a bounded toolchain that converts trusted EPUB originals into a Gemini-ready supervised-tuning corpus.
- Fix the specific failure modes identified in the re-audit:
  - wrong SSOT folder selection
  - brittle filename parsing
  - brittle `chapter_1.xhtml` extraction
  - lack of dedupe and validation split discipline
- Keep the implementation bounded to tooling and validation.
- Do not treat this item as approval to run a full NAS-scale corpus build or Vertex AI job unless the user separately asks for that operation.

## 2. Baseline Facts

- Governing survey: `docs/report_investment_epub_pipeline.md`
- Candidate title set: 27 title folders, title-based candidate set only, not yet final gold-label investment set
- Raw EPUB total across candidates: 10,993
- SSOT EPUB total after current folder rules: 8,724
- Current SSOT selection families:
  - `prefer-standard-serial-epub`: 16 titles
  - `prefer-root-superset-or-equal`: 7 titles
  - `prefer-renamed-after`: 3 titles
  - `prefer-final`: 1 title
- Current filename families observed in SSOT paths:
  - `pure_number`
  - `id_number`
  - `title_number_hwa`
  - `title_number_plain_suffix`
- Current EPUB content layout families observed:
  - `chapter_1.xhtml`
  - `Section0001.xhtml`
  - `chapter_1.xhtml + Section0001.xhtml`
  - `Section0001.xhtml + Section0002.xhtml`
  - mixed `.html` / `.htm` via OPF spine
- Existing text folders are explicitly untrusted and out of bounds as corpus input.
- Gemini managed tuning requires JSONL example format; raw txt is only an intermediate artifact.

## 3. Scope

Included:

- implementation of SSOT title/folder selection logic for the current 27-title candidate set
- implementation of EPUB episode number parsing for all currently observed filename families
- implementation of EPUB text extraction based on `container.xml -> content.opf -> manifest/spine`
- implementation of UTF-8 episode txt emission, `manifest.json`, and `errors.log`
- implementation of Gemini supervised-tuning JSONL builder using continuation-style examples
- implementation of validation split rules that avoid naive random leakage
- representative smoke validation on a small set of titles that cover the observed layout and naming variants

Excluded:

- final business approval of the 27-title set as the permanent investment gold set
- full 8,724-episode production corpus build on the NAS
- GCS upload
- Vertex AI tuning job submission
- prompt experimentation beyond the core continuation-style schema
- narrative-pipeline documents or work-id based production flows

## 4. Pass 1. Inventory Summary

- primary evidence surfaces:
  - `docs/report_investment_epub_pipeline.md`
  - `C:\Users\User\Desktop\reference\2_단행본 보조 스크립트\1_EPUB-TXT 변환 및 합본-개선.py`
  - NAS source root `\\172.16.10.120\소설사업부\판무사업팀\2. 연재 진행 파일\1. 제작 진행 연재_Epub`
- implementation surfaces expected:
  - `scripts/` for the extractor and JSONL builder
  - `data/investment_corpus/` for local outputs
  - optional `tests/` coverage for filename parsing and EPUB extraction edge cases
- main hotspots from the re-audit:
  - folder SSOT ambiguity in titles with root plus subfolder duplicates
  - OPF/spine parsing instead of fixed XHTML path assumptions
  - duplicate episode detection
  - schema-safe JSONL assembly for Gemini supervised tuning

## 5. Pass 2. Semantic Classification

### Class A. Source Selection and Provenance

- input authority is the NAS EPUB tree only
- existing txt, hwp, hwpx, cover assets, and ad hoc exports are non-authoritative
- per-title SSOT choice must be recorded in manifest metadata

### Class B. Extraction and Normalization

- extraction authority is the EPUB spine, not filename heuristics inside the archive
- output authority is per-episode UTF-8 txt
- normalization must be deterministic enough for dedupe and repeatable reruns

### Class C. Training Dataset Construction

- training output authority is Gemini supervised-tuning JSONL
- dominant example type should be local continuation windows
- validation must be split by title or contiguous episode block, not random line shuffle

### Class D. Operator Safety

- the first implementation pass should prove correctness on representative titles before any full-batch operation
- the toolchain must be resumable from manifest plus logged failures

## 6. Side-Effect Map

- file writes / artifacts:
  - local txt outputs under `data/investment_corpus/titles/`
  - `data/investment_corpus/manifest.json`
  - `data/investment_corpus/errors.log`
  - `data/investment_corpus/gemini/train.jsonl`
  - `data/investment_corpus/gemini/val.jsonl`
- DB / schema / transaction boundaries:
  - not applicable in this execution item
- JSONL / log / audit sinks:
  - JSONL training and validation datasets
  - local extraction error log
  - local per-title corpus manifest
- console / UI / operator output:
  - progress lines
  - title-level warnings
  - duplicate or malformed EPUB notices
- rollback / recovery / retry:
  - rerun from source EPUBs must be safe
  - partial outputs must be overwritable or cleanly resumable
  - failed EPUBs must be isolated via `errors.log`
- cache / global state:
  - no long-lived cache or shared global runtime state should be introduced
- bootstrap fallback / config-env mutation:
  - source path and output root may be configurable
  - no env mutation or application bootstrap mutation is required

## 7. Realization Architecture

- preferred implementation shape:
  - one extractor entry point
  - one JSONL builder entry point
  - shared utility layer for SSOT selection, filename parsing, and normalization
- extractor contract:
  - input: configured NAS root plus candidate title manifest
  - output: per-title episode txt, manifest metadata, error log
- JSONL builder contract:
  - input: extracted txt corpus
  - output: Gemini-compatible `train.jsonl` and `val.jsonl`
- canonical extraction rule:
  - read `container.xml`
  - resolve OPF path
  - parse manifest and spine
  - gather ordered text/html documents excluding cover/copyright/navigation noise
  - normalize text and emit UTF-8
- dedupe contract:
  - dedupe at least by normalized text hash within a title
  - log duplicate collisions instead of silently overwriting
- validation split contract:
  - no naive random split over windows from the same contiguous episode stream
  - prefer title-level holdout when data volume permits
  - otherwise use contiguous episode blocks reserved for validation

## 8. Execution Tranches

1. Lock the title manifest and codify the current SSOT folder selection rules from the governing survey.
2. Implement EPUB extraction with episode parsing, OPF/spine traversal, UTF-8 text normalization, and manifest/error logging.
3. Implement JSONL generation for continuation-style Gemini supervised-tuning examples plus non-leaky validation split logic.
4. Run representative smoke validation on titles covering:
   - root-level EPUB authority
   - renamed/final SSOT folder authority
   - `chapter_1.xhtml`
   - `Section0001.xhtml`
   - multi-document spine
5. Refresh the governing report only if implementation evidence materially contradicts the current survey.

## 9. Acceptance Criteria

- the implementation can reproduce the current SSOT selection rules on the 27-title candidate set
- the implementation can parse all observed filename families without manual rename prework
- the extractor does not depend on fixed archive names such as `chapter_1.xhtml`
- extracted episode txt files are UTF-8, stable, and naturally ordered with zero-padded filenames
- manifest metadata records title, source path, SSOT path, selection rule, episode count, and duplicate/error status
- Gemini JSONL output conforms to the supervised-tuning schema with `systemInstruction` plus `contents`
- validation data is split by title or contiguous episode block, never by naive random per-window shuffle
- representative smoke validation passes on the audited edge-case titles before any full-batch run is considered

## 10. Verification Plan

- parser unit checks for the four observed filename families
- extractor checks against representative EPUBs from:
  - `금수저 투자백서`
  - `대기업 말단이 일을 잘함`
  - `만렙요원 재벌이 되다`
  - `재벌집 막내 도련님은 악당입니다!`
  - `창업의 신`
- manifest verification:
  - per-title episode counts are plausible
  - duplicate collisions are logged
  - failed extractions are logged
- JSONL verification:
  - each line is valid JSON
  - each line includes `systemInstruction` and `contents`
  - no empty `model` text
  - validation split contains no overlap with training windows from the same reserved holdout surface
- UTF-8 verification on emitted txt and JSONL files

## 10A. Current-State Revalidation

- Revalidated immediately before implementation start on 2026-03-14.
- `HEAD` remains `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`.
- Workspace drift since baseline is `none`; dirty surfaces remain documentation-local and do not change the planned implementation surface.
- The governing survey still matches live evidence for:
  - SSOT title counts
  - folder selection rules
  - filename families
  - EPUB content layout variants
  - Gemini 2.5 Pro managed tuning direction
- Revalidation outcome: the execution order and acceptance criteria remain sufficient for implementation start.

## 11. Guardrails

- do not read or merge legacy txt into the new corpus
- do not hardcode `chapter_1.xhtml` or any small fallback list as the authoritative extraction rule
- do not start with a full NAS-scale batch run before representative smoke validation passes
- do not treat the 27-title candidate set as final business-approved gold labels without the separate content review pass
- do not design the JSONL schema around long natural-language prompts that drown the continuation signal
- do not use random window-level validation splits that leak adjacent context into both train and validation

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: satisfied; canonical SSOT updated with closure evidence and temp mirror eligible for removal
- roadmap dependency: none; this is the only active execution SSOT mirror at creation time

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note

- closure status: `closed`
- realized scope:
  - added candidate title manifest at `scripts/investment_epub_title_manifest.json`
  - added shared corpus utility layer at `scripts/investment_corpus_support.py`
  - added extractor CLI at `scripts/build_investment_epub_corpus.py`
  - added Gemini JSONL builder CLI at `scripts/build_investment_gemini_jsonl.py`
  - added synthetic EPUB and dataset coverage at `tests/test_investment_epub_corpus_tools.py`
- verification evidence:
  - `python -m pytest tests/test_investment_epub_corpus_tools.py -q`
  - `python -m ruff check scripts/investment_corpus_support.py scripts/build_investment_epub_corpus.py scripts/build_investment_gemini_jsonl.py tests/test_investment_epub_corpus_tools.py`
  - `python -m ruff format --check scripts/investment_corpus_support.py scripts/build_investment_epub_corpus.py scripts/build_investment_gemini_jsonl.py tests/test_investment_epub_corpus_tools.py`
  - live smoke extraction against representative NAS titles covering:
    - standard serial folder + `chapter_1.xhtml`
    - standard serial folder + `Section0001.xhtml`
    - root-superset SSOT selection
    - mixed `.htm` spine extraction
    - `prefer-final` SSOT selection
- residual risk:
  - full NAS-scale batch extraction remains intentionally unrun in this item
  - 27-title candidate set still needs content-level business review before final training inclusion
- follow-up:
  - next operator action, if requested: run the extractor on the approved title set and inspect `manifest.json` plus `errors.log`
  - next realization item, if requested: perform full corpus build and Gemini upload/tuning runbook
- temp cleanup action:
  - remove `docs/temp/investment-epub-gemini-corpus-execution-ssot.md` after final queue validation
