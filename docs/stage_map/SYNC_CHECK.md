# stage_map 동기화 체크 — 실행 프롬프트

> 사용법: 이 파일을 Claude에게 던지거나 "stage_map 동기화 체크해" 라고 말하면 됨.

---

## 실행 프롬프트 (Claude에게 그대로 전달)

```
docs/stage_map/SYNC_CHECK.md 읽고 동기화 체크 실행해줘.
```

---

## 체크 절차

### Step 1. 마지막 체크 기준점 파악
- `docs/stage_map/doc_status.md` 읽기
- 각 파일의 `Last Verified` 커밋 해시 확인

### Step 2. 그 이후 변경된 코드 파일 확인
아래 bash 명령으로 커밋 이후 변경 파일 목록 추출:
```bash
git log --oneline -20
git diff {마지막_커밋}..HEAD --name-only
```

### Step 3. 변경 파일 → 대응 stage_map 파일 매핑

| 변경된 코드 경로 | 확인할 stage_map 파일 |
|---|---|
| `modules/core/stage2_*.py` | `stage2.md`, `interfaces.md` |
| `modules/core/stage3_*.py` | `stage3.md` |
| `modules/core/stage4_*.py` | `stage4.md` |
| `modules/domain/agents/three_phase_blueprint_generator.py` | `stage3.md`, `gotchas.md` |
| `modules/domain/agents/director*.py` | `stage2.md`, `stage3.md`, `stage4.md` |
| `modules/domain/agents/chief_writer*.py` | `stage4.md` |
| `modules/core/db_manager.py` | `interfaces.md` |
| `modules/core/project_manager.py` | `interfaces.md`, `runbook.md` |
| `modules/core/services/project_service.py` | `runbook.md` |
| `modules/core/stage0/` | `stage0.md` |
| `config/settings/validation.yaml` | `metrics_baseline.md`, `stage3.md` |
| `modules/core/constants.py` | `metrics_baseline.md` |
| `main_a.py` | `runbook.md` |

### Step 4. 대응 파일 읽고 불일치 판단

변경된 코드 핵심 내용과 stage_map 문서 내용 대조.
판단 기준:
- 임계값 수치 변경 → `metrics_baseline.md` 수치 불일치
- 함수명/진입점 변경 → 해당 stage 파일 Entry Points 불일치
- 흐름/분기 변경 → 해당 stage 파일 Key Flow 불일치
- 새로운 함정 패턴 발견 → `gotchas.md` 누락 여부
- DB 테이블/계약 변경 → `interfaces.md` 불일치
- 롤백/초기화 동작 변경 → `runbook.md` 불일치

### Step 5. 보고

아래 형식으로 출력:

```
## stage_map 동기화 체크 결과 (YYYY-MM-DD)

### ✅ 동기화됨
- [파일명]: 변경 없음 또는 문서 반영 확인

### ⚠️ 업데이트 필요
- [stage_map 파일]: [불일치 내용]
  - 코드: [실제 값/동작]
  - 문서: [현재 기재된 값/동작]
  - 수정 제안: [한 줄]

### 📝 판단 불가 (직접 확인 필요)
- [항목]: [이유]
```

### Step 6. 업데이트 여부 사용자 결정
- 사용자가 "고쳐" 하면 해당 stage_map 파일 수정
- 사용자가 "넘어가" 하면 `doc_status.md`에 "Known mismatch" 기록

---

## 실행 주기 권장

| 시점 | 체크 범위 |
|---|---|
| 코드 대규모 수정 후 | 전체 |
| 특정 스테이지 버그 수정 후 | 해당 stage.md + gotchas.md |
| 임계값 변경 후 | metrics_baseline.md 단독 |

---

## 제약

- bash `git log` / `git diff` 는 허용 필요 (파일 목록 추출용)
- Read 툴로 코드 직접 읽기 (rg/grep 자동화 금지)
- 불일치 판단은 LLM이 함 — 100% 자동 아님, 반자동
