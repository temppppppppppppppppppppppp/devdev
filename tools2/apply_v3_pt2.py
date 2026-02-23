import json
import sys

_INPUT = sys.argv[1] if len(sys.argv) > 1 else "treatments/골든루트_tr_block_ALL_v3_snack_5060.json"
_OUTPUT = sys.argv[2] if len(sys.argv) > 2 else _INPUT.replace(".json", "_patched.json")

with open(_INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

v3_blocks_4_to_6 = [
  {
    "block_id": "Block 4",
    "title": "리먼 브라더스의 강물, 부의 대이동",
    "content": {
      "context": "2008년 가을. 한시우가 서브프라임에 베팅한 200억이 1,500억으로 불어나 있다. 전 세계 증시는 피바다다. 강남 유수의 자산가들은 반토막 난 펀드 잔고를 보며 소주를 마시지만, 시우의 강남 오피스에선 최고급 돔 페리뇽이 터진다. 그의 타깃은 이제 폭락한 알짜 국내 기업 사냥이다.",
      "event_villain": "과거 시우를 깔보던 강남 1타 PB 센터장 최영민. 그는 리먼 사태로 고객 돈 수천억을 날려먹고 파산 위기에 몰렸다. 그는 지푸라기라도 잡는 심정으로 한시우의 사무실에 무작정 찾아와 무릎을 꿇는다. '한 대표님... 제발 200억만 융통해 주십시오. 1년 안에 두 배로 이자 쳐드리겠습니다. 저 이대로면 한강 가야 합니다!'",
      "solution": "시우는 소파에 깊숙이 기대앉아 시가(Cigar) 연기를 내뿜는다. '최 센터장, 나한테 투자 운운하며 가르치려 들던 게 엊그제 같은데.' 시우는 차갑게 센터장을 내려다본다. '내 돈 빌려줄게. 대신 당신이 관리하던 VVIP 고객 장부, 그리고 당신 집구석 등기까지 전부 내 앞으로 돌려. 이자는 월 3푼(3%)이다.' 센터장은 눈물을 뚝뚝 흘리며 도장을 찍는다. 시우가 강남 자산가 네트워크를 통째로 삼키는 순간이다.",
      "reward": "시우는 1,500억의 잭팟을 사실상 확정 짓는다. 게다가 강남 최고의 알짜 네트워크 장부를 손에 넣으며, 대한민국의 진정한 '숨은 전주(錢主)'로 등극한다. 반면 잘난 척하던 최 센터장은 시우의 돈 심부름꾼 전락한다. 돈과 권력의 씁쓸하고 묵직한 계급 역전."
    },
    "stakes": "없음. 이미 이긴 게임의 화려한 피날레 점검. 하지만 이 과정에서 과거 자신을 무시했던 기득권층을 확실하게 발밑에 꿇림으로써 독자들에게 강렬한 대리만족(Cider)을 선사한다.",
    "power_shift": {
      "protagonist": "재벌 3세 도련님에서, 대한민국 상위 0.1%를 쥐고 흔드는 강남의 진짜 큰손으로 격상.",
      "antagonist": "대한민국의 내로라하는 증권가 권력자들이 시우 앞에선 그저 목숨 구걸하는 파리 목숨이 됨."
    },
    "relationship_delta": [
      {
        "target": "최영민 센터장 (강남 1타 PB)",
        "before": "오만한 강남의 뱀",
        "after": "시우가 기르는 사냥개"
      }
    ],
    "foreshadow": [
      "VVIP 장부에 적힌 가문 내 정관계 로비 명단 - 향후 가문 장악 레이스의 강력한 무기"
    ],
    "callback": [
      "Block 1에서 어린 시절 형들의 심부름꾼이었던 서러운 과거에 대한 통렬한 보상"
    ],
    "emotional_beat": {
      "type": "climax",
      "intensity": 10
    },
    "tension_level": 3,
    "pov_character": "한시우",
    "location": {
      "place": "강남 테헤란로 한시우의 최상층 펜트 오피스",
      "type": "실내"
    },
    "time_span": {
      "duration": "3개월",
      "in_story_time": "2008년 9월 ~ 11월"
    },
    "genre_ext": {
      "capital_before": "800억대 미실현 이익",
      "capital_after": "현금 1,500억 + 강남 VVIP 채권/장부",
      "capital_delta": "막대한 자본 + 무형의 권력",
      "profit_loss": "서브프라임 숏 최종 청산",
      "method": "위기에 처한 엘리트의 목줄을 쥐고 흔드는 고리대업",
      "investment_type": "파생 청산 및 사모 채권 인수",
      "deal_type": "채권 및 네트워크 흡수",
      "leverage_used": ["리먼 파산이라는 공포", "압도적 현금력"],
      "opponent": {
        "name": "최영민 센터장",
        "type": "몰락한 기득권 엘리트",
        "weakness_exploited": "파산에 대한 본능적 공포"
      },
      "historical_event": {
        "name": "2008년 하반기 글로벌 금융 위기 본격화",
        "year": 2008,
        "month": "가을",
        "how_exploited": "절망의 절정에서 홀로 폭리를 취하며 탐욕의 끝을 보여줌"
      },
      "time_pressure": "시우에겐 시간의 제약이 없다. 조급한 건 상대뿐.",
      "knowledge_used": "금융위기 바닥 시점에 대한 100% 확신",
      "risk_level": "없음 (군림의 시간)",
      "business_sector": "종합 투자 및 사금융"
    },
    "regression_ext": {
      "is_regressor": True,
      "regression_type": "회귀",
      "timeline_knowledge": {
        "info_used": "리먼 파산 이후 한국 금융 시장 패닉 최고조 시점",
        "accuracy": "완벽",
        "source": "과거 뉴스 도배의 기억"
      },
      "butterfly_effect": {
        "original_event": "최 센터장 자살 혹은 해외 도피",
        "changed_event": "시우의 노예가 되어 강남 자본을 시우에게 상납",
        "ripple_effect": "강남 큰손들의 지형도가 한시우 중심으로 비밀리에 개편됨"
      },
      "death_flag": {"avoided": None, "method": None},
      "regression_hint": {"slip_up": "전혀 없음.", "suspicion_from": "없음"},
      "future_prep": {"action": "방대한 현금 실탄 장전", "target_event": "가족(형들)의 기업 부도 처리 방어 겸 강탈"}
    }
  },
  {
    "block_id": "Block 5",
    "title": "집안 단속, 호로자식들의 최후 (가권 탈취)",
    "content": {
      "context": "2008년 말. 금융위기와 중소형 조선사(KIKO 사태 등) 문제로 집안 사업이 휘청거린다. 큰형 한태준과 둘째형 한태민이 방만하게 벌려놓은 핵심 계열사들이 부도 위기다. 형들은 아버지 한정호 회장 앞에서 눈물 콧물 짜며 구걸한다. 아버지는 뒷목을 잡지만 현금이 부족해 속수무책이다.",
      "event_villain": "큰형 한태준은 마지막 발악으로 시우를 물고 늘어진다. '아버지! 저 막내 자식, 장외에서 굴리는 돈 1,000억 넘는다는 소문 다 났습니다! 당장 뺏어다 계열사부터 막아야 합니다! 가문을 위해 당연히 내놔야죠!' 염치도 철면피도 없는 전형적인 거만하고 무능한 장남의 꼰대질.",
      "solution": "문이 열리고 한시우가 들어선다. 정장을 빼입고 변호사를 대동한, 완벽한 사냥꾼의 모습이다. 시우는 한태준의 얼굴에 그룹 계열사 부채 내역과 차명 계좌 횡령 내역서를 집어 던진다. '가문을 말아먹은 개자식이 어디서 주둥이를 털어.' 아버지는 사색이 된다. 시우는 차갑게 선언한다. '제가 그룹 유동성 풀로 뚫어드립니다. 조건은 하나. 태준 형과 태민 형이 가진 지주사 지분 전량 저한테 양도하십시오. 안 그러면 오늘 부로 우리 그룹 간판 내립니다.'",
      "reward": "아버지는 형들의 따귀를 후려갈긴 후, 떨리는 손으로 막내의 서류에 도장을 찍는다. 형들은 알거지가 되어 계열사 말단 영업사원으로 강등당하며 오열한다. 시우는 단돈 1,500억으로 수조 원대 가치인 대기업 지주사의 실질적 지배주주, 새로운 가주(家主)의 자리에 오른다. 구시대적 장남 우선주의를 박살 내는 처절하고 통쾌한 사이다."
    },
    "stakes": "가주 자리를 둔 핏줄의 전쟁. 하지만 막대한 현금을 쥔 시우의 '돈과 법리' 앞에 피는 물보다 옅다.",
    "power_shift": {
      "protagonist": "집안의 이단아에서 그룹 전체를 호령하는 옥좌의 주인으로 군림.",
      "antagonist": "형들(한태준, 한태민). 권세와 허영을 모두 빼앗기고 평민보다 못한 노예로 전락."
    },
    "relationship_delta": [
      {
        "target": "한태준, 한태민 (형들)",
        "before": "오만함과 견제",
        "after": "파멸, 비참함, 무릎 연골이 닳도록 빌고 또 빎"
      },
      {
        "target": "한정호 (아버지)",
        "before": "'쓸만한 자식'",
        "after": "'무서운 범'. 가문의 미래를 의탁하며 권좌를 내어줌"
      }
    ],
    "foreshadow": [
      "그룹 장악 후 구시대적 임원진(임원회) 물갈이 파동 예고",
      "다음 먹거리로 통신/모바일 시장(아이폰 강림 전야) 언급"
    ],
    "callback": [
      "Block 1에서 20억 던져주고 비웃던 형들, 이제 1,500억 앞에 인생이 파멸됨"
    ],
    "emotional_beat": {
      "type": "overpowering",
      "intensity": 10
    },
    "tension_level": 4,
    "pov_character": "한시우",
    "location": {
      "place": "대기업 본사 최상위 회장실",
      "type": "실내"
    },
    "time_span": {
      "duration": "1개월",
      "in_story_time": "2008년 12월"
    },
    "genre_ext": {
      "capital_before": "1,500억",
      "capital_after": "지주사 지분 40% (수조 원대 그룹 장악)",
      "capital_delta": "그룹 사유화 및 현금 투입",
      "profit_loss": "단숨에 재계 순위권 가주 등극",
      "method": "유동성 위기를 악용한 지분 강제 수용 (적대적 M&A급 가족 사냥)",
      "investment_type": "경영권 인수 (그룹 승계)",
      "deal_type": "피도 눈물도 없는 빅딜",
      "leverage_used": ["부도 어음이 돌아오는 시간적 강박", "형들의 부패/횡령 자료"],
      "opponent": {
        "name": "한태준, 한태민",
        "type": "무능력한 적통 꼰대",
        "weakness_exploited": "회사가 망하면 깜빵에 가야 한다는 죽음의 공포"
      },
      "historical_event": {
        "name": "2008 KIKO 사태 및 기업 줄도산",
        "year": 2008,
        "month": "겨울",
        "how_exploited": "가장 취약한 순간, 가장 확실한 목줄을 움켜쥠"
      },
      "time_pressure": "부도 처리 직전의 긴박함 (형들에게만)",
      "knowledge_used": "과거 가문이 부도났던 핵심 아킬레스건을 그대로 찌름",
      "risk_level": "저위험",
      "business_sector": "그룹 경영"
    },
    "regression_ext": {
      "is_regressor": True,
      "regression_type": "회귀",
      "timeline_knowledge": {
        "info_used": "가문 기업의 부도 시나리오 회피",
        "accuracy": "완벽",
        "source": "전생 가문 몰락의 처절한 기억"
      },
      "butterfly_effect": {
        "original_event": "가문 전체가 길거리에 나앉음",
        "changed_event": "무능한 형들만 길거리에 나앉고 시우는 재벌 회장 등극",
        "ripple_effect": "재계 서열 지형도에 거대 메기 '한시우'의 등장 공표"
      },
      "death_flag": {"avoided": "재벌가 파산 비극", "method": "가장 잔인한 구조조정"},
      "regression_hint": {"slip_up": "없다.", "suspicion_from": "없음"},
      "future_prep": {"action": "그룹 자금 풀 안정화", "target_event": "전통 산업을 넘어 스마트 IT 시대 장악 준비"}
    }
  },
  {
    "block_id": "Block 6",
    "title": "구시대 공룡의 목을 베다 (재계 1위 척살)",
    "content": {
      "context": "2009년 초. 20대 후반의 젊은 나이에 대기업 그룹을 장악한 한시우. 재계의 늙은 너구리들은 시우를 '졸부 핏덩이'로 취급한다. 특히 대한민국 권력 1위, 정보기술(IT) 통신망 사업 독점을 쥐고 있는 대성그룹 일가가 그렇다. 2009년은 스티브 잡스가 아이폰을 한국에 상륙시키기 직전. 피처폰의 황혼기다.",
      "event_villain": "대성그룹 부회장 최강수(60대). 그는 정부 과천청사에서 열린 차세대 통신망 입찰 참여장에서 시우와 마주친다. 그는 멸시하는 표정으로 시우의 어깨를 툭 친다. '어이 젊은 회장, 남의 형님들 피 빨아서 자리 차지하면 뼛속까지 재벌 되는 줄 아나 봐? IT와 통신은 근본 없는 투기꾼이 손댈 수준이 아니야. 집에 가서 젖이나 더 먹고 와.'",
      "solution": "시우는 중년의 능구렁이 같은 조소를 흘린다. '부회장님, 피처폰 재고창고에 벽돌 쌓아두고 제사 지내십니까?' 시우는 이미 대성그룹이 자랑하던 '국산 폐쇄형 무선 인터넷' 기술이 곧 쓰레기가 될 것임을 안다. 입찰 프리젠테이션 현장, 최강수가 고루한 피처폰 국책 사업을 나열할 때, 시우는 단상에 올라 오직 '스마트폰 생태계 개방과 무제한 데이터망' 하나만을 발표한다. 정부의 평가단은 큰 충격에 빠진다.",
      "reward": "시우의 그룹이 압도적인 기술 혁신성장 평가로 차세대 통신망 국책 사업을 강탈해온다. 대성그룹의 통신 계열사 주가는 반토막이 나고 수천억의 손실이 발생한다. 최강수 부회장은 언론의 몰매를 맞으며 사퇴한다. 시우는 재계 1위의 우상을 완벽히 파괴하며, 명실상부한 미래 권력 1인자로 추앙받는다. 늙은 꼰대의 권위를 완전히 찍어누르는 압도적 사이다."
    },
    "stakes": "대한민국 재계 1위와의 첫 전면전. 하지만 상대는 총 대신 녹슨 활(피처폰)을 들고 있다. 5060 독자들이 혐오하는 '답답한 기존 정치/경제 기득권'을 시우의 노련함으로 쓸어버리는 쾌감.",
    "power_shift": {
      "protagonist": "대한민국 재계 판도를 180도 뒤집는 '파괴적 혁신가'이자 거물.",
      "antagonist": "기존 재계 1위 대성그룹. 시우의 혁신 앞에 한낱 낡은 폐기물로 전락해 처참히 패배함."
    },
    "relationship_delta": [
      {
        "target": "최강수 부회장 (대성그룹)",
        "before": "'어린 놈의 호기기'",
        "after": "자리 보전도 못하고 쫓겨난 한 줌의 재(灰)"
      }
    ],
    "foreshadow": [
      "스마트폰 생태계 장악 이후 플랫폼 '앱(App)' 스타트업 사냥(카카오 등) 예고"
    ],
    "callback": [
      "과거 시우를 무시했던 모든 구 기득권들이 차례로 목이 잘려 나가는 전통적 복수극"
    ],
    "emotional_beat": {
      "type": "vindication",
      "intensity": 10
    },
    "tension_level": 5,
    "pov_character": "한시우",
    "location": {
      "place": "정부 과천청사 대강당 / 여의도 증권가 전광판 앞",
      "type": "실내"
    },
    "time_span": {
      "duration": "2개월",
      "in_story_time": "2009년 봄"
    },
    "genre_ext": {
      "capital_before": "그룹 장악 직후",
      "capital_after": "조 단위 통신 국책사업 수주 및 기업 가치 2배 펌핑",
      "capital_delta": "그룹 시총 급등",
      "profit_loss": "장부상 수조 단위 가치 창출",
      "method": "시대의 패러다임(스마트폰)을 인질로 잡고 국책 심사위원단 농락",
      "investment_type": "국책 사업 및 통신 인프라 알박기",
      "deal_type": "정부 입찰 경쟁 (B2G)",
      "leverage_used": ["스마트폰 혁명에 대한 광신적 믿음", "상대 그룹 부회장의 무지"],
      "opponent": {
        "name": "최강수 부회장 (재계 1위)",
        "type": "늙고 교만한 기존 권력",
        "weakness_exploited": "갈라파고스(피처폰)에 갇힌 노인네들의 현실 도피 극대화"
      },
      "historical_event": {
        "name": "2009년 아이폰 국내 출시 및 통신 패러다임 전환기",
        "year": 2009,
        "month": "봄",
        "how_exploited": "미래 기술 표준을 선점하여 경쟁사를 시대 밖으로 밀어냄"
      },
      "time_pressure": "없음. 애플의 출시 일정이 곧 시우의 칼날 타이밍.",
      "knowledge_used": "피처폰의 완전한 멸종 시나리오 암기",
      "risk_level": "외견상 고위험(국책 사업 탈락 시 타격), 사실상 초저위험",
      "business_sector": "IT 통신 및 통신망 구축"
    },
    "regression_ext": {
      "is_regressor": True,
      "regression_type": "회귀",
      "timeline_knowledge": {
        "info_used": "와이파이(Wi-Fi) 전면 개방 및 모바일 인터넷 폭발 예측",
        "accuracy": "완벽",
        "source": "5060세대가 피부로 겪었던 모바일 혁명 1세대의 기억"
      },
      "butterfly_effect": {
        "original_event": "대성그룹이 기득권 유지",
        "changed_event": "대성그룹 IT 천하의 붕괴, 한시우 천하 개막",
        "ripple_effect": "재계 1등이 처음으로 패배하며 공포심리에 휩싸임"
      },
      "death_flag": {"avoided": None, "method": None},
      "regression_hint": {"slip_up": "전혀 없음. 혁신적 천재 CEO.", "suspicion_from": "없음"},
      "future_prep": {"action": "다음 단계 '카카오톡' 등 초기 모바일 메신저 기업 M&A 준비", "target_event": "모바일 플랫폼 독점 시대 발발"}
    }
  }
]

data[3:6] = v3_blocks_4_to_6

with open(_OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
