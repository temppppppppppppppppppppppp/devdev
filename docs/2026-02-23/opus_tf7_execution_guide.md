# TF-7 Codex 실행 가이드 — 마스터 오더

> **작성일**: 2026-02-23
> **베이스라인**: 2,377 passed, ruff 0 violations, commit `9f0de73`
> **목적**: TF-7 A~N 14개 Opus 에이전트의 병렬/순차 실행 조율

---

## ★★★ Codex 실행 수칙 (최우선, 절대 준수) ★★★

```
1. rg / freg / gfreg / grep / find 등 셸 자동 탐색 도구 절대 금지
   → 반드시 Read 도구로 파일을 직접 읽어 검사

2. 수정 금지 — 감사 단계에서는 코드 변경 없음
   → 발견 사항 문서화만. 패치 오더는 별도 문서로

3. 근거 필수 — 파일명:줄번호 + 코드 스니펫
   → "가능성 있음" 수준 주관 판단은 이슈 등록 금지

4. 인코딩 주의 — 모든 파일 I/O는 UTF-8 기준
   → open() encoding 미명시, ensure_ascii 미설정 경로 탐지

5. 컨텍스트 컴팩트 시 → 이 문서 + 해당 TF 오더 파일 재독 후 이어서 진행
   → 절대 처음부터 다시 시작하지 않음
```

---

## 무중단 운영 프로토콜 (Compact-Safe)

컨텍스트 컴팩트가 발생해도 아래 고정 절차로 즉시 재개한다.

### 고정 체크포인트 파일
- `docs/2026-02-23/opus_tf7_checkpoint.md`

### 컴팩트 직후 재개 순서 (고정)
1. `docs/2026-02-23/opus_tf7_execution_guide.md` 재독
2. `docs/2026-02-23/opus_tf7_system_audit_order.md` 재독
3. `docs/2026-02-23/opus_tf7_checkpoint.md`에서 `Last Completed TF`와 `Next Action` 확인
4. 수동 스윕 validator 실행
   - 시작 전(빈 라운드 허용): `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --allow-empty`
   - 라운드 시작 후(엄격 검증): `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100`
   - FP 게이트(권장): `python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
5. 체크포인트의 다음 TF 오더 파일로 즉시 복귀
6. 라운드 종료마다 체크포인트를 갱신하고 다음 액션을 명시

### 무중단 운영 규칙
- 활성 스윕 라운드 중에는 사용자 질의 없이 진행(차단 사유만 예외)
- 차단 시 1회만 보고: `Blocker / Last Completed Round / Next Action`
- 기존 완료 라운드는 재스윕하지 않고 마지막 완료 지점부터 이어서 진행

---

## 실행 순서 (3단계)

### Phase 1: 독립 병렬 실행 가능 (6개)

다음 TF는 서로 독립적이므로 동시에 실행 가능:

| TF | 주제 | 오더 파일 | 출력 파일 |
|----|------|-----------|----------|
| **TF-7-A** | Stage0 모듈 교차 버그 | `opus_tf7_a_order.md` | `opus_tf7_a_audit.md` |
| **TF-7-F** | 인코딩·직렬화 안전성 | `opus_tf7_f_order.md` | `opus_tf7_f_audit.md` |
| **TF-7-G** | Narrative Diversity / Repetition | `opus_tf7_g_order.md` | `opus_tf7_g_audit.md` |
| **TF-7-I** | Adaptive Retry / Feedback Loop | `opus_tf7_i_order.md` | `opus_tf7_i_audit.md` |
| **TF-7-J** | Emotion / Foreshadow / Karma | `opus_tf7_j_order.md` | `opus_tf7_j_audit.md` |
| **TF-7-M** | YAML / Prompt Config | `opus_tf7_m_order.md` | `opus_tf7_m_audit.md` |

### Phase 2: Phase 1 결과 일부 참조 (5개)

TF-7-A, F, J 결과를 참조하면 더 정확하나, 독립 실행도 가능:

| TF | 주제 | 참조 TF | 오더 파일 | 출력 파일 |
|----|------|---------|-----------|----------|
| **TF-7-B** | Context Advisor / SC | - | `opus_tf7_b_order.md` | `opus_tf7_b_audit.md` |
| **TF-7-C** | Director 체인 | - | `opus_tf7_c_order.md` | `opus_tf7_c_audit.md` |
| **TF-7-D** | Validation Orchestrator | - | `opus_tf7_d_order.md` | `opus_tf7_d_audit.md` |
| **TF-7-H** | Genre Guard 체인 | TF-7-A | `opus_tf7_h_order.md` | `opus_tf7_h_audit.md` |
| **TF-7-L** | Quality Dashboard | TF-7-I | `opus_tf7_l_order.md` | `opus_tf7_l_audit.md` |

### Phase 3: Phase 1+2 결과 참조 (3개)

| TF | 주제 | 참조 TF | 오더 파일 | 출력 파일 |
|----|------|---------|-----------|----------|
| **TF-7-E** | World State / Fact Ledger | TF-7-D | `opus_tf7_e_order.md` | `opus_tf7_e_audit.md` |
| **TF-7-K** | Stage0 Preset ↔ Stage2 | TF-7-A | `opus_tf7_k_order.md` | `opus_tf7_k_audit.md` |
| **TF-7-N** | 크로스컷 시나리오 (종단간) | 전체 TF | `opus_tf7_n_order.md` | `opus_tf7_n_audit.md` |

---

## 진행 테이블

| TF | 주제 | Phase | 상태 |
|----|------|-------|------|
| TF-7-A | Stage0 모듈 교차 버그 | 1 | ⬜ |
| TF-7-B | Context Advisor / SC | 2 | ⬜ |
| TF-7-C | Director 체인 완전성 | 2 | ⬜ |
| TF-7-D | Validation Orchestrator | 2 | ⬜ |
| TF-7-E | World State / Fact Ledger / State Delta | 3 | ⬜ |
| TF-7-F | 인코딩·직렬화 안전성 | 1 | ⬜ |
| TF-7-G | Narrative Diversity / Repetition | 1 | ⬜ |
| TF-7-H | Genre Guard 체인 완전성 | 2 | ⬜ |
| TF-7-I | Adaptive Retry / Feedback Loop | 1 | ⬜ |
| TF-7-J | Emotion / Foreshadow / Karma | 1 | ⬜ |
| TF-7-K | Stage0 Preset ↔ Stage2 | 3 | ⬜ |
| TF-7-L | Quality Dashboard / Metrics | 2 | ⬜ |
| TF-7-M | YAML / Prompt Config | 1 | ⬜ |
| TF-7-N | 크로스컷 시나리오 | 3 | ⬜ |
| **종합 보고서** | opus_tf7_consolidated_report.md | 종료 후 | ⬜ |

---

## 이슈 분류 기준 (공통)

| 등급 | 기준 | 예시 |
|------|------|------|
| CRITICAL | 데이터 유실·무한루프·크래시 | 롤백 후 사망NPC 재등장 경로 |
| HIGH | silent 품질 저하·검증 무력화·잘못된 PASS | karma_service 스텁, blueprint=None silent PASS |
| MEDIUM | 관측 사각·매직넘버·계약 불일치 | YAML 키 누락, 상한 미설정 |
| LOW | 스타일·주석·위생 | |
| FP | 실제 문제 없음 | 코드 읽기 오류, 설계 의도 확인 |

---

## 종합 보고서 형식

**파일**: `docs/2026-02-23/opus_tf7_consolidated_report.md`

```markdown
# TF-7 종합 감사 보고서

## 1) 전체 발견 건수
| 심각도 | 건수 |
|--------|------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |
| 합계 | N |

## 2) TF별 분포
| TF | 파일 | CRITICAL | HIGH | MEDIUM | LOW | 핵심 이슈 |

## 3) Cross-TF 이슈 (복수 TF 연관)

## 4) TF-5/6 패치 회귀 확인 결과
| 패치 ID | 확인 여부 | 증거 |

## 5) 우선순위 제안 (P0/P1/P2)

## 6) 패치 오더 연계 → opus_tf7_patch_order.md
```

---

## 베이스라인 검증 명령

감사 시작 전 1회 실행 (코드 변경 없으므로 이후 재실행 불필요):
```bash
pytest tests/ -q
python -m ruff check modules/ tests/ main_a.py
python -m ruff format --check modules/ tests/ main_a.py
```

기대 결과: `2377 passed`, ruff 0 violations

---

## 문서 파일 목록

| 파일 | 역할 |
|------|------|
| `opus_tf7_system_audit_order.md` | TF-7 전체 상세 감사 오더 |
| `opus_tf7_execution_guide.md` | **본 파일** — 마스터 실행 가이드 |
| `opus_tf7_checkpoint.md` | 컨텍스트 컴팩트 대응용 운영 체크포인트 |
| `opus_tf7_a_order.md` | TF-7-A 세부 실행 오더 |
| `opus_tf7_b_order.md` | TF-7-B 세부 실행 오더 |
| `opus_tf7_c_order.md` | TF-7-C 세부 실행 오더 |
| `opus_tf7_d_order.md` | TF-7-D 세부 실행 오더 |
| `opus_tf7_e_order.md` | TF-7-E 세부 실행 오더 |
| `opus_tf7_f_order.md` | TF-7-F 세부 실행 오더 |
| `opus_tf7_g_order.md` | TF-7-G 세부 실행 오더 |
| `opus_tf7_h_order.md` | TF-7-H 세부 실행 오더 |
| `opus_tf7_i_order.md` | TF-7-I 세부 실행 오더 |
| `opus_tf7_j_order.md` | TF-7-J 세부 실행 오더 |
| `opus_tf7_k_order.md` | TF-7-K 세부 실행 오더 |
| `opus_tf7_l_order.md` | TF-7-L 세부 실행 오더 |
| `opus_tf7_m_order.md` | TF-7-M 세부 실행 오더 |
| `opus_tf7_n_order.md` | TF-7-N 세부 실행 오더 |
| `opus_tf7_{a~n}_audit.md` | 각 TF 감사 결과 (Opus 작성) |
| `opus_tf7_consolidated_report.md` | 종합 보고서 (Opus 작성) |
| `opus_tf7_patch_order.md` | 패치 오더 (종합 후 별도 작성) |
