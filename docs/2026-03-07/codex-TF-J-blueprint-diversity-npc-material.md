# Codex TF-J: Arc 다양성 강화 + CW 배경 NPC 재료 주입

> **근거**: projects/0001 Stage 2-3 전수 조사 (Arc 5개, Blueprint 20개, 로그 전량) + 2차 조사 (Stage별 컨텍스트/토큰/인과 분석)
> **확신도**: 99% — 6차 병렬 조사 (NPC 경로/프롬프트/코드/인과 분석/토큰 예산/캐싱) + 실물 데이터 교차 검증
> **대원칙 준수**: Python은 수집만 + Director 주권 불변 + 팩트시트 LLM만
> **LLM 추가 호출**: 0회 (프롬프트 변경 + Python 수집만)

---

## 1. 문제 요약

projects/0001 Stage 2-3 실물 데이터 검증에서 발견된 구조적 품질 이슈:

| ID | 등급 | 내용 | 수치 근거 |
|----|------|------|-----------|
| DIV-1 | P1 | 캐릭터 극심 편중 — 16화(Ep.5~20) 동안 실질 2인(한시우+박성호) | 64씬 중 한시우 63씬(98%), 박성호 31씬(48%, 7화 연속 전화만) |
| DIV-2 | P1 | 공간 단조 — Ep.7~18 (12화 연속) 전 씬 SW사무실 | 64씬 중 54씬(84%) 동일 장소 |
| DIV-3 | P2 | Blueprint tension_level 전량 미기록 | 64씬 전량 `?` — 스키마에 필드 자체 미정의 |
| DIV-4 | P2 | Blueprint scene_4 cliffhanger 고착 | 16화 중 15화(93%) scene_4=cliffhanger |
| DIV-5 | P1 | CW에 배경 NPC 활용 지시 부재 — 투자사에 직원 0명 | CW 프롬프트에 NPC 추가 장려/유도 규칙 없음 |

---

## 2. 근본 원인: Arc가 모든 것을 지배한다

### 2차 조사 핵심 발견: 개입 지점은 Stage 2(Arc)이다

**Blueprint(Stage 3)에 다양성 지시를 넣는 것은 구조적으로 효과가 매우 제한적이다.** Arc가 지정한 장소/NPC를 95%+ 추종하는 행동 패턴 때문이다 (규칙이 아닌 LLM 추종 패턴). 이유:

```
Treatment Block (curr_block)
  -> Arc tactical_doc (Stage 2, 화당 500자+, 전체 3-15K자)
    -> Blueprint arc_focus (Stage 3, 해당 화 발췌, 최대 15K자)  <-- Arc에 종속
      -> CW common_context (Stage 4, tactical_doc 전문 + Blueprint 전체)  <-- 이중 종속
```

| 근거 | 데이터 |
|------|--------|
| Blueprint 장소 추종률 | **95%+** — Arc에 없는 새로운 장소를 만든 사례 **0건** (LLM 행동 패턴, 코드 강제 아님) |
| Blueprint NPC 추종률 | **~100%** — Arc에 없는 NPC 독자 추가 1건뿐 (9화 리스크관리팀장, Arc에 간접 언급 있음). Blueprint가 Arc 범위 내 미시 다양화는 구조적으로 가능하나, 실물 데이터상 자발적 추가 빈도 극히 낮음 |
| 12화 연속 단일 장소의 원인 | **100% Arc tactical_doc** — Arc 3~4가 9화 연속 "SW사무실"만 지정 |

**실물 검증**:
- Arc 2 tactical_doc: 3화 모두 "사무실" 중심 → Blueprint 3화 모두 사무실
- Arc 3 tactical_doc: 4화 전부 "사무실 only" → Blueprint 4화 전부 사무실
- Arc 4 tactical_doc: 5화 전부 "오피스 only" → Blueprint 5화 전부 사무실
- Arc 5 tactical_doc: 19~20화에 "성북동 본가" 등장 → Blueprint 19~20화에서 장소 다양화 발생

**결론**: Arc가 다양하면 Blueprint도 자동으로 다양해진다. Arc가 단조로우면 Blueprint/CW가 아무리 노력해도 단조로울 수밖에 없다.

### Stage별 토큰 여유 분석

| Stage | 현재 사용량 | 절대 한도 | 여유 | 다양성 지시 추가 영향 |
|-------|-----------|----------|------|---------------------|
| **Stage 2 (Arc)** | **15~43KB** | 1,000KB | **950KB+ 여유** | 무시 가능 (~1KB 추가) |
| Stage 3 (Blueprint) | 16~38KB | 1,000KB | 920KB+ 여유 | 무시 가능이나 **효과 없음** |
| Stage 4 (CW) | **185~445KB** | 1,000KB | **가장 빡빡** | 배경 NPC 힌트 ~1KB만 허용 |

**Stage 2가 토큰 여유 최대 + 인과적 지배력 최대 → 다양성 지시의 유일한 정답.**

---

## 3. 패치 설계

### 3-1. 대원칙 검증

| 대원칙 | 준수 | 근거 |
|--------|------|------|
| Python은 수집만, 판단은 LLM | 준수 | Python은 장소/NPC 힌트 수집만. 다양성 판단은 Arc LLM이 수행 |
| 팩트시트 수정 권한은 LLM만 | 해당 없음 | NPC 팩트시트 미변경 |
| Director 주권주의 | 준수 | Director 판정 로직 미변경 |
| 사망 캐릭터 | 해당 없음 | |

### 3-2. 설계 원칙

1. **다양성 지시는 Arc(Stage 2)에 넣는다** — 하위 Stage에 넣으면 Arc의 장소/NPC 결정을 벗어날 수 없음
2. **Blueprint에는 넣지 않는다** — Arc가 이미 다양하면 Blueprint는 자동 추종. Blueprint에 지시해봐야 Arc와 충돌만 발생
3. **CW에는 배경 NPC 재료만 준다** — Arc/Blueprint가 정한 씬 내에서 무명 배경 인물 활용 유도 (이것은 Arc 레벨이 아닌 원고 레벨 문제)
4. **NPC 이름을 강제하지 않는다** — "사무실 직원", "카페 점원" 같은 역할 힌트만 제공

---

## 4. 패치 상세

### 패치 1 (P1): Arc 생성 프롬프트에 공간/인물 다양성 지시

**파일**: `config/prompts/ensemble.yaml`
**위치**: `ENSEMBLE_ARC_PROMPT` (L3) 내 "서사 흥미 설계" 섹션 (L25~29 부근)

**추가 내용**:
```yaml
### 공간/인물 다양성 규칙
- 공간 다양성: 각 에피소드의 tactical_doc에서 주인공이 활동하는 장소를 다양화하라. 사무실/오피스 같은 단일 장소에 3화 이상 연속 머물지 마라. 카페, 거래소, 차 안, 외부 미팅 장소, 거리, 다른 인물의 공간 등을 활용하여 공간 이동을 만들어라.
- 인물 배치: 주인공 혼자만 등장하는 에피소드를 2화 이상 연속하지 마라. 기존 NPC와의 대면(전화가 아닌 직접), 또는 새로운 조력자/적대자/배경 인물과의 상호작용을 배치하라. 투자사에는 직원이 있고, 거래소에는 브로커가 있고, 카페에는 손님이 있다.
```

**효과**: Arc LLM이 tactical_doc 작성 시 공간/인물을 다양화. 이 tactical_doc이 Blueprint→CW로 자동 전파되므로 하위 Stage도 자연스럽게 다양화.

**위험**: Arc가 불필요한 장소 이동을 만들어 서사 일관성이 깨질 가능성 → 낮음 ("3화 이상 연속"은 관대한 기준. 위치 연속성 검증(V70.1)이 이미 존재하여 급격한 이동 방지)

**토큰 영향**: ~500자 추가 → Stage 2 현재 15~43KB 대비 무시 가능 (950KB+ 여유)

---

### 패치 2 (P1): CW 프롬프트에 배경 NPC 활용 규칙 추가

**파일**: `config/prompts/chief_writer.yaml`
**위치**: `COMMON_RULES` 또는 `WRITING_GUIDELINES` 섹션, 기존 규칙 뒤

**추가 내용** (규칙 15):
```yaml
15. 배경 인물 활용: 장소에 자연스러운 배경 인물(직원, 점원, 경비원, 행인 등)을 적극 활용하라. 이름을 붙일 필요는 없다. "사무실 직원이 커피를 가져왔다", "로비 경비원이 고개를 숙였다" 등 장면에 생동감을 주는 무명 인물을 배치하라. 단, Blueprint에 명시된 핵심 캐릭터의 역할을 대체하면 안 된다.
```

**효과**: CW가 Arc/Blueprint가 정한 씬 내에서 배경 NPC를 자율 생성. "투자사에 직원 0명" 문제 해소.

**위험**: 낮음 — "이름 없이 역할만" + "핵심 캐릭터 대체 금지"로 제한. 기존 NPC 추적 시스템(3-5C)은 KeyNPCs만 대상이므로 간섭 없음.

**토큰 영향**: ~200자 → Stage 4 현재 185~445KB 대비 무시 가능

---

### 패치 3 (P1): 장소 기반 배경 인물 힌트 주입 (Python 수집)

**파일**: `modules/core/stage4_context_builder.py`
**위치**: `mandatory_context` 조립부 (NPC 요약 주입 직후)

**신규 함수**: `_suggest_ambient_npcs(blueprint: dict) -> str`

```python
def _suggest_ambient_npcs(blueprint: dict) -> str:
    """[TF-J] Blueprint 씬 장소 기반 배경 인물 힌트 생성.

    Python은 장소 키워드 매칭만 수행. 어떤 인물을 실제로 쓸지는 CW가 판단.
    """
    _LOCATION_HINTS = {
        "사무실": "직원, 비서, 인턴, 배달 기사",
        "오피스": "직원, 비서, 인턴, 배달 기사",
        "카페": "바리스타, 다른 손님, 종업원",
        "레스토랑": "웨이터, 소믈리에, 다른 손님",
        "호텔": "프론트 직원, 벨보이, 컨시어지",
        "병원": "간호사, 접수 직원, 다른 환자",
        "거래소": "트레이더, 브로커, 경비원",
        "증권": "영업 직원, 애널리스트, 다른 투자자",
        "은행": "은행원, 지점장, 대기 고객",
        "법원": "서기, 변호사, 방청객",
        "공항": "승무원, 세관 직원, 다른 승객",
        "택시": "택시 기사",
        "거리": "행인, 노점상, 경찰",
        "학교": "교사, 학생, 교직원",
        "본가": "집사, 가사 도우미, 경호원",
        "저택": "집사, 가사 도우미, 경호원",
    }
    hints = []
    sb = blueprint.get("scene_breakdown", {})
    if not isinstance(sb, dict):
        return ""
    for scene_key in sorted(sb.keys()):
        scene = sb[scene_key]
        if not isinstance(scene, dict):
            continue
        loc = str(scene.get("location", ""))
        matched = []
        for keyword, npcs in _LOCATION_HINTS.items():
            if keyword in loc:
                matched.append(npcs)
        if matched:
            hints.append(
                f"  {scene_key} ({loc[:30]}): "
                f"{', '.join(set(', '.join(matched).split(', ')))}"
            )
    if not hints:
        return ""
    return (
        "[TF-J 배경 인물 힌트]\n"
        "아래는 각 씬 장소에 자연스러운 배경 인물 후보입니다. "
        "이름 없이 역할만으로 활용하세요. 반드시 사용할 필요는 없습니다.\n"
        + "\n".join(hints)
    )
```

**호출 위치**: `stage4_context_builder.py`의 `mandatory_context` 조립 → NPC 요약 직후 append

**대원칙 준수**: Python은 키워드 매칭으로 힌트 수집만. 실제 활용 여부는 CW(LLM)가 판단. "반드시 사용할 필요는 없습니다" 명시.

**토큰 영향**: 씬당 ~50자 × 4씬 = ~200자 → Stage 4 대비 무시 가능

---

### 패치 4 (P2): Blueprint tension_level 프롬프트 명시

**파일**: `config/prompts/ensemble.yaml`
**위치**: `BLUEPRINT_GENERATION_PROMPT`의 씬 JSON 예시 부분

**변경**: 기존 `"tension": 5` 예시를 더 명시적으로:
```yaml
각 씬에 반드시 "tension_level" (1~10 정수)을 기재하라. 1=평온, 5=긴장, 8=절정, 10=최고조.
```

**효과**: LLM이 tension_level 필드를 반환하도록 유도. 긴장도 곡선 분석 가능.

---

### 패치 5 (P2): Director 심사에 공간/인물 다양성 항목 추가

**파일**: `config/prompts/director.yaml`
**위치**: NC-3 consistency_checklist 카테고리 (현재 12개 → 13개)

**추가 항목**:
```yaml
13. scene_variety — 씬 장소가 과도하게 단일하지 않은가? 주인공 외 인물(배경 인물 포함)과의 상호작용이 있는가?
```

**파일**: `modules/domain/agents/director_ensemble.py`
**위치**: `_nc3_keys` 리스트에 `"scene_variety"` 추가

---

## 5. 왜 Blueprint(Stage 3)에는 넣지 않는가

| 이유 | 근거 |
|------|------|
| **Arc에 종속** | Blueprint는 Arc tactical_doc의 장소/NPC를 95%+ 추종. Arc가 "사무실"이면 Blueprint가 "카페"를 독자 추가할 수 없음 |
| **충돌 위험** | Blueprint에 "다양한 장소를 사용하라" → Arc에는 "사무실"만 있음 → Blueprint가 Arc를 위반하여 일관성 손상 가능 |
| **중복 지시** | Arc가 이미 다양하면 Blueprint는 자동 추종. Blueprint에 별도 지시 불필요 |
| **실물 증거** | Arc 5(19~20화)에서 "성북동 본가" 지정 → Blueprint가 자동으로 "다이닝 룸/복도/서재"로 세분화. Arc가 다양하면 Blueprint도 따라감 |

---

## 6. 비패치 사항 (현행 유지)

### 모니터 2대→3대 유령 증가 (Arc 5)
**판단**: P2 유보. 서사 영향 미미. cross-Arc 소지품 추적의 경미한 한계.

### PATCH-B "이전 Arc 소지품 소멸" 반복
**판단**: 정상 동작. LLM 누락 → auto-correct 복원. 시스템이 올바르게 작동 중.

### "시작 내공 100%→0%" 수정
**판단**: 적절한 auto-correct. TF-45 근본 원인 이미 해소.

### Arc 4 1차 REJECT(65점)
**판단**: 시스템 정상 작동. Patch Mode → PASS(100점) 복구.

---

## 7. 변경 파일 목록

| 파일 | 변경 내용 | 등급 |
|------|----------|------|
| `config/prompts/ensemble.yaml` | **Arc 프롬프트(ENSEMBLE_ARC_PROMPT)에 공간/인물 다양성 규칙 추가** | P1 |
| `config/prompts/chief_writer.yaml` | CW 규칙 15 "배경 인물 활용" 추가 | P1 |
| `modules/core/stage4_context_builder.py` | `_suggest_ambient_npcs()` 신규 + mandatory_context 주입 | P1 |
| `config/prompts/ensemble.yaml` | tension_level 필수 기재 지시 추가 | P2 |
| `config/prompts/director.yaml` | NC-3 체크리스트 12번째 항목 `scene_variety` 추가 | P2 |
| `modules/domain/agents/director_ensemble.py` | `_nc3_keys`에 13번째 `"scene_variety"` 추가 | P2 |

**P1 패치: 3파일 3곳. P2 패치: 3파일 3곳. 총 5파일 6곳.**

> **[감리 수정 이력]**: 3회 독립 감리(2026-03-07) 결과 반영 — Patch 1 파일 경로 `analyst.yaml`→`ensemble.yaml` 수정, NC-3 키 개수 11→12 오류 수정(현재 12→13), "Blueprint 무력" PARTIAL로 완화, "Director REJECT" 근거 없는 주장 삭제.

---

## 8. 테스트 계획

| # | 테스트 | 검증 내용 |
|---|--------|----------|
| 1 | `test_suggest_ambient_npcs_office` | 사무실 장소 → "직원, 비서" 힌트 포함 |
| 2 | `test_suggest_ambient_npcs_cafe` | 카페 장소 → "바리스타" 힌트 포함 |
| 3 | `test_suggest_ambient_npcs_no_match` | 매칭 없는 장소 → 빈 문자열 반환 |
| 4 | `test_suggest_ambient_npcs_empty_blueprint` | 빈 Blueprint → 빈 문자열 반환 |
| 5 | `test_nc3_keys_includes_scene_variety` | `_nc3_keys`에 `scene_variety` 포함 |

기존 테스트 영향: 없음 — 프롬프트 텍스트 변경과 신규 함수 추가만.

회귀 테스트: `pytest tests/ -q --tb=short` 기준선 3,642 passed

---

## 9. 위험 요소

| 위험 | 확률 | 완화 |
|------|------|------|
| Arc LLM이 다양성 규칙을 과잉 해석 | 낮음 | "3화 이상 연속"은 관대한 기준. V70.1 위치 연속성 검증이 급격한 이동 방지 |
| CW가 배경 NPC를 과다 생성 | 낮음 | "이름 없이 역할만" + "핵심 캐릭터 대체 금지" 제한 |
| 장소 힌트 딕셔너리 누락 | 중간 | 16개 키워드로 주요 장소 커버. 매칭 안 되면 빈 문자열 (안전) |
| Arc 다양성이 서사 일관성 해침 | 낮음 | "연속 3화"만 금지. 투자사 → 거래소/카페/미팅 장소 이동은 투자물에서 자연스러움 |
| Stage 4 토큰 예산 압박 | 없음 | 배경 인물 힌트 ~200자. Stage 4 현재 185~445KB, 한도 1,000KB |

---

## 10. 확신도 평가

| 조사 항목 | 결과 | 조사 차수 |
|-----------|------|-----------|
| Arc tactical_doc → Blueprint 인과 지배 | **확인** — 장소 추종률 95%+, NPC 100% | 2차 |
| Stage별 토큰 여유 | Stage 2 최대 여유 (950KB+), Stage 4 최소 여유 | 2차 |
| Blueprint에 넣으면 효과 제한적인 이유 | **확인** — Arc 장소를 95%+ 추종하는 LLM 행동 패턴. 미시 다양화는 구조적으로 가능하나 빈도 극히 낮음 | 2차+감리 |
| CW 배경 NPC 자유 추가 가능 | **확인** — 코드상 제한 없음 | 1차 |
| Context Caching 구조 | Stage 2/3/4 전부 캐싱 사용, 다양성 지시는 stable_context에 포함될 수 있음 | 2차 |
| NPC 경로 전수 추적 | 5개 경로 전량 확인 (Bible→Arc→Blueprint→CW→Director) | 1차 |
| 실물 데이터 — 장소/NPC | 64씬 전량 확인, 84% 단일 장소, 98% 한시우 | 1차 |
| 실물 데이터 — Arc→Blueprint 대조 | 20화 전량 대조, Blueprint 독자 장소 추가 0건 | 2차 |
| Auto-correct/모순 | PATCH-B 정상, 모니터 유령 1건(P2) | 1차 |
| 프롬프트 정확한 삽입 위치 | `ensemble.yaml` L3 ENSEMBLE_ARC_PROMPT "서사 흥미 설계" 섹션 (L25~29) 확인 | 2차+감리 |

**종합 확신도: 99%** — 6차 병렬 조사 + 3회 독립 감리로 "Arc가 모든 것을 지배한다"는 인과 구조를 실물 데이터(20화 전량 대조)로 검증. 다양성 지시는 **Stage 2(Arc) 프롬프트가 최적 개입 지점**이며, Stage 3(Blueprint)에 넣으면 효과가 매우 제한적임을 확인. 파일 경로·키 개수·과대 주장 3건 감리 결과 반영 완료.

---

## 11. 실행 순서

**P1 (즉시)**:
1. `config/prompts/ensemble.yaml` — **Arc 프롬프트(ENSEMBLE_ARC_PROMPT)에 공간/인물 다양성 규칙 추가**
2. `config/prompts/chief_writer.yaml` — CW 규칙 15 배경 인물 활용 추가
3. `modules/core/stage4_context_builder.py` — `_suggest_ambient_npcs()` 구현 + 호출 배선

**P2 (후순위)**:
4. `config/prompts/ensemble.yaml` — tension_level 필수 기재 지시
5. `config/prompts/director.yaml` + `director_ensemble.py` — NC-3 scene_variety 추가

**검증**:
6. 신규 테스트 5개 작성
7. `pytest tests/ -q` 전량 통과 확인
8. projects/0001 Stage 2 재실행으로 실전 효과 확인 (선택)
