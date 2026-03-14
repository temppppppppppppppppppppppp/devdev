# Evidence Manifest Harness

Date: 2026-03-14
Status: active
Applies To: surveys, audits, execution SSOTs, and closure work with multiple supporting artifacts
Template: `docs/implementation/evidence-manifest-template.md`
Automation:
- `python scripts/generate_evidence_manifest.py`

## 1. Purpose
- Standardize how evidence artifacts are indexed for reuse.
- Reduce repeated rediscovery of the same inventories, logs, and checks.
- Keep execution docs concise when evidence volume grows.

## 2. When To Use
Use this harness when:
- there are three or more supporting evidence artifacts
- the same evidence will be reused across survey, execution, and closure docs
- the topic spans multiple directories, logs, or inventories

## 3. Manifest Contents
- artifact path
- artifact type
- acquisition method
- capture date
- freshness assessment
- intended reuse
- notes on limitations

## 4. Path Rule
- evidence manifests are canonical docs in `docs/YYYY-MM-DD/`
- they are not mirrored into `docs/temp/`
- preferred filename follows the execution-doc topic slug

## 5. Guardrails
- Do not treat the manifest as evidence itself; it is an index.
- Do not keep stale evidence unlabeled.
- Do not bury critical evidence in ad hoc terminal notes only.
