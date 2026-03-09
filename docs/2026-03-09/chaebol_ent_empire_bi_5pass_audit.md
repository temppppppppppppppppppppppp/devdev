# BI 5-Pass 감리 보고서 (2026-03-09)

## 대상
- phase0: `treatments/chaebol_ent_empire_phase0_design.json`
- draft: `treatments/chaebol_ent_empire_tr_block_070_draft.json`
- bi: `bible/0_bi_chaebol_ent_empire.json`

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
- MetaInfo.title: 망나니 재벌 3세의 엔터 제국
- MetaInfo.grand_objective: 유통·식품·호텔 중심 재벌가의 망나니 3세가, 누가 스타가 될지와 어떻게 띄워야 할지 직감하는 감각을 무기로 망해가는 소형 엔터 자회사를 배우·아이돌·유튜버·스트리머·셰프·팬덤 플랫폼을 포괄하는 스타 IP 대기업으로 키운다.
- MetaInfo.genre_archetype: 현대 한국 엔터 타이쿤 성장물
- MetaInfo.logline: 인정받지 못한 재벌 3세 권태하는 부친이 던져 준 적자 엔터 자회사에서 아무도 못 알아본 재능들을 집어 올리고, 사람과 포맷과 공간을 묶는 감각으로 한국 엔터 산업의 규칙 자체를 바꾼다.
- CoreIdentity.protagonist: 권태하
- CoreIdentity.protagonist_faction: 세령컬처웍스 (초기) -> 스타 IP 복합기업 세령컬처웍스 (후기)
- CoreIdentity.edge: 누가 뜰지뿐 아니라 어떤 포지션, 어떤 순서, 어떤 포맷으로 띄워야 하는지까지 읽는 스타 감각
- CoreIdentity.desire: 아버지에게 인정받기보다 자신의 사람 보는 눈이 맞다는 것을 증명한다.
- CoreIdentity.crisis: 술, 여자, 새벽, 카드값으로 대표되는 망나니 도련님으로 낙인찍혀 문화 사업에서도 실패를 기대받는 상태에서 출발한다.
- FinanceHUD.actual_truth.name: 권태하
- FinanceHUD.actual_truth.rank: 세령그룹 오너 3세 / 세령컬처웍스 대표
- FinanceHUD.actual_truth.current_objective: 세령컬처웍스를 청산 직전 상태에서 생존시킨다.
- FinanceHUD.actual_truth.final_goal: 자신의 방식을 업계 표준으로 만든다.
- WorldState.CurrentEra: 2009년 8월 말
- WorldState.CurrentLocation: 세령그룹 회장실 / 세령컬처웍스 지하 연습실
- KeyNPCs[0].name: 권태하
- KeyNPCs[1].name: 권도현
- KeyNPCs[2].name: 한도윤
- plot_roadmap[0].title: 쓰레기통 상속
- plot_roadmap[34].title: 한 군데에 기대지 않는다
- plot_roadmap[69].title: 인정이 아니라 표준

## 메모
- summary: 5개 PASS 모두 통과

