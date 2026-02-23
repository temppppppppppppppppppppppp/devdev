# Opus TF-5: 전체 시스템 디버깅 감사 종합 보고서

> 감사일: 2026-02-23  
> 감사자: Claude Opus 4.6 × 12 TF (Codex 통합)  
> 대상: HEAD 기준 전체 시스템 (core + agents + validation + ops/config)

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 18 |
| MEDIUM | 14 |
| LOW | 0 |

- 총 확정 이슈: **32건**
- 성격: 크래시성 결함보다 **silent 품질 저하 / 검증 무력화 / 운영 관측 사각지대**가 중심
- 패치 원칙: 감사 단계에서는 코드 수정 없이 문서화만 수행

## Cross-TF 이슈

### [X-1] Scene 계약 드리프트가 Stage4 품질 게이트를 이중 약화
- 관련 TF: B-3, K-2
- 요약:
  - SC 컨텍스트 쪽에서 `scene_breakdown` 타입 계약 불일치(B-3)
  - Stage4 candidate 검증 컨텍스트에 `blueprint` 자체가 누락(K-2)
- 영향: Scene 반영/완성도 계열 검증이 실행되지 않거나 약화되어 잘못된 PASS 가능성이 상승.

### [X-2] 장르 가드 체계와 Validation Consistency 체계가 분리되어 장르별 검증 강도 불균형
- 관련 TF: H-계열, K-3
- 요약:
  - 플랫폼은 10개 장르 Guard를 운영하지만
  - `ConsistencyValidator` 내부 guard 로더는 3개 장르만 직접 지원
- 영향: 일부 운영 장르에서 일관성 검증이 사실상 부분 비활성화.

### [X-3] 운영 관측 레이어는 호출되지만 Stage4 실데이터 유입이 없어 경보 체인이 공회전
- 관련 TF: L-1
- 요약:
  - Stage4 후처리에서 회귀/드리프트 탐지를 호출
  - 그러나 Stage4 결과를 `QualityDashboard`에 기록하지 않음
- 영향: Stage4 품질 하락에 대한 자동 경보 신뢰도 저하.

## TF별 요약

| TF | 보고서 | CRITICAL | HIGH | MEDIUM | LOW | 핵심 요약 |
|----|--------|----------|------|--------|-----|----------|
| A | `docs/2026-02-22/opus_tf5_stage2_debug_audit.md` | 0 | 1 | 1 | 0 | Stage2 경로의 검증/분기 결함 |
| B | `docs/2026-02-22/opus_tf5_stage4_debug_audit.md` | 0 | 1 | 2 | 0 | Stage4 후처리/컨텍스트 계약 회귀 |
| C | `docs/2026-02-22/opus_tf5_npc_state_debug_audit.md` | 0 | 1 | 1 | 0 | NPC 상태 수명주기 불일치 |
| D | `docs/2026-02-22/opus_tf5_infra_debug_audit.md` | 0 | 2 | 1 | 0 | 인프라 계층 배선/복원 문제 |
| E | `docs/2026-02-22/opus_tf5_director_debug_audit.md` | 0 | 1 | 1 | 0 | Director 체인 판정 경계 결함 |
| F | `docs/2026-02-22/opus_tf5_integration_debug_audit.md` | 0 | 2 | 1 | 0 | 통합 시나리오 회귀 |
| G | `docs/2026-02-22/opus_tf5_stage0_3_debug_audit.md` | 0 | 2 | 1 | 0 | Stage0/3 DI/병렬 연속성 결함 |
| H | `docs/2026-02-22/opus_tf5_genre_guards_debug_audit.md` | 0 | 1 | 2 | 0 | Guard 구현/적용 일관성 문제 |
| I | `docs/2026-02-22/opus_tf5_continuity_debug_audit.md` | 0 | 1 | 2 | 0 | Continuity 체인 누락/과탐 경계 |
| J | `docs/2026-02-22/opus_tf5_arc_gen_debug_audit.md` | 0 | 2 | 0 | 0 | Arc 생성 중복 검증 우회 |
| K | `docs/2026-02-22/opus_tf5_validation_debug_audit.md` | 0 | 2 | 1 | 0 | Validation scene/guard 경로 무력화 |
| L | `docs/2026-02-22/opus_tf5_ops_config_debug_audit.md` | 0 | 2 | 1 | 0 | 운영 지표/설정 정합성 결함 |

## Tier 1~5 회귀 확인 결과

- `[NPC-L1]` DB bind 배선: 회귀 이슈 재발견 없음.
- `[NPC-L2]` rollback state reset: 회귀 이슈 재발견 없음.
- `[Tier4-12]` 하이브리드 컨텍스트: 계약 불일치 관련 파급(B-2/B-3, K-2) 존재.
- `[Phase A-3]` post-select 검증: 기능 동작은 유지되나 검증 입력 품질(B/K 측)에서 약화 지점 존재.
- `[SC-Skip]` Director self-consistency 임계 로깅: 회귀 없음.
- `SafeDict`/`format_map`: 치명 회귀 미발견.

## Codex 핸드오프 권장 작업

### 즉시 수정 (HIGH)
1. K-2: Stage4 `_cv_context`에 `blueprint`/`blueprint_text` 주입해 Blocking scene 계열 검사 복원.
2. K-1: `required_scenes` 최소치 계산을 `scene_count` 연동형으로 교정.
3. L-1: Stage4 PASS/REJECT 확정 지점에서 `quality_dashboard.record_validation(..., stage=4)` 배선.
4. L-2: Stage2Optimizer dict 아이템 정규화(`name/item`) 대칭화.
5. K-3: ConsistencyValidator guard 로딩을 `create_genre_guard()` 기반으로 통합.

### 중기 수정 (MEDIUM)
1. L-3: `retry.director_max_attempts`를 Stage4 루프와 연결해 설정-코드 정합성 복원.
2. Cross-TF(X-1): Scene 계약(dict/list) 단일화 및 검증 컨텍스트 표준 스키마 문서화.
3. Cross-TF(X-2): 장르 가드 주입 경로(오케스트레이터/검증기) 단일 팩토리로 통합.

### 장기/운영
1. Stage4 품질 지표(회귀/드리프트/편향) 대시보드에 알림 기준선과 샘플 수 기준을 명시.
2. TF-5 확정 이슈를 기반으로 회귀 테스트 세트(특히 scene/guard/config wiring) 추가.
