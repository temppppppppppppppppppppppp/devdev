# 실파이프라인 실행 감사: 00_20260306

> 실행일: 2026-03-06
> 프로젝트: 00_20260306 (골든루트, 투자물, 1인칭 회귀자)
> 범위: Stage 0 + Stage 2 (Arc 1~5, 총 22화 분량)
> 총 소요: ~42분
> 감사 버전: v3 (TF 6개 심층 조사 + 감리 3회 교차검증 반영)

---

## 1. 실행 요약

| Arc | 시도 | 최종 결과 | 소요 시간 | 주요 이슈 |
|-----|------|-----------|-----------|-----------|
| Arc 1 (Ep 1~4) | 1회 | PASS 100 (재심사) | ~3m18s | PASS_WITH_FIX(95) → InPlace patch로 internal_energy 제거 → 재심사 PASS 100 |
| Arc 2 (Ep 5~8) | 2회 | PASS 100 (재심사) | ~10m51s | 1차: SC REJECT(수익률 산술 모순) → 2차: Patch Mode → 재심사 PASS |
| Arc 3 (Ep 9~12) | 1회 | PASS 100 (재심사) | ~7m53s | 위치 불연속(강남→여의도) + 시작묘사 반복 → InPlace patch |
| Arc 4 (Ep 13~17) | 2회 (2차 내 ArcValidator REJECT 포함) | PASS 90 | ~14m24s (최장) | 1차 SC 만장일치 REJECT(위치+수치), 2차 SC 2/3 PASS(위치 모순 잔존) |
| Arc 5 (Ep 18~22) | 1회 | PASS 100 | ~5m11s (최단) | 이슈 없음 |

- 크래시/에러: 0건
- LLM 호출 실패: 0건
- 전체 API 응답률: 100% (1회 attempt로 전부 성공)
- Enrichment: 5블록 병렬 완료 39.9s, 인과율 용접 4건 순차 ~2m6s

---

## 2. 코드 버그

### BUG-1: "금지 아이템 획득 시도: 다음" 오탐 [P1]

**현상**: Arc 2~5의 거의 모든 후보가 "금지 아이템 획득 시도: 다음..."으로 -15점 감점 (16회+ 발생). Arc 1은 이전 Arc 소지품이 없어 "다음 아이템 획득 금지" 목록 자체가 생성되지 않으므로 **Arc 2+부터만 발동**.

**원인 경로**:
1. `preflight_checker.py:442` — `"❌ 다음 아이템 획득 금지 (이미 보유 중):"` 제목 라인 출력
2. `preflight_checker.py:451` — `"❌ 다음 수여물 재수여 금지:"` 제목 라인 출력
3. `arc_ensemble.py:623` — regex `r"❌\s*([가-힣\w]+)"` 가 `"다음"`을 금지 아이템 이름으로 추출
4. `arc_ensemble.py:627` — `item in _acq_strs or ("획득" in tactical and item in tactical)` 조건에서, `item="다음"`이 tactical 본문에 포함 + "획득" 키워드도 대부분 존재 → -15점

**영향 — pre-Director 점수 왜곡 사례**:
- Arc 2 시도 1: creative=30, conservative=30 (오탐 -15 적용) → balanced 분량 미달(2,830자 < 3,150자 최소 기준) 제외 → 2후보만 비교
- Arc 4 시도 2-2차: balanced=15 (최저점, -15 오탐 + 위치 불일치 -10 등 다중 감점 중첩)
- Arc 5: conservative=55, creative=30, balanced=25 → Director가 balanced(25점 최하위)를 최종 선택하여 대원칙 3 정상 작동 입증

**Director 보정 사례**: Arc 4 시도 1에서 pre-Director가 conservative(90)를 1위로 선정했으나, Director compare에서 balanced(30점, 3위)를 최종 선택하여 PASS(98). BUG-1 점수 왜곡에도 Director가 독립 판단으로 보정 가능.

**동일 regex가 `arc_draft_validator.py:709`에도 존재.** 단 L724 `len(forbidden) < 2` 가드 + L735 근접 패턴 매칭(`{forbidden}[를을]?\s*(?:획득|얻|받...)`)이 추가되어 실제 오탐 확률은 낮음.

**수정 권장**: (C) 제목 라인을 `"[금지 아이템 목록]"` 형태로 변경하여 ❌를 아이템 앞에만 배치

### BUG-2: internal_energy 관성 생성 [P2, 근본 원인 추가 규명]

**현상**: 투자 장르임에도 Arc 1, 3에서 LLM이 `state_constraints`에 `internal_energy` 필드 반복 생성 (Arc 2에서는 미출현)

**근본 원인 (TF-B)**: `preflight_checker.py` L87-88의 `PREFLIGHT_ANALYSIS_PROMPT`에 `"internal_energy": 85`, `"martial_level": "일류 초입"` 등 무협 전용 예시가 하드코딩되어 있음. LLM이 이 예시를 참고하여 투자물에서도 internal_energy를 포함하는 관성 발생.

**상태**: Director가 매번 PASS_WITH_FIX로 제거 지시 → 시스템 자체 교정 동작. 최종 파일(arc_001~005.txt)에서 internal_energy 완전 제거 확인됨. 불필요한 retry 비용만 발생.

**수정 방안**: (A) `preflight_checker.py` 프롬프트 예시를 장르별 분기 또는 장르 중립 예시로 교체 (B) `genre_schema_builder.py`에서 투자 장르 시 `internal_energy` 필드를 스키마에서 명시적 제외

### BUG-3: 소지품 계승 검사 무협 편향 [P2]

**현상**: `arc_ensemble.py:651`의 소지품 계승 regex가 무협 무기류 접미사에만 반응:
```python
key_items = re.findall(r"([가-힣]+(?:도|검|창|궁|패|인장))", prev_inv)
```

**확장 범위 (TF-B)**: 동일 무협 편향이 3곳에 추가 존재:
- `arc_draft_validator.py:38-42` `acquire_patterns`: `도|검|창|봉|환|단|경|비급|서|책`
- `arc_draft_validator.py:46-49` `grant_patterns`: `패|권|인장|직`
- `arc_draft_validator.py:53` `weapon_keywords`: `도, 검, 창, 봉, 궁, 부, 도끼, 낫, 곤, 편`

투자물 장르의 핵심 소지품("법인 인감", "계약서", "통장" 등)이 매칭되지 않아 소지품 계승 검사가 사실상 비활성화. 오탐이 아닌 미탐(false negative) 방향이므로 위험도는 낮으나 검증 공백.

### BUG-4: arc_draft_validator dead code [P2]

**현상**: `arc_draft_validator.py` L518, L523에서 expression의 반환값을 변수에 할당하지 않음.
- L523: `any(kw in content for kw in ["종료 상태", "종료:", "끝:", "마무리"])` — 결과 미사용
- L518: `episode_sections.get(sorted_eps[i - 1], "")` — 결과 미사용

의도된 검사(`has_end_state` 등)가 누락된 것일 수 있음.

### BUG-5: ArcValidator CRITICAL/MAJOR 세부 내용 미출력 [P2, 로깅 갭]

**현상**: Arc 4 시도 2에서 ArcValidator가 `CRITICAL:2, MAJOR:2` 감지하여 REJECT했으나, 4건의 구체적 모순 내용이 콘솔에 출력되지 않음. `UnifiedArcValidator`가 요약 카운트만 로깅하고 세부 설명은 생략.

**수정 방안**: `arc_draft_validator.py`의 REJECT 시 각 CRITICAL/MAJOR 항목의 1줄 요약을 WARNING 레벨로 출력

---

## 3. 구조적 설계 이슈 (TF-D/TF-F 발견)

### STRUCT-1: SC 투표 추가 호출 thinking_level 격하 [P1]

**위치**: `director_auditor.py` L949

SC 투표에서 1차 평가는 `thinking_level="medium"`이지만, 추가 2/3번 투표는 `thinking_level="low"`로 격하됨. 모순 감지 능력이 저하되어, 1번 투표자가 감지한 위치 모순을 2/3번 투표자가 놓칠 확률 증가.

**실제 사례**: Arc 4 시도 2 audit — 1번 투표(medium) score=80에서 위치 모순 지적, 2번(low) PASS_WITH_FIX(90), 3번(low) PASS_WITH_FIX(95) → 모순 있는 Arc 통과

### STRUCT-2: PASS_WITH_FIX가 SC 다수결에서 PASS와 동등 [P1]

**위치**: `director_auditor.py` L1015
```python
pass_votes = sum(1 for e in evaluations if e.get("decision") in ("PASS", "PASS_WITH_FIX"))
```

PASS_WITH_FIX는 "모순이 있지만 수정 가능"이라는 의미인데, SC 다수결에서 순수 PASS와 동일하게 집계됨. 2/3번 투표자 모두 **모순의 존재를 인정**(PASS_WITH_FIX)했는데, 이것이 PASS로 전환되어 모순 있는 Arc가 InPlace patch loop에 진입하지 못하고 통과됨.

### STRUCT-3: Stage 2/3 audit에 Contradiction Firewall 없음 [P1]

**위치**: `director_auditor.py` (audit 경로) vs `director_ensemble.py` L860-888 (compare 경로)

Stage 4의 compare 경로에는 CRITICAL 1건 or MAJOR 2건 시 REJECT 강제하는 Contradiction Firewall이 있지만, Stage 2/3의 audit 경로에는 이 방어막이 없음. SC 투표에만 의존하므로, SC 다수결이 위치 모순을 통과시키는 경우 방어 수단이 없음.

### STRUCT-4: InPlace patch 범위 한계 — 이전 Arc 수정 불가 [P2]

**위치**: `four_phase_arc_generator.py` L762-823

InPlace patch는 현재 심사 중인 Arc의 JSON dict만 수정 가능. Director가 "이전 Arc의 요약을 수정하라"고 지시해도, 이미 저장된 이전 Arc 파일은 수정 범위 밖. Arc 3 패치에서 "Arc 2 요약본의 위치를 여의도로 수정"을 지시했지만, `arc_002.txt`는 변경되지 않고 "강남 테헤란로"로 잔존.

### STRUCT-5: compare vs audit 구조적 점수 괴리 [INFO, 설계 의도]

| 항목 | compare (다후보 비교) | audit (단후보 심사) |
|------|----------------------|---------------------|
| temperature | 0.3 | 0.1 |
| thinking_level | "high" | "medium" |
| Self-Consistency | 없음 (1회) | 있음 (1~3회) |
| 후처리 | raw LLM 점수 | NC-3B 교정, Firewall, SCM 보정 |
| 컨텍스트 | 후보 비교용 | advisory 전량 + 이전 Arc tactical_doc 전문 |

**실제 사례**: Arc 4 시도 1에서 compare PASS(98) → audit REJECT(75), -23점 급락. compare는 "3후보 중 최선" 상대 평가, audit는 "절대 기준 무결성 검사". 이 괴리는 2중 게이트의 상호보완으로 설계 의도에 부합.

---

## 4. Arc 상태 정합성 수동 검증

### 4-A. 자산 흐름 추적

| 시점 | 현금 | 포지션 | 총자산 | 검증 |
|------|------|--------|--------|------|
| Arc 1 종료 (Ep 4) | 20억 | - | 20억 | OK |
| Arc 2 Ep 5 | 5억 | WTI 15억 | 20억 | OK |
| Arc 2 Ep 7 | 5억 | WTI 25.4억 (15+10.4) | 30.4억 | OK (23%x3=69%, 15억x69.3%=10.4억) |
| Arc 2 종료 (Ep 8) | 5억 | WTI ~25.4억 | ~30.4억 | OK |
| Arc 3 Ep 10 | 17.5억 (5+5.23+7.27실현) | WTI ~12.5억 | ~30억 | OK |
| Arc 3 종료 (Ep 12) | ~17.5억 | WTI ~12.5억 | ~30억 | OK (사무실 비용 수천만 차감 미반영 — 근사치 OK) |
| Arc 4 Ep 14 | 40억 (전량 청산) | - | 40억 | OK (누적 WTI 수익 20억) |
| Arc 4 Ep 15 | 25억 | 금 15억 | 40억 | OK |
| Arc 4 Ep 17 | ~37.5억 (절반 익절 +5억 실현, 금 7.5억 환수) | 금 ~7.5억 | ~45억 | OK |
| Arc 5 Ep 19 | 50억 (금 전량 청산 +5.14억) | - | 50억 | OK |
| Arc 5 종료 (Ep 22) | 50억 | - | 50억 | OK |

**자산 흐름 결론: 전체적으로 정합. 산술 모순 없음.**

**Arc 종료 수치 미기재 이슈 (TF-C)**: Arc 2, Arc 3의 arc_end_state에 정확한 총자산 수치가 명시되지 않음. Arc 2는 "평가액 30억 넘어섬"으로만 기술, Arc 3는 종료 수치 자체가 없음. 다음 Arc 시작 시 수치가 재설정되므로 파이프라인 동작에는 지장 없으나, 교차검증이 어려움.

### 4-B. 위치 연속성 추적

| Arc 전환 | 이전 종료 위치 | 다음 시작 위치 | 판정 |
|----------|---------------|---------------|------|
| Arc 1→2 | 강남 테헤란로, SW인베스트먼트 사무실 | 강남 테헤란로의 소형 오피스텔 | OK |
| Arc 2→3 | 강남 테헤란로의 소형 오피스텔 (Ep 8) | **서울 여의도**, SW인베스트먼트 사무실 (Ep 9) | **GAP** |
| Arc 3→4 | 서울 여의도, SW인베스트먼트의 **새 사무실** (Ep 12) | **서울 강남구 역삼동의 5평짜리 원룸 오피스** (Ep 13) | **CRITICAL GAP** |
| Arc 4→5 | 서울 여의도, SW인베스트먼트 사무실 (Ep 17) | 서울 여의도, SW인베스트먼트 사무실 (Ep 18) | OK |

### 4-C. 발견된 모순

#### CONTRA-1: Arc 2→3 위치 점프 [MAJOR]

- Arc 2 Ep 6~8 종료 위치 "강남 테헤란로의 소형 오피스텔" (Ep 5 종료는 "서울 여의도, 한미증권 VIP룸" — 방문 후 귀환, 본거지는 강남)
- Arc 3 Ep 9 시작이 "서울 여의도, SW인베스트먼트 개인 사무실"
- 여의도 이사는 Arc 3 Ep 11에서야 발생 ("여의도 증권가의 심장부에 최고급 오피스 빌딩")
- **Ep 9~10이 이미 여의도에 있으면, Ep 11의 여의도 이사는 논리적 모순**
- InPlace patch 적용됨. 패치 지시는 "Arc 2 요약본의 사무실 위치를 '강남 테헤란로'에서 '여의도'로 수정"이었으나, **실제로는 Arc 3의 JSON dict만 수정** — `arc_002.txt`는 여전히 "강남 테헤란로"로 잔존 (STRUCT-4 한계)

#### CONTRA-2: Arc 3→4 위치 역행 + 이중 묘사 [CRITICAL]

- Arc 3 종료: "서울 여의도, SW인베스트먼트의 새 사무실" (Ep 11에서 대형 사무실 확보)
- Arc 4 Ep 13 시작 태그: "서울 강남구 역삼동의 5평짜리 원룸 오피스"
- Arc 4 Ep 13 본문: "성북동 본가 서재"에서 시작 — **시작 태그와 본문도 불일치** (TF-C)
- Arc 4 Ep 14부터는 다시 "여의도, SW인베스트먼트 사무실"로 정상 복귀

**이중 묘사 텍스트 충돌 (TF-F)**: Ep 13 시작 상태에 `"5평짜리 원룸 오피스. 창문에는 암막 블라인드... 텅 빈 에너지 드링크 캔이 놓여 있다.. 텅 비어있는 넓은 공간에 최고 사양 워크스테이션 두 대만이 놓여 있다."` — 마침표 2개 연속 `..`이 존재하며, "5평"과 "넓은 공간"이 자기모순. 두 개의 서로 다른 후보 텍스트가 병합된 잔해로 추정.

**SC 통과 원인 (TF-D)**: audit 1번 투표자(thinking_level="medium")가 score=80으로 위치 모순 지적. 그러나 2/3번 투표자(thinking_level="low")가 각각 PASS_WITH_FIX(90, 95)를 줌. SC 다수결 2/3 PASS, median=90 → PASS 확정. InPlace patch loop 미진입으로 위치 미수정 잔존.

#### CONTRA-2b: Arc 4 시도 2 ArcValidator REJECT 세부 [참고]

- Arc 4 시도 2 1차 생성에서 ArcValidator가 CRITICAL 2건 + MAJOR 2건 감지하여 REJECT
- 해당 후보는 자동 폐기되고 3후보 재생성이 수행됨
- 재생성 후 Director compare에서 후보 2(conservative) 선택, PASS_WITH_FIX(92점)
- **4건의 구체적 모순 내용은 콘솔에 미출력** (BUG-5 로깅 갭)

#### CONTRA-3: Arc 3 Ep 9~10 시작 묘사 반복 [MINOR]

- Ep 9 "이제 막 배달된 최신형 컴퓨터 두 대가 놓여 있다", Ep 10 "최신형 컴퓨터 두 대의 모니터에서 WTI 선물 차트가 깜빡이고 있다" — Ep 9~10 간 유사 문구 반복. Ep 11은 "컴퓨터 화면에는 막대한 수익 실현을 알리는 거래 내역이 떠 있다"로 변형됨
- 세 에피소드 모두 "서울 여의도, SW인베스트먼트 개인 사무실"로 시작하며 뒤의 환경 묘사만 다름
- Director 재심사 피드백에서 지적되었고 InPlace patch 대상이었으나, 최종 저장 텍스트에 구조적 유사성 잔존

### 4-D. 관계 연속성 추적

| NPC | Arc 1 종료 | Arc 2 종료 | Arc 3 종료 | Arc 4 종료 | Arc 5 종료 |
|-----|-----------|-----------|-----------|-----------|-----------|
| 아버지 한정호 | 무관심→의외성 인지 | (언급 없음) | 관망→직접 개입 | 의중 숨김 관망 | (언급 없음) |
| 큰형 한태준 | 무관심 | 관심 시작 | 경계/잠재적 적대 | (직접 언급 없음) | 적대(엿듣기) |
| 둘째형 한태민 | 무관심 | (언급 없음) | (언급 없음) | (언급 없음) | 적대(엿듣기) |
| 박성호 PB | (미등장) | 의심→경악 | 경악→절대 신뢰 | 광신에 가까운 믿음 | 광신적 신뢰 (유지) |
| 윤지수 | (미등장) | (미등장) | 미존재→핵심 조력자 | 파트너 강화 | 절대 신뢰 |
| 강민혁 | (미등장) | (미등장) | (미등장) | (미등장) | 법률 방패 합류 |

**관계 연속성 결론: 정합. 모순 없음. NPC 등장/퇴장 패턴 자연스러움.** (TF-C 확인)

### 4-E. 소지품 연속성

- Arc 1→2: 법인인감+통장+워크스테이션 계승 OK (Equipment Sync 6개: 정장, 가방, 법인인감, 인감증명서, 통장, 워크스테이션)
- Arc 2→3: +박성호 명함, 노키아 폰 계승 OK (Equipment Sync 7개 — 인감증명서 탈락, +2 -1)
- Arc 3→4: +여의도 사무실, +윤지수 계약서, 워크스테이션 1→2대 계승 OK (Equipment Sync 9~10개)
- Arc 4→5: +WTI 청산보고서, +금 선물 계약서 계승 OK (Equipment Sync 11~12개)

**소지품 연속성: 대체로 정합. 매 Arc 1~2개 자연 증가. 단, Arc 2→3 전환에서 "법인 인감증명서"가 설명 없이 탈락 — 소실 1건.**

### 4-F. 시간선 정합성 (TF-C)

| Arc | 시간 범위 | 판정 |
|-----|-----------|------|
| Arc 1 | 2006년 1월 (회귀) ~ 법인설립 2~3주 | OK |
| Arc 2 | 2006년 2~3월 ~ 이란 핵 위기 4월 | OK |
| Arc 3 | Arc 2 직후 ~ 에콰도르 5월 16일 이후 | OK |
| Arc 4 | 6~7월 (이스라엘-헤즈볼라) ~ 8월 (금리 중단) | OK |
| Arc 5 | 2006년 9월 ~ 12월 31일 | OK |

**시간선: 정합. 역행/겹침 없음.**

---

## 5. Treatment → Arc 수치 발산 분석 (TF-E)

| Block | Treatment capital_after | Arc 실제 총자산 | 괴리 | 심각도 |
|-------|------------------------|----------------|------|--------|
| Block 1 | 20억 | 20억 | 0 | OK |
| Block 2 | **23억** (미실현 +3억) | **30.4억** (미실현 +10.4억) | **7.4억** | MAJOR |
| Block 3 | 30억 | 30억 | 0 (Block 2 괴리가 수렴) | OK |
| Block 4 | 45억 | 45억 | 0 | OK |
| Block 5 | 50억 | 50억 | 0 | OK |

**Block 2 괴리 원인**: Treatment 원본의 reward 서술("15억이 18억이 된다", +3억)은 이란 핵 농축 재개 시점의 초기 수익을 묘사. Arc 2는 이를 4에피소드에 걸쳐 전개하면서 수익을 +10.4억으로 확대(23%×3배=69.3%).

**Director 행동 관찰 (TF-A)**: Arc 2 시도 2의 Director audit에서 요약 블록(Treatment 기준 3억)과 tactical doc(LLM 생성 10.4억) 불일치를 발견하고, **LLM 생성물(10.4억)을 정답으로 채택**하여 요약 블록을 수정 지시. Treatment 원본보다 자기 생성물을 우선시하는 패턴 — 수치의 극적 확대 방향이므로 서사적으로는 유리하나, Treatment 준수성 관점에서 잠재 이슈.

**연쇄 영향**: Block 2의 23억→30.4억 확대가 Block 3 capital_before에 전파되었으나, Block 3 종료 시 30억으로 수렴하여 이후 Arc 4~5는 정합.

---

## 6. Director SC 투표 전수 분석 (TF-A/TF-D)

### SC 발동 3건 상세

| # | Arc/시도 | 1차 투표 | 2차 투표 | 3차 투표 | 결과 | 정당성 |
|---|---------|---------|---------|---------|------|--------|
| 1 | Arc 2 시도 1 | REJECT(83) | PASS_WITH_FIX(90) | REJECT(85) | REJECT (1/3, median=85) | **정당** — 산술 모순 정확히 감지 |
| 2 | Arc 4 시도 1 | REJECT(75) | REJECT(76) | REJECT(50) | REJECT (0/3, median=75) | **정당** — 만장일치, 위치+수치 모순 |
| 3 | Arc 4 시도 2 | REJECT(80) | PASS_WITH_FIX(90) | PASS_WITH_FIX(95) | PASS (2/3, median=90) | **부당** — 위치 모순 잔존 상태 통과 |

SC #3이 부당한 이유:
- 3명 모두 위치 모순을 인지 (1번 REJECT, 2/3번 PASS_WITH_FIX)
- PASS_WITH_FIX = "모순은 있지만 수정 가능" → 그런데 SC PASS 확정으로 **InPlace patch loop 미진입** → 수정 기회 박탈
- 2/3번 투표자의 `thinking_level="low"`가 모순 심각도 과소평가에 기여

### Director audit 2단계 호출 구조 (TF-A)

audit 메서드가 2단계로 LLM을 호출하는 패턴이 관찰됨:
- 1차: 짧은 응답 (134~469자, JSON verdict 추출 추정)
- 2차: 상세 응답 (1143~2684자, Director Thinking 포함)

Arc 2 시도1(134자→1656자), Arc 3(469자→1364자), Arc 4 시도1(637자→1681자), Arc 4 시도2(332자→2684자), Arc 5(1275자→1143자)에서 동일 패턴. 1차 호출 비용이 추가되지만 기능적 문제는 아님.

---

## 7. 개선 아이디어

### IDEA-1: preflight_checker 마커 분리 [수정 필요, BUG-1 해결]

`preflight_checker.py`의 제목 라인에서 ❌를 제거하고, 개별 아이템 앞에만 ❌ 배치:
```
AS-IS: ❌ 다음 아이템 획득 금지 (이미 보유 중):
         - 아이템A - 이유
TO-BE: [아이템 획득 금지 (이미 보유 중)]:
         ❌ 아이템A - 이유
```

### IDEA-2: SC 투표 thinking_level 균등화 [P1, STRUCT-1 해결]

추가 투표(2/3번)의 `thinking_level`을 1차와 동일한 `"medium"`으로 변경. 또는 `PASS_WITH_FIX`를 SC 다수결에서 `PASS`와 별도 카운트하여, PASS_WITH_FIX 다수 시 InPlace patch loop 진입 보장.

### IDEA-3: Stage 2/3 audit에 Contradiction Firewall 추가 [P1, STRUCT-3 해결]

Stage 4 compare 경로의 Contradiction Firewall(CRITICAL 1건 or MAJOR 2건 → REJECT 강제)을 Stage 2/3 audit 경로에도 적용. SC 투표 결과 이후 Python 후처리로 삽입.

### IDEA-4: internal_energy 후처리 자동 strip + 프롬프트 예시 수정 [P2, BUG-2 해결]

(A) `preflight_checker.py` 프롬프트의 무협 전용 예시(`internal_energy`, `martial_level`)를 장르별 분기 (B) 비무협 장르에서 `state_constraints`의 `internal_energy` 필드가 생성되면 Python 후처리에서 자동 제거

### IDEA-5: InPlace patch 후 위치 교차 검증 [P2, STRUCT-4 보완]

InPlace patch 적용 후 `arc_start_state.location`과 이전 Arc `arc_end_state.location`의 정합성을 Python으로 재검증. 현재는 Director 재심사에만 의존.

### IDEA-6: ArcValidator 세부 모순 로깅 [P2, BUG-5 해결]

ArcValidator REJECT 시 각 CRITICAL/MAJOR 항목의 1줄 요약을 `logging.warning`으로 출력하여 디버깅 지원.

### IDEA-7: 장르별 소지품 패턴 확장 [P2, BUG-3 해결]

`genre_schema_builder`에서 장르별 key_item 패턴을 제공하거나, `arc_ensemble.py:651`의 regex를 장르 중립 패턴으로 교체.

---

## 8. 조치 우선순위

| ID | 유형 | 심각도 | 설명 | 상태 |
|----|------|--------|------|------|
| BUG-1 | 코드 버그 | P1 | "금지 아이템: 다음" 오탐 (Arc 2+, 16회+/run) | 미수정 |
| STRUCT-1 | 구조 이슈 | P1 | SC 추가 투표 thinking_level="low" 격하 | 미수정 |
| STRUCT-2 | 구조 이슈 | P1 | PASS_WITH_FIX가 SC에서 PASS와 동등 | 미수정 |
| STRUCT-3 | 구조 이슈 | P1 | Stage 2/3 audit에 Contradiction Firewall 없음 | 미수정 |
| CONTRA-2 | 데이터 모순 | CRITICAL | Arc 3→4 위치 역행 + 이중 묘사 + 태그-본문 불일치 | 저장된 Arc에 잔존 |
| CONTRA-1 | 데이터 모순 | MAJOR | Arc 2→3 위치 점프 (강남→여의도) | 저장된 Arc에 잔존 |
| BUG-2 | 코드 관찰 | P2 | internal_energy 관성 (프롬프트 예시 원인) | 시스템 자체교정, 후순위 |
| BUG-3 | 코드 관찰 | P2 | 소지품 regex 무협 편향 (4곳) | 미수정 |
| BUG-4 | 코드 위생 | P2 | arc_draft_validator dead code (L518, L523) | 미수정 |
| BUG-5 | 로깅 갭 | P2 | ArcValidator CRITICAL/MAJOR 세부 미출력 | 미수정 |
| STRUCT-4 | 구조 한계 | P2 | InPlace patch가 이전 Arc 파일 수정 불가 | 설계 한계 |
| CONTRA-3 | 데이터 반복 | MINOR | Arc 3 Ep 9~10 시작묘사 반복 | 저장된 Arc에 잔존 |
| STRUCT-5 | 설계 정보 | INFO | compare vs audit 구조적 점수 괴리 (설계 의도) | 인지 완료 |

---

## 9. 긍정 관찰

- **수치 정합성 검사 정상 작동**: Arc 2에서 WTI 8% 상승 x 3배 레버리지 != 69.3% 모순을 Director가 정확히 감지하고 REJECT → 수정 후 23% x 3배 = 69%로 교정
- **PASS_WITH_FIX + InPlace patch 루프**: Arc 1, 2, 3에서 모순 감지 → 패치 → 재심사 → PASS 흐름이 설계 의도대로 동작
- **NC-1 레버리지 수익률 검증**: `_check_leverage_return_pct` advisory가 수익률 괴리 감지에 기여
- **Ensemble 3후보 비교**: 매 Arc에서 conservative/balanced/creative 3개 전략이 다양한 접근 제시, Director가 최적 선택
- **Director 독립 판단**: BUG-1로 인한 pre-Director 점수 왜곡(creative=30, balanced=15 등)에도 Director가 서사 판단으로 올바른 후보 선택 (대원칙 3 정상 작동)
- **API 안정성**: gemini-2.5-pro/flash 모든 호출 attempt=1 성공, timeout/retry 0건
- **Enrichment 품질**: 5블록 중 4건 GOOD+ 평가. joint_docs(위치/소지품/복선) 정상 소비, 인과율 용접 4건 전량 반영
- **internal_energy 완전 제거**: InPlace patch/PASS_WITH_FIX로 투자물 오염 근절, 최종 파일에 잔존 0건
- **소지품 누적 정합**: Equipment Sync (6→7→9~10→11~12) 매 Arc 증가, 인감증명서 탈락 1건 외 소실 없음
- **시간선 정합**: 2006년 1월~12월 순차 진행, 역행/겹침 0건
- **LM-G 정상 동작**: Arc 3부터 서사 구조 컨텍스트 주입 — Arc 1~2 미주입은 이전 서사 데이터 부재에 의한 정상 스킵
- **compare→audit 2중 게이트**: Arc 4 시도 1에서 compare PASS(98) → audit REJECT(75), 상대 평가를 통과해도 절대 기준에서 잡아내는 보완적 구조 정상 작동
