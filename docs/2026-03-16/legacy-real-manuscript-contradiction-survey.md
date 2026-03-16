<!-- [참고자료] -->
<\!-- [참고자료] -->
Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/legacy-real-manuscript-contradiction-survey.md`
Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
Baseline Dirty Summary: `dirty: desktop icon/version files, stage4/continuity runtime modules and tests, project runtime artifacts/db, opus memo edits, and untracked 2026-03-16 follow-up docs`
Scope: `legacy real-manuscript contradiction survey`, `artifact truth + metadata truth + narrative truth`, `projects/0 + projects/000 + projects/00_20260314 + projects/00_260315`
Evidence Artifact: `docs/2026-03-16/legacy-real-manuscript-contradiction-survey-evidence.txt`
Confidence: `97%`

# Legacy Real Manuscript Contradiction Survey

## 1. Scope And Method

이번 조사는 `DB 행`이나 `로그 요약`만 보는 방식으로 끝내지 않았다. 아래 네 프로젝트의 Stage 4 최종 authority 원고를 전편 직접 읽고, 각 화를 `DB manuscripts`, `director_selections`, `stage_attempts`, `episode_bibles`와 대조했다.

- `projects/0`
- `projects/000`
- `projects/00_20260314`
- `projects/00_260315`

직접 읽은 최종 authority는 총 `21편`, 약 `100,714자`, `2,085줄`이다. 조사 기준은 세 층이다.

1. `artifact truth`
   - final/patched txt 존재
   - UTF-8 decode 성공
   - DB `manuscripts.content`와 최종 authority 일치 여부
2. `metadata truth`
   - `director_selections`가 무엇을 최종 authority로 가리키는지
   - `stage_attempts`가 무엇을 최종 authority로 기록하는지
   - pre-fix / patched authority drift 여부
3. `narrative truth`
   - 실제 본문 기준 화간 설정/시간/장소/자산/관계/행동 연속성

## 2. Corpus Result

| Project | Episodes Read | Final/Patched Authority | DB Manuscript Match | Surviving Hard Contradiction |
| --- | ---: | --- | --- | --- |
| `0` | 2 | `final_manuscript` 2 | `2/2` | `0` |
| `000` | 6 | `final_manuscript` 5 + `patched_after_fix` 1 | `6/6` | `0` |
| `00_20260314` | 2 | `final_manuscript` 1 + `patched_after_fix` 1 | `2/2` | `0` |
| `00_260315` | 11 | `final_manuscript` 8 + `patched_after_fix` 3 | `11/11` | `0` |

핵심 결론은 단순하다.

- `실물 최종 authority 원고` 기준으로는, 이번 조사 범위 안에서 `surviving hard contradiction`을 찾지 못했다.
- 대신 `출간 전 후보` 단계에서는 실제 연속성 충돌이 여러 번 발생했고, 그중 상당수는 patch / reselect로 해결되었다.
- 그리고 `projects/00_260315`에서는 `director_selections`가 여전히 pre-fix 원고를 가리키는 `stale metadata authority`가 `2건` 남아 있었다.

즉, 이번 조사에서 살아남은 문제의 중심은 `최종 원고 본문`보다 `authority sink 불일치`에 더 가깝다.

## 3. Project-Level Findings

### 3.1 `projects/0`

실물 최종본 `2편`을 끝까지 읽은 결과, 고신뢰 모순은 보이지 않았다.

- `ep1`은 회귀 인지 -> 가족 냉대 -> 투자사 선언 -> 이준영 연결 -> 형의 위협으로 끝난다.
- `ep2`는 그 직후 박성호 접촉과 아버지의 “자격을 증명하라” 과제로 이어지며, 자산/목표/관계 변화가 자연스럽다.

판정:

- `hard contradiction`: 없음
- `soft inconsistency`: 없음
- `ambiguity`: 경미한 서사 압축은 있으나 판정 가능한 충돌은 없음

### 3.2 `projects/000`

실물 최종본 `6편`을 직접 읽은 결과, published authority에는 `hard contradiction`이 남아 있지 않았다. 다만 후보 단계에서 발생한 실제 충돌이 patch / reselect로 해소된 흔적이 선명하다.

#### `resolved-by-patch / reselect` 1: dual-laptop continuity (`ep2`)

`ep1`에서 이준영이 제공한 `최신형 노트북`이 등장한 뒤, `ep2` blueprint에는 `2006년형 구형 노트북`이 핵심 장치로 다시 들어온다. 최종본은 이 충돌을 회피하지 않고 본문 안에서 해결한다.

- final authority는 `조수석의 최신형 노트북`과 `셀프 스토리지에서 꺼낸 2006년형 구형 노트북`을 명확히 분리한다.
- `director_selections`도 이 지점을 잠재 모순으로 인지하고, final candidate가 `셀프 스토리지` 장치로 해결했다고 기록한다.

판정: `resolved-by-patch`, `engineering-fixable carryover issue`

#### `resolved-by-patch / reselect` 2: Park Seong-ho loyalty continuity (`ep4`)

`ep3` 말미의 박성호는 거의 절대적 충성 상태다. 그런데 `ep4` 중간 후보에서는 그가 갑자기 계획 자체를 의심하는 방향으로 흔들렸고, 이 때문에 `round 1 REJECT`가 발생했다.

- rejected rationale는 `3화 엔딩에서 절대적 충성을 보인 박성호`가 `4화에서 갑자기 계획에 대한 의구심`을 보인다고 적시한다.
- 최종 authority는 박성호의 긴장감은 유지하되, 의심 대신 `대표의 수에 대한 경외감과 마지막 확인`으로 톤을 바꿔 연속성을 복원한다.

판정: `resolved-by-patch`, `hybrid LLM + continuity-gate issue`

#### `resolved-by-patch / reselect` 3: all-in `20억` continuity (`ep5`)

이 구간은 후보 단계에서 가장 큰 충돌 압력을 받았다.

- `ep4` published ending은 `20억 전액 투자 체결`이다.
- 반면 `ep5` blueprint 전제에는 `5억 선투자 후 15억 추가 투자`가 섞여 있었다.
- 실제 `director_selections`는 `round 0`, `round 2`에서 이 문제를 `Contradiction Firewall: CRITICAL`로 반복 기록한다.

최종 authority는 이 충돌을 다음 방식으로 정리한다.

- 이미 `20억 전액 투자`가 들어간 상태를 유지한다.
- `WTI 하락 2% -> 3배 레버리지 -> 평가손실 -6%` 계산을 그대로 따라간다.
- 이후 갈등은 `추가 매수`가 아니라 `기존 포지션 유지 여부`와 `리스크 관리팀 압박`으로 재구성한다.

판정: `resolved-by-patch`, `engineering-fixable state/arithmetic carryover issue`

### 3.3 `projects/00_20260314`

실물 최종 authority `2편`을 직접 읽은 결과, surviving hard contradiction은 보이지 않았다.

- `ep1`은 회귀 인지 -> 형/가족과의 첫 대치 -> 독립 선언 흐름이 안정적이다.
- `ep2`는 patched final authority 기준으로 그 직후의 가족 압박, 안전금고/열쇠/유산 계열 장치, 박성호 접촉으로 이어진다.

`ep2`는 patched authority이지만 `director_selections`와 `stage_attempts`의 content hash가 같고, DB manuscript도 patched final과 일치한다. 즉 이 프로젝트는 patch가 있어도 `authority sink drift`는 없다.

판정:

- `hard contradiction`: 없음
- `soft inconsistency`: 없음
- `metadata drift`: 없음

### 3.4 `projects/00_260315`

이 프로젝트는 `11편`으로 가장 길고, 실제 후보/patch 흔적도 가장 많이 남아 있다. 실물 final/patched authority를 직접 읽은 결과, `surviving hard contradiction`은 보이지 않았다. 대신 `narrative continuity fix`와 `stale metadata authority`가 동시에 남아 있다.

#### `resolved-by-patch` 1: computer relocation / reassembly continuity (`ep4`)

`ep3` 말미에는 아버지가 보내준 최고 사양 컴퓨터가 이미 `자택 방`에 설치된다. 그런데 `ep4` pre-fix 원고는 여의도 사무실에서 그 컴퓨터를 마치 처음 조립하는 것처럼 읽힐 여지가 있었고, `director_selections.verdict_reason`도 정확히 그 지점을 지적한다.

patched final authority는 이 점을 명확히 보정한다.

- `성북동 자택에서 옮겨온 거대한 상자`
- `전날 설치되었던 ... 컴퓨터 부품`
- `재설치를 위해 대기하던 전문가`
- `자신의 무기는 자신의 손으로 만들어야 했다. 그것은 단순한 재조립이 아니었다`

즉 published final은 `자택 설치 -> 분해/이송 -> 사무실 재조립`으로 읽히도록 수정되어 narrative contradiction을 지웠다.

판정: `resolved-by-patch`, `engineering-fixable equipment carryover issue`

#### `surviving soft inconsistency` 1: stale metadata authority (`ep4`)

하지만 metadata truth는 깔끔하게 닫히지 않았다.

- `director_selections`는 여전히 `selected_before_fix__C.txt`와 pre-fix hash를 최종 authority처럼 기록한다.
- 반면 `stage_attempts`와 DB `manuscripts`, 실제 published artifact는 `patched_after_fix__A_InPlace.txt`와 patched hash를 authority로 쓴다.

즉, 사람이 `director_selections`만 읽으면 아직 수정 전 원고를 정본처럼 오인할 수 있다. 실물 원고는 맞는데, `authority index`가 stale하다는 뜻이다.

판정: `soft inconsistency`, `metadata authority drift`, `engineering-fixable`

#### `surviving soft inconsistency` 2: stale metadata authority after directive patch (`ep5`)

`ep5`의 final text 자체는 화간 모순을 만들지 않는다. patch도 실제로는 서사 충돌이 아니라 금지 표현 제거에 가깝다.

- `director_selections.verdict_reason`: 금지 표현 `강철` 사용
- pre-fix text: `서늘한 강철 심이 박혀 있었다`
- patched final text: `흔들림 없는 단호함이 서려 있었다`

그런데 여기서도 metadata sink는 동일하게 어긋난다.

- `director_selections`는 `selected_before_fix__A.txt`를 가리킨다.
- `stage_attempts`와 DB manuscript는 `patched_after_fix__A_InPlace.txt`를 최종 authority로 쓴다.

이건 narrative contradiction은 아니지만, `pre-fix authority`가 상위 인덱스에 남아 있는 구조적 문제다.

판정: `soft inconsistency`, `metadata authority drift`, `engineering-fixable`

#### `resolved-before-publication` 1: Park Seong-ho title drift (`ep11`)

`ep11` 후보 평가에서는 `박성호의 직책을 팀장 -> 차장으로 잘못 표기한 후보`가 명시적으로 탈락했다. 최종 authority는 이 오류를 포함하지 않는다.

판정: `resolved-before-publication`, `identity/role carryover issue`

## 4. Finding Ledger

| ID | Severity | Project / Episode | Class | Summary | LLM Limit vs Fixability |
| --- | --- | --- | --- | --- | --- |
| `LM-F1` | Medium | `00_260315 / ep4` | `soft inconsistency` | final manuscript는 patched authority인데 `director_selections`는 pre-fix `selected_before_fix__C.txt`를 가리킴 | `engineering-fixable` |
| `LM-F2` | Low | `00_260315 / ep5` | `soft inconsistency` | narrative는 정상이나 `director_selections`가 pre-fix `selected_before_fix__A.txt`에 머묾 | `engineering-fixable` |
| `LM-R1` | Closed | `000 / ep2` | `resolved-by-patch` | 최신형 노트북 vs 2006년형 노트북 충돌을 셀프 스토리지 장치로 해결 | `engineering-fixable carryover` |
| `LM-R2` | Closed | `000 / ep4` | `resolved-by-patch` | 박성호가 갑자기 의심 모드로 흔들리는 후보를 버리고, 경외/긴장 톤으로 재선정 | `hybrid` |
| `LM-R3` | Closed | `000 / ep5` | `resolved-by-patch` | `20억 전액 투자`와 `5억+15억` blueprint 충돌을 full-position continuity로 재구성 | `engineering-fixable state carryover` |
| `LM-R4` | Closed | `00_260315 / ep4` | `resolved-by-patch` | 이미 설치된 컴퓨터와 새 조립 컴퓨터의 관계를 `자택 설치 -> 이송 -> 재조립`으로 명확화 | `engineering-fixable carryover` |
| `LM-R5` | Closed | `00_260315 / ep11` | `resolved-before-publication` | 박성호 직책 drift 후보를 필터링하고 final authority에서는 제거 | `engineering-fixable identity carryover` |

## 5. Interpretation

이번 조사에서 중요한 점은 `실물 원고가 멀쩡하냐`와 `메타데이터 권위가 멀쩡하냐`를 분리해서 봐야 한다는 것이다.

1. `실물 final/patched authority`
   - 이번 범위에서는 고신뢰 `hard contradiction`이 남아 있지 않았다.
2. `pre-fix candidate / selection history`
   - 실제 연속성 충돌이 여러 번 발생했고, 시스템은 그것을 patch 또는 reselect로 상당 부분 흡수했다.
3. `authority metadata`
   - `00_260315 ep4-5`처럼 `director_selections`가 pre-fix를 가리키는 stale index가 남을 수 있다.

즉, 사람이 이전 프로젝트를 검토할 때 `director_selections`만 읽고 판정하면 오판할 수 있다. 이번 수동 실독 결과가 보여주는 운영 규칙은 명확하다.

- `최종 원고 진실`은 `DB manuscripts + final/patched artifact + stage_attempts`를 먼저 본다.
- `director_selections`는 후보 심사 히스토리로는 유용하지만, patched 이후에도 stale할 수 있으므로 단독 authority로 쓰면 안 된다.

## 6. Relation To Current Code Risk

이번 legacy 실독 결과는 앞선 위험평가 문서의 결론과도 맞물린다.

- `continuity drift`는 실제 후보 단계에서 여러 번 발생했다.
- 다만 current system은 patch / reselect / contradiction firewall / stage attempt persistence로 일부를 흡수한다.
- 반대로 `authority sink finalization`이 완전히 닫히지 않으면, 실물 원고는 맞아도 audit surface는 틀릴 수 있다.

따라서 현재 코드에서 재발 가능성이 큰 영역은 두 축이다.

1. `carryover continuity`
   - 자산 총액, 장비, 인물 충성도, 직책, 시간 경과
2. `final authority sink alignment`
   - patched 결과를 `director_selections`, `stage_attempts`, `manuscripts`, artifact path 전부에 일관되게 반영하는 문제

## 7. Final Conclusion

이번 범위에서 직접 읽은 `21편`의 최종 원고 기준으로는 `surviving hard contradiction`을 발견하지 못했다. 이건 “문제가 없었다”가 아니라, `후보 단계의 충돌 상당수가 실제 final authority에서 이미 수정되었다`는 뜻이다.

반대로, 실제로 남아 있는 유효한 문제는 `projects/00_260315 ep4-5`의 `stale metadata authority`다. 즉 모순의 중심은 현재 `원고 본문`보다 `patched 이후 metadata sink 정렬 실패`에 있다.

결론적으로:

- `실물 원고 조사`는 가치가 있었다.
- `director_selections 단독 신뢰`는 위험하다.
- legacy contradiction 조사에서 지금 가장 신뢰할 수 있는 authority 순서는 `DB manuscript == final/patched artifact == stage_attempts`, 그 다음이 `director_selections history`다.
