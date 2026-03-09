# Treatment 블록 제작 가이드

> 인코딩: UTF-8
> 작성일: 2026-03-09
> 근거: 8작품 560블록 전수 감사 결과 (aggregate_audit_report.md)
> 대상: `tools/treatment_builder.py` 및 수동/LLM 기반 Treatment 생성 전반
> 목적: 코덱스 감사에서 발견된 8대 결함 패턴을 원천 차단하는 제작 하네스

---

## 1. 현황 진단: 왜 8작품이 동일하게 망가졌는가

### 1.1 근본 원인

현재 `treatment_builder.py`는 3-Phase 구조:
```
Phase 1: 60블록 뼈대 (1회 LLM 호출 → 전량 일괄 생성)
Phase 2: 3블록씩 상세 (20회 LLM 호출 → content 4필드만)
Phase 3: 메타데이터 추출 (60회 LLM 호출 → 각 블록 독립)
```

**문제점**:
- Phase 1에서 60블록을 **한 번에** 생성 → LLM이 "안전한 패턴"으로 수렴
- Phase 3 메타데이터 추출이 **블록 간 독립** → 연속성 보장 메커니즘 0
- **검증 루프 부재** → 생성 후 자본/NPC/감정 정합성 미검사
- **안티패턴 명시 없음** → LLM이 균등 분배(5종×14회)를 최적 전략으로 채택

### 1.2 8대 결함 패턴 (감사 결과)

| ID | 패턴 | 8작품 공유율 | 심각도 |
|----|------|-------------|--------|
| A | capital_before ≠ prev capital_after (68/70) | 100% | P0 |
| B | NPC 2명 고정, before 매 블록 리셋 | 100% | P0 |
| C | 적대자 단일 고정 (70블록 동일) | 100% | P1 |
| D | emotional_beat 4종×3강도 수학적 순환 | 100% | P1 |
| E | deal_type 5종×14회 균등 분배 | 100% | P1 |
| F | duration 전량 "7일" 고정 | 100% | P2 |
| G | solution/callback/success_pattern 템플릿 반복 | 100% | P1 |
| H | 빙의 death_flag/slip_up 전량 동일 | 100% (빙의) | P1 |

---

## 2. 권장 제작 아키텍처

### 2.1 5-Phase 분할 생성 (핵심 변경)

기존 3-Phase를 5-Phase로 확장하여 **서사 품질 게이트**를 삽입한다.

```
Phase 0: 대단원 아크 설계 (1회)
  → 7개 대단원 × 10블록 구조 설계
  → 적대자 변천사, NPC 등퇴장 타임라인, 자본 변곡점 설계
  → 이 단계에서 "패배 블록", "전환점 블록" 위치 확정

Phase 1: 대단원별 10블록 상세 생성 (7회)
  → 이전 대단원 요약 + 이번 대단원 목표 주입
  → 직전 블록의 capital_after를 다음 블록 capital_before로 강제
  → NPC 관계 누적 상태를 컨텍스트로 전달

Phase 2: 메타데이터 채움 (블록별, 이전 블록 참조)
  → Phase 3과 동일하나 이전 5블록 메타데이터를 컨텍스트로 주입
  → relationship_delta.before = 직전 블록의 after 강제

Phase 3: Python 자동 검증 + 수정 루프
  → 8대 결함 패턴 자동 탐지
  → 위반 블록만 재생성 요청 (전체 재생성 X)

Phase 4: 3-Pass 감리
  → 1차 전수조사 → 2차 오탐 제거 → 3차 최종 확정
```

### 2.2 Phase 0: 대단원 아크 설계 (가장 중요)

70블록을 생성하기 **전에** 서사 골격을 먼저 확정한다. 이 단계가 없으면 LLM은 무한 균등 반복으로 수렴한다.

**프롬프트 구조**:
```
당신은 웹소설 시놉시스 설계 전문가입니다.

[Bible 컨텍스트]

아래 규격으로 7개 대단원(각 10블록)의 서사 골격을 설계하세요.

## 필수 설계 항목

### 적대자 변천사 (최소 3세력)
- 대단원 1~2: 초기 적대자 (예: 내부 반대파)
- 대단원 3~4: 중기 적대자 (예: 경쟁사 연합)
- 대단원 5~7: 최종 적대자 (예: 글로벌 세력)
- 각 적대자의 등장/퇴장/약점 변화 명시

### NPC 등퇴장 타임라인 (최소 8명)
- 대단원별 신규 NPC 1~2명 추가
- 기존 NPC 관계 변화 마일스톤 (협력→갈등→화해 등)
- NPC 이탈/배신/사망 이벤트 배치

### 자본 성장 곡선 (변동 필수)
- 초반(1~20): 급성장 구간 (20~40% 변동)
- 중반(21~40): 위기 구간 (성장 둔화/일시 하락 포함)
- 후반(41~60): 재도약 구간 (변동폭 줄어듦)
- 최종(61~70): 안정화 또는 최종 승부
- 최소 3개 블록에서 자본 감소 필수 (패배/손실)

### 감정 곡선 설계
- 대단원별 emotional_beat 분포 설계
- 10블록 내에서 최소 5종 이상의 beat type 사용
- intensity 1~10 전 구간 활용 (저조한 구간 필수)
- "조용한 블록" 최소 5개 배치 (tension 4~6, intensity 3~5)

### 복선 장기 아크 (최소 5개)
- 10블록 이상 지연 회수되는 장기 복선 배치
- 각 복선의 심기 블록, 힌트 블록, 회수 블록 명시

### 패배/좌절 블록 (최소 7개)
- 70블록 중 최소 10%는 주인공이 실질적으로 지는 블록
- success_pattern이 "실패"/"부분 성공"/"피로스 승리"인 블록 배치

## 출력 형식
[대단원별 JSON 구조]
```

### 2.3 Phase 1: 대단원별 10블록 생성

**핵심: 이전 대단원 결과를 컨텍스트로 주입**

```
프롬프트:
  [Phase 0 전체 아크 설계]

  ## 직전 대단원 종료 상태
  - 마지막 자본: {prev_capital_after}
  - 활성 NPC: {active_npcs_with_relations}
  - 활성 적대자: {current_opponent}
  - 미회수 복선: {open_foreshadows}
  - 마지막 감정: {last_emotional_beat}
  - 마지막 위치: {last_location}

  ## 이번 대단원 목표 (Phase 0에서 설계한 것)
  - 목표 자본 범위: {target_capital_range}
  - 등장 예정 NPC: {new_npcs}
  - 적대자 변화: {opponent_change}
  - 회수 예정 복선: {foreshadows_to_resolve}
  - 패배 블록 위치: {defeat_block_positions}
```

**안티패턴 명시** (프롬프트 하단에 반드시 포함):
```
## 절대 금지 (이 규칙을 어기면 전량 재생성)
1. 성장률 3블록 이상 동일 값 금지 (±2%p 이상 변동 필수)
2. emotional_beat.type 2블록 연속 동일 금지
3. emotional_beat.intensity 3블록 연속 동일 값 금지
4. relationship_delta.before가 직전 블록의 after와 다르면 금지
5. callback이 "직전 블록의 X 성과가..." 패턴 2회 이상 금지
6. success_pattern 동일 표현 3회 이상 반복 금지
7. opponent.weakness_exploited 동일 표현 3회 이상 금지
8. deal_type 동일 값 3블록 이내 재등장 금지
9. location 동일 장소 3블록 이내 재등장 금지
10. duration 전량 동일 값 금지 (블록별 서사 규모에 맞게 3일~3개월)
```

### 2.4 Phase 2: 메타데이터 채움 (연속성 주입)

현재 Phase 3의 문제: 각 블록을 **독립적으로** 메타데이터 추출 → NPC 관계 리셋.

**수정**: 직전 5블록의 메타데이터를 컨텍스트로 주입.

```python
def extract_metadata(block, prev_blocks_meta):
    """
    prev_blocks_meta: 직전 5블록의 완성된 메타데이터
    → relationship_delta.before = prev[-1].relationship_delta.after
    → capital_before = prev[-1].genre_ext.capital_after
    → callback = prev[-1].foreshadow 중 회수 대상
    """

    # 이전 블록 상태 요약
    prev_state = {
        "capital": prev_blocks_meta[-1]["genre_ext"]["capital_after"],
        "active_npcs": [rd["target"] for rd in prev_blocks_meta[-1]["relationship_delta"]],
        "npc_relations": {
            rd["target"]: rd["after"]
            for rd in prev_blocks_meta[-1]["relationship_delta"]
        },
        "open_foreshadows": collect_unresolved_foreshadows(prev_blocks_meta),
        "last_location": prev_blocks_meta[-1]["location"]["place"],
        "last_emotion": prev_blocks_meta[-1]["emotional_beat"],
    }

    # LLM 호출 시 prev_state를 컨텍스트로 전달
    prompt = build_metadata_prompt(block, prev_state)
    # ...
```

### 2.5 Phase 3: Python 자동 검증

생성 완료 후 8대 결함 패턴을 자동 탐지하여 위반 블록만 재생성.

```python
def validate_treatment(blocks: list) -> list[dict]:
    """8대 결함 패턴 자동 탐지. 위반 목록 반환.
    NOTE: parse_capital()은 한국어 단위 파서 — "1조 2,000억" → 12000억 단위.
    구현: re.findall(r'(\d+)(조|억|만)', text) → 조*10000 + 억 + 만*0.0001
    """
    violations = []

    for i in range(1, len(blocks)):
        prev = blocks[i - 1]
        curr = blocks[i]

        # --- Pattern A: 자본 연속성 ---
        prev_after = parse_capital(prev["genre_ext"]["capital_after"])
        curr_before = parse_capital(curr["genre_ext"]["capital_before"])
        if prev_after != curr_before:
            violations.append({
                "block": i + 1, "pattern": "A",
                "severity": "P0",
                "msg": f"capital_before({curr_before}) != prev capital_after({prev_after})",
                "auto_fix": True  # capital_before를 prev_after로 강제 교체
            })

        # --- Pattern B: NPC before 리셋 ---
        if i > 1:
            prev_rd = {rd["target"]: rd["after"] for rd in prev["relationship_delta"]}
            for rd in curr["relationship_delta"]:
                if rd["target"] in prev_rd and rd["before"] != prev_rd[rd["target"]]:
                    violations.append({
                        "block": i + 1, "pattern": "B",
                        "severity": "P0",
                        "msg": f"NPC {rd['target']} before 리셋",
                        "auto_fix": True  # before를 prev.after로 교체
                    })

        # --- Pattern D: emotional_beat 연속 반복 ---
        if i >= 2:
            types_3 = [blocks[j]["emotional_beat"]["type"] for j in range(i-2, i+1)]
            if len(set(types_3)) == 1:
                violations.append({
                    "block": i + 1, "pattern": "D",
                    "severity": "P1",
                    "msg": f"emotional_beat.type 3연속 동일: {types_3[0]}",
                    "auto_fix": False  # 재생성 필요
                })

            intensities_3 = [blocks[j]["emotional_beat"]["intensity"] for j in range(i-2, i+1)]
            if len(set(intensities_3)) == 1:
                violations.append({
                    "block": i + 1, "pattern": "D",
                    "severity": "P1",
                    "msg": f"emotional_beat.intensity 3연속 동일: {intensities_3[0]}"
                })

        # --- Pattern E: deal_type 근접 반복 ---
        if i >= 2:
            deals_3 = [blocks[j]["genre_ext"].get("deal_type", "") for j in range(i-2, i+1)]
            if deals_3[0] == deals_3[2] and deals_3[0]:
                violations.append({
                    "block": i + 1, "pattern": "E",
                    "severity": "P1",
                    "msg": f"deal_type 3블록 이내 재등장: {deals_3[0]}"
                })

        # --- Pattern F: duration 전량 동일 ---
        # (전체 스캔 후 판정)

        # --- Pattern G: callback 템플릿 반복 ---
        if curr.get("callback"):
            cb = curr["callback"][0] if isinstance(curr["callback"], list) else str(curr["callback"])
            if "성과가 이번" in cb and "전환의 발판" in cb:
                violations.append({
                    "block": i + 1, "pattern": "G",
                    "severity": "P1",
                    "msg": "callback 템플릿 반복 (X 성과가 Y 전환의 발판)"
                })

    # --- Pattern C: 적대자 단일 고정 (전체 스캔) ---
    opponents = set()
    for b in blocks:
        opp = b.get("genre_ext", {}).get("opponent", {})
        if isinstance(opp, dict):
            opponents.add(opp.get("name", ""))
        elif isinstance(opp, str):
            opponents.add(opp)
    if len(opponents) <= 1:
        violations.append({
            "block": "전체", "pattern": "C",
            "severity": "P1",
            "msg": f"적대자 단일 고정: {opponents}"
        })

    # --- Pattern F: duration 전량 동일 (전체 스캔) ---
    durations = set(b.get("time_span", {}).get("duration", "") for b in blocks)
    if len(durations) <= 1:
        violations.append({
            "block": "전체", "pattern": "F",
            "severity": "P2",
            "msg": f"duration 전량 동일: {durations}"
        })

    # --- Pattern G 추가: success_pattern 반복 ---
    sp_counts = {}
    for b in blocks:
        sp = b.get("genre_ext", {}).get("success_pattern", "")
        if sp:
            sp_counts[sp] = sp_counts.get(sp, 0) + 1
    for sp, cnt in sp_counts.items():
        if cnt >= 3:
            violations.append({
                "block": "전체", "pattern": "G-success",
                "severity": "P1",
                "msg": f"success_pattern '{sp[:40]}...' {cnt}회 반복 (3회 이상)"
            })

    # --- 성장률 고정 탐지 ---
    growth_rates = []
    for i in range(len(blocks)):
        ge = blocks[i].get("genre_ext", {})
        before = parse_capital(ge.get("capital_before", "0"))
        after = parse_capital(ge.get("capital_after", "0"))
        if before > 0:
            growth_rates.append(round((after - before) / before * 100, 1))

    # 5블록 연속 동일 성장률 탐지
    for i in range(len(growth_rates) - 4):
        window = growth_rates[i:i+5]
        if len(set(window)) == 1:
            violations.append({
                "block": f"{i+1}~{i+5}", "pattern": "A-growth",
                "severity": "P0",
                "msg": f"성장률 5블록 연속 고정: {window[0]}%"
            })
            break  # 첫 발견만 보고

    # --- 패배 블록 부재 탐지 ---
    defeat_count = sum(
        1 for b in blocks
        if any(kw in b.get("content", {}).get("reward", "").lower()
               for kw in ["실패", "손실", "패배", "좌절", "하락"])
        or (parse_capital(b.get("genre_ext", {}).get("capital_delta", "+0")) < 0)
    )
    if defeat_count < 3:
        violations.append({
            "block": "전체", "pattern": "DEFEAT",
            "severity": "P1",
            "msg": f"패배/손실 블록 {defeat_count}개 (최소 7개 권장)"
        })

    return violations
```

### 2.6 Phase 4: 3-Pass 감리

자동 검증 후 LLM 감리 3회.

```
1차 감리: 전수조사 (6개 검사 항목 × 70블록)
  → P0/P1/P2 분류

2차 감리: 1차 결과 재검토
  → 오탐(FP) 제거, 누락 추가, 등급 조정
  → "설계 의도로 판단" → FP

3차 감리: 최종 확정
  → 테이블 출력, 통계, 건전성 점수
```

---

## 3. 필드별 품질 기준

### 3.1 수치 필드 (P0 — 위반 시 파이프라인 오류)

| 필드 | 규칙 | 검증 방법 |
|------|------|-----------|
| `genre_ext.capital_before` | N블록 = N-1블록의 `capital_after` | Python 자동 |
| `genre_ext.capital_delta` | `capital_after - capital_before` 정합 | Python 자동 |
| `genre_ext.capital_after` | 성장률 3블록 연속 동일 금지 | Python 자동 |
| 자본 감소 | 70블록 중 최소 3블록은 `capital_delta < 0` | Python 자동 |
| 성장률 범위 | -20% ~ +40%, 평균 5~15% | Python 경고 |

### 3.2 시간 필드

| 필드 | 규칙 | 비고 |
|------|------|------|
| `time_span.in_story_time` | 순방향 진행 (역행 금지) | Python 자동 |
| `time_span.duration` | 블록별 서사 규모 반영 (3일~3개월) | 전량 동일 금지 |
| 블록 간 시간 갭 | 후반부 과도 압축 금지 (최소 2주 간격) | 감리 확인 |

### 3.3 인물 필드

| 필드 | 규칙 | 비고 |
|------|------|------|
| `pov_character` | 전 블록 일관 | Python 자동 |
| `relationship_delta.before` | N블록 = N-1블록의 해당 NPC `after` | Python 자동 |
| `relationship_delta` NPC 수 | 대단원당 최소 3명, 전체 최소 8명 | 감리 확인 |
| NPC 등퇴장 | 20블록마다 최소 1명 추가 또는 교체 | 감리 확인 |
| `opponent.name` | 70블록에 최소 3개 세력 | 감리 확인 |
| `opponent.weakness_exploited` | 동일 표현 3회 이상 반복 금지 | Python 경고 |

### 3.4 서사 필드

| 필드 | 규칙 | 비고 |
|------|------|------|
| `emotional_beat.type` | 2블록 연속 동일 금지, 전체 6종+ 사용 | Python 자동 |
| `emotional_beat.intensity` | 3블록 연속 동일 금지, 1~10 전구간 활용 | Python 자동 |
| `tension_level` | 전구간 활용 (4~10), "조용한 블록" 최소 5개 | 감리 확인 |
| `foreshadow` | 장기 복선 5개+ (10블록 이상 지연 회수) | 감리 확인 |
| `callback` | 구체적 이전 사건 참조 (템플릿 반복 금지) | Python 경고 |
| `success_pattern` | 동일 표현 3회 이상 금지, "실패" 포함 7블록+ | 감리 확인 |
| `content.solution` | 섹터명만 교체한 템플릿 반복 금지 | 감리 확인 |

### 3.5 장르 확장 필드 (투자물)

| 필드 | 규칙 | 비고 |
|------|------|------|
| `deal_type` | 3블록 이내 재등장 금지, 10종+ 사용 | Python 경고 |
| `method` | 동일 표현 3회 이상 금지 | 감리 확인 |
| `investment_type` | 블록별 서사 맥락 반영 (주식/부동산/외환/협상 등) | 감리 확인 |
| `leverage_used` | 블록별 최소 1항목 차별화 | 감리 확인 |
| `business_sector` | 순환 가능하나 3블록 이내 재등장 금지 | Python 경고 |
| `success_pattern` | 최소 4종 사용 (실패/부분성공/피로스 포함), 동일 3회 금지 | Python 경고 |
| `location` | 3블록 이내 재등장 금지, 전체 8곳+ | Python 경고 |
| `risk_level` | "저"~"극고" 전구간 활용 | 감리 확인 |
| `historical_event` | 실제 시대 배경과 정합 (in_story_time 기준) | 감리 확인 |
| `time_pressure` | 블록별 고유 서술 (템플릿 반복 금지) | 감리 확인 |

### 3.6 빙의/회귀 확장 필드

| 필드 | 규칙 | 비고 |
|------|------|------|
| `death_flag.avoided` | 대단원별 최소 다른 위기 유형 | 감리 확인 |
| `death_flag.method` | 대단원별 최소 다른 회피 방식 | 감리 확인 |
| `regression_hint.slip_up` | 10종+ 사용, 에스컬레이션 필수 | 감리 확인 |
| `regression_hint.suspicion_from` | 최소 3개 세력/인물로 분산 | 감리 확인 |
| `butterfly_effect` | 블록별 고유 (섹터명만 교체 금지) | 감리 확인 |
| `execution_doctrine` | 대단원별 변화 (위기 시 전략 전환 등) | 감리 확인 |

---

## 4. 파이프라인 소비 지점과의 정합

Treatment의 각 필드가 파이프라인 어디서 소비되는지 명시. 이 필드들이 부실하면 해당 검사에서 경고/REJECT이 발생한다.

| Treatment 필드 | 소비 지점 | 검사 내용 |
|----------------|-----------|-----------|
| `genre_ext.capital_*` | `_format_block_numeric_targets()` → CW self-critique | 블록 목표 자본 달성 여부 |
| `genre_ext.capital_*` | `_check_arc_vs_block_targets()` (NS-3-B) | Arc 결과 vs Treatment 목표 ±30% 괴리 |
| `genre_ext.*` | `_build_block_event_guard()` | 블록 경계 이벤트 침범 방지 |
| `content.event_villain` | Arc 생성 → Blueprint → 원고 | 빌런 행동의 서사적 기반 |
| `content.solution` | Arc 생성 → Blueprint → 원고 | 해결 방식의 서사적 기반 |
| `emotional_beat` | Director 심사 (NC-3 체크리스트) | 감정선 자연스러움 평가 |
| `relationship_delta` | NPC 연속성 검사 | NPC 관계 변화 추적 |
| `time_span` | Timeline 연속성 (NS-4) | 시간 역행/압축 감지 |
| `foreshadow/callback` | Arc 복선 관리 | 복선 심기/회수 추적 |
| `regression_ext` | 빙의/회귀 정합성 검사 | 회귀자 설정 일관성 |

---

## 5. 골든 블록 예시

### 5.1 좋은 블록 (변주와 긴장감 존재)

```json
{
  "block_id": "Block 23",
  "title": "우한의 겨울 — 공급망 붕괴",
  "content": {
    "context": "2020년 1월, 중국 우한발 팬데믹이 전 세계 공급망을 마비시켰다. 한도준의 물류 자회사 3개 중 2개가 항만 봉쇄로 화물을 받지 못하는 상황. 이사회는 긴급 대책 회의를 소집했다.",
    "event_villain": "글로벌 물류 연합이 한도준의 독점 노선을 빼앗으려 각국 정부에 로비를 시작했다. 동시에 내부 배신자 최부장이 경쟁사에 노선 데이터를 유출. 자금 조달선마저 은행들이 회수 통보.",
    "solution": "한도준은 팬데믹을 예견하고 선제 확보한 방역 물자를 동남아 4개국에 무상 제공하여 정치적 우군을 만들었다. 최부장의 유출은 미끼 데이터였음이 밝혀졌다. 은행 자금 회수는 자체 유동성으로 버텼지만 순손실 800억을 감수해야 했다.",
    "reward": "물류 노선 3개 중 2개를 사수했지만 1개는 경쟁사에 넘어갔다. 자본은 1.2조에서 1.12조로 감소. 그러나 동남아 정부와의 신뢰로 향후 독점 입찰 자격을 확보했다."
  },
  "stakes": "물류 자회사 3개 전량 상실 시 핵심 사업 기반 붕괴. 은행 자금 회수가 연쇄되면 유동성 위기로 전체 그룹 매각 위험",
  "tension_level": 9,
  "power_shift": {
    "protagonist": "한도준은 순손실 800억을 감수하면서 전략적 후퇴를 단행. 단기 패배를 인정했지만 장기 포석을 깔았다.",
    "antagonist": "글로벌 물류 연합이 노선 1개를 탈취하며 첫 실질적 승리를 거둠. 내부 배신자 최부장은 미끼에 걸려 신뢰를 잃었다."
  },
  "relationship_delta": [
    {
      "target": "박재현 CFO",
      "before": "팬데믹 대비 자금 운용에 대해 '과잉 방어'라며 불만을 표출하던 상태",
      "after": "유동성 위기를 자체 자금으로 넘기자 한도준의 판단력을 인정. '다음엔 미리 알려달라'며 신뢰 회복 조짐"
    },
    {
      "target": "최부장 (내부 배신자)",
      "before": "5년간 신뢰받던 물류 담당 임원",
      "after": "미끼 데이터 유출이 밝혀져 경영진에서 퇴출. 경쟁사 측에서도 불신당하는 양쪽 모두에서 버림받는 처지"
    },
    {
      "target": "닌 쏜차이 (태국 교통부 차관)",
      "before": "한도준을 '외국 자본의 침략자'로 경계하던 관료",
      "after": "방역 물자 제공에 감사하며 물류 입찰 자격 심사에서 우호적 입장으로 전환"
    }
  ],
  "foreshadow": [
    "동남아 정부와의 신뢰가 Block 31에서 독점 입찰 수주로 연결될 것",
    "최부장의 퇴출 소식을 들은 다른 임원 중 한 명이 동요하기 시작할 것 (Block 26)"
  ],
  "callback": [
    "Block 15에서 한도준이 '최부장에게 너무 많은 권한을 줬다'고 독백한 것이 이번 배신으로 현실화",
    "Block 18에서 선제 확보한 방역 물자 500억 분이 이번 위기의 핵심 카드로 활용"
  ],
  "emotional_beat": {
    "type": "pyrrhic_victory",
    "intensity": 7
  },
  "pov_character": "한도준",
  "location": {
    "place": "인천 송도 물류통합관제실",
    "type": "위기 대응 사령부"
  },
  "time_span": {
    "duration": "6주",
    "in_story_time": "2020년 1월~2월"
  },
  "genre_ext": {
    "capital_before": "1조 2,000억",
    "capital_after": "1조 1,200억",
    "capital_delta": "-800억",
    "profit_loss": "물류 노선 1개 상실 + 방역 물자 무상 제공으로 순손실",
    "method": "전략적 후퇴 — 단기 손실 감수 + 정치적 신뢰 자산 확보",
    "deal_type": "정부 간 물자 공여 계약",
    "leverage_used": ["선제 확보 방역 물자", "미끼 데이터 역이용", "동남아 정치 네트워크"],
    "opponent": {
      "name": "글로벌 물류 연합 (DHL-Maersk 컨소시엄)",
      "type": "다국적 기업 연합",
      "weakness_exploited": "현지 정부와의 관계 부재 — 자본력만으로 노선 확보 시도"
    },
    "risk_level": "극고",
    "business_sector": "물류",
    "global_partner": {
      "name": "방콕 로열 로지스틱스",
      "cadence": "위기 시 긴급 공조",
      "objective": "동남아 노선 공동 방어"
    }
  }
}
```

**이 블록이 좋은 이유**:
- `capital_delta`가 **마이너스** (실질적 패배/손실)
- `emotional_beat.type`이 "pyrrhic_victory" (기계적 4종 순환 탈피)
- NPC 3명 등장 (2명 고정 탈피), 1명은 이번 블록에서 퇴출
- `callback`이 구체적 블록 번호 참조 (템플릿 탈피)
- `foreshadow`가 10블록+ 미래 참조 (장기 복선)
- `duration`이 "6주" (전량 "7일" 탈피)
- `method`가 고유한 전략 서술 (템플릿 탈피)
- `opponent`가 구체적 기업명 (단일 "연합" 탈피)

### 5.2 나쁜 블록 (8대 결함 패턴 전량 포함)

```json
{
  "block_id": "Block 23",
  "title": "Block 23 — 물류 확장 라운드 3",
  "content": {
    "context": "한도준은 물류 분야에서 새로운 기회를 포착했다. 기존 성과를 바탕으로 추가 확장을 계획했다.",
    "event_villain": "경쟁 물류 연합이 한도준의 확장을 저지하기 위해 조달 계약을 방해했다.",
    "solution": "한도준은 물류 수익구조 정비 + 계약 단계화를 통해 위기를 극복하고 전략 제휴를 체결했다.",
    "reward": "물류 확장에 성공하며 자본이 증가했다."
  },
  "stakes": "물류 사업 기반이 흔들릴 위험",
  "tension_level": 8,
  "power_shift": {
    "protagonist": "한도준은 물류 전략적 우위를 확보했다.",
    "antagonist": "경쟁 물류 연합의 방어 손실 3."
  },
  "relationship_delta": [
    {
      "target": "이은호 인프라본부장",
      "before": "이은호 인프라본부장와의 협력은 제한적이었다.",
      "after": "이은호 인프라본부장가 사업확장 구간의 핵심 실행 파트너가 되었다."
    },
    {
      "target": "한지민 정책협력실장",
      "before": "한지민 정책협력실장은 조건부 검토 입장이었다.",
      "after": "한지민 정책협력실장이 리스크 재무 통합안을 공동 주도했다."
    }
  ],
  "foreshadow": ["다음 블록에서는 에너지관리 관련 변수가 발생할 것이다."],
  "callback": ["직전 블록의 전력망 성과가 이번 물류 전환의 발판이 되었다."],
  "emotional_beat": { "type": "breakthrough", "intensity": 9 },
  "time_span": { "duration": "7일", "in_story_time": "2016년 5월" },
  "genre_ext": {
    "capital_before": "2,848억",
    "capital_after": "3,161억",
    "capital_delta": "+313억",
    "method": "물류 수익구조 정비 + 계약 단계화",
    "deal_type": "공동 투자 계약",
    "opponent": {
      "name": "정경 카르텔 연합",
      "weakness_exploited": "조달 의사결정 지연"
    },
    "risk_level": "중상"
  }
}
```

**이 블록이 나쁜 이유**:
- 모든 감사 결함 패턴(A~H) 해당
- `method`가 "X 수익구조 정비 + 계약 단계화" 템플릿
- NPC 2명, before 리셋, 조사격 오류 ("본부장와의")
- `callback`이 "직전 블록의 X 성과가 Y 전환의 발판" 템플릿
- `foreshadow`가 즉시 소비 (장기 복선 0)
- `duration` "7일", `opponent` 동일, `emotional_beat` 순환 패턴

---

## 6. 체크리스트 (생성 후 자가 점검)

### P0 체크 (자동화 필수 — 위반 시 파이프라인 오류)
- [ ] `capital_before(N) == capital_after(N-1)` 전 블록 정합
- [ ] `capital_delta == capital_after - capital_before` 전 블록 정합
- [ ] `relationship_delta.before(N) == relationship_delta.after(N-1)` NPC별 연속
- [ ] `time_span.in_story_time` 순방향 진행 (역행 0건)
- [ ] `pov_character` 전 블록 일관

### P1 체크 (감리 확인 — 위반 시 서사 품질 저하)
- [ ] 적대자 최소 3세력 (70블록 기준)
- [ ] NPC 최소 8명 (등퇴장 포함)
- [ ] 패배/손실 블록 최소 7개 (`capital_delta < 0` 또는 서사적 후퇴)
- [ ] `emotional_beat.type` 6종 이상 사용
- [ ] `emotional_beat.intensity` 1~10 전구간 활용
- [ ] `tension_level` "조용한 블록" (4~6) 최소 5개
- [ ] `callback`이 구체적 사건/블록 참조 (템플릿 반복 금지)
- [ ] `success_pattern` 최소 4종 사용 (실패/부분성공/피로스 포함)
- [ ] `foreshadow` 장기 복선 5개+ (10블록+ 지연 회수)
- [ ] `deal_type` 3블록 이내 재등장 금지, 10종+ 사용
- [ ] 성장률 3블록 연속 동일 금지

### P2 체크 (품질 개선 — 권장)
- [ ] `duration` 블록별 차별화 (3일~3개월)
- [ ] `location` 8곳+, 3블록 이내 재등장 금지
- [ ] `method` 블록별 고유 전략 서술
- [ ] `leverage_used` 블록별 최소 1항목 차별화
- [ ] (빙의) `death_flag` 대단원별 다른 위기 유형
- [ ] (빙의) `regression_hint.slip_up` 10종+, 에스컬레이션

---

## 7. 기존 도구 개선 권고 (`treatment_builder.py`)

### 즉시 적용 가능 (코드 변경 최소)

1. **Phase 1 분할**: `total_blocks=60` → 대단원별 10블록씩 6회 호출
2. **안티패턴 프롬프트 추가**: 섹션 2.3의 "절대 금지" 10개 항목을 Phase 2 프롬프트에 삽입
3. **Phase 3 컨텍스트 주입**: `_extract_block_metadata()`에 `prev_blocks[-5:]` 전달
4. **자본 연속성 강제**: Phase 3 후 Python으로 `capital_before` 자동 교정
5. **NPC before 자동 교정**: Phase 3 후 Python으로 `before = prev.after` 강제

### 중기 개선 (구조 변경)

6. **Phase 0 추가**: 대단원 아크 설계 LLM 호출 1회
7. **검증 루프 추가**: Phase 3 후 자동 검증 → 위반 블록만 재생성
8. **골든 예시 주입**: Few-shot으로 섹션 5.1의 좋은 블록 예시 1~2개 삽입

---

## 부록 A: 감정 비트 권장 유형 (20종+)

기존 4종(`resolve/pressure/breakthrough/victory`)을 탈피하기 위한 확장 목록:

| 유형 | 설명 | intensity 범위 |
|------|------|---------------|
| `triumph` | 완전한 승리 | 8~10 |
| `pyrrhic_victory` | 대가를 치른 승리 | 5~7 |
| `defeat` | 실질적 패배 | 2~4 |
| `betrayal` | 배신당함 | 7~9 |
| `revelation` | 중대한 사실 발견 | 6~9 |
| `sacrifice` | 희생적 선택 | 5~8 |
| `isolation` | 고립/고독 | 3~5 |
| `reconciliation` | 화해/관계 회복 | 5~7 |
| `escalation` | 위기 고조 | 7~9 |
| `respite` | 숨고르기/평화 | 2~4 |
| `moral_dilemma` | 윤리적 갈등 | 6~8 |
| `confrontation` | 정면 대결 | 8~10 |
| `realization` | 깨달음/자기성찰 | 4~6 |
| `humiliation` | 굴욕 | 3~6 |
| `alliance` | 새로운 동맹 | 5~7 |
| `deception` | 속임수 성공/발각 | 6~8 |
| `transformation` | 캐릭터 변화 | 5~8 |
| `countdown` | 시간 제한 긴장 | 8~10 |
| `aftermath` | 사건 후유증 | 3~5 |
| `foreshadowing` | 불길한 전조 | 4~6 |

---

## 부록 B: 투자물 거래 유형 권장 (15종+)

기존 5종 순환을 탈피하기 위한 확장 목록:

| 유형 | 설명 | 적합 자본 규모 |
|------|------|--------------|
| 주식 장외 매입 | 비상장 주식 직접 매수 | 50억~500억 |
| 적대적 M&A | 경영권 인수 공격 | 1,000억+ |
| 우호적 M&A | 합의 인수 | 500억+ |
| 조인트 벤처 | 합작 법인 설립 | 100억~5,000억 |
| 컨소시엄 입찰 | 대형 프로젝트 공동 응찰 | 5,000억+ |
| 부실 자산 인수 | 파산/부실 기업 저가 매입 | 100억~3,000억 |
| IPO/공모 | 자회사 상장 | 1,000억+ |
| 사모펀드 조성 | 투자 펀드 결성 | 500억~1조 |
| 기술 라이선싱 | 특허/기술 사용권 거래 | 50억~500억 |
| 정부 특허권 | 규제 관련 독점 허가 | 상황별 |
| 공급망 수직 통합 | 원재료→완제품 체인 구축 | 300억~5,000억 |
| 자산유동화(ABS) | 미래 수익 증권화 | 500억+ |
| 크로스보더 스왑 | 해외 자산 교환 | 1,000억+ |
| 전환사채(CB) 발행 | 조건부 지분 전환 채권 | 200억~2,000억 |
| 워런트 행사 | 주식 매입 옵션 실행 | 상황별 |

---

## 8. 코덱스 강제 수동 처리 오더 (Anti-Shortcut Harness)

> **배경**: 코덱스(LLM)는 긴 지시를 받으면 핵심 키워드만 읽고 나머지를 "안전한 패턴"으로 채우는 경향이 있다.
> 아래 오더는 LLM이 각 단계를 **증명 가능한 방식으로 수동 처리**하도록 강제한다.
> 프롬프트에 이 오더를 통째로 삽입하거나, 단계별로 분리 호출한다.

### 8.1 Step-by-Step 강제 출력 프로토콜

프롬프트 끝에 아래를 삽입:

```
## 출력 프로토콜 (이 규칙을 건너뛰면 전량 재작업)

블록을 생성하기 전에, 반드시 아래 "사전 선언"을 먼저 출력하라.
사전 선언 없이 JSON을 출력하면 무효 처리된다.

### 사전 선언 (블록 생성 전 필수)
각 블록마다 JSON 출력 **직전에** 아래 5개 항목을 자연어로 서술하라:

1. **이전 블록 잔향**: 직전 블록에서 무슨 일이 일어났는가? 주인공의 감정 상태는?
   관계 변화는? 자본은 얼마였나? (첫 블록이면 "첫 블록" 명시)
2. **이번 블록의 고유 사건**: 이 블록에서만 일어나는 일은 무엇인가?
   이전/이후 블록에서는 절대 반복되지 않는 고유 이벤트를 1문장으로 서술하라.
3. **차별화 증명**: 직전 블록과 비교하여 아래 5개 필드가 어떻게 다른지 명시하라.
   - emotional_beat.type: [직전] → [이번] (다른 이유)
   - deal_type: [직전] → [이번] (다른 이유)
   - opponent 또는 weakness: [직전] → [이번]
   - location: [직전] → [이번]
   - duration: [직전] → [이번]
   5개 중 3개 이상이 직전과 동일하면 해당 블록을 다시 구상하라.
4. **자본 계산 과정**: capital_before = [직전 capital_after] = [구체적 숫자].
   이번 블록 사건으로 인한 변동: [서사적 근거]. capital_after = [계산식].
5. **NPC 관계 이월**: 이번 블록에 등장하는 각 NPC의 before를
   직전 블록 after에서 그대로 복사하여 인용하라. 새 NPC면 "신규" 명시.

### 사전 선언 예시 (이렇게 쓰라)

**Block 24 사전 선언:**
1. 이전 블록 잔향: Block 23에서 한도준은 물류 노선 1개를 잃고 800억 순손실.
   자본 1조 1,200억. 감정은 pyrrhic_victory(7). 박재현 CFO와 신뢰 회복 조짐.
2. 이번 블록의 고유 사건: 잃어버린 노선을 탈환하기 위해 경쟁사 내부 불만 세력과
   비밀 접촉. 이전에 없던 "적진 내 아군 만들기" 전략.
3. 차별화 증명:
   - emotional_beat: pyrrhic_victory(7) → deception(6). 이유: 비밀 공작 분위기
   - deal_type: 정부간 물자 공여 → 주식 장외 매입. 이유: 경쟁사 지분 은밀 매수
   - opponent: 글로벌 물류 연합 → 연합 내부 강경파(신규 분화). 이유: 연합 분열 유도
   - location: 인천 송도 → 상하이 비밀 회동장소. 이유: 적진 침투
   - duration: 6주 → 3개월. 이유: 비밀 접촉은 시간이 걸림
4. 자본 계산: capital_before = 1조 1,200억 (Block 23 after).
   비밀 지분 매수 200억 지출 + 기존 사업 운영 수익 150억 = net -50억.
   capital_after = 1조 1,150억.
5. NPC 관계 이월:
   - 박재현 CFO: before = "한도준의 판단력을 인정. 다음엔 미리 알려달라며
     신뢰 회복 조짐" (Block 23 after 그대로)
   - 왕리 (경쟁사 내부자): 신규 NPC. before = "없음 (첫 등장)"
```

### 8.2 블록 간 차이 행렬 강제 (10블록 배치용)

10블록을 한 번에 생성할 때, JSON 출력 **후에** 차이 행렬을 출력하도록 강제:

```
## 차이 행렬 (10블록 생성 후 필수 출력)

10개 블록을 모두 작성한 뒤, 아래 행렬을 채워라.
행렬을 출력하지 않으면 전량 무효다.

| Block | beat_type | intensity | tension | deal_type | opponent | location | duration | capital_delta | 성장률 | success |
|-------|-----------|-----------|---------|-----------|----------|----------|----------|---------------|--------|---------|
| N+1   | ?         | ?         | ?       | ?         | ?        | ?        | ?        | ?             | ?%     | ?       |
| N+2   | ?         | ?         | ?       | ?         | ?        | ?        | ?        | ?             | ?%     | ?       |
| ...   | ...       | ...       | ...     | ...       | ...      | ...      | ...      | ...           | ...    | ...     |
| N+10  | ?         | ?         | ?       | ?         | ?        | ?        | ?        | ?             | ?%     | ?       |

### 자가 검증 (행렬 출력 후 수행)
행렬을 보고 아래 질문에 답하라. 하나라도 "예"이면 해당 블록을 수정하라.

1. beat_type 열에 2연속 동일 값이 있는가? → 있으면 수정
2. intensity 열에 3연속 동일 값이 있는가? → 있으면 수정
3. deal_type 열에 3블록 이내 동일 값이 있는가? → 있으면 수정
4. opponent 열이 전부 동일한가? → 그러면 최소 2개 분화
5. location 열에 3블록 이내 동일 값이 있는가? → 있으면 수정
6. duration 열이 전부 동일한가? → 그러면 최소 3종으로 분화
7. 성장률 열에 3연속 ±1%p 이내 값이 있는가? → 있으면 수정
8. success 열이 전부 동일한가? → 그러면 최소 2개 "실패" 또는 "부분성공"
9. capital_delta 열이 전부 양수인가? → 그러면 최소 1개 음수 필수
10. 전체적으로 "이 10블록이 전부 같은 이야기처럼 보이는가?" → 보이면 재설계
```

### 8.3 NPC 생존 추적표 강제

```
## NPC 추적표 (대단원 종료 시 필수 출력)

10블록 생성 후, 현재 활성 NPC 전원의 상태를 테이블로 출력하라.
이 테이블의 "현재 관계"가 다음 대단원 첫 블록의 relationship_delta.before가 된다.

| NPC 이름 | 등장 블록 | 마지막 활동 | 현재 관계 (= 다음 블록 before) | 다음 예정 |
|----------|-----------|-------------|-------------------------------|-----------|
| 박재현   | Block 5   | Block 24    | "한도준의 판단력을 인정..."     | Block 25+ |
| 왕리     | Block 24  | Block 24    | "비밀 접촉 단계, 신뢰 미형성"  | Block 25  |
| (퇴장)최부장 | Block 3 | Block 23  | 퇴출됨                        | -         |

### 검증
- 활성 NPC가 2명 이하이면: 다음 대단원에서 최소 2명 추가 필수
- 10블록 동안 NPC 변동(추가/퇴장/배신)이 0건이면: 재설계
- "현재 관계" 열에 동일 문장이 2명 이상이면: 차별화 필수
```

### 8.4 복선 원장 강제

```
## 복선 원장 (대단원 종료 시 필수 출력)

현재까지 심은 모든 foreshadow와 회수 상태를 원장으로 관리하라.
원장을 출력하지 않으면 다음 대단원 생성 불가.

| # | 복선 내용 | 심기 블록 | 목표 회수 블록 | 실제 회수 블록 | 상태 |
|---|-----------|-----------|---------------|---------------|------|
| 1 | "최부장의 퇴출 후 다른 임원 동요" | Block 23 | Block 26 | - | OPEN |
| 2 | "동남아 정부 신뢰 → 독점 입찰" | Block 23 | Block 31 | - | OPEN |
| 3 | "초기 투자 실패의 교훈" | Block 3  | Block 12 | Block 12 | CLOSED |

### 검증
- OPEN 복선이 20개 이상 누적되면: 5개 이상을 이번 대단원에서 회수 필수
- 심기 후 20블록 이상 미회수 복선이 있으면: 즉시 회수 또는 "포기됨" 명시
- 전체 복선 중 "장기 복선" (심기~회수 간격 10블록 이상)이 5개 미만이면: 추가 필수
```

### 8.5 자본 곡선 시각화 강제

```
## 자본 곡선 (대단원 종료 시 필수 출력)

10블록의 자본 변동을 ASCII 차트로 그려라.
상승만 있으면 재설계. 최소 1개 하락 필수.

Block N+1:  ████████████████ 1,150억 (-4.5%)
Block N+2:  █████████████████ 1,230억 (+7.0%)
Block N+3:  ████████████████████ 1,400억 (+13.8%)
Block N+4:  ██████████████████ 1,280억 (-8.6%)  ← 패배 블록
Block N+5:  ██████████████████ 1,310억 (+2.3%)
...

### 검증
- 10블록 연속 상승이면: 최소 1블록 하락으로 수정
- 성장률이 5블록 이상 ±2%p 이내로 평탄하면: 변동폭 확대
- 최종 자본이 Phase 0에서 설계한 목표 범위를 ±20% 이상 벗어나면: 조정
```

### 8.6 적대자 교체 체크포인트

```
## 적대자 상태 (20블록마다 필수 출력)

현재 적대자의 상태를 점검하고, 교체/분화 여부를 결정하라.
동일 적대자가 20블록 이상 지속되면 강제 분화.

현재 적대자: [이름]
- 활동 기간: Block [X] ~ Block [Y] ([Z]블록)
- 주인공에게 준 실질적 타격 횟수: [N]회
- 약점 노출 횟수: [N]종 (3종 이하이면 추가 필요)

### 20블록 초과 시 필수 조치 (택 1)
□ 적대자 분열: 내부 분화로 2개 세력 발생
□ 적대자 교체: 기존 세력 퇴장/약화, 신규 세력 등장
□ 적대자 진화: 동일 세력이 전략/목표/약점을 근본적으로 변경
□ 적대자 동맹: 기존 세력 + 새로운 세력 합류

선택한 조치: [___]
적용 블록: Block [___]
```

### 8.7 프롬프트 주입 종합 템플릿

위 8.1~8.6을 하나로 묶은 **실전 프롬프트 미리 끝 부분에 붙여넣기용**:

```
═══════════════════════════════════════════════════
  ANTI-SHORTCUT HARNESS — 아래를 건너뛰면 전량 무효
═══════════════════════════════════════════════════

당신은 지금부터 매 블록마다 "사전 선언 → JSON → 차이 행렬" 순서로 출력한다.
순서가 틀리면 전량 재작업이다. 지름길은 없다.

[STEP 1] 사전 선언 5항목 (섹션 8.1) — 블록마다 필수
[STEP 2] 블록 JSON 출력
[STEP 3] 10블록 완료 후 차이 행렬 (섹션 8.2) + 자가 검증 10문항 답변
[STEP 4] NPC 추적표 (섹션 8.3) — 대단원 종료 시
[STEP 5] 복선 원장 (섹션 8.4) — 대단원 종료 시
[STEP 6] 자본 곡선 ASCII (섹션 8.5) — 대단원 종료 시
[STEP 7] 적대자 상태 (섹션 8.6) — 20블록마다

하나라도 빠지면:
→ "HARNESS VIOLATION: [누락 항목]" 을 출력하고 해당 구간을 재작성하라.
→ 절대로 HARNESS VIOLATION을 무시하고 다음 블록으로 넘어가지 마라.

이 하네스의 목적: 당신이 "핵심만 읽고 나머지를 복붙"하는 것을 물리적으로
불가능하게 만드는 것이다. 매 블록마다 직전 블록과의 차이를 증명해야 하므로,
템플릿 복사가 구조적으로 차단된다.
═══════════════════════════════════════════════════
```

---

## 9. Gemini 적용 가이드 (저지능 모델 호환)

> Gemini Flash/Pro 등 지능 층위가 낮은 모델에서 하네스를 적용할 때의 조정 사항.
> 핵심 원칙: **한 번에 적게 시키고, 검증은 별도 호출로 분리한다.**

### 9.1 배치 크기 축소

| 항목 | Opus/Sonnet | Gemini Flash | Gemini Pro |
|------|-------------|--------------|------------|
| 블록 생성 배치 | 10블록 | **3블록** | **5블록** |
| 사전 선언 항목 | 5개 전부 | **3개 필수** (1,4,5) | 5개 전부 |
| 차이 행렬 | 10블록 후 1회 | **3블록마다 1회** | 5블록마다 1회 |
| 복선 원장 항목 | 무제한 | **최대 10개 유지** | 최대 15개 |

**Gemini Flash 최적 구성**: 3블록 생성 → 차이 행렬 → 다음 3블록. 이렇게 하면 컨텍스트 내에서 패턴 수렴이 시작되기 전에 끊는다.

### 9.2 사전 선언 축소판 (Gemini Flash용 — 3항목)

```
## 사전 선언 (블록마다 JSON 앞에 필수)

1. **직전 상태 인용**: 직전 블록의 capital_after, emotional_beat,
   각 NPC의 after 텍스트를 그대로 복사하라.
2. **자본 계산**: capital_before = [직전 capital_after].
   변동 근거 = [1문장]. capital_after = [계산식].
3. **차별화 1줄**: 직전 블록과 이번 블록의 가장 큰 차이를 1문장으로 서술하라.
```

5항목을 3항목으로 줄이되, 가장 중요한 것(자본 연속성, NPC 이월, 차별화)만 남긴다.
"이번 블록의 고유 사건"과 "5필드 차별화 증명"은 차이 행렬에서 사후 검증한다.

### 9.3 검증 분리 호출 (핵심)

Gemini에서는 **생성과 검증을 같은 호출에 넣지 않는다**. 생성 품질이 떨어진다.

```
[호출 1] 생성: "Block N~N+2를 만들어라" + 사전 선언 3항목
  → 블록 3개 JSON 출력

[호출 2] 검증: "아래 3블록의 차이 행렬을 채우고 자가 검증 10문항에 답하라"
  → 차이 행렬 + 위반 사항 목록

[호출 3] 수정 (위반 시만): "Block N+1의 deal_type을 변경하고 재출력하라"
  → 수정된 블록 1개만 재생성

[Python] 자동 교정: capital_before 강제, NPC before 강제, duration 중복 체크
```

### 9.4 한국어 단위 계산 보호

Gemini는 "1조 2,000억 + 800억 = ?" 같은 한국어 단위 혼합 산술에서 오류가 빈발.

**대책: 억 단위 정수로 통일**

```
## 자본 표기 규칙 (Gemini 전용)

모든 자본을 "억" 단위 정수로 표기하라. 조/만 혼용 금지.
- ✅ capital_before: "12000억"  (= 1조 2,000억)
- ❌ capital_before: "1조 2,000억"
- ❌ capital_before: "1.2조"

capital_delta 계산 예시:
- capital_before: "12000억"
- capital_after: "11200억"
- capital_delta: "-800억"
- 검증: 11200 - 12000 = -800 ✅
```

생성 완료 후 Python에서 "12000억" → "1조 2,000억" 으로 자동 변환하면 된다.

### 9.5 복선 관리 축소판

Gemini Flash는 OPEN 복선 10개를 넘으면 누락이 시작된다.

```
## 복선 관리 규칙 (Gemini 전용)

1. OPEN 복선은 최대 10개만 유지한다.
2. 10개 초과 시, 가장 오래된 OPEN 복선을 이번 블록에서 회수하거나 "폐기"로 변경한다.
3. 복선 원장은 대단원(10블록)이 아니라 **배치(3블록)**마다 출력한다.
4. 원장 형식을 단순화한다:

| # | 내용 (20자 이내) | 심기 | 회수 예정 | 상태 |
|---|-----------------|------|----------|------|
| 1 | 임원 동요 | 23 | 26 | OPEN |
| 2 | 동남아 입찰 | 23 | 31 | OPEN |
```

### 9.6 Gemini 프롬프트 종합 템플릿

```
═══════════════════════════════════════════════════
  TREATMENT BLOCK 생성 (Gemini Flash/Pro 전용)
═══════════════════════════════════════════════════

당신은 웹소설 treatment 블록을 3개씩 생성한다.
반드시 아래 순서를 지켜라. 순서를 어기면 전량 무효.

[A] 컨텍스트 수신
  - 직전 3블록 JSON (제공됨)
  - NPC 추적표 (제공됨)
  - 복선 원장 (제공됨)
  - 이번 배치 목표 (대단원 아크에서 발췌)

[B] 사전 선언 3항목 (블록마다)
  1. 직전 상태 인용 (capital_after, beat, NPC after 복사)
  2. 자본 계산 (before = 직전 after, 변동 근거, after = 계산식)
  3. 차별화 1줄

[C] 블록 JSON 출력 (3개)

[D] 차이 행렬 + 자가 검증 (3블록 분량)

[E] 복선 원장 업데이트

## 자본 규칙
- 전부 "억" 단위 정수 (조/만 금지)
- capital_before = 직전 capital_after (예외 없음)

## 절대 금지
- beat_type 2연속 동일
- deal_type 3블록 이내 재등장
- 성장률 3연속 동일 (±2%p 이상 변동)
- NPC before ≠ 직전 after
- callback "성과가...발판" 패턴
- duration 전부 동일

## 하네스 위반 시
→ "VIOLATION: [항목]" 출력 후 해당 블록 재작성
→ 절대로 무시하고 다음으로 넘어가지 마라
═══════════════════════════════════════════════════
```

### 9.7 실전 운용 플로우 (Python 오케스트레이션)

Gemini 단독으로는 하네스를 100% 준수하기 어렵다. **Python이 오케스트레이션**한다.

```python
def generate_treatment_gemini(bible, arc_design, total_blocks=70):
    """Gemini Flash/Pro용 treatment 생성 오케스트레이터"""

    blocks = []
    npc_tracker = {}    # {name: last_after_text}
    foreshadow_ledger = []  # [{content, plant_block, target_block, status}]
    batch_size = 3  # Gemini Flash: 3, Pro: 5

    for batch_start in range(0, total_blocks, batch_size):
        batch_end = min(batch_start + batch_size, total_blocks)

        # --- 호출 1: 생성 ---
        prev_context = format_prev_blocks(blocks[-3:])  # 직전 3블록
        npc_table = format_npc_tracker(npc_tracker)
        foreshadow_table = format_foreshadow_ledger(foreshadow_ledger)
        arc_goals = extract_batch_goals(arc_design, batch_start, batch_end)

        new_blocks = call_gemini_generate(
            prev_context, npc_table, foreshadow_table, arc_goals,
            batch_start + 1, batch_end
        )

        # --- Python 자동 교정 (LLM 불신 영역) ---
        for i, block in enumerate(new_blocks):
            global_idx = batch_start + i

            # 자본 연속성 강제
            if global_idx > 0:
                prev_after = blocks[-1]["genre_ext"]["capital_after"]
                block["genre_ext"]["capital_before"] = prev_after
                # delta 재계산
                before_val = parse_capital(prev_after)
                after_val = parse_capital(block["genre_ext"]["capital_after"])
                block["genre_ext"]["capital_delta"] = format_capital(after_val - before_val)

            # NPC before 강제
            for rd in block.get("relationship_delta", []):
                if rd["target"] in npc_tracker:
                    rd["before"] = npc_tracker[rd["target"]]

            blocks.append(block)

            # NPC tracker 갱신
            for rd in block.get("relationship_delta", []):
                npc_tracker[rd["target"]] = rd["after"]

        # --- 호출 2: 검증 (분리 호출) ---
        violations = call_gemini_validate(new_blocks)

        # --- Python 자동 검증 (LLM 검증도 불신) ---
        py_violations = validate_batch(blocks, batch_start, batch_end)

        # --- 호출 3: 수정 (위반 시만) ---
        all_violations = merge_violations(violations, py_violations)
        if all_violations:
            for v in all_violations:
                if not v.get("auto_fixed"):
                    fixed = call_gemini_fix(blocks[v["block_idx"]], v)
                    blocks[v["block_idx"]] = fixed

        # 복선 원장 갱신
        update_foreshadow_ledger(foreshadow_ledger, new_blocks, batch_start)

    return blocks
```

**핵심 설계 원칙**:
- **LLM은 창작만, Python은 수치/연속성 강제** — 대원칙 1과 동일 사상
- **생성/검증/수정 3단 분리 호출** — 한 번에 시키면 Gemini가 검증을 건너뜀
- **Python이 최종 교정권** — `capital_before`, `NPC before`, `delta` 는 LLM 출력을 덮어씀

---

## 10. 2세대 결함 패턴 방어 (dynasty_heir 평가 기반)

> **배경**: dynasty_heir은 1세대 결함(Pattern A~H)을 부분적으로 해결했으나,
> 새로운 유형의 "정교한 템플릿 반복"이 발견됨.
> 1세대 하네스만으로는 이 패턴을 차단할 수 없다.

### 10.1 발견된 2세대 결함 (I~P)

| ID | 패턴 | 설명 | 심각도 |
|----|------|------|--------|
| I | **영문 혼용** | relationship_delta/foreshadow/callback/reward 전량 영문 | P1 |
| J | **코드형 값** | method="execution_plan_01", death_flag="systemic_risk_type_1" 등 서사 텍스트가 아닌 코드 식별자 | P2 |
| K | **10문장 로테이션** | solution/context/event_villain/stakes가 ~10종 문장 템플릿을 섹터명만 교체하며 순환 | P1 |
| L | **leverage_used 고정** | 70블록 전량 동일 4개 항목 (현금흐름 분석, 규제 타이밍 관리, 거점 선점, X 시퀀스 설계) | P1 |
| M | **is_regressor 오류** | 빙의 설정인데 is_regressor=false — timeline_knowledge와 논리 모순 | P0 |
| N | **복선-회수 단절** | foreshadow가 Block N+10 가리키지만, 해당 블록 callback이 회수 안 함 | P1 |
| O | **페이즈 내 NPC 동결** | 2명씩 10블록 고정, 페이즈 내 before=after 동일 문장 | P1 |
| P | **고정 장소 순환** | 정확히 10곳이 10블록 주기로 순환 | P2 |

### 10.2 신규 "절대 금지" 규칙 (§2.3 안티패턴에 추가)

Phase 1 프롬프트 하단 "절대 금지" 목록에 아래를 추가한다:

```
## 절대 금지 — 2세대 (추가 11~20)
11. 영어 문장 금지: relationship_delta, foreshadow, callback, reward, stakes는
    반드시 한국어로 작성하라. 영어 1문장이라도 있으면 재작성.
12. 코드 식별자 금지: method, death_flag.avoided, slip_up, success_pattern,
    weakness_exploited에 "type_1", "plan_01", "anomaly_02" 같은
    코드/번호 접미사 금지. 서사적 한국어 문장으로 서술하라.
    - ❌ "systemic_risk_type_1"
    - ✅ "유동성 경색으로 인한 그룹 전체 연쇄 부도 위기"
    - ❌ "execution_plan_01"
    - ✅ "분할 매수로 지분을 은밀히 확보한 뒤 이사회에서 의결권 행사"
13. 문장 템플릿 재사용 금지: solution/context/event_villain/stakes에서
    "섹터명만 교체"한 동일 구조 문장을 2회 이상 사용하면 재작성.
    탐지법: 섹터명을 마스킹한 뒤 자카드 유사도 50% 이상이면 위반.
14. leverage_used 고정 금지: 70블록 전체에서 동일 4항목 세트가
    3회 이상 반복되면 위반. 블록별 최소 2항목은 고유해야 한다.
15. is_regressor 정합성: regression_type이 "빙의" 또는 "회귀"이면
    is_regressor=true 필수. false인데 timeline_knowledge를 사용하면 모순.
16. 복선 실제 회수 의무: foreshadow에서 "Block N" 지목 시,
    해당 Block N의 callback에 명시적으로 회수 문장 포함 필수.
    "Block N-1 carry-over" 패턴 금지 (직전 블록 기계 참조).
17. 페이즈 내 NPC 변화 의무: 동일 NPC가 5블록 이상 등장하면,
    before≠after인 블록이 최소 3개 있어야 한다.
    10블록 동안 before=after인 NPC가 2명 이상이면 재설계.
18. 장소 순환 주기 최소 15블록: 동일 장소가 15블록 이내에 재등장하면 위반.
    (10곳×10블록 순환 패턴 차단)
19. global_partner 분화 의무: 70블록에 최소 3개 해외 파트너 등장.
    단일 파트너 고정 금지.
20. execution_doctrine 진화 의무: 빙의/회귀 작품에서 execution_doctrine이
    20블록 이상 동일 문장이면 재작성. 위기/성장에 따른 전략 변화 필수.
```

### 10.3 Python 검증 추가 함수

§2.5 `validate_treatment()` 함수에 아래 검증을 추가한다:

```python
def validate_treatment_v2(blocks: list) -> list[dict]:
    """2세대 결함 패턴 탐지. v1 violations에 추가."""
    violations = []

    # --- Pattern I: 영문 혼용 ---
    import re
    ENGLISH_RE = re.compile(r'[A-Za-z]{5,}')  # 5자+ 영단어
    for i, b in enumerate(blocks):
        for rd in b.get("relationship_delta", []):
            for field in ["before", "after"]:
                if ENGLISH_RE.search(rd.get(field, "")):
                    violations.append({
                        "block": i + 1, "pattern": "I",
                        "severity": "P1",
                        "msg": f"relationship_delta.{field} 영문 포함: "
                               f"'{rd[field][:40]}...'"
                    })
                    break
        for fs in b.get("foreshadow", []):
            if ENGLISH_RE.search(fs):
                violations.append({
                    "block": i + 1, "pattern": "I",
                    "severity": "P1",
                    "msg": f"foreshadow 영문: '{fs[:40]}...'"
                })
        for cb in b.get("callback", []):
            if ENGLISH_RE.search(cb):
                violations.append({
                    "block": i + 1, "pattern": "I",
                    "severity": "P1",
                    "msg": f"callback 영문: '{cb[:40]}...'"
                })

    # --- Pattern J: 코드형 값 ---
    CODE_RE = re.compile(r'(?:_\d+|type_\d|plan_\d|anomaly_\d|protocol_\d|_B\d)')
    CODE_FIELDS = [
        ("genre_ext", "method"),
        ("genre_ext", "success_pattern"),
        ("regression_ext", "execution_doctrine"),
    ]
    CODE_NESTED = [
        ("genre_ext", "opponent", "weakness_exploited"),
        ("regression_ext", "death_flag", "avoided"),
        ("regression_ext", "death_flag", "method"),
        ("regression_ext", "regression_hint", "slip_up"),
    ]
    for i, b in enumerate(blocks):
        for parent, key in CODE_FIELDS:
            val = b.get(parent, {}).get(key, "")
            if CODE_RE.search(val):
                violations.append({
                    "block": i + 1, "pattern": "J",
                    "severity": "P2",
                    "msg": f"{parent}.{key} 코드형 값: '{val[:40]}'"
                })
        for *parents, key in CODE_NESTED:
            obj = b
            for p in parents:
                obj = obj.get(p, {}) if isinstance(obj, dict) else {}
            val = obj.get(key, "") if isinstance(obj, dict) else ""
            if CODE_RE.search(str(val)):
                violations.append({
                    "block": i + 1, "pattern": "J",
                    "severity": "P2",
                    "msg": f"{'.'.join(parents)}.{key} 코드형 값: '{str(val)[:40]}'"
                })

    # --- Pattern K: 문장 템플릿 로테이션 (자카드 기반) ---
    def mask_sector(text: str) -> str:
        """섹터명을 마스킹하여 템플릿 비교 가능하게"""
        sectors = ["지주구조", "금융", "반도체", "에너지", "물류",
                   "바이오", "유통", "플랫폼", "인프라", "미디어"]
        for s in sectors:
            text = text.replace(s, "SECTOR")
        return text

    def trigram_jaccard(a: str, b: str) -> float:
        if len(a) < 3 or len(b) < 3:
            return 0.0
        set_a = {a[i:i+3] for i in range(len(a)-2)}
        set_b = {b[i:i+3] for i in range(len(b)-2)}
        inter = len(set_a & set_b)
        union = len(set_a | set_b)
        return inter / union if union > 0 else 0.0

    for field_path in ["content.context", "content.event_villain",
                       "content.solution", "stakes"]:
        texts = []
        for b in blocks:
            parts = field_path.split(".")
            val = b
            for p in parts:
                val = val.get(p, "") if isinstance(val, dict) else ""
            texts.append(mask_sector(str(val)))

        # 비교: 각 블록 vs 이후 5블록
        similar_count = 0
        for i in range(len(texts)):
            for j in range(i+1, min(i+6, len(texts))):
                if trigram_jaccard(texts[i], texts[j]) > 0.5:
                    similar_count += 1
        if similar_count > len(blocks) * 0.3:  # 30% 이상 유사 쌍
            violations.append({
                "block": "전체", "pattern": "K",
                "severity": "P1",
                "msg": f"{field_path} 템플릿 로테이션 감지: "
                       f"유사 쌍 {similar_count}개 (임계: {int(len(blocks)*0.3)})"
            })

    # --- Pattern L: leverage_used 고정 ---
    lev_sets = []
    for b in blocks:
        lev = b.get("genre_ext", {}).get("leverage_used", [])
        if isinstance(lev, list):
            lev_sets.append(tuple(sorted(lev)))
    from collections import Counter
    lev_counter = Counter(lev_sets)
    for lev_set, cnt in lev_counter.items():
        if cnt >= 3:
            violations.append({
                "block": "전체", "pattern": "L",
                "severity": "P1",
                "msg": f"leverage_used 동일 세트 {cnt}회 반복: "
                       f"{list(lev_set)[:2]}..."
            })

    # --- Pattern M: is_regressor 정합 ---
    for i, b in enumerate(blocks):
        reg = b.get("regression_ext", {})
        if not reg:
            continue
        reg_type = reg.get("regression_type", "")
        is_reg = reg.get("is_regressor", None)
        has_knowledge = bool(reg.get("timeline_knowledge", {}).get("info_used"))
        if reg_type in ("빙의", "회귀") and is_reg is False and has_knowledge:
            violations.append({
                "block": i + 1, "pattern": "M",
                "severity": "P0",
                "msg": f"is_regressor=false이나 regression_type='{reg_type}'"
                       f" + timeline_knowledge 사용 → 모순"
            })
            break  # 전 블록 동일이므로 1회만

    # --- Pattern N: 복선-회수 단절 ---
    # 복선에서 지목한 블록 번호 추출 → 해당 블록 callback에 관련 참조 있는지
    plant_targets = {}  # {target_block: [foreshadow_text]}
    BLOCK_REF_RE = re.compile(r'Block\s*(\d+)', re.IGNORECASE)
    for i, b in enumerate(blocks):
        for fs in b.get("foreshadow", []):
            for m in BLOCK_REF_RE.finditer(fs):
                target = int(m.group(1))
                plant_targets.setdefault(target, []).append(fs)

    disconnected = 0
    for target_block, foreshadows in plant_targets.items():
        if 1 <= target_block <= len(blocks):
            tb = blocks[target_block - 1]
            callbacks = tb.get("callback", [])
            # 콜백에 복선 내용이 반영되었는지 (20자 이상 겹침)
            resolved = False
            for cb in callbacks:
                for fs in foreshadows:
                    # 간단한 겹침 체크
                    fs_words = set(fs.split())
                    cb_words = set(cb.split())
                    if len(fs_words & cb_words) >= 3:
                        resolved = True
                        break
                if resolved:
                    break
            if not resolved:
                disconnected += 1
    if disconnected > len(plant_targets) * 0.5:
        violations.append({
            "block": "전체", "pattern": "N",
            "severity": "P1",
            "msg": f"복선-회수 단절: {disconnected}/{len(plant_targets)} "
                   f"복선이 지목 블록에서 회수되지 않음"
        })

    # --- Pattern O: 페이즈 내 NPC 동결 ---
    # 10블록 단위로 NPC before==after 비율 체크
    for phase_start in range(0, len(blocks), 10):
        phase_end = min(phase_start + 10, len(blocks))
        phase_blocks = blocks[phase_start:phase_end]
        npc_frozen = {}  # {name: frozen_count}
        for b in phase_blocks:
            for rd in b.get("relationship_delta", []):
                name = rd.get("target", "")
                if rd.get("before", "") == rd.get("after", ""):
                    npc_frozen[name] = npc_frozen.get(name, 0) + 1
        for name, cnt in npc_frozen.items():
            if cnt >= 7:  # 10블록 중 7블록 이상 동결
                violations.append({
                    "block": f"{phase_start+1}~{phase_end}",
                    "pattern": "O",
                    "severity": "P1",
                    "msg": f"NPC '{name}' 페이즈 내 {cnt}블록 동결 "
                           f"(before=after)"
                })

    # --- Pattern P: 장소 고정 순환 ---
    locations = [b.get("location", {}).get("place", "") for b in blocks]
    for i in range(len(locations)):
        # 15블록 이내 동일 장소 재등장 체크
        for j in range(i+1, min(i+15, len(locations))):
            if locations[i] and locations[i] == locations[j]:
                violations.append({
                    "block": f"{i+1},{j+1}", "pattern": "P",
                    "severity": "P2",
                    "msg": f"장소 '{locations[i]}' {j-i}블록 만에 재등장"
                })
                break  # 첫 발견만

    return violations
```

### 10.4 하네스 보강 — 사전 선언 항목 추가

§8.1 사전 선언 5항목에 아래 **6번째 항목**을 추가한다:

```
6. **언어·형식 체크**: 이번 블록의 relationship_delta, foreshadow, callback,
   reward, stakes가 전부 한국어인지 확인하라.
   method, death_flag, slip_up, success_pattern에 코드 식별자(_01, type_N 등)가
   없는지 확인하라. 하나라도 위반이면 수정 후 JSON을 출력하라.
```

### 10.5 차이 행렬 보강 — 자가 검증 11~15번

§8.2 자가 검증 10문항에 아래 5개를 추가한다:

```
11. relationship_delta/foreshadow/callback에 영어 문장이 있는가? → 한국어로 교체
12. method/death_flag/slip_up에 코드 접미사(_01, type_N)가 있는가? → 서사 문장으로 교체
13. solution/event_villain 열에서 "섹터명만 다르고 나머지 동일"한 쌍이 있는가? → 재작성
14. leverage_used가 3블록 이상 동일 4항목인가? → 최소 2항목 교체
15. callback이 전부 "Block N-1 carry-over" 패턴인가? → 구체적 사건 참조로 교체
```

### 10.6 체크리스트 보강 (§6에 추가)

**P0 추가**:
- [ ] `is_regressor` 정합성: 빙의/회귀면 `true`, 일반이면 `false`

**P1 추가**:
- [ ] 전 필드 한국어 작성 (relationship_delta/foreshadow/callback/reward/stakes)
- [ ] 코드형 값 0건 (method, death_flag, slip_up, success_pattern, weakness_exploited)
- [ ] solution/context/event_villain 템플릿 로테이션 비율 30% 미만 (섹터 마스킹 후 자카드)
- [ ] leverage_used 동일 세트 3회 미만
- [ ] callback이 실제 이전 사건/블록을 구체적으로 참조 (기계 패턴 금지)
- [ ] foreshadow가 지목한 블록에서 실제 회수 (50% 이상)
- [ ] 페이즈 내 NPC before≠after 블록 3개 이상
- [ ] global_partner 최소 3곳
- [ ] execution_doctrine 20블록 내 변화

**P2 추가**:
- [ ] location 15블록 이내 재등장 0건
- [ ] reward 한국어 서사 서술 (영문/기계 표현 금지)

### 10.7 dynasty_heir 사례 — "개선된 것 같지만 여전히 나쁜" 블록

```json
{
  "_comment": "dynasty_heir Block 7 — 1세대 해결, 2세대 전량 위반",
  "block_id": "Block 7",
  "title": "재벌가 빙의 후 승계전 7 - 기반 구축",
  "content": {
    "context": "2007년 9월 차도혁은 유통 라인의 병목을 해소하기 위해 자금·인력 배치를 동시에 재조정했다. 현금흐름 방어선 확립이 이번 라운드의 1순위 과제다.",
    "event_villain": "구경영진 연합이 계약 조건을 일방적으로 재해석해 유통 딜의 신뢰를 흔들었다. 외부 관측치는 부정적으로 기울었다. (기반 구축 7차 국면)",
    "solution": "차도혁은 위험자산과 성장자산을 분리해 의사결정을 단순화했고, Global Mega Fund와의 협상에서 정보 비대칭을 역이용했다. [실행코드:DYN-07]",
    "reward": "Capital moved from 277억 to 330억 (+53억)."
  }
}
```

**이 블록이 "겉보기 개선이지만 여전히 나쁜" 이유**:
- **1세대 해결**: capital_before=277억=Block 6 after ✓, deal_type/beat 다양 ✓, duration 45일 ✓
- **2세대 위반 전량**:
  - `reward` 영문 (Pattern I)
  - `solution`에 `[실행코드:DYN-07]` 코드 (Pattern J)
  - `context` = Block 1의 "지주구조"→"유통" 교체 (Pattern K — 자카드 0.85)
  - `leverage_used` Block 1과 완전 동일 4항목 (Pattern L)
  - `relationship_delta.before/after` 영문 + 6블록 연속 동결 (Pattern I+O)
  - `foreshadow` 영문 + Block 17 지목하지만 Block 17 callback이 회수 안 함 (Pattern N)

**같은 블록의 올바른 버전**:

```json
{
  "block_id": "Block 7",
  "title": "유통 현장을 장악하다 — 대형마트 인수전",
  "content": {
    "context": "2007년 9월, 차도혁은 수도권 유통 시장의 지각 변동을 감지했다. 외환위기 후유증으로 대형마트 체인 '마트플러스'가 매물로 나왔다. 330억 규모의 인수에 도전하려면 현금흐름이 아닌 레버리지 전략이 필요했다.",
    "event_villain": "구경영진 연합의 이호성 상무가 국세청 인맥을 동원해 차도혁의 세무 조사를 유도. 동시에 외국계 PEF '시타델 아시아'가 마트플러스에 경합 입찰서를 제출.",
    "solution": "차도혁은 세무 조사를 역이용해 투명경영 이미지를 구축. 마트플러스 노조 위원장 김판수에게 고용 승계를 약속하며 내부 지지를 확보. 시타델 아시아보다 낮은 가격이었지만 노조+지자체 동의로 우선협상 대상자 선정.",
    "reward": "마트플러스 인수에 성공했으나 레버리지 비용으로 순자산은 277억에서 330억으로 소폭 증가에 그침. 노조와의 약속이 향후 구조조정의 족쇄가 될 수 있다."
  },
  "relationship_delta": [
    {
      "target": "채지훈 부회장",
      "before": "Block 6에서 바이오 투자 성과를 인정하며 '이 정도면 사업 감각이 있다'고 평가 전환",
      "after": "유통 인수 소식에 '재벌 2세가 유통까지? 무리하면 다 잃는다'며 경계심 표출. 공식 석상에서 칭찬하되 사적으로 견제."
    },
    {
      "target": "김판수 (마트플러스 노조위원장)",
      "before": "신규 NPC. 차도혁을 '또 하나의 구조조정 사냥꾼'으로 의심.",
      "after": "고용 승계 약속에 조건부 협력. 그러나 '약속 어기면 파업한다'는 압박도 동시에."
    }
  ],
  "foreshadow": [
    "김판수와의 고용 승계 약속이 Block 15의 구조조정 국면에서 최대 장애물이 될 것",
    "세무 조사 과정에서 발견된 구경영진 비자금 흔적이 Block 12에서 역공 카드로 활용될 것"
  ],
  "callback": [
    "Block 3에서 반도체 계약을 '단계형으로 쪼개 리스크를 분산'한 경험이 이번 마트플러스 인수 조건 설계에 직접 활용됨"
  ],
  "emotional_beat": { "type": "realization", "intensity": 6 },
  "genre_ext": {
    "method": "노조 동의 확보를 통한 입찰 경쟁 우회 — 가격이 아닌 신뢰로 승부",
    "success_pattern": "경합에서 이겼으나 고용 승계라는 시한폭탄을 안고 가는 조건부 승리",
    "leverage_used": ["마트플러스 내부 노조 네트워크", "세무 조사 투명경영 전환", "지자체 고용 안정 니즈 활용"],
    "opponent": {
      "name": "이호성 상무 (구경영진) + 시타델 아시아 (PEF)",
      "weakness_exploited": "시타델은 현지 노조/정치 관계가 전무 — 순수 자본력만으로 입찰"
    }
  },
  "regression_ext": {
    "is_regressor": true,
    "death_flag": {
      "avoided": "유통 확장 실패 → 레버리지 상환 불능 → 그룹 전체 유동성 위기",
      "method": "노조 동의 확보로 인수 리스크를 정치적 보험으로 전환"
    },
    "regression_hint": {
      "slip_up": "마트플러스 인수 발표 기자회견에서 '이 가격이면 3년 안에 흑자'라고 단언 — 전생 데이터 기반 확신이 너무 강해 기자들이 의아해함",
      "suspicion_from": "이호성 상무"
    },
    "execution_doctrine": "초기 단계에서는 가격보다 관계를 우선한다. 싸게 사는 것보다 안전하게 사는 것이 복리의 기반이다."
  }
}
```

**차이**:
- 모든 텍스트 한국어
- 코드 식별자 0건
- context/solution이 이 블록만의 고유 이야기 (마트플러스 인수전)
- 신규 NPC 김판수 등장 + 채지훈 관계 변화
- foreshadow가 구체적 사건 + 구체적 블록 참조
- callback이 Block 3의 구체적 경험 참조
- leverage_used가 이 블록 고유 3항목
- is_regressor=true, slip_up이 서사적 장면
- execution_doctrine이 "초기 단계" 맥락의 고유 원칙

---

*이 문서는 8작품 560블록 전수 감사 + dynasty_heir 심층 평가 결과를 기반으로 작성되었습니다.*
*감사 리포트: `treatments/audit_reports/aggregate_audit_report.md`*
