# BI 5-Pass 감리 보고서 (2026-03-11)

## 대상
- phase0: `treatments/chaebol_allowance_zero_phase0_design.json`
- draft: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- bi: `bible/02_bi_chaebol_allowance_zero.json`

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
- MetaInfo.title: 재벌 3세인데 용돈이 0원
- MetaInfo.grand_objective: 회귀한 윤성그룹 3세 윤재이가 유언장 때문에 가문 돈 한 푼 못 쓰는 상태에서 급식, 세탁, 청소, 폐기물, 셔틀, 소모품 같은 생활 인프라 계약을 묶어 현금흐름 제국을 만들고, 끝내 가문이 먼저 그 돈줄에 의존하게 한다.
- MetaInfo.genre_archetype: 현대 한국 재벌 하청 캐시플로우 장악물
- MetaInfo.logline: 카드가 잘린 장례식장 뒷문에서 윤재이는 상속보다 돈줄이 먼저라는 걸 배운다. 그는 회귀 전 기억으로 재벌집 밑단의 B2B 계약을 하나씩 집어삼키고, 끝내 가문이 매일 쓰는 돈의 관문이 된다.
- CoreIdentity.protagonist: 윤재이
- CoreIdentity.protagonist_faction: 제로라인파트너스 (초기) -> 윤성그룹 필수 운영망을 쥔 제로라인파트너스 (후기)
- CoreIdentity.edge: 어느 현장에 어떤 지출이 언제 터지고 누가 그 돈줄을 쥐면 조직이 흔들리는지 기억하는 회귀자의 생활권 지식
- CoreIdentity.desire: 상속을 구걸하지 않고, 가문이 먼저 자기 현금흐름을 찾게 만든다.
- CoreIdentity.crisis: 유언장 7항으로 카드와 계좌가 모두 끊긴 채 0원에서 출발하고, 형과 CFO가 실패를 기다린다.
- FinanceHUD.actual_truth.name: 윤재이
- FinanceHUD.actual_truth.rank: 윤성그룹 오너 3세 / 제로라인파트너스 대표
- FinanceHUD.actual_truth.current_objective: 윤성그룹 계열사들이 매일 쓰는 운영비의 절반 이상을 자기 네트워크로 돌린다.
- FinanceHUD.actual_truth.final_goal: 가문이 먼저 자기 현금흐름망에 의존하게 만들어 상속보다 강한 지배권을 갖는다.
- WorldState.CurrentEra: 2022년 10월 초
- WorldState.CurrentLocation: 제로라인 본사 / 윤성그룹 전략포럼
- KeyNPCs[0].name: 윤재이
- KeyNPCs[1].name: 노현주
- KeyNPCs[2].name: 서도윤
- plot_roadmap[0].title: 잘린 카드
- plot_roadmap[34].title: 닫힌 외래동
- plot_roadmap[69].title: 상속보다 센 돈줄

## 메모
- summary: 5개 PASS 모두 통과

