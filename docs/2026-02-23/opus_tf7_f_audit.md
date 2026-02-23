# TF-7-F 감사 보고서 — 인코딩·직렬화 안전성

## 감사 파일 목록
- `modules/core/db_manager.py`
- `modules/core/project_manager.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage0/reverse_expander.py`
- `modules/core/stage0/style_extractor.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/prompt_loader.py`
- `main_a.py`
- `config/prompts/analyst.yaml`
- `config/prompts/director.yaml`
- `config/prompts/writer_rules.json`
- `config/prompts/analyst_libraries.json`
- `config/prompts/weaver_rules.json`

## 발견 이슈 (총 0건)
- 확정 버그 없음.

## Risk (총 1건)

### [TF-7-F-R1] LLM 응답 JSON 파싱 전 surrogate 정규화 부재 (MEDIUM, Risk)
**파일**: `modules/domain/agents/base_agent.py`  
**줄**: `982`, `1001`, `1009`

**현재 코드**:
```python
if not text or not isinstance(text, str):
    return {"parsing_error": True, "content": "Empty or Invalid Input"}
...
clean_text = re.sub(r"```json\s*|```\s*", "", text.strip())
...
data = json.loads(raw_json, strict=False)
```

**문제(위험)**: `json.loads()` 전에 unpaired surrogate(U+D800~U+DFFF) 정규화/치환 단계가 없음.

**영향**: 깨진 문자열이 유입되면 JSON 1차 파싱 실패 후 regex/RAW fallback으로 내려가 구조 정보가 손실될 수 있음(즉시 크래시보다는 품질 저하 경로).

**Bug-vs-intent 근거**: 같은 함수에 다단 fallback(`ast.literal_eval`, regex 추출, RAW 반환)이 이미 의도적으로 설계되어 있어 즉시 결함으로 단정하기 어렵고, 운영 리스크로 분류하는 것이 타당.

**Open Question**: 운영 로그에서 surrogate 관련 파싱 실패가 반복되는지(빈도/재현성) 확인 필요.

## [FP] 오탐 목록

### [FP-1] `open()`/`read_text()` UTF-8 누락
- **판정**: 오탐 (누락 경로 미발견)
- **수동 근거**:
  - `main_a.py:10`, `main_a.py:1027`, `main_a.py:1240`, `main_a.py:1292`, `main_a.py:1352`, `main_a.py:1557`, `main_a.py:1692`, `main_a.py:2000`
  - `modules/core/project_manager.py:105`, `modules/core/project_manager.py:719`, `modules/core/project_manager.py:722`, `modules/core/project_manager.py:818`
  - `modules/core/stage0/reverse_expander.py:130`, `modules/core/stage0/reverse_expander.py:193`, `modules/core/stage0/reverse_expander.py:442`, `modules/core/stage0/reverse_expander.py:446`
  - `modules/core/prompt_loader.py:93`, `modules/core/stage4_post_processor.py:157`
- **의도 확인**: Windows(cp949) 환경 대응 목적의 명시적 UTF-8 사용이 일관됨.

### [FP-2] `json.dumps(..., ensure_ascii=False)` 누락
- **판정**: 오탐 (핵심 저장 경로에서 누락 미발견)
- **수동 근거**:
  - `modules/core/db_manager.py:757`, `modules/core/db_manager.py:1113`, `modules/core/db_manager.py:1159`, `modules/core/db_manager.py:1184`, `modules/core/db_manager.py:1261`, `modules/core/db_manager.py:1865`
  - `modules/core/project_manager.py:207`, `modules/core/project_manager.py:216`
  - `modules/core/stage0/reverse_expander.py:443`, `modules/core/stage0/reverse_expander.py:447`
  - `modules/core/stage0/style_extractor.py:64`
  - `modules/domain/agents/base_agent.py:942`, `modules/domain/agents/base_agent.py:961`
  - `main_a.py:1353`
- **의도 확인**: 한글 가독성 보존 의도가 코드 전반에 반영됨.

### [FP-3] 위험한 `yaml.load()` 사용
- **판정**: 오탐 (`yaml.load()` 단독 사용 미발견)
- **수동 근거**:
  - `modules/domain/agents/base_agent.py:63`, `modules/domain/agents/base_agent.py:114` → `yaml.safe_load`
  - `main_a.py:1028` → `yaml.safe_load`
  - `modules/core/prompt_loader.py:83-85` → PyYAML 대신 자체 파서(unsafe load 호출 없음)
- **의도 확인**: 안전 로더 또는 비-PyYAML 파서 사용으로 보안 리스크 회피.

### [FP-4] Stage4 출력 BOM(`utf-8-sig`) 불일치
- **판정**: 오탐 (BOM 강제/혼용 경로 미발견)
- **수동 근거**:
  - `modules/core/stage4_post_processor.py:157` → `write_text(..., encoding="utf-8")`
  - 샘플 파일 BOM 검사 결과: `config/prompts/analyst.yaml`, `config/prompts/director.yaml`, `config/prompts/writer_rules.json`, `config/prompts/analyst_libraries.json`, `config/prompts/weaver_rules.json` 모두 BOM 없음.
- **의도 확인**: UTF-8(no BOM) 방향이 일관됨.

### [FP-5] Windows 경로 `\` 하드코딩으로 인한 역설계 입력 실패
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/stage0/reverse_expander.py:128`, `modules/core/stage0/reverse_expander.py:164`, `modules/core/stage0/reverse_expander.py:573`, `modules/core/stage0/reverse_expander.py:609`
- **의도 확인**: `pathlib.Path` 중심 구현으로 OS 경로 구분자 종속성이 낮음.

### [FP-6] DB TEXT 역직렬화 이중 처리 (`json.loads(json.dumps(...))`)
- **판정**: 오탐 (확정 경로 미발견)
- **수동 근거**:
  - 저장: `modules/core/db_manager.py:1113`, `modules/core/db_manager.py:1159`, `modules/core/db_manager.py:1184`
  - 조회: `modules/core/db_manager.py:1138`, `modules/core/db_manager.py:1172`, `modules/core/db_manager.py:1199`, `modules/core/db_manager.py:1214`
- **의도 확인**: 저장(직렬화 1회) ↔ 조회(역직렬화 1회) 대칭 구조가 유지됨.

## 요약 테이블 (파일별 인코딩 안전성 등급)

| 파일 | F-1 Encoding | F-2 ensure_ascii | F-3/F-8 직렬화 일관성 | F-4 YAML 안전 | F-5 BOM | F-6 경로 | F-7 surrogate | 등급 |
|---|---|---|---|---|---|---|---|---|
| `modules/core/db_manager.py` | PASS | PASS | PASS | N/A | N/A | N/A | N/A | A |
| `modules/core/project_manager.py` | PASS | PASS | PASS | N/A | N/A | N/A | N/A | A |
| `modules/core/stage4_post_processor.py` | PASS | N/A | PASS | N/A | PASS | N/A | N/A | A |
| `modules/core/stage0/reverse_expander.py` | PASS | PASS | PASS | N/A | N/A | PASS | N/A | A |
| `modules/core/stage0/style_extractor.py` | PASS | PASS | PASS | N/A | N/A | N/A | N/A | A |
| `modules/domain/agents/base_agent.py` | PASS | PASS | PASS | PASS | N/A | N/A | **RISK** | B |
| `modules/core/prompt_loader.py` | PASS | N/A | N/A | PASS(unsafe load 없음) | N/A | N/A | N/A | A |
| `main_a.py` | PASS | PASS | PASS | PASS | N/A | N/A | N/A | A |
| `config/prompts/*` 샘플 5개 | PASS | N/A | N/A | N/A | PASS(BOM 없음) | N/A | N/A | A |
