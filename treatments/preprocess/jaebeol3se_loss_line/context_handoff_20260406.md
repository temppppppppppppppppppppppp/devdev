# Context Handoff — jaebeol3se_loss_line

Date: 2026-04-06
Status: TR sequential production in progress
Last completed unit: Block 12 (감리 PASS)
Next unit: Block 13 (공동 서명) — 사전 선언 완료, JSON 미생성

## 1. Work Identity

- work_id: `jaebeol3se_loss_line`
- title: `재벌 3세는 손실선을 먼저 읽는다`
- family: `blockguide`
- profiles: `investment_market_profile` + `office_power_profile`

## 2. Canonical Artifact Paths

| Artifact | Path | Status |
|----------|------|--------|
| Canon | `material_ssot/20_pitch/canon/jaebeol3se_loss_line.md` | frozen |
| Synthesis | `material_ssot/20_pitch/synthesis/investment_dokshik_jaebeol3se_working_synthesis.md` | canon locked |
| Work Guard | `work_guards/10_jaebeol3se_loss_line.yaml` | WG-V1 PASS, WG-V2 PASS, WG-V3 PASS, frozen |
| Work Guard (genre) | `work_guards/investment/jaebeol3se_loss_line.yaml` | copy |
| Phase0 | `treatments/phase0/jaebeol3se_loss_line_phase0_design.json` | canonical |
| Phase0 (preprocess) | `treatments/preprocess/jaebeol3se_loss_line/02_phase0_work/phase0_candidate.json` | source |
| TR | `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json` | Block 1~12 상세, 13~70 미생성 |
| TR (preprocess) | `treatments/preprocess/jaebeol3se_loss_line/04_tr_final/jaebeol3se_loss_line_tr_block_070_draft.json` | Block 1~5 only (outdated) |
| BI | `bible/10_bi_jaebeol3se_loss_line.json` | ���� (sync_manifest.tr_block_count=5, 업데이트 필요) |
| Stage 0 4-pack | `treatments/preprocess/jaebeol3se_loss_line/{source_manifest,profile_lock,material_bundle_summary,phase0_ready_snapshot}.json` | all present, manual_audit_pass=true |

## 3. Harness Compliance

| 절차 | 상태 |
|------|------|
| Stage 0 preprocess 4-pack | 완료 |
| Phase 0 design | 완료 (5 ARCs, 70 blocks) |
| WG-V1 shape validator | PASS |
| WG-V2 freeze checklist | PASS (7/7 yes) |
| WG-V3 drift audit | PASS |
| Work guard freeze | 완료 |
| Block 001~010 자체 감리 | PASS |
| Block 011 생산 + 감리 | PASS |
| Block 012 생산 + 감리 | PASS |
| Block 013 | 사전 선언 완료, JSON 미생성 |

## 4. Production Progress

### Completed Blocks (1~12)

| Block | Title | Emotional Beat | Tension | Key Reward |
|-------|-------|---------------|---------|------------|
| 1 | 리스크 표 만드는 도련님 | humiliation | 3 | 없음 (관찰) |
| 2 | 세 개의 숫자 | tension_build | 5 | 한 장 표 (비공개) |
| 3 | 관리 범위입니다 | tension_peak | 7 | 없음 (대기) |
| 4 | 18일 | first_saida | 9 | 평가 수정: 손실선을 먼저 그린 사람 |
| 5 | 도련님이 감히 | counter_pressure | 7 | 없음 (검증 받는 중) |
| 6 | 회장의 메모 | recognition_receipt | 6 | 직보 주간 메모 라인 개방 |
| 7 | 손실선 카운트다운 | preparation | 6 | 결재선에 안건 등재 |
| 8 | 조용한 준비 | quiet_preparation | 3 | 없음 (외부 레인 밑그림) |
| 9 | 마진이 꺾이다 | vindication | 8 | 적중 증명, 평가 승격 |
| 10 | 선��입의 대가 | tempered_victory | 5 | 순기여 플러스 공식 인정 |
| 11 | 배석권 | status_upgrade | 4 | 리스크 회의 정식 배석권 |
| 12 | 대시보드 | access_granted | 4 | 보험·클레임 대시보드 열람권 |

### Remaining ARC-01 Blocks (13~15)

| Block | Phase0 Title | Phase0 Function |
|-------|-------------|-----------------|
| 13 | 공동 서명 | 긴급 헤지 실행 공동 서명권 부여. 결재선에 이름 등재. |
| 14 | 파일럿 50억 | 전략금융실 산하 파일럿 운용금 50억 배정. 자본��� 권한 뒤 하위 증명. |
| 15 | 다음 손실선 | 배석자로서 새 trigger set 감지. ARC-02 입장권. |

### Block 13 사전 선언 (작성 완료, JSON 미생성)

- emotional_beat: access_granted → authority_stamp
- deal_type: 열람권 → 서명권
- opponent: 임재훈 → CFO 보좌 라인
- location: 업무 공간 → CFO 집무실
- duration: 반나절 → 2시간
- capital: 0 → 0

## 5. Core Doctrine (작업 재개 시 반드시 확인)

1. **보상 순서**: 평가 수정 → 권한 → 자본. 절대 뒤집지 않음.
2. **Dual-lane separation**: 내부 데이터는 손실 방어/권한 전용, 외부 포지션은 공개 신호 전용. 출처를 섞지 않음.
3. **Insider-trading 금지**: 내부 데이터를 근거로 외부 포지션을 잡는 구조 절대 불가.
4. **사촌 형 도현석**: 무능 캐리커처 금지. 숫자를 따로 봤기 때문에 연결을 못 본 사��.
5. **Asset-first 금지**: 자산 수치가 보상�� 얼굴이 되면 안 됨.

## 6. NPC State at Block 12

| NPC | Current State |
|-----|---------------|
| 도현석 (사촌 형) | 긴장 (옆자리에 도진우가 앉음). 아직 적대 행동 없음. |
| ��태호 (CFO) | 도구 부여 (대시보드 접근권 발급). 계산으로 도진우를 올림. |
| 임재훈 (보험 담당 임원) | 경계 완화 (대시보드 상세 탭까지 열어줌). |
| 도경일 (회장) | 신뢰 강화 (직보 메모를 다시 꺼내 봄). |
| 박동수 (구매실장) | 처음으로 도진우에게 의견을 물어옴. |

## 7. Open Foreshadows

| Planted | Content | Expected Payoff |
|---------|---------|-----------------|
| Block 8 | 외부 레인 밑그림 | Block 14+ 파일럿 운용금 후 집행 |
| Block 10 | 분��막 단가 역전 교훈 | ARC-02 포지션 정밀화 |
| Block 11 | 박동수 복도 의견 요청 | ARC-02 구매실장 먼저 전화 |
| Block 11 | 배석 회의에서 보험 갱신 일정 언급 | ARC-02 보험 재협상 테이블 |
| Block 12 | 다음 분기 갱신 만기 건 | ARC-02 핵심 소재 |
| Block 12 | 임재훈 경계 완화 | ARC-02 먼저 자료 가져오는 장면 |

## 8. 10-Block Audit Status

| Range | Status |
|-------|--------|
| Block 001~010 | 감리 PASS |
| Block 011~020 | Block 15 완료 후 감리 필요 (하��스 §1.1C는 Block 010/020/030... 경계) |

## 9. Resume Instructions

1. 이 문서를 읽는다.
2. `treatments/10_jaebeol3se_loss_line_tr_block_070_draft.json`을 열어 마지막 블록 확인.
3. `treatments/phase0/jaebeol3se_loss_line_phase0_design.json`에서 다음 블록 slot 확인.
4. Block 13 사전 선언(§4)을 참고해 JSON 생성 → ��가 점검 → 감리.
5. Block 15 완료 후 ARC-01 마무리 → Block 11~15 구간은 Block 020 감리 시 합산.
6. 하네스: `docs/blockguide/treatment-production-harness-v2.md` §1.4 초세분화 루틴.

## 10. Temp Files to Clean

- `treatments/preprocess/jaebeol3se_loss_line/_append_block.py` — 블록 append 임시 스크립트. Block 13 사전 선언 상태로 남아 있음. 재���용 가능하나 block_id/content를 교체해야 함.
