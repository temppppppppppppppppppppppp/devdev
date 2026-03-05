# 글도비 + 블록메이커 + Vertex AI 대량 원고 학습 전략

작성일: 2026-03-05  
적용 범위:
- `C:\Users\wjjo\Desktop\블록메이커` (원고 정제/블록 추출)
- `C:\Users\wjjo\Desktop\글도비` (스토리 생성/검증 파이프라인)

## 1) 결론 먼저: 대량 원고는 `RAG 우선`, 튜닝은 `선별 적용`

원고가 매우 많을 때는 처음부터 전량 파인튜닝보다, 아래 순서가 비용/품질/속도에서 유리하다.

1. 블록메이커로 원고를 구조화(JSON)한다.
2. Vertex AI RAG(또는 Grounding with Vertex AI Search)로 지식 접근을 먼저 붙인다.
3. 실제 실패 케이스 기반으로 소량 고품질 학습셋을 만들고 Gemini SFT를 수행한다.
4. 운영 로그가 쌓이면 continuous tuning으로 주기 업데이트한다.

## 2) 왜 이 순서가 맞는가 (Vertex AI 현재 기능 기준)

- Gemini supervised fine-tuning은 현재 공식 지원이며, 지원 모델은 `Gemini 2.5 Pro/Flash/Flash-Lite`, `Gemini 2.0 Flash/Flash-Lite`다.
- 튜닝 데이터는 JSONL 기반이며 Cloud Storage에 올려서 작업한다.
- Grounding with Vertex AI Search는 문서 기반 RAG에 적합하고, 최대 10개 데이터 소스를 결합할 수 있다.
- RAG Engine + Vector Search 구성 시 인덱스는 `STREAM_UPDATE` 등 호환 조건을 맞춰야 한다.
- continuous tuning은 Google Gen AI SDK에서 지원되고(문서 기준), Vertex AI SDK for Python은 미지원 항목이 있다.

즉, "지식 주입"은 RAG가 즉시성/유지보수성이 좋고, "응답 스타일/판단 습관 교정"은 튜닝이 효과적이다.

## 3) 두 프로젝트를 하나의 학습 파이프라인으로 묶는 방법

### A. 블록메이커 역할 (`C:\Users\wjjo\Desktop\블록메이커`)

- 입력: 대량 txt 원고
- 출력: 장르별 블록 JSON (`output/*.json`)
- 목적: 비정형 원고를 학습 가능한 단위(블록/메타데이터)로 표준화

권장 출력 스키마(핵심):
- `block_id`
- `title`
- `summary`
- `entities` (인물/조직/장소)
- `timeline` (시점/순서)
- `genre_ext_fields` (장르 특화 필드)

### B. 글도비 역할 (`C:\Users\wjjo\Desktop\글도비`)

- 블록 JSON을 Arc/Blueprint/집필 단계의 컨텍스트로 공급
- 검증 파이프라인에서 실패 유형(모순/관계오류/반복/톤붕괴)을 로그화
- 이 실패 로그를 다시 SFT 데이터셋 후보로 수집

핵심 연결점:
- 블록메이커 산출물은 "지식 저장소 입력"으로
- 글도비 검증 로그는 "튜닝 데이터 입력"으로

## 4) 실행 로드맵 (현실적인 4단계)

### 단계 1. 데이터 표준화

1. 블록메이커로 전 원고를 JSON 블록화
2. 품질 게이트 적용
   - UTF-8/문장 길이/중복/비어있는 필드 검증
3. 데이터셋 버전 부여
   - 예: `manuscript_blocks_v2026_03_05`

### 단계 2. RAG 먼저 구축

선택지:
- 빠른 시작: Grounding with Vertex AI Search
- 고급 제어: Vertex AI RAG Engine + Vector Search

권장:
- 한국어 중심이면 다국어 임베딩(`text-multilingual-embedding-002`) 우선 검토
- 문서 chunk는 "장면/블록 단위"로 유지 (너무 길면 검색 정밀도 저하)

### 단계 3. SFT는 선별해서

튜닝 데이터 원칙:
- 좋은 정답/나쁜 정답/수정 정답(최종본)을 페어로 저장
- 장르/문체/시점 분포를 균형화
- 운영에서 자주 틀리는 패턴(예: 관계 역전, 시간축 붕괴) 우선 학습

최초 SFT 운영 팁:
- 기본 하이퍼파라미터로 1회 수행 후 비교
- SFT 전후 동일 평가셋으로 자동 평가
- 통과 기준 미달 시 데이터셋 품질부터 재점검

### 단계 4. 지속 튜닝(선택)

- 월/격주 단위로 검증 실패 로그를 재라벨링
- checkpoint 기반 continuous tuning 적용
- 모델/데이터/평가 리포트를 함께 버전 관리

## 5) 운영 구조 제안 (최소 구성)

### 저장소 분리

- 원본 원고 저장소(원문)
- 블록 저장소(정제 JSON)
- 튜닝 저장소(JSONL 학습셋/검증셋)
- 평가 저장소(벤치마크 프롬프트/정답/스코어)

### 메타데이터 필수 항목

- `source_project`: `blockmaker` | `geuldobi`
- `source_file`
- `genre`
- `episode`
- `revision`
- `qa_status`
- `labeler`
- `created_at`

## 6) 실패를 줄이는 가드레일

- 전량 튜닝 금지: 먼저 샘플 3~5%로 효과 검증
- 데이터 누수 방지: 학습셋/평가셋 에피소드 분리
- 비용 통제: RAG 히트율, 재생성률, 검증 실패율을 KPI로 둔다
- 보안: API 키/원문 민감정보를 저장소에 평문으로 두지 않는다

## 7) 이번 주 바로 할 일 (실행 체크리스트)

1. 블록메이커 출력 스키마를 고정하고 버전 태깅한다.
2. 글도비 검증 로그에서 상위 실패 유형 Top 5를 뽑는다.
3. Vertex AI에서 RAG PoC를 먼저 붙여 품질/비용 베이스라인을 만든다.
4. 실패 유형 중심으로 SFT 학습셋 1차(소규모) 생성 후 A/B 평가한다.
5. 기준 통과 시에만 본격 튜닝/지속 튜닝으로 확장한다.

## 참고 문서 (공식)

- Gemini SFT 개요: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning
- Gemini SFT 실행: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning
- SFT 데이터 준비(JSONL/Cloud Storage): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare
- RAG 임베딩 모델: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-embedding-models
- RAG Engine + Vector Search: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-vertexai-vector-search
- Grounding with Vertex AI Search: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/grounding/grounding-with-vertex-ai-search
- Continuous tuning: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-continuous-tuning
