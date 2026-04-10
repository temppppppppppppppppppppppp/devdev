# TR Block Bundle Density Benchmark Design

Date: 2026-04-10
Status: active design
Scope: material-side `TR block` density law for discard vs repair decisions

---

## 1. Why This Exists

Current pair triage already distinguishes:

- `benchmark alias`
- `opening pacing triage`
- `naming drift`

But one missing law remains:

- when is a `TR block` too thin to honestly carry `2~6` downstream episodes?

That law cannot be guessed from vibes alone.

We already say:

- one meaningful `TR block` should unfold into roughly `2~6` downstream episodes

But we do not yet have an empirical lower bound that says:

- `below this density band = likely YELLOW`
- `below this floor = RED archive candidate`

---

## 2. Operator Position

### 2.1 The important distinction

`same-block cider` and `2~6 episode bundle density` are not the same thing.

- a block can have cider and still be thin
- a block can have visible movement and still fail macro pacing
- a pair can fail opening pacing even when individual blocks are not locally empty

So the law must stay split:

- `block 1 no cider` -> existing `YELLOW ceiling`
- `opening macro battlefield overstay` -> current pacing triage
- `2~6 bundle density failure` -> new density law

### 2.2 Current recommendation

Do **not** make `2~6 bundle density failure = automatic RED` yet.

First close a bounded empirical pack.

Until then:

- treat density weakness as `YELLOW/RED investigation trigger`
- not as a standalone irreversible archive verdict

---

## 3. What We Need To Measure

The baseline is not just `char count`.

We need three layers.

### 3.1 Downstream episode window density

From real serialized episodes, measure windows of:

- `2 episodes`
- `3 episodes`
- `4 episodes`
- `5 episodes`
- `6 episodes`

Core axes:

- `window_char_count`
- `window_paragraph_count`
- `window_sentence_count`
- `domain_anchor_per_1000_chars`
- `quote_paragraph_ratio`

This gives a real lower bound for what `2~6 episodes` actually look like on the page.

### 3.2 TR-side bundle proxy density

From `TR` blocks, do not ask “is it long?”

Ask:

- does this block contain enough turns to split into multiple downstream beats?
- does it carry proof + reevaluation + token + next-gate logic?
- does it contain enough concrete domain anchors to survive scene-splitting?
- does it have carry-over fuel, not just same-block receipt?

Existing substrate already helps:

- `bundle_size`
- `thin_blocks`
- `callback_ratio`
- `opening reader-earning signal`

But these are not yet a full `2~6 bundle density` law.

### 3.3 Conversion law

The final law is not “TR block length >= X”.

The final law is:

- can this block plausibly be decomposed into `2~6` episodes without inventing filler?

That requires both:

- downstream empirical lower bounds
- TR-side proxy structure

---

## 4. Bounded Corpus Strategy

### 4.1 Provisional local baseline

Start with corpus bundles already inside repo.

Strong references:

- `투자물_금수저 투자백서`
- `투자물_금수저생활백서`

Low-bound references:

- `재벌물_독식하는 재벌 3세`
- `재벌물_재벌 3세는 총수가 되고 싶다`

Cross-lane check:

- `medical_magical_surgeon_sample_corpus`

This is enough to produce a first-pass lower band without waiting on NAS.

### 4.2 NAS expansion

Then extend with bounded NAS titles:

- `대한민국 절대 재벌`
- `신흥재벌`
- `재벌생활기록부`
- `김 대리는 인생이 너무 가볍다`
- `매지컬 써전(강산)`

Why these:

- they cover 정통 재벌 / 성장형 재벌 / 운영형 재벌 / 생활 감각형 오피스 / cross-lane medical

### 4.3 Pack location

- pack README:
  - `material_ssot/10_research/50_corpus_curated/reference_samples/tr_block_bundle_density_benchmark_pack/README.md`
- pack manifest:
  - `material_ssot/10_research/50_corpus_curated/reference_samples/tr_block_bundle_density_benchmark_pack/manifest.json`

---

## 5. Current Tooling

New snapshot builder:

- `scripts/bundle_density_snapshot.py`

It summarizes bounded episode corpora by:

- episode-level quantiles
- rolling `2~6` episode windows
- domain anchor density
- quote/dialogue-lean ratio

Current provisional artifact:

- `docs/2026-04-10/tr-block-bundle-density-provisional-baseline.json`

This is not the final law.
It is the first empirical floor.

### 5.1 First provisional local read

From the local bounded snapshot:

- `금수저 투자백서` `4-episode window char_count p50` ≈ `26.3k`
- `금수저생활백서` `4-episode window char_count p50` ≈ `24.5k`
- `독식하는 재벌 3세` `4-episode window char_count p50` ≈ `22.3k`
- `재벌 3세는 총수가 되고 싶다` `4-episode window char_count p50` ≈ `24.8k`
- `medical_magical_surgeon_sample_corpus` `4-episode window char_count p50` ≈ `20.0k`

What this means right now:

- strong business windows roughly sit in the mid `24k~26k` band
- local low-bound business windows are still around `22k+`
- cross-lane medical windows can sit lower

So today we can say:

- `window_char_count` alone should **not** become a hard RED law yet
- but a `4-episode equivalent` that keeps collapsing under roughly the low `20k` band is a serious investigation trigger
- the final cut still needs NAS expansion plus non-char axes

---

## 6. Proposed Grade Law

### 6.1 Before NAS wave closes

Do this:

- `bundle density weak` -> `YELLOW investigation`
- `bundle density weak + opening pacing failure + low carry-over` -> `RED candidate, manual confirmation required`

Do not do this yet:

- `bundle density weak` -> immediate automatic `RED`

### 6.2 After bounded NAS pack closes

Then we can promote:

- `RED`:
  - TR block proxy sits below weak-reference `P25` on multiple core axes
  - and receipt/carry-over conversion is also weak
  - and the block would need filler to reach `2~6` episodes
- `YELLOW`:
  - below strong median but above weak-reference lower bound
  - or only one core axis is weak
  - or evidence is mixed
- `GREEN`:
  - comfortably above lower bound and structurally decomposable

Short version:

`2~6 bundle density failure` can become a RED law, but only after the empirical weak-reference floor is frozen.

---

## 7. Immediate Next Step

1. refresh the provisional local baseline snapshot
2. read the numbers against current `YELLOW` queue
3. collect the bounded NAS expansion set
4. then decide whether density becomes a standalone `RED` cut

That order matters.

If we skip step `1~3`, we risk calling “simple” or “lean” writing `RED` when it is merely stylistically light.
