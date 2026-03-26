# 웹소설 일러스트 AI 대체 가능성 조사 보고서

> 작성일: 2026-03-24
> 방법론: 5-TF 병렬 웹서치 + 4-TF 병렬 에이전트 → 1pass 통합 → 2pass 적대적 감리 → 3pass 확정
> 조사 범위: 국내/해외(일본·중국·영미권) 업계 현황, AI 모델·서비스, 실무 방법론, 법적·시장 리스크

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [국내 업계 현황](#2-국내-업계-현황)
3. [해외 업계 동향](#3-해외-업계-동향)
4. [AI 모델·서비스 비교](#4-ai-모델서비스-비교)
5. [실무 방법론·워크플로우](#5-실무-방법론워크플로우)
6. [비용 구조 분석](#6-비용-구조-분석)
7. [법적·제도적 환경](#7-법적제도적-환경)
8. [한계점·리스크](#8-한계점리스크)
9. [글도비 프로젝트 시사점](#9-글도비-프로젝트-시사점)
10. [적대적 감리 결과](#10-적대적-감리-결과)
11. [출처](#11-출처)

---

## 1. Executive Summary

**한 줄 결론:** 웹소설 일러스트의 AI 대체는 기술적으로 "단일 표지는 상용 수준, 시리즈 일관성은 미완" 단계이며, 법적 불확실성·독자 반감·감별 기술 발전으로 인해 **"AI+인간 하이브리드" 모델이 현 시점 최적해**다.

| 축 | 현황 | 전망 |
|---|---|---|
| 기술 성숙도 | 단일 표지 품질은 상용 수준. Niji V7/NovelAI V4.5가 애니메 최전선 | 캐릭터 일관성: 단순 포트레이트 70%, 장면 변화 시 40%까지 하락. FLUX Kontext가 제로샷 일관성 돌파구 |
| 비용 절감 | 인간 대비 1/10~1/50 수준 | GPU 클라우드 비용 하락(RunPod RTX4090 $0.69/hr), SaaS $10~30/월 |
| 법적 안전성 | 한·미·일 모두 "인간 기여 필수" 원칙 확립 | 미 대법원 Thaler 기각(2026.03) 확정. 한국 AI기본법 시행(2026.01). 70건+ AI 저작권 소송 진행 중 |
| 시장 수용도 | 국내: 별점 테러 수준의 강한 반감. AI 감별 정확도 92~97% | 한국 AI기본법 AI 생성 콘텐츠 고지 의무. EU AI Act 2026.08 마킹 의무 |
| 실무 채택 | 컨셉·러프 용도로 은밀히 확산. 중국은 산업화 단계 | 하이브리드 워크플로우가 글로벌 표준으로 수렴 중 |
| 일자리 영향 | 영국 AOI: 일러스트레이터 32% 일감 상실. 중국 게임업계 70% 감소 | 스탠퍼드: AI 허용 마켓 → 비AI 아티스트 23% 추가 이탈 |

---

## 2. 국내 업계 현황

### 2.1 주요 사건

- **'이별해주세요, 제발!' 사건**: 네이버 시리즈 웹소설의 표지·삽화에 AI 사용이 발각되어 작가·출판사 모두 공식 사과, 당일 일러스트 전량 삭제. 웹소설 업계 최대 AI 논란 사건. ([헤럴드경제](https://biz.heraldcorp.com/article/3158791))
- **로판 웹소설 AI 표지 연쇄 발각**: 루리웹 등 커뮤니티에서 다수 작품의 AI 표지 사용이 고발되며 "도둑질로 만든 그림"이라는 비판 확산. ([루리웹](https://bbs.ruliweb.com/community/board/300143/read/61504061))
- **별점 테러 현상**: AI 사용 의혹만으로도 별점 테러가 발생. 한국 특유의 강경 반응. ([블로터](https://www.bloter.net/news/articleView.html?idxno=650498), [머니투데이](https://www.mt.co.kr/tech/2026/03/11/2026022508052980108))
- **노벨피아 실태**: 실시간 인기 Top10 중 약 40%가 AI 생성 표지 사용 (2023년 기준, 이후 증가 추세).

### 2.2 플랫폼 정책

| 플랫폼/기관 | 정책 |
|---|---|
| 한국웹소설협회 | 유료 작품·공모전 AI 표지 사용 금지 |
| 카카오페이지 | 공식 AI 금지 정책 미발표. 심의 기준은 폭력성·선정성 중심 |
| 네이버시리즈 | 공식 정책 미발표. AI 감별 체계 부재 |
| 한국 AI기본법 | **2026.01 시행**: 제31조 AI 생성 콘텐츠 고지 의무. 비가시 워터마크 허용 |

- 국내 콘텐츠 사업체 생성형 AI 활용률: 20% (한국콘텐츠진흥원 조사). 만화·웹툰 분야는 보조 업무 위주.
- **크몽/숨고**: 92개 이상 AI 표지 제작 서비스 등록, 5,000원부터. Midjourney+포토샵 후보정이 주류.

### 2.3 비용 구조 (국내)

| 구분 | 가격 |
|---|---|
| 일반 일러스트레이터 표지 | 80~150만 원 |
| 인기 일러스트레이터 | 건당 300~500만 원 |
| 캐릭터 시트 (풀바디) | 50~100만 원 |
| AI 생성 (자체 제작) | 거의 0원 (GPU 비용만) |
| AI 생성 (외주/크몽) | 0.5~5만 원 |

→ 영세 출판사·초보 작가에게 AI의 유혹이 강력한 구조적 원인.

---

## 3. 해외 업계 동향

### 3.1 일본

- **문화청 판단 기준**: 프롬프트 설계 세밀도, 재생성·수정 반복 횟수, 후편집·합성·보정 등 "인간의 선택과 판단 축적 정도"로 저작물성 판단.
- **첫 형사 사건 (2025.11)**: 지바현 경찰이 Stable Diffusion으로 생성한 이미지를 무단 복제한 혐의로 검찰 송치. AI 생성물이 저작물로 인정된 일본 최초 형사 사례. ([나우뉴스](https://m.nownews.seoul.co.kr/news/global-topic/international-insight/2025/11/20/20251120601013))
- **GA문庫 등 공모전**: AI 사용 작품에 대한 주의사항 추가 움직임.
- **소학관 NOVELOUS**: 북미 라이트노벨 배급 앱. Mantra AI 번역 활용, **일러스트 영역은 인간 작가 유지** 방침.
- **Pixiv**: 2023년 AI 생성 작품 별도 태그/필터링 시스템 도입. DLsite, FANZA도 AI 생성 콘텐츠 표시 의무화.
- **나로우(なろう) 계열**: 개인 작가가 AI 삽화 사용 증가하나, 상업 출판 전환 시 인간 일러스트레이터로 교체가 관행.

### 3.2 중국

- **阅文그룹 (텐센트 산하)**: 2025년 "IP+AI" 전략 전면 채택.
  - AI 만화극(漫剧) **~1,000편** 출시, 100편 이상 조회수 1,000만 돌파, 12편 1억 돌파.
  - AI 만화극 하반기 매출 **1억 위안 돌파** (약 190억 원). ([신랑재경](https://finance.sina.com.cn/jjxw/2026-03-18/doc-inhrkskx9409548.shtml))
  - "妙笔通鉴" AI 지식베이스 출시 → 작가-AI 상호작용 40% 증가.
  - DeepSeek R1 모델 통합, 전 업계 작가 대상 개방.
  - 해외 플랫폼 WebNovel: AI 번역 작품 17,000부 이상, 매출 YoY 39% 성장.
- **카카오엔터테인먼트 Helix Shorts**: 웹툰 패널 → 40초 숏폼 영상 변환 AI. 제작 시간 수 주→수 시간, 비용 수천 달러→수 달러로 단축.
- **게임 업계 영향**: 중국 게임업계 일러스트레이터 일자리 **70% 감소**, 생산성 40배 증가. ([Artisana](https://www.artisana.ai/articles/chinas-video-game-ai-art-crisis-40x-productivity-spike-70-job-loss))
- **핵심 시사점**: 중국은 AI 일러스트·만화를 **대규모 산업화 단계**에 진입. 한국·일본 대비 압도적으로 공격적.

### 3.3 영미권

- **Amazon KDP**: AI 생성 콘텐츠 공시(disclosure) 의무화. AI-generated vs AI-assisted 구분.
  - 미공시 시 작품 삭제 가능.
  - 독자에게는 AI 라벨 비공개 (내부 모니터링 용도, 2025.12 기준).
  - 한때 한 카테고리 베스트셀러 100위 중 81개가 AI 스팸 도서로 의심된 사례 (2023년, 특정 카테고리 한정).
- **Midjourney V7** (2025.04.03): Draft Mode, Omni Reference 도입. 포토리얼리즘·자연어 이해도 대폭 향상. ([Midjourney](https://docs.midjourney.com/))
- **"Anti-AI" 미학 트렌드**: 수작업 느낌(붓자국, 수제 요소, 불완전한 텍스처)을 강조하는 역트렌드 형성.
- **Royal Road**: LitRPG, Progression Fantasy 장르 인디 작가들 중심으로 AI 커버아트 사용 보편화.
- **하이브리드 트렌드**: AI 생성 → 인간 편집·타이포그래피·레이아웃 = 저작권 보호 가능 + 품질 보장.

---

## 4. AI 모델·서비스 비교

### 4.1 주요 모델 타임라인 (2025~2026)

| 시점 | 사건 | 의의 |
|---|---|---|
| 2025.02.28 | NovelAI V4 Full | 자체 아키텍처 전환, SD 의존 탈피 |
| 2025.03 | GPT-4o 네이티브 이미지 | 지브리풍 열풍. 범용 AI의 이미지 생성 진입 |
| 2025.04.03 | Midjourney V7 | Draft Mode/Omni Reference. 품질 도약 |
| 2025.05.05 | NovelAI V4.5 Curated | 클린 데이터셋, 안전성/일관성 개선 |
| 2025.05.29 | NovelAI V4.5 Full | 충실도 향상, 확장 데이터셋 |
| 2025.09 | Illustrious XL v3.6 | SDXL 애니메 모델 선두 확정 |
| 2025.11 | FLUX.2 출시 (Black Forest Labs) | 프로덕션급 오픈소스 32B dev / 9B klein |
| 2025.11 | Z-Image (Alibaba) | FLUX급 품질을 소형 모델로 구현 |
| 2026.01.09 | **Niji V7** | 애니메 AI 일러스트 최고 수준. 눈동자/라인아트 혁신 |

**아키텍처 트렌드**: DiT(Diffusion Transformer)가 UNet을 대체하는 추세. FLUX, SD3, NovelAI V4 모두 Transformer 기반.

### 4.2 모델 비교 매트릭스

| 모델 | 애니메 적합성 | 제어력 | 속도 | 캐릭터 일관성 | 비고 |
|---|---|---|---|---|---|
| **Niji V7** (2026.01) | ★★★★★ | ★★☆ | 빠름 | ★★★ (--cref 미지원) | 애니메 최고 품질, 단 캐릭터 레퍼런스 기능 미개발 |
| **Midjourney V7** (2025.04) | ★★★★ | ★★★ (Omni Ref) | 빠름 | ★★★☆ | 판타지·SF·호러 표지 최강 |
| **NovelAI V4.5** (2025.05) | ★★★★★ | ★★★☆ (Danbooru 태그) | 보통 | ★★★★ (멀티캐릭터) | 즉시 사용 가능한 가장 쉬운 옵션 |
| **SDXL + Illustrious XL** | ★★★★★ | ★★★★★ | 보통 | ★★★★★ (LoRA) | 2025~26 SDXL 애니메 사실상 주류 |
| **FLUX.2 dev** (2025.11) | ★★★★ | ★★★★ | 느림(4x) | ★★★★ | 32B. 포즈 정확도 최고. 24GB+ VRAM 필요 |
| **FLUX Kontext** (2025~26) | ★★★★ | ★★★★★ | 보통 | ★★★★★ | 12B DiT. 제로샷 캐릭터 일관성 돌파구 |
| **Pony Diffusion** | ★★★★★ | ★★★★ | 보통 | ★★★★ | 스타일화/NSFW 특화 |

### 4.3 애니메 특화 체크포인트 (커뮤니티)

| 체크포인트 | 기반 | 특징 | 현재 위치 |
|---|---|---|---|
| **Illustrious XL v3.6** | SDXL 파인튠 | 최대 1536x1536, 라인워크/색상/해부학 우수 | **2025~26 SDXL 애니메 주류** |
| **Hassaku XL v2.2** | Illustrious 파인튠 | 고품질 애니메 파생 모델 | Illustrious 생태계 인기 파생 |
| **AnimagineXL 4.0** | SDXL 완전 재훈련 | 8.4M 애니메 이미지. 범용 안정적 | Illustrious 등장 후 비중 감소 |
| **AAM XL AnimeMix** | SDXL | 풍부한 디테일, 캐릭터/씬 모두 강점 | Civitai 최고 평가 |
| **NTR Mix FLUX** | FLUX LoRA | FLUX 위 애니메 스타일 | FLUX 기반 애니메 대표 |
| **Counterfeit V3.0** | SD 1.5 | 대담한 색감, 역사적 중요성 | 레거시. 신규 비권장 |

### 4.4 서비스 가격·용도 비교

| 서비스 | 플랜/가격 | 핵심 강점 | 약점 |
|---|---|---|---|
| **NovelAI** | Tablet $10 / Scroll $15 / Opus $25 | 애니메 1위. 즉시 사용. V4.5 멀티캐릭터 | 로컬 불가. LoRA 커스텀 불가 |
| **Midjourney** | Basic $10 / Std $30 / Pro $60 / Mega $120 | V7 최고 품질. Niji V7 애니메 특화 | 로컬 불가. 캐릭터 일관성 도구 제한 |
| **Leonardo.ai** | Free / $12 / $24 / $60 | 게임 에셋 강점. 무료 티어 존재 | 애니메 전문성 부족 |
| **PixAI** | Free / Premium $9.99 | 애니메 퍼스트. 커뮤니티 LoRA | 품질 상한 낮음 |
| **로컬 SD/FLUX** | GPU 비용만 (초기 HW 제외) | 무제한. 완전한 제어. 프라이버시 | 기술 진입 장벽. VRAM 12GB+(FLUX 24GB+) |

**웹소설 일러스트 용도 추천**:
- 빠르고 쉬운 고품질: **NovelAI Opus** ($25/월)
- 예술적 커버/홍보물: **Midjourney Niji V7** ($30/월)
- 캐릭터 일관성 + 완전한 제어: **로컬 SDXL + Illustrious XL + LoRA** (무료, 기술력 필요)
- 제로샷 캐릭터 일관성: **FLUX Kontext** (오픈소스, 24GB+ VRAM)

※ NovelAI "생성물 저작권 포기": NovelAI가 자사 권리를 포기하여 사용자 자유 사용을 허용한 것이지, 사용자에게 저작권이 자동 발생하는 것은 아님. 각국 법률에 따라 별도 판단 필요.

---

## 5. 실무 방법론·워크플로우

### 5.1 캐릭터 일관성 유지 — 4단계 체계

#### Tier 1: LoRA 트레이닝 (최강, 시리즈물 필수)

**데이터셋 준비**
- 이미지 수: 20~40장 (최소 15장, 권장 30장)
- 해상도: SDXL 1024x1024, SD1.5 768x768 이상
- 구성: 전면/측면/3/4뷰, 표정 변화, 조명 차이 포함. 배경은 단색·투명 권장
- 캡셔닝: **WD14 Tagger v3** 자동 태깅, 캐릭터 태그 최우선 배치

**모델별 권장 파라미터** (Kohya-ss/sd-scripts 기준)

| 파라미터 | SD 1.5 | SDXL | FLUX.1 |
|---|---|---|---|
| Learning Rate | 2e-4 | 1e-4 | 1e-4 |
| Network Dim | 64 | 128 | 128 |
| Network Alpha | 32 | 64 | 128 |
| Optimizer | AdamW8bit | Adafactor | AdamW8bit (bf16) |
| 훈련량 | 15 epochs | 10 epochs | ~2,000 steps |
| 최소 VRAM | 12GB | 17GB (bf16 시 10GB) | 24GB (양자화 필수) |

- 결과: 다양한 장면에서 동일 캐릭터 재현율 **가장 높음**
- LoRA 강도: 0.6~0.8에서 스타일-일관성 밸런스

#### Tier 2: IP-Adapter + FaceID (훈련 불요, 빠른 대안)

| 변형 | 기능 | 권장 강도 |
|---|---|---|
| IP-Adapter | 참조 이미지의 전체 분위기 반영 | 0.6~0.85 |
| IP-Adapter FaceID Plus v2 | 얼굴 ID 보존 특화 | weight 0.6 |
| InstantID | InsightFace 기반, 1장으로 얼굴 일관성 | - |
| PhotoMaker V2 | Tencent ARC, stacked ID embedding | - |

- ComfyUI: `ComfyUI_IPAdapter_plus`, `cubiq/ComfyUI_InstantID`
- 3~5장 레퍼런스 권장. 프로덕션 대부분에 "충분히 좋음"

#### Tier 3: FLUX Kontext (2025~26 최신, 제로샷)

- 12B DiT, 텍스트+이미지 동시 입력
- **파인튜닝 없이** 단일 참조 이미지에서 캐릭터 서사 전체 생성
- 반복 편집에도 일관성 저하 최소화
- 오픈소스 dev 버전 (상업 라이선스 확인 필요)

#### Tier 4: 프롬프트 엔지니어링 (가장 쉬움, 일관성 최저)

- 캐릭터 트리거 워드 최상단 배치: `[trigger], 1girl, silver hair, blue eyes, ...`
- 시드 고정, CFG Scale 7~12
- 네거티브 임베딩: `EasyNegative`, `badhandv4` 필수

**방법 선택 기준**

| 상황 | 추천 |
|---|---|
| 빠른 실험/프로토타입 | IP-Adapter + InstantID |
| 장기 시리즈 (10권+) | 캐릭터별 LoRA 트레이닝 |
| 1~2장 참조만 가능 | FLUX Kontext 또는 PhotoMaker V2 |
| 얼굴+포즈 동시 제어 | IP-Adapter FaceID + OpenPose ControlNet |

### 5.2 구도/포즈 제어 기술

| 기술 | 용도 | 비고 |
|---|---|---|
| ControlNet OpenPose | 인체 포즈 정밀 제어 | 액션 씬, 멀티캐릭터 |
| ControlNet Canny/Lineart | 윤곽선 기반 구도 | 러프 스케치 → AI 변환 |
| ControlNet Depth | 깊이맵 기반 원근 | 배경 씬 |
| Illustrious ControlNet | Illustrious XL 전용 스위트 | 애니메 최적화 |

**Ultimate Combo**: LoRA(캐릭터 동일성) + ControlNet OpenPose(포즈) + IP-Adapter(스타일 일관성) + 프롬프트(장면 디테일) → 4중 동시 적용이 현재 최강 조합.
- 권장: IP-Adapter weight 0.75, FaceID weight 0.6, 40+ 스텝, Face Detailer 후처리

### 5.3 프로덕션 파이프라인 (ComfyUI 기반)

```
[1] 컨셉 설계
    └─ 장르·분위기·캐릭터 설정 문서화
    └─ 레퍼런스 이미지 수집
    └─ ControlNet 입력용 포즈/구도 확정
    └─ 표지 비율 결정 (웹소설: 보통 3:4 또는 2:3)

[2] 캐릭터 시트 생성 (VNCCS 워크플로우)
    └─ Illustrious 기반 모델 사용
    └─ 4단계: 캐릭터 시트 → 의상 → 표정 → 최종 스프라이트
    └─ 표정 10종 × 캐릭터 5명 = 50 스프라이트
    └─ 소요: 10~15시간 (8GB+ VRAM 필요)

[3] 표지 생성
    └─ LoRA(캐릭터) + ControlNet(구도) + IP-Adapter(포즈)
    └─ txt2img → 배치 8~16장 생성 → 후보 3장 선별
    └─ 시드 기록

[4] 디테일 보정
    └─ ADetailer: face_yolov8n(얼굴) + hand_yolov8n(손) 자동 감지·인페인팅
    └─ 수동 인페인팅: denoise 0.4~0.6, 눈/손가락/장신구
    └─ img2img (denoise 0.3~0.5) 전체 품질 향상

[5] 업스케일링
    └─ 1차: Lanczos 2x
    └─ 2차: 4x-UltraSharp 또는 Real-ESRGAN 4x+
    └─ GFPGAN 얼굴 복원 (선택)
    └─ 최종 해상도: 2400x3200+ (인쇄 대응)

[6] 마감
    └─ Photoshop/Clip Studio로 이관
    └─ 색보정, 타이포그래피(제목/작가명), 로고 배치
    └─ 플랫폼별 사이즈 리사이즈 (카카오/네이버/리디)
    └─ AI 감별 도구 자체 테스트
    └─ 유사 이미지 역검색 (저작권 리스크 체크)
```

**ComfyUI 핵심 노드 체인**:
```
SDXL Checkpoint Loader
  → CLIP Text Encode (프롬프트)
  → IP-Adapter FaceID Plus v2 (캐릭터 참조)
  → ControlNet Apply (OpenPose)
  → KSampler (Steps: 25~30, CFG: 7~8, Euler a)
  → VAE Decode
  → ADetailer / FaceDetailer
  → Upscale (4x-UltraSharp)
  → Save Image
```

**핵심 확장팩**: `ComfyUI_IPAdapter_plus`, `cubiq/ComfyUI_InstantID`, `ComfyUI-Impact-Pack` (FaceDetailer/SAM), `ComfyUI_UltimateSDUpscale`

### 5.4 업스케일러 비교

| 업스케일러 | 특징 | 용도 |
|---|---|---|
| 4x-UltraSharp | 가장 선명. 별도 설치 필요 | 최종 인쇄용 |
| Real-ESRGAN 4x+ | 범용, 디테일 우수 | 일반 용도 |
| Real-ESRGAN Anime6B | 애니메 특화 | 애니 스타일 전용 |
| GFPGAN | 얼굴 복원 특화 | 보조용 |
| Lanczos | 비AI, 빠름 | 중간 단계 |

### 5.5 하이브리드 모델 (현 시점 최적)

1. AI로 러프/컨셉 아트 대량 생성 (10~50장)
2. 아트 디렉터/작가가 최적안 선정
3. 인간 일러스트레이터가 over-paint 또는 대폭 수정
4. 타이포그래피·레이아웃은 반드시 인간 작업
5. 작업 과정 기록 (저작권 등록용 증거 확보)
6. → 저작권 보호 가능 + 품질 보장 + 비용 50~70% 절감

---

## 6. 비용 구조 분석

### 6.1 시나리오별 비용 비교 (표지 1건 기준)

| 방식 | 비용 | 소요 시간 | 품질 | 저작권 안전성 |
|---|---|---|---|---|
| 인기 일러스트레이터 위탁 | 300~500만 원 | 2~4주 | ★★★★★ | ★★★★★ |
| 일반 일러스트레이터 위탁 | 80~150만 원 | 1~2주 | ★★★★ | ★★★★★ |
| 하이브리드 (AI 컨셉 + 인간 마감) | 30~80만 원 | 3~5일 | ★★★★ | ★★★★ |
| AI 서비스 이용 (Midjourney 등) | 1~5만 원 | 1~2시간 | ★★★☆ | ★★☆ |
| AI 100% 자체 생성 (로컬) | ~0원 | 2~4시간 | ★★★ | ★★ (리스크 높음) |

### 6.2 시리즈 12권 표지 시뮬레이션

| 방식 | 총비용 | 비고 |
|---|---|---|
| 인간 전담 | 960~1,800만 원 | 일러스트레이터 단가 80~150만/건 |
| 하이브리드 | 360~960만 원 | AI 컨셉 + 인간 마감 |
| AI(SaaS) | 30~36만 원/년 | NovelAI/Midjourney 구독 |
| AI(로컬) | ~0원 (초기 250~300만 HW 투자) | RTX 4090 기준 |

### 6.3 클라우드 GPU 비용 (2026.03 기준)

| 서비스 | RTX 3090 | RTX 4090 | A100 80GB |
|---|---|---|---|
| RunPod (Community) | $0.22/hr | $0.69/hr | $1.19/hr |
| RunPod (Secure) | $0.43/hr | - | $1.64/hr |
| Vast.ai | $0.16/hr | ~$0.50/hr | ~$1.00/hr |

→ 표지 1장 생성(후보정 포함 2시간 가정): RunPod RTX4090 기준 약 $1.38 ≈ 1,800원

### 6.4 해외 비용 참조

- 영미권 신인: $100~300 (13~40만 원)
- 영미권 중견: $300~800 (40~105만 원)
- 영미권 탑티어: $1,000~2,500+ (130~330만 원)
- AI 북커버 서비스: 건당 $10 (BeYourCover), 무제한 $79.99/월 (BookIllustrationAI)

---

## 7. 법적·제도적 환경

### 7.1 국가별 비교

| 항목 | 한국 | 미국 | 일본 |
|---|---|---|---|
| AI 단독 생성물 저작권 | 불인정 | 불인정 (**확정**, 대법원 2026.03) | 불인정 (원칙) |
| AI 활용 저작물 | 등록 가능 (문체부 안내서 2025.06) | 케이스별 판단 | 인간 개입도에 따라 인정 가능 |
| AI 콘텐츠 고지 의무 | **AI기본법 제31조** (2026.01 시행) | Amazon KDP 의무화, 연방 REAL Act 진행 중 | 미확정 (Pixiv/DLsite 자율 표기) |
| 핵심 판례/사건 | - | Thaler v. Perlmutter (대법원 기각) | 지바현 형사 송치 (2025.11) |

### 7.2 한국 문체부 가이드라인 핵심 (2025.06)

저작권 등록이 인정되는 "창작적 기여" 3가지:
1. **자기 저작물을 프롬프트로 입력** → AI 결과물에 그 창작성이 반영된 경우
2. **AI 산출물을 수정·증감** → 추가 작업 부분에 창작성이 있는 경우
3. **AI 산출물의 선택·배열·구성** → 그 편집에 창작성이 있는 경우

→ **작업 기록 영상·설명 자료가 등록 심사의 핵심 증거**

### 7.3 한국 AI기본법 (2026.01 시행)

- 제31조: AI 생성 콘텐츠 고지 의무
- 웹툰/웹소설 등 시각 콘텐츠: 기계 판독 가능 비가시 워터마크 허용
- Naver Webtoon, KakaoPage, Lezhin 등: 업로드 시스템에 AI 사용 공개 토글/UI 알림 도입 필요
- "어느 수준의 AI 사용을 'AI 생성'으로 볼 것인가"의 구체 기준은 아직 미비

### 7.4 주요 소송 현황

| 소송명 | 당사자 | 현황 |
|---|---|---|
| **Andersen v. Stability AI** | 일러스트레이터 vs Stability/Midjourney/DeviantArt | 2023 제기. LAION 50억 이미지. 2024.08 핵심 청구 디스커버리 진행 허가 |
| **Disney/Universal v. Midjourney** | Disney, Universal, Warner Bros. vs Midjourney | 2025.06 제기, 2025.11 통합 |
| **Disney 등 v. Minimax** | Disney, Universal, WB vs 중국 Minimax | 2025.09. 최초 외국 AI 기업 대상 소송 |
| **Thaler v. Perlmutter** | Thaler vs US Copyright Office | **미 대법원 2026.03.02 상고 기각 → AI 단독 저작물 불인정 확정** |
| **Bartz v. Anthropic** | - | **$15억(약 2조 원) 합의** — AI 저작권 역대 최대 합의 |

- 2025년 말 기준 **70건 이상** AI 저작권 침해 소송 진행 중
- EU AI Act: 2026.08 AI 생성 콘텐츠 투명성/마킹/라벨링 의무 발효
- 미국 뉴욕주: 2026.06 합성 퍼포머 사용 공개 의무
- 미국 캘리포니아: 2026.01 생성 AI 학습 데이터 요약 공표 의무

---

## 8. 한계점·리스크

### 8.1 기술적 한계

| 문제 | 현 상태 | 해결 방향 |
|---|---|---|
| 캐릭터 일관성 | 단순 포트레이트 전환 ~70%, 장면 변화 시 ~40% (스탠퍼드) | LoRA+IP-Adapter+FLUX Kontext. 근본 한계: 생성 모델에 이전 결과 메모리 없음 |
| **Concept Bleeding** | 다인물 씬에서 A 캐릭터 특성이 B에 전이 | Regional Prompter, 개별 생성 후 합성 (Adobe: 90% 일관성 유지) |
| 손/눈 디테일 | 상당히 개선, 간헐적 오류 잔존 | ADetailer 자동 보정 + 수동 인페인팅 필수 |
| 3인+ 다인물 씬 | 여전히 신뢰성 극히 낮음 | 개별 생성 → 포토샵 합성 우회 |
| 텍스트/로고 | Flux에서 텍스트 렌더링 개선, 아직 불완전 | Photoshop 레이어 합성 필수 |
| 스타일 통일성 | 시리즈물 수십~수백 장 동일 화풍 유지 어려움 | 전용 스타일 LoRA + 체크포인트 고정 |

### 8.2 시장 리스크

- **독자 반감**: 한국은 특히 강경. AI 사용 의혹만으로 별점 테러, 불매 운동.
- **AI 감별 기술**: CNN+Transformer 하이브리드 88~95%, 멀티스케일 텍스처 주파수 분석 **92~97%** 정확도. ([Nature 2025](https://www.nature.com/articles/s41598-025-29229-2))
  - 주요 도구: Winston AI, AI or Not, Illuminarty, GPTZero, Hive Moderation
  - 단, 생성 모델도 동시 진화 → **영원한 군비 경쟁**
- **"Anti-AI" 미학 트렌드**: 수작업 느낌을 강조하는 역트렌드 형성.

### 8.3 법적 리스크

- 순수 AI 생성 표지 → 저작권 보호 불가 → 누구나 복사·사용 가능
- 학습 데이터 소송(70건+) 결과에 따라 소급 리스크 발생 가능
- AI기본법 고지 의무 위반 시 제재 리스크
- 제3자가 동일/유사 이미지 생성 가능 → 독점적 권리 주장 불가

### 8.4 윤리적·일자리 영향

| 지표 | 수치 | 출처 |
|---|---|---|
| 영국 일러스트레이터 일감 상실 비율 | **32%** | AOI 2025 조사 |
| 피해 아티스트 평균 손실액 | £9,262 (~1,600만 원) | AOI 2025 |
| 영국 일러스트레이터 AI에 일감 빼앗김 | 26% | 영국 저작자 협회 2024 |
| 중국 게임업계 일러스트레이터 일자리 감소 | **70%** | Artisana |
| 중국 게임업계 생산성 증가 | **40배** | Artisana |
| AI 허용 마켓 이미지 총량 증가 | 78% | 스탠퍼드 경영대학원 (320만 이미지, 62,000 아티스트) |
| AI 허용 마켓 비AI 아티스트 추가 이탈 | 23% | 스탠퍼드 |
| 자신의 작품 AI 학습 동의·보상 요구 | **95%** | - |

---

## 9. 글도비 프로젝트 시사점

### 9.1 적용 가능 영역

| 영역 | AI 활용 가능성 | 권장 방식 |
|---|---|---|
| 장르 프리셋 미리보기 이미지 | 높음 | AI 생성 + 내부용도 한정 |
| 캐릭터 컨셉 시각화 | 높음 | Midjourney/NovelAI로 러프 생성, 작가 피드백 루프 |
| 출판용 표지 최종물 | 낮음 (리스크) | 하이브리드 필수 (AI 러프 → 인간 마감). 작업 기록 보존 |
| 장면 삽화 | 중간 | LoRA 기반 캐릭터 일관성 확보 후 검토 |
| 역설계 파이프라인 시각 보조 | 높음 | 기존 원고의 장면 시각화에 AI 활용 |
| AI 만화극(숏폼) | 높음 | 阅文 사례 참조. 웹소설 → 숏폼 변환 파이프라인 |

### 9.2 권장 전략

1. **단기 (즉시)**
   - 내부 컨셉·기획 용도로 Midjourney/NovelAI 활용
   - 외부 공개물에는 AI 단독 사용 금지
   - AI기본법 고지 의무 대응 체계 수립

2. **중기 (3~6개월)**
   - ComfyUI + Illustrious XL + LoRA 파이프라인 구축
   - VNCCS 기반 캐릭터 시트 자동화 검증
   - FLUX Kontext 제로샷 일관성 평가

3. **장기 (6개월+)**
   - 하이브리드 워크플로우 표준화
   - AI 컨셉 → 인간 마감 프로세스로 표지 제작 비용 50~70% 절감
   - 작업 기록 보존 체계 (저작권 등록 증거)
   - 숏폼 변환 파이프라인 검토 (阅文 AI 만화극 모델)

---

## 10. 적대적 감리 결과

### Pass 2-A: 사실 검증

| # | 검증 항목 | 결과 | 비고 |
|---|---|---|---|
| F1 | 국내 AI 활용률 20% | ✅ 검증됨 | 한국콘텐츠진흥원 출처 |
| F2 | 표지 비용 150만 원선 | ✅ 검증됨 | 이데일리 보도 + TF4 교차 검증 (80~150만 원 범위) |
| F3 | 阅文 AI 만화극 매출 1억 위안 | ✅ 검증됨 | 신랑재경 2026.03.18 보도 |
| F4 | 미 대법원 Thaler 기각 2026.03.02 | ✅ 검증됨 | CNBC, Mayer Brown, Holland & Knight 등 다수 |
| F5 | 한국 문체부 안내서 2025.06 | ✅ 검증됨 | 전자신문, ditoday, KOCCA |
| F6 | Midjourney V7 2025.04.03 출시 | ✅ 검증됨 | TF2 에이전트가 Midjourney 공식 문서에서 확인 |
| F7 | LoRA 레퍼런스 15~30장 | ✅ 검증됨 | Apatero + Kohya Wiki + TF4 교차 일치 |
| F8 | Amazon 베스트셀러 81/100 AI 스팸 | ⚠️ 주의 | 2023년 한 시점의 **특정 카테고리** 한정 사례. 일반화 주의 |
| F9 | NovelAI V4 2025.02.28 출시 | ✅ 검증됨 | TF2 공식 출처 확인 |
| F10 | Niji V7 2026.01.09 출시 | ✅ 검증됨 | TF2 nijijourney.com 블로그 확인 |
| F11 | AI 감별 정확도 92~97% | ✅ 검증됨 | Nature 2025 + TF5 교차 검증 |
| F12 | 한국 AI기본법 2026.01 시행 | ✅ 검증됨 | ANN, TNPS 보도 + TF5 교차 확인 |
| F13 | 영국 AOI 32% 일감 상실 | ✅ 검증됨 | 80.lv, Design Week 보도 |
| F14 | 중국 게임업계 70% 일자리 감소 | ✅ 검증됨 | Artisana 보도 |
| F15 | Bartz v. Anthropic $15억 합의 | ⚠️ 주의 | TF5 단일 출처. 교차 검증 추가 필요 |

### Pass 2-B: 논리 모순 점검

| # | 항목 | 판정 | 보완 |
|---|---|---|---|
| L1 | "단일 표지 상용 수준" vs "캐릭터 일관성 40~70%" | ✅ 해소됨 | "단일 표지 ≠ 시리즈 일관성" 명확 구분 → 본문 반영 |
| L2 | 중국 공격적 채택 vs 한국 강한 반감 | ✅ 모순 아님 | 문화·제도 차이 |
| L3 | NovelAI "저작권 포기" vs "저작권 보호 불가" | ✅ 해소됨 | 본문에 주석 추가: NovelAI 자사 권리 포기 ≠ 사용자 저작권 자동 발생 |
| L4 | LoRA "최강" vs Concept Bleeding 문제 | ✅ 모순 아님 | LoRA는 캐릭터 동일성, Concept Bleeding은 다인물 씬 문제. 영역 다름 |
| L5 | AI 감별 92~97% vs "은밀히 확산" | ⚠️ 미세 긴장 | 감별 도구 사용이 보편화되지 않아 확산 가능. 도구가 보편화되면 균형 이동 |

### Pass 2-C: 누락 영역 점검

| # | 누락 항목 | 심각도 | 대응 |
|---|---|---|---|
| M1 | 국내 플랫폼별 정책 차이 (카카오 vs 네이버 vs 리디) | 중 | 공식 발표 부재, "미발표" 명시 |
| M2 | 일본 출판사별 구체적 AI 채택 사례 | 중 | 업계가 공개 채택 기피. 나로우 계열 비공식 확산은 기술 |
| M3 | GPU 클라우드 구체 비용 | ✅ 해소 | TF4 데이터로 RunPod/Vast.ai 비용 추가 |
| M4 | AI 감별 구체 정확도 | ✅ 해소 | TF5 데이터로 92~97% 수치 추가 |
| M5 | LoRA 훈련 파라미터 | ✅ 해소 | TF4 Kohya-ss 파라미터 테이블 추가 |
| M6 | FLUX Kontext 등 최신 모델 | ✅ 해소 | TF4 데이터로 추가 |

### Pass 3: 최종 확정 판정

| 항목 | 판정 |
|---|---|
| 사실 오류 | 0건 확정 오류, 2건 주의 표기 (F8 Amazon 일반화, F15 Bartz 단일 출처) |
| 논리 모순 | 0건 심각, 1건 미세 긴장 (L5 감별·확산 역설) |
| 누락 | 초안 대비 4건 해소 (M3~M6), 2건 잔존 (M1~M2, 수집 한계) |
| **종합 신뢰도** | **A- (실무 참조 가능. F8·F15 재확인 시 A)** |

---

## 11. 출처

### 국내 보도
- [AI로 만든 웹소설 표지, 논란의 정점에 선 이유 - 이데일리](https://www.edaily.co.kr/news/read?newsId=01420246635670256&mediaCodeNo=257)
- ["내 그림 학습시킨 웹소설 AI 표지, 해명하세요" - 헤럴드경제](https://biz.heraldcorp.com/article/3158791)
- ['AI 표지' 웹소설계 발칵 뒤집었다 - 유니콘팩토리](https://www.unicornfactory.co.kr/article/2023051917440286736)
- ["뭐야 AI로 썼어?" 별점 테러…웹소설 작가들 딜레마 - 머니투데이](https://www.mt.co.kr/tech/2026/03/11/2026022508052980108)
- ['AI 웹툰' 의혹만으로 '별점 테러' - 블로터](https://www.bloter.net/news/articleView.html?idxno=650498)
- [상업 창작물로 번진 생성 AI 논란 - 이코리아뉴스](https://www.ekoreanews.co.kr/news/articleView.html?idxno=67099)

### 법적·제도
- [문체부 AI 저작권 등록 안내서 - 전자신문](https://www.etnews.com/20250701000303)
- [2025 생성형 AI 저작권 등록 안내서 총정리 - ditoday](https://ditoday.com/gai-copyright/)
- [AI 저작권 안내서 내용과 의미 - KOCCA](https://www.kocca.kr/trendott/vol04/trend_1.html)
- [생성형 AI 저작권 판결 동향 - 법률신문](https://www.lawtimes.co.kr/news/articleView.html?idxno=216497)
- [미 법원 "AI 학습, 저작권 침해 아냐" 판결 - 경향신문](https://www.khan.co.kr/article/202507120800001)
- [US Copyright Office AI Policy](https://www.copyright.gov/ai/)
- [Supreme Court Denies Cert in Thaler - Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/03/supreme-court-denies-review-in-ai-authorship-case)
- [Andersen v. Stability AI - NYU JIPEL](https://jipel.law.nyu.edu/andersen-v-stability-ai-the-landmark-case-unpacking-the-copyright-risks-of-ai-image-generators/)
- [AI Copyright Lawsuit Developments 2025 - Copyright Alliance](https://copyrightalliance.org/ai-copyright-lawsuit-developments-2025/)
- [AI 저작권 가이드라인 - Kim & Chang](https://www.kimchang.com/en/insights/detail.kc?sch_section=4&idx=32432)
- [South Korea AI Basic Act - ANN](https://www.animenewsnetwork.com/news/2026-01-24/south-korea-new-ai-law-raises-questions-for-webtoon-creators-platforms/.233383)

### 해외 동향
- [阅文 2025 매출 73.7억 위안, AI만화극 매출 1억 돌파 - 신랑재경](https://finance.sina.com.cn/jjxw/2026-03-18/doc-inhrkskx9409548.shtml)
- [阅文 CEO 내부 서신: IP+AI 전략 - 신랑뉴스](https://k.sina.com.cn/article_7879922982_1d5ae15260190a8fc0.html)
- [阅文 × DeepSeek - 36kr](https://36kr.com/p/3154970726767363)
- ["AI도 창작물" 일본 첫 형사 송치 - 나우뉴스](https://m.nownews.seoul.co.kr/news/global-topic/international-insight/2025/11/20/20251120601013)
- [Amazon KDP AI 공시 정책 - Authors Guild](https://authorsguild.org/news/amazons-new-disclosure-policy-for-ai-generated-book-content-is-a-welcome-first-step/)
- [소학관 NOVELOUS AI 활용 - High-Five](https://high-five.careers/column/shogakukan/)
- [China Video Game AI Art Crisis - Artisana](https://www.artisana.ai/articles/chinas-video-game-ai-art-crisis-40x-productivity-spike-70-job-loss)
- [When AI Art Enters Market - Stanford GSB](https://www.gsb.stanford.edu/insights/when-ai-generated-art-enters-market-consumers-win-artists-lose)

### 기술·워크플로우
- [Anime Character Consistency Guide 2025 - Apatero](https://apatero.com/blog/anime-character-consistency-complete-guide-2025)
- [AI Consistent Character Generator 2026 - Apatero](https://www.apatero.com/blog/ai-consistent-character-generator-multiple-images-2026)
- [VNCCS Visual Novel Character Suite - Apatero](https://apatero.com/blog/vnccs-visual-novel-character-creation-suite-comfyui-2025)
- [FLUX Kontext - Black Forest Labs](https://bfl.ai/models/flux-kontext)
- [LoRA Training Guide 2025 - sanj.dev](https://sanj.dev/post/lora-training-2025-ultimate-guide)
- [How to Train LoRA - Stable Diffusion Art](https://stable-diffusion-art.com/train-lora/)
- [ADetailer - Stable Diffusion Art](https://stable-diffusion-art.com/adetailer/)
- [Flux vs SDXL 비교 - Stable Diffusion Art](https://stable-diffusion-art.com/sdxl-vs-flux/)
- [Best Stable Diffusion Anime Models - Aituts](https://aituts.com/anime-models/)
- [Illustrious XL Comparison - Civitai](https://civitai.com/articles/11668/illustrious-xl-10-comparison-against-other-up-to-date-anime-models)
- [NovelAI Review 2025 - Skywork](https://skywork.ai/blog/novelai-review-2025-text-anime-image-generation/)
- [Niji V7 Guide - HonoGear](https://www.honogear.com/en/blog/engineering/niji-journey-v7-guide)
- [IP-Adapters Guide - Stable Diffusion Art](https://stable-diffusion-art.com/ip-adapter/)
- [ComfyUI Workflow Guide - Shakker AI](https://wiki.shakker.ai/en/comfyui-workflow)
- [AI Illustration vs Traditional 2025 - BookIllustrationAI](https://bookillustrationai.com/blog/ai-illustration-vs-traditional-illustration-complete-comparison-2025)

### 윤리·일자리
- [A Third of Illustrators Lost Jobs to AI - 80.lv](https://80.lv/articles/a-third-of-translators-a-quarter-of-illustrators-have-lost-their-jobs-to-ai)
- [Illustration Industry AI Report - Design Week](https://www.designweek.co.uk/how-the-illustration-industry-is-grappling-with-ai-a-special-report/)
- [AI Artwork Detection Using Self-Distilled Transformers - Nature 2025](https://www.nature.com/articles/s41598-025-29229-2)
- [AI Image Detectors Accuracy 2026 - OpenPR](https://www.openpr.com/news/4295987/how-accurate-are-modern-ai-image-detectors-in-2026)

---

*본 보고서는 5-TF 병렬 웹서치 + 4-TF 병렬 에이전트(모델·서비스/해외동향/실무방법론/한계리스크) → 1pass 통합 초안 → 2pass 적대적 감리(사실검증 15항목/논리모순 5항목/누락 6항목) → 3pass 확정의 절차를 거쳐 작성되었습니다. 종합 신뢰도 A-.*
