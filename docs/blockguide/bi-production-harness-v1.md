# BI 생산 하네스 v1

> 인코딩: UTF-8
> 작성일: 2026-03-09
> 근거: `treatment-production-harness-v2.md` + `tr-bi-3pass-audit.md` + 실제 BI 오염 사례
> 목적: **Windows/PowerShell 환경에서 한글 BI JSON이 `???`로 오염되지 않도록, 생성-동기화-감리 절차를 강제**
> 출력: `bible/0_bi_{work_id}.json`

---

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
- 장기 복선, NPC 타임라인, 자본 곡선은 반드시 `phase0_design`에서 읽어 온다.
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
  ↓ MasterBible / ProjectData / FinanceHUD 뼈대
Phase 2: 결정적 동기화
  ↓ plot_roadmap / portfolio_history / npc_timeline / seeds 주입
Phase 3: UTF-8 저장 + 오염 탐지
  ↓ ??? / � / 공백 주인공명 / stale title 탐지
Phase 4: TR↔BI 정합성 검증
  ↓ protagonist / 길이 / edge title / hash or title-line sync
Phase 5: 5-Pass 감리
  ↓ PASS 1~5 전부 통과 시 확정
```

---

## 4. Phase 0: 원천 고정

### 4.1 필수 확인

BI 생성 전에 아래를 먼저 확인한다.

- `phase0_design` UTF-8 파싱 성공
- `TR draft` UTF-8 파싱 성공
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
- `plot_roadmap[n].title == TR[n].title`
- `plot_roadmap[n].summary`는 `TR[n].content.context`
- `plot_roadmap[n].capital_before/after`는 `TR[n].genre_ext`에서 복사

### 6.2 주인공 핵심 필드

아래 3개는 반드시 동일해야 한다.

- `MasterBible.ProjectData.MetaInfo.title`
- `MasterBible.ProjectData.CoreIdentity.protagonist`
- `MasterBible.FinanceHUD.Protagonist.actual_truth.name`

### 6.3 파생 섹션

아래는 `phase0_design` 기반으로 넣는다.

- `capital_curve`
- `npc_timeline`
- `Seeds`
- `HistoricalEvents`
- `GenreRules`

원칙:

- `phase0_design`에 있는 문장은 그대로 최대한 활용한다.
- 새로 쓰는 설명은 짧고 요약적이어야 한다.

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

### 7.3 오염 탐지

최소 탐지 패턴:

```powershell
rg -n "\?\?\?" bible\0_bi_chaebol_ent_empire.json
rg -n "�" bible\0_bi_chaebol_ent_empire.json
```

해석:

- 콘솔 표시 문제일 수 있으므로 `rg`와 `python -X utf8` 둘 다로 확인한다.
- 파일 내부에 실제 `???`가 있으면 인코딩 오염 또는 손상된 문자열로 본다.

---

## 8. 5-Pass 감리

### PASS 1: 인코딩/파싱

통과 조건:

- UTF-8 읽기 성공
- JSON 파싱 성공
- `???`, `�` 0건

실패 시 조치:

- 손상 필드가 넓으면 부분 수정 금지
- `phase0_design + TR draft` 기준으로 BI 재생성

### PASS 2: 최소 스키마

통과 조건:

- `validate_bible_structure` 통과
- `MasterBible.ProjectData.MetaInfo.title` 존재
- `plot_roadmap` 길이 70

### PASS 3: 내부 정합성

통과 조건:

- `CoreIdentity.protagonist == FinanceHUD.Protagonist.actual_truth.name`
- `MetaInfo.title` 정상 한글
- `portfolio_history` 증가 흐름과 `TR draft` 주요 자본 이력 충돌 없음

### PASS 4: TR↔BI 동기화

통과 조건:

- `BI.plot_roadmap` 길이 = 70
- 첫/마지막 title 일치
- 전 title 리스트 순서 일치
- 가능하면 `title/capital_before/capital_after` 기준 비교 통과

### PASS 5: 품질 감리

통과 조건:

- 한국어 필드에 `??`, `???` 없음
- 다른 작품 흔적 없음
- arc 명칭, NPC 이름, 회사명 일치
- `plot_roadmap`가 stale copy가 아님

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
- BI 파일명 ASCII 사용
- BI 저장은 UTF-8 only
- `plot_roadmap`는 TR에서 복사
- 주인공명 2중 위치 일치
- `???` 0건
- `validate_bible_structure` 통과
- `tr_batch_harness.py prompt --roadmap {BI}` 입력 성공
- 5-Pass 결과 문서 기록

---

## 11. 실전 규칙 한 줄 요약

**BI는 생성물이 아니라 동기화 산출물이다.**  
한글 장문을 다시 쓰지 말고, `phase0_design`과 `TR draft`를 UTF-8로 읽어 구조화해서 저장하고 5-Pass로 감리한다.
