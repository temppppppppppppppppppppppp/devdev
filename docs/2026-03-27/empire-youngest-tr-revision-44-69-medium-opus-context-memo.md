# Empire Youngest TR Revision (Block 44-69 MEDIUM) — OPUS Context Memo

Date: 2026-03-27
Purpose: minimal handoff memo for worker OPUS (fresh context)
Target: `empire_youngest_allsector` Block 44, 45, 47, 53, 55, 56, 57, 60, 67

## 1. Project Context (for fresh session)

`empire_youngest_allsector`는 blockguide family의 서사 작품.
- 주인공 이준서가 2045년에서 2025년으로 회귀, 신용카드 3,000만원으로 시작해 200조 all-sector 제국을 건설하는 이야기.
- TR(treatment) 70블록 + BI(bible) 1개가 `_quarantine`에 있으며 아직 active path로 승격되지 않은 상태.

## 2. What's Already Done (이전 세션들)

| 단위 | 상태 | 요약 |
|------|------|------|
| truth-reconciliation re-audit | 완료 | 70블록 존재 확인, 품질 MIXED |
| weakness report | 완료 | 5축 gap catalog. HIGH 7 / MEDIUM 9 / LOW 5 분류 |
| TR revision Block 32-43 | **완료** | 12블록 확장 (avg 558→1,401자, ×2.51). POV merge, 이준혁 1-beat |
| TR revision Block 44-69 HIGH | **완료** | 7블록 확장 (avg 362→1,373자, ×3.79). 최다은/정하윤 gap closer |
| TR revision Block 44-69 MEDIUM | **이번 런** | 9블록 domain texture 복원 |

**절대 수정 금지 블록**:
- Block 1-31 (원본)
- Block 32-43 (확장 완료)
- Block 46, 50, 52, 62, 65 (기존 full narrative)
- Block 54, 58, 59, 61, 63, 64, 66 (HIGH 확장 완료)
- Block 48, 49, 51, 68, 69 (LOW — 의도적 스킵)

## 3. The 9 Blocks

| block_id | chars | sector | core need |
|----------|-------|--------|-----------|
| 44 | 230 | 금융/PE | 정하윤 LP 설득 대면 |
| 45 | 173 | 금융/핀테크 | 오승아 금융 인가 (→Block 46 setup) |
| 47 | 147 | 패션/럭셔리 | 파리 패션위크 visual spectacle |
| 53 | **105** | 에너지/SMR | **최소 블록**. heavy-tech domain texture 0 |
| 55 | 344 | 방산 | 권도준 납품, AI 드론 시연 |
| 56 | 256 | 에너지/풍력 | 해상풍력 입찰, 현장 |
| 57 | 391 | 에너지/규제 | **준서 첫 타이밍 실패**. "기다리지 않는다" 시험 |
| 60 | 273 | EV/배터리 | 대기업 입찰 경쟁, 창업자 설득 |
| 67 | 276 | 구조조정 | 노조 대면, Block 66 "정리하겠습니다" 실행 |

## 4. This Run's Core Task

**Domain texture 복원**. 이전 확장(32-43, HIGH)이 protagonist engine + 감정선이었다면, 이번은 **각 섹터의 고유 언어**가 핵심.

"투자하고 성공했다"가 아니라 "이 섹터에서는 이런 일이 벌어진다"를 장면으로 보여줄 것.

## 5. Quality Baseline

- content chars: 1,200-2,000 (HIGH보다 약간 짧아도 됨)
- domain-specific language: ≥ 2 per block
- tactile detail: ≥ 1
- direct dialogue: ≥ 1
- JSON 4-key structure 유지

## 6. Creative Anchors

- `세 개씩. 쉬지 않고.`: Block 57에서 직접 시험 (좌절에도 멈추지 않음)
- all-sector rolling: 9개 섹터 각각 고유 언어 필수
- low-affect: Block 57(좌절), Block 67(구조조정) 억제 유지
- independent-capital: PE LP 구조 + 자력 유지

## 7. Supporting Cast

- **정하윤**: Block 44 (PE 펀드레이징 주도)
- **오승아**: Block 45 (금융 인가), Block 53 (SMR 기술 실사)
- **권도준**: Block 55 (방산 납품 — Block 35 영입의 payoff)

## 8. Do Not Do

- 위에 나열한 수정 금지 블록 수정
- 새 블록 추가
- BI / status / gate 수정
- 코드 수정
- 2,000자 초과 팽창
- 섹터 간 장면 패턴 반복 ("미팅→협상→성사" 동일 구조)

## 9. Main Order Doc

- `docs/2026-03-27/opus-empire-youngest-tr-revision-44-69-medium-order.md`

여기에 per-block 상세 가이드, sector language 목록, scene entry 다양화 테이블이 있음.

## 10. Expected Deliverables

1. 수정된 TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
2. 변경로그: `docs/2026-03-27/empire-youngest-tr-revision-44-69-medium-changelog.md`

## 11. Suggested One-Line OPUS Prompt

```text
너는 이번 런의 worker-OPUS다. `docs/2026-03-27/opus-empire-youngest-tr-revision-44-69-medium-order.md`와 `docs/2026-03-27/empire-youngest-tr-revision-44-69-medium-opus-context-memo.md`를 UTF-8로 읽고, `empire_youngest_allsector` TR Block 44, 45, 47, 53, 55, 56, 57, 60, 67을 weakness report 기반으로 확장 수정하라. 핵심은 sector domain texture 복원. 블록 수 70 유지. 수정 범위 9블록만. 이전 확장 결과(32-43, HIGH 7블록) 절대 수정 금지.
```

Confidence:
- 97% this memo provides sufficient context for a fresh-session worker OPUS
