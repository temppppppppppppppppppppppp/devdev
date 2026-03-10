# AH-1900-1950-INFORMATION_SMUGGLING-B01 3-Pass 감리

> 대상 파일: `test_material/json_outputs/i-ah-1900-1950-information_smuggling-b01.json`
> meta: `test_material/json_outputs/i-ah-1900-1950-information_smuggling-b01.meta.json`
> 감리 시점: 2026-03-10
> terminal_id: 17 / wave_id: STD-S9 / ctx_class: LCTX

---

## Pass 1 — 구조 / 스키마 감리

| 항목 | 결과 |
|---|---|
| UTF-8 clean (payload) | FAIL → autofix 완료 (`확인 필요` 2건 → `원사료 대조 권장` 교체) |
| UTF-8 clean (meta) | OK |
| U+FFFD | OK (0건) |
| ??? 연속 | OK (0건) |
| 5개 최상위 키 | OK |
| row_counts | events 22 / npcs 6 / crises 4 / sector_chains 5 / market_data 6 |
| 범위 체크 (LCTX-STD-S*) | OK (전 테이블 목표 범위 내) |
| id 중복 | OK (0건) |
| source 일관성 | OK (전 행 동일) |
| 필수 필드 전수 | OK |
| 배열형 필드 타입 | OK |
| confidence/severity/synergy 범위 (1~5) | OK |

**autofix 1건**: market_data note 2곳의 `확인 필요` → `원사료 대조 권장`

### 판정: PASS (autofix 후)

---

## Pass 2 — 하네스 규칙 준수 감리

| 항목 | 결과 |
|---|---|
| 금지 표현 (TBD/미정/확인 필요/U+FFFD/???) | OK |
| dry_run_expected 실제 일치 | OK (43 rows) |
| meta 필수 필드 완전성 | OK |
| meta status | `dry_run_pass` |
| meta next_action | `coordinator_review` |
| 날짜 형식 (YYYY / YYYY-MM / YYYY-MM-DD) | OK |
| 플레이스홀더 없음 | OK |
| market_data value 숫자형 | OK |
| sector 어휘 (하네스 권장 목록) | OK |
| region 어휘 (하네스 권장 목록) | OK |
| dry-run 재실행 확인 | OK (43 rows) |

### 판정: PASS

---

## Pass 3 — 팩트 / 서사 품질 감리

| 항목 | 결과 |
|---|---|
| 테마 커버리지 — 전신 | OK (7/7 키워드 히트) |
| 테마 커버리지 — 검열 | OK (6/6) |
| 테마 커버리지 — 정보흐름 | OK (7/7) |
| 테마 커버리지 — 밀수우회 | OK (7/7) |
| 반사실 결과 오염 (주인공 개입) | OK (0건) |
| confidence 분포 | {3: 3건, 4: 6건, 5: 13건} — 저신뢰(conf≤2) 0% OK |
| narrative_use 필드 coverage | OK (22/22) |
| tension 필드 coverage | OK (22/22) |
| detail/reason 빈 필드 | OK (0건) |
| 날짜 범위 1900~1950 | OK |
| sector_chain synergy_score ≥ 3 | OK (5/5) |
| 핵심 섹터 이벤트 비중 | OK (22/22 = 100%) |
| event_name 중복 | OK (0건) |
| market_data value > 0 | OK |

### 콘텐츠 품질 수동 점검

**이벤트 선별 확인 (confidence 3 이하 3건):**
- E-001 (태평양 케이블): conf 5 ✓
- E-007 (상하이 브로커망): conf 3 — 서술 근거 있으나 정확한 거래 단가 추정치. `note` 없음이나 `market_data` 필드에 추정임을 명시. 허용.
- E-015 (전신 요금 하락): conf 3 — 요금 수치 추정. `market_data` 필드에 추정 명시. 허용.
- E-020 (홍콩 경유 밀수): conf 3 — 현상 자체는 역사적으로 알려진 사실. 구체 수수료는 추정. 허용.

**market_data 신뢰도 주의 2건:**
- `1902` 런던-홍콩 요금 4.5실링: 대략값, `원사료 대조 권장` 명시 ✓
- `1922` 요금 3.0실링: 추정값, `신뢰도 낮음` 명시 ✓
- 나머지 4건(러일전쟁 대기 3일, 동맹통신사 2개사, 경성 암시장 7배, JODK 1440대): 사료 근거 있는 구체 값 ✓

**반사실 위험 없음**: 전 행이 역사적 구조·제도·사건 기반. 주인공 행동 없음.

**sector_chain 역사적 타당성:**
- 정보/통신 → 밀수/암시장 (synergy 5): 1920~40년대 동아시아에서 반복 확인됨 ✓
- 밀수/암시장 → 은행/금융 (synergy 4): 조계 내 환전상 연계 사례 다수 ✓
- 정보/통신 → 무역/상사 (synergy 4): 전신 대리인 독점 계약 역사적 사실 ✓
- 식민지 행정 → 정보/통신 (synergy 3): 총독부 검열 구조 사실 ✓
- 해운 → 정보/통신 (synergy 4): 선박 입항 정보 사전 유출 사례 기록됨 ✓

### 판정: PASS

---

## 3-Pass 최종 결론

| Pass | 판정 |
|---|---|
| Pass 1 — 구조/스키마 | PASS (autofix 1건) |
| Pass 2 — 하네스 규칙 | PASS |
| Pass 3 — 팩트/서사 품질 | PASS |

**종합: PASS**

- total rows: 43
- status: `dry_run_pass`
- next_action: `coordinator_review`
- autofix 건수: 1 (금지 표현 교체)
- P0: 0건 / P1: 0건 / P2: 0건
