# Vertex AI 전환 필요성

**작성일**: 2026-03-03
**근거**: 실 운용 중 발생한 장애 기록 기반

---

## 현재 환경

- Google Gemini API 직접 호출 (API Key 인증)
- 에피소드당 6+ 병렬 LLM 호출 (앙상블 3후보 × 2단계)
- 4단계 모델 폴백 체인 + API Key 멀티 로테이션 + 22회 네트워크 재시도

## 문제

2026-03-03 실 생산 중 `gemini-3.1-pro-preview` 모델이 503/500 에러를 연속 반환했다. 3개 병렬 호출이 동시에 실패하며 1화 Blueprint 생성에 11분+ 소요, Stage 4 원고 생산은 시작 불가 상태가 되었다.

직접 API 테스트 결과:

| 모델 | 상태 | 응답 시간 |
|------|------|-----------|
| gemini-3.1-pro-preview | **500 Internal Server Error** | 실패 |
| gemini-3-pro-preview | 정상 | 10.5초 |
| gemini-2.5-pro | 정상 | 5.9초 |
| gemini-2.5-flash | 정상 | 1.2초 |

최신 모델(3.1-pro)만 선택적으로 죽었다. 원인은 Google 서버 측 과부하이며, 직접 API 사용자는 공용 트래픽 풀을 공유하기 때문에 수요 급증 시 먼저 밀려난다.

## 임시 대응

`gemini-3.1-pro-preview` → `gemini-3-pro-preview`로 전량 교체하여 운용 재개. 단, 모델명이 `config/models.yaml` 외에 `constants.py`, `config_manager.py`, 개별 에이전트 `.py` 파일 등 **10+ 파일에 분산 하드코딩**되어 있어 교체에 수작업이 필요했다. 이 자체가 기술 부채.

## 직접 API vs Vertex AI

| 항목 | 직접 API (현재) | Vertex AI |
|------|----------------|-----------|
| 인증 | API Key | GCP 서비스 계정 (OAuth2) |
| 트래픽 풀 | 공용 (전체 무료/개인 사용자 공유) | GCP 프로젝트 전용 할당 |
| RPM 제한 | 무료 티어 기준 (낮음) | 기업 등급 (수십~수백배) |
| 503 과부하 | 타 사용자 트래픽에 영향 받음 | 전용 할당으로 격리 |
| 모델 | 동일 Gemini | 동일 Gemini |
| 토큰 단가 | 동일 | 동일 (약정 시 할인 가능) |
| 할당량 증설 | 불가 (Google 재량) | 콘솔에서 요청 가능 |

## 전환 범위

코드 변경은 **인증 계층에 한정**된다.

1. `base_agent.py`의 `genai.configure(api_key=...)` → Vertex AI SDK 인증으로 교체
2. `google.generativeai` → `google.cloud.aiplatform` 또는 `vertexai` SDK 전환
3. 모델명 포맷 변경 (예: `gemini-3-pro-preview` → Vertex AI 모델 경로)
4. 환경 변수: `GOOGLE_API_KEY` → `GOOGLE_APPLICATION_CREDENTIALS` (서비스 계정 JSON)

파이프라인 로직, 프롬프트, 검증 체계, DB 구조는 **변경 없음**.

## 전환하지 않으면

- 최신 모델 출시 때마다 초기 수요 폭주 → 503 장애 반복
- 야간 무인 생산 중 장애 발생 시 수동 개입 필요
- 병렬 호출 수 증가(복수 작품 동시 생산) 시 RPM 상한에 더 빈번하게 충돌
- 폴백 체인이 아무리 견고해도 **1차 모델 자체가 죽으면** 폴백 모델의 품질·속도 저하를 감수해야 함

## 비용

Vertex AI 자체는 추가 비용 없음 (토큰 단가 동일). GCP 프로젝트 생성 + 결제 계정 연결만 필요. 기존 API 비용 구조와 동일하되, 안정성이 올라간다.

---

*이 문서는 2026-03-03 실제 장애 경험을 근거로 작성되었다.*
