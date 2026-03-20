# Illustration Pipeline

Text-free illustration generation pipeline.

Goal:

- use a strong reference cover for energy / composition
- reimagine it into a new illustration direction
- generate multiple candidates
- judge them automatically for style, beauty, polish, and unwanted text

Current experiment:

- `d.png` -> premium romance-fantasy (`로판`) illustration

Run:

```powershell
python visual_lab/illustration_pipeline/scripts/run_illustration_pipeline.py ^
  --job visual_lab/illustration_pipeline/jobs/d_ropan.json
```
