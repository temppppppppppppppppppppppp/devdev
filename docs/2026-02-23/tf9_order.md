# TF-9 Codex 실행 오더

---

## 너의 임무

글도비 프로젝트의 TF-9 패치를 수행한다.
TF-8 2차 감리에서 발견된 HIGH 1건 + MEDIUM 3건을 순서대로 수정하고 테스트를 추가한다.

---

## 시작 전 필수 2단계

1. **플랜 문서 전체를 읽어라**
   `docs/2026-02-23/tf9_patch_plan.md`

2. **findings 파일을 읽어라**
   `docs/2026-02-23/tf9_findings.md`
   → "현재 위치" 섹션 확인 → 마지막 완료 Step 이후부터 시작

---

## 절대 수칙

1. **각 Step은 반드시 Read 도구로 해당 파일을 직접 읽은 후 수정한다**
   셸 자동 탐색 도구(`grep`, `find`, `rg`) 금지. Read만 허용.

2. **pytest 통과 = 완료가 아니다**
   코드를 읽지 않은 Step은 무효다.

3. **근거 필수**
   모든 수정은 `파일명:줄번호 + 수정 전/후 스니펫`을 기록한다.
   플랜 문서의 코드 스니펫은 참고용이다 — 실제 줄 번호는 Read 후 직접 확인한다.

4. **감사 없음 — 수정만**
   이번 TF는 감사 단계 없이 플랜 문서에 명시된 수정만 수행한다.

5. **각 Step 완료 즉시 tf9_findings.md "현재 위치" 섹션을 업데이트한다**
   이것이 컨텍스트 컴팩트 복구의 유일한 기준점이다.

---

## 컨텍스트 컴팩트 복구

리셋이 발생하면:
1. `docs/2026-02-23/tf9_patch_plan.md` 재독
2. `docs/2026-02-23/tf9_findings.md` 재독
3. "현재 위치" 섹션에서 다음 미완료 Step 확인
4. 그 Step부터 즉시 재개
5. **절대 Step 1부터 다시 시작하지 않는다**

---

## Step 순서

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5
```

| Step | 내용 | 등급 |
|------|------|------|
| Step 1 | arc_no 전달 수정 (TF8R-1) — stage4_context_builder.py | HIGH |
| Step 2 | invalid mode 경고 로그 — stage2_preflight.py + stage4_context_builder.py | MEDIUM |
| Step 3 | retrieval_mode 라우팅 테스트 신규 파일 작성 | MEDIUM |
| Step 4 | D2 로그 caplog 테스트 추가 — test_vec_memory.py | MEDIUM |
| Step 5 | 최종 pytest + ruff + 커밋 | — |

플랜 문서에 각 Step의 수정 위치, 코드 스니펫, 검증 명령이 상세히 명시되어 있다.

---

## 완료 기준

- pytest 2,545+ passed, 0 xfailed
- ruff 0 violations
- tf9_findings.md "현재 위치" = Step 5 (TF-9 완료)
- 최종 커밋 메시지: `fix(tf9): arc_no retrieval 전달 수정 + MEDIUM 백로그 패치 (TF8R-1/F-2/I-2/I-3)`

---

지금 바로 `docs/2026-02-23/tf9_patch_plan.md`를 읽는 것부터 시작하라.
