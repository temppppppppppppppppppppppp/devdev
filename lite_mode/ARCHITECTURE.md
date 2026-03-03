# 글도비라이트 — 시스템 로직 문서

> V63.4 | Selenium Bridge ($0) | 최종 수정: 2026-02-12

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────┐
│                   main_lite.py                       │
│                  (진입점 + 메뉴)                       │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│               BridgeRunner (runner.py)                │
│          파이프라인 오케스트레이션 + 품질 관리              │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Stage 2  │→ │ Stage 3  │→ │ Stage 4  │            │
│  │ 분배표   │  │Blueprint │  │  원고    │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                       │
│  ┌──────────────────────────────────────────┐        │
│  │ Director (AI 품질 검증, 10회 루프)         │        │
│  │ Cross-checker (교차 검증, 2회 루프)        │        │
│  └──────────────────────────────────────────┘        │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│            GeminiDriver (gemini_driver.py)            │
│          Selenium 웹 자동화 + UI 자동 탐지              │
│                                                       │
│  ┌──────────────┐  ┌──────────────────────┐          │
│  │ UIDiscovery  │  │ Upload Interceptor   │          │
│  │ (API 기반    │  │ (HTMLInputElement     │          │
│  │  셀렉터 탐지) │  │  .click() hijack)    │          │
│  └──────────────┘  └──────────────────────┘          │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│     Chrome (--remote-debugging-port=9222)             │
│     → gemini.google.com/app                          │
└─────────────────────────────────────────────────────┘
```

---

## 2. 생성 파이프라인

### 2.1 Stage 2: 분배표 생성

```
treatment/block_001.txt  ──→  stage2/arc_001.txt (5화 분배표)
treatment/block_002.txt  ──→  stage2/arc_002.txt
...
treatment/block_050.txt  ──→  stage2/arc_050.txt
```

- **입력**: 줄거리 블록 (block_XXX.txt) + bible.txt(세계관)
- **출력**: 화별 분배표 — 각 블록을 5화(설정 가능)로 분배
- **누락 검사**: 파일 존재 여부로 판단, 없는 것만 생성

### 2.2 Stage 3: Blueprint 생성

```
stage2/arc_020.txt + treatment/block_020.txt
    + ep_0097_context.txt (누적 컨텍스트)
    ──→  stage3/ep_0097.txt (씬 설계)
```

- **입력**: 분배표 + 원본 블록 + 누적 컨텍스트
- **출력**: 에피소드별 Blueprint (씬, 대사, 감정 설계)
- **컨텍스트**: 이전 에피소드들의 Blueprint를 누적하여 일관성 유지
- **품질 검증**: Director + Cross-checker (아래 참조)

### 2.3 Stage 4: 원고 집필

```
stage3/ep_0097.txt (Blueprint)
    + ep_0097_context.txt
    ──→  stage4/manuscripts/ep_0097.txt (완성 원고)
```

- **입력**: Blueprint + 누적 컨텍스트
- **출력**: 최종 원고 (2000자 내외)

---

## 3. 품질 관리 시스템

### 3.1 Director 루프 (최대 10회)

```
생성 결과물
    │
    ▼
Director 평가 (사고 모드)
    │
    ├── 90점 이상 → PASS
    │
    └── 90점 미만 → REVISE
        │
        ├── 피드백 + 수정 요청
        │       │
        │       ▼
        │   수정본 생성 → 다시 평가 (최대 10회)
        │
        └── 0점 연속 3회 → 세션 리셋 + 재생성
```

**평가 항목:**
- 모순 검사 (이전 결과물/세계관 대조)
- 이름/고유명사 정확성
- 연속성 (직전 화와의 자연스러운 연결)
- 누락 요소
- 시간선 정합성
- 블록/분배표 일치
- 사망 NPC 위반 (사망 처리된 캐릭터 등장 시 0점)

### 3.2 Cross-checker (교차 검증, 최대 2회)

```
Director PASS 후
    │
    ▼
Cross-checker 평가
    │
    ├── 씬 중복
    ├── 공간 모순
    ├── 인물 상태 불일치
    ├── 아이템 연속성
    └── 시간선 오류
    │
    ├── PASS → 최종 저장
    └── REVISE → 수정 후 재검증
```

### 3.3 가비지 필터링

응답이 돌아올 때마다 자동 필터링:
1. **세정 (Sanitize)**: UI 잔재, 사고과정 헤더 제거
2. **가비지 판정**: 무관한 내용, 반복, 포맷 오류
3. **장르 오염 감지**: 설정과 다른 장르 요소 검출
4. **최소 길이 검사**: 너무 짧은 응답 거부

---

## 4. GeminiDriver — Selenium 자동화

### 4.1 초기화 플로우

```
Chrome 디버깅 포트 연결 (9222)
    │
    ▼
gemini.google.com/app 이동
    │
    ▼
maximize_window()  ← 항상 최대화 (UI 렌더링 보장)
    │
    ▼
Upload Interceptor 설치
    (HTMLInputElement.click() hijack
     + Page Visibility API 오버라이드)
    │
    ▼
UIDiscovery 캘리브레이션
    (DOM 덤프 → Gemini Flash API → 셀렉터 캐싱)
    │
    ▼
모델 선택 (Pro)
    │
    ▼
hide_window()  ← 초기화 완료 후 숨김
    (창을 화면 밖 -3000,0 으로 이동)
```

### 4.2 파일 업로드 플로우

```
upload_file(path)
    │
    ▼
Upload Interceptor 재설치
    │
    ▼
업로드 메뉴 클릭 (최대 5회)
    ├── UIDiscovery 셀렉터 우선 시도
    └── 하드코딩 폴백 (aria-label 기반)
    │
    ├── 실패 시 3회째: new_chat() 페이지 리셋
    └── 최종 실패: return False → 상위 재시도 루프로
    │
    ▼
약관 동의 모달 처리 (첫 업로드 시)
    │
    ▼
input[type=file] 탐색 (최대 3회)
    ├── DOM 직접 탐색
    ├── interceptor 캡처 확인
    └── 모든 input 순회
    │
    ├── 실패 시: interceptor 재설치 or 페이지 리셋(reset_session)
    └── 최종 실패: return False
    │
    ▼
send_keys()로 파일 경로 주입
    │
    ▼
업로드 완료 대기 (JS polling, 최대 15초)
```

### 4.3 세션 관리

```
reset_session()
    │
    ▼
show_window()  ← 삭제 시 창이 보여야 ⋮ 버튼 렌더링
    │
    ▼
_delete_current_chat()
    ├── 사이드바 채팅 호버 → ⋮ 버튼 → 삭제
    └── 실패해도 진행
    │
    ▼
new_chat()
    ├── gemini.google.com/app 이동
    ├── Upload Interceptor 재설치
    └── 모델 재선택
    │
    ▼
hide_window()  ← 다시 숨기기
```

---

## 5. UIDiscovery — 자동 셀렉터 탐지

### 5.1 목적

Google이 Gemini 웹 UI를 업데이트해도 자동 적응.
셀렉터를 하드코딩하지 않고, **목적 기반 탐색**으로 요소를 찾음.

### 5.2 캘리브레이션 플로우

```
calibrate()
    │
    ├── 캐시 유효 (72시간 이내)?
    │   ├── Yes → 핵심 셀렉터 DOM 검증 → 유효하면 스킵
    │   └── No ↓
    │
    ▼
_discover()
    │
    ▼
[Step 1] DOM 덤프 (JS)
    250개 인터랙티브 요소 추출
    (tag, class, role, aria-label, text, icon, visibility, 부모 3단계)
    │
    ▼
[Step 2] Gemini Flash API 분석
    DOM + 요소 설명 → CSS 셀렉터 JSON 반환
    (비용: ~$0.001/회)
    │
    ▼
[Step 3] 셀렉터 검증
    각 셀렉터를 실제 DOM에서 querySelector()로 확인
    실패 시 → 폴백 셀렉터 순차 시도
    │
    ▼
[Step 4] upload_menu_btn 클릭 검증 ★
    실제로 클릭 → 드롭다운 메뉴 열리는지 확인
    '파일 업로드' 텍스트 있는 메뉴 항목 존재 확인
    실패 시 → 입력창 주변 모든 버튼 브루트포스 탐색
    │
    ▼
_ui_cache.json에 캐싱 (72시간 유효)
```

### 5.3 탐지 대상 요소

| 요소명 | 설명 | 용도 |
|--------|------|------|
| `upload_menu_btn` | 입력창 옆 '+' / 첨부 아이콘 버튼 | 파일 업로드 메뉴 열기 |
| `upload_file_option` | 메뉴 안 '파일 업로드' 항목 | 파일 선택 트리거 |
| `send_btn` | 전송 버튼 | 메시지 전송 |
| `input_box` | 텍스트 입력 영역 | 프롬프트 입력 |
| `model_picker` | 모델 선택 드롭다운 | Pro/Flash/Think 전환 |
| `stop_btn` | 중지 버튼 | 응답 생성 중지 |
| `more_options_btn` | 사이드바 ⋮ 버튼 | 채팅 삭제 |
| `delete_option` | '삭제' 메뉴 항목 | 채팅 삭제 실행 |
| `response_container` | AI 응답 컨테이너 | 응답 텍스트 추출 |

---

## 6. 에러 복구 체계

### 6.1 재시도 계층

```
Layer 1: upload_file 내부
    └── 업로드 메뉴 5회 + input 탐색 3회
        (3회째: 페이지 리셋)

Layer 2: _send_and_save 루프
    └── 최대 5회 (TIMEOUT/EMPTY/가비지)
        매 실패 시: reset_session() + 5초 대기

Layer 3: 스테이지 루프
    └── 5회 모두 실패 시: 해당 화 SKIP → 다음 화 진행
```

### 6.2 에러별 처리

| 에러 | 처리 |
|------|------|
| 파일 업로드 실패 | return False → Layer 2 재시도 |
| 응답 타임아웃 | reset_session → 재시도 |
| 가비지 응답 | reset_session → 재시도 |
| 장르 오염 | reset_session → 재시도 |
| 응답 짧음 | reset_session → 재시도 |
| Pro 제한 감지 | **STOP** (인간 판단 대기) |
| 모델 피커 읽기 불가 | 새로고침 → 재확인 → 최종 STOP |
| Director 0점 3연속 | 세션 리셋 → 재생성 |

---

## 7. 프로젝트 파일 구조

```
test_mode/
├── main_lite.py              진입점
├── .env                      GOOGLE_API_KEY (UIDiscovery용)
├── _ui_cache.json            UI 셀렉터 캐시 (자동 생성)
│
├── bridge/
│   ├── gemini_driver.py      Selenium 자동화 드라이버
│   ├── ui_discovery.py       UI 자동 탐지 시스템
│   ├── runner.py             파이프라인 오케스트레이터
│   ├── prompt_builder.py     프롬프트 템플릿
│   └── state_ledger.py       세계 상태 추적 (NPC 사망 등)
│
└── projects/{name}/
    ├── bible.txt             세계관 설정
    ├── style_guide.txt       문체 가이드
    ├── macro_outline.txt     거시 구조
    ├── _config.json          설정 (ep_per_arc, model 등)
    ├── _state.json           진행 상태
    │
    ├── treatment/            줄거리 블록 입력
    │   ├── block_001.txt
    │   └── ...
    │
    ├── stage2/               분배표 출력
    │   ├── arc_001.txt
    │   └── ...
    │
    ├── stage3/               Blueprint 출력
    │   ├── ep_0001.txt
    │   ├── ep_0001_context.txt
    │   └── ...
    │
    └── stage4/               원고 출력
        └── manuscripts/
            ├── ep_0001.txt
            └── ...
```

---

## 8. 실행 방법

### 사전 조건

```powershell
# 1. Chrome 디버깅 모드 실행
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug"

# 2. Gemini에 로그인 (수동, 1회만)

# 3. 의존성 설치
pip install selenium webdriver-manager beautifulsoup4
```

### 실행

```powershell
cd C:\Users\User\Desktop\글도비\test_mode
python main_lite.py
```

### 환경 변수 (.env)

```
GOOGLE_API_KEY=AIzaSy...     # UIDiscovery용 (선택, 없으면 하드코딩 폴백)
SLACK_WEBHOOK_URL=https://...  # 알림 (선택)
```

---

## 9. 알려진 제한사항

1. **Gemini UI 의존**: Google이 DOM 구조를 크게 변경하면 UIDiscovery도 실패 가능
2. **동시 접속**: 같은 계정으로 다른 사람이 Pro 사용 시 응답 딜레이/실패
3. **컨텍스트 크기**: ep_XXX_context.txt가 80~95KB → Gemini 입력 한계 근접
4. **세션 누적**: _delete_current_chat 실패 시 사이드바에 채팅 쌓임
5. **단일 스레드**: Chrome 1개에 순차 처리, 병렬 불가
