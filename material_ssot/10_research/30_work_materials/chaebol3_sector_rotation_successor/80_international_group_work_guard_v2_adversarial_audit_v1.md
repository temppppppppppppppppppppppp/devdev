# International-Group Work Guard v2 Adversarial Audit v1

Date: 2026-05-17
Status: audit complete
Work ID: `chaebol3_sector_rotation_successor`
Target: `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml`

## 0. Verdict

`PASS_AFTER_EXPOSURE_FILTER_PATCH`

The v2 guard correctly supersedes v1 for the International Group baseline.

It captures the EP001 micro-canary lesson:

- LC buys time, not victory;
- folder and stamp route must visibly move;
- telex access is the first access reward;
- bank-side behavior cost must be visible;
- grandfather recognition must remain conditional;
- later sectors must rotate room, actor, proof object, human cost, and access token.

## 1. Initial Adversarial Finding

Independent audit first returned:

`NEEDS_PATCH`

Reason:

- direction and material doctrine were correct;
- but the guard still carried operator/harness language near writer-adjacent fields:
  - `EP001/B1-B2`;
  - `EP002`;
  - `EP003`;
  - `Phase0`;
  - `TR 1-10`;
  - `TR70`;
  - `BI`;
  - `first-arc scene-ready packet`;
- if passed raw into Firefly S4, those labels could leak as AI-slop or production-meta prose;
- the guard also needed an explicit ban on `immediate-use/range-complete` promotion.

## 2. Patch Applied

Added `work_identity.s4_handoff_filter` to v2 guard.

Operator-only:

- `Phase0`;
- `TR 1-10`;
- `TR70`;
- `BI`;
- `range-complete`;
- `immediate-use`;
- `B1-B2/EP labels`;
- production status labels;
- validator/audit wording.

S4-expose:

- 도장용 표지가 뒤로 밀린다;
- 문도윤의 짧은 메모가 은행 회의철 첫 장 뒤로 들어간다;
- 인주 뚜껑이 닫히고 도장 순서가 멈춘다;
- 복도에 서 있던 문도윤에게 텔렉스실 의자가 배정된다;
- 산업은행 김태완 차장이 멈춘 결재란 앞에서 LC 번호를 두드리며 누가 썼는지 묻는다;
- 72시간 보류는 칭찬이 아니라 실패 조건이 붙은 확인 절차다;
- 부산 급여, 선적 마감, 외국 구매자 회신이 다음 장면의 외부 증거다.

Added explicit rule:

- this guard does not authorize final Phase0, immediate-use, range-complete, production BI, or production TR70.

## 3. Validation

Command:

```powershell
python -X utf8 scripts/run_work_guard_v1.py --path material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml
```

Result:

```text
WG-V1 PASS
tracking_slots=4
mandatory_scene_engines=3
forbidden_flattenings=8
protagonist_weapon=3
admiration_axes=5
```

## 4. Remaining Watch

The guard is suitable for material-side operation, not raw S4 input.

Before Firefly S4 writing, create a compact writer seed from `s4_handoff_filter.s4_expose` plus the Phase0 scene packet. Do not feed the full guard/canon/audit stack to the writer.

## 5. Next Recommendation

Proceed to International Group Phase0 restart.

Phase0 must read:

- `70_international_group_historical_opportunity_atlas_v1.md`;
- `71_international_group_sector_gate_matrix_v1.md`;
- `72_international_group_phase0_research_checklist_arcs01_02_v1.md`;
- `73_international_group_opening_phase0_seed_v1.md`;
- `75_international_group_ep001_micro_canary_packet_v1.md`;
- `78_international_group_ep001_micro_canary_sample_v1.md`;
- `79_international_group_ep001_micro_canary_director_audit_v1.md`;
- `chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml`.

Do not generate production TR70 or production BI.
