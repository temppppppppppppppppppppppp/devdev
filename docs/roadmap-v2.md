# 글도비 거시 로드맵 (메모)

작성일: 2026-03-17
상태: 초안 — 합의 후 확정

---

## 목표

글도비 2.0.0 = **"사후 평가 시 모순이 적은 퀄리티의 안정적 생산"** 공정 closure

closure 조건: Opus + Codex가 산출물 실물을 보고 평가, 상호 합의하에
**LLM 성능 제약 하 최선의 결과임을 95% 확신**할 수 있을 때.

---

## 트랙 구조

### 상시 트랙: 안정화

디버깅. 매일 하는 것. 별도 숙제로 취급.

- 런타임 버그 수정
- 크래시/복구 경로 점검
- 끊긴 루프 잔여 remediation
- 테스트 보강

코드 리팩토링(main_a.py 분리, 모듈 정리 등)은 **별개 숙제**로 분리.
안정화는 아래 Phase들과 항상 병렬 진행.

---

### Phase 1: 구조 개선 — "처음부터 잘 쓰게, 틀리면 잘 다시 쓰게"

핵심 전환:
- 기존 방향: 틀리면 Director가 수정 요청 → 고치게 만든다
- 보강 방향: **처음부터 잘 쓰게 만든다**
- 결합: **처음부터 잘 쓰게 + 틀리면 잘 다시 쓰게**

수단: 주요 LLM들의 정보 병목 제거. 정보 구조화·연결성·few-shot 보강.

#### 워크스트림 A: "처음부터 잘 쓰게" (입력 품질)

| 항목 | 대상 | 설명 |
|------|------|------|
| A-1 | CW 컨텍스트 계층화 | 진실(팩트시트/연속성) > 검색 > 참고자료 티어 분리 (Lane 1 방향) |
| A-2 | Blueprint→원고 정보 전달 | 블루프린트의 핵심 지시가 CW 프롬프트에 구조적으로 도달하는지 점검 |
| A-3 | Few-shot 보강 | 장르별 좋은 원고 예시를 CW 프롬프트에 삽입. 모방 기준 제공 |
| A-4 | StateTracker 정보 정확도 | CW에 전달되는 상태 정보(NPC, 위치, 시간, 재무)의 정합성 |

#### 워크스트림 B: "틀리면 잘 다시 쓰게" (판정·수정 품질)

| 항목 | 대상 | 설명 |
|------|------|------|
| B-1 | Director 판단 핵심 분리 | 판정 근거 / 참고자료 / 점수를 의미적으로 분리 (Lane 2 방향) |
| B-2 | Director→CW 피드백 구조화 | 수정 요청이 CW에 구체적·구조적으로 전달되는지 |
| B-3 | PASS_WITH_FIX 범위 축소 | 진짜 국소 수정만 허용, 나머지는 재생성 (Lane 3 방향) |
| B-4 | Retry 예산 명시화 | 라운드/수리/전략/에스컬레이션 축 정리 (Lane 3 방향) |

#### 병렬 가능성

```
워크스트림 A (입력 품질)          워크스트림 B (판정·수정 품질)
─────────────────────          ──────────────────────────
A-1 CW 컨텍스트 ──────┐        B-1 Director 판단 분리
A-2 BP→원고 전달       │ 병렬    B-2 Director→CW 피드백
A-3 Few-shot          │        B-3 PASS_WITH_FIX ─────── B-1 선행 필요
A-4 StateTracker      │        B-4 Retry 예산 ─────────── B-1 선행 필요
                      │
A-1 ←→ B-1 약한 의존 (컨텍스트 계층이 Director 입력에도 영향)
A-3은 독립적. 언제든 착수 가능.
```

---

### Phase 2: 모순 최소화 생산 공정 → v2.0.0 closure

Phase 1의 개선을 적용한 상태에서 실제 에피소드를 생산하고 평가.

- [ ] 모순 유형 분류 체계 확정 (연속성, 설정, 인과, 시공간, NPC 상태)
- [ ] 벤치마크 생산 런 실행 (최소 1개 작품, N에피소드 연속)
- [ ] Opus + Codex 교차 평가 — 산출물 실물 기반
- [ ] 발견된 모순 패턴 → Phase 1 워크스트림으로 피드백 (반복)
- [ ] 95% 확신 합의 도달 → **v2.0.0 태깅**

Phase 1과 Phase 2는 반복 루프:
```
구조 개선 → 생산 런 → 평가 → 모순 패턴 발견 → 구조 개선 → ...
                                                    ↓
                                          95% 확신 → v2.0.0
```

---

### Phase 3: 연출 퀄리티 개선 (v2.1.x~)

모순이 잡힌 공정 위에서 "읽는 맛" 개선.

- [ ] AI slop 제거 (상투적 표현, 반복 패턴)
- [ ] dialogue_ratio 동적 타겟
- [ ] 캐릭터 보이스 분화
- [ ] 페이싱/감정곡선 실전 반영
- [ ] 장르별 연출 특화

---

### Phase 4+: (향후)

- 멀티 LLM 백엔드
- 사용자 피드백 학습 루프
- 웹 서비스화 / API
- ...

---

## 별개 숙제 (Phase 무관, 비동기)

- main_a.py 모놀리스 분리
- 모듈 순환 의존 정리
- 미사용 파일/코드 정리
- Stage 2 병렬/순차 명확화
- FactLedger / StateTracker 이원화 정리

---

## 구조 개선 아이디어 풀 (브레인스토밍 2026-03-17)

코드 실물 분석 기반. 아이디어 확보용. 실행 시 재검증 필요.

### 발견된 핵심 병목

**병목 1: CW가 "왜 이렇게 써야 하는지" 모른다**
- Arc에서 설계한 power_changes, foreshadowing, hybrid_composition이 Stage 3~4에서 완전 소실
- CW는 "무엇을 쓸지"만 받고 "이 Arc가 전체 이야기에서 왜 이런 역할인지"를 모름
- 소실 경로: Arc.state_constraints → Stage 3 constraint_compiler가 operational만 추출 → strategic intent 탈락

**병목 2: Director 피드백이 CW에 도달할 때 60~80% 손실**
- `_extract_fix_feedback()`: fix_scope_reasoning → 300자 절삭, open_review → 300자 절삭
- `_build_retry_feedback_provenance()`: contradiction_details → 라인당 180자, 최대 3개, warnings → 상위 3개만
- `_join_unique_lines()`: 글자 수 limit=500
- 절삭 마크 없음 → CW는 잘린 줄도 모름
- 결과: "대략 뭔가 잘못됐다"만 알고 "정확히 뭘 어떻게"는 모름 → 고쳐도 같은 이유로 재REJECT

**병목 3: CW가 "좋은 원고가 뭔지" 기준이 없다**
- negative_example_injector ~40개 있으나 positive few-shot 0개
- reader satisfaction guide가 프롬프트 맨 끝(41번째 정보원) → LLM 간과
- 씬 페이싱 가이드 없음 ("균등 배분"만 존재)

### Arc→Blueprint→CW 정보 소실 지도

| 설계 의도 | Arc 필드 | Stage 3 도달 | Stage 4/CW 도달 |
|-----------|---------|-------------|----------------|
| 주인공 파워 여정 | power_changes | 미추출 | 소실 |
| 복선→회수 쌍 | foreshadowings | 미추출 | 소실 |
| 패턴 혼합 전략 | hybrid_composition | 미추출 | 소실 |
| 관계 변화 곡선 | relationship_changes | 요약 텍스트화 | 엔드포인트만 도달 |
| 상태 여정 전체 | state_constraints 계층 | arc_start_state만 | constraint_summary만 |
| NPC 사건 | state_changes | state_changes_summary | entity 컬렉션 도달 |
| 전술 문서 | tactical_doc | 에피소드별 추출 | reference anchor 도달 |
| 제약 요약 | constraint_summary | 캐시 | 직접 주입 도달 |

### 아이디어: 테마 A — 처음부터 잘 쓰게

**A-1. Arc 설계 의도 관통 파이프라인** [중 난이도]
- power_changes, foreshadowing, hybrid_composition을 Stage 3 constraint_compiler → Stage 4 CW 프롬프트까지 전달
- "이 화는 주인공이 약해지는 구간이다"를 CW가 알게 됨
- 수정 대상: constraint_compiler.compile(), stage4_context_builder.build_mandatory_context()

**A-2. Few-shot 성공 예시 주입** [소 난이도]
- 장르별 "잘 쓴 원고" 3~5개를 YAML/JSON으로 관리
- CW 프롬프트에 구조적 예시로 삽입
- 현재 negative만 있고 positive 0개 → 비대칭 해소

**A-3. 만족도 가이드 프롬프트 상위 이동** [소 난이도]
- reader satisfaction guide를 현재 맨 끝 → Blueprint 분석 직전(STEP 0)으로
- "이 화에서 반드시 보상 시점 1개 포함" — 톤 앵커 역할

**A-4. 씬 페이싱 자동 배분** [소 난이도]
- Blueprint 씬 수 + 중요도 기반 글자 수 배분 제안
- "Scene 1: 600자(셋업), Scene 3: 2,000자(클라이맥스)"
- CW에 구조적 가이드 제공

**A-5. Arc→에피소드 "목적 문장" 주입** [소 난이도]
- 각 에피소드에 1줄짜리 "이 화의 존재 이유" 생성
- "이 화는 주인공이 처음으로 패배를 인정하는 화다" → CW가 톤 잡는 앵커
- tactical_doc에서 추출하거나 Stage 3에서 생성

**A-6. CW 2단계 호출 (설계→집필)** [대 난이도]
- 1차 호출: Blueprint 분석 → 씬 페이싱 + 감정곡선 설계안 출력
- 2차 호출: 설계안 기반 실제 집필
- 환각 감소, 구조 향상. 단 비용 2배

**A-7. NPC 대사 샘플 뱅크** [중 난이도]
- character_voice_section에 실제 대사 예시 2~3개씩 추가
- "이 NPC는 이렇게 말한다" → 보이스 분화 촉진

### 아이디어: 테마 B — 틀리면 잘 다시 쓰게

**B-1. 피드백 절삭 한도 대폭 완화** [소 난이도, 즉효]
- 300자→1000자, 180자→500자
- 토큰 비용 미미 증가, 정보 도달률 대폭 상승

**B-2. 모순 구조화 전달** [중 난이도]
- Director의 contradiction_details를 텍스트가 아닌 구조화된 JSON으로 CW에 전달
- 유형/심각도/위치/수정방향 명시

**B-3. 재시도 횟수별 피드백 에스컬레이션** [소 난이도]
- 1회차: 요약 피드백
- 2회차: 상세 피드백
- 3회차+: 절삭 없이 전문 전달 + 구체적 수정 지시 강화

**B-4. Director→CW "수정 지시서" 포맷** [중 난이도]
- 현재 자유 텍스트 피드백 → 구조화된 수정 지시서
- `[CRITICAL 수정]` `[MAJOR 수정]` `[MINOR 참고]` 계층으로 CW가 우선순위 인지

**B-5. 피드백 손실 감사 로그** [소 난이도]
- 절삭 전/후 비교 기록
- "Director가 1,200자 보냈는데 CW에 400자 도달" → 병목 정량 추적

### 아이디어: 테마 C — A+B 교차

**C-1. Director 사전 검토 (Pre-flight Director)** [대 난이도]
- 원고 생성 전에 Director가 Blueprint + Context를 검토
- "이 조건이면 여기서 틀릴 것 같다" 사전 경고 → CW가 함정을 미리 앎

**C-2. 실패 패턴 DB → CW 사전 주입** [중 난이도]
- 과거 REJECT 사유를 장르/에피소드 유형별로 축적
- "이런 상황에서 자주 틀리니 주의" 형태로 CW에 사전 전달

**C-3. 연속성 체크포인트 양방향화** [소 난이도]
- 현재: CW가 쓰고 → Director가 검사
- 개선: CW 프롬프트에 자체 체크리스트 삽입
- "쓰기 전에 확인: 사망 NPC, 미습득 아이템, 시간대" → 1차 오류 사전 차단

### 우선순위 제안 (임팩트 × 난이도)

즉시 착수 가능 (소 난이도, 고 효과):
1. B-1 피드백 절삭 한도 완화
2. A-3 만족도 가이드 위치 이동
3. A-5 에피소드 목적 문장 주입
4. B-3 재시도 횟수별 에스컬레이션
5. C-3 CW 자체 체크리스트 삽입

중기 (중 난이도, 고 효과):
6. A-1 Arc 설계 의도 관통
7. B-2 + B-4 모순 구조화 + 수정 지시서 포맷
8. A-2 Few-shot 성공 예시
9. C-2 실패 패턴 DB

장기 (대 난이도, 고 효과):
10. A-6 CW 2단계 호출
11. C-1 Pre-flight Director

---

## 다음 테마: 절삭 하드코딩 전수조사

Gemini는 컨텍스트 한도가 크므로 기존 절삭 하드코딩의 존재 이유가 없다.
파이프라인 전체에서 `[:N]`, `[:limit]`, `max_items`, `line_limit` 등 하드코딩된 절삭을 전수조사하여
불필요한 정보 손실을 제거한다.

### 전수조사 결과 (2026-03-17, 코드베이스 전체)

총 300건+ 하드코딩 절삭 발견. LLM 프롬프트 경로에 직접 영향을 주는 것 중심으로 분류.

#### 카테고리 1: Director↔CW 피드백 경로 (정보 손실 최심각)

| 파일 | 위치 | 절삭 | 한도 | 영향 |
|------|------|------|------|------|
| stage4_interview_round.py | `_compact_text()` | open_review | **300자** | Director 자유 리뷰 60%+ 손실 |
| stage4_interview_round.py | `_compact_text()` | reason, verdict_reason, selection_reason | **500자** | 판정 근거 절삭 |
| stage4_interview_round.py | `_compact_text()` | runtime_advisory, retry_directives | **500자** | 재시도 지시 절삭 |
| stage4_interview_round.py | `_compact_contradiction_detail_lines()` | 모순 세부 | **3개, 줄당 180자** | 4번째 이후 모순 완전 소실 |
| stage4_interview_round.py | 재시도 모드 | 모순 세부 | **2개, 줄당 120자** | 더 심한 절삭 |
| stage4_interview_round.py | fix suggestion | 수정 제안 | **120자** | 수정 방향 절삭 |
| stage4_interview_round.py | `_collect_validation_warning_lines()` | 검증 경고 | **20개, 개당 180자** | 경고 상세 손실 |
| stage4_interview_round.py | 구조화된 검증 증거 | NPC 필드/expected/found | **40/60/60자** | 필드값 절삭 |
| stage4_interview_round.py | 수치/커버리지/진실게이트 경고 | 개별 warning | **160자** | 경고 상세 절삭 |
| stage4_interview_round.py | action_items | 행동 항목 리스트 | **20개** | (비교적 여유) |

#### 카테고리 2: CW 입력 컨텍스트 (처음부터 잘 쓰게에 직결)

| 파일 | 대상 | 한도 | 비고 |
|------|------|------|------|
| stage4_context_builder.py | World state summary | **50,000자** | 3곳에서 동일 한도 |
| stage4_context_builder.py | Fact ledger summary | **25,000자** | 3곳에서 동일 한도 |
| stage4_context_builder.py | Tier 2 EP summary | **5,000자** | 에피소드 요약 |
| stage4_context_builder.py | Tier 3 Arc summary | **8,000자** | 아크 요약 |
| stage4_context_builder.py | NPC 상태 desc | **200자** | NPC 설명 절삭 |
| stage4_context_builder.py | NPC history entry | **100자** | 이력 엔트리 절삭 |
| stage4_context_builder.py | Scene snippet | **300자** | 씬 조각 |
| stage4_context_builder.py | Tactical doc query | **1,800자** | 전술 문서 |
| stage4_context_builder.py | Relation slice | **560자** | 관계 컨텍스트 |
| stage4_interview_round.py | Relation slice | **420자** | 관계 컨텍스트 |
| stage4_interview_round.py | Manuscript snippet | **500자** | 과거 원고 조각 |
| stage4_orchestrator.py | World state (폴백) | **8,000자** | 폴백 경로 더 심한 절삭 |
| stage4_orchestrator.py | Fact ledger (폴백) | **5,000자** | 폴백 경로 더 심한 절삭 |
| context_advisor.py | Query slots | **stage별 5/6/8개** | 검색 슬롯 수 제한 |

#### 카테고리 3: Director 입력 컨텍스트

| 파일 | 대상 | 한도 | 비고 |
|------|------|------|------|
| director_ensemble.py | mandatory context | **400,000자** | 설정 가능하나 기본값 |
| director_ensemble.py | candidate evidence | **220,000자** | 설정 가능 |
| director_ensemble.py | reference appendix | **120,000자** | 설정 가능 |
| director_ensemble.py | manuscript in prompt | **6,000자** | 직접 [:6000] |
| director_ensemble.py | blueprint in prompt | **5,000자** | 직접 [:5000] |
| director_continuity.py | content | **15,000자** | 연속성 검사 |
| director_continuity.py | current_manuscript | **36,000자** | 연속성 검사 |
| director_auditor.py | manuscript | **12,000자** | 감사 프롬프트 |

#### 카테고리 4: Stage 2/3 (Arc/Blueprint 생성)

| 파일 | 대상 | 한도 |
|------|------|------|
| stage2_preflight.py | relation slice | **420자** |
| stage2_preflight.py | fact_ledger context | **10개 항목** |
| stage3_orchestrator.py | relation slice | **420자** |
| stage3_orchestrator.py | relationship history | **3개 레코드** |
| arc_ensemble.py | vol_strategy, assets | **6,000자** |
| arc_ensemble.py | feedback | **9,000자** |
| arc_corrector.py | arc JSON | **3,000자** |
| arc_corrector.py | context | **1,000자** |
| arc_critic.py | arc JSON | **18,000자** |
| arc_critic.py | constraints | **9,000자** |
| continuity_arc.py | tactical_doc | **50,000자** |
| continuity_arc.py | last_ep_content | **4,000자** |
| blueprint_ensemble.py | arc_focus | **15,000자** |

#### 카테고리 5: 보조 검증 LLM (advisor/validator)

| 파일 | 대상 | 한도 | 비고 |
|------|------|------|------|
| info_paradox_checker.py | manuscript | **4,000자** | 정보 역설 검사 |
| truth_gate.py | manuscript | **3,000자** | 진실 게이트 |
| long_term_repetition_advisor.py | manuscript | **3,000자** | 반복 감지 |
| relationship_drift_advisor.py | manuscript | **4,000자** | 관계 드리프트 |
| npc_drift_advisor.py | manuscript | **4,000자** | NPC 드리프트 |
| advisory_validator.py | manuscript | **1,500자** | 자문 검증 |
| semantic_plot_guard.py | plot text | **2,000자** | 플롯 가드 |

#### 카테고리 6: CW 원고 패칭

| 파일 | 대상 | 한도 |
|------|------|------|
| chief_writer.py | original_manuscript (패치용) | **150,000자** (head 20,000) |
| critic.py | manuscript | **80,000~100,000자** |
| analyst.py | draft_contents | **200,000자** (head 40K + tail 160K) |

#### 카테고리 7: Stage 0 역설계

| 파일 | 대상 | 한도 |
|------|------|------|
| reverse_expander.py | genre sample | **6,000자** |
| reverse_expander.py | protagonist sample | **8,000자** |
| reverse_expander.py | NPC sample | **10,000자** |
| reverse_expander.py | world sample | **6,000자** |
| reverse_expander.py | episode bible | **10,000자** |
| reverse_expander.py | draft per sample | **2,000자** |
| story_expander.py | concept text | **4,000자** |

#### 카테고리 8: Bridge/Runner (lite_mode, test_mode)

| 파일 | 대상 | 한도 |
|------|------|------|
| runner.py | context trimming | **80,000 bytes** |
| runner.py | fallback context | **150,000 bytes** |
| runner.py | file chunk | **1,500~2,000자** |
| state_ledger.py | state summary | **3,000자** |

#### 카테고리 9: 안전 게이트 (1M 천장)

| 파일 | 한도 | 비고 |
|------|------|------|
| base_agent.py | MAX_CONTEXT_CHARS | 초과 시 notice 삽입 후 절삭 |
| stage2_finalizer.py | 1M | arc history 게이트 |
| stage3_orchestrator.py | 1M | manuscript 게이트 |
| director_continuity.py | 1M | 컨텍스트 게이트 |
| preflight_checker.py | 200K | 하드 게이트 |
| four_phase_arc_generator.py | 200K | 하드 게이트 |
| blueprint_ensemble.py | 400K | 안전 게이트 |

#### 카테고리 10: DB 쿼리 제한

| 파일 | 대상 | 한도 |
|------|------|------|
| db_manager.py | causal_summary_chain | **5개** |
| db_manager.py | context_manuscripts | **3개** |
| db_manager.py | manuscript_excerpts | **10개 × 200자** |
| db_manager.py | npc_history | **50개** |
| stage4_context_builder.py | npc_history (호출 시) | **3개** |
| stage4_context_builder.py | relationship_history | **5개** |

### 즉시 조치 가능 (Gemini 컨텍스트 여유 감안)

**1순위 — 피드백 경로 (카테고리 1):**
- 300자/500자 절삭 → 제거하거나 대폭 완화 (Gemini 1M 토큰 기준 불필요)
- 모순 3개/2개 제한 → 제거
- line_limit 180/120 → 제거하거나 1000+

**2순위 — CW 입력 컨텍스트 (카테고리 2):**
- NPC desc 200자, history 100자 → 대폭 완화
- relation slice 420/560자 → 수천 자로
- manuscript snippet 500자 → 수천 자로

**3순위 — 보조 검증 LLM (카테고리 5):**
- manuscript 3,000~4,000자 → 원고 전문 또는 대폭 확대
- 이들은 별도 LLM 호출이므로 개별 비용 고려 필요

**유지 권장 — 안전 게이트 (카테고리 9):**
- 1M 천장 게이트는 API 오류 방지용이므로 유지
- 다만 200K/400K 게이트는 Gemini 기준 보수적 → 재검토 가능

---

## 테마 D: Stage 2→3→4 정보 소실 복구

Arc(Stage 2)에서 설계한 전략적 의도가 CW(Stage 4)에 도달하기 전 소실되는 문제.
근본 원인: BlueprintConstraintCompiler가 operational 제약만 추출하고 strategic intent는 버림.

### 소실 필드 목록

| 필드 | Arc 모델 위치 | 내용 | 소실 지점 | CW 영향 |
|------|-------------|------|----------|---------|
| **power_changes** | state_constraints.power_changes | start_power, end_power, growth_justification | S2→S3 constraint_compiler | CW가 파워 스케일링 근거 없이 집필. 비약적 성장/약화 발생 |
| **foreshadowings** | state_constraints.foreshadowings[] | id, type, description, expected_payoff | S2→S3 constraint_compiler | 의도된 복선 심기 불가. 사후 auto-detect에 의존 (반응적) |
| **hybrid_composition** | ArcData.hybrid_composition | primary, secondary[], mixing_logic | S2→S3 constraint_compiler | CW가 패턴 혼합 전략 모름. 톤 급변 발생 가능 |
| **relationship_changes** | state_constraints.relationship_changes[] | target, from/to_state, trigger, justification | S2→S3 constraint_compiler | CW가 관계 변화를 발명함 (Arc 계획과 무관하게) |
| **state_constraints 전체 계층** | state_constraints.* | arc_start/end_state, items, checkpoints, investment_calc | S3→S4 파이프라인 | CW가 HUD 재구성에 의존 (2차 휴리스틱, 비권위적) |

### 현재 CW가 대신 쓰는 것 (취약한 대체재)

- power_changes → 없음. 완전 맹목
- foreshadowings → ForeshadowTracker.auto_detect_from_manuscript() (원고 텍스트에서 역추적, 누락/중복 발생)
- hybrid_composition → 없음. 완전 맹목
- relationship_changes → CW가 직접 생성 (Arc 계획과 충돌 가능)
- state_constraints → HUD tracking + NPC roster 추출 (단편적, 비권위적)

### 복구 방안

**즉시 가능 (constraint_compiler + chief_writer_context 수정):**
1. foreshadowings → constraint_block에 추가. ForeshadowTracker가 Arc 원본 사용하도록 연결
2. hybrid_composition → constraint_block에 추가. CW에 "[Arc 패턴: 복수(주) + 성장(부)]" 주입
3. state_constraints → Stage 4에 직접 전달. CW가 권위적 상태 소스 확보

**중기 (추가 설계 필요):**
4. power_changes → inherited_state에 포함. "이 화에서 파워 30→45 예상" 가이드
5. relationship_changes → constraint_block에 타임라인 형태로. "이 화에서 A↔B: 동맹→적대 전환"

### 수정 대상 파일

- `modules/domain/agents/blueprint_constraint_compiler.py` — compile()에 5개 필드 추출 추가
- `modules/domain/agents/chief_writer_context.py` — build_common_context()에 섹션 추가
- `modules/core/stage4_interview_round.py` — state_constraints를 CW kwargs에 전달
- `modules/domain/agents/chief_writer.py` — generate_ensemble() 시그니처에 파라미터 추가

---

## 테마 G: Director 사전 경고 체계

CW 1차 시도에 과거 실패 패턴을 사전 주입하는 체계.

### 현재 상태: 95% 준비됨

**이미 존재하는 인프라:**
- `failure_learning.py` — FailureLearner 클래스. 17개 실패 카테고리 분류 체계:
  - 연속성: ITEM_DUPLICATE, ITEM_MISSING, STATE_DISCONTINUITY, TIMELINE_ERROR
  - 구조: SCOPE_OVERFLOW, BLUEPRINT_MISMATCH, MISSING_SCENE
  - 캐릭터: RELATIONSHIP_JUMP, CHARACTER_OOC, VILLAIN_STUPIDITY
  - 서사: FREE_POWERUP, DEUS_EX_MACHINA, PACING_ISSUE
  - 기술: JSON_ERROR, LENGTH_ERROR
- `generate_constraint_prompt(stage=N)` — 실패 빈도 기반 제약 프롬프트 자동 생성
- `pass_rate_monitor.py` — AttemptRecord 저장 (reject_reason, reject_bucket, error_category, score_breakdown). 최대 1,000건 영속

**Stage 2에서는 이미 사용 중:**
- `stage2_preflight.py` ~L591: `failure_learner.generate_constraint_prompt(stage=2)` → Analyst에 주입
- 매 시도(1차 포함)에 적용

**Stage 4에서는 사용 안 됨 (핵심 갭):**
- `stage4_interview_round.py` `_build_common_writer_kwargs()` — failure_constraints 미포함
- CW 1차 시도 시 `failure_constraints=""` (빈 문자열)
- **재시도 시에만** 직전 rejection 사유가 전달됨 (과거 축적 패턴은 아님)

### 수정 방안

**즉시 가능 (8줄 코드):**
- `stage4_interview_round.py`의 `_build_common_writer_kwargs()`에 추가:
  ```
  if self.ctx.failure_learner:
      _learned = self.ctx.failure_learner.generate_constraint_prompt(stage=4)
  _common_writer_kwargs["failure_constraints"] = _learned
  ```
- Stage 2 패턴 그대로 복사. 새 LLM 호출 0회. 비용 0원.

**확장 가능 (선택적):**
- Arc 위치별 가중치: "초반 Arc에서는 RELATIONSHIP_JUMP가 빈번, 클라이맥스에서는 STATE_DISCONTINUITY 빈번"
- 임계값 경고: 특정 카테고리 5회 초과 시 ESCALATE
- Director 사전 검토 UI (고급, 장기)

### 기대 효과

- REJECT→재시도 사이클 15~25% 감소 추정 (Stage 2 적용 실적 기반)
- CW가 "자주 틀리는 패턴"을 1차부터 회피
- 추가 비용 0원 (로컬 데이터만 사용)

### 수정 대상 파일

- `modules/core/stage4_interview_round.py` — `_build_common_writer_kwargs()` 8줄 추가

---

## 테마 H: 보조 검증 LLM 원고 절삭 문제

Stage 4 advisory 체인의 보조 검증 LLM들이 원고 일부만 보고 판단하는 문제.

### 검증기별 현황

| 검증기 | 파일 | 한도 | 5,000자 대비 가시율 | 사각지대 | 모델 |
|--------|------|------|-------------------|---------|------|
| InfoParadoxChecker | info_paradox_checker.py:176 | 4,000자 | 80% | 후반 정보 역설 | Director 콜백 |
| TruthGate | truth_gate.py:407 | 3,000자 | 60% | 후반 세계법칙 위반 | Director 콜백 |
| LongTermRepetitionAdvisor | long_term_repetition_advisor.py:170 | 3,000자 | 60% | 후반 반복 패턴 | Director 콜백 |
| RelationshipDriftAdvisor | relationship_drift_advisor.py:100 | 4,000자 | 80% | 결말부 관계 급변 | Director 콜백 |
| NpcDriftAdvisor | npc_drift_advisor.py:122 | 4,000자 | 80% | 후반 NPC 속성 변이 | Director 콜백 |
| SemanticPlotGuard | semantic_plot_guard.py:96 | 2,000자 | 40% | 트위스트 차별화 | 임베딩 API |
| AdvisoryValidator | advisory_validator.py:128 | 1,500자 | 30% | 결말 표현 품질 | gemini-2.5-flash |

### 핵심 문제

- **원고 타겟 5,000자+ 중 후반 40~70%가 검증 사각지대**
- 클라이맥스, 결말, 클리프행어 = 원고 후반부 = 가장 중요한 부분이 안 보임
- 특히 AdvisoryValidator(1,500자/30%)와 SemanticPlotGuard(2,000자/40%)가 심각

### 놓치는 오류 유형

- 결말부 정보 역설 (주인공이 아직 모르는 정보 사용)
- 클라이맥스에서의 세계법칙 위반 (금지된 능력 사용)
- 결말부 NPC 속성 급변 (무적의 검객이 갑자기 무력)
- 동기 없는 관계 반전 (마지막 장면에서 갑자기 화해)
- 결말 표현의 상투성 (가장 중요한 부분에서 AI slop)

### 수정 방안

**1순위 — 절삭 제거 (4개 검증기):**
- InfoParadoxChecker, TruthGate, RelationshipDriftAdvisor, NpcDriftAdvisor
- `smart_truncate(manuscript, 4000)` → 원고 전문 전달
- 비용 증가: 에피소드당 ~2~3센트 USD (토큰 2.5배 증가, Director 콜백이므로 Flash급)

**2순위 — 한도 확대 (2개 검증기):**
- AdvisoryValidator: 1,500자 → 3,000자+ (Flash 모델이므로 비용 미미)
- SemanticPlotGuard: 2,000자 → 전문 (임베딩 비용 고정)

**유지 가능 — LongTermRepetitionAdvisor:**
- ep≥20에서만 작동, Python 사전 탐지가 주력, 3,000자로도 충분 가능

### 비용 영향

- 현재: advisory 체인 7~8회 호출 × 1~1.2K 토큰 = 에피소드당 ~8~10K 토큰
- 전문 전달 시: 7~8회 × 2.5~3K 토큰 = ~18~24K 토큰 (+100~150%)
- 실비: 에피소드당 +2~3센트. 생산 품질 대비 무시 가능

### 수정 대상 파일 (각 1줄)

- `modules/core/info_paradox_checker.py:176`
- `modules/core/truth_gate.py:407`
- `modules/core/relationship_drift_advisor.py:100`
- `modules/core/npc_drift_advisor.py:122`
- `modules/validation/advisory_validator.py:128`
- `modules/core/semantic_plot_guard.py:96`

---

## 테마 I: Taxonomy 뉘앙스 손실 + 중간단계/CoT 소실

### Part 1: Taxonomy — 분류 체계에서의 뉘앙스 손실

LLM이 생산한 풍부한 출력이 이산 카테고리로 매핑되면서 신호가 소실되는 지점들.

#### 발견된 분류 체계 10개

**1. FailureCategory (17개 enum)** — failure_learning.py
- 입력: "아이템 중복 획득 + 위치 + 심각도 + 수정 난이도" (자유 텍스트)
- 출력: `ITEM_DUPLICATE` (단일 카테고리)
- 손실: 심각도 스펙트럼, 수정 난이도, 맥락(주인공 vs NPC vs 세계), 빈도 패턴
- False bin: "부상 자연치유", "부상 악화 불일치", "부상 언급 소실" → 전부 STATE_DISCONTINUITY

**2. RejectBucket (3개)** — stage4_interview_round.py:317-328
- constraint_violation, structure_error, **quality_issue (catch-all)**
- 키워드 substring 매칭 기반 → 70%가 quality_issue로 분류
- 손실: quality_issue 안에 문체/보이스/감정/몰입/장르/주제 5개+ 하위 원인 뭉침
- False positive: "constraint: 대화가 지루함" → constraint_violation로 오분류 (실제는 품질)

**3. Director Verdict (3-state)** — response_schemas.py
- PASS / PASS_WITH_FIX / REJECT
- 손실: 87점 borderline pass와 95점 solid pass 구별 불가
- 손실: 수정 소요 시간 추정 (15분 vs 4시간) → 같은 PASS_WITH_FIX
- 손실: 수렴 가능성 ("이 패치는 성공할 것" vs "루프 빠질 위험") 미반영

**4. fix_scope (4-state)** — director_ensemble.py:76-78
- inplace / partial / full / none (폴백)
- normalize: LLM이 "local", "patch" 등 반환 시 → "none"으로 폴백 (의도 소실)
- partial이 30분~4시간 범위를 커버 → 구분 불가

**5. Scoring Threshold (이진화)** — validation_orchestrator.py
- 72점 PASS / 69점 FAIL (3점 차이에 운명 갈림)
- 손실: 점수 분포 형태 (균일 vs 극단적 편차) → 같은 합산점
- 한계: marginal 케이스 [72, 71, 68, 69, 75, 70, 69] 진동 → 이진 뷰에서 안 보임

**6. Prompt Weighting (10개 카테고리)** — dynamic_prompt_weighting.py
- 실패 키워드 → 프롬프트 가중치 카테고리 매핑
- 오분류: "대화 품질 저하로 관계가 비현실적" → RELATIONSHIP (실제는 DIALOGUE 문제)
- 결과: 잘못된 차원 강화 (관계 드라마 증가 vs 대화 자연스러움 개선)

**7. Quality Gate Override (이진)** — director_ensemble.py:338-372
- force_reject / force_pass_with_fix → ON/OFF만
- 손실: 확신도 ("60% 확신 REJECT" vs "확정 REJECT") 미반영
- 손실: Director가 PASS 줬는데 Gate가 REJECT → 왜 불일치인지 기록 없음

**8. Gate Basis Attribution (6개)** — director_ensemble.py:81-97
- continuity_firewall, quality_floor_fail, director_primary_pass, ...
- 복합 개입 시 1개만 기록: Director PASS + Firewall 트리거 + Gate REJECT → "continuity_firewall"만
- 손실: 3개 시스템이 다른 차원에서 우려했다는 복합 신호

**9. ForeshadowStatus (5-state)** — foreshadow_tracker.py
- planted / hinted / payoff / overdue / abandoned
- 손실: overdue 내 "수정 가능 지연" vs "구조적 영구 미회수" 구분 불가
- 손실: abandoned 이유 (스토리 변경? 너무 미묘?) 미기록

**10. ErrorCategory (9개)** — error_helper.py
- 문자열 매칭 기반: "timeout" → API_TIMEOUT
- 손실: 네트워크 타임아웃 vs LLM thinking 타임아웃 vs IO 오진단 → 같은 버킷

#### Taxonomy 교차 문제

- **키워드 매칭 취약**: LLM 표현 변형에 민감 ("아이템 중복" vs "중복 아이템" vs "재획득")
- **Catch-all 블랙홀**: UNKNOWN, quality_issue가 전체의 70%+ 흡수 → 학습 불가
- **경계값 민감도**: 3점 차이에 PASS/FAIL 전환, 신뢰구간 없음
- **폴백 기본값 함정**: 누락 → "none"/"100%" 등 기본값 → 불확실성 은폐

---

### Part 2: 중간단계(Intermediate Steps) 소실

파이프라인 각 단계에서 생산된 중간 산출물이 다음 단계에 전달되지 않거나 압축/폐기되는 지점들.

#### 1. LLM Thinking 토큰 소실 — base_agent.py

- thinking_level="high"로 생성된 Director 추론 → `_last_thinking` 필드에 5,000자 저장
- **Director만 로깅에 사용**. CW, Architect 등 후속 에이전트에 전달 안 됨
- 재시도 시 Director가 이전에 왜 그렇게 판단했는지 CW가 모름

#### 2. 앙상블 낙선 후보 완전 폐기 — arc/blueprint/chief_writer ensemble

| 단계 | 후보 수 | 보존 | 폐기 |
|------|---------|------|------|
| Arc (Stage 2) | 3개 | 1등 arc만 | 2~3등의 _score, _issues, 전략 근거 |
| Blueprint (Stage 3) | 3개 | 1등 blueprint만 | 전략명, qualified 여부, scene_count |
| Manuscript (Stage 4) | 3개 | Director 선택 1개 | 나머지 2개의 강점/약점, 품질 메트릭 |

- 낙선 후보의 비교 분석(comparison_notes) → 240자로 절삭 후 로깅만
- 왜 특정 전략이 반복적으로 낮은 점수를 받는지 학습 불가

#### 3. JSON 파싱 시 미등록 필드 무음 폐기 — base_agent.py:1666-1786

- `_extract_json_robust()`: 스키마에 없는 키는 무시
- LLM이 `"internal_reasoning"`, `"considered_alternatives"` 등 자발적으로 생성해도 → 사라짐
- 경고/로그 없이 drop

#### 4. Stage 3→4 핸드오프: Blueprint 선택 근거 미전달

- Stage 3 Director가 blueprint를 선택한 이유(comparison_notes, contradictions) → Stage 4에 미전달
- CW는 "왜 이 blueprint가 선택됐는지" 모름
- blueprint의 약점(Director가 우려했던 부분)도 모름

#### 5. 상태 추출 신뢰도 미보존 — state_extractor.py

- LLM이 Arc에서 상태를 추출할 때의 추론 과정 → 최종 JSON만 보존
- 추출 신뢰도(confidence) 필드 없음
- Python 폴백 발동 시에도 기록 없음 → 상태가 권위적 사실로 취급됨

#### 6. Validation 계층별 상세 → 이진 결과로 붕괴 — validation_orchestrator.py

| 계층 | 생산 | 보존 | 소실 |
|------|------|------|------|
| PreLLM (9개 검사) | 검사별 상세 경고 | score_deduction (-1) | 어떤 검사가 실패했는지 |
| Continuity | 위반별 상세 dict | 위반 리스트 요약 → 감점 | 위반 유형별 구체 내용 |
| Blocking | entity/scene/consistency 상세 | 실패 건수만 | 어떤 타입 blocking 실패인지 |
| Scoring (6차원) | 차원별 LLM 근거 | {차원: {score, max}} | 차원별 "왜 이 점수인지" |
| Advisory | 제안 리스트 (N개) | 제안 건수만 | 실제 제안 내용 |

- 최종: `final_decision + feedback(한 줄)` → 모든 계층 상세 소실

#### 7. 연속성 검증 6단계 CoT → PASS/REJECT — continuity_*.py

- 프롬프트에 Step 1~6 체계적 분석 요구
- LLM이 단계별 추론 생산
- 보존: 최종 PASS/REJECT + severity만
- 소실: Step 1~5 중간 추론, 각 항목별 통과/실패 이유, 경계 케이스 감지, 수정 가능성 판단

#### 8. ToT 탐색 경로 — tree_of_thoughts.py:250-261

- 3개 경로 탐색 → best_path.output만 반환
- paths[1], paths[2]의 reasoning, strengths, weaknesses → 소실
- 어떤 접근이 왜 실패하는지 학습 불가

#### 9. Scoring Validator 차원별 근거 — scoring_validator.py:135-166

- 6개 차원: character_consistency, emotion_arc, dialogue_quality, commercial_appeal, pattern_diversity, reader_satisfaction
- 각 차원에 LLM 근거 생산
- 보존: `{dimension: {score, max_score}}`만
- 소실: "왜 이 점수인지" 텍스트 근거

---

### 종합: 개선 방향

#### 즉시 가능 (구조 변경 없이)

| 항목 | 방안 | 파일 |
|------|------|------|
| Thinking 전파 | Director thinking → retry 시 CW에 전달 | stage4_interview_round.py |
| JSON 미등록 필드 보존 | `_extra_fields` dict로 캡처 + 로깅 | base_agent.py |
| RejectBucket 세분화 | quality_issue를 5개 하위 카테고리로 분할 | stage4_interview_round.py |
| fix_scope 폴백 방지 | "local"/"patch" 등 동의어 매핑 추가 | director_ensemble.py |

#### 중기 (로깅/저장 확장)

| 항목 | 방안 |
|------|------|
| 낙선 후보 메타데이터 보존 | 3개 후보 전부 score + strategy + issues를 JSONL에 기록 |
| Validation 계층별 상세 보존 | per-tier verdict + 상위 3개 상세를 Director에 전달 |
| 상태 추출 신뢰도 | extraction_confidence 필드 추가 |
| Scoring 차원별 근거 | per-dimension reasoning을 Director feedback에 포함 |

#### 장기 (아키텍처 변경)

| 항목 | 방안 |
|------|------|
| 경계값 연속화 | 72점 이진 → confidence band (65~75 = "marginal" 구간) |
| 복합 gate_basis | 단일 → 복수 intervention 기록 |
| 후보 간 강점 병합 | 낙선 후보의 우수 부분을 선택 후보에 반영하는 merge 단계 |
| 학습 피드백 루프 | 축적된 taxonomy + CoT 데이터 → 실패 패턴 자동 인식 |

---

## 테마 J: 비용/지연 — LLM 호출 패턴과 중복

### 에피소드당 LLM 호출 추정

- 클린 패스: **15~25회** / 재시도 포함 시: **25~40회**
- Advisory 체인: 9개 검증기 병렬 (TruthGate, NpcDrift, NumericDrift, Flashback, InfoParadox, RelDrift, LongTermRep, NumericConsistency, StyleSignal)
- Director: 비교+판정에 3~5회 (thinking_level="high")
- Director 감사: 1~2회
- Post-select 충돌검사: 1~2회

### 발견된 중복

**1. 9개 advisory가 같은 원고를 독립적으로 재분석**
- stage4_interview_round.py:4600 — 9개 스레드가 각각 LLM 콜백
- TruthGate(사실 검증), NumericDrift(수치 검증), InfoParadox(정보 역설) 등이 겹치는 상태 분석을 각각 수행
- 공유 가능한 중간 분석(상태 변화 추출 등)이 9번 반복

**2. Director가 advisory 결과 위에 다시 전문 분석**
- advisory 9회 + Director 비교 1회 = 같은 원고 10회 분석
- Director는 advisory 경고를 받지만 독립 판단도 수행

**3. NumericDrift + NumericConsistency 중첩**
- 둘 다 수치 속성 분석, 별도 병렬 태스크로 실행

### 모델 라우팅 문제

- Director 앙상블 비교에 thinking_level="high" (Pro 모델) 사용 — 사전 채점된 후보 비교는 Flash+medium으로 충분 가능
- Advisory 9개가 각각 독립 LLM 콜백 — 단일 멀티체크 프롬프트로 통합 가능
- 응답 캐시: 프롬프트 캐시만 있고 응답 메모이제이션 없음 → 재시도 시 동일 후보 재평가

### 개선 방향

| 항목 | 방안 | 절감 추정 |
|------|------|----------|
| Advisory 통합 | 9개 개별 호출 → 단일 멀티체크 프롬프트 | -30~40% 호출 |
| Director 비교 모델 다운그레이드 | Pro high → Flash medium | -50% 비교 비용 |
| 응답 메모이제이션 | 동일 후보셋 재판정 시 캐시 | 재시도당 -5~10회 |
| Advisory 중간결과 공유 | 상태 추출 1회 → 9개가 공유 | 추출 중복 제거 |

---

## 테마 K: 장기 연재 품질 열화

에피소드 수 증가에 따라 품질이 구조적으로 열화하는 메커니즘.

### 열화 임계점 맵

| 컴포넌트 | 안전 구간 | 경고 구간 | 위험 구간 | 메커니즘 |
|----------|----------|----------|----------|----------|
| 컨텍스트 윈도우 Tier1 (전문) | 1~30화 | 31~59화 | **60화+** | Tier2(요약 5K/화), Tier3(아크요약 8K)으로 전환 |
| NPC 가시성 | <30명 | 30~50명 | **50명+** | WorldState/FactLedger 표시 상한 30명(alive)/20명(dead) |
| FactLedger 이력 | <100건 | 100건 | **100건+** | FIFO로 초기 사실 소실 (MAX_HISTORY_PER_ENTITY=100) |
| Advisory 샘플링 | 전체 | 샘플링 | **베이스라인 소실** | NumericDrift MAX_HISTORY_POINTS=20 → 100건 중 20개만 표시 |
| 정보 역설 감지 (reveals) | <300개 | 300~500개 | **500개+** | MAX_REVEALS=500 초과 시 FIFO로 초기 지식 소실 |
| 관계 추적 | <20쌍 | 20쌍 | **20쌍+** | MAX_PAIRS=20, 나머지 쌍 advisory 미커버 |
| 반복 탐지 윈도우 | 최근 20화 | - | **25화+ 주기** | 20화 윈도우 → 25화 이상 매크로 주기 탐지 불가 |
| 세계법칙/파괴 | <30/50건 | 30/50건 | **초과** | FIFO로 오래된 파괴/법칙 소실 |
| Bible 캐시 | 정상 | 증가 | **100화+** | _MAX_BIBLE_CACHE=5 → 오래된 스냅샷 재계산 지연 |

### 복합 오류 문제

- 에피소드 다이제스트가 정규식 기반 추출 (LLM 미사용) → 정확도 ~98%
- Tier 2/3에서는 "다이제스트의 다이제스트" → 오류 복합적 누적
- 200화 시점: 초기 세계관 설정의 원본 접근 불가, 요약에만 의존

### 기존 대응 (부분적)

- `docs/2026-02-28/long-term-memory-evaluation.md` — P0/P1/P2 개선 우선순위 문서 존재
- Tier 구간 확장 (30→60화로 Tier2 시작점 이동) 이미 적용
- FactLedger MAX 10→100 확장 완료

### 추가 개선 방향

- NPC 표시 상한 30→동적 (활성 NPC 수 기반)
- FactLedger 핵심 사실 핀(FIFO 제외) 메커니즘
- 반복 탐지 윈도우 20→40화 확대
- Bible 캐시 5→20 스냅샷 확대
- Tier 3 요약에 LLM 기반 요약 도입 (정규식 대체)

---

## 테마 L: 상류 설계 품질 — Stage 2/3 자체의 한계

Stage 4(CW)만 아무리 개선해도 Arc/Blueprint가 부실하면 한계.

### Stage 2 (Arc) 품질 갭

**A1. tactical_doc 최소 길이 부족**
- 현재 최소: ep_count × 450자 (4화 Arc = 1,800자)
- 화당 450자 = 씬당 100~150자 = **2~3문장** → CW 실행에 너무 모호
- 권장: ep_count × 800자 이상

**A2. joint_docs ↔ tactical_doc 불일치**
- joint_docs.final_location과 tactical_doc 서사가 모순 가능
- ArcCritic이 사후 검출하지만 사전 방지 없음

**A3. 에피소드 단위 구조 마커 없음**
- tactical_doc이 산문 1덩어리 → Blueprint가 화 경계를 역파싱해야 함
- 에피소드별 "[제N화]" 마커 강제 필요

**A4. state_constraints 인과 매핑 없음**
- "injuries: 없음→좌팔부상" 만 있고 "어떤 사건이 부상을 유발하는지" 없음
- CW가 부상 원인 장면을 추측해야 함

**A5. "충분히 구체적인가" 검증 없음**
- 길이/연속성/일관성은 검증하지만 **구체성**은 미검증
- 5개 다른 이야기에 쓸 수 있는 범용 Arc가 통과 가능

### Stage 3 (Blueprint) 품질 갭

**B1. scene_breakdown 스키마 없음**
- 완전 비구조 dict → 일관성 없는 포맷
- CW가 매번 다른 형태를 파싱해야 함
- 필요: 씬별 name, focus, tension_level, key_beats, min_chars 구조화

**B2. 씬 수 vs Arc 이벤트 밀도 불일치**
- Arc에 10개 이벤트인데 Blueprint가 4씬만 → 이벤트 누락
- 검증 없음

**B3. ending_hook 범용성**
- "주인공은 위험을 감지했다" 수준의 범용 훅이 통과
- 구체성/서스펜스 강도 검증 없음

**B4. 주제적 일관성 미검증**
- Arc의 core tension을 Blueprint가 실제로 실행하는지 미확인
- 구조적 연속성(위치, 시간)만 검증, 서사적 충실도 미검증

### 피드백 루프

- Stage 4 실패 → Stage 3/2로의 역피드백 존재하나 얕음
- CW가 marginal PASS (55~70점)일 때 Blueprint 재생성 미트리거
- "같은 Arc/Blueprint로 재시도"가 기본 → 상류 품질 문제가 은폐됨

---

## 테마 M: 장르별 성능 편차 (우선 제외 — 2.0.0 스코프 밖)

10개 장르의 지원 깊이가 체계적으로 다름. v2.0.0 이후 검토.

### 장르별 지원 3계층

| 계층 | 장르 | Guard 코드 | 프롬프트 전용 | 전용 검증기 | YAML 설정 | 임계값 |
|------|------|-----------|-------------|-----------|----------|--------|
| **Tier 1 (프리미엄)** | 투자물 | 717줄 | ★★★ (전용) | 2개 (수학) | 113줄 | 72 |
| | 무협 | 662줄 | ★☆☆ | 1개 (pre_llm) | 238줄 | 70 |
| **Tier 2 (표준)** | 헌터 | 867줄 | ★★☆ | 1개 (pre_llm) | 123줄 | 68 |
| | 의학 | 469줄 | ★☆☆ | 0 | 107줄 | 72 |
| | 요리 | 511줄 | ★☆☆ | 0 | ~90줄 | 70 |
| | 작곡 | 518줄 | ★☆☆ | 0 | ~90줄 | 71 |
| **Tier 3 (기본)** | 배우 | 464줄 | ★☆☆ | 0 | 136줄 | 70 |
| | 스포츠 | 462줄 | ★☆☆ | 0 | 105줄 | 69 |
| | 대체역사 | 492줄 | ★☆☆ | 0 | ~90줄 | 72 |
| | **판타지** | **362줄** | **★☆☆** | **0** | **83줄** | **70** |

### 핵심 격차

- Guard 코드: 판타지 362줄 vs 헌터 867줄 = **2.4배 차이**
- YAML 설정: 판타지 83줄 vs 무협 238줄 = **2.9배 차이**
- 전용 프롬프트: **투자물만** 전용 writing_guidelines 보유. 나머지 9개는 공유
- 전용 검증기: 투자물 2개 (InvestmentArithmeticChecker + InvestmentMathVerifier), 나머지 0~1개

### 판타지 (최약 장르) 구체적 갭

- 마법 티어 시스템만 있고 마나 비용/자원 추적 없음
- 주문 티어 매칭 검증 없음
- 아이템 희귀도 시스템 없음 (헌터는 있음)
- Guard 코드가 헌터의 42% 수준

### 개선 방향

- 판타지 Guard 강화 (마법 밸런스, 자원 추적)
- Tier 3 장르에 전용 프롬프트 섹션 추가
- 장르 가중치 세분화 (현재 scoring_validator에서 장르별 가중치 존재하나 얕음)

---

## 테마 N: 프롬프트 구조 최적화

CW 프롬프트 41개 정보원의 배치가 Gemini attention 특성에 최적인지.

### 현재 프롬프트 순서 (chief_writer_prompts.py)

```
[PRIMACY ZONE: 상위 5%]
  Role + Task + 핵심 철학 + 모순 절대 금지

[UPPER MIDDLE: 5~20%]
  환생 설정 → 연결고리 → 엔딩훅 → DNA → 장르 순혈 → 세계관 제약
  → Director 피드백 → REJECT 패턴 → 미래 가드 → 과거 가드
  → Character Voice + World State → HUD 급변

[MIDDLE: 20~70%]
  STEP 1: Blueprint + 씬 분해 + 감정 정점
  STEP 2: 이전 화 다이제스트 + 직전 엔딩
  STEP 3: HUD + NPC 장비 + NPC 빈도
  STEP 4: Arc 설계도
  STEP 5: 주인공 동기

[LOWER: 70~93%]
  STEP 6: 문체 가이드 + 참조 원고
  STEP 7: 만족도 가이드 ← 여기가 문제
  공통 규칙 + 집필 지침

[BOTTOM: 하위 7%]
  이전 원고 전문 (20K+ 자) ← recency 낭비
```

### 발견된 문제

**1. 만족도 가이드가 맨 끝 (41번째 정보원)**
- "이 화에서 보상 시점 1개 필수" 같은 핵심 창작 지시가 프롬프트 93% 지점
- Gemini middle attrition에 의해 간과 가능성 높음

**2. 이전 원고 전문이 recency zone 차지**
- 20K+ 자의 밀집 텍스트가 프롬프트 맨 끝
- recency 효과를 "읽기 자료"에 낭비 (행동 지시가 아님)

**3. 가드/제약이 6곳에 분산 반복**
- future_guard, past_guard, constraint, feedback, "모순 절대 금지" (인라인), common_rules
- "절대/금지/필수/반드시" 33회 등장
- 사망 NPC 경고가 2곳에서 거의 동일하게 반복

**4. 가드가 보호 대상보다 먼저 등장**
- "미습득 무공 금지" (line 115) → 무공 목록은 HUD에서 30줄 뒤에
- "사망 NPC 금지" (line 117) → prev_manuscripts는 50줄 뒤에

### 프롬프트 크기 분석

| 섹션 | 추정 크기 | 비중 | 성격 |
|------|----------|------|------|
| 가드/제약 | ~23,000자 | 20% | 방어적 |
| 창작 지시 (Blueprint/Style/Scene) | ~47,000자 | 41% | 공격적 |
| 상태/컨텍스트 (HUD/NPC/Arc) | ~25,000자 | 22% | 참조 |
| 이전 원고 | ~20,000자 | 17% | 사실 기반 |

### 개선 제안

**1. 가드 통합** — 6곳 → 1곳 "ABSOLUTE CONSTRAINTS" 섹션
- 사망NPC, 미습득아이템, 미배운무공을 한 블록에
- 절감: ~5,000자, 명확성 향상

**2. 만족도 가이드 상위 이동** — STEP 7 → STEP 1 직후 (Blueprint 앞)
- "이 화의 목표: 보상 시점 1개 + 감정 정점" → 톤 앵커

**3. 이전 원고 recency 최적화** — 전문 20K를 핵심 사실 불릿 500자로
- "사망: OOO(N화), 획득: OOO, 현재 자산: OOO"
- recency zone에 행동 지시("FINAL CHECKLIST") 배치

**4. Primacy+Recency 양단 핀** — 핵심 제약 3~4줄을 프롬프트 끝에도 반복
- "FINAL CHECKLIST: 사망NPC 확인, 미습득아이템 확인, 분량 5000자+"

**5. Director 패턴 참고** — Director는 모순 검사를 원고 앞에 배치 (올바름)
- CW도 동일하게: 제약 → 참조 데이터 → 창작 지시 순서로

### 추정 효과

| 변경 | 복잡도 | 절감 | attention 개선 |
|------|--------|------|---------------|
| 가드 통합 | 소 | 5,000자 | +3% |
| 이전 원고 요약화 | 중 | 19,500자 | +12% |
| 만족도 가이드 이동 | 소 | 0 | +5% |
| 스타일 가이드 이동 | 소 | 0 | +3% |
| FINAL CHECKLIST 추가 | 소 | +500자 | +8% |
| Director 패턴 정렬 | 소 | 0 | +2% |
| **합계** | | **~25,000자 절감** | **+33% 추정** |
