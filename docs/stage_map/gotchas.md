# Gotchas — 새 세션 AI 주의사항

> 이 문서를 먼저 읽어라. 코드 보기 전에 알아야 할 함정들.

## G-1. Stage 3 REJECT는 실제 운영에서 잘 안 터진다
**현상**: Director 비교 선택에서 보통 최소 1개 후보가 높은 점수를 받아 REJECT 루프가 길게 이어지지 않는다. 운영 관측(2026-02-25, `0225_1`)에서도 이 패턴이 반복됐다.  
**원인**: Stage 3은 Director 비교 선택 후 점수 게이트(80)만 추가 적용하는 구조라, "모순 없음 = 고득점" 경향이 있으면 REJECT 빈도가 낮아진다.  
**실제 영향**: `_inplace_patch_blueprint()`/전면 재생성 분기가 구현돼 있어도 실사용 빈도는 낮을 수 있다.  
**확인 위치**: `modules/domain/agents/three_phase_blueprint_generator.py:334`, `modules/domain/agents/three_phase_blueprint_generator.py:368`, `modules/domain/agents/director_ensemble.py:143`, `docs/stage_map/ENHANCE_ORDER.md`

## G-2. PASS_WITH_WARNING은 생각보다 쉽게 발동한다
**현상**: 재시도 종료 후 `last_score >= 50`이면 최종 verdict를 `PASS_WITH_WARNING`으로 올린다.  
**원인**: 실패 후 긴급 폴백 조건이 `PatchModeThresholds.REWRITE(50)` 기준으로 열려 있기 때문이다.  
**실제 영향**: "완전 실패(FAILED)"는 `score < 50`이거나 생성 결과 자체가 없는 경우로 수렴한다.  
**확인 위치**: `modules/domain/agents/three_phase_blueprint_generator.py:448`, `modules/domain/agents/three_phase_blueprint_generator.py:452`, `modules/core/constants.py:563`

## G-3. Blueprint txt는 사람이 읽는 백업이고, Stage 4 입력은 DB다
**현상**: `plans/blueprints/*.txt`를 고쳐도 Stage 4 입력에 반영되지 않는다.  
**원인**: Stage 4는 `current_project.get_blueprint(next_ep)` -> `db.get_blueprint()` 경로만 사용한다. txt는 export artifact다.  
**실제 영향**: Blueprint 수정은 DB(`blueprints`) 기준으로 해야 한다. txt-only 수정은 무효다.  
**확인 위치**: `modules/core/stage4_orchestrator.py:335`, `modules/core/project_manager.py:832`, `modules/core/db_manager.py:774`, `modules/core/project_manager.py:380`

## G-4. WARNING 로그가 많아도 실제 오류가 아닐 수 있다
**현상**: 정보성 메시지가 `logging.warning`으로 출력되는 구간이 있다.  
**원인**: 레거시 로깅 레벨 정리가 완전히 끝나지 않았다.  
**실제 영향**: WARNING 개수만으로 장애 판단하면 오탐이 난다. 메시지 본문/컨텍스트를 같이 봐야 한다.  
**확인 위치**: `modules/domain/agents/blueprint_ensemble.py:188`, `modules/domain/agents/unified_blueprint_validator.py:103`

## G-5. Director 주권주의를 Python 게이트가 덮어쓰면 안 된다
**현상**: Director 프롬프트 기준보다 Python QualityGate가 높으면, Director PASS를 Python이 REJECT로 뒤집는 역전이 발생한다.  
**원인**: Stage별 점수 게이트를 분리하지 않으면 기준선이 충돌한다.  
**실제 영향**: Stage 3은 `blueprint_quality_gate_score=80`으로 Director 기준과 맞춰야 한다. 새 코드도 이 원칙을 유지해야 한다.  
**확인 위치**: `modules/domain/agents/three_phase_blueprint_generator.py:368`, `config/settings/validation.yaml:34`, `config/settings/validation.yaml:35`

## G-6. quality gate 임계값은 Stage별로 다르다
**현상**: 같은 `PASS`여도 Stage별 최소 점수가 다르다.  
**원인**: Stage 3은 Blueprint 전용 게이트(80), Stage 2/4는 공통 게이트(90)로 분리 설계됐다.  
**실제 영향**: 임계값을 통합하거나 복붙 수정하면 Stage 간 품질/재시도 동작이 깨진다.  
**확인 위치**: `config/settings/validation.yaml:34`, `config/settings/validation.yaml:35`, `modules/core/stage4_interview_round.py:873`, `modules/core/stage2_finalizer.py:182`

## G-7. 수치 모순은 "후보 탈락"과 "라운드 실패"를 구분해서 봐야 한다
**현상**: Director는 후보별로 수치/사실 모순을 잡아 특정 후보만 탈락시킬 수 있다.  
**원인**: 비교 프롬프트가 후보별 모순 검사를 강제하고, `contradictions` 필드를 별도로 반환한다.  
**실제 영향**: 모순 검출이 있어도 다른 후보가 PASS면 라운드는 통과한다. 운영 해석 시 "후보 REJECT"와 "라운드 REJECT"를 분리해야 한다.  
**확인 위치**: `modules/domain/agents/director_ensemble.py:129`, `modules/domain/agents/director_ensemble.py:136`, `modules/domain/agents/director_ensemble.py:190`, `modules/domain/agents/three_phase_blueprint_generator.py:349`, `docs/stage_map/ENHANCE_ORDER.md`

## G-8. Arc는 단일 anchor(`key='arcs'`)로 저장된다
**현상**: Arc는 화별 row가 아니라 하나의 JSON 리스트로 관리된다.  
**원인**: `save_v20_anchor("arcs", data)`가 `anchors.key='arcs'`를 덮어쓰는 구조다.  
**실제 영향**: `DELETE FROM anchors WHERE key='arcs'`는 Stage 2 전체 Arc를 한 번에 지운다(메뉴 88).  
**확인 위치**: `modules/core/project_manager.py:264`, `modules/core/project_manager.py:272`, `modules/core/db_manager.py:202`, `modules/core/services/project_service.py:65`
