# Codex P0 구현 오더

## 지시

`docs/2026-03-05/TF-LLM-ease-accuracy-improvement-spec.md`의 "코덱스 구현 오더" 섹션을 읽고,
**P0 오더 3건(TF-D, TF-E, TF-A)** 을 순서대로 구현하세요.

세 오더는 서로 독립적이므로 순서 무관하나, 아래 순서를 권장합니다: TF-D → TF-E → TF-A.

---

## 대원칙 (CLAUDE.md 발췌 — 절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python 코드가 "이건 오류니까 감점" 같은 판단을 하면 안 됨.
2. **디렉터 주권주의** — Director(LLM)가 최종 품질 결정권. Python이 Director를 우회하면 안 됨.
3. **사망 캐릭터 금지 표현은 유지** — "사망 NPC 행동/대사 등장 금지" 같은 핵심 금지는 톤 변경 대상이 아님.

---

## 오더별 핵심 요약

### TF-D: Advisory 우선순위 시각화
- **파일**: `modules/core/stage4_interview_round.py`
- **위치**: `_run_advisory_chain()` 반환값을 `_director_mc_parts`에 합치는 블록 (L457 `_director_mc_parts = _advisory_parts + _director_mc_parts` 직전)
- **할 일**: `_advisory_parts` 리스트의 각 문자열에 CRITICAL/MAJOR/INFO 헤더 태그 추가 + 경고 0건 advisory 1줄 축약
- **건드리지 말 것**: 각 advisory 모듈 파일(truth_gate.py 등)의 반환값, `_advisory_summary` dict 로직(L440-456)
- **상세**: 명세 문서 오더 1 참조

### TF-E: Chief Writer 규칙 톤 조절
- **파일**: `config/prompts/chief_writer.yaml`
- **할 일**: "절대 금지"→"사용하지 마세요", "무조건 REJECT"→"감점 대상입니다", "벽돌 문단 = 독자 이탈 1순위"→"5줄 이상 연속 서술은 줄바꿈으로 끊어주세요" 등 톤 다운
- **건드리지 말 것**: 사망NPC 금지, 미습득 무공/스킬 금지, 원시인모드 현대용어 금지 — 이 3가지는 톤 변경 대상 아님
- **주의**: `절대 금지`가 8곳 있음(L23, L49, L51, L52, L53, L66, L104 등). 대원칙 관련 3곳은 유지, 나머지만 변경.
- **상세**: 명세 문서 오더 2 참조

### TF-A: 프롬프트 중복 제거
- **파일**: `config/prompts/director.yaml`
- **할 일**: ENSEMBLE_VARIABLE_PROMPT에서 아래 3개 블록을 삭제하고 참조 1블록으로 교체:
  - `[V67] 모순 검사 9항` (L345-385, ~41줄) — ENSEMBLE_STABLE_CONTEXT(L61-101)과 동일 중복
  - `[I-10] 점진적 감점 규칙` (L371-375) — L87과 동일 중복
  - `[TF-27] 100점 지향 원칙` (L377) — L93과 동일 중복
- **교체 블록**:
  ```yaml
      ### ※ 중복 방지 — stable_context 참조
      아래 항목은 stable_context에 이미 포함되어 있으므로 동일 기준을 적용하세요:
      - [V67] 명시적 모순 검사 9항
      - [I-10] 점진적 감점 규칙 (CRITICAL/MAJOR/MINOR)
      - [TF-27] 100점 지향 원칙
  ```
- **건드리지 말 것**: ENSEMBLE_STABLE_CONTEXT(L61-101)의 원본 — 이것이 SSOT임
- **주의**: 삭제 대상 블록들은 연속되지 않을 수 있음. V67 블록 안에 I-10과 TF-27이 포함되어 있으므로 실제로는 L345-395 범위의 큰 블록 1개를 삭제하고 참조 블록으로 교체하는 형태일 수 있음. **반드시 현재 파일을 읽어서 정확한 범위를 확인한 후 작업할 것.**
- **상세**: 명세 문서 오더 3 참조

---

## ⚠️ 인코딩 주의 (최우선)

이 프로젝트의 YAML/Python 파일은 **전량 UTF-8 (BOM 없음)** 입니다.

**필수 규칙**:
1. **파일 읽기/쓰기 시 반드시 UTF-8 인코딩 유지** — YAML 파일에 한글이 대량 포함됨. latin-1이나 cp949로 읽으면 즉시 깨짐.
2. **BOM 삽입 금지** — UTF-8 BOM(`\xef\xbb\xbf`)을 절대 추가하지 마세요. Python `PromptLoader`가 BOM을 처리하지 않음.
3. **줄바꿈: LF (`\n`)** — CRLF(`\r\n`)로 변환하지 마세요.
4. **YAML 특수문자 이스케이프 주의** — 한글 큰따옴표(`"`, `"`)와 ASCII 큰따옴표(`"`)를 혼동하지 마세요. YAML 문자열 내부의 따옴표 이스케이프(`\"` 또는 `''`)를 깨뜨리면 파싱 실패.
5. **수정 후 반드시 검증**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/prompts/director.yaml', encoding='utf-8'))"
   python -c "import yaml; yaml.safe_load(open('config/prompts/chief_writer.yaml', encoding='utf-8'))"
   ```
   이 명령이 에러 없이 통과해야 함.
6. **diff 확인**: 수정 전후 `git diff`에서 의도하지 않은 한글 깨짐(`\uXXXX` escape, `?????` 등)이 없는지 확인.

---

## 검증

각 TF 완료 후:

```bash
# 1. 인코딩 무결성 (YAML 파싱)
python -c "import yaml; yaml.safe_load(open('config/prompts/director.yaml', encoding='utf-8'))"
python -c "import yaml; yaml.safe_load(open('config/prompts/chief_writer.yaml', encoding='utf-8'))"

# 2. 구문 검사
python -m py_compile <변경한_py_파일>

# 3. 전체 테스트
pytest tests/ -q
```

**기준선: 3,348 passed**. 이보다 줄어들면 안 됨.

TF-A 완료 후 프롬프트 길이가 크게 줄어들므로 `tests/test_satisfaction_step2_prompts.py`의 프롬프트 길이 임계값이 깨질 수 있음 → 임계값을 현재 길이에 맞게 조정.

---

## 커밋

TF별 1커밋:
```
feat(TF-D): Advisory 우선순위 시각화 — CRITICAL/MAJOR/INFO 헤더 + 0건 축약
feat(TF-E): Chief Writer 규칙 톤 조절 — 강압 표현 완화 (핵심 금지 유지)
feat(TF-A): Director 프롬프트 중복 제거 — V67/I-10/TF-27 VARIABLE→STABLE 참조
```

---

## P0 감리 결과 (2026-03-05)

| TF | 결과 | 상세 |
|----|------|------|
| TF-D | ✅ PASS | CRITICAL/MAJOR/INFO 헤더 + 0건 축약 정상 |
| TF-E | ✅ PASS | 톤 다운 4곳 + 핵심 금지 3곳 유지 |
| TF-A | ❌→복구 | Codex가 VARIABLE_PROMPT(SSOT) 삭제 → 수동 복원. **오더 설계 오류**: STABLE_CONTEXT에 V67 없음. P2 재분류 |

**최종 상태**: 3,348 passed, YAML 파싱 OK, VARIABLE_PROMPT SSOT 복원 완료.

---

## 참고 파일

- **명세 전문**: `docs/2026-03-05/TF-LLM-ease-accuracy-improvement-spec.md` (오더 1~3 섹션)
- **CLAUDE.md**: 프로젝트 대원칙 + 현재 상태
- **주요 변경 대상**:
  - `modules/core/stage4_interview_round.py` (TF-D)
  - `config/prompts/chief_writer.yaml` (TF-E)
  - `config/prompts/director.yaml` (TF-A)
  - `tests/test_satisfaction_step2_prompts.py` (TF-A 후 임계값 조정)
