# WG-V2 Verdict: office_checkup_next_day

- Date: 2026-04-06
- Terminal: 1
- Batch: work_guard_greenplus_batch01

## 1. Target Work

- work_id: `office_checkup_next_day`
- title: 검진 다음 날부터
- family: blockguide
- profiles: `office_power_profile` + `business_growth_profile`

## 2. Authority Set Used

- canonical pitch: `material_ssot/20_pitch/canon/office_checkup_next_day.md`
- pitch philosophy: `material_ssot/20_pitch/pitch-philosophy.md`
- protagonist-first constitution: `material_ssot/20_pitch/protagonist-first-constitution.md`
- translation map: `material_ssot/20_pitch/work-guard-translation-map.md`
- profile lock: `treatments/preprocess/office_checkup_next_day/profile_lock.json`
- phase0 ready snapshot: `treatments/preprocess/office_checkup_next_day/phase0_ready_snapshot.json`
- live phase0: `treatments/office_checkup_next_day_phase0_design.json`
- live TR: `treatments/07_office_checkup_next_day_tr_block_070_draft.json`
- live BI: `bible/07_bi_office_checkup_next_day.json`
- production grade: `GREENPLUS`

## 3. WG-V2 Checklist

### 1. One-Line Truth — YES

`B0짜리 말단 사원이 결재선 병목과 숨긴 숫자를 먼저 읽어, 우회 경로와 실데이터 대안으로 관문을 만들고, 모두가 허락을 구하는 조직의 관문이 된다`

주인공 장악 판타지가 바로 읽힌다. generic theme 아님. `왜 이 주인공이 멋있는가`가 한 문장에 들어 있다.

### 2. Protagonist-First Purity — YES

결핍(B0 말단, 사수 퇴사, 잡무 담당)은 명확하되 과실은 없다. 회개물/자업자득 스타트와 무관. 검진 후 감각 발화로 시작하되 시스템/상태창이 아니라 `조직 역학 조감`이라는 비명시적 감각으로 처리됨.

### 3. Tracking Slots — YES

4개 slot 모두 `서열 변화 / 통제권 회수 / 재평가` 축이다.

- 결재선 위치 상승 (Lv1→Lv7) — 제도적 서열 추적
- 저평가→고평가 전환 — 호칭·자리·CC로 체감
- 프로젝트 오너십 / TF 실권 회수 — 통제권
- 병목 형성 — 장악도

`성장`, `성공`, `열심히 함` 같은 generic 없음.

### 4. Signature Scene Engine — YES

3개 engine 모두 `저건 쟤라서 가능했다`를 증명하는 구조.

- 병목 감지 + 우회 상신: 시혁만의 조감 감각 + 경로 설계력
- 회의장 공개 증명: 조작 데이터 인용 지점을 한 줄로 짚는 장면
- 성과 직후 체감형 보상 부착: 실명 메일/TF/자리/CC 중 즉시 1종+

첫 블록 간판(임원회의 통합안 저지)이 engine에 정확히 잡혀 있다.

### 5. Protagonist Weapon — YES

3개 무기 모두 인과가 선명하다.

- 조직 역학 조감 감각: 결재선·숫자·사람을 동시에 읽는 것은 이 작품 고유
- 우회 경로 설계력: 사업부장이 막기 어려운 상신 경로를 짜는 것은 generic competence 아님
- 실데이터 대안 속도: 하룻밤 안에 실물동량 기반 대안을 만드는 실무력

### 6. Reward Vector — YES

- 초반 보상이 돈이 아니라 `실명 호명 → TF 발령 → 자리 이동 → CC 변경`으로 서열 변화 4종 동시 부착
- `admiration_axes`에 `결과로 인정 강제`, `판을 잘못 읽히게 만드는 여유` 등 재평가 방식 명시
- `observer_tiers`가 동료→전무→팀장(견제)→사업부장(적대적 재평가)→대표이사로 계층화
- `evaluation_thresholds`에 1화/3화/Block 1 기준점 명시

### 7. Crisis Doctrine — YES

- `남들보다 먼저 읽음`이 admiration_axes 첫 항목
- `손실을 통제함`이 별도 축
- `위기 때 빈손/무대응/무보상`이 forbidden_flattenings에 포함
- custom_rules에 `위기는 피해 연출보다 우선순위 선택권 증명`, `반격 예약 없는 손해 금지` 명시

### 8. Forbidden Flattenings Coverage — YES

12개 항목으로 치명 drift를 충분히 막고 있다. 7대 기본 drift 전부 포함 + 작품 고유 금지(적대자 캐리커처, 결재선 추상화, MD 적자 뭉뚱그림, 능력 자기 해설, 운빨 포장) 5개 추가.

### 9. Translation Discipline — YES

upstream 철학 문서 복붙 없음. 모든 항목이 작품별 doctrine으로 압축됨. 교육용 설명문 없음.

### 10. Work Specificity — YES

이 guard를 다른 작품에 그대로 붙이면 어색하다. `결재선 Lv1~Lv7`, `CC 라인`, `전용 코드 vs 공용 코드`, `물동량`, `밀어내기`, `오세진/장현태` 등 이 작품 고유의 산업 언어와 인물 역학이 전면에 있다.

## 4. WG-V2 Result

**PASS**

- NO: 0개
- WEAK: 0개
- 4번(Signature Scene Engine), 5번(Protagonist Weapon), 6번(Reward Vector) 모두 YES

## 5. Weak Points

없음. 이 작품은 authority chain이 가장 완비되어 있고, GREENPLUS 사유 자체가 `첫 블록 conversion이 가장 깨끗하다`이므로 work_guard 번역도 가장 직선적이다.

## 6. Next Action

- freeze candidate로 확정
- 다른 터미널의 draft 완료 후 batch close 시 일괄 freeze 검토
