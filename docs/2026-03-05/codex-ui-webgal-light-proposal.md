# 글도비 데스크톱 앱 제안서 (PoC 고도화)

## 한줄 결론
터미널 기반 글도비를 **Windows 데스크톱 앱**으로 감싸고, 실행 제어/로그/상태 시각화를 제공한다.  
핵심 원칙은 `백엔드 로직 보존 + UI는 얇은 래퍼`.

---

## 핵심 결정사항
- 터미널 UX는 유지(개발자용), 데스크톱 UI는 추가(비개발자용).
- UI 버튼은 콘솔 메뉴 키를 1:1 매핑하되, `0`은 Stage 0 하위 옵션까지 2단계로 매핑한다.
- 초기 PoC는 `subprocess + stdin/stdout` 방식으로 시작한다.
- 2단계에서 `FastAPI 브리지`를 도입해 구조를 안정화한다.
- 연출은 업무를 방해하지 않는 수준(짧고 끌 수 있음)으로 제한한다.

---

## 목표와 비목표

### 목표
- 터미널/명령줄 비노출 상태로 파이프라인 실행
- 프로젝트 선택, Stage 실행, 로그 확인, 결과 판정 확인
- `.exe` 설치형 배포(팀원이 Python 별도 설치 없이 사용)
- 앱 업데이트 팝업(`패치하시겠습니까?`) 기반 유지보수

### 비목표 (PoC 범위 밖)
- 완전한 클라우드 SaaS 전환
- 복잡한 3D 월드/메타버스 구현
- 연출 중심의 장시간 애니메이션
- 대규모 권한/조직 관리(SSO 등)

---

## 대상 사용자
- 비개발자 기획/운영자: 버튼 중심 실행, 파일 탐색 최소화
- 개발자: 기존 CLI 유지, 디버깅과 운영 자동화 병행

---

## 아키텍처

```text
글도비-Desktop.exe (Electron)
├─ Main Process (Node)
│  ├─ Python 런너 subprocess 기동/중지
│  ├─ stdout/stderr 수집
│  ├─ Update manifest 체크
│  └─ IPC 브리지
├─ Renderer (React + Canvas 2D)
│  ├─ 실행 패널 (Stage 버튼)
│  ├─ 상태 시각화 패널 (Office 분위기)
│  ├─ 로그 타임라인
│  └─ 설정/프로젝트 관리
└─ 번들 Python 런타임 (PyInstaller)
   ├─ main_a.py
   ├─ 글도비 모듈
   └─ 의존성 (sqlite-vec 포함)
```

---

## 실행 모드 전략

### Mode A: CLI 호환 모드 (PoC 1단계)
- UI가 백엔드 프로세스를 숨김 실행
- UI 버튼 입력을 메뉴 키로 변환해 `stdin` 전달
- `stdout` 파싱으로 상태/판정/점수 추출
- **기본 운영 모드: Mode A**

장점:
- 기존 코드 변경 최소
- 초기 구현 속도 빠름

한계:
- 콘솔 출력 포맷 변경에 민감

### Mode B: API 브리지 모드 (PoC 2단계)
- `main_a.py` 앞에 얇은 FastAPI 서버 추가
- UI는 HTTP/WS만 사용
- 이벤트 계약(JSON) 고정으로 안정성 확보
- **운영 정책: beta 채널에서 우선 검증 후 stable 반영**

---

## API 계약 (통일안)

> 문서 내 API 경로는 아래 계약으로 통일한다.

### HTTP
- `POST /run`
  - body: `{ "key": "0|1|2|3|4|5|6|44|77|88|99" }`
  - 추가 규칙: `key=0`일 때 body에 `"sub_key": "0|1|2|3|4|5|6"` 필수
  - Mode A(`stdin/stdout`)에서는 key별 후속 프롬프트 답변을 순차 `stdin`으로 전달
- `POST /run/batch`
  - body: `{ "count": 10 }`
- `POST /stop`
- `GET /status`

### WebSocket
- `WS /events`

### 인터랙티브 프롬프트 계약 (Mode B 확장안)
- 목적: Mode A의 `stdin` 후속 입력을 Mode B에서 명시적 API 계약으로 치환
- 권장 엔드포인트:
  - `GET /run/{run_id}/prompts` (대기 프롬프트 조회)
  - `POST /run/{run_id}/input` body: `{ "prompt_id": "...", "value": "..." }`
- 권장 이벤트:
  - `prompt_request` (필드: `prompt_id`, `key`, `step`, `type`, `options`, `default`, `required`)
  - `prompt_resolved` (필드: `prompt_id`, `value`, `by`)
  - `prompt_timeout` (필드: `prompt_id`, `default_applied`)
- 본 문서 기준:
  - PoC 기본은 Mode A(`stdin`)를 사용
  - Mode B에서는 위 계약으로 단계적 전환

### 이벤트 스키마 예시
```json
{ "event_version": 1, "seq": 101, "run_id": "run-20260306-1", "type": "agent_state", "agent": "chief_writer", "state": "typing", "ts": "2026-03-06T10:20:30+09:00" }
{ "event_version": 1, "seq": 102, "run_id": "run-20260306-1", "type": "stage_result", "stage": 3, "verdict": "PASS", "score": 87, "ep": 12, "ts": "2026-03-06T10:20:41+09:00" }
{ "event_version": 1, "seq": 103, "run_id": "run-20260306-1", "type": "log_line", "level": "INFO", "message": "Stage 3 complete", "ts": "2026-03-06T10:20:41+09:00" }
```

### 명령/동시성 규칙 (2차 감리 보강)
- `key` 허용값 화이트리스트: `0,1,2,3,4,5,6,44,77,88,99`
- `key=0` 요청은 `sub_key` 필수이며 허용값은 `0,1,2,3,4,5,6`
- `key!=0` 요청에서 `sub_key`가 오면 `400 SUB_KEY_NOT_ALLOWED`로 거절
- `STAGE0_AVAILABLE=false` 환경에서 `sub_key=2~6` 요청은 `400 INVALID_SUB_KEY`로 거절
- `key=1,2,3,4,6,44,77,88,99`는 후속 입력 프롬프트가 존재하며 UI에서 사전 입력 모달이 필요
- 허용값 외 입력은 `400 Bad Request` + `error(code=INVALID_KEY)` 반환
- 실행 중(`running`)에는 추가 `run` 요청 거절(`409 Conflict`)
- 기본 정책: **단일 실행 락(one-active-run)** + **중복 실행 거절**
- `stop`은 멱등성 보장(중복 호출 시 성공 응답 유지)
- verdict 약어는 UI 표시에서만 `PWF` 사용, 계약값은 `PASS_WITH_FIX` 고정

### 이벤트 버전 규칙
- 모든 이벤트에 `event_version`, `seq`, `run_id` 필드 포함(필수)
- UI는 `event_version` 불일치 시 경고 배지 표시 + 안전 모드 파싱
- `seq` 역전/누락 발생 시 로그에 `EVENT_GAP` 기록

### 에러 코드 카탈로그 (초안)
| code | 의미 | UI 처리 |
|---|---|---|
| `INVALID_KEY` | 허용되지 않은 메뉴 키 | 토스트 경고 + 요청 취소 |
| `SUB_KEY_REQUIRED` | `key=0`인데 `sub_key` 누락 | Stage 0 하위 옵션 선택 모달 표시 |
| `SUB_KEY_NOT_ALLOWED` | `key!=0`인데 `sub_key` 전달 | 요청 차단 + 입력 정정 안내 |
| `INVALID_SUB_KEY` | 허용되지 않은 Stage 0 하위 키 | 하위 옵션 재선택 유도 |
| `RUN_ALREADY_ACTIVE` | 실행 중 중복 run 요청 | 상태 배지 유지 + 안내 |
| `RUN_NOT_ACTIVE` | 중지 요청 시 활성 실행 없음 | 정보 메시지 |
| `BACKEND_START_FAIL` | 백엔드 프로세스 시작 실패 | 재시도/로그 열기 버튼 |
| `WS_DISCONNECTED` | 이벤트 스트림 끊김 | 자동 재연결 + 상단 경고 |
| `INVALID_PROMPT_ID` | 존재하지 않는/만료된 prompt_id | 프롬프트 재조회 후 재입력 |
| `PROMPT_ALREADY_RESOLVED` | 이미 처리된 prompt_id 중복 입력 | 최신 상태 동기화 안내 |
| `UPDATE_BLOCKED_RUNNING` | 실행 중 업데이트 요청 | 종료 후 업데이트 안내 |
| `UPDATE_CHECKSUM_FAIL` | 패치 파일 검증 실패 | 롤백 + 실패 보고 안내 |

---

## UI 정보구조

```text
┌────────────────────────────────────────────────────────────┐
│ [프로젝트 드롭다운] [새 프로젝트] [설정] [종료]           │
├──────────────┬──────────────────────────┬──────────────────┤
│ 실행 패널     │ 상태 시각화 패널          │ 로그 패널          │
│ Stage 0      │ Office 뷰 + 에이전트      │ 실시간 stdout/WS   │
│ Stage 1      │ 상태 애니메이션            │ verdict/score 뱃지 │
│ Stage 2      │ PASS/REJECT/PWF 이펙트     │ 검색/필터/복사      │
│ Stage 3      │ (Skip/Mute 가능)          │                  │
│ Stage 4      │                            │                  │
│ One-Stop     │                            │                  │
│ Rollback     │                            │                  │
│ Wipe/Reset   │                            │                  │
│ Rewind       │                            │                  │
│ Stop         │                            │                  │
└──────────────┴──────────────────────────┴──────────────────┘
```

---

## 콘솔 메뉴 1:1 매핑

### 상위 메뉴 매핑 (Main Menu)

| 콘솔 키 | UI 버튼 | 의미 |
|---|---|---|
| `0` | Stage 0 | Stage 0 서브메뉴 진입(직접 실행 아님) |
| `1` | Stage 1 | Volume Strategy |
| `2` | Stage 2 | Arc Tactical Design |
| `3` | Stage 3 | Episode Blueprinting |
| `4` | Stage 4 | Sovereign Production |
| `6` | One-Stop | Arc-by-Arc 자동 실행 |
| `44` | Rollback | Stage 4 회차 롤백 |
| `77` | Wipe Stage4 | Stage 4 생산 기록만 삭제 |
| `88` | Reset Stage2 | Stage 2 초기화 |
| `99` | Rewind Stage2 | Stage 2 정밀 되감기 |
| `5` | Exit | 종료 |

### Stage 0 서브메뉴 매핑 (`key=0` 진입 후)

| sub_key | UI 버튼 | 실제 동작 |
|---|---|---|
| `1` | 기존 방식 | Bible/Treatment 파일 선택 |
| `2` | 컨셉 → Bible 생성 | `stage_0_extended(mode=1)` (`STAGE0_AVAILABLE=true` 필요) |
| `3` | 역설계 | `stage_0_extended(mode=2)` (`STAGE0_AVAILABLE=true` 필요) |
| `4` | Bible JSON 임포트 | `stage_0_extended(mode=3)` (`STAGE0_AVAILABLE=true` 필요) |
| `5` | Block 확장 | `stage_0_extended(mode=4)` (`STAGE0_AVAILABLE=true` 필요) |
| `6` | 스타일 레퍼런스 분석 | `stage_0_extended(mode=5)` (`STAGE0_AVAILABLE=true` 필요) |
| `0` | 취소 | Stage 0 취소 후 상위 메뉴 복귀 |

운영 메모:
- 콘솔 기준 기본값은 `1`(입력값 비었을 때 기존 방식 경로 진입).
- `STAGE0_AVAILABLE=false` 환경에서는 `2~6` 버튼을 UI에서 비활성화한다.

### 기타 키 후속 입력 매핑 (Mode A stdin 시퀀스)

| key | 후속 입력 | 옵션/기본값 | UI 처리 포인트 |
|---|---|---|---|
| `1` (Stage 1) | 진행/스킵 선택 | `[1] 진행 [2] 스킵` (기본 `1`) | Stage 1 버튼 클릭 시 2버튼 모달 표시 |
| `2` (Stage 2) | Stage 1 미완료 시 진행 확인 | `(y/N)` (기본 `N`) | 사전 경고 모달 후 확정 시 진행 |
| `2` (Stage 2) | 목표 Arc 상한 입력 | `현재+1 ~ 최대` (기본 `현재+5`) | 숫자 입력 모달/슬라이더 |
| `2` (Stage 2) | 실패 시 분기 선택 | `[1] 건너뛰기 [2] 중단 [3] 다시 하기 [4] 수동 개입` (기본 `2`) | 실패 핸들링 모달 필수 |
| `2` (Stage 2) | 수동 개입 후 추가 입력 | `[Enter]=재시도`, `skip`, `quit` | option `4` 선택 시 2차 모달 |
| `3` (Stage 3) | 목표 화 입력 | `현재+1 ~ 최대` (기본 `최대`) | 숫자 입력 모달 |
| `3` (Stage 3) | 실패 처리 | 후속 입력 없음(즉시 중단) | UI에서 자동 중단/원인 안내 |
| `4` (Stage 4) | 목표 화 입력(단독 실행 시) | `1 ~ 최대 blueprint 화수` | 숫자 입력 모달 |
| `4` (Stage 4) | 스타일 선택(스타일 가이드 없을 때) | `[1] 카카오 [2] 네이버` (기본 `1`) | 조건부 스타일 모달 |
| `4` (Stage 4) | 라운드 소진 시 처리 | `[1] 최선 결과물 채택 [2] 건너뛰기` (기본 `2`) | 실패 후 의사결정 모달 |
| `6` (One-Stop) | 배치 Arc 개수 입력 | `1 ~ 남은 Arc` (기본 `min(3, 남은수)`) | 초기 배치 크기 모달 |
| `6` (One-Stop) | Stage 3 실패 시 분기 | `[1] 건너뛰기 [2] 중단` (기본 `2`) | 오류 복구 모달 |
| `6` (One-Stop) | 배치 후 계속 여부 | `[1] 계속 [2] 중단` (기본 `1`) | 배치 완료 후 연장 모달 |
| `44` (Rollback) | 되감기 화수 + 확인 | `1 ~ 최신화`, 확인 `(y/n)` | UI 2단계 확인(CLI는 1단계) |
| `77` (Wipe) | 삭제 확인 | `(y/n)` | UI 2단계 확인(CLI는 1단계) |
| `88` (Reset Stage2) | 삭제 확인 | `(y/n)` | UI 2단계 확인(CLI는 1단계) |
| `99` (Rewind Stage2) | 시작 Arc 번호 + 확인 | `1 ~ 총 Arc`, 확인 `(y/n)` | UI 2단계 확인(CLI는 1단계) |

운영 원칙:
- UI는 key 클릭 후 필요한 후속 입력을 모달로 수집하고, 백엔드에는 순차 `stdin`으로 주입한다.
- 위험작업(`44/77/88/99`)은 확인 모달 2회(요약 + 최종 확인) 적용을 권장한다.
- Stage 3는 실패 시 건너뛰기 없이 즉시 중단되는 구조이므로 UI에서도 동일 정책을 유지한다.

감리 근거(코드 기준, 2026-03-06):
- `main_a.py`: 메인 메뉴 `choice=="0"` 시 `_phase_0_recovery()` 호출
- `modules/core/stage01_helpers.py`: Stage 0 서브메뉴 출력(`[0]~[6]`) 및 `p0_choice` 분기 처리
- `modules/core/stage2_orchestrator.py`: Stage 2 목표 범위/실패 분기 입력 처리
- `modules/core/stage3_orchestrator.py`: Stage 3 목표 화수 입력 처리
- `modules/core/stage4_orchestrator.py`: Stage 4 목표 화수/스타일/실패 fallback 입력 처리
- `modules/core/services/project_service.py`: `44/77/88/99` 키 후속 입력 및 위험작업 확인 처리

---

## 시각화/연출 가이드 (Office Chic)

### 톤
- 오피스/스튜디오 무드(저채도, 가독성 우선)
- 상태 전달 중심(장식 과다 금지)

### 상태 연출
- `RUNNING`: 에이전트 작업 루프
- `PASS_WITH_FIX`: 문서 다듬기 연출 + `한 번 더`
- `PASS`: 완료 하이라이트 + `채택`
- `REJECT`: 짧은 실패 연출 + `재시도`

### 규칙
- 이펙트 길이 1.0~1.5초
- `Skip animation`, `Mute`, `Low spec mode` 제공
- 로그 가독성을 가리는 풀스크린 연출 금지
- 기본값: 연출 `ON` (저강도), 필요 시 즉시 OFF 가능

---

## 스플래시 스크린

### 목적
- exe 실행 직후 Python 프로세스 기동 대기 시간을 자연스럽게 커버
- 첫 실행(PyInstaller one-file 압축 해제, 10~30초) 안내

### 구현 방식
- Electron `BrowserWindow` 별도 창 (`frame: false`, 400×260)
- Python ready 신호(`GET /status` → `"state":"idle"`) 수신 시 자동 닫힘

### 로고
- 전용 이미지 없음 → `lucide-react` 아이콘으로 대체
- 추천 아이콘: `PenLine` (글쓰기 도구 직관적 표현) 또는 `BookOpen`
- 색상: `#475569` (저채도 slate, Office Chic 톤 일치)
- 크기: 64×64px, 중앙 배치

```
설치: npm install lucide-react
사용: import { PenLine } from 'lucide-react'
```

### 레이아웃
```
┌──────────────────────────────────┐
│                                  │
│         [PenLine 아이콘]          │
│           글  도  비              │
│                                  │
│   ─────────────────────────      │  ← CSS 애니메이션 로딩바
│                                  │
│   시작하는 중...                  │  ← 첫 실행 시: "첫 실행은
│                                  │     잠시 시간이 걸립니다"
└──────────────────────────────────┘
```

### 첫 실행 감지
- `%LOCALAPPDATA%/Geuldobi/.first_run` 파일 유무로 판단
- 없으면 첫 실행 → 안내 문구 표시 + 파일 생성
- 있으면 일반 실행 → "시작하는 중..." 만 표시

### 디자인 토큰
| 항목 | 값 |
|---|---|
| 배경 | `#f8fafc` (light) / `#0f172a` (dark, 추후) |
| 아이콘 색 | `#475569` |
| 텍스트 색 | `#64748b` |
| 로딩바 색 | `#94a3b8` |
| 폰트 | 시스템 기본 (`-apple-system, "Malgun Gothic"`) |

---

## 파일 관리 UX (폴더 비노출)
- 기본 저장 위치: `%LOCALAPPDATA%/Geuldobi/projects`
- 설치/저장 경로 정책: 기본 경로 고정, 고급 설정에서만 변경 허용
- UI에는 절대경로 미노출
- 제공 기능:
  - 프로젝트 드롭다운
  - 가져오기(파일/ZIP)
  - 내보내기(ZIP)
  - 백업/복원(원클릭)

---

## API 키 및 보안
- 첫 실행 시 키 입력 화면 제공
- 로컬 암호화 저장(평문 저장 금지)
- 팀 공유 키 번들 금지(개인 키 원칙)
- 로그 마스킹: 키/민감 토큰 자동 숨김
- 로컬 API 접근제어: loopback + 세션 토큰 방식

---

## 패키징/배포

| 단계 | 도구 | 결과물 |
|---|---|---|
| Python 번들 | PyInstaller | backend 실행 바이너리 |
| Desktop 빌드 | Electron Builder | 앱 패키지 |
| 설치 배포 | NSIS | `글도비-setup.exe` |

예상 설치 크기: 300~500MB

---

## 업데이트 전략

### 흐름
```text
앱 시작
→ manifest 버전 체크
→ 새 버전 존재 시 "패치하시겠습니까?"
→ 다운로드
→ 재시작 후 적용
```

### 최소 인프라
- version manifest JSON
- 패치 파일 저장소(GitHub Releases / R2 / S3)
- 업데이트 채널 운영: `stable + beta` (beta 선검증 후 stable 배포)

### manifest 스키마 (v1 권장)
```json
{
  "version": "1.4.0",
  "channel": "stable",
  "published_at": "2026-03-06T10:30:00+09:00",
  "min_supported_version": "1.0.0",
  "packages": {
    "windows-x64": {
      "url": "https://example.com/geuldobi-1.4.0-win-x64.zip",
      "sha256": "HEX_SHA256",
      "size_bytes": 412345678
    }
  },
  "notes": "감리 2차 안정성 개선"
}
```

### 필수 안전장치
- 코드 서명
- 체크섬 검증
- 실패 시 롤백
- stable/beta 채널 분리

### 업데이트-실행 상호배제 규칙 (2차 감리 보강)
- `running` 상태에서는 업데이트 시작 금지
- 업데이트는 `idle` 상태에서만 진행
- 업데이트 승인 시 현재 작업 중단 확인 팝업 필수
- 실패 복구 후 자동으로 이전 실행 파일 재바인딩
- 사용자 데이터(`projects/`)는 업데이트 대상에서 제외

---

## 단계별 실행 계획

### P0: 스파이크 (1~2일)
- subprocess stdin 제어 가능성 확인
- stdout 파싱 안정성 확인
- PyInstaller에서 sqlite-vec 포함 테스트

완료 기준:
- 로컬에서 버튼 입력 3개 이상 정상 실행

### P1: 런너 + 로그 패널 (2~3일)
- Electron 껍데기 + Python 런너
- 실시간 로그 표시
- 프로젝트 선택 UI

완료 기준:
- 비개발자 1명이 터미널 없이 Stage 3 실행 성공

### P2: 메뉴 1:1 실행 패널 (2일)
- Stage/운영 버튼 전체 구현
- Stage 0 버튼 클릭 시 하위 옵션(0~6) 패널 표시
- Stop/상태 표시 구현

완료 기준:
- 메인 키 + Stage 0 하위 키 전부 UI에서 호출 가능

### P3: 상태 시각화 패널 (2일)
- 에이전트 상태 애니메이션
- verdict 이펙트 + Skip/Mute

완료 기준:
- PASS/REJECT/PWF가 UI에서 즉시 구분됨

### P4: 설치/업데이트 (2~3일)
- 인스톨러 빌드
- manifest 기반 업데이트

완료 기준:
- 클린 PC 설치 + 업데이트 팝업 시나리오 통과

---

## 품질 기준 (문서 기준선)
- 기존 테스트 기준선 유지: `pytest tests/ -q` 최신 green
- 린트 통과: 변경 파일 `ruff check` green
- UI 응답성: 버튼 클릭 후 200ms 내 상태 표시 시작
- 안정성: 실행 중 앱 크래시율 0% 목표(PoC 테스트 샘플 기준)
- 계약 안정성: 이벤트 스키마 스냅샷 테스트 green

---

## 주요 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| stdout 포맷 변경 | 상태 파싱 실패 | Mode B(API 이벤트 계약)로 전환 |
| sqlite-vec 번들 실패 | 앱 실행 불가 | P0에서 바이너리 포함 선검증 |
| 설치 파일 대용량 | 배포 지연 | 내부 배포 채널 + 증분 업데이트 |
| 키 관리 부실 | 보안 이슈 | 로컬 암호화 + 마스킹 + 개인 키 원칙 |

---

## 운영 시나리오 (실사용 기준)

### 시나리오 A: 신규 사용자 첫 실행
1. 앱 실행
2. API 키 입력/저장
3. 프로젝트 생성(장르/이름)
4. Stage 0 또는 Stage 2부터 실행
5. 로그 패널에서 진행/판정 확인

성공 조건:
- 터미널 노출 없이 흐름 완료
- 앱 재실행 시 키/프로젝트 정보 재사용

### 시나리오 B: 기존 프로젝트 이어쓰기
1. 프로젝트 드롭다운에서 선택
2. 현재 진행 상태 배지 확인
3. 필요한 Stage만 선택 실행
4. PASS/REJECT/PASS_WITH_FIX 상태 확인
5. 결과 내보내기(ZIP)

성공 조건:
- 중간 단계부터 재개 가능
- 잘못된 단계 호출 시 UI 가드 메시지 제공

### 시나리오 C: 운영자 업데이트 적용
1. 앱 시작 시 새 버전 감지
2. `패치하시겠습니까?` 선택
3. 다운로드/검증/재시작
4. 버전 변경 확인

성공 조건:
- 실패 시 자동 롤백
- 데이터 손실 없음

---

## 이벤트 사전 (Mode B 표준)

> UI는 `type` 기반으로 라우팅하고, 알 수 없는 이벤트는 무시 + 로그 기록.

| type | 필수 필드 | 설명 |
|---|---|---|
| `run_state` | `state` | 전체 실행 상태 (`idle/running/stopping/error`) |
| `stage_start` | `stage`, `ts` | Stage 시작 |
| `stage_result` | `stage`, `verdict`, `ts` | Stage 결과 |
| `agent_state` | `agent`, `state`, `ts` | 에이전트 상태 변화 |
| `log_line` | `level`, `message`, `ts` | 로그 스트리밍 |
| `progress` | `current`, `total`, `label` | 배치 진행률 |
| `error` | `code`, `message`, `recoverable` | 오류 이벤트 |

상태 값 권장:
- `verdict`: `PASS`, `PASS_WITH_FIX`, `REJECT`, `ERROR`
- `agent.state`: `idle`, `walk`, `work`, `review`, `typing`

---

## 오류 처리/복구 정책

### 원칙
- 앱은 `fail-soft`: 에러가 나도 로그/상태 화면은 살아있어야 함.
- 백엔드는 `best effort`: 중단 요청 후 정상 정리 시도.

### 케이스별 대응
| 케이스 | UI 동작 | 백엔드 동작 |
|---|---|---|
| subprocess 시작 실패 | 즉시 에러 배너 + 재시도 버튼 | 프로세스 재기동 1회 |
| WebSocket 끊김 | 상단 경고 배지 + 자동 재연결 | 세션 유지 |
| Stage 실행 중 예외 | `ERROR` 판정 표시 + 로그 강조 | 가능한 범위까지 정리 후 idle |
| 중지 버튼 누름 | `Stopping...` 배지 | 안전 종료 시퀀스 호출 |
| 업데이트 실패 | 실패 안내 + 이전 버전 복귀 | 롤백 후 버전 잠금 |

---

## UX 세부 규칙

| 항목 | 규칙 |
|---|---|
| 버튼 비활성화 | 실행 중 중복 클릭 방지를 위해 동일 액션 버튼 잠금 |
| 로그 자동 스크롤 | 기본 ON, 사용자가 스크롤 올리면 자동 OFF |
| 판정 배지 유지 시간 | 4초 표시 후 로그 헤더로 축약 |
| 단축키 | `Ctrl+Enter=실행`, `Esc=중지 요청` |
| 접근성 | 색상 외 텍스트/아이콘으로 상태 중복 표기 |

---

## 데이터/저장 정책

| 데이터 | 저장 위치 | 보존 정책 |
|---|---|---|
| 앱 설정 | `%LOCALAPPDATA%/Geuldobi/config` | 앱 삭제 시 제거 옵션 |
| API 키(암호화) | `%LOCALAPPDATA%/Geuldobi/secure` | 사용자 재설정 가능 |
| 실행 로그 캐시 | `%LOCALAPPDATA%/Geuldobi/logs` | 최근 N일(기본 14일) |
| 프로젝트 데이터 | `%LOCALAPPDATA%/Geuldobi/projects` | 사용자 명시 삭제 전 유지 |

---

## 데모 시나리오 (10분)

1. 앱 실행 후 프로젝트 선택
2. Stage 3 실행
3. 로그 스트리밍과 상태 시각화 확인
4. PASS_WITH_FIX 케이스 확인(배지/연출)
5. Stage 4 실행 후 결과 내보내기
6. 업데이트 팝업 모의 시연

데모 성공 기준:
- 터미널 창 0개
- 실행/중지/재실행 연속 동작 성공
- verdict 3종 시각적으로 구분

---

## 릴리즈 체크리스트 (PoC)

| 체크 | 기준 |
|---|---|
| 기능 | Stage 버튼 1:1 호출 동작 |
| 안정성 | 30분 연속 실행 중 앱 크래시 없음 |
| 품질 | `pytest tests/ -q` 최신 green |
| 보안 | API 키 평문 미저장 확인 |
| 배포 | 클린 PC 설치/실행/삭제 검증 |
| 복구 | 업데이트 실패 롤백 검증 |

---

## 의사결정 로그 (ADR 요약)

| ID | 결정 | 이유 |
|---|---|---|
| ADR-001 | CLI 유지 + GUI 추가 | 개발/운영 병행 및 리스크 최소화 |
| ADR-002 | Mode A로 시작 | 초기 구현 속도 우선 |
| ADR-003 | Mode B로 수렴 | 장기 안정성/유지보수성 확보 |
| ADR-004 | Office Chic 톤 | 비개발자 수용성 + 업무툴 일관성 |
| ADR-005 | 업데이트 팝업 방식 | 현장 배포/유지보수 단순화 |

---

## 실행 태스크 백로그 (Jira 변환용)

| ID | 작업 | 예상 | 완료 조건 |
|---|---|---|---|
| UI-001 | Electron 셸 생성 (React/Vite 포함) | 0.5d | 앱 창/기본 라우트 구동 |
| UI-002 | Python 런너 모듈 구현 (start/stop/restart) | 1d | subprocess 제어/종료 코드 안정 |
| UI-003 | stdout/stderr 스트리머 구현 | 0.5d | 로그 패널 실시간 표시 |
| UI-004 | 실행 패널 버튼 1:1 매핑 | 0.5d | 키 매핑 전부 동작 |
| UI-005 | 프로젝트 드롭다운/생성 화면 | 1d | 선택/생성 후 상태 반영 |
| UI-006 | verdict 파서(PASS/PWF/REJECT) | 0.5d | 뱃지/카피 정확 표기 |
| UI-007 | Office 상태 시각화 패널 | 1d | run/verdict 이벤트 반응 |
| UI-008 | 설정 화면(API 키/애니메이션 옵션) | 0.5d | 저장/재로딩 정상 |
| BE-001 | FastAPI 브리지 초안(`/run`,`/stop`,`/events`) | 1d | HTTP/WS 기본 연결 |
| BE-002 | 이벤트 emit 포인트 연결 | 1d | agent/stage/log 이벤트 송출 |
| PKG-001 | PyInstaller spec 작성 + sqlite-vec 포함 | 1d | backend 단독 실행 통과 |
| PKG-002 | Electron Builder NSIS 인스톨러 | 0.5d | setup.exe 설치/실행 |
| OPS-001 | 업데이트 manifest + 체크섬 검증 | 1d | 팝업/다운로드/적용 통과 |
| QA-001 | PoC E2E 시나리오 테스트 | 0.5d | 체크리스트 전항목 통과 |

---

## 초기 파일 구조 제안

```text
desktop/
├─ app/
│  ├─ main/                 # Electron Main
│  │  ├─ runner.ts          # Python subprocess 제어
│  │  ├─ updater.ts         # 버전 체크/업데이트
│  │  └─ ipc.ts             # IPC 라우팅
│  ├─ renderer/             # React UI
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ stores/
│  │  └─ styles/
│  └─ shared/
│     └─ event-types.ts     # 이벤트 타입 정의
├─ backend/
│  ├─ ui_server.py          # FastAPI 브리지 (Mode B)
│  └─ entrypoint.py         # 실행 진입점 래퍼
├─ build/
│  ├─ pyinstaller.spec
│  └─ electron-builder.yml
└─ docs/
   └─ ui-runbook.md
```

---

## 운영 런북 초안

1. 앱 실행 실패 시 `로그 열기`로 최근 로그 확인
2. `Runner restart` 버튼으로 백엔드만 재기동
3. 2회 연속 실패 시 `Safe mode`(연출 OFF, 로그 전용 모드) 전환
4. 업데이트 실패 시 `Rollback now` 버튼으로 이전 버전 즉시 복귀
5. 장애 보고 시 첨부 파일:
   - 앱 버전
   - 최근 로그 200줄
   - 프로젝트명/실행 Stage

---

## 성능/운영 SLO (PoC 목표)

| 항목 | 목표 |
|---|---|
| 앱 콜드 스타트 | 5초 이내(권장 PC 기준) |
| Stage 실행 반응 | 버튼 클릭 후 200ms 내 상태 변경 표시 |
| 로그 지연 | 백엔드 출력 후 UI 반영 1초 이내 |
| 장시간 안정성 | 1시간 연속 실행 중 크래시 0건 |
| 업데이트 성공률 | 95% 이상(실패 시 롤백 보장) |

---

## 보안 체크리스트 (최소)

| 항목 | 적용 |
|---|---|
| API 키 암호화 저장 | 필수 |
| 민감정보 로그 마스킹 | 필수 |
| 업데이트 파일 체크섬 검증 | 필수 |
| 코드 서명 | 권장(배포 전 필수 전환) |
| HTTPS/TLS 전송 | 필수(업데이트/원격 API) |
| 디버그 모드 보호 | 필수(릴리즈에서 비활성) |

---

## Mode A → Mode B 마이그레이션 계획

### 목표
- 초기 속도(Mode A)와 장기 안정성(Mode B)을 모두 확보.

### 단계
1. Mode A 기본 동작 완성 (stdin/stdout)
2. 이벤트 파서 규칙을 `event-types`로 고정
3. FastAPI 브리지 도입 후 Mode B 병행 지원
4. 기능 플래그로 런타임 전환 (`backend.mode = A|B`)
5. Mode B 안정화 후 기본값 전환 여부 별도 승인(현 기본값 A 유지)

### 컷오버 기준
- 2주간 Mode B 크래시/이벤트 누락 중대 이슈 0건
- 기존 E2E 시나리오 100% 통과

---

## 테스트 매트릭스

| 분류 | 케이스 | 기준 |
|---|---|---|
| 기능 | 메인 메뉴 키 1:1 실행 | 전 키 정상 호출 |
| 기능 | Stage 0 하위 키 1:1 실행 | `0 -> sub_key` 정상 분기 |
| 기능 | Stage 1 스킵 분기 | `1 -> [진행/스킵]` 양 경로 정상 |
| 기능 | Stage 2 실패 분기 | `[건너뛰기/중단/다시 하기/수동]` 정상 동작 |
| 기능 | Stage 2 수동 개입 2차 입력 | `[Enter]/skip/quit` 분기 정상 동작 |
| 기능 | Stage 3 목표 화 입력 | 범위 검증 + 기본값 적용 정상 |
| 기능 | Stage 3 실패 중단 정책 | 실패 시 후속 화 건너뛰기 없이 즉시 중단 |
| 기능 | Stage 4 fallback 분기 | `[최선 채택/건너뛰기]` 분기 정상 |
| 기능 | One-Stop 배치 분기 | 배치 크기/계속/추가 배치 입력 정상 |
| 기능 | 위험 작업 키 확인 | `44/77/88/99` 확인 모달 후 실행 |
| 기능 | 프롬프트 이벤트 왕복 | `prompt_request -> input -> prompt_resolved` 정상 |
| 기능 | 프롬프트 타임아웃 | default 적용 + `prompt_timeout` 이벤트 기록 |
| 기능 | 중지/재실행 | 3회 연속 성공 |
| 기능 | 프로젝트 전환 | 상태/데이터 오염 없음 |
| 기능 | 실행 중 중복 run 요청 | 409 거절(중복 실행 금지) |
| 기능 | 유효하지 않은 key 요청 | 400 + INVALID_KEY 반환 |
| 기능 | `key=0` + `sub_key` 누락 | 400 + SUB_KEY_REQUIRED 반환 |
| 기능 | `key!=0` + `sub_key` 전달 | 400 + SUB_KEY_NOT_ALLOWED 반환 |
| 기능 | 유효하지 않은 `sub_key` 요청 | 400 + INVALID_SUB_KEY 반환 |
| 연동 | WS 재연결 | 3초 내 자동 복구 |
| 연동 | 업데이트 팝업 | 버전 비교 정확 |
| 연동 | running 상태 업데이트 시도 | 시작 차단 + 안내 메시지 |
| 보안 | API 키 저장 | 평문 노출 없음 |
| 보안 | 로컬 API 접근제어 | loopback 바인딩 + 토큰 검증 |
| 패키징 | 클린 PC 설치 | 실행/삭제 정상 |
| 회귀 | 기존 pytest/ruff | 최신 green 유지 |

---

## 관측성/텔레메트리 (로컬 우선)

수집 원칙:
- 기본은 로컬 파일 저장, 외부 전송은 옵트인.
- 개인/민감 정보 제외.

권장 지표:
- `app_start_ms`, `runner_start_ms`
- `stage_run_count`, `stage_run_fail_count`
- `update_check_count`, `update_fail_count`
- `ws_reconnect_count`

활용:
- 병목 구간 식별
- 업데이트 실패 원인 추적
- PoC 의사결정 데이터 확보

---

## 범위 고정선 (Scope Guard)

PoC에서 하지 않음:
- 멀티테넌시/계정 시스템
- 서버 사이드 장기 세션 관리
- 고급 3D 월드/실시간 멀티플레이
- 복잡한 권한 정책 엔진

PoC에서 반드시 함:
- 터미널 비노출 실행
- 메뉴 1:1 버튼
- 로그/판정 가시화
- 설치/업데이트 최소 경로

## 도입 순서 원칙 (POC 우선)

핵심 원칙:
- 원격 패치/클라우드 인프라는 `POC 기능 완성` 이후에 착수한다.
- PoC가 불안정한 상태에서 원격 패치부터 도입하지 않는다.

단계별 진행:
| 단계 | 목표 | 착수 조건 | 산출물 |
|---|---|---|---|
| 1단계 (POC 완성) | 로컬 앱 기능/안정성 확보 | 메뉴 1:1 + 핵심 E2E 통과 | `qa-report-v1.16.md` |
| 2단계 (내부 재배포 검증) | 파일 재배포 운영 리허설 | 1단계 완료 | 설치/업데이트/롤백 운영 로그 |
| 3단계 (원격 패치 도입) | 중앙 manifest/패치 배포 | 1~2단계 완료 + 운영 승인 | 원격 패치 runbook + 승인 증빙 |

원격 패치 3단계 최소 요구:
- 체크섬/서명 검증
- `stable/beta` 채널 분리
- 승인 로그(`risk-approval-log`)와 배포 로그 추적 가능

---

## 문서 버전

- `v1.0` 초기 구조안
- `v1.1` API/실행계약 통일
- `v1.2` 운영/복구/체크리스트 추가
- `v1.3` SLO/보안/마이그레이션/테스트 매트릭스 추가
- `v1.4` 감리 2차 반영(동시성/이벤트 버전/업데이트 상호배제)
- `v1.5` 의사결정 확정(Mode/채널/보존기간/연출/경로/인증)
- `v1.6` 고도화 루프 1(실행 API/상태머신/타임아웃 명세 추가)
- `v1.7` 고도화 루프 2(자산 거버넌스/라이선스 감리 템플릿 추가)
- `v1.8` 고도화 루프 3(실행 패킷/운영 KPI/릴리즈 서명 절차 추가)
- `v1.9` 콘솔 1:1 재감리(메뉴 `0` 하위 매핑/API 계약/QA 항목 보강)
- `v1.10` 즉시 실행 런북/테스트 케이스/릴리즈 산출물 표준 추가
- `v1.11` 추가 감리 3회 반영(오류코드 세분화/실행 안정성/승인 증빙 표준화)
- `v1.12` 타 Stage 후속입력 매핑 감리 + 문서 고도화 3회 점검 반영
- `v1.13` 디테일 재감리 5회 + 추가 고도화 점검 3회 반영
- `v1.14` 2차 고도화 테마(구현 준비) 반영: 산출물/티켓/DoD/착수계획 고정
- `v1.15` 3차 고도화 실행판 반영: `IMP-001~003` 템플릿 고정 + 스모크 자동화 명세 + 위험키 승인 게이트 강화
- `v1.16` 4차 고도화 실행 반영: 실파일 생성(`IMP-001~003`, `IMP-007`, `IMP-008`) + 승인 운영팩 + 릴리즈 No-Go 자동 규칙
- `v1.17` 도입 순서 원칙 반영: `POC 완성 -> 내부 재배포 검증 -> 원격 패치` 게이트 고정

---

## 역할 분담 (RACI)

| 업무 | PO/기획 | UI 개발 | 백엔드 개발 | QA | 운영 |
|---|---|---|---|---|---|
| 요구사항 확정 | A | C | C | C | C |
| Electron UI 구현 | C | R | C | C | I |
| FastAPI 브리지 | C | C | R | C | I |
| 패키징/설치 | I | R | R | C | C |
| 테스트/검증 | I | C | C | R | C |
| 배포/업데이트 | I | C | C | C | R |

`R`: Responsible, `A`: Accountable, `C`: Consulted, `I`: Informed

---

## 마일스톤/게이트

| 마일스톤 | 목표 | 게이트 조건 |
|---|---|---|
| M1 (P1 완료) | 런너 + 로그 패널 동작 | Stage 3 실행 성공, 로그 실시간 표시 |
| M2 (P2 완료) | 메뉴 1:1 버튼 완성 | 메인 키/Stage 0 하위 키 호출 + Stop 정상 동작 |
| M3 (P3 완료) | 상태 시각화 완성 | verdict 3종 시각 구분 + Skip/Mute 동작 |
| M4 (P4 완료) | 설치/업데이트 검증 | 클린 PC 설치 + 업데이트/롤백 통과 |

릴리즈 게이트:
- 기능/품질/보안 체크리스트 100% 충족 시에만 배포

---

## 비용 추정 (초기 운영)

### 전제
- AI 추론은 사용자 로컬 실행
- 서버는 버전 매니페스트 + 패치 파일 호스팅만 담당

| 항목 | 구성 | 월 예상 |
|---|---|---|
| 업데이트 manifest | 정적 JSON | 거의 0 |
| 패치 파일 저장소 | GitHub Releases / R2 / S3 | 0 ~ 소액 |
| 트래픽 | 팀 규모/업데이트 빈도 의존 | 소액 |
| 코드 서명 인증서 | 연 단위 | 별도 비용 |

메모:
- 실비가 커지는 지점은 `원격 추론 서버` 도입 시점

---

## 호환성 매트릭스 (PoC)

| 항목 | 지원 범위 |
|---|---|
| OS | Windows 10/11 (64-bit) |
| CPU | x64 권장 |
| RAM | 16GB 권장(최소 8GB) |
| 디스크 | 설치 여유 1GB+ 권장 |
| 네트워크 | 업데이트 체크/모델 호출 시 필요 |

비지원(초기):
- macOS, Linux
- ARM 네이티브 패키징

---

## 장애 등급/대응 SLA

| 등급 | 정의 | 목표 대응 |
|---|---|---|
| Sev-1 | 앱 실행 불가/데이터 손실 위험 | 당일 핫픽스 |
| Sev-2 | 핵심 기능 일부 불가(Stage 실행 실패 등) | 1~2영업일 |
| Sev-3 | UI 결함/비핵심 기능 문제 | 다음 정기 배포 |
| Sev-4 | 개선 요청/경미한 버그 | 백로그 반영 |

보고 최소 항목:
- 앱 버전, OS 버전, 재현 절차, 최근 로그 200줄

---

## 확정 의사결정 (v1.5)

| ID | 주제 | 확정안 |
|---|---|---|
| OI-001 | 기본 실행 모드 | Mode A 기본, Mode B는 beta에서 선검증 |
| OI-002 | 업데이트 채널 운영 | `stable + beta` |
| OI-003 | 로그 보존 기간 | 기본 14일 |
| OI-004 | 연출 기본값 | ON(저강도), Skip/Mute 상시 제공 |
| OI-005 | 설치 경로 정책 | 기본 경로 고정, 고급 설정에서만 변경 허용 |
| OI-006 | running 중 추가 run 처리 | 기본 409 거절(중복 실행 금지) |
| OI-007 | 로컬 API 인증 방식 | loopback + 세션 토큰 |

---

## PoC 종료 기준 (Exit Criteria)

아래를 모두 만족하면 PoC 종료:
1. 비개발자 2명 이상이 터미널 없이 Stage 3~4 실행 성공
2. verdict 3종(PASS/PASS_WITH_FIX/REJECT) 즉시 시각 구분
3. 설치/업데이트/롤백 E2E 1회 이상 통과
4. `pytest tests/ -q`, `ruff check` 최신 green 유지
5. Sev-1/Sev-2 미해결 이슈 0건

---

## 감리 3차 결과

### 확인 항목
- API 계약/동시성/업데이트 정책 간 문구 충돌 여부
- 이벤트 스키마 필드 필수성 명시 여부
- 확정 의사결정(OI-001~007)과 테스트 매트릭스 정합성

### 보강 내용
- 이벤트 버전 필드(`event_version/seq/run_id`)를 권장에서 필수로 상향
- 중복 실행 처리 기준을 문서 전역에서 `409 거절`로 통일
- Mode 전환 문구를 `기본값 A 유지 + 별도 승인`으로 명확화

### 감리 결론
- 설계 충돌 이슈: 해소
- 남은 리스크: 구현 단계(런너/패키징/업데이트) 기술 검증 리스크만 존재

---

## 추가 감리 3회 결과 (v1.11)

### 1회차 감리: API 계약 엄밀성
- 점검: `sub_key` 누락/오입력/불필요 전달을 서로 다른 오류로 구분하는지 확인
- 조치:
  - `SUB_KEY_NOT_ALLOWED` 오류 코드 추가
  - `POST /run` 실패 케이스에 `SUB_KEY_NOT_ALLOWED` 반영
  - E2E `TC-P0-005` 기대값을 `INVALID_SUB_KEY`에서 `SUB_KEY_NOT_ALLOWED`로 수정

### 2회차 감리: 런북 실행 안정성
- 점검: 비개발자 환경에서 PowerShell 실행 정책으로 첫 실행이 막히는지 확인
- 조치:
  - `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 대응 절차 추가
  - venv 활성화 실패 시 직접 실행 대체 커맨드(`.venv\\Scripts\\python.exe`) 추가

### 3회차 감리: 릴리즈 승인 운영성
- 점검: Go/No-Go 의사결정 시 증빙 파일/승인 책임자가 명확한지 확인
- 조치:
  - 승인 증빙 표(증빙 파일 + 승인자) 추가
  - 기능/안정성/보안/운영 게이트별 책임 경로 명시

### 결론
- 문서 성격이 “제안서”에서 “즉시 실행 가능한 운영 지침서” 수준으로 상향됨
- 남은 리스크는 구현체 준비(실제 브리지 서버/패키징 자동화) 영역으로 한정됨

---

## 타 Stage 서브메뉴 매핑 감리 3회 결과 (v1.12)

### 1회차 감리: 메뉴 키별 후속 입력 누락 점검
- 점검 범위: `1/2/3/4/6/44/77/88/99`
- 결과: Stage 0 외에도 다수 키에 후속 프롬프트 존재 확인
- 조치: `기타 키 후속 입력 매핑` 표 신설 (UI 모달/기본값/위험작업 확인 포함)

### 2회차 감리: 분기/실패 처리 흐름 점검
- 점검 범위: Stage 2 실패 분기, Stage 4 fallback, One-Stop 배치 연장 분기
- 결과: 단순 1:1 키 매핑만으로는 비개발자 UI에서 재현 불가 구간 존재
- 조치: 테스트 매트릭스/QA 체크리스트/E2E 케이스에 분기별 검증 항목 추가

### 3회차 감리: 운영 위험 키 점검
- 점검 범위: `44/77/88/99` 파괴적 작업
- 결과: 확인 절차 표준화 필요
- 조치: 위험 작업 키를 “2단계 확인 모달” 권장 정책으로 고정

### 결론
- “키 매핑” 기준이 `메인 키`에서 `메인 키 + 후속 입력 시퀀스` 기준으로 확장됨

---

## 문서 고도화 가능성 3회 점검 결과 (v1.12)

### 점검 1
- 질문: 후속 입력을 API 파라미터 기반으로 무프롬프트화할 수 있는가?
- 결론: 가능. 단, 현재 구현은 Mode A stdin 기반이므로 차기 단계(Mode B) 백로그로 분리 유지.

### 점검 2
- 질문: 비개발자 실행 실패를 더 줄일 즉시 조치가 있는가?
- 결론: 있음. 실행 정책 오류 대응/대체 실행 커맨드를 런북에 반영 완료.

### 점검 3
- 질문: 배포 승인 시 책임/증빙이 충분히 명시됐는가?
- 결론: 보강 완료. Go/No-Go 증빙표(파일+승인자)로 운영 의사결정 경로 확보.

최종 판정:
- 추가 고도화 여지는 존재하나, 현재 문서는 “착수/검증/승인”을 즉시 수행 가능한 수준.

---

## 디테일 재감리 5회 결과 (v1.13)

### 1회차: 키-후속입력 전수 재검증
- 점검 범위: `0/1/2/3/4/6/44/77/88/99`의 후속 프롬프트 유무와 기본값
- 결과: Stage 2 수동개입(옵션 `4`)의 2차 입력(`Enter/skip/quit`) 누락 확인
- 조치: 후속 입력 매핑 표에 2차 입력 행 추가

### 2회차: 기본값/범위 검증 재점검
- 점검 범위: 숫자 입력(`Arc 상한`, `목표 화`, `되감기 화수/Arc`)의 min/max/기본값
- 결과: Stage 3 실패 정책(건너뛰기 없음, 즉시 중단) 명시 부족 확인
- 조치: 후속 입력 표/테스트 매트릭스/QA에 “Stage 3 실패 즉시 중단” 명시

### 3회차: 실패 분기 일관성 점검
- 점검 범위: Stage 2/4/One-Stop 실패 분기와 사용자가 보는 선택지
- 결과: 테스트 케이스에서 Stage 2 수동개입 2차 분기 검증 누락
- 조치: `TC-S2-003` 추가, 최소 통과 조건에 반영

### 4회차: 파괴적 작업 안전성 재점검
- 점검 범위: `44/77/88/99` 위험 키 확인 절차
- 결과: CLI는 1단계 확인, UI는 2단계 권장이라는 차이 명시 필요
- 조치: 매핑 표에 `UI 2단계 확인(CLI 1단계)`로 명확화

### 5회차: Mode A/B 상호작용 계약 점검
- 점검 범위: Mode A `stdin` 기반 입력과 Mode B API 이벤트 계약의 연결성
- 결과: 프롬프트 왕복 계약이 본문에 약함
- 조치:
  - `인터랙티브 프롬프트 계약 (Mode B 확장안)` 섹션 추가
  - 에러코드(`INVALID_PROMPT_ID`, `PROMPT_ALREADY_RESOLVED`) 및 QA/E2E 검증 항목 추가

### 결론
- 현재 문서는 단순 메뉴 매핑 문서를 넘어, “키 + 후속입력 + 실패분기 + 운영안전”을 함께 다루는 실행 명세 수준으로 상향됨.

---

## 추가 고도화 점검 3회 결과 (v1.13)

### 점검 1: 프롬프트 값 타입 표준화 필요성
- 판단: 필요
- 권장: Prompt schema에 `value_type(enum/int/string/bool)`과 `validation_regex` 필드 추가

### 점검 2: 재현 가능한 자동 검증 스크립트 필요성
- 판단: 필요
- 권장: `tests/e2e_menu_flow.md` + PowerShell smoke 스크립트(`scripts/e2e_menu_smoke.ps1`) 추가

### 점검 3: 운영자 관점 실패 가시성
- 판단: 필요
- 권장: 실패 분기 선택 이력을 `run_audit.jsonl`에 구조화 저장(선택지, 시각, run_id)

최종 판정:
- 즉시 실행 가능한 수준은 확보됨.
- 다음 고도화 우선순위는 `Mode B 프롬프트 계약 고정`과 `E2E 스모크 자동화`.

---

## 2차 고도화 결과 (구현 준비, v1.14)

### 목표
- 문서만으로 개발팀이 즉시 구현에 착수할 수 있도록 산출물/책임/완료기준을 고정한다.

### 구현 준비 산출물 패키지 (필수)
| ID | 파일 경로 | 내용 | 담당 | 완료 기준 |
|---|---|---|---|---|
| `IMP-001` | `docs/implementation/prompt-map-v1.json` | key별 후속 입력 정의서 | BE | `0/1/2/3/4/6/44/77/88/99` 전부 정의 |
| `IMP-002` | `docs/implementation/api-contract-v1.yaml` | `/run`,`/stop`,`/status`,`/events` 계약 | BE | 오류코드/예시/필수필드 포함 |
| `IMP-003` | `docs/implementation/event-schema-v1.json` | WS 이벤트 타입 스키마 | BE | `prompt_request/resolved/timeout` 포함 |
| `IMP-004` | `docs/implementation/ui-flow-v1.md` | 키 클릭→모달→실행 플로우 | UI | 전 key의 화면 전이도 완성 |
| `IMP-005` | `docs/implementation/risk-operations-v1.md` | 위험키(`44/77/88/99`) 안전정책 | UI/OPS | UI 2단계 확인 절차 명시 |
| `IMP-006` | `docs/implementation/e2e-matrix-v1.md` | TC 실행 절차/판정 기준 | QA | TC별 입력/기대결과/증빙 경로 |
| `IMP-007` | `docs/implementation/release-gate-v1.md` | Go/No-Go 판단표 | OPS | 승인자 서명란 포함 |
| `IMP-008` | `scripts/e2e_menu_smoke.ps1` | 핵심 E2E 스모크 자동검증 | QA/BE | 실패 시 non-zero exit 코드 |

### Prompt Map 최소 스키마
```json
{
  "key": "2",
  "steps": [
    {
      "step_id": "stage2_target_limit",
      "type": "int",
      "required": true,
      "default": 5,
      "min": 1,
      "max": 99
    }
  ]
}
```

### key별 Prompt Map DoD
1. 각 key마다 `steps`가 빈 배열이더라도 명시되어야 한다.
2. 기본값이 있는 입력은 `default` 필드가 반드시 있어야 한다.
3. 선택형 입력은 `options`와 `default`를 함께 명시해야 한다.
4. 위험 작업 key(`44/77/88/99`)는 `requires_double_confirm=true`를 명시한다.
5. Stage 3 실패 정책은 `skip_allowed=false`로 명시한다.

### 구현 워크플로 고정 규칙
1. 브랜치: `feat/ui-runner-*`, `feat/backend-bridge-*`, `feat/e2e-*`
2. PR 단위: 최대 1개 기능 축(예: prompt map만, api contract만)
3. PR 템플릿 필수 항목:
   - 변경 목적
   - 영향 범위(key/endpoint/event)
   - 수동 테스트 절차
   - 롤백 방법
4. 병합 조건:
   - 체크리스트 B/C 해당 항목 확인
   - 최소 1명 리뷰 승인
   - CI green (`pytest`, `ruff`)
5. 위험 키(`44/77/88/99`) 관련 변경은 운영 담당 승인 필수

### 10일 착수 플랜 (구현 준비 중심)
| Day | 목표 | 산출물 |
|---|---|---|
| D1 | 계약 동결 | `IMP-001~003` 초안 |
| D2 | UI 흐름 동결 | `IMP-004`, `IMP-005` 초안 |
| D3 | 러너/입력 파이프 연결 | key별 입력 주입 프로토타입 |
| D4 | 오류코드/예외 처리 | `INVALID_*`, `SUB_KEY_*` 처리 완료 |
| D5 | Stage 0~2 E2E | `TC-P0`, `TC-S1`, `TC-S2` 통과 |
| D6 | Stage 3~4 E2E | `TC-S3`, `TC-S4` 통과 |
| D7 | One-Stop/위험키 E2E | `TC-OS`, `TC-RISK` 통과 |
| D8 | Mode B prompt 왕복 | `TC-PRM-001~002` 통과 |
| D9 | 릴리즈 게이트 리허설 | `IMP-007` 서명 준비 |
| D10 | Go/No-Go | 승인 회의 + 릴리즈 후보 확정 |

### 구현 준비 완료 선언 조건
1. `IMP-001~008` 산출물 생성 완료.
2. `TC-P0`, `TC-S1~S4`, `TC-OS`, `TC-RISK` 테스트 절차 문서화 완료.
3. 오류코드 카탈로그와 API 계약 문구 불일치 0건.
4. Go/No-Go 승인 표에 책임자 할당 완료.

### 구현 착수 차단 조건 (Blockers)
| 차단 항목 | 영향 | 우회/해소 |
|---|---|---|
| API 키 미확보 | 실환경 E2E 불가 | 모의 응답 모드로 UI 플로우 우선 검증 |
| Prompt map 미정의 | 키별 모달 구현 정지 | `IMP-001` 우선 완료 후 UI 착수 |
| 이벤트 스키마 미고정 | WS 파서 회귀 위험 | `IMP-003` 동결 전 렌더러 파서 병합 금지 |
| 위험 키 정책 미합의 | 운영사고 리스크 | `IMP-005` 승인 전 배포 금지 |

## 3차 고도화 실행판 (v1.15)

### 목표 (1-2-3 고정)
1. `IMP-001~003`를 즉시 작성 가능한 계약 템플릿으로 고정한다.
2. `scripts/e2e_menu_smoke.ps1` 명세를 확정해 반복 가능한 스모크 테스트를 만든다.
3. 위험 작업 키(`44/77/88/99`)를 `2인 승인 + 2단계 확인 + 감사로그` 정책으로 고정한다.

### 1) `IMP-001~003` 즉시 작성 템플릿

#### `IMP-001`: `docs/implementation/prompt-map-v1.json` 템플릿
```json
{
  "version": "v1",
  "keys": {
    "0": {
      "requires_sub_key": true,
      "allowed_sub_keys": ["0", "1", "2", "3", "4", "5", "6"],
      "steps": []
    },
    "1": {
      "requires_sub_key": false,
      "steps": [
        {
          "step_id": "stage1_mode",
          "type": "enum",
          "required": true,
          "options": ["proceed", "skip"],
          "default": "proceed"
        }
      ]
    },
    "2": {
      "requires_sub_key": false,
      "steps": [
        {
          "step_id": "stage2_target_arc_limit",
          "type": "int",
          "required": true,
          "default": 5,
          "min": 1,
          "max": 99
        },
        {
          "step_id": "stage2_fail_action",
          "type": "enum",
          "required": true,
          "options": ["skip", "stop", "retry", "manual"],
          "default": "retry"
        },
        {
          "step_id": "stage2_manual_input",
          "type": "string",
          "required_if": { "stage2_fail_action": "manual" },
          "default": ""
        }
      ]
    },
    "3": {
      "requires_sub_key": false,
      "steps": [
        {
          "step_id": "stage3_target_episode",
          "type": "int",
          "required": true,
          "default": 1,
          "min": 1,
          "max": 999
        },
        {
          "step_id": "stage3_skip_allowed",
          "type": "bool",
          "required": true,
          "default": false
        }
      ]
    },
    "4": {
      "requires_sub_key": false,
      "steps": [
        {
          "step_id": "stage4_target_episode",
          "type": "int",
          "required": true,
          "default": 1,
          "min": 1,
          "max": 999
        },
        {
          "step_id": "stage4_style",
          "type": "enum",
          "required": true,
          "options": ["style_a", "style_b"],
          "default": "style_a"
        },
        {
          "step_id": "stage4_fallback",
          "type": "enum",
          "required": true,
          "options": ["adopt_best", "skip"],
          "default": "adopt_best"
        }
      ]
    },
    "6": {
      "requires_sub_key": false,
      "steps": [
        {
          "step_id": "onestop_batch_count",
          "type": "int",
          "required": true,
          "default": 1,
          "min": 1,
          "max": 20
        },
        {
          "step_id": "onestop_continue",
          "type": "bool",
          "required": true,
          "default": true
        }
      ]
    },
    "44": {
      "requires_sub_key": false,
      "requires_double_confirm": true,
      "approval_policy": "dual_control",
      "steps": []
    },
    "77": {
      "requires_sub_key": false,
      "requires_double_confirm": true,
      "approval_policy": "dual_control",
      "steps": []
    },
    "88": {
      "requires_sub_key": false,
      "requires_double_confirm": true,
      "approval_policy": "dual_control",
      "steps": []
    },
    "99": {
      "requires_sub_key": false,
      "requires_double_confirm": true,
      "approval_policy": "dual_control",
      "steps": []
    }
  }
}
```

#### `IMP-002`: `docs/implementation/api-contract-v1.yaml` 템플릿
```yaml
openapi: 3.1.0
info:
  title: Geuldobi Runner API
  version: v1
paths:
  /run:
    post:
      summary: 메뉴 key 실행 요청
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RunRequest'
      responses:
        '202':
          description: accepted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RunAccepted'
        '400':
          description: validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorEnvelope'
        '403':
          description: risk approval required or expired
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorEnvelope'
        '409':
          description: run already active
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorEnvelope'
  /stop:
    post:
      summary: 실행 중지(멱등)
      responses:
        '200':
          description: stopped or already stopped
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OkEnvelope'
  /status:
    get:
      summary: 현재 상태 조회
      responses:
        '200':
          description: current status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StatusEnvelope'
components:
  schemas:
    RunRequest:
      type: object
      required: [key]
      properties:
        key:
          type: string
          enum: ["0", "1", "2", "3", "4", "5", "6", "44", "77", "88", "99"]
        sub_key:
          type: string
          nullable: true
        inputs:
          type: object
          additionalProperties: true
        approval_id:
          type: string
          nullable: true
    RunAccepted:
      type: object
      required: [ok, run_id, code, message]
      properties:
        ok: { type: boolean, const: true }
        run_id: { type: string }
        code: { type: string, const: OK }
        message: { type: string }
        data: { type: object, additionalProperties: true }
    OkEnvelope:
      type: object
      required: [ok, code, message]
      properties:
        ok: { type: boolean, const: true }
        code: { type: string }
        message: { type: string }
        data: { type: object, additionalProperties: true }
    StatusEnvelope:
      type: object
      required: [ok, code, data]
      properties:
        ok: { type: boolean, const: true }
        code: { type: string, const: OK }
        data:
          type: object
          required: [state]
          properties:
            state:
              type: string
              enum: [idle, running, waiting_input, stopping, error]
            run_id:
              type: string
              nullable: true
    ErrorEnvelope:
      type: object
      required: [ok, code, message]
      properties:
        ok: { type: boolean, const: false }
        run_id: { type: string, nullable: true }
        code:
          type: string
          enum:
            - INVALID_KEY
            - SUB_KEY_REQUIRED
            - SUB_KEY_NOT_ALLOWED
            - INVALID_SUB_KEY
            - RUN_ALREADY_ACTIVE
            - RISK_APPROVAL_REQUIRED
            - RISK_APPROVAL_EXPIRED
            - RISK_APPROVAL_DUAL_CONTROL_REQUIRED
            - INVALID_PROMPT_ID
            - PROMPT_ALREADY_RESOLVED
        message: { type: string }
        data: { type: object, nullable: true, additionalProperties: true }
```

#### `IMP-003`: `docs/implementation/event-schema-v1.json` 템플릿
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Geuldobi WS Event v1",
  "type": "object",
  "required": ["event_version", "seq", "run_id", "type", "ts", "payload"],
  "properties": {
    "event_version": { "type": "string", "const": "v1" },
    "seq": { "type": "integer", "minimum": 1 },
    "run_id": { "type": "string" },
    "type": {
      "type": "string",
      "enum": [
        "run_started",
        "progress",
        "prompt_request",
        "prompt_resolved",
        "prompt_timeout",
        "run_completed",
        "run_failed"
      ]
    },
    "ts": { "type": "string", "format": "date-time" },
    "payload": { "type": "object" }
  },
  "allOf": [
    {
      "if": { "properties": { "type": { "const": "prompt_request" } } },
      "then": {
        "properties": {
          "payload": {
            "type": "object",
            "required": ["prompt_id", "step_id", "input_type", "options", "default", "timeout_sec"],
            "properties": {
              "prompt_id": { "type": "string" },
              "step_id": { "type": "string" },
              "input_type": { "type": "string", "enum": ["enum", "int", "string", "bool"] },
              "options": { "type": "array", "items": { "type": "string" } },
              "default": {},
              "timeout_sec": { "type": "integer", "minimum": 1 }
            }
          }
        }
      }
    },
    {
      "if": { "properties": { "type": { "const": "prompt_resolved" } } },
      "then": {
        "properties": {
          "payload": {
            "type": "object",
            "required": ["prompt_id", "value", "source"],
            "properties": {
              "prompt_id": { "type": "string" },
              "value": {},
              "source": { "type": "string", "enum": ["user", "default"] }
            }
          }
        }
      }
    },
    {
      "if": { "properties": { "type": { "const": "prompt_timeout" } } },
      "then": {
        "properties": {
          "payload": {
            "type": "object",
            "required": ["prompt_id", "applied_default"],
            "properties": {
              "prompt_id": { "type": "string" },
              "applied_default": {}
            }
          }
        }
      }
    }
  ]
}
```

### 2) `scripts/e2e_menu_smoke.ps1` 명세 (작성 기준)

#### 파라미터
| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `BaseUrl` | string | `http://127.0.0.1:8000` | 로컬 API 주소 |
| `OutDir` | string | `artifacts/smoke` | 결과 JSON/로그 출력 경로 |
| `TimeoutSec` | int | `15` | 케이스별 HTTP 타임아웃 |
| `StopOnFail` | switch | `false` | 실패 즉시 중단 여부 |
| `DryRun` | switch | `false` | 요청 생성만 하고 전송은 생략 |

#### 최소 스모크 케이스
| ID | 요청 | 기대 |
|---|---|---|
| `SMK-MAIN-001` | `POST /run {"key":"2"}` | `202 + code=OK` |
| `SMK-P0-001` | `POST /run {"key":"0","sub_key":"1"}` | `202 + code=OK` |
| `SMK-P0-002` | `POST /run {"key":"0"}` | `400 + code=SUB_KEY_REQUIRED` |
| `SMK-P0-003` | `POST /run {"key":"2","sub_key":"1"}` | `400 + code=SUB_KEY_NOT_ALLOWED` |
| `SMK-RISK-001` | `POST /run {"key":"44"}`(approval_id 없음) | `403 + code=RISK_APPROVAL_REQUIRED` |
| `SMK-STOP-001` | `POST /stop` 2회 | 둘 다 성공(`ok=true`) |

#### 종료 코드 규칙
- `0`: 전 케이스 통과
- `1`: 테스트 실패(기대 코드 불일치)
- `2`: 네트워크/타임아웃 실패
- `3`: 결과 파일 기록 실패

#### 출력 파일
- `artifacts/smoke/smoke-summary.json`
- `artifacts/smoke/smoke-results.jsonl`
- `artifacts/smoke/smoke-failures.log` (실패 시만)

#### 스크립트 골격
```powershell
param(
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$OutDir = "artifacts/smoke",
  [int]$TimeoutSec = 15,
  [switch]$StopOnFail,
  [switch]$DryRun
)

$cases = @(
  @{ id="SMK-MAIN-001"; method="POST"; path="/run"; body=@{key="2"}; expectStatus=202; expectCode="OK" },
  @{ id="SMK-P0-002"; method="POST"; path="/run"; body=@{key="0"}; expectStatus=400; expectCode="SUB_KEY_REQUIRED" },
  @{ id="SMK-RISK-001"; method="POST"; path="/run"; body=@{key="44"}; expectStatus=403; expectCode="RISK_APPROVAL_REQUIRED" }
)

# 구현 시 규칙:
# 1) 각 케이스 결과를 JSONL로 누적 기록
# 2) 실패 시 expect/actual 모두 저장
# 3) 마지막에 summary 생성 후 exit code 반환
```

### 3) 위험키 승인 게이트 강화 (`44/77/88/99`)

#### 정책 고정
1. 위험키 실행 전 `approval_id`가 없는 요청은 모두 `403 RISK_APPROVAL_REQUIRED`를 반환한다.
2. 승인 유효시간(`expires_at`) 경과 시 `403 RISK_APPROVAL_EXPIRED`를 반환한다.
3. 승인자 2명이 동일인인 경우 `403 RISK_APPROVAL_DUAL_CONTROL_REQUIRED`를 반환한다.
4. UI는 반드시 2단계 확인 모달을 거친다.
5. CLI는 최소 1단계 확인 + 승인 ID 입력을 강제한다.

#### 승인 레코드 템플릿 (`risk-approval-log.jsonl`)
```json
{
  "approval_id": "APR-20260306-0001",
  "key": "44",
  "ticket_id": "OPS-1234",
  "requested_by": "requester_id",
  "approved_by_primary": "approver_a",
  "approved_by_secondary": "approver_b",
  "reason": "정리 작업 실행",
  "created_at": "2026-03-06T10:00:00+09:00",
  "expires_at": "2026-03-06T12:00:00+09:00",
  "status": "approved"
}
```

#### 승인 절차 (운영/감사 공통)
1. 요청자: 티켓 발행(`ticket_id`) + 실행 사유 입력
2. 1차 승인자: 영향 범위 확인 후 승인
3. 2차 승인자: 복구 가능성 확인 후 승인
4. 실행자: UI 2단계 확인 완료 후 `approval_id` 포함 실행
5. 시스템: 실행 전 승인 유효성 검증, 실행 후 감사 로그 저장
6. QA/운영: `approval_id` 기준으로 실행 로그와 티켓 연결 검증

#### DoD 추가
- `IMP-005` 문서에 승인자 역할 분리(요청자/승인자/실행자) 표가 포함되어야 한다.
- `IMP-006` E2E에 `승인 없음/만료/2인 미충족/정상승인` 4개 케이스가 포함되어야 한다.
- 릴리즈 게이트 증빙에 `risk-approval-log.jsonl` 샘플 3케이스(정상/만료/2인 미충족) 첨부되어야 한다.

## 4차 고도화 실행 반영 (v1.16)

### 반영 완료 항목
1. 계약 실파일 생성 완료
   - `docs/implementation/prompt-map-v1.json`
   - `docs/implementation/api-contract-v1.yaml`
   - `docs/implementation/event-schema-v1.json`
2. 스모크 자동화 실파일 생성 완료
   - `scripts/e2e_menu_smoke.ps1`
   - 케이스 `SMK-MAIN/P0/RISK/STOP` + 종료코드 `0/1/2/3` 구현
3. 위험키 승인 운영팩 생성 완료
   - `docs/implementation/risk-approval-request-template.md`
   - `docs/implementation/risk-approval-checklist.md`
   - `docs/implementation/samples/risk-approval-log.samples.jsonl`
4. 릴리즈 게이트 자동 No-Go 규칙 실파일 생성 완료
   - `docs/implementation/release-gate-v1.md`
   - 필수 증빙 파일 누락 시 `NO-GO` 규칙 명시

### v1.16 즉시 착수 체크
- [ ] `prompt-map-v1.json`을 런타임 로더에 연결
- [ ] `/run/{run_id}/input` API 라우트 구현
- [ ] WS 이벤트를 `event-schema-v1.json` 기준으로 검증
- [ ] `scripts/e2e_menu_smoke.ps1`를 CI nightly 잡에 연결
- [ ] `release-gate-v1.md` 기준으로 Go/No-Go 회의 템플릿 갱신

---

## 실행 체크리스트 (최종)

### A. 개발 착수 전
- [ ] 문서 버전 `v1.17` 공유 완료
- [ ] OI-001~007 확정안 팀 공지 완료
- [ ] 담당자(RACI) 확정 및 티켓 할당 완료
- [ ] PoC 범위 고정선(Scope Guard) 합의 완료
- [ ] 도입 순서 원칙(`POC -> 내부 재배포 -> 원격 패치`) 팀 합의 완료
- [ ] `IMP-001~008` 산출물 담당자 지정 완료
- [ ] `IMP-001~003` 계약 템플릿 동결일(D1) 및 변경 승인자 지정 완료
- [ ] PR 템플릿/브랜치 네이밍 규칙 공지 완료

### B. 개발 중
- [ ] `POST /run`, `POST /run/batch`, `POST /stop`, `GET /status`, `WS /events` 구현
- [ ] key/sub_key 화이트리스트 및 400 오류(`INVALID_KEY/SUB_KEY_REQUIRED/SUB_KEY_NOT_ALLOWED/INVALID_SUB_KEY`) 처리 구현
- [ ] running 중 중복 run 요청 409 거절 구현
- [ ] stop 멱등성 구현
- [ ] 이벤트 필수 필드(`event_version/seq/run_id`) 포함 구현
- [ ] key별 후속 입력 정의서(prompt map) 및 기본값 정책 반영
- [ ] `docs/implementation/prompt-map-v1.json` 작성 완료
- [ ] `docs/implementation/api-contract-v1.yaml` 작성 완료
- [ ] `docs/implementation/event-schema-v1.json` 작성 완료
- [ ] `IMP-001~003` 템플릿 필드명/오류코드 동결(임의 확장 금지 규칙 적용)
- [ ] `scripts/e2e_menu_smoke.ps1` 구현(파라미터/종료코드/출력파일 규칙 준수)
- [ ] loopback + 세션 토큰 인증 적용
- [ ] 로그 마스킹 적용(API 키/토큰)
- [ ] UI에서 verdict 3종 배지/카피 반영

### C. QA
- [ ] 메뉴 키 1:1 실행 테스트 통과
- [ ] `0 -> Stage 0 서브메뉴 -> sub_key(0~6)` 분기 테스트 통과
- [ ] `1 -> Stage 1 [진행/스킵]` 분기 테스트 통과
- [ ] `2 -> Stage 2 실패 분기[건너뛰기/중단/다시 하기/수동]` 테스트 통과
- [ ] `2 -> Stage 2 수동개입`의 2차 입력(`[Enter]/skip/quit`) 분기 테스트 통과
- [ ] `3 -> Stage 3 목표 화 입력` 범위/기본값 테스트 통과
- [ ] Stage 3 실패 시 후속 화 자동 진행 없이 즉시 중단되는지 확인
- [ ] `4 -> Stage 4 fallback[최선 채택/건너뛰기]` 분기 테스트 통과
- [ ] `6 -> One-Stop` 배치/연장 분기 테스트 통과
- [ ] `key=0`에서 `sub_key` 누락 시 `SUB_KEY_REQUIRED` 반환 확인
- [ ] `key!=0`에서 `sub_key` 전달 시 `SUB_KEY_NOT_ALLOWED` 반환 확인
- [ ] 잘못된 `sub_key` 입력 시 `INVALID_SUB_KEY` 반환 확인
- [ ] (Mode B) `prompt_request -> input -> prompt_resolved` 왕복 테스트 통과
- [ ] (Mode B) 프롬프트 타임아웃 시 default 적용 및 이벤트 기록 확인
- [ ] `44/77/88/99` 위험 키 확인 모달(2단계) 동작 확인
- [ ] 위험키 승인 케이스 4종(`없음/만료/2인 미충족/정상 승인`) 통과
- [ ] 중지/재실행 3회 연속 통과
- [ ] WS 끊김 후 3초 내 재연결 확인
- [ ] 업데이트 중 running 차단 확인
- [ ] 업데이트 체크섬 실패 시 롤백 확인
- [ ] 클린 PC 설치/실행/삭제 테스트 통과
- [ ] `scripts/e2e_menu_smoke.ps1` 결과(`smoke-summary.json`, `smoke-results.jsonl`) 첨부
- [ ] `pytest tests/ -q` 최신 green
- [ ] `ruff check` green

### D. 릴리즈
- [ ] stable/beta 채널 manifest 게시
- [ ] 릴리즈 노트 작성
- [ ] 코드 서명 적용(릴리즈 빌드)
- [ ] 롤백 패키지 준비
- [ ] 배포 후 헬스체크(앱 시작/실행/업데이트) 완료
- [ ] `docs/implementation/release-gate-v1.md` 승인 서명 완료
- [ ] `risk-approval-log.jsonl` 샘플(최소 1건) 릴리즈 증빙 첨부
- [ ] 원격 패치 착수 시, `POC 완료 증빙 + 내부 재배포 검증 로그` 승인 첨부

### E. 운영
- [ ] 로그 보존 14일 정책 적용
- [ ] 장애 보고 템플릿(버전/OS/재현절차/로그 200줄) 배포
- [ ] Sev-1/2 대응 연락망 확인
- [ ] 다음 배포 전 beta 검증 완료

---

## 무료 오피스 타일셋 대체 전략 (pixel-agents 중심)

### 배경 (감리 확인)
- `pixel-agents`는 MIT 라이선스이지만, README에 오피스 가구 풀타일셋은 라이선스 이슈로 repo 미포함이라고 명시.
- 즉, 코드/구조는 재사용 가능하나 오피스 타일셋은 별도 조달이 필요.
- 다행히 확장은 타일셋 없이도 동작하며, 대체 타일셋 import 파이프라인을 제공.

### 무료 후보 (우선순위)
| 우선 | 자산 | 라이선스 | 호환성 메모 |
|---|---|---|---|
| 1 | OpenGameArt: Office 8x8 Tileset | CC0 | 8x8 → 16x16 Nearest 업스케일 권장 |
| 2 | OpenGameArt: Interior Tileset 16x16 | CC-BY-SA 3.0 | 16x16 직접 사용 가능(출처표기/동일조건 공유 검토) |
| 3 | Kenney Generic Items | CC0 | 오피스 전용은 아니나 가구/소품 대체 가능 |

후보 링크:
- https://opengameart.org/content/office-8x8-tileset
- https://opengameart.org/content/interior-tileset-16x16
- https://www.kenney.nl/assets/generic-items

### 호환 기준
- 단일 타일시트 PNG
- 탑다운 시점
- 타일 해상도 16x16 권장
- 8x8 사용 시 `nearest-neighbor` 2배 업스케일 후 사용

### import 절차 (요약)
1. 무료 타일셋 확보(PNG)
2. 프로젝트 `assets/office_tileset_16x16.png`로 배치
3. `npm run import-tileset` 실행
4. asset editor/review 단계에서 메타데이터 정리
5. 결과 catalog 반영 후 UI에서 시각 확인

### 라이선스 운영 규칙
- 에셋별 라이선스 URL과 버전을 `THIRD_PARTY_ASSETS.md`에 기록
- CC0 외 라이선스는 별도 조항(저작자표시/재배포/동일조건 공유) 확인
- 원본 에셋 재판매/재배포 금지 조항 여부 확인 후 배포

### PoC 권장안
- 1차 PoC는 무료 CC0 타일셋(Office 8x8, Kenney) 중심으로 진행
- 상용 배포 직전 최종 아트셋(무료/유료) 라이선스 재감리 1회 수행

---

## 고도화 루프 1 (실행 명세 확장)

### API 응답 표준
모든 HTTP 응답은 아래 envelope 사용:

```json
{
  "ok": true,
  "run_id": "run-20260306-1",
  "code": "OK",
  "message": "accepted",
  "data": {}
}
```

실패 예시:
```json
{
  "ok": false,
  "run_id": null,
  "code": "RUN_ALREADY_ACTIVE",
  "message": "another run is active",
  "data": null
}
```

### 엔드포인트별 계약
| API | 요청 | 성공 | 실패 |
|---|---|---|---|
| `POST /run` | `{ key, sub_key? }` | `202 Accepted` + `run_id` | `400 INVALID_KEY/SUB_KEY_REQUIRED/SUB_KEY_NOT_ALLOWED/INVALID_SUB_KEY`, `409 RUN_ALREADY_ACTIVE` |
| `POST /run/batch` | `{ count }` | `202 Accepted` + `run_id` | `400 INVALID_BATCH_COUNT`, `409 RUN_ALREADY_ACTIVE` |
| `POST /stop` | 없음 | `200 OK` (멱등) | `500` 내부오류 |
| `GET /status` | 없음 | `200 OK` + 현재 상태 | `500` 내부오류 |

참고:
- `key=1,2,3,4,6,44,77,88,99`의 세부 입력은 Mode A에서 `stdin` 시퀀스로 처리(본 문서의 후속 입력 매핑 표 참조).

### 상태머신 (Run Lifecycle)
`idle -> starting -> running -> stopping -> idle`  
예외 경로: `starting/running/stopping -> error -> idle`

상태 전이 규칙:
- `run` 요청은 `idle`에서만 수락
- `stop` 요청은 모든 상태에서 허용(멱등)
- `error` 진입 시 로그 플러시 후 `idle` 복귀 시도

### 타임아웃 예산
| 항목 | 제한 |
|---|---|
| `/run` 요청 승인 | 2초 이내 |
| `/stop` 응답 | 2초 이내 |
| WS 재연결 시도 간격 | 1초, 최대 3회 후 백오프 |
| 업데이트 다운로드 확인 | 60초 내 진행 표시 필수 |

### idempotency 규칙
- `POST /run`은 `X-Idempotency-Key` 지원 권장
- 같은 키의 중복 요청은 동일 `run_id` 반환
- `POST /stop`은 키 없이 멱등 처리

---

## 고도화 루프 2 (자산/라이선스 거버넌스)

### `THIRD_PARTY_ASSETS.md` 표준 템플릿
```md
# Third Party Assets

## Asset
- Name:
- Source URL:
- Author:
- License:
- Allowed Use:
- Attribution Required: (Yes/No)
- Redistribute Allowed: (Yes/No)
- Share-Alike Required: (Yes/No)
- Notes:
```

### 라이선스 등급 정책
| 등급 | 조건 | PoC 허용 |
|---|---|---|
| Green | CC0/MIT/명확 허용 | 즉시 사용 가능 |
| Yellow | CC-BY/CC-BY-SA(조건부) | 출처/동일조건 검토 후 사용 |
| Red | 재배포 금지/상업 제한/모호 | PoC 제외 |

### 자산 반입 게이트
1. 출처 URL 확인
2. 라이선스 텍스트 캡처/기록
3. `THIRD_PARTY_ASSETS.md` 등록
4. 샘플 화면 1장에 출처/저작자 표시 확인
5. 배포 전 최종 재검증

### pixel-agents 연동 가이드 (자산 관점)
- 코드/구조 참조: 가능(MIT)
- 기본 캐릭터/벽 자산 사용: 가능 쪽이나, 상용 전 재확인 권장
- Donarg 타일셋: 별도 구매 및 조건 준수 필요
- 대체 무료셋: CC0 우선 채택

---

## 고도화 루프 3 (실전 실행 패킷)

### 킥오프 D1 체크리스트 (당일 착수)
| 시간 | 작업 | 담당 |
|---|---|---|
| 10:00 | 문서 확정안 브리핑(v1.17) | PO |
| 11:00 | 리포 구조 생성(`desktop/`, `backend/`) | UI/BE |
| 13:00 | Runner 시작/중지 프로토타입 | BE |
| 15:00 | 로그 패널 스트리밍 연결 | UI |
| 17:00 | Stage 3 호출 데모 | UI/BE |

### 주간 운영 cadence
| 요일 | 이벤트 | 산출물 |
|---|---|---|
| 월 | 계획/리스크 정렬 | 주간 스프린트 보드 |
| 화-수 | 기능 구현 | PR/데모 영상 |
| 목 | 통합 테스트 | QA 리포트 |
| 금 | 릴리즈 후보 평가 | Go/No-Go 결정 |

### KPI 대시보드 (PoC)
| KPI | 목표 |
|---|---|
| 비개발자 온보딩 시간 | 10분 이내 |
| Stage 실행 성공률 | 95% 이상 |
| 업데이트 실패율 | 5% 이하 |
| Sev-1 발생 건수 | 0 |

### 릴리즈 서명 절차
1. 빌드 산출물 해시 생성
2. 코드 서명 적용
3. 체크섬 파일 공개
4. manifest 버전/해시 동기화
5. beta 배포 후 24시간 모니터링
6. stable 승격

### 운영 인수인계 패킷
- 설치 가이드 1장
- 장애 대응 카드(Sev-1~4)
- 업데이트 롤백 가이드 1장
- 자산 라이선스 레지스터(`THIRD_PARTY_ASSETS.md`)

---

## 바로 실행 런북 (v1.17)

### Track A: 기존 CLI 즉시 실행 (오늘 바로)

목적:
- 현재 코드베이스를 즉시 실행해 Stage 메뉴 동작(특히 `0 -> 하위 메뉴`) 확인

PowerShell 명령(복붙용):
```powershell
Set-Location C:\Users\wjjo\Desktop\글도비
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env -Force
notepad .env
python main_a.py
```

PowerShell 실행 정책으로 venv 활성화가 막히면:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

또는 활성화 없이 직접 실행:
```powershell
.\.venv\Scripts\python.exe main_a.py
```

실행 중 확인 포인트:
1. 메인 메뉴에서 `0` 입력 시 Stage 0 서브메뉴가 열려야 한다.
2. Stage 0 서브메뉴에서 `1` 입력 시 기존 방식(Bible/Treatment 선택) 경로로 진입해야 한다.
3. Stage 0 서브메뉴에서 `0` 입력 시 취소되고 상위 메뉴로 돌아와야 한다.
4. `1` 입력 시 Stage 1 진행/스킵 선택 프롬프트가 표시되어야 한다.
5. `2` 입력 시 목표 Arc 범위 입력 프롬프트가 표시되어야 한다.
6. `4` 입력 시 목표 화수 입력(및 조건부 스타일 선택) 프롬프트가 표시되어야 한다.
7. `44/77/88/99` 입력 시 파괴적 작업 확인 프롬프트가 표시되어야 한다.

완료 기준:
- `0 -> sub_key(0~6)` 분기 동작이 콘솔에서 재현됨
- `1/2/4/6/44/77/88/99` 후속 프롬프트 노출이 콘솔에서 확인됨
- API 키/의존성 문제 없이 `main_a.py` 정상 기동됨

### Track B: UI PoC 착수 (D1~D2)

목적:
- 기존 백엔드 변경 최소로 비개발자용 버튼 실행 껍데기 착수

D1 산출물:
1. 런너 프로세스 시작/중지
2. 로그 스트리밍 패널
3. 메인 메뉴 키 버튼(0/1/2/3/4/5/6/44/77/88/99)
4. Stage 0 하위 옵션 모달(0~6)

D2 산출물:
1. `key=0 + sub_key` 요청 계약 반영
2. key/sub_key 유효성 검사 + 오류 토스트
3. Stop 멱등 처리
4. 실행 중 중복 run 409 처리
5. key별 후속 입력 정의서(prompt map) 작성
6. `IMP-001~003` 초안 작성(계약/스키마 동결 준비)

인코딩/경로 규칙:
- 문서/설정 파일(`.md/.json/.yaml`)은 UTF-8로 저장
- API 요청/응답 JSON은 UTF-8 고정
- 경로 표시는 한글 가능, API 필드명과 에러코드는 ASCII 고정

---

## API 실전 예시 (PowerShell)

전제:
- FastAPI 브리지 기본 URL은 `http://127.0.0.1:8787`로 가정
- 팀 표준 포트를 다르게 쓰면 `BASE` 값만 교체

```powershell
$BASE = "http://127.0.0.1:8787"

# Stage 0 진입 + 하위 선택(역설계)
Invoke-RestMethod -Method Post -Uri "$BASE/run" -ContentType "application/json" -Body '{"key":"0","sub_key":"3"}'

# Stage 2 실행
Invoke-RestMethod -Method Post -Uri "$BASE/run" -ContentType "application/json" -Body '{"key":"2"}'

# 잘못된 호출 예시 (sub_key 누락) -> 400 SUB_KEY_REQUIRED 기대
Invoke-RestMethod -Method Post -Uri "$BASE/run" -ContentType "application/json" -Body '{"key":"0"}'

# 잘못된 호출 예시 (key!=0인데 sub_key 전달) -> 400 SUB_KEY_NOT_ALLOWED 기대
Invoke-RestMethod -Method Post -Uri "$BASE/run" -ContentType "application/json" -Body '{"key":"2","sub_key":"1"}'

# 상태 조회
Invoke-RestMethod -Method Get -Uri "$BASE/status"

# 중지 (멱등)
Invoke-RestMethod -Method Post -Uri "$BASE/stop"
```

성공 응답 예시:
```json
{
  "ok": true,
  "run_id": "run-20260306-1001",
  "code": "OK",
  "message": "accepted",
  "data": {
    "key": "0",
    "sub_key": "3"
  }
}
```

실패 응답 예시:
```json
{
  "ok": false,
  "run_id": null,
  "code": "SUB_KEY_REQUIRED",
  "message": "sub_key is required when key is 0",
  "data": null
}
```

---

## E2E 테스트 케이스 (실행형)

| TC ID | 시나리오 | 입력 | 기대 결과 |
|---|---|---|---|
| `TC-MAIN-001` | 메인 키 실행 | `{"key":"2"}` | `202 + run_id`, Stage 2 시작 |
| `TC-P0-001` | Stage 0 기본 경로 | `{"key":"0","sub_key":"1"}` | `202 + run_id`, 기존 방식 진입 |
| `TC-P0-002` | Stage 0 취소 경로 | `{"key":"0","sub_key":"0"}` | `202` 후 상위 메뉴 복귀 이벤트 |
| `TC-P0-003` | Stage 0 sub_key 누락 | `{"key":"0"}` | `400 SUB_KEY_REQUIRED` |
| `TC-P0-004` | Stage 0 sub_key 오입력 | `{"key":"0","sub_key":"9"}` | `400 INVALID_SUB_KEY` |
| `TC-P0-005` | 비Stage0에서 sub_key 전달 | `{"key":"2","sub_key":"1"}` | `400 SUB_KEY_NOT_ALLOWED` |
| `TC-P0-006` | Stage0 확장 비활성 상태 요청 | `{"key":"0","sub_key":"2"}` + `STAGE0_AVAILABLE=false` | `400 INVALID_SUB_KEY` |
| `TC-S1-001` | Stage 1 진행/스킵 분기 | `key=1` 후 `[1]`, `[2]` 각각 입력 | 두 경로 모두 정상 종료 |
| `TC-S2-001` | Stage 2 목표 범위 입력 | `key=2`, 목표 Arc 상한 입력 | 지정 범위까지 생성 |
| `TC-S2-002` | Stage 2 실패 분기 | 실패 상황에서 `1/2/3/4` 선택 | 선택지별 기대 흐름 일치 |
| `TC-S2-003` | Stage 2 수동개입 2차 분기 | `4` 선택 후 `[Enter]/skip/quit` | 재시도/건너뛰기/중단 정상 |
| `TC-S3-001` | Stage 3 목표 화 입력 | `key=3`, 목표 화 입력 | 범위 검증 + 생성 성공 |
| `TC-S3-002` | Stage 3 실패 정책 | 의도적 실패 유도 | 후속 화 건너뛰기 없이 즉시 중단 |
| `TC-S4-001` | Stage 4 스타일 선택 | `key=4`, 스타일 `1/2` 입력 | 스타일 가이드 반영 |
| `TC-S4-002` | Stage 4 fallback 분기 | 면담 소진 후 `1/2` 선택 | 최선 채택 또는 스킵 정상 |
| `TC-OS-001` | One-Stop 배치 분기 | `key=6`, 배치/계속/추가 입력 | 연속 배치 처리 정상 |
| `TC-RISK-001` | 위험 키 확인 | `44/77/88/99` + 확인 입력 | 확인 후에만 실행 |
| `TC-PRM-001` | (Mode B) 프롬프트 왕복 | `prompt_request` 수신 후 `POST /run/{run_id}/input` | `prompt_resolved` 이벤트 수신 |
| `TC-PRM-002` | (Mode B) 프롬프트 타임아웃 | 응답 미입력으로 timeout 유도 | default 적용 + `prompt_timeout` 기록 |
| `TC-LOCK-001` | 중복 run 방지 | 실행 중 `POST /run` 2회 | 두 번째 요청 `409 RUN_ALREADY_ACTIVE` |
| `TC-STOP-001` | stop 멱등성 | `POST /stop` 2회 | 두 번 모두 성공 응답 |
| `TC-WS-001` | WS 자동 복구 | 연결 강제 종료 | 3초 내 재연결 |
| `TC-UPD-001` | 실행 중 업데이트 차단 | running 상태에서 업데이트 | `UPDATE_BLOCKED_RUNNING` |

최소 통과 조건:
- `TC-P0-001~006` 전부 통과
- `TC-S1-001`, `TC-S2-001~003`, `TC-S3-001~002`, `TC-S4-001~002`, `TC-OS-001`, `TC-RISK-001` 통과
- (Mode B 활성 시) `TC-PRM-001~002` 통과
- `TC-LOCK-001`, `TC-STOP-001` 통과
- 클린 PC 1회 설치/실행/삭제 통과

---

## 릴리즈 산출물 표준 (바로 배포 가능 기준)

필수 산출물:
1. 설치 파일: `geuldobi-setup-x64.exe`
2. 업데이트 manifest: `manifest.json`
3. 체크섬 파일: `checksums.txt`
4. 릴리즈 노트: `RELEASE_NOTES.md`
5. QA 리포트: `qa-report-v1.16.md`
6. 라이선스 레지스터: `THIRD_PARTY_ASSETS.md`

릴리즈 게이트(전부 만족 시 배포):
1. 기능 게이트: 메뉴 키 및 Stage 0 하위키 테스트 통과
2. 안정성 게이트: 중복 run/stop 멱등/WS 재연결 통과
3. 보안 게이트: 토큰/키 마스킹 + 체크섬 검증 통과
4. 운영 게이트: 롤백 절차 리허설 1회 통과

Go/No-Go 승인 증빙:
| 항목 | 증빙 파일 | 승인자 |
|---|---|---|
| 기능/E2E | `qa-report-v1.16.md` | QA 리드 |
| 안정성/관측 | `run-stability-report.md` | 백엔드 리드 |
| 보안/서명 | `security-signoff.md` | 운영/보안 담당 |
| 배포/롤백 | `release-runbook-check.md` | 릴리즈 매니저 |

---

## 5분 롤백 절차 (운영용)

1. 현재 실행 중 프로세스 `stop` 호출
2. `manifest.json`을 직전 안정 버전으로 교체
3. 이전 설치 패키지 재적용
4. 앱 재기동 후 `GET /status` 헬스체크
5. 문제 재현 여부 확인 후 장애 보고서 발행

운영 메모:
- 사용자 데이터(`projects/`)는 롤백 대상에서 제외
- 롤백 성공/실패 로그는 별도 파일로 보관

---

## 참고 링크
- OPUS+Codex 10터미널 실행 오더: `docs/2026-03-06/OPUS_Codex_10터미널_협업_실행오더_v2.md`
- Pixel Agents (레퍼런스): https://github.com/pablodelucca/pixel-agents
- VS Marketplace: https://marketplace.visualstudio.com/items?itemName=pablodelucca.pixel-agents
- Pixel Agents LICENSE (MIT): https://github.com/pablodelucca/pixel-agents/blob/main/LICENSE
- Pixel Agents README: https://github.com/pablodelucca/pixel-agents
- Metro City 캐릭터(README 명시, CC0): https://jik-a-4.itch.io/metrocity-free-topdown-character-pack
- Donarg Office Tileset(유료): https://donarg.itch.io/officetileset
- Spline Community: https://community.spline.design/
- LottieFiles: https://lottiefiles.com/free-animations/kawaii
