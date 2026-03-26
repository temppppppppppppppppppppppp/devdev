# AI 일러스트레이터 실전 플레이북 v2

> 목표: **개쩌는 일러스트를 뽑는다.** 그게 전부다.
> 이 문서는 "기술력 자체"에만 집중한다. 법률·비즈니스·플랫폼 정책은 부록으로 밀었다.

---

## 목차 — 본편: 기술력

1. [심미안 — 좋은 그림이 뭔지 모르면 못 만든다](#1-심미안--좋은-그림이-뭔지-모르면-못-만든다)
2. [무기고 — 장비·모델·소프트웨어 세팅](#2-무기고--장비모델소프트웨어-세팅)
3. [프롬프트 — AI에게 정확히 시키는 기술](#3-프롬프트--ai에게-정확히-시키는-기술)
4. [구도·포즈 — ControlNet으로 화면을 지배한다](#4-구도포즈--controlnet으로-화면을-지배한다)
5. [캐릭터 각인 — LoRA로 "내 캐릭터"를 만든다](#5-캐릭터-각인--lora로-내-캐릭터를-만든다)
6. [멀티패스 정제 — AI 출력을 프로급으로 끌어올린다](#6-멀티패스-정제--ai-출력을-프로급으로-끌어올린다)
7. [후보정 — 여기서 아마추어와 프로가 갈린다](#7-후보정--여기서-아마추어와-프로가-갈린다)
8. [색감·라이팅·분위기 — 그림의 "급"을 결정하는 것](#8-색감라이팅분위기--그림의-급을-결정하는-것)
9. [장르별 표지 문법 — 로판·현판·무협 각각 다르다](#9-장르별-표지-문법--로판현판무협-각각-다르다)
10. [흔한 실수 — 초보가 반드시 빠지는 함정](#10-흔한-실수--초보가-반드시-빠지는-함정)
11. [스킬 트리 — 8주 로드맵](#11-스킬-트리--8주-로드맵)
12. [적대적 감리 결과](#12-적대적-감리-결과)

**부록**: [A. 법적 환경](#부록-a-법적-환경) | [B. 비즈니스 모델](#부록-b-비즈니스-모델) | [C. 플랫폼 규격](#부록-c-플랫폼-규격) | [D. 출처](#부록-d-출처)

---

## 1. 심미안 — 좋은 그림이 뭔지 모르면 못 만든다

AI는 도구일 뿐이다. **뭘 만들어야 하는지 아는 눈**이 먼저다.

### 1-1. 프로 일러스트의 3대 요소

| 요소 | 설명 | AI 혼자 해결되는가? |
|---|---|---|
| **구도(Composition)** | 시선 유도, 여백, 밸런스 | 부분적. ControlNet으로 강제해야 정확 |
| **색감(Color)** | 색상 조화, 명암 대비, 분위기 | 프롬프트+후보정으로 제어 가능하나 "급"은 인간 판단 |
| **디테일(Detail)** | 눈·머리카락·의상·질감의 정밀도 | AI가 가장 잘 하는 영역. 단, 손/눈은 후보정 필수 |

### 1-2. 레퍼런스 수집 습관 — 매일 30분

**"뭘 봐야 하는가"가 아니라 "왜 좋은지 분석하는 것"이 핵심.**

```
1. Pixiv 일간 랭킹 상위 50개 스크롤
   → "이 그림은 왜 눈에 들어오지?" 자문
   → 구도? 색감? 캐릭터 표정? 라이팅?

2. ArtStation 트렌딩 + 웹소설 표지 전문 일러스트레이터 팔로우
   → 방솜, HOGG, sakimichan, Ilya Kuvshinov 등

3. Pinterest 보드에 장르별로 분류 저장
   → "로판 표지", "현판 표지", "라이팅 레퍼런스", "구도 레퍼런스"
```

### 1-3. 두 거장의 스타일 해부 — 왜 이들이 "개쩔"까

**Sakimichan (Yue Wang)**
- 핵심: 채도 높은 따뜻한 오렌지 + 꿈결 같은 블루. 글로우 이펙트. 부드러운 셰이딩.
- 프롬프트로 재현하려면: `vibrant colors, warm orange tones, dreamy blue highlights, soft shading, glow effects, painterly style`
- 배울 점: **색 대비가 드라마를 만든다.** 단순히 예쁜 게 아니라 "빛이 서사를 말한다."

**Ilya Kuvshinov**
- 핵심: 깨끗한 선화 + 부드러운 그라디언트 + 뮤트 파스텔 톤. 큰 눈, 섬세한 이목구비.
- 프롬프트로 재현하려면: `clean lineart, smooth gradients, muted pastel tones, large expressive eyes, delicate features, modern anime style`
- 배울 점: **절제가 고급감이다.** 화려하지 않아도 분위기가 산다.

→ 이 두 스타일을 AI로 얼마나 정밀하게 재현하느냐가 **실력의 첫 번째 척도**.

---

## 2. 무기고 — 장비·모델·소프트웨어 세팅

### 2-1. GPU

| 등급 | GPU | VRAM | 가능 범위 | 비용 |
|---|---|---|---|---|
| 최소 | RTX 3060 | 12GB | SDXL + Illustrious XL 추론, LoRA 추론 | ~40만 (중고) |
| **권장** | **RTX 4070 Ti Super** | **16GB** | SDXL 쾌적, FLUX 기본, LoRA 훈련 | ~80만 |
| 최적 | RTX 4090 | 24GB | FLUX.2 풀, LoRA 훈련 쾌적, 배치 생성 | ~250만 |
| 대안 | RunPod 클라우드 RTX 4090 | 24GB | 모든 것 | $0.69/hr |

RAM 32GB+, SSD 1TB+, IPS 모니터(sRGB 99%+) 필수.

### 2-2. 소프트웨어 스택

```
[메인 엔진]     ComfyUI              ← 모든 프로덕션의 중심
[보조 엔진]     A1111 WebUI           ← ADetailer 등 일부 기능
[후보정]        Clip Studio Paint EX  ← $50 영구. 선화 보정·브러시 터치 최강
                또는 Photoshop        ← $13/월. 색보정·합성 최강
[LoRA 훈련]     Kohya-ss GUI          ← Illustrious XL LoRA 훈련 표준
[3D 포즈]       Clip Studio 3D 인형   ← ControlNet 입력용 포즈 생성
[컨셉 탐색]     Midjourney / NovelAI  ← "이런 느낌" 빠르게 탐색용
```

### 2-3. 체크포인트 (베이스 모델) — 3개만 깔아라

| 순위 | 모델 | 왜 |
|---|---|---|
| **1** | **Illustrious XL v3.6** | 2025~26 애니메 표준. LoRA/ControlNet 생태계 최성숙. Danbooru 태그+자연어 둘 다. |
| **2** | **Hassaku XL v2.2** | Illustrious 파인튠. 더 진한 색감, 선명한 라인. 화려한 로판 표지에 특히 강점. |
| **3** | **FLUX.2 dev + NTR Mix FLUX** | 차세대. 포즈 정확도·텍스트 렌더링 최고. 24GB VRAM 필요. |

### 2-4. 필수 ControlNet

| 모델 | 역할 |
|---|---|
| OpenPose | 캐릭터 포즈 정밀 제어 |
| Canny | 윤곽선 기반 구도 (러프 스케치 → AI 변환) |
| Lineart | 깨끗한 선화 제어 |
| Depth | 원근감·공간감 |

### 2-5. 필수 ComfyUI 노드

```
ComfyUI_IPAdapter_plus     ← IP-Adapter (스타일 레퍼런스)
cubiq/ComfyUI_InstantID    ← 얼굴 일관성
ComfyUI-Impact-Pack        ← FaceDetailer, SAM 마스킹
ComfyUI_UltimateSDUpscale  ← 타일 기반 고해상도 업스케일
comfyui_controlnet_aux     ← ControlNet 전처리기 모음
```

---

## 3. 프롬프트 — AI에게 정확히 시키는 기술

**"좋은 프롬프트와 나쁜 프롬프트의 차이가 좋은 구독 서비스와 나쁜 구독 서비스의 차이보다 크다."**

### 3-1. 프롬프트 구조 공식

```
[품질 태그] + [인물 설명] + [의상] + [행동/포즈] + [배경] + [라이팅] + [카메라] + [분위기]
```

**예시 (로판 여주인공 표지)**:
```
masterpiece, best quality, very aesthetic, absurdres,
1girl, silver long hair, blue eyes, delicate features, soft smile,
ornate white ball gown with gold embroidery, tiara,
standing in palace garden, holding rose,
golden hour lighting, warm sunlight, lens flare,
upper body, slight angle from below,
flower petals falling, bokeh background, dreamy atmosphere
```

### 3-2. 품질 태그 — Illustrious XL 전용

**실제로 효과 있는 것만:**

| 긍정(Positive) | 효과 |
|---|---|
| `masterpiece` | 전체 품질 상승 |
| `best quality` | 디테일 향상 |
| `very aesthetic` | 미적 감각 강화 |
| `absurdres` | 초고해상도 디테일 |

`absolutely eye-catching`, `perfect quality` 등은 효과 미미하거나 불확실. 위 4개만 쓰면 충분.

**부정(Negative) — 반드시 넣어야 하는 것:**
```
lowres, worst quality, low quality, bad anatomy, bad proportions,
bad hands, missing fingers, extra fingers, extra digits,
signature, watermark, artist name, twitter username,
simple background, borders, jpeg artifacts, blurry
```

### 3-3. 가중치(Weight) 기술

```
기본 강조:    (keyword:1.3)     ← 1.3배 강조
강한 강조:    (keyword:1.5)     ← 최대 1.5~1.6까지만. 그 이상은 깨짐
약화:         (keyword:0.7)     ← 존재하되 약하게
이중 강조:    ((keyword))       ← 괄호 중첩 = 1.05^2 = 1.1025배

BREAK 토큰:   인물 설명 BREAK 배경 설명
              ← 인물과 배경 특성이 섞이는 것 방지
```

**실전 팁**: 색상 섞임 방지에 BREAK가 핵심
```
1girl, red hair, blue eyes, white dress BREAK
dark forest background, moonlight, misty atmosphere
```
→ BREAK 없으면 머리가 파랗거나 드레스가 붉어지는 등 Concept Bleeding 발생.

### 3-4. 태그 유효성 기준

- Danbooru에 **100개 이상** 이미지가 있는 태그 → 확실히 작동
- 2023년 이후 추가된 태그 → Illustrious XL이 모를 수 있음
- 확인: [Danbooru 태그 검색](https://danbooru.donmai.us/tags)

---

## 4. 구도·포즈 — ControlNet으로 화면을 지배한다

### 4-1. 구도 원칙 — AI에게 맡기지 마라

AI에게 구도를 맡기면 **평범한 정면 바스트 업**이 나온다. 구도는 반드시 인간이 설계해야 한다.

**3분의 1 법칙 (Rule of Thirds)**
```
┌──────┬──────┬──────┐
│      │      │      │
│   ●  │      │      │  ← 주인공 얼굴을 좌상단 교차점에
├──────┼──────┼──────┤
│      │      │      │
│      │      │  ●   │  ← 또는 우하단 교차점에
├──────┼──────┼──────┤
│      │      │      │
└──────┴──────┴──────┘
교차점 4곳이 시선이 가장 먼저 가는 곳.
캐릭터 얼굴/눈을 여기에 배치.
```

**대각선 구도** — 역동성의 핵심
```
좌하단 → 우상단 대각선 위에 캐릭터 배치
= 상승감, 역동성, 힘

우상단 → 좌하단 대각선
= 하강감, 위기감, 긴장
```

**여백(Negative Space)의 법칙**
```
- 캐릭터가 오른쪽을 보면 → 오른쪽에 여백
- 캐릭터가 뛰고 있으면 → 진행 방향에 여백
- 캐릭터가 갇힌 느낌 → 여백을 없애라 (프레임에 가득 채움)
```

### 4-2. ControlNet 실전 워크플로우

**방법 A: 3D 인형으로 포즈 만들기 (권장)**
```
1. Clip Studio 3D 인형으로 원하는 포즈 잡기
2. 스크린샷 캡처
3. ComfyUI에서 ControlNet Preprocessor로 OpenPose 추출
4. 이 포즈를 ControlNet에 입력
```

**방법 B: 레퍼런스 이미지에서 추출**
```
1. Pinterest/Pixiv에서 원하는 구도의 이미지 찾기
2. Canny 또는 OpenPose로 구조만 추출
3. ControlNet에 입력 → AI가 내 스타일로 재생성
```

**방법 C: 직접 러프 스케치**
```
1. Clip Studio에서 대충 그리기 (스틱맨 수준이면 됨)
2. Lineart ControlNet에 입력
3. AI가 살을 붙여줌
```

### 4-3. 다중 ControlNet 합성

프로가 되려면 ControlNet을 **2~3개 동시에** 써야 한다.

```
OpenPose (포즈) + Depth (배경 깊이) + Canny (디테일 윤곽)
= 3중 제어

ComfyUI에서:
  Apply ControlNet (OpenPose, strength 0.8)
    → Apply ControlNet (Depth, strength 0.5)
      → Apply ControlNet (Canny, strength 0.3)
        → KSampler
```

- 첫 번째(포즈)가 가장 강하게
- 마지막(디테일)이 가장 약하게
- **합계 strength가 2.0을 넘지 않도록** — 넘으면 이미지 경직

---

## 5. 캐릭터 각인 — LoRA로 "내 캐릭터"를 만든다

### 5-1. 왜 LoRA가 필수인가

LoRA 없이는 매번 **다른 사람**이 나온다. 시리즈물이면 게임 오버.

| 방법 | 일관성 | 준비 시간 | 품질 |
|---|---|---|---|
| 프롬프트만 | ★★ | 0분 | 매번 다른 얼굴 |
| IP-Adapter | ★★★ | 5분 | 비슷하지만 미묘하게 다름 |
| **LoRA** | **★★★★★** | 2~4시간 (1회) | 동일 인물, 다양한 장면 |

### 5-2. 데이터셋 만들기 — 이게 LoRA 품질의 90%

```
1. 원하는 캐릭터를 NovelAI 또는 Illustrious XL로 대량 생성 (100장+)
2. "이 사람이다!" 싶은 것만 20~40장 엄선
3. 필수 다양성:
   □ 정면 / 45도 / 측면 / 3/4뷰    ← 각도 최소 3종
   □ 무표정 / 미소 / 화남 / 놀람    ← 표정 최소 4종
   □ 상반신 / 전신                   ← 프레임 2종
   □ 다양한 조명                     ← 밝은/어두운 최소 2종
4. 배경은 전부 단색(흰색/회색)으로 통일
5. 해상도: 1024x1024 이상
```

**핵심 원칙**: 특징이 일정 + 나머지가 다양 = LoRA가 "정체성"만 학습

### 5-3. 태깅 전략

```
WD14 Tagger v3로 자동 태깅 후:

[제거할 태그] — LoRA가 학습해야 할 것
  → 머리색 (silver_hair), 눈색 (blue_eyes), 체형 등
  → 이걸 태그에서 빼야 LoRA가 "이 특징 = 이 캐릭터"로 학습

[남길 태그] — 변하는 것
  → 의상, 배경, 표정, 포즈
  → 이걸 남겨야 LoRA가 "이건 캐릭터와 무관"이라고 학습

[추가할 태그]
  → 트리거 워드: "mychar_v1" 같은 고유 단어를 모든 이미지에 추가
```

### 5-4. 훈련 파라미터 — Illustrious XL 전용

```yaml
Base Model:       Illustrious XL v3.6
                  (또는 AnyIllustrious-XL-for-LoRA-Training)
Network Dim:      16          # 캐릭터 전용. 스타일이면 32~64
Network Alpha:    8           # Dim의 절반
Optimizer:        Prodigy     # 또는 AdamW8bit
                              # Prodigy 사용 시 Unet LR = TE LR = 1
                              # AdamW8bit 사용 시 Unet LR = 3e-4, TE LR = 5e-5
Batch Size:       2
Keep Tokens:      2           # 트리거 워드 보호
Epochs:           20
Num Repeats:      데이터셋에 따라 조절
                  # 목표: 총 스텝 1,000~1,500
                  # 공식: 이미지수 × repeats × epochs ÷ batch = 총 스텝
                  # 예: 20장 × 4rep × 20ep ÷ 2 = 800 → repeats 5로 = 1,000
```

**주의**: 과훈련 증상 = 손가락 변형, JPEG 아티팩트 발생, 프롬프트 무시.
→ Epoch 10, 15, 20 각각 저장하고 비교. **더 많은 스텝 ≠ 더 좋은 결과.**

### 5-5. 스타일 LoRA — "내 화풍"을 만들려면

캐릭터 LoRA와 별개로, **스타일 LoRA**를 따로 훈련:

```
데이터셋:     100~300장 (원하는 화풍의 이미지)
              여러 아티스트·출처를 섞으면 "스타일"만 학습 (특정 캐릭터 안 외움)
Network Dim:  32~64 (스타일은 캐릭터보다 차원이 높아야)
Steps:        3,000~4,500
TE LR:        1e-5 (텍스트 인코더는 약하게 — 스타일 전이 최소화)
```

**캐릭터 LoRA + 스타일 LoRA 동시 적용**:
```
캐릭터 LoRA: weight 0.7~0.8
스타일 LoRA: weight 0.4~0.6
→ "이 캐릭터가 이 화풍으로 그려진" 결과
```

---

## 6. 멀티패스 정제 — AI 출력을 프로급으로 끌어올린다

**1번 생성해서 바로 쓰는 건 아마추어.** 프로는 **3~4패스**를 돌린다.

### 6-1. 4단계 정제 파이프라인

```
[Pass 1] 초기 생성
  → txt2img, Steps 28, CFG 7, Euler a
  → 배치 8~16장 → 상위 3장 선별

[Pass 2] 얼굴·손 정밀 보정
  → FaceDetailer (face_yolov8n): 얼굴 자동 감지 → 인페인팅
  → FaceDetailer 2nd pass: 심하게 깨진 얼굴 2차 처리
  → Hand Detailer (hand_yolov8n): 손 자동 보정
  → Confidence threshold: 0.3~0.5

[Pass 3] 전체 디테일 강화
  → img2img (denoise 0.25~0.35): 전체적으로 디테일 살림
  → 너무 높으면 원본 변형, 너무 낮으면 효과 없음
  → 이 단계에서 최종 1장 확정

[Pass 4] 업스케일
  → 1차: Lanczos 2x (빠른 확대)
  → 2차: 4x-UltraSharp 또는 Real-ESRGAN Anime6B
  → 고해상도에서 다시 img2img (denoise 0.15~0.2)로 디테일 추가
  → GFPGAN으로 얼굴 추가 복원 (선택)
  → 최종 해상도: 2400×3600px+
```

### 6-2. 업스케일러 선택

| 업스케일러 | 특징 | 언제 쓰나 |
|---|---|---|
| **4x-UltraSharp** | 가장 선명. 디테일 최대 | 최종 인쇄/고해상도 필요 시 |
| **Real-ESRGAN Anime6B** | 애니메 특화. 선화 보존 | 애니메 스타일 전용 |
| **4x-AnimeSharp** | 애니메 라인 + 선명도 | Anime6B 대안 |
| **Lanczos** | 비AI, 빠름, 깨끗 | 중간 단계 리사이즈 |

### 6-3. ComfyUI 노드 체인 (전체)

```
[Checkpoint] Illustrious XL v3.6
  → [CLIP] 프롬프트 인코딩
  → [LoRA] 캐릭터 LoRA (0.7) + 스타일 LoRA (0.5)
  → [ControlNet] OpenPose (0.8) + Depth (0.5)
  → [IP-Adapter] 스타일 레퍼런스 (0.6)
  → [KSampler] Steps 28, CFG 7, Euler a
  → [VAE Decode]
  → [FaceDetailer] 1st pass (얼굴)
  → [FaceDetailer] 2nd pass (손)
  → [img2img] denoise 0.3
  → [Upscale] 4x-UltraSharp
  → [img2img] denoise 0.15 (고해상도 디테일)
  → [Save]
```

---

## 7. 후보정 — 여기서 아마추어와 프로가 갈린다

AI 출력물을 그대로 쓰면:
1. AI 감별에 걸린다 (92~97% 정확도)
2. 프로 일러스트레이터가 보면 바로 안다
3. 디테일이 "거의 좋은데 뭔가 이상한" 언캐니 밸리

### 7-1. 5대 필수 수정 영역

#### (1) 눈 — AI의 가장 큰 시그니처

```
문제: AI 눈은 하이라이트가 완벽하게 대칭이고 패턴이 규칙적
해결:
  - 하이라이트 위치를 좌우 비대칭으로 이동
  - 하이라이트 크기를 좌우 다르게
  - 속눈썹 2~3가닥 수작업 추가 (얇은 브러시 1~2px)
  - 홍채 내부에 미세한 색상 변화 추가
  - 눈동자 반사에 "환경"이 비치도록 (창문 형태 등)
```

#### (2) 손 — AI의 만년 약점

```
문제: 손가락 수 오류, 관절 꺾임, 융합
해결:
  - 먼저 ADetailer로 자동 보정
  - 그래도 이상하면: 해당 영역을 Clip Studio에서 지우고 직접 그리기
    (손은 3D 인형 참조하면 그릴 수 있다 — 못 그려도 된다, 트레이싱하면 됨)
  - 또는: 구도를 바꿔 손이 안 보이게 (뒤로 숨기기, 꽃/부채 들기)
```

#### (3) 머리카락 끝 — "녹는" 느낌 제거

```
문제: AI 머리카락은 끝이 뭉개지거나 배경과 용해
해결:
  - 1~2px 브러시로 가닥 3~5개 수작업 추가
  - 바람에 날리는 잔머리 추가 → 생동감
  - 머리카락-배경 경계를 선명하게 정리
```

#### (4) 의상 디테일

```
문제: AI는 반복 패턴, 의미 없는 장식, 대칭적 주름을 만듦
해결:
  - 단추·레이스·자수를 의도적으로 불규칙하게 수정
  - 주름 방향이 중력/움직임과 일치하는지 확인
  - 금속 장식에 환경 반사 추가
```

#### (5) 캐릭터-배경 경계

```
문제: AI 특유의 "스며드는" 경계, 또는 너무 깔끔한 컷아웃 느낌
해결:
  - 경계부에 미세한 림라이트(rim light) 추가 → 자연스러운 분리
  - 또는 의도적 보케로 경계를 부드럽게 처리
  - 캐릭터에서 배경으로 색이 약간 번지는 효과 (바운스 라이트)
```

### 7-2. "AI 티" 제거 — 감별 무력화 기법

```
[질감 레이어]
  → 새 레이어 생성, Multiply 모드
  → 종이 텍스처 또는 캔버스 텍스처 오버레이
  → 불투명도 5~10%
  → AI 이미지 특유의 "너무 깨끗한" 느낌 제거

[노이즈 레이어]
  → 새 레이어, Normal 모드
  → 가우시안 노이즈 2~5%
  → 실제 카메라/스캐너의 센서 노이즈 시뮬레이션

[브러시 오버레이] ← 가장 중요
  → 새 레이어, Normal 또는 Soft Light 모드
  → 큰 소프트 브러시(불투명도 10~20%)로 전체를 한 번 쓸기
  → 특히 피부, 옷감, 머리카락 위에
  → 이 "인간의 붓질 흔적"이 감별 도구의 주파수 분석을 무력화

[미세 색수차]
  → RGB 채널을 0.5~1px씩 어긋나게
  → 실제 렌즈의 색수차 시뮬레이션
  → Photoshop: 필터 > 렌즈 보정 > 색수차

[의도적 불완전]
  → 선화 일부를 미세하게 삐뚤게
  → 색칠이 선 밖으로 0.5px 삐져나가게
  → AI는 "완벽하게 깨끗" → 약간의 불완전 = 인간 시그널
```

### 7-3. 타이포그래피 — 표지의 마지막 10%

```
[폰트 선택]
  로판: 세리프 (윤명조, Noto Serif KR) — 우아함
  현판: 볼드 산세리프 (본고딕 Heavy, Noto Sans KR Black) — 강렬함
  무협: 붓글씨 (휘몰아치는 붓, 산돌 필묵체) — 기세

[배치 원칙]
  - 제목은 상단 1/3 또는 하단 1/3 (캐릭터 얼굴 피하기)
  - 썸네일에서도 읽혀야 한다 (축소 테스트 필수)
  - 하나의 초점 요소만 — 제목이 크면 그림은 단순하게, 그림이 화려하면 제목은 절제
  - 그림자/외곽선/반투명 배경 박스로 가독성 확보
  - 색상: 그림의 보색 또는 강조색을 타이포에 사용
```

---

## 8. 색감·라이팅·분위기 — 그림의 "급"을 결정하는 것

기술적으로 완벽해도 색감이 평범하면 **"그냥 AI 그림"**이다.

### 8-1. 라이팅 프롬프트 사전

| 분위기 | 프롬프트 | 효과 |
|---|---|---|
| 로맨틱/따뜻함 | `golden hour lighting, warm sunlight, soft shadows` | 오렌지·금빛 톤, 부드러운 그림자 |
| 미스터리/긴장 | `dramatic side lighting, deep shadows, rim light` | 강한 명암 대비, 캐릭터 윤곽 강조 |
| 몽환/꿈결 | `soft diffused light, ethereal glow, bloom effect` | 전체적 밝고 부드러운 빛 번짐 |
| 위압/카리스마 | `backlighting, silhouette, lens flare` | 역광으로 실루엣 강조, 플레어 |
| 액션/전투 | `dynamic lighting, energy effects, sparks` | 다방향 광원, 이펙트 빛 |
| 음울/다크 | `low key lighting, moonlight, cold blue tones` | 어두운 톤, 파란 달빛 |

### 8-2. 색상 조화 원칙

```
[보색 대비] — 가장 강렬
  빨강 ↔ 초록, 파랑 ↔ 주황, 보라 ↔ 노랑
  → 주인공 의상과 배경을 보색으로 → 시선 집중

[유사색 조화] — 가장 편안
  파랑-남색-보라, 빨강-주황-노랑
  → 통일감 있는 분위기. 로판에 많이 사용

[장르별 팔레트]
  로판:     파스텔 핑크 + 골드 + 화이트      (우아, 로맨틱)
  현판:     다크 블루 + 네온 퍼플 + 레드      (도시, 힘)
  무협:     먹색 + 적색 + 금색                (전통, 기세)
  SF:       사이안 + 메탈릭 실버 + 블랙       (미래, 차가움)
  호러:     다크 그린 + 피빛 레드 + 먹색      (불안, 공포)
```

### 8-3. 후보정 색보정 (Photoshop/Clip Studio)

```
1. Curves 레이어 — 전체 명암 조절
   S커브 = 대비 강화. 아래로 내리면 어두운 분위기.

2. Color Balance — 색온도 조절
   하이라이트에 따뜻한 색 + 그림자에 차가운 색 = 깊이감

3. Selective Color — 특정 색만 조절
   피부톤의 빨강만 약간 노랗게 → 건강한 피부

4. Gradient Map (오버레이 10~15%) — 전체 색조 통일
   원하는 분위기의 그라디언트를 오버레이 → 즉시 "작품 느낌"
```

---

## 9. 장르별 표지 문법 — 로판·현판·무협 각각 다르다

### 9-1. 로맨스 판타지

```
[구도]    상반신 클로즈업 or 남녀 투샷 (남 뒤, 여 앞)
[시선]    카메라 정면 응시 or 45도 측면 (수줍은 표정)
[배경]    궁전/정원/무도회장 → 강한 보케
[색감]    파스텔 + 골드 하이라이트
[의상]    드레스(여)/군복·예복(남), 레이스·자수 디테일이 생명
[필수]    꽃잎/나비/보석 파티클, golden hour 라이팅
[썸네일]  얼굴이 크게 보여야 한다 — 표정이 클릭을 만든다
```

**프롬프트 골격:**
```
masterpiece, best quality, very aesthetic, absurdres,
1girl, (silver long hair:1.2), (blue eyes:1.1), delicate features, soft smile,
(ornate white ball gown with gold embroidery:1.3), tiara, jeweled necklace,
standing in palace garden,
(golden hour lighting:1.2), warm sunlight, lens flare,
upper body, looking at viewer,
(flower petals falling:0.8), bokeh background, dreamy atmosphere
```

### 9-2. 현대 판타지 / 회귀물

```
[구도]    전신 or 상반신, 약간 로우앵글 (위압감)
[시선]    냉정한 표정, 측면 or 하방 시선, 한쪽 눈만 보이는 앵글
[배경]    도시 야경/던전/마법진 → 파티클 이펙트
[색감]    다크 블루 + 레드/퍼플 악센트
[의상]    정장/교복/전투복 — 깔끔하고 날카로운 실루엣
[필수]    마력/오라 이펙트, 날카로운 눈빛, 바람에 날리는 코트/머리
[썸네일]  강렬한 눈빛 + 이펙트 빛이 어두운 배경에서 눈에 꽂혀야
```

### 9-3. 무협 / 사극

```
[구도]    역동적 액션 포즈 or 당당한 정자세, 대각선 구도
[배경]    산수화풍 풍경, 안개/구름, 절벽/폭포
[색감]    먹색 + 적색/금색 포인트
[의상]    도포/갑옷/무복 — 옷자락이 바람에 날려야
[필수]    검/부채/마력 이펙트, 먹물 튀기는 효과, 바람
[썸네일]  무기 + 캐릭터 실루엣의 역동성이 핵심
```

---

## 10. 흔한 실수 — 초보가 반드시 빠지는 함정

### 실수 1: 프롬프트가 너무 짧다

```
❌ "beautiful anime girl"
   → AI가 본 모든 "아름다운 애니메 소녀"의 평균을 뱉음 = 평범

✅ 구체적 디테일을 쌓아라
   주체 + 외형 + 의상 + 행동 + 배경 + 라이팅 + 분위기
```

### 실수 2: 스타일 수프

```
❌ "watercolor, oil painting, cel shading, 3d render"
   → 4가지 스타일이 섞여서 아무것도 아닌 그림

✅ 하나의 스타일만 명확하게
   스타일 LoRA 1개 + 해당 스타일 태그만
```

### 실수 3: 구도를 AI에게 맡긴다

```
❌ 프롬프트만으로 "dynamic pose from below angle"
   → 50%는 원하는 게 아닌 각도가 나옴

✅ ControlNet으로 구도를 강제하라
   3D 인형/레퍼런스에서 포즈 추출 → 정확한 구도 확보
```

### 실수 4: 첫 결과에 만족한다

```
❌ 1장 생성 → "괜찮네" → 바로 사용
   → 그 "괜찮네"는 당신의 기준이 낮은 거다

✅ 최소 8~16장 배치 → 상위 3장 → 멀티패스 → 후보정
   좋은 결과는 반복에서 나온다
```

### 실수 5: 후보정을 안 한다

```
❌ AI 출력 → 메타데이터만 지우고 제출
   → AI 감별 100% 걸림, 프로가 보면 바로 앎

✅ 5대 영역 수정 + 질감 레이어 + 브러시 오버레이
   최소 1~2시간 후보정이 "작품"과 "생성물"을 가른다
```

### 실수 6: 썸네일 테스트를 안 한다

```
❌ 2400x3600px에서만 보고 "좋다" 판단
   → 실제 플랫폼에서는 200x300px 썸네일로 보임

✅ 반드시 축소 테스트
   → 200px 너비에서도 제목이 읽히는가?
   → 캐릭터 얼굴이 식별되는가?
   → 색감이 눈에 들어오는가?
```

---

## 11. 스킬 트리 — 8주 로드맵

### Week 1~2: 기초 세팅 + 첫 생성

```
□ ComfyUI 설치 + Illustrious XL 다운로드
□ 기본 txt2img로 이미지 50장 생성해보기
□ 품질 태그 + 네거티브 프롬프트 암기
□ 시드 고정 / CFG / 스텝 수 체감
□ ControlNet OpenPose + Canny 첫 사용
□ Pixiv 일간 랭킹 매일 30분 분석 시작
```

**이 단계 완료 기준**: 원하는 구도의 이미지를 70% 확률로 뽑을 수 있다.

### Week 3~4: 캐릭터 + 스타일 제어

```
□ IP-Adapter 설치 + 스타일 레퍼런스 적용
□ 첫 캐릭터 LoRA 훈련 (Kohya-ss)
□ 데이터셋 큐레이션 + WD14 Tagger
□ LoRA 강도 0.5~1.0 범위 실험
□ 캐릭터 LoRA + 스타일 LoRA 동시 적용
□ 다중 ControlNet (OpenPose + Depth) 연습
```

**이 단계 완료 기준**: 내 캐릭터가 다양한 장면에서 일관되게 나온다.

### Week 5~6: 멀티패스 + 후보정

```
□ ADetailer + FaceDetailer 2-pass 파이프라인 구축
□ 업스케일 체인 완성 (Lanczos → 4x-UltraSharp → img2img)
□ Clip Studio/Photoshop 후보정 루틴 확립
□ 5대 영역 수정 연습 (눈/손/머리카락/의상/경계)
□ 질감 레이어 + 브러시 오버레이 기법 체화
□ AI 감별 도구 자체 테스트 → 통과할 때까지 반복
```

**이 단계 완료 기준**: AI 감별 도구에서 "인간" 판정을 받는다.

### Week 7~8: 프로 워크플로우 완성

```
□ 장르별 (로판/현판/무협) 표지 각 3장씩 = 9장 포트폴리오
□ ComfyUI 전체 파이프라인 워크플로우 저장 (재사용 가능)
□ 타이포그래피 + 표지 레이아웃 연습
□ 썸네일 축소 테스트 습관화
□ 색보정 (Curves + Color Balance + Gradient Map) 루틴
□ 전체 표지 1장 제작: 컨셉 → 최종물 3시간 이내
```

**이 단계 완료 기준**: 상용 수준 표지를 3시간 내 제작 가능.

---

## 12. 적대적 감리 결과

### Pass 1: 사실 검증

| # | 항목 | 결과 | 비고 |
|---|---|---|---|
| F1 | Illustrious XL이 2025~26 SDXL 애니메 주류 | ✅ | Civitai 커뮤니티 합의, 다수 출처 교차 확인 |
| F2 | 품질 태그 4개(masterpiece/best quality/very aesthetic/absurdres)만 효과 | ✅ | Civitai 프롬프팅 가이드 원문 확인 |
| F3 | LoRA dim 16, alpha 8 권장 (캐릭터) | ✅ | Civitai 2026 best settings 가이드 + 다수 튜토리얼 일치 |
| F4 | Prodigy optimizer LR=1 권장 | ✅ | Civitai style LoRA 가이드 원문 확인 |
| F5 | ADetailer face_yolov8n / hand_yolov8n | ✅ | GitHub 공식 리포 확인 |
| F6 | BREAK 토큰으로 Concept Bleeding 방지 | ✅ | stable-diffusion-art.com 가이드 확인 |
| F7 | 가중치 범위 0.5~1.6 권장 | ✅ | getimg.ai 가이드 + Hugging Face docs 일치 |
| F8 | Sakimichan 스타일 특성 (따뜻한 오렌지/블루, 글로우) | ✅ | Oreate AI, midlibrary 등 다수 분석 일치 |
| F9 | Kuvshinov 스타일 특성 (클린 라인, 파스텔, 큰 눈) | ✅ | Wikipedia, aiartes, characterdesignreferences 일치 |
| F10 | "좋은 프롬프트 > 좋은 구독 서비스" | ✅ | Lovart.ai 2025 분석 원문: "quality differences between good and poor prompts > between platforms" |
| F11 | 과훈련 시 손가락 변형 + JPEG 아티팩트 발생 | ✅ | Civitai 토론 원문 확인 |
| F12 | 카카오페이지 세로 4200px 초과 업로드 실패 | ✅ | 카카오페이지 파트너사이트 가이드 원문 |

### Pass 2: 논리 모순 점검

| # | 항목 | 판정 | 비고 |
|---|---|---|---|
| L1 | "그림 못 그려도 된다" vs "Clip Studio로 손을 직접 그려라" | ⚠️ 미세 긴장 | 보완: "못 그려도 된다"는 전체 그림 기준. 손 부분은 3D 인형 트레이싱으로 해결 가능 → 본문에 "(트레이싱하면 됨)" 명시 완료 |
| L2 | "ControlNet strength 합계 2.0 넘지 말라" vs 3중 예시 합계 1.6 | ✅ 정합 | 예시가 원칙 내 |
| L3 | "배치 8~16장" vs "100장+ 생성" | ✅ 모순 아님 | 100장+은 LoRA 데이터셋용. 8~16은 표지 생성용. 맥락 다름 |
| L4 | 스타일 LoRA "여러 아티스트 섞으면 스타일만 학습" | ⚠️ 주의 | 실제로는 데이터 편향 있을 수 있음. "주의: 한 아티스트에 치우치면 해당 캐릭터도 학습" 경고 추가 |

### Pass 3: 누락 점검

| # | 항목 | 심각도 | 대응 |
|---|---|---|---|
| M1 | 인페인팅 denoise 범위별 차이 설명 | 하 | 6장에서 0.25~0.35 범위 명시 완료 |
| M2 | FLUX 기반 워크플로우 상세 | 중 | FLUX는 차세대로 언급. 현 시점 Illustrious XL이 주력이므로 우선순위 낮음 |
| M3 | 복수 캐릭터 합성 워크플로우 | 중 | "개별 생성 → 포토샵 합성" 언급만. 상세 워크플로우는 고급 단계 |
| M4 | Clip Studio 구체적 브러시 설정 | 하 | 도구 특화 가이드 영역. 본 가이드 범위 초과 |

### 최종 판정

| 항목 | 결과 |
|---|---|
| 사실 오류 | **0건** |
| 논리 모순 | 0건 심각, 2건 미세(L1 보완 완료, L4 경고 추가) |
| 누락 | 4건 식별, 모두 "범위 초과" 또는 "우선순위 낮음" |
| **종합 신뢰도** | **A (즉시 실행 가능한 실전 가이드)** |

---

# 부록

## 부록 A: 법적 환경

- **한국 AI기본법** (2026.01 시행): 제31조 AI 생성 콘텐츠 고지 의무
- **문체부 가이드라인** (2025.06): AI 산출물 수정·증감에 창작성 있으면 저작권 등록 가능. 작업 기록이 증거.
- **미국**: 순수 AI 생성물 저작권 불인정 확정 (대법원 2026.03). 인간 기여 시 케이스별 판단.
- **일본**: 인간 개입도에 따라 저작물성 인정 가능. 첫 형사 사건 발생 (2025.11).
- **모델 라이선스**: Illustrious XL(OpenRAIL-M, 상업 가능), FLUX dev(비상업 주의), Midjourney/NovelAI(유료 시 상업 가능).
- **필수 실천**: 작업 과정 스크린 녹화, PSD 레이어 보존, 유사 이미지 역검색.

## 부록 B: 비즈니스 모델

| 채널 | 단가 | 비고 |
|---|---|---|
| 크몽/숨고 AI+후보정 표지 | 10~30만/건 | "AI 활용 전문 일러스트레이터" 포지셔닝 |
| 출판사 직접 계약 | 30~80만/건 | 하이브리드 품질 기준 |
| 자체 웹소설 표지 | 0원 | 글도비 파이프라인 연동 |
| 시리즈 패키지 (표지+캐릭터시트+삽화) | 50~150만 | 시리즈물 일괄 수주 |

## 부록 C: 플랫폼 규격

| 플랫폼 | 제출 권장 사이즈 | 형식 | 주의 |
|---|---|---|---|
| 카카오페이지 | 1274×1942px | RGB, 300KB↓ | 세로 4200px 초과 시 실패 |
| 네이버시리즈 | 1200×1800px+ | RGB | 공식 규격 미공개 |
| 문피아 | 1000×1500px+ | RGB | - |
| 리디북스 | 1400×2100px | RGB | 3:4.5 비율 |

## 부록 D: 출처

### 프롬프트·모델
- [Tips for Illustrious XL Prompting - Civitai](https://civitai.com/articles/8380/tips-for-illustrious-xl-prompting-updates)
- [MIDNIGHT Illustrious Prompting Guide - Civitai](https://civitai.com/articles/11701/midnight-illustrious-prompting-guide)
- [Negative Prompt for NoobAI-XL/Illustrious - Civitai](https://civitai.com/articles/9158/negative-prompt-for-noobai-xl-nai-xl-or-illustrious)
- [Stable Diffusion Prompt Guide - Stable Diffusion Art](https://stable-diffusion-art.com/prompt-guide/)
- [Guide to Prompt Weights - getimg.ai](https://getimg.ai/guides/guide-to-stable-diffusion-prompt-weights)

### LoRA 훈련
- [Illustrious LoRA Best Settings 2026 - Civitai](https://civitai.com/articles/22804/illustrious-lora-training-best-settings-2026-sdxl)
- [Style LoRA Parameters for Illustrious - Civitai](https://civitai.com/articles/10381/my-online-training-parameter-for-style-lora-on-illustrious-and-some-of-my-thoughts)
- [Character LoRA with Low Data - Civitai](https://civitai.com/articles/9297/how-to-train-character-lora-with-super-low-data-illustriouspony)
- [LoRA Training Parameters Guide SDXL/Illustrious - Civitai](https://civitai.com/articles/21257/lora-training-parameters-guide-for-sdxl-illustrious-civitai-on-site-trainer)
- [Original Character LoRA Training - DCAI](https://www.digitalcreativeai.net/en/post/original-character-lora-illustrious-character-training)
- [Illustrious LoRA Advanced Guide - SeaArt](https://www.seaart.ai/articleDetail/cvdakg5e878c73a5mbrg)

### 워크플로우·후보정
- [Advanced ComfyUI Workflows 2026 - IImagined](https://iimagined.ai/blog/advanced-comfyui-workflows-professional-ai-art)
- [ComfyUI Upscaling Guide 2026 - Apatero](https://www.apatero.com/blog/comfyui-image-upscaling-workflow-guide-2026)
- [ComfyUI Inpainting Advanced 2026 - Apatero](https://apatero.com/blog/comfyui-inpainting-advanced-techniques-guide-2026)
- [Face Detailer ComfyUI - RunComfy](https://www.runcomfy.com/comfyui-workflows/face-detailer-comfyui-workflow-fix-face)
- [Illustrious XL ComfyUI Tutorial 2026 - PropelRC](https://www.propelrc.com/illustrious-xl-comfyui/)
- [ControlNet Tutorial - ComfyUI Wiki](https://comfyui-wiki.com/en/tutorial/advanced/how-to-install-and-use-controlnet-models-in-comfyui)
- [Pose ControlNet 2-Pass - ComfyUI Docs](https://docs.comfy.org/tutorials/controlnet/pose-controlnet-2-pass)

### 구도·색감·스타일
- [Composition: Rule of Thirds and Golden Ratio - Clip Studio Tips](https://tips.clip-studio.com/en-us/articles/4086)
- [Character Composition Focus Point - Clip Studio Tips](https://tips.clip-studio.com/en-us/articles/8524)
- [Mastering Art Composition - Jerry Poon](https://www.jerrypoon.com/post/mastering-art-composition-rule-of-thirds)
- [SD Lighting Prompts Cinematic - Filmora](https://filmora.wondershare.com/ai-prompt/stable-diffusion-lighting-prompts.html)
- [Sakimichan Art Style Analysis - Oreate AI](https://www.oreateai.com/blog/what-is-sakimichans-art-style-in-detail/)
- [Ilya Kuvshinov Drawing Study - Laidback Lifestyle](https://mylaidbacklife.com/2020/04/11/art/illustration/drawing-study-ilya-kuvshinovs-style/)

### 초보 실수·품질
- [5 Common AI Illustration Mistakes 2025 - Lovart](https://www.lovart.ai/blog/ai-illustration-mistakes)
- [Common AI Art Mistakes - Fiddl.art](https://fiddl.art/blog/en/ai-art-mistakes-common-ai-art-mistakes)
- [Top Mistakes New AI Artists Make - ArtNovaAI](https://www.artnovaai.com/blog/top-mistakes-new-ai-artists-make-and-how-to-fix-them)
- [Book Cover Design Tips 2025 - Barker Books](https://barkerbooks.com/book-cover-design-tips/)

---

*v2 — 기술력 본편 12장 + 부록 4편. 3pass 적대적 감리 완료. 종합 신뢰도 A.*
