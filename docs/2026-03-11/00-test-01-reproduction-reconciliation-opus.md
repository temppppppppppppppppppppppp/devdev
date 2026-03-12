# 00_test_01 Reproduction Reconciliation — OPUS

> 작성일: 2026-03-11
> 작성자: Claude Opus 4.6
> 입력: `00-test-01-reproduction-crosscheck-report-OPUS.md` (자기 보고서) + `00-test-01-reproduction-crosscheck-codex.md` (상대 보고서)
> 성격: reconciliation layer (원문 두 문서 수정 금지)

---

## 1. 합의 사실

| id | 항목 | OPUS 근거 | Codex 근거 | 비고 |
|---|---|---|---|---|
| AF-1 | 최종 판정: **재현함** | OPUS 한줄 판정 | Codex 한줄 판정 | 양쪽 동일 |
| AF-2 | material divergence **0건** | OPUS 표 C 13건 중 0건 | Codex 표 C 7건 중 0건 | 양쪽 동일 |
| AF-3 | artifact parity **match** (arc 1개, blueprint 4개, draft 4개) | OPUS 표 A: 9개 match | Codex 표 A: arc/blueprint/draft 전부 match | 양쪽 동일 |
| AF-4 | DB 품질 계측 parity (labels=4, signals=4) | OPUS D-4 confirmed reproduction | Codex D3 confirmed reproduction | 양쪽 동일 |
| AF-5 | Stage 2→3→4 파이프라인 완주 재현 | OPUS 표 B: 양쪽 PASS | Codex D2 confirmed reproduction | 양쪽 동일 |
| AF-6 | retry 횟수 차이 (18→11 stage_attempts, 14→7 director_selections)는 **acceptable drift** | OPUS D-5, D-6 | Codex D4 | 양쪽 동일. "LLM 비결정성" (OPUS) vs "hardening 효과" (Codex) 해석은 ID-2에서 분리 |
| AF-7 | runtime_audit_summary 차이 (stage3_complete→stage4_complete)는 **acceptable drift** | OPUS D-8 | Codex D5 | 양쪽 동일. "개선" 해석 합의 |
| AF-8 | prose full text 1:1 parity 미증명은 **hypothesis pending** | OPUS D-13 | Codex D7 | 양쪽 동일. 다만 impact 해석은 ID-1에서 분리 |
| AF-9 | 비용/토큰 차이 ($1.97→$1.66)는 **acceptable drift** | OPUS D-7 | Codex 표 A metrics near-match | 양쪽 동일 |

---

## 2. 해석 차이

| id | 항목 | OPUS 해석 | Codex 해석 | OPUS 판단 |
|---|---|---|---|---|
| ID-1 | **확신도: 92% vs 95%** | prose-level manual reading (D-13)이 미완이므로 95% 미달. "같은 재료, 같은 방식"의 텍스트 수준 재현을 구조적 parity만으로 완전히 닫을 수 없음 | artifact/stage/state parity가 핵심이며 prose parity는 오더가 요구하지 않으므로 95% 허용 | **Codex 해석에 일리 있음.** 오더 §3 표 A 작성 규칙에 "prose의 완전 동일성은 요구하지 않는다"가 명시되어 있다. OPUS의 D-13은 reproduction 핵심이 아닌 부가 검증이므로, 95% 차단 근거로 쓰기엔 과도했을 수 있다. 다만 "같은 재료, 같은 방식" 전제의 텍스트 수준 확인이 빠진 점은 잔여 불확실성으로 유효하다. **조정 후 확신도: 94%** |
| ID-2 | retry 감소 원인 해석 | "LLM 비결정성의 자연적 결과" | "P0/P1 이후 hardening 효과로 읽는 편이 맞다" | **양쪽 모두 가능하며 분리 불가.** 00_test_00과 01 사이에 코드 변경이 있었을 수 있고 (runtime_audit CF-2 해소가 방증), 동시에 LLM 비결정성도 작용한다. 인과 분리는 동일 코드 + 동일 seed 재현이 아닌 한 불가. reproduction 판정에는 영향 없음 |
| ID-3 | ep4 시간축 drift | OPUS D-11에서 session 시간 차이(54분 vs 43분)로만 언급 | Codex D6에서 "약 2주 후→다음 날 오후→일주일 후" elapsed-time 표현까지 추적 | **Codex가 더 세밀함.** OPUS는 session 시간만 봤으나 Codex는 서사 내 시간축까지 대조했다. 다만 양쪽 모두 acceptable drift 분류이므로 결론은 동일 |

---

## 3. 편측 발견

| id | 발견자 | 항목 | 내용 | 상대 문서 대응 | OPUS 평가 |
|---|---|---|---|---|---|
| UF-1 | OPUS | 00_test_00 live DB 공조회 | manuscripts/stage_attempts/director_selections 0행, llm_calls 528행만 존재. 오더 §1.2 "reset 경고"를 실증 확인 | Codex 미언급 (SSOT 기반 접근 동일하나 live DB 직접 조회 안 함) | 사실 확인용으로 유효. reproduction 판정에 영향 없음 |
| UF-2 | OPUS | ep3 V67 근본 원인 분석 | "18년 실패 교훈" vs "운동선수 반사신경" 동기 모순. 00_test_00 ep1 실패(JSON/rubric)와 원인 상이 | Codex D4에서 "retry profile 줄었다"로만 언급, 실패 원인 비교 없음 | acceptable drift 판정에 보강 근거 제공. 양쪽 모두 retry 후 PASS라는 결론 동일 |
| UF-3 | OPUS | 점수 비교 불완전성 (D-10) | 00_test_00 최종 ep별 점수가 SSOT에 미공개. 01 전체 98점과 직접 비교 불가 | Codex 미언급 | 사실이나 impact low. SSOT에 "4 PASS" 확인되므로 핵심 재현에 지장 없음 |
| UF-4 | OPUS | 품질 신호 패턴 match (D-12) | CED=0.0, AI slop≤1.0, 대화비율/길이 경고 등 동일 유형 noise 확인 | Codex 표 A db_rows match로 포함 | OPUS가 명시적으로 분리했으나 Codex도 DB match에 포함. 실질 동일 |
| UF-5 | Codex | 17/17 필수 입력 검증 | 오더 §1.2 목록 대비 17개 파일 전수 존재 확인 | OPUS 미언급 (파일별 읽기는 수행했으나 카운트 명시 안 함) | 유효한 절차적 확인. OPUS도 실질적으로 전수 읽기 수행 |
| UF-6 | Codex | ep4 elapsed-time 서사 내 세부 대조 | baseline "약 2주 후→다음 날 오후→일주일 후" vs candidate "다음 날 오후" 유지 확인 | OPUS D-11에서 session 시간만 비교 | Codex가 더 깊은 서사 내 시간축 추적. acceptable drift 결론 동일 |

---

## 조정 후 종합 판정

| 항목 | OPUS 원본 | 조정 후 |
|---|---|---|
| 최종 판정 | 재현함 | **재현함** (불변) |
| 종합 확신도 | 92% | **94%** (ID-1 반영: prose parity는 오더 비요구사항이므로 차단 근거 약화) |
| material divergence | 0건 | **0건** (불변) |
| 95% 미달 잔여 근거 | prose manual reading + ep 점수 비교 | ep4 시간축 exact form + baseline live draft 부재 (1% 미만 잔여) |

**Codex 95% 판정에 대한 OPUS 입장**: 오더 규칙에 충실한 해석으로 수용 가능하다. OPUS의 92%는 보수적 측정이었으며, 오더 §3 표 A "prose 동일성 비요구" 규칙을 적용하면 94~95% 범위가 합리적이다. 양쪽 모두 "재현함" + "material divergence 0건"이라는 핵심 결론은 완전히 합의한다.

---

*이 문서는 reconciliation layer이며, 원문 두 보고서(OPUS/Codex)를 수정하지 않는다.*
