# 덴시피케이션 하네스(Densification Harness) 실행 가이드

> **⚠️ DEPRECATED — 이 문서는 `docs/blockguide/treatment-densification-harness-v1.md` (v1.1 강화판)으로 대체되었습니다.**
> **무협물은 `docs/wuxguide/treatment-densification-harness-v1.md`를 참조하세요.**
> 이 파일은 기록 보존용으로만 남겨둡니다.

이 문서는 '차합설(chaebol_allowance_zero)' 프로젝트의 Block 7~70 구간의 밀도를 Block 1~6 수준으로 끌어올리기 위한 정량적 기준과 워크플로우를 정의한다.

## 1. Step 3: 밀도 게이트 (Density Gates)

모든 블록은 다음의 정량적 기준을 통과해야 `fixed` 상태로 전이될 수 있다.

| 지표 | 최소 기준 | 비고 |
|------|-----------|------|
| **핵심 필드 글자 수** | 800자 이상 | context, event_villain, solution, reward 합산 |
| **템플릿 유사도** | 30% 이하 | 이전 3개 블록과의 문장 구조 유사도 검사 |
| **역사적 이벤트** | 1건 필수 | `config/historical_events_2018_2022.json` 내 데이터 주입 |
| **고유 적대자** | 블록당 1명 | 아크 내 동일 적대자 반복 시 전술적 변화 필수 서술 |
| **구체적 사물(Item)** | 1개 필수 | 계약서, 출입표, 장부, 사진 등 실물 증거 언급 |
| **조사 및 문법** | 오류 0건 | "로서/으로서", "을/를" 등 기계적 오류 전수 교정 |

## 2. Step 5: 농축용 입력 팩 (Enrichment Input Pack)

농축기(Densifier)에 전달될 입력 데이터는 다음과 같이 구성된다.

```json
{
  "source_skeleton": { "block_id": "Block 21", "title": "새벽 식판", "...": "기존 데이터" },
  "external_assets": {
    "historical_event": { "year": 2018, "event": "최저임금 인상", "impact": "인건비 부담 증가" },
    "bigshot_pool": ["해당 아크의 외부 거물 데이터"],
    "item_catalog": ["해당 섹션의 키 아이템"]
  },
  "global_context": {
    "gap_12y": "2006-2018 주인공의 행적(의도적 잠행)",
    "current_capital": "36억"
  }
}
```

## 3. 실행 프로세스

1. **Phase 1 (Block 7~15)**: 장례식 종료 및 초기 자본(10억대) 형성기 집중 농축.
2. **Phase 2 (Block 16~35)**: 12년 공백의 이유가 드러나는 '회상' 주입 및 역사적 이벤트(최저임금, 미중 무역) 본격 연결.
3. **Phase 3 (Block 36~70)**: 외부 거물(은행장, 가문 본가 인사) 투입을 통한 판의 확대.

---

## 4. 즉시 적용 대상 (Step 16)

다음의 템플릿 구문은 사용을 전면 금지하며, 발견 시 즉시 반려한다.
- "그는 먼저 전생의 윤성그룹은~" (금지)
- "이번 한 번의 흔들림으로 꺾일 수 있다는 걸 안다" (금지)
- "이제는 한 번 쓰고 버릴 도련님이 아니라~" (금지)
- "장례식장 운영실로서" (조사 오류 금지)
