# 투자물 EPUB 코퍼스 및 Vertex AI Gemini 튜닝 전략 재감리 보고서

- 작성일: 2026-03-14
- 상태: final (3-pass 감리 통과)
- 문서 경로: `docs/report_investment_epub_pipeline.md`
- 목적: 사내 보유 EPUB 자산을 기준으로 현대판타지 재벌/기업/돈벌기 계열 코퍼스를 재정리하고, Vertex AI에서 Gemini 서비스 모델에 최대한 문체를 체화시키는 현실적인 학습 경로를 확정한다.
- 범위:
  - NAS EPUB 폴더 재스캔
  - SSOT 폴더 선택 규칙 재정의
  - EPUB 본문 추출 규칙 재설계
  - Vertex AI 공식 문서 기준 Gemini 튜닝 경로 재판정
  - 기존 보고서 오판 수정
- 비범위:
  - 실제 변환 스크립트 작성
  - 실제 GCS 업로드 및 튜닝 잡 실행
  - 작품 내용 기반 장르 확정 감리
- Evidence Basis:
  - 2026-03-14 NAS 실경로 재스캔: `\\172.16.10.120\소설사업부\판무사업팀\2. 연재 진행 파일\1. 제작 진행 연재_Epub`
  - 27개 후보 작품 폴더의 EPUB 수량 및 SSOT 경로 재집계
  - 27개 SSOT 후보의 첫 EPUB 내부 구조 표본 점검
  - Vertex AI 공식 문서 재확인: Gemini tuning / continuous tuning / supervised-tuning data format / Google model pages
- Commit State:
  - Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
  - Baseline Dirty Summary: `dirty: 7 tracked, 2 untracked; hotspots: docs/implementation/*, docs/report_investment_epub_pipeline.md`
  - Resume Commit: `same-as-baseline`
  - Resume Drift Summary: `none`
- Confidence:
  - 96%: Vertex AI 경로 판단, NAS 구조 재스캔, SSOT 규칙, EPUB 추출 설계
  - 85%: "투자물 확정 27건"의 장르 순도 자체. 현재는 제목 기반 사업 후보 목록이며, 내용 감리 전 최종 gold set으로 쓰면 안 된다.

---

## 0. 핵심 결론

1. 기존 보고서는 **3-pass 통과 상태가 아니었다**. `Gemma 3 CPT 권장`과 `Gemini 2.5 Pro SFT 채택`이 같은 문서 안에 동시에 존재했고, EPUB 구조와 SSOT 수량에도 실제 NAS와 다른 서술이 있었다.
2. 2026-03-14 기준 Vertex AI 공식 문서상, **Gemini 서비스 모델에 대해 현실적으로 바로 쓸 수 있는 경로는 `Gemini 2.5 Pro supervised tuning`**이다.
3. 같은 날짜 기준 공식 문서에는 **`Gemini 3 Pro` preview 모델 페이지는 존재하지만, Gemini 3.x Pro 계열은 tuning 지원 목록에 없다.** 따라서 "Gemini 3.1 Pro에 지금 바로 학습시킨다"는 경로는 문서상 확정할 수 없다.
4. EPUB 원본은 계속 핵심 자산이다. 다만 **Gemini 튜닝 입력은 raw txt가 아니라 JSONL 예제 포맷**이어야 한다. txt는 중간 산출물로만 유지한다.
5. NAS 재스캔 결과, 현재 제목 기반 27개 후보 폴더의 **raw EPUB 총량은 10,993건**, SSOT 규칙 적용 후 **우선 학습 후보 EPUB는 8,724건**이다.
6. EPUB 내부 구조는 균일하지 않다. `chapter_1.xhtml`만 가정하면 실패한다. **새 추출기는 `content.opf`의 spine 순서 기반으로 본문 문서를 순회**해야 한다.
7. 문체 체화를 최대화하려면 "1화 전체를 지시문과 함께 생성"보다 **짧은 continuation window 중심의 SFT 데이터셋**이 더 낫다. 즉, `앞 본문 -> 다음 본문` 형태를 반복적으로 만드는 쪽이 Gemini managed tuning에서 가장 현실적이다.

---

## 1. 기존 보고서 감리 결과

### 1.1 Pass 1: 구조와 범위 실패

- 문서 목표는 Gemini 서비스 모델 활용인데, 본문 주 권장안이 `Gemma 3 CPT`였다.
- 뒤 부록에서는 다시 `Gemini 2.5 Pro SFT 단일 경로`를 최종 판정으로 적어 **권장 경로가 문서 내부에서 충돌**했다.
- "투자물 확정 27건"과 "경계선 10건"을 같은 톤으로 적었지만, 실제 근거 수준은 제목 heuristic과 폴더 존재 확인에 머물렀다.

### 1.2 Pass 2: 근거와 일관성 실패

- `1980 독식하는 재벌!`의 `이펍수정용`을 EPUB 후보로 봤으나, 실제로는 `.hwpx`만 있었다.
- `만렙요원 재벌이 되다`는 실제로 루트에 370 EPUB가 있고, 하위 `만렙요원_epub`는 1~90 중복본 90개였다. 기존 문서는 하위 폴더만 SSOT처럼 다뤘다.
- `회귀로 나 혼자 독식`도 루트가 350 EPUB의 상위 집합이고, `구표지이펍`은 324개의 구버전/부분 중복본이었다.
- EPUB 내부 구조를 "전부 `chapter_1.xhtml`"로 썼지만, 실제 표본에서는 `Section0001.xhtml`, `Section0001 + Section0002`, `.html/.htm` 조합이 모두 확인됐다.
- Vertex AI 판단에 공식 문서 외 외부 글을 섞어 과감한 결론을 냈다. 이번 재감리에서는 **현행 플랫폼 판단은 Google 공식 문서만 근거로 사용**한다.

### 1.3 Pass 3: 실행성 실패

- `Gemma CPT`와 `Gemini Pro 서비스` 사이의 모델 전이 불가 문제가 본문 단계에서 해소되지 않았다.
- 데이터셋 설계가 `앞20% -> 뒤80%`, `N화 후반 -> N+1화 전체` 수준으로만 고정돼 있어, 실제 토큰 제어와 중복 관리 기준이 약했다.
- 검증 계획이 "빈 파일/중복/인코딩" 수준에 머물고, **title split 검증**, **정규화 해시 dedupe**, **본문 spine 추출**이 빠져 있었다.

결론: 기존 보고서는 저장 경로는 맞았지만, **주 권장안과 사실 근거가 서로 맞물리지 않아 final 문서로 보기 어렵다.**

---

## 2. NAS 재스캔 결과

### 2.1 현재 기준 수량 요약

| 항목 | 수치 | 비고 |
|---|---:|---|
| 제목 기반 1차 후보 작품 폴더 | 27 | 내용 감리 전 candidate set |
| raw EPUB 총량 | 10,993 | 중복/구버전 포함 |
| SSOT 적용 후 1차 학습 후보 EPUB | 8,724 | 중복 경로 제외 |
| 기존 txt 신뢰도 | 0 | 모두 폐기, EPUB 재추출만 사용 |

### 2.2 SSOT 선택 규칙 분포

| 규칙 | 작품 수 | 설명 |
|---|---:|---|
| `prefer-standard-serial-epub` | 16 | `연재이펍` 단일/표준 폴더 채택 |
| `prefer-root-superset-or-equal` | 7 | 루트 EPUB가 하위 폴더보다 상위 집합 또는 동등 |
| `prefer-renamed-after` | 3 | `필명변경후` 또는 `필명갈음후` 채택 |
| `prefer-final` | 1 | `최종` 표기 폴더 채택 |

### 2.3 예외 케이스 교정

| 작품 | 기존 문서 문제 | 재감리 결과 |
|---|---|---|
| `1980 독식하는 재벌!` | `이펍수정용`을 EPUB 후보처럼 서술 | `이펍수정용`은 `.hwpx`만 존재. SSOT는 `연재이펍` 216개 |
| `만렙요원 재벌이 되다` | 하위 `만렙요원_epub` 460개처럼 인식 | 실제는 루트 370개, 하위 90개. 하위는 1~90 중복본. SSOT는 루트 370개 |
| `회귀로 나 혼자 독식` | `구표지이펍` 중심 서술 | 실제는 루트 350개가 상위 집합, 하위 `구표지이펍` 324개는 부분 중복. SSOT는 루트 350개 |
| `재벌집 막내 도련님은 악당입니다!` | 대체로 맞았지만 근거 약함 | `4.표지갈음연재이펍_최종` 225개 채택이 타당 |
| `악당에서 재벌까지!` / `졸부집 망나니(개정판)` / `출판으로 재벌 되기!` | `변경후/갈음후` 선택은 맞았음 | 이 규칙은 유지 가능 |

### 2.4 파일명 패턴 재분류

SSOT 후보 EPUB 8,724개 기준 분포:

| 패턴 | 개수 | 예시 |
|---|---:|---|
| `pure_number` | 3,645 | `1.epub` |
| `id_number` | 1,894 | `606377_1.epub` |
| `title_number_hwa` | 2,712 | `금수저 투자백서 10화.epub` |
| `title_number_plain_suffix` | 473 | `창업의 신 1.epub`, `재벌집 망나니 7대독자_0001.epub` |
| `unknown` | 0 | 현재 SSOT 기준 없음 |

결론: 기존 문서의 "정규식 2개면 전부 커버"는 과감했다. 실제 구현은 최소 4개 패턴을 안전하게 다뤄야 한다.

### 2.5 장르 순도 주의

- 현재 27건은 **제목 기반 사업 후보 목록**이다.
- 즉, "이 폴더는 투자물 코퍼스에 넣을 만하다"는 운영 후보이지, **작품 내용까지 보고 gold-label 확정한 목록은 아니다.**
- 실제 학습 전에는 최소한 다음 둘 중 하나가 필요하다.
  - 시놉시스/1화 본문 기반 수동 감리
  - 추출 txt의 키워드/장면 기반 반자동 필터링

이 문서에서는 코퍼스 파이프라인 설계가 목적이므로, 후보 27건 자체는 유지하되 **최종 학습 세트 확정 전 1회 내용 감리**를 필수 단계로 둔다.

---

## 3. EPUB 본문 추출 설계 재판정

### 3.1 기존 가정이 틀린 이유

27개 SSOT 후보의 첫 EPUB 표본을 점검한 결과:

| 레이아웃 | 작품 수 |
|---|---:|
| `OEBPS/Text/chapter_1.xhtml` | 20 |
| `OEBPS/Text/Section0001.xhtml` | 3 |
| `OEBPS/Text/chapter_1.xhtml; OEBPS/Text/Section0001.xhtml` | 2 |
| `OEBPS/Text/Section0001.xhtml; OEBPS/Text/Section0002.xhtml` | 1 |
| `OEBPS/Text/0.html; OEBPS/Text/17.html; OEBPS/Text/section0001.htm` | 1 |

즉:

- `chapter_1`만 찾는 방식은 실패한다.
- `Section0001` fallback만 추가해도 아직 부족하다.
- 한 EPUB 안에서 본문 파일이 2개 이상일 수도 있다.
- `.xhtml`만이 아니라 `.html`, `.htm`도 실제로 존재한다.

### 3.2 권장 추출 규칙

신규 추출기는 아래 순서를 따라야 한다.

1. `META-INF/container.xml`을 읽어 OPF 위치를 찾는다.
2. OPF의 `manifest`와 `spine`을 파싱한다.
3. spine 순서대로 본문 문서를 순회한다.
4. `cover`, `copyright`, `nav`, 표지/광고성 페이지만 제외한다.
5. 나머지 `xhtml/html/htm` 문서를 순서대로 연결한다.
6. HTML 태그 제거 후 줄바꿈을 정규화한다.
7. UTF-8로 저장한다.
8. 정규화 텍스트 해시를 만들어 exact duplicate를 한 번 더 제거한다.

이 방식이면 `chapter_1`, `Section0001`, 복수 본문 파일, OPF spine 기반 변형까지 모두 커버 가능하다.

### 3.3 레거시 스크립트에서 계승 가능한 부분과 폐기할 부분

레거시 스크립트 경로:

`C:\Users\User\Desktop\reference\2_단행본 보조 스크립트\1_EPUB-TXT 변환 및 합본-개선.py`

계승 가능:

- `zipfile.ZipFile`
- `BeautifulSoup(html, "html.parser")`
- 본문 태그 줄바꿈 보정
- UTF-8 저장

폐기 또는 재작성 필요:

- 단일 경로 하드코딩
- `int(filename.split('.')[0])` 기반 파일명 파싱
- `Section0001/chapter_1/Section0002` 고정 탐색
- 합본 `0_합본.txt` 생성
- 기존 txt 참조
- 에러 로그/manifest 부재

---

## 4. Vertex AI Gemini 경로 재판정

### 4.1 2026-03-14 기준 공식 문서로 확정 가능한 사실

- Vertex AI Gemini tuning 문서의 supervised tuning 지원 모델 목록에는:
  - `Gemini 2.5 Pro`
  - `Gemini 2.5 Flash`
  - `Gemini 2.5 Flash-Lite`
  - `Gemini 2.0 Flash`
  - `Gemini 2.0 Flash-Lite`
  가 명시돼 있다.
- continuous tuning 문서는:
  - 기존 튜닝 job에 대해 **추가 training examples 또는 epochs를 더하는 경로**다.
  - raw corpus CPT가 아니다.
- preference tuning 문서는:
  - `Gemini 2.5 Flash`
  - `Gemini 2.5 Flash-Lite`
  만 지원 대상으로 적고 있다.
- Google model page에는 `Gemini 3 Pro` preview 모델 페이지가 존재하지만, tuning 지원 목록에는 Gemini 3.x Pro가 보이지 않는다.

### 4.2 이 사실이 의미하는 것

1. **Gemini 서비스 모델에 raw txt만 넣고 체화시키는 managed CPT 경로는 문서상 확정할 수 없다.**
2. 따라서 "문체를 최대한 배게 한다"는 목표는 **Gemini 2.5 Pro supervised tuning을 최대한 continuation-like 데이터셋으로 설계**해서 접근해야 한다.
3. `Gemini 3 Pro` 또는 사용자가 말한 `Gemini 3.1 Pro` 계열은, 2026-03-14 현재 **tuning 가능 모델로 문서상 확정되지 않았다.**
4. 그래서 실무 판단은 아래 둘 중 하나다.
   - 지금 바로 학습해서 서비스해야 한다: `Gemini 2.5 Pro supervised tuning`
   - 장기적으로 3.x Pro 계열을 쓸 생각이다: 코퍼스와 JSONL 빌더는 지금 만들되, 3.x tuning 공식 지원이 나올 때 재실행

### 4.3 최종 판정

**현재 시점의 최종 경로는 `Gemini 2.5 Pro supervised tuning`이다.**

`Gemma CPT`는 "문체 체화" 관점의 이론적 배경으로는 이해되지만, 사용자가 실제로 쓸 서비스 모델이 Gemini Pro라면 **가중치 전이가 불가능**하므로 이 문서의 주 경로로 둘 수 없다.

---

## 5. Gemini에서 문체 체화를 최대화하는 데이터 설계

### 5.1 원칙

- instruction은 짧고 고정한다.
- 학습 예제의 대부분은 "이전 본문 -> 다음 본문"으로 구성한다.
- 작품명/회차 같은 운영 메타데이터는 별도 manifest에 두고, 학습 본문 안에는 최소한만 넣는다.
- validation split은 random line split이 아니라 **title split 또는 episode block split**으로 한다.
- 1예제 길이는 공식 한도보다 훨씬 짧게 유지해 밀도를 높인다.

### 5.2 왜 기존 `20% -> 80%` 단일 방식만으로는 부족한가

그 방식도 나쁘진 않지만:

- output 구간이 너무 길어지면 토큰 관리가 둔해진다.
- 한 화 앞부분 하나에 지나치게 종속된다.
- 문체/문장 리듬 학습에는 더 짧은 local continuation이 유리하다.

### 5.3 권장 데이터셋 구조

#### A. Local Continuation Window

- 목적: 문체, 문장 호흡, 문단 리듬
- 입력: 같은 화의 직전 1,500~3,000 tokens
- 출력: 이어지는 다음 1,500~3,000 tokens
- 방식: sliding window, stride 750~1,500 tokens

이게 가장 중요하다. Gemini managed tuning 안에서 CPT에 가장 가깝게 흉내낼 수 있는 형태다.

#### B. Episode Bridge Window

- 목적: 클리프행어 -> 다음 화 오프닝, 회차 간 페이싱
- 입력: N화 말미 1,000~2,000 tokens
- 출력: N+1화 초반 1,500~3,000 tokens

#### C. Whole-Episode Continuation

- 목적: 장면 장기 호흡
- 입력: 화 앞 15~25%
- 출력: 나머지 본문

이건 보조용으로만 둔다. 전량을 이 포맷으로 만들 필요는 없다.

### 5.4 권장 JSONL 형태

```json
{
  "systemInstruction": {
    "parts": [
      {
        "text": "앞 문체와 호흡을 유지해 자연스럽게 이어 쓴다."
      }
    ]
  },
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "[직전 본문 구간]"
        }
      ]
    },
    {
      "role": "model",
      "parts": [
        {
          "text": "[바로 다음 본문 구간]"
        }
      ]
    }
  ]
}
```

운영 포인트:

- `systemInstruction`은 짧게 고정한다. 이것도 토큰을 먹는다.
- user 파트에 제목/회차/장르 설명을 장황하게 넣지 않는다.
- title, episode, source_path, hash는 학습 JSONL 바깥 manifest에 둔다.

### 5.5 txt와 JSONL의 관계

파이프라인은 아래가 맞다.

```text
EPUB -> 회차별 UTF-8 txt -> validation/dedupe -> Gemini supervised-tuning JSONL
```

즉:

- txt는 필요하다. 하지만 **중간 산출물**이다.
- Vertex AI Gemini tuning 입력은 **JSONL이 최종 포맷**이다.

---

## 6. 실행 권장안

### 6.1 산출물 구조

```text
data/investment_corpus/
  manifest.json
  errors.log
  titles/
    <slug>/
      0001.txt
      0002.txt
      ...
  gemini/
    train.jsonl
    val.jsonl
```

`0001.txt`처럼 4자리 zero-pad를 권장한다. 현재 최대 화수는 751이지만, 정렬 안정성을 위해 4자리가 낫다.

### 6.2 단계

1. **후보 세트 동결**
   - 현재 27개는 candidate set으로 두고 시작
   - 경계선/오분류 우려 작품은 separate review queue로 유지
2. **EPUB -> txt 추출기 작성**
   - OPF spine 기반
   - UTF-8 고정
   - 해시 기반 dedupe
3. **manifest 생성**
   - title
   - source path
   - ssot path
   - selection rule
   - raw epub count
   - txt count
   - text hash
4. **내용 감리 1회**
   - 최소 시놉시스 또는 1화 기반으로 gold set 확정
5. **txt -> JSONL 빌더 작성**
   - local continuation
   - episode bridge
   - optional whole-episode continuation
6. **validation split**
   - 작품 단위 또는 후반부 화 단위로 분리
7. **Gemini 2.5 Pro supervised tuning**
8. **평가**
   - held-out episode continuation
   - 블라인드 문체 일치도
   - 회차 연결 자연스러움

### 6.3 side-effect 범위

- 파일 쓰기:
  - `data/investment_corpus/`
  - `manifest.json`
  - `errors.log`
  - `train.jsonl`, `val.jsonl`
- 콘솔/운영자 출력:
  - 변환 진행률
  - 실패 EPUB 경고
  - dedupe/검증 요약
- 네트워크 쓰기:
  - 향후 GCS 업로드 시 발생
- DB 쓰기:
  - 현재 단계에서는 비적용
- retry/recovery:
  - 실패 EPUB는 `errors.log`에 남기고 재실행 가능하게 설계
- cache/global state:
  - 현재 단계에서는 비적용
- UI/앱 상태 변경:
  - 현재 단계에서는 비적용
- env/config mutation:
  - 현재 단계에서는 비적용

---

## 7. 리스크 및 대응

| ID | 리스크 | 대응 |
|---|---|---|
| R1 | 제목 기반 후보 목록에 장르 노이즈가 섞일 수 있음 | 최종 학습 전 시놉시스/1화 감리 1회 필수 |
| R2 | EPUB 구조 편차로 추출 누락 가능 | OPF spine 기반 추출기로 고정 |
| R3 | 루트/하위 폴더 중복본이 섞여 중복 학습 가능 | SSOT 규칙 + 정규화 텍스트 해시 dedupe |
| R4 | Gemini 3.x Pro tuning 지원이 아직 불명확 | 코퍼스는 지금 구축, 튜닝은 2.5 Pro로 실행 |
| R5 | 기존 txt를 섞으면 출처 신뢰성이 무너짐 | 기존 txt 전량 무시 |
| R6 | validation leakage로 과대평가 가능 | random split 금지, title split 사용 |

---

## 8. 최종 판정

이 문서 기준 최종 운영 판단은 아래와 같다.

1. **서비스 모델이 Gemini Pro여야 한다면, 지금 당장 쓸 수 있는 학습 경로는 `Gemini 2.5 Pro supervised tuning`이다.**
2. **`Gemini 3 Pro/3.1 Pro` 계열은 2026-03-14 현재 tuning 지원 모델로 문서상 확정하지 못했다.**
3. **문체 체화를 최대화하려면 raw txt만 쌓는 게 아니라, EPUB에서 깨끗하게 뽑은 본문을 continuation window 중심 JSONL로 바꿔야 한다.**
4. **코퍼스 구축의 첫 우선순위는 추출기 품질이다.** 지금 가장 위험한 건 모델 선택보다도 `본문을 잘못 뽑는 것`이다.

---

## 9. 3-Pass 감리 기록

### Pass 1. Structure and Scope

- Gemini 서비스 모델 기준으로 범위를 다시 고정했다.
- `Gemma CPT`를 주 권장안에서 제거했다.
- 후보 세트와 gold set을 분리했다.

### Pass 2. Evidence and Consistency

- NAS 실경로를 재스캔했다.
- SSOT 수량과 예외 작품을 다시 판정했다.
- EPUB 내부 레이아웃을 27개 표본 기준으로 다시 확인했다.
- Vertex AI 최신 공식 문서만으로 Gemini 경로를 재확인했다.

### Pass 3. Execution and Readability

- `EPUB -> txt -> JSONL -> Gemini tuning` 순서로 단순화했다.
- continuation window 중심 설계로 실행 단위를 구체화했다.
- side-effect 범위를 명시했다.

### Confidence Gate

- 문서 전체 운용 신뢰도: 96%
- 잔여 불확실성:
  - 27개 후보의 장르 순도는 아직 내용 감리 전
  - Gemini 3.x Pro tuning 지원은 공식 문서 추가 확인이 필요

---

## 공식 문서 출처

- Vertex AI tuning overview: https://cloud.google.com/vertex-ai/generative-ai/docs/models/tune-models
- Prepare supervised tuning data for Gemini: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare
- Continuous tuning for Gemini: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-continuous-tuning
- Preference tuning for Gemini: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-preference-tuning
- Gemini 3 Pro model page: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro
- Vertex AI pricing: https://cloud.google.com/vertex-ai/pricing
