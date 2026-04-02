# 글도비

> LLM 기반 장편 웹소설 자동 생성 워크스페이스.
> CLI 런타임, Electron 데스크톱 앱, narrative pipeline 도구, 운영 감리 문서를 함께 포함한다.

## 저장소 한눈에 보기

글도비는 세계관 자료와 플롯 입력을 바탕으로 Stage 0부터 Stage 4까지의 생산 파이프라인을 운영하는 시스템이다. 기본 진입점은 `main_a.py`이며, 장르별 가드, Director 중심 심사, advisory/validation 체인, SQLite 기반 상태 저장, Electron control plane이 한 저장소 안에 묶여 있다.

현재 루트 README는 루트 런타임과 운영 동선을 설명한다. 작품별 TR/BI 라우팅 엔트리와 narrative-family 전용 흐름은 [`README.narrative-router.md`](README.narrative-router.md)로 분리되어 있다.

## 현재 브랜치 기준 스냅샷

Tracked Python 파일 기준으로 집계한 현재 코드 스냅샷이다.

| 항목 | 값 |
| --- | --- |
| Python 소스 파일 | 442 |
| Python 테스트 파일 | 414 |
| Python 소스 LOC | 235,920 |
| Python 테스트 LOC | 122,938 |
| `modules/domain/agents/*.py` | 51 |
| `modules/validation/*.py` | 17 |
| `modules/core/genre_guards/*.py` | 14 |
| 데스크톱 셸 | Electron 40 + React 18 |

## 파이프라인 개요

| 단계 | 역할 | 대표 산출물 |
| --- | --- | --- |
| Stage 0 | 세계관, 스타일, 프로젝트 입력 정리 | Bible, Treatment, 스타일 정보 |
| Stage 1 | 권/볼륨 전략 수립 | volume strategy |
| Stage 2 | Arc 전술 설계 | tactical doc, state constraints |
| Stage 3 | 에피소드 블루프린트 생성 | scene breakdown, integrated scenario |
| Stage 4 | 원고 집필 및 검증 | manuscript, 상태 업데이트, 검증 결과 |
| OneStop | Arc 단위 자동 실행 | Stage 2 -> 3 -> 4 연쇄 결과 |

핵심 운영 원칙은 다음과 같다.

- Director가 최종 품질 판정권을 가진다.
- Python은 수집, 포맷팅, 전달을 담당하고 판단은 LLM 에이전트가 맡는다.
- 장르 가드, advisory chain, validation pipeline을 통해 장기 연재 모순을 줄인다.
- UTF-8은 워크스페이스 전역 불변식이다.

## 저장소 지도

- `main_a.py`
  - CLI 진입점이자 Stage 0/1/2/3/4/OneStop 운영 오너
- `modules/core/`
  - 오케스트레이터, 런타임 분해 모듈, DB, 상태/컨텍스트, 검증 공용 코어
- `modules/domain/agents/`
  - Analyst, Director, Chief Writer, ensemble, validator 계열 LLM 에이전트
- `modules/api/`
  - desktop/control-plane용 bridge server, process runner, risk approval, run validator
- `modules/validation/`
  - blocking, continuity, scoring, advisory 등 검증기 구현
- `geuldobi-desktop/`
  - Electron 데스크톱 앱
  - authoritative desktop entry는 `geuldobi-desktop/src/main.js`
  - 루트 `main.js`는 debug shadow entry만 담당
- `scripts/`
  - ops governance, UTF-8 hygiene, narrative routing, test support 스크립트
- `tests/`
  - unit, integration, e2e, property, desktop/runtime contract 테스트
- `projects/`
  - 프로젝트별 DB, 실행 산출물, 회차 결과물
- `treatments/`, `bible/`
  - 작품 입력/중간 산출물
- `docs/`
  - 운영 하네스, 감리 문서, execution SSOT, dated audit 문서
- `AGENTS.md`
  - 현재 워크스페이스 운영 SSOT

## 빠른 시작

### 1. Python 환경 준비

요구사항:

- Python 3.11 이상
- 기본 런타임용 Gemini API 키
- 데스크톱 앱을 사용할 경우 Node.js + npm

설치:

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

최소 구성은 `GOOGLE_API_KEY`다.

```bash
GOOGLE_API_KEY=your_google_api_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/workspace/webhook
```

멀티 프로바이더 실험을 할 경우 아래 환경 변수를 추가로 사용할 수 있다.

```bash
GOOGLE_API_KEY_2=your_second_key
GOOGLE_API_KEY_3=your_third_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
VERTEX_API_KEY=your_vertex_api_key
VERTEX_PROJECT_ID=your_gcp_project
VERTEX_LOCATION=asia-northeast3
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
```

기본 provider 활성화 상태는 [`config/models.yaml`](config/models.yaml)에 정의되어 있으며, 현재 기본값은 Gemini 우선이다.

### 주요 설정 파일

- [`config/models.yaml`](config/models.yaml)
  - provider 활성화 상태, 에이전트별 모델 매핑, 폴백 체인
- [`config/settings/validation.yaml`](config/settings/validation.yaml)
  - 길이 기준, 품질 게이트, 장르별 threshold, retry/patch/context 예산
- `config/prompts/`
  - 프롬프트 외부화 자산

### 3. CLI 실행

```bash
python main_a.py
```

일반적인 운영 흐름:

1. 프로젝트 선택 또는 생성
2. Stage 0으로 입력 정리
3. 필요 시 Stage 1 진행
4. Stage 2 -> Stage 3 -> Stage 4 순차 실행
5. 반복 작업은 OneStop으로 Arc 단위 자동 실행

### 4. 데스크톱 앱 실행

```bash
cd geuldobi-desktop
npm install
npm start
```

패키징:

```bash
cd geuldobi-desktop
npm run build
```

## 테스트와 검증

Windows 환경에서는 메모리 보수 모드가 기본 권장 경로다.
필요하면 `PYTHONIOENCODING=utf-8`을 설정한 뒤 `pytest`를 실행한다.

```bash
python scripts/run_pytest_lowmem.py
```

대상 테스트만 빠르게 돌릴 때:

```bash
pytest tests/test_director_modules.py -q
```

전체 테스트 스위트:

```bash
pytest tests/ -q
```

추가 운영 검증:

```bash
python scripts/check_utf8_hygiene.py README.md
python scripts/ops_validator.py
```

세부 규칙은 [`tests/README.md`](tests/README.md), [`scripts/README.md`](scripts/README.md)를 참고한다.

## 문서와 운영 동선

시스템 트랙과 narrative 트랙의 시작 지점이 다르다.

- 시스템 트랙
  - [`AGENTS.md`](AGENTS.md)
  - [`docs/implementation/system-order-init-harness.md`](docs/implementation/system-order-init-harness.md)
  - [`docs/2026-03-23/llm-codebase-orientation-pack.md`](docs/2026-03-23/llm-codebase-orientation-pack.md)
- narrative 트랙
  - [`AGENTS.md`](AGENTS.md)
  - [`README.narrative-router.md`](README.narrative-router.md)
  - [`docs/narrative-router/SSOT_narrative-router-integrated-order.md`](docs/narrative-router/SSOT_narrative-router-integrated-order.md)

추가 참고 문서:

- [`scripts/README.md`](scripts/README.md)
- [`tests/README.md`](tests/README.md)
- [`docs/temp/README.md`](docs/temp/README.md)

## 최상위 구조

```text
글도비/
├── AGENTS.md
├── README.md
├── README.narrative-router.md
├── main_a.py
├── main.js
├── config/
├── modules/
├── geuldobi-desktop/
├── scripts/
├── tests/
├── projects/
├── treatments/
├── bible/
└── docs/
```

## 라이선스

Private repository. All rights reserved.
