# 전처리 SSOT 1차 기획안

> 작성일: 2026-03-12
> 목적: Stage 0에서 사용되는 BI·TR JSON을 **설계 → 생산 → 검증 → 출고**하는 전처리 공정의 SSOT 폴더 구조와 파이프라인 설계
> 출력 목적지: `treatments/` (TR), `bible/` (BI)

---

## §0. 왜 전처리 SSOT가 필요한가

### 현황 (as-is)

| 자산 | 현재 위치 | 문제 |
|------|-----------|------|
| 하네스 문서 4+2개 | `docs/blockguide/` | 읽는 순서·단계 판정은 있으나, **실행 코드와 분리** |
| 소재 DB | `test_material/material_bank.db` | 빌드 스크립트 15개가 같은 폴더에 혼재 |
| 빌드 스크립트 | `scripts/build_*.py`, `scripts/generate_*.py` | 작품별 1파일 80~160KB 모놀리스, 재사용 불가 |
| 배치 하네스 | `scripts/tr_batch_harness.py` (47KB) | validate 로직 내장, 하네스 문서와 이중 관리 |
| 감사 리포트 | `bible/audit_reports/` (3파일), `treatments/audit_reports/` (63+파일) | TR/BI별 분리는 되어 있으나, 전처리 중앙 관리 시 편의 향상 가능 |
| Phase 0 설계 | 작품별 `_phase0_design.json` 산재 | `preset_registry.py` (40KB)에 프리셋 기반 템플릿 존재하나, 전처리 전용 확장(P-1 opponent 배치, P-2 weakness 사전설계)은 미구현 |

### 핵심 문제 3가지

1. **산재** — 하네스(docs) + 소재(test_material) + 코드(scripts + tools + tools2) + 출력(treatments/bible)이 **5곳 이상**에 흩어져 있어 신규 작품 착수 시 "뭘 먼저 해야 하지?" 반복
2. **부분 재사용 + 복사-수정 혼재** — `tr_batch_harness.py` 3함수(validate_candidate, build_open_foreshadow_ledger, render_report)는 작품 간 공유 중이나, Phase 0 설계·블록 데이터 구성·BI 생성 로직은 여전히 작품별 복사-수정 구조 (build_*.py 82~158KB)
3. **검증 이중화** — `tr_batch_harness.py`의 validate + `tools2/apply_v3.py`의 validate_v3 + 하네스 문서(v1/v2/v3)의 규칙 텍스트가 3곳에서 별도 관리 → 어느 게 진짜인가?

### 목표 (to-be)

```
전처리_ssot/  ← 단일 진입점
├── 하네스 읽기
├── 소재 조회
├── Phase 0 설계
├── TR 생산 (배치 단위)
├── 검증 (validate_v3 통합)
├── BI 생산
├── 감사
└── 출고 → treatments/ + bible/
```

---

## §1. 폴더 구조 설계

```
전처리_ssot/
│
├── 00_전처리_SSOT_1차_기획안.md          ← 이 문서
├── README.md                             ← 진입점 가이드 (어디서 시작하나)
│
├── 하네스/                               ← 생산기지 작업 매뉴얼 (사본, §3.1)
│   ├── SSOT_통합오더.md                   ← SSOT_blockguide-integrated-order.md 사본
│   ├── 기획_하네스.md                     ← treatment-planning-harness.md 사본
│   ├── 생산_하네스_v2.md                  ← treatment-production-harness-v2.md 사본
│   ├── BI_하네스_v1.md                    ← bi-production-harness-v1.md 사본
│   ├── 블록보강_TF-BH1.md                ← TF-BH1_block_harness_reinforcement.md 사본
│   ├── 3pass_감사패치.md                  ← harness_3pass_audit_and_patch.md 사본
│   └── README.md                         ← 원본 경로 + 동기화 규칙
│
├── 장르_프로파일/                         ← SSOT 참조 안내 (별도 YAML 없음, §4.1)
│   └── README.md                         ← preset_registry.py + genre_schema_builder 경로
│
├── 소재뱅크/                             ← 조회 도구 (DB는 원본 위치 참조)
│   ├── query.py                          ← 소재 조회 CLI (키워드, 섹터, 연도)
│   └── 소재_카탈로그.md                   ← 테이블별 통계 + 사용법 가이드
│
├── 템플릿/                               ← Phase 0 / TR / BI 표준 템플릿
│   ├── phase0_template.json              ← Phase 0 설계 빈 껍데기
│   ├── tr_block_template.json            ← TR 블록 1개 빈 껍데기
│   ├── bi_template.json                  ← BI 빈 껍데기
│   └── genre_ext/                        ← 장르별 genre_ext 확장 필드 예시
│       ├── investment_ext.json
│       ├── alt_history_ext.json
│       └── ...
│
├── 작품별/                               ← 작품 단위 작업 공간
│   ├── 02_chaebol_allowance_zero/
│   │   ├── phase0_design.json            ← 이 작품의 Phase 0
│   │   ├── batch_log/                    ← 배치별 candidate + fixed + audit
│   │   │   ├── batch_001_candidate.json
│   │   │   ├── batch_001_fixed.json
│   │   │   └── batch_001_audit.md
│   │   ├── work_config.yaml              ← 작품별 설정 (장르, 프로파일, 블록수)
│   │   └── progress.json                 ← 현재 진행 상태 (몇 블록까지, PASS/FAIL)
│   ├── 05_fallen_prince_buys_joseon/
│   │   └── ...
│   └── ...
│
├── 검증/                                 ← validate_v1/v2/v3 통합
│   ├── validate.py                       ← 통합 검증 CLI (v1+v2+v3)
│   ├── rules/                            ← 검증 규칙 YAML
│   │   ├── v1_basic.yaml                 ← 기본 구조 검사
│   │   ├── v2_pattern.yaml               ← 패턴 Q~U 검사
│   │   └── v3_density.yaml               ← R27~R33 밀도 검사
│   └── reports/                          ← 검증 리포트 출력
│
├── 출고/                                 ← 최종 출고 게이트
│   ├── export.py                         ← TR/BI → treatments/bible/ 복사 + UTF-8 검증
│   └── gate_checklist.md                 ← 출고 전 체크리스트
│
└── 감사/                                 ← 감사 리포트 아카이브
    ├── tr/                               ← TR 감사 리포트
    ├── bi/                               ← BI 감사 리포트
    └── cross/                            ← TR↔BI 교차 감사
```

---

## §2. 파이프라인 흐름도

```
┌─────────────────────────────────────────────────────────────┐
│                    전처리 SSOT 파이프라인                      │
└─────────────────────────────────────────────────────────────┘

[입력] 작품 컨셉 + 장르 선택
         │
         ▼
┌──────────────────┐
│  §A. 하네스 읽기   │  SSOT 통합오더 → 기획 하네스 순서로 읽기
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §B. 소재 조회    │  material_bank.db에서 키워드/섹터/연도 검색
│                  │  → 역사 이벤트, NPC 원형, 위기 시나리오 수집
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §C. Phase 0     │  장르 프로파일 로드 + 소재 결합
│   설계            │  → opponent 배치 매트릭스 (P-1)
│                  │  → weakness 사전 설계 (P-2)
│                  │  → sector_roadmap 70블록
│                  │  → npc_timeline + foreshadow_map
│                  │  출력: 작품별/XX/phase0_design.json
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §D. TR 생산      │  1턴 1배치 (3블록 안전 모드)
│   (배치 순차)      │  배치마다:
│                  │    1. blocks_so_far로 패턴 피드백 생성 (P-3)
│                  │    2. 프롬프트 = phase0 + 패턴피드백 + "Block X~Y"
│                  │    3. LLM 생성 → candidate.json
│                  │    4. Python auto-fix → fixed.json
│                  │    5. validate_v3 검사
│                  │    6. P0 위반 → 같은 배치 재작업
│                  │    7. PASS → 다음 배치
│                  │  출력: 작품별/XX/batch_log/
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §E. TR 병합      │  batch_001~024 → 70블록 단일 파일
│                  │  + 전체 validate_v3 재검사
│                  │  출력: tr_block_070_draft.json (임시)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §F. BI 생산      │  TR → BI 동기화 (bi-production-harness-v1)
│                  │  Phase 0~5 순서 실행
│                  │  출력: 0_bi_XX.json (임시)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §G. 교차 감사    │  TR↔BI 정합성 검증
│                  │  + 5-pass BI 감사
│                  │  + 3-pass TR 감사
│                  │  출력: 감사/cross/XX_audit.md
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  §H. 출고 게이트   │  체크리스트 전항 PASS 확인
│                  │  UTF-8 검증
│                  │  파일 복사:
│                  │    tr → treatments/XX_tr_block_070_draft.json
│                  │    bi → bible/XX_bi.json
└──────────────────┘
```

---

## §3. 핵심 설계 결정

### 3.1 하네스 문서 — 사본 + 동기화

> **[TF-PP1 P2-05 + TF-PP2 F-01 재검토]** 심링크는 Windows에서 불안정.
> 그러나 **생산기지에 작업 매뉴얼이 물리적으로 없으면 기지가 아님**.
> 참조 문서(README만)로 축소하면 매번 원본 경로를 찾아가야 함 → SOP 흐름 파괴.

**결정: 사본 (copy) + README에 동기화 규칙**

- `docs/blockguide/`가 원본(SSOT) 유지 → git 추적
- `전처리_ssot/하네스/`에 6개 문서 **사본** 배치 → 생산 중 즉시 참조 가능
- 원본 수정 시 사본도 수동 동기화 (README.md에 "원본 변경 시 여기도 갱신" 규칙 기재)
- 사본은 **읽기 전용** — 수정은 반드시 원본(docs/blockguide/)에서
- 심링크 대비 단점(이중 파일)은 있으나, 6개 문서 수준이면 관리 가능

### 3.2 소재뱅크 DB — 이동 vs 참조

**결정: 참조 (현 위치 유지, 조회 도구만 전처리에 배치)**

- `material_bank.db` 14.2MB → 이동 시 기존 빌드 스크립트 전부 경로 변경 필요
- 전처리에는 조회용 `query.py`만 두고, DB는 원본 경로 참조
- 빌드 스크립트 15개는 `test_material/`에 그대로 둠 (소재 수집은 전처리 밖)

### 3.3 작품별 디렉토리 구조

**결정: 번호 프리픽스 + work_id**

```
작품별/
├── 02_chaebol_allowance_zero/       ← 기존 02번
├── 05_fallen_prince_buys_joseon/    ← 기존 05번
├── 08_us_ai_exile_monopoly/         ← 기존 08번
└── _template/                       ← 신규 작품 시 복사할 빈 틀
    ├── phase0_design.json
    ├── work_config.yaml
    └── batch_log/
```

### 3.4 검증 SSOT — 코드 vs 문서

**결정: YAML 규칙 + Python 실행기**

현재 문제:
- `tr_batch_harness.py`에 validate 로직 내장 (47KB)
- 하네스 문서에 규칙 텍스트로 기술
- `TF-BH1`에 validate_v3 Python 코드 인라인

해결:
- 규칙을 `검증/rules/*.yaml`로 SSOT화
- `검증/validate.py`가 YAML 읽어서 실행
- 하네스 문서는 규칙의 **설명**만 담고, 실행 코드는 참조하지 않음

### 3.5 감사 리포트 분리

**결정: 전처리_ssot/감사/ 로 이동**

현재 `treatments/audit_reports/`와 `bible/audit_reports/`에 섞여 있음
→ 감사는 전처리의 일부이므로 전처리 폴더로 이동
→ 출고된 TR/BI 파일만 `treatments/`, `bible/`에 남김 (깨끗한 출력)

---

## §4. 장르 프로파일 시스템

### 4.1 설계 원칙 — 기존 시스템 단일 참조 (SSOT)

> **[TF-PP1 P3-01 수정]** 장르 프로파일을 새로 만들면 `modules/core/stage0/preset_registry.py` (40KB)와 이중 관리됨.
> 전처리는 기존 프리셋 시스템을 **참조**하거나 **확장**해야 하며, 별도 YAML로 복제하면 안 됨.

**SSOT 참조 경로:**
```
장르 프리셋 정의       → modules/core/stage0/preset_registry.py (40KB)
장르별 genre_ext 스키마 → modules/core/genre_schema_builder.py
장르 가드 실행         → modules/core/genre_guards/*.py (10종)
```

**전처리에서의 사용 방식:**
```
전처리_ssot/장르_프로파일/
└── README.md  ← "장르 프로파일 SSOT는 아래 파일 참조:
                   - modules/core/stage0/preset_registry.py
                   - modules/core/genre_schema_builder.py
                   전처리 전용 확장이 필요하면 preset_registry.py에 추가하되,
                   별도 YAML을 만들지 않는다."
```

**만약 YAML 외부화가 필요하다면 (향후):**
```
config/presets/           ← 전처리와 런타임이 공유하는 단일 위치
├── _common.yaml
├── investment.yaml
└── ...

modules/core/stage0/preset_registry.py → config/presets/ 로드
전처리_ssot/ → config/presets/ 참조 (같은 파일)
```

SSOT 통합오더 §0A~0C의 **general mode** 체계 참조 스키마:

```yaml
# 참고: 이 구조는 preset_registry.py에 이미 구현되어 있음
# 공통 코어 (모든 작품)
core_contract:
  protagonist:
    must_have: [desire, deficiency, edge]
  growth_resource:
    field_alias: "capital"
  decisive_action:
    field_alias: "deal_type"
  structure:
    total_blocks: 70
    arcs_per_volume: 7
    blocks_per_arc: 10
    episodes_per_arc: [3, 6]
```

### 4.2 장르 가드 ↔ 전처리 프로파일 매핑

| # | 장르 가드 | 전처리 프로파일 | 핵심 자원 | genre_ext 특화 필드 |
|---|-----------|----------------|-----------|-------------------|
| 1 | `investment_guard` | `investment.yaml` | 자본, 수익률 | capital, leverage, historical_event |
| 2 | `wuxia_guard` | `wuxia.yaml` | 내공, 무공, 경지 | realm, qi_nature, martial_arts |
| 3 | `hunter_guard` | `hunter.yaml` | 전투력, 랭크, 던전 | hunter_rank, dungeon_tier, party_power |
| 4 | `fantasy_guard` | `fantasy.yaml` | 마나, 스킬, 레벨 | mana_pool, skill_tree, class_tier |
| 5 | `alt_history_guard` | `alt_history.yaml` | 품계, 파벌, 어전 | rank, faction_leverage, political_action |
| 6 | `composer_guard` | `composer.yaml` | 작품, 평판, 계약 | composition_rank, contract_value |
| 7 | `medical_guard` | `medical.yaml` | 집도권, 케이스, 신뢰도 | surgery_authority, case_complexity |
| 8 | `sports_guard` | `sports.yaml` | 기록, 순위, 팀 | personal_record, team_rank, season |
| 9 | `actor_guard` | `actor.yaml` | 화제성, 캐스팅, IP | buzz_score, casting_tier, ip_value |
| 10 | `cooking_guard` | `cooking.yaml` | 레시피, 매장, 평점 | recipe_mastery, store_rating |

### 4.3 범용 추가 프로파일 (가드 미구현 장르)

SSOT 통합오더에서 선언했지만 아직 장르 가드가 없는 프로파일:

| 프로파일 | 상태 | 비고 |
|----------|------|------|
| `business_growth_profile` | 프로파일만 | investment_guard 확장으로 커버 가능 |
| `entertainment_media_profile` | 프로파일만 | actor_guard 확장으로 커버 가능 |
| `office_power_profile` | 미구현 | 신규 guard 필요 시 후순위 |
| `tech_startup_profile` | 미구현 | 신규 guard 필요 시 후순위 |
| `urban_power_profile` | 미구현 | hunter_guard 확장으로 커버 가능 |

---

## §5. 패턴 피드백 루프 (P-3 구현 설계)

3-pass 감사에서 식별된 **RC-3 (생산 프롬프트에 패턴 피드백 없음)** 해소를 위한 설계.

### 5.1 피드백 생성 함수

```python
def build_pattern_feedback(blocks_so_far: list[dict]) -> str:
    """이전 배치까지의 패턴을 분석하여 다음 배치 프롬프트에 주입할 피드백 생성."""

    # 0. opponent 이름 추출 (dict/str 양쪽 호환 — TF-PP1 P1-03)
    def _get_opponent_name(block: dict) -> str:
        opp = block.get("genre_ext", {}).get("opponent")
        if isinstance(opp, dict):
            return opp.get("name", "")
        if isinstance(opp, str):
            return opp
        return ""

    # 1. opponent 빈도
    opps = Counter(_get_opponent_name(b) for b in blocks_so_far)

    # 2. weakness 다양성
    weaknesses = set(
        b.get("genre_ext", {}).get("opponent", {}).get("weakness_exploited", "")
        for b in blocks_so_far
    )

    # 3. solution 말미 반복
    tails = Counter(
        b.get("content", {}).get("solution", "")[-20:]
        for b in blocks_so_far
    )

    # 4. business_sector 분포
    sectors = Counter(
        b.get("genre_ext", {}).get("business_sector", "")
        for b in blocks_so_far
    )

    lines = ["[패턴 피드백 — 이전 블록 분석 결과]"]
    lines.append(f"생산된 블록 수: {len(blocks_so_far)}")
    lines.append(f"opponent 빈도: {dict(opps.most_common(5))}")
    lines.append(f"사용된 weakness 종류: {len(weaknesses)}종")
    lines.append(f"sector 분포: {dict(sectors.most_common(5))}")

    for tail, cnt in tails.most_common(3):
        if cnt >= 3:
            lines.append(f"⚠ solution 말미 '{tail}' {cnt}회 반복 — 변형 필수")

    if opps and opps.most_common(1)[0][1] > len(blocks_so_far) * 0.25:
        top_opp, top_cnt = opps.most_common(1)[0]
        lines.append(f"⚠ opponent '{top_opp}' 독점 {top_cnt}/{len(blocks_so_far)} — 교체 필수")

    return "\n".join(lines)
```

### 5.2 주입 시점 (P-3은 생성 **전** 주입 — 생성 후가 아님)

```
배치 N 생산 시:
  1. blocks_so_far = batch_001 ~ batch_(N-1) 병합
  2. feedback = build_pattern_feedback(blocks_so_far)  ← 생성 전 경고
  3. 프롬프트 = phase0_context + feedback + "Block X~Y 생산"
  4. LLM 생성 → candidate.json
  5. Python auto-fix → fixed.json
  6. validate_v3 검사 ← 이건 생성 후 검증 (P-3과 다른 역할)
```

> **근거**: treatment-production-harness-v2.md §3.1 — "위 피드백은 장식이 아니라 **생성 전 경고**다."
> P-3의 목적은 LLM이 "이미 많이 쓴 패턴"을 인지한 상태에서 생성하는 것이지, 생성 후 사후 교정이 아님.

---

## §6. 기존 자산 마이그레이션 계획

### 6.1 즉시 이동 (1차)

| 원본 | 대상 | 방식 |
|------|------|------|
| `treatments/audit_reports/*` | `전처리_ssot/감사/tr/` | 이동 |
| `bible/audit_reports/*` | `전처리_ssot/감사/bi/` | 이동 |
| `treatments/*_batch_*` 24쌍 | `전처리_ssot/작품별/02_chaebol_allowance_zero/batch_log/` | 이동 |
| `docs/blockguide/실패작들/` | `전처리_ssot/감사/실패작_아카이브/` | 이동 |

### 6.2 하네스 사본 + 참조 문서 (1차)

| 대상 | 내용 |
|------|------|
| `전처리_ssot/하네스/` 6파일 | `docs/blockguide/` 원본 6개 사본 (SSOT·기획·생산v2·BI·TF-BH1·3pass감사) |
| `전처리_ssot/하네스/README.md` | 원본 경로 + "원본 변경 시 여기도 갱신" 동기화 규칙 |
| `전처리_ssot/장르_프로파일/README.md` | preset_registry.py + genre_schema_builder.py 참조 경로 |
| `전처리_ssot/소재뱅크/소재_카탈로그.md` | material_bank.db 경로 + 테이블 통계 + 쿼리 예시 |

### 6.3 신규 생성 (2차) — TF-PP2 F-07/F-08 수정

| 파일 | 내용 |
|------|------|
| `템플릿/phase0_template.json` | Phase 0 빈 껍데기 (preset_registry.py 스키마 기반) |
| `템플릿/tr_block_template.json` | TR 블록 1개 빈 껍데기 |
| `템플릿/bi_template.json` | BI 빈 껍데기 |
| `템플릿/work_config_template.yaml` | 작품별 설정 템플릿 |
| `검증/validate.py` | 통합 검증 CLI (tr_batch_harness에서 추출) |
| `검증/rules/*.yaml` | 검증 규칙 SSOT |
| `출고/export.py` | 출고 스크립트 (기존 scripts/ 래핑) |

### 6.4 유지 (변경 없음)

| 위치 | 이유 |
|------|------|
| `test_material/*.py` (빌드 스크립트) | 소재 수집은 전처리 밖. DB 빌드용 |
| `scripts/run_stage*_smoke.py` | 런타임 테스트, 전처리 무관 |
| `modules/core/stage0/` | Stage 0 런타임 코드, 전처리가 참조·확장할 SSOT |
| `treatments/*.json` (최종 TR) | 출고 결과물. 전처리에서 복사해 올 목적지 |
| `bible/*.json` (최종 BI) | 출고 결과물. 전처리에서 복사해 올 목적지 |

### 6.5 통합 대상 — 기존 자동화 자산 전수 인벤토리 (TF-PP1 P2-04)

> **기획안 1차에서 완전 누락된 41파일.** 새로 만들지 말고 기존 도구를 전처리 구조에 통합·리팩토링한다.

#### 즉시 통합 (전처리 핵심 기능)

| 파일 | 역할 | 전처리 매핑 |
|------|------|------------|
| `scripts/generate_tr_bibles.py` (496줄) | TR → BI 생성 | §F BI 생산 |
| `scripts/build_bi_from_phase0_and_tr.py` (563줄) | Phase0+TR → BI | §F BI 생산 |
| `scripts/process_and_audit_tr_bi_loop.py` (278줄) | 파이프라인 오케스트레이션 | §D~§G 루프 |
| `tools/treatment_builder.py` | TR 빌드 도구 | §D TR 생산 |
| `tools/bible_builder.py` | BI 빌드 도구 | §F BI 생산 |
| `tools/story_expander.py` | 컨셉→Bible/TR (Stage 0 원본) | §C Phase 0 |
| `tools/genre_library_builder.py` | 장르별 소재 라이브러리 | §B 소재 조회 |
| `tools/treatment_extractor.py` | TR 추출 도구 | §E TR 병합 |
| `tools2/apply_v3.py` + `apply_v3_pt2.py` | validate_v3 적용 | §3.4 검증 통합 |
| `tools2/reverse_bible.py` | BI 역추출 | §F BI 생산 |

#### 정리 대상 (산재 스크립트 → scripts/ 집약)

| 파일 | 처리 |
|------|------|
| `generate_empire_reborn_tr70.py` (루트) | `scripts/`로 이동 |
| `tools/0_json만들기.py` | 역할 확인 후 scripts/ 또는 폐기 |
| `tools/fix_future_items.py` | 역할 확인 후 scripts/ 또는 폐기 |

#### 참조 유지 (이동 불필요)

| 파일 | 이유 |
|------|------|
| `tools/make_BP.py`, `tools/db_porter.py` 등 | 런타임/유틸, 전처리 직접 연관 낮음 |
| `tools2/` 대시보드·비용계산 등 16파일 | 분석·시각화 도구, 전처리 밖 |

---

## §7. 작업 우선순위

### Phase 1 — 뼈대 + 검증 (즉시)

1. 폴더 구조 생성 (`전처리_ssot/` 하위 디렉토리)
2. 하네스 참조 문서 작성 (`하네스/README.md`에 원본 경로 목록)
3. 기존 배치 파일 + 감사 리포트 이동
4. `장르_프로파일/README.md` 작성 (preset_registry.py 참조 안내)
5. `tools/` + `tools2/` + `scripts/` 전수 인벤토리 → 통합 대상 확정
6. **검증: 참조 경로 전수 접근 테스트**
7. **검증: 이동된 파일 UTF-8 파싱 + 원본 해시 대조**
8. **검증: 기존 스크립트 출력 경로가 이동으로 깨지지 않는지 확인**

### Phase 2 — 검증 통합

6. `검증/validate.py` — tr_batch_harness.py에서 validate 로직 추출
7. `검증/rules/*.yaml` — 하네스 문서의 규칙을 YAML로 SSOT화
8. 기존 `tr_batch_harness.py`가 `검증/validate.py`를 import하도록 리팩토링

### Phase 3 — 생산 자동화

9. `출고/export.py` — TR/BI 파일 UTF-8 검증 + 목적지 복사
10. 패턴 피드백 함수 (P-3) 구현
11. `작품별/_template/` 신규 작품 부트스트랩 도구

### Phase 4 — 장르 확장

12. 나머지 장르 프로파일 9개 작성
13. 장르별 `genre_ext` 템플릿 작성
14. 대체역사 등 특수 프로파일 연동

---

## §8. 전처리 vs 런타임 경계

> **[TF-PP1 P1-02 수정]** Stage 0은 TR/BI를 로드하지 않고 **생성**하는 모듈.
> 전처리는 Stage 0의 **오프라인 대체제** — 동일 출력물(TR/BI)을 사람+LLM 협업으로 정밀 생산한다.
> 양자는 **대체 관계**이지 입출력 관계가 아님.

```
┌───────────────────────────┐     ┌───────────────────────────┐
│       전처리 (offline)      │     │       런타임 (online)       │
│                           │     │                           │
│  소재뱅크 조회              │     │  Stage 0 (컨셉→Bible/TR    │
│  Phase 0 설계              │     │    프리셋 기반 자동 생성)    │
│  TR 생산 (배치)             │     │         ↕ 양립 가능         │
│  BI 생산                   │     │  Stage 2 (Arc 생성)        │
│  검증 + 감사               │     │  Stage 3 (Blueprint)      │
│  출고                      │     │  Stage 4 (원고)            │
│                           │     │  Director 심사             │
│  출력:                     │     │  Advisory 체인             │
│  treatments/*.json ────────┼────▶│  Stage 2 직접 로드          │
│  bible/*.json ─────────────┼────▶│  Stage 2 직접 로드          │
└───────────────────────────┘     └───────────────────────────┘

경계 원칙:
- 전처리 = Stage 0의 오프라인 대체제 (정밀 생산, 사람+LLM 협업)
- Stage 0 = 빠른 프로토타이핑용 (컨셉 → 즉석 Bible/TR 자동 생성)
- 전처리 출력(TR/BI)은 Stage 0을 우회하여 Stage 2에 직접 투입됨
- 런타임은 Python 자동화 기반 (Stage 2~4 파이프라인)
- 양자 택일이 아님: Stage 0으로 빠르게 시작 → 전처리로 정밀 교체 가능
```

---

## §9. 성공 기준

| 기준 | 측정 |
|------|------|
| 신규 작품 착수 시간 | "뭘 먼저 해야 하지?" 없이 `전처리_ssot/README.md` → 즉시 시작 |
| Phase 0 완성도 | opponent 배치 매트릭스 + weakness 사전설계 포함 (P-1, P-2) |
| TR 생산 1회차 PASS율 | validate_v3 P0 위반 0건 달성 (현재: 12건+ → 0건) |
| 검증 SSOT | "어느 규칙이 진짜인가?" 질문 소멸 → `검증/rules/*.yaml` 단일 참조 |
| 감사 리포트 정리 | 출력 폴더(treatments/bible)에 감사 파일 0개 → 전처리_ssot/감사/로 분리 |
| 장르 확장 | 신규 장르 착수 시 프로파일 YAML 1개 추가 → Phase 0부터 즉시 가동 |

---

## §10. 미결 사항 (2차 기획에서 결정)

1. ~~**심링크 vs 사본**~~ → **사본 + 동기화로 결정** (TF-PP2 재검토). 생산기지에 매뉴얼 물리 배치 필수
2. **소재뱅크 확장** — 현재 투자물 특화 DB. 장르 확장 시 테이블 추가 vs 별도 DB
3. **빌드 스크립트 리팩토링** — `scripts/build_*.py` 부분 재사용 중(tr_batch_harness 3함수 공유). Phase 0 설계·블록 구성 로직의 공통 빌더 추출 여부
4. **TR 번호 체계** — 현재 `02_`, `05_`, `08_` 비연속 → 연번 정리 vs 현상 유지
5. **git 추적 범위** — `material_bank.db` 14.2MB + batch JSON들 git에 포함 vs .gitignore
6. **tools/ + tools2/ 정리** — 전처리 핵심 도구 10개 통합 후, 나머지 31파일의 폐기/유지/이동 판단
7. **검증 전환 전략** — `tr_batch_harness.validate_candidate()` + `tools2/apply_v3.py` → `검증/validate.py` 통합 시, 기존 import 경로 호환성 유지 방법
8. **장르 프로파일 YAML 외부화** — preset_registry.py 40KB를 config/presets/*.yaml로 분리할 경우, 전처리와 런타임 공유 경로 설계

---

## §12. 투입 자원 명세 (Bill of Materials) — TF-PP2 F-02

### 필수 투입

| # | 자원 | 위치 | 형식 | 최소 요건 |
|---|------|------|------|----------|
| 1 | 작품 컨셉 | 운영자 작성 | 텍스트 | 장르 + 주인공명 + 유형 + 핵심 갈등 + 성장 자원 + 블록 수 |
| 2 | 소재 뱅크 | `test_material/material_bank.db` | SQLite | 이벤트 10건 + NPC 원형 8건 + 위기 5건 |
| 3 | LLM API | Gemini (models.yaml) | API Key | ~30회 호출/작품, ~$5~15 |
| 4 | 하네스 문서 | `docs/blockguide/` | Markdown | 4개 필수 + 2개 선택 |
| 5 | Python 환경 | 로컬 | 3.10+ | json, re, collections (표준 라이브러리) |

### 선택 투입

| # | 자원 | 용도 |
|---|------|------|
| 6 | 골든 TR/BI (01번) | 성공 사례 참조 |
| 7 | 실패작 아카이브 | 반면교사 (어떤 패턴이 실패하는지) |
| 8 | TF-BH1 문서 | validate_v3 심화 규칙 R27~R33 |

### 산출물

| 출력 | 경로 | 크기 |
|------|------|------|
| TR 70블록 JSON | `treatments/NN_work_id_tr_block_070_draft.json` | ~300~400KB |
| BI JSON | `bible/NN_bi_work_id.json` | ~500~650KB |
| 배치 이력 | `작품별/NN/batch_log/` | ~48파일 (24쌍) |
| 감사 리포트 | `감사/cross/` | ~3~5파일 |

---

## §13. 운영자 SOP (Standard Operating Procedure) — TF-PP2 F-01

> 신규 작품 1개를 처음부터 출고까지 생산하는 전체 절차.
> 예상 소요: ~20시간 (§D TR 생산이 60%).

### STEP 0. 작업 공간 생성 (~5분)

```
전처리_ssot/작품별/_template/ 복사 → 작품별/NN_work_id/
work_config.yaml 작성 (장르, 주인공, 블록 수)
progress.json 초기화: {"current_step": "STEP_1", "blocks_done": 0}
```

### STEP 1. 하네스 읽기 (~30분)

```
1. docs/blockguide/SSOT_blockguide-integrated-order.md → 단계 판정
2. docs/blockguide/treatment-planning-harness.md → 11대 원칙 + 18단계
3. modules/core/stage0/preset_registry.py → 장르 필드 확인
4. modules/core/genre_schema_builder.py → genre_ext 구조 확인
```

### STEP 2. 소재 조회 (~1시간)

```
python test_material/query_material_bank.py
  → 키워드: 장르 핵심어
  → 최소 수집: 이벤트 10건 + NPC 원형 8건 + 위기 5건
  → 출력: 작품별/NN/소재_수집.json
```

### STEP 3. Phase 0 설계 (~2시간)

```
treatment-planning-harness.md 18단계 순서 실행
필수 산출물:
  - opponent_allocation_matrix: 7아크 × 2~3명 = 8명+ 고유 (P-1)
  - weakness_predesign: opponent별 2종+ = 16종+ (P-2)
  - sector_roadmap: 70블록 × sector 배정
  - npc_timeline + foreshadow_map
출력: 작품별/NN/phase0_design.json
```

### STEP 4. TR 생산 — 배치 순차 (~12시간)

```
배치 크기: 3블록 (안전 모드), Arc 내 3배치 연속 PASS → 5블록 승격
배치 1개 사이클 (~30분):
  4a. 패턴 피드백 생성 (P-3) — build_pattern_feedback(blocks_so_far)
  4b. 프롬프트 조립 = phase0 + 패턴피드백 + "Block X~Y 생산"
  4c. LLM 생성 → batch_NNN_candidate.json
  4d. Python auto-fix → batch_NNN_fixed.json
  4e. validate_v3 검사 → P0 위반 0건이면 PASS, 있으면 4a로 복귀
  4f. 배치 로그 기록 → 작품별/NN/batch_log/

Arc 전환 시: 배치 크기 3블록으로 강제 리셋 (P-5)
3연속 실패 시: Phase 0 해당 Arc 재설계 검토
```

### STEP 5. TR 병합 + 전체 검증 (~30분)

```
batch_001~NNN fixed.json 병합 → tr_block_070_draft.json
전체 validate_v3 재실행 (병합 시 새 패턴 발생 가능)
P0 위반 → 해당 배치로 복귀
```

### STEP 6. BI 생산 (~2시간)

```
bi-production-harness-v1.md 5-Phase 실행
기존 도구: python scripts/build_bi_from_phase0_and_tr.py
  --phase0 작품별/NN/phase0_design.json
  --tr 작품별/NN/tr_block_070_draft.json
  --output 작품별/NN/bi_draft.json
```

### STEP 7. 교차 감사 (~2시간)

```
5-pass BI 감사: python scripts/audit_bi_5pass.py
3-pass TR 감사: TF-BH1 §8 출구 게이트 기준
TR↔BI 교차: python scripts/process_and_audit_tr_bi_loop.py
감사 리포트 → 감사/cross/NN_work_id_audit.md
```

### STEP 8. 출고 (~15분)

```
출고 게이트 체크리스트:
  □ validate_v3 P0 위반 0건
  □ 5-pass BI 감사 전항 PASS
  □ TR↔BI 교차 검증 PASS
  □ UTF-8 인코딩 확인
  □ JSON 파싱 정상
  □ opponent 고유 8명+ (25% 이하 독점)
  □ weakness 16종+ (아크 내 중복 없음)
  □ solution 말미 20자 반복 3회 이하
  □ content 평균 밀도 500자+
  □ block_id 1~70 연번 정상

파일 복사:
  tr → treatments/NN_work_id_tr_block_070_draft.json
  bi → bible/NN_bi_work_id.json
progress.json: {"current_step": "DONE", "blocks_done": 70, "exported": true}
```

---

## §14. 품질 다층 방어 — TF-PP2 F-04

```
Layer 1: Python 자동 검증 (매 배치)
  ├── validate_v3: 구조 + 패턴 R27~R33
  ├── build_pattern_feedback: opponent/weakness/solution 반복 감지
  └── UTF-8 + JSON 파싱 무결성

Layer 2: LLM 교차 검증 (아크 완료 시)
  ├── 장르 정합성: "이 블록이 {장르}로서 성립하는가?"
  ├── 수치 현실성: capital 변화율 현실적인가?
  └── NPC 일관성: 사망 NPC 재등장, 이름 변경 없는가?

Layer 3: 사람 감사 (전체 완료 후)
  ├── 5-pass BI 감사
  ├── 3-pass TR 감사
  └── TR↔BI 교차 감사

임계값:
  Layer 1 FAIL → 같은 배치 즉시 재작업
  Layer 2 FAIL → 해당 아크 Phase 0 재설계 검토
  Layer 3 FAIL → 전체 감사 문서화 후 대응 결정
```

---

## §15. 처리 시간 및 병목 분석 — TF-PP2 F-03

| 공정 | 예상 시간 | 비중 | 병목 요인 |
|------|----------|------|----------|
| STEP 0 작업 공간 | 5분 | <1% | — |
| STEP 1 하네스 읽기 | 30분 | 3% | 사람 읽기 속도 |
| STEP 2 소재 조회 | 1시간 | 5% | 쿼리 설계 + 결과 선별 |
| STEP 3 Phase 0 | 2시간 | 10% | LLM 1회 + 사람 검토 |
| **STEP 4 TR 생산** | **12시간** | **60%** | **24배치 × LLM생성 + 검증 루프** |
| STEP 5 TR 병합 | 30분 | 3% | Python 자동 |
| STEP 6 BI 생산 | 2시간 | 10% | LLM + 동기화 |
| STEP 7 교차 감사 | 2시간 | 10% | 5-pass + 3-pass |
| STEP 8 출고 | 15분 | 1% | 체크리스트 |
| **합계** | **~20시간** | 100% | **STEP 4가 핵심 병목** |

**병목 최적화 방향:**
- 배치 크기 3→5 승격 조건 완화 (현재: 3연속 PASS)
- validate_v3 피드백을 프롬프트에 정밀 주입 → 1회 PASS율 향상
- Phase 0 opponent/weakness 사전 설계 충실 → 재작업 감소

---

## §11. TF-PP1 감리 수정 이력

> 이 절은 `01_TF_전처리기획_재감리_3pass.md` 감리 결과에 따른 수정 내역을 기록한다.

| TF ID | 심각도 | 수정 내용 | 관련 절 |
|-------|--------|----------|--------|
| P1-01 | P0 | P-3 주입 순서: LLM 생성 후 → 생성 **전**으로 수정 | §2, §5.2 |
| P1-02 | P0 | Stage 0 역할: "로드" → "생성". 전처리 = Stage 0 대체제로 재정의 | §8 |
| P3-01 | P0 | 장르 프로파일: 별도 YAML → preset_registry.py 단일 참조 | §4.1 |
| P2-04 | P0 | 기존 자산 41파일 인벤토리 추가 (tools 15 + tools2 22 + scripts 3 + 루트 1) | §6.5 신설 |
| P2-01 | P1 | 모놀리스 진단: "재사용 불가" → "부분 재사용 + 복사-수정 혼재" | §0 핵심문제 2 |
| P2-02 | P1 | Phase 0 템플릿: "없음" → "preset_registry.py 존재, 전처리 확장만 필요" | §0 as-is 표 |
| P2-03 | P2 | 감사 섞임: "섞임" → "TR/BI별 분리됨, 중앙화 시 편의 향상 가능" | §0 as-is 표 |
| P2-05 | P1 | 심링크 → 사본+동기화 (생산기지에 매뉴얼 물리 배치) | §3.1 |
| P1-03 | P1 | opponent 필드: dict 전용 → dict/str 양쪽 호환 | §5.1 |
| P3-04 | P2 | Phase 1 검증: 스텝 6~8 검증 절차 추가 | §7 Phase 1 |

---

*끝.*
