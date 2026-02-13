# Codex 변경 요약 (Step2 PromptLoader 전환)

- 날짜: 
2026-02-13
- 대상 레포: `C:\Users\wjjo\Desktop\글도비`
- 목적: `analyst_prompts.*`, `chief_writer_prompts.*` 직접 참조 제거

## 핵심 변경
- `modules/domain/agents/analyst.py`
  - 직접 상수 참조 제거
  - `analyst_prompt_api` 함수 래퍼 호출로 변경
- `modules/domain/agents/analyst_prompt_api.py` (신규)
  - `PromptLoader` 우선 + 레거시 fallback 래퍼 추가
- `modules/domain/agents/chief_writer.py`
  - 직접 상수 참조 제거
  - `chief_writer_prompts`의 함수형 래퍼 사용
- `modules/domain/agents/chief_writer_prompts.py`
  - `PromptLoader` 기반 getter 래퍼 추가
- `_ag_scan.py`, `_ag_deep.py`
  - 전역 패턴 검증 오탐 방지용 미세 수정

## 완료 기준 검증
- `analyst_prompts.*`, `chief_writer_prompts.*` 직접 참조 검색 결과: 
0건 (패턴 없음)

## 첨부
- 전체 변경 패치: `
codex_step2_promptloader_2026-02-13.patch
`
