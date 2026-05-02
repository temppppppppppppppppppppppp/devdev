# 50_tr

Role:

- own stage-level contracts and work index for TR generation
- point to live TR files without moving them

Primary docs:

- `work-index/`
- `contracts/`

Current live path:

- `treatments/NN_*_tr_block_070_draft.json` for numbered live works
- legacy fallback: `treatments/*_tr_block_070_draft.json`

Current note:

- routed and harness paths currently guarantee canonical TR outputs
- fresh, newly touched, regenerated, or promotion-target pairs must show a donor decision before `TR` pair readiness may be claimed; see `../00_governance/donor-review-and-adoption-contract-v1.md`
- range-complete immediate-use claims must attach `genre_ext.downstream_episode_pacing_hint` per TR block; see `../00_governance/downstream-episode-pacing-hint-attachment-harness-v1.md`
- this hint is advisory material-side pacing guidance only and must not overwrite existing `webnovel_pacing_contract` or core TR block content
