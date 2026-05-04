# Style Wrapper Ingestion Bug Audit

Date: 2026-05-03
Repo: `C:\Users\PC\Desktop\글도비`
Remote: `temppppppppppppppppppppppp/devdev`

## Verdict

Confirmed, with an important boundary: the normal Stage0 style cache hit path is wrapper-aware, but downstream style consumers are not. If a rich ready-pack/cache style guide shaped as `{ "_cache_meta": ..., "style_guide": { ... } }` is stored as a project anchor or used as a project-local style file, Stage4 and StyleGuard can silently degrade to default style values.

## Evidence

- `config/style_references/investment/style_guide.json` is a wrapped rich style cache: root keys are `_cache_meta` and `style_guide`.
- `modules/core/stage0/style_extractor.py:408` unwraps this shape in `_load_cache_payload()`, so cache reuse inside Stage0 is safe.
- `modules/core/stage0/style_extractor.py:79` defines `StyleGuide.from_dict()` as a flat dataclass-key filter. It does not unwrap nested `style_guide`.
- `main_a.py:1901` passes the loaded `style_guide` anchor directly into `StyleGuide.from_dict()`.
- `modules/core/stage4_orchestrator.py:2676` also passes the loaded style anchor directly into `StyleGuide.from_dict(saved_style)`. Because default construction succeeds, fallback rendering is not triggered.
- `modules/core/project_support.py:95` returns the raw anchor dict, and `modules/core/project_support.py:236` reads root-level style keys for summaries.

## Repro Snapshot

Using the repo's own `StyleGuide.from_dict()` against the wrapped investment style cache:

```text
root_keys=_cache_meta,style_guide
wrapped_tone=중립
wrapped_anti_ai=0
wrapped_exemplary=0
wrapped_excerpt_len=0
unwrapped_tone=<rich source tone present>
unwrapped_anti_ai=10
unwrapped_exemplary=15
unwrapped_excerpt_len=4585
```

No current `projects/**/project_data.db` style anchor in this local checkout was found with a wrapped payload, and project `stage0_output/style_guide.json` files searched did not show `_cache_meta`. So this is best classified as a latent ingestion/interop bug rather than proof that an active local project is already poisoned.

## Impact

The symptom matches the Firefly-side bug class: rich few-shot fields exist, but the writer can receive only generic/default style guidance. The most damaging losses are `reference_excerpt`, `exemplary_passages`, `anti_ai_patterns`, `dialogue_narration_pattern`, and `sentence_rhythm`.

## Suggested Fix

1. Add a shared style payload normalizer, for example `unwrap_style_guide_payload(payload)`, that accepts both flat and cache-wrapped shapes.
2. Use it in `StyleGuide.from_dict()` or at every ingress point: `load_style_guide_anchor()`, `load_style_guide_file()`, `main_a._resolve_project_guard()`, and `Stage4Orchestrator._resolve_session_style_guide()`.
3. Make `_render_style_guide_payload()` include rich fields when falling back from dict payloads.
4. Add tests covering wrapped style payloads for Stage4 prompt rendering, StyleGuard wrapping, and project-support summaries.

## 3-Pass Review

Pass 1: The bug is not in Stage0 cache hit itself because `_load_cache_payload()` unwraps correctly.

Pass 2: The downstream bug is real because `StyleGuide.from_dict()` defaults successfully on the wrapped root, which makes failure silent.

Pass 3: The issue should be filed as a latent ingestion/interoperability bug, not as evidence of current active-project corruption.
