# TF-7-M: YAML / Prompt Config 완전성 — 감사 실행 오더

> **Opus TF-7-M** | 2026-02-23
> **담당**: Opus 에이전트 M
> **출력**: `docs/2026-02-23/opus_tf7_m_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / 근거 필수

---

## 배경
TF-6 G 패치에서 4개 임계값이 `validation.yaml`에 외부화됨. `system.yaml`에는 TF-5 L-3에서 `retry.director_max_attempts` 관련 이슈 발생 — 패치 확인 필요. 43개 YAML 프롬프트 전량 읽기는 비현실적이므로 핵심 경로 집중 + 공통 패턴 점검.

---

## 실행 순서

### Step 1: validation.yaml 최신 상태 확인
**파일**: `config/settings/validation.yaml`
- Read 도구로 전체 파일 읽기
- TF-6 G 패치 추가 키 확인:
  - `smart_retrieval.slot_max_chars_default: 1500`
  - `smart_retrieval.max_npcs_per_slot: 5`
  - `scope.min_beats_floor: 1`
  - `scope.min_avg_words: 6`
  - `scope.min_word_per_beat: 4`
  - `scope.min_diversity: 0.6`
  - `scope.max_stagnation_hits: 3`
  - `scoring.sanitize_max_chars: 3000`
  - `scoring.cv_optimal_low: 0.35`
  - `scoring.cv_optimal_high: 0.55`
  - `scoring.wuxia_martial_min: 3`
  - `scoring.hunter_system_min: 5`
- 누락된 키 → MEDIUM 이슈 (코드에서 `_threshold()` 기본값 fallback 동작하나 YAML 누락)

### Step 2: system.yaml Director 설정
**파일**: `config/system.yaml`
- Read 도구로 전체 파일 읽기
- TF-5 L-3 패치 확인: `retry.director_max_attempts` 키 존재 여부 + Stage4 루프에서 사용 여부
- TF-6 G-4 패치 확인: `retry.max_json_payload`, `cache.context_max_entries`, `cache.min_content_chars` 존재 여부
- YAML 파일 형식: UTF-8 (BOM 없음) 확인 — 첫 줄 `---` 또는 키 이름으로 판단

### Step 3: settings.json 레거시 여부
**파일**: `config/settings.json`
- Read 도구로 전체 파일 읽기
- `system.yaml`과 중복된 키 목록 파악
- 어느 쪽이 우선권을 갖는지: `config_manager.py`에서 로드 순서 확인
- 레거시로 판단되면 MEDIUM 이슈 (혼용으로 인한 설정 불투명성)

### Step 4: PromptLoader 캐시 정책
**파일**: `modules/core/prompt_loader.py`
- Read 도구로 전체 파일 읽기
- 싱글톤 캐시 무효화 트리거: YAML 파일 변경 감지(mtime) vs 영구 캐시
- YAML 파일 `open()` 시 `encoding="utf-8"` 명시
- `yaml.safe_load()` vs `yaml.load()` 확인 (보안)
- 프롬프트 키 조회 실패 시: `KeyError` 전파 vs `None` 반환 vs 기본값

### Step 5: ConfigManager 로드 우선순위
**파일**: `modules/core/config_manager.py`
- Read 도구로 전체 파일 읽기
- `system.yaml`과 `settings.json` 병합 우선순위
- `validation.yaml` 로드 경로 및 싱글톤 여부

### Step 6: YAML 프롬프트 샘플 점검
**파일**: `config/prompts/` 디렉터리 내 파일 목록 확인 후 대표 10개 읽기
- 선정 기준: chief_writer, director, analyst, arc_generator 관련 핵심 프롬프트
- 각 파일에서 확인:
  - `{변수명}` 플레이스홀더가 `prompt_loader.py`에서 치환되는지
  - 미치환 플레이스홀더가 LLM에 그대로 전달되는 경로
  - 한글 내용의 인코딩 (UTF-8 BOM 없음 여부)
  - 미사용 키(코드에서 참조되지 않는 YAML 키) — 파악 가능한 범위에서

### Step 7: models.yaml 모델 ID 일치 확인
**파일**: `config/models.yaml` (존재하면)
- Read 도구로 읽기
- `base_agent.py`에서 사용하는 실제 모델 ID와 비교
  - `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001` 등
  - 오타 또는 구버전 모델 ID 잔존 여부

---

## 출력 파일 구조
```
# TF-7-M 감사 보고서 — YAML / Prompt Config 완전성

## 감사 파일 목록
## TF-6 G 패치 validation.yaml 반영 확인 (키별 체크리스트)
## TF-5 L-3 패치 system.yaml 반영 확인
## 발견 이슈 (총 N건)
### [TF-7-M-1] ...
## YAML 키 현황 테이블 (코드 사용 O/X)
## [FP] 오탐 목록
## 요약 테이블
```
