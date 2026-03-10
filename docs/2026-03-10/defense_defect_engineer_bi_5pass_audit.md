# BI 5-Pass 감리 보고서 (2026-03-10)

## 대상
- phase0: `treatments/defense_defect_engineer_phase0_design.json`
- draft: `treatments/defense_defect_engineer_tr_block_070_draft.json`
- bi: `bible/0_bi_defense_defect_engineer.json`

## PASS 1: 인코딩/파싱
- result: OK
- utf8_json_parse: OK
- garbled_token_zero: OK
- draft_schema_valid: OK

## PASS 2: 최소 스키마
- result: OK
- validate_bible_structure: OK
- meta_title_present: OK
- plot_roadmap_len_70: OK

## PASS 3: 내부 정합성
- result: OK
- protagonist_match: OK
- title_match_phase0: OK
- starter_company_match: OK
- portfolio_monotonic: OK
- portfolio_sync_with_tr: OK

## PASS 4: TR↔BI 동기화
- result: OK
- roadmap_title_sequence: OK
- roadmap_first_last: OK
- roadmap_hash_equal: OK

## PASS 5: 품질 감리
- result: OK
- sample_fields_clean: OK
- foreign_token_zero: OK
- company_name_consistent: OK
- npc_name_consistent: OK

## 샘플링
- MetaInfo.title: 결함이 보이는 방산 엔지니어
- MetaInfo.grand_objective: 추락 사고의 책임을 뒤집어쓴 전생을 기억한 하준영이 설계 결함과 원가 누수와 납품 사기의 선을 동시에 읽는 능력으로, 안전을 명분 삼아 설계권과 시험평가권과 규격권을 독점하는 이야기.
- MetaInfo.genre_archetype: 현대 한국 방산 기업 패권 성장물
- MetaInfo.logline: 회귀한 항공공학자 하준영은 도면 위에 떠오르는 결함선과 비리선을 무기로 방산 프로젝트의 결함을 먼저 읽고, 그 정보 우위를 시험평가권과 협력사 라인과 수출 규격 통제권으로 바꿔 산업 실권자가 된다.
- CoreIdentity.protagonist: 하준영
- CoreIdentity.protagonist_faction: 현무에어로테크 결함검증실 (초기) -> 레드라인 디펜스 홀딩스 (후기)
- CoreIdentity.edge: 도면 위에서 결함선, 원가누수선, 비리선을 동시에 읽고 그것을 통제권으로 바꾸는 능력
- CoreIdentity.desire: 차세대 훈련기 추락 사고를 막는 동시에 결함검증 라인과 외부 검사권을 자기 손으로 가져온다.
- CoreIdentity.crisis: 까다롭고 입만 산 구조해석 엔지니어으로 취급받는 상태에서 출발하지만, 누구보다 먼저 병목을 읽는 순간 판을 다시 짠다.
- FinanceHUD.actual_truth.name: 하준영
- FinanceHUD.actual_truth.rank: 현무에어로테크 결함검증 태스크포스 합류 예정 외부 구조해석 전문가 / 현무에어로테크 핵심 설계권자
- FinanceHUD.actual_truth.current_objective: 차세대 훈련기 추락 사고를 막는 동시에 결함검증 라인과 시험평가권을 손에 넣는다.
- FinanceHUD.actual_truth.final_goal: 국내 방산 규격과 수출 패키지의 결정권을 장악해 산업 실권자가 된다.
- WorldState.CurrentEra: 2010년 3월 초
- WorldState.CurrentLocation: 현무에어로테크 본사 면접실 - 면접장 붉은 선
- KeyNPCs[0].name: 하준영
- KeyNPCs[1].name: 김도현
- KeyNPCs[2].name: 서기태
- plot_roadmap[0].title: 면접장 붉은 선
- plot_roadmap[34].title: 사막 시험권 매입
- plot_roadmap[69].title: 산업 실권자

## 메모
- summary: 5개 PASS 모두 통과

