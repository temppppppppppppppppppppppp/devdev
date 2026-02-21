# Stage 0/1 Opus TF Audit Report

**Date**: 2026-02-21
**Scope**: `stage01_helpers.py`, `analyst.py`, `analyst_prompts.py`, `stage0/` modules

## Findings

### S01-01. `arcs_anchor` dict-path dead code with unreachable key format
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/analyst.py:927-929`
- **Content**: `_post_process_arc`의 dict 분기는 `arcs_anchor.get(f"arc_{clean_arc_no - 1}")`를 사용하지만, 모든 프로덕션 저장 경로는 `list[dict]`를 사용. dict 분기는 항상 `None` 반환하여 연속성 검증을 무시. `get_state_constraint_prompt`(L1456)은 list만 처리하여 dict인 경우 조용히 빈 결과 반환.
- **Impact**: 레거시 dict 형식 arcs에서 연속성 검증 우회
- **Difficulty**: LOW
- **Previous**: NEW

### S01-02. `persist_to_vectordb` uses `ep_num - 1` index for non-contiguous episodes
- **TF**: TF-2 (Data flow)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage0/reverse_expander.py:453`
- **Content**: `episode_bibles[ep_num - 1]` 인덱싱 — 비연속 에피소드(예: [5,10,15])에서 잘못된 인덱스. 루프 인덱스 `i` 대신 `ep_num - 1` 사용.
- **Impact**: 역공학 프로젝트에서 벡터화 메타데이터 누락
- **Difficulty**: LOW
- **Previous**: NEW

### S01-03. Self-critic `final_arc` corrections are generated but never consumed
- **TF**: TF-1 (LLM interaction)
- **Severity**: IMPORTANT
- **File**: `modules/domain/agents/analyst.py:836-864`
- **Content**: 자기비평 LLM이 `final_arc` 필드에 수정본을 생성하지만, 코드는 항상 원본 `draft_result`만 사용. 수정본 무시됨.
- **Impact**: 자기비평의 수정 사항 낭비 — pass/fail 게이트로만 기능
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S01-04. `story_expander` silently produces empty Bible when LLM fails
- **TF**: TF-1 (LLM interaction)
- **Severity**: IMPORTANT
- **File**: `modules/core/stage0/story_expander.py:55-75`
- **Content**: 두 폴백 모델 모두 실패 시 `_call_llm`이 `""` 반환 → 빈 Bible 생성/저장. 사용자에게 성공 메시지 표시되지만 Bible 데이터 없음.
- **Impact**: 빈 Bible로 Stage 2 진행 시 품질 저하
- **Difficulty**: MEDIUM
- **Previous**: NEW

### S01-05. Double `input()` prompt in block extension and style analysis paths
- **TF**: TF-3 (UX)
- **Severity**: INSIGHT
- **File**: `modules/core/stage01_helpers.py:428+491`
- **Content**: 블록 확장/문체 분석 경로에서 Enter 2회 필요
- **Impact**: UX 불편
- **Difficulty**: LOW
- **Previous**: NEW

### S01-06. `_extract_npcs` may return dict instead of list
- **TF**: TF-1 (LLM interaction)
- **Severity**: INSIGHT
- **File**: `modules/core/stage0/reverse_expander.py:267-278`
- **Content**: LLM이 `{"npcs": [...]}` 래핑 반환 시 dict가 list 대신 저장됨
- **Impact**: 다운스트림 NPC 반복 실패 가능
- **Difficulty**: LOW
- **Previous**: NEW

### S01-07. `persist_to_vectordb` may create `VecMemory` with `lock=None`
- **TF**: TF-4 (Thread safety)
- **Severity**: INSIGHT
- **File**: `modules/core/stage0/reverse_expander.py:419`
- **Content**: `getattr(ctx.db, "_lock", None)` → VecMemory가 lock 없이 동작 가능
- **Impact**: 현재 단일 스레드라 낮음
- **Difficulty**: LOW
- **Previous**: NEW

## Summary: 0 CRITICAL, 4 IMPORTANT, 3 INSIGHT
