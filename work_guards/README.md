# Work Guards

`work_guards/`는 Stage 0에서 선택적으로 가져올 작품가드 원본 라이브러리다.

- 런타임 적용 파일은 언제나 `{project}/config/work_guard.yaml`이다.
- 이 폴더 아래 YAML은 템플릿/샘플/원본 보관용이다.
- 작품가드는 필수 입력이 아니다. 없는 프로젝트도 정상 baseline으로 Stage 0~4를 진행해야 한다.

권장 구조:

- `work_guards/investment/`
- `work_guards/wuxia/`
- `work_guards/hunter/`

Stage 0에서는 아래 중 하나를 선택한다.

1. 라이브러리에서 가져오기
2. 기본 템플릿으로 초기화
3. 현재 프로젝트 작품가드 미리보기
4. 현재 프로젝트 작품가드 삭제
