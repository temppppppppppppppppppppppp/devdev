# Codex Canon OS v2 Plan (18-Domain Upgrade)

## 0. 목적
- 직함 롤백, 직업/클래스 뒤집힘, 능력 증발, 자산 급변, 아이템 별칭 불일치 같은 장기 연속성 사고를 구조적으로 줄인다.
- 필드를 무한정 고정 컬럼으로 늘리지 않고, 다필드/다차원 대응 체계를 만든다.
- 컨텍스트 컴팩트가 발생해도 무중단 복구가 가능해야 한다.

## 1. 운영 원칙
- Canon 시스템은 기본적으로 `수집/추적/경고`를 수행한다.
- Python은 `검증/정규화/경고`만 수행한다.
- 자동 강제 생성/자동 reject는 금지한다.
- `strict`는 "자동 차단"이 아니라 `high_warning` 승격 정책을 의미한다.
- 최종 승인/기각은 Director LLM이 수행한다.
- Canon write 권한은 Stage4만 가진다.
- 필드 확장은 컬럼 추가가 아니라 `Field Registry`로 처리한다.

## 2. Canon 18-Domain 모델

### 2.1 Core 12 (우선 적용, strict 가능)

| ID | Domain | 대표 필드 예시 |
|---|---|---|
| D01 | Character | `character.alive`, `character.title`, `character.class` |
| D02 | Relationship | `relationship.{a}.{b}.state`, `relationship.{a}.{b}.strength` |
| D03 | Affiliation | `character.affiliation.org`, `character.affiliation.rank` |
| D04 | Item/Asset | `item.owner`, `item.status`, `item.location` |
| D05 | Skill/Power | `skill.level`, `skill.usable`, `skill.locked_reason` |
| D06 | Location | `character.location`, `location.access_state` |
| D07 | Economy | `economy.wealth`, `economy.debt`, `economy.equity` |
| D08 | Quest/Conflict | `quest.state`, `conflict.state`, `resolution_ep` |
| D09 | Event Ledger | `event.type`, `event.from`, `event.to`, `event.evidence` |
| D10 | World Rules | `rule.magic_system`, `rule.rank_system`, `rule.taboo` |
| D11 | Foreshadow/Promise | `foreshadow.state`, `payoff_due_window` |
| D12 | Theme/Tone Vector | `theme.primary`, `theme.secondary[]`, `tone.guardrail` |

### 2.2 Extended 6 (2차 적용, soft/warn 중심)

| ID | Domain | 대표 필드 예시 |
|---|---|---|
| D13 | Time/StateMachine | `timeline.day`, `state.transition` |
| D14 | POV/화자 | `narrative.pov`, `narrative.voice_mode` |
| D15 | Knowledge/Causality | `knowledge.{actor}`, `causality.chain_id` |
| D16 | Dialogue Voice | `voice.lexicon`, `voice.politeness`, `voice.catchphrase` |
| D17 | Law/Economy Rules | `law.constraint`, `economy.rule_violation` |
| D18 | Scene Continuity | `scene.entry_state`, `scene.exit_state`, `scene.object_state` |

### 2.3 적용 정책
- Core 12는 우선적으로 `strict/warn` 혼합 적용한다.
- Extended 6은 초기에는 `warn-only`로 시작하고 데이터가 쌓이면 강화한다.
- 모든 domain은 기본적으로 "강제 생성"이 아니라 "일관성 추적" 목적이다.
- `collect` 필드는 판단 재료 수집용이며, 서사 강제에 직접 사용하지 않는다.

## 3. 핵심 구조 (Field Registry + Facts + Events + Alias)

### 3.1 Field Registry
- 파일: `config/canon_fields.yaml`
- 단위: `entity_type.field_path`
- 필수 정책:
  - `domain_id`: `D01..D18`
  - `importance`: `core` | `normal`
  - `enforcement`: `collect` | `warn` | `strict`
  - `event_required`: bool
  - `conflict_policy`: `strict` | `soft`
  - `bounded_delta`: 수치 필드 급변 제한 규칙
  - `state_machine`: 허용 전이 정의

### 3.2 Canon Facts (현재값)
- 테이블 예시: `canon_facts`
- 컬럼 예시: `entity_id`, `field_path`, `value_json`, `updated_ep`, `confidence`
- 목적: 생성 시 빠른 스냅샷 주입

### 3.3 Canon Events (변경이력)
- 테이블 예시: `canon_events`
- 컬럼 예시: `event_id`, `entity_id`, `field_path`, `old_value_json`, `new_value_json`, `event_type`, `ep_num`, `evidence`, `approved_by`
- 목적: 변경 근거 추적, 롤백, 재구성

### 3.4 Alias/Normalization Layer
- 목적: C-13 계열(동일 아이템/동일 인물 별칭)을 정확히 식별
- 예시:
  - `item.aliases`: `천잠사의`, `비단 갑옷`, `갑옷`
  - `character.aliases`: 호칭/직함/별명
- 정책:
  - exact match 실패 시 alias 매칭
  - alias도 실패 시 similarity 후보 생성 + Director 판단

## 4. Stage 계약
| Stage | Canon Read | Canon Write | Python 역할 | 최종 판단 |
|---|---|---|---|---|
| Stage1 | Yes | No | collect/warning | Director |
| Stage2 | Yes | No | collect/warning | Director |
| Stage3 | Yes (강화) | No | warning/high_warning | Director |
| Stage4 | Yes (전체) | Yes (승인 후) | warning/high_warning | Director |

## 5. 생성 순서 정책 (정확도 우선)
- 권장 루프:
  - `1 Arc 확정 -> 즉시 Blueprint -> 즉시 Manuscript -> Stage4 Canon Commit -> 다음 Arc`
- 이유:
  - 장기 선생산(아크 여러 개 미리 확정)보다 drift 누적이 적다.
  - 커밋된 canon을 다음 아크에 즉시 재주입할 수 있다.
- 실무 모드:
  - 상세 확정: 현재 1아크
  - 다음 1아크는 개요만 유지 (rolling window)

## 6. 검증/판단 파이프라인
1. Stage별 생성 전에 Canon snapshot read 주입
2. Stage2/3은 변경 후보(candidate)만 생성
3. Stage4에서 후보 + 원고 증거를 통합
4. Python이 정책 기반 충돌 검사 후 `warning/high_warning` 생성
5. Director가 항목별로 결정:
   - `fix_text`
   - `accept_change`
   - `override_with_reason` (사유 필수)
7. **[Gemini 3.1 Pro / Antigravity 권고사항]**: 모든 Director 위반 개입, 사유 입력, 수동 패치 등은 동기식 `input()` 대신 UI 추상화 계층(`ui.ask_user()` 또는 `aioconsole`)을 통과하도록 강제하여 Event Loop Freezing을 방지해야 합니다.

## 7. 다필드 공통 규칙 템플릿
- `regression_without_event`:
  - 이전 대비 역행인데 필수 이벤트가 없으면 `high_warning`
- `state_machine_violation`:
  - 허용 전이 밖 변화면 `high_warning`
- `bounded_delta_violation`:
  - 수치 급변이 규칙 초과면 `high_warning`
- `mutual_exclusive_violation`:
  - 상호배타 상태 동시 존재 시 `high_warning`
- `alias_identity_conflict`:
  - 동일 엔티티 별칭이 분리 엔티티로 인식되면 `high_warning`
- `causality_gap`:
  - 결과는 있는데 원인 이벤트가 없으면 `warning/high_warning`

## 8. 코드 반영 최소 지점
- 저장 게이트: `modules/core/stage4_post_processor.py`
- Canon 저장/조회: `modules/core/db_manager.py`
- 누적 정규화: `modules/core/fact_ledger.py`
- 생성 컨텍스트 주입: `modules/core/stage4_context_builder.py`
- 연속성 경고 엔진: `modules/validation/continuity_validator.py`
- 아이템/엔티티 동일성 보강: `modules/domain/agents/continuity_inspector.py`
- Director 판단 연결: `modules/core/stage4_interview_round.py`

## 9. 무중단 복구 규칙
- 에피소드 커밋 시 `snapshot_id`, `event_cursor`를 함께 저장
- 컨텍스트 컴팩트/재시작 시 DB에서 상태 재구성
- 채팅 내 기억에 의존하지 않고 DB를 단일 진실원으로 사용

## 10. 롤아웃 (리스크 최소)
### Phase 0 (Shadow, 1주)
- 경고만 생성, 자동 차단 없음
- drift/오탐/토큰 비용 지표 수집

### Phase 1 (Core 12, 1~2주)
- D01~D12 우선 적용
- Stage4 승인 커밋 게이트 적용
- **[Gemini 3.1 Pro 권고사항]**: 이 시점에서 모든 수동 개입 인터페이스의 비동기화(`to_thread` 등) 점검 포함

### Phase 2 (Alias + C-13, 1주)
- item/character alias registry 도입
- exact-only 매칭 제거

### Phase 3 (Extended 6, 2주)
- D13~D18 warn-only 적용
- Stage2/3 read-only 주입 강화

### Phase 4 (운영 고정)
- 리그레션 테스트 자동화
- override 사유 로그 리뷰 주간 운영

## 11. KPI / 합격 기준
- 10화 연속에서 Core 12 회귀 0건
- C-13 유형(동일 아이템 별칭 오인식) 오탐/미탐 동시 감소
- 컨텍스트 컴팩트 후 canon 복원 성공률 100%
- high_warning 대비 실제 결함 정밀도 개선 추세
- Director override는 100% 사유/근거 로그 보유

## 12. 위험과 대응
- 위험: 규칙 과도 강화로 창의성 저하
  - 대응: Core는 strict 일부, Extended는 warn-only 유지
- 위험: 잘못 승인된 canon 오염
  - 대응: event 근거 저장, rollback 가능 구조 유지
- 위험: 토큰/지연 증가
  - 대응: 관련 엔티티 top-k 주입, 요약 주입 우선

## 13. 즉시 실행 체크리스트
- [ ] `config/canon_fields.yaml` 초안 작성 (D01~D18 포함)
- [ ] `canon_facts`/`canon_events` 스키마 추가
- [ ] item/character alias 레이어 스키마 추가
- [ ] Stage4 승인 커밋 인터페이스 추가
- [ ] continuity validator에 정책 기반 high_warning 추가
- [ ] Director 결정 타입 3종 강제 (`fix_text`, `accept_change`, `override_with_reason`)
- [ ] 1아크 롤링 생산 운영 전환
