# Stage 2 내부 Preflight Enrichment 전면 조사 보고서

> 기준 커밋: `9a55ac0`
> 조사일: 2026-03-06
> 조사 범위: Stage 2 preflight enrichment 경로 전체
> 감리: 코드 직접 확인 5회 완료
> 결론: **P0 0건 / P1 3건 / P2 4건 / OK 5건 / 오탐 제거 2건**

---

## 조사 대상 파일

```
modules/core/stage2_preflight.py    — _preflight_enrichment() 본체 (L729-1221)
modules/core/stage2_orchestrator.py — enrichment 호출 원점 (L251-509)
modules/domain/agents/analyst.py    — enrich_raw_block_async() 실제 구현
```

> **스코프 노트**: 11~16번 터미널 통합보고서 대상 외 영역.

---

## 전체 흐름

```
stage2_orchestrator.py (L251-274)
  └─ analyst.enrich_raw_block_async()   ← Stage 2 enrichment 진입점
       └─ enriched_block (dict) 반환

stage2_orchestrator.py (L281, L287-332)
  └─ asyncio.gather() → 병렬 농축
       └─ Exception 감지 + 재시도 메커니즘 (L287-332)

stage2_orchestrator.py (L480-509)
  └─ _preflight_enrichment() 전달

stage2_preflight.py (L729-1221)  ← 본 조사 핵심
  _preflight_enrichment():
    1. enriched_block 필드 → refined_arc.state_changes 매핑 (L978-1010)
    2. FourPhaseArcGenerator 생성 + 3-tier 수정 분기 (L829-929)
    3. StateTracker extract_* 블록 업데이트 (L1047-1163)
    4. 결과 dict 반환

stage2_orchestrator.py (L494-513)
  └─ refined_arc is None 체크 (L508) → attempt += 1, continue
```

---

## TF 목록 (감리 3회 후 확정)

### P1 항목 (3건)

| TF번호 | 등급 | 파일:줄 | 종류 | 설명 | 패치 방향 |
|--------|------|---------|------|------|-----------|
| TF-S2PE-02 | P1 | stage2_preflight.py:1002-1010 | GAP | `arc_end_state.equipment - arc_start_state.equipment` Python diff로 `items_acquired` 자동 채움 (`# Fix 7`). 구현 버그 3종: ①순서 의존(`i not in _start_eq`) ②중복 처리 미흡 ③문맥(대사/이벤트) 무시. LLM 미제공 시에만 동작하나 equipment diff는 이벤트 기반 획득과 의미가 다름 | `items_acquired`를 FourPhase `state_constraints` 스키마 필수 필드로 선언해 LLM이 대사·이벤트 기반으로 직접 명시. Python diff는 `[advisory]` 태그로 컨텍스트 주입만 |
| TF-S2PE-03 | P1 | analyst.py:1264-1275 | GAP | `_extract_json_robust(raw_res)` JSON 파싱 전실패 시 `{"parsing_error": True, "content": text, "status": "RAW_TEXT_ONLY"}` 반환 (빈 dict 아님). 이 dict가 merged에 병합되어 반환 → orchestrator의 `isinstance(item, dict)` 통과, 핵심 enrichment 필드(`joint_docs`, `relationship_delta` 등) 없는 채로 성공으로 오인. LLM 호출 예외는 L1277 `logging.warning`으로 기처리됨 — 이 갭은 파싱 전실패 경로에 한정 | `enriched_result.get("parsing_error")` 감지 시 `logging.warning("[Analyst Enrich] JSON 파싱 전실패: block_id=%s", _block_id)` + 반환 dict에 `"_enrich_skipped": True` 플래그 삽입. orchestrator에서 플래그 감지 시 audit_event 기록 |
| TF-S2PE-05 | P1 | stage2_preflight.py:1047-1060 | GAP | StateTracker `extract_*` 첫 9개 호출(L1047-1060)에 try/except 없음. 이후 호출들(L1066+)은 각자 try/except + logging 완비. **첫 9개 중 하나가 예외 발생 시 L1188 outer except로 점프 → `four_phase_passed=True` + `refined_arc=set` 상태 유지** (L1012에서 이미 True 설정). Director PASS 시 부분 업데이트된 StateTracker가 잔존. 단, 이 함수들은 refined_arc 데이터 파싱 수준이라 실제 예외 발생 가능성 낮음 | L1047-1060 블록 전체를 `try/except Exception as _st_err:` 래핑 + `logging.error("[Preflight] StateTracker 부분 업데이트 실패: %s", _st_err)`. Director PASS 이후 영향 없도록 실패 항목을 명시 기록 |

### P2 항목 (4건)

| TF번호 | 등급 | 파일:줄 | 종류 | 설명 | 패치 방향 |
|--------|------|---------|------|------|-----------|
| TF-S2PE-06 | P2 | stage2_preflight.py:997-999 | GAP | `_ts.get("in_story_time", "")` → 필드 없으면 `""` 저장. `arc.state_changes["timeline"] = {"start": "", "end": ""}` → Director/NC-3 timeline 체크에서 빈 값 그대로 전달 | `_ts_val = _ts.get("in_story_time", "")` 후 `if _ts_val:` 조건 추가. 빈 문자열이면 timeline 필드 자체 건너뜀 |
| TF-S2PE-07 | P2 | stage2_preflight.py:471 | GAP | `except Exception: pass  # [Phase 3-QR] advisory, 실패 시 비차단` — 비차단 의도는 명확하나 logging 전무 | `except Exception as e: logging.debug("[S2-QR] 품질 추세 수집 실패 (비차단): %s", e)` |
| TF-S2PE-08 | P2 | stage2_preflight.py:807-810 | GAP | SC Advisor 실패 → legacy fallback 진입 시 `audit_event()` 호출만. `logging.warning()` 없어 로그 파일 미기록 | `except Exception as exc:` 블록에 `logging.warning("[S2-SC] advisor 실패, legacy fallback: %s", exc)` 추가 |
| TF-S2PE-09 | P2 | stage2_preflight.py:991 | GAP | `relationship_delta` → `relationship_changes` 매핑 시 `"episode": 0` 하드코딩. 어느 화에서 관계 변경이 일어나는지 Python이 알 수 없어 0으로 고정 → Director가 episode 정보를 신뢰할 수 없음. 활성화 조건이 "LLM 미제공 시에만"이라 영향 범위 좁음. 추가 확인 필요: enrich 프롬프트에서 `relationship_delta` 필드가 `before/after`로 정의됐는지 (매핑 코드 `r.get("before", "")` 사용) | 매핑 시 `"episode": 0` → `"episode": None` 으로 교체해 "미정" 상태 명시. enrich 프롬프트 스키마 `before/after` 일관성 확인 후 필요 시 동기화 |

---

## 감리 기록 (3회 — 코드 직접 확인)

### 감리 1회 — 오탐 1차 제거 (코드 실측)

```
[TF-S2PE-01 검토] relationship_delta → state_changes 자동 매핑 (대원칙 1·3 위반 주장)
  코드 확인: L981 "# Fix 6: enriched_block → state_changes 매핑 보강"
  근거: relationship_delta는 analyst LLM이 생성한 데이터.
        Python은 "LLM이 결정한 관계 변경"을 state_changes 스키마 필드명으로 재포맷할 뿐.
        LLM의 판단 자체를 Python이 대체하는 것이 아님 — 포맷 변환 shim.
        "LLM 미제공 시에만 동작" (if not _sc.get("relationship_changes")) 조건 확인.
  판정: ✅ 오탐 — 대원칙 1·3 위반 아님. 단, episode:0 하드코딩은 별도 P2(TF-S2PE-09).

[TF-S2PE-04 검토] refined_arc=None 호출자 체크 누락 (P1 주장)
  코드 확인: stage2_orchestrator.py:508-513
    if refined_arc is None:
        self.ctx.ui.log("... FourPhase 실패 → 재시도")
        attempt += 1
        continue
  판정: ✅ 오탐 — 이미 명시적 None 체크 + continue 처리 완비.

[TF-S2PE-03 범위 명확화]
  코드 확인: analyst.py L1277-1279
    except Exception as e:
        logging.warning(f" [Enrich Critical Error] {e}")
        return raw_block
  근거: LLM 호출 예외(Exception)는 이미 logging.warning + raw_block 반환으로 처리됨.
        stage2_orchestrator.py L292-303에서 Exception·비dict 타입 감지 + 재시도 있음.
        갭: _extract_json_robust() 파싱 전실패(예외 없이 빈 dict 반환) 케이스만 silent.
        이 경우 orchestrator의 isinstance(item, dict) 통과 → 성공으로 오인.
  판정: P1 유지 — 단, 범위를 "파싱 전실패 케이스"로 명확화.
```

### 감리 2회 — 잔여 항목 재확인 (대원칙·설계 의도)

```
[TF-S2PE-02] items_acquired equipment diff
  코드 확인: L1002 "# Fix 7: items_acquired 자기모순 해결" 주석.
  의도: LLM이 items_acquired 미제공 시 보완 목적.
  재확인: equipment는 "최종 보유 목록"(상태), items_acquired는 "획득 이벤트"(서사).
          equipment diff ≠ 획득 이벤트. 서사적으로 다른 개념을 Python이 동치 취급.
          대원칙 violation보다 구현 정확성 이슈로 framing 수정.
  판정: P1 유지 (framing 수정: 대원칙 violation → 구현 정확성 이슈 3종).

[TF-S2PE-05] StateTracker 원자성
  코드 확인:
    - L1014-1044: st_snapshot = extract_* 실행 전 deepcopy → 스냅샷 타이밍 올바름
    - L1047-1060: 첫 9개 extract_* → try/except 없음
    - L1066+: 이후 호출들은 개별 try/except 있음
  시나리오: L1052 extract_npc_info_from_arc() 예외 → L1188 except → four_phase_passed=True
             → orchestrator 계속 진행 → Director PASS → 부분 업데이트 StateTracker 잔존
  Director REJECT 시: st_snapshot(pre-extract)으로 rollback → 정상 (스냅샷 타이밍 올바름)
  Director PASS 시: 부분 업데이트 StateTracker → 이후 Arc에 누적 오류 가능성
  판정: P1 유지 (Director PASS 시 부분 업데이트 잔존).

[TF-S2PE-07] L471 except Exception: pass
  코드 확인: `# [Phase 3-QR] advisory, 실패 시 비차단` 주석 명시.
  근거: 비차단 의도 설계 맞음. 그러나 logging.debug 0줄은 observability 갭.
  판정: P2 유지 (의도적 비차단, logging.debug 보강 권고).
```

### 감리 3회 — 기존 테스트 커버 · 최종 등급 확정

```
[TF-S2PE-02] items_acquired diff: 테스트 미커버.
  test_stage2_preflight.py에 equipment diff 순서 의존 케이스 없음. → P1 유지.

[TF-S2PE-03] enrich 파싱 전실패 silent: 테스트 미커버.
  orchestrator recovery 경로 테스트는 있으나 "파싱 전실패 → 성공으로 오인" 경로 없음.
  → P1 유지.

[TF-S2PE-05] StateTracker 부분 업데이트: 테스트 미커버.
  첫 9개 extract_* 중 중간 실패 + Director PASS 시나리오 없음. → P1 유지.

[TF-S2PE-09] episode:0 하드코딩: 신규 발견 (감리 1회 오탐 처리 시 파생).
  테스트 미커버. → P2 확정.

최종 오탐 제거: 2건 (TF-S2PE-01, TF-S2PE-04)
```

---

## OK 확인 항목 (5건)

| 체크 항목 | 근거 |
|-----------|------|
| refined_arc=None 호출자 처리 | stage2_orchestrator.py:508-513 명시적 None 체크 + attempt 재시도 ✅ |
| analyst LLM 예외 처리 | analyst.py:1277-1279 `logging.warning` + raw_block 반환 ✅ |
| orchestrator 병렬 농축 예외 감지 | L292-303 `isinstance(item, Exception)` + `isinstance(item, dict)` 체크 + 재시도(L308-332) ✅ |
| enriched_block None/빈값 방어 | `_collect_npc_roster()` L59 isinstance 체크 + `arc_data=enriched_block or {}` ✅ |
| relationship_delta 요소 타입 검증 | L994 `if isinstance(r, dict)` 내부 체크 ✅ |

---

## 최종 요약

| 등급 | 건수 | 상세 |
|------|------|------|
| P0 | 0건 | — |
| P1 | 3건 | items_acquired 구현 버그 3종 + 파싱 전실패 silent + StateTracker 부분 업데이트 |
| P2 | 4건 | 공문자열 timeline + silent pass 2건 + episode:0 하드코딩 |
| OK | 5건 | None 체크·LLM예외·병렬예외·enriched_block방어·타입검증 |
| 오탐 제거 | 2건 | TF-S2PE-01 (대원칙 위반 아닌 포맷 변환) · TF-S2PE-04 (None 체크 이미 존재) |

### 패치 우선순위

```
즉시 처리 (P1):
  TF-S2PE-02 items_acquired diff → LLM 스키마 필수 필드 선언 + Python은 advisory만
  TF-S2PE-03 파싱 전실패 silent → logging.warning + _enrich_skipped 플래그
  TF-S2PE-05 StateTracker 첫 9개 try/except 래핑 + logging.error

후속 처리 (P2):
  TF-S2PE-06 공문자열 timeline → 유효성 검증 후 건너뜀
  TF-S2PE-07 L471 silent pass → logging.debug
  TF-S2PE-08 L807 logging.warning 추가
  TF-S2PE-09 episode:0 → None/unknown 교체
```

### 오탐 근거 요약

| 항목 | 오탐 판정 근거 |
|------|--------------|
| TF-S2PE-01 | `relationship_delta`는 analyst LLM이 생성. Python은 필드명만 재포맷 (shim). 대원칙 1·3 위반 아님 |
| TF-S2PE-04 | `stage2_orchestrator.py:508` `if refined_arc is None: attempt += 1; continue` 이미 존재 |
