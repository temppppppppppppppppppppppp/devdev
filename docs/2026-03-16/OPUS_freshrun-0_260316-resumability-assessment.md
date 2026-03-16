# OPUS_freshrun-0_260316-resumability-assessment.md
## TF-D: 재개 가능성 평가

---

### 1. 요약

프로젝트 `0_260316` freshrun은 ep6 원고 완료(score=99) 후, ep7 생성 중 API 호출 단계에서 중단되었다.
중단 지점은 clean cut(부분 아티팩트 없음)이며, DB 무결성은 확인 완료 상태이다.

**현재 상태:**
- ep1-6 원고: 완료 (DB + drafts + artifacts 저장)
- ep7 블루프린트: 존재 (PASS, score=100, action_focused)
- ep8-11 블루프린트: 존재 (전부 PASS, score=100)
- Arc 1-3: 완료
- DB integrity_check: PASS
- ep7 부분 아티팩트: 없음 (clean cut)
- ep6: 마지막 완료 원고 (score=99)

결론: **ep7부터 재개 가능**하며, Menu 7 이어쓰기가 최적 경로이다.

---

### 2. ep7 재개에 필요한 상태 목록

| # | 필요 상태 | 현재 상태 | 비고 |
|---|----------|----------|------|
| 1 | ep1-6 원고 (DB) | PASS | 6건 모두 저장 확인 |
| 2 | ep6 최종 원고 (predecessor context) | PASS | score=99, 컨텍스트 참조용 |
| 3 | Blueprint ep7 (action_focused) | PASS | score=100 |
| 4 | Blueprint ep8-11 | PASS | 전부 score=100 |
| 5 | Arc 2 전술 문서 | PASS | ep7은 Arc 2 범위 |
| 6 | Arc 3 전술 문서 | PASS | ep8+ 대비 |
| 7 | Style Guide | PASS | DB 내 존재 |
| 8 | NPC History | PASS | ep1-6 추적 데이터 존재 |
| 9 | 벡터 검색 (sqlite-vec) | PENDING | vec0 모듈 미설치, 비차단 |

---

### 3. 재개 옵션

#### Option A: Menu 7 이어가기 (추천)

- 기존 세션에서 **"7. 이어쓰기"** 메뉴 선택
- Stage 4 frontier를 자동 감지하여 ep7부터 재개
- DB에서 ep6까지의 원고와 ep7 블루프린트를 자동 로드
- **장점:** 수동 설정 불필요, 상태 자동 복원, clean cut이므로 오염 없음
- **단점:** 없음 (모든 사전 조건 충족)

#### Option B: Menu 4 수동 지정

- Stage 4 메뉴에서 시작 회차를 ep7로 수동 지정
- Menu 7과 동일한 결과이나 수동 개입 필요
- **장점:** frontier 감지 로직에 의존하지 않음
- **단점:** 불필요한 수동 작업, 설정 오류 가능성

#### Option C: 전체 freshrun 재시도

- ep1부터 전체 재생성
- **장점:** 완전히 깨끗한 상태
- **단점:** ep1-6 재생성 비용(API 토큰 + 시간), 기존 ep1-6 품질 보장 불가, 비효율적
- **비추천:** ep1-6이 이미 고품질(score=99)로 완료되어 재생성 이유 없음

---

### 4. 사전 체크리스트

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 1 | DB integrity_check | PASS | 이미 확인 완료 |
| 2 | ep6 원고 존재 + 내용 확인 | PASS | score=99, DB + drafts 존재 |
| 3 | Blueprint ep7-11 존재 확인 | PASS | 전부 score=100 |
| 4 | Arc 2-3 존재 확인 | PASS | 전술 문서 정상 |
| 5 | vec0 모듈 (벡터 검색) | PENDING | sqlite-vec 미설치. 벡터 검색 없이도 원고 생성 가능(non-blocking)하나, 참조 품질 저하 가능 |

**총 평가:** 5개 중 4개 PASS, 1개 PENDING(non-blocking) — **재개 가능**

---

### 5. 리스크

#### 5.1 NPC Drift 잔여

- **현상:** ep5에서 박성호의 직급/소속이 혼란스러웠던 전례 존재
- **영향:** ep7 이후 NPC 속성 불일치 재발 가능
- **대응:** ep7 생성 후 NPC 추적 데이터와 원고 내 NPC 언급을 교차 검증. 필요 시 수동 보정 후 다음 회차 진행

#### 5.2 컨텍스트 토큰 증가

- **현상:** ep7 기준 mandatory_context = 10,086자. ep8 이후 점진적 증가 예상
- **영향:** API 호출 시 토큰 한도 압박, 응답 품질 저하 가능
- **대응:** 컨텍스트 윈도우 모니터링. 임계치 초과 시 요약 기반 컨텍스트 압축 적용

#### 5.3 Soft Failure 열화

- **현상:** sink_alignment projection이 계속 실패 (non-blocking)
- **영향:** 감사(audit) 품질 저하. 원고 생성 자체에는 영향 없음
- **대응:** non-blocking이므로 원고 생성은 진행. 감사 결과 해석 시 sink_alignment 미반영 감안

#### 5.4 대화 비율 경고

- **현상:** style_guide의 dialogue_ratio=0.0이 매 회차 경고 유발
- **영향:** 경고 로그 누적. 실제 원고의 대화 비율과 무관한 false alarm
- **대응:** style_guide의 dialogue_ratio 값을 실제 ep1-6 원고의 평균 대화 비율로 갱신 권장. 미갱신 시에도 원고 생성에 차단 영향 없음

---

### 6. 추천

**Option A (Menu 7 이어가기)** 를 추천한다.

**근거:**
1. DB 무결성 확인 완료
2. ep7 재개에 필요한 모든 사전 조건 충족 (4/4 PASS, 1 PENDING non-blocking)
3. ep7 블루프린트 이미 존재 (score=100, action_focused)
4. Clean cut이므로 상태 오염 없음 — 부분 아티팩트 정리 불필요

**재개 전 수행 단계:**
1. 프로젝트 `0_260316` 로드
2. ep6 원고 내용을 육안 확인 (마지막 장면이 ep7 블루프린트 시작과 연결되는지)
3. Menu 7 선택 → Stage 4 frontier ep7 자동 감지 확인
4. ep7 생성 완료 후 NPC 추적 데이터 교차 검증
5. 이상 없으면 ep8로 계속 진행

---

### 7. 예상 소요

| 항목 | 예상 시간 | 비고 |
|------|----------|------|
| 사전 확인 (ep6 육안 검토) | 5분 | 마지막 장면 + ep7 블루프린트 연결 확인 |
| ep7 원고 생성 | 3-5분 | API 호출 1회 기준 |
| ep7 검증 (NPC + 연속성) | 5분 | 자동 감사 + 육안 확인 |
| ep8-11 원고 생성 | 12-20분 | 4회차, 회당 3-5분 |
| 전체 완료 | 25-35분 | ep7-11 전부 생성 + 검증 기준 |

**참고:** API rate limit 또는 soft failure 재시도로 인해 실제 소요 시간은 증가할 수 있음.

---

*작성: Claude Opus 4.6 (TF-D)*
*일자: 2026-03-16*
