import json
import sys

_INPUT = sys.argv[1] if len(sys.argv) > 1 else "treatments/골든루트_tr_block_ALL_v3_snack_5060.json"
_OUTPUT = sys.argv[2] if len(sys.argv) > 2 else _INPUT.replace(".json", "_patched.json")

with open(_INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

v3_blocks = [
  {
    "block_id": "Block 1",
    "title": "애송이들의 건방짐, 노련함으로 짓밟다",
    "content": {
      "context": "2024년 고독사 후 2006년으로 돌아온 한시우. 재벌가의 막내 육신에 들어왔지만, 그의 내면은 산전수전 다 겪은 노련한 범의 영혼이다. 회귀하자마자 주어진 과제는 20억의 시드 머니 확보. 과거의 기억엔 형들에게 비굴하게 머리를 조아렸지만, 이번엔 다르다.",
      "event_villain": "가족 식사 자리. 30대 초반의 새파란 형들은 50대가 넘는 영혼을 가진 시우를 향해 건방지게 훈계를 늘어놓는다. '막내야, 세상이 호락호락한 줄 아냐? 돈맛을 덜 봐서 정신을 못 차리지.' 특히 큰형 한태준은 시우 앞의 고기 접시를 슬쩍 치우며 무시하는 태도를 보인다.",
      "solution": "시우는 헛기침 한 번으로 분위기를 장악한다. 내면에서 우러나오는 진짜 어른의 묵직한 카리스마. 시우가 회장인 아버지를 똑바로 응시하며 말한다. '호적 파기 전에 20억만 깔끔하게 내주십시오. 형님들 하시는 꼬락서니 보아하니 10년 안에 기업 말아먹을 텐데, 제 노후 자금은 제가 알아서 벌겠습니다.' 아버지는 막내의 기백에 눌려 곧바로 수표를 끊어준다.",
      "reward": "어린 형들은 시우의 서늘한 기세에 기가 질려 꿀 먹은 벙어리가 된다. 시우는 곧바로 이 돈을 들고 한미증권으로 향한다. 타깃은 원자재. 젊은 PB가 잘난 척하며 IT 주식을 추천하지만, 시우는 단호하게 WTI 원유에 몰빵할 것을 지시한다. 며칠 뒤 중동 정세 불안으로 유가가 폭등하며 20억은 50억이 된다. 건방 떨던 PB는 시우 앞에 90도로 허리를 굽힌다."
    },
    "stakes": "형들의 도발에 대한 시우의 대응. 독자는 인생 경험이 풍부한 50대 남성이 새파랗고 건방진 재벌 2세들을 어떻게 압도하는지 보며 통쾌함을 체감한다.",
    "power_shift": {
      "protagonist": "육신은 젊지만, 영혼은 무게감 있는 진짜 어른. 카리스마 하나로 집안 서열을 흔들기 시작한다.",
      "antagonist": "큰형 한태준과 젊은 PB. 잘난 척하다가 시우의 실력과 기백 앞에 식은땀을 흘리며 물러선다."
    },
    "relationship_delta": [
      {
        "target": "한정호 (아버지)",
        "before": "한심한 막내",
        "after": "'내 핏줄 맞나?' 호랑이 새끼임을 짐작"
      },
      {
        "target": "잘난 척하던 젊은 PB",
        "before": "'돈 많은 도련님, 내가 요리해 주지'",
        "after": "'회장님, 모시겠습니다!'"
      }
    ],
    "foreshadow": [
      "큰형 한태준이 무리한 해외 투자를 준비 중이라는 대화 조각 - 훗날 크게 말아먹을 복선",
      "시우가 강남 부동산 트렌드를 유심히 살피는 장면 - 실물 자산으로의 진출 암시"
    ],
    "callback": [],
    "emotional_beat": {
      "type": "triumph",
      "intensity": 9
    },
    "tension_level": 4,
    "pov_character": "한시우",
    "location": {
      "place": "본가 대저택 만찬장 / 여의도 증권가",
      "type": "실내"
    },
    "time_span": {
      "duration": "1개월",
      "in_story_time": "2006년 1월 ~ 2월"
    },
    "genre_ext": {
      "capital_before": "0",
      "capital_after": "50억",
      "capital_delta": "+50억",
      "profit_loss": "+30억",
      "method": "기선 제압을 통한 초기 자본 확보 및 확신에 찬 원자재 베팅",
      "investment_type": "원자재 선물 (WTI 롱)",
      "deal_type": "저점 매수, 확실한 익절",
      "leverage_used": ["연륜의 카리스마", "정확한 역사 지식"],
      "opponent": {
        "name": "건방진 형들 및 증권사 애송이",
        "type": "시건방진 젊은 엘리트",
        "weakness_exploited": "연륜 콤플렉스와 얄팍한 지식"
      },
      "historical_event": {
        "name": "2006년 중동 정세 불안으로 인한 유가 급등",
        "year": 2006,
        "month": "2월",
        "how_exploited": "신문 경제면을 꿰고 있던 노련함으로 선취매"
      },
      "time_pressure": "이벤트 직전 진입의 묘미",
      "knowledge_used": "과거 유가 폭등 시기",
      "risk_level": "확실한 수익판 (사이다 보장)",
      "business_sector": "금융/원자재"
    },
    "regression_ext": {
      "is_regressor": True,
      "regression_type": "회귀",
      "timeline_knowledge": {
        "info_used": "중동 사태",
        "accuracy": "완벽",
        "source": "과거 경제지 탐독의 기억"
      },
      "butterfly_effect": {
        "original_event": "20억 구걸 실패",
        "changed_event": "당당하게 요구하여 쟁취",
        "ripple_effect": "아버지의 관심 집중"
      },
      "death_flag": {"avoided": "고독사", "method": "가문과의 빠른 선긋기"},
      "regression_hint": {"slip_up": "없음. 노련한 말투로 덮음.", "suspicion_from": "없음"},
      "future_prep": {"action": "50억 현찰화 완료", "target_event": "알짜 부동산 경매 준비"}
    }
  },
  {
    "block_id": "Block 2",
    "title": "눈먼 돈 줍기, 진짜 부자의 품격 (부동산 & 건설)",
    "content": {
      "context": "2006년 봄. 50억을 쥔 시우의 다음 타깃은 역시 5060세대의 근본, '부동산'이다. 젊은 애들이 머리 싸매며 파생상품 굴릴 때, 진짜 돈은 땅과 철강에서 나온다는 것을 경험으로 안다. 시우는 강남 한복판의 알짜 빌딩 경매에 눈을 돌린다.",
      "event_villain": "경매장에서 마주친 졸부 사장. 그는 롤렉스를 번쩍거리며 시우를 어린애 취급한다. '어이쿠, 학생. 이런 덴 웬일이야? 어른들 노는 물인데.' 졸부는 꼴랑 10억 정도 더 질러놓고 낙찰을 여유만만하게 확신하며 거드름을 피운다.",
      "solution": "시우는 가소롭다는 듯 졸부를 쳐다본다. '그 정도 베팅으로 강남 땅을 드시려고? 사장님, 간덩이가 콩알만 하시네.' 시우는 대리인을 통해 정확한 타이밍에 50억 전액(레버리지 포함)을 베팅하여 압도적인 금액으로 골든 블록 빌딩을 가로챈다. 동시에 정부의 대규모 건설 발표(판교 위례 등)에 맞춰 철강/건설주를 바닥권에서 싹 쓸어 담는다.",
      "reward": "빌딩 낙찰 소식에 졸부 사장은 뒷목을 잡고, 시우는 여유롭게 시가 100억 대의 빌딩주가 된다. 여기에 건설/철강주가 3연상을 기록하며 주식 계좌마저 150억을 찍어버린다. 진짜 부자의 중후한 멋과 압도적 자본력에 얄팍한 배짱의 졸부는 오금을 지린다."
    },
    "stakes": "가벼운 졸부와의 경매 눈치싸움. 5060 독자에게 가장 익숙하고 확실한 재테크 수단인 부동산 점령기를 통해 확실한 대리만족 부여.",
    "power_shift": {
      "protagonist": "단기 투자자에서 거대한 실물 자산(강남 빌딩)을 소유한 진짜 자산가로 등극.",
      "antagonist": "졸부 사장 및 부동산 꾼들. 겉멋만 든 자들의 얄팍한 허세가 시우의 정통파 베팅에 박살남."
    },
    "relationship_delta": [
      {
        "target": "가문 사람들 (형들)",
        "before": "'쟤가 벌어봤자 얼마나...'",
        "after": "'강남 빌딩을 샀다고?' 배아파하며 뒤집어짐"
      }
    ],
    "foreshadow": [
      "건설 경기 활황의 끝물에 대한 시우의 냉정한 평가 - 서브프라임 사태 대비",
      "형들이 건설업에 과도하게 투자하는 모습 - 훗날의 파멸 예약"
    ],
    "callback": ["졸부 사장의 롤렉스 자랑, 시우는 시계조차 차지 않고 결과로 증명"],
    "emotional_beat": {
      "type": "overpowering",
      "intensity": 10
    },
    "tension_level": 3,
    "pov_character": "한시우",
    "location": {
      "place": "강남 알짜 경매장 / 빌딩 최상층 오피스",
      "type": "실내"
    },
    "time_span": {
      "duration": "4개월",
      "in_story_time": "2006년 3월 ~ 6월"
    },
    "genre_ext": {
      "capital_before": "50억",
      "capital_after": "건물(호가 100억) + 주식/현금 150억",
      "capital_delta": "+200억 가치",
      "profit_loss": "확실한 실물 자산 및 폭발적 주식 수익",
      "method": "압도적 경매 입찰 및 뻔한 정부 정책 선취매",
      "investment_type": "상업용 강남 부동산 / 철강·건설주",
      "deal_type": "경매 낙찰 및 주식 스윙",
      "leverage_used": ["노련한 감가상각 계산", "정부 주도 신도시 발표일 암기"],
      "opponent": {
        "name": "졸부 사장",
        "type": "경매 시장의 허세꾼",
        "weakness_exploited": "작은 돈에 벌벌 떠는 소인배 기질"
      },
      "historical_event": {
        "name": "2006년 판교 등 2기 신도시 건설 붐 / 코스피 철강 랠리",
        "year": 2006,
        "month": "봄",
        "how_exploited": "부동산으로 헷지하고 주식으로 공격적인 뻥튀기"
      },
      "time_pressure": "경매 마감 시간의 여유로운 즐김",
      "knowledge_used": "강남 알짜 빌딩의 미래 가치 완벽 인지",
      "risk_level": "저위험",
      "business_sector": "부동산 개발 사업 및 주식"
    },
    "regression_ext": {
      "is_regressor": True,
      "regression_type": "회귀",
      "timeline_knowledge": {
        "info_used": "강남 부동산 폭등 연대기와 신도시 발표",
        "accuracy": "완벽",
        "source": "5060세대 특유의 부동산 감각 + 회귀 치트"
      },
      "butterfly_effect": {
        "original_event": "졸부의 낙찰",
        "changed_event": "시우가 강남 핵심 요지에 베이스캠프 구축",
        "ripple_effect": "강남 큰손들 사이에 시우의 이름이 오르내림"
      },
      "death_flag": {"avoided": None, "method": None},
      "regression_hint": {"slip_up": "없음", "suspicion_from": "없음"},
      "future_prep": {"action": "현금 동원력 과시", "target_event": "다음 스텝인 해외 거물 사냥"}
    }
  },
  {
    "block_id": "Block 3",
    "title": "국격(國格)의 참교육, 거만한 외국 자본을 찢어버리다",
    "content": {
      "context": "2007년 초. 자산 200억대. 시우는 다가올 최악의 거품 붕괴, '서브프라임 모기지 사태'를 준비한다. 이 시기, 버릇없는 외국계 투자은행(IB) 딜러들이 한국 증시를 현금인출기 취급하며 거들먹거린다. 서울에서 열린 프라이빗 파티, 시우는 월스트리트 출신 펀드매니저 '제임스 스미스'를 만난다.",
      "event_villain": "제임스는 샴페인 잔을 흔들며 한국 시장을 대놓고 조롱한다. '코리아는 그저 변두리 놀이터입니다. 미국 주택 시장의 위대함을 알기나 합니까? 리먼 브라더스의 AAA 등급 채권이 뭔지, 당신 같은 변방의 부자들은 평생 가도 모를 겁니다.' 그의 말에 주변의 젊은 한국 펀드매니저들은 굽실대며 동조한다.",
      "solution": "시우는 중후한 미소를 띠며 제임스 앞의 테이블에 스위스 뱅크 잔액 증명서를 툭 던진다. '잔말 말고, 그 잘난 리먼이랑 메릴린치 파산에 내 전 재산 숏 쳐봐. 할 줄은 아나?' 제임스는 200억 잔고에 눈이 튀어나올 듯 놀라면서도, '이 미친 동양인이 미국이 망한다에 베팅한다고?'라며 비웃으며 계약을 수락한다.",
      "reward": "몇 달 후, 뉴센추리 파이낸셜이 파산하며 시우의 숏 포지션은 매일 수십억씩 폭주하기 시작한다. 제임스는 사색이 되어 시우의 강남 오피스로 찾아와 무릎을 꿇는다. '미, 미스터 한... 포지션 청산 좀...' 시우는 국산 고급 세단을 닦으며 쳐다보지도 않는다. '내 앞길 막지 말고 눈깔아라. 아직 양털 깎기는 시작도 안 했어.' 오만한 금발 머리 양키가 한국의 어르신(젊은 몸)에게 영혼까지 털리는 통쾌함."
    },
    "stakes": "미국이 안 망한다고 철석같이 믿는 오만한 양키를 어떻게 합법적으로 짓밟느냐의 통쾌한 싸움.",
    "power_shift": {
      "protagonist": "로컬 벼락부자에서 미국 금융 엘리트들을 개처럼 부리는 세계적 타짜로 스케일이 진화함.",
      "antagonist": "제임스 등 외국계 매니저. 오만방자함에서 완벽한 굴복과 두려움으로 전락."
    },
    "relationship_delta": [
      {
        "target": "제임스 스미스 (외국계 딜러)",
        "before": "한국을 무시하는 양키",
        "after": "시우의 뒤나 닦아주는 충견"
      }
    ],
    "foreshadow": [
      "리먼 파산(본게임) 임박을 예고하는 시우의 대사",
      "한국 경제의 위기가 오지만 시우는 혼자 달러를 쓸어 담을 복선"
    ],
    "callback": ["프라이빗 파티에서의 굽실거리던 젊은 매니저들, 시우 앞에서 고개도 못 듦"],
    "emotional_beat": {
      "type": "vindication",
      "intensity": 10
    },
    "tension_level": 5,
    "pov_character": "한시우",
    "location": {
      "place": "서울 최고급 호텔 라운지 / 강남 시우 빌딩",
      "type": "실내"
    },
    "time_span": {
      "duration": "4개월",
      "in_story_time": "2007년 1월 ~ 4월"
    },
    "genre_ext": {
      "capital_before": "200억 동원",
      "capital_after": "장부상 800억 육박 (수익 폭증 중)",
      "capital_delta": "기하급수적 성장",
      "profit_loss": "미실현 수익 대폭발",
      "method": "서브프라임 파생상품(CDS 등) 최대 레버리지 숏/역배팅",
      "investment_type": "글로벌 매크로 숏",
      "deal_type": "파산 베팅",
      "leverage_used": ["오만한 월가놈의 자만심", "위기 타이밍 100% 암기"],
      "opponent": {
        "name": "제임스와 월가 세력",
        "type": "오만하고 싸가지 없는 외국인 자본",
        "weakness_exploited": "절대 망하지 않는다는 오만과 탐욕"
      },
      "historical_event": {
        "name": "2007 서브프라임 위기 전조 발생",
        "year": 2007,
        "month": "4월",
        "how_exploited": "거품이 터지기 직전에 폭탄을 떠넘기고 스위치 쥠"
      },
      "time_pressure": "터지기만 기다리면 되는 완벽한 꽃놀이패",
      "knowledge_used": "미국 서브프라임 시장 붕괴 역사 완벽 숙지",
      "risk_level": "외견상 고위험, 사실상 무위험 꿀단지",
      "business_sector": "글로벌 금융 시장"
    },
    "regression_ext": {
      "is_regressor": True,
      "regression_type": "회귀",
      "timeline_knowledge": {
        "info_used": "미국 발 모기지 파산 시작점 정확히 타겟팅",
        "accuracy": "완벽",
        "source": "신문과 뉴스에서 귀에 못이 박히게 들었던 역사"
      },
      "butterfly_effect": {
        "original_event": "한국의 막대한 자본이 미국에 물리며 손실",
        "changed_event": "한국인 한시우 혼자서 미국의 부를 흡수",
        "ripple_effect": "여의도 외인 세력들 사이에 '공포의 큰손'이 등장했다는 소문 퍼짐"
      },
      "death_flag": {"avoided": None, "method": None},
      "regression_hint": {"slip_up": "없다. 철저한 애국적(?) 투자 포장", "suspicion_from": "없음"},
      "future_prep": {"action": "수백억 달러화 인출 준비", "target_event": "환율 폭등(원화 약세) 대비"}
    }
  }
]

data[0:3] = v3_blocks

with open(_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
