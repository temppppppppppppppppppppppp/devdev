# Reference Collection Index v3

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-30
> 목적: 현재 우리가 어떤 reference 작품/트랙을 모았고, 무엇이 바로 usable이며 무엇이 재감리 대상인지 한눈에 본다
> 2026-04-03 migration note: canonical few-shot root moved to `material_ssot/10_research/20_fewshot_bank`

---

## 0. 진실 우선순위

이 인덱스의 현재 진실 우선순위는 아래와 같다.

1. `reference_card_manifest.json`
2. `cards/` 실제 카드 파일 존재 여부
3. `../10_reference_profiles/2026-03-30_modern_business_reference_master_order.md`의 후보/운영 메모

즉, `master order`에 오더가 있어도 `manifest`와 `cards`가 맞지 않으면 아직 usable reference가 아니다.

---

## 1. Snapshot

- manifest 등록 엔트리: `24`
- 작품 수: `12`
- 실제 카드 파일 수: `24`
- `audited / pass`: `24`
- `saved / needs_reaudit`: `0`
- `pending`: `0`

핵심 판정:

- 현재 풀은 `전량 수집 완료`, `부분 usable` 상태다.
- `24개 전부` 바로 synthesis 후보로 쓸 수 있다.
- 남은 재감리 대상은 없다.

구조적 공통 원인:

- `A 트랙` 대부분이 `현대 현판 적용 분해` 섹션 없이 저장됐다.
- `A 오더 템플릿/수집 계약 불일치` 잔여분도 이번 wave에서 해소됐다.
- 현재 병목은 수집/재감리가 아니라 Director synthesis다.

---

## 2. 작품별 현황

| 작품 | 트랙 현황 | 현재 판정 | 메모 |
| --- | --- | --- | --- |
| `독식하는 재벌 3세` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 코어 세트 완료 |
| `금수저 투자백서` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 딜/거물화 HOW 확보 |
| `김 대리는 벼락부자` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 직장인 출발/사업 확장 축 확보 |
| `국세청 망나니` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 권위 행사/압박 축 확보 |
| `주식의 신` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 투자/주식형 정보격차 축 확보 |
| `연봉 1조 신입사원` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 신입 과잉 성능/보상 축 확보 |
| `검은 머리 미국 대재벌!` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 글로벌 재벌 스케일 축 확보 |
| `불행을 보는 재벌집 손자` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 리스크 감지형 성장 축 확보 |
| `대한민국 절대 재벌` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 정통 재벌 스케일 축 확보 |
| `신흥재벌` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 재벌 확장 축 확보 |
| `재벌생활기록부` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 생활밀착 재벌 운영 축 확보 |
| `김 대리는 인생이 너무 가볍다` | `A=audited/pass`, `B=audited/pass` | 전량 usable | 자수성가형 현대 현판 확장 축 확보 |

---

## 3. 트랙별 상세 목록

| 작품 | 트랙 | status | audit_status | 카드 경로 |
| --- | --- | --- | --- | --- |
| `주식의 신` | `A` | `audited` | `pass` | `cards/jusigui_sin_A.md` |
| `주식의 신` | `B` | `audited` | `pass` | `cards/jusigui_sin_B.md` |
| `독식하는 재벌 3세` | `A` | `audited` | `pass` | `cards/dokshik_jaebeol3se_A.md` |
| `독식하는 재벌 3세` | `B` | `audited` | `pass` | `cards/dokshik_jaebeol3se_B.md` |
| `금수저 투자백서` | `A` | `audited` | `pass` | `cards/geumsujeo_tujabaekseo_A.md` |
| `금수저 투자백서` | `B` | `audited` | `pass` | `cards/geumsujeo_tujabaekseo_B.md` |
| `김 대리는 벼락부자` | `A` | `audited` | `pass` | `cards/gim_daerineun_byeorakbuja_A.md` |
| `김 대리는 벼락부자` | `B` | `audited` | `pass` | `cards/gim_daerineun_byeorakbuja_B.md` |
| `국세청 망나니` | `A` | `audited` | `pass` | `cards/guksecheong_mangnani_A.md` |
| `국세청 망나니` | `B` | `audited` | `pass` | `cards/guksecheong_mangnani_B.md` |
| `연봉 1조 신입사원` | `A` | `audited` | `pass` | `cards/yeonbong_1jo_sinipsawon_A.md` |
| `연봉 1조 신입사원` | `B` | `audited` | `pass` | `cards/yeonbong_1jo_sinipsawon_B.md` |
| `검은 머리 미국 대재벌!` | `A` | `audited` | `pass` | `cards/geomeunmeori_american_jaebeol_A.md` |
| `검은 머리 미국 대재벌!` | `B` | `audited` | `pass` | `cards/geomeunmeori_american_jaebeol_B.md` |
| `불행을 보는 재벌집 손자` | `A` | `audited` | `pass` | `cards/bulhaengeul_boneun_jaebeoljip_sonja_A.md` |
| `불행을 보는 재벌집 손자` | `B` | `audited` | `pass` | `cards/bulhaengeul_boneun_jaebeoljip_sonja_B.md` |
| `대한민국 절대 재벌` | `A` | `audited` | `pass` | `cards/daehanminguk_absolute_jaebeol_A.md` |
| `대한민국 절대 재벌` | `B` | `audited` | `pass` | `cards/daehanminguk_absolute_jaebeol_B.md` |
| `신흥재벌` | `A` | `audited` | `pass` | `cards/sinheung_jaebeol_A.md` |
| `신흥재벌` | `B` | `audited` | `pass` | `cards/sinheung_jaebeol_B.md` |
| `재벌생활기록부` | `A` | `audited` | `pass` | `cards/jaebeol_saenghwal_girokbu_A.md` |
| `재벌생활기록부` | `B` | `audited` | `pass` | `cards/jaebeol_saenghwal_girokbu_B.md` |
| `김 대리는 인생이 너무 가볍다` | `A` | `audited` | `pass` | `cards/gim_daerineun_insaengi_neomu_gabyeopda_A.md` |
| `김 대리는 인생이 너무 가볍다` | `B` | `audited` | `pass` | `cards/gim_daerineun_insaengi_neomu_gabyeopda_B.md` |

---

## 4. 현재 usable 세트

### 4.1 바로 synthesis 가능한 카드 24개

- `독식하는 재벌 3세`
- `금수저 투자백서`
- `김 대리는 벼락부자`
- `국세청 망나니`
- `주식의 신`
- `연봉 1조 신입사원`
- `검은 머리 미국 대재벌!`
- `불행을 보는 재벌집 손자`
- `대한민국 절대 재벌`
- `신흥재벌`
- `재벌생활기록부`
- `김 대리는 인생이 너무 가볍다`

### 4.2 재감리 필요 카드

- 없음

### 4.3 현재 가장 안전한 Director 조합용 코어

- `독식하는 재벌 3세 B`
- `금수저 투자백서 B`
- `김 대리는 벼락부자 B`
- `국세청 망나니 B`

---

## 5. 다음 액션

현재 기준 최우선 작업:

1. `24개 audited/pass` 풀에서 기능 매트릭스를 뽑는다
2. `Director synthesis`로 opening / edge / spike / first reward / growth axis를 교차 조합한다
3. 그 다음 `work_id` 기획안 조립으로 이동

운영 메모:

- 수집/재감리 wave는 종료됐다
- 이제는 `24개 usable 카드` 전량을 synthesis pool로 쓰면 된다
- 새 작품 추가 조사는 Director synthesis 뒤 부족 기능이 남을 때만 연다

---

## 6. 3-Pass Self Audit

### Pass 1. 구조

- `Snapshot -> 작품별 현황 -> 트랙별 상세 -> usable 세트 -> 다음 액션` 순으로 바로 운영에 쓰게 재구성했다.

### Pass 2. 근거

- `reference_card_manifest.json`과 실제 `cards/` 파일 존재 여부만 기준으로 삼았다.
- 이번 버전에서는 stale `pending`/`미수집` 정보를 모두 제거했다.

### Pass 3. 실행성

- 지금 바로 usable한 카드 풀과 다음 단계가 명확해졌다.
- 이제 reference collection은 병목이 아니고, Director synthesis가 다음 병목이다.
