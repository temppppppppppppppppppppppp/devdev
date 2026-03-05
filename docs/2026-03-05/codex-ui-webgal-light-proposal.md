# 글도비 라이트 GUI 제안 (WebGal 스타일)

## 한줄 결론
- 방향 좋습니다. 비개발자 접근성은 확실히 좋아집니다.
- 다만 `WebGal`은 **연출 레이어**로 쓰고, 메뉴/입력/로그는 일반 웹 UI로 구성하는 것이 안정적입니다.
- 핵심은 백엔드(`main_a.py`)를 거의 안 건드리고, 콘솔 메뉴를 GUI에 1:1 매핑하는 방식입니다.

## 목표 범위 (가볍게)
- 기존 콘솔 메뉴를 그대로 버튼화
- Stage 대기 시간에 빠칭코 애니메이션 재생
- 결과 이펙트 3종
  - `PASS`: 좋은 이펙트
  - `REJECT`: 나쁜 이펙트
  - `PASS_WITH_FIX`: `"한 번 더!"` 이펙트

## 콘솔 메뉴 → GUI 매핑
기준: `main_a.py`의 메인 메뉴 키(`0/1/2/3/4/5/6/44/77/88/99`)를 그대로 유지.

| 콘솔 키 | 현재 기능 | GUI 버튼 라벨 |
|---|---|---|
| `0` | Stage 0: Bible/역설계/스타일 추출 | `Stage 0` |
| `1` | Stage 1: Volume Strategy | `Stage 1` |
| `2` | Stage 2: Arc Tactical Design | `Stage 2` |
| `3` | Stage 3: Episode Blueprinting | `Stage 3` |
| `4` | Stage 4: Sovereign Production | `Stage 4` |
| `6` | One-Stop Arc-by-Arc 자동 파이프라인 | `One-Stop` |
| `44` | Stage 4 회차 롤백 | `Rollback` |
| `77` | Stage 4 생산기록만 삭제 | `Wipe Stage4` |
| `88` | Stage 2 초기화 | `Reset Stage2` |
| `99` | Stage 2 정밀 되감기 | `Rewind Stage2` |
| `5` | 종료 | `Exit` |

추가: 프로젝트 선택(`_select_project`)은 시작 화면에서 드롭다운/리스트로 동일 동작.

## 화면 구성 (최소)
- 좌측: 메뉴 버튼(콘솔 키 구조 그대로)
- 중앙: 실시간 로그 타임라인(콘솔 출력 스트리밍)
- 우측: 대기/결과 연출 패널(빠칭코 + 상태 이펙트)

## 상태/이펙트 규칙
- `RUNNING`: 빠칭코 자동 재생
- `PASS`: 초록/금색 성공 연출 + 짧은 축하 사운드(옵션)
- `REJECT`: 붉은 실패 연출 + 흔들림/노이즈
- `PASS_WITH_FIX`: 노랑 강조 + `"한 번 더!"` 배지 표시 후 계속 진행

권장: 이펙트 길이 1.0~1.8초로 고정해서 작업 흐름 방해 최소화.

## 기술 방식 (백엔드 유지)
1. GUI에서 Python 프로세스(`main_a.py`) 실행
2. `stdout/stderr`를 실시간 수집해 로그 패널 출력
3. 로그에서 `PASS/REJECT/PASS_WITH_FIX`, `score=...`, `Stage ...` 패턴만 파싱해 이벤트화
4. 이벤트에 따라 우측 연출 패널 상태 전환

## 트리거 방식 (터미널 비노출)
- 결론: 가능. 비개발자는 터미널을 전혀 보지 않아도 됩니다.
- 버튼 클릭만으로 실행되게 구성:
  - `Stage 0` 버튼 → 내부적으로 메뉴 키 `0` 전달
  - `Stage 1` 버튼 → 내부적으로 메뉴 키 `1` 전달
  - `Stage 2/3/4/One-Stop/...`도 동일

옵션 A (빠른 MVP)
- GUI가 `main_a.py`를 숨김 실행하고, `stdin`으로 메뉴 입력값을 전달
- 장점: 기존 코드 변경 최소
- 단점: 콘솔 입출력 파싱 의존

옵션 B (권장, 2단계)
- `main_a.py` 앞에 얇은 브리지 API를 추가
- 예: `POST /run/stage3`, `POST /run/stage4`
- GUI는 API만 호출하고 상태는 JSON으로 수신
- 장점: 안정적, 유지보수 쉬움, 버튼 UX에 최적

운영 형태
- 데스크톱 앱(`.exe`) 또는 웹앱 모두 가능
- 공통 목표: 사용자 화면에는 버튼/로그/이펙트만 보이고 터미널은 숨김

## 비개발자 파일관리 UX (폴더 비노출)
- 전제: 내부적으로 프로젝트 폴더(`arcs/blueprints/manuscripts`)는 유지
- 원칙: 사용자에게는 폴더/경로를 보여주지 않고 "보관함 UI"만 제공

핵심 컴포넌트
- 프로젝트 드롭다운: `프로젝트 선택 / 새로 만들기 / 복제`
- 자료 탭: `Arc`, `Blueprint`, `Manuscript`
- 가져오기: 파일 또는 ZIP 업로드 시 내부 규칙에 따라 자동 배치
- 내보내기: 선택 자료를 ZIP으로 묶어 다운로드
- 백업/복원: 원클릭 스냅샷 생성/복구

동작 예시
1. 사용자가 드롭다운에서 프로젝트 선택
2. `Blueprint 탭 > 가져오기` 클릭 후 파일 업로드
3. 앱이 내부 폴더에 자동 저장 및 인덱싱
4. Stage 실행 버튼 클릭
5. 필요 시 `내보내기`로 결과 묶음 다운로드

저장 위치 정책
- 기본: OS 사용자 데이터 영역(예: `%LOCALAPPDATA%/Geuldobi/projects`)에 저장
- 옵션: 설정에서 작업 폴더 변경 가능(기본값은 숨김 유지)
- UI에는 절대경로 대신 프로젝트명/세트명만 표시

VM 필요성
- 결론: 본 요구(폴더 숨김/버튼 운영)에는 VM 필수 아님
- VM은 보안 격리 목적이 있을 때만 별도 검토

## MVP 일정 (짧게)
- Day 1: 메뉴 버튼 + 프로젝트 선택 + 실행/중지
- Day 2: 로그 스트리밍 + Stage 상태 뱃지
- Day 3: 빠칭코 + 3종 결과 이펙트

## 리스크 한 줄
- `WebGal` 단독으로 업무 UI까지 다 하면 유지보수가 불편할 수 있어, **연출 전용 사용**을 권장합니다.

## 연출 아이디어 백로그 (가볍게)
- 원칙: 기능 변경 없이 연출만 추가하고, 작업 흐름을 방해하지 않음
- 목표: 재미 + 상태 인지 강화 (PASS/REJECT/PASS_WITH_FIX 체감)

레퍼런스 감성
- `보상 상자 개봉` 계열 연출 느낌 참고
- 예: 닫힌 상자 → 빛 누출 → 개봉 → 등급 컬러 확산 → 결과 문구
- 주의: 특정 게임 자산 복제 금지, 감성/구조만 참고

미니 서사(나레이터 1명)
- 공통: 짧은 한 줄 멘트만 사용 (로그와 충돌 금지)
- `PASS`: "채택 완료. 다음 화로 진입합니다."
- `PASS_WITH_FIX`: "좋다. 한 번만 더 다듬자."
- `REJECT`: "이번 판은 리롤. 근거를 모아 재시도."

빠칭코/슬롯 연출 샘플
1. `RUNNING`: 릴 회전 + "심사중..."
2. `PASS`: 금색 플래시 + 짧은 컨페티
3. `PASS_WITH_FIX`: 노랑 펄스 + "한 번 더!" 배지
4. `REJECT`: 붉은 글리치 0.8초 + 즉시 로그 복귀

사운드/자산 (있는 것 활용)
- 애니메이션: Lottie 무료 템플릿
- SFX: Pixabay 등 무료 효과음
- 파티클: 경량 캔버스 라이브러리 사용

범위 제한 (과투자 방지)
- 연출 구현 시간 상한: MVP 총 1~2일
- 각 이펙트 길이: 1.0~1.5초
- `Skip animation`, `Mute`, `Low spec mode` 기본 제공
- 우선순위: 기능 안정성 > 로그 가독성 > 연출

## 애니메 감성 가이드 (빠른 적용)
- 결론: 가능. "재패니즈 애니메 느낌"은 자산 + 색 + 타이포 + 전환 타이밍으로 구현
- 구현 우선순위
  1. 배경(정적 1장) + 카드형 UI
  2. 상태 이펙트 3종(Lottie)
  3. 짧은 SFX(승리/실패/재시도)

스타일 키워드
- 파스텔 + 네온 포인트(청록/핑크/골드)
- 소프트 글로우, 라운드 패널, 얇은 하이라이트 라인
- 텍스트는 짧고 강하게: `심사중`, `채택`, `한 번 더`, `리롤`

바로 쓸 수 있는 소스 (검증 링크)
- Lottie 무료 Kawaii/Anime 계열: https://lottiefiles.com/free-animations/kawaii
- Lottie 상업 사용 안내(Simple License): https://help.lottiefiles.com/hc/en-us/articles/900002438343-Can-I-use-a-free-animation-on-Lottiefiles-for-commercial-business-use
- GUI Kawaii Pack (itch.io, 라이선스 명시): https://pocogamesco.itch.io/ui-user-interface-kawaii-pack
- Anime 배경(무료): https://unsplash.com/wallpapers/art/anime
- 슬롯/잭팟 SFX(무료): https://mixkit.co/free-sound-effects/slot-machine/
- 대체 SFX(무료): https://pixabay.com/sound-effects/slot-machine-payout-81725/

라이선스 체크 최소 규칙
- 각 에셋 페이지의 상업 사용 가능 여부 확인 후 사용
- 재배포 금지 조항 준수(원본 에셋 재판매/재배포 금지)
- 프로젝트 내 `credits.md`에 출처 URL 기록

## 세련 톤 프리셋 (Anime Chic)
- 목표: `애니메 감성`은 유지하고 `업무 도구`처럼 깔끔하게 보이기
- 비율: `작동 화면 80% + 연출 20%`

컬러
- 베이스: 오프화이트(`--bg: #F7F7F5`), 차콜(`--ink: #1F2329`)
- 포인트: 골드(`--accent-gold: #D4AF37`), 민트(`--accent-mint: #6ED3CF`)
- 상태색:
  - PASS: 골드+민트 하이라이트
  - PASS_WITH_FIX: 웜 앰버
  - REJECT: 저채도 레드

타이포
- 본문: 가독성 높은 산세리프 1종
- 타이틀: 일본풍 디스플레이 폰트 1종만 제한 사용
- 원칙: 강조 폰트 남용 금지 (헤더/배지 한정)

모션
- 기본 트랜지션: 160~220ms
- 결과 이펙트: 최대 1.2초
- 즉시 제어: `Skip animation` 항상 노출

카피(짧고 쿨하게)
- PASS: `채택`
- PASS_WITH_FIX: `한 번 더`
- REJECT: `재시도`
- RUNNING: `심사중`

금지 규칙
- 과도한 반짝임, 과포화 네온, 긴 애니메이션 금지
- 화면 전체를 가리는 이펙트 금지 (로그 가독성 우선)
- 사운드 자동재생 강제 금지 (`Mute` 기본 제공)

## 참고 레퍼런스 링크 모음 (나중에 보기)
- UI 구조 참고
  - Mobbin: https://mobbin.com
  - Nicelydone: https://nicelydone.club
  - One Page Love: https://onepagelove.com/inspiration
- 비주얼/감성 참고
  - Land-book: https://land-book.com
  - Godly: https://godly.website
  - Lapa Ninja: https://www.lapa.ninja/post/
- 일본풍 감성 참고
  - SANKOU!: https://sankoudesign.com/
  - MUUUUU.ORG: https://muuuuu.org/zh
  - Japan Web Design Gallery: https://japanwebdesign.com/
- 모션/연출 에셋
  - LottieFiles (Kawaii): https://lottiefiles.com/free-animations/kawaii
- 폰트 참고
  - Zen Maru Gothic: https://fonts.google.com/specimen/Zen+Maru+Gothic
  - M PLUS Rounded 1c: https://fonts.google.com/specimen/M+PLUS+Rounded+1c
  - DotGothic16: https://fonts.google.com/specimen/DotGothic16

## 대기실 미니게임 (옵션)
- 아이디어: Stage 실행 대기 중 우측 패널에서 `공룡 점프` 미니게임 제공
- 목적: 긴 대기 시간 체감 완화 (사용자 선택 기능)

운영 원칙
- 기본값 `OFF` (사용자가 `대기실 열기`를 켤 때만 표시)
- 백엔드 비차단: 게임 동작이 파이프라인/로그/버튼 동작에 영향 주면 안 됨
- 이벤트 우선순위: `PASS/REJECT/PASS_WITH_FIX` 발생 시 게임 자동 일시정지 후 결과 이펙트 우선
- 입력 충돌 방지: 게임 키 입력은 게임 패널 포커스 시에만 유효
- 데이터 정책: 점수는 로컬 임시 저장만 사용 (DB/서버 연동 없음)

MVP 범위
- Canvas 기반 1종 (`점프`, `장애물`, `점수`, `재시작`)
- 구현 시간 상한: 0.5~1일
- 저사양 모드에서 자동 비활성화 가능
