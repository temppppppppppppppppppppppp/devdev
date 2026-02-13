# OPUS 4.6 + Codex 안전 디버깅/테스트 협업 플랜

- 대상: `C:\Users\wjjo\Desktop\글도비\modules`
- 목표: 디버깅 조사 + 테스트 수행 시 크래시(프로세스 다운, stderr 유실, 시스템 불안정) 방지
- 기준일: 2026-02-13

## 1. 협업 원칙

1. Opus 4.6은 "분석/설계/판단" 담당, Codex는 "실행/검증/기록" 담당.
2. 한 번에 큰 테스트를 돌리지 않고, 작은 단위로 분할 실행한다.
3. 모든 실행은 timeout + 로그 파일 저장 + 실패 즉시 중단 규칙을 건다.
4. 코드 수정 없이 시작하고, 조사-재현-격리-수정은 반드시 단계적으로 진행한다.

## 2. 역할 분담

### Opus 4.6
- 리스크 우선순위 지정 (예: Stage2/Stage4/Validator 순)
- 실패 원인 가설 작성
- 각 테스트의 "통과/중단 기준" 승인

### Codex
- 명령 실행 자동화
- 결과 수집/요약/증적(로그, 라인, 스택트레이스) 정리
- 안전 가드레일 준수 여부 체크
- 단계별 보고서 md 갱신

## 3. 크래시 방지 가드레일 (필수)

1. 프로세스 보호
- `PYTHONIOENCODING=utf-8` 고정
- pytest 캡처 충돌 회피: 기본 `-s` 사용
- 모든 명령에 타임아웃 부여 (기본 120초, 장기 300초)

2. 범위 제한
- 전체 테스트 일괄 금지
- 파일/모듈 단위로 점진 실행 (`validation` -> `core` -> `domain`)

3. 기록 강제
- stdout/stderr를 파일로 저장
- 실패 시 재실행 전에 원인 태깅 (`env`, `capture`, `dependency`, `logic`)

4. 중단 규칙
- 동일 유형 오류 2회 연속 발생 시 즉시 중단
- `lost sys.stderr`, `I/O operation on closed file` 재발 시 pytest 전략 변경 전 추가 실행 금지

## 4. 실행 순서 (No-Crash 버전)

### Phase A. 사전 안전 점검 (읽기 전용)
1. 파일 구조/대상 수 확인 (`*.py` 개수, 대형 파일 상위)
2. 정적 스캔 (`except Exception`, `except: pass`, `self.app` 밀도)
3. AST 파싱 체크 (SyntaxError 0 여부)

산출물:
- `debug_phaseA_report.md`

### Phase B. 테스트 러너 안정화
1. 최소 실행: `pytest -q -s` (루트)
2. 실패 시 캡처 비활성/플러그인 최소화 시나리오로 전환
3. 그래도 실패하면 pytest를 중단하고 "실행기 이슈"로 분리

산출물:
- `test_runner_stability.md`

### Phase C. 저위험 테스트부터 점진 실행
1. 존재 시 단일 테스트 파일 먼저 실행
2. 없으면 스모크 스크립트(임포트/핵심 함수 호출 없는 수준) 작성 후 실행
3. 모듈 그룹 단위로 확장 (validation -> core 일부 -> domain 일부)

산출물:
- `test_phaseC_matrix.md` (대상/결과/실패원인/다음액션)

### Phase D. 딥 디버깅 (오류 재현 기반)
1. 상위 리스크 2개 파일 우선 (`stage2_orchestrator.py`, `stage4_orchestrator.py`)
2. `except Exception: pass` 지점의 실패 은닉 가능성 표 작성
3. "수정 필요"와 "관찰 유지"를 분리

산출물:
- `deep_debug_findings.md`

## 5. 실행 명령 템플릿 (안전형)

```powershell
$env:PYTHONIOENCODING='utf-8'
pytest -q -s *> .\logs\pytest_smoke.log
```

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m py_compile .\modules\core\stage2_orchestrator.py
```

```powershell
rg -n "except Exception|except:\\s*$|pass\\s*$" .\modules
```

## 6. 실패 분류 체계

- `RUNNER_CAPTURE`: pytest 캡처/스트림 계열 문제
- `ENV_DEP`: 패키지/버전/경로 문제
- `CODE_LOGIC`: 실제 코드 동작 오류
- `DATA_STATE`: 입력 데이터/프로젝트 상태 의존 문제

## 7. 오늘 바로 적용할 최소 실행안

1. Phase A만 먼저 완료 (크래시 리스크 거의 없음)
2. Phase B는 단 1회만 실행하고 결과 판정
3. 캡처 오류 재발 시 테스트 확장 금지, Runner 안정화 문서 먼저 확정

## 8. 완료 기준 (Definition of Done)

- 크래시 없이 최소 1개 테스트 경로 성공 또는
- 테스트 불가 원인을 재현 가능하게 문서화 + 우회전략 확정
- 조사 md 3종 이상 생성 및 다음 실행 순서가 명확히 남아 있음

---

## 협업 메모

- Opus 4.6에게는 "우선순위/가설/중단기준" 판단을 요청.
- Codex는 "실행 안전성"과 "증적 정리"를 지속 담당.
- 수정 작업은 본 플랜 완료 후 별도 단계로 분리.
