# OPUS_TF 추가플랜 실행 보고서 (2026-02-21)

> Codex + Opus TF 의견 채택, Gemini 기각. 17개 문서 전수 검토 후 즉시 실행 가능한 작업 5건 완료.

---

## 실행 결과 요약

| Step | 작업 | 파일 | 상태 |
|------|------|------|------|
| 1 | adversarial_self_play 시그니처 버그 수정 | `four_phase_arc_generator.py` | ✅ 완료 |
| 2 | Memory ROI P0-1 — 거리 기반 랭킹 | `vec_memory.py` | ✅ 완료 |
| 3 | Memory ROI P0-2 — 임베딩 실패 LIKE 폴백 | `vec_memory.py` | ✅ 완료 |
| 4 | Memory ROI P0-3 — 요약 정규화 | `stage4_post_processor.py` | ✅ 완료 |
| 5 | Memory ROI P0-4 — Config 상향 | `validation.yaml` | ✅ 완료 |

---

## Step 1: adversarial_self_play 시그니처 버그 (CRITICAL)

**문제**: `stage2_preflight.py:526`이 `adversarial_self_play=self.ctx.adversarial_self_play`를 전달하지만
`four_phase_arc_generator.py:451` `patch_arc_with_feedback()` 시그니처에 해당 파라미터 없음 → **TypeError 크래시**

**수정 내용**:
1. `patch_arc_with_feedback()` 시그니처에 `adversarial_self_play=None` 파라미터 추가
2. PASS 판정 후 ASP 교정 로직 추가 (generate() L338-349 패턴 재사용)
   - retry≥2 조건은 패치 모드에서 불필요 (PASS 시에만 적용)
   - tactical_doc 존재 확인 후 교체

**영향**: Stage 2 패치 모드 진입 시 크래시 방지. ASP 활성화 시 패치된 Arc에도 교정 적용.

---

## Step 2: Memory ROI P0-1 — 거리 기반 랭킹

**문제**: `retrieve_multi_query_context()` — 에피소드 번호 균등 간격 샘플링 → 유사도 높은 결과 버림

**수정 내용**:
- 정렬 기준을 `ep_num ASC` → `distance ASC` (유사도 우선)로 변경
- 다양성 보정: 연속 에피소드(±1) 중 더 먼(덜 유사한) 것 제거
- 결과: 유사도 높은 에피소드가 우선 선택되면서도 시간적 다양성 유지

---

## Step 3: Memory ROI P0-2 — 임베딩 실패 LIKE 폴백

**문제**: 임베딩 API 실패 시 빈 문자열 반환 → 메모리 블랙아웃 (과거 맥락 완전 소실)

**수정 내용**:
1. `_keyword_fallback_search()` 헬퍼 추가
   - 쿼리에서 2글자 이상 키워드 추출 (최대 5개)
   - `episode_meta` 테이블의 summary, event_types, entity_names 필드 LIKE 검색
2. `retrieve_high_res_context()`: 임베딩 실패 시 키워드 폴백 호출
3. `retrieve_multi_query_context()`: 모든 쿼리 임베딩 실패 시 키워드 폴백 호출

**영향**: 임베딩 API 장애 시에도 키워드 매칭으로 최소한의 맥락 제공.

---

## Step 4: Memory ROI P0-3 — 요약 정규화

**문제**: 요약 형식 비일관 (제목 | 사건 | 장면 ad-hoc 조합)

**수정 내용**:
- 4-슬롯 정규화: `사건: ... | 인물: ... | 장소: ... | 결말: ...`
- `_extract_state_change_info()` 산출물 활용 (이벤트, 엔티티)
- blueprint에서 scene_summary → 장소, cliffhanger/ending_hook → 결말 추출
- 빈 슬롯은 자동 제외

**영향**: 벡터 검색 시 구조화된 요약으로 매칭 품질 향상.

---

## Step 5: Memory ROI P0-4 — Config 상향

**변경**:
- `vector_max_results_s4`: 10 → 12 (+20%)
- `vector_max_results_s2`: 5 → 8 (+60%)

**근거**: Gemini 2.0 Pro의 대용량 컨텍스트(2M tokens) 여유 활용. 추가 2~3건의 과거 맥락이 연속성 품질에 기여.

---

## 검증 결과

| 검증 | 결과 |
|------|------|
| `py_compile` 4파일 | ✅ 전량 통과 |
| `pytest tests/ -q` | ✅ **2,213 passed, 68 xfailed** (기준선 일치) |
| `test_vec_memory.py` | ✅ 36 passed |
| `test_arc_patch_mode.py` | ✅ 7 passed |

---

## 미실행 항목

| 항목 | 사유 |
|------|------|
| Patch Retry Extension | 대형 작업 — 라인 재매핑 + 설계 필요. 별도 세션에서 착수 |
| Resume/Replay 멱등성 | 스키마 마이그레이션 의존 — 별도 세션 |
| Canon OS / Stage Canon Memory | 아키텍처 설계 선행 필요 — 별도 세션 |
