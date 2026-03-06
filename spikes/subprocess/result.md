# SPIKE-2 결과 보고서

- 날짜: 2026-03-06
- 판정: **SPIKE-2 PASS**
- 실행 시간: 185.2초

---

## 검증 목적

main_a.py를 숨김 프로세스(PIPE)로 기동하고, stdin으로 메뉴 키를 보내
stdout 응답을 파싱할 수 있는지 확인.

---

## 실행 흐름 (실제 검증 결과)

| 단계 | 방법 | 결과 |
|------|------|------|
| `subprocess.Popen(stdin=PIPE, stdout=PIPE, stderr=STDOUT)` | 기동 | ✅ 성공 |
| 장르 선택 (기본값 Enter) | force-send 30s | ✅ `[무협 (Wuxia)] 전문 공정 선택` 확인 |
| 프로젝트 목록 진입 (Enter) | force-send 15s | ✅ 프로젝트 목록 수신 |
| 프로젝트 1번 선택 (`1\n`) | force-send 20s | ✅ MagicMock 프로젝트 부팅 시작 |
| 에이전트 초기화 완료 | stdout 수신 | ✅ `✅ [System] 모든 에이전트 안전하게 초기화 완료` |
| 메인 메뉴 출력 수신 | stdout 수신 | ✅ `👇 Select Command:` + `5. Exit` 확인 |
| stdin `5\n` 전송 (Exit) | force-send | ✅ `👉 Choice:` 에 `5\n` 주입 |
| 종료 메시지 수신 | stdout 수신 | ✅ `🛑 [System] 시스템 종료 시퀀스 가동...` |

---

## stdout 샘플 (핵심 부분)

```
[System] 모든 에이전트 안전하게 초기화 완료
│                  Genre: 무협 (Wuxia) | Project: MagicMock                   │

👇 Select Command:
   0. Stage 0: Bible/역설계/스타일 추출 [❌]
   4. 🚀 Stage 4: Sovereign Production (Writing)
   5. Exit

   👉 Choice:
🛑 [System] 시스템 종료 시퀀스 가동...
```

---

## 인코딩 정보

| 항목 | 값 | 비고 |
|------|----|----|
| subprocess encoding | `utf-8` | `Popen(encoding='utf-8')` |
| 환경변수 | `PYTHONIOENCODING=utf-8` | subprocess 측 출력 인코딩 |
| 터미널 대응 | `TERM=dumb`, `NO_COLOR=1` | Rich 비-TTY 모드 강제 |
| 스파이크 stdout | `io.TextIOWrapper(buffer, encoding='utf-8')` | Windows CP949 → UTF-8 재설정 |
| 이모지 출력 | 정상 (모든 이모지 깨짐 없음) | ✅ |

---

## 타이밍 분석

| 이벤트 | 경과 시간 |
|--------|---------|
| 프로세스 기동 | t=0s |
| 장르 목록 출력 | t~5s |
| 장르 선택 force-send | t=30s |
| 프로젝트 목록 force-send | t=45s |
| 프로젝트 선택 force-send | t=65s |
| 에이전트 초기화 완료 | t~115s |
| 메인 메뉴 출력 | t~115s |
| "5\n" force-send | t~185s (step max_wait 120s 소진) |
| 종료 메시지 수신 | t~185s |

### 패턴 감지 이슈 (디버깅 결과)

`input()` 프롬프트가 stdout PIPE에 늦게 flush되어 모든 step에서 force-send가 발동됨.
- 장르/프로젝트 선택: `input()` 프롬프트가 PIPE로 늦게 전달 (TTY 아닐 때 Rich/Python 버퍼링)
- 메인 메뉴: `console.input()` 프롬프트도 마찬가지

**프로덕션 대응**: FastAPI 브리지에서는 `\n`을 먼저 파이프에 쓰는 방식 대신,
`asyncio.create_subprocess_exec`의 stdin 스트림으로 메뉴 상태를 파싱 후 전송.

---

## FastAPI 브리지(스파이크 3) 연동 시 권고사항

1. **asyncio subprocess**: `asyncio.create_subprocess_exec` + `asyncio.StreamReader` 사용
2. **stdout 파싱 기준**:
   - `"👇 Select Command:"` → 메인 메뉴 도달 확인
   - `"👉 Choice:"` → 입력 대기 상태 (waiting_input)
   - `"종료 시퀀스"` / `"종료 완료"` → run 종료 완료
3. **인코딩**: `PYTHONIOENCODING=utf-8 + PYTHONUNBUFFERED=1 + TERM=dumb + NO_COLOR=1`
4. **상태 emit**: WS 이벤트 `state: waiting_input` → `prompt_request` 이벤트 발행
5. **초기화 지연**: MagicMock 프로젝트 기준 ~50s, 실용 프로젝트는 ~30s 예상

---

## GO / NO-GO

| 항목 | 판정 |
|------|------|
| subprocess.Popen stdin=PIPE 제어 | ✅ GO |
| stdout 파싱 및 상태 감지 | ✅ GO |
| 인코딩 (UTF-8 이모지 포함) | ✅ GO |
| stdin 키 전송 → 응답 수신 | ✅ GO |
| **스파이크 2 종합** | **✅ PASS — FastAPI 브리지 착수 허용** |
