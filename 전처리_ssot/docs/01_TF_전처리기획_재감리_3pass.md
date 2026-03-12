# TF-PP1: 전처리 SSOT 1차 기획안 재감리 (3-Pass)

> 감사 대상: `전처리_ssot/00_전처리_SSOT_1차_기획안.md`
> 감사 방식: 3-Pass (구조 → 사실 교차검증 → 설계 타당성)
> 감사 기준: 원본 코드·파일·하네스 문서와의 정합성
> 작성일: 2026-03-12

---

## PASS 1 — 구조 감사 (문서가 논리적으로 성립하는가)

### P1-01. 파이프라인 흐름도 §2 — P-3 주입 순서 오류 ❌

**기획안 주장 (§2, §5.2):**
> §D. TR 생산 배치마다:
> 1. LLM 생성 → candidate.json
> 2. 패턴 피드백 주입 (P-3)

**실제 (treatment-production-harness-v2.md §3.1, harness_3pass_audit_and_patch.md P-3):**
> "위 피드백은 장식이 아니라 **생성 전 경고**다."
> "이미 많이 쓴 패턴을 이번 배치에서 다시 쓰지 마라"를 자연어로 먼저 이해한 뒤 JSON을 쓴다.

**문제:** P-3 패턴 피드백은 LLM 생성 **전**에 프롬프트에 주입해야 한다. 기획안은 Step 2에 배치 → LLM이 이미 생성한 후 피드백을 줘봤자 소용없다.

**왜 이게 중요한가:**
- P-3의 존재 이유 자체가 RC-3 ("생산 프롬프트에 패턴 피드백 없음") 해소
- LLM 생성 후 피드백 → 그건 검증(validate)이지 피드백이 아님
- 이 순서 오류가 실행되면 P-3 자체가 무효화 → RC-3 미해소 → 동일 실패 반복

**심각도:** **P0 — 파이프라인 설계 결함**

**수정:**
```
§D. TR 생산 배치마다:
  1. blocks_so_far로 패턴 피드백 생성 (P-3)
  2. 프롬프트 = phase0 + 패턴 피드백 + "Block X~Y 생산"
  3. LLM 생성 → candidate.json
  4. Python auto-fix → fixed.json
  5. validate_v3 검사
  6. P0 위반 → 같은 배치 재작업
  7. PASS → 다음 배치
```

---

### P1-02. §8 전처리 vs 런타임 경계 — Stage 0 역할 오인 ❌

**기획안 주장 (§8):**
> 전처리 출력 = 런타임 입력
> 전처리에서 만든 TR/BI가 런타임 Stage 0에서 **로드**됨

**실제 (modules/core/stage0/__init__.py L216-251):**
```python
def generate_from_concept(self, concept: str):
    expander = StoryExpander(...)
    self.bible = expander.generate_bible(...)   # ← 생성
    self.treatment = expander.generate_treatment(60)  # ← 생성
    expander.save_all(str(output_dir))
```

**실제 데이터 흐름:**
```
Stage 0 → Bible + Treatment 생성 → Stage 2에서 소비
```

Stage 0은 TR/BI를 **로드하는 게 아니라 생성**한다. 전처리(오프라인)에서 만든 TR/BI는 Stage 0을 **우회**하여 Stage 2에 직접 투입되거나, Stage 0의 입력 컨셉으로 사용된다.

**왜 이게 중요한가:**
- 경계를 잘못 그으면 전처리 출력물이 어디로 가야 하는지 모호해짐
- "Stage 0에서 로드됨"이 맞다면 Stage 0에 로더를 만들어야 하고
- "Stage 0을 대체함"이 맞다면 Stage 2 직접 투입 경로를 만들어야 함
- 두 설계의 구현 비용이 전혀 다름

**심각도:** **P0 — 아키텍처 경계 오류**

**수정:**
```
전처리(offline)                    런타임(online)

  소재뱅크 조회                      Stage 0 (프리셋 → Bible/TR 생성)
  Phase 0 설계                              ↕ 양립 가능
  TR 생산 (배치)      ─── 전처리 TR/BI는 Stage 0을 대체하거나
  BI 생산                  Stage 0의 시드로 사용됨
  검증 + 감사
  출고                     Stage 2 (Arc 생성) ← TR/BI 소비
                           Stage 3 (Blueprint)
출력:                      Stage 4 (원고)
  treatments/*.json ──────▶ Stage 2 직접 로드
  bible/*.json ───────────▶ Stage 2 직접 로드
```

**경계 재정의:**
- 전처리 = Stage 0의 **오프라인 대체제** (동일 출력물을 사람+LLM 협업으로 정밀 생산)
- Stage 0 = 빠른 프로토타이핑용 (컨셉 → 즉석 Bible/TR)
- 양자는 **대체 관계**이지 입출력 관계가 아님

---

### P1-03. §5.1 피드백 함수 — opponent 필드 경로 불일치 ⚠️

**기획안 주장 (§5.1 build_pattern_feedback):**
```python
opps = Counter(
    b.get("genre_ext", {}).get("opponent", {}).get("name", "")
    for b in blocks_so_far
)
```

**실제 TR JSON (02_chaebol_allowance_zero Block 1):**
```json
"genre_ext": {
    "opponent": {
        "name": "노현주",
        "weakness_exploited": "..."
    }
}
```

여기서는 `opponent`가 dict이므로 `.get("opponent", {}).get("name", "")` 패턴이 맞다.

**그러나 01_골든_sample Block 2:**
```json
"genre_ext": {
    "opponent": "박성호 PB"
}
```

여기서는 `opponent`가 **문자열**이므로 `.get("name", "")` 호출 시 **AttributeError** 발생.

**왜 이게 중요한가:**
- 작품마다 스키마가 다름 → 피드백 함수가 한 작품에서만 작동하고 다른 작품에서 크래시
- 전처리 SSOT가 **범장르 공통 도구**를 표방하면서 특정 스키마에 하드코딩

**심각도:** **P1 — 호환성 결함**

**수정:**
```python
def _get_opponent_name(block: dict) -> str:
    opp = block.get("genre_ext", {}).get("opponent")
    if isinstance(opp, dict):
        return opp.get("name", "")
    if isinstance(opp, str):
        return opp
    return ""
```

---

### P1-04. §1 폴더 구조 — `출고/` 와 `감사/` 분리가 파이프라인 순서와 불일치 ⚠️

**기획안 §2 파이프라인:**
> §G 교차 감사 → §H 출고 게이트

**기획안 §1 폴더 구조:**
```
├── 출고/       ← 맨 끝에서 두 번째
└── 감사/       ← 맨 끝
```

**문제:** 폴더 순서가 파이프라인 순서와 역전됨. 감사가 출고보다 뒤에 있으면, 실행자가 감사 없이 출고부터 보게 될 위험.

**심각도:** **P2 — 가독성**

**수정:** 폴더명에 번호 프리픽스 추가하거나, `감사/`를 `출고/` 앞에 배치.

---

## PASS 2 — 사실 교차검증 (주장이 실제와 일치하는가)

### P2-01. §0 "빌드 스크립트 재사용 불가" — 사실과 불일치 ❌

**기획안 주장 (§0, 핵심문제 2):**
> `build_chaebol_allowance_zero_assets.py` 82KB, `generate_defense_defect_engineer_assets.py` 158KB → 작품마다 거대 스크립트 1개씩 복사-수정

**실제 (generate_defense_defect_engineer_assets.py L20-25):**
```python
from scripts.tr_batch_harness import (
    build_open_foreshadow_ledger,
    render_report,
    validate_candidate,
)
```

**사실:** `tr_batch_harness.py`가 공유 유틸리티로 이미 사용 중. `validate_candidate`, `build_open_foreshadow_ledger`, `render_report` 3개 함수가 작품 간 재사용됨.

**왜 이게 중요한가:**
- "재사용 불가"라는 진단 위에 "공통 빌더 추출" 설계를 세우면 → 이미 존재하는 공유 레이어를 무시하고 중복 구현할 위험
- 기획의 핵심 동기 3개 중 1개(모놀리스)가 과장됨 → 기획 필요성 자체의 설득력 약화

**심각도:** **P1 — 진단 오류**

**수정:** "재사용 불가" → "부분 재사용 (tr_batch_harness 3함수 공유). 그러나 Phase 0 설계·블록 데이터 구성·BI 생성 로직은 여전히 작품별 복사-수정 구조"

---

### P2-02. §0 "Phase 0 설계 표준 템플릿 없음" — 사실과 불일치 ❌

**기획안 주장 (§0 as-is 표):**
> Phase 0 설계: 작품별 `_phase0_design.json` 산재. **표준 Phase 0 템플릿 없음**

**실제:**
1. `modules/core/stage0/preset_registry.py` (40KB) — 장르별 필드 정의 + 프리셋 조합 시스템
2. `modules/core/stage0/story_expander.py` (20KB) — Phase 0 출력 생성기
3. `treatments/chaebol_allowance_zero_phase0_design.json` — 구조화된 Phase 0 설계 JSON (arcs[], block_slots[], opponents[], npc_timeline 등)

**사실:** Stage 0 모듈에 프리셋 기반 템플릿 시스템이 **이미 구현되어 있음**. `preset_registry.py`가 장르별 필드를 정의하고, `story_expander.py`가 이를 조합하여 Phase 0 JSON을 생성함.

**왜 이게 중요한가:**
- "없음"이라고 진단하면 → 새로 만들겠다는 설계가 나옴
- 실제로는 **이미 있는 것과 중복 구현** → Stage 0 모듈과 전처리가 같은 일을 두 번
- CLAUDE.md에도 `Stage 0 (프리셋 로드)` + `preset_registry.py`가 명시됨

**심각도:** **P1 — 기존 자산 누락**

**수정:** "표준 템플릿 없음" → "Stage 0 모듈에 프리셋 기반 템플릿 존재 (preset_registry.py + story_expander.py). 전처리는 이 시스템을 **확장하거나 재사용**해야 하며, 별도 구축하면 안 됨"

---

### P2-03. §0 "감사 결과가 섞임" — 과장 ⚠️

**기획안 주장 (§0 as-is 표):**
> 감사 리포트: `bible/audit_reports/`, `treatments/audit_reports/` — 출력 폴더에 감사 결과가 **섞임**

**실제:**
- `treatments/audit_reports/` — TR 배치 감사 63+파일 (batch별 audit, check, merge)
- `bible/audit_reports/` — BI 감사 3파일 (5pass, retry_vs_failed)

**사실:** 이미 TR/BI 별로 **분리 관리**됨. "섞임"이라는 표현은 부정확. 출력 폴더 안에 감사 서브폴더가 있는 구조는 관행적으로 일반적.

**왜 이게 중요한가:**
- "섞여 있다" → "분리해야 한다"는 설계 동기가 됨
- 실제로는 이미 분리되어 있으므로 이동의 ROI가 낮음
- 이동 시 기존 스크립트 (`audit_bi_5pass.py` 등)의 출력 경로도 변경해야 → 불필요한 작업 발생

**심각도:** **P2 — 과장 진단**

**수정:** "섞임" → "출력 폴더 안에 audit_reports/ 서브디렉토리로 존재. 분리는 되어 있으나, 전처리 공정 관점에서 감사 리포트를 중앙화하면 관리 편의 향상 가능"

---

### P2-04. §6 마이그레이션 — 누락된 기존 자산 대규모 ❌

**기획안 §6에 언급 없는 파일:**

#### A. scripts/ 내 자동화 스크립트 (3개, 1,337줄)

| 파일 | 크기 | 역할 |
|------|------|------|
| `scripts/generate_tr_bibles.py` | 496줄 | TR에서 독립 Bible JSON 생성 |
| `scripts/build_bi_from_phase0_and_tr.py` | 563줄 | Phase 0 + TR → BI 빌드 |
| `scripts/process_and_audit_tr_bi_loop.py` | 278줄 | TR→BI 파이프라인 오케스트레이션 + 감사 루프 |

#### B. tools/ 디렉토리 (15파일 — 기획안에서 완전 누락)

| 파일 | 전처리 연관도 | 역할 |
|------|-------------|------|
| `tools/treatment_builder.py` | **직접** | TR 빌드 도구 |
| `tools/story_expander.py` | **직접** | 컨셉 → Bible/TR 확장 (Stage 0 원본) |
| `tools/genre_library_builder.py` | **직접** | 장르별 소재 라이브러리 빌드 |
| `tools/bible_builder.py` | **직접** | BI JSON 빌드 |
| `tools/treatment_extractor.py` | **직접** | TR 추출 도구 |
| `tools/0_json만들기.py` | 관련 | JSON 생성 유틸 |
| `tools/fix_future_items.py` | 관련 | 미래 아이템 오류 수정 |
| `tools/normalize_arcs_db.py` | 관련 | Arc DB 정규화 |
| `tools/db_porter.py` | 참조 | DB 마이그레이션 |
| `tools/make_BP.py` | 참조 | Blueprint 생성 |
| 기타 5파일 | 낮음 | 시각화/PPT/concat 유틸 |

#### C. tools2/ 디렉토리 (22파일 — 기획안에서 완전 누락)

| 파일 | 전처리 연관도 | 역할 |
|------|-------------|------|
| `tools2/apply_v3.py` | **직접** | validate_v3 적용 스크립트 |
| `tools2/apply_v3_pt2.py` | **직접** | validate_v3 2차 적용 |
| `tools2/reverse_bible.py` | **직접** | BI 역추출 |
| `tools2/sanitize_reference.py` | 관련 | 참조 정제 |
| `tools2/validation_test_harness.py` | 관련 | 검증 테스트 하네스 |
| `tools2/automate_snack.py` | 관련 | 자동화 도구 |
| 기타 16파일 | 낮음 | 대시보드/비용계산/테스트/문서 |

#### D. 루트 빌드 스크립트 (1개)

| 파일 | 역할 |
|------|------|
| `generate_empire_reborn_tr70.py` | scripts/ 밖에 있는 TR70 생성 스크립트 |

**합계:** scripts 3파일 + tools 15파일 + tools2 22파일 + 루트 1파일 = **41파일의 전처리 관련 코드**가 기획안에서 완전히 누락.

**왜 이게 중요한가:**
- §F "BI 생산"과 §G "교차 감사"의 실행 코드가 **이미 존재**하는데, 기획안은 이를 모르고 새로 만들겠다고 함
- `process_and_audit_tr_bi_loop.py`는 전처리 파이프라인의 §D~§G를 이미 오케스트레이션하는 스크립트
- `tools/treatment_builder.py`, `tools/bible_builder.py`는 전처리의 핵심 기능 그 자체
- `tools2/apply_v3.py`는 검증 SSOT 논의(§3.4)에서 반드시 포함되어야 할 기존 코드
- 이 41개를 무시하고 새로 만들면 → 대규모 중복 구현 + 기존 도구와의 충돌

**심각도:** **P0 — 기존 자산 대규모 누락 (P1에서 상향)**

**수정:** §6에 추가:
```
### 6.5 통합 대상 (기존 자동화 자산 — 전수 인벤토리)

■ 즉시 통합 (전처리 핵심)
| 파일 | 역할 | 전처리 SSOT 매핑 |
|------|------|-----------------|
| scripts/generate_tr_bibles.py | TR → BI 생성 | §F BI 생산 |
| scripts/build_bi_from_phase0_and_tr.py | Phase0+TR → BI | §F BI 생산 |
| scripts/process_and_audit_tr_bi_loop.py | 파이프라인 루프 | §D~§G 오케스트레이션 |
| tools/treatment_builder.py | TR 빌드 | §D TR 생산 |
| tools/bible_builder.py | BI 빌드 | §F BI 생산 |
| tools/story_expander.py | 컨셉→Bible/TR | §C Phase 0 |
| tools/genre_library_builder.py | 장르 소재 | §B 소재 조회 |
| tools/treatment_extractor.py | TR 추출 | §E TR 병합 |
| tools2/apply_v3.py + pt2 | validate_v3 적용 | §3.4 검증 통합 |
| tools2/reverse_bible.py | BI 역추출 | §F BI 생산 |

■ 정리 대상 (루트 산재 스크립트)
| 파일 | 처리 |
|------|------|
| generate_empire_reborn_tr70.py | scripts/로 이동 |

→ 새로 만들지 말고, 기존 도구를 전처리_ssot/ 구조에 맞게 통합·리팩토링
```

---

### P2-05. §3.1 심링크 — Windows 환경 검증 부재 ⚠️

**기획안 주장:**
> 결정: 심링크 (symlink)
> Windows에서 mklink 또는 상대경로 참조

**실제:**
- 프로젝트 전체에 symlink **0개** — 한 번도 사용된 적 없음
- Windows 11에서 mklink는 **관리자 권한** 또는 **개발자 모드** 필요
- git은 symlink를 기본적으로 텍스트 파일로 저장 (Windows) → 다른 머신에서 클론 시 깨짐

**왜 이게 중요한가:**
- "심링크로 하겠다"는 결정이 실행 불가능할 수 있음
- 실패 시 대안(§10.1에 언급)으로 전환하면 1차 구현 후 재작업
- Windows + git에서 symlink는 알려진 고통점

**심각도:** **P1 — 실행 가능성 미검증**

**수정:** 심링크 대신 다음 중 택 1:
1. **상대경로 참조 문서** — `하네스/README.md`에 "원본 경로: `../../docs/blockguide/...`" 기재
2. **하드카피 + git hook** — 원본 변경 시 자동 복사
3. **심링크 시도 → 실패 시 1번 폴백** (§10에서 2차로 미루지 말고 Phase 1에서 즉시 검증)

---

## PASS 3 — 설계 타당성 감사 (이렇게 해야 하는 이유가 있는가)

### P3-01. §4 장르 프로파일 YAML — Stage 0 preset_registry.py와 이중 관리 위험 ❌

**기획안 설계:**
```
장르_프로파일/
├── _common.yaml         ← 공통 코어
├── investment.yaml      ← 투자물
├── wuxia.yaml           ← 무협
└── ...
```

**기존 시스템:**
```
modules/core/stage0/preset_registry.py  (40KB)
  ← 장르별 프리셋 정의 (필드, 해석, 조합 규칙)
  ← 런타임에서 Stage 0이 사용
```

**문제:** 기획안의 `장르_프로파일/*.yaml`과 기존 `preset_registry.py`가 **동일한 정보를 다른 형식으로 관리**하게 됨.

- `investment.yaml`의 `genre_ext_fields.required: [capital_before, capital_after, opponent, business_sector]`
- `preset_registry.py`의 투자물 프리셋 필드 정의

둘 중 하나가 업데이트되고 다른 하나가 안 되면 → 전처리에서 만든 TR이 런타임에서 안 읽히는 사고.

**왜 이렇게 하면 안 되는가 (근거):**
1. **SSOT 위반** — 같은 정보의 출처가 2개 → "어느 게 진짜?" 문제 재발 (기획안 §0 핵심문제 3과 동일 패턴)
2. **CLAUDE.md 대원칙** — "검증 이중화"를 해소하겠다면서 "프로파일 이중화"를 새로 만드는 모순
3. **유지보수 비용** — 장르 추가 시 YAML + preset_registry.py 두 곳 수정 필요

**심각도:** **P0 — SSOT 위반**

**수정:** 장르 프로파일을 새로 만들지 말고:
```
장르_프로파일/
└── README.md  ← "장르 프로파일 SSOT는 modules/core/stage0/preset_registry.py
                   전처리에서도 이 모듈을 import하여 사용한다.
                   장르별 genre_ext 스키마는 modules/core/genre_schema_builder.py 참조."
```

또는 `preset_registry.py`를 YAML 외부화하되, **전처리와 런타임이 같은 YAML을 읽도록** 단일 참조점 유지:
```
config/presets/
├── _common.yaml
├── investment.yaml
└── ...

modules/core/stage0/preset_registry.py → config/presets/ 로드
전처리_ssot/ → config/presets/ 참조
```

---

### P3-02. §1 검증 YAML SSOT — 기존 validate_candidate()와의 관계 미정의 ⚠️

**기획안 설계 (§3.4):**
> 규칙을 `검증/rules/*.yaml`로 SSOT화
> `검증/validate.py`가 YAML 읽어서 실행

**기존 시스템:**
- `scripts/tr_batch_harness.py` L736+ — `validate_candidate()` 함수 (200+줄)
- 이미 작품 빌드 스크립트에서 import하여 사용 중 (P2-01에서 확인)

**문제:** 새 `검증/validate.py`를 만들면:
1. 기존 `tr_batch_harness.validate_candidate()`는 어떻게 되나?
2. 두 곳에서 검증 → 결과 불일치 가능
3. 기존 빌드 스크립트가 `from scripts.tr_batch_harness import validate_candidate` → 경로 변경 필요

**왜 이게 중요한가:**
- "검증 이중화" 해소가 기획 동기인데, 해소하면서 **새로운 이중화**를 만들면 본말전도
- 올바른 접근: `tr_batch_harness.py`에서 validate 로직을 **추출**하여 `검증/validate.py`로 이동 + `tr_batch_harness.py`가 새 위치를 import

**심각도:** **P1 — 전환 전략 미정의**

**수정:** §3.4에 전환 전략 추가:
```
1. tr_batch_harness.py에서 validate_candidate() 추출 → 검증/validate.py
2. tr_batch_harness.py는 from 전처리_ssot.검증.validate import validate_candidate
3. 기존 빌드 스크립트 import 경로 유지 (tr_batch_harness가 re-export)
4. 규칙 YAML은 validate.py가 읽되, 하드코딩 규칙과 1:1 매핑 검증
```

---

### P3-03. §6.1 감사 리포트 이동 — 기존 스크립트 출력 경로 파괴 ⚠️

**기획안 설계 (§6.1):**
> `treatments/audit_reports/*` → `전처리_ssot/감사/tr/` 이동
> `bible/audit_reports/*` → `전처리_ssot/감사/bi/` 이동

**기존 시스템:**
- `scripts/audit_bi_5pass.py` — BI 감사 결과를 `bible/audit_reports/`에 저장
- `scripts/process_and_audit_tr_bi_loop.py` — TR 감사 결과를 `treatments/audit_reports/`에 저장
- `scripts/tr_batch_harness.py` — 배치 감사 결과를 `treatments/audit_reports/`에 저장

**문제:** 파일 이동 시 3개 스크립트의 출력 경로를 모두 변경해야 함. 변경하지 않으면 새 감사 결과가 여전히 옛 경로에 생성 → 전처리_ssot/감사/는 죽은 아카이브가 됨.

**왜 이게 중요한가:**
- 이동만 하고 스크립트 수정을 빠뜨리면 → "감사 결과가 두 곳에 생기는" 새로운 혼란
- 이동 비용 대비 효과가 불분명 (P2-03에서 이미 정리되어 있음 확인)

**심각도:** **P1 — 부작용 미고려**

**수정:** 두 가지 중 택 1:
1. **이동 + 스크립트 3개 출력 경로 변경** (완전 전환)
2. **이동하지 않고 참조만** — `전처리_ssot/감사/README.md`에 "감사 리포트 위치: treatments/audit_reports/, bible/audit_reports/" 기재

---

### P3-04. §7 작업 우선순위 — Phase 1에 검증 없는 실행 위험 ⚠️

**기획안 설계 (§7 Phase 1):**
> 1. 폴더 구조 생성
> 2. 하네스 심링크 연결
> 3. 기존 배치 파일 + 감사 리포트 이동
> 4. _common.yaml + investment.yaml 작성
> 5. phase0_template.json 작성

**문제:** Phase 1의 5개 작업 중 **검증 스텝이 없음**. 심링크가 작동하는지, 이동한 파일이 깨지지 않았는지, YAML이 기존 스키마와 호환되는지 확인하는 절차가 없음.

**왜 이게 중요한가:**
- Phase 1 완료 후 Phase 2로 넘어갔는데 심링크가 안 되면 → Phase 1 재작업
- 이동한 batch 파일이 깨졌는데 모르고 Phase 2에서 검증 도구를 만들면 → 깨진 데이터로 검증 도구 테스트

**심각도:** **P2 — 검증 누락**

**수정:** Phase 1 끝에 검증 스텝 추가:
```
Phase 1 — 뼈대 + 검증
  ...기존 5개...
  6. 검증: 심링크/참조 경로 전수 접근 테스트
  7. 검증: 이동된 파일 UTF-8 파싱 + 원본 해시 대조
  8. 검증: YAML 스키마와 preset_registry.py 필드 교차 확인
```

---

## 종합 판정표

| ID | 항목 | 심각도 | 유형 | 요약 |
|----|------|--------|------|------|
| **P1-01** | §2 P-3 주입 순서 | **P0** | 설계결함 | LLM 생성 후가 아니라 **전**에 주입해야 함 |
| **P1-02** | §8 Stage 0 역할 | **P0** | 아키텍처 | Stage 0은 TR/BI를 로드하지 않고 **생성**함 |
| **P3-01** | §4 장르 프로파일 이중 관리 | **P0** | SSOT위반 | preset_registry.py와 중복 → 단일 참조점 필요 |
| **P2-01** | §0 모놀리스 진단 | **P1** | 사실오류 | tr_batch_harness 3함수 이미 공유 중 |
| **P2-02** | §0 Phase 0 템플릿 없음 | **P1** | 사실오류 | preset_registry.py + story_expander.py 존재 |
| **P2-04** | §6 기존 자산 대규모 누락 | **P0** | 누락 | tools/ 15 + tools2/ 22 + scripts 3 + 루트 1 = **41파일** 기획에 없음 |
| **P2-05** | §3.1 심링크 실행 가능성 | **P1** | 미검증 | Windows + git 환경에서 symlink 0건 |
| **P3-02** | §3.4 검증 전환 전략 | **P1** | 미정의 | 기존 validate_candidate()와의 관계 불명 |
| **P3-03** | §6.1 감사 이동 부작용 | **P1** | 미고려 | 스크립트 3개 출력 경로 변경 필요 |
| **P1-03** | §5.1 opponent 필드 경로 | **P1** | 호환성 | dict/str 양쪽 처리 필요 |
| **P2-03** | §0 감사 섞임 과장 | **P2** | 과장 | 이미 서브디렉토리로 분리됨 |
| **P1-04** | §1 폴더 순서 | **P2** | 가독성 | 감사 → 출고 순서로 배치 권장 |
| **P3-04** | §7 Phase 1 검증 없음 | **P2** | 절차누락 | 심링크·파일·스키마 검증 스텝 필요 |

---

## 감리 결론

### PASS 1 결론: **구조적 결함 2건 (P0)**
- 파이프라인 순서 오류 (P-3 주입 시점)
- 아키텍처 경계 오인 (Stage 0 역할)

### PASS 2 결론: **사실 오류 4건 (P0 1건 상향)**
- 모놀리스 진단 과장, Phase 0 템플릿 존재 누락, 감사 분리 과장
- **기존 자산 대규모 누락 (P1→P0 상향)**: tools/ 15 + tools2/ 22 + scripts 3 + 루트 1 = 41파일

### PASS 3 결론: **설계 위험 4건**
- SSOT 위반 (장르 프로파일 이중화), 전환 전략 미정의, 부작용 미고려, 검증 절차 누락

### 총평

1차 기획안의 **방향성은 맞다** — 산재된 전처리 자산을 SSOT화하는 것은 필요하다.
그러나 **기존 시스템에 대한 조사가 불충분**하여:

- 이미 있는 것을 없다고 진단 (Phase 0 템플릿, 공유 함수)
- 이미 있는 것과 충돌하는 새 시스템을 설계 (장르 프로파일 YAML)
- 이미 있는 자동화 코드를 대규모 누락 (41파일 — scripts 3 + tools 15 + tools2 22 + 루트 1)
- 특히 `tools/treatment_builder.py`, `tools/bible_builder.py`, `tools2/apply_v3.py`는 전처리의 핵심 기능 자체

**P0 4건 총정리:**

| # | ID | 문제 | 수정 방향 |
|---|-----|------|----------|
| 1 | P1-01 | P-3 주입 순서 역전 | LLM 생성 **전**으로 이동 |
| 2 | P1-02 | Stage 0 역할 오인 | "대체 관계"로 경계 재정의 |
| 3 | P3-01 | 장르 프로파일 이중 관리 | preset_registry.py 단일 참조 |
| 4 | P2-04 | 기존 자산 41파일 누락 | 전수 인벤토리 → 통합 vs 신규 판단 |

**2차 기획안 작성 전 필수 선행:**
1. `modules/core/stage0/` 전체 읽기 → 전처리와의 관계 재정의
2. `scripts/` + `tools/` + `tools2/` 전체 인벤토리 → 재사용 vs 신규 구축 판단
3. P0 4건 수정 적용

---

*끝.*
