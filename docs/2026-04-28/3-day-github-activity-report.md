# 근 3일 GitHub 작업 보고서 (2026-04-25 ~ 2026-04-28)

> **집계 범위**: 2026-04-25 00:00 KST ~ 2026-04-28 16:01 KST
> **규모**: PR 머지 87건(#12~#112), 커밋 156건(머지 제외 88건), 신규 도큐먼트 60+건
> **핵심 작성자**: macximin(원격 codex 자동화), wjjo(로컬 보정/문서)
> **브랜치**: `codex/stage4-initial-draft-quality-hardening` (현재 HEAD `fc5bd933`)

---

## 1. 한 줄 요약

3일 동안 **Stage3/Stage4 파이프라인의 안정화·증거화·정합성 강화**에 집중했고, 그 토대 위에서 **frontier watchdog**과 **replay/캐시 lineage** 결함을 모두 수술했다. 동시에 **레포·런타임 위생(루트 정리, 세션 메모리, GCP cleanrun)**을 끝내 5-arc proof 게이트를 직전 단계까지 끌어올렸다.

---

## 2. 작업 흐름 — 시간축

| 일자 | 큰 흐름 | 대표 산출 |
|---|---|---|
| **04-25** | 레포·런타임 정리 + 세션 메모리 하드닝 | PR #12~#31, P0 라이브런 안전락, 데스크톱 계약 CI 게이트 |
| **04-26** | 권한·진실성 게이트 lock 작업, 루트 위생 청소 | PR #47~#53, authority alignment, GCP IAM cleanrun 준비 |
| **04-27** | Stage3/Stage4 결함 대수술의 도입부 | PR #54~#90, frontier lag clean run, issue 56/59 처리 |
| **04-28** | 결함 잔여 박멸 + frontier proof 직전 단계 | PR #91~#112, opening lock 정상화 시리즈, 벤치마크 증거 아카이브 |

---

## 3. 주제별 개선 작업 — 무엇이 어떻게 되었는가

### 3.1. Stage4 초안 품질 하드닝 (현 브랜치의 본 주제)
**문제 인식**: Stage4 초안에서 빈 패치 반복, scene header 누락, post-select conflict 잔존, rejected artifact 재사용 등 안정성 균열이 다발.

| PR | 결함 | 조치 |
|---|---|---|
| #74 | post-select retry scope shadow 변수 | retry scope 격리 픽스 |
| #75 | sessionless 상태에서 hydration guard 통과 | guard 정상화 |
| #76 | rejected artifact 재수화(rehydration) | guard 추가 |
| #92 | 빈 Stage4 패치 반복 | 반복 시 escalation 로직 추가 |
| #99 | scene header 누락 시 전체 실패 | 로컬 처리로 전환 |
| #106 | Stage4 게이트 이슈 디테일 손실 | 디테일 보존 |
| #80 | 대시보드의 stale Stage4 runtime summary | stale 표시 추가 |
| #113 (이슈 신규) | 전환부/헤더/씬 구조 추가 하드닝 필요 | 차주 작업 큐 등록 |

### 3.2. Stage3 opening lock 정상화 시리즈
**문제 인식**: opening 위치·인물 역할 잠금이 false positive로 정상 흐름을 차단. 4월 28일 하루에만 7건 패치.

| PR | 픽스 포인트 |
|---|---|
| #94 | opening binding lock 자체 결함 복구 |
| #95 | placeholder opening location은 락 무시 |
| #96 | progressive opening bridge 허용 |
| #97 | hard lock을 carryover 소스로만 한정 |
| #98 | progressive opening shift 명시 허용 |
| #103 | hard-bound opening location 정규화 |
| #109 | person role lock에서 prose fragment 필터링 |
| #107 | arc timeline 설명 정규화 |

### 3.3. Replay/캐시 lineage 가드 강화
**문제 인식**: 완료 이벤트 토큰이 약한 매칭으로 false replay 통과, Director/Stage4 캐시가 lineage 검증 없이 통과.

| PR | 조치 |
|---|---|
| #77 | Director manuscript 캐시 lineage 가드 추가 |
| #78 | Director 캐시 체크를 lineage guard 경유로 라우팅 |
| #90 | Stage3/Stage4 통합 완료 이벤트 replay 차단 |
| #101 | parent-location 기반 false replay 거부 회피 |
| #102 | 완료 이벤트 replay 토큰 매칭 강화 |
| #104 | parent-only 가구 단위 replay 매칭 회피 |
| #105 | 약한 완료 이벤트 replay 토큰 무시 |

### 3.4. Frontier watchdog 안정화
**문제 인식**: provider 대기 동안 watchdog이 false stall 판정, 동시 provider 대기 미추적.

| PR | 조치 |
|---|---|
| #87 | provider wait 하드닝 |
| #91 | active wait 하드닝 |
| #108 | false stall 회피 |
| #110 | concurrent provider wait 추적 |
| #111/#112 | post-110 핸드오프·벤치마크 증거 아카이브 (현 브랜치 마무리) |

### 3.5. 5-Arc Frontier Lag Clean Run (GCP/Vertex)
- PR #51 — 5-arc 사후 감사 추가
- PR #52 — frontier lag 메모리 캐시 파이프라인 안정화 (8,154 추가)
- PR #53 — GCP IAM cleanrun proof 준비
- PR #54 — clean run 최종 안정화 (2,278 추가)
- PR #55 — 프로젝트 런 아티팩트 추가 (51,255 추가; 증거 아카이브)
- PR #86 — frontier lag proof 게이트 재감사

→ 이슈 #57(5-arc 종결 strict proof)는 여전히 OPEN — 현재 브랜치의 frontier proof 작업이 직접 닿아 있음.

### 3.6. 이슈 56·58·59 클로즈
- **#56** (장르 정렬 — 액션/긴장 전략): PR #79, #84로 Stage3/Stage4 장르 계약 정렬, 프루프 워닝 패리티 도달 → 04-27 14:19 클로즈.
- **#58** (POST_SELECT_CONFLICT 표류): PR #74로 retry scope shadow 픽스 → 04-27 09:24 클로즈.
- **#59** (proof-digest warn 잔여, CoVe 자문): PR #79, #83으로 프루프 워닝 surface 닫음 → 04-27 14:19 클로즈.

### 3.7. 레포 위생·세션 메모리·CI 게이트 (04-25 토대 작업)
- **레포 정리**: PR #13~#23 — Stage0 핸드오프 매니페스트 정규화, canary 런타임 루트 격리, repo trashbox 격리·정리·제거(저위험 4단계), 생성 프로젝트 잔여물 정리. → 이슈 #8/#9/#10 모두 클로즈.
- **세션 메모리**: 8030b5f5(Stage3-4 흐름 강화), 7befed04(resume context), 5152f3fb/046c4128(persistence telemetry hardening).
- **CI 게이트 신설**: PR #30(memory persistence reliability shard), PR #31(desktop contract).
- **루트 위생** (04-26): PR #47~#50 — rerun 입력/cost fix 스크립트/저위험 잔여물/메모 노트 모두 아카이브. 이슈 #45는 후속 작업으로 OPEN 유지.
- **권한·진실성 lock**: 6f930a28(run-control authority), 3b67e894(pipeline truth gates), 8d4b8d5d(authority alignment), 21196cb1(authority evidence + run result truth).

### 3.8. 보안 이슈 6건 신규 등록 (04-27)
PR이 아니라 이슈로 백로그 적재됨. 모두 OPEN:
- #66 시크릿/구성 표준화
- #67 Vertex AI 인증의 공유 Barobook 계정 분리
- #68 로컬 앱 설정 → 승인 사용자 구성 디렉토리 이전
- #69 테스트/개발 스크립트의 프로덕션 트리 분리
- #70 내부 배포용 실행파일 접근 제어
- #71 보안 대응·완화 현황 문서화

---

## 4. 정량 지표

```
머지 PR             87건  (#12 → #112 연속)
머지된 코드 변화량   +93,455 / -1,615,581 (대규모는 잔여물 정리·아카이브)
신규 도큐먼트       60+건 (docs/2026-04-25 ~ 04-28)
신규 OPEN 이슈      8건 (#57, #60-#71, #113)
클로즈된 이슈       8건 (#3, #4, #6, #7, #8, #9, #10, #41, #56, #58, #59)
```

> 대규모 deletions는 04-25~04-26 레포 위생 청소(생성 프로젝트 잔여, repo trashbox, 루트 cost fix 스크립트, tmp DB 등)에서 발생. 코드 로직 변화량 자체는 PR당 100~700 라인 수준의 정밀 픽스가 주류.

---

## 5. 현재 브랜치 (codex/stage4-initial-draft-quality-hardening) 미커밋 상태

- **수정**: `modules/core/writer_template.py`, `modules/domain/agents/chief_writer.py`, `modules/domain/agents/manuscript_validator.py`, 그리고 대응 테스트 3종.
- **신규 도큐먼트**: `docs/2026-04-28/`에 4월 파일럿 성과 보고서, 예산 결재 메일 초안, 스케일 컨텍스트 메모, 그리고 본 보고서.
- **다음 단계 신호**: 이슈 #113(Stage4 전환부/헤더/씬 구조 하드닝)이 04-28 07:14에 생성됨 → 현재 브랜치가 그 작업의 출발점.

---

## 6. 남은 위험·다음 작업

| 항목 | 상태 | 우선순위 |
|---|---|---|
| 이슈 #57 — 종결 GCP/Vertex strict 5-arc proof | OPEN, 직전 단계 | P0 |
| 이슈 #113 — Stage4 초안 전환부/헤더/씬 구조 추가 하드닝 | OPEN, 신규 | P0 (현 브랜치) |
| 이슈 #60 — main에 추적 중인 5-arc 잠정 런 아티팩트 격리 | OPEN | P1 |
| 보안 이슈 #66~#71 (6건) | 모두 OPEN | P1 (외부 배포 전 필수) |
| 이슈 #45 — 루트 위생/Git 정리 후속 | OPEN | P2 |
| 이슈 #61~#65 — 운영자 위험 승인, 벤치마크 비교/캐시 측정 | OPEN | P2 |

---

## 7. 결론

3일치 작업의 핵심 메시지는 두 가지다:

1. **수술 완료**: 4월 중순부터 누적된 Stage3/Stage4 결함(replay false positive, opening lock 과민 반응, 빈 패치 반복, watchdog false stall, 캐시 lineage 누락)을 PR 단위로 모두 정밀 봉합했다.
2. **증거화 진입**: frontier proof 게이트(이슈 #57)와 데스크톱 계약·메모리 영속성 CI 게이트가 상시 가동되기 시작했다. 다음은 strict 5-arc proof의 종결과 보안 이슈 6건의 가시화다.
