# BI 생산 하네스 v1
<!-- utf8-hygiene: allow-file rationale: this harness intentionally documents literal mojibake tokens like ??? and � as detection examples. -->

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-09
> 근거: `treatment-production-harness-v2.md` + `tr-bi-3pass-audit.md` + 실제 BI 오염 사례
> 목적: **Windows/PowerShell 환경에서 한글 BI JSON이 `???`로 오염되지 않도록, 생성-동기화-감리 절차를 강제**
> 출력: `bible/0_bi_{work_id}.json`
> 선행 문서: `SSOT_blockguide-integrated-order.md`

---

## 0A. 초저지능 LLM용 빠른 시작

이 문서는 **`TR draft`가 이미 있는 상태에서만** 실행한다.
사용자가 작품명, `work_id`, `다음 스텝`만 줘도 아래 순서를 먼저 수행한다.

1. `SSOT_blockguide-integrated-order.md`를 **UTF-8로 먼저 읽는다.**
2. `treatment-production-harness-v2.md`를 다시 확인해 TR이 감리 통과 상태인지, source TR audit snapshot이 있는지 본다.
3. 작품이 현대판타지이고 업계/직업/전문분야 재료가 필요하면 `modern_fantasy_material_harness.md`를 추가로 읽는다.
4. 장르가 `alt_history`이거나 역사 재료 DB 조회가 필요하면 `alt_history_db_harness.md`를 추가로 읽는다.
5. 이 문서를 **UTF-8로 다시 읽는다.**
6. `phase0_design`, `tr_block_070_draft`, 기존 `BI`를 UTF-8로 재오픈한다.
7. `TR draft`가 없으면 BI를 만들지 말고 production 단계로 되돌린다.
8. BI는 새 창작이 아니라 동기화 작업으로 이해한다.
9. 항상 아래 순서로만 진행한다.
   - source TR handoff gate 확인
   - 최소 스켈레톤
   - 결정적 동기화
   - UTF-8 저장
   - 정합성 검증
   - 5-Pass 감리
   - PASS/FAIL 보고 후 정지
10. 하나라도 실패하면 다음 단계로 넘어가지 않는다.

추가 해석:

- TR production의 `5블록 자동 연속 cap`은 source TR 쪽 규칙이다.
- BI 단계는 block count로 환산하지 않는다.
- source TR이 70블록 완료 전이거나, 5블록 창 중간 정지 상태면 BI로 넘어가지 않는다.

금지:

- `TR draft` 없이 BI부터 만들기
- `plot_roadmap`를 기억으로 다시 요약하기
- 감리 전 BI를 완료본으로 부르기

## 0B. SSOT 우산 정의

현재 일부 런타임과 코드 경로는 여전히 `investment`, `FinanceHUD`, `portfolio_history` 같은 이름을 사용한다.
그러나 이 문서의 SSOT 의미는 **현대판타지 all-genre general mode용 BI**다.

핵심 해석:

- `FinanceHUD`는 키 이름만 유지하며, 문서상 의미는 **Resource-Power HUD**다.
- `portfolio_history`는 지분 평가액 전용이 아니라 주인공의 성장 자원/권력 변화 체크포인트다.
  현재 계약상 지위는 **권장 확장 필드(P1)** 다.
- `business_lines`는 키 이름만 유지하며, 실제 의미는 작품의 active domain lines다.
- `company_state`는 키 이름만 유지하며, 실제 의미는 현재 operating arena / base state다.
- `financial_status`는 경제 숫자만이 아니라 해당 프로파일에서 즉시 동원 가능한 자원 상태의 최소 레이어다.
- 신입사원물, 엔터물, 의학물, 헌터물도 측정 가능한 성장 축이 있으면 이 BI 범위에 포함한다.

## 0C. 공통 용어표

| 용어 | SSOT 의미 |
| ---- | ---- |
| `capital` | 돈, 예산, 반복 현금흐름, 케이스, 팬덤, 권한, 길드 자산 등을 함께 추적하는 호환 지표 |
| `deal_type` | 결정적 진행 액션 단위 |
| `power` | 승인권, 정보권, 정산권, 규격권, 집도권, 편성권, 조직 통제력 |
| `control` | 회사/가문/조직이 주인공 조건표를 거치지 않고는 움직이기 어려운 상태 |
| `business_lines` | 키 이름은 유지하되 실제 의미는 작품의 active domain lines |
| `company_state` | 키 이름은 유지하되 실제 의미는 current operating arena / base state |
| `failure` | 손실, 여론전 패배, 결재선 패배, 조직 이탈까지 포함한 실질 후퇴 |
| `payoff` | 돈 회수뿐 아니라 권한, 관계, 복선, 굴욕 회수 |

## 0D. 구현 드리프트 메모

현재 일부 공용 BI 빌더는 `phase0_design`에서 `partner_location_sector_distribution`, `capital_curve`, `defeat_blocks` 같은 보조 필드를 더 기대할 수 있다.
하지만 Blockguide SSOT의 **최소 동기화 계약**은 더 작다.

문서 기준:

- 최소 필수: `arcs`, `npc_timeline`, `foreshadow_map`, `opponent_transition_plan`
- 권장 확장: `capital_curve`, `defeat_blocks`, `distribution_plan`
- 보조 필드가 있으면 복사/요약에 활용하되, 없다고 BI 생성 금지 사유로 보지 않는다.

## 0E. BI 계약 계층

## 0F. Shared `evolution` Metadata Standard

- Shared standard doc: `docs/narrative-router/SSOT_bi-evolution-metadata-standard.md`
- Blockguide BI에서 compact growth-trace metadata의 canonical key는 `evolution`이다.
- `evolution`은 concrete owner object에 붙인다.
  - example: `protagonist_config.special_ability.evolution`
- `evolution` value type은 `string` 또는 `string[]`를 허용한다.
- Legacy alias:
  - `engine_evolution`
  - `evolution_arc`
  - `evolution_stages`
- 새로 생성하거나 새로 터치하는 blockguide BI는 legacy alias 대신 `evolution`을 우선 사용한다.
- 하나의 newly touched object 안에 canonical key와 legacy alias를 동시에 새로 쓰지 않는다.

BI 계약은 한 번에 전부 P0로 올리지 않는다.
문서가 실제 생성기/감리보다 앞서가며 거짓 요구를 하지 않도록 **최소 계약(P0)** 과 **확장 계약(P1)** 을 분리한다.

최소 계약(P0):

- `plot_roadmap` 길이 70
- `plot_roadmap` title sequence가 source `TR draft`와 일치
- `CoreIdentity.protagonist == FinanceHUD.Protagonist.actual_truth.name`
- `MasterBible.ProjectData.MetaInfo.title` 정상 한글
- `FinanceHUD.Protagonist.actual_truth.financial_status.total_assets`와
  `FinanceHUD.Protagonist.actual_truth.financial_status.mobilizable_capital`이 source TR 최종 `capital_after`와 충돌하지 않음
- source TR handoff gate PASS
- UTF-8 / JSON 파싱 PASS

확장 계약(P1):

- `FinanceHUD.Protagonist.portfolio_history`
- `portfolio_history` milestone이 source TR 주요 자본 곡선과 충돌하지 않음
- 추가 HUD 세부 필드, milestone 서술, 보조 성장 이력

승격 규칙:

- P1 필드를 P0로 올리려면 아래 3개를 모두 만족해야 한다.
- 생성기/빌더가 source TR에서 해당 필드를 결정적으로 채울 수 있어야 한다.
- 최근 골든 BI 3개 이상이 실제로 그 필드를 안정적으로 채워야 한다.
- 감리 스크립트/수동 감리가 그 필드를 재현 가능하게 검사할 수 있어야 한다.

## 0. 왜 BI 전용 하네스가 필요한가

Treatment는 블록 단위로 쪼개 생산할 수 있지만, BI는 보통 한 번에 길고 넓게 생성된다.  
이 때문에 아래 4가지가 한 번에 겹치면 오염률이 급상승한다.

1. 긴 한국어 중첩 JSON을 콘솔 인라인 코드로 직접 생성
2. compaction 이후 모델 메모리만으로 BI를 다시 조립
3. UTF-8이 아닌 콘솔/기본 인코딩 경로를 경유해 저장
4. 이미 검증된 TR/Phase0를 복사 동기화하지 않고 BI를 독립 생성

핵심 판단:

- `plot_roadmap`는 **창작 대상이 아니라 동기화 대상**이다.
- BI 상단 메타/서술 필드는 **짧은 수기 보정 영역**이다.
- BI 본문 대부분은 **검증된 원천 파일에서 읽어 와서 채워야 한다**.

---

## 1. BI 오염 패턴

| ID | 패턴 | 증상 | 심각도 |
|----|------|------|--------|
| B-1 | 인코딩 오염 | `???`, `??`, `�` 다량 발생 | P0 |
| B-2 | stale roadmap | `TR`과 `BI.plot_roadmap` 제목/길이 불일치 | P0 |
| B-3 | 주인공 불일치 | `CoreIdentity.protagonist != FinanceHUD.Protagonist.actual_truth.name` | P0 |
| B-4 | 메모리 재조립 | compaction 후 이전 설정 일부가 누락되거나 다른 작품 값이 섞임 | P0 |
| B-5 | 이중 SSOT | `plot_roadmap`를 여러 위치에 중복 저장하고 서로 어긋남 | P1 |
| B-6 | 빈약한 스키마만 통과 | `title`만 맞고 실제 한국어 서술은 깨진 상태 | P1 |
| B-7 | PowerShell 기본 인코딩 의존 | 파일은 생성됐지만 한글만 손상 | P0 |
| B-8 | 장문 인라인 생성 | heredoc/파이프라인 내부 한글 문자열이 부분 손상 | P0 |

---

## 2. 생산 원칙

### 2.1 SSOT 고정

BI 생성 시 원천 데이터는 아래 2개만 신뢰한다.

1. `treatments/{work_id}_phase0_design.json`
2. `treatments/{work_id}_tr_block_070_draft.json`

규칙:

- `plot_roadmap`는 반드시 `TR draft`에서 복사 생성한다.
- 장기 복선, NPC 타임라인, 적대축은 반드시 `phase0_design`에서 읽어 온다.
- `capital_curve`, `defeat_blocks`, `distribution_plan`이 있으면 함께 읽고, 없으면 필수 아님으로 처리한다.
- compaction 이후에도 **메모리 재구성 금지**, 먼저 위 2개 파일을 다시 열어 확인한다.

### 2.2 한글 생성 영역 최소화

BI에서 직접 새로 써야 하는 한글은 최소화한다.

- 직접 작성 허용:
  - `MetaInfo.title`
  - `grand_objective`
  - `genre_archetype`
  - 짧은 `CommercialCode`
  - 짧은 `GenreRules`
- 직접 작성 금지:
  - `plot_roadmap`
  - NPC 목록 대량 본문
  - 자본 이력
  - 블록 제목/요약

원칙:

- **긴 한국어는 새로 쓰지 말고 검증된 파일에서 복사한다.**
- BI를 “다시 창작”하지 말고 “구조화 + 동기화”한다.

### 2.3 파일명과 저장 규칙

- 출력 파일명은 ASCII 기준을 권장한다.
  - 예: `bible/0_bi_chaebol_ent_empire.json`
- 파일 내용은 UTF-8, BOM 없음으로 저장한다.
- Windows PowerShell 5.x에서는 `Set-Content -Encoding UTF8`의 BOM/표시 문제를 피하기 위해 **JSON 저장은 Python `-X utf8` 또는 검증된 편집기 저장만 사용**한다.

---

## 3. BI 생산 아키텍처: 5-Phase + 5-Pass

```text
Phase 0: 원천 고정
  ↓ phase0_design + tr_block_070_draft 확인
Phase 1: BI 최소 스켈레톤 작성
  ↓ MasterBible / ProjectData / FinanceHUD(=Resource-Power HUD) 뼈대
Phase 2: 결정적 동기화
  ↓ plot_roadmap / financial_status / (선택) portfolio_history / npc_timeline / seeds 주입
Phase 3: UTF-8 저장 + 오염 탐지
  ↓ ??? / � / 공백 주인공명 / stale title 탐지
Phase 4: TR↔BI 정합성 검증
  ↓ protagonist / 길이 / edge title / hash or title-line sync
Phase 5: 5-Pass 감리
  ↓ PASS 1~5 전부 통과 시 확정
```

### 3.1 `다음 스텝` 기반 TR→BI handoff 프로토콜

TR 생산이 끝난 뒤 사용자가 `다음 스텝`만 입력해도 BI 단계가 자연스럽게 이어지도록,
아래 handoff 규칙을 고정한다.

핵심 해석:

- `다음 스텝` at TR 완료
  → `TR draft`를 종착점으로 보지 말고 **BI 생성 시작 신호**로 해석
- `다음 스텝` at BI 생성 완료
  → **UTF-8 검증 + 감리**를 수행
- `다음 스텝` at BI 감리 완료
  → 정리/보존 정책 또는 최종 출고 안내로 넘어간다

운영 순서:

| 사용자 입력 시점 | 기본 행동 | 출력 단위 |
| ---------------- | --------- | --------- |
| TR 70블록 draft 직후 | Phase 0/ TR 원천 재오픈 | handoff 준비 |
| 그다음 `다음 스텝` | BI 최소 스켈레톤 + 결정적 동기화 | `0_bi_{work_id}.json` |
| 그다음 `다음 스텝` | UTF-8 저장 검증 + 5-Pass 감리 | 감리 report |
| 그다음 `다음 스텝` | 중간 산출물 정리 또는 최종 패키징 | 보존본만 남김 |

기본 원칙:

1. BI는 `TR draft`가 나온 뒤 **별도 독립 창작 단계**가 아니라 handoff 산출물이다.
2. 사용자가 `다음 스텝`만 입력하면, 이미 있는 `TR draft`를 SSOT로 삼아 BI를 계속 전진시킨다.
3. 깨진 BI가 있으면 수선보다 재생성을 우선한다.
4. BI 감리 전에는 “완료”라고 부르지 않는다.
5. `auto-run`은 handoff 순서를 이어 간다는 뜻이지, 스크립트를 자동 실행하라는 뜻이 아니다.

### 3.1A source TR handoff gate

BI handoff 전에는 source TR이 **구조상 존재**하는 것만으로는 부족하다.
아래가 모두 확인돼야 BI 단계로 진입한다.

- `production_density_gate = PASS`
- `avg_bundle_chars` 확인 가능
- `opponent_unique` 확인 가능
- `deal_top_repetition` 또는 동등 반복 지표 확인 가능
- `method_top_repetition` 또는 동등 반복 지표 확인 가능
- `pattern_feedback_snapshot` 또는 동등한 반복 경고 요약 확인 가능
- source TR에 `skeleton draft`, 반복 FAIL, density FAIL이 없음

규칙:

- 위 항목 중 하나라도 비면 BI 진입 금지
- 이 경우 production 단계 또는 Failure Triage로 되돌린다
- BI가 구조적으로 맞아 보여도 source TR gate 실패면 PASS 불가
- source TR에 cadence 경고 또는 반복 경고가 남아 있으면, BI 감리 보고서에 그 사실을 명시한다.

### 3.1B BI auto-handoff boundary

TR production의 5블록 cap은 BI 단계에 그대로 적용하지 않는다.
BI는 block 단위가 아니라 handoff 단위로 움직인다.

규칙:

1. BI auto-run은 `스켈레톤 -> 결정적 동기화 -> UTF-8 저장 -> 5-Pass 감리` **1사이클**까지만 허용한다.
2. PASS 또는 FAIL 보고가 나오면 그 지점에서 멈춘다. 같은 오더로 BI를 무한 재생성하지 않는다.
3. source TR이 5블록 cap 때문에 중간 정지한 상태라면 BI로 넘어가지 않는다. BI 시작 조건은 `TR 70블록 완료 + source TR handoff gate PASS`다.

### 3.2 연속 handoff 허용 모드 (Quality-First)

BI 단계도 연속 handoff를 허용한다.
다만 기본 철학은 **quality-first**이며, 생성보다 수동 감리와 동기화 확인이 상위다.

자동 진행 순서:

1. `TR draft` UTF-8 파싱 확인
2. 기존 `BI` 존재 시 오염 여부 확인
3. 손상 시 재생성, 무손상이면 정합성 점검
4. `0_bi_{work_id}.json` 저장
5. UTF-8/정합성/감리 실행
6. 최종본만 남길지 여부가 명시된 경우 정리 단계까지 진행

강제 정지 게이트:

- `TR draft` 또는 `phase0_design` 부재
- source TR audit snapshot 부재
- source TR density/repetition FAIL
- `plot_roadmap` hash 불일치
- `???` / `�` 탐지
- 감리 FAIL
- 삭제 범위가 사용자 의도와 직접 연결되는 경우

원칙:

1. auto-run은 허용 모드일 뿐, 품질보다 우선하지 않는다.
2. auto-run의 의미는 `BI 생성 -> 수동 감리 -> 다음 단계` 순서를 이어 간다는 뜻이지, 스크립트 자동 호출 강제가 아니다.
3. BI 생성 직후에는 반드시 사람이 읽는 수동 감리 메모를 1회 남긴다.
4. 컨텍스트 compaction이 발생해도 같은 원칙을 유지한다. 이 경우 `TR draft`, `phase0_design`, 기존 `BI`를 UTF-8로 재오픈한 뒤 자동 재개한다.
5. BI와 감리 보고서는 전부 **UTF-8 only**로 읽고 쓴다. 한글 깨짐은 즉시 재생성 대상으로 본다.
6. BI 감리 PASS 전에는 후처리 삭제로 넘어가지 않는다.
7. TR의 5블록 cap은 BI에 적용하지 않는다. BI는 handoff 1사이클 기준으로만 자동 진행한다.
8. 중간에 하나라도 실패하면 자동 진행을 중단하고, 실패 단계와 원인을 바로 보고한다.
9. PASS/FAIL 보고가 끝나면 새 오더 전까지 재생성 루프를 이어 가지 않는다.

### 3.3 초세분화 handoff 루틴 (저지능 LLM 기본값)

느리더라도 아래 13단계를 그대로 따르면 BI 오염 가능성이 가장 낮다.

1. `SSOT_blockguide-integrated-order.md`를 다시 읽는다.
2. `phase0_design`를 UTF-8로 연다.
3. `tr_block_070_draft`를 UTF-8로 연다.
4. source TR handoff gate(`production_density_gate`, `avg_bundle_chars`, `opponent_unique`, `deal_top_repetition`, `method_top_repetition`)를 확인한다.
5. 기존 `0_bi_{work_id}.json`이 있으면 UTF-8 파싱과 오염 여부만 확인한다.
6. 오염이 있으면 부분 수선보다 재생성을 택한다.
7. BI 최소 스켈레톤만 먼저 만든다.
8. `plot_roadmap`는 `TR draft`에서 복사 주입한다.
9. 장기 복선, NPC 타임라인, 적대축은 `phase0_design`에서만 복사하고, `capital_curve` 같은 보조 시트는 있으면 추가 반영한다.
10. 직접 새로 쓰는 한글은 상단 짧은 메타 필드로 제한한다.
11. UTF-8로 저장한다.
12. 정합성 검증과 5-Pass 감리를 실행한다.
13. PASS가 뜬 뒤에만 handoff 완료로 기록한다.

턴 종료 시 최소 보고 형식:

1. 이번에 연 SSOT
2. 새로 생성했는지, 재사용했는지
3. 감리 상태
4. 다음 행동

---

## 4. Phase 0: 원천 고정

### 4.1 필수 확인

BI 생성 전에 아래를 먼저 확인한다.

- `phase0_design` UTF-8 파싱 성공
- `TR draft` UTF-8 파싱 성공
- `phase0_design` 최소 필수 시트(`arcs`, `npc_timeline`, `foreshadow_map`, `opponent_transition_plan`) 존재 확인
- `TR draft` 블록 수 70
- `TR draft` 첫 블록/마지막 블록 title 확인

### 4.2 compaction 대응 규칙

compaction 직후에는 절대 BI를 바로 수정하지 않는다.

먼저 해야 하는 일:

1. `phase0_design` 재오픈
2. `TR draft` 재오픈
3. 현재 `BI`가 있으면 UTF-8 파싱과 `???` 존재 여부 확인
4. 손상 시 부분 수선보다 **재생성 우선**

금지:

- “아까 기억나는 설정”으로 BI 재작성
- 다른 작품 BI를 복붙 후 일부 치환
- `plot_roadmap`를 LLM이 다시 요약하게 두기

---

## 5. Phase 1: BI 최소 스켈레톤

BI 최소 스켈레톤은 아래 필드만 먼저 만든다.

```json
{
  "_schema_version": "2.0",
  "_schema_description": "작품 설명",
  "_last_updated": "YYYY-MM-DD",
  "_genre": "genre_code",
  "MasterBible": {
    "ProjectData": {
      "MetaInfo": {
        "title": "작품명"
      }
    }
  },
  "plot_roadmap": []
}
```

규칙:

- 처음부터 모든 섹션을 장문으로 채우지 않는다.
- 스켈레톤 생성 후 바로 UTF-8/JSON 파싱 검사를 한 번 통과시킨다.

---

## 6. Phase 2: 결정적 동기화

### 6.1 `plot_roadmap`

`plot_roadmap`는 반드시 `TR draft`에서 생성한다.

최소 동기화 규칙:

- 길이 = 70
- 가능하면 `TR draft`의 블록 객체 전체를 그대로 복사한다.
- 최소한 `plot_roadmap[n].title == TR[n].title`
- 요약 필드가 따로 필요하면 `TR[n].content.context`를 사용한다.
- `capital_before/after` 계열 값은 `TR[n].genre_ext`에서 복사한다.

### 6.2 `financial_status` 최소 계약

`FinanceHUD.Protagonist.actual_truth.financial_status`는 BI의 최소 계약(P0)에 포함된다.

최소 규칙:

- `mobilizable_capital` 존재
- `total_assets` 존재
- 가능하면 `max_assets` 존재
- 최종 `mobilizable_capital`과 `total_assets`는 source TR 마지막 블록의 `capital_after`와 충돌하지 않는다.
- `company_state`, `business_lines`는 실제 장악한 domain lines와 operating arena 상태와 충돌하지 않는다.

주의:

- `portfolio_history`가 비어 있거나 생략돼도, 위 최소 계약이 맞으면 즉시 FAIL로 보지 않는다.
- 반대로 `portfolio_history`가 있어도 `financial_status` 최종 자본이 source TR과 어긋나면 P0 FAIL이다.
- 비사업 장르라 해도 `financial_status`를 비워 두지 않는다. 해당 프로파일에서 즉시 동원 가능한 운영 자원 기준선으로 채운다.

### 6.3 주인공 핵심 필드

아래 3개는 반드시 동일해야 한다.

- `MasterBible.ProjectData.MetaInfo.title`
- `MasterBible.ProjectData.CoreIdentity.protagonist`
- `MasterBible.FinanceHUD.Protagonist.actual_truth.name`

### 6.4 파생 섹션

아래는 `phase0_design` 기반으로 넣는다.

최소 필수:

- `npc_timeline`
- `Seeds`
- `HistoricalEvents`
- `opponent_transition_plan`

권장 확장:

- `capital_curve`
- `defeat_blocks`
- `distribution_plan`
- `GenreRules`

원칙:

- `phase0_design`에 있는 문장은 그대로 최대한 활용한다.
- 새로 쓰는 설명은 짧고 요약적이어야 한다.
- `business_lines`는 TR의 실제 domain lines를 요약해서 채운다.
- `company_state`는 작품의 운영 무대 상태와 통제 수준을 반영한다.

### 6.5 장르 프로파일별 BI 매핑 예시

| 프로파일 | `FinanceHUD`에서 강조할 것 | `company_state` 해석 | `business_lines` 구성 |
| ---- | ---- | ---- | ---- |
| `business_growth_profile` | 반복 현금흐름, 운영권, 정산권 | "필수 인프라 운영사", "그룹 운영망 관문" 같은 운영 상태 | 급식, 세탁, 정산, 공급망, 포털, 운영금융 |
| `investment_market_profile` | 자산, 지분, 수익률, 구조화 거래 | "저평가 자산 집적기", "시장 지배력 확장 단계" | 지분, 펀드, 라이선스, 금융 구조, 시장 채널 |
| `entertainment_media_profile` | IP, 팬덤, 편성권, 유통창구, 화제성 | "레이블 성장 단계", "편성/유통 관문 보유" | 아티스트, IP, 유통 채널, 팬덤, 공연/방송 라인 |
| `medical_professional_profile` | 집도권, 케이스, 신뢰도, 병원 권한 | "수술실 접근권 보유", "진료과 영향력 확대" | 진료과, 수술/케이스, 레퍼럴, 연구 라인, 의료팀 |
| `office_power_profile` | KPI, 예산, 결재선, 인사권 | "핵심 부서 승인 관문", "실적 배분 권한 보유" | 예산, 평가, 결재, 조직, 운영 프로세스 |
| `tech_startup_profile` | 제품 우위, 라이선스, 데이터, 사용자 기반 | "제품-시장 적합 단계", "배포/표준 선점 상태" | 제품군, 특허, 데이터, 고객 채널, 파트너십 |
| `urban_power_profile` | 전투력, 길드 자산, 던전 권리, 위상 | "길드 핵심 전력", "독점권 보유 팀" | 레이드 팀, 훈련 라인, 던전 권리, 후원/보급 채널 |

현재 repo 앵커:

- `chaebol_allowance_zero` → `business_growth_profile` + `office_power_profile`
- `chaebol_ent_empire` → `entertainment_media_profile` + `business_growth_profile`
- `defense_defect_engineer` → `business_growth_profile` + `tech_startup_profile`
- `us_ai_exile_monopoly` → `investment_market_profile` + `tech_startup_profile`

---

## 7. Phase 3: UTF-8 저장 규칙

### 7.1 읽기 규칙

PowerShell:

```powershell
$p='C:\path\to\file.json'
Get-Content -Encoding UTF8 -Raw -Path $p | ConvertFrom-Json
```

Python:

```powershell
@'
import json
from pathlib import Path
p = Path('bible/0_bi_work.json')
json.loads(p.read_text(encoding='utf-8'))
print('JSON_OK')
'@ | python -X utf8 -
```

### 7.2 쓰기 규칙

권장:

- Python `Path.write_text(..., encoding="utf-8")`
- `json.dumps(..., ensure_ascii=False, indent=2)`
- 문서/템플릿 수기 편집은 `apply_patch`
- Python/Powershell 인라인 실행 시 파일 경로는 **상대경로 우선**
- Windows 한글 절대경로를 Python stdin 문자열에 직접 박아 넣지 않기

비권장:

- PowerShell 기본 `Set-Content`
- `Out-File` 인코딩 미지정
- 한글 대량 문자열을 shell heredoc 내부에서 새로 작성
- 한글 절대경로를 inline Python 문자열로 직접 전달
- shell 인라인 코드 안에서 한글 장문 report/markdown 본문을 직접 조립

추가 원칙:

- BI JSON뿐 아니라 **감리 report도 UTF-8 산출물**이다.
- report 본문을 shell 인라인 한글 상수로 길게 작성하면 JSON은 멀쩡한데 report만 `??`/`�`로 깨질 수 있다.
- 감리 report는 가능하면 Python 파일/템플릿/`apply_patch`로 작성하고,
  shell 인라인 실행이 필요하면 ASCII 안전 포맷 또는 원천 파일 복사값 위주로 제한한다.

### 7.3 오염 탐지

최소 탐지 패턴:

```powershell
rg -n "\?\?\?" bible\0_bi_chaebol_ent_empire.json
rg -n "�" bible\0_bi_chaebol_ent_empire.json
```

해석:

- 콘솔 표시 문제일 수 있으므로 `rg`와 `python -X utf8` 둘 다로 확인한다.
- 파일 내부에 실제 `???`가 있으면 인코딩 오염 또는 손상된 문자열로 본다.
- `???`가 없더라도 `�` 1건만 있으면 FAIL이다. 한 필드만 깨져도 재생성 또는 부분 교정 후 재감리한다.

---

## 8. 5-Pass 감리

### 8.0 5-Pass 감리 체크리스트

아래 5개 Pass를 **순서대로** 실행한다. 앞 Pass가 FAIL이면 뒤 Pass로 넘어가지 않는다.

| Pass | 검증 대상 | 통과 조건 요약 |
| ---- | --------- | -------------- |
| 1 | UTF-8 + JSON 파싱 | UTF-8 읽기 성공, JSON 파싱 성공, `???`/`�` 0건 |
| 2 | plot_roadmap 70개 일치 | `plot_roadmap` 길이 = 70, 제목 = source TR 제목, `MasterBible.ProjectData.MetaInfo.title` 정상 한글 |
| 3 | 주인공 최종 자산 | `FinanceHUD.Protagonist.actual_truth.financial_status`의 최종 자본 = TR 마지막 블록 `genre_ext.capital_after` |
| 4 | NPC deceased 정합성 | `deceased=True`인 NPC가 후속 블록에서 행동 주체로 등장하지 않는지 검증 |
| 5 | 복선 심기/회수 블록 번호 | BI의 복선 심기/회수 블록 = TR `foreshadow`/`callback` 블록 번호 일치 |

감리 결과 형식:

```text
=== BI 5-Pass Audit ===
Work: {work_id}
Date: {date}

PASS 1 (UTF-8 + JSON 파싱): OK / FAIL
PASS 2 (plot_roadmap 70개 일치): OK / FAIL
PASS 3 (주인공 최종 자산): OK / FAIL
PASS 4 (NPC deceased 정합성): OK / FAIL
PASS 5 (복선 심기/회수 블록 번호): OK / FAIL

Final Verdict: PASS / FAIL
Notes: ...
```

---

### PASS 1: 인코딩/파싱

통과 조건:

- UTF-8 읽기 성공
- JSON 파싱 성공
- `???`, `�` 0건

실패 시 조치:

- 손상 필드가 넓으면 부분 수정 금지
- `phase0_design + TR draft` 기준으로 BI 재생성

### PASS 2: 최소 스키마 + plot_roadmap 70개 일치

통과 조건:

- `validate_bible_structure` 통과
- `MasterBible.ProjectData.MetaInfo.title` 존재하고 정상 한글
- `plot_roadmap` 길이 = 70
- `plot_roadmap` title sequence가 source `TR draft`와 **전수 일치** (제목 = source TR 제목)

### PASS 3: 주인공 최종 자산 동기화

통과 조건:

- `CoreIdentity.protagonist == FinanceHUD.Protagonist.actual_truth.name`
- `MetaInfo.title` 정상 한글
- 주인공 최종 자산 = TR 마지막 블록 `genre_ext.capital_after`
- `financial_status.total_assets`와 `financial_status.mobilizable_capital`이 source TR 최종 `capital_after`와 충돌 없음
- `portfolio_history`가 있으면 증가 흐름과 `TR draft` 주요 자본 이력 충돌 없음
- `portfolio_history`가 비어 있거나 생략된 경우, P0 실패가 아니라 P1 미충족 또는 경고로 분리

### PASS 4: NPC deceased 정합성

통과 조건:

- `deceased=True`인 NPC가 해당 사망 블록 이후의 `plot_roadmap` 블록에서 **행동 주체로 등장하지 않음**
- 사망 NPC가 회상/언급으로만 등장하는 것은 허용
- `npc_timeline`에서 해당 NPC의 `status`가 `deceased`로 표시됨
- 사망 블록 번호가 `npc_timeline`과 `plot_roadmap` 간 일치

검증 방법:

1. `npc_timeline`에서 `deceased=True`인 NPC와 사망 블록을 모두 추출한다.
2. `plot_roadmap`에서 해당 NPC가 사망 블록 이후에 행동 주체로 나오는지 확인한다.
3. 불일치 시 P0 FAIL.

### PASS 5: 복선 심기/회수 블록 번호 정합성

통과 조건:

- BI의 `Seeds` 또는 `foreshadow_map`에 기록된 복선 심기 블록 번호가 TR의 `foreshadow` 기록과 일치
- BI의 복선 회수 블록 번호가 TR의 `callback` 기록과 일치
- 심어진 복선 중 미회수 항목은 `status: open`으로 명시
- 회수된 복선의 `callback_block`이 `foreshadow_block`보다 후순위
- 한국어 필드에 `??`, `???` 없음
- 다른 작품 흔적 없음
- arc 명칭, NPC 이름, 회사명 일치
- `plot_roadmap`가 stale copy가 아님
- `bi_structure_ok_but_source_tr_failed = true`가 아니어야 함

실패 규칙:

- source TR이 `skeleton draft`, 반복 FAIL, density FAIL이면
  BI 구조 정합성과 무관하게 `final_verdict = FAIL`
- 복선 블록 번호가 1건이라도 어긋나면 해당 항목 수정 후 재감리

권장:

- PASS 5는 사람이 실제 한 번 읽는다.
- 최소 20개 필드 샘플링:
  - 상단 메타 5개
  - NPC 5개
  - KeyItems/Locations 5개
  - roadmap 앞/중간/끝 5개

---

## 9. 실패 시 복구 원칙

### 9.1 부분 수선보다 재생성 우선

아래 중 하나면 재생성이 더 빠르다.

- `???`가 10개 이상
- 상단 메타와 NPC/Location까지 넓게 깨짐
- `plot_roadmap` title이 다수 어긋남
- compaction 직후 메모리 기반 수선이 이미 한 번 섞임

### 9.2 절대 금지

- 깨진 BI를 기준으로 다시 덮어쓰기
- 깨진 한글을 추측 복원해서 대량 치환
- `plot_roadmap`를 수동으로 70개 다시 요약

### 9.3 정석 복구 순서

1. 손상된 BI 보관 또는 폐기
2. `phase0_design` 확인
3. `TR draft` 확인
4. BI 최소 스켈레톤 재생성
5. `plot_roadmap` 결정적 복사
6. 5-Pass 감리 재실행

---

## 10. 수동 운영 체크리스트

- `phase0_design` UTF-8 파싱 성공
- `TR draft` UTF-8 파싱 성공
- `phase0_design` 최소 필수 시트 존재
- BI 파일명 ASCII 사용
- BI 저장은 UTF-8 only
- `plot_roadmap`는 TR에서 복사
- 주인공명 2중 위치 일치
- `FinanceHUD`를 Resource-Power HUD 의미로 채움
- `financial_status.total_assets` / `mobilizable_capital` 최종 자본 동기화
- BI 생성 직후 수동 감리 메모 1회 작성
- `business_lines`/`company_state`를 실제 domain lines와 operating arena 상태에 맞게 채움
- `portfolio_history`가 있으면 TR milestone과 충돌 없음
- source TR `production_density_gate = PASS`
- source TR `avg_bundle_chars` 확인
- source TR `opponent_unique` 확인
- source TR `deal_top_repetition` 확인
- source TR `method_top_repetition` 확인
- `???` 0건
- `validate_bible_structure` 통과
- `tr_batch_harness.py prompt --roadmap {BI}` 입력 성공
- 5-Pass 결과 문서 기록

---

## 11. 실전 규칙 한 줄 요약

**BI는 생성물이 아니라 동기화 산출물이다.**  
한글 장문을 다시 쓰지 말고, `phase0_design`과 `TR draft`를 UTF-8로 읽어 구조화해서 저장하고 5-Pass로 감리한다.
