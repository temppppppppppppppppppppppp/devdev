# BlockGuide 프로덕션 Quick-Ref (treatment-production-harness-v2)

## 절대 규칙 요약

### 블록 순서
- **1블록씩 순차 생산**. 블록 건너뛰기 절대 금지.
- 현재 블록이 검증 통과해야 다음 블록 진입.
- `auto-run`도 내부 단위는 여전히 1블록.
- 같은 운영 오더에서 **최대 5블록까지만** 자동 연속 진행.
- `Block 005/010/015...` 경계에 도달하면 새 오더 전까지 정지.

### 인코딩
- **UTF-8 only**. BOM 금지, EUC-KR 금지.

### 자본 연속성
- `capital_before` = 직전 블록의 `capital_after` (정확히 일치).
- 최초 블록은 BI의 초기 자산과 일치해야 함.
- 인과 없는 자산 변동 금지.

### deal_type 규칙
- **동일 deal_type 3블록 연속 금지**. 2블록까지만 허용.
- deal_type은 반드시 TR에 명시된 범위 내에서 선택.

### NPC 규칙
- **사망 NPC 행동 금지**. 사망 처리된 NPC는 이후 블록에서 등장·대사·행동 불가.
- 사망 블록 번호를 기록하고 이후 참조 시 체크.

### 서사 원칙
- **self-interest-first (자기이익 우선)**: 주인공은 도덕적 선택보다 이득과 통제권을 우선한다.
- 캐릭터 행동은 BI의 execution_doctrine과 일치해야 함.

### 검증 및 저장
- **Python 검증 스크립트 실행 후 저장**. 검증 미통과 시 저장 금지.
- `block_continuity_checker.py --family blockguide` 통과 필수.
- fixed.json 생성 = 감리 통과 확정.
- 재개 포인터는 `sequential_run_status.json`을 먼저 읽고, `next_block_id` 기준으로 판단.

### 기타
- 에피소드 분량: TR 지정 범위 준수.
- HUD 17필드 매 블록 끝에 갱신 기록.
- 모든 JSON 출력은 ensure_ascii=False.
