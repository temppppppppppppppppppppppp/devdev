# Work Guards

`work_guards/`는 Stage 0에서 선택적으로 가져올 작품가드 원본 라이브러리다.

- 런타임 적용 파일은 언제나 `{project}/config/work_guard.yaml`이다.
- 이 폴더 아래 YAML은 템플릿/샘플/원본 보관용이다.
- 작품가드는 필수 입력이 아니다. 없는 프로젝트도 정상 baseline으로 Stage 0~4를 진행해야 한다.

publish 원칙:

- `material_ssot` 재료 사이드에서 작성/감리 완료된 작품별 `work_guard`는 최종 publish본을 이 라이브러리로 올릴 수 있다.
- Stage 0 가시성을 위해 publish 경로는 `work_guards/<genre>/<work_id>.yaml` 또는 `work_guards/<work_id>.yaml`를 표준으로 삼는다.
- 실전 browse 가독성을 위해 live publish본에는 `work_guards/NN_<work_id>.yaml`처럼 2자리 번호 prefix를 붙여도 된다.
- Stage 0 browse가 기본으로 보지 않는 deep nested publish lane은 표준으로 쓰지 않는다.
- work-specific publish본은 내부 `work_identity.work_id`를 canonical `work_id`로 유지하고, 숫자 prefix는 file ordering용으로만 취급한다.

구분 원칙:

- `default_work_guard.yaml`는 장르 lane의 얇은 기본 템플릿이어야 한다.
- 특정 작품의 참고 카드, research pack, YouTube raw 경로는 기본 템플릿에 과도하게 넣지 않는다.
- 작품별 고유 doctrine, concrete registry_profiles, role_fit_constraints는 개별 `work_guard.yaml`에서 선언한다.
- research synthesis 정본은 `material_ssot/10_research/` 쪽 문서에 두고, work guard는 그것을 번역한 runtime 규칙만 담는다.

검증 진입점:

- draft 또는 publish 후보는 먼저 `python -X utf8 scripts/run_work_guard_v1.py --path <yaml>`로 `WG-V1` shape validation을 돌린다.
- `--work-id <work_id>`를 쓰면 라이브러리 publish 경로를 바로 찾아 검증할 수 있다.
- 이 검증은 `PASS / HOLD / FAIL`만 표면화하며, stage detection이나 runtime optionality를 바꾸지 않는다.

권장 구조:

- `work_guards/investment/`
- `work_guards/wuxia/`
- `work_guards/hunter/`

Stage 0에서는 아래 중 하나를 선택한다.

1. 라이브러리에서 가져오기
2. 기본 템플릿으로 초기화
3. 현재 프로젝트 작품가드 미리보기
4. 현재 프로젝트 작품가드 삭제
