# Empire Youngest — Weakness Report

Date: 2026-03-27
work_id: `empire_youngest_allsector`
Unit: weakness report
Predecessor: `docs/2026-03-27/empire-youngest-truth-reaudit-report.md`

---

## 0. Summary Stats

- total blocks: 70
- full narrative quality (1,500+ chars content): **12 blocks** (1-5, 46, 50, 52, 62, 65, 70 + Block 6-31 중 대부분)
- compressed (400-700 chars, scene elements present but abbreviated): **12 blocks** (32-43)
- inline summary (under 400 chars, scene-less or near scene-less): **20 blocks** (44-45, 47-49, 51, 53-57, 59-61, 63-64, 66-69)
- scene-deficit blocks requiring attention: **32 blocks** (Block 32-43 compression + Block 44-69 중 scene-less 20개)

Note: Block 46, 50, 52, 62, 65는 44-69 범위 내이나 full narrative 품질을 보유하여 제외.

---

## 1. Block-Level Scene-Deficit Catalog (Block 32-43)

이 구간은 4-key JSON 구조(context/event_villain/solution/reward)를 유지하지만 각 블록 content가 400-700자로 압축됨. Block 1-5의 블록당 2,000자+와 비교하면 서사 밀도가 1/3~1/4 수준.

| block_id | content chars | current content summary | missing scene/tension | should feel like |
|----------|-------------|------------------------|----------------------|-----------------|
| Block 32 | 556 | B2B SaaS 3개사 인수 + J-클라우드 출범. 오승아 데이터 격리 계약. | 병원 고객의 데이터 유출 공포가 2줄 요약. 오승아가 계약에 명시하는 장면이 "조건을 명시한다"로 축약. | 병원장이 계약을 거부하고 오승아가 격리 아키텍처를 화이트보드에 그리며 설득하는 긴장 장면. |
| Block 33 | 528 | 야마모토 통해 사무라이엔터 IP 800개 인수. 일본 정서 반발. | 야마모토와의 도쿄 미팅 장면 부재. 이사회 설득 과정이 "공동 투자 구조를 제안"으로 1줄 축약. | 도쿄 밤거리에서 야마모토와 소주잔 돌리며 이사회 전략을 짜는 tactile scene. |
| Block 34 | 663 | 게임 개발팀 30명 반발, PD 5명 퇴사, 영혼의 검 취소. | 퇴사 현장의 감정적 대면 부재. "Block 18과 같은 프레임을 적용한다"로 해결이 메타-요약화됨. | PD가 사직서를 던지며 "당신은 우리 게임을 이해 못 한다"라고 외치고, 준서가 4초간 눈을 감는(low-affect) 대면 장면. |
| Block 35 | 558 | 권도준 영입. 방산 포석. | 권도준이 거부하는 긴장이 "'나는 국가 안보 사람'이라며 거부"로 축약. 실제 설득 장면의 심리전 부재. | 을지로 국방 관련 술집에서 권도준이 "민간이 방산을 건드리면 사람이 죽는다"라고 말하고, 준서가 넥스칩 NPU 스펙 시트를 테이블에 펼치는 장면. |
| Block 36 | 576 | 타자 POV — K사 본부장이 준서의 IP 장악을 논의. | Block 15/25의 타자 POV(600-800자)에 비해 짧지만 구조는 유지. **다만** Block 46/52 타자 POV(1,600-2,200자)와 비교하면 2/3 축약. K사의 구체적 대응 실패 장면이 약함. | K사 이사회가 실제로 방어 인수를 시도했다가 법적으로 막히는 구체적 좌절 장면. |
| Block 37 | 665 | AI 완성. J-클라우드 ARR 2,000억. 개인정보보호위 사전 점검. | 규제 대응이 오승아의 "사전 준수 보고서 제출"로 1줄 처리. 위원회 담당자의 반응도 1줄. 20조 도달의 emotional weight가 산술 나열로 대체됨. | 개인정보보호위 사무실에서 오승아가 200페이지 보고서를 내밀고 담당자가 넘기다 "이건 뭐... 우리가 만들 가이드라인보다 상세한데요"라고 말하는 장면. '다음.'을 말하는 준서의 미시 모먼트. |
| Block 38 | 589 | K-pop 기획사 인수 + J캐피탈파트너스 출범. 팬덤 반발. | 팬덤 온라인 반대 운동의 실체가 없음. 대형 기획사 이적 시도를 "오승아가 법적 구속력으로 차단"으로 1줄 처리. JSR→J캐피탈 법인명 변경의 서사적 무게가 산술화됨. | 팬덤이 해시태그로 1위를 만들고, 스타빌드 아티스트 본인이 "저는 남겠습니다"라고 라이브에서 선언하는 장면. |
| Block 39 | 488 | OTT J-Stream 설립. 버티컬 전략. | 가장 압축된 블록 중 하나. 넷플릭스/디즈니+와의 경쟁 구도가 "경쟁하지 않는다"로 1줄. 구독자 500만 달성 과정이 산술만. | J-Stream 론칭 날 서버가 터질 뻔하고 김태석이 긴급 스케일링하는 launch night 장면. |
| Block 40 | 476 | J-YAMA 아시아 펀드 2조. 야마모토 LP 보증. | **content 최소 블록**. LP 설득 과정이 "기존 포트폴리오 실적을 보여준다"로 1줄. 야마모토의 "30년 경력에서 가장 뛰어난 투자자" 발언이 대사가 아닌 요약. | 도쿄 야마모토 사무실에서 일본 기관투자자 3명이 테이블에 앉아 "한국 GP에게 1조를?"이라고 묻고, 야마모토가 사무라이엔터 수익률 차트를 스크린에 띄우며 직접 보증하는 장면. |
| Block 41 | 577 | 이준민 공매도 연합. 넥스칩 -12%. 자사주 매입 역공. | 쇼트 스퀴즈가 잠재적으로 가장 사이다 장면인데 "실적 서프라이즈를 발표 시점을 앞당긴다"로 1줄. 이준민의 패배 반응 부재. | 준서가 실적 발표 타이밍을 3일 앞당기자고 정하윤에게 지시하는 장면. 공매도 세력이 실시간으로 포지션이 역전되는 것을 보며 전화기를 내던지는 장면. 이준민이 손실 청산 후 혼자 사무실에 앉아있는 장면. |
| Block 42 | 548 | 공정위 M&A 3개월 동결. 내부 최적화. 무혐의. | 3개월 규제 위기가 가장 약하게 처리된 블록. 공정위 심사 과정, 오승아의 법리 대응이 "데이터를 제출"로 축약. | 공정위 심판정에서 오승아가 시장점유율 데이터를 하나하나 제시하고, 심판관이 "그래서 당신들 어느 시장에서 독점이라는 겁니까"라고 되묻는 법리 긴장 장면. |
| Block 43 | 564 | 이커머스+게임 완성. 자산 35조. 정하윤 "다음은 뭡니까?" | 완성 블록으로서 적절한 마감이나, 정하윤의 "다음은 뭡니까?" 대사가 서사적 무게 대비 맥락 부족. "전부"라는 답의 emotional weight가 scene 없이 대사만으로 처리됨. | 야경이 보이는 J캐피탈 사무실에서 정하윤이 자산 스프레드시트를 닫으며 묻고, 준서가 의자에서 일어서 창밖을 보며 "전부."라고 말하는 장면. 정하윤의 "... 네."가 경외인지 체념인지 모호한 표정. |

**Axis 1 종합**: 12블록 전부 scene-deficit. 공통 패턴: (1) 갈등이 1줄로 축약 (2) 해결이 메타-요약("~로 처리한다") (3) 캐릭터 반응·미시 모먼트 부재 (4) tactile detail(장소, 시간, 감각) 부재.

---

## 2. Inline-to-Narrative Restoration Inventory (Block 44-69)

Block 44-69 중 full narrative 품질 블록(46, 50, 52, 62, 65)은 제외. 나머지 21블록을 priority tier로 분류.

### Priority HIGH — 서사적 핵심 이벤트인데 inline 상태 (7블록)

| block_id | content chars | current inline content (quoted) | minimum narrative elements for restoration |
|----------|-------------|-------------------------------|------------------------------------------|
| Block 54 | 200 | "ARC-05 마감. 금융PE 15조. 패션 글로벌. 식품 아시아15국. SMR 착수. 총60조. 이준혁 전화: '아버지 편찮으셔.'" | 이준혁 전화가 감정 arc의 핵심 전환점. 통화 장면 전체 필요. 준서가 수화기를 내려놓은 뒤의 미시 모먼트. 최다은이 "감지"하는 장면. '다음.' 여섯 번째의 tone 변화(짓는→구하는). |
| Block 58 | 562 | 이준혁이 J캐피탈을 직접 찾아오는 장면. "준서야, 아버지가 치매 초기 진단..." | **이미 중간 수준 서사 보유(562자)**. 하지만 형제 대면 장면의 물리적 묘사(사무실 어디에 앉았나, 시선, 침묵의 길이) 부재. 5분간 형을 보는 동안의 inner monologue 부재. Block 1 회귀 기억과의 callback(전생에서 형이 구속됐던 기억) 필요. |
| Block 61 | 280 | "이준민 분식회계로 구속. 제국 계열사 3곳 경영 공백. 주가 -20%." | 이준민 구속 장면 자체가 부재. Block 41에서 공매도 실패 후 어떻게 분식회계까지 갔는지 내면 경로 부재. 준서가 뉴스를 보는 장면(형제에 대한 감정 억제 균열 가능성). |
| Block 66 | 416 | "지분 51.3%. 이사회 첫 출석. '정리하겠습니다.' 이사진 12명 침묵." | 12년 여정의 핵심 payoff 장면. 이사회장의 물리적 묘사, 12명의 표정, 준서가 일어서는 순간의 weight. Block 1 옥상 기억과의 대비. 이사장(부친 대리)의 "발언하시겠습니까?"에 담긴 감정. |
| Block 59 | 383 | "J제국홀딩스 설립 선언. 법인 등기만. '먹는다. 내 방식으로.'" | 서사 정점 선언인데 scene-less. "먹는다. 내 방식으로."를 말하는 순간의 물리적 상황(어디서, 누구 앞에서, 아니면 혼자서?). 이 선언이 Block 1의 "제국그룹은 나 혼자 짓는다"와 연결되는 callback. |
| Block 63 | 357 | "SMR 인허가 통과. 에너지 완성. 90조. 채권단 직접 협상 제안." | 채권단 협상 시작이 제국 최종전의 opening shot인데 1줄. 채권단 회의실에서 준서가 직접 프레젠테이션하는 장면 필요. |
| Block 64 | 339 | "레이첼 5조 + 야마모토 5조 = 10조 집행. 해운 JV." | Block 62에서 정하윤이 47분 만에 10조를 확보한 감동 장면의 실행 편. 실제 자금 집행 과정, 이자 5,000억 조건 수용의 inner monologue. |

### Priority MEDIUM — 섹터 진입 블록으로 domain texture 필요 (9블록)

| block_id | content chars | current inline content (quoted) | minimum narrative elements for restoration |
|----------|-------------|-------------------------------|------------------------------------------|
| Block 44 | 230 | "PE 1호 펀드 5조. GP 1조+LP 4조. 정하윤 펀드레이징." | 산업 투자자→기관 GP 진화 모멘트. 국민연금 앵커 코미트먼트 장면. 정하윤이 기관 LP를 직접 설득하는 첫 대면. |
| Block 45 | 173 | "PE 첫 딜: 새한저축은행+J-핀테크. 금융 인가 3개월." | 오승아의 금융 인가 주도 장면. Block 46(타자 POV)에서 금감원이 놀라는 장면의 setup이 되어야 하는데 너무 얇음. |
| Block 47 | 147 | "K-럭셔리 2개사 3,000억. 파리 패션위크. 스타빌드 아티스트 런웨이." | 파리 패션위크 장면이 잠재적 visual spectacle인데 완전 부재. 유럽 럭셔리 냉소→K-pop 팬덤 역전의 드라마. |
| Block 53 | 105 | "오승아 2년 준비. 코리아뉴클리어 인수 3,000억." | **content 최소 블록 (105자)**. SMR이라는 heavy-tech 섹터의 domain texture가 0. 원자력 설비, 규제 환경, 기술 설명이 전무. |
| Block 55 | 344 | "드론 스타트업 스카이포스 1,500억. 권도준 납품 1호. AI NPU 탑재." | 방산 진입의 첫 장면. 방위사업청 납품 과정의 보안·기술 texture. AI 드론 시연 장면. |
| Block 56 | 256 | "서해안 해상풍력 500MW. 베스타스 JV. 통합 에너지 제안." | 에너지 입찰 경쟁 장면 부재. 통합 제안의 구체성 부족. |
| Block 57 | 391 | "반핵 시위. 인허가 18개월 유예. 방산/EV로 선회." | SMR 좌절이 준서의 첫 명확한 타이밍 실패인데 감정적 무게 부재. "기다리지 않는다"는 교리의 시험 장면. |
| Block 60 | 273 | "전고체 배터리 솔리드파워코리아 5,000억. LG/삼성SDI 경쟁." | 배터리 대기업과의 입찰 경쟁이 "독립 라이선싱 모델 제안"으로 1줄. 창업자 설득 장면 필요. |
| Block 67 | 276 | "방산/우주 완성. 구조조정 착수. 노조 반발. 재배치 프로그램." | 제국 구조조정의 첫 실행인데 scene-less. 노조 대표와의 대면, 부실 계열사 경영진 교체 장면. |

### Priority LOW — 완성/전환 블록으로 현재 분량도 기능적 (5블록)

| block_id | content chars | current inline content (quoted) | minimum narrative elements for restoration |
|----------|-------------|-------------------------------|------------------------------------------|
| Block 48 | 145 | "H그룹 비공식 접촉. 바이오 공동연구 제안. 연합 이탈." | 연합 균열의 political drama가 잠재적으로 풍부하나 독립 복원 시 서사 흐름 대비 우선도 낮음. |
| Block 49 | 159 | "IP800+아티스트+OTT+패션 통합 라이선싱. 연 5,000억." | 비즈니스 정산 블록. 장면보다 수치가 핵심. |
| Block 51 | 121 | "퇴원 1주 후. 그린프로틴+밥심=2,000억. 식품 진입." | Block 50(입원)의 여파로 바로 복귀하는 것의 emotional weight는 있으나, Block 50이 이미 이를 충분히 커버. |
| Block 68 | 317 | "J제국홀딩스 공식 출범. 180조. 취임 연설 없음. 법인 등기만." | "취임 연설 없음"이 오히려 캐릭터를 말해주는 장면. 현재도 기능적. 다만 48,000명 직원의 반응 1줄 추가 가능. |
| Block 69 | 208 | "글로벌 AAA. 회사채 발행. 200조." | 완결 준비 블록. 재무 정상화 확인. scene 복원 우선도 낮음. |

**Axis 2 종합**: 21블록 중 HIGH 7 / MEDIUM 9 / LOW 5. 최소 복원 대상: HIGH 7블록. 이상적 복원 대상: HIGH + MEDIUM = 16블록.

---

## 3. 타자 POV Diminishing Returns

### 확인된 타자 POV 블록

| block_id | POV character | content chars | what it adds | what it costs (protagonist agency loss) | recommendation |
|----------|--------------|---------------|-------------|----------------------------------------|----------------|
| Block 15 | S그룹 기획조정실장 | ~600 | 재벌 연합이 준서를 처음 인식. "반도체 다 먹었다." 원 패턴 STEP 2 첫 실행. | 준서 부재. 타자 시점이 처음이라 신선함 있음. | **keep** |
| Block 25 | S그룹 기획조정실장 | ~600 | "동시에 세 개?"라는 반응. 원 패턴 STEP 2 두 번째. | 같은 인물(S그룹 실장) 반복. Block 15와 동일 패턴. | **keep — 단, Block 36과 차별화 필요** |
| Block 36 | K사 전략기획본부장 | 576 | "IP까지 쓸어담고 있다." 게임 섹터 타자 반응. | 압축 구간 내 타자 POV로 준서 agency가 이미 약한 구간에서 추가 부재. Block 15/25와 구조 동일(기득권 무력감). **패턴 피로 시작점.** | **merge into protagonist POV** — K사 대응이 준서의 정보망으로 들어오는 형태로 전환. 준서가 K사 움직임을 인지하고 무시하는 장면으로 바꾸면 agency 회복. |
| Block 46 | 금감원 박정호/김수연 | 1,676 | 오승아의 법적 천재성을 타자 눈으로 입증. "선례가 없다." 금융 규제 장면의 domain texture. | 준서 완전 부재. 그러나 오승아 캐릭터 성장을 보여주는 유일한 심층 장면. 타자 POV 중 가장 domain-specific하고 비반복적. | **keep** — 유일하게 "기득권 무력감" 패턴을 넘어 "제도적 무력감"을 보여주는 변주. |
| Block 52 | Citadel 제임스 리/사라 킴 | 2,240 | Phase 3 적대자(글로벌 헤지펀드) 본격 등장. "현금 부족할 거야." Block 62/65의 필수 setup. | 준서 완전 부재. 그러나 Block 65 역스퀴즈의 사전 조건을 세팅하므로 서사 기능이 가장 높음. | **keep** — 없으면 Block 65가 deus ex machina가 됨. |
| Block 65 | 이준서 + Citadel 딜데스크 | 2,386 | 역스퀴즈 실행. 가장 높은 사이다 장면. 타자 전환은 Citadel이 당하는 것을 보여주기 위한 것. | 준서→Citadel 전환이 자연스러움. 이것은 "타자 POV 블록"이 아니라 "듀얼 POV 블록". | **keep** — 구조적으로 듀얼 POV가 필요한 유일한 장면. |

### 타자 POV 분석 종합

**패턴**: Block 15→25→36은 동일 구조(기득권이 준서를 논의하지만 막을 방법이 없음)의 3회 반복. 3회째(Block 36)에서 diminishing returns 시작.

**처방**:
- Block 15, 25: keep (초기 신선함 + 패턴 확립)
- Block 36: **merge** — 준서 POV로 전환하여 K사 반응을 정보로 수신하는 형태
- Block 46: keep (구조 변주)
- Block 52: keep (필수 setup)
- Block 65: keep (듀얼 POV)

**Note**: 오더에서 언급한 "Block 41 타자 POV"는 실제 확인 결과 이준서 POV임. 이준민 공매도 연합이 등장하지만 POV는 준서. 타자 POV 목록에서 제외.

---

## 4. Emotional Arc Gap Map

### 4.1 최다은 — 유일한 일상 연결고리

| block_id | appearance type | content |
|----------|----------------|---------|
| 50 | **Entry** (첫 등장) | 입원 5일째 병문안. "너 지금 웃었어? 8년 만에 처음 보는데." 감정 억제 균열 첫 목격자. |
| 51 | brief mention | "쉬면 죽어?" 대사 반복 (Block 50 callback). |
| 54 | brief mention | 이준혁 전화 후 준서 표정 변화를 "최다은만 감지". |
| 58 | brief scene | 이준혁 방문 후 커피를 내려놓고 아무 말 안 함. 감정 억제 균열 두 번째 장면. |
| 62 | text mention | "또야?"라는 문자. 준서 미답장. |
| 70 | **Final** | "새해 복 많이 받아." 12년간 첫 개인 메시지. 감정 균열의 결정적 장면. |

**Gap intervals**:
- Block 50→51: 1블록 (OK)
- Block 51→54: 3블록 (OK)
- Block 54→58: 4블록 (OK)
- **Block 58→62: 4블록** (OK but 등장이 문자 1줄)
- **Block 62→70: 8블록** — 가장 긴 공백. 준서가 Citadel 역스퀴즈, 경영권 확보, 구조조정, 홀딩스 출범을 하는 동안 최다은 완전 부재.

**Gap closing recommendation**: Block 66(경영권 확보) 또는 Block 68(홀딩스 출범)에 최다은 1-beat 삽입. "뉴스 봤어. 대단하다."가 아닌 일상적 한 마디("밥은 먹고 다녀?")로 준서의 감정선에 접촉하는 것이 Block 70 문자의 emotional payoff를 높임.

**Anchor 판정**: 최다은 arc는 "low-affect protagonist의 delayed emotional crack"이라는 creative anchor의 핵심 운반체. 현재 Block 50과 70에서만 제대로 작동하며 중간 구간(51, 54, 58, 62)은 mention 수준. 이는 crack이 점진적이 아니라 **이진적(off→on)**으로 느껴지게 만든다.

### 4.2 정하윤 — CFO→CIO 진화

| block range | appearance density | note |
|------------|-------------------|------|
| 3-30 | **극히 높음** (거의 매 블록) | 초기부터 핵심 조력자. 펀딩, IR, 재무. |
| 32-43 | 35, 41, 43에만 등장 | 압축 구간에서 등장 빈도 급감. |
| 44-50 | 44, 48, 50 | PE 펀드레이징(44), 입원 시 서명 위임(50) |
| 50-70 | 61, 62, 65, 70 | Block 62 "11년입니다", Block 65 실행 인정 |

**Gap intervals**:
- **Block 43→50: 7블록** — 정하윤이 PE 설립(44)과 재벌연합(48)에 잠깐 나오지만 scene-level 부재.
- **Block 50→61: 11블록** — 가장 긴 공백. 정하윤의 CFO→CIO 진화가 이 기간에 일어나야 하는데 장면 부재.

**Gap closing recommendation**: Block 54(금융+패션 완성)에 정하윤 1-beat 삽입. '다음.' 여섯 번째를 정하윤이 아닌 다른 방식으로 받는 장면(예: 60조 스프레드시트를 닫으며 혼자 고개를 숙이는 정하윤 — 12년의 무게).

### 4.3 이준혁 — 형제 갈등→동맹

| block_id | appearance | content |
|----------|-----------|---------|
| 14 | mention | HBM4 대량 납품 |
| 19 | scene | 형 첫 대면 |
| 20 | mention | 반도체 완성 |
| 52 | Citadel mention | "장남과 관계 개선 중" |
| 54 | phone call | "아버지 편찮으셔" |
| 58 | **key scene** | J캐피탈 방문. "2년 뒤에 내가 가겠다." |
| 61 | mention | 이준민 구속 관련 |
| 65-66 | mention→scene | 지분 위임 10%, 이사회 |
| 70 | mention | "이준혁은 아이들과 집에 있다" |

**Gap intervals**:
- **Block 20→52: 32블록** — 가장 심각한 공백. 형 첫 대면(19-20) 이후 32블록 동안 형제 arc가 완전 정지. Block 52는 Citadel의 분석에서 간접 언급일 뿐.
- **Block 20→54: 34블록** — 실질적으로 형이 다시 등장하기까지의 공백.

**Gap closing recommendation**: Block 35-40 구간(2031년)에 이준혁 1-beat 삽입. 제국그룹이 악화되는 뉴스를 준서가 보는 장면, 또는 형에게서 온 부재중 전화를 무시하는 장면. 이것이 Block 54 전화의 setup이 됨.

### 4.4 오승아 — 적대→법무 총괄

| block range | appearance density | note |
|------------|-------------------|------|
| 7-29 | 높음 (7, 11, 13, 16, 17, 20, 21, 22, 23, 28, 29) | 적대에서 중립으로 전환, 법무 역할 확립 |
| 32-43 | 32, 35, 37, 42 | 규제 대응 전담 (J-클라우드, 공정위) |
| 44-70 | 45, 46, 53, 57, 62, 65, 67, 70 | 안정적 등장. Block 46에서 타자 POV를 통한 간접 spotlight. |

**Gap intervals**: 최대 공백 5블록 수준. **가장 안정적인 arc.** 오승아는 모든 규제/법률 이벤트에 등장하며 공백이 거의 없음.

**Gap closing recommendation**: 불필요. 현재 arc가 가장 건강함.

---

## 5. Sector Texture Recovery List

Block 32-69에서 섹터별 domain-specific scene pressure 상태:

| sector | block_id | current state | concrete scene suggestion |
|--------|----------|--------------|--------------------------|
| AI/SaaS | 32 | timing summary | 병원장이 데이터 유출을 우려하며 계약을 거부하는 대면. 오승아가 격리 아키텍처 시연. |
| 게임/IP | 33 | partial scene | 도쿄 사무라이엔터 이사회. 일본어로 진행되는 회의에서 야마모토가 통역 겸 보증. |
| 게임/IP | 34 | partial scene | PD가 개발실에서 사직서를 던지는 물리적 대면. "영혼의 검" 프로토타입이 모니터에 떠있는 상태. |
| 방산 | 35 | timing summary | 권도준의 과거(국정원 시절 에피소드)가 1줄이라도 드러나는 인물 깊이. |
| AI 완성 | 37 | timing summary | 개인정보보호위 사무실. 오승아의 200페이지 보고서. 위원의 당혹. |
| 엔터/K-pop | 38 | timing summary | 팬덤 해시태그 전쟁. 아티스트 본인의 선택. 대형 기획사 이적 시도 차단. |
| OTT | 39 | timing summary | J-Stream 론칭 나이트. 서버 이슈 또는 구독자 실시간 카운터. |
| 펀드 | 40 | timing summary | 도쿄 LP 미팅. 야마모토의 직접 보증. 일본 기관투자자의 보수적 질문. |
| 금융/PE | 44 | timing summary | 국민연금 코미트먼트 미팅. 기관 LP 앞에서의 정하윤 프레젠테이션. |
| 금융/핀테크 | 45 | timing summary | 오승아의 금융 인가 프로세스. 저축은행 인수 서명. |
| 패션/럭셔리 | 47 | timing summary | 파리 패션위크. 유럽 비평가의 냉소→K-pop 아티스트 런웨이→역전. |
| 정치 | 48 | timing summary | H그룹 비공식 접촉 장면. 호텔 로비 또는 골프장. 연합 균열의 정치적 texture. |
| 콘텐츠/IP | 49 | timing summary | 넷플릭스/디즈니/레고와의 라이선싱 협상 테이블. |
| 식품/대체육 | 51 | timing summary | 대체육 공장 방문. 또는 밥심글로벌의 아시아 진출 첫 매장. |
| 에너지/SMR | 53 | timing summary | 코리아뉴클리어 원자로 설계실. 엔지니어와의 기술 대화. |
| 에너지/풍력 | 56 | timing summary | 서해안 해상풍력 현장. 바다 위 터빈 기초 공사. 또는 입찰 경쟁 발표장. |
| 에너지/규제 | 57 | partial scene | 반핵 시위 현장. 국회 청문회. 준서가 TV로 보며 "기다리지 않는다"를 결정하는 장면. |
| EV/배터리 | 60 | timing summary | 솔리드파워 창업자의 연구실. 전고체 배터리 셀 시연. "기술이 묻히면 안 됩니다." |
| 방산/우주 | 55 | partial scene | 방위사업청 드론 시연장. AI 드론이 자율비행하는 장면. 군 관계자의 반응. |
| 해운/물류 | 64 | timing summary | 싱가포르 JV 서명. 항구 또는 물류 허브 방문. |
| 구조조정 | 67 | timing summary | 노조 대표와의 대면. 부실 계열사 직원의 재배치 안내. |
| 경영권 | 66 | partial scene | 이사회장. 12명의 이사. 준서의 "정리하겠습니다." |

**Anchor 판정**: Block 32+에서 "all-sector rolling structure"와 "domain-specific scene pressure"가 "timing summary"로 대체됨. 각 섹터의 고유한 언어(반도체의 nm, 바이오의 임상, 금융의 LP/GP, 방산의 보안인가)가 Block 1-31 수준으로 살아있으려면 최소 1개의 domain-specific dialogue가 각 블록에 필요.

---

## 6. Revision Priority Matrix

impact = (서사적 무게 × anchor 관련도 × 후속 블록 의존도) 기준 상위 10블록:

| rank | block_id | title | current state | impact if restored | rationale |
|------|----------|-------|--------------|-------------------|-----------|
| 1 | **Block 66** | 경영권 확보. 이사회 첫 발언 | 416자 inline | **극대** | 12년 여정의 payoff. Block 1 옥상→Block 66 이사회장의 대칭 구조가 작품의 spine. 현재 scene-less. |
| 2 | **Block 54** | 금융+패션 완성. 이준혁 전화 | 200자 inline | **극대** | "짓는 것→구하는 것"으로의 전환점. 이준혁 전화 + 최다은 감지 + 정하윤 감정 arc 3개가 교차. |
| 3 | **Block 59** | J제국홀딩스 선언. "먹는다. 내 방식으로." | 383자 inline | **극대** | 서사 정점 선언. Block 1 "제국은 나 혼자 짓는다"의 공개 버전. |
| 4 | **Block 61** | 이준민 구속 | 280자 inline | **high** | 형제 arc 해소. Block 41 공매도 실패의 결과. 3세 중 마지막 적대자 퇴장. |
| 5 | **Block 41** | 이준민 공매도 연합 | 577자 compressed | **high** | 가족 내 적대의 정점. 쇼트 스퀴즈가 Block 65 역스퀴즈의 prototype. 현재 사이다가 산술로 처리됨. |
| 6 | **Block 42** | 공정위 3개월 동결 | 548자 compressed | **high** | 규제 위기가 가장 약하게 처리됨. 오승아 캐릭터의 법리 역량 직접 장면 필요. |
| 7 | **Block 63** | 에너지 완성. 채권단 협상 | 357자 inline | **high** | 제국 최종전의 opening shot. 현재 scene-less. |
| 8 | **Block 34** | 게임 개발팀 퇴사 | 663자 compressed | **medium-high** | 인재 이탈에 대한 준서의 냉정한 대응이 캐릭터 핵심. "사람은 가도 IP는 남는다." |
| 9 | **Block 33** | 일본 게임사 IP 800개 | 528자 compressed | **medium-high** | 야마모토 동맹의 시작점. 도쿄 미팅이 tactile scene이면 Block 40/62/65의 동맹 무게가 올라감. |
| 10 | **Block 47** | K-럭셔리 + 파리 패션위크 | 147자 inline | **medium** | visual spectacle 잠재력. K-pop×럭셔리 교차가 독자 쾌감 포인트. |

---

## 7. Next Unit Recommendation

**targeted TR revision — Block 32-43 compression zone first**

근거:
1. Block 32-43은 이미 4-key JSON 구조를 보유하므로 "확장"만 필요 (구조 재설계 불필요)
2. 이 구간의 복원이 Block 44-69의 setup을 강화 (예: Block 42 공정위 장면 복원 → Block 46 타자 POV의 맥락 강화)
3. 12블록 일괄 확장이므로 scope가 명확
4. 복원 후 Block 44-69 중 HIGH priority 7블록으로 이동

단, 복원 순서는 Revision Priority Matrix 순위를 따르되, 작업 단위는 "zone" 단위(32-43 먼저, 그 다음 44-69 HIGH)가 효율적.

---

## 8. Handoff

```text
work_id: empire_youngest_allsector
current_stage: audit_or_repair
finished_unit: weakness report
changed_files: docs/2026-03-27/empire-youngest-weakness-report.md
next_unit: targeted TR revision (Block 32-43 compression zone)
stop_reason: gap catalog complete — 5 axes cataloged, revision priority matrix produced, no block rewriting performed
```
