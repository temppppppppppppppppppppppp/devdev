# Opus Report: Sweep300 대비 Manual Sweep100 비교

작성일: 2026-02-20  
대상 문서:
- `docs/codex_findings_sweep300.md`
- `docs/codex_findings_sweep100_manual.md`

## 1) 결론 요약
- `Sweep300`는 범위는 넓지만 문서 구조 중복과 포맷 불일치가 커서, 그대로는 고신뢰 의사결정 근거로 쓰기 어렵습니다.
- `Manual Sweep100`는 라운드 구조/근거 규칙/검증 스크립트 기준을 충족해 보고 신뢰도가 높습니다.
- Opus 보고 본문은 `Manual Sweep100`를 기준 본문으로 두고, `Sweep300`는 “보조 참고(coverage 확장)”로 제한하는 구성이 적절합니다.

## 2) 정량 비교
| 항목 | Sweep300 | Manual Sweep100 |
|---|---:|---:|
| 라운드 헤더 개수(파싱) | 600 | 100 |
| 고유 라운드 번호 범위 | 1~300 | 1~100 |
| 라운드 중복 | 있음 (각 라운드 2회) | 없음 |
| 최종 Confirmed Bugs | 60 (P1 14, P2 42, P3 4) | 1 (P1 1) |
| 최종 Risks | 35 | 41 |
| 최종 False Positives Excluded | 39 | 19 |
| 최종 Test Gaps | 90 | 100 |
| 최종 FP Ratio | 29.1% | 31.1% |
| 최종 Consecutive Empty Rounds | 58 | 0 |
| Manual Evidence Compliance Rate | 미기재 | 100% |

근거:
- `docs/codex_findings_sweep300.md:10413`
- `docs/codex_findings_sweep300.md:10417`
- `docs/codex_findings_sweep300.md:10422`
- `docs/codex_findings_sweep100_manual.md:2266`
- `docs/codex_findings_sweep100_manual.md:2270`
- `docs/codex_findings_sweep100_manual.md:2275`
- `docs/codex_findings_sweep100_manual.md:2276`

산출 기준:
- 라운드 헤더 개수는 문서 내 `### Round N` 블록 파싱 기준.
- Sweep300의 600개는 `1~300`이 2회 기록된 결과이며, 고유 라운드는 300개.
- 포맷 통과율은 `scripts/validate_manual_sweep.py`의 `validate_round` 규칙을 동일 적용해 계산.

## 3) 구조/신뢰도 차이
1. `Sweep300` 라운드 구조가 중복되어 문서 일관성 리스크가 큽니다.
- `Round 1`이 2회 존재: `docs/codex_findings_sweep300.md:3`, `docs/codex_findings_sweep300.md:4915`
- `Round 300`도 2회 존재: `docs/codex_findings_sweep300.md:4880`, `docs/codex_findings_sweep300.md:10395`

2. `Sweep300`는 수동검증 포맷 기준 충족률이 낮습니다.
- 내부 검증 로직 기준으로 1~300 범위 파싱 블록 600개 중 invalid 463개(통과율 22.8%).
- 반면 `Manual Sweep100`는 1~100 범위 invalid 0개(통과율 100%).

3. `Sweep300`의 폭넓은 버그 집계(60건)는 유효 참고 가치가 있으나, 포맷/중복 이슈로 “우선순위 확정 근거”로 바로 사용하기 어렵습니다.
- 예시: Stage2 cache sync 결함 기술 자체는 구체적임 `docs/codex_findings_sweep300.md:6`
- 다만 동일 라운드 중복 및 후반 반복 라운드 패턴으로 문서 신호대잡음비가 떨어집니다.

4. `Manual Sweep100`는 고강도 수동근거 중심 문서로, 확정버그는 1건으로 좁지만 근거-검증 정합성이 높습니다.
- 핵심 확정버그: cross-arc transition 누락 `docs/codex_findings_sweep100_manual.md:923`

## 4) Opus 보고 권장 서술
1. 본문 기준 문서: `Manual Sweep100`
- 이유: 라운드 단위 근거(`file:line`), 체크포인트, 검증 스크립트 통과, Evidence Compliance 100%.

2. 보조 근거 문서: `Sweep300`
- 이유: 초기 대규모 탐색 범위/주제 커버리지 참고.
- 단, “정제 전 참고본”으로 명시하고 수치 재사용 시 중복 제거/포맷 정규화 선행.

3. 경영/리드 의사결정 포인트
- “버그 총량”보다 “검증 가능성/재현성” 가중치를 높게 반영.
- `Sweep300`의 확정 버그는 재검증 큐로 재편성 후 재분류 권장.

## 5) 즉시 실행 액션
1. `Sweep300` 정제본 생성
- 중복 라운드(2회 기록) 제거
- 수동검증 포맷 불일치 라운드 정규화

2. `Manual Sweep100` 확정버그 우선 조치
- `modules/domain/agents/state_tracker.py:1449` cross-arc transition 누락 수정 및 회귀 테스트 추가

3. 보고 패키지 구성
- Opus 본문: 본 문서 + `Manual Sweep100` 핵심 라운드(40, 100 checkpoint)
- 부록: `Sweep300`에서 재검증 대상 상위 이슈 목록
