# TF-BATCH: Vertex Batch API 일괄 생산 가능성 메모

> 상태: **PARKED** (가능성 검토 완료, 구현 보류)
> 작성일: 2026-03-12

---

## 요약

TR 70블록을 Batch API 1회 제출로 24시간 내 일괄 생산하는 방안.
Phase 0 설계에 블록별 타겟이 전부 있으므로 각 블록을 독립 요청으로 생산 가능.

## 구조

```
1개 Batch Job = 70개 독립 요청
각 요청 = SSOT 규칙 + Phase 0 설계 + "Block N 생산하라"
공통 prefix (SSOT + Phase 0) → implicit caching 90% 할인
Batch 할인 50% 중첩
```

## 되는 이유

- Phase 0에 블록별 tension_level, deal_type, opponent, capital, foreshadow/callback, relationship_delta 전부 정의됨
- TR은 시놉시스(구조 설계)지 산문이 아님 → 직전 블록 실제 문체 참조 불필요
- 컨텍스트 윈도우 문제 원천 제거 (매 요청 fresh context)

## 트레이드오프

- 얻는 것: 컨텍스트 문제 제거, 70블록 24h 완성, 비용 ~$1-2
- 잃는 것: 블록 간 톤 연속성, 직전 블록 구체 표현 참조, 후처리 검수 필요
- 필요한 것: JSONL 빌더 + 결과 파서 스크립트 개발 (3-4시간)

## 비용 추정 (2.5 Pro)

- 공통 prefix ~50K 토큰 × 70 → implicit cache 90% 할인
- 블록별 고유 ~2K × 70 = 140K
- 출력 ~3K × 70 = 210K
- 총 ~$1-2

## Batch API 제약

- 요청 간 의존성 없음 (전부 병렬 독립 처리)
- explicit context caching 미지원 (implicit만)
- 24h 타겟, 큐 최대 72h
- 출력 상한: 모델과 동일 (2.5 Pro 65,536 토큰)

## 구현 시 필요 작업

1. JSONL 프롬프트 빌더 (Phase 0 파싱 → 70개 요청 생성)
2. Batch 제출 + 폴링 스크립트
3. 결과 파서 (응답 → block candidate JSON 70개)
4. 후처리 검수 (capital 연속성, NPC 교차참조, 부적합 블록 재생산)

## 판정

ROI 있음. 단, 현재는 수동 대화 방식이 충분히 동작하므로 보류.
작품 수가 늘어나거나 반복 생산이 필요해지면 재검토.

## 참고

- [Gemini Batch API](https://ai.google.dev/gemini-api/docs/batch-api)
- [Vertex AI Batch Prediction](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/batch-prediction-gemini)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
