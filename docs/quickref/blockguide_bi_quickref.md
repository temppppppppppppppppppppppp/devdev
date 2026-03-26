# BlockGuide BI Quick-Ref (bi-production-harness-v1)

## 절대 규칙 요약

### TR Gate Pass
- **TR gate pass 필수**. TR 감리를 통과하지 않은 작품은 BI 생성 불가.
- TR 통과 증빙: audit_status.json의 audit_pass == true.
- TR이 70블록 완료 전이거나, TR 5블록 창 중간 정지 상태면 BI 진입 금지.

### Auto-Handoff 경계
- TR의 **5블록 cap은 upstream 전용**. BI는 block count로 계산하지 않는다.
- BI auto-run은 `스켈레톤 -> 동기화 -> UTF-8 저장 -> 5-Pass 감리` 1사이클까지만 허용.
- PASS/FAIL 보고가 나오면 새 오더 전까지 재생성 루프 금지.

### plot_roadmap 규칙
- **plot_roadmap = TR에서 그대로 복사**. 재작성 절대 금지.
- 블록 번호, 순서, 내용 일체 수정 불가.
- 70블록 고정 (minItems: 70, maxItems: 70).

### FinanceHUD 최종값
- **FinanceHUD 최종값 = TR Block 70의 capital_after**.
- BI의 financial_status는 TR 마지막 블록 상태를 반영.
- portfolio_history 마지막 항목과 일치해야 함.

### 5-Pass 감리 체크리스트
1. **Pass 1 (구조)**: JSON 스키마 유효성, 필수 필드 존재, plot_roadmap 70블록 확인.
2. **Pass 2 (연속성)**: capital_before/after 블록 간 연속성, deal_type 3연속 위반 검사.
3. **Pass 3 (인물)**: 사망 NPC 재등장 여부, protagonist 이름 일치, CoreIdentity 정합성.
4. **Pass 4 (서사)**: self-interest-first 원칙 준수, 인과 없는 자산 점프 검출.
5. **Pass 5 (최종)**: BI ↔ TR 교차 검증, FinanceHUD 최종값 일치, UTF-8 인코딩 확인.

### 기타
- BI 파일명: `{work_id}_bi.json`
- _schema_version 필수 기재.
- 모든 출력 UTF-8, ensure_ascii=False.
