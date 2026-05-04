# GSD Quick: style wrapper ingestion audit

Date: 2026-05-03
Track: system order

## Goal

Check whether the Firefly-style style cloning bug exists in the local Geuldobi workspace, especially when a rich `style_guide.json` is wrapped as `{ "_cache_meta": ..., "style_guide": ... }`.

## Scope

- Read-only investigation of style cache, Stage0, Stage4, StyleGuard, and project support loaders.
- If confirmed, document the issue and open a GitHub issue against the Geuldobi repository.
- Do not patch runtime code in this pass.

## Result

Confirmed as a latent ingestion bug: the Stage0 cache path unwraps the wrapper correctly, but Stage4/StyleGuard/project-support consumers accept raw anchor/file payloads and can silently default when a wrapped payload reaches those surfaces.
