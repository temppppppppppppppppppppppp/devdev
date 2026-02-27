# 장기 기억 강화 구현 명세 (코드 기반 감사 결과)

작성일: 2026-02-27 (2차 갱신)
기준 커밋: `68b6b93` → 2차 감사 시점 HEAD
참조: `long_term_memory_system_250ep_recommendation.md` (고수준 아키텍처)
참조: `long_term_memory_continuity_part5_audit.md` (PART 5 통과 가능성 점검)
방식: Opus × 4 병렬 코드 감사 → 통합 명세 → 물리 인프라 점검 + PART 5 통합 + 디렉터 주권 재검토

---

## 0. 감사 근거 — 현재 시스템 실제 동작

### 벡터 검색 (vec_memory.py)

- **검색 범위**: `ep_num < current_ep` 필터. 1화~(N-1)화 전량 검색 대상. 화수 상한 없음.
- **저장**: 임베딩(3072d) + summary[:1000] + entity_names[:1000] + event_types. **원문 전체 저장 없음.**
- **FTS5 tokenizer**: `unicode61`. 한국어 형태소 미분리. "헌터길드" ≠ "헌터"+"길드".
- **Arc 내 보너스**: 동일 Arc 내 결과 `distance × 0.9` 우선 부여 → 최근 Arc 편향 존재.

### TruthGate (truth_gate.py) — 6개 검사

| 검사 | 데이터 소스 | 한계 |
|------|------------|------|
| 사망 NPC 행동/대사 | `world_state.dead_npcs` (인메모리) | npc_history 테이블 미참조 |
| 미보유 아이템 | `world_state.active_items` (인메모리) | status="보유"만 추적 |
| 파괴 장소 방문 | `world_state.destroyed[]` (인메모리) | — |
| 스킬 중복 습득 | `world_state.protagonist.skills[]` (인메모리) | — |
| 카르마 범위 초과 | `state_updates` dict 직접 | DB 조회 없음 |
| NPC 역할 무단 변경 | `world_state.alive_npcs[].role_at_intro` | state_updates에 명시적 기재 시만 감지 |

**world_laws 위반 검사: 없음.** world_laws는 프롬프트 주입만, LLM 자발적 준수 의존.

### ContinuityInspector (stage2_validation_pipeline.py L483)

- `prev_arcs = all_refined_arcs` — Arc 전량 비교(상한 없음). 단, Arc 요약 전달 시 `첫화 + 끝화 요약`만(tactical_doc 4500자 절삭). 중간 화 내용 누락.
- ContinuityBlueprintValidator: **최근 30화 window 하드코딩** (`max(1, working_ep - 30)`).

### PreLLMValidator (pre_llm_validator.py)

10개 검증기 **전부 현재 원고 내부만**. 이전 화 참조: 0개. 모두 `passed=True` 고정(advisory).

### FactLedger (fact_ledger.py) — 추적 필드

```
characters: {status, role, relationship, history[]}
numbers:    {value, unit, last_ep, history[]}   ← 누적 비교 로직 없음
items:      {owner, status, history[]}
locations:  {status, history[]}
organizations: {status, history[]}
```

### WorldState — 핵심 갭

| 구조 | 한계 |
|------|------|
| `world_laws[]` | 최대 30개 FIFO. 초과 시 초기 법칙 탈락. **자동 등록 배선 없음.** |
| `alive_npcs[].known_attrs` | 나이/외모/신체/언어/출신 필드 없음. `role_at_intro`만 존재. |
| `active_plots[]` | 최대 30개. 핵심 동기(motivation) 해결 상태 미추적. |
| `timeline[]` | 최대 20개(인메모리). |
| NPC 부상 | protagonist.injuries만 있음. NPC별 부상 구조화 필드 없음. |
| NPC 스킬 | protagonist.skills만 있음. NPC별 스킬 목록 없음. |

### npc_history 테이블 — 미기록 필드

| 필드 | 기록 여부 |
|------|----------|
| status (사망) | ✅ 기록 |
| weapon, level | ✅ 기록 |
| personality_traits, primary_motivation | ✅ 기록 |
| **relation_to_protag** | ❌ 메모리만, DB 미기록 |
| **injury** | ❌ 메모리만 |
| **location** | ❌ 메모리만 |
| **permanent_injuries** | ❌ 메모리만 |

### npc_relationship_edges — 최신값 UPSERT만

이력 없음. `(npc1, npc2) UNIQUE` — 항상 현재 관계만 유지.

---

## 0-B. 물리적 인프라 현황 점검 (2026-02-27 2차 감사)

> LM-A~G 각 컴포넌트가 의존하는 **피지컬 경로**(컨텍스트 전달, DB 조회, 캐싱)가
> 현재 시스템에 실제로 존재하는지 코드 기반으로 검증한 결과.

### 컨텍스트 전달 경로

| 경로 | 현재 값 | 코드 위치 | LM 충분성 |
|------|---------|-----------|----------|
| **max_context_chars** | 700,000자 (~1.05M 토큰) | `config/system.yaml:19` | ✅ 모든 LM 컴포넌트의 advisory 프롬프트 수용 가능 |
| **Stage4 컨텍스트 구조** | Tier1: 30화 full text + Tier2: 30~60화 summary + Tier3: arc summary | `stage4_context_builder.py:420~500` | ✅ LM-C/D/G 포맷팅 결과 삽입 가능 (mandatory_context에 추가) |
| **Director 프롬프트** | structured_warnings 배열 + 이전 화 참조 30화 상한 | `director.py:57` | ✅ advisory 결과는 structured_warnings로 전달 |
| **ContinuityInspector** | Arc 전량 비교 (tactical_doc 4500자 절삭) | `stage2_validation_pipeline.py:483` | ✅ LM-D/G 컨텍스트 포함 가능 |

### DB 조회 경로

| 인프라 | 현재 상태 | 코드 위치 | LM 의존 |
|--------|----------|-----------|---------|
| **manuscripts 테이블** (원고 전문) | ✅ 저장+조회 | `db_manager.py:820` (get_manuscript), `:2027` (get_recent_manuscripts), `:2050` (get_manuscripts_range) | LM-E: 회상 원본 대조 시 필수 |
| **episode_meta 테이블** (요약) | ✅ 저장+조회 | `db_manager.py` | LM-E/G: 장기 요약 참조 가능 |
| **npc_history 테이블** | ✅ append-only, 100/entity | `db_manager.py` | LM-B: NPC 이력 참조 가능 |
| **FactLedger history** | ✅ 100/entity 상한 | `fact_ledger.py:20` (MAX_HISTORY_PER_ENTITY=100) | LM-C: ⚠️ 150화+ 시 초기 이력 탈락 |
| **FactLedger summary** | ✅ 50,000자 | `fact_ledger.py:21` (MAX_SUMMARY_CHARS=50,000) | LM-C: ✅ 충분 |
| **npc_relationship_edges** | ⚠️ UPSERT only, 이력 없음 | `db_manager.py` | LM-D: ❌ 이력 테이블 신규 필요 |
| **world_laws** | ⚠️ 30개 FIFO, 자동등록 없음 | `world_state.py:659` | LM-A: ❌ CRITICAL 핀 + 자동등록 필요 |
| **causal_graph** | ⚠️ Write만 존재, Read 미연결 | `db_manager.py:246`/`:1630`, `stage4_post_processor.py:619` | 보조: ❌ 현재 LM 직접 의존 없음. 후순위. |

### 캐싱/검색 인프라

| 인프라 | 현재 상태 | 코드 위치 | LM 충분성 |
|--------|----------|-----------|----------|
| **VecMemory** (3072d + FTS5 + RRF) | ✅ 전량 검색 | `vec_memory.py` | LM-E: ✅ 회상 원본 에피소드 검색 |
| **Gemini Context Caching** | ✅ 50 entries, 1800s TTL | `base_agent.py:1175~1250` | LM-A/B: ✅ advisory LLM 호출 시 활용 가능 |
| **known_attrs** | ⚠️ `role_at_intro` 1개만 | `world_state.py:695` | LM-B: ❌ age/appearance/physical 등 확장 필요 |
| **Retrospective lookback** | ⚠️ 5화 고정 | `retrospective_validator.py:23` | LM-B/D: ⚠️ 장기 커버리지 부족 (LM 포맷터가 DB 직접 조회로 우회) |
| **ContinuityBlueprint window** | ⚠️ 30화 하드코딩 | `stage2_validation_pipeline.py` | LM-A/D: ⚠️ 60화+ 미커버 (LM 포맷터가 전량 조회로 보완) |

### 결론

LM-A~G 구현에 필요한 **핵심 인프라 3종**(manuscripts DB 조회, 700K 컨텍스트 버짓, VecMemory 검색)은 **이미 존재**.
병목은 인프라 부재가 아니라 **데이터 구조 확장**(known_attrs, npc_relationship_history, world_laws 핀)과
**포맷팅→프롬프트 주입 배선** 미비임.

FactLedger MAX_HISTORY_PER_ENTITY=100은 150화+ 시 초기 이력이 탈락하므로, LM-C 구현 시
NumericHistoryFormatter가 **DB manuscripts 원본에서 재추출하는 폴백 경로**를 고려해야 함.

---

## 0-C. PART 5 감사 결과 반영 (`long_term_memory_continuity_part5_audit.md`)

> `docs/2026-02-27/long_term_memory_continuity_part5_audit.md` 코드 정적 감사 결과를
> 본 명세에 통합한 내용.

### PART 5 판정 vs LM 컴포넌트 매핑

| PART 5 영역 | 현재 판정 | 대응 LM 컴포넌트 | 해소 전략 |
|-------------|----------|------------------|----------|
| L1 (NPC 장기 속성) | 부분 통과 | **LM-B** (NpcDriftAdvisor) | known_attrs 확장 + LLM advisory 대조 |
| L2 (세계관 절대 법칙) | 실패 위험 높음 | **LM-A** (TruthGate 7번째 검사) | Bible→world_laws 자동등록 + CRITICAL 핀 |
| L3 (관계도 장기 누적) | 부분 통과 | **LM-D** (RelationshipHistoryFormatter) | 이력 테이블 + 타임라인 포맷팅 |
| L4 (수치 누적 드리프트) | 실패 위험 매우 높음 | **LM-C** (NumericHistoryFormatter) | 전량 이력 포맷팅 + advisory LLM |
| L5 (회상/플래시백 왜곡) | 실패 위험 높음 | **LM-E** (FlashbackVerifier) | VecMemory 검색 + 원본 대조 |
| L6 (정보 역설) | 실패 위험 높음 | **LM-F** (KnowledgeLedger) | 정보 획득 원장 + 역방향 검출 |
| L7 (장기 서사 구조) | 실패 위험 높음 | **LM-G** (NarrativeContextFormatter) | 동기/약속/스케일 포맷팅 |

### PART 5 POC 필수 요건 대응

| POC 요건 (원문) | 대응 | 비고 |
|----------------|------|------|
| ①L2/L4/L6/L7 차단 가능 검증기(fail-closed 게이트) | **advisory-only 유지** | 디렉터 주권주의 준수. 대신 Director 프롬프트에 `severity=CRITICAL` 경고 시 최우선 심사 지시를 강화 |
| ②retrospective lookback 확장 및 60화+ 전용 검증 경로 | **LM 포맷터가 DB 직접 조회로 우회** | Retrospective lookback 5화 제한은 기존 유지. LM-B/C/D 포맷터는 `npc_history`/`FactLedger`/신규 `npc_relationship_history` 테이블에서 **전량 조회** |
| ③causal_graph read 경로 실연결 | **후순위** | 현재 LM-A~G 어느 컴포넌트도 causal_graph에 직접 의존하지 않음. 향후 인과 추론 강화 시 활용 |
| ④PART 5 시나리오 pass/fail 로그 재현 | **V76 episode_production.jsonl로 부분 커버** + LM advisory 결과 audit_event 기록 | 시나리오 단위 재현은 별도 테스트 프레임워크 필요 |

### DB 샘플 이슈

Part 5 감사에서 확인된 DB 샘플 문제:
- `causal_graph`: 5개 프로젝트 모두 row 0건 (write는 실행되나 LLM이 causal_links를 반환 안 할 때 비축적)
- 일부 DB에 `timeline_entries`, `npc_relationship_edges` 테이블 자체 MISSING
  - **원인**: 해당 테이블은 특정 버전 이후 추가됨. 이전 프로젝트 DB는 마이그레이션 미적용
  - **대응**: LM-D 구현 시 `npc_relationship_history` 테이블을 `_create_tables()`에 추가하면 신규 프로젝트에서 자동 생성. 기존 프로젝트는 `_ensure_tables()` 마이그레이션으로 처리

### 디렉터 주권주의 vs fail-closed 긴장 해소

PART 5 감사는 "fail-closed 게이트" 추가를 권고하나, 이는 **디렉터 주권주의(대원칙 3)**와 직접 충돌:
- 디렉터 주권: Director가 최종 품질 결정권. 검증기가 auto-reject하면 Director 우회.
- 해결: **advisory 강도를 3단계로 분류** (INFO/MAJOR/CRITICAL) + Director 프롬프트에 "CRITICAL advisory는 반드시 해소해야 PASS" 지시 추가

이 방식은 Python이 차단하지 않고(대원칙 1 준수), Director가 판단하되(대원칙 3 준수),
CRITICAL 경고를 무시할 경우 Director 자체의 판단 책임으로 귀속시킴.

---

## 0-D. 디렉터 주권주의 재검토 (LM-A~G 전 컴포넌트)

> 대원칙 3: "Director가 최종 품질 결정권. Chief Writer·Analyst 등은 초안 제출만,
> 합격/불합격/수정 지시는 Director가 내림. Director를 우회하면 안 됨."

### 컴포넌트별 주권 준수 검증

| 컴포넌트 | Python 역할 | LLM 판단 경로 | Director 우회 여부 | 판정 |
|----------|------------|--------------|-------------------|------|
| **LM-A** TruthGate world_law | world_laws 목록 수집·포맷팅 | `_check_world_law_violation()` → `structured_warnings` → Director | ❌ 우회 없음 | ✅ |
| **LM-B** NpcDriftAdvisor | NPC 스냅샷 수집·포맷팅 | flash advisory → `logging.warning` + `audit_event` → Director | ❌ 우회 없음 | ✅ |
| **LM-C** NumericHistoryFormatter | 수치 이력 표 포맷팅 | advisory LLM → `logging.warning` + `audit_event` → Director | ❌ 우회 없음 | ✅ |
| **LM-D** RelationshipHistoryFormatter | 관계 타임라인 포맷팅 | ContinuityInspector 컨텍스트 → Director | ❌ 우회 없음 | ✅ |
| **LM-E** FlashbackVerifier | 회상 마커 감지 + 원본 로드 | flash advisory → warnings → Director | ❌ 우회 없음 | ✅ |
| **LM-F** KnowledgeLedger | 정보 획득 원장 수집/저장 | InfoParadoxChecker (LLM) → Director | ❌ 우회 없음 | ✅ |
| **LM-G** NarrativeContextFormatter | 동기/약속/스케일 포맷팅 | ContinuityInspector 컨텍스트 → Director | ❌ 우회 없음 | ✅ |

### 판정 결론

**7개 컴포넌트 모두 디렉터 주권주의 준수.**

- Python은 데이터 수집·포맷팅·전달만 수행
- "이것이 오류인가?" 판단은 전부 LLM advisory (flash 또는 Director 직접)
- 어떤 컴포넌트도 auto-reject/auto-block을 수행하지 않음
- Director가 CRITICAL advisory를 무시하고 PASS 판정할 자유가 보장됨

### 대원칙 전체 준수 체크

| 대원칙 | 준수 | 근거 |
|--------|------|------|
| 1. Python은 수집만, 판단은 LLM | ✅ | 모든 Formatter/Advisor: Python이 이력·스냅샷 포맷팅만. 임계값 기반 Python 판단 없음 |
| 2. 팩트시트 수정 권한은 LLM만 | ✅ | KnowledgeLedger/motivations/promises: LLM 생성 state_changes에서만 갱신 |
| 3. 디렉터 주권주의 | ✅ | 7개 컴포넌트 모두 advisory-only. Director에 structured_warnings로 전달 |
| 4. 사망 캐릭터 규칙 | ✅ | 기존 TruthGate 유지 + LM-E FlashbackVerifier가 회상 속 사망 NPC 추가 감지 |

---

## 1. LM-A — [L2] 세계관 절대 법칙 강제 (P0)

**현재 한계**: world_laws 배열 존재하나 ①Bible 추출 시 자동 등록 없음 ②TruthGate 미참조 ③30개 FIFO 탈락.

### 1-1. Bible 추출 → world_laws 자동 등록

**파일**: `modules/core/stage0/story_expander.py`
**위치**: Bible 추출 후 후처리 블록

```python
# StageZeroManager 또는 story_expander Bible 생성 직후
for law in bible_result.get("world_laws", []):
    law_text = law if isinstance(law, str) else law.get("text", "")
    if law_text:
        world_state.add_world_law(law_text, established_ep=0)
```

**LLM 프롬프트 수정**: Bible 추출 프롬프트에 `world_laws` 필드 추가:
```yaml
# config/prompts/bible_extraction.yaml (또는 해당 프롬프트)
세계관 절대 법칙을 배열로 반환하라:
"world_laws": ["이 세계에서 마법은 왕족 혈통만 가능", "죽은 자는 되살릴 수 없다", ...]
```

### 1-2. TruthGate 7번째 검사 — `_check_world_law_violation()`

**파일**: `modules/core/truth_gate.py`
**위치**: `validate()` 메서드 내 기존 6개 검사 뒤

```python
def _check_world_law_violation(
    self, manuscript: str, warnings: list, structured_warnings: list
) -> None:
    if not self._world_state:
        return
    laws = self._world_state.get_world_laws()
    if not laws:
        return
    # Python은 법칙 목록 수집·포맷팅만. "위반인가?" 판단은 LLM이.
    # (Python 선검사/필터링 없음 — 오탐 위험 차단)
    laws_text = "\n".join(f"- {l}" for l in laws)
    prompt = (
        f"다음 원고에서 세계관 절대 법칙을 위반한 부분이 있으면 지적하라. "
        f"위반이 없으면 violation=false로 반환하라.\n\n"
        f"【절대 법칙】\n{laws_text}\n\n"
        f"【원고】\n{manuscript[:3000]}"
    )
    result = self._llm_advisory(prompt)  # 기존 _ask 패턴 활용
    if result.get("violation"):
        structured_warnings.append({
            "check": "world_law_violation",
            "severity": "CRITICAL",
            "details": result.get("details", ""),
        })
```

### 1-3. world_laws 상한 보호

**파일**: `modules/core/world_state.py` L659 (`_add_world_law_internal`)

현재: `if len(laws) > 30: laws[:] = laws[-30:]` — 오래된 법칙 탈락.
수정: 중요도 태그 추가. `{"law": "...", "established_ep": 0, "priority": "CRITICAL"}` 에서 `priority=CRITICAL`은 탈락 제외.

```python
# _add_world_law_internal 수정
if len(laws) > 30:
    # CRITICAL 법칙은 보호, 나머지에서 오래된 것 탈락
    critical = [l for l in laws if l.get("priority") == "CRITICAL"]
    others = [l for l in laws if l.get("priority") != "CRITICAL"]
    if len(others) > 30 - len(critical):
        others = others[-(30 - len(critical)):]
    laws[:] = critical + others
```

**구현 난이도**: 낮음 | **예상 비용**: $0 (Python 로직) + flash advisory ~$0.003/화
**삽입 위치**: Stage 0 (등록), Stage 4 TruthGate (검증)

---

## 2. LM-B — [L1] NPC 속성 장기 표류 대응 (P0)

**현재 한계**: `known_attrs`에 나이/외모/신체/언어/출신 없음. `role_at_intro`는 role만 추적. 원고 내 묘사 대조 로직 없음.

### 2-1. NPC known_attrs 필드 확장

**파일**: `modules/core/world_state.py` — `_update_npc_intro_snapshot()` (또는 신규 메서드)
**시점**: NPC 첫 등장 시 (`first_seen_ep` 설정 시점)

```python
# alive_npcs 엔트리에 고정 속성 필드 추가
NPC_IMMUTABLE_FIELDS = [
    "age",           # 나이 (숫자 또는 "52세")
    "appearance",    # 외모 묘사 (키/체형/특징)
    "physical",      # 신체 특성 (의족, 절단, 장애 등)
    "language",      # 언어 능력 (한국어 불가 등)
    "origin",        # 출신 배경 (고졸/현장직 등)
    "occupation_at_intro",  # 최초 직업/지위 (role_at_intro 보완)
]
# known_attrs dict에 위 키로 저장
# {"age": {"value": "52세", "ep": 5}, "physical": {"value": "의족, 오른발 절단", "ep": 9}}
```

**LLM 프롬프트 수정**: NPC 첫 등장 추출 프롬프트에 위 필드 요청 추가.

### 2-2. NpcDriftAdvisor — Stage 4 post-processor

**신규 파일**: `modules/core/npc_drift_advisor.py`

```python
class NpcDriftAdvisor:
    """원고 내 NPC 속성이 초기 스냅샷과 일치하는지 LLM advisory 검사."""

    def check(
        self,
        manuscript: str,
        npc_snapshots: dict,  # {name: {role_at_intro, known_attrs}}
        ep_num: int,
    ) -> list[dict]:
        """
        Returns: [{"npc": str, "attr": str, "expected": str, "found": str, "severity": str}]
        """
        # 1. regex로 등장 NPC 이름 추출 (state_tracker_npc.py 패턴 재사용)
        # 2. known_attrs 있는 NPC만 대상 필터링
        # 3. LLM advisory (flash): "아래 NPC가 스냅샷과 다르게 묘사된 부분을 찾아라"
        # 4. 오탐 최소화: 서사적 변화(성장/부상)와 모순(소멸/역전) 구분 요청
        ...
```

**삽입 위치**: `stage4_post_processor.py` — TruthGate 호출 직후 (기존 L309~337 블록 뒤)

```python
# stage4_post_processor.py post-processor 블록
if self.ctx.world_state and hasattr(self.ctx.world_state, "get_npc_snapshots"):
    _npc_snaps = self.ctx.world_state.get_npc_snapshots(
        names=list(_appearing_npcs)[:10]  # 성능 상한
    )
    if _npc_snaps:
        _drift_advisor = NpcDriftAdvisor()
        _drift_warns = _drift_advisor.check(final_manuscript, _npc_snaps, next_ep)
        for _dw in _drift_warns:
            logging.warning("[LM-B] NPC 속성 표류 감지 ep=%d: %s", next_ep, _dw)
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("npc_drift_detected", "NPC 속성 표류", _dw)
```

**구현 난이도**: 중간 | **예상 비용**: flash ~$0.01/화
**삽입 위치**: Stage 0 (known_attrs 등록), Stage 4 post-processor (대조)

---

## 3. LM-C — [L4] 수치 누적 표류 감지 (P1)

**현재 한계**: `FactLedger.numbers`에 이미 `history[]` 존재. 화별 delta만 봄. 누적 이력을 LLM에 전달하는 경로 없음.

**설계 원칙**: Python은 이력을 포맷팅해서 제공. "이게 비정상인가?" 판단은 LLM이.

### 3-1. NumericHistoryFormatter — Python 역할 (수집·포맷팅만)

**신규 파일**: `modules/core/numeric_history_formatter.py`

```python
class NumericHistoryFormatter:
    """FactLedger.numbers.history → LLM이 읽을 수 있는 포맷으로 변환."""

    def format_for_llm(self, numbers: dict, min_history: int = 5) -> str:
        """
        각 수치 항목의 전체 이력을 표로 반환.
        Python은 수집·포맷팅만. 이상 여부 판단 없음.

        반환 예시:
        [자산]
          4화: 210만원 → 11화: 350만원 → 19화: 800만원 → 28화: 1억 → 67화: 300억

        [전투력]
          1화: 500 → 10화: 750 → 20화: 1200 → 35화: 3800 → 63화: 50000
        """
        lines = []
        for key, data in numbers.items():
            history = data.get("history", [])
            if len(history) < min_history:
                continue
            ep_vals = " → ".join(
                f"{h.get('last_ep', '?')}화: {h.get('value', '?')}"
                for h in history
            )
            lines.append(f"[{key}]\n  {ep_vals}")
        return "\n\n".join(lines) if lines else ""

    def format_world_caps(self, db) -> str:
        """
        세계관 수치 상한(world_cap) 포맷팅.
        Stage 0 Bible에서 LLM이 추출한 값 그대로 전달.
        """
        caps = db.get_canonical_facts(fact_type="world_cap")
        if not caps:
            return ""
        return "\n".join(f"- {c['fact_key']}: {c['value_json']}" for c in caps)
```

### 3-2. LLM advisory 검사

포맷팅된 이력을 **5화마다 Director 또는 독립 advisory LLM**에 전달:

```python
# stage4_post_processor.py — FactLedger 갱신 직후, next_ep % 5 == 0 시점
if next_ep % 5 == 0 and self.ctx.fact_ledger:
    _formatter = NumericHistoryFormatter()
    _num_history = _formatter.format_for_llm(
        self.ctx.fact_ledger.get_numbers(), min_history=5
    )
    _world_caps = _formatter.format_world_caps(self.ctx.current_project.db)
    if _num_history:
        # LLM advisory: Python이 이력 제공, LLM이 판단
        _prompt = (
            "다음 수치 이력에서 서사적 근거 없이 비정상적으로 누적된 표류가 있으면 지적하라.\n\n"
            f"【세계관 수치 상한】\n{_world_caps}\n\n"
            f"【수치 이력】\n{_num_history}"
        )
        _result = self.ctx.agents["director"].ask_advisory(_prompt)
        if _result.get("issues"):
            logging.warning("[LM-C] 수치 누적 표류 advisory ep=%d: %s", next_ep, _result["issues"])
            if callable(getattr(self.ctx, "audit_event", None)):
                self.ctx.audit_event("numeric_drift_advisory", "수치 누적 표류", {"ep": next_ep})
```

### 3-3. Stage 0: 세계관 수치 상한 등록

```python
# story_expander.py Bible 추출 후 — LLM이 추출한 값 그대로 저장
for cap_key, cap_val in bible_result.get("world_caps", {}).items():
    db.upsert_canonical_fact(cap_key, "world_cap", cap_val, first_ep=0)
```

**삽입 위치**: Stage 0 (세계관 상한 등록), Stage 4 post-processor (매 5화 이력 전달)

**구현 난이도**: 낮음 | **예상 비용**: flash ~$0.003/5화 (=~$0.0006/화)

---

## 4. LM-D — [L3] 관계도 장기 표류 감지 (P1)

**현재 한계**: `npc_relationship_edges` UPSERT 전용 — 현재 관계만 유지. 이력 없음. 점진적 역전 감지 불가.

### 4-1. 신규 테이블 — npc_relationship_history

**파일**: `modules/core/db_manager.py` — `_create_tables()` 또는 마이그레이션

```sql
CREATE TABLE IF NOT EXISTS npc_relationship_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    npc1           TEXT NOT NULL,
    npc2           TEXT NOT NULL,
    old_relation   TEXT,
    new_relation   TEXT NOT NULL,
    change_ep      INTEGER,
    arc_no         INTEGER,
    change_reason  TEXT,          -- state_changes.relationship_changes[].justification
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rel_hist_pair
    ON npc_relationship_history(npc1, npc2, change_ep);
```

`upsert_npc_relationship_edge()` 내부에서:
```python
# 기존 값 조회 → 변경 시 history INSERT
old = self._get_current_relation(npc1, npc2)
if old and old != new_relation:
    self.insert_relationship_history(npc1, npc2, old, new_relation, ep, arc_no, reason)
self.upsert_npc_relationship_edge(npc1, npc2, new_relation, ep, arc_no)
```

### 4-2. RelationshipHistoryFormatter — Python 역할 (수집·포맷팅만)

**설계 원칙**: Python은 `npc_relationship_history` 에서 이력을 읽어 타임라인으로 포맷팅. "역전이 비정상인가?" 판단은 LLM이.

```python
class RelationshipHistoryFormatter:
    """npc_relationship_history → LLM이 읽을 수 있는 타임라인으로 변환."""

    def format_for_llm(self, db, npc_pairs: list[tuple]) -> str:
        """
        주어진 NPC 쌍 목록의 관계 이력을 타임라인으로 반환.
        Python은 수집·포맷팅만. 이상 여부 판단 없음.

        반환 예시:
        [A ↔ B]
          1화: 원수 (등록) → 23화: 경쟁 (이유: 거래 이후)
          → 45화: 중립 (이유: 없음) → 73화: 협력 (이유: 없음)
        """
        lines = []
        for npc1, npc2 in npc_pairs:
            history = db.get_relationship_history(npc1, npc2)
            if len(history) < 2:
                continue
            steps = " → ".join(
                f"{h['change_ep']}화: {h['new_relation']}"
                f"{'(이유: ' + h['change_reason'] + ')' if h.get('change_reason') else '(이유: 없음)'}"
                for h in history
            )
            lines.append(f"[{npc1} ↔ {npc2}]\n  {steps}")
        return "\n\n".join(lines) if lines else ""
```

**LLM advisory 호출**: Stage 2 Arc 생성 전, ContinuityInspector 컨텍스트에 포함:

```python
# stage2_preflight.py 또는 Arc 컨텍스트 빌드 시
_rel_formatter = RelationshipHistoryFormatter()
_rel_timeline = _rel_formatter.format_for_llm(db, appearing_npc_pairs)
if _rel_timeline:
    # ContinuityInspector 프롬프트에 추가 — LLM이 판단
    entity_registry["relationship_timelines"] = _rel_timeline
```

**삽입 위치**: Stage 2 Arc 컨텍스트 빌드 (이력 전달), Stage 4 post-processor (관계 변경 기록)

**구현 난이도**: 중간 | **예상 비용**: flash advisory Arc당 ~$0.005 (LLM이 이미 보는 컨텍스트에 포함 시 추가 비용 $0)

---

## 5. LM-E — [L5] 회상/플래시백 오염 감지 (P1)

**현재 한계**: 회상 감지 로직 전무. TruthGate의 recall_patterns는 "회상에서 사망 NPC 허용" 필터일 뿐, 내용 검증 없음.

### 5-1. FlashbackDetector + Verifier

**신규 파일**: `modules/core/flashback_verifier.py`

```python
class FlashbackVerifier:
    """회상/플래시백 장면 감지 및 원본 사건 대조."""

    FLASHBACK_MARKERS = [
        r"회상", r"그때", r"기억했다", r"떠올렸다", r"눈을 감[으면]",
        r"그 시절", r"예전에", r"돌이켜보면", r"몇 년 전",
    ]

    def detect_flashbacks(self, manuscript: str) -> list[dict]:
        """원고에서 회상 구간 추출."""
        # regex로 마커 주변 200자 추출
        # 반환: [{"text": "...", "marker": "회상", "position": int}]
        ...

    def verify(
        self,
        flashbacks: list[dict],
        current_ep: int,
        vec_memory,        # VecMemory 인스턴스
        db,                # DBManager 인스턴스
    ) -> list[dict]:
        """
        각 회상 구간에 대해:
        1. vec_memory로 참조 에피소드 검색
        2. manuscripts 테이블에서 원본 로드
        3. LLM advisory: 회상 내용 vs 원본 일치 여부
        """
        warnings = []
        for fb in flashbacks:
            orig_ep = vec_memory.retrieve_high_res_context(
                fb["text"], current_ep, n_results=1
            )
            if not orig_ep:
                continue
            orig_manuscript = db.get_manuscript(orig_ep)
            if not orig_manuscript:
                continue
            result = self._llm_compare(fb["text"], orig_manuscript[:2000])
            if result.get("mismatch"):
                warnings.append({
                    "type": "flashback_contamination",
                    "current_ep": current_ep,
                    "referenced_ep": orig_ep,
                    "mismatch": result["mismatch"],
                    "severity": "MAJOR",
                })
        return warnings
```

**삽입 위치**: Stage 4 Director 검증 단계 (원고 확정 후, post-processor 초반)

**구현 난이도**: 높음 | **예상 비용**: flash ~$0.01/회상 장면
**Note**: manuscripts 테이블에 원본 저장 경로 확인 필요 (현재 logs/ 파일 저장 방식이면 DB 경로 조회)

---

## 6. LM-F — [L6] 정보 역설 감지 (P2)

**현재 한계**: episode_bibles.knowledge_map 필드 존재하나 누적 추적 없음. "누가 무엇을 아는가" 원장 없음.

### 6-1. KnowledgeLedger

**신규 파일**: `modules/core/knowledge_ledger.py`
**저장**: `anchors` 테이블 `key="knowledge_ledger"` (기존 인프라, 테이블 추가 불필요)

```python
class KnowledgeLedger:
    """캐릭터별 정보 획득 원장. anchors 테이블에 JSON 저장."""

    @staticmethod
    def _empty():
        return {
            "characters": {},
            # {name: {"knows": [{"fact": str, "source_ep": int, "source_type": str}]}}
            "secrets": {},
            # {fact_id: {"text": str, "known_by": [str], "revealed_ep": int}}
            "last_updated_ep": 0,
        }

    def update_from_state_changes(self, ep_num: int, state_changes: dict) -> None:
        """reveals + knowledge_map → KnowledgeLedger 갱신 (Python 수집)."""
        for reveal in state_changes.get("reveals", []):
            # 비밀 X가 공개됨 → known_by에 주인공 추가
            ...
        for k, v in state_changes.get("knowledge_map", {}).items():
            # "witnesses": [...], "mistaken_beliefs": [...]
            ...

    def format_for_llm(self, character: str) -> str:
        """
        캐릭터가 알고 있는 정보 목록을 포맷팅해서 반환.
        Python은 목록 수집만. "알 수 있는가?" 판단은 LLM이.

        반환 예시:
        [주인공이 알고 있는 정보]
        - "X의 정체" (14화, 직접 목격)
        - "그림자단 존재" (9화, 직접 조우)
        """
        ...
```

### 6-2. InfoParadoxChecker (LLM advisory, 1인칭 시점 전용)

```python
class InfoParadoxChecker:
    """정보 역설 LLM advisory. POV=1인칭 시점 작품에서만 활성화."""

    def check(
        self,
        manuscript: str,
        pov_character: str,
        knowledge_summary: str,  # KnowledgeLedger에서 생성
        ep_num: int,
    ) -> list[dict]:
        # prompt: "1인칭 화자 {pov_character}가 이 원고에서 사용하는 정보 중,
        #          아래 '알고 있는 것' 목록에 없는 정보가 있으면 지적하라."
        ...
```

**삽입 위치**: Stage 4 post-processor (KnowledgeLedger 갱신), Director 검증 (InfoParadoxChecker)

**구현 난이도**: 높음 | **오탐 위험**: 중간~높음
**Note**: POV 설정이 1인칭인 경우에만 활성화 권장

---

## 7. LM-G — [L7] 서사 구조 붕괴 감지 (P2)

**현재 한계**: active_plots 추적 있으나 핵심 동기 해결 상태, 약속 이행, Arc 스케일 역행 추적 없음.

### 7-1. WorldState 확장 — motivations + promises

**파일**: `modules/core/world_state.py` — `_INIT_STATE`

```python
# _INIT_STATE 추가
"motivations": [],
# [{"text": "아버지 누명 해소", "status": "active", "since_ep": 1, "resolved_ep": None}]
"promises": [],
# [{"text": "이 검을 당신에게 주겠다", "promiser": "주인공",
#   "promisee": "NPC_A", "since_ep": 19, "status": "pending"}]
```

### 7-2. NarrativeContextFormatter — Python 역할 (수집·포맷팅만)

**설계 원칙**: Python은 동기/약속/스케일 이력을 목록으로 포맷팅. "이게 붕괴인가?" 판단은 LLM이.

**신규 파일**: `modules/core/narrative_context_formatter.py`

```python
class NarrativeContextFormatter:
    """WorldState의 motivations/promises/arc_scales → LLM 컨텍스트로 변환."""

    def format_motivations(self, motivations: list[dict], current_ep: int) -> str:
        """
        동기 목록 + 현재 상태를 포맷팅.
        Python은 상태만 수집. "재개방이 문제인가?" 판단 없음.

        반환 예시:
        [동기]
        - "아버지 누명 해소" (1화 등록, 50화 resolved → 51화~ 재등장 감지됨)
        - "배신자 처단" (7화 등록, 현재 active, 현재 68화)
        """
        ...

    def format_promises(self, promises: list[dict], current_ep: int) -> str:
        """
        약속 목록 + 경과 화수를 포맷팅.
        Python은 경과 화수만 계산. "미이행이 문제인가?" 판단 없음.

        반환 예시:
        [약속/서약]
        - "이 검을 당신에게 주겠다" 주인공→NPC_A (19화, 현재 68화 — 49화 경과, pending)
        - "반드시 복수하겠다" 주인공→자신 (13화, fulfilled 45화)
        """
        ...

    def format_arc_scales(self, arcs: list[dict]) -> str:
        """
        Arc별 위기 스케일 키워드 포맷팅. LLM 생성 데이터(tactical_doc)에서 추출.
        Python은 Arc 목록만 나열. "역행인가?" 판단 없음.

        반환 예시:
        Arc 1: 마을 존망 위기 / Arc 2: 왕국 멸망 위기 / Arc 3: 대륙 전쟁
        Arc 4: 세계 붕괴 / Arc 5 (현재): 마을 패권 다툼
        """
        ...
```

**LLM advisory 호출**: Stage 2 Arc 생성 전, Director 또는 ContinuityInspector에 컨텍스트로 포함:

```python
# stage2_preflight.py Arc 생성 전
_nav_formatter = NarrativeContextFormatter()
_nav_context = "\n".join([
    _nav_formatter.format_motivations(world_state.get("motivations", []), current_ep),
    _nav_formatter.format_promises(world_state.get("promises", []), current_ep),
    _nav_formatter.format_arc_scales(all_refined_arcs),
])
if _nav_context.strip():
    # 프롬프트에 포함 — LLM이 서사 구조 이상 여부를 판단
    arc_context["narrative_structure_summary"] = _nav_context
```

**삽입 위치**: Stage 2 Arc 컨텍스트 빌드 (포맷팅 전달), Stage 4 post-processor (motivations/promises 갱신)

**구현 난이도**: 중간 | **예상 비용**: ContinuityInspector 기존 LLM 호출에 컨텍스트 추가 → 추가 비용 $0에 가까움

---

## 8. DB/인프라 변경 요약

| 변경 | 종류 | 필요성 |
|------|------|--------|
| `npc_relationship_history` 테이블 신규 | DDL | L3 필수 |
| `world_state._INIT_STATE` 확장 (motivations, promises) | 코드 | L7 |
| `known_attrs` 키 추가 (age, appearance, physical, language, origin) | 코드 | L1 |
| `world_laws` 우선순위 태그 (priority) | 코드 | L2 |
| `anchors` 키 추가 (knowledge_ledger) | 런타임 | L6 |
| `canonical_facts` `fact_type="world_cap"` | 런타임 | L4 |
| `validation.yaml` 섹션 추가 | 설정 | L2 (world_laws 설정), L4 (check_interval), L7 (enabled 플래그) |

**신규 테이블**: 1개 (`npc_relationship_history`)
**기존 테이블 스키마 변경**: 없음
**기존 테이블 신규 활용**: `anchors`, `canonical_facts`

---

## 9. 신규 컴포넌트 파일 목록

| 파일 | 항목 | Python 역할 | LLM 판단 경로 |
|------|------|------------|--------------|
| `modules/core/npc_drift_advisor.py` | L1 | NPC 이름 추출 + 스냅샷 포맷팅 | flash advisory |
| `modules/core/numeric_history_formatter.py` | L4 | 수치 이력 표 포맷팅 | Director/advisory LLM |
| `modules/core/relationship_history_formatter.py` | L3 | 관계 타임라인 포맷팅 | ContinuityInspector 컨텍스트 |
| `modules/core/flashback_verifier.py` | L5 | 회상 마커 감지 + 원본 로드 | flash advisory |
| `modules/core/knowledge_ledger.py` | L6 | 정보 획득 원장 수집/저장 | InfoParadoxChecker (LLM) |
| `modules/core/narrative_context_formatter.py` | L7 | 동기/약속/스케일 포맷팅 | ContinuityInspector 컨텍스트 |
| `truth_gate.py` (기존 확장) | L2 | world_laws 전달 | `_check_world_law_violation()` (LLM) |

---

## 10. 구현 로드맵 및 우선순위

| 순서 | 항목 | 우선순위 | 난이도 | 비용 영향 | 테스트 기준 |
|------|------|---------|--------|----------|------------|
| 1 | **LM-A-1**: Bible → world_laws 자동 등록 | P0 | 낮음 | $0 | Stage 0 테스트: world_laws ≥ 1건 |
| 2 | **LM-A-2**: TruthGate `_check_world_law_violation()` | P0 | 낮음 | ~$0.003/화 | truth_gate 단위 테스트 |
| 3 | **LM-A-3**: world_laws CRITICAL 핀 보호 | P0 | 낮음 | $0 | 30개 초과 시 CRITICAL 법칙 보존 확인 |
| 4 | **LM-B-1**: NPC known_attrs 필드 확장 | P0 | 중간 | $0 | Stage 0 후 known_attrs 저장 확인 |
| 5 | **LM-B-2**: NpcDriftAdvisor Stage 4 삽입 | P0 | 중간 | ~$0.01/화 | 불일치 시 audit_event 발생 확인 |
| 6 | **LM-C**: 수치 이력 포맷팅 → advisory LLM | P1 | 낮음 | ~$0.0006/화 | 포맷 출력 + advisory 결과 로그 확인 |
| 7 | **LM-D**: npc_relationship_history + 타임라인 포맷팅 | P1 | 중간 | $0 (컨텍스트 포함) | 관계 변경 시 history 기록 확인 |
| 8 | **LM-E**: FlashbackVerifier | P1 | 높음 | ~$0.01/회상 | 회상 포함 화에서 감지 확인 |
| 9 | **LM-F**: KnowledgeLedger | P2 | 높음 | ~$0.01/화 | reveals 이벤트 → KL 갱신 확인 |
| 10 | **LM-G**: 동기/약속/스케일 포맷팅 → ContinuityInspector 컨텍스트 | P2 | 중간 | $0 (컨텍스트 포함) | 포맷 출력이 Arc 컨텍스트에 포함 확인 |

---

## 11. 설계 원칙 준수 체크 (0-D 재검토 결과 통합)

| 원칙 | 준수 방식 | 2차 검증 결과 |
|------|----------|-------------|
| **Python은 수집만, 판단은 LLM** | 모든 컴포넌트: Python은 이력/스냅샷/타임라인 **포맷팅**만. "이게 문제인가?" 판단은 LLM advisory. 임계값 기반 Python 자체 판단 없음. | ✅ 7/7 컴포넌트 확인 |
| 팩트시트 수정 권한은 LLM만 | KnowledgeLedger/WorldState 동기·약속는 LLM 생성 state_changes에서만 갱신. Python이 직접 기입 안 함. | ✅ |
| **디렉터 주권주의** | 모든 검사 advisory. Director에 structured_warnings로 전달, PASS/REJECT는 Director. **PART 5 "fail-closed" 권고는 advisory 강도 3단계(INFO/MAJOR/CRITICAL)로 대체.** | ✅ 0-D 전수 검증 완료 |
| 사망 캐릭터 규칙 | TruthGate 기존 검사 유지 + FlashbackVerifier가 회상 속 사망 NPC 행동 추가 감지. | ✅ |
| SQLite 단일 DB | 신규 테이블 1개(npc_relationship_history). 나머지 anchors/canonical_facts 기존 인프라 재사용. | ✅ |
| 대규모 리팩토링 금지 | 각 Stage 기존 코드에 hook 포인트만 추가. | ✅ |
| **피지컬 인프라 충분성** | 핵심 3종(manuscripts DB, 700K 컨텍스트, VecMemory)이 이미 존재. 병목은 데이터 구조 확장과 배선 미비. | ✅ 0-B 검증 완료 |

---

## 부록: 현재 시스템 감지 범위 지도 (코드 감사 기반)

```
                  1화     10화    30화    60화    100화+
                  │       │       │       │       │
PreLLMValidator ──●───────●───────●───────●───────●── (현재 화 내부만)
                  │
ContinuityBlueprint ──────●───────●             (최근 30화 window 하드코딩)
                  │
ContinuityArc ────●───────●───────●───────●───── (Arc 전량, 단 요약만)
                  │
TruthGate ────────●───────●───────●───────●───── (WorldState 스냅샷, 인메모리)
                  │
FactLedger ───────●───────●───────●───────●───── (전량, 단 누적비율 미분석)
                  │
WorldState ───────●───────●───────●───────●───── (전량, 단 NPC 30명 상한)
                  │
VecMemory ────────●───────●───────●───────●───── (전량, 단 요약 1000자만)
                  │
world_laws ───────●───────●               ×      (30개 FIFO, 60화+ 탈락 위험)
                  │
known_attrs ──────●       ×               ×      (현재: role_at_intro만 1개)
                  │
npc_rel_history ──×                               (현재: UPSERT만, 이력 없음)
```

---

---

## 12. PART 5 통합 결론

### 현재 시스템 상태

PART 5(L1~L7, 35개 시나리오)를 현재 시스템은 **전부 통과하지 못함**.
그러나 통과 불가의 원인은 "인프라 부재"가 아닌 **"포맷팅→프롬프트 주입 배선 미비"**:

- **manuscripts DB** 전문 저장·조회: ✅ 존재 (get_manuscript / get_manuscripts_range)
- **700K 컨텍스트 버짓**: ✅ 존재 (Gemini 1M 토큰)
- **VecMemory 전량 검색**: ✅ 존재 (3072d + FTS5 + RRF)
- **FactLedger history 100/entity**: ✅ 존재 (150화+ 시 보완 필요)
- **Gemini 캐싱 50 entries**: ✅ 존재 (advisory LLM 비용 절감)

### LM-A~G 구현 시 예상 전환

| 영역 | 현재 | LM 구현 후 |
|------|------|-----------|
| L1 | 부분 통과 | **통과** (known_attrs 확장 + NpcDriftAdvisor) |
| L2 | 실패 위험 높음 | **대폭 개선** (TruthGate 7번째 검사 + CRITICAL 핀) |
| L3 | 부분 통과 | **통과** (npc_relationship_history + 타임라인 포맷팅) |
| L4 | 실패 위험 매우 높음 | **대폭 개선** (NumericHistoryFormatter + advisory) |
| L5 | 실패 위험 높음 | **대폭 개선** (FlashbackVerifier + 원본 대조) |
| L6 | 실패 위험 높음 | **개선** (KnowledgeLedger, 오탐 위험 잔존) |
| L7 | 실패 위험 높음 | **개선** (NarrativeContextFormatter, 구조적 한계 잔존) |

### 후순위 과제 (LM 완료 후)

1. `causal_graph` read 경로 실연결 — 인과 추론 강화용 (현재 LM 직접 의존 없음)
2. Retrospective lookback 5→10+ 확장 검토 (LM 포맷터가 DB 직접 조회로 우회하므로 urgent하지 않음)
3. PART 5 시나리오 단위 자동 재현 테스트 프레임워크 (V76 JSONL로 부분 커버)

---

*1차: 4개 Opus/Sonnet 병렬 에이전트 코드 감사(2026-02-27) → 통합 작성*
*2차: 물리적 인프라 점검 + PART 5 감사 통합 + 디렉터 주권 재검토(2026-02-27)*
*참조 파일: vec_memory.py, truth_gate.py, context_advisor.py, db_manager.py,*
*world_state.py, fact_ledger.py, state_tracker_npc.py, continuity_inspector.py,*
*pre_llm_validator.py, stage2_validation_pipeline.py, stage4_post_processor.py,*
*stage4_context_builder.py, base_agent.py, retrospective_validator.py, config/system.yaml*
