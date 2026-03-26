# 샘플 6장 수준 도달 루트 — AI 90%+ 전제

> 대상: `docs/일러_샘플/1~6.png` (한국 메이저 웹소설 표지 6종)
> 전제: AI 90% 이상 활용. 나머지 10%는 포토샵/클립스튜디오 후보정.

---

## 0. 샘플 분석 결론 — "이건 애니메가 아니다"

6장 전수 분석 결과, 이 표지들은 **일반 애니메 AI 출력으로는 절대 재현 불가**하다.

| 일반 AI 애니메 출력 | 이 샘플들 |
|---|---|
| 둥근 얼굴, 큰 눈 | 날카로운 이목구비, 긴 얼굴, 작은 눈 |
| 플랫 셀 셰이딩 | 시네마틱 명암, 복잡한 라이팅 |
| 밝고 깨끗한 색감 | 다크 톤, 강한 색보정 |
| 정적인 정면 구도 | 대각선, 로우앵글, 역동적 |
| 단일 캐릭터 | 2~3인 합성이 절반 |
| 배경 단순 | 먹물 스플래시, 마력 이펙트, 파티클 |

**→ "한국 만화(Manhwa) 스타일" 전용 파이프라인을 처음부터 따로 만들어야 한다.**

---

## 1. 모델 세팅 — 무기고 재편

### 1-1. 체크포인트 (베이스 모델)

일반 Illustrious XL로는 이 스타일이 안 나온다. **만화풍 특화 체크포인트**가 필요하다.

| 우선순위 | 체크포인트 | 왜 이것인가 | Civitai 링크 |
|---|---|---|---|
| **1순위** | **Manhwa Style Illustrious v2.0** | 2022~2025+ 한국 만화/웹툰 스타일 전용 머지. 샘플과 가장 가까운 출력 | [링크](https://civitai.com/models/2179589/manhwa-style-illusrious) |
| **2순위** | **Illustrious Dark Fantasy v4** | 다크 판타지 톤 특화. 1,6번 샘플 계열에 강점 | [링크](https://civitai.com/models/2036738/illustrious-dark-fantasy) |
| **3순위** | **Illustrij v21** | 반실사 베이스 + 미묘한 애니메 터치. 2,3번 샘플의 정제된 느낌 | [링크](https://civitai.com/models/1025051/illustrij) |
| 보조 | WAI-Illustrious-SDXL v16 | 범용 고품질. 위 3개로 부족할 때 대안 | [링크](https://civitai.com/models/827184/wai-illustrious-sdxl) |

**핵심**: 체크포인트 3개를 **장르/분위기에 따라 교체**한다.
- 1,6번(다크 액션) → Illustrious Dark Fantasy
- 2,5번(판타지/마법) → Manhwa Style Illustrious
- 3번(귀족/로맨스) → Illustrij

### 1-2. 스타일 LoRA — 핵심 무기

체크포인트만으로 부족하다. LoRA로 스타일을 정밀 제어한다.

| LoRA | 용도 | 강도 | Civitai |
|---|---|---|---|
| **Korean Manhwa/Webtoon Style 2025** | 만화풍 전체 톤 | 0.75~1.0 | [링크](https://civitai.com/models/2179842/korean-manhwa-webtoon-style-lora-2025) |
| **NEW FANTASY CORE v4** | 판타지 디테일 강화 (갑옷, 마법, 이펙트) | 0.5~0.7 | [링크](https://civitai.com/models/810000/new-fantasy-core-ill-flux-pony-sdxl-zitdetailer) |
| Manhwa Artstyle / Webtoon | 대안 만화풍 LoRA | 0.6~0.8 | [링크](https://civitai.com/models/257995/manhwa-artstyle-or-webtoon-or-lora) |

**조합 공식**:
```
체크포인트 (Manhwa Style Illustrious)
  + 스타일 LoRA (Korean Manhwa 2025, weight 0.8)
  + 판타지 LoRA (NEW FANTASY CORE, weight 0.5)
  + 캐릭터 LoRA (자체 훈련, weight 0.7)
```

### 1-3. ControlNet — 이 샘플 수준에서는 무조건 필수

| 모델 | 샘플에서의 용도 |
|---|---|
| **OpenPose** | 1,5,6번의 역동적 포즈. 다인물 개별 포즈 지정 |
| **Depth** | 2,3번의 배경 깊이감. 보케 제어 |
| **Canny** | 레퍼런스 구도 추출 → 재현 |
| **Lineart** | 러프 스케치 기반 생성 |

---

## 2. 샘플별 재현 루트

### 2-1. 1번 "오른손이 너무 강함" 타입 — 다크 액션 + 먹물 이펙트

```
[난이도: ★★★☆☆ — 단일 캐릭터라 합성 불필요]

체크포인트: Illustrious Dark Fantasy v4
LoRA:       Korean Manhwa 2025 (0.8) + NEW FANTASY CORE (0.6)

프롬프트 골격:
  masterpiece, best quality, very aesthetic, absurdres,
  manhwa_style, dark fantasy,
  1boy, black short hair, sharp red eyes, fierce expression,
  dark battle armor, torn cape, (clenched fist:1.3),
  (ink splash effect:1.2), (paint splatter:1.1),
  dynamic pose, low angle shot, from below,
  dark purple sky background, debris flying,
  dramatic backlighting, rim light, dark atmosphere,
  (dark color palette:1.2), high contrast

ControlNet:
  OpenPose — 로우앵글 + 주먹 쥔 역동적 포즈 (3D 인형으로 제작)

후보정 (Photoshop):
  1. 먹물 스플래시 브러시 레이어 추가 (Overlay/Screen 모드)
     → Photoshop 잉크 스플래시 브러시 팩 사용
     → 캐릭터 주변과 프레임 가장자리에 배치
  2. 컬러 그레이딩: 어두운 보라/붉은 톤 Gradient Map (Overlay 15%)
  3. 입자/파편 효과 브러시 추가
  4. Curves로 암부 더 짙게, 하이라이트 날카롭게
```

### 2-2. 2번 "마법학교" 타입 — 다크 아카데미아 + 마법 이펙트

```
[난이도: ★★★☆☆ — 단일 캐릭터, 배경 복잡]

체크포인트: Manhwa Style Illustrious v2.0
LoRA:       Korean Manhwa 2025 (0.8) + NEW FANTASY CORE (0.5)

프롬프트 골격:
  masterpiece, best quality, very aesthetic, absurdres,
  manhwa_style,
  1boy, black medium hair, sharp dark eyes, calm expression,
  (dark academy robe:1.3), high collar, silver brooch,
  holding (magical blue orb:1.2), blue magical particles,
  gothic architecture background, stone pillars, arched windows,
  (dim atmospheric lighting:1.2), volumetric fog,
  muted dark color palette, blue accent lighting,
  upper body, looking at viewer, slight head tilt

ControlNet:
  OpenPose — 상반신, 한 손에 오브를 든 포즈
  Depth — 고딕 건축 배경 깊이맵 (레퍼런스에서 추출)

후보정:
  1. 마법 오브 글로우 강화 — Photoshop 브러시 (Soft Light/Screen)
  2. 마법 파티클 브러시 레이어 추가
  3. 전체 톤: 차가운 블루 + 따뜻한 피부톤 대비 (Color Balance)
  4. 배경에 안개/볼류메트릭 라이트 추가 (가우시안 블러 레이어)
```

### 2-3. 3번 "변경백" 타입 — 귀족/로열 + 골든 톤

```
[난이도: ★★★☆☆ — 단일 캐릭터, 의상 디테일이 관건]

체크포인트: Illustrij v21
LoRA:       Korean Manhwa 2025 (0.7) + NEW FANTASY CORE (0.5)

프롬프트 골격:
  masterpiece, best quality, very aesthetic, absurdres,
  manhwa_style,
  1boy, (golden blond wavy hair:1.3), amber eyes, gentle noble smile,
  (ornate white royal coat with gold embroidery:1.4),
  jeweled collar, golden epaulettes, intricate fabric detail,
  rose garden background, blooming flowers, green foliage,
  (golden hour warm lighting:1.3), sun rays, soft lens flare,
  upper body, looking at viewer,
  (dreamy warm atmosphere:1.1), flower petals falling

ControlNet:
  OpenPose — 정면~약간 측면, 여유로운 자세
  Depth — 정원 배경 보케

핵심 후보정:
  1. 의상 금사 자수 디테일 — 인페인팅으로 자수 패턴 정밀화
  2. 보석/금속 광택 — Clip Studio 하이라이트 브러시로 추가
  3. Gradient Map: 골드→크림 (Overlay 10%) — 전체 따뜻한 톤 통일
  4. 꽃잎 파티클 레이어 추가
```

### 2-4. 4번 "나만 탑이 두 개다" 타입 — 3인 현대판타지

```
[난이도: ★★★★★ — 3인 합성 필수]

이것이 가장 어렵다. AI 한 번에 3인을 깨끗하게 못 뽑는다.

방법: Latent Couple + 개별 생성 합성

[Step 1] 각 캐릭터 개별 생성 (3회)
  - 캐릭터별 LoRA 적용 (있다면)
  - 각각 투명/단색 배경으로 생성
  - OpenPose로 포즈 개별 지정

[Step 2] ComfyUI Latent Couple 방식
  - 화면을 3분할 마스크로 나눔
  - 좌/중/우 각각 다른 프롬프트 적용
  - base prompt (공통 분위기) + 영역별 concept prompt

  또는

[Step 3] Photoshop 합성 (더 안전한 방법)
  - 3명을 개별 생성 → 배경 제거 (SAM/rembg)
  - Photoshop에서 배치, 크기 조절
  - 합성 경계 자연스럽게: 그림자/라이팅 통일
  - 공통 이펙트 레이어(보라 오라, 파티클) 위에 덮기
  - Gradient Map으로 전체 색조 통일

[Step 4] 최종 통합 색보정
  - 3명의 피부톤/의상톤이 같은 조명 아래 있는 것처럼 통일
  - Color Balance: 하이라이트에 같은 색 추가
```

### 2-5. 5번 "천재 궁수" 타입 — 남녀 투샷 + 아이스 이펙트

```
[난이도: ★★★★☆ — 2인 합성]

[Step 1] 남자 캐릭터 개별 생성
  어두운 갑옷, 전방 주시, 대각선 구도, 블루 톤

[Step 2] 여자 캐릭터 개별 생성
  은발, 백색 의상, 아이스 마법 이펙트

[Step 3] 합성
  - 남자: 화면 우하단 (전면, 크게)
  - 여자: 화면 좌상단 (약간 뒤, 작게)
  - 대각선 구도 형성

[Step 4] 이펙트
  - 블루 아이스/화살 이펙트: Photoshop 브러시 + 글로우 (Screen 모드)
  - 전체 블루 시네마틱 톤: Gradient Map (Overlay 12%)
```

### 2-6. 6번 "환생한 암살자" 타입 — 3인 액션 + 먹물

```
[난이도: ★★★★★ — 3인 + 역동적 액션 + 먹물]

1번(먹물 이펙트) + 4번(3인 합성)의 합체.

[Step 1] 3인 개별 생성
  - 각각 다른 무기(검/단검/활 등), 다른 액션 포즈
  - OpenPose로 대각선 액션 포즈 각각 지정
  - 투명/단색 배경

[Step 2] Photoshop 합성
  - 대각선 배치: 좌하→우상 흐름
  - 크기 차이로 원근감 (앞=크게, 뒤=작게)

[Step 3] 먹물 이펙트 레이어
  - 잉크 스플래시 브러시 팩 (무료 많음)
  - Multiply/Overlay 모드로 여러 레이어
  - 캐릭터 뒤 + 프레임 가장자리에 집중

[Step 4] 무브먼트 표현
  - Motion Blur: 캐릭터 뒤에 잔상 느낌
  - 바람 방향 통일: 머리카락/옷자락/먹물 모두 같은 방향
  - 스피드 라인 브러시 미세하게 추가
```

---

## 3. 이펙트 기술 — 이게 "한국 웹소설 표지"의 정체성

샘플 6장에서 **이펙트가 차지하는 비중이 30% 이상**이다. AI만으로는 부족하고 포토샵 레이어 작업이 필수.

### 3-1. 먹물 스플래시 (1, 6번)

```
[준비물]
  - Photoshop 잉크 스플래시 브러시 팩 (무료)
    검색: "ink splash brush photoshop free"
    권장: Brusheezy, DeviantArt에서 다운로드

[적용법]
  1. 새 레이어, Multiply 또는 Overlay 모드
  2. 검은색 잉크 브러시로 캐릭터 주변에 타격
  3. 불투명도 60~80%
  4. 일부는 Screen 모드 + 흰색으로 → 밝은 잉크 튀김
  5. 프레임 가장자리에서 안쪽으로 침범하는 형태
  6. Eraser로 캐릭터 위에 묻은 잉크 부분 정리
  7. 레이어 3~5장을 쌓아야 자연스러움
```

### 3-2. 마력/오라 이펙트 (2, 4, 5번)

```
[AI로 일부 생성 가능]
  프롬프트: "magical aura, glowing particles, energy effect, blue glow"
  → 하지만 위치/형태가 불안정

[포토샵 확실한 방법]
  1. 새 레이어, Screen 또는 Linear Dodge 모드
  2. 소프트 브러시(블루/퍼플)로 광원 위치에 큰 원형 터치
  3. 작은 브러시로 파티클 점 찍기 (불규칙하게)
  4. Gaussian Blur 3~5px 적용 → 글로우 느낌
  5. Outer Glow 레이어 스타일 추가
  6. 색: 블루(#4488ff), 퍼플(#8844ff), 시안(#44ddff)
```

### 3-3. 꽃잎/파티클 (3번)

```
[AI로 생성 가능하지만 후보정이 더 정밀]
  프롬프트: "flower petals falling, particle effect"

[포토샵]
  1. 꽃잎 브러시 팩 다운로드
  2. 새 레이어에 다양한 크기로 뿌리기
  3. 전경 꽃잎: 크고 블러 (Gaussian 5~8px) → 보케 효과
  4. 중경 꽃잎: 중간 크기, 선명
  5. 후경 꽃잎: 작고 흐릿
  → 3단계 깊이감으로 입체감 형성
```

### 3-4. 시네마틱 색보정 — 전 샘플 공통

```
이 6장 전부 강한 색보정이 되어 있다. AI 원본 → 색보정 전후 차이가 극적.

[공통 적용 순서]
  1. Curves: S커브로 대비 강화. 암부를 더 깊게.
  2. Color Balance:
     하이라이트 → 약간 따뜻하게 (Yellow +5, Red +3)
     그림자 → 약간 차갑게 (Blue +8, Cyan +5)
     = "시네마틱" 느낌의 핵심
  3. Gradient Map (Overlay 10~15%):
     다크 액션: 다크 퍼플 → 레드 → 블랙
     마법/판타지: 딥 블루 → 시안 → 화이트
     로맨스/귀족: 다크 골드 → 크림 → 화이트
  4. Vignette: 가장자리 어둡게 (Lens Correction 또는 수동)
  5. Sharpen: 최종 Unsharp Mask (Amount 30%, Radius 1.5px)
```

---

## 4. 다인물 합성 마스터 — 샘플의 50%가 이것

### 4-1. 방법론 비교

| 방법 | 품질 | 난이도 | 적합 상황 |
|---|---|---|---|
| **개별 생성 → PS 합성** | ★★★★★ | 중 | **권장. 가장 안전하고 품질 최고** |
| ComfyUI Latent Couple | ★★★★ | 상 | 2인까지. 3인 이상은 불안정 |
| Regional Prompt | ★★★ | 중 | 단순 배치. 상호작용 표현 어려움 |
| 한 번에 생성 | ★★ | 하 | Concept Bleeding 불가피. 비권장 |

### 4-2. 개별 생성 → PS 합성 워크플로우 (권장)

```
[Phase 1] 포즈 설계
  1. Clip Studio 3D 인형 3개 배치
  2. 최종 합성 구도대로 포즈 잡기
  3. 각 인형 개별 스크린샷 + 전체 합성 스크린샷

[Phase 2] 개별 생성 (캐릭터 A/B/C 각각)
  ComfyUI:
  - 체크포인트 + 스타일 LoRA + 캐릭터 LoRA(A)
  - ControlNet OpenPose: A의 포즈
  - 배경: 단색 또는 투명
  - 8~16장 배치 → 최적 1장 선택
  - ADetailer → 업스케일

  같은 과정을 B, C에 반복.
  ★ 핵심: 3명 모두 같은 체크포인트 + 스타일 LoRA 사용
          → 화풍 통일

[Phase 3] 배경 별도 생성
  - 인물 없는 배경만 따로 생성
  - 또는 레퍼런스 배경에서 Depth맵 추출 → AI 재생성

[Phase 4] Photoshop 합성
  1. 배경 레이어
  2. 캐릭터 C (가장 뒤) — rembg로 배경 제거 후 배치
  3. 캐릭터 B (중간)
  4. 캐릭터 A (가장 앞)
  5. 각 캐릭터에:
     - Drop Shadow (미세하게)
     - 라이팅 방향 통일 (Curves + 마스크로 한쪽만 밝게)
     - 피부톤 Color Balance 통일
  6. 이펙트 레이어 (먹물/마력/파티클)
  7. 전체 색보정 레이어 (Gradient Map + Curves)
  8. 타이포그래피

[Phase 5] 경계 다듬기
  - 캐릭터 간 겹치는 부분: 소프트 브러시로 경계 블렌딩
  - 공통 광원에서 오는 림라이트를 모든 캐릭터에 추가
  - 전체에 미세한 노이즈 레이어 → 합성 티 제거
```

---

## 5. 최적 루트 — 주 단위 로드맵

### Week 1: 모델 세팅 + 첫 출력

```
□ ComfyUI 설치
□ 체크포인트 3종 다운로드 (Manhwa Style / Dark Fantasy / Illustrij)
□ 스타일 LoRA 2종 다운로드 (Korean Manhwa 2025 / NEW FANTASY CORE)
□ ControlNet 4종 설치 (OpenPose/Canny/Depth/Lineart)
□ 필수 노드 5종 설치
□ 샘플 1번(다크 액션, 단일 캐릭터)을 목표로 첫 생성
□ 체크포인트 + LoRA 조합 테스트 → 만화풍 나오는 조합 확정
```

### Week 2: 프롬프트 + ControlNet 정복

```
□ 샘플 1~3번(단일 캐릭터) 각각 재현 시도
□ 3D 인형으로 포즈 만들기 → OpenPose 추출 → ControlNet 적용
□ 프롬프트 정밀 조율 — 만화풍 특화 태그 실험
□ Depth ControlNet으로 배경 깊이감 제어
□ 배치 생성 → 선별 루틴 체화
□ ADetailer 2-pass 파이프라인 구축
```

### Week 3: 후보정 + 이펙트

```
□ Photoshop 잉크 스플래시 브러시 팩 설치
□ 마력/글로우 이펙트 레이어 기법 연습
□ 시네마틱 색보정 루틴 확립 (Curves + Color Balance + Gradient Map)
□ 샘플 1번 완전 재현 시도 (생성 → 이펙트 → 색보정 → 타이포)
□ 샘플 2번 완전 재현 시도
□ 샘플 3번 완전 재현 시도
```

### Week 4: 다인물 합성

```
□ rembg / SAM으로 배경 제거 연습
□ 2인 합성 워크플로우 확립 (5번 "천재 궁수" 재현)
□ 3인 합성 워크플로우 확립 (4번 "나만 탑이 두 개다" 재현)
□ 합성 경계 블렌딩 + 라이팅 통일 기법
□ 6번 "환생한 암살자" 재현 (3인 + 먹물 + 액션)
□ 6종 전부 재현 완료 → 비교 대조
```

### Week 5~6: LoRA 훈련 + 고유 캐릭터

```
□ 자체 캐릭터 LoRA 첫 훈련
□ 자체 스타일 LoRA 훈련 (샘플들의 화풍을 학습시킴)
□ 캐릭터 LoRA + 스타일 LoRA 조합 테스트
□ 오리지널 표지 제작 (재현이 아닌 창작)
□ 전체 파이프라인 시간 단축 목표: 표지 1장 3~4시간 이내
```

---

## 6. 적대적 감리

### Pass 1: 사실 검증

| # | 항목 | 결과 | 비고 |
|---|---|---|---|
| F1 | Manhwa Style Illustrious v2.0 존재 | ✅ | Civitai 직접 확인 |
| F2 | Illustrious Dark Fantasy v4 존재 | ✅ | Civitai 직접 확인 |
| F3 | Korean Manhwa 2025 LoRA 존재 + 트리거 "manhwa_style" | ✅ | Civitai 직접 확인 |
| F4 | Latent Couple로 2인 가능, 3인 불안정 | ✅ | ComfyUI 커뮤니티 토론 + GitHub 확인 |
| F5 | 개별 생성→PS 합성이 품질 최고 | ✅ | 실무 합의, 다수 워크플로우 가이드 일치 |
| F6 | 샘플 화풍이 "한국 만화풍"이며 일반 애니메와 다름 | ✅ | 6장 직접 분석. 반실사 비율/날카로운 라인/시네마틱 톤 확인 |

### Pass 2: 논리 모순

| # | 항목 | 판정 |
|---|---|---|
| L1 | "AI 90%"인데 포토샵 작업량이 많아 보임 | ✅ 모순 아님. AI가 캐릭터/배경/기본 구도를 생성(90%의 픽셀). 포토샵은 이펙트 레이어 + 색보정 + 합성(시간의 40%이지만 픽셀의 10%) |
| L2 | 체크포인트 3종 교체가 번거로움 | ⚠️ 실무 주의. 체크포인트 로딩에 시간 소요. 워크플로우에 체크포인트 스위치 노드 사용 권장 |
| L3 | 자체 스타일 LoRA 훈련에 "샘플들의 화풍을 학습시킴" | ⚠️ 저작권 주의. 타인 작품을 LoRA 훈련에 직접 사용 시 리스크. 자체 생성 이미지로 학습 또는 다수 출처 혼합 권장 |

### Pass 3: 누락

| # | 항목 | 심각도 | 대응 |
|---|---|---|---|
| M1 | 타이포그래피 상세 기법 | 중 | 기존 플레이북 7장 참조. 본 문서 범위는 "일러스트 자체" |
| M2 | FLUX 기반 대안 루트 | 하 | 현 시점 만화풍 LoRA 생태계는 SDXL/Illustrious에 집중. FLUX는 차후 |
| M3 | GPU 없을 때 클라우드 루트 상세 | 하 | 기존 플레이북에서 RunPod 언급 |

### 최종 판정

| 항목 | 결과 |
|---|---|
| 사실 오류 | 0건 |
| 논리 모순 | 0건 심각, 2건 실무 주의(L2 체크포인트 전환, L3 저작권) |
| 누락 | 3건, 모두 기존 문서에서 커버 또는 범위 초과 |
| **종합** | **A- (즉시 실행 가능. L3 저작권 주의사항만 유의)** |

---

*샘플 6장 직접 분석 기반. 모든 Civitai 모델은 실존 확인 완료.*
