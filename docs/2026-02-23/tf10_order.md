# TF-10 Codex 실행 오더 — 데이터 흐름 무결성 감사

---

## ★ CODEX 환경 규칙 (최우선)

1. **인코딩**: findings 파일 작성 시 UTF-8만 사용. 한글 깨짐 방지를 위해 Write 도구로 파일을 쓸 때 BOM 없는 UTF-8로 작성한다.
2. **자동 검색 도구 금지**: `grep`, `rg`, `find`, `ag`, `ripgrep` 등 셸 자동 검색 도구를 절대 사용하지 않는다. 파일 내용 확인은 **오직 Read 도구**로만 수행한다.
3. **컨텍스트 컴팩트 시 중단 금지**: 컨텍스트 컴팩트가 발생해도 **감사를 중단하지 않는다**. findings.md의 "현재 위치"를 읽고, 미완료 Round부터 이어서 끝까지 완료한다. Round A부터 재시작하면 안 된다.
4. **토큰 절약**: 파일 내용을 findings에 통째로 복사하지 않는다. `파일:줄번호 + 핵심 스니펫(1~3줄) + 등급 + 한 줄 설명`만 기록한다.

---

## 너의 임무

글도비 프로젝트의 **데이터 흐름 무결성**을 감사한다.
Stage 0→2→3→4에서 arc_data, blueprint, world_state, fact_ledger, NPC 데이터가
변형·소실·오염되는 지점이 있는지 코드를 직접 읽고 판정한다.

**코드 수정 없음. Read-only 감사.**

---

## 시작 전 필수

1. **이 문서 전체를 읽어라**
2. **`docs/2026-02-23/tf10_findings.md`를 읽어라** → "현재 위치" 확인 → 마지막 완료 Round 이후부터 시작

---

## 절대 수칙

1. **모든 판정은 Read 도구로 파일을 직접 읽은 후 수행한다**
2. **발견 즉시 tf10_findings.md에 기록한다**: `파일:줄번호 + 스니펫 + 등급(HIGH/MEDIUM/LOW/INFO) + 설명`
3. **각 Round 완료 즉시 tf10_findings.md "현재 위치" 섹션을 업데이트한다**
4. **코드를 수정하지 않는다** — 발견만 기록

---

## 컨텍스트 컴팩트 복구

리셋이 발생하면:
1. `docs/2026-02-23/tf10_order.md` 재독
2. `docs/2026-02-23/tf10_findings.md` 재독
3. "현재 위치" 섹션에서 다음 미완료 Round 확인
4. 그 Round부터 즉시 재개
5. **절대 Round A부터 다시 시작하지 않는다**

---

## Round 순서

```
Round A → B → C → D → E → F → 완료
```

---

## Round A: Stage 0 → Stage 2 (arc_data 생성·전달)

### 읽어야 할 파일

| 파일 | 구간 | 목적 |
|------|------|------|
| `modules/core/stage0/__init__.py` | 전체 | arc 초기 생성, save_anchor 호출 |
| `modules/core/stage0/story_expander.py` | 전체 | arc 구조 확장 |
| `modules/core/stage0/reverse_expander.py` | 전체 | 역설계 arc 생성 |
| `modules/core/stage2_orchestrator.py` | L1~200 | arc 수신, load_anchor 호출 |

### 체크리스트

- [ ] Stage0에서 save_anchor("arcs")로 저장하는 arc dict의 필수 필드 목록 확인
- [ ] Stage2에서 load_anchor("arcs")로 읽을 때 기대하는 필드 목록 확인
- [ ] 두 필드 목록의 차집합 (누락/불일치) 판정
- [ ] reverse_expander 경로와 story_expander 경로의 arc 스키마 동일성 확인

### 판정 기준

- 필드 누락 → HIGH
- 타입 불일치 → MEDIUM
- 스키마 동일 → PASS

---

## Round B: Stage 2 내부 (arc 정제 체인)

### 읽어야 할 파일

| 파일 | 구간 | 목적 |
|------|------|------|
| `modules/core/stage2_preflight.py` | 전체 | preflight 분석 입출력 |
| `modules/core/stage2_validation_pipeline.py` | 전체 | 검증 입출력 |
| `modules/core/stage2_finalizer.py` | 전체 | 최종화 입출력 |
| `modules/core/stage2_optimizer.py` | 전체 | 최적화 입출력 |
| `modules/domain/agents/analyst.py` | L1~400 | enrich 반환값 스키마 |

### 체크리스트

- [ ] arc_data가 preflight → optimizer → validator → finalizer를 거치며 필드가 추가/변경되는 추적
- [ ] 각 단계에서 arc_data를 in-place 수정 vs 새 dict 생성 (mutation 추적)
- [ ] analyst.enrich() 반환값의 스키마 vs finalizer 기대 스키마

---

## Round C: Stage 2 → Stage 3 (blueprint 생성)

### 읽어야 할 파일

| 파일 | 구간 | 목적 |
|------|------|------|
| `modules/core/stage3_orchestrator.py` | 전체 | arcs 읽기, blueprint 생성 |
| `modules/domain/agents/blueprint_ensemble.py` | L1~300 | blueprint 구조 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | L1~200 | 3단계 생성 |

### 체크리스트

- [ ] Stage3이 arcs에서 읽는 필드 vs Stage2가 저장하는 필드
- [ ] world_state / fact_ledger 초기화 시점 확인 (L220, L237)
- [ ] blueprint dict 필수 필드 vs 실제 생성 필드

---

## Round D: Stage 3 → Stage 4 (원고 컨텍스트)

### 읽어야 할 파일

| 파일 | 구간 | 목적 |
|------|------|------|
| `modules/core/stage4_orchestrator.py` | L300~500 | blueprint 읽기 |
| `modules/core/stage4_context_builder.py` | L700~800 | arc_data → 컨텍스트 |
| `modules/core/stage4_interview_round.py` | L1~200 | 인터뷰 입력 |
| `modules/domain/agents/chief_writer.py` | L300~600 | Writer 프롬프트 조립 |
| `modules/domain/agents/chief_writer_context.py` | L1~400 | CW 컨텍스트 빌더 |

### 체크리스트

- [ ] Stage4가 blueprint에서 읽는 필드 vs Stage3이 저장하는 필드
- [ ] world_state.get_snapshot() 반환값이 Writer 프롬프트에 올바르게 직렬화되는가
- [ ] fact_ledger 제약 조건이 blocking_validator에 올바르게 전달되는가
- [ ] arc_data → stage4_context_builder의 arc_no 전달 경로 (TF-9 수정 재검증)

---

## Round E: NPC 데이터 흐름

### 읽어야 할 파일

| 파일 | 구간 | 목적 |
|------|------|------|
| `modules/domain/agents/state_tracker_npc.py` | 전체 | NPC 상태 추적 |
| `modules/domain/agents/state_tracker.py` | L1~500 | NPC 등록·변경 |
| `modules/domain/agents/state_extractor.py` | L1~300 | 상태 추출 |
| `modules/core/db_manager.py` | npc_history 관련 | 이력 기록 |

### 체크리스트

- [ ] NPC 등록 → 상태 변경 → 이력 기록 → 검증 참조의 전체 체인
- [ ] state_tracker에서 NPC 속성 변경 시 npc_history append-only 패턴 준수
- [ ] deceased=True NPC가 행동/대사로 등장하는 경로가 차단되는지 (대원칙 4)

---

## Round F: 검증 체인 데이터 흐름

### 읽어야 할 파일

| 파일 | 구간 | 목적 |
|------|------|------|
| `modules/validation/validation_orchestrator.py` | 전체 | 검증 오케스트레이션 |
| `modules/validation/continuity_validator.py` | L1~400 | 연속성 검증 입력 |
| `modules/validation/scoring_validator.py` | L1~400 | 점수 검증 입력 |
| `modules/validation/pre_llm_validator.py` | 전체 | Pre-LLM 검증 |

### 체크리스트

- [ ] 검증기가 받는 입력 데이터의 출처 추적 (manuscript, blueprint, arc_data)
- [ ] 검증 결과(PASS/REJECT/score)가 Director에 올바르게 전달되는지
- [ ] CRITICAL vs MAJOR vs MINOR 이슈 분류가 Director 결정에 미치는 영향

---

## 완료 기준

- tf10_findings.md "현재 위치" = Round F 완료
- 모든 체크리스트 항목에 PASS/FAIL/WARN 판정 기록
- 발견 건수 집계 (HIGH/MEDIUM/LOW/INFO)

---

지금 바로 `docs/2026-02-23/tf10_findings.md`를 읽는 것부터 시작하라.
