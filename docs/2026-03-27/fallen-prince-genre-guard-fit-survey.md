# fallen_prince_buys_joseon Genre Guard Fit Survey

Date: 2026-03-27
Type: system-track genre-guard fit survey
Scope: compare built-in `alt_history` vs `investment` guard suitability for `fallen_prince_buys_joseon` under the current live workspace

Commit State:
- Baseline Commit: `161b71348732e06d9542daf3f54ad8a65126eada`
- Baseline Dirty Summary: `dirty: many tracked/untracked; target hotspots include bible/_quarantine/05_fallen_prince_buys_joseon_bi.json and docs/2026-03-27/fallen-prince-*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Question

현재 글도비 시스템에서 `fallen_prince_buys_joseon`을 돌릴 때,
내장 장르가드를 `alt_history`로 두는 편이 맞는가, 아니면 `investment`로 두는 편이 맞는가.

이 문서는 **작품 취향**이 아니라 **현재 시스템 계약과 런타임 보호장치** 기준으로 판정한다.

---

## 2. Live Authority Used

Target artifacts used for this survey:
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`
- preprocess: `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`
- preprocess: `treatments/preprocess/fallen_prince_buys_joseon/profile_lock.json`
- preprocess: `treatments/preprocess/fallen_prince_buys_joseon/phase0_ready_snapshot.json`

Important live drift:
- duplicate BI path also exists: `bible/_quarantine/05_bi_fallen_prince_buys_joseon.json`
- earlier same-day docs referenced both BI names
- this survey treats the currently modified live path `05_fallen_prince_buys_joseon_bi.json` as authority because it is the active edited surface and now exposes the runtime genre/HUD choice directly

---

## 3. Pass 1 - Inventory

### 3.1 Runtime Guard Routing

Runtime guard selection is direct and exclusive.

Evidence:
- `modules/core/genre_guards/__init__.py:22-69`
- `main_a.py:1340-1344`

Observed behavior:
- `create_genre_guard()` creates one base guard from the selected genre
- `investment` routes to `InvestmentGuard`
- `alt_history` routes to `AltHistoryGuard`
- there is **no built-in hybrid dispatcher** for `alt_history_investment`

Implication:
- the system does not natively run both guards together just because the work is semantically hybrid
- one primary runtime guard must win

### 3.2 Alt-History Lane Surfaces

Evidence:
- `modules/core/genre_guards/alt_history_guard.py:13-24`
- `modules/core/genre_guards/alt_history_guard.py:236-257`
- `modules/core/genre_guards/alt_history_guard.py:263-337`
- `modules/core/genre_guards/alt_history_guard.py:492-500`
- `modules/core/constants.py:417-425`
- `modules/core/genre_hud_manager.py:653-665`
- `modules/core/stage0/preset_registry.py:158-176`
- `modules/core/genre_schema_builder.py:184-193`
- `docs/blockguide/alt_history_db_harness.md:5-7`
- `docs/blockguide/alt_history_db_harness.md:13-31`
- `docs/blockguide/alt_history_db_harness.md:214-229`

What the lane provides:
- first-class genre key `alt_history`
- dedicated guard class `AltHistoryGuard`
- dedicated HUD root `JoseonHUD`
- dedicated Stage 0 preset fields: `social_class`, `court_rank`, `position`, `faction`, `political_influence`, `public_trust`, `karma`
- dedicated schema keys oriented around 신분/품계/당파/민심
- dedicated material-prep contract: `alt_history_db_harness` requires `material_bank` lookup and AH-* source binding before Phase 0/TR/BI

What the guard actually enforces:
- forbidden modern/fantasy terms
- Joseon term set and hierarchy reminders
- state/action incompatibilities based on 신분, 품계, status
- justification patterns for 승진, 신분 초월, 기술 도입, 정치 명분

Current depth limit:
- same-day system survey classifies `alt_history_guard.py` as `Term-only`, with no registries and no blocking validator gate: `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md:125-133, 312-313`
- older structural audit says `alt_history_guard.run_deep_validation()` is effectively pass-through compared with investment helpers: `docs/2026-03-10/TF-QI-structural-quality-gaps-audit.md:169-176`
- live code matches that assessment: `modules/core/genre_guards/alt_history_guard.py:492-500`

### 3.3 Investment Lane Surfaces

Evidence:
- `modules/core/genre_guards/investment_guard.py:12-21`
- `modules/core/genre_guards/investment_guard.py:200-219`
- `modules/core/genre_guards/investment_guard.py:225-321`
- `modules/core/genre_guards/investment_guard.py:484-646`
- `modules/core/genre_guards/investment_guard.py:652-720`
- `modules/core/constants.py:417-425`
- `modules/core/genre_hud_manager.py:657-659`
- `modules/core/genre_schema_builder.py:157-165`
- `modules/core/stage0/preset_registry.py:321-327`
- `modules/domain/agents/blueprint_constraint_compiler.py:111-118`
- `modules/domain/agents/blueprint_constraint_compiler.py:178-190`
- `modules/domain/agents/blueprint_constraint_compiler.py:697-704`
- `modules/domain/agents/four_phase_arc_runtime.py:1191-1225`
- `modules/domain/agents/four_phase_arc_runtime.py:1534-1536`
- `modules/domain/agents/manuscript_validator.py:161-167`
- `docs/2026-03-10/production-readiness-assessment.md:81-92`
- `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md:125-133, 303-305`

What the lane provides:
- first-class genre key `investment`
- dedicated guard class `InvestmentGuard`
- dedicated HUD root `FinanceHUD`
- dedicated schema keys oriented around capital, total_assets, stocks, connections, market_insight
- runtime helpers for investment scale, return-rate realism, leverage-return formula, timeline event sanity
- investment-only capital continuity packet at Stage 3
- investment-only arithmetic advisory path in four-phase runtime
- investment-only manuscript financial-number checks

Current maturity:
- same-day system survey classifies `investment_guard.py` as `Complete`: `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md:125-133`
- earlier readiness doc says investment is the only non-wuxia lane with full real-pipeline verification: `docs/2026-03-10/production-readiness-assessment.md:81-92`

### 3.4 Target Work Artifact Truth

Evidence:
- `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json:3-6`
- `treatments/preprocess/fallen_prince_buys_joseon/profile_lock.json:2-4`
- `treatments/preprocess/fallen_prince_buys_joseon/phase0_ready_snapshot.json:1-8`
- `docs/2026-03-10/opus_망국황자는조선을산다.md:3-14, 64-79`
- `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json:42-43`
- `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json:5-12, 48`

Live target facts:
- preprocess locked `primary_profile = investment_market_profile`
- preprocess locked `secondary_profile = business_growth_profile`
- preprocess manual audit already passed
- core pitch is "대체역사 회귀 + 식민지 자산 인수/해운/보험/금융" hybrid
- TR block metadata uses `genre_ext.type = alt_history_investment`
- current live BI top-level `_genre = investment`
- current live BI uses `FinanceHUD`, not `JoseonHUD`

Implication:
- the work is semantically hybrid
- but the live artifact stack is already wired closer to `investment` runtime than to `alt_history` runtime

---

## 4. Pass 2 - Semantic Classification

### 4.1 What `alt_history` is best at for this work

`fallen_prince_buys_joseon` absolutely needs the alt-history contract in these areas:
- 1907-1938 timeline anchoring
- 황실/통감부/총독부/조선 내 제도적 개연성
- 신분/품계/당파/왕실 접근의 plausibility
- 역사 재료를 memory가 아니라 AH-* source로 묶는 source-manifest discipline

This is not optional flavor.
Without it, the work flattens into generic colonial-capital wish fulfillment.

### 4.2 What `alt_history` is weak at in the current system

The current built-in `AltHistoryGuard` does not provide the deep enforcement depth this work also needs.

Observed gaps:
- no financial registry lane
- no capital continuity packet
- no arithmetic advisory path
- no manuscript financial-number check
- no blocking validator specific to alt-history state truth
- deep validation is effectively base pass-through

So `alt_history` currently protects **surface authenticity and hierarchy language** better than it protects **the investment engine that actually drives this work**.

### 4.3 What `investment` is best at for this work

`fallen_prince_buys_joseon` is not a court-politics alt-history first. It is a 병목-독점 투자/기업물 with an alt-history wrapper.

The core engine is:
- 황실 자산 선점
- 해운/보험/은행/철도/광산 병목 장악
- 채권, 담보, 운임, 보험료, 경매, 지분, 결제선 통제
- capital continuity and leverage logic across long horizon blocks

The current system's `investment` lane is the one that actually has runtime protection for those failure modes.

### 4.4 Why pure `alt_history` primary would be risky right now

If the project is run as pure `alt_history` primary genre:
- current live BI/HUD wiring already mismatches that choice (`_genre = investment`, `FinanceHUD` live)
- Stage 3 capital continuity packet will not activate: `blueprint_constraint_compiler.py:697-704`
- four-phase investment arithmetic advisory will not activate: `four_phase_arc_runtime.py:1191-1225`
- manuscript financial-number check will not activate: `manuscript_validator.py:161-167`

That means the system would gain Joseon-flavor enforcement, but lose the stronger numeric/financial continuity protection that this work structurally depends on.

### 4.5 Why pure `investment` primary is still incomplete by itself

Pure `investment` primary also has a blind spot.

If nothing else is added:
- Joseon hierarchy, court rank, faction logic, and historical material sourcing become under-enforced
- the work can flatten into "generic investment fiction wearing hanbok"

So the correct answer is **not** "ignore alt-history".
The answer is that alt-history must survive as a **mandatory overlay contract**, but it should not be the primary runtime guard in the current system state.

---

## 5. Pass 3 - Verdict and Operating Consequence

### Verdict

**Current best-fit primary guard for `fallen_prince_buys_joseon` is `investment`, not `alt_history`.**

More precise form:
- **Primary runtime guard**: `investment`
- **Mandatory semantic overlay**: `alt_history`
- **Target label**: `alt_history_investment` hybrid, but with `investment` as the winning runtime lane under today's Geuldobi contracts

Reason in one line:
- the work's live preprocess/profile/BI/HUD stack already leans investment, and the current system's meaningful runtime protections for this work's failure modes are investment-only; alt-history remains essential, but mostly as material/authenticity contract rather than the main enforcement lane

---

## 6. Required Contract Stack For This Work

If this work continues under the current system, the safest contract stack is:

1. Set primary runtime genre to `investment`
   - Guard: `InvestmentGuard`
   - HUD root: `FinanceHUD`
   - stage/blueprint/manuscript numeric protection stays alive

2. Preserve hybrid semantic tag in artifacts
   - keep `genre_ext.type = alt_history_investment`
   - do not collapse the work label to generic modern investment fiction

3. Make `alt_history_db_harness` mandatory upstream
   - `docs/blockguide/alt_history_db_harness.md`
   - AH-* source lookup, source_manifest, and manual audit are required before planning/prose regeneration

4. Treat Joseon/historical authenticity as explicit overlay checks
   - social class / court rank / position / faction / public trust / historical-event binding
   - if needed, enforce through WorkGuard or survey-time manual audit until a true hybrid guard exists

5. Do not switch the live BI/HUD root to `JoseonHUD` unless the runtime is also upgraded to preserve investment continuity checks in hybrid mode

---

## 7. Decision Table

| Choice | Strength | Fatal Gap | Recommendation |
|---|---|---|---|
| `alt_history` primary only | 역사성, 신분/품계, 사극 문체, AH-* 재료 discipline | 자본 연속성/금융 검산/투자 수치 보호 약함 | 비추천 |
| `investment` primary only | 자본/포지션/수익률/연속성 보호 strongest | 역사성/조선 제도 개연성 under-enforced | 단독으로는 불완전 |
| `investment` primary + `alt_history` overlay | 현재 system maturity와 target hybrid성 둘 다 수용 | hybrid guard를 수동/문서로 보강해야 함 | **추천** |

---

## 8. Side-Effect Coverage

Survey-only scope. No live code patch or runtime run executed.

Applicability:
- file writes: survey doc only
- DB writes: not applicable
- JSONL/log/audit sink writes: not applicable
- console/UI runtime output: not applicable
- rollback/retry/cache/global-state mutation: not applicable
- config/env mutation: not applicable

Inspected instead:
- runtime guard routing
- HUD root routing
- Stage 0 preset/schema contracts
- Stage 3 constraint injection
- Stage 3.5/4 financial advisory hooks
- target artifact genre/HUD/profile truth

---

## 9. Final Recommendation

For `fallen_prince_buys_joseon`, use this operator sentence:

> `fallen_prince_buys_joseon`은 현재 글도비에서 `alt_history` 단독 장르가드보다 `investment` 장르가드를 주가드로 두고, `alt_history_db_harness`와 AH-* source_manifest, historical-event binding을 보조 계약으로 강제하는 쪽이 더 적합하다.

Confidence: **96%**

Why confidence is high:
- live artifacts, preprocess locks, guard code, HUD routing, and runtime-only investment protections all point in the same direction
- the only ambiguity is future design preference, not current system authority
