# TF-11 Codex 실행 오더 — DI 배선 검증 감사

---

## ★ CODEX 환경 규칙 (최우선)

1. **인코딩**: findings 파일 작성 시 UTF-8만 사용. 한글 깨짐 방지를 위해 Write 도구로 파일을 쓸 때 BOM 없는 UTF-8로 작성한다.
2. **자동 검색 도구 금지**: `grep`, `rg`, `find`, `ag`, `ripgrep` 등 셸 자동 검색 도구를 절대 사용하지 않는다. 파일 내용 확인은 **오직 Read 도구**로만 수행한다.
3. **컨텍스트 컴팩트 시 중단 금지**: 컨텍스트 컴팩트가 발생해도 **감사를 중단하지 않는다**. findings.md의 "현재 위치"를 읽고, 미완료 Round부터 이어서 끝까지 완료한다. Round A부터 재시작하면 안 된다.
4. **토큰 절약**: 파일 내용을 findings에 통째로 복사하지 않는다. `파일:줄번호 + 핵심 스니펫(1~3줄) + 등급 + 한 줄 설명`만 기록한다.

---

## 너의 임무

글도비 프로젝트의 **DI 배선 검증**을 감사한다.
Stage2Context(45슬롯) + Stage3Context(19슬롯) + Stage4Context(24슬롯) = 88개 DI 슬롯이
런타임에 올바른 객체를 받는지, 죽은 슬롯은 없는지, 타입 불일치는 없는지 판정한다.

**코드 수정 없음. Read-only 감사.**

---

## 시작 전 필수

1. **이 문서 전체를 읽어라**
2. **`docs/2026-02-23/tf11_findings.md`를 읽어라** → "현재 위치" 확인 → 마지막 완료 Round 이후부터 시작

---

## 절대 수칙

1. **모든 판정은 Read 도구로 파일을 직접 읽은 후 수행한다**
2. **발견 즉시 tf11_findings.md에 기록한다**: `파일:줄번호 + 스니펫 + 등급 + 설명`
3. **각 Round 완료 즉시 tf11_findings.md "현재 위치" 섹션을 업데이트한다**
4. **코드를 수정하지 않는다**

---

## 컨텍스트 컴팩트 복구

1. `docs/2026-02-23/tf11_order.md` 재독
2. `docs/2026-02-23/tf11_findings.md` 재독 → "현재 위치" 확인
3. 다음 미완료 Round부터 즉시 재개

---

## Round 순서

```
Round A → B → C → D → 완료
```

---

## Round A: Stage2Context 45개 슬롯

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/stage2_context.py` | 슬롯 정의 (45개) |
| `modules/core/stage2_orchestrator.py` | ctx.XXX 접근 패턴 |
| `modules/core/stage2_preflight.py` | 위임 사용 패턴 |
| `modules/core/stage2_validation_pipeline.py` | 위임 사용 패턴 |
| `modules/core/stage2_finalizer.py` | 위임 사용 패턴 |

### 체크리스트

- [ ] 45개 슬롯 각각: 정의됨 / from_app()에서 할당됨 / 런타임 사용처 존재 여부
- [ ] 사용되지 않는 죽은 슬롯 식별
- [ ] from_app()에서 getattr 기본값(None)이 런타임에 AttributeError를 유발하는 경로

### 판정 포맷

각 슬롯에 대해:
```
슬롯명 | 정의 | from_app 할당 | 사용처 | 판정
```

---

## Round B: Stage3Context 19개 슬롯

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/stage3_context.py` | 슬롯 정의 (19개) |
| `modules/core/stage3_orchestrator.py` | ctx.XXX 접근 패턴 |

### 체크리스트

- [ ] 19개 슬롯 사용 현황 매핑
- [ ] world_state / fact_ledger lazy init 패턴의 안전성
- [ ] Stage3 전용 콜백 10개의 실제 호출 여부

---

## Round C: Stage4Context 24개 슬롯 + conditional_modules

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/stage4_context.py` | 슬롯 정의 (24개 + conditional 8종) |
| `modules/core/stage4_orchestrator.py` | ctx.XXX 접근 패턴 |
| `modules/core/stage4_context_builder.py` | 위임 사용 패턴 |
| `modules/core/stage4_post_processor.py` | 위임 사용 패턴 |
| `modules/core/stage4_interview_round.py` | 위임 사용 패턴 |

### 체크리스트

- [ ] 24개 슬롯 + conditional_modules 8종 사용 현황 매핑
- [ ] get_module() 호출 시 존재하지 않는 모듈명 요청 경로
- [ ] emotion_tracker (TF7-P2-06 추가) 실제 사용 여부

---

## Round D: 크로스 스테이지 DI 일관성

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `main_a.py` | app 객체 구성 (DI 원천) — 전체 검색 |
| `modules/core/stage2_context.py` | from_app() |
| `modules/core/stage3_context.py` | from_app() |
| `modules/core/stage4_context.py` | from_app() |

### 체크리스트

- [ ] main_a.py에서 app에 할당하는 속성 vs 각 Context.from_app()이 읽는 속성
- [ ] app 속성명 불일치 (typo, 리네임 누락)
- [ ] 슬롯 간 의존성 (A 슬롯이 B 슬롯 존재를 전제하는 경우)

---

## 완료 기준

- tf11_findings.md "현재 위치" = Round D 완료
- 모든 슬롯에 대해 사용 현황 매핑 완료
- 발견 건수 집계

---

지금 바로 `docs/2026-02-23/tf11_findings.md`를 읽는 것부터 시작하라.
