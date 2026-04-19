# 60_bi

Role:

- own stage-level contracts and work index for BI generation
- point to live BI files without moving them

Primary docs:

- `work-index/`
- `contracts/`

Current live path:

- `bible/NN_bi_{work_id}.json` for numbered live works
- legacy fallback: `bible/0_bi_{work_id}.json`

Current note:

- routed and harness paths currently guarantee canonical BI outputs
- fresh, newly touched, regenerated, or promotion-target pairs must show a donor decision before `BI` pair readiness may be claimed; see `../00_governance/donor-review-and-adoption-contract-v1.md`
