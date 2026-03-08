# 실파이프라인 감사 07 — Stage 4 원고 전수조사 (00000, 2026-03-08)

> **대상**: `projects/00000/drafts/ep_0001.txt ~ ep_0015.txt` (15편)
> **감사 범위**: 코드 버그 + 콘텐츠 모순 + 경고 오탐 + 반복 패턴
> **감리**: 2라운드 (1차 3-에이전트 병렬 + 2차 교차검증)
> **확신도**: 99%

---

## 파이프라인 실행 요약

| 항목 | 값 |
|------|-----|
| Stage 2 | 5 Arc, REJECT 1건 (ep2 → 3회차 PASS) |
| Stage 3 | 20 Blueprint, 20/20 PASS |
| Stage 4 | 15 에피소드, REJECT 3건 (ep10×2, ep15×1) → 15/15 최종 PASS |
| Director 평균 점수 | 97.9 (96~100) |
| 평균 분량 | 5,259자 (4,157~6,452) |
| 총 소요 | ~2시간 (10:55~12:51) |

---

## 발견 사항

### BUG-1 [P0/CRITICAL] ep_0015.txt InPlace 패치 JSON 미파싱

**증상**: `drafts/ep_0015.txt`에 원고가 아닌 Python dict 문자열이 그대로 저장됨.

```
# 제15화

{'corrected_manuscript': '고요함은 때로 칼날보다...', 'patch_state_updates': {'location.office.floor': 15}}
```

**발생 경위** (episode_production.jsonl):
- ep15 Round 0: PASS score=98, strategy=tension → **Director가 PASS_WITH_FIX로 판정**
- ep15 Round 1: strategy=inplace_patch, verdict=PASS, score=90, flags.mad=true

**근본 원인 추적**:

1. `chief_writer.inplace_patch()` (L775-883): LLM이 `{"corrected_manuscript": "...", "patch_state_updates": {...}}` 형태로 반환
2. TF-47 JSON 파싱 1단계 (L832-849): `patched_text`, `content`, `text`, `manuscript`, `patched_manuscript` 키를 순서대로 시도
3. **문제**: LLM이 `corrected_manuscript` 키로 반환 → 5개 키 중 어디에도 매칭 안 됨
4. `_manuscript` = `""` → 2단계 폴백(마커 기반)으로 넘어감
5. 2단계에서도 마커를 못 찾으면 → **dict 전체가 문자열로 변환되어 반환**

**누락된 키**: `corrected_manuscript`가 TF-47 파싱 키 목록에 없음.

**수정 방향**: `chief_writer.py` L842-849에 `corrected_manuscript` 키 추가:
```python
_manuscript = (
    _parsed.get("corrected_manuscript")  # ← 추가
    or _parsed.get("patched_text")
    or _parsed.get("content")
    or _parsed.get("text")
    or _parsed.get("manuscript")
    or _parsed.get("patched_manuscript")
    or ""
)
```

**영향 범위**: InPlace 패치를 사용하는 모든 Stage (S2/S3/S4). 단, LLM이 `corrected_manuscript` 키로 응답하는 경우에만 발생.

**관련 코드**:
- `modules/domain/agents/chief_writer.py` L832-849 (TF-47 파싱)
- `modules/core/stage4_interview_round.py` L1306 (결과 추출)
- `modules/core/stage4_post_processor.py` L323-324 (파일 저장)

---

### CON-1 [P1/MAJOR] 장비 수준 모순 (ep_05 vs ep_10)

**ep_0005.txt L18,24,28**: 블룸버그 터미널 + 모니터 4대 + 서버급 컴퓨터 설치 완료
```
"블룸버그 터미널 포함, 최고 사양으로."
거대한 곡면 모니터 네 개가 스탠드에 장착되고, 서버급 사양의 컴퓨터 본체가 책상 아래 자리를 잡았다.
```

**ep_0010.txt L9**: 같은 사무실을 "동네 PC방" 수준으로 묘사
```
고작 노트북 한 대와 모니터 몇 개로 이뤄진 이 임시 지휘소는, 동네 PC방보다 나을 게 없었다.
```

**판정**: 5화에서 고급 장비를 설치했는데, 10화에서 그 장비가 사라진 것처럼 서술. Blueprint 씬이 "시스템 업그레이드"를 지시했으나, CW가 기존 장비를 무시하고 처음부터 없었던 것처럼 작성.

---

### CON-2 [P1/MAJOR] NPC 직함 불일치 (박성호 차장→팀장)

**ep_0006.txt L28**: `"박성호 차장님 연결 부탁합니다."`
**ep_0011.txt L21,65**: `"박성호 팀장님"` / `"박 팀장."`
**ep_0012~15**: 일관되게 "팀장"

**판정**: 승진 에피소드 없이 직함 변경. ep_0006의 "차장"이 오류일 가능성 높음 (이후 전부 "팀장").

---

### CON-3 [P1/MAJOR] 블랙베리 수량 불일치 (3대 주문→4개 배달)

**ep_0010.txt L55**: `"블랙베리 7290, 세 대 더 추가해주십시오."`
**ep_0011.txt L9**: `팀 리더가 작은 상자 네 개를 들고 내게 다가왔다.`

**판정**: 3대 주문 → 4개 배달. 수량 불일치.

---

### CON-4 [P1/MAJOR] 1인칭/3인칭 시점 혼재 (ep_10)

**ep_0010.txt L75** (마지막 행):
```
모든 것이 제자리를 찾아가자, 한시우는 비로소 이 고독한 싸움에서 승리할 수 있다는 확신을 얻었다.
```

전체 작품이 1인칭("나") 시점인데, 이 행만 3인칭("한시우는"). POV 체크(V70)가 이 문장을 잡지 못함.

---

### CON-5 [P2/MINOR] 시대 고증 오류 (2006년 태블릿 PC)

**ep_0004.txt L73**: `중개인의 얼굴에 당혹감이 스쳤다. 그는 재빨리 태블릿 PC로 무언가를 확인하더니`

2006년 1월 시점, 태블릿 PC(MS Tablet PC 규격)는 존재했지만 일반 부동산 중개인이 사용할 정도로 보편적이지 않았음. 경미한 시대 오류.

---

### CON-6 [P2/INFO] 반복 패턴 과다 (6종)

| 패턴 | 발생 횟수 | 에피소드 |
|------|----------|---------|
| "톱니바퀴" 은유 | 11회+ | ep1,2,4,5,6,7,8,9,13 |
| 박성호 전화 패닉→차갑게 끊음 | 7회 | ep8,9,11,12,13,14,15 |
| "창가에서 도시 내려다보며 독백" 엔딩 | 5회 | ep9,10,11,12,13 |
| "오케스트라/지휘자" 은유 | 4회 | ep4,7,9 |
| "이것은 도박이 아니다" 선언 | 2회 | ep5,8 |
| ep_09→ep_10 동일 장면 반복 | 1회 | ep9 끝 = ep10 시작 |

**판정**: WritingDirective(TF-54)가 패턴 추적 중이나, 현재 데이터 양(15화)이 누적 분석 기준(직전 N화)을 만족하지 못해 효과 미미. Block/Treatment에서 다양한 씬 설계 필요.

---

### WARN-1 [P2/INFO] 대화 비율 전체적으로 낮음

15편 전체에서 `"대화 부족: 0개 (최소 4개)"` 경고 반복. Director가 매번 "서사적 필연성"으로 기각.

**코드 위치**: `pre_director_manuscript_checker.py` L62-76
**원인**: `min_dialogue = 4` 하드코딩, 장르별 분기 없음.
**판정**: 투자물은 심리 묘사/나레이션 중심으로 대화가 적은 것이 정상. 다만 웹소설 기준으로는 개선 여지 있음. Block/Treatment에서 대화 장면 설계로 해결 가능.

---

### WARN-2 [P2/INFO] "부상 상태" 오탐

`[V66.1] 부상 상태에서 무리한 행동 감지` 경고가 투자물에서 반복 발생.

**원인**: `genre_schema_builder.py`가 투자물에도 `injuries` 필드 생성 → LLM이 "부상 상태 없음"을 "상태 불명"으로 해석 → 오탐
**판정**: 오탐. 투자물에서 injuries 필드가 비어있으면 경고 스킵 필요.

---

### WARN-3 [P2/INFO] "개미 자칭 불가" 오탐

`[V63.2] 직위에서 '개미' 자칭 불가` 경고 반복 (ep6,9,13,14,15).

**원인**: 주인공이 타인을 "개미"로 지칭한 것을 시점 체크가 주인공 자칭으로 오인.
**판정**: 오탐. Director가 매번 기각.

---

### WARN-4 [P2/INFO] quality_metrics.jsonl Stage 4 score=0

Stage 4 PASS 항목의 score가 전부 0. 실제 점수는 episode_production.jsonl에만 기록됨.

**원인**: `quality_dashboard.py` L121에서 `result.get("score", 0)` → validation 레이어가 Director 점수를 전달하지 않는 설계.
**판정**: 의도된 설계. episode_production.jsonl이 SSOT. 혼동 방지를 위해 quality_metrics에도 점수 전파하면 좋겠으나 P3 수준.

---

## 1차 조사 오탐 제거

| 항목 | 1차 판정 | 2차 교차검증 결과 |
|------|---------|----------------|
| 박성호 경력 10년→15년 모순 | MAJOR | **오탐 제거** — ep_0006에 "10년" 언급 없음. 15년은 ep_0013에서만 등장. |

---

## 패치 우선순위

| 순서 | ID | 심각도 | 유형 | 설명 |
|------|-----|--------|------|------|
| 1 | BUG-1 | P0/CRITICAL | 코드 | `corrected_manuscript` 키 누락 → InPlace JSON 미파싱 |
| 2 | CON-1 | P1 | 콘텐츠 | 장비 수준 모순 (5화 설치 vs 10화 무시) |
| 3 | CON-2 | P1 | 콘텐츠 | 박성호 직함 (차장→팀장) |
| 4 | CON-3 | P1 | 콘텐츠 | 블랙베리 수량 (3대→4개) |
| 5 | CON-4 | P1 | 콘텐츠 | 1인칭/3인칭 혼재 (ep_10 마지막 행) |
| 6 | CON-5 | P2 | 콘텐츠 | 태블릿 PC 시대 고증 |
| 7 | CON-6 | P2 | 콘텐츠 | 반복 패턴 6종 |
| 8 | WARN-1 | P2 | 코드 | 대화 비율 장르 분기 없음 |
| 9 | WARN-2 | P2 | 코드 | 부상 상태 투자물 오탐 |
| 10 | WARN-3 | P2 | 코드 | 개미 자칭 오탐 |
| 11 | WARN-4 | P3 | 코드 | quality_metrics score=0 |

---

## 코드 패치 대상 (BUG-1만 즉시 패치 필요)

### BUG-1 수정

**파일**: `modules/domain/agents/chief_writer.py`
**위치**: L842-849 (TF-47 JSON 파싱 1단계)
**변경**: `corrected_manuscript` 키를 파싱 키 목록 첫 번째에 추가

### 콘텐츠 모순 (CON-1~5)

콘텐츠 모순은 **코드 수정 대상이 아님**. 다음 파이프라인 실행 시 Block/Treatment 설계에서 방지해야 함. 다만 시스템 차원에서:
- CON-2 (직함): NPC 속성 DB에 직함이 기록되므로, StateTracker가 정상 작동했다면 CW에 올바른 직함이 전달되었어야 함. StateTracker→CW 전달 경로 확인 필요.
- CON-4 (시점): V70 POV 체크가 마지막 문장을 놓침. 3인칭 감지 로직 확인 필요.

---

## 감리 이력

| 라운드 | 내용 | 결과 |
|--------|------|------|
| 1차 | 3-에이전트 병렬 (InPlace 버그 / 경고 오탐 / 콘텐츠 모순) | BUG 1건 + CON 6건 + WARN 4건 |
| 2차 교차검증 | InPlace 정확한 코드 경로 + 콘텐츠 모순 원문 대조 | 오탐 1건 제거 (경력 10년→15년) |
| **최종** | **P0 1건 + P1 4건 + P2 4건 + P3 1건 = 10건** | **확신도 99%** |
