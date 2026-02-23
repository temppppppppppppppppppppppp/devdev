# TF-12 Codex 실행 오더 — 실패 경로 감사

---

## ★ CODEX 환경 규칙 (최우선)

1. **인코딩**: findings 파일 작성 시 UTF-8만 사용. 한글 깨짐 방지를 위해 Write 도구로 파일을 쓸 때 BOM 없는 UTF-8로 작성한다.
2. **자동 검색 도구 금지**: `grep`, `rg`, `find`, `ag`, `ripgrep` 등 셸 자동 검색 도구를 절대 사용하지 않는다. 파일 내용 확인은 **오직 Read 도구**로만 수행한다.
3. **컨텍스트 컴팩트 시 중단 금지**: 컨텍스트 컴팩트가 발생해도 **감사를 중단하지 않는다**. findings.md의 "현재 위치"를 읽고, 미완료 Round부터 이어서 끝까지 완료한다. Round A부터 재시작하면 안 된다.
4. **토큰 절약**: 파일 내용을 findings에 통째로 복사하지 않는다. `파일:줄번호 + 핵심 스니펫(1~3줄) + 등급 + 한 줄 설명`만 기록한다.

---

## 너의 임무

글도비 프로젝트의 **실패 경로(except 블록)**를 감사한다.
580+ except 블록 중 프로덕션에서 silent failure → 데이터 오염으로 이어지는 경로를 식별한다.

**코드 수정 없음. Read-only 감사.**

---

## 시작 전 필수

1. **이 문서 전체를 읽어라**
2. **`docs/2026-02-23/tf12_findings.md`를 읽어라** → "현재 위치" 확인

---

## 절대 수칙

1. **모든 판정은 Read 도구로 파일을 직접 읽은 후 수행한다**
2. **발견 즉시 tf12_findings.md에 기록한다**
3. **각 Round 완료 즉시 "현재 위치" 업데이트**
4. **코드를 수정하지 않는다**

---

## 컨텍스트 컴팩트 복구

1. `docs/2026-02-23/tf12_order.md` 재독
2. `docs/2026-02-23/tf12_findings.md` 재독 → "현재 위치" 확인
3. 다음 미완료 Round부터 즉시 재개

---

## Round 순서

```
Round A → B → C → D → E → F → 완료
```

---

## Round A: DB 트랜잭션 실패 경로

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/db_manager.py` | 44개 except 블록 — 트랜잭션 관련 |
| `modules/core/project_manager.py` | 롤백 경로 |

### 체크리스트

- [ ] rollback 실패 시 트랜잭션 상태 (특히 L240-242)
- [ ] commit 실패 시 재시도 vs 무시 패턴
- [ ] save_anchor / load_anchor 실패 시 데이터 일관성

---

## Round B: 메모리/검색 실패 경로

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/vec_memory.py` | 33개 except — 임베딩·검색 |
| `modules/core/stage4_context_builder.py` | 28개 except — retrieval |
| `modules/core/stage2_preflight.py` | 46개 except — preflight retrieval |

### 체크리스트

- [ ] 임베딩 실패 → 검색 빈값 → Writer 컨텍스트 부실 체인
- [ ] hybrid retrieval 실패 시 dense fallback 동작
- [ ] FTS5 테이블 손상 시 graceful degradation

---

## Round C: 에이전트 실패 경로

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/domain/agents/base_agent.py` | 25개 except — 메트릭·API |
| `modules/domain/agents/chief_writer.py` | Writer 실패 경로 |
| `modules/domain/agents/analyst.py` | Analyst 실패 경로 |
| `modules/core/adaptive_retry.py` | 재시도 로직 |

### 체크리스트

- [ ] LLM API 호출 실패 시 재시도 로직
- [ ] API 키 로테이션 실패 시 동작
- [ ] 구조화 응답 파싱 실패 시 fallback
- [ ] metrics startup/end 실패가 에이전트 로직에 영향을 미치는가

---

## Round D: Stage 오케스트레이터 실패 경로

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/stage2_orchestrator.py` | Stage2 실패 정책 |
| `modules/core/stage3_orchestrator.py` | Stage3 실패 정책 |
| `modules/core/stage4_orchestrator.py` | Stage4 실패 정책 |

### 체크리스트

- [ ] "실패 시 전체 중단" vs "부분 진행" 정책 일관성
- [ ] perf_timer 실패가 오케스트레이터 로직에 영향을 미치는 경로
- [ ] audit_event 실패 시 감사 로그 유실 가능성

---

## Round E: 검증기 실패 경로

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/validation/validation_orchestrator.py` | 검증 오케스트레이션 |
| `modules/validation/blocking_validator.py` | 기본 검증자 |
| `modules/validation/blocking_validator_entity_checks.py` | 엔티티 체크 |
| `modules/validation/blocking_validator_scene_checks.py` | 장면 체크 |
| `modules/validation/continuity_validator.py` | 연속성 검증 |

### 체크리스트

- [ ] 검증기 예외 발생 시 원고 무검증 통과 경로
- [ ] CRITICAL 이슈 감지 실패 시 REJECT 누락 경로
- [ ] 타임아웃 시 검증 결과 기본값

---

## Round F: 리소스 정리 + pass-only 블록

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/stage01_helpers.py` | 8개 pass 블록 |
| `modules/core/stage0/__init__.py` | 3개 pass 블록 |
| `modules/core/diversity_sampler.py` | 빈 결과 반환 패턴 |

### 체크리스트

- [ ] stage01_helpers.py 8개 pass 블록 각각의 의도 확인
- [ ] diversity_sampler 빈 결과 반환이 하위 파이프라인에 미치는 영향
- [ ] 리소스 정리 경로의 완전성

---

## 완료 기준

- tf12_findings.md "현재 위치" = Round F 완료
- 발견 건수 집계

---

지금 바로 `docs/2026-02-23/tf12_findings.md`를 읽는 것부터 시작하라.
