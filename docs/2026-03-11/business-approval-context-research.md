# 사업 승인 요청서 — 컨텍스트 조사 결과

> 2026-03-11 작성. 사업 승인 요청서 작성을 위한 3-pass 전수조사 결과물.

---

## 1. 파이프라인 아키텍처 종합

### 전체 흐름

```
Treatment(tr) + Bible(bi)
       ↓
Stage 0: 초기 설정 (세계관 바이블 추출, NPC 등록, 문체 분석, POV 설정)
       ↓
Stage 2: Arc 설계 (5~7화 단위 서사 호)
  - Analyst → 전략 문서 생성
  - ArcEnsemble → 3개 후보 Arc 병렬 생성 (4-Phase Generator)
  - ArcValidator → 구조 검증
  - Director → Arc 최종 선택
       ↓
Stage 3: Blueprint 배치 (화별 씬/대사 구성안)
  - BlueprintEnsemble → 3개 후보 Blueprint 병렬 생성
  - ContinuityInspector → 연속성 검사 (4개 검사)
  - Validator → 일관성 검증
  - Director → Blueprint 최종 선택
       ↓
Stage 4: 원고 집필 + 심사
  - ChiefWriter → 3개 후보 원고 병렬 생성 (균형/서사/긴장감 전략)
  - Self-Critique → 17개 Python 검사 (1~3회 루프)
  - Advisory Chain → 8개 병렬 검증 (TruthGate~NumericConsistency)
  - Director → 최종 심사 (PASS / PASS_WITH_FIX / REJECT)
       ↓
Output: 최종 원고 (카카오/네이버 포맷)
```

### 대원칙 3가지

1. **Python은 수집만, 판단은 LLM** — Python은 데이터 포맷팅/필터링만, 오류 판정/수정 결정은 LLM
2. **팩트시트 수정권은 LLM만** — NPC 속성/세계관/관계도 수정은 LLM 에이전트만
3. **Director 주권주의 (내각제)** — Chief Writer/Analyst는 초안만 제출, Director가 최종 합격/불합격 + 수정 지시

### LLM 에이전트 20+개

| 에이전트 | 역할 | 모델 |
|---------|------|------|
| Analyst | Treatment 분석 → 전략 문서 | pro |
| ArcEnsemble | 3개 Arc 후보 병렬 생성 | pro |
| FourPhaseArcGen | 4-Phase Arc 생성 | pro |
| ArcDraftValidator | Arc 구조 검증 | pro |
| ArcCritic | Arc 비평 | pro |
| ContinuityInspector | 연속성 검증 (4개 검사) | pro |
| BlueprintEnsemble | 3개 Blueprint 후보 | pro |
| ThreePhaseBlueprintGen | 화별 씬 구성 | pro |
| ChiefWriter | 원고 생성 (3 전략) | pro |
| Director | 최종 심사 + 판정 | pro |
| DirectorEnsemble | 후보 비교 | pro |
| DirectorAuditor | 감사 | pro |
| DirectorContinuity | 연속성 | pro |
| Manager | 중간 레벨 조율 | flash |
| StateTracker | WorldState/FactLedger | Python-only |
| PreflightChecker | 사전 검사 | flash |

### 장르 지원 10개

무협, 헌터, 투자, 판타지, 스포츠, 의료, 배우, 요리, 음악, 대체역사

Guard 체인: GenreGuard → WorkGuard(있으면) → StyleGuard(있으면)

---

## 2. 비용 구조 및 성능 메트릭

### 모델 가격표 (2026년 기준)

| 모델 | 입력 ($/1M tokens) | 출력 ($/1M tokens) |
|------|-------------------|-------------------|
| gemini-2.5-pro | $1.25 | $5.00 |
| gemini-2.5-flash | $0.15 | $0.60 |

### 에피소드당 비용 (실파이프라인 데이터)

| 구간 | 에피소드당 비용 | 라운드 | 비고 |
|------|---------------|--------|------|
| Arc 1 (초반) | $0.29~$0.44 (평균 $0.33) | 1 | 컨텍스트 적음 |
| Arc 2 (중반~) | $0.41~$0.82 (평균 $0.61) | 1~3 | 누적 컨텍스트 증가 |

### 250화 총 비용 추정

| 구성 | 수량 | 비용/단위 | 소계 |
|------|------|---------|------|
| Stage 2 | 50 Arc | $0.23 | $11.50 |
| Stage 3 | 250 ep | $0.06 | $15.00 |
| Stage 4 성공 | 250 ep × 1.2라운드 | $0.33 | $99.00 |
| Stage 4 재시도 | 50 ep × 1.5라운드 | $0.50 | $37.50 |
| **합계** | — | — | **$163~$198** |

### 비용 비중

- Stage 4: **81%** (원고 생성이 지배적)
- Pro 모델: **99.5%** (비용 기준)
- Flash 모델: 0.5% (manager/preflight만)

### 코드 규모

| 항목 | 수치 |
|------|------|
| 모듈 코드 | 129,661줄 |
| 테스트 코드 | 63,134줄 |
| 테스트 개수 | 3,847 collected, 3,831 passed |
| Ruff violations | 0개 |
| 전수조사 | 10차+ (P0 0건, P1 0건) |

---

## 3. 품질 보증 시스템

### Advisory Chain (Stage 4, 8개 병렬)

| 순서 | 이름 | 역할 | 유형 | 위험도 |
|------|------|------|------|--------|
| 1 | TruthGate | 사망NPC부활/미소유아이템/장소파괴 7개 사실 검사 | Python | CRITICAL |
| 2 | NpcDriftAdvisor | NPC 속성 텍스트 레벨 표류 감지 | LLM | MAJOR |
| 3 | NumericDriftAdvisor | FactLedger 수치 급변 감지 | LLM | MAJOR |
| 4 | FlashbackVerifier | 회상/플래시백 오염 감지 | LLM | MAJOR |
| 5 | InfoParadoxChecker | 1인칭 시점 정보 역설 감지 | LLM | MAJOR |
| 6 | RelationshipDriftAdvisor | NPC 관계도 역전 감지 | LLM | MAJOR |
| 7 | LongTermRepetitionAdvisor | 20화+ 플롯/씬 반복 감지 | LLM | INFO |
| 8 | NumericConsistencyChecker | FactLedger 교차/산술 9개 검사 | Python | 선택사항 |

### Self-Critique 17개 체크

1. HUD 모순 (high)
2. 클리셰 과다 (high)
3. 정당화 부족 (high)
4. NPC 관계 (high)
5. 동기/약속 방치 (high)
6. WritingDirective 준수 (high)
7. 표현 신선도 (medium)
8. AI TELL 패턴 (medium)
9. Ending Hook 존재 (high)
10. 산술 일관성 (medium)
11. 메타용어 노출 (high)
12. 엔딩 참신성 (medium)
13. 시간 논리 (medium)
14. 문단 구조 (medium)
15. 톤 일관성 (medium)
16. POV 일관성 (medium)
17. 씬 전환 마커 (medium)

### 3-Tier 수정 전략 (PASS_WITH_FIX)

| Tier | 조건 | 실행 |
|------|------|------|
| InPlace | fix_scope="inplace" 또는 score≥60 | LLM 1회 국소 수정 |
| Partial | fix_scope="partial" | 최고 후보 1개만 재생성 |
| Full | fix_scope="full" | 3후보 전면 재생성 |

### Contradiction Firewall

- CRITICAL 1건+ → REJECT 강제, score ≤ 44
- MAJOR 2건+ → REJECT 강제, score ≤ 44

### NC-1/NC-2/NC-3 검증

- **NC-1**: Python-only 수치 정합 9개 검사 (LLM 0회)
- **NC-2**: 씬 유사도/공간 연속성/시간 경과 (Python-only)
- **NC-3**: Director 일관성 체크리스트 17개 카테고리 (권장, 미작성 감점 없음)

---

## 4. State 관리 SSOT

```
project_data.db (SQLite):
  ├─ npc_history (append-only, NPC 변경 이력)
  ├─ npc_relationship_history (관계도 이력)
  ├─ episode_bibles (화별 팩트시트)
  ├─ fact_ledger (누적 팩트 원장)
  ├─ world_state (세계 상태)
  ├─ llm_calls (LLM 호출 로그)
  ├─ stage_attempts (Stage 시도별 로그)
  ├─ director_selections (Director 판정 이력)
  └─ episode_quality_labels (품질 레이블 sidecar)
```

### Context Caching (Gemini API)

- 대상: 5개 에이전트 (ChiefWriter, ArcEnsemble, BlueprintEnsemble, DirectorEnsemble, DirectorContinuity)
- 캐시 쓰기 25% 할인, 읽기 90% 할인
- 50KB+ 컨텍스트만 적용

---

## 5. 학술 이론 근거

### 5.1 장편 서사 생성

| 논문 | 핵심 | 글도비 대응 |
|------|------|-----------|
| DOC (Yang et al., ACL 2023) | 계층적 아웃라인 → 본문 제어 | Stage 2→3→4 계층 구조 |
| RecurrentGPT (Zhou et al., 2023) | 장/단기 메모리로 임의 길이 생성 | WorldState/FactLedger/VecMemory |
| Dramatron (Mirowski, Google DeepMind, 2022) | 로그라인→극본 계층 생성 | Treatment→Arc→Blueprint→원고 |
| LongStory (PAKDD 2024) | 길이 제어 + 컨텍스트 가중치 | ManuscriptLimits + Context Caching |
| Dynamic Hierarchical Outlining (NAACL 2025) | 동적 계층 아웃라인 + 메모리 보강 | 4-Phase Arc + DB SSOT |

### 5.2 멀티에이전트 협업

| 논문 | 핵심 | 글도비 대응 |
|------|------|-----------|
| MetaGPT (Hong et al., 2023) | SOP 기반 역할 분담 | Director/CW/Analyst 역할 분리 |
| Agents' Room (ICLR 2025) | Planning + Writing 에이전트 분업 | Stage 2(계획) + Stage 4(집필) |
| StoryWriter (CIKM 2025) | Outline+Planning+Writing 3모듈 | Treatment+Arc+Blueprint+원고 |
| CollabStory (NAACL 2025) | 다중 LLM 순차 세그먼트 작성 | Ensemble 3후보 병렬 생성 |

### 5.3 품질 보증

| 논문 | 핵심 | 글도비 대응 |
|------|------|-----------|
| Constitutional AI (Anthropic, 2022) | AI 자체 비판/수정 반복 | Self-Critique 17개 체크 |
| Self-Refine (Madaan et al., NeurIPS 2023) | 생성→피드백→수정 루프 | PASS_WITH_FIX 3-Tier 수정 |
| Self-Correct via RL (DeepMind, 2024) | RL 기반 자기 수정 | Director 재심사 반복 (최대 3회) |

### 5.4 시장 규모

- 2024년 한국 웹소설 시장: **약 1조 3,500억원** (KPIPA 2025.04)
- 네이버 계열 7,799억, 카카오페이지 3,602억
- 작가 연평균 소득 1,953만원; 편당 1억원 이상 작가 1%

### 5.5 주요 참조 링크

- RecurrentGPT: https://arxiv.org/abs/2305.13304
- DOC: https://arxiv.org/abs/2212.10077
- Dramatron: https://arxiv.org/abs/2209.14958
- MetaGPT: https://arxiv.org/abs/2308.00352
- Agents' Room: https://arxiv.org/abs/2410.02603
- StoryWriter: https://arxiv.org/abs/2506.16445
- Constitutional AI: https://arxiv.org/abs/2212.08073
- Self-Refine: https://arxiv.org/abs/2303.17651
- Narrative Theory Survey: https://arxiv.org/abs/2602.15851
- Lost in Stories (일관성 버그): https://arxiv.org/abs/2603.05890
- 2024 웹소설 산업 현황: https://www.kpipa.or.kr/p/g3_1/143
- AI 웹소설 창작 현재와 미래 (박성준, 2024): https://cdn.apub.kr/journalsite/sites/ricc/2024-032-00/N0870320006/N0870320006.pdf
