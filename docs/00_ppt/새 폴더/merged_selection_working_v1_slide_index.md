# merged_selection_working_v1 slide index

- source A: `Geuldobi_AI_Production_Briefing [복구].pptx`
- source B: `geuldobi-pipeline-compact-human-brief-draft_(3차).pptx`
- merged output: `merged_selection_working_v1.pptx`

## Slide map

| Merged # | Source | Original # | Title | Preview |
| --- | --- | --- | --- | --- |
| 1 | A | 1 | 목표사항 | 목표사항 | 집필 | - | 편집 루프 대체 | 1/8 | 핵심 선언 |
| 2 | A | 2 | 목표 구조와 현재 상태 | 목표 구조와 현재 상태 | 지향은 인간 배제이고, 현재는 drift 때문에 과도기라는 점을 분리해서 본다 | 2/8 | 축 | 최종 지향 | 현재 상태 |
| 3 | A | 3 | 생산 파이프라인 | 생산 파이프라인 | Stage 0-2-3-4를 거치며 AI가 설계, 생산, 평가를 수행한다 | 3/8 | Stage | 입력 | 출력 |
| 4 | A | 4 | 왜 사업 구조가 바뀌는가 | 왜 사업 구조가 바뀌는가 | 핵심은 품질 보조가 아니라 선인세, RS, IP 통제, 생산 스케일의 재편이다 | 4/8 | 비교 항목 | 인간 포트폴리오 | 글도비 운영 |
| 5 | A | 5 | 인간 포트폴리오도 안전하지 않다 | 인간 포트폴리오도 안전하지 않다 | AI 비용만 과하게 위험해 보이는 착시는 인간 시장의 편차를 빼고 보기 때문에 생긴다 | 5/8 | 관찰 | 숫자 | 뜻 |
| 6 | A | 6 | 기술적으로 어디까지 왔는가 | 기술적으로 어디까지 왔는가 | AI가 쓰고 AI가 평가하는 구조는 이미 어느 수준까지는 작동하고 있다 | 7/8 | 항목 | 현재 상태 | 의미 |
| 7 | B | 1 | Stage 0-2-3-4 전체샷 | Stage 0-2-3-4 전체샷 | 모든 스테이지에 저장 전 판정 또는 handoff 차단 지점이 있다 | Stage | 0 | 이런 | 세계관 |
| 8 | B | 2 | 현재 주요 병목 3가지 | 현재 주요 병목 3가지 | 운영 관찰상 retry 비용, 계약 정규화, 인간 선호 품질이 핵심 병목이다 | 최적화 문제 | 안정화 문제 | 돌아는 가는 상태 | 구조 |
| 9 | B | 3 | 현재 취약점과 해결 방안 | 현재 취약점과 해결 방안 | FE 시나리오별로 보면 취약점의 무게중심이 달라지지만, 공통 핵심은 API/자격증명 관리다 | FE 포기 · 운영 전용 백엔드 | 현재 취약점 | • | 주요 리스크는 외부 해킹보다 평문 API 키 저장, 백업본, subprocess env 확산이다. |
| 10 | B | 4 | 수정 | 수정 | 루프 | PASS_WITH_FIX는 accept branch 내부 patch loop이고, REJECT는 retry routing으로 빠진다 | PASS | accept and persist | 사후 검증까지 통과하면 저장 후보가 된다. |
| 11 | B | 5 | 전체 구조 | 전체 구조 | 머메이드 |

## Quick pick format

- `remove: 2, 5, 9`
- `keep: 1, 3, 4, 7, 8`
- `edit: 6 title`, `edit: 10 bullets`, `move: 11 after 4`