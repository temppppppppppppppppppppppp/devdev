# TF-55 코드 검증 경영 보고

---

## 1. 보고 개요

| 항목 | 내용 |
|------|------|
| 검증일 | 2026-03-04 |
| 입력 파일 | `docs/2026-03-04/code-verification-result.md` |
| 검증 방식 | 파일 직접 읽기 (셸 명령어 미사용) |
| 검증 대상 | `stage4_interview_round.py`, `context_advisor.py`, `npc_drift_advisor.py` |
| 검증 목적 | Feature Activation Audit 결과(advisory 5개 모듈 발화 0건)의 원인 규명 |

---

## 2. 핵심 결과 요약표

### Advisory 모듈 로그 마커 불일치 현황

| 모듈 | 감사 검색 마커 | 실제 코드 마커 | 일치 여부 |
|------|--------------|--------------|---------|
| NpcDriftAdvisor | `NpcDriftAdvisor->Director` | `[NpcDriftAdvisor→Director]` | **불일치** |
| TruthGate | `TruthGate->Director` | `[TruthGate→Director]` | **불일치** |
| RelationshipDriftAdvisor | `RelationshipDrift->Director` | `[RelationshipDriftAdvisor→Director]` | **불일치** |
| LongTermRepetitionAdvisor | `LongTermRep->Director` | `[LongTermRepetitionAdvisor→Director]` | **불일치** |
| NumericDriftAdvisor | `NumericDrift->Director` | `[NumericDriftAdvisor→Director]` | **불일치** |

- **공통 원인**: 감사 검색 시 ASCII `->` 사용, 코드 실제 마커는 Unicode `→` (U+2192) 사용
- **5개 모듈 전량 해당**

### 발화 0건 판정 번복

| 항목 | Feature Activation Audit 결론 | 코드 검증 결론 |
|------|-------------------------------|--------------|
| NpcDriftAdvisor | 발화 0건 (비활성) | **마커 불일치 — 판정 불가** |
| TruthGate | 발화 0건 (비활성) | **마커 불일치 — 판정 불가** |
| RelationshipDriftAdvisor | 발화 0건 (비활성) | **마커 불일치 — 판정 불가** |
| LongTermRepetitionAdvisor | 발화 0건 (비활성) | **마커 불일치 — 판정 불가** |
| NumericDriftAdvisor | 발화 0건 (비활성) | **마커 불일치 — 판정 불가** |

---

## 3. 상세 결과

### 3-1. Task 1: Advisory 모듈 Guard 및 마커 확인

#### Guard 조건 (LLM 실행 차단 가능 경로)

| 모듈 | Guard 조건 | 코드 위치 |
|------|-----------|---------|
| NpcDriftAdvisor | `if _ws and hasattr(_ws, "get_npc_role_snapshot")` | L1763 |
| NpcDriftAdvisor | `if _npc_snaps` | L1765 |
| NpcDriftAdvisor | `if not _ms: continue` | L1770 |
| NpcDriftAdvisor | `if _drifts` | L1773 |
| NpcDriftAdvisor | `if _drift_all` | L1779 |
| TruthGate | `if not _ms: continue` | L1733 |
| TruthGate | `if _tg_result.get("structured_warnings")` | L1740 |
| TruthGate | `if _tg_warnings_all` | L1747 |
| RelationshipDriftAdvisor | `if next_ep < 5: return []` | L1958–1959 |
| RelationshipDriftAdvisor | `if _db and hasattr(_db, "get_all_relationship_pairs_with_history")` | L1962 |
| LongTermRepetitionAdvisor | `if next_ep < 20: return []` | L2006–2007 |
| NumericDriftAdvisor | `if next_ep % 5 != 0: return []` | L1804–1805 |

- **epoch 조건 주목**: RelationshipDriftAdvisor는 5화 미만, LongTermRepetitionAdvisor는 20화 미만, NumericDriftAdvisor는 5의 배수 화수에서만 실행
- 단, Guard 통과 여부와 무관하게 **마커 불일치로 인해 발화 감지 자체가 불가능했음**

#### 실제 로그 마커 (코드 내 원문)

| 모듈 | 코드 내 원문 | 디코딩 결과 |
|------|-----------|----------|
| NpcDriftAdvisor | `"[NpcDriftAdvisor\u2192Director] %d건 표류 감지 전달"` | `[NpcDriftAdvisor→Director] %d건 표류 감지 전달` |
| TruthGate | `"[TruthGate\u2192Director] %d개 경고 전달"` | `[TruthGate→Director] %d개 경고 전달` |
| RelationshipDriftAdvisor | `"[RelationshipDriftAdvisor\u2192Director] %d건 관계 표류 감지"` | `[RelationshipDriftAdvisor→Director] %d건 관계 표류 감지` |
| LongTermRepetitionAdvisor | `"[LongTermRepetitionAdvisor\u2192Director] %d건 장기 반복 감지"` | `[LongTermRepetitionAdvisor→Director] %d건 장기 반복 감지` |
| NumericDriftAdvisor | `"[NumericDriftAdvisor\u2192Director] %d건 수치 표류 감지"` | `[NumericDriftAdvisor→Director] %d건 수치 표류 감지` |

### 3-2. Task 2: 씬 쿼리 생성 경로

| 항목 | 확인 결과 | 코드 위치 |
|------|---------|---------|
| `_build_scene_query()` 반환 형식 | `"장면{idx}: {value[:52]}"` 형태 `\|` 구분, 최대 260자 | L611, L614, L615 |
| `_build_stage4_slots()` 호출 | `scene_query = self._build_scene_query(blueprint)` → `RetrievalSlot("scene_context", ...)` | L488–490 |
| `source=` 파라미터 | **미지정** (기본값 사용) | L490 |
| 기본 source | `RetrievalSources.VEC_MEMORY = "vec_memory"` | L112 |
| 생성 경로 수 | **단일 경로** (`_build_stage4_slots` 1회만 호출) | L488 |
| `RetrievalSources` 전체 정의 | `VEC_MEMORY`, `DB_NPC_HISTORY`, `MANUSCRIPT_DB` (3종) | L101–103 |

- `scene_context` 슬롯은 VecMemory로 라우팅되며, hits=0 원인은 해당 씬 내용이 VecMemory에 미입력된 것이 가장 유력
- `DB_NPC_RELATIONSHIP` 등 관계형 DB 소스 상수는 정의되지 않음

### 3-3. Task 3: NpcDriftAdvisor 내부

| 항목 | 확인 결과 | 코드 위치 |
|------|---------|---------|
| LLM 실행 전 Guard (check()) | 4개 조건 (아래 표) | L40–60 |
| 빈 리스트 반환 경로 | 4가지 | — |
| LLM 호출 성공 시 로그 | **없음** | — |
| LLM 호출 실패 시 로그 | `logger.warning("[LM-B] NpcDriftAdvisor LLM 호출 실패 (비치명): %s")` | L123 |

`check()` 빈 리스트 반환 경로:

| 경로 | Guard 조건 | 위치 |
|------|-----------|------|
| 1 | `if not manuscript or not npc_snapshots: return []` | L40–41 |
| 2 | `if not appearing: return []` | L44–45 |
| 3 | `if not targets: return []` | L56–57 |
| 4 | `if not self._llm_ask: return []` | L59–60 |

---

## 4. 데이터 무결성 체크

| 항목 | 결과 |
|------|------|
| 검증 대상 파일 전량 읽기 완료 | ✅ (3개 파일 전부) |
| 유니코드 이스케이프 디코딩 포함 | ✅ (`\u2192` → `→`) |
| Guard 조건 정확 인용 (줄 번호 포함) | ✅ |
| 코드 수정 없음 | ✅ |
| 셸 명령어 미사용 | ✅ |
| Feature Activation Audit 결론과 충돌 항목 | 5건 (번복 검토 필요) → **재감사 완료, 번복 0건 / 유지 5건** |

---

## 5. 확인된 사실 요약

- **마커 불일치**: Feature Activation Audit의 `->` 검색 마커와 코드 실제 마커 `→`(U+2192)가 다르며, 5개 모듈 전량 해당한다. 발화 0건 판정은 검색 오류로 인한 것이다.
- **Guard 조건 존재**: RelationshipDriftAdvisor(5화 미만), LongTermRepetitionAdvisor(20화 미만), NumericDriftAdvisor(5 배수 아닌 화수)는 에피소드 조건에 따라 LLM이 호출되지 않는다.
- **씬 쿼리 경로 단일**: `scene_context` 슬롯은 `_build_stage4_slots()` 내 1개 경로이며, source는 `VEC_MEMORY` 기본값을 사용한다.
- **NpcDriftAdvisor LLM 실행 조건**: `check()`는 4개 Guard를 모두 통과해야 `_llm_check_batch()`에 진입하며, 성공 시 info 로그가 없어 실행 여부를 외부에서 확인하기 어렵다.
- **TF-55a 비활성화 확정**: `→` 마커 재감사 결과 5개 모듈 전량 0건 유지 (번복 0건). 마커 불일치는 검색 오류였으나 발화 0건 판정 자체는 정확했다. TF-55a 비활성화 방침 원복.
