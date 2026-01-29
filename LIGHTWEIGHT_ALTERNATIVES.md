# Lightweight Alternatives - 가벼운 동적 기능

**개념**: Full 동적 앵커링 시스템 대신 핵심 기능만 간단히 구현

**비교**:
- Full System: 2-3일 개발, 품질 +1~2점
- Lightweight: 2.5시간 개발, 품질 +0.8~1.3점
- **ROI**: 80% 효과를 10% 비용으로

---

## Option A: HUD Trend Injection (1시간)

### 문제
현재 HUD는 "현재 화"만 보여줌. 추세를 파악 못함.
```python
# 현재
"무력: 65"  # 이게 증가 중인지, 감소 중인지 모름
```

### 해결
최근 5화 변화를 간단히 계산해서 프롬프트에 추가
```python
# 개선
"무력: 65 (최근 5화: 50→55→60→62→65, △15 상승 중)"
```

### 구현 방법

**Step 1**: `modules/core/martial_manager.py`에 메서드 추가
```python
def get_hud_trend(self, ep_num: int, window: int = 5) -> str:
    """
    최근 N화의 HUD 변화 추세 반환

    Args:
        ep_num: 현재 화 번호
        window: 추적할 화 수 (기본 5화)

    Returns:
        str: "무력: 50→65 (△15), 내공: 30→28 (▽2)"
    """
    trends = []

    # 주요 메트릭만 (무력, 내공, 경공, 검법, 장법)
    metrics = ['무력', '내공', '경공', '검법', '장법']

    for metric in metrics:
        values = []
        for i in range(max(1, ep_num - window), ep_num + 1):
            hud = self.get_snapshot(i)
            if hud and metric in hud:
                values.append(hud[metric])

        if len(values) >= 2:
            start, end = values[0], values[-1]
            change = end - start
            if change > 0:
                trends.append(f"{metric}: {start}→{end} (△{change})")
            elif change < 0:
                trends.append(f"{metric}: {start}→{end} (▽{abs(change)})")
            # 변화 없으면 생략

    return ", ".join(trends) if trends else "안정적"
```

**Step 2**: Architect/Writer 프롬프트에 주입
```python
# modules/domain/agents/architect.py (design_v20_breakdown 메서드)
# 기존 HUD 정보 다음에 추가

hud_trend = self.martial.get_hud_trend(ep_num, window=5)
prompt += f"\n\n[최근 HUD 변화 추세]\n{hud_trend}\n"
```

**Step 3**: Writer도 동일하게
```python
# modules/domain/agents/writer.py (write_v20_manuscript 메서드)
hud_trend = self.martial.get_hud_trend(ep_num, window=5)
dynamic_prompt += f"\n\n💪 [최근 5화 HUD 추세]\n{hud_trend}\n⚠️ 갑작스런 변화 시 반드시 정당화 필요\n"
```

### 예상 효과
- **HUD 모순 감소**: -5% (갑작스런 변화 감지)
- **정당화 품질**: +0.5점 (추세 인식으로 더 자연스러운 성장)
- **비용**: $0 (로컬 계산, API 호출 없음)
- **구현 시간**: 1시간

---

## Option B: Cliché Counter (30분)

### 문제
같은 표현을 최근 화에서 반복 사용해도 모름
```python
# 예시
3화: "피를 토하며 쓰러졌다"
7화: "피를 토하고 무릎을 꿇었다"
11화: "또다시 피를 토했다"  # 과용!
```

### 해결
최근 10화에서 주요 클리셰 빈도 추적
```python
"⚠️ '피를 토하다' 최근 10화 중 3회 사용 → 다른 표현 권장"
```

### 구현 방법

**Step 1**: `modules/domain/agents/writer.py`에 메서드 추가
```python
def _count_recent_cliches(self, ep_num: int, manuscript: str, window: int = 10) -> Dict[str, int]:
    """
    최근 N화에서 클리셰 빈도 카운트

    Returns:
        dict: {"피를 토하다": 3, "기세": 5, ...}
    """
    # 주요 무협 클리셰 키워드
    cliche_keywords = [
        "피를 토하", "기세", "살기", "냉기", "검기",
        "압도", "전율", "경악", "창백", "경외"
    ]

    counts = {keyword: 0 for keyword in cliche_keywords}

    # 최근 화들 검색
    for i in range(max(1, ep_num - window), ep_num):
        try:
            past_ms = self.context.get_manuscript(i)
            if past_ms:
                for keyword in cliche_keywords:
                    counts[keyword] += past_ms.count(keyword)
        except:
            continue

    # 현재 원고도 체크
    for keyword in cliche_keywords:
        counts[keyword] += manuscript.count(keyword)

    return {k: v for k, v in counts.items() if v > 0}
```

**Step 2**: Self-Critic에 통합
```python
# modules/domain/agents/writer.py (_self_critique 메서드 내부)

def _check_cliche_overuse(self, manuscript: str, ep_num: int) -> List[str]:
    """클리셰 과용 체크 (기존 메서드 개선)"""
    issues = []

    # 최근 빈도 체크 추가
    recent_counts = self._count_recent_cliches(ep_num, manuscript, window=10)

    overused = [
        f"'{keyword}' ({count}회)"
        for keyword, count in recent_counts.items()
        if count >= 3  # 10화 중 3회 이상이면 과용
    ]

    if overused:
        issues.append(
            f"⚠️ 최근 클리셰 과용: {', '.join(overused)}\n"
            f"→ 다른 표현으로 다양화 필요"
        )

    return issues
```

### 예상 효과
- **표현 다양성**: +0.5점 (클리셰 감소)
- **독자 경험**: 향상 (지루함 감소)
- **비용**: $0 (문자열 검색만)
- **구현 시간**: 30분

---

## Option C: NPC Frequency Warning (1시간)

### 문제
주요 NPC가 오래 안나왔는데도 모름
```python
# 예시
연홍 (여주인공): 1-5화 등장 → 6-25화 미등장 (20화 공백!)
→ 독자: "여주인공 어디갔어?"
```

### 해결
주요 NPC 최근 등장 빈도 추적
```python
"⚠️ 연홍 (KeyNPC): 최근 10화 중 0회 등장 → 관계 유지 필요"
"✅ 화산장로: 최근 10화 중 8회 등장 → 주연급 일관성 유지"
```

### 구현 방법

**Step 1**: `modules/domain/agents/writer.py`에 메서드 추가
```python
def _get_npc_frequency(self, ep_num: int, window: int = 10) -> Dict[str, int]:
    """
    최근 N화에서 주요 NPC 등장 횟수

    Returns:
        dict: {"연홍": 8, "화산장로": 2, ...}
    """
    master_bible = self.context.get_anchor('bible')
    if not master_bible:
        return {}

    assets = master_bible.get('AssetLibrary', {})
    key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])

    if not key_npcs:
        return {}

    # NPC 이름 추출
    npc_names = [npc.get('name', '') for npc in key_npcs if npc.get('name')]

    # 빈도 카운트
    frequency = {name: 0 for name in npc_names}

    for i in range(max(1, ep_num - window), ep_num):
        try:
            past_ms = self.context.get_manuscript(i)
            if past_ms:
                for name in npc_names:
                    if name in past_ms:
                        frequency[name] += 1
        except:
            continue

    return frequency
```

**Step 2**: Writer 프롬프트에 주입
```python
# modules/domain/agents/writer.py (write_v20_manuscript 메서드)

npc_freq = self._get_npc_frequency(ep_num, window=10)

if npc_freq:
    npc_warnings = []
    for name, count in npc_freq.items():
        if count == 0:
            npc_warnings.append(f"⚠️ {name}: 최근 10화 미등장 → 관계 유지 고려")
        elif count >= 7:
            npc_warnings.append(f"✅ {name}: 최근 {count}회 등장 → 주연급 일관성 유지")

    if npc_warnings:
        dynamic_prompt += f"\n\n[주요 NPC 등장 빈도]\n" + "\n".join(npc_warnings) + "\n"
```

### 예상 효과
- **NPC 관계 모순**: -3~5% (장기 미등장 방지)
- **서사 밀도**: +0.3점 (NPC 활용도 향상)
- **비용**: $0 (문자열 검색만)
- **구현 시간**: 1시간

---

## 총 효과 비교

| 항목 | Full 동적 앵커링 | Lightweight Alternatives | 비율 |
|------|-----------------|-------------------------|------|
| **구현 시간** | 2-3일 | 2.5시간 | 10% |
| **품질 향상** | +1~2점 | +0.8~1.3점 | 65-80% |
| **HUD 모순 감소** | -5~10% | -5% | 50-100% |
| **표현 다양성** | +0.5점 | +0.5점 | 100% |
| **NPC 모순 감소** | -3~5% | -3~5% | 100% |
| **API 비용** | +$0.10 | +$0 | 0% |
| **코드 복잡도** | +20% | +5% | 25% |

**ROI**: Lightweight가 압도적으로 높음 ⭐⭐⭐⭐⭐

---

## 구현 순서

### 우선순위 1: Cliché Counter (30분)
- 가장 빠르고 효과 확실
- Writer Self-Critic에 한 줄만 추가
- 즉시 표현 다양성 향상

### 우선순위 2: HUD Trend (1시간)
- HUD 모순 감소 효과 큼
- MartialManager에 메서드 하나 추가
- Architect/Writer 프롬프트에 주입

### 우선순위 3: NPC Frequency (1시간)
- NPC 일관성 향상
- 장편에서 특히 유용
- Writer 프롬프트에 경고 추가

**총 시간**: 2.5시간
**즉시 배포 가능**: 각 기능은 독립적, 하나씩 추가 가능

---

## 실제 코드 위치

구현할 파일:
1. `modules/core/martial_manager.py` - HUD trend 메서드 추가
2. `modules/domain/agents/writer.py` - Cliché counter + NPC frequency 메서드 추가
3. `modules/domain/agents/architect.py` - HUD trend 프롬프트 주입

---

## 결론

**Lightweight alternatives = 가성비 최고 선택**

- Full system 효과의 80%를 10% 비용으로
- 2.5시간 만에 품질 +0.8~1.3점
- API 비용 $0 증가
- 복잡도 최소화
- 즉시 배포 가능

**추천**: Phase 5 Self-Refine 통합 후, 이 3가지 lightweight 기능을 하나씩 추가해보세요.
