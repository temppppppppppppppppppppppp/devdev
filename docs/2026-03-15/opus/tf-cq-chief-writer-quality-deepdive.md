<!-- [참고자료] -->
# TF-CQ: ChiefWriter Quality 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | ChiefWriter Quality: rubric evaluation, self-critique, character consistency, quality gates |
| Source files | chief_writer_quality.py:1290줄 |
| TF Items | 18 (CRITICAL 3 / IMPORTANT 8 / INSIGHT 7) |

---

## 1. Executive Summary

`ChiefWriterQualityGate`는 원고 자기비판(Self-Critique) 파이프라인의 핵심 구현체로, 17개의 독립 검사기(checker)를 순차 실행하여 원고 품질 이슈를 탐지한 뒤, LLM 기반 교정을 최대 3라운드 반복한다. Rubric 평가(4차원 점수)로 조기 스킵 여부를 결정한다.

주요 발견 사항:
- **Rubric 가중치가 동일(equal-weight)로 하드코딩**되어 있어 장르별 특성이 반영되지 않음
- **Severity 판정 로직이 이슈 수량 기반**이라 1~2건의 high-severity 이슈가 "low"로 분류되어 수정을 건너뛸 수 있음 (수정 완료 흔적 있으나 경계 조건 잔존)
- **NPC 관계 일관성 검사가 re.DOTALL 패턴**을 사용하여 수천 자 떨어진 무관한 맥락에서 오탐 발생 가능
- **_fix_manuscript_issues에서 최대 3개 이슈만 수정 지시**하므로 4개 이상 이슈가 탐지되어도 나머지는 무시
- **Rubric 점수 정규화에 NaN/Infinity 위험은 없으나**, division-by-zero guard가 `max(x, 1)` 패턴으로 일부 비직관적 결과 생성 가능

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
  chief_writer.py:generate_ensemble()
         |
         v
  quality_gate.apply_self_critique(manuscript, hud, npcs, genre, ...)
         |
         +---> _evaluate_with_rubric() --- score >= 3.5? ---+
         |         |                                         |
         |    [4 dimensions]                          YES: _self_critique()
         |    1. Show vs Tell                              structural check
         |    2. Sentence diversity                        |
         |    3. Dialogue ratio                   no medium/high? --> SKIP (return original)
         |    4. Sensory balance                           |
         |         |                               has medium/high --> PROCEED
         |    avg(scores) -> 1.0~4.0                       |
         |                                                 v
         +---> _check_ending_hook_presence() --------+     |
         +---> _check_system_term_exposure() --------+--> Gate Issues (forced "high")
         +---> length < 5000 -------------------------+     |
         |                                                  |
         |  if gate issues: _fix_manuscript_issues()        |
         |                                                  v
         +===> MAIN LOOP (max 3 rounds) <==================+
                   |
                   v
              _self_critique(manuscript, hud, encyclopedia, ...)
                   |
                   +---> 17 checkers (sequential):
                   |     1. _check_hud_consistency
                   |     2. _check_cliche_overuse
                   |     3. _check_justification_gaps
                   |     4. _check_npc_relationship
                   |     5. _check_motivation_consistency
                   |     6. _check_writing_directive
                   |     7. _check_expression_freshness
                   |     8. _check_ai_tell_patterns
                   |     9. _check_ending_hook_presence
                   |    10. _check_arithmetic_consistency
                   |    11. _check_system_term_exposure
                   |    12. _check_ending_novelty
                   |    13. _check_temporal_logic
                   |    14. _check_paragraph_structure
                   |    15. _check_tonal_consistency
                   |    16. _check_pov_consistency_critique
                   |    17. _check_scene_transition_markers
                   |    +18. manuscript_length (inline)
                   |
                   v
              severity = count-based:
                   >=5 issues -> "high"
                   >=3 or any high issue -> "medium"
                   1-2 issues -> "low" (treated as "break" in loop)
                   |
                   +-- severity == "low" --> BREAK (no fix)
                   +-- severity >= "medium" --> _fix_manuscript_issues()
                   |                                |
                   |                           LLM ask() with fix prompt
                   |                           (max 3 issues per prompt)
                   |                                |
                   +--- round > 1? ---> _evaluate_with_rubric() >= 3.5? --> BREAK
                   |
                   v
              return current_manuscript
```

---

## 3. TF Items

### TF-CQ-01: Rubric Equal-Weight 하드코딩 -- 장르 무관 동일 가중치 — IMPORTANT

- **Location**: `chief_writer_quality.py:L1186-L1254`
- **Description**: `_evaluate_with_rubric()`는 4개 차원(감정 Show/Tell, 문장 시작 다양성, 대화 비율, 오감 묘사)을 각각 1~4점으로 채점한 뒤 단순 산술 평균(`sum(scores) / len(scores)`)을 계산한다. 가중치가 모두 동일하며 장르별 차별화가 전혀 없다.
- **Evidence**:
  ```python
  # L1254
  avg_score = sum(scores) / len(scores) if scores else 2.0
  ```
  4개 차원 모두 동일한 1/4 가중치. `genre_name` 파라미터를 받지만 사용하지 않음.
- **Impact**: 투자물/현대물에서는 오감 묘사(시각/청각/촉각/후각 키워드)가 무협에 비해 자연스럽게 적을 수 있어, 장르 무관 동일 기준은 투자/현대 장르에서 rubric 점수를 체계적으로 낮게 평가할 수 있다. 반대로 무협에서는 대화 비율이 낮아도 무방한 경우가 있으나 동일 기준 적용.
- **Suggested fix direction**: `genre_name`에 따른 가중치 맵 도입 (예: 무협은 오감 가중 1.5x, 투자물은 대화 가중 1.5x). 또는 validation.yaml에 `quality.rubric_weights.{genre}` 키 추가.

---

### TF-CQ-02: 1~2건 이슈가 severity="low"로 분류되어 수정 건너뜀 — CRITICAL

- **Location**: `chief_writer_quality.py:L346-L358` (severity 판정) + `L219-L220` (break 조건)
- **Description**: `_self_critique()`는 이슈 수량 기반으로 severity를 결정한다. `_has_high_issue` 플래그로 high 이슈 1건이 있으면 "medium"으로 올리는 보정이 L352에 있지만, **1~2건이면서 모두 "medium" severity인 경우** 전체 severity가 "low"가 되어 `apply_self_critique()`의 L219-220에서 즉시 break된다. 즉 medium-severity 이슈 1~2건은 수정되지 않고 통과한다.
- **Evidence**:
  ```python
  # L346-354
  severity = "low"
  _has_high_issue = any(isinstance(i, dict) and i.get("severity") == "high" for i in issues)
  if len(issues) >= 5:
      severity = "high"
  elif len(issues) >= 3 or _has_high_issue:
      severity = "medium"
  # 1~2건: severity="low", has_issues=True → apply_self_critique에서 break

  # L219-220
  if critique_result["severity"] == "low":
      break
  ```
- **Impact**: `hud_contradiction` (medium), `npc_relationship_inconsistency` (medium), `justification_gap` (medium) 등의 이슈가 단독 또는 2건만 발생할 때 수정 없이 통과. 특히 NPC 관계 불일치 같은 서사적으로 중대한 이슈가 놓칠 수 있다.
- **Suggested fix direction**: severity 판정에서 medium 이슈가 1건이라도 있으면 최소 "medium" 반환. 또는 `apply_self_critique`에서 low-severity 판정 시에도 medium 개별 이슈가 있으면 fix를 시도.

---

### TF-CQ-03: _fix_manuscript_issues 최대 3개 이슈만 수정 지시 — IMPORTANT

- **Location**: `chief_writer_quality.py:L1103`
- **Description**: `_fix_manuscript_issues()`는 `issues[:3]`로 슬라이싱하여 최대 3개 이슈만 LLM 교정 프롬프트에 포함한다. 17개 검사기가 5건 이상 이슈를 탐지할 수 있으나 4번째 이후 이슈는 LLM에 전달되지 않는다.
- **Evidence**:
  ```python
  # L1103
  for issue in issues[:3]:  # 최대 3개만 수정
  ```
- **Impact**: 한 라운드에서 5건 이상 이슈가 발견되면 일부가 누락된다. 다음 라운드에서 재감지될 수 있으나, 그 사이 LLM이 수정하면서 새로운 이슈를 도입할 수도 있어 수렴성이 보장되지 않는다. 특히 MAX_CRITIQUE_ROUNDS=3이므로 이론적으로 최대 9개 이슈만 수정 가능.
- **Suggested fix direction**: 이슈 수가 많을 때는 severity 기준으로 정렬하여 high > medium > low 순으로 상위 3개를 선택. 현재는 검사기 등록 순서에 의존.

---

### TF-CQ-04: NPC 관계 일관성 검사의 re.DOTALL 오탐 위험 — IMPORTANT

- **Location**: `chief_writer_quality.py:L698-L710`
- **Description**: `_check_npc_relationship()`는 NPC 이름과 무시/조롱 키워드의 동시 존재를 `re.DOTALL` 패턴으로 확인한다. 이는 NPC 이름이 원고 시작 부분에, 무시 키워드가 수천 자 떨어진 완전히 다른 씬에 있어도 매칭된다.
- **Evidence**:
  ```python
  # L701-702
  context_pattern = f"{esc_name}.*{kw}|{kw}.*{esc_name}"
  if re.search(context_pattern, content, re.DOTALL):
  ```
  `re.DOTALL`은 `.`이 줄바꿈도 매칭하므로 전체 원고를 하나의 문자열로 취급.
- **Impact**: 5,000~15,000자 원고에서 NPC A가 1화 초반 경외 장면에 등장하고, 완전히 다른 NPC B가 후반에서 무시당하는 장면이 있을 때 `{A이름}.*무시` 패턴이 매칭되어 오탐 발생. 이는 "NPC 관계 불일치" 이슈를 잘못 보고하여 불필요한 LLM 교정을 유발.
- **Suggested fix direction**: 단락(paragraph) 단위로 범위를 제한하거나, `re.DOTALL` 대신 `\n{2,}` 이내의 근접 윈도우(예: 500자)에서만 매칭. 또는 양방향 패턴 `{name}.*{kw}|{kw}.*{name}`을 단락 분할 후 적용.

---

### TF-CQ-05: Rubric "Skip" 경로에서 Gate 검사 미적용 — CRITICAL

- **Location**: `chief_writer_quality.py:L138-L159` vs `L166-L194`
- **Description**: `apply_self_critique()`에서 rubric >= 3.5이고 구조적 이슈가 없으면 L159에서 즉시 `return current_manuscript`한다. 그런데 **Gate 검사**(ending_hook 누락, 분량 부족, 메타 용어 노출)는 L166-L194에 위치하여, rubric 조기 스킵 시 Gate 검사가 전혀 실행되지 않는다.
- **Evidence**:
  ```python
  # L138-159: rubric skip path
  rubric_score = self._evaluate_with_rubric(current_manuscript, genre_name)
  if rubric_score >= 3.5 and current_content_length >= int(ManuscriptLimits.MIN_LENGTH):
      _structural = self._self_critique(...)
      _medium_plus = [i for i in _structural.get("issues", []) ...]
      if not _medium_plus:
          return current_manuscript  # <-- Gate 검사 전에 리턴

  # L166-194: Gate 검사 (ending_hook, 분량, 메타 용어)
  _gate_issues: list[str] = []
  if blueprint:
      _eh_issues = self._check_ending_hook_presence(...)
  ```

  그러나 `_self_critique()` 내부에서 동일한 `_check_ending_hook_presence` (L304)와 `_check_system_term_exposure` (L310), 분량 체크(L330-344)가 실행된다. 따라서 구조적 검사(L141의 `_self_critique`) 결과에 이미 이 이슈들이 포함되어 있다. 단, severity 필터가 `medium` 이상만 통과시키므로 ending_hook(medium)과 분량(medium/high)은 걸리지만 `_check_system_term_exposure`의 meta_wall(high)도 걸린다.

  **실질적 위험**: `_self_critique`가 medium 이상 이슈를 반환하면 스킵하지 않으므로, gate 검사 대상 이슈는 대부분 `_self_critique` 내부에서 이미 캡처됨. 그러나 **Gate 전용 로직**(L183-190의 `severity: "high"` 강제 설정과 `_fix_manuscript_issues` 즉시 호출)이 건너뛰어진다는 점이 차이. Gate 경로는 이슈를 "high"로 강제 승격시켜 즉시 수정하지만, `_self_critique` 경로에서는 원래 severity로 처리됨.
- **Impact**: rubric >= 3.5인 고품질 원고에서 시스템 용어("Blueprint", "Block 2")가 노출되었을 때, Gate 경로의 강제 high 승격이 적용되지 않을 수 있음. `_self_critique` 내부에서 meta_wall이 이미 "high"이므로 구조적 검사에서 걸리긴 하지만, Gate 경로의 즉시 수정(별도 LLM 호출) 대신 일반 self-critique 루프에서 처리되어 수정 강도가 다를 수 있다.
- **Suggested fix direction**: Gate 검사를 rubric 스킵 판정 이전으로 이동하거나, rubric 스킵 경로에서도 Gate 검사를 별도 실행.

---

### TF-CQ-06: _check_paragraph_structure 첫 번째 매칭만 보고하고 조기 리턴 — INSIGHT

- **Location**: `chief_writer_quality.py:L969-L1004`
- **Description**: `_check_paragraph_structure()`는 문단을 순회하면서 첫 번째 벽돌 문단을 발견하면 즉시 `return`한다. 원고 전체에 벽돌 문단이 여러 개 있어도 1건만 보고된다.
- **Evidence**:
  ```python
  # L980-983, L988-995, L996-1003 모두 return [...]
  for paragraph in paragraphs:
      ...
      if len(paragraph) >= 1000 and sentence_count >= 12:
          return [...]
      if len(paragraph) >= 700 and sentence_count >= 8:
          return [...]
      if sentence_count >= 12:
          return [...]
  ```
- **Impact**: 복수 벽돌 문단 존재 시 LLM에 1건만 보고되어 나머지는 방치. 다만 multi-round critique에서 재감지 가능.
- **Suggested fix direction**: `return` 대신 `issues.append()`로 수집 후 전체 반환. 또는 의도적 설계라면 주석으로 명시.

---

### TF-CQ-07: _check_temporal_logic 첫 번째 매칭만 보고 — INSIGHT

- **Location**: `chief_writer_quality.py:L949-L967`
- **Description**: `_check_temporal_logic()`도 동일하게 첫 번째 시간 논리 충돌 문단만 보고하고 즉시 리턴.
- **Evidence**:
  ```python
  # L959-966
  if has_immediate and has_long_jump:
      return [...]  # 첫 번째 매칭에서 즉시 리턴
  ```
- **Impact**: TF-CQ-06과 동일. 복수 문단 시간 충돌 시 1건만 보고.
- **Suggested fix direction**: 수집 후 전체 반환.

---

### TF-CQ-08: Rubric 감정 표현 평가 키워드가 한국어 전용 — INSIGHT

- **Location**: `chief_writer_quality.py:L1189-L1201`
- **Description**: `_evaluate_with_rubric()`의 "감정 표현 평가" 차원은 `direct_emotions = ["기뻤다", "슬펐다", "화났다", ...]` 등 한국어 직접 감정 표현만 카운트한다. 장르가 영문 기반이거나 다국어 혼합 원고에서는 완전히 무력화.
- **Evidence**:
  ```python
  # L1189
  direct_emotions = ["기뻤다", "슬펐다", "화났다", "놀랐다", "두려웠다", "경악했다", "분노했다"]
  ```
- **Impact**: 현재 시스템이 한국어 웹소설 전용이라면 문제없으나, 향후 다국어 확장 시 이 rubric 차원이 항상 최고점(4)을 반환하여 실제 품질과 무관해짐. 현재 상태에서는 영향 낮음.
- **Suggested fix direction**: 현재 범위에서는 영향 없음. 다국어 확장 시 키워드 맵을 언어별로 분리.

---

### TF-CQ-09: Rubric 대화 비율 측정의 따옴표 매칭 한계 — INSIGHT

- **Location**: `chief_writer_quality.py:L1222-L1233`
- **Description**: 대화 비율 측정이 `""` 또는 `''` 따옴표 쌍으로 대화를 감지한다. 한국 웹소설에서 흔히 사용되는 닫힘 없는 대사 형식("~라고 말했다" 같은 서술형 대사)이나 하이픈/대시(―) 기반 대사를 캡처하지 못한다.
- **Evidence**:
  ```python
  # L1222
  dialogue_matches = re.findall(r'["\u201c].*?["\u201d]|[\'\u2018].*?[\'\u2019]', content)
  ```
- **Impact**: 따옴표 없이 서술형으로 쓰인 대사가 많은 원고에서 대화 비율이 0에 가깝게 측정되어 rubric 점수 2점(또는 1점)이 부여됨. 이는 rubric 전체 평균을 낮춰 불필요한 self-critique 루프를 유발할 수 있다.
- **Suggested fix direction**: 한국어 대사 패턴 추가 (예: `".*?"` + `―.*?\n` + `~라고` 패턴).

---

### TF-CQ-10: _check_hud_consistency의 무협 편향 키워드 — IMPORTANT

- **Location**: `chief_writer_quality.py:L570-L595`
- **Description**: HUD 모순 체크에서 "강력한 행동" 키워드(`일격에`, `압도`, `박살`, `분쇄`, `제압`, `일도양단`)와 정당화 키워드(`발경`, `기혈`, `폭발`, `전생`)가 무협 장르에 특화되어 있다. 투자물/현대물/판타지에서는 이 검사가 거의 트리거되지 않아 HUD 모순이 통과한다.
- **Evidence**:
  ```python
  # L576-577
  weak_keywords = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "빈사"]
  strong_actions = ["일격에", "압도", "박살", "분쇄", "제압", "일도양단"]
  # L582
  justification_kws = ["발경", "기혈", "폭발", "전생", "대가", "고통", "각오", "최후"]
  ```
- **Impact**: 투자물에서 주인공이 "파산 직전" 상태(HUD)인데 "수십억 투자"를 성공하는 장면은 이 검사를 완전히 우회. HUD 모순 체크가 사실상 무협 전용.
- **Suggested fix direction**: 장르별 키워드 맵 도입 또는 validation.yaml에 장르별 HUD 키워드 외부화.

---

### TF-CQ-11: _check_cliche_overuse 무협 전용 — 비무협 장르 클리셰 미감지 — IMPORTANT

- **Location**: `chief_writer_quality.py:L597-L642`
- **Description**: 클리셰 과다 체크에서 장르별 패턴 분기가 `genre_name == "무협"` 조건에만 있다. 헌터물/투자물/판타지의 장르 특화 클리셰 패턴은 정의되어 있지 않아 recent cliche 카운트(L602-616)만 작동하고 장르 패턴 매칭은 건너뛴다.
- **Evidence**:
  ```python
  # L619
  if genre_name == "무협":
      cliche_patterns = [...]
  # else: 없음 — 비무협 장르는 패턴 매칭 없이 통과
  ```
  또한 `cliche_keywords` (L1261-1276)도 무협 키워드(`검기`, `살기`, `기세`, `경외`)에 편향.
- **Impact**: 헌터물의 "시스템 창 열림 → 스킬 획득 → 레벨업" 반복 패턴이나 투자물의 "폭락 → 매수 → 대박" 클리셰가 감지되지 않음.
- **Suggested fix direction**: GenreGuard 체계와 유사하게 장르별 클리셰 패턴 맵 도입. 또는 `validation.yaml`에 `quality.cliche_patterns.{genre}` 키 추가.

---

### TF-CQ-12: _count_recent_cliches DB 캐시 미스 시 빈 dict 반환 — IMPORTANT

- **Location**: `chief_writer_quality.py:L1257-L1289`
- **Description**: `_count_recent_cliches()`는 `self.host._get_cached_manuscript(i)`를 호출하는데, 캐시가 비어있으면 `{"content": "", "hud_snapshot": {}}` 기본값을 반환한다 (chief_writer.py:L1832). 캐시 미구축 상태에서는 모든 이전 에피소드의 content가 빈 문자열이므로 클리셰 카운트가 항상 0이 되어 과다 사용을 감지하지 못한다.
- **Evidence**:
  ```python
  # chief_writer_quality.py L1282-1283
  cached = self.host._get_cached_manuscript(i)
  content = cached.get("content", "")
  # chief_writer.py L1830-1832
  def _get_cached_manuscript(self, ep_num: int) -> dict:
      return self._manuscript_cache.get(ep_num, {"content": "", "hud_snapshot": {}})
  ```
- **Impact**: 첫 실행이나 캐시 무효화 후에는 클리셰 과다 감지가 완전히 비활성화. 이는 알려진 한계이나 문서화되어 있지 않음. DB에서 직접 로드하는 fallback이 없음.
- **Suggested fix direction**: 캐시 미스 시 DB fallback 조회 추가 또는 캐시 미스 빈도를 모니터링하는 로깅 추가.

---

### TF-CQ-13: Self-Critique 루프의 비수렴 위험 — IMPORTANT

- **Location**: `chief_writer_quality.py:L196-L239`
- **Description**: Self-Critique 루프는 최대 3라운드를 반복한다. 각 라운드에서 LLM이 이슈를 수정하지만, LLM 수정이 새로운 이슈를 도입할 수 있다 (예: 분량 확장 시 새 클리셰 도입, 엔딩 훅 수정 시 톤 불일치 발생). 3라운드 상한이 있어 무한 루프는 아니지만, 수렴하지 않고 왕복(oscillation)할 가능성이 있다.
- **Evidence**:
  ```python
  # L196
  for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
      critique_result = self._self_critique(...)
      ...
      current_manuscript = self._fix_manuscript_issues(current_manuscript, critique_result, hud_report)
      # LLM이 수정한 원고로 다시 _self_critique → 새 이슈 발생 가능
  ```
  특히 `_fix_manuscript_issues`가 최대 3개 이슈만 수정하므로(TF-CQ-03), 미수정 이슈 + 새로 도입된 이슈로 다음 라운드에 이슈 수가 증가할 수도 있다.
- **Impact**: 최악의 경우 3라운드 모두 소진하면서 원고 품질이 개선되지 않거나 오히려 저하됨. LLM API 비용 3회 추가 발생.
- **Suggested fix direction**: 라운드 간 이슈 카운트 모니터링 — 이슈 수가 증가하면 조기 종료. 또는 이전 라운드와 동일한 이슈가 재발하면 break.

---

### TF-CQ-14: _check_motivation_consistency 키워드 추출 로직 취약 — INSIGHT

- **Location**: `chief_writer_quality.py:L715-L758`
- **Description**: 동기/약속 방치 감지에서 키워드를 `mot["text"].split()[:4]`로 추출한다. 한국어는 공백으로 분리하면 조사가 포함된 어절이 되어, "복수를 위한 여정"에서 `["복수를", "위한", "여정"]`이 추출된다. "복수"라는 핵심 단어가 "복수를"로 변형되어 원고에서 "복수"만 쓰였을 때 매칭 실패.
- **Evidence**:
  ```python
  # L728
  _kws = [w for w in mot["text"].split()[:4] if len(w) >= 2]
  if _kws and not any(kw in content for kw in _kws):
  ```
  `"복수를" in "그는 복수를 다짐했다"` → True (OK), 하지만 `"복수를" in "복수의 칼날"` → False (false negative).
- **Impact**: 조사 변형으로 인한 false negative. severity가 "low"이므로 실질적 영향은 제한적이나, 체계적으로 동기 방치를 놓칠 수 있다.
- **Suggested fix direction**: 형태소 분석기 적용 또는 최소 조사 제거 (`re.sub(r"[을를이가은는에의로]$", "", word)`).

---

### TF-CQ-15: sanitize_leakage의 JSON 파싱 후 원본 텍스트 처리 경로 불일치 — IMPORTANT

- **Location**: `chief_writer_quality.py:L32-L77`
- **Description**: `sanitize_leakage()`에서 JSON 파싱 성공 시 banned_keys 제거 후 `json.dumps()`로 반환하지만, 파싱 실패 시 텍스트 라인 필터링 + 영문 괄호 병기 제거를 수행한다. 두 경로의 처리 범위가 다르다: JSON 경로에서는 영문 괄호 병기 제거(L75)가 적용되지 않고, 텍스트 경로에서는 banned_keys 중 "scene_summary", "spoiler" 등 키 이름이 아닌 라인 패턴만 제거한다.
- **Evidence**:
  ```python
  # L57-61: JSON 성공 경로 — banned_keys 제거 후 바로 return
  if isinstance(data, dict):
      for key in banned_keys:
          if key in data:
              del data[key]
      return json.dumps(data, ensure_ascii=False, indent=4)
  # 영문 괄호 병기 제거(L75)는 여기 도달 안 함

  # L67-76: 텍스트 경로 — 라인 필터링 + 영문 괄호 제거
  ```
- **Impact**: JSON 형식 원고에서 "윈도우(Windows)" 같은 영문 괄호 병기가 제거되지 않음. 비JSON 원고에서는 "scene_summary", "spoiler" 키가 JSON 키 형태가 아닌 한 제거되지 않음. 두 경로의 sanitization 강도가 불균일.
- **Suggested fix direction**: JSON 경로에서도 `json.dumps()` 결과에 대해 영문 괄호 병기 제거를 적용. 또는 공통 후처리 함수로 통합.

---

### TF-CQ-16: _check_writing_directive expression_ban 부분 문자열 매칭 — INSIGHT

- **Location**: `chief_writer_quality.py:L769-L778`
- **Description**: `expression_ban` 검사에서 `expr in manuscript` 사용. 금지 표현이 다른 단어의 부분 문자열일 때 오탐 발생 가능. 예: 금지 표현 "경"이 "경외", "경고", "경험" 등에서 모두 매칭.
- **Evidence**:
  ```python
  # L771
  if expr and expr in manuscript:
  ```
- **Impact**: 실제로 `expression_ban`에 1글자 표현이 들어올 가능성은 낮으므로 현실적 위험은 제한적. 다만 "어느새", "그야말로" 같은 2~3글자 표현이 다른 맥락에서 사용될 수 있음.
- **Suggested fix direction**: 최소 길이 필터(예: `len(expr) >= 2`)는 이미 있으나, 어절 경계 검사(`f" {expr} "` 또는 regex `\b` 상당) 추가 고려.

---

### TF-CQ-17: _check_ending_novelty 50자 꼬리 비교의 과소 범위 — INSIGHT

- **Location**: `chief_writer_quality.py:L918`
- **Description**: 엔딩 참신성 검사에서 원고 마지막 50자만 비교 대상으로 사용한다. 한국어 기준 50자는 약 2~3문장으로, 엔딩 문구가 여러 문장에 걸쳐 유사한 경우를 놓칠 수 있다.
- **Evidence**:
  ```python
  # L918
  tail = manuscript[-50:].strip() if len(manuscript) > 50 else manuscript.strip()
  ```
  반면 `_check_ending_hook_presence`(L890)는 500자를 사용.
- **Impact**: 엔딩 반복이 50자 이내에서만 감지되어, 마지막 200자에 걸친 유사한 패턴은 놓침.
- **Suggested fix direction**: 비교 범위를 100~200자로 확장. `_check_ending_hook_presence`의 500자와 균형 맞추기.

---

### TF-CQ-18: 에러 핸들링 — Gate 수정 실패 시 비차단이나 원본 미보존 — CRITICAL

- **Location**: `chief_writer_quality.py:L193-L194` + `L1138-L1161`
- **Description**: Gate 검사 실패 시(L193) `logging.warning`으로 기록하고 계속 진행한다. 이 자체는 적절한 비차단 정책이다. 그러나 `_fix_manuscript_issues` 내부(L1138-1161)에서 더 심각한 문제가 있다:

  1. LLM `ask()` 호출 성공 후 JSON 파싱 성공 시 **분량 부족 경고만 로깅하고 수정본을 반환**(L1155). 즉 LLM이 content를 빈 문자열로 반환해도 JSON 파싱이 성공하면 그대로 채택.
  2. LLM 응답의 JSON 파싱 실패 시(L1156-1158) 원본을 유지하지만, `logging.info` 레벨이라 운영 시 놓치기 쉬움.
  3. `ask()` 자체 예외 시(L1159-1161) `logging.warning`으로 기록하고 원본 반환 — 이 부분은 적절.

- **Evidence**:
  ```python
  # L1143-1158
  try:
      _fixed_parsed = json.loads(fixed)
      _fixed_content = _fixed_parsed.get("content", "") if isinstance(_fixed_parsed, dict) else ""
      if isinstance(_fixed_content, str):
          _fc_len = len(_fixed_content)
          _min = int(ManuscriptLimits.MIN_LENGTH)
          if _fc_len < _min:
              logging.warning(...)
      return fixed  # <-- content가 빈 문자열이어도 반환
  except (json.JSONDecodeError, ValueError, TypeError):
      logging.info(...)  # info 레벨
      return manuscript
  ```
- **Impact**: LLM이 `{"content": ""}` 또는 `{"content": "짧은 수정"}` (100자 미만)을 반환하면 경고만 로그하고 그대로 채택. 원본보다 품질이 낮은 수정본이 최종 원고가 될 수 있음. 분량 부족 경고(L1150-1154)는 있지만 **반환을 차단하지 않음**.
- **Suggested fix direction**: 수정본의 content 길이가 원본 대비 현저히 짧으면(예: 50% 미만) 원본을 유지. 또는 `_fc_len < _min` 일 때 원본 반환.

---

## 4. Summary Matrix

| ID | Title | Severity | Location (Lines) | 수정 필요성 |
|----|-------|----------|-------------------|-------------|
| TF-CQ-01 | Rubric Equal-Weight 하드코딩 | IMPORTANT | L1186-L1254 | 장르별 가중치 도입 |
| TF-CQ-02 | 1~2건 medium 이슈 "low" 분류 | CRITICAL | L346-L358, L219-L220 | severity 로직 보강 |
| TF-CQ-03 | 최대 3개 이슈만 수정 지시 | IMPORTANT | L1103 | severity 기반 정렬 |
| TF-CQ-04 | NPC 관계 re.DOTALL 오탐 | IMPORTANT | L698-L710 | 근접 윈도우 제한 |
| TF-CQ-05 | Rubric Skip 시 Gate 미적용 | CRITICAL | L138-L159 vs L166-L194 | Gate 검사 순서 조정 |
| TF-CQ-06 | paragraph_structure 조기 리턴 | INSIGHT | L969-L1004 | 수집 후 전체 반환 |
| TF-CQ-07 | temporal_logic 조기 리턴 | INSIGHT | L949-L967 | 수집 후 전체 반환 |
| TF-CQ-08 | Rubric 감정 키워드 한국어 전용 | INSIGHT | L1189-L1201 | 현재 무영향 |
| TF-CQ-09 | 대화 비율 따옴표 한계 | INSIGHT | L1222-L1233 | 한국어 대사 패턴 추가 |
| TF-CQ-10 | HUD 검사 무협 편향 | IMPORTANT | L570-L595 | 장르별 키워드 맵 |
| TF-CQ-11 | 클리셰 검사 무협 전용 | IMPORTANT | L597-L642 | 장르별 패턴 추가 |
| TF-CQ-12 | 클리셰 캐시 미스 시 무감지 | IMPORTANT | L1257-L1289 | DB fallback 추가 |
| TF-CQ-13 | Self-Critique 비수렴 위험 | IMPORTANT | L196-L239 | 이슈 증가 시 조기 종료 |
| TF-CQ-14 | 동기 키워드 조사 변형 | INSIGHT | L715-L758 | 조사 제거 전처리 |
| TF-CQ-15 | sanitize_leakage 경로 불일치 | IMPORTANT | L32-L77 | 공통 후처리 통합 |
| TF-CQ-16 | expression_ban 부분문자열 | INSIGHT | L769-L778 | 어절 경계 검사 |
| TF-CQ-17 | ending_novelty 50자 과소 | INSIGHT | L918 | 범위 확장 |
| TF-CQ-18 | 수정본 품질 검증 부재 | CRITICAL | L1138-L1161 | 원본 대비 길이 검증 |

---

## 5. 핵심 코드 참조 (Appendix)

### A. Rubric 평가 차원 (L1186-L1254)

```python
# 차원 1: 감정 Show vs Tell (L1188-L1201)
direct_emotions = ["기뻤다", "슬펐다", "화났다", "놀랐다", "두려웠다", "경악했다", "분노했다"]
direct_rate = direct_count / max(chars_per_1000, 1)
# 0.5이하→4, 1.5이하→3, 3.0이하→2, 초과→1

# 차원 2: 문장 시작 다양성 (L1203-L1218)
starters = [s[:2] for s in sentences[:20]]
unique_rate = len(set(starters)) / max(len(starters), 1)
# 0.7이상→4, 0.5이상→3, 0.3이상→2, 미만→1

# 차원 3: 대화 비율 (L1220-L1233)
dialogue_ratio = dialogue_chars / max(len(content), 1)
# 0.15~0.40→4, 0.10~0.50→3, >0→2, 0→1

# 차원 4: 오감 묘사 균형 (L1235-L1252)
# visual/auditory/tactile/olfactory 각 키워드 존재 여부
# 3개이상→4, 2개→3, 1개→2, 0개→1

# 최종: 단순 평균 (L1254)
avg_score = sum(scores) / len(scores) if scores else 2.0
```

### B. Severity 판정 로직 (L346-L358)

```python
severity = "low"
_has_high_issue = any(isinstance(i, dict) and i.get("severity") == "high" for i in issues)
if len(issues) >= 5:
    severity = "high"
elif len(issues) >= 3 or _has_high_issue:
    severity = "medium"
# 주의: 1~2건 medium 이슈 → severity="low" → break
```

### C. Gate 검사 흐름 (L166-L194)

```python
_gate_issues: list[str] = []
if blueprint:
    _eh_issues = self._check_ending_hook_presence(current_manuscript, blueprint)
if len(current_manuscript) < 5000:
    _gate_issues.append(...)
_meta_issues = self._check_system_term_exposure(current_manuscript, genre_name)
if _gate_issues:
    current_manuscript = self._fix_manuscript_issues(...)
    # severity="high" 강제 설정
```

### D. Self-Critique 17개 검사기 등록 순서 (L271-L344)

| # | 검사기 | Severity 반환 | 장르 의존 |
|---|--------|---------------|-----------|
| 1 | _check_hud_consistency | medium | 무협 편향 |
| 2 | _check_cliche_overuse | low~medium | 무협 전용 |
| 3 | _check_justification_gaps | medium | 무협 편향 |
| 4 | _check_npc_relationship | medium | 범용 |
| 5 | _check_motivation_consistency | low | 범용 |
| 6 | _check_writing_directive | medium | 범용 |
| 7 | _check_expression_freshness | low | 범용 |
| 8 | _check_ai_tell_patterns | low | 한국어 |
| 9 | _check_ending_hook_presence | medium | 범용 |
| 10 | _check_arithmetic_consistency | high | 범용 |
| 11 | _check_system_term_exposure | high | 장르 조건부 |
| 12 | _check_ending_novelty | medium | 범용 |
| 13 | _check_temporal_logic | medium | 범용 |
| 14 | _check_paragraph_structure | low~medium | 범용 |
| 15 | _check_tonal_consistency | medium | 범용 |
| 16 | _check_pov_consistency_critique | medium | 범용 |
| 17 | _check_scene_transition_markers | low~medium | 범용 |
| 18 | manuscript_length (inline) | medium~high | 범용 |

### E. ManuscriptLimits 참조값

```python
MIN_LENGTH = 4000    # 최소 글자수 (blocking)
WARNING_LENGTH = 4500
TARGET_LENGTH = 5000  # 목표 글자수
MAX_LENGTH = 15000
```

### F. 임계값 외부화 현황

| 항목 | 외부화 여부 | 위치 |
|------|------------|------|
| CLICHE_WINDOW | YES | validation.yaml `quality.cliche_window` |
| ManuscriptLimits | YES | validation.yaml `manuscript.*` |
| Rubric 점수 임계값 3.5 | NO | L139, L226 하드코딩 |
| Rubric 차원 가중치 | NO | 동일 가중치 하드코딩 |
| Max critique rounds (3) | NO | L123 하드코딩 |
| Fix issues max (3) | NO | L1103 하드코딩 |
| Severity 경계 (3건, 5건) | NO | L350-352 하드코딩 |
| 클리셰 임계값 (3회) | NO | L605 하드코딩 |
| 벽돌 문단 임계값 (1000자/700자) | NO | L980, L988 하드코딩 |
| 톤 불일치 임계값 (2회/3회) | NO | L1031, L1042 하드코딩 |
| 산술 오차 허용률 (5%) | NO | L452 하드코딩 |
