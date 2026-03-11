# 글도비 프로덕션 준비도 평가

> 일자: 2026-03-10
> 방법: 6영역 에이전트 스캔 + 3-pass 감리 (오탐 제거 + 팩트 체크 + UI 실물 확인)
> 확신도: 95%

---

## 총평: **백엔드 Pre-production, 시스템 전체 Late MVP**

| 구분 | 수준 | 준비도 | 근거 |
|------|------|--------|------|
| **백엔드** | **Pre-production** | 99% | P0/P1 0건, 3,847 테스트, 10+ 감사 라운드, advisory 8개 병렬, DB SSOT, DI 완비 |
| **Desktop UI** | **MVP+** | 85% | 전체 파이프라인 구동 가능(One-Stop), 실시간 WebSocket 로그, Rollback/Wipe/Reset. Treatment/Bible 편집기 미구현 |
| **멀티장르 검증** | **MVP** | 80% | 투자물 1개만 실파이프라인 통과. 나머지 9개 장르는 GenreGuard config + unit test 수준 |
| **Ops** | **POC+** | 60% | 비용 추적(metrics_collector) + 로깅(DB) 존재. 알림·배포 자동화·SLA 미구비 |

---

## 1. 백엔드 (99%)

### 코드 품질
- **TF-BE 전수조사**: 120+ 파일 3-pass 감리 → P0 0건, P1 0건, P2 12건 (코드 위생/로깅/문서)
- **TF-FINAL 건강 감사**: 4 병렬 에이전트 × 120+ 파일 스캔, HIGH 전량 오탐, P0/P1 0건
- **테스트**: 3,847 수집, 3,831 통과, 16 스킵 (99.6% 통과율)
- **Ruff**: 0 violations
- **Protocol 준수**: db_repository.py 55+ 메서드 전량 db_manager.py 구현 일치
- **Import 건강도**: 순환 의존성 0건

### 파이프라인 완성도
- Stage 0→2→3→4 전체 체인 정상 동작
- PASS_WITH_FIX 3-tier 수정 라우팅 (inplace/partial/full)
- Director SC 자기일관성 투표 + Ensemble 3후보 경쟁
- Advisory 체인 8개 병렬 (ThreadPoolExecutor, 60s timeout)
- FactLedger + WorldState + NPC History append-only 이력
- Context Caching 5개 에이전트

### 안전장치
- TruthGate 7검사 (사망NPC/아이템/장소/스킬/카르마/NPC역할/세계법칙)
- NC-1 Python-only 수치 정합성 9개 검사
- NC-3 Director 일관성 체크리스트 20개 카테고리
- NumericConsistencyChecker + SceneSimilarity + Timeline 교차검증
- GenreGuard 10종 + WorkGuard + StyleGuard 체인
- 4th wall 메타용어 3단계 방어

---

## 2. Desktop UI (85%)

### 구현 완료
- **프레임워크**: Electron + FastAPI + PyInstaller (standalone .exe ~300MB)
- **메인 화면**: 좌측 패널(메뉴) + 우측(오피스 씬 캔버스 + 로그)
- **파이프라인 실행 버튼**:
  - 장르 설정
  - Stage 0 (6개 서브메뉴: 바이블/NPC/문체 등)
  - Stage 2 (Arc 생성)
  - Stage 3 (Blueprint)
  - Stage 4 (원고)
  - **One-Stop** (전체 일괄 실행)
- **운영 기능**: Rollback / Wipe / Reset / Rewind / Stop
- **실시간 피드백**: WebSocket 스트리밍 로그 + PASS/REJECT/PWF 배너 이펙트
- **스프라이트 애니메이션**: 오피스 씬 캔버스 (도트 캐릭터 작업 연출)
- **설정**: API 키, 프로젝트 경로, 출력 디렉토리

### 미구현
- Treatment 편집기 (현재: YAML 파일 수동 편집)
- Bible 편집기 (현재: Stage 0에서 자동 생성, 수동 수정 시 파일 직접 편집)
- 원고 리뷰/비교 뷰어 (현재: 출력 폴더의 .txt/.md 직접 열기)
- Kakao/Naver 포맷 내보내기 (코드 존재, Desktop 연동 미완)

---

## 3. 멀티장르 검증 (80%)

### 구현된 장르 (10종)

| 장르 | Guard | Config YAML | 실파이프라인 검증 |
|------|-------|-------------|----------------|
| 무협 (wuxia) | ✅ | ✅ | ❌ |
| 헌터 (hunter) | ✅ | ✅ | ❌ |
| **투자물 (investment)** | ✅ | ✅ | **✅ 유일하게 실검증 완료** |
| 판타지 (fantasy) | ✅ | ✅ | ❌ |
| 의료 (medical) | ✅ | ✅ | ❌ |
| 스포츠 (sports) | ✅ | ✅ | ❌ |
| 요리 (cooking) | ✅ | ✅ | ❌ |
| 배우/연예 (actor) | ✅ | ✅ | ❌ |
| 음악/작곡 (composer) | ✅ | ✅ | ❌ |
| 대체역사 (alt_history) | ✅ | ✅ | ❌ |

### 검증 수준
- **투자물**: TF-A~E 효과 검증 100% 합격률, 블록 침범 0건, 수치 날조 0건 (감사 06)
- **나머지 9개**: GenreGuard 단위 테스트 통과, 비무협 오염 근절 (TF-45) 확인, 실파이프라인 미실행

### Pre-production 진입 조건
- 나머지 9개 장르 × 최소 3화 실파이프라인 실행 + 합격률/모순/블록 침범 검증

---

## 4. Ops 인프라 (60%)

### 있는 것
| 기능 | 구현체 | 상태 |
|------|--------|------|
| 비용 추적 | `metrics_collector.py` (모델별 토큰 비용, 세션 합산) | ✅ |
| Rate Limit | `adaptive_retry.py` (quota_exceeded 감지 + 백오프) | ✅ |
| DB 로깅 | `llm_calls` + `stage_attempts` 테이블 | ✅ |
| Graceful Degradation | VecMemory miss → STATIC/DB 폴백 | ✅ |
| 에피소드 롤백 | DB + NPC History + WorldState + FactLedger | ✅ |
| 실패 분석 | `FailureAnalyzer` (실패 패턴 사후 분석 11개 메서드) | ✅ |

### 없는 것
| 기능 | 필요 이유 | 우선순위 |
|------|----------|---------|
| 외부 알림 (Slack/Email/Dashboard) | P0 장애 즉시 인지 | 높음 |
| 비용 한도 차단 | API 과금 폭주 방지 | 높음 |
| 배포 자동화 | .exe 수동 배포 → 자동 업데이트 | 중간 |
| 중앙 로그 수집 | 다중 세션 추적 | 낮음 (단일 사용자 시) |
| SLA 정의 | 업타임/지연/에러 예산 | 낮음 (단일 사용자 시) |

---

## 5. 사용자 시나리오별 준비도

| 시나리오 | 준비 상태 | 남은 작업 |
|----------|----------|----------|
| **1인 기술 사용자 테스트** | ✅ **지금 가능** | 없음 |
| **소규모(2~3인) 기술 프리뷰** | ✅ **Ops 런북만 추가** | 에러 대응 가이드 문서화 |
| **단일 장르(투자물) 프로덕션** | ⚠️ **거의 가능** | Treatment 편집 UX + 비용 한도 |
| **멀티장르 프로덕션** | ⚠️ **장르 검증 필요** | 9개 장르 실파이프라인 검증 |
| **베타 릴리스 (100+ 사용자)** | ❌ | UI 편집 도구 + 모니터링 + 에러 알림 |
| **SaaS (1000+ 사용자)** | ❌ | 멀티테넌시 + 인증 + 과금 |

---

## 6. Pre-production 진입 체크리스트

### 필수 (Blocker)

- [ ] **멀티장르 실파이프라인 검증** — 9개 장르 × 3화+ 실행, 합격률/모순/블록 침범 확인
- [ ] **비용 한도 차단** — 세션당 API 비용 상한 설정, 초과 시 자동 중단

### 권장 (Pre-production 품질)

- [ ] **Treatment 인앱 편집기** — YAML 수동 편집 탈피
- [ ] **에러 알림** — P0 장애 시 Slack/Email 통지
- [ ] **Ops 런북** — 장애 대응 절차 문서

### 후순위 (Production 시)

- [ ] 원고 리뷰/비교 뷰어
- [ ] Kakao/Naver 포맷 내보내기 Desktop 연동
- [ ] 배포 자동화 (electron-updater 활성화)
- [ ] 중앙 로그 수집

---

## 7. 기존 NO-GO/폐기 항목 (Pre-production에 영향 없음)

| 항목 | 상태 | 영향 |
|------|------|------|
| FTS5 한국어 형태소 분리 | 후순위 유지 | Python re.split 97% 처리. 검색 recall ~95% |
| 동적 장르 확장 | 폐기 | 장르 추가 시 코드 변경 필요. 10개로 충분 |
| 캐시 최적화 | NO-GO | Context Caching 5개 에이전트 활성. 추가 불필요 |
| R4 async 통일 | NO-GO | 현 동기+asyncio 혼합 안정적 |

---

## 8. 한 줄 요약

**백엔드는 Pre-production. 시스템 전체는 Late MVP. 9개 장르 실파이프라인 검증 + Treatment 편집 UX가 채워지면 Pre-production 진입.**
