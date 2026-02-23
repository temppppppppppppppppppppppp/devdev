# TF-6 종합 감사 보고서

- 대상 문서: `docs/2026-02-23/opus_tf6_system_audit_order.md`
- 감사 범위: TF-A ~ TF-H 전 구간 수동 점검
- 기준선: 테스트/린트는 본 보고서 말미 검증 섹션 참조

## 1) 전체 발견 건수

| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 16 |
| 합계 | 18 |

## 2) TF별 분포

| TF | 파일 | HIGH | MEDIUM | 핵심 이슈 |
|----|------|------|--------|-----------|
| TF-A | 롤백 원자성 | 1 | 2 | HUD 선반영, VecMemory rollback 누락 |
| TF-B | 상태 누적 | 0 | 3 | resolved_plots/all_reveals/feedback_log 무한 누적 |
| TF-C | 트랜잭션 | 0 | 2 | nested 상태 샘플링 1회, transaction 락 스코프 |
| TF-D | LLM 견고성 | 0 | 1 | 백업 응답 검증 키셋 과제약 |
| TF-E | 엣지 경계값 | 1 | 0 | ep_count=1 아크 구조적 REJECT |
| TF-F | 모듈 계약 | 0 | 1 | validator str 계약 위반 시 예외 전파 |
| TF-G | 임계값 외부화 | 0 | 4 | Stage2/4/Scoring/BaseAgent 매직넘버 잔존 |
| TF-H | 데드코드/위생 | 0 | 3 | 루트 임시 스크립트/도구 절대경로·덮어쓰기 |

## 3) 우선순위 제안 (P0/P1/P2)

### P0 (즉시)
1. `TF-A-1` 커밋 실패 시 HUD 인메모리 선반영 제거
2. `TF-E-1` 단일 에피소드 아크(`ep_count=1`) 허용 로직 정정

### P1 (단기)
1. `TF-A-2` VecMemory 삭제 예외 rollback 명시
2. `TF-A-3` rollback API에서 state_tracker 무효화 책임 일원화
3. `TF-C-1` commit_episode_factory 트랜잭션 상태 재평가
4. `TF-C-2` transaction 컨텍스트 락 일원화
5. `TF-F-1` BlockingValidator 입력 타입 정규화
6. `TF-D-1` BaseAgent 백업 응답 검증 키셋 분리

### P2 (중기)
1. `TF-B-*` 누적 저장소 상한/eviction 정책 정리
2. `TF-G-*` threshold 외부화 마무리
3. `TF-H-*` 임시 스크립트/아티팩트 격리 및 정리 정책 적용

## 4) 예상 패치 작업량

| 우선순위 | 예상 작업량 | 비고 |
|----------|-------------|------|
| P0 | 0.5~1일 | 코드 2~4곳 + 단위테스트 |
| P1 | 1.5~2.5일 | 트랜잭션/검증기 회귀 테스트 포함 |
| P2 | 2~4일 | 설정 외부화 + 운영 위생 정리 |

## 5) 생성된 TF별 보고서

- `docs/2026-02-23/opus_tf6_a_audit.md`
- `docs/2026-02-23/opus_tf6_b_audit.md`
- `docs/2026-02-23/opus_tf6_c_audit.md`
- `docs/2026-02-23/opus_tf6_d_audit.md`
- `docs/2026-02-23/opus_tf6_e_audit.md`
- `docs/2026-02-23/opus_tf6_f_audit.md`
- `docs/2026-02-23/opus_tf6_g_audit.md`
- `docs/2026-02-23/opus_tf6_h_audit.md`

## 6) 검증

다음 명령 실행 결과를 기준선으로 기록:
- `pytest tests/ -q`
- `python -m ruff check modules/ tests/ main_a.py`
- `python -m ruff format --check modules/ tests/ main_a.py`
