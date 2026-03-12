# 00_test_00 수동 원고 감리

> 작성일: 2026-03-11
> 범위: `projects/00_test_00` Arc 1 / ep 1~4
> 감리 방식: 직접 판독 3-pass
> 판정축: 모순 방지 우선
> 최종 등급: `부분적`

---

## 0. 최종 판정

- 최종 산출물 `ep_0001.txt` ~ `ep_0004.txt`에는 이번 1-arc 범위에서 확인되는 `hard contradiction`이 없다.
- 다만 `Director가 모순을 막는 제1 역할을 정말로 잘 했느냐`에 대한 답은 `부분적`이다.
- 이유는 두 갈래다.
  - 결과물 기준: 최종 원고는 `Stage 2 -> 3 -> 4` 설계 연속성을 대체로 유지했고, 특히 ep1 클리프행어와 ep2/ep3 화간 연결은 안정적이다.
  - 과정 기준: Stage 3에서 고유명사/시간축 drift가 실제로 발생했고, Stage 4는 이를 일부 복구했지만 review 과정은 length / keyword gate / InfoParadox 오탐에 심하게 흔들렸다.

이번 수동 감리의 결론은 아래 두 줄로 압축된다.

1. `최종 텍스트는 생각보다 안정적이다.`
2. `그 안정성을 만들어내는 review 과정은 아직 신뢰하기 어렵다.`

---

## 1. 기준 입력과 읽은 파일 목록

### 1.1 기준 입력

- `bible/01_bi_투자물_골든_sample.json`
  - 프로젝트 메타: `골든 루트 (가제)`
  - 장르: `investment + 회귀물`
  - 주인공: `한시우`
  - 회귀 지점: `2024 -> 2006년 1월`, `26세`, `승마 국가대표 은퇴 직후`
- `treatments/01_tr_투자물_골든_sample.json`
  - Block 1 핵심: 회귀 직후 독립 선언, 개인 자산 정리, 투자 법인 설립, 원유 선물 진입 준비
- `projects/00_test_00/stage0_output/style_guide.json`
  - `tone`: `진지하고 결연함 (초반의 절망적이고 어두운 톤에서 회귀 후 냉철하고 계산적인 톤으로 전환)`
  - `pov`: `1인칭`

### 1.2 실제 읽은 산출물

- Stage 2: `projects/00_test_00/plans/arcs/arc_001.txt`
- Stage 3:
  - `projects/00_test_00/plans/blueprints/blueprint_0001.txt`
  - `projects/00_test_00/plans/blueprints/blueprint_0002.txt`
  - `projects/00_test_00/plans/blueprints/blueprint_0003.txt`
  - `projects/00_test_00/plans/blueprints/blueprint_0004.txt`
- Stage 4:
  - `projects/00_test_00/drafts/ep_0001.txt`
  - `projects/00_test_00/drafts/ep_0002.txt`
  - `projects/00_test_00/drafts/ep_0003.txt`
  - `projects/00_test_00/drafts/ep_0004.txt`
- 보조 근거:
  - `projects/00_test_00/logs/session_20260311_112831.log`
  - `projects/00_test_00/logs/episode_production.jsonl`
  - `projects/00_test_00/project_data.db`

### 1.3 수동 감리 taxonomy

- `hard contradiction`: 앞 화 / 상위 설계와 정면 충돌
- `soft drift`: 의미는 유지되지만 시간, 고유명사, 수치 강도가 흔들림
- `omission`: blueprint/arc 핵심 사건이 약화되거나 빠짐
- `allowed enrichment`: 설계와 충돌 없는 확장
- `warning false positive`: 로그/체커는 경고했지만 텍스트상 defect로 보기 어려움

---

## 2. Pass 1: 팩트 ledger

| 항목 | 기준 팩트 | 근거 |
|---|---|---|
| 주인공 | `한시우`, 2024년 고독사 후 2006년 1월로 회귀한 26세 | Bible, Treatment |
| 시점 / 톤 | `1인칭`, 진지하고 결연한 톤 | `style_guide.json:2-3` |
| 가족 축 | 아버지 `한정호`, 형 `한태준`, `한태민`과의 무관심/긴장 관계 | Treatment Block 1, arc |
| 독립 선언 | 그룹 돈과 이름을 쓰지 않고 `투자사`를 직접 세운다 | Treatment Block 1, `arc_001.txt` |
| 자산 정리 | 어머니 유산 계열사 주식, 강남 상가, 애마 `아퀼라` 포함 개인 자산 정리 | `arc_001.txt:51` |
| 자본금 | 개인 자산 정리 후 `20억 3천만 원` 확보 | `arc_001.txt:51` |
| 법인 잔고 | 사무실/설립 비용 차감 후 법인 계좌 `19억 5천만 원` | `arc_001.txt:67` |
| 첫 투자 | `WTI` 원유 선물, 이란 핵 이슈를 계기로 진입 | `arc_001.txt:51`, `arc_001.txt:67` |
| ep1 목표 | 회귀, 기억 과부하, 쓰러짐, 한태준 등장 클리프행어 | `blueprint_0001.txt` |
| ep2 목표 | 형과 대면, 독립 결심, 아버지에게 투자 선언, 수정 문진 위협 | `blueprint_0002.txt` |
| ep3 목표 | 자산 정리, `아퀼라` 매각, `20억 3천만 원`, 유진우 접촉, 질문 훅 | arc, `blueprint_0003.txt` |
| ep4 목표 | 유진우와 손잡기, 소형 여의도 사무실, `19억 5천만 원`, WTI 첫 베팅 | arc, `blueprint_0004.txt` |

---

## 3. Pass 2: 화별 수동 판독표

### 3.1 ep1

| 항목 | 설계 근거 | 실제 원고 근거 | 분류 | 판정 |
|---|---|---|---|---|
| 클리프행어 유지 | `blueprint_0001.txt:7`은 기억 과부하 후 쓰러지고 한태준이 `"꼴사납게 뭐 하는 짓이냐"`라고 끝난다 | `ep_0001.txt:114`가 동일 대사로 종료 | 설계 준수 | 정상 |
| 회귀/정보 폭풍 | blueprint의 `2006년 회귀 + 경제 정보 해일` 구성이 그대로 살아 있다 | 초반 절망 -> 회귀 -> 정보 폭풍 -> 코피/붕괴가 일관되게 전개 | 설계 준수 | 정상 |
| 원룸/감각 묘사 강화 | 설계엔 있지만 축약된 절망 묘사를 원고가 크게 확장한다 | 곰팡내, 냉기, 원룸 묘사 등 감각 디테일이 증가 | allowed enrichment | 허용 가능 |
| hard contradiction | 없음 | 없음 | hard contradiction | 없음 |

수동 판정:

- ep1 최종본은 blueprint의 핵심 scene과 ending hook을 정확히 구현했다.
- 이 화는 `결과물`만 놓고 보면 Director가 잡아내야 할 핵심 구조를 결국 지켰다.
- 다만 `과정`은 좋지 않았다. DB 기준 Stage 4 ep1은 `9회 시도 / 8회 REJECT / 1회 PASS`였고, 실제 핵심 구조 문제인 ending hook 수정은 8차에서야 정면으로 지적됐다.

### 3.2 ep2

| 항목 | 설계 근거 | 실제 원고 근거 | 분류 | 판정 |
|---|---|---|---|---|
| ep1 종료 상태 연속성 | ep1은 한태준 대사로 끝남 | ep2는 그 대사를 받은 직후 의식 회복 장면으로 시작 | 설계 준수 | 정상 |
| 독립 선언 | `blueprint_0002.txt:7`은 아버지에게 투자사 설립과 그룹 완전 독립을 선언한다 | `ep_0002.txt` 후반부가 동일 구조를 유지 | 설계 준수 | 정상 |
| 수정 문진 위협 | `blueprint_0002.txt:44`와 본문은 한정호가 수정 문진을 들고 `"그 말, 감당할 수 있겠느냐"`라고 끝난다 | `ep_0002.txt:77-81`이 동일하게 구현 | 설계 준수 | 정상 |
| 형/가족 무관심 축 | blueprint의 가족 무관심 구도 유지 | draft가 다이닝룸 정적과 가족 구조를 더 촘촘히 묘사 | allowed enrichment | 허용 가능 |
| hard contradiction | 없음 | 없음 | hard contradiction | 없음 |

수동 판정:

- ep2는 ep1에서 ep2로 넘어가는 연결이 자연스럽고, 아버지 confrontation이 blueprint와 거의 동일하다.
- 이 화에서는 Director가 막아야 할 모순이 사실상 남아 있지 않다.

### 3.3 ep3

| 항목 | 설계 근거 | 실제 원고 근거 | 분류 | 판정 |
|---|---|---|---|---|
| ep2 종료 상태 연속성 | ep2는 수정 문진 위협 상태로 끝난다 | `ep_0003.txt`는 그 위협 직후 허락으로 넘어간다 | 설계 준수 | 정상 |
| 자산 정리 / 법인 접촉 | 자산 정리 -> `20억 3천만 원` -> 유진우 접촉 -> 질문 훅 | `ep_0003.txt:51`, `ep_0003.txt:106`이 이를 유지 | 설계 준수 | 정상 |
| 애마 이름 | arc는 `아퀼라`다 (`arc_001.txt:51`) | blueprint는 `이클립스`를 사용 (`blueprint_0003.txt:7`, `:28`) | soft drift | Stage 3 defect |
| 애마 이름 복구 | blueprint는 `이클립스`지만 | final draft는 `아퀼라`를 일관되게 사용 (`ep_0003.txt:44-51`) | 설계 복구 | Stage 4에서 복구 |
| 질문 훅 | blueprint는 유진우가 `"어디서 배우셨습니까?"`를 던진다 | `ep_0003.txt:106`이 동일 질문으로 종료 | 설계 준수 | 정상 |
| hard contradiction | 최종 draft 기준 없음 | 없음 | hard contradiction | 없음 |

수동 판정:

- ep3 최종 원고는 좋다. ep2와의 연결도 매끄럽고, 자산 정리-유진우 첫 대면-정체 의심까지 설계 흐름이 안정적이다.
- 실제 문제는 최종 원고가 아니라 `Stage 3 blueprint`다. 상위 arc가 `아퀼라`를 쓰는데 blueprint가 `이클립스`로 drift했다.
- 즉 `최종 결과물은 정상`, `중간 설계 산출물은 비정상`이다.

### 3.4 ep4

| 항목 | 설계 근거 | 실제 원고 근거 | 분류 | 판정 |
|---|---|---|---|---|
| ep3 종료 상태 연속성 | ep3는 유진우의 질문으로 끝난다 | ep4는 그 질문을 정면으로 받는 장면으로 시작 | 설계 준수 | 정상 |
| WTI 첫 베팅 / 조력자 축 | `blueprint_0004.txt:7`은 유진우와 손잡고 여의도 사무실에서 WTI 진입으로 간다 | `ep_0004.txt:97`, `:132`가 이를 구현 | 설계 준수 | 정상 |
| 시간 경과 | arc는 `약 2주 후` 여의도 사무실 진입을 상정 (`arc_001.txt:67`) | blueprint는 `다음 날 오후`로 압축 (`blueprint_0004.txt:7`), final draft는 `일주일 후`로 완화 (`ep_0004.txt:37`) | soft drift | 일부만 복구 |
| 애마 이름 | blueprint는 `이클립스` (`blueprint_0004.txt:7`, `:37`) | final draft는 `아퀼라`로 복구 (`ep_0004.txt:89`) | 설계 복구 | Stage 4에서 복구 |
| 독립 의지 시각화 | blueprint보다 확장 | `비즈니스호텔`, `시장 옷`, `본가 이탈`을 추가 (`ep_0004.txt:37`) | allowed enrichment | 허용 가능 |
| 대화 존재 여부 | 원고에는 다수의 대화가 있다 | 그러나 로그는 최종본에 `대화 0%`를 기록 (`session_20260311_112831.log:4724`) | warning false positive | telemetry noise |
| hard contradiction | 최종 draft 기준 없음 | 없음 | hard contradiction | 없음 |

수동 판정:

- ep4는 최종 원고만 놓고 보면 강하다. 유진우와의 관계, 작은 사무실 선택, 19억 5천만 원의 무게, WTI 첫 베팅이 모두 살아 있다.
- 다만 elapsed time은 끝까지 완전히 정리되지 않았다. `약 2주 후 -> 다음 날 오후 -> 일주일 후`로 흔들린다.
- 즉 이 화의 실제 defect는 `연속성 전체 붕괴`가 아니라 `시간축 soft drift 잔존`이다.

---

## 4. Pass 3: Director 역할 판정

### 4.1 축별 판정

| 축 | 판정 | 근거 |
|---|---|---|
| `Stage 2 -> 3` | `부분적` | ep3/ep4 blueprint에서 `아퀼라 -> 이클립스`, `약 2주 후 -> 다음 날 오후` drift 발생 |
| `Stage 3 -> 4` | `부분적` | final draft가 horse name은 복구했지만, time drift는 `일주일 후`로만 부분 복구 |
| `Episode-to-Episode` | `잘 막음` | ep1->ep2, ep2->ep3, ep3->ep4 연결은 실제 텍스트상 안정적 |
| `Director Review Quality` | `불충분` | ep1 `9회` 시도, ep3 `REJECT 44` false-positive성 기록, ep4 `대화 0%` telemetry 등 noise 비중이 높음 |

### 4.2 Director가 실제로 막아낸 모순

- ep1에서 최종본의 ending hook은 blueprint에 정확히 복귀했다.
- ep3과 ep4 최종본은 blueprint의 구조를 유지하면서도 `이클립스` drift를 `아퀼라`로 바로잡았다.
- 1화부터 4화까지 최종 원고 사이에는 이번 범위에서 확인되는 `hard contradiction`이 없다.

### 4.3 Director가 놓쳤거나, 오탐으로 흔들린 항목

- `Stage 3 blueprint` 단계의 고유명사 drift를 사전에 막지 못했다.
- `약 2주 후`라는 arc 시간축이 최종본까지 완전 복원되지 않았다.
- ep1에서는 실제 구조 이슈보다 길이/게이트 noise가 오랫동안 우선했다.
- ep3에서는 `InfoParadox('유진우의 의구심')`를 근거로 `REJECT 44`가 발생했는데, reject_reason과 selection_reason/open review가 서로 다른 방향을 가리켰다.
- ep4 최종본은 대사가 여러 번 등장하는데도 로그엔 `대화 0%`가 남았다.

### 4.4 최종 등급

`부분적`

- 결과물 품질만 보면 `잘 막음`에 가깝다.
- 그러나 review 시스템의 신호 품질과 중간 산출물 안정성까지 포함하면 `부분적`이 더 정확하다.

---

## 5. 실제 문제 목록

| ID | 분류 | 증거 | 현재 해석 | 영향 |
|---|---|---|---|---|
| MR-1 | Stage 3 continuity defect | `arc_001.txt:51`은 `아퀼라`, `blueprint_0003.txt:7/28`, `blueprint_0004.txt:7/37`은 `이클립스` | blueprint 단계에서 proper noun continuity가 깨졌다 | 이후 review가 noise에 흔들리면 최종 원고까지 오염될 수 있다 |
| MR-2 | residual soft drift | arc는 `약 2주 후` (`arc_001.txt:67`), blueprint는 `다음 날 오후` (`blueprint_0004.txt:7`), final draft는 `일주일 후` (`ep_0004.txt:37`) | 시간축 drift가 일부만 복구되고 최종본에도 잔존 | 연재 누적 시 chronology 관리가 흔들릴 수 있다 |
| MR-3 | review prioritization defect | DB 기준 ep1 Stage 4는 `9회 시도`, 로그상 실질적인 구조 수정 지시는 8차에서야 등장 | 실제 모순 방지보다 분량/키워드 gate가 먼저 시스템을 장악한다 | 비용과 시간이 폭증하고, 진짜 구조 이슈 탐지가 늦어진다 |
| MR-4 | false-positive / record incoherence | ep3 attempt 1은 `REJECT 44`인데 selection_reason은 continuity를 칭찬하고, reject_reason은 `InfoParadox` false positive를 싣는다 | final verdict, 자유 리뷰, reject_reason 저장층이 서로 어긋난다 | review 결과를 인간이 신뢰하기 어렵다 |
| MR-5 | telemetry noise | `session_20260311_112831.log:4724`는 ep4 최종본에 `대화 0%`를 기록하지만, `ep_0004.txt`에는 다수의 대화가 존재한다 | 스마트따옴표/검출 규칙 문제로 dialogue telemetry가 무너진다 | dialogue ratio 경고를 운영 지표로 쓰기 어렵다 |

---

## 6. 즉시 개선 가능성

### 6.1 감지 규칙 개선

- arc에서 확정된 고유명사와 핵심 수치(`아퀼라`, `20억 3천만 원`, `19억 5천만 원`)를 blueprint 단계에서 강제 대조한다.
- elapsed time 표현(`즉시`, `다음 날`, `며칠 후`, `약 2주 후`)을 scene transition ledger로 체크한다.
- 스마트따옴표를 dialogue ratio와 quote-based checker가 모두 인식하도록 통일한다.
- ending hook은 keyword 2개 매칭보다 `scene intent` 기반의 semantic check 비중을 올린다.

### 6.2 Director prompt 개선

- 문장력이 좋아도 `상위 설계 팩트 drift`면 우선 감점하도록 우선순위를 명시한다.
- 이전 화 published text와 blueprint가 충돌하면 `published text`를 우선 정본으로 취급하도록 못 박는다.
- `모순 없음`과 `REJECT`가 동시에 저장되지 않도록 판정 문구와 scoring 설명을 분리한다.

### 6.3 저장/표시 개선

- `pre-firewall score`, `post-firewall score`, `final verdict`, `human-readable reason`을 분리 저장한다.
- `reject_reason`과 `selection_reason`이 서로 반대 의미를 갖는 상태를 금지한다.
- dialogue ratio / scene coverage / InfoParadox는 `advisory`와 `blocking`을 분리 표기한다.

### 6.4 운영 절차 개선

- 새 프로젝트 최초 1-arc 완료 시, 이번 문서와 같은 `manual reading gate`를 release gate로 한 번 거친다.
- 이 gate를 통과하기 전에는 quality telemetry 숫자를 절대 진실로 취급하지 않는다.

---

## 7. SSOT 반영 요약

- 이번 수동 감리는 기존 SSOT의 큰 방향을 뒤집지 않는다.
- 대신 아래 네 가지를 더 정확하게 만든다.
  - 최종 원고 기준 `hard contradiction`은 없다는 점
  - Director 전체 등급은 `잘 막음`이 아니라 `부분적`이라는 점
  - 실제 text-level defect는 `proper noun drift`와 `elapsed time soft drift`라는 점
  - `InfoParadox`, `dialogue ratio`, 일부 `ending_hook` 경고는 수동 재판정이 필요하다는 점

수동 감리 결과가 강화하는 기존 SSOT 항목:

- `CF-4`: ep1 retry/cost 폭증
- `WN-2`: dialogue ratio 과민 / 오탐
- `WN-3`: `InfoParadox('유진우의 의구심')` 과잉 해석

수동 감리로 새로 드러난 text-level 문제:

- Stage 3 blueprint proper noun drift
- Stage 2->4 elapsed time soft drift

이 둘은 현재 문서 기준으로 `실제 문제`이지만, 이번 1-arc 샘플 한정이므로 SSOT 본문에서는 우선 `manual reading layer`에 둔다.

### 7.1 외부 Director 감리 대조

- `docs/2026-03-11/director-quality-audit-00_test_00.md`와 대조한 결과, 아래 세 항목은 내 수동 감리와 합치한다.
  - ep1 `88점` 후보를 ending hook drift 때문에 REJECT한 점은 `좋은 글`보다 `설계 충실도`를 우선한 사례다.
  - ep3에서 blueprint의 `이클립스` 오류보다 기발행 원고의 `아퀼라`를 우선한 점은 continuity SSOT 원칙과 맞는다.
  - ep4의 `호텔`, `시장 옷`, `본가 이탈` 디테일은 설계 훼손이 아니라 `allowed enrichment`로 보는 편이 타당하다.
- 다만 외부 감리의 `Director 종합 등급 A-`는 `결과물 품질 중심 판정`으로 읽어야 한다. 현재 문서의 `부분적` 평가는 `중간 산출물 drift`, `ep1 9회 시도`, `ep3 REJECT 44 표기 혼선`, `ep4 대화 0% telemetry`까지 포함한 `시스템/과정 평가`라서 둘은 충돌하지 않는다.
- 외부 감리에서 그대로 SSOT 사실로 올리지 않은 항목도 있다.
  - `상업적 수준` 평가는 주관적 표현이라 SSOT 확정 문구로 쓰지 않았다.
  - `스스로` 항목은 실제 오탈자 근거로 성립하지 않아 반영하지 않았다.

---

## 8. 참고 근거

- `bible/01_bi_투자물_골든_sample.json`
- `treatments/01_tr_투자물_골든_sample.json`
- `projects/00_test_00/stage0_output/style_guide.json`
- `projects/00_test_00/plans/arcs/arc_001.txt`
- `projects/00_test_00/plans/blueprints/blueprint_0001.txt`
- `projects/00_test_00/plans/blueprints/blueprint_0002.txt`
- `projects/00_test_00/plans/blueprints/blueprint_0003.txt`
- `projects/00_test_00/plans/blueprints/blueprint_0004.txt`
- `projects/00_test_00/drafts/ep_0001.txt`
- `projects/00_test_00/drafts/ep_0002.txt`
- `projects/00_test_00/drafts/ep_0003.txt`
- `projects/00_test_00/drafts/ep_0004.txt`
- `projects/00_test_00/logs/session_20260311_112831.log`
- `projects/00_test_00/logs/episode_production.jsonl`
- `projects/00_test_00/project_data.db`
- `docs/2026-03-11/director-quality-audit-00_test_00.md`
