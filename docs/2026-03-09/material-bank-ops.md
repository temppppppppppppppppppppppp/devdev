# Material Bank 운영 메모

> 대상 DB: `test_material/material_bank.db`
> 목적: 수집 원본 DB를 **집필용 재료 은행**으로 안정화한다.
> 기준일: 2026-03-09

---

## 1. 역할 분리

- 원본 테이블 `events / npcs / crises / sector_chains / market_data`는 **수집 원본**이다.
- 집필과 프롬프트 투입에는 `material_bank_events / material_bank_npcs / material_bank_crises / material_bank_sector_chains / material_bank_market_data` 뷰만 사용한다.
- 제외 대상은 `material_bank_exclusions`에 기록한다.
- 정제 실행 정보와 usable 건수는 `material_bank_meta`에 저장한다.
- `material_bank_source_meta`는 source 단위 메타 카탈로그다.
  - `domain / source_group / scope_type / fit / use_modes / meta_tags / row_counts`를 담는다.
  - 현대판타지 TR/BI JSON 설계 시 "이 재료를 어떤 용도로 써야 하는가"를 빠르게 걸러내는 용도로 사용한다.

이 원칙이 필요한 이유:

- 수집 단계는 “많이 모으기”가 목적이라 노이즈가 일부 섞여도 허용된다.
- 집필 단계는 Phase 0/1에서 바로 재사용해야 하므로 placeholder, 추상 슬롯, 깨진 섹터 연결을 제거해야 한다.
- 하네스의 연속성 보정은 DB가 아니라 Python/NPC tracker/복선 원장이 담당한다.

---

## 2. 현재 usable 건수

`python -X utf8 test_material/query_material_bank.py audit --json` 기준:

| 테이블 | raw | usable | 제외 |
|---|---:|---:|---:|
| events | 3,490 | 3,158 | 332 |
| npcs | 860 | 815 | 45 |
| crises | 268 | 268 | 0 |
| sector_chains | 185 | 107 | 78 |
| market_data | 18,989 | 18,989 | 0 |

주요 제외 사유:

- `events`: 핵심 필드가 여전히 placeholder 상태인 교차검증/마스터 이벤트
- `npcs`: 개별 인물이 아니라 갈등/구조/확장 같은 추상 슬롯
- `sector_chains`: 원본 파손으로 의미 있는 시너지 복원이 어려운 행

---

## 3. 정제 명령

```powershell
python -X utf8 test_material/material_bank_postprocess.py
python -X utf8 test_material/query_material_bank.py audit
```

정제 스크립트가 하는 일:

1. DB 백업 생성
2. `X1` 교차통합 이벤트 텍스트 정리
3. `X2` 연도별 자본 시뮬레이션 자연어화
4. `P2` 전설 인물 자료를 NPC 스키마로 재구성
5. `X4` 위기 접두/접미 노이즈 제거
6. unusable 행을 `material_bank_exclusions`로 격리
7. `material_bank_*` usable 뷰 재생성
8. source 단위 메타를 `material_bank_source_meta`로 재구축

---

## 4. 조회 명령

단일 테이블 검색:

```powershell
python -X utf8 test_material/query_material_bank.py search `
  --table events `
  --sector "조선/해운" `
  --fit modern_fantasy `
  --source-group sector `
  --year-start 2006 `
  --year-end 2012 `
  --limit 10
```

Phase 0/1 번들 생성:

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --sectors "조선/해운,금융/은행" `
  --fit modern_fantasy `
  --source-group sector `
  --year-start 2006 `
  --year-end 2012 `
  --keyword "서브프라임,조선" `
  --limit-events 12 `
  --limit-npcs 8 `
  --limit-crises 6 `
  --limit-sector-chains 6 `
  --limit-market-data 12
```

source 카탈로그 확인:

```powershell
python -X utf8 test_material/query_material_bank.py catalog `
  --domain modern_econ `
  --source-group sector `
  --limit 10
```

메타를 함께 출력해서 LLM 입력으로 넘기기:

```powershell
python -X utf8 test_material/query_material_bank.py bundle `
  --sectors "조선/해운,금융/은행" `
  --fit modern_fantasy `
  --source-group sector `
  --year-start 2018 `
  --year-end 2022 `
  --with-meta
```

권장 출력 사용법:

- Phase 0: `events 8~12`, `npcs 6~8`, `crises 4~6`, `sector_chains 3~5`, `market_data 10~20`
- Phase 1 배치: 직전 블록 상태 + NPC 추적표 + 복선 원장 + material bundle만 넣는다
- raw 테이블을 통째로 주입하지 않는다
- `fit / source_group / meta_tags`로 먼저 범위를 줄인 뒤 번들을 뽑는 것이 안전하다

---

## 5. 품질 규칙

- `material_bank_*` 뷰만 “집필 투입 가능”으로 간주한다.
- `sector_chains`는 특히 엄격하게 걸러야 한다. raw 테이블에는 exploratory 초안이 섞여 있다.
- `P2`는 전설 인물/멘토/라이벌 레퍼런스용이며, 연속 등장 NPC로 그대로 쓰지 않는다.
- `X2`는 사건이 아니라 연도별 자본 기준선 자료다. 자본 곡선 설계에만 사용한다.
- continuity 필드(`capital_before`, `relationship_delta.before`, `foreshadow/callback`)는 material bank가 아니라 하네스의 교정/검증 파이프라인이 책임진다.
- `material_bank_source_meta`는 row를 대체하지 않는다. row 본문은 여전히 각 테이블에서 읽고, source meta는 검색 축과 용도 판정에만 쓴다.
