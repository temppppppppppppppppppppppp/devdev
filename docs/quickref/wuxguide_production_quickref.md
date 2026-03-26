# WuxGuide 프로덕션 Quick-Ref (wuxia-production-harness)

## 절대 규칙 요약

### 블록 순서
- **1블록씩 순차 생산**. 블록 건너뛰기 절대 금지.
- 현재 블록이 검증 통과해야 다음 블록 진입.
- `auto-run`도 내부 단위는 여전히 1블록.
- 같은 운영 오더에서 **최대 5블록까지만** 자동 연속 진행.
- `Block 005/010/015...` 경계에 도달하면 새 오더 전까지 정지.

### 인코딩
- **UTF-8 only**. BOM 금지, EUC-KR 금지.

### 경지 연속성
- `realm_before` = 직전 블록의 `realm_after` (정확히 일치).
- 최초 블록은 BI의 realm_at_arrival과 일치해야 함.

### 경지 역행 금지
- **경지 역행 금지**. 상위 경지에서 하위 경지로의 하락 불가.
- 예외: 부상 또는 봉인에 의한 일시적 하락만 허용 (사유 필수 기록).

### 돌파 규칙
- **내공 인과 없는 돌파 금지**. 수련·전투·비급 습득 등 명시적 사유 없이 경지 상승 불가.
- 돌파 블록에서 martial_event 필드에 사유 기록 필수.

### NPC 규칙
- **사망 NPC 행동 금지**. 사망 처리된 NPC는 이후 블록에서 등장·대사·행동 불가.

### 서사 원칙
- **self-interest-first (자기이익 우선)**: 주인공은 의리나 도덕보다 생존과 세력 확장을 우선한다.

### MartialHUD 기록
- **MartialHUD 17필드 매 블록 기록**. 블록 끝에 반드시 갱신.
- realm, internal_energy, martial_arts, faction, injuries 등 전체 상태 스냅샷.
- 누락 필드 발생 시 검증 실패.

### 검증 및 저장
- **Python 검증 스크립트 실행 후 저장**. 검증 미통과 시 저장 금지.
- `block_continuity_checker.py --family wuxguide` 통과 필수.
- fixed.json 생성 = 감리 통과 확정.
- 재개 포인터는 `sequential_run_status.json`을 먼저 읽고, `next_block_id` 기준으로 판단.

### 기타
- 에피소드 분량: TR 지정 범위 준수.
- 모든 JSON 출력은 ensure_ascii=False.
