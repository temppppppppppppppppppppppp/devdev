# TF-7-F: 인코딩·직렬화 안전성 (횡단) — 감사 실행 오더

> **Opus TF-7-F** | 2026-02-23
> **담당**: Opus 에이전트 F
> **출력**: `docs/2026-02-23/opus_tf7_f_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
한국어 소설 파이프라인이므로 UTF-8 인코딩 안전성은 운영 필수 조건. TF-6 실행 수칙에도 "인코딩: 모든 파일 I/O는 UTF-8, 한글 깨짐 절대 금지"가 명시됐으나 전용 감사 TF가 없었음. Windows 환경에서 `open()` 기본 인코딩은 `cp949`이므로 `encoding` 미명시 시 깨짐 발생.

---

## 실행 순서

### Step 1: DB Manager I/O 핵심 경로
**파일**: `modules/core/db_manager.py` (전체 읽기, 대용량이므로 구간 분할)
- 집중 검사 영역:
  - `json.dumps()` 호출 전체 → `ensure_ascii=False` 여부
  - `json.loads()` 호출 → `str` vs `bytes` 입력 타입
  - `open()` 호출 → `encoding="utf-8"` 명시 여부
- 이슈 등록 기준: `json.dumps(...)` 에서 `ensure_ascii` 파라미터 없거나 `True`인 경우

### Step 2: Project Manager 파일 저장/로드
**파일**: `modules/core/project_manager.py`
- 파일 크기 확인 후 Read
- `open(path, 'w')` 또는 `open(path, 'r')` 호출에서 `encoding` 파라미터 누락 탐지
- JSON 파일 저장: `json.dump(data, f, ensure_ascii=False, indent=2)` 패턴 여부
- `pathlib.Path.write_text()` 사용 시 `encoding` 파라미터 확인

### Step 3: Stage4 Post Processor 출력 파일
**파일**: `modules/core/stage4_post_processor.py` (543줄)
- Read 도구로 전체 파일 읽기
- 카카오/네이버 포맷 파일 출력 경로: `open(output_path, 'w', encoding=?)` 확인
- BOM(`utf-8-sig`) 사용 여부 — 플랫폼별 요구사항 문서화
- 한글 이스케이프(`\uXXXX`) 포함 여부 확인

### Step 4: ReverseExpander 원고 파일 읽기
**파일**: `modules/core/stage0/reverse_expander.py` (1131줄)
- 집중 검사: `open(path, ...)` 호출 경로만 추적 (전체 읽기 후 `open` 키워드 위치)
- 외부 원고 파일 경로 처리: `os.path` vs `pathlib.Path` 사용
- Windows 역슬래시(`\`) 경로가 Unix 환경에서 실패 여부

### Step 5: BaseAgent JSON 파싱
**파일**: `modules/domain/agents/base_agent.py`
- 집중 검사: `json.loads()`, `json.dumps()` 호출 전체
- LLM 응답 문자열 처리:
  - 서로게이트 문자 (U+D800~U+DFFF) 포함 시 `json.loads()` 오류 방어
  - `ensure_ascii=False` 기반 `json.dumps()` 여부
- `_extract_json_robust()` 내부에서 bytes → str 변환 경로

### Step 6: PromptLoader YAML 읽기
**파일**: `modules/core/prompt_loader.py`
- Read 도구로 전체 파일 읽기
- `yaml.safe_load()` vs `yaml.load()` 사용 확인 (보안 이슈)
- YAML 파일 `open()` 시 `encoding="utf-8"` 명시 여부
- 한글 프롬프트 값 처리: YAML에서 읽은 한글 문자열이 그대로 LLM 입력에 전달되는지

### Step 7: main_a.py UI 출력
**파일**: `main_a.py`
- 대용량이므로 집중 검사: `open()` 호출, `print()` 경로 확인
- 파일 저장/로드 경로에서 `encoding` 파라미터
- `sys.stdout`의 인코딩 처리 (`UTF-8 mode` 설정 여부)

### Step 8: YAML Config 파일 인코딩
**파일**: `config/prompts/` 내 주요 YAML 파일 샘플 3~5개
- BOM 없는 UTF-8 저장 여부 (파일 첫 3바이트 확인 방법은 Read 도구로 내용 확인)
- 한글 주석이 올바르게 표시되는지

---

## 이슈 분류
| 항목 | 등급 |
|------|------|
| `open()` `encoding` 누락 (한글 포함 파일) | HIGH |
| `json.dumps()` `ensure_ascii` 미설정 (한글 포함) | MEDIUM |
| `yaml.load()` (보안) | HIGH |
| Windows 경로 `\` 하드코딩 | MEDIUM |
| 서로게이트 문자 방어 누락 | MEDIUM |

---

## 출력 파일 구조
```
# TF-7-F 감사 보고서 — 인코딩·직렬화 안전성

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-F-1] open() encoding 누락: {파일명}:{줄}
...
## [FP] 오탐 목록
## 요약 테이블 (파일별 인코딩 안전성 등급)
```
