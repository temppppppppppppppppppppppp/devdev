# Cover AI Pipeline

High-quality cover generation lab for webnovel-style key visuals.

This project isolates the cover workflow from the main narrative runtime and
focuses on repeatable image production:

1. Generate multiple title-integrated candidates with Gemini image models.
2. Judge each candidate against:
   - exact Korean title fidelity
   - style match to a reference cover
   - character preservation
   - commercial-cover readability
3. Rank outputs and keep all evidence.

## Structure

- `jobs/`
  - job configs with input paths, title, model names, and prompt variants
- `scripts/`
  - orchestration and judging logic
- `outputs/`
  - generated candidates, judge JSON, and ranked summaries
- `docs/`
  - notes for future iteration

## Current constraint

- Workspace currently has Gemini Developer API access.
- Vertex / Imagen is not configured in env right now.
- Therefore the current highest-quality path is:
  - `gemini-3-pro-image-preview` for generation
  - `gemini-2.5-pro` for judging

## Run

```powershell
python visual_lab/cover_pipeline/scripts/run_cover_pipeline.py ^
  --job visual_lab/cover_pipeline/jobs/isekai_helper.json
```
