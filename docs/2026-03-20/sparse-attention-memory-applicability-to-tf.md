# 장기연재 관련 논문 수집 + Sparse Attention/Memory → 글도비 TF 적용 가능성 분석

> **목적**: (1) 장기연재 소설 생성에 도움되는 최신 논문을 분야별로 수집하고,
> (2) Sparse Attention / Memory 논문들의 핵심 기법을 글도비 TF 4대 시스템에 매핑한다.
>
> **범위**: 문서화 전용 — 코드 수정 없음
>
> **작성일**: 2026-03-20
>
> **3Pass 적대적 감리**: 2026-03-21 완료

---

# 감리 결과 요약표

## Pass 1 — ROI 판정

| 섹션 | ROI | 배치 | 사유 |
|------|-----|------|------|
| A-1 | HIGH | 본문 | 장편 생성 = 글도비 핵심 도메인, Director→Blueprint→CW 구조 동형 논문 다수 |
| A-2 | HIGH | 본문 | 서사 일관성/모순 감지 = TF Advisory Chain 핵심 과제, ConStory-Bench 벤치마킹 가능 |
| A-3 | HIGH | 본문 | 에피소딕 메모리 = TF-3 ChainLink/TF-4 Summary Pyramid 직접 대응, ComoRAG 아키텍처 유사 |
| A-4 | MEDIUM | 본문 | MAS 협업 패턴 참고 가능하나, 글도비는 고정 파이프라인이라 에이전트 간 동적 협업은 거리 있음 |
| A-5 | LOW | Appendix | Sparse Attention/KV Cache 커널 최적화 = 모델 내부 접근 필요, Gemini API 소비자 적용 불가 |
| A-6 | HIGH | 본문 | 할루시네이션 감지 = TruthGate/Advisory 핵심, SelfCheckGPT 블랙박스 패턴 직접 차용 가능 |
| A-7 | MEDIUM | 본문 | RAG/컨텍스트 엔지니어링 참고용, 글도비 hybrid search 이미 운영 중이나 개선 여지 |
| A-8 | MEDIUM | 본문 | 평가 벤치마크 — Director 채점 rubric 개선 참고, 직접 적용보다는 벤치마킹 소스 |
| A-9 | MEDIUM | 본문 | 문체 제어 = StyleGuard/GenreGuard 참고, 다만 API 소비자로서 디코딩 제어 불가 |
| A-10 | HIGH | 본문 | Temporal KG = TF-1 WorldState/TF-2 FactLedger 직접 대응, Graphiti 구현체 참고 가치 높음 |
| A-11 | HIGH | 본문 | 서사 구조/긴장감 = pacing_analyzer/LongTermRep 직접 대응, SCORE 논문 일관성 향상 기법 |
| A-12 | HIGH | 본문 | Self-Refinement = Stage4 REJECT→재시도 루프 핵심 패턴, Self-Refine 20% 향상 근거 |
| A-13 | HIGH | 본문 | 캐릭터 모델링 = NPC 100+명 인격 유지 핵심, CoSER 771권 데이터 직접 참고 |
| A-14 | HIGH | 본문 | LLM-as-Judge = Director 판정/Ensemble 채점 핵심, 글도비 품질 루프 전체에 적용 |
| A-15 | HIGH | 본문 | 프롬프트 압축 = 400K mandatory_context 예산 관리 직접 대응, LLMLingua 20x 압축 |
| A-16 | MEDIUM | 본문 | 소설 대화/드라마 — 참고 가치 있으나 글도비 ChiefWriter 대사 생성은 이미 안정 |
| A-17 | HIGH | 본문 | 플롯홀 감지 = TruthGate/Advisory 핵심 과제, FlawedFictions 벤치마크 활용 가능 |
| A-18 | HIGH | 본문 | 계층적 요약 = TF-4 Summary Pyramid 직접 대응, BooookScore coherence error 분류 활용 |
| A-19 | MEDIUM | 본문 | 감정 호 추적 — ChainLink emotional_state 참고, 다만 글도비는 감정을 명시적으로 관리 중 |
| A-20 | MEDIUM | 본문 | GraphRAG — Vector memory 개선 참고, 현재 hybrid search로 운영 중이라 증분 개선 |
| A-21 | HIGH | 본문 | LLM 앙상블 = ArcEnsemble/BlueprintEnsemble/DirectorEnsemble 핵심, Best-of-N 이론 근거 |
| A-22 | LOW | Appendix | 구조화 출력 = Gemini response_mime_type으로 이미 해결, constrained decoding은 API 소비자 적용 불가 |
| A-23 | HIGH | 본문 | 워크플로우 오케스트레이션 = Stage 0~4 파이프라인 직접 대응, AFlow MCTS 참고 |
| A-24 | HIGH | 본문 | API 비용 최적화 = Gemini Context Caching 90% 할인 체계와 직접 대응, FrugalGPT cascade |
| A-25 | LOW | Appendix | RLHF/RL for Creative Writing = 모델 fine-tuning 필요, Gemini API 소비자 적용 불가 |
| A-26 | MEDIUM | 본문 (축약) | 한국어 LLM — 참고용이나 글도비는 Gemini API 사용이라 모델 학습 불가, 무협 스타일 분석만 유의미 |
| A-27 | MEDIUM | 본문 | 월드빌딩 = WorldStateManager 참고, 다만 글도비는 수동 구축이라 절차적 생성과 거리 |
| A-28 | MEDIUM | 본문 (축약) | 가드레일 = GenreGuard/WorkGuard 참고, 다만 글도비 가드레일은 이미 3계층 구축 완료 |
| A-29 | HIGH | 본문 | 메모리 라우팅/선택적 검색/계층형 저장 = TF-1/2/3/VecMem 선택적 접근 핵심, 가장 실용적 |
| Part B | — | 본문 (유지) | TF 적용 가능성 분석 본론 |

## Pass 2 — 누락/중복/오류 감지

| 항목 | 유형 | 상세 | 조치 |
|------|------|------|------|
| Act-LLM | 중복 | A-2 (L44)와 A-13 (L283)에 동일 논문 수록 | A-2에서 제거, A-13에만 유지 (캐릭터 모델링이 더 적합한 분류) |
| Lost in Stories | 중복 | A-2 (L40)와 A-17 (L358)에 동일 논문 수록 | A-17에서 "(→ A-2 참조)" 교차 참조로 대체 |
| Multi-Agent Character Simulation | 중복 | A-4 (L83)와 A-16 (L347)에 동일 논문 수록 | A-16에만 유지 (대화/드라마가 더 적합), A-4에서 교차 참조 |
| Agent-Memory-Paper-List | 중복 | A-3 (L69)와 A-29d (L613)에 동일 리포 수록 | A-29d에만 유지 (메모리 전문 섹션), A-3에서 교차 참조 |
| LLM-as-a-Judge 리포 | 중복 | A-8 (L176)와 A-14 Awesome Lists (L309)에 동일 리포 수록 | A-14에만 유지 (전문 섹션), A-8에서 교차 참조 |
| MSA 논문 | 분류 오류 | A-4 MAS에 수록되었으나 실제로는 Sparse Attention 논문 | A-5 Sparse Attention으로 이동 (단, A-5 전체가 Appendix이므로 Part B 소스 목록에서 참조) |
| PragWorld arXiv 링크 | 링크 오류 | A-27 PragWorld가 arXiv 2506.13013을 가리키나 이것은 Wuxia Fiction 논문(A-26)의 ID | PragWorld 올바른 ID 확인 불가 — arXiv 링크 제거 후 "AAAI 2026" 학회 정보만 유지 |
| LONGMEM GitHub 링크 | 링크 오류 | [GitHub]로 표시되었으나 실제 URL은 arXiv PDF (arxiv.org/pdf/2306.07174) | [arXiv PDF]로 레이블 수정 |
| Assessing Language Models' Worldview | 깨진 링크 | GitHub 링크가 `https://github.com/` (루트만) | 링크 제거, "—" 표시 |

## Pass 3 — 구조 최적화

- HIGH ROI 섹션 (16개): 본문 유지
- MEDIUM ROI 섹션 (9개): 본문 유지, A-26/A-28은 축약
- LOW ROI 섹션 (3개: A-5, A-22, A-25): Appendix로 이동, 본문에 교차 참조 1줄만 유지
- Part B: 전체 유지 (TF 적용 분석 본론)

---

# Part A. 장기연재에 도움되는 논문 수집

## A-1. 장편 소설 생성 (Long-form Story Generation)

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **DOME**: Dynamic Hierarchical Outlining with Memory-Enhancement | NAACL 2025 | [GitHub](https://github.com/Qianyue-Wang/Generating-Long-form-Story-Using-Dynamic-Hierarchical-Outlining-with-Memory-Enhancement) | 계층적 아웃라인 + temporal KG 메모리로 장편 일관성 유지. **글도비 TF-4 Summary Pyramid과 직접 대응** |
| **StoryWriter**: Multi-Agent Framework for Long Story Generation | CIKM 2025 | [GitHub](https://github.com/THU-KEG/StoryWriter) | Outline Agent → Planning Agent → Writing Agent 3단계. **글도비 Director→Blueprint→CW 파이프라인과 구조 동형** |
| **ReasoningNCP**: Learning to Reason for Long-Form Story Generation | arXiv 2503.22828 | [GitHub](https://github.com/Alex-Gurung/ReasoningNCP) | Next-Chapter Prediction + RL 보상. 장편 추론 능력 학습 |
| **RecurrentGPT**: Interactive Generation of Arbitrarily Long Text | arXiv 2305.13304 | [GitHub](https://github.com/aiwaves-cn/RecurrentGPT) | LSTM 메커니즘을 자연어로 시뮬레이션. short/long-term memory 분리. **TF-2 FactLedger 영감** |
| **Agents' Room**: Narrative Generation through Multi-step Collaboration | ICLR 2025 | [GitHub](https://github.com/google-deepmind/tell-me-a-story) | Planning Agent + Writing Agent + 공유 Scratchpad. DeepMind |
| **RaPID**: Retrieval-Augmented Long Text Generation with Writing Planning | ACL 2025 Findings | [GitHub](https://github.com/USTC-StarTeam/RaPID) | Outline → Attribute Search → Plan-guided 생성. 장문 할루시네이션 감소 |
| Long Story via Knowledge Graph and Literary Theory | arXiv 2508.03137 | — | KG + 문학 이론 기반 장편 구조화 |
| Measuring Information Distortion in Hierarchical Ultra-long Novel Reconstruction | arXiv 2505.12572 | — | 초장편 재구성 시 정보 왜곡 측정. 최적 확장 비율 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-Story-Generation](https://github.com/yingpengma/Awesome-Story-Generation) | LLM 시대 스토리 생성 논문 종합 (가장 포괄적) |
| [story-generation topic](https://github.com/topics/story-generation) | GitHub 토픽 모음 |

---

## A-2. 서사 일관성 / 모순 감지 (Narrative Consistency)

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Lost in Stories**: Consistency Bugs in Long Story Generation by LLMs | arXiv 2603.05890 (2026.03) | [Project](https://picrew.github.io/constory-bench.github.io/) | ConStory-Bench 2,000 프롬프트 + 5대 에러 카테고리 19 세부 유형. **TF Advisory Chain 벤치마킹에 직접 활용 가능** |
| **ConStory-Checker** (위 논문 부속) | — | — | 자동 모순 감지 파이프라인. 텍스트 증거 기반 판정 |
| **CharacterBox**: Evaluating Role-Playing Capabilities of LLMs | NAACL 2025 | — | 역할극 일관성 평가 프레임워크 |
| Assessing Language Models' Worldview for Fiction Generation | arXiv 2408.07904 | — | 9개 LLM 세계관 일관성 테스트. 2개만 일관적 |
| **CollabStory**: Multi-LLM Collaborative Story Generation and Authorship Analysis | 2025 | — | 최대 5 에이전트 협업 장편. 저자 분석 |

> **Act-LLM** → A-13 참조 (캐릭터 모델링 분류가 더 적합)

---

## A-3. 장기 메모리 / 에피소딕 메모리 (Long-term & Episodic Memory)

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **EM-LLM**: Human-inspired Episodic Memory for Infinite Context LLMs | ICLR 2025 | [GitHub](https://github.com/em-llm/EM-LLM-model) | Bayesian surprise 기반 이벤트 세그멘테이션 + 2단계 retrieval. 10M 토큰 처리. **TF-3 ChainLink 이벤트 경계와 유사** |
| **ComoRAG**: Cognitive-Inspired Memory-Organized RAG for Stateful Long Narrative | AAAI 2026 | [GitHub](https://github.com/EternityJune25/ComoRAG) | 인지 과학 영감 메모리 워크스페이스. 200K+ 토큰 서사 추론. **TF 전체 아키텍처와 가장 유사한 논문** |
| **MemoRAG**: Memory-based RAG for Long Context Processing | TheWebConf 2025 | [GitHub](https://github.com/qhjqhj00/MemoRAG) | 전역 메모리 모델 + dual-system RAG. 수백만 토큰 처리 |
| **LONGMEM**: Augmenting LMs with Long-Term Memory | NeurIPS 2023 | [arXiv PDF](https://arxiv.org/pdf/2306.07174) | Non-differentiable memory bank + decoupled module. Staleness 해결 |
| **InfLLM**: Training-Free Long-Context Extrapolation | NeurIPS 2024 | [arXiv](https://arxiv.org/abs/2402.04617) | Sliding window + context memory bank. Training-free |
| Recursively Summarizing for Long-Term Dialogue Memory | arXiv 2308.15022 | — | 재귀적 요약으로 대화 장기 기억 유지 |
| Episodic Memories Generation and Evaluation Benchmark | ICLR 2025 | [GitHub](https://github.com/ahstat/episodic-memory-benchmark) | 에피소딕 메모리 벤치마크 |
| Look Back to Reason Forward: Revisitable Memory for Long-Context Agents | arXiv 2509.23040 | — | 에이전트 장문맥 메모리 재방문 패턴 |
| Memory Matters More: Event-Centric Memory as Logic Map for Agent Reasoning | 2026.01 | — | 이벤트 중심 메모리 → 에이전트 추론 지도 |
| **EverMemOS**: Self-Organizing Memory OS for Structured Long-Horizon Reasoning | 2026.01 | — | 메모리 자가 조직화 OS |
| From RAG to Memory: Non-Parametric Continual Learning for LLMs | 2025.02 | — | RAG → 지속 학습 메모리 전환 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| Agent-Memory-Paper-List → A-29d Awesome Lists 참조 (메모리 전문 섹션에 통합) |
| [Awesome-LLM-Long-Context-Modeling](https://github.com/Xnhyacinth/Awesome-LLM-Long-Context-Modeling) | Long Context 논문 필독 리스트 |
| [Long-Context-Language-Modeling Survey](https://github.com/LCLM-Horizon/A-Comprehensive-Survey-For-Long-Context-Language-Modeling) | Long Context LM 종합 서베이 |

---

## A-4. MAS (Multi-Agent System) 논문

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **MARTI**: Multi-Agent Reinforced Training and Inference | ICLR 2026 | [GitHub](https://github.com/TsinghuaC3I/MARTI) | Multi-Agent RL 학습 프레임워크 |
| **LatentMAS**: Latent Collaboration in Multi-Agent Systems | arXiv 2511.20639 | [GitHub](https://github.com/Gen-Verse/LatentMAS) | 잠재 공간 에이전트 협업. GSM8K/AIME/GPQA 벤치마크 |
| Multi-Agent Collaboration Mechanisms: A Survey of LLMs | arXiv 2501.06322 | — | MAS 협업 메커니즘 서베이 |
| Multi-Agent Based Character Simulation for Story Writing | in2writing 2025 | — | Director Agent + Character Agent 역할극 기반 집필 (→ A-16 참조) |
| LLM Collaboration with MAGRPO | arXiv 2508.04652 | — | Multi-Agent Group Relative Policy Optimization |
| Context-Engineering for Multi-Agent Systems | 2026 | [GitHub](https://github.com/Denis2054/Context-Engineering-for-Multi-Agent-Systems) | 도메인 불문 MAS 오케스트레이션 블루프린트 |

> **MSA** (Memory Sparse Attention) → Appendix A-5 참조 (Sparse Attention 분류가 더 적합)

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [awesome-multi-agent-papers](https://github.com/kyegomez/awesome-multi-agent-papers) | Swarms 팀 MAS 논문 모음 |
| [Awesome-LLM-based-MultiAgents](https://github.com/Andrewzh112/Awesome-LLM-based-MultiAgents) | LLM 기반 멀티에이전트 논문/프로젝트 |
| [Multi-Agent-Papers](https://github.com/shizhl/Multi-Agent-Papers) | MAS 필독 논문 + SOTA |
| [awesome-ai-agent-papers](https://github.com/VoltAgent/awesome-ai-agent-papers) | 2026 arXiv 주간 업데이트 |
| [awesome-multi-agent-systems](https://github.com/richardblythman/awesome-multi-agent-systems) | MAS 리소스/프레임워크/도구 |
| [Awesome-Agent-Papers](https://github.com/luo-junyu/Awesome-Agent-Papers) | LLM Agent Survey (up-to-date) |
| [Autonomous-Agents](https://github.com/tmgthb/Autonomous-Agents) | LLM 자율 에이전트 논문 (매일 업데이트) |

---

## A-5. Sparse Attention / KV Cache 압축

> **→ Appendix B-1 참조** (모델 내부 커널 최적화 = Gemini API 소비자 적용 불가)

---

## A-6. 할루시네이션 감지 / Fact Checking

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **SelfCheckGPT**: Zero-Resource Black-Box Hallucination Detection | 2023 | [GitHub](https://github.com/potsawee/selfcheckgpt) | 샘플링 기반 자기 일관성 검증. **TF TruthGate와 유사 패턴** |
| **SAC3**: Semantic-aware Cross-check Consistency | 2023 | [GitHub](https://github.com/intuit/sac3) | 의미론적 교차 일관성 검증. Self-consistency만으론 부족 |
| **LLM-Check**: Hallucination Detection via Internal Signals | NeurIPS 2024 | [GitHub](https://github.com/GaurangSriramanan/LLM_Check_Hallucination_Detection) | Attention map + hidden activation 기반 감지 |
| **UQLM**: Uncertainty Quantification for LMs | 2024 | [GitHub](https://github.com/cvs-health/uqlm) | 다중 응답 → claim 분해 → 일관성 평가 |
| Siren's Song: Survey on Hallucination in LLMs | Survey | [GitHub](https://github.com/HillZhang1999/llm-hallucination-survey) | 할루시네이션 서베이 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [awesome-hallucination-detection](https://github.com/EdinburghNLP/awesome-hallucination-detection) | 할루시네이션 감지 논문 (Edinburgh NLP) |
| [Awesome-LLM-hallucination](https://github.com/LuckyyySTA/Awesome-LLM-hallucination) | LLM 할루시네이션 논문 리스트 |
| [hallucination-leaderboard](https://github.com/vectara/hallucination-leaderboard) | 할루시네이션 리더보드 (Vectara) |

---

## A-7. RAG / 컨텍스트 엔지니어링

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Disco-RAG**: Discourse-Aware RAG for Long-Form QA | 2026 | — | 담화 구조 인식 RAG |
| **TreePS-RAG**: Tree-based Process Supervision for RAG | 2026 | — | 트리 기반 프로세스 감독 |
| **ArcAligner**: Long Memory RAG | 2026.01 | — | 장기 메모리 정렬 |
| **Fiction.LiveBench**: Long-Context Comprehension Benchmark | 2025 | [GitHub](https://github.com/mnismt/llms-long-context-benchmark) | 장문맥 서사 이해 벤치마크 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-RAG](https://github.com/liunian-Jay/Awesome-RAG) | RAG 기술 발전 추적 |
| [RAG-Survey](https://github.com/hymie122/RAG-Survey) | RAG for AIGC 서베이 |
| [Awesome-RAG-Reasoning](https://github.com/DavidZWZ/Awesome-RAG-Reasoning) | EMNLP 2025. RAG + 추론 |
| [Awesome-Context-Engineering](https://github.com/Meirtz/Awesome-Context-Engineering) | 컨텍스트 엔지니어링 종합 (Prompt → Production) |
| [AgenticRAG-Survey](https://github.com/asinghcsu/AgenticRAG-Survey) | Agentic RAG 서베이 |

---

## A-8. 평가 / 벤치마크

| 리소스 | GitHub | 핵심 |
|--------|--------|------|
| Creative Writing Quality Benchmark | [GitHub](https://github.com/lechmazur/writing) | 10개 필수 요소 통합 평가 |
| Story Evaluation LLM Dataset | [GitHub](https://github.com/lars76/story-evaluation-llm) | 15개 모델 x 다국어 품질 평가 |
| Awesome LLM Eval Benchmark (250개) | [GitHub](https://github.com/VyetGokyra/awaresome_LLM_eval_benchmark) | 250개 벤치마크/데이터셋 |

> **LLM-as-a-Judge 리포** → A-14 Awesome Lists 참조 (전문 섹션에 통합)

---

## A-9. Controllable Text Generation / Style Transfer

> 글도비 대응: StyleGuard, GenreGuard, WorkGuard — 장르별 문체 제어 + 작가 보이스 일관성

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **CTG Survey**: Controllable Text Generation for LLMs | arXiv 2408.12599 | [GitHub](https://github.com/IAAR-Shanghai/CTGSurvey) | Content(Hard) + Attribute(Soft) 제어 분류 체계. Training/Inference-stage 방법론 |
| **Language Model Arithmetic**: Controlled Generation | ICLR 2024 | [GitHub](https://github.com/eth-sri/language-model-arithmetic) | 프롬프트+모델+분류기 조합으로 정밀 LLM 제어 |
| **Top-H Decoding**: Entropy-Aware Sampler | arXiv 2509.02510 | [GitHub](https://github.com/ErfanBaghaei/Top-H-Decoding) | 엔트로피 기반 창의성/일관성 균형. Training-free |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Style-Transfer-in-Text](https://github.com/fuzhenxin/Style-Transfer-in-Text) | 텍스트 스타일 전이 논문 종합 |
| [Text-Style-Transfer-Survey](https://github.com/zhijing-jin/Text_Style_Transfer_Survey) | 텍스트 속성 전이 서베이 |
| [controllable-text-generation topic](https://github.com/topics/controllable-text-generation) | GitHub 토픽 |

---

## A-10. Temporal Knowledge Graph

> 글도비 대응: WorldState (TF-1), FactLedger (TF-2) — 사실상 수동 구축 temporal KG

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Graphiti**: Real-Time Knowledge Graphs for AI Agents | 2025 | [GitHub](https://github.com/getzep/graphiti) | Bi-temporal 모델 (발생 시점 vs 수집 시점). 실시간 점진 갱신. **TF-1 WorldState와 가장 유사한 구현체** |
| **ATOM**: Adaptive Temporal KG Construction using LLMs | arXiv 2510.22590 (2026.01 개정) | [GitHub](https://github.com/AuvaLab/itext2kg) | Atomic fact 분해 → 5-tuple 추출 → 병렬 merge. 93.8% 지연 감소 |
| **MemoTime**: Memory-Augmented TKG Enhanced LLM Reasoning | ACM WebConf 2026 | [arXiv](https://arxiv.org/abs/2510.13614) | Tree of Time 재귀 추론 + self-evolving experience memory. 소형 모델이 GPT-4-Turbo급 달성 |
| **EvoReasoner**: Temporal Reasoning over Evolving KGs | arXiv 2509.15464 | [arXiv](https://arxiv.org/abs/2509.15464) | Confidence 기반 모순 해소 + temporal trend tracking |
| **TG-RAG**: Temporal GraphRAG | arXiv 2510.16715 | [arXiv](https://arxiv.org/abs/2510.16715) | Bi-level temporal graph + 다단위 시간 요약. RAG 결합 |
| LLM-empowered KG Construction Survey | arXiv 2510.20345 | [arXiv](https://arxiv.org/abs/2510.20345) | LLM 기반 KG 구축 서베이. 동적 메모리 기판으로서의 KG |
| Temporal KG Generation Dataset (LLM-supervised) | Nature Scientific Data 2025 | [Nature](https://www.nature.com/articles/s41597-025-05062-0) | LLM distant supervision 기반 TKG 데이터셋 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [tkger](https://github.com/stmrdus/tkger) | Temporal KG Embedding/Reasoning 논문 |
| [dynamic-KG](https://github.com/woojeongjin/dynamic-KG) | Dynamic KG Completion/Reasoning |
| [Awesome-KG-Reasoning](https://github.com/LIANGKE23/Awesome-Knowledge-Graph-Reasoning) | KG Reasoning 종합 |
| [Awesome-DynamicGraphLearning](https://github.com/SpaceLearner/Awesome-DynamicGraphLearning) | Dynamic/Temporal 그래프 학습 |
| [Awesome-TKGC](https://github.com/jiapuwang/Awesome-TKGC) | Temporal KG Completion 전용 |

---

## A-11. Narrative Pacing / Tension / Story Structure

> 글도비 대응: pacing_analyzer, LongTermRep advisory — 긴장감 곡선/구조 반복 감지

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Narrative Theory-Driven LLM Survey** | arXiv 2602.15851 (2026.01) | [arXiv](https://arxiv.org/abs/2602.15851) | 서사 이론 x LLM 생성/이해 종합 서베이. 문학 이론 기반 분류 체계 |
| **SCORE**: Story Coherence and Retrieval Enhancement | arXiv 2503.23512 | [arXiv](https://arxiv.org/abs/2503.23512) | Dynamic State Tracking + Hierarchical Episode Summary + Hybrid Retrieval. 23.6% 일관성 향상 |
| **STORYTELLER**: Enhanced Plot-Planning Framework | ACL 2025 Findings | [GitHub](https://github.com/hyc2026/StoryTeller) | SVO triplet 기반 plot node + NEKG(Narrative Entity KG). 84.33% 인간 선호도 |
| Are LLMs Capable of Human-Level Narratives? | arXiv 2407.13248 | [arXiv](https://arxiv.org/abs/2407.13248) | Story arc + turning point + arousal/valence 분석. GPT-4 pacing 결함 식별 |
| Can LLMs Generate Good Stories? (Narrative Planning) | arXiv 2506.10161 | [arXiv](https://arxiv.org/abs/2506.10161) | Causal soundness, character intentionality, dramatic conflict 벤치마크 |
| LLM Story Generation via Social Structure Network | arXiv 2510.18932 | [arXiv](https://arxiv.org/abs/2510.18932) | 서사 내 사회 구조를 signed character network로 분석 |
| **StoryBox**: Multi-Agent Hybrid Bottom-Up Long Story | arXiv 2510.11618 | [arXiv](https://arxiv.org/abs/2510.11618) | Multi-Agent 협업 bottom-up 장편 생성 |

---

## A-12. Self-Refinement / Iterative Revision

> 글도비 대응: Stage4 REJECT→재시도 루프, CoVe 검증, Director 피드백 → CW 재생성

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Self-Refine**: Iterative Refinement with Self-Feedback | NeurIPS 2023 | [GitHub](https://github.com/madaan/self-refine) | 생성→피드백→개선 반복. 단일 LLM. ~20% 성능 향상 |
| **EVOLVE**: Evolving Self-Refinement via Synergistic Training-Inference | arXiv 2502.05605 | [arXiv](https://arxiv.org/abs/2502.05605) | Training+Inference 시너지 루프. GPT-4o 초과 달성 |
| **Self-Rewarding Reasoning LLM** | 2025 | [GitHub](https://github.com/RLHFlow/Self-rewarding-reasoning-LLM) | 자기 보상 기반 추론 LLM 학습. 자체 생성 데이터만 사용 |
| **SSR**: Socratic Self-Refine for LLM Reasoning | arXiv 2511.10621 | [arXiv](https://arxiv.org/abs/2511.10621) | 소크라테스식 자기반박 추론 |
| Self-Critique and Refinement for Faithful Summarization | arXiv 2512.05387 | [arXiv](https://arxiv.org/abs/2512.05387) | Self-critique → preference optimization. 요약 충실성 |
| Learning to Refine: Self-Refinement of Parallel Reasoning | arXiv 2509.00084 | [arXiv](https://arxiv.org/abs/2509.00084) | 병렬 추론 경로 자기 교정 |
| On the Intrinsic Self-Correction Capability of LLMs | 2025 | [GitHub](https://github.com/HaitaoMao/LLM-self-correction) | 내재적 자기교정 능력 분석: 불확실성 + 잠재 개념 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [llm-self-correction-papers](https://github.com/ryokamoi/llm-self-correction-papers) | LLM 자기교정 논문 (포괄적) |
| [self-correction-llm-papers](https://github.com/teacherpeterpan/self-correction-llm-papers) | 자동 피드백 기반 자기교정 |
| [ICSFSurvey](https://github.com/IAAR-Shanghai/ICSFSurvey) | Self-Correct/Refine/Improve/Play 서베이 |
| [Awesome-LLM-Self-Improvement](https://github.com/dongxiangjue/Awesome-LLM-Self-Improvement) | Inference-Time Self-Improvement (ITSI) |
| [Self-Evolving-Agents](https://github.com/CharlesQ9/Self-Evolving-Agents) | 자기 진화 에이전트 |

---

## A-13. Persona / Character Modeling

> 글도비 대응: NpcDrift advisory, NPC Registry, 캐릭터 보이스 섹션 — NPC 100+명 인격 유지

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **CoSER**: Coordinating LLM-Based Persona Simulation | ICML 2025 | [GitHub](https://github.com/Neph0s/CoSER) | 771권 x 17,966 캐릭터. Given-circumstance acting. CoSER-70B >= GPT-4o. **글도비 NPC 모델링에 가장 직접적** |
| **Persona Vectors**: Monitoring/Controlling Character Traits | arXiv 2507.21509 (Anthropic) | [arXiv](https://arxiv.org/abs/2507.21509) | Activation space에서 trait 방향 추출. 인격 변화 모니터링/교정 |
| **Persona-Aware Contrastive Learning** for Role-Playing | arXiv 2503.17662 | [arXiv](https://arxiv.org/abs/2503.17662) | Annotation-free. Role chain + contrastive learning으로 역할 일관성 |
| **Score Before You Speak**: Persona Consistency via Quality Scores | arXiv 2508.06886 | [GitHub](https://github.com/arpita2512/score_before_you_speak) | 응답 품질 점수로 페르소나 일관성 향상 |
| **OpenCharacter**: Customizable Role-Playing with Synthetic Personas | arXiv 2501.15427 | [arXiv](https://arxiv.org/abs/2501.15427) | 대규모 합성 페르소나 기반 역할극 LLM 학습 |
| Facet-Level Persona Control via Trait-Activated Routing | arXiv 2602.19157 (2026.02) | [arXiv](https://arxiv.org/abs/2602.19157) | Big Five 30-facet 모델 기반 SAE 인격 제어 |
| **Fusian**: Multi-LoRA for MBTI Personality Control | arXiv 2603.15405 (2026.03) | [arXiv](https://arxiv.org/abs/2603.15405) | MBTI 연속 성격 제어. Multi-LoRA 융합 |
| Four-Quadrant Taxonomy for LLM Persona Design | arXiv 2511.02979 | [arXiv](https://arxiv.org/abs/2511.02979) | 장기 감정 일관성 프레임워크 |
| **Act-LLM**: Character-Centric Role-Playing with Dual-Term Memory | SSRN 2025 | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5230378) | Long-term(구조화DB) + Short-term(컨텍스트) 이중 메모리 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [awesome-llm-role-playing-with-persona](https://github.com/Neph0s/awesome-llm-role-playing-with-persona) | LLM 역할극 + 페르소나 논문 (포괄적) |
| [PersonaLLM-Survey](https://github.com/MiuLab/PersonaLLM-Survey) | Two Tales of Persona in LLMs 서베이 |
| [PersonaLLM NeurIPS 2025 Workshop](https://personallmworkshop.github.io/) | NeurIPS 2025 Persona 워크숍 |

---

## A-14. LLM-as-Judge for Creative Writing

> 글도비 대응: Director 판정, Advisory chain 전체, Ensemble 채점

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **LLMs-as-Judges Survey** (종합) | arXiv 2412.05579 | [GitHub](https://github.com/CSHaitao/Awesome-LLMs-as-Judges) | Functionality/Methodology/Applications/Meta-eval/Limitations 5축 |
| **A Survey on LLM-as-a-Judge** | arXiv 2411.15594 | [Project](https://llm-as-a-judge.github.io/) | LLM 판정자 종합 서베이. 확장성/비용/일관성 분석 |
| Igniting Creative Writing: LLM-as-Judge vs Multi-Agent Rewards | arXiv 2508.21476 | [arXiv](https://arxiv.org/abs/2508.21476) | 소형 LM 창작 품질 향상. Judge vs Refined Rewards 비교 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-LLM-as-a-judge](https://github.com/llm-as-a-judge/Awesome-LLM-as-a-judge) | LLM 판정자 논문 (daily update) |
| [Awesome-LLMs-as-Judges](https://github.com/CSHaitao/Awesome-LLMs-as-Judges) | LLM 기반 평가 방법론 |

---

## A-15. Prompt Compression / Optimization

> 글도비 대응: PromptBuilder (920줄+), mandatory_context 400K 예산 — 같은 예산 내 더 많은 정보

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Prompt Compression Survey** | NAACL 2025 Oral | [GitHub](https://github.com/ZongqianLi/Prompt-Compression-Survey) | 프롬프트 압축 종합 서베이 |
| **LLMLingua** (1/2/Long): Prompt Compression | EMNLP'23 + ACL'24 | [GitHub](https://github.com/microsoft/LLMLingua) | 최대 20x 압축, 최소 성능 손실. Microsoft |
| **500xCompressor**: Generalized Prompt Compression | ACL 2025 Main | [GitHub](https://github.com/ZongqianLi/500xCompressor) | 500 토큰 → 1 special 토큰. 극한 압축 |
| Dynamic Compressing Prompts for Efficient Inference | arXiv 2504.11004 | [arXiv](https://arxiv.org/abs/2504.11004) | 동적 프롬프트 압축 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-Collection-Token-Reduction](https://github.com/ZLKong/Awesome-Collection-Token-Reduction) | 토큰 축소(pruning/merging/clustering) 기법 |
| [Awesome-LLM-Prompt-Optimization](https://github.com/jxzhangjhu/Awesome-LLM-Prompt-Optimization) | 프롬프트 최적화/튜닝 방법론 |
| [Awesome-Multimodal-Token-Compression](https://github.com/cokeshao/Awesome-Multimodal-Token-Compression) | TMLR 2026 서베이. 멀티모달 토큰 압축 |
| [prompt-optimizer](https://github.com/vaibkumr/prompt-optimizer) | 실용 프롬프트 최적화 도구 |

---

## A-16. Dialogue in Fiction / Interactive Drama

> 글도비 대응: ChiefWriter 대사 생성, NPC 대사체 분리, 무협 대화 패턴

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Open-Theatre**: Open-Source LLM Interactive Drama Toolkit | arXiv 2509.16713 | [GitHub](https://github.com/johnnie193/Open-Theatre) | 계층적 메모리(global/summary/archive) + multi-agent. **글도비 Stage4 메모리 구조와 유사** |
| Enhanced Immersion and Agency for LLM-based Interactive Drama | arXiv 2502.17878 | [arXiv](https://arxiv.org/abs/2502.17878) | Plot-based reflection으로 player-centered story curve 조정 |
| **Story2Game**: Generating Everything in Interactive Fiction | arXiv 2505.03547 | [arXiv](https://arxiv.org/abs/2505.03547) | 스토리 → 게임 월드 → 인터랙션 코드 자동 생성 |
| **DramaLLM**: From Role-Play to Drama-Interaction | ACL 2024 | [GitHub](https://github.com/vickywu1022/DramaLLM) | 역할극 → 드라마 상호작용 전환 |
| Generative AI & Fictionality: How Novels Power LLMs | arXiv 2603.01220 (2026.03) | [arXiv](https://arxiv.org/abs/2603.01220) | 소설이 LLM을 어떻게 구동하는가 — 허구성 분석 |
| Multi-Agent Character Simulation for Story Writing | in2writing 2025 | [ACL](https://aclanthology.org/2025.in2writing-1.9.pdf) | Director Agent + Character Agent 역할극 기반 집필 |

---

## A-17. Plot Hole Detection / Contradiction Finding

> 글도비 대응: TruthGate, ConStory-Checker와 유사한 Advisory 파이프라인

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **FlawedFictions**: Plot Hole Detection in LLM Stories | arXiv 2504.11900 | [arXiv](https://arxiv.org/abs/2504.11900) | FlawedFictionsMaker 합성 알고리즘 + FlawedFictions 벤치마크. SOTA LLM도 스토리 길이 증가 시 급격히 실패 |
| **Lost in Stories**: Consistency Bugs (→ A-2 참조) | arXiv 2603.05890 (2026.03) | — | 5대 에러 카테고리 19 세부 유형. ConStory-Checker 자동 감지 파이프라인 |
| Lightweight Latent Reasoning for Narrative Tasks | arXiv 2512.02240 | [arXiv](https://arxiv.org/abs/2512.02240) | FlawedFictions 벤치마크 활용 평가 |

---

## A-18. Hierarchical / Book-length Summarization

> 글도비 대응: TF-4 Summary Pyramid, Episode Bible, Arc Summary — 계층적 요약 생성/소비

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **NexusSum**: Hierarchical LLM Agents for Long-Form Narrative | ACL 2025 Long | [arXiv](https://arxiv.org/abs/2505.24575) | Multi-agent 파이프라인. Dialogue-to-Description + Hierarchical Multi-LLM. BERTScore 30% 향상 |
| **BooookScore**: Book-length Summarization | ICLR 2024 Oral | [GitHub](https://github.com/lilakk/BooookScore) | Incremental updating vs hierarchical merging 비교. 8가지 coherence error 분류 |
| Context-Aware Hierarchical Merging for Long Doc Summary | arXiv 2502.00977 | [arXiv](https://arxiv.org/abs/2502.00977) | 100K+ 토큰 문서. 재귀 merge 시 할루시네이션 방지를 위한 컨텍스트 보강 |
| **SciZoom**: Hierarchical Scientific Summarization Benchmark | arXiv 2603.16131 (2026.03) | [arXiv](https://arxiv.org/abs/2603.16131) | 44,946편 x 3계층 (Abstract/Contributions/TL;DR). 압축비 600:1 |
| CoTHSSum: CoT + Hierarchical Segmentation | 2025 | [Springer](https://link.springer.com/article/10.1007/s44443-025-00041-2) | Chain-of-Thought + 계층 분할 장문 요약 |
| Adversarial Agentic Collaboration for Long Doc Summary | arXiv 2509.20900 | [arXiv](https://arxiv.org/abs/2509.20900) | 적대적 에이전트 협업 요약 |
| Agent-as-Judge for Factual Summarization of Long Narratives | EMNLP 2025 | [ACL](https://aclanthology.org/2025.emnlp-main.1204.pdf) | Agent 기반 팩트 요약 판정 |

---

## A-19. Emotion / Sentiment Arc Tracking

> 글도비 대응: ChainLink emotional_state, pacing_analyzer, StyleSignal advisory

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Affective Computing in the Era of LLMs**: A Survey (NLP) | arXiv 2408.04638 (2025 개정) | [arXiv](https://arxiv.org/abs/2408.04638) | NLP 관점 감정 컴퓨팅 종합 서베이 |
| **MER 2025**: Affective Computing Meets LLMs | arXiv 2504.19423 | [arXiv](https://arxiv.org/abs/2504.19423) | 사전 정의 감정 분류 → LLM 생성적 방법 패러다임 전환 |
| Collaborative Affective Computing with LLMs | arXiv 2506.01698 | [arXiv](https://arxiv.org/abs/2506.01698) | 다중 LLM 협업 감정 분석. 인간 수준 사회적 지능 접근 |
| Decoding Emotion in the Deep: How LLMs Represent Emotion | arXiv 2510.04064 | [arXiv](https://arxiv.org/abs/2510.04064) | LLM 내부 감정 표현/유지/표출 메커니즘 |
| MultiSentimentArcs: Coherence in Multimodal Sentiment for Narratives | Frontiers 2024 | [Frontiers](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2024.1444549/full) | 장편 서사 내 감정 호 일관성 측정. 멀티모달 벤치마크 |

---

## A-20. GraphRAG / Graph-based Retrieval

> 글도비 대응: Vector memory (hybrid search), FactLedger 엔티티 관계, WorldState 관계망

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Microsoft GraphRAG** | 2024 | [GitHub](https://github.com/microsoft/graphrag) | 모듈형 Graph-based RAG. 커뮤니티 요약 기반 검색 |
| **LightRAG**: Simple and Fast RAG | EMNLP 2025 | [GitHub](https://github.com/HKUDS/LightRAG) | 경량 GraphRAG. 29.6K stars. 멀티모달 지원 |
| **GFM-RAG**: Graph Foundation Model for RAG | NeurIPS 2025 + ICLR 2026 | [GitHub](https://github.com/RManLuo/gfm-rag) | Graph Foundation Model 기반 RAG |
| **SubgraphRAG**: Simple is Effective | ICLR 2025 | [GitHub](https://github.com/Graph-COM/SubgraphRAG) | KG + LLM 결합 RAG. 서브그래프 단위 검색 |
| **HyperGraphRAG**: Hypergraph-Structured Knowledge | NeurIPS 2025 | [GitHub](https://github.com/LHRLAB/HyperGraphRAG) | 하이퍼그래프 구조 지식 표현 RAG |
| **SimGRAG**: Similar Subgraphs for KG-Driven RAG | ACL 2025 | [GitHub](https://github.com/YZ-Cai/SimGRAG) | 유사 서브그래프 활용 RAG |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-GraphRAG](https://github.com/DEEP-PolyU/Awesome-GraphRAG) | GraphRAG 논문/벤치마크/오픈소스 종합 |

---

## A-21. LLM Ensemble / Best-of-N

> 글도비 대응: ArcEnsemble, BlueprintEnsemble, DirectorEnsemble — 다전략 앙상블 채점

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **LLM Ensemble Survey**: Harnessing Multiple LLMs | arXiv 2502.18036 | [arXiv](https://arxiv.org/abs/2502.18036) | Before/During/After-inference 3분류. 7방법론 체계화 |
| **Ensemble Learning for LLMs** (Text+Code) | arXiv 2503.13505 | [arXiv](https://arxiv.org/abs/2503.13505) | 텍스트+코드 생성 앙상블 서베이 |
| **Best-of-Inf**: Asymptotic Test-Time Compute | arXiv 2509.21091 | [arXiv](https://arxiv.org/abs/2509.21091) | Test-time compute 무한 확장 이론 |
| **EMORL**: Ensemble Multi-Objective RL for LLM Fine-Tuning | arXiv 2505.02579 | [arXiv](https://arxiv.org/abs/2505.02579) | 다목적 RL 앙상블 fine-tuning |
| Multi-LLM Repeated Sampling (ModelSwitch) | arXiv 2504.00762 | [arXiv](https://arxiv.org/abs/2504.00762) | Consistency-accuracy 상관관계 활용. 효율적 multi-LLM 반복 샘플링 |
| Stable LLM Ensemble: Representativeness x Diversity | arXiv 2510.13143 | [arXiv](https://arxiv.org/abs/2510.13143) | 예제 대표성 x 다양성 상호작용 |

---

## A-22. Structured Output / JSON Extraction

> **→ Appendix B-2 참조** (Gemini response_mime_type으로 이미 해결, constrained decoding은 API 소비자 적용 불가)

---

## A-23. Agentic Workflow Orchestration

> 글도비 대응: Stage 0→1→2→3→4 파이프라인, Stage4Orchestrator, InterviewRound

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **AFlow**: Automating Agentic Workflow Generation | ICLR 2025 Oral (top 1.8%) | [GitHub](https://github.com/FoundationAgents/AFlow) | MCTS 기반 워크플로우 자동 생성. Operator = Generate/Review/Revise/Ensemble. **글도비 Stage 구조와 직접 대응** |
| **DAAO**: Difficulty-Aware Agentic Orchestration | arXiv 2509.11079 (2026.02 개정) | [arXiv](https://arxiv.org/abs/2509.11079) | 쿼리 난이도 기반 동적 워크플로우 + LLM 배정 |
| Efficient LLM Serving for Agentic Workflows (Data Systems) | arXiv 2603.16104 (2026.03) | [arXiv](https://arxiv.org/abs/2603.16104) | 데이터 시스템 관점 에이전트 워크플로우 서빙 최적화 |
| Production-Grade Agentic AI Workflows Guide | arXiv 2512.08769 | [arXiv](https://arxiv.org/abs/2512.08769) | 프로덕션급 에이전틱 워크플로우 설계/배포 가이드 |
| Agentic AI Architectures & Taxonomies | arXiv 2601.12560 (2026.01) | [arXiv](https://arxiv.org/abs/2601.12560) | LLM Agent 아키텍처 통합 분류 체계 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-Agentic-Reasoning](https://github.com/weitianxin/Awesome-Agentic-Reasoning) | Agentic Reasoning 논문 |
| [Awesome-Self-Evolving-Agents](https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents) | 자기 진화 에이전트 서베이 |

---

## A-24. API Cost Optimization / LLM Cascade

> 글도비 대응: Gemini Context Caching (90% 할인), 전략별 모델 선택, 조건부 지능

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **FrugalGPT**: Reducing Cost + Improving Performance | TMLR | [GitHub](https://github.com/stanford-futuredata/FrugalGPT) | LLM cascade — 저렴한 모델 먼저, 필요 시만 고급 모델. GPT-4 성능 98% 비용 절감 |
| **TRIM**: Token Reduction for Cost-Effective Generation | arXiv 2412.07682 | [arXiv](https://arxiv.org/abs/2412.07682) | 의미적 무관 토큰 생략. GPT-4o 평균 19.4% 토큰 절감 |
| **Argus**: Token-Aware Distributed LLM Inference | arXiv 2512.22925 | [arXiv](https://arxiv.org/abs/2512.22925) | 출력 길이 예측 기반 edge-cloud 분산 추론 |
| Token Reduction Beyond Efficiency | arXiv 2505.18227 | [arXiv](https://arxiv.org/abs/2505.18227) | Vision/Language/Multimodal 토큰 축소 종합 |
| Towards Optimizing the Costs of LLM Usage | arXiv 2402.01742 | [arXiv](https://arxiv.org/abs/2402.01742) | LLM 사용 비용 최적화 체계 |

---

## A-25. RLHF / RL for Creative Writing

> **→ Appendix B-3 참조** (모델 fine-tuning 필요, Gemini API 소비자 적용 불가)

---

## A-26. Korean LLM / Language-Specific (축약)

> 글도비 대응: 한국어 소설 생성, 한글 토큰 효율, 무협 장르 특수 어휘
>
> 참고: 글도비는 Gemini API를 사용하므로 한국어 LLM 모델 학습 논문은 직접 적용 불가. 무협 스타일 분석만 직접 참고 가치.

| 논문 | 학회/시기 | 핵심 |
|------|----------|------|
| Wuxia Fiction Stylistic Analysis (중→영 번역) | arXiv 2506.13013 | 무협 소설 스타일 지표 분석 (어휘 길이, 동사-형용사 비율 등). **글도비 무협 StyleGuard에 직접 참고** |
| **Thunder-LLM**: Efficiently Adapting LLMs to Korean | arXiv 2506.21595 | 한국어 30B 토큰 한계 극복. 체계적 데이터 큐레이션 |
| **Llama-3-Motif**: Expanding Korean Capabilities (102B) | arXiv 2509.03972 | LlamaPro + Masked Structure Growth. 102B 파라미터 |
| **KatFishNet**: Detecting LLM-Generated Korean Text | arXiv 2503.00032 | 한국어 LLM 생성 텍스트 탐지. AUROC 19.78% 향상 |
| Optimizing Language Augmentation for Multilingual LLMs: Korean | arXiv 2403.10882 | 다국어 LLM 한국어 증강 최적화 |

---

## A-27. World Building / Procedural Simulation

> 글도비 대응: WorldStateManager 9필드 스키마, 세계 법칙, 조직/NPC 생태계

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **PragWorld**: LLM Local World Model Benchmark | AAAI 2026 | — | 최소 언어 변경 + 대화 동역학 기반 세계 모델 평가 |
| **Patchview**: LLM-Powered Worldbuilding with Generative Dust | UIST 2024 | [Paper](https://johnr0.github.io/assets/publications/UIST24-Patchview.pdf) | 생성적 먼지 기반 월드빌딩 도구 |
| Procedural Content Generation in Games: LLM Integration Survey | arXiv 2410.15644 | [arXiv](https://arxiv.org/abs/2410.15644) | PCG + LLM 통합 서베이 |
| Generative Agent Simulations of 1,000 People | arXiv 2411.10109 | [arXiv](https://arxiv.org/abs/2411.10109) | 1,000명 규모 에이전트 시뮬레이션 |
| Symmetry-Aware LLM-Driven Interactive Fiction Graphs (Twine) | MDPI 2025 | [MDPI](https://www.mdpi.com/2073-8994/18/1/113) | 대칭성 인식 인터랙티브 픽션 그래프 생성/복구 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-World-Models](https://github.com/leofan90/Awesome-World-Models) | World Models 종합 (비디오/로봇/자율주행 포함) |
| [awesome-llm-human-simulation](https://github.com/Persdre/awesome-llm-human-simulation) | ICLR 2025 BlogPost. LLM 인간 시뮬레이션 |

---

## A-28. Guardrails / Content Safety for Fiction (축약)

> 글도비 대응: GenreGuard (금기어/패턴), WorkGuard (작품별 커스텀), forbidden_terms
>
> 참고: 글도비 가드레일은 이미 GenreGuard → WorkGuard → StyleGuard 3계층 구축 완료. 아래는 향후 참고용.

| 논문 | 학회/시기 | 핵심 |
|------|----------|------|
| Guardrails for Trust, Safety, and Ethical LLM Deployment | arXiv 2601.14298 (2026.01) | 유연 적응형 안전 모듈 체계. LLM 개발/배포 전 주기 |
| **R2-Guard** | ICLR 2025 | 2단계 가드레일 |
| **RigorLLM**: Resilient Guardrails | arXiv 2403.13031 | 원치 않는 콘텐츠 방어. 탄력적 가드레일 |
| Building Domain-specific Guardrails in Production | arXiv 2408.01452 | 도메인 특화 프로덕션 가드레일 구축 |

---

## A-29. "어디서 찾을지" — Memory Routing / Selective Retrieval / Tiered Memory

> **핵심 질문**: 메모리를 통으로 주입하지 않고, **"이 질문에 필요한 정보가 어디에 있는지"를 먼저 판단**한 뒤
> 해당 저장소만 선택적으로 접근하는 방법론.
>
> 글도비 대응: WorldState(TF-1) vs FactLedger(TF-2) vs ChainLink(TF-3) vs Vector Memory vs Episode Bible
> — 현재는 전부 로드 후 예산 내 truncation. **라우팅/포인터 기반 선택적 접근으로 전환 가능**

### A-29a. Memory Store Routing (어디서 꺼낼지)

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Did You Check the Right Pocket?** Cost-Sensitive Store Routing | arXiv 2603.15658 (2026.03) | [arXiv](https://arxiv.org/abs/2603.15658) | **메모리 검색을 store-routing 문제로 정식화**. Oracle router: 더 적은 토큰으로 더 높은 정확도. 비용-정확도 trade-off 의사결정 이론. **TF-1/2/3/VecMem 선택 라우팅에 직접 적용 가능** |
| **MemR3**: Memory Retrieval via Reflective Reasoning | arXiv 2512.20237 | [arXiv](https://arxiv.org/abs/2512.20237) | Retrieve→Reflect→Answer 폐쇄 루프 컨트롤러. Evidence-gap tracker로 "아직 뭘 모르는지" 추적. **Advisory의 "어디서 더 찾아야 하나" 판단에 활용 가능** |
| **Diagnosing Retrieval vs. Utilization Bottlenecks** | arXiv 2603.02473 (2026.03) | [GitHub](https://github.com/boqiny/memory-probe) | 3x3 실험 (write 전략 x retrieval 방법). **핵심 발견: retrieval 방법이 write 전략보다 20pp 더 중요**. Raw chunk가 비싼 요약보다 낫다 |
| **Self-Route**: RAG vs Long-Context Hybrid | arXiv 2407.16833 (Google DeepMind) | [arXiv](https://arxiv.org/abs/2407.16833) | 모델 self-reflection으로 RAG/LC 라우팅. 60%+ 쿼리는 RAG=LC → 비용 65% 절감 |
| **SR-RAG**: Self-Routing RAG with Knowledge Verbalization | arXiv 2504.01018 | [arXiv](https://arxiv.org/abs/2504.01018) | Internal/External 지식 소스 선택을 hidden state + nearest-neighbor 정책으로 결정 |
| **A-RAG**: Scaling Agentic RAG via Hierarchical Retrieval | arXiv 2602.03442 (2026.02) | [arXiv](https://arxiv.org/abs/2602.03442) | Keyword search / Semantic search / Chunk read 3개 도구 노출. 에이전트가 자율적으로 다단위 검색 |
| **AIR-RAG**: Adaptive Iterative Retrieval | 2025.12 | [GitHub](https://github.com/aialt/AIR-RAG) | 적응적 피드백으로 retrieval ranking + document refinement 반복 최적화 |
| **Adaptive-RAG**: Adapting through Question Complexity | NAACL 2024 | [arXiv](https://arxiv.org/abs/2403.14403) | 쿼리 복잡도 기반 검색 전략 동적 선택 (단순→정교) |
| **Self-RAG**: Learning to Retrieve, Generate, Critique | ICLR 2024 | [GitHub](https://github.com/AkariAsai/self-rag) | Reflection token으로 "검색할지 말지" 자율 판단. **글도비 Advisory "검색 필요 여부" 판단 원형** |

### A-29b. Memory Admission Control (뭘 저장할지)

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **A-MAC**: Adaptive Memory Admission Control | arXiv 2603.04549 (2026.03) | [arXiv](https://arxiv.org/abs/2603.04549) | 메모리 입장을 5축 의사결정으로 분해: **Future Utility, Factual Confidence, Semantic Novelty, Temporal Recency, Content Type Prior**. Rule-based + LLM hybrid. **FactLedger 입장 정책에 직접 적용 가능** |
| **D-MEM**: Dopamine-Gated Agentic Memory via RPE Routing | arXiv 2603.14597 (2026.03) | [arXiv](https://arxiv.org/abs/2603.14597) | 도파민 영감 Fast/Slow 라우팅. 낮은 RPE(일상) → O(1) 버퍼. 높은 RPE(모순/변화) → O(N) 진화 파이프라인. **토큰 80%+ 절감. TF-1 WorldState "변화가 있을 때만 갱신"에 적용** |
| **CLAG**: Adaptive Memory Organization via Clustering | arXiv 2603.15421 (2026.03) | [arXiv](https://arxiv.org/abs/2603.15421) | 클러스터링 기반 메모리 조직. 토픽별 프로파일 자동 생성 → 2단계 검색(클러스터 필터 → 로컬 검색). **cross-topic 간섭 제거** |

### A-29c. Tiered / Hierarchical Memory Architecture (계층형 저장)

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **H-MEM**: Hierarchical Memory for High-Efficiency Long-Term Reasoning | arXiv 2507.22925 | [arXiv](https://arxiv.org/abs/2507.22925) | 다층 의미 추상화 + **위치 인덱스 포인터**로 하위 메모리 연결. 유사도 계산 없이 계층적 탐색. **TF Summary Pyramid의 학술적 근거** |
| **TierMem**: Provenance-Aware Tiered Memory for Agents | arXiv 2602.17913 (2026.02) | [arXiv](https://arxiv.org/abs/2602.17913) | **Write-before-query barrier** 문제 정식화. 요약(lossy) + 원본 로그(provenance) 이중 보관. **추론 시점에 evidence allocation**. **글도비 "요약은 있되 원본도 보존" 패턴과 정확히 일치** |
| **A-Mem**: Agentic Memory for LLM Agents | NeurIPS 2025 | [GitHub](https://github.com/agiresearch/A-mem) | Zettelkasten 원리. LLM이 키워드/컨텍스트/태그 자동 생성 → 동적 링크. 구조화 속성 기반 검색 |
| **Mem0**: Production-Ready Scalable Long-Term Memory | TheWebConf 2025 | [GitHub](https://github.com/mem0ai/mem0) | 프로덕션급 메모리 레이어. 26% 정확도 UP, 90% 토큰 DOWN. Graph-based 관계 표현 변형 포함 |
| **CraniMem**: Cranial Inspired Gated and Bounded Memory | arXiv 2603.15642 (2026.03) | [arXiv](https://arxiv.org/abs/2603.15642) | 두개골 영감 게이트 + 경계 메모리 |
| Human-Like Remembering and Forgetting (ACT-R) | HAI 2025 | [ACM](https://dl.acm.org/doi/10.1145/3765766.3765803) | ACT-R 인지 아키텍처 기반 기억/망각 |
| AI Agents Need Memory Control Over More Context | arXiv 2601.11653 (2026.01) | [arXiv](https://arxiv.org/abs/2601.11653) | 에이전트에게 더 많은 컨텍스트 제어 권한 부여 필요성 |
| **Recursive Language Models** (RLM) | arXiv 2512.24601 | [Blog](https://www.primeintellect.ai/blog/rlm) | 10M+ 토큰 스케일에서 다른 방법 대비 이중 자릿수 우위. **재귀적 메모리 접근** |

### A-29d. Memory System Surveys & Benchmarks

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **Memory for Autonomous LLM Agents**: Mechanisms, Evaluation, Emerging Frontiers | arXiv 2603.07670 (2026.03) | [arXiv](https://arxiv.org/abs/2603.07670) | **최신 종합 서베이**. Pattern A~E 분류: 버퍼, 구조화 DB, vector store, cold archive, 학습 컨트롤러 |
| **Anatomy of Agentic Memory**: Taxonomy and Empirical Analysis | arXiv 2602.19320 (2026.02) | [arXiv](https://arxiv.org/abs/2602.19320) | 에이전트 메모리 해부학. 평가/시스템 한계 실증 분석 |
| From Storage to Experience: Evolution of LLM Agent Memory | Preprints 2026.01 | [Preprints](https://www.preprints.org/manuscript/202601.0618) | 저장 → 경험으로의 메모리 진화 서베이 |
| **AMA-Bench**: Evaluating Long-Horizon Memory for Agentic Apps | arXiv 2602.22769 (2026.02) | [arXiv](https://arxiv.org/abs/2602.22769) | 장기 에이전트 메모리 벤치마크 |
| **MemMA**: Coordinating Memory Cycle through Multi-Agent Reasoning | arXiv 2603.18718 (2026.03) | [arXiv](https://arxiv.org/abs/2603.18718) | Multi-Agent 메모리 사이클 협조. In-Situ 자기 진화 |
| **ActMem**: Bridging Retrieval and Reasoning in LLM Agents | arXiv 2603.00026 (2026.03) | [arXiv](https://arxiv.org/abs/2603.00026) | 검색과 추론 사이 격차 해소 |
| **AdaMem**: Adaptive User-Centric Memory for Long-Horizon Dialogue | arXiv 2603.16496 (2026.03) | [arXiv](https://arxiv.org/abs/2603.16496) | 사용자 중심 적응형 메모리 |
| Multi-Agent Memory from Computer Architecture Perspective | arXiv 2603.10062 (2026.03) | [arXiv](https://arxiv.org/abs/2603.10062) | **컴퓨터 아키텍처 관점** 다중 에이전트 메모리 |
| Retrieval-Augmented LLM Agents: Learning to Learn from Experience | arXiv 2603.18272 (2026.03) | [arXiv](https://arxiv.org/abs/2603.18272) | 경험에서 학습하는 RAG 에이전트 |
| Context Length Alone Hurts LLM Performance Despite Perfect Retrieval | arXiv 2510.05381 | [arXiv](https://arxiv.org/abs/2510.05381) | **완벽한 검색이라도 컨텍스트가 길면 성능 하락** — 선택적 주입의 근거 |
| **SimpleMem**: Efficient Lifelong Memory for LLM Agents | 2025 | [GitHub](https://github.com/aiming-lab/SimpleMem) | 경량 평생 메모리 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Agent-Memory-Paper-List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List) | AI Agent 메모리 논문 종합 (Survey 동반, **최고 추천**) |
| [general-agentic-memory](https://github.com/VectorSpaceLab/general-agentic-memory) | 범용 에이전트 메모리 시스템 (deep-research 기반) |

---

# Part B. Sparse Attention / Memory → 글도비 TF 적용 가능성 분석

## 0. 논문 소스 목록

| 약어 | 논문/프로젝트 | 핵심 기법 |
|------|-------------|----------|
| **MSA** | [Memory Sparse Attention (EverMind, 2026.03)](https://github.com/EverMind-AI/MSA) | 100M 토큰 end-to-end 메모리, Doc-wise RoPE, KV 압축 |
| **SpargeAttn** | [SpargeAttention (ICML 2025)](https://github.com/thu-ml/SpargeAttn) | Training-free sparse attention, 모든 모델 추론 가속 |
| **XAttn** | [XAttention (ICML 2025)](https://github.com/mit-han-lab/x-attention) | Block Sparse + Antidiagonal Scoring |
| **SparseD** | [SparseD (ICLR 2026)](https://github.com/INV-WZQ/SparseD) | Diffusion LM용 sparse attention |
| **MARTI** | [MARTI (ICLR 2026)](https://github.com/TsinghuaC3I/MARTI) | Multi-Agent RL Training & Inference |
| **MInference** | [MInference (NeurIPS 2024)](https://github.com/microsoft/MInference) | Dynamic sparse, 1M pre-fill 10x 가속 |
| **KASCADE** | [KASCADE (2024.12)](https://arxiv.org/pdf/2512.16391) | Anchor-layer Top-k → reuse-layer 전파 |
| **LONGMEM** | [LONGMEM (NeurIPS 2023)](https://arxiv.org/pdf/2306.07174) | Non-differentiable memory bank + decoupled module |
| **InfLLM** | [InfLLM (NeurIPS 2024)](https://arxiv.org/abs/2402.04617) | Sliding window + context memory, training-free |
| **SparseFrontier** | [The Sparse Frontier (2026.01)](https://arxiv.org/abs/2504.17768) | 6 방법 x 128K x sparsity 0.95 trade-off |

---

## 1. 글도비 TF 시스템 현황 요약

```
+---------------------------------------------------------+
|                    Stage 4 Pipeline                      |
|                                                          |
|  +----------+   +----------+   +----------+   +--------+|
|  | TF-1     |   | TF-2     |   | TF-3     |   | TF-4   ||
|  |WorldState|   |FactLedger|   |ChainLink |   |Summary ||
|  | ~5K JSON |   | ~50K max |   | per-EP   |   |Pyramid ||
|  +----+-----+   +----+-----+   +----+-----+   +----+---+|
|       |              |              |              |      |
|       +--------------+------+-------+--------------+     |
|                             |                            |
|              +--------------v--------------+             |
|              |  Stage4ContextBuilder       |             |
|              |  Tier 0/1/2 조립            |             |
|              |  예산: 400K 문자            |             |
|              +--------------+--------------+             |
|                             |                            |
|              +--------------v--------------+             |
|              |  Gemini Context Caching     |             |
|              |  min 50K, TTL 600/1800s     |             |
|              |  90% 비용 절감 (HIT 시)     |             |
|              +-----------------------------+             |
+---------------------------------------------------------+
```

### 현재 수치

| 항목 | 현재 값 | 비고 |
|------|---------|------|
| mandatory_context_max | 400,000자 | CW/Director 상한 |
| lookback_total_chars | 40,000자 | 최근 화 참조 |
| lookback_excerpt_chars | 5,000자 | 화별 발췌 |
| FactLedger MAX_SUMMARY | 50,000자 | 누적 팩트 상한 |
| FactLedger MAX_HISTORY | 100건/엔티티 | 히스토리 깊이 |
| WorldState | ~5K JSON | 현재 세계 스냅샷 |
| Context Cache min | 50,000자 | 캐싱 임계값 |
| Context Cache TTL | 600/1,800초 | intra/cross-episode |
| Gemini 윈도우 | 1,000,000 토큰 | 사용률 27-37% 피크 |
| Advisory 병렬 | 9개, 60초/개 | ThreadPoolExecutor |

---

## 2. 적용 가능성 매핑

### 2.1 MSA → TF-1/TF-2 장기 메모리 계층

**MSA 핵심 아이디어**:
- 100M 토큰을 **sparse latent state**로 압축하여 near-linear 복잡도 달성
- Document-wise RoPE: 문서 단위로 위치 인코딩 → 문서 간 간섭 최소화
- KV cache 압축 + Memory Parallel 추론

**글도비 대응 구조**:

| MSA 개념 | 글도비 현재 | 적용 가능 지점 |
|----------|-----------|--------------|
| Sparse latent state | WorldState ~5K JSON | **WSM 계층화**: 자주 접근하는 "hot state" vs 드문 "cold state" 분리 |
| Document-wise RoPE | chain_link_{ep} per-EP | **이미 유사**: 에피소드별 독립 앵커, 하지만 cross-EP 관계는 flat |
| KV cache 압축 | Gemini Context Caching | **압축 계층 추가 가능**: 50K 미만 → 버림이 아니라 요약 캐시 |
| Memory Parallel | Advisory 9개 병렬 | **이미 적용 중**, 확장 여지: advisory별 dedicated memory slice |

**구체적 적용 시나리오 — WSM Hot/Cold 분리**:

```
현재:
  WorldState = 단일 JSON (~5K)
  → 200화 시 alive_npcs 100+명, relationships 200+건
  → 매 화 전체 로드, 전체 주입

MSA 영감 적용:
  WorldState = Hot Layer (자주 참조, ~2K)
    - protagonist, active_plots, cumulative_elapsed
    - 최근 10화 내 등장 NPC만
  + Cold Layer (드물게 참조, ~10K+)
    - 50화 이상 미등장 NPC
    - 해소된 plots (resolved)
    - 파괴된 entities 상세

  컨텍스트 주입 시:
    Hot Layer → 항상 mandatory_context에 포함
    Cold Layer → retrieval query 매칭 시에만 주입 (sparse access)
```

**ROI 판정**: **MEDIUM-HIGH**
- 200화 이상에서 WorldState 비대화 시 유의미
- 현재 5K는 아직 여유 있으나, NPC 100+명 시점에서 필요

---

### 2.2 InfLLM / LONGMEM → TF-2 FactLedger 메모리 뱅크

**InfLLM 핵심 아이디어**:
- Sliding window + **context memory bank**: 윈도우 밖 토큰을 memory에 저장
- 관련성 높은 토큰만 memory에서 retrieval → 윈도우에 주입

**LONGMEM 핵심 아이디어**:
- Non-differentiable memory bank (학습 불필요)
- Decoupled memory module: in-context attention + memory attention 분리
- **Staleness 문제** 해결: 오래된 메모리의 관련성 감쇠

**글도비 대응 구조**:

| 논문 개념 | 글도비 현재 | 적용 가능 지점 |
|----------|-----------|--------------|
| Sliding window | Tier 1: 직전 1화 전문 | **이미 유사**: 직전 화만 full-text |
| Context memory bank | FactLedger 50K | **확장 가능**: FactLedger를 retrieval-backed memory bank으로 전환 |
| Staleness decay | MAX_HISTORY=100 hard cap | **감쇠 함수 도입 가능**: 오래된 fact의 relevance weight 감소 |
| Decoupled module | Advisory chain (관측 전용) | **이미 분리**: Advisory는 LLM 판단 불변, 관측만 |

**구체적 적용 시나리오 — FactLedger Relevance Decay**:

```
현재:
  FactLedger.characters["장백산"] = {
    "status": "alive",
    "history": [ep1_entry, ep5_entry, ..., ep200_entry]  # 최대 100건
  }
  → to_summary() 시 전체 history를 flat하게 직렬화
  → 200화 기준: 50K 자 상한에 도달 → 균등 truncation

LONGMEM 영감 적용:
  FactLedger.to_summary(target_ep=N) 시:
    - recency_weight: 최근 20화 내 fact → weight 1.0
    - decay_weight: 21~50화 전 fact → weight 0.5
    - archive_weight: 50화+ 전 fact → weight 0.1 (landmark만 보존)

  결과:
    - 같은 50K 예산 내에서 최근 사실 밀도 2-3x 향상
    - "100화 전 장백산이 어디 있었나" → cold retrieval로 별도 조회
```

**ROI 판정**: **HIGH**
- 현재 50K 상한에 이미 도달 가능한 구간
- 균등 truncation 대비 관련성 기반 감쇠가 모순 방지에 직접 기여
- TruthGate advisory의 정밀도 향상에 연결

---

### 2.3 MInference / KASCADE → Lookback 계층 최적화

**MInference 핵심**:
- Dynamic sparse attention: **A-shape, Vertical-Slash, Block-Sparse** 3패턴 자동 선택
- 1M 컨텍스트 pre-fill 10x 가속

**KASCADE 핵심**:
- Anchor layer에서 exact Top-k 계산 → intermediate layer에서 재사용
- Training-free, plug-and-play

**글도비 Lookback 현재 구조**:

```
Tier 1 (Full): EP N-1 전문 (~5K)
Tier 2 (Summary): EP N-2 ~ N-3 요약 (~2K/화)
Tier 3 (Arc-Summary): EP N-4 ~ N-10 Arc 요약 (~4K/Arc)
→ 총 lookback_total_chars: 40K
```

**적용 가능 지점 — Dynamic Lookback Depth**:

| MInference 패턴 | 글도비 대응 | 적용 |
|-----------------|-----------|------|
| A-shape (초반+최근 집중) | Tier 1 + Tier 3 (최근+Arc 요약) | **이미 유사** |
| Vertical-Slash (특정 토큰 집중) | Vector retrieval (Tier 3) | **강화 가능**: 키워드 기반 selective EP 로드 |
| Block-Sparse (블록 단위) | chain_link per-EP | **적용 가능**: 관련 EP만 block 단위 로드 |

**구체적 적용 시나리오 — Anchor-EP + Reuse 패턴 (KASCADE 영감)**:

```
현재:
  prepare_episode_context(ep=150):
    → Tier 2: EP 148, 147 요약 (고정 2화)
    → Tier 3: EP 140~146 Arc 요약 (고정 범위)

KASCADE 영감 적용:
  "Anchor EP" 선정:
    1. 현재 EP의 blueprint에서 언급된 NPC/장소/아이템 추출
    2. FactLedger에서 해당 엔티티의 established_ep, last_ep 조회
    3. 관련 EP를 "anchor"로 선정 (예: EP 23, 67, 142)

  "Reuse EP" 확장:
    4. anchor EP +/-2화를 "reuse" 범위로 확장
    5. reuse EP는 chain_link만 로드 (summary 수준)
    6. anchor EP는 full excerpt 로드 (5K/화)

  결과:
    - 고정 lookback 40K 예산 내에서 관련성 3-5x 향상
    - "150화에서 23화 NPC 재등장" 시나리오 커버
```

**ROI 판정**: **HIGH**
- 장기연재 핵심 문제: "먼 과거 사실 참조" — 고정 lookback으로는 해결 불가
- FactLedger의 EP 메타데이터와 결합하면 구현 복잡도 낮음
- 기존 Vector retrieval (hybrid search)과 상호 보완

---

### 2.4 SparseFrontier Trade-off → Advisory Chain 효율화

**SparseFrontier 핵심 발견**:
- Sparsity 0.90까지: 대부분 task에서 < 5% 성능 저하
- Sparsity 0.95: task-dependent, 일부 task에서 급격한 저하
- **"Sparse ceiling"**: 각 task마다 최적 sparsity가 다름

**글도비 Advisory Chain 현황**:

```
9개 Advisory x 60초 timeout = 최대 300초
각 Advisory: 전체 원고 + 컨텍스트 (~30-50K) 주입
→ LLM 7개 + Python 1개 + StyleSignal 1개
→ 총 LLM 호출: 7-8회 (병렬)
```

**적용 가능 지점 — Advisory Sparse Selection**:

```
현재:
  모든 Advisory가 매 라운드 실행
  → 9개 중 평균 2-3개만 유의미한 경고 생성
  → 나머지 6-7개: "no issues found" 반환 (비용만 소모)

SparseFrontier 영감 적용:
  Phase 1 — Python-only 사전 스크리닝 (< 1초):
    - NumericConsistency (이미 Python-only)
    - 추가: NPC 등장 빈도 체크 (Python)
    - 추가: 키워드 매칭으로 관련 advisory 필터링

  Phase 2 — 스크리닝 결과 기반 selective LLM 호출:
    - NPC 이름 변경 감지 → NpcDrift만 호출
    - 수치 언급 감지 → NumericDrift만 호출
    - 회상 장면 감지 → Flashback만 호출
    - 관계 변화 언급 → RelDrift만 호출

  결과:
    - 평균 LLM 호출: 7-8개 → 2-3개 (sparsity ~0.7)
    - SparseFrontier 기준: sparsity 0.7은 < 3% 성능 저하
    - 비용 60-70% 절감, 지연 시간 50% 단축
```

**ROI 판정**: **MEDIUM**
- 이미 병렬화로 지연 시간은 해결됨 (60초 wall-clock)
- 비용 절감은 유의미하나, advisory는 방어 레이어 → false negative 위험
- Python 사전 스크리닝 정확도에 의존

---

### 2.5 MSA Document-wise RoPE → TF-3 ChainLink 위치 인코딩

**MSA Document-wise RoPE 핵심**:
- 문서별 독립 위치 인코딩 → 문서 간 위치 간섭 제거
- 100M 토큰에서도 extrapolation 안정

**글도비 ChainLink 현황**:

```
chain_link_{ep} = {
  "cliffhanger": "...",
  "pending_actions": [...],
  "emotional_state": "...",
  "physical_state": "...",
  "location": "...",
  "time_marker": "..."
}
→ 에피소드별 독립 저장 (이미 document-wise 분리)
→ 단, 컨텍스트 주입 시 flat하게 연결
```

**적용 가능 지점 — ChainLink Boundary Markers**:

```
현재 주입 형태:
  "[V68] 직전 화 연결고리\n{chain_link_json}"
  → LLM은 이것이 "어느 화"의 것인지 암묵적으로만 파악

MSA 영감 적용:
  다중 ChainLink 주입 시 (lookback 확장):
    "<<EP_BOUNDARY ep=147>>\n{chain_link_147}\n<<EP_BOUNDARY_END>>"
    "<<EP_BOUNDARY ep=148>>\n{chain_link_148}\n<<EP_BOUNDARY_END>>"
    "<<EP_BOUNDARY ep=149>>\n{chain_link_149}\n<<EP_BOUNDARY_END>>"

  → LLM이 에피소드 경계를 명시적으로 인식
  → cross-EP 혼동(EP 147 사건을 EP 149에 귀속) 방지
```

**ROI 판정**: **LOW-MEDIUM**
- 현재 직전 1화만 chain_link 주입 → 다중 주입 시에만 유의미
- Lookback 확장(2.3)과 결합하면 가치 상승

---

### 2.6 MARTI (Multi-Agent RL) → Advisory Chain 학습

**MARTI 핵심**:
- Multi-Agent 시스템을 RL로 학습 — 에이전트 간 협력 최적화
- Function-calling 기반 오케스트레이션

**글도비 Advisory 현황**:
- 9개 Advisory가 독립 실행 → 결과 merge
- 에이전트 간 정보 공유 없음
- `_suppress_conflicting_advisories()`로 사후 충돌 해소

**적용 가능 지점**:

```
현재 문제:
  - TruthGate "사실 오류" + NpcDrift "NPC 변화" → 같은 문제를 다른 관점에서 보고
  - 사후 suppression으로 해결 중이나, 중복 LLM 호출은 이미 발생

MARTI 영감 적용 (장기):
  Phase 1 — 공유 컨텍스트 풀:
    - Advisory 간 "공유 관찰" 슬롯 도입
    - TruthGate가 "팩트 X 위반" 발견 → 슬롯에 기록
    - NpcDrift가 슬롯 확인 → 중복 검사 스킵

  Phase 2 — 피드백 루프 (장기):
    - Director의 최종 판정(PASS/REJECT)을 advisory별 정확도로 추적
    - false positive 빈도 높은 advisory의 호출 우선순위 하향
```

**ROI 판정**: **LOW** (장기 과제)
- 현재 suppression이 작동 중
- RL 학습은 글도비 규모에서는 과도한 엔지니어링
- Phase 1(공유 슬롯)만 단기 적용 가능

---

## 3. 우선순위 매트릭스

```
          높은 ROI ----------------------- 낮은 ROI
          |                                    |
쉬운 구현  |  [2.2] FactLedger Decay     |  [2.5] ChainLink Boundary |
          |  [2.4] Advisory Sparse       |                           |
          |                              |                           |
          |------------------------------|---------------------------|
          |                              |                           |
어려운 구현 |  [2.3] Anchor-EP Lookback   |  [2.6] MARTI RL           |
          |  [2.1] WSM Hot/Cold          |                           |
          |                              |                           |
```

### 단기 적용 후보 (T67+ 범위)

| 순위 | 시나리오 | 논문 출처 | TF 대상 | 예상 효과 |
|------|---------|----------|---------|----------|
| **1** | FactLedger Relevance Decay | LONGMEM, InfLLM | TF-2 | 같은 50K 내 최근 사실 밀도 2-3x |
| **2** | Anchor-EP Lookback | KASCADE, MInference | TF-4 | 원거리 EP 참조 정밀도 3-5x |
| **3** | Advisory Python Pre-screen | SparseFrontier | Advisory | LLM 호출 60-70% 절감 |

### 중기 적용 후보 (v1.7+ 범위)

| 순위 | 시나리오 | 논문 출처 | TF 대상 | 예상 효과 |
|------|---------|----------|---------|----------|
| **4** | WSM Hot/Cold 분리 | MSA | TF-1 | 200화+ NPC 비대화 대응 |
| **5** | ChainLink EP Boundary | MSA Doc-RoPE | TF-3 | cross-EP 혼동 방지 |
| **6** | Advisory 공유 슬롯 | MARTI | Advisory | 중복 검사 제거, 정밀도 향상 |

---

## 4. TF 구성 변경 임팩트 맵

### 4.1 FactLedger Decay 도입 시 TF 구성 변경

```
변경 대상:
  fact_ledger.py
    - to_summary() 메서드에 target_ep 파라미터 추가
    - _relevance_weight(entry_ep, target_ep) 내부 함수 추가
    - history 직렬화 시 weight 기반 예산 배분

  validation.yaml
    + fact_ledger:
    +   recency_window: 20        # weight 1.0 범위
    +   decay_window: 50          # weight 0.5 범위
    +   archive_threshold: 50     # weight 0.1 이하
    +   landmark_keywords:        # archive에서도 보존할 키워드
    +     - "사망"
    +     - "파괴"
    +     - "결혼"
    +     - "배신"

  stage4_context_builder.py
    - FactLedger.to_summary() 호출 시 target_ep=next_ep 전달

영향 범위:
  - TruthGate advisory: 더 정밀한 recent fact → 정확도 향상
  - NpcDrift advisory: 최근 NPC 상태 밀도 증가 → 감지력 향상
  - WorldState와 독립 (TF-1 무변경)
```

### 4.2 Anchor-EP Lookback 도입 시 TF 구성 변경

```
변경 대상:
  stage4_context_builder.py
    - _build_prev_manuscripts_text() 리팩터
    + _select_anchor_eps(blueprint, fact_ledger) → List[int]
    + _load_anchor_ep_excerpts(anchor_eps) → str
    - Tier 3 고정 범위 → Anchor-EP 기반 동적 범위

  fact_ledger.py
    + get_related_episodes(entity_name) → List[int]
      (history에서 ep 번호만 추출)

  validation.yaml
    + lookback:
    +   anchor_ep_max: 5           # 최대 anchor EP 수
    +   anchor_ep_chars: 5000      # anchor EP당 발췌 상한
    +   reuse_ep_range: 2          # anchor +/-N화 reuse 범위
    +   reuse_ep_chars: 1000       # reuse EP당 발췌 상한

영향 범위:
  - Tier 3 대체 (Tier 1/2 무변경)
  - lookback_total_chars 40K 예산 내 운용
  - Vector retrieval(hybrid search)과 상호 보완
    → anchor-EP는 "확실히 관련된 EP" (precision)
    → vector retrieval은 "유사한 EP" (recall)
```

### 4.3 Advisory Sparse Selection 도입 시 TF 구성 변경

```
변경 대상:
  stage4_interview_round.py
    - _run_advisory_chain() 앞에 _prescreen_advisories() 추가
    + _prescreen_advisories(manuscript, context) → Set[str]
      - 키워드/패턴 매칭으로 관련 advisory 식별
      - 항상 실행: TruthGate (안전망), NumericConsistency (Python-only)
      - 선택 실행: 나머지 7개

  validation.yaml
    + advisory:
    +   always_run:
    +     - truth_gate
    +     - numeric_consistency
    +   prescreen_rules:
    +     npc_drift: ["npc_name_pattern", "character_change_keywords"]
    +     numeric_drift: ["\\d+", "가격", "수량", "거리"]
    +     flashback: ["회상", "과거", "그때", "기억"]
    +     rel_drift: ["관계", "사이", "원수", "동맹"]
    +     info_paradox: ["알고 있", "모르", "비밀", "발각"]
    +     long_term_rep: ["또", "다시", "반복"]
    +     style_signal: []  # 항상 skip 가능 (lowest priority)

영향 범위:
  - Advisory 병렬 구조 유지 (ThreadPoolExecutor)
  - 선택된 advisory만 submit → 나머지 skip
  - false negative 위험: TruthGate 상시 실행으로 안전망 확보
```

---

## 5. 미적용 판정 (적용하지 않는 이유)

| 논문 기법 | 미적용 사유 |
|----------|-----------|
| MSA의 end-to-end 학습 | 글도비는 API 호출 기반 (Gemini) — 모델 가중치 접근 불가 |
| SpargeAttn/XAttn의 커널 최적화 | 추론 가속은 API 서버 측 관심사, 클라이언트 적용 불가 |
| SparseD의 Diffusion 특화 | 글도비는 autoregressive 생성, diffusion LM 미사용 |
| MARTI의 RL 학습 루프 | 글도비 규모에서 과도한 엔지니어링, 데이터 수집 인프라 부재 |
| MInference의 GPU 커널 | API 호출 기반 → GPU 레벨 최적화 접근 불가 |

**공통 제약**: 글도비는 Gemini API 소비자 — 모델 내부(attention 패턴, KV cache)에 직접 개입 불가.
따라서 **논문의 "개념적 패턴"**만 애플리케이션 레벨에서 차용 가능.

---

## 6. 결론

### 핵심 인사이트

Sparse Attention 논문들의 핵심 통찰은 **"모든 정보를 균등하게 처리하지 말라"**이다.
글도비 TF 시스템에 이 원칙을 적용하면:

1. **FactLedger**: 균등 truncation → **relevance decay** (LONGMEM 영감)
2. **Lookback**: 고정 범위 → **anchor-EP 동적 선택** (KASCADE 영감)
3. **Advisory**: 전수 실행 → **sparse pre-screening** (SparseFrontier 영감)
4. **WorldState**: 단일 계층 → **hot/cold 분리** (MSA 영감)

이 4가지 모두 **API 소비자 레벨에서 구현 가능**하며,
모델 내부 접근 없이도 sparse attention의 핵심 이점(효율성 + 정밀도)을 취할 수 있다.

### 다음 단계

이 문서는 적용 가능성 분석이며, 구현은 별도 execution-ssot에서 관리한다.
코드 수정 진행 시 우선순위: **2.2 → 2.3 → 2.4 → 2.1 → 2.5 → 2.6** 순서 권장.

---

# Appendix. 참고용 — 글도비 직접 적용 낮음

> 아래 섹션은 글도비가 Gemini API 소비자(모델 내부 접근 불가)이거나, 기존 시스템으로 이미 해결된 영역이라
> 직접 적용 ROI가 낮다. 배경 지식 또는 향후 환경 변경 시 참고용으로 보존한다.

## B-1. Sparse Attention / KV Cache 압축 (원 A-5)

> **미적용 사유**: 커널/GPU 레벨 최적화 — Gemini API 소비자는 모델 내부 attention 패턴/KV cache에 접근 불가.
> 단, 개념적 패턴(sparse selection, anchor-reuse)은 Part B에서 애플리케이션 레벨로 차용됨.

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **MSA**: Memory Sparse Attention (100M Tokens) | arXiv 2026.03 | [GitHub](https://github.com/EverMind-AI/MSA) | 100M 토큰 end-to-end 메모리. Doc-wise RoPE + KV 압축 |
| **SpargeAttn**: Training-free Sparse Attention | ICML 2025 | [GitHub](https://github.com/thu-ml/SpargeAttn) | 모든 모델 추론 가속. Training-free |
| **XAttention**: Block Sparse + Antidiagonal Scoring | ICML 2025 | [GitHub](https://github.com/mit-han-lab/x-attention) | Plug-and-play long-context 가속 |
| **SparseD**: Sparse Attention for Diffusion LMs | ICLR 2026 | [GitHub](https://github.com/INV-WZQ/SparseD) | Diffusion LM용 near-lossless 가속 |
| **The Sparse Frontier**: Trade-offs in Transformer LLMs | arXiv 2504.17768 (2026.01 개정) | — | 6 방법 x 128K x sparsity 0.95 체계적 분석 |
| Scaling Linear Attention with Sparse State Expansion | arXiv 2507.16577 | — | Row-sparse update + top-k hard classification |
| **MInference**: Dynamic Sparse Attention for 1M Pre-fill | NeurIPS 2024 | [arXiv](https://arxiv.org/abs/2407.02490) | A-shape/Vertical-Slash/Block-Sparse 패턴. 10x 가속 |
| **KASCADE**: Practical Sparse Attention for Long-Context Inference | arXiv 2512.16391 | — | Anchor-layer Top-k → reuse-layer 전파. Training-free |
| **KVzip**: Query-agnostic KV Cache Eviction | NeurIPS 2025 Oral | [GitHub](https://github.com/snu-mllab/KVzip) | 3-4x 메모리 감소, 2x 지연 감소 |
| **RocketKV**: Two-Stage KV Cache Compression | ICML 2025 | [GitHub](https://github.com/NVlabs/RocketKV) | Training-free 2단계 KV 압축 |
| **kvpress**: LLM KV Cache Compression Made Easy | NVIDIA | [GitHub](https://github.com/NVIDIA/kvpress) | NVIDIA 공식 KV 압축 라이브러리 |
| Efficient Attention Mechanisms for LLMs: A Survey | arXiv 2507.19595 (2026.02 개정) | — | Sparse/Linear/Memory attention 전체 조망 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-KV-Cache-Compression](https://github.com/October2001/Awesome-KV-Cache-Compression) | KV Cache 압축 논문 (상시 업데이트) |
| [Awesome-LLM-KV-Cache](https://github.com/Zefan-Cai/Awesome-LLM-KV-Cache) | KV Cache 논문 + 코드 |
| [Awesome-KV-Cache-Management](https://github.com/TreeAI-Lab/Awesome-KV-Cache-Management) | KV Cache 관리 종합 서베이 |
| [Awesome-LLM-Inference](https://github.com/xlite-dev/Awesome-LLM-Inference) | LLM 추론 최적화 전체 |
| [Awesome-LLM-Compression](https://github.com/HuangOwen/Awesome-LLM-Compression) | LLM 압축 전반 |

---

## B-2. Structured Output / JSON Extraction (원 A-22)

> **미적용 사유**: 글도비는 Gemini `response_mime_type="application/json"` + `_extract_json_robust()`로 구조화 출력 이미 해결.
> Constrained decoding은 모델 내부 접근 필요.

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **JSONSchemaBench**: Structured Outputs Benchmark | arXiv 2501.10868 | [GitHub](https://github.com/guidance-ai/jsonschemabench) | 10K 실전 JSON 스키마. 6개 constrained decoding 프레임워크 비교 |
| **Schema RL**: Learning Structured Output via RL | arXiv 2502.18878 | [arXiv](https://arxiv.org/abs/2502.18878) | RL 기반 구조화 출력 학습 |
| Draft-Conditioned Constrained Decoding | arXiv 2603.03305 (2026.03) | [arXiv](https://arxiv.org/abs/2603.03305) | Draft 기반 제약 디코딩 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [Awesome-LLM-Constrained-Decoding](https://github.com/Saibo-creator/Awesome-LLM-Constrained-Decoding) | Constrained decoding 논문/벤치마크 |

---

## B-3. RLHF / RL for Creative Writing (원 A-25)

> **미적용 사유**: 모델 fine-tuning/RL 학습 필요 — Gemini API 소비자는 적용 불가.
> Director 채점 rubric 설계 참고용으로만 가치.

| 논문 | 학회/시기 | GitHub | 핵심 |
|------|----------|--------|------|
| **RLMR**: RL with Mixed Rewards for Creative Writing | arXiv 2508.18642 | [arXiv](https://arxiv.org/abs/2508.18642) | 창작 글쓰기 전용 mixed reward. GRPO 기반 |
| **RLHF Book**: Reinforcement Learning from Human Feedback | arXiv 2504.12501 (2025) | [Book](https://rlhfbook.com/book.pdf) | RLHF 종합 교과서 |
| RLHF Survey | arXiv 2312.14925 | [arXiv](https://arxiv.org/abs/2312.14925) | RLHF 서베이 |

### Awesome Lists

| 리포 | 설명 |
|------|------|
| [awesome-RLHF](https://github.com/opendilab/awesome-RLHF) | RLHF 리소스 (상시 업데이트) |
| [learning-from-rewards-llm-papers](https://github.com/bobxwu/learning-from-rewards-llm-papers) | 보상 기반 학습 논문 (post-training + test-time) |
