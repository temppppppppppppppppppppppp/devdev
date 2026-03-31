# narrative contracts

Status: scaffold draft
Date: 2026-03-31

이 폴더는 `narrative_ssot/`의 실행 계약층이다.

구성:

- top-level contract json
- stage별 schema
- quality gate
- handoff rule

원칙:

- 사람 설명은 `md`
- 기계 계약은 `json`
- V0.1에서는 최소 계약만 잠근다
- legacy와 scaffold가 공존하므로, cutover 전까지는 schema가 곧바로 legacy 정본을 대체하지 않는다

