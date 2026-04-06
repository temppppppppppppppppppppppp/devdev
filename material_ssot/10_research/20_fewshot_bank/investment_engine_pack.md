# Investment Engine Pack

Date: 2026-04-06
Status: active
Scope: canonical deep-study engine pack for future `investment_market_profile` and adjacent office/investment pitch generation

## 1. Purpose

이 문서는 투자물 신규 기획안을 만들 때 매번 카드 24장을 다시 훑지 않도록, 현재 가장 중요한 내러티브 엔진 5개와 보조 YouTube 재료 라인을 우선 세트로 고정한다.

운용 원칙:

- 이 문서는 `작품 감상문`이 아니다
- 이 문서는 `비슷한 작품을 베끼기 위한 목록`이 아니다
- 이 문서는 `신규 투자물 기획안 조합용 핵심 엔진 세트`다
- 이 문서를 `default_work_guard.yaml`에 그대로 이식하지 않는다

## 2. Priority Model

### 2.1 Tier 1. Deep Engine Core 5

아래 5개를 현재 투자물 신규 기획안의 최우선 deep-study 엔진으로 본다.

1. `김 대리는 인생이 너무 가볍다 A`
   - path: `material_ssot/10_research/20_fewshot_bank/cards/gim_daerineun_insaengi_neomu_gabyeopda_A.md`
   - primary use:
     - 현대 직장인 톤
     - 직장 내 humiliation -> 태도 변화 리듬
     - 투자와 회사 생활의 병렬 성장

2. `김 대리는 벼락부자 A`
   - path: `material_ssot/10_research/20_fewshot_bank/cards/gim_daerineun_byeorakbuja_A.md`
   - primary use:
     - 벼락부자 이후에도 퇴사하지 않는 `stay method`
     - 이중 생활 긴장 유지
     - 돈이 생긴 뒤에도 일상선이 살아 있는 구조

3. `주식의 신 A`
   - path: `material_ssot/10_research/20_fewshot_bank/cards/jusigui_sin_A.md`
   - primary use:
     - 순정 투자물 리듬
     - 정보 장치 -> 첫 매수 -> 홀드 -> 회수
     - HTS/매매/가족 피해 복구형 동기 엔진

4. `재벌생활기록부 A`
   - path: `material_ssot/10_research/20_fewshot_bank/cards/jaebeol_saenghwal_girokbu_A.md`
   - primary use:
     - 돈만이 아닌 생활/권력/재벌 외피의 가시화
     - 일상 속 재벌 감각
     - 회사/가문 안 위치 변화의 보여주기

5. `독식하는 재벌 3세 A`
   - path: `material_ssot/10_research/20_fewshot_bank/cards/dokshik_jaebeol3se_A.md`
   - primary use:
     - 극단 바닥 설계
     - 안목 보정형 치트의 설계 방식
     - 수익 전액 재투자 에스컬레이션
     - 1화 마이크로 사이다

### 2.2 Tier 2. Supporting YouTube Material Lanes

아래 YouTube raw lanes는 `주인공 엔진`이 아니라 `도메인 현실감 / 시장 감각 / 산업 촉감` 보강용 보조 재료로 쓴다.

1. `eo`
   - path: `material_ssot/10_research/80_ingest_raw/2026-04-03/_eo_raw.jsonl`
   - use:
     - 창업가/운영자 인터뷰 톤
     - 사업 의사결정 맥락
     - 회사에 남아 있는 이유의 현실화

2. `syuka`
   - path: `material_ssot/10_research/80_ingest_raw/2026-04-03/_syuka_raw.jsonl`
   - use:
     - 거시 흐름
     - 시장 센티먼트 어휘
     - 투자 리듬의 현실 배경

3. `techmong`
   - path: `material_ssot/10_research/80_ingest_raw/2026-04-03/_techmong_raw.jsonl`
   - use:
     - 제조/부품/테크 밸류체인 감각
     - 공급망 병목과 수혜주 연결
     - 산업 리스크 투자물의 소재 보강

4. `changeground`
   - path: `material_ssot/10_research/80_ingest_raw/2026-04-03/_changeground_raw.jsonl`
   - use:
     - 조직/심리/의사결정 프레이밍
     - 직장인 자기서사와 갓생 전환 톤

5. `minani`
   - path: `material_ssot/10_research/80_ingest_raw/2026-04-03/_minani_raw.jsonl`
   - use:
     - 산업/기술/시대 변화의 설명 재료
     - "왜 지금 이 섹터인가"의 why-now 보강

## 3. Borrowing Contract

이 엔진팩을 쓸 때는 아래 계약을 반드시 지킨다.

1. 한 작품에서 `큰 엔진`은 하나만 가져온다.
   - 예: `김 대리는 벼락부자`에서 `stay method`를 가져왔다면, 같은 작품의 고유 벼락부자 기믹까지 통째로 가져오지 않는다.

2. YouTube 재료는 `도메인 질감`만 주고, 주인공 엔진은 주지 않는다.
   - 주인공 얼굴, 첫 승리, proof scene, first reward는 반드시 few-shot card에서 먼저 조립한다.

3. 고유 기믹은 금지한다.
   - 특정 앱
   - 특정 치트 UI
   - 특정 종목/수치
   - 특정 인물/회사 구조

4. 새 기획안은 반드시 `pitch-selection-checklist.md`를 통과해야 한다.
   - innocence
   - first win = 평가 수정
   - proof scene
   - early reward = status-first
   - crisis 4요소

## 4. What To Extract

새 투자물 기획안 전에 아래 8개 항목만 추출해 조합한다.

1. `opening humiliation`
2. `stay method`
3. `protagonist edge`
4. `first proof scene`
5. `first reward`
6. `authority gain route`
7. `growth axis`
8. `must_not_copy`

실전 조합 예시:

- 직장인 톤: `김 대리는 인생이 너무 가볍다`
- 회사 잔류 논리: `김 대리는 벼락부자`
- 투자 플레이 리듬: `주식의 신`
- 권력 외피/생활감: `재벌생활기록부`
- 안목 보정/에스컬레이션: `독식하는 재벌 3세`
- 산업 도메인 재료: `techmong + syuka + eo`

## 5. Practical Flow

신규 투자물 기획안 생성 시 순서는 아래가 기본값이다.

1. `Tier 1`에서 3~5개 엔진 슬롯을 고른다
2. `Tier 2`에서 1~2개 YouTube 재료 라인을 얹는다
3. one-line premise / why now / protagonist position / first block reward를 1장으로 쓴다
4. `pitch-selection-checklist.md`로 hard gate를 친다
5. 통과한 안만 `work_guard.yaml` 번역 대상으로 넘긴다

## 6. Current Recommendation

현 시점 투자물 신규 기획안은 아래 방향에서 가장 안정적이다.

- `퇴사 판타지`보다 `회사에 남아 있어야 먼저 읽을 수 있다`
- `돈 자랑`보다 `태도 변화 + 접근권 + 시드 자본`
- `운빨 대박`보다 `안목 + 정보격차 + 회수 리듬`
- `자산 증가만`보다 `회사 안 위치 변화`를 같이 찍는다

## 7. Bridge Note

이 엔진팩은 upstream research synthesis 정본이다.

- pitch selection 정본: `material_ssot/20_pitch/pitch-selection-checklist.md`
- pitch house-law 정본: `material_ssot/20_pitch/protagonist-first-constitution.md`
- runtime translation bridge: `material_ssot/20_pitch/work-guard-translation-map.md`
- investment runtime template: `work_guards/investment/default_work_guard.yaml`

역할 분리:

- 이 문서: 신규 기획안 조합과 작품별 work guard 설계 전의 research synthesis 정본
- `default_work_guard.yaml`: 얇은 장르 템플릿
- 작품별 `work_guard.yaml`: 실제 런타임 doctrine
