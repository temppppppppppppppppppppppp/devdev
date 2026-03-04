# TF-55 코드 검증 결과

> 검증일: 2026-03-04

## Task 1: Advisory 모듈 Guard 및 마커 확인

### _advisory_npc_drift()
- Guard 조건:
  - `if _ws and hasattr(_ws, "get_npc_role_snapshot"):` (line 1763)
  - `if _npc_snaps:` (line 1765)
  - `if not _ms: continue` (line 1770)
  - `if _drifts:` (line 1773)
  - `if _drift_all:` (line 1779)
- 실제 로그 마커:
  - 원문: `"[NpcDriftAdvisor\u2192Director] %d건 표류 감지 전달"` (line 1794)
  - 디코딩: `[NpcDriftAdvisor→Director] %d건 표류 감지 전달`
- LLM 호출 위치:
  - `NpcDriftAdvisor(llm_ask=self._truth_gate_llm_ask)` (line 1766)
  - `_drift_advisor.check(manuscript=_ms, npc_snapshots=_npc_snaps, ep_num=next_ep)` (line 1772)
- 감사 마커 일치 여부: 불일치 (`->` 아님, `→` 사용)

### _advisory_truth_gate()
- Guard 조건:
  - `if not _ms: continue` (line 1733)
  - `if _tg_result.get("structured_warnings"):` (line 1740)
  - `if _tg_warnings_all:` (line 1747)
- 실제 로그 마커:
  - 원문: `"[TruthGate\u2192Director] %d개 경고 전달"` (line 1751)
  - 디코딩: `[TruthGate→Director] %d개 경고 전달`
- LLM 호출 위치:
  - `TruthGate(..., llm_ask=self._truth_gate_llm_ask)` (line 1727)
  - `_tg.validate(manuscript=_ms, state_updates=..., npc_registry=...)` (line 1735)
- 감사 마커 일치 여부: 불일치 (`->` 아님, `→` 사용)

### _advisory_rel_drift()
- Guard 조건:
  - `if next_ep < 5: return []` (line 1958-1959)
  - `if _db and hasattr(_db, "get_all_relationship_pairs_with_history"):` (line 1962)
  - `if _rel_timeline:` (line 1966)
  - `if not _ms: continue` (line 1971)
  - `if _rd_warns:` (line 1978)
  - `if _rd_all:` (line 1982)
- 실제 로그 마커:
  - 원문: `"[RelationshipDriftAdvisor\u2192Director] %d건 관계 표류 감지"` (line 1996)
  - 디코딩: `[RelationshipDriftAdvisor→Director] %d건 관계 표류 감지`
- LLM 호출 위치:
  - `RelationshipDriftAdvisor(llm_ask=self._truth_gate_llm_ask)` (line 1967)
  - `_rd_advisor.check(_ms, ep_num=next_ep, relationship_timeline=_rel_timeline)` (line 1973-1977)
- 감사 마커 일치 여부: 불일치 (`->` 아님, `→` 사용)

### _advisory_long_term_rep()
- Guard 조건:
  - `if next_ep < 20: return []` (line 2006-2007)
  - `if _db is not None:` (line 2012)
  - `if _pattern_summary:` (line 2014)
  - `if _ms:` (line 2019)
  - `if _ltr_all:` (line 2024)
- 실제 로그 마커:
  - 원문: `"[LongTermRepetitionAdvisor\u2192Director] %d건 장기 반복 감지"` (line 2038)
  - 디코딩: `[LongTermRepetitionAdvisor→Director] %d건 장기 반복 감지`
- LLM 호출 위치:
  - `LongTermRepetitionAdvisor(llm_ask=self._truth_gate_llm_ask)` (line 2015)
  - `_ltr_advisor.check(_ms, ep_num=next_ep, pattern_summary=_pattern_summary)` (line 2020)
- 감사 마커 일치 여부: 불일치 (`->` 아님, `→` 사용)

### _advisory_numeric_drift()
- Guard 조건:
  - `if next_ep % 5 != 0: return []` (line 1804-1805)
  - `if _fl:` (line 1810)
  - `if _nums:` (line 1812)
  - `if _num_drifts:` (line 1815)
- 실제 로그 마커:
  - 원문: `"[NumericDriftAdvisor\u2192Director] %d건 수치 표류 감지"` (line 1822)
  - 디코딩: `[NumericDriftAdvisor→Director] %d건 수치 표류 감지`
- LLM 호출 위치:
  - `NumericDriftAdvisor(llm_ask=self._truth_gate_llm_ask)` (line 1813)
  - `_num_advisor.check(numbers=_nums, ep_num=next_ep)` (line 1814)
- 감사 마커 일치 여부: 불일치 (`->` 아님, `→` 사용)

---

## Task 2: 씬 쿼리 생성 경로

- _build_scene_query() 반환 형식:
  - 시그니처: `def _build_scene_query(blueprint: Any) -> str:` (line 597)
  - dict scene 항목: `parts.append(f"장면{idx}: {value[:52]}")` (line 611)
  - str scene 항목: `parts.append(f"장면{idx}: {scene[:52]}")` (line 614)
  - 반환: `return " | ".join(parts)[:260]` (line 615)
- _build_stage4_slots() 호출 위치 및 source:
  - 호출: `scene_query = self._build_scene_query(blueprint)` (line 488)
  - 슬롯 추가: `RetrievalSlot("scene_context", scene_query, priority=2)` (line 490)
  - `source=` 인자 미지정
  - 기본 source 정의: `source: str = RetrievalSources.VEC_MEMORY` (line 112)
- `"장면1"`/`scene_query` 확장 위치(다른 위치):
  - `scene_query` 참조: lines 488, 489, 490, 597
  - `"장면1"` 리터럴 문자열: 없음
  - 장면 접두 생성 포맷: lines 611, 614 (`"장면{idx}: ..."`)
- RetrievalSources 정의 전체:
  - `VEC_MEMORY = "vec_memory"` (line 101)
  - `DB_NPC_HISTORY = "db_npc_history"` (line 102)
  - `MANUSCRIPT_DB = "manuscript_db"` (line 103)

---

## Task 3: NpcDriftAdvisor 내부

- check() Guard 조건:
  - `if not manuscript or not npc_snapshots: return []` (line 40-41)
  - `if not appearing: return []` (line 44-45)
  - `if not targets: return []` (line 56-57)
  - `if not self._llm_ask: return []` (line 59-60)
- 빈 리스트 반환 경로 (check()):
  - 입력 원고/스냅샷 미존재
  - 등장 NPC 없음
  - 검사 대상(targets) 없음
  - `llm_ask` 미주입
- LLM 호출 로그:
  - 호출: `response = self._llm_ask(prompt)` (line 118, `_llm_check_batch`)
  - 실패 로그: `logger.warning("[LM-B] NpcDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])` (line 123)
  - 성공 시 info 로그: 없음

---

## 확인된 사실 요약

- 발화 0건 원인(guard 차단 vs 마커 불일치): 5개 모듈 로그 마커는 모두 `->`가 아니라 `\u2192`(`→`) 형식이다.
- 씬 쿼리 생성 경로 단일/복수: `scene_query` 생성은 `_build_scene_query()` 1개 경로이며 `_build_stage4_slots()`에서 1회 사용된다.
- NpcDriftAdvisor LLM 실행 여부: `check()`는 `self._llm_ask` 존재 시에만 `_llm_check_batch()`로 진입한다.
- TF-55 구현 영향 사항: `scene_context` 슬롯은 `source` 미지정으로 `RetrievalSources.VEC_MEMORY` 기본값을 사용한다.

---

## 체크리스트

- [x] 코드 수정 없음
- [x] 검색 명령어 미사용
- [x] 로그 마커 유니코드 디코딩 포함
- [x] Guard 조건 정확 인용
- [x] 출력 파일 경로 준수
