# WuxGuide BI Quick-Ref (wuxia-bi-production-harness)

## 절대 규칙 요약

### TR Gate Pass
- **TR gate pass 필수**. TR 감리를 통과하지 않은 작품은 BI 생성 불가.
- TR 통과 증빙: audit_status.json의 audit_pass == true.

### plot_roadmap 규칙
- **plot_roadmap = TR에서 그대로 복사**. 재작성 절대 금지.
- 블록 번호, 순서, 내용 일체 수정 불가.
- 70블록 고정 (minItems: 70, maxItems: 70).

### MartialHUD 최종 경지
- **MartialHUD 최종 경지 = TR Block 70의 realm_after**.
- BI의 martial_status.realm은 TR 마지막 블록 경지를 반영.
- realm_history 마지막 항목과 일치해야 함.

### 5-Pass 감리 체크리스트
1. **Pass 1 (구조)**: JSON 스키마 유효성, 필수 필드 존재, plot_roadmap 70블록 확인.
2. **Pass 2 (연속성)**: realm_before/after 블록 간 연속성, internal_energy 이월, 경지 역행 검사.
3. **Pass 3 (인물)**: 사망 NPC 재등장 여부, protagonist 이름 일치, CoreIdentity 정합성.
4. **Pass 4 (서사)**: self-interest-first 원칙 준수, 인과 없는 돌파 검출, 부상/봉인 이월 정합성.
5. **Pass 5 (최종)**: BI ↔ TR 교차 검증, MartialHUD 최종 경지 일치, UTF-8 인코딩 확인.

### 기타
- BI 파일명: `{work_id}_bi.json`
- _schema_version 필수 기재.
- 모든 출력 UTF-8, ensure_ascii=False.
