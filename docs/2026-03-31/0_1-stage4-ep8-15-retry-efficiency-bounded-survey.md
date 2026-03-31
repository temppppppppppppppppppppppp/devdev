# 0_1 Stage4 EP8-15 Retry Efficiency Bounded Survey

- Date: 2026-03-31
- Scope: work `0_1`, Stage 4 retry efficiency from EP8 through EP15
- Baselines:
  - `docs/2026-03-31/0_1-stage4-ep1-15-db-log-bounded-audit.md`
  - `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-survey.md`
  - `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-bounded-survey.md`
- Method: DB + JSONL + code + cost telemetry triangulation, then 3-pass audit
- Confidence: 96%

## Answer First

효율 저하는 실제로 존재한다. 다만 주원인은 `모델 티어 부족`이 아니라 `downstream gate churn + 재선정 중복 + advisory-only early-stop`이다.

이번 survey에서 가장 중요한 결론은 다섯 가지다.

1. Stage 4 평균 시도 수는 EP1-7의 `1.29`에서 EP8-15의 `5.38`로 급증했다.
2. EP8-15의 reject `35건` 중 `31건(88.6%)`은 Director가 이미 `PASS` 또는 `PASS_WITH_FIX`로 본 뒤 downstream에서 깨진 케이스다.
3. candidate / hash 재순환이 크다. EP8-15 Stage 4 rows `43건` 중 repeated-hash 관여 rows는 `14건(32.6%)`, repeated-candidate 관여 rows는 `21건(48.8%)`이다.
4. `QR-7`은 stop signal이 아니라 feedback advisory일 뿐이라서, 발화 후에도 실제 시도가 계속된다.
5. CW/Director 모델은 EP8-15 전 구간에서 모두 `gemini-3.1-pro-preview`로 고정돼 있어, 이 구간 효율 저하를 모델 down-tier 문제로 보긴 어렵다.

## How This Augments The Prior Conclusion

이 addendum은 기존 `residual gate observability` 결론을 강화한다.

- 기존 결론: late-stage inefficiency는 CW 무능보다는 gate / observability seam이 더 크다.
- 이번 결론: 그 seam은 실제로 비용과 재시도 횟수까지 직접 밀어 올리고 있다.

즉:

- `왜 자주 떨어졌는가`는 이전 문서가 설명했고
- `왜 그렇게 비효율적으로 오래 돌았는가`는 이번 문서가 설명한다

## Hard Conclusions

### 1. retry volume은 운영적으로 비정상적으로 높다

- EP1-7 Stage 4 total rows는 `9`, mean은 `1.29`다.
- EP8-15 Stage 4 total rows는 `43`, mean은 `5.38`이다.
- chronological row depth 기준 final PASS까지 걸린 row depth는
  - EP8 `9`
  - EP9 `7`
  - EP10 `5`
  - EP11 `5`
  - EP12 `2`
  - EP13 `6`
  - EP14 `4`
  - EP15 `5`
  이다.

판정:

- 설계상 retry는 정상이어도, 현재 관측된 EP8-15 retry depth는 운영 건강 상태로는 비정상적으로 높다.

### 2. 재시도 대부분은 low-quality first-pass보다 downstream churn에서 소모됐다

- EP8-15 reject `35건` 중 `31건`은 Director verdict가 `PASS` 또는 `PASS_WITH_FIX`였는데 final row verdict가 `REJECT`로 닫혔다.
- share는 `88.6%`다.
- EP8-15 각 에피소드의 첫 Stage 4 row를 보면 `8개 중 7개`가 이미 `Director non-reject -> final reject` 구조였다.
- 대표 first-row gate basis는
  - `pass_with_fix_contract_missing_patch_targets`
  - `strong_advisory_escalation_non_local_fix`
  - `post_select_conflict`
  였다.

판정:

- 효율 문제를 `CW가 처음부터 못 써서`로 보는 건 틀린 진단이다.
- 이 구간의 retry budget은 대부분 downstream gate churn이 태웠다.

### 3. candidate reselection과 same-hash reuse가 실질 탐색 폭을 줄였다

- EP8-15 repeated-hash 관여 rows는 `14/43 = 32.6%`다.
- EP8-15 repeated-candidate 관여 rows는 `21/43 = 48.8%`다.
- 특히
  - EP8 repeated-candidate share `88.9%`
  - EP9 repeated-hash share `57.1%`
  - EP11 repeated-candidate share `60.0%`
  가 높다.
- final PASS가 직전 REJECT와 동일 hash였던 episode도 `4/8`이다.
  - EP8
  - EP11
  - EP13
  - EP14

판정:

- 일부 retry는 새 탐색이 아니라 기존 candidate/hashing의 재판정에 가까웠다.
- same-hash reselection 억제는 효율 측면에서 실제 가치가 있다.

### 4. early-stop 신호는 존재하지만 binding stop으로 작동하지 않는다

- `stage4_outcome_runtime.py:672-699`의 `QR-7`는 plateau advisory를 `director_feedback` 앞에 붙이고 UI log를 남길 뿐, loop를 중단하지 않는다.
- 실제 JSONL에서도 `QR-7`은 EP13, EP15에서만 1회씩 발생했다.
  - `projects/0_1/logs/session/ui_events.jsonl:4765`
  - `projects/0_1/logs/session/ui_events.jsonl:5277`
- 그리고 두 경우 모두 `QR-7` 이후 Stage 4 attempt rows가 `2건`씩 더 이어졌다.
- `stage4_retry_runtime.py:858-928`는 `TF-PATCH-GATE`와 `TF-4`를 통해 patch를 rewrite로 밀어낼 수는 있지만, hard stop은 아니다.

판정:

- 현재 early-stop은 `operator hint`와 `lane reroute` 수준이지, retry compression 장치로는 약하다.

### 5. 모델 티어/프로바이더는 이 구간 효율 저하의 1차 원인이 아니다

- EP8-15에서 `chief_writer`는 전부 `gemini-3.1-pro-preview`였다.
- EP8-15에서 `director`도 전부 `gemini-3.1-pro-preview`였다.
- aggregate call count는
  - chief_writer `252`
  - director `367`
  다.
- aggregate cost는
  - chief_writer `$11.90`
  - director `$5.07`
  다.
- EP8-15 총 LLM cost는 `$20.82`였다.

판정:

- 적어도 EP8-15 retry explosion을 `모델이 갑자기 약해졌다`로 설명할 근거는 없다.
- 우선순위는 tier uplift보다 gate churn reduction이다.

## Medium-Confidence Conclusions

- `TF-PATCH-GATE`가 rewrite fallback을 유도하는 방식은 fail-close 측면에선 맞지만, 현재는 `patch-ready contract`가 비지 않는 구간이 많지 않아 rewrite budget을 넓게 태우는 부작용이 있다.
- EP13, EP15는 `QR-7`이 실제로 “동일 루프 반복”을 꽤 정확하게 감지했다. 다만 감지 후에도 stop이 없어 budget compression 효과는 거의 없었다.
- EP8-9의 `TF-4` full rewrite 전환은 late window EP10-15보다 earlier pathology를 보여준다. 이번 조사 범위에선 late episodes의 핵심은 `TF-4`보다 `TF-PATCH-GATE + downstream churn + reselection`이었다.

## Open Questions

1. same-hash / same-candidate reselection을 hard-block하면 convergence가 빨라질까, 아니면 candidate diversity만 악화될까?
2. `QR-7`을 advisory에서 stop-or-escalate gate로 바꾸면 quality regression 없이 평균 attempt rows를 얼마나 줄일 수 있을까?
3. `post_select_conflict`는 얼마나 줄일 수 있나? patch-ready fix_pack 개선만으로 줄어드는지, candidate selection contract 자체를 바꿔야 하는지 추가 확인이 필요하다.
4. EP8-15 비용 중 어느 정도가 truly unavoidable generation cost이고, 어느 정도가 avoidable re-review cost인지 finer attribution이 필요하다.

## Improvement Priorities

1. `Director non-reject -> final reject` churn 축소
2. same-hash / repeated-candidate reselection 억제
3. `QR-7`을 binding stop-or-escalate 정책으로 승격 검토
4. retry-lane `attempt_key` 복구로 operator diagnosis latency 단축
5. 모델 tier 변경보다 gate / selection / retry policy부터 수정

## Query Examples

```sql
-- 1) EP8-15 retry volume
select ep_num, count(*) as attempt_rows
from stage_attempts
where stage = 4 and ep_num between 8 and 15
group by ep_num
order by ep_num;
```

```sql
-- 2) reject rows 중 Director non-reject 비율
select ep_num, verdict, advisory_flags
from stage_attempts
where stage = 4 and ep_num between 8 and 15
order by ep_num, ts, id;
```

```sql
-- 3) same-hash reselection
select ep_num, content_hash, count(*) as ct
from stage_attempts
where stage = 4 and ep_num between 8 and 15
group by ep_num, content_hash
having count(*) > 1;
```

```python
# 4) QR-7 이후 실제 attempt rows가 얼마나 더 있었는지
import json, pathlib, sqlite3
conn = sqlite3.connect("projects/0_1/project_data.db")
for line in pathlib.Path("projects/0_1/logs/session/ui_events.jsonl").read_text(encoding="utf-8").splitlines():
    obj = json.loads(line)
    if obj.get("component") == "retry_lane" and "[QR-7]" in str(obj.get("message") or ""):
        later = conn.execute(
            "select count(*) from stage_attempts where stage=4 and ep_num=? and ts > ?",
            (obj["ep_num"], obj["ts"]),
        ).fetchone()[0]
        print(obj["ep_num"], later)
```

## Final Assessment

- retry efficiency는 현재 분명히 문제다.
- 하지만 `모델을 더 좋은 걸 쓰면 해결`이 아니라
  - downstream gate churn 줄이기
  - duplicate reselection 막기
  - early-stop을 advisory에서 policy로 올리기
  이 세 개가 먼저다.

기존 deep dive의 결론을 운영 관점으로 번역하면 한 줄로 이렇게 된다.

`품질 문제처럼 보이던 많은 루프가 사실은 gate/selection/policy inefficiency였고, 그 inefficiency가 실제 retry budget과 비용을 밀어 올렸다.`

## Audit Record

- Pass 1: DB retry volume / gate churn / reselection / llm cost 수집
- Pass 2: chronological row order 기준으로 attempt depth 재계산
- Pass 3: code anchor와 JSONL line anchor 재검토, UTF-8 read-back 확인
- Final save threshold: confidence 96%, save allowed
