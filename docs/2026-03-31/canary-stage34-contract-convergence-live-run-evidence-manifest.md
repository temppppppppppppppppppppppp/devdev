Date: 2026-03-31
Status: live-run-evidence (run-active)
Document Type: live-run evidence manifest
Mode: ROL live-merge
Run Status: ACTIVE (EP13 Round 1+ director review)
Session ID: 20260331_112930
Evidence Capture Cutoff: 2026-03-31 13:16:18 UTC

# Canary Stage34 Contract-Convergence Live-Run Evidence Manifest

## 1. Run Timeline Summary

```
11:29:31  Session boot
11:48:11  Stage 3 EP10 blueprint PASS (score 73, action_focused, A5)
12:00:03  Stage 3 EP11 blueprint PASS (score 95, action_focused, A4)
12:05:51  Stage 3 EP12 blueprint PASS (score 76, emotion_focused, A1)
12:11:05  Stage 3 EP13 blueprint PASS (score 92, action_focused, A2)
12:14:54  Stage 3 EP14 blueprint PASS (score 95, emotion_focused, A1)
12:15:08  Stage 4 EP10 preflight
12:22:02  Stage 4 EP10 PASS (score 96, candidate A, 1 round)
12:24:06  Stage 4 EP11 R0 start
12:29:39  Stage 4 EP11 R0 REJECT (score 95, post_select_conflict 타임라인)
12:30:47  Stage 4 EP11 V75-D blueprint inplace patch (change_ratio 0.1039)
12:36:51  Stage 4 EP11 R1 REJECT (score 95, constraint_violation + plateau)
12:42:36  Stage 4 EP11 R2 start
12:45:24  Stage 4 EP11 R2 REJECT (score 96, post_select_conflict timeline collision)
12:49:04  Stage 4 EP11 R3 start
12:52:11  Stage 4 EP11 R3 PASS (score 92, candidate A, 4 rounds total)
12:52:28  Stage 4 EP12 R0 start
12:58:31  Stage 4 EP12 R0 REJECT (score 44, CRITICAL 자본금정합 + firewall)
12:59:26  Stage 4 EP12 V75-D blueprint inplace patch (change_ratio 0.1796)
13:02:54  Stage 4 EP12 R1 start
13:07:15  Stage 4 EP12 R1 PASS_WITH_FIX (score 90, candidate B, action items)
13:07:31  Stage 4 EP13 R0 start
13:13:24  Stage 4 EP13 R0 REJECT (score 95, strong_advisory_escalation NPC drift)
13:16:18  Stage 4 EP13 R1 director review in progress (evidence cutoff)
```

## 2. Log File Statistics

| Log File | Entries | Last Update |
|----------|---------|-------------|
| decisions.jsonl | 13 | active |
| llm_io.jsonl | 156 | active |
| state_changes.jsonl | 6 | EP12 final |
| ui_events.jsonl | 642+ | seq 666+ active |
| episode_production.jsonl | 16 | active |
| quality_metrics.jsonl | ~20 | active |
| runtime_audit.jsonl | 10 | active |

## 3. Stage 3 Evidence

### Blueprint Production (5/5 PASS, 100% success rate)

| EP | Attempt | Strategy | Score | Duration | Cost | Quality Risk |
|----|---------|----------|-------|----------|------|-------------|
| 10 | A5 | action_focused | 73 | 1034s | $0.532 | TRUE |
| 11 | A4 | action_focused | 95 | 712s | $0.426 | TRUE |
| 12 | A1 | emotion_focused | 76 | 348s | $0.218 | TRUE |
| 13 | A2 | action_focused | 92 | 314s | $0.211 | TRUE |
| 14 | A1 | emotion_focused | 95 | 229s | $0.171 | FALSE |

- Total Stage 3 cost: $1.558
- Total Stage 3 duration: 2,637s (44min)
- Model: Gemini 3.1 Pro Preview (all)
- revision_required: TRUE (all)

### Blueprint Coverage (quality_metrics 기준)

| EP | Expected | Reflected | Coverage |
|----|----------|-----------|----------|
| 10 | 5 | 4 | 80% |
| 11 | 4 | 1 | 25% |
| 12 | 4 | 2 | 50% |

- EP11 25% coverage — FLAG: 낮은 coverage가 Stage 4 4-round retry의 원인 가능성

### Blueprint Artifacts (Disk)

```
stage3/ep_0010/attempt_05/final_blueprint__action_focused.json
stage3/ep_0011/attempt_04/final_blueprint__action_focused.json
stage3/ep_0012/attempt_01/final_blueprint__emotion_focused.json
stage3/ep_0013/attempt_02/final_blueprint__action_focused.json
stage3/ep_0014/attempt_01/final_blueprint__emotion_focused.json
```

## 4. Stage 4 Evidence

### Episode 10 — Clean Pass (1 Round)

- Duration: 509,061ms (8.5min)
- Calls: 17 | Tokens: 425,590 | Cost: $0.669
- Gate: director_primary_pass
- Score: 96
- Selected: A (긴장감 + 반전 강조)
- AI Slop: 3.0 (순식간에x2, 시선을 돌렸다x1)
- CED: 0.0
- Draft saved: `drafts/ep_0010.txt` (15K, 12:22)

### Episode 11 — 4-Round Retry (Timeline Conflicts)

**Round 0 (REJECT)**
- Score: 95
- Pathology: post_select_conflict (타임라인)
- Issue: '며칠 전' → '오늘 오전' timing error; 박성호 위치 불일치 (대표실→딜링룸)
- Gate: director_reject

**V75-D Blueprint Patch**
- Change ratio: 0.1039
- Artifact: `stage4/ep_0011/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json`

**Round 1 (REJECT)**
- Score: 95 (plateau)
- Pathology: constraint_violation + plateau_detected
- Gate: strong_advisory_escalation_non_local_fix
- Note: "점수 plateau — 동일 수정 루프 반복 중"

**Round 2 (REJECT)**
- Score: 96
- Pathology: post_select_conflict (timeline collision 2006년 2월→4월)
- Issue: EP10-11 연속 장면인데 연월 불일치

**Round 3 (PASS)**
- Score: 92
- Gate: director_primary_pass
- Selected: A (balanced tension)
- Draft saved: `drafts/ep_0011.txt` (16K, 12:50)
- Total cost: ~$1.49+

**Convergence Pattern**: V75-D patch → plateau 감지 → 추가 시도 → 수렴. 에스컬레이션 사다리 작동 확인.

### Episode 12 — Capital Consistency Critical (2 Rounds)

**Round 0 (REJECT)**
- Score: 44
- Pathology: post_select_conflict + CRITICAL 자본금정합 + continuity_firewall
- Issue: WTI 포지션에 자본 묶인 상태에서 15억 원 금 선물 매수 모순
- Gate: continuity_firewall
- Firewall triggered: YES

**V75-D Blueprint Patch**
- Change ratio: 0.1796
- Artifact: `stage4/ep_0012/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json`

**Round 1 (PASS_WITH_FIX)**
- Score: 90 (initial 96, fix 후 90)
- Selected: B (긴장감 + 반전 강조)
- Repair scope: inplace
- Action items: "씬 5 마지막 문단 주변에 시장 변동성과 주인공 평온함 대비 묘사 추가"
- AI Slop: 4.0 (고개를 끄덕였다, 순식간에, 시선을 돌렸다, 침을 삼켰다)
- Draft saved: `drafts/ep_0012.txt` (13K, 13:05)

**Convergence Pattern**: firewall → V75-D patch → PASS_WITH_FIX. fail-closed → patch → 수렴 확인.

### Episode 13 — NPC Drift Escalation (In Progress)

**Round 0 (REJECT)**
- Score: 95
- Pathology: quality_issue + missing_patch_targets
- Gate: strong_advisory_escalation_non_local_fix
- Issues:
  - Candidate B: NPC '투기 세력' relation_to_protag 왜곡 (기대='오해 대상' → 원고='방패막이')
  - Candidate C: 분량 미달 + 금 현물→금 선물 설정 왜곡
  - Candidate A: 검은색 만년필 중복 획득 (V66.1), 연속성 위반 (장소 변화)
- fix_pack status: missing_patch_targets → REJECT

**Round 1 (IN PROGRESS as of 13:16:18)**
- ui_events seq 647-666: Director review active
- 2 candidates under review
- Advisory chain: 9 parallel validators running
- Candidate A: 5 warnings (5487 chars)
- Candidate B: 4 warnings (4697 chars)

## 5. Persistence Evidence

### Saved Drafts (Disk)

| EP | Size | Timestamp | Source |
|----|------|-----------|--------|
| 01-09 | 9.9K-16K | 2026-03-30 | Prior runs |
| 10 | 15K | 2026-03-31 12:22 | Canary run |
| 11 | 16K | 2026-03-31 12:50 | Canary run |
| 12 | 13K | 2026-03-31 13:05 | Canary run |

### World State Progression (state_changes.jsonl)

| Change # | EP | Capital | Key State |
|----------|----|---------|-----------|
| ... | 10 | 23억 400만 원 | WTI 포지션 유지 |
| ... | 12 | 33억 원 | 금 현물 매집 채널 확보, 레바논 사태 대비 |

- 자본 증가: 23억 400만 → 33억 원 (EP10→EP12)
- Protagonist state: 금 현물 매집 채널 확보
- Injuries: 통증 해소됨
- Mood: 냉철함 (HUD: 평온)

### DB Status

- project_data.db: 17.4MB, WAL 4.2MB active
- Last modification: 2026-03-31 13:11

## 6. Retry Pathology Summary

| # | EP | Round | Pathology | Trigger | Score | Resolution |
|---|-----|-------|-----------|---------|-------|-----------|
| 1 | 11 | R0 | post_select_conflict (타임라인) | director_reject | 95 | Retry |
| 2 | 11 | R1 | constraint_violation + plateau | strong_advisory | 95 | Retry |
| 3 | 11 | R2 | post_select_conflict (timeline) | post_select_conflict | 96 | PASS R3 |
| 4 | 12 | R0 | capital CRITICAL + firewall | continuity_firewall | 44 | V75-D + Retry |
| 5 | 13 | R0 | NPC drift + missing_patch_targets | strong_advisory | 95 | Escalated REJECT |
| 6 | 13 | R1 | (in progress) | - | - | Pending |

### Pattern Observations

1. **Post-select conflict 반복** (EP11): 3 rounds 동안 타임라인 관련 충돌. 각 round에서 다른 측면의 타임라인 오류 발견 — 수렴 경로가 존재하나 느림
2. **Capital consistency firewall** (EP12): 강력한 fail-closed. score 44로 가장 낮은 점수. V75-D patch → 2nd round PASS
3. **NPC drift escalation** (EP13): Director가 PASS 판정했으나 downstream advisory가 override. fix contract 미완성 (missing_patch_targets)
4. **V75-D blueprint patch 3회 적용** (EP11 1회 + EP12 1회 + EP13 pending): blueprint-level 수정이 빈번 — Stage 3 coverage 개선 여지

## 7. Quality Signal Trends

### AI Slop Scores

| EP | Score | Patterns |
|----|-------|----------|
| 10 | 3.0 | 순식간에x2, 시선을 돌렸다x1 |
| 11 | 2.0 | 고개를 끄덕였다x1, 한순간x1 |
| 12 | 4.0 | 고개를 끄덕였다x1, 순식간에x1, 시선을 돌렸다x1, 침을 삼켰다x1 |

### Dialogue Ratio

| EP | Ratio | Assessment |
|----|-------|-----------|
| 12 | 0.8 | 대화 과다 |
| 13-A | 0.4 | 묘사 과다 |
| 13-B | 0.5 | 균형 (but 분량 부족) |

### Director Score Trend

| EP | Final Score | Rounds | Trend |
|----|------------|--------|-------|
| 10 | 96 | 1 | Baseline |
| 11 | 92 | 4 | -4 (retry 소모) |
| 12 | 90 | 2 | -2 (fix 적용) |
| 13 | 95 (rejected) | 1+ | Escalated |

## 8. Artifact Completeness Check

### Stage 3 Artifacts
- [x] EP10 final_blueprint (A5)
- [x] EP11 final_blueprint (A4)
- [x] EP12 final_blueprint (A1)
- [x] EP13 final_blueprint (A2)
- [x] EP14 final_blueprint (A1)

### Stage 4 Artifacts
- [x] EP10 final_manuscript (A, attempt_01)
- [x] EP11 final_manuscript (A, attempt_04) + rejected_best x3 + patched_blueprint
- [x] EP12 selected_before_fix (B, attempt_02) + patched_after_fix + rejected_best x2 + patched_blueprint
- [ ] EP13 rejected_best (A, attempt_01) — PENDING further rounds
- [ ] EP14 — NOT STARTED

### Draft Files
- [x] EP10 draft
- [x] EP11 draft
- [x] EP12 draft
- [ ] EP13 draft — PENDING
- [ ] EP14 draft — PENDING

## 9. Runtime Audit Summary Snapshot

- Tag: stage3_complete
- Proof Digest Status: WARN
- Stage 3: 14 attempts considered, 5 complete finals
- Stage 4: 25 attempts considered, 0 complete finals (run active)
- Coverage Issues: final_sink_missing (18 S3, 50 S4), artifact_missing_files (9 S3, 10 S4)

## 10. Pending Items for Post-Run Merge

- [ ] EP13 final verdict and artifact
- [ ] EP14 Stage 4 production (if reached)
- [ ] Final state_changes.jsonl entries for EP13+
- [ ] Final WorldState / FactLedger DB anchor snapshots
- [ ] director_selections DB table vs artifact cross-check
- [ ] stage_attempts DB table completeness
- [ ] runtime_audit final digest
- [ ] Total session cost and token usage
- [ ] TF-C10 sequential mode occurrence check
- [ ] Blueprint coverage vs retry round count correlation analysis
