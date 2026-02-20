# OPUS 실행 지시서: Truncation(절삭) 수동 감사

> 작성일: 2026-02-20  
> 목적: "컨텍스트 충분"인데도 정보가 사라지는 원인을 코드 절삭/샘플링 관점에서 수동 검증

---

## 1. 목표

1. LLM 한도 문제가 아니라 **코드 선절삭(pre-truncation)** 때문에 정보 손실이 나는 지점을 찾는다.
2. 장르/인물/설정/사건/수치(재산, 레벨, 직함) 연속성 훼손의 원인이 되는 절삭 로직을 식별한다.
3. "설계 의도"와 "실버그"를 분리해 오탐 없이 보고한다.

---

## 2. 강제 규칙 (중요)

1. `rg`, `grep`, `freg`, `findstr`, 대량 자동 스캔 스크립트 사용 금지.
2. 코드 파일을 직접 열어 **수동 판독**으로 확인한다.
3. 모든 판정은 `파일:라인` 근거를 붙인다.
4. 설계 의도 가능성이 있으면 `Reject` 금지, `Warning`으로만 남긴다.
5. Python 도구는 집계/정리 용도만 허용, 결함 최종 판정은 LLM이 수행한다.

---

## 3. 감사 범위 (우선순위)

1. Stage0 핵심:
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/story_expander.py`
- `modules/core/stage0/reverse_expander.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage0/preset_registry.py`
- `modules/core/constants.py`

2. Stage1~4 전달 경로:
- Stage별 context builder / validator / post processor / finalizer
- prompt 생성부, input 조립부, 저장 전 정규화부

3. 공통 유틸:
- JSON 파서/정규화, 요약기, tracker/fact ledger, HUD 루팅

---

## 4. 수동 점검 절차

1. 엔트리에서 호출 체인을 손으로 따라간다.
- 입력 생성 -> 전처리 -> LLM 호출 -> 파싱 -> 저장

2. 각 단계에서 아래 항목을 체크한다.
- 하드 절삭: `text[:N]`, `list[:N]`, `split()[:N]`
- 샘플 축소: "처음 N개만", "최근 N개만"
- 길이 상한: `max_tokens`, `max_output_tokens`, char budget
- 폴백: unknown 장르/키 누락 시 임의 기본값 대체

3. 절삭 지점마다 아래를 기록한다.
- `before` 정보량(개념적으로 어떤 정보가 있었는지)
- `after` 정보량(어떤 정보가 사라졌는지)
- 손실 종류(장르/인물/설정/수치/플롯)
- 설계 의도 가능성 여부

4. 판정 기준
- `Critical`: 연속성 붕괴 가능(직함 회귀, 능력 소실, 장르 오분류 등)
- `Medium`: 품질 저하/누락 가능, 즉시 붕괴는 아님
- `Warning`: 의도된 가드일 수 있어 추가 정책 판단 필요

---

## 5. 필수 검증 포인트

1. Stage0 절삭 상수 하드코딩 존재 여부 (`[:3000]`, `[:2000]`, 샘플 3개 등)
2. Skeleton/outline 대량 단일 호출로 인한 후반 누락 리스크
3. 장르 목록 불일치 -> unknown genre -> MartialHUD 폴백 경로
4. 하드코딩 모델명으로 SSOT 상수 변경이 무시되는 경로
5. retry/fallback 부재로 빈 결과가 정상 흐름으로 전파되는 경로

---

## 6. 산출물 형식 (반드시 준수)

`docs/opus_truncation_manual_audit_findings_2026-02-20.md` 생성:

1. Findings (심각도 순)
- ID
- 판정(Critical/Medium/Warning)
- 파일:라인
- 실제 코드 근거
- 영향 시나리오 1줄
- "설계 의도 가능성" 코멘트

2. Non-findings (오탐 방지)
- 의도된 제한/정책으로 판단한 항목
- 왜 버그가 아닌지 근거

3. Patch proposal (최소 변경 우선)
- 상수화/SSOT 정렬
- hard truncation -> smart truncation
- 배치 호출로 분할
- fail-open -> degraded 표식 강화

4. Regression tests
- 긴 입력에서 핵심 사실 보존 검증
- 장르/직함/능력/수치 연속성 테스트

---

## 7. 완료 기준 (DoD)

1. 최소 1회차: Stage0 전 파일 수동 확인 완료
2. 최소 2회차: Stage1~4 전달 경로 샘플 수동 확인
3. 모든 finding에 `파일:라인` 근거 존재
4. 오탐 방지용 non-finding 섹션 포함
5. "코드 절삭 vs 모델 한도" 원인 분리 결론 명시

---

## 8. OPUS 전달용 한 줄 지시

"자동 검색 금지. Stage0~4를 수동으로 읽고, 선절삭/샘플 축소/폴백 때문에 연속성 깨지는 지점을 파일:라인 근거로만 보고하라. 설계 의도는 Warning으로 분리하고 오탐 금지."
