# Codex Order: TF-55 사전 코드 검증

> **목적**: 코드 수정 전 불확실 사항 확인. 보고서 작성만. 코드 수정 금지.
> **출력(고정)**: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/code-verification-result.md`
> **분석 방식**: 파일 직접 읽기만. 셸 명령어(`rg`, `grep` 등) 금지.

---

## 0) 강제 제약

- 코드 수정, 설정 변경, 파일 생성(출력 파일 제외), 파일 삭제 금지.
- 결론 섹션: 확인된 사실만. 개선안/추천/의견 금지.
- 파일이 없으면 `파일 없음`으로 기록하고 계속.

---

## 배경

Codex 감사 결과, advisory chain 7개 모듈 중 5개가 전 세션 발화 0건으로 확인됐다.
비활성화 전에 두 가지를 코드에서 직접 확인해야 한다.

**불확실 사항 A**: 5개 모듈의 발화 0건이
  (a) 모듈 내부 guard 조건에 걸려 LLM 자체가 실행 안 된 것인지,
  (b) LLM은 실행됐지만 감사에 사용한 마커 문자열이 실제 로그 문자열과 달랐던 것인지.

**불확실 사항 B**: VecMemory hits=0인 씬 쿼리(`장면1:`)의 생성 경로가
`_build_scene_query()` 단일 경로인지, 다른 경로도 있는지.

---

## Task 1: 5개 모듈의 guard 조건 및 실제 로그 마커 확인

### 읽을 파일

```
C:/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py
```

### 확인할 메서드 5개

아래 각 메서드를 읽고 다음 두 가지를 보고한다.

**메서드 목록:**
- `_advisory_npc_drift()`
- `_advisory_truth_gate()`
- `_advisory_rel_drift()`
- `_advisory_long_term_rep()`
- `_advisory_numeric_drift()`

**각 메서드에서 확인할 항목:**

(1) **Guard 조건**: LLM 호출에 도달하기 전에 `return []`로 빠져나오는 조건이 있는가?
  - 예: `if next_ep % 5 != 0: return []`
  - 예: `if not _ws or not hasattr(_ws, ...): return []`
  - 예: `if not _npc_snaps: (LLM 호출 없이 종료)`
  - 각 guard 조건을 정확히 인용한다.

(2) **실제 로그 마커**: `logging.info(...)` 또는 `logging.warning(...)`에서
  Director로 전달 시 출력하는 문자열을 정확히 인용한다.
  - `\uXXXX` 유니코드 이스케이프가 있으면 디코딩해서 함께 표기한다.
  - 감사에서 사용한 마커: `FlashbackVerifier->Director`, `NpcDriftAdvisor->Director` 등 `->` 형식.
  - 실제 코드의 마커가 `→`(유니코드 화살표)인지, `→`(ASCII `->`)인지, 아니면 다른 형식인지 확인한다.

(3) **LLM 호출 위치**: `llm_ask(...)` 또는 `self._truth_gate_llm_ask(...)` 호출이 있는 줄 번호.
  없으면 "LLM 호출 없음"으로 기록.

---

## Task 2: 씬 쿼리 생성 경로 확인

### 읽을 파일 (순서대로)

```
C:/Users/wjjo/Desktop/글도비/modules/core/context_advisor.py
```

### 확인 항목

(1) `_build_scene_query()` 메서드 전체를 읽고 반환 문자열 형식을 확인한다.
  - 반환 예시: `"장면1: ..."` 형태인가?
  - 입력 파라미터와 반환 타입을 정확히 인용한다.

(2) `_build_stage4_slots()` 내에서 `_build_scene_query()` 호출 위치와
  결과를 어떤 `source`로 슬롯에 추가하는지 확인한다.
  - `RetrievalSlot(...)` 생성 시 `source=` 파라미터가 있는가? 없는가?
  - 없으면 기본 source가 무엇인지 `RetrievalSlot` dataclass 정의에서 확인한다.

(3) `context_advisor.py` 전체에서 `"장면1"` 또는 `scene_query`가 등장하는
  다른 위치가 있는지 확인한다. (줄 번호만 기록)

(4) `RetrievalSources` 클래스/상수 정의를 찾아 현재 정의된 source 목록을 전부 인용한다.

---

## Task 3: NpcDriftAdvisor 내부 확인

### 읽을 파일

```
C:/Users/wjjo/Desktop/글도비/modules/core/npc_drift_advisor.py
```

### 확인 항목

(1) `check()` 메서드 시그니처와 내부에서 LLM을 호출하는 조건을 확인한다.
  - LLM 호출 전 guard 조건이 있는가? 있으면 정확히 인용.
  - LLM이 실제로 호출되면 어떤 로그를 남기는가?

(2) `check()`가 빈 리스트 `[]`를 반환하는 경로를 모두 나열한다.

---

## 출력 형식 (고정)

```markdown
# TF-55 코드 검증 결과

> 검증일: 2026-03-04

## Task 1: Advisory 모듈 Guard 및 마커 확인

### _advisory_npc_drift()
- Guard 조건: (인용)
- 실제 로그 마커: (정확한 문자열)
- LLM 호출 위치: (줄 번호 또는 "없음")
- 감사 마커 일치 여부: 일치 / 불일치 / 확인불가

### _advisory_truth_gate()
(동일 형식)

### _advisory_rel_drift()
(동일 형식)

### _advisory_long_term_rep()
(동일 형식)

### _advisory_numeric_drift()
(동일 형식)

---

## Task 2: 씬 쿼리 생성 경로

- _build_scene_query() 반환 형식: (인용)
- _build_stage4_slots() 호출 위치 및 source: (인용)
- "장면1" 등장 줄 번호 (다른 위치): (목록)
- RetrievalSources 정의 전체: (인용)

---

## Task 3: NpcDriftAdvisor 내부

- check() Guard 조건: (인용)
- 빈 리스트 반환 경로: (목록)
- LLM 호출 로그: (인용)

---

## 확인된 사실 요약

- 발화 0건 원인 (guard 차단 vs 마커 불일치): ...
- 씬 쿼리 생성 경로 단일/복수: ...
- NpcDriftAdvisor LLM 실행 여부: ...
- TF-55 구현 영향 사항: (사실만, 의견 없이)
```

---

## 체크리스트

- [ ] 코드 수정 없음
- [ ] 셸 명령어 미사용
- [ ] 로그 마커 유니코드 디코딩 포함
- [ ] Guard 조건 정확 인용
- [ ] 출력 파일 경로 준수
