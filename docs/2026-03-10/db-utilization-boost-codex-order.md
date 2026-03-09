# DB 활용 극대화 코덱스 오더 (10건)

> 작성: 2026-03-10
> 상태: 구현 대기
> 전제: CP 1차 + CP 확장이 먼저 완료되어야 함 (§1~§4는 독립 실행 가능)
> 목표: "DB에 저장되어 있지만 LLM이 못 보는" 데이터를 적시에 주입

---

## 공통 원칙

- **LLM 호출 0회** — 순수 Python 데이터 조립
- **읽기 전용** — DB/WorldState/FactLedger에 쓰기 금지
- **비치명** — 실패 시 `logging.debug` + skip, 기존 동작 불변
- **Director 주권** — advisory만 제공, REJECT 강제 금지 (대원칙 3)
- **예산 의식** — Director MC 총량 40K cap 내에서 추가

---

## §1. episode_pacing → Stage 4 Director Advisory

### 문제
`episode_pacing` 테이블에 매화 호흡 분석(대화비율·장면전환·문장길이)이 저장된다.
Stage 3 Blueprint 생성(`blueprint_ensemble.py:558`)에서는 `get_recent_pacing_records()`로 조회하여 활용 중이나,
**Stage 4 Director는 이 데이터를 전혀 보지 못한다.** Director가 원고 심사 시 "대화 부족 3화 연속"을 모른다.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `episode_pacing` (ep_num PK, pacing_score, dialogue_ratio, scene_break_count, avg_sentence_length, short/long_sentence_ratio, issues) |
| 쓰기 | `stage4_post_processor.py:1151` `save_pacing_record()` |
| 읽기 | `blueprint_ensemble.py:558` `get_recent_pacing_records(before_ep, lookback=5)` — **Stage 3만** |
| **갭** | Stage 4 Director MC에 미주입 |

### 구현

**위치**: `stage4_interview_round.py`, L645 (`_director_mandatory_context` 조립) 직전

```python
    # [DB-1] 호흡 분석 추이 → Director advisory
    try:
        if _db is not None and hasattr(_db, "get_recent_pacing_records"):
            _pacing_recs = _db.get_recent_pacing_records(before_ep=next_ep, lookback=5)
            if _pacing_recs and len(_pacing_recs) >= 2:
                _avg_dial = sum(r.get("dialogue_ratio") or 0 for r in _pacing_recs) / len(_pacing_recs)
                _avg_score = sum(r.get("pacing_score") or 50 for r in _pacing_recs) / len(_pacing_recs)
                _pacing_lines = []
                if _avg_dial < 0.15:
                    _pacing_lines.append(f"대화 비율 평균 {_avg_dial:.0%} — 최근 {len(_pacing_recs)}화 대화 부족 추세")
                if _avg_score < 40:
                    _pacing_lines.append(f"호흡 점수 평균 {_avg_score:.0f}/100 — 문장 다양화·장면 전환 필요")
                # 대화비율 연속 하락 감지
                _dial_vals = [r.get("dialogue_ratio") or 0 for r in _pacing_recs]
                if len(_dial_vals) >= 3 and all(_dial_vals[i] > _dial_vals[i + 1] for i in range(len(_dial_vals) - 1)):
                    _pacing_lines.append(f"대화 비율 {len(_dial_vals)}화 연속 하락 ({_dial_vals[0]:.0%}→{_dial_vals[-1]:.0%})")
                if _pacing_lines:
                    _director_mc_parts.append("[DB-1 호흡 추이]\n" + "\n".join(_pacing_lines))
    except Exception as _pace_err:
        logging.debug("[DB-1] pacing advisory 실패 (비치명): %s", _pace_err)
```

### 테스트 (`tests/test_db_utilization.py`)
```
1. test_pacing_advisory_low_dialogue
   - 직전 3화 dialogue_ratio 0.10, 0.08, 0.05 → "대화 부족 추세" 포함 확인
2. test_pacing_advisory_normal
   - 직전 3화 dialogue_ratio 0.30 → advisory 미출력 확인
3. test_pacing_advisory_consecutive_decline
   - 5화 연속 하락 → "연속 하락" 포함 확인
```

---

## §2. satisfaction_tags → Stage 4 Director Advisory

### 문제
`episode_satisfaction_tags` 테이블에 매화 만족도(satisfaction_score·protagonist_agency·frustration_flag)가 저장된다.
Stage 3(`blueprint_ensemble.py:534`) + `continuity_validator.py:1019`에서 조회하나,
**Stage 4 Director는 만족도 추세를 모른다.** "3화 연속 좌절감"을 Director가 인지 못 한다.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `episode_satisfaction_tags` (ep_num PK, primary_tag, satisfaction_score, protagonist_agency, frustration_flag) |
| 쓰기 | `stage4_post_processor.py:1137` `save_satisfaction_tag()` |
| 읽기 | `blueprint_ensemble.py:534` + `continuity_validator.py:1019` — **Stage 3/Validator만** |
| **갭** | Stage 4 Director MC에 미주입 |

### 구현

**위치**: §1 직후 (같은 try 블록 내 또는 별도 블록)

```python
    # [DB-2] 만족도 추이 → Director advisory
    try:
        if _db is not None and hasattr(_db, "get_recent_satisfaction_tags"):
            _sat_tags = _db.get_recent_satisfaction_tags(before_ep=next_ep, lookback=5)
            if _sat_tags and len(_sat_tags) >= 2:
                _sat_lines = []
                _consecutive_frust = 0
                _low_agency_count = 0
                for _st in _sat_tags:
                    if _st.get("frustration_flag"):
                        _consecutive_frust += 1
                    else:
                        _consecutive_frust = 0
                    if _st.get("protagonist_agency") in ("타력", "수동"):
                        _low_agency_count += 1
                if _consecutive_frust >= 2:
                    _sat_lines.append(f"좌절감 {_consecutive_frust}화 연속 — 주인공 능동적 활약 필수")
                if _low_agency_count >= 3:
                    _sat_lines.append(f"주인공 에이전시 저조 {_low_agency_count}/{len(_sat_tags)}화 — 주체적 선택 장면 필요")
                _avg_score = sum(_st.get("satisfaction_score", 5) for _st in _sat_tags) / len(_sat_tags)
                if _avg_score < 4:
                    _sat_lines.append(f"만족도 평균 {_avg_score:.1f}/10 — 긴장·보상·캐릭터 성장 보강 필요")
                if _sat_lines:
                    _director_mc_parts.append("[DB-2 만족도 추이]\n" + "\n".join(_sat_lines))
    except Exception as _sat_err:
        logging.debug("[DB-2] satisfaction advisory 실패 (비치명): %s", _sat_err)
```

### 테스트
```
4. test_satisfaction_advisory_consecutive_frustration
   - 직전 3화 frustration_flag=1 → "좌절감 3화 연속" 포함 확인
5. test_satisfaction_advisory_low_agency
   - 직전 5화 중 3화 protagonist_agency="수동" → "에이전시 저조" 포함 확인
6. test_satisfaction_advisory_normal
   - 만족도 7/10 + frustration 0 → advisory 미출력 확인
```

---

## §3. arc_dependencies → Stage 2 Analyst Advisory

### 문제
`arc_dependencies` 테이블에 Arc 간 의존 그래프(from_arc→to_arc, dep_type, description)가 저장된다.
`stage2_finalizer.py:961-977`에서 쓰기하나, **읽기 호출이 프로덕션에 0회.** `get_arc_dependencies()` 메서드는 테스트에서만 사용.
Arc N+1 생성 시 "Arc 3이 Arc 1의 복선에 의존"을 Analyst/Director가 모른다.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `arc_dependencies` (from_arc_no, to_arc_no PK, dep_type, description) |
| 쓰기 | `stage2_finalizer.py:961-977` `upsert_arc_dependency()` |
| 읽기 | `get_arc_dependencies(arc_no)` — **테스트에서만 호출, 프로덕션 0회** |
| **갭** | Stage 2 Arc 생성 시 의존성 미참조 |

### 구현

**위치**: `stage2_finalizer.py`, Director `compare_and_select_arc()` 호출 직전의 `_story_context` 조립부

```python
    # [DB-3] Arc 의존성 → Director story_context 주입
    try:
        _arc_no = refined_arc.get("arc_no") or arc_data.get("arc_no") or 0
        if _arc_no and _db and hasattr(_db, "get_arc_dependencies"):
            _deps = _db.get_arc_dependencies(int(_arc_no))
            if _deps:
                _dep_lines = []
                for _dep in _deps[:5]:
                    _from = _dep.get("from_arc_no", "?")
                    _to = _dep.get("to_arc_no", "?")
                    _dtype = _dep.get("dep_type", "causes")
                    _ddesc = _dep.get("description", "")[:80]
                    if int(_to) == int(_arc_no):
                        _dep_lines.append(f"  Arc {_from} → 현재: {_dtype} ({_ddesc})")
                    else:
                        _dep_lines.append(f"  현재 → Arc {_to}: {_dtype} ({_ddesc})")
                if _dep_lines:
                    _story_context += "\n\n[DB-3 Arc 의존성]\n" + "\n".join(_dep_lines)
    except Exception as _dep_err:
        logging.debug("[DB-3] arc_dependencies advisory 실패 (비치명): %s", _dep_err)
```

### 테스트
```
7. test_arc_dependency_advisory_basic
   - Arc 3에 from=1→to=3 "causes" 의존 → "[DB-3 Arc 의존성]" + "Arc 1 → 현재" 포함 확인
8. test_arc_dependency_advisory_empty
   - 의존성 없음 → advisory 미출력 확인
```

---

## §4. foreshadow/seeds → Stage 3 Blueprint Advisory

### 문제
`foreshadow` 테이블에 복선 씨앗(seed_id, category, content, status, planted_ep, resolved_ep)이 저장된다.
`seeds` 테이블도 동일 구조(active/archived). **두 테이블 모두 쓰기만 하고 읽기 0회.**
`get_active_seeds()` dead code. 미회수 복선이 100화 넘게 방치되어도 감지 불가.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `seeds` (seed_id PK, category, content, status, planted_ep, recovered_ep) + `foreshadow` (seed_id PK, category, content, status, planted_ep, resolved_ep, data) |
| 쓰기 | `stage4_post_processor.py` + `character_voice_profiler.py` |
| 읽기 | `get_active_seeds()` — **프로덕션 0회, dead code** |
| **갭** | Stage 3 Blueprint 생성 시 미회수 복선 미참조 |

### 구현

**위치**: `stage3_orchestrator.py`, Blueprint 생성 직전 advisory 조립부

```python
    # [DB-4] 미회수 복선 → Blueprint advisory
    try:
        _db = getattr(self.ctx.current_project, "db", None)
        if _db and hasattr(_db, "get_active_seeds"):
            _seeds = _db.get_active_seeds()
            if _seeds:
                _stale_seeds = []
                for _seed in _seeds:
                    _planted = _seed.get("planted_ep") or 0
                    # 20화 이상 미회수 복선만 경고
                    if _planted and (next_ep - _planted) >= 20:
                        _stale_seeds.append(
                            f"  - {_seed.get('content', '?')[:60]} (ep{_planted}~ 미회수, {next_ep - _planted}화 경과)"
                        )
                if _stale_seeds:
                    _advisory_text = "[DB-4 장기 미회수 복선]\n" + "\n".join(_stale_seeds[:5])
                    # Blueprint LLM 컨텍스트에 advisory 주입
                    _enriched_context = _advisory_text + "\n\n" + _enriched_context
    except Exception as _seed_err:
        logging.debug("[DB-4] foreshadow advisory 실패 (비치명): %s", _seed_err)
```

### 테스트
```
9. test_foreshadow_stale_seed_advisory
   - planted_ep=5, next_ep=30 → "25화 경과" 경고 포함 확인
10. test_foreshadow_recent_seed_no_advisory
    - planted_ep=25, next_ep=30 → advisory 미출력 확인
11. test_foreshadow_empty
    - seeds 없음 → advisory 미출력 확인
```

---

## §5. canonical_facts → Stage 4 CP 섹션 7

### 문제
`canonical_facts` 테이블에 정규 팩트(fact_key, fact_type, value_json, confidence)가 저장된다.
`upsert_canonical_fact()`로 쓰기하나, **프로덕션 읽기 0회** (테스트에서만 사용).
NC-1 수치 검증이 FactLedger만 참조하고, canonical_facts의 `confidence` 정보를 못 본다.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `canonical_facts` (fact_key PK, fact_type, value_json, first_ep, last_ep, confidence) |
| 쓰기 | `fact_ledger.py:274` `upsert_canonical_fact()` |
| 읽기 | `get_canonical_facts(fact_type)` — **테스트에서만 호출** |
| **갭** | Stage 4 CP 또는 NC advisory에 미주입 |

### 구현

**위치**: `stage4_context_builder.py` `_build_continuity_packet()` 내부, 섹션 6(수치 이력) 직후

> **전제**: CP 확장(continuity-packet-ext-codex-order.md)이 먼저 완료되어야 함.
> budget은 6500→7000으로 상향 (500자 추가, 50K 대비 14%).

```python
    # 7. 정규 팩트 교차 검증 (canonical_facts)
    if db and hasattr(db, "get_canonical_facts"):
        try:
            _c_facts = db.get_canonical_facts(fact_type="numerical")
            if _c_facts:
                _cf_lines = []
                for _cf in _c_facts[:10]:
                    _cf_key = _cf.get("fact_key", "")
                    if not _cf_key:
                        continue
                    # Blueprint 텍스트에 팩트 키가 등장하는 경우만
                    _ft = entities.get("_full_text", "")
                    if _ft and _cf_key not in _ft:
                        continue
                    _cf_val = _cf.get("value", {})
                    _cf_conf = _cf.get("confidence", "confirmed")
                    if isinstance(_cf_val, dict):
                        _v = _cf_val.get("value", "?")
                        _u = _cf_val.get("unit", "")
                        _cf_lines.append(f"  {_cf_key}: {_v} {_u} (ep{_cf.get('first_ep','?')}~{_cf.get('last_ep','?')}, {_cf_conf})")
                if _cf_lines:
                    cf_section = "• 정규 팩트 참조\n" + "\n".join(_cf_lines[:8])
                    if used + len(cf_section) <= budget:
                        parts.append(cf_section)
                        used += len(cf_section)
        except Exception as _cf_err:
            logging.debug("[CP-7] canonical_facts 조회 실패 (비치명): %s", _cf_err)
```

### budget 변경
```python
    budget = 7000  # 총 예산 (자) — 섹션 5·6·7 확장분 반영 (50K 대비 14%)
```

### 테스트
```
12. test_canonical_facts_in_packet
    - canonical_facts에 "자본금" fact + Blueprint에 "자본금" 포함 → CP에 "정규 팩트 참조" 포함
13. test_canonical_facts_no_match
    - Blueprint 텍스트에 미등장 → 미출력
```

---

## §6. episode_bibles 미사용 컬럼 → Stage 4 Director Advisory

### 문제
`episode_bibles` 테이블은 12컬럼 중 대부분이 쓰기·저장되지만, 프로덕션 읽기는 일부만.
특히 `reveals`(밝혀진 사실)·`causal_links`(인과관계)는 `info_paradox_checker`와 `numeric_consistency_checker`에서 개별 조회되나,
**Director가 직접 보는 경로가 없다.** 100화 전에 밝혀진 반전이 잊혀질 수 있다.

### 현황
| 컬럼 | 쓰기 | 읽기 | 갭 |
|------|------|------|-----|
| new_items | ✅ | ✅ stage4_interview_round | — |
| lost_items | ✅ | ✅ fact_ledger, world_state | — |
| new_npcs | ✅ | ✅ world_state | — |
| npc_deaths | ✅ | ✅ world_state | — |
| relationship_changes | ✅ | ✅ world_state | — |
| state_changes | ✅ | ✅ numeric_consistency | — |
| time_passed | ✅ | ✅ world_state | — |
| **reveals** | ✅ | △ info_paradox (개별) | **Director 미참조** |
| **causal_links** | ✅ | △ LM-post-1 (개별) | **Blueprint 생성 미참조** |
| **karma_matrix** | ✅ | △ consistency_validator | — |
| **knowledge_map** | ✅ | △ info_paradox (개별) | **Director 미참조** |

### 구현

**위치**: `stage4_interview_round.py`, §1·§2와 같은 블록

```python
    # [DB-6] 최근 reveals → Director advisory (미회수 반전/복선 경고)
    try:
        if _db and hasattr(_db, "get_episode_bible"):
            _reveal_all = []
            for _prev_ep in range(max(1, next_ep - 10), next_ep):
                _bible = _db.get_episode_bible(_prev_ep)
                if _bible:
                    for _rev in (_bible.get("reveals") or []):
                        if isinstance(_rev, str) and _rev.strip():
                            _reveal_all.append(f"  ep{_prev_ep}: {_rev[:80]}")
            if _reveal_all:
                _director_mc_parts.append(
                    f"[DB-6 최근 10화 내 밝혀진 사실 ({len(_reveal_all)}건)]\n"
                    + "\n".join(_reveal_all[-8:])
                )
    except Exception as _rev_err:
        logging.debug("[DB-6] reveals advisory 실패 (비치명): %s", _rev_err)
```

### 테스트
```
14. test_reveals_advisory_basic
    - ep15에 reveals=["범인은 박대리"] → Director MC에 "ep15: 범인은 박대리" 포함
15. test_reveals_advisory_empty
    - reveals 없음 → advisory 미출력
```

---

## §7. character_voice → Stage 2/3 전파

### 문제
`character_voice` 테이블에 NPC별 말투 프로필(tone, speech_pattern, vocabulary, catchphrases)이 저장된다.
Stage 4에서만 조건부 사용 (`V50_MODULES_AVAILABLE=True` 필요).
**Stage 2 Arc 생성·Stage 3 Blueprint 생성 시 NPC 말투 정보가 전혀 없다.**

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `character_voice` (npc_name PK, profile_data JSON, updated_at) |
| 쓰기 | `character_voice.save_to_db()` |
| 읽기 | Stage 4 `character_voice.get_writer_injection()` — **V50 플래그 의존** |
| **갭** | Stage 2/3에서 NPC 말투 정보 미참조 |

### 구현

**위치**: `stage2_finalizer.py`, Director `compare_and_select_arc()` 호출 직전

```python
    # [DB-7] NPC 말투 프로필 → Director story_context 보조 주입
    try:
        if _db and hasattr(_db, "get_all_character_voices"):
            _voices = _db.get_all_character_voices()  # 기존 메서드 없으면 아래 SQL 직접 실행
            if _voices:
                _voice_lines = []
                for _v in _voices[:8]:
                    _name = _v.get("npc_name", "")
                    _profile = _v.get("profile_data", {})
                    if isinstance(_profile, str):
                        import json as _json
                        _profile = _json.loads(_profile) if _profile else {}
                    _tone = _profile.get("tone", "")
                    _speech = _profile.get("speech_pattern", "")
                    if _name and (_tone or _speech):
                        _voice_lines.append(f"  {_name}: {_tone}, {_speech}"[:80])
                if _voice_lines:
                    _story_context += "\n\n[DB-7 NPC 말투 참고]\n" + "\n".join(_voice_lines)
    except Exception as _voice_err:
        logging.debug("[DB-7] character_voice advisory 실패 (비치명): %s", _voice_err)
```

> **주의**: `get_all_character_voices()` 메서드가 없으면 `db_manager.py`에 추가 필요:
> ```python
> def get_all_character_voices(self) -> list[dict]:
>     with self._lock:
>         try:
>             rows = self.conn.execute("SELECT npc_name, profile_data FROM character_voice").fetchall()
>             return [dict(row) for row in rows]
>         except Exception:
>             return []
> ```

### 테스트
```
16. test_character_voice_stage2_injection
    - character_voice에 NPC "장천" tone="냉철" → story_context에 "장천: 냉철" 포함
17. test_character_voice_empty
    - 프로필 없음 → advisory 미출력
```

---

## §8. reflexion_memory → Director MC 주입

### 문제
`reflexion_memory` 테이블에 과거 실패 패턴(pattern_type, description, frequency, solution)이 저장된다.
현재 `ReflexionManager.get_prompt_injection()`이 Chief Writer에만 1-shot 주입.
**Director는 반복 실패 패턴을 모른다.** 같은 오류가 매화 반복되어도 Director 심사에 반영 안 됨.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `reflexion_memory` (pattern_type PK, description, frequency, solution, first_ep, last_ep) |
| 쓰기 | `reflexion_manager.py` |
| 읽기 | CW 프롬프트에 1-shot 주입 (`stage4_context_builder.py:1543`) |
| **갭** | Director MC에 미주입 |

### 구현

**위치**: `stage4_interview_round.py`, §1·§2와 같은 블록

```python
    # [DB-8] 반복 실패 패턴 → Director advisory
    try:
        if next_ep >= 20:
            from modules.core.reflexion_manager import ReflexionManager
            _reflexion = ReflexionManager(self.ctx.current_project)
            _top_patterns = _reflexion.get_top_patterns(min_frequency=3, limit=3)
            if _top_patterns:
                _refl_lines = []
                for _p in _top_patterns:
                    _ptype = _p.get("pattern_type", "?")
                    _freq = _p.get("frequency", 0)
                    _desc = _p.get("description", "")[:60]
                    _refl_lines.append(f"  - {_ptype} ({_freq}회): {_desc}")
                _director_mc_parts.append(
                    "[DB-8 반복 실패 패턴 (빈도≥3)]\n" + "\n".join(_refl_lines)
                )
    except Exception as _refl_err:
        logging.debug("[DB-8] reflexion advisory 실패 (비치명): %s", _refl_err)
```

> **주의**: `get_top_patterns(min_frequency, limit)` 메서드가 없으면 `reflexion_manager.py`에 추가 필요:
> ```python
> def get_top_patterns(self, min_frequency: int = 2, limit: int = 5) -> list[dict]:
>     """빈도 기준 상위 패턴 반환."""
>     self.load_memory()
>     patterns = [
>         p for p in self._memory
>         if p.get("frequency", 0) >= min_frequency
>     ]
>     patterns.sort(key=lambda x: x.get("frequency", 0), reverse=True)
>     return patterns[:limit]
> ```

### 테스트
```
18. test_reflexion_director_advisory
    - reflexion_memory에 frequency=5 패턴 → Director MC에 "반복 실패 패턴" 포함
19. test_reflexion_below_threshold
    - frequency=1 패턴만 → advisory 미출력
20. test_reflexion_early_episode
    - next_ep=5 → 조기 에피소드는 skip (ep>=20 조건)
```

---

## §9. timeline_entries → Stage 2 Arc 생성 확장 타임라인

### 문제
`timeline_entries` 테이블에 무제한 타임라인(ep_no, story_date, elapsed_days, time_note)이 저장된다.
`world_state.py:634`에서 `get_timeline_range()`로 WorldState에 로드하나, **WorldState.get_summary()는 최근 5건만 출력.**
Stage 2 Arc 생성 시 30화 이상의 시간 흐름을 볼 수 없어 시간 도약/역전이 발생한다.

### 현황
| 항목 | 상태 |
|------|------|
| DB 테이블 | `timeline_entries` (ep_no PK, story_date, elapsed_days, time_note, idx) |
| 쓰기 | `world_state.py:394-399` `upsert_timeline_entry()` |
| 읽기 | `world_state.py:634` `get_timeline_range()` — WorldState 내부 로드 |
| **갭** | get_summary()에서 5건 cap → Arc 생성 시 장기 시간 흐름 미참조 |

### 구현

**위치**: `four_phase_arc_generator.py`, `_generate_prev_context()` 반환 직전

```python
    # [DB-9] 확장 타임라인 → Arc 생성 컨텍스트
    try:
        _db = getattr(self.ctx.current_project, "db", None)
        if _db and hasattr(_db, "get_timeline_range"):
            _timeline = _db.get_timeline_range(start_ep=1, end_ep=9999, limit=30)
            if _timeline and len(_timeline) >= 5:
                _tl_lines = []
                for _te in _timeline[-15:]:  # 최근 15개만
                    _ep = _te.get("ep_no", "?")
                    _date = _te.get("story_date", "")
                    _elapsed = _te.get("elapsed_days", "")
                    _note = _te.get("time_note", "")[:40]
                    _parts = [f"ep{_ep}"]
                    if _date:
                        _parts.append(_date)
                    if _elapsed:
                        _parts.append(f"+{_elapsed}일")
                    if _note:
                        _parts.append(_note)
                    _tl_lines.append("  " + " | ".join(_parts))
                if _tl_lines:
                    _prev_context += "\n\n[DB-9 확장 타임라인 (최근 15화)]\n" + "\n".join(_tl_lines)
    except Exception as _tl_err:
        logging.debug("[DB-9] timeline advisory 실패 (비치명): %s", _tl_err)
```

### 테스트
```
21. test_timeline_extended_injection
    - timeline_entries 10건 → _prev_context에 "[DB-9 확장 타임라인]" 포함
22. test_timeline_short_skip
    - timeline_entries 3건 → 5건 미만이므로 skip
```

---

## §10. npc_history reason 컬럼 → CP 확장

### 문제
`npc_history` 테이블의 `reason` 컬럼(TF-D 추가)에 변경 이유가 저장되나,
CP 1차 구현은 `episode_no`, `field_name`, `old_value`, `new_value`만 읽고 `reason`은 무시한다.
"왜 변경되었는지"를 CW가 모른다.

### 현황
| 항목 | 상태 |
|------|------|
| DB 컬럼 | `npc_history.reason` TEXT (TF-D 추가) |
| 쓰기 | 21곳에서 `insert_npc_change(reason="...")` |
| 읽기 | CP 1차에서 3행 읽기하나 **reason 미표시** |
| **갭** | 변경 이유가 CW에 미전달 |

### 구현

**위치**: `stage4_context_builder.py` `_build_continuity_packet()`, 기존 NPC 변경 이력 출력 부분

**변경 전** (현재 CP 1차 구현, L306-309):
```python
                        npc_block.append(
                            f"  [변경 {row.get('episode_no', '?')}화] "
                            f"{row.get('field_name', '')}: {str(row.get('old_value', ''))[:30]} → "
                            f"{str(row.get('new_value', ''))[:30]}"
                        )
```

**변경 후**:
```python
                        _reason = row.get("reason", "")
                        _reason_str = f" ({_reason[:30]})" if _reason else ""
                        npc_block.append(
                            f"  [변경 {row.get('episode_no', '?')}화] "
                            f"{row.get('field_name', '')}: {str(row.get('old_value', ''))[:30]} → "
                            f"{str(row.get('new_value', ''))[:30]}{_reason_str}"
                        )
```

### 테스트
```
23. test_npc_history_with_reason
    - npc_history에 reason="부상으로 인한 위치 이동" → CP에 "(부상으로 인한 위치 이동)" 포함
24. test_npc_history_no_reason
    - reason="" → 기존 포맷 유지 (괄호 없음)
```

---

## 파일 변경 목록

| 파일 | 변경 | §번호 |
|------|------|-------|
| `modules/core/stage4_interview_round.py` | Director MC에 §1·§2·§6·§8 advisory 추가 | §1,2,6,8 |
| `modules/core/stage2_finalizer.py` | Director story_context에 §3·§7 advisory 추가 | §3,7 |
| `modules/core/stage3_orchestrator.py` | Blueprint advisory에 §4 복선 경고 추가 | §4 |
| `modules/core/stage4_context_builder.py` | CP 섹션 7 + budget 상향 + §10 reason 표시 | §5,10 |
| `modules/core/four_phase_arc_generator.py` | _prev_context에 §9 타임라인 추가 | §9 |
| `modules/core/db_manager.py` | `get_all_character_voices()` 메서드 추가 (§7 필요 시) | §7 |
| `modules/core/reflexion_manager.py` | `get_top_patterns()` 메서드 추가 (§8 필요 시) | §8 |
| `tests/test_db_utilization.py` | 테스트 24개 신규 | 전량 |

## 절대 하지 말 것

- DB 테이블 스키마를 변경하지 말 것
- 기존 쓰기 로직을 수정하지 말 것
- LLM 호출을 추가하지 말 것
- Director MC 40K cap을 초과하지 말 것
- 기존 advisory (TruthGate, NpcDrift 등)를 제거·변경하지 말 것
- CP 1차·확장 구현의 기존 로직을 변경하지 말 것 (§10 reason은 출력 포맷만 확장)

## 검증 기준

- `pytest tests/test_db_utilization.py -v` 전량 PASS (24개)
- `pytest tests/ -q` 기존 테스트 전량 유지
- `ruff check` 변경 파일 전량 0 violations

## 구현 순서 권장

1. **§10** (1줄 변경, 최소 리스크) → 즉시 검증 가능
2. **§1 + §2** (같은 파일, 같은 위치) → 함께 구현
3. **§3** (Stage 2 독립) → 단독 구현
4. **§6** (Stage 4 Director, §1·§2와 같은 파일) → 함께 구현
5. **§8** (reflexion, 새 메서드 필요) → 단독 구현
6. **§4** (Stage 3 독립) → 단독 구현
7. **§9** (Stage 2 Arc 생성) → 단독 구현
8. **§7** (새 DB 메서드 필요) → 단독 구현
9. **§5** (CP 확장 의존) → CP 확장 완료 후 구현
