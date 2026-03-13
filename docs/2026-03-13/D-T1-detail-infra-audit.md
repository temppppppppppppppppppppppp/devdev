# [D-T1] 미열거 인프라 & 유틸리티 디테일 감사 보고서

> **터미널**: Terminal 1
> **작성일**: 2026-03-13
> **범위**: 미열거 Core 유틸리티 12개, `__init__.py` 12개, `modules/core/stage0/__init__.py` 내부 로직, 교차 경계(import/설정/에러처리)
> **방법**: 자체 3PASS 감리 + 2026-03-13 터미널 출력 복원분을 실코드로 재검증하여 문서화

---

## 확정 발견사항

### [D-T1-001] P3 | `error_helper.py`는 실사용 import가 없는 dead helper

**파일**: `modules/core/error_helper.py`

**증거**
- `modules/` + `tests/` + `main_a.py` 범위에서 `error_helper` 직접 참조는 자기 문서용 usage 예시만 확인됨 (`modules/core/error_helper.py:209`).
- 실제 소프트 실패 경로는 `soft_failure.py`를 중심으로 연결되어 있음.
  - `artifact_logging.py`
  - `failure_analyzer.py`
  - `session_logger.py`
  - `stage4_post_processor.py`
- `ErrorHelper.print_error()`의 `severity_emoji` 매핑은 전 값이 빈 문자열이라 표시 계층도 실질적으로 죽어 있음 (`modules/core/error_helper.py:268-269`).

**영향**
- 유지보수자가 활성 에러 라우트로 오인할 수 있다.
- V44 도입 이후 남은 보조 유틸리티로 보이며 현재 운영 경로에는 연결되지 않는다.

**수정안**
- 삭제 전 최종 grep 1회 후 제거하거나, 최소한 legacy/deprecated 표기를 추가.

---

### [D-T1-002] P2 | `stage0/__init__.py` 외부 시점 삽입 정책 메뉴에 mojibake 잔존

**파일**: `modules/core/stage0/__init__.py:309-317`

**증거**
- 콘솔 출력 문자열과 입력 프롬프트 일부가 깨진 한글로 저장되어 있다.
- 정책 값 자체는 `default_external_pov_insert_policy()`와 `normalize_external_pov_insert_policy()`로 후처리되어 로직은 정상 동작한다.
- 동일 성격의 깨진 문자열이 `stage01_helpers.py`에도 남아 있어 계층별 복제 흔적이 보인다.

**영향**
- Stage 0 수기 입력 시 UI/CLI 가독성이 무너진다.
- 사용자 입력은 계속 받지만 정책 선택 메뉴의 설명력이 떨어진다.

**수정안**
- 깨진 문자열만 UTF-8 정상 문구로 교체.
- 같은 정책 메뉴를 쓰는 `stage01_helpers.py`와 동기화 확인 필요.

---

### [D-T1-003] P3 | 패키지 맵 인식과 실제 디렉토리 구조 사이에 문서 드리프트

**대상 경로**
- 미존재: `modules/services`
- 미존재: `modules/domain/models`
- 미존재: `modules/domain/protocols`
- 미존재: `modules/domain/validation`

**실제 대응 경로**
- 실존: `modules/core/services`
- 실존: `modules/models`
- 실존: `modules/protocols`
- 실존: `modules/validation`

**증거**
- 파일시스템 기준으로 위 4개 대체 경로는 존재하지 않는다.
- 반면 오더 기준 검사 대상 `__init__.py` 12개는 모두 실존한다.
- `modules/` + `tests/` + `docs/2026-03-13` 범위 grep에서 미존재 경로를 향하는 live import는 확인되지 않았다.

**영향**
- 런타임 import 오류는 아니다.
- 다만 패키지 레이아웃을 설명하는 문서/구두 보고가 실제 트리와 어긋나면 후속 감리와 수동 탐색에서 혼선을 만든다.

**수정안**
- 후속 통합 문서에서는 실제 경로만 SSOT로 사용.
- `domain/*` 아래에 있다고 서술된 오래된 설명은 정리 필요.

---

### [D-T1-004] P2 | `reflexion_manager.py`가 `DBManager` commit API를 우회

**파일**: `modules/core/reflexion_manager.py:93-115`
**관련 파일**: `modules/core/db_manager.py:1039-1047`, `modules/core/db_manager.py:268-280`

**증거**
- `ReflexionManager`는 `execute_update()` 호출 직후 `self.context.db.conn.commit()`을 직접 호출한다 (`reflexion_manager.py:99`, `115`).
- `DBManager.execute_update()`는 내부에서 `cur.execute()`까지만 수행하고 commit을 호출하지 않는다 (`db_manager.py:1039-1047`).
- `reflexion_memory` 테이블 DDL 자체는 이미 `DBManager`에 존재한다 (`db_manager.py:268-280`).

**판정 보정**
- 초기 터미널 요약의 "`reflexion_memory` CREATE도 없음"은 PASS 2에서 **오탐 제거**.
- 남는 진짜 문제는 "테이블 부재"가 아니라 "write API가 commit 정책을 외부 호출자에게 새고 있는 구조"다.

**영향**
- `ReflexionManager`만 DB 내부 구현(`conn`)에 결합된다.
- 다른 호출자가 `execute_update()`를 재사용하면 저장 누락이 발생할 수 있다.

**수정안**
- `execute_update()`에 `nested` 패턴 기반 commit 일관화 추가, 또는 `ReflexionManager` 전용 write API 신설.

---

## 교차 경계 분석

- 설정 3중 경로(`config_manager` / `prompt_loader` / `constants`): 역할 분리 명확, 직접 충돌 징후 없음.
- 투자 수학 이중 경로(`investment_arithmetic_checker` / `investment_math_verifier`): Python 검증 후 LLM 검증으로 이어지는 보완 쌍으로 판단.
- 헌법 이중 경로(`constitutional_checker` / `quality_constitution`): 사전 프롬프트 제약과 사후 평가 루브릭으로 표면이 다름.

## `__init__.py` 점검 메모

- 오더에 적힌 대상 `__init__.py` 12개는 전부 실존 확인.
- `modules/ui/__init__.py`도 추가 실존 확인됐으나 오더 범위 바깥이라 집계에는 미포함.
- 실존 `__init__.py`의 re-export 불일치로 인한 즉시 오류는 발견하지 못함.

## 오탐 제거 로그

| ID | PASS1 후보 | PASS2 결과 | 사유 |
|----|------------|------------|------|
| FP-1 | `reflexion_memory` 테이블 CREATE 부재 | 제거 | `db_manager.py`에 DDL 존재 확인 |
| FP-2 | `__init__.py` 4개 미존재 | 제거 | 오더 대상 12개는 전부 실존, 문제는 별도 패키지 경로 드리프트 |
| FP-3 | 설정 3중 경로 충돌 | 제거 | 역할 분리와 호출 표면이 다름 |
| FP-4 | 투자 수학 검증 이중 구현 = 중복 결함 | 제거 | Python 검증 + LLM 검증의 순차 보완 관계 확인 |
| FP-5 | 헌법 체크 이중 구현 = 중복 결함 | 제거 | 사전/사후 레이어 분리 확인 |

**PASS1**: 17건 후보
**PASS2**: 13건 오탐 제거
**PASS3**: **4건 확정**

- P0: 0건
- P1: 0건
- P2: 2건 (`D-T1-002`, `D-T1-004`)
- P3: 2건 (`D-T1-001`, `D-T1-003`)

