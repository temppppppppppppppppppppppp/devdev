# 00_test_01 Reproduction Cross-Check Report — OPUS

> 작성일: 2026-03-11
> 작성자: Claude Opus 4.6
> 오더: `00-test-01-reproduction-crosscheck-order.md`
> 성격: reproduction verification layer (기존 SSOT를 대체하지 않음)

---

## 최종 한줄 판정

현재 판정: 00_test_01은 00_test_00의 Arc 1 baseline을 **재현함**

---

## Pass 1. 재현 사실 고정

### 표 A. Artifact Parity

| layer | baseline_00_test_00 | candidate_00_test_01 | parity | source |
|---|---|---|---|---|
| arc | arc_001.txt (1 arc, ep_count=4, 투자물) | arc_001.txt (1 arc, ep_count=4, 투자물) | match | SSOT §1.1 / 01 plans/arcs/ |
| blueprint (ep1) | blueprint_0001.txt 존재 | blueprint_0001.txt (54줄, 4씬 구조) | match | SSOT §2 / 01 plans/blueprints/ |
| blueprint (ep2) | blueprint_0002.txt 존재 | blueprint_0002.txt (54줄, 4씬 구조) | match | SSOT §2 / 01 plans/blueprints/ |
| blueprint (ep3) | blueprint_0003.txt 존재 | blueprint_0003.txt (54줄, 4씬 구조) | match | SSOT §2 / 01 plans/blueprints/ |
| blueprint (ep4) | blueprint_0004.txt 존재 | blueprint_0004.txt (54줄, 4씬 구조) | match | SSOT §2 / 01 plans/blueprints/ |
| draft (ep1) | ep_0001.txt 존재 (PASS) | ep_0001.txt (~7,500자, PASS 98) | match | SSOT / 01 drafts/ |
| draft (ep2) | ep_0002.txt 존재 (PASS) | ep_0002.txt (~6,800자, PASS 98) | match | SSOT / 01 drafts/ |
| draft (ep3) | ep_0003.txt 존재 (PASS) | ep_0003.txt (~7,200자, PASS 98) | match | SSOT / 01 drafts/ |
| draft (ep4) | ep_0004.txt 존재 (PASS) | ep_0004.txt (~7,800자, PASS 98) | match | SSOT / 01 drafts/ |
| db_rows: episode_quality_labels | 4행 | 4행 (전체 98점 PASS) | match | SSOT Pass1 표 / 01 DB |
| db_rows: episode_quality_signals | 4행 | 4행 (CED 0.0, AI slop ≤1.0) | match | SSOT Pass1 표 / 01 DB |
| db_rows: director_selections | 14행 | 7행 | mismatch | SSOT Pass1 표 / 01 DB |
| db_rows: stage_attempts | 18행 | 11행 | mismatch | SSOT Pass1 표 / 01 DB |
| metrics | 169 calls, $1.97, 1,027K tokens | 139 calls, $1.66, 907K tokens | near-match | SSOT / 01 metrics JSON |
| runtime_audit | tag=stage3_complete (CF-2 결함) | tag=stage4_complete (11 events) | near-match | SSOT CF-2 / 01 summary JSON |

### 표 B. Run Summary

| project | scope | stage2 | stage3 | stage4 | artifacts_complete | major_counts | notes | source |
|---|---|---|---|---|---|---|---|---|
| 00_test_00 | Arc 1 / ep_0001~0004 | 1 PASS | 4 PASS | 13 attempts (4 PASS, 9 REJECT) | 4/4 | labels=4, signals=4, dir_sel=14, stg_att=18 | ep1 9회 시도, $1.11 집중 | SSOT 3-pass |
| 00_test_01 | Arc 1 / ep_0001~0004 | 1 PASS | 4 PASS | 6 attempts (4 PASS, 2 REJECT) | 4/4 | labels=4, signals=4, dir_sel=7, stg_att=11 | ep3 3회 시도 (V67 History Conflict) | 01 DB + logs |

---

## Pass 2. 차이 분해

### 표 C. Delta Taxonomy

| id | taxonomy | evidence | current interpretation | impact on reproduction claim | next check point | confidence |
|---|---|---|---|---|---|---|
| D-1 | confirmed reproduction | 01 arc_001.txt vs SSOT §1.1: 동일 장르(투자물), 동일 주인공(한시우), 동일 ep_count(4), 동일 시간대(2006-01) | Arc 구조 완전 재현 | none | — | 98% |
| D-2 | confirmed reproduction | 01 blueprints 1-4 존재 + 4씬 구조 vs SSOT §2: 동일 Stage 3 산출물 형태 | Blueprint 산출물 형태 재현 | none | — | 95% |
| D-3 | confirmed reproduction | 01 drafts 1-4 존재 + 전체 PASS vs SSOT: 4/4 최종 PASS | 최종 원고 4편 완성 재현 | none | — | 98% |
| D-4 | confirmed reproduction | 01 DB episode_quality_labels=4, signals=4 vs SSOT 동일 | 품질 계측 파이프라인 재현 | none | — | 98% |
| D-5 | acceptable drift | 01 stage_attempts=11 vs SSOT 18 (차이 7행) | 00_test_00 ep1이 9회 시도한 반면 01은 ep1이 1회 PASS. ep3에서 2회 REJECT 발생했으나 총 retry 횟수가 적음. 재현 대상은 "최종 산출물 + 파이프라인 완주"이며 retry 횟수는 LLM 비결정성의 자연적 결과 | none | — | 95% |
| D-6 | acceptable drift | 01 director_selections=7 vs SSOT 14 (차이 7행) | stage_attempts 차이의 직접 결과. retry 감소 → Director 판정 횟수 감소. 파이프라인 구조 자체는 동일 | none | — | 95% |
| D-7 | acceptable drift | 01 총비용 $1.66 / 907K tokens vs SSOT $1.97 / 1,027K tokens | 00_test_01이 retry 적어서 비용·토큰이 낮음. 동일 모델(gemini-2.5-pro 주력) 사용 확인. 비용 차이는 retry 차이의 자연스러운 결과 | none | — | 95% |
| D-8 | acceptable drift | 01 runtime_audit tag=stage4_complete vs SSOT CF-2 tag=stage3_complete | 00_test_00의 CF-2는 "Stage 4 완료 이벤트 미기록" 결함으로 SSOT에서 확인됨. 01에서는 stage4_complete가 정상 기록됨. 이는 01이 오히려 정상 동작한 것 | none | — | 95% |
| D-9 | acceptable drift | 01 ep3 V67 History Conflict (동기 모순) vs SSOT MR-1 proper noun drift + MR-3 ep1 9회 시도 | 실패 지점이 다름 (00: ep1 반복 실패, 01: ep3 동기 모순). 그러나 양쪽 모두 retry 후 최종 PASS 달성. 실패 패턴의 차이는 LLM 비결정성 범위 내 | low | prose-level 대조 시 확인 가능 | 90% |
| D-10 | acceptable drift | 01 ep 전체 98점 PASS vs SSOT 최종 ep 점수 비공개 (4 PASS 확인) | 00_test_00 최종 에피소드별 점수가 SSOT에 명시되지 않음. 01의 전체 98점은 높은 품질 일관성 시사. 점수 비교 자체가 불완전 | low | 00_test_00 pinned log 점수 확인 시 해소 | 85% |
| D-11 | acceptable drift | 01 session 54분 vs SSOT ~43분 (Arc 1 acceptance) | 시간 차이 ~11분. 01의 ep3 retry (523s+171s+351s = 17.4분)가 원인. 00은 ep1에서 시간 집중. 절대 시간 차이는 retry 패턴 차이의 결과 | none | — | 95% |
| D-12 | confirmed reproduction | 01 모든 원고 CED=0.0, AI slop≤1.0 vs SSOT 품질 경고 WN-1~3 유사 패턴 | 양쪽 모두 대화 비율 부족, 길이 경고 등 동일 유형 noise 경고 발생. 품질 신호 패턴 재현 | none | — | 95% |
| D-13 | hypothesis pending | 01 원고 prose vs SSOT manual-reading-audit 텍스트 기준 | prose 동일성은 요구하지 않으나, "같은 재료" 전제 하에 서사 구조·인물 행동·설정 일관성은 manual reading 없이 완전 확인 불가. 다만 arc/blueprint 구조 match + 전체 PASS로 구조적 재현은 확인됨 | low | 01 원고 manual reading 수행 시 해소 | 80% |

---

## Pass 3. 확신도 판정

### 표 D. Confidence Ladder

| claim | current status | blocker to 95% | confidence_now | confidence_if_resolved |
|---|---|---|---|---|
| Arc 1 artifact reproduction | confirmed reproduction | — | 98% | 98% |
| Stage 2→3→4 pipeline reproduction | confirmed reproduction | — | 97% | 97% |
| operator-readable observability parity | acceptable drift (runtime_audit tag 차이 + retry 수 차이) | — | 93% | 95% |
| 00_test_00 대비 baseline fidelity | acceptable drift (retry 횟수·비용·실패 지점 차이) | D-13: 01 원고 prose-level manual reading 미수행 | 90% | 96% |

**종합 확신도: 92%**

95% 도달 조건:
1. D-13 해소: 00_test_01 원고 4편에 대한 manual reading audit 수행 → prose-level 서사 구조/인물 행동/설정 일관성 확인
2. D-10 보강: 00_test_00 pinned session log에서 최종 에피소드별 점수 추출·비교

현재 근거로 95% 미달 사유: prose-level 대조가 없어 "같은 재료, 같은 방식"의 텍스트 수준 재현을 구조적 parity만으로 완전히 닫을 수 없음. 다만 material divergence는 발견되지 않았으며, 모든 차이가 acceptable drift 또는 hypothesis pending 범위 내.

---

## 비교용 요약

- **00_test_01은 00_test_00를 어디까지 재현했는가**: Arc 1 / ep_0001~0004 전체 산출물(arc·blueprint·draft·DB rows)을 완전히 재현했다. Stage 2→3→4 파이프라인 전 단계를 정상 완주했다.
- **핵심 parity는 어디서 확인되는가**: artifact 존재 match (arc 1개, blueprint 4개, draft 4개), episode_quality_labels 4행, episode_quality_signals 4행, 전체 PASS verdict.
- **허용 가능한 drift는 무엇인가**: retry 횟수 차이 (stage_attempts 18→11, director_selections 14→7), 실패 지점 차이 (00: ep1 9회, 01: ep3 3회), 비용 차이 ($1.97→$1.66), runtime_audit 태그 차이 (CF-2 결함 vs 정상 기록).
- **재현 판정을 흔드는 material divergence가 있는가**: 없다. 모든 차이가 LLM 비결정성 또는 기존 결함(CF-2) 해소의 자연스러운 결과다.
- **현재 근거로 확신도 95%에 도달하는가**: 미달 (92%). prose-level manual reading이 없어 텍스트 수준 재현 확인이 불완전하다. 구조적 재현은 확인됨.

---

## Appendix A. Agent-specific observations

1. **00_test_00 live DB 상태 확인**: `projects/00_test_00/project_data.db`를 직접 조회한 결과, manuscripts/stage_attempts/director_selections 등 핵심 테이블이 모두 0행이다 (llm_calls 528행만 존재). 이는 오더 §1.2의 "이후 reset/초기화로 live 산출물이 바뀌었을 수 있다" 경고와 정확히 일치한다. SSOT 문서 기반 baseline 사용이 필수임을 실증적으로 확인했다.

2. **00_test_01 ep3 실패 근본 원인**: V67 History Conflict — ep2가 확립한 "18년의 실패에서 얻은 교훈"을 ep3가 "운동선수로서의 반사신경"으로 모순시킨 동기 부여 오류. 00_test_00의 ep1 반복 실패 (JSON mode/rubric 문제, MR-3)와는 원인이 다르다. 양쪽 모두 retry 메커니즘이 정상 작동하여 최종 PASS를 달성한 점은 동일하다.

3. **runtime_audit_summary 개선**: 00_test_00의 CF-2 결함(stage3_complete에서 끊김)이 00_test_01에서는 stage4_complete로 정상 기록되었다. 이는 code-level fix가 적용되었거나 실행 경로 차이의 결과일 수 있다. reproduction 판정에는 영향 없음 (오히려 01이 정상).

4. **점수 일관성**: 00_test_01의 4개 에피소드 모두 동일 98점. score_breakdown도 동일 구조 (`continuity_contradiction: 40, blueprint_coverage: 20, quality_engagement: 20, length: 10, python_warnings: 8`). 이는 Director 채점 rubric의 안정적 적용을 시사한다.

5. **비용 효율**: 00_test_01의 에피소드당 비용 $0.42 (00_test_00: ~$0.49). retry 감소가 주요 원인이며, 단가 자체는 동일 모델(gemini-2.5-pro) 사용으로 유사하다.

## Appendix B. 반례 / 이견 / 추가 가설

1. **D-9에 대한 보수적 해석 가능성**: 실패 지점이 "완전히 다르다" (ep1 vs ep3, JSON/rubric vs V67 History Conflict)는 사실은 "같은 파이프라인이 다른 약점을 노출했다"로도 읽을 수 있다. 만약 이를 material divergence로 승격하면 재현 판정이 "부분 재현"으로 바뀔 수 있다. 그러나 오더 §3 Pass 3의 과장 방지 규칙("retry 횟수 차이가 reproduction 핵심과 별개면 acceptable drift")에 따라 acceptable drift로 분류했다.

2. **D-13의 해소 가능성**: 00_test_01 원고 manual reading을 수행하면 "같은 재료(Bible·Treatment), 같은 서사 골격(투자물·회귀), 같은 인물 행동 패턴"이 텍스트 수준에서도 확인될 가능성이 높다. arc/blueprint 구조가 match이고 전체 98점 PASS인 점이 간접 근거다. 다만 prose 동일성이 아닌 "서사 구조 동등성"만 확인하면 95%에 도달할 수 있다.

---

*이 문서는 `00-test-01-reproduction-crosscheck-order.md`의 OPUS 실행 결과이며, 기존 SSOT를 대체하지 않는 reproduction verification layer로만 동작한다.*
