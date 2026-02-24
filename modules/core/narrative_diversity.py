"""
[V48 Premium] 서사 다양성 통합 모듈

Pattern Tracking + Diversity Sampling + Contrastive CoT 통합 관리

사용법:
    from modules.core.narrative_diversity import NarrativeDiversityEngine

    engine = NarrativeDiversityEngine(context, genre='wuxia')
    engine.analyze_recent_episodes(10)  # 최근 10화 분석

    # Architect용 (Stage 3)
    blueprint, meta = engine.generate_diverse_blueprint(architect_fn)

    # Writer용 (Stage 4, 조건부)
    manuscript, meta = engine.generate_diverse_manuscript(writer_fn)

    # 프롬프트 주입
    injection = engine.get_writer_injection()
"""

import logging
from collections.abc import Callable

from .diversity_sampler import ConditionalDiversitySampler, DiversitySampler
from .pattern_tracker import PatternTracker


class NarrativeDiversityEngine:
    """
    서사 다양성 통합 엔진

    기능:
    1. Pattern Tracking: 반복 패턴 감지 및 경고
    2. Diversity Sampling: 다양한 후보 생성 및 선택
    3. Contrastive CoT: 네거티브 예시 기반 프롬프트 강화
    """

    # Contrastive CoT 네거티브 예시
    CONTRASTIVE_EXAMPLES = {
        "wuxia": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 전투 묘사 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공은 검을 휘둘렀다. 적은 피를 뿜으며 쓰러졌다.
주인공은 다음 적에게 검을 휘둘렀다. 그 적도 쓰러졌다.
순식간에 모든 적이 쓰러졌다."

→ 문제점:
  - 동작 반복 (검을 휘둘렀다 x3)
  - 결과 반복 (쓰러졌다 x3)
  - 긴장감 없음

✅ 올바른 예시:
"검이 허공을 갈랐다. 첫 번째 적의 목이 꺾이기도 전에,
검끝은 이미 두 번째 적의 명치를 관통하고 있었다.
피가 공중에 흩뿌려질 찰나, 세 번째 검격이 마지막 적의
비명마저 삼켜버렸다."

→ 해결: 동작 연결, 시간 압축, 오감 묘사

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 캐릭터 반응 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"장로는 눈을 크게 떴다. 경악했다.
'이, 이런...!' 장로가 말했다.
그는 믿을 수 없다는 표정을 지었다."

→ 문제점:
  - 감정 직접 서술 (경악했다)
  - 진부한 대사 ('이, 이런')
  - 동일한 감정을 3번 반복

✅ 올바른 예시:
"장로의 손에서 찻잔이 미끄러졌다. 바닥에 부딪히는
소리조차 귓전을 스쳐 지나갔다. 그의 입술이
달싹거렸지만, 목구멍은 단단히 굳어 있었다."

→ 해결: 행동으로 감정 표현, 신체 반응 묘사

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 3: 플롯 전개 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시 (매화 반복):
"적이 도발했다 → 주인공이 화났다 → 전투 → 승리 → 경악"

→ 문제점:
  - 도발→전투→승리 패턴이 5화 연속
  - 예측 가능한 전개
  - 독자 피로

✅ 다양한 전개 예시:
A: 도발 → 무시 → 적의 자충수 → 주인공 이득
B: 협력 제안 → 의심 → 조건부 동맹 → 예상치 못한 배신
C: 정보 수집 → 함정 발견 → 역이용 → 적 자멸
D: 오해 → 갈등 → 진실 발견 → 관계 심화

→ 해결: 패턴 변주, 예측 불가능성, 캐릭터 심리

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[핵심 원칙]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 같은 단어를 연속 3문장 내에 반복하지 마라
2. 감정을 직접 서술하지 말고 행동/신체로 보여줘라
3. 최근 5화에서 사용한 플롯 패턴을 반복하지 마라
4. 문장 시작을 '그는/그녀는'으로 25% 이상 쓰지 마라
""",
        "hunter": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 시스템 메시지 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"[레벨업!] 레벨이 올랐습니다.
[스킬 획득!] 새로운 스킬을 얻었습니다.
[스탯 상승!] 힘이 10 올랐습니다."

→ 문제점:
  - 시스템 메시지 나열
  - 감정 없음
  - 게임 로그처럼 읽힘

✅ 올바른 예시:
"뼈가 부러질 것 같은 통증이 전신을 관통했다.
하지만 그 고통의 끝에서, 무언가가 열렸다.
손끝에서 시작된 전율이 심장을 거쳐 뇌까지
스며들었다. 세상이 달라 보였다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 던전 공략 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"몬스터가 나타났다. 주인공이 스킬을 썼다. 몬스터가 죽었다.
다음 몬스터가 나타났다. 또 스킬을 썼다. 또 죽었다."

✅ 올바른 예시:
전투의 리듬, 위기의 순간, 성장의 의미를 담아라.
""",
        "investment": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 주식 거래 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주가가 올랐다. 주인공은 기뻤다.
'역시 내 예상대로야.' 주인공이 미소를 지었다.
주가가 더 올랐다. 더 기뻤다."

✅ 올바른 예시:
내면의 갈등, 불확실성, 승리의 복잡한 감정을 담아라.
""",
        "fantasy": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 마법 사용 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 마법을 썼다. 적이 날아갔다.
다시 마법을 썼다. 이번에도 이겼다."

→ 문제점:
  - 마법 시스템 규칙 부재
  - 대가/제약 없는 만능 능력
  - 전투 리듬 단조

✅ 올바른 예시:
"룬이 빛나자 손목의 문양이 검게 타들어갔다.
세 번째 주문을 억지로 이어 붙이는 순간,
가슴 안쪽에서 마나가 끊어지는 통증이 번졌다.
그래도 그는 마지막 한 음절을 밀어 넣었다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 세계관 설명 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"이 세계는 오래전에 망했고, 왕국은 셋이며,
정령은 다섯 속성이고, 마탑은 일곱 층이다."

✅ 올바른 예시:
설정 나열 대신 장면 속 충돌로 세계관을 드러내라.
규칙과 대가를 사건으로 증명하고, 인물의 선택과 연결해라.
""",
        "composer": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 작곡 장면 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 곡을 썼다. 모두 감동했다.
천재라는 소문이 났다."

→ 문제점:
  - 창작 과정 생략
  - 감동의 근거 부재
  - 청각 묘사 실종

✅ 올바른 예시:
"새벽 네 시, 메트로놈의 딱딱한 박자가 방 안을 쪼갰다.
그는 3도 진행을 지우고, 현 파트를 한 옥타브 낮췄다.
클라이맥스 직전 베이스가 비워지자,
멜로디 한 줄이 심장처럼 튀어 올랐다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 공연 반응 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"연주가 끝났다. 관객이 박수쳤다."

✅ 올바른 예시:
반응은 숫자 대신 현장 감각으로 보여줘라.
첫 박수의 지연, 객석의 숨 멈춤, 앵콜 직전의 정적을 써라.
""",
        "cooking": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 요리 묘사 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 요리를 만들었다. 손님이 맛있다고 했다.
다음 요리를 만들었다. 또 맛있다고 했다.
모든 요리가 성공했다."

→ 문제점:
  - 과정 생략 (만들었다 반복)
  - 반응 단조 (맛있다 반복)
  - 오감 묘사 부재

✅ 올바른 예시:
"칼끝이 도마 위에서 리듬을 타기 시작했다.
양파의 투명한 단면에서 올라오는 매운 향이 눈시울을 적셨고,
뜨거운 팬 위에 올려진 순간 지글거리는 소리와 함께
캐러멜색으로 변해가는 양파의 달콤한 향이 주방을 채웠다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 식당 경영 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"매출이 올랐다. 주인공은 기뻤다."

✅ 올바른 예시:
요리의 완성과 고객 반응, 경영의 고뇌와 성취를 감각적으로 담아라.
맛을 직접 서술하지 말고 먹는 사람의 표정, 행동, 비유로 보여줘라.
""",
        "alt_history": """
[V48 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 조정 장면 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 조정에서 발언했다. 왕이 허락했다.
반대파가 반대했다. 주인공이 이겼다."

→ 문제점:
  - 정치적 논리와 명분 부재
  - 유교적 예법과 격식 무시
  - 당쟁의 복잡한 역학 관계 단순화

✅ 올바른 예시:
"'전하, 신이 감히 아뢰옵니다.'
옥좌 앞에 엎드린 그의 목소리가 근정전을 울렸다.
좌의정이 미간을 좁혔고, 노론 대신들 사이로
보이지 않는 시선의 그물이 오갔다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 기술 도입 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 현대 기술을 설명했다. 모두가 놀랐다. 바로 도입했다."

✅ 올바른 예시:
현대 지식의 도입은 반드시 시대적 저항과 점진적 설득 과정을 거쳐야 한다.
유교적 보수 세력의 반발, 장인들의 기술적 한계, 재원 확보의 어려움을 그려라.
""",
        "actor": """
[V62 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 오디션/촬영 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 연기했다. 감독이 감동했다.
'컷! 완벽해!' 감독이 말했다.
모두가 박수를 쳤다."

→ 문제점:
  - 연기 과정 생략 (연기했다 한 줄)
  - 반응 진부 (감동+박수)
  - 이중 레이어 부재 (배우의 감정 vs 역할의 감정)

✅ 올바른 예시:
"카메라 빨간불이 켜진 순간, 그의 눈동자가 변했다.
아버지를 잃은 아들의 분노가 아니라, 그 분노를
삼키고 미소 짓는 법을 배운 남자의 떨림이
턱선을 타고 흘러내렸다. 모니터 뒤에서
감독의 손이 멈췄다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 업계 반응 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"시청률이 올랐다. 주인공은 기뻤다."

✅ 올바른 예시:
연기의 결과는 숫자가 아닌 관객과 업계의 반응으로 보여줘라.
댓글의 온도, 업계 관계자의 전화, 거리에서 알아보는 시선의 변화로 표현하라.
""",
        "sports": """
[V62.1 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 경기 묘사 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"주인공이 골을 넣었다. 팀원들이 기뻐했다.
관중들이 환호했다. 주인공은 뿌듯했다."

→ 문제점:
  - 경기 과정 생략 (골을 넣었다 한 줄)
  - 신체 감각 부재 (속도감/호흡/근육)
  - 전술적 맥락 없음 (어떤 작전, 어떤 기회)

✅ 올바른 예시:
"미드필더의 롱패스가 수비 라인 뒤로 뜨는 순간,
그의 종아리 근육이 폭발했다. 수비수의 어깨가
시야 가장자리를 스쳐 지나가고, 잔디를 차는
오른발 안쪽에 공이 빨려들었다.
골 네트가 출렁이기 전에, 그는 이미
관중석의 포효를 뼛속으로 느꼈다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 훈련/성장 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"열심히 훈련해서 실력이 늘었다."

✅ 올바른 예시:
훈련은 구체적 과정으로, 성장은 경기 중 발현으로 보여줘라.
새벽 러닝의 폐 타는 감각, 반복 드릴의 근육 기억, 영상 분석의 눈 뜨임으로 묘사하라.
""",
        "medical": """
[V62.1 CONTRASTIVE CoT: 이렇게 쓰지 마라]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 1: 수술 묘사 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"수술이 시작됐다. 주인공은 능숙하게 메스를 움직였다.
수술은 성공이었다. 환자 가족이 감사했다."

→ 문제점:
  - 수술 과정 생략 (능숙하게 한 줄)
  - 의학적 디테일 부재 (바이탈/출혈/시간)
  - 긴장감 없는 결과 보고

✅ 올바른 예시:
"메스가 피부를 가르자 혈관이 드러났다.
'BP 90/60, 떨어지고 있어요.' 간호사의 목소리가
수술실 공기를 가를 때, 그의 손가락은 이미
출혈점을 향해 움직이고 있었다. 모니터의
심박수가 한 박자 늦게 반응했다.
0.3초의 판단이 생사를 갈랐다."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[예시 2: 진단/성장 - 틀린 방식]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 잘못된 예시:
"환자를 진찰해서 병을 찾아냈다."

✅ 올바른 예시:
진단은 추리 과정으로, 성장은 임상 판단의 변화로 보여줘라.
검사 결과의 모순, 교과서에 없는 증상 조합, 선배의 한마디에서 번뜩이는 통찰로 묘사하라.
""",
    }

    def __init__(self, context, genre: str = "wuxia", window_size: int = 10):
        """
        Args:
            context: ProjectContext 인스턴스
            genre: 장르 (wuxia/hunter/investment)
            window_size: 패턴 분석 윈도우 크기
        """
        self.context = context
        self.genre = genre
        self.window_size = window_size

        # 서브 모듈 초기화
        self.pattern_tracker = PatternTracker(window_size=window_size, genre=genre)
        self.diversity_sampler = None  # analyze 후 초기화
        self.conditional_sampler = None

        # 분석 결과 캐시
        self._analysis_report = None
        self._recent_manuscripts = []

    def analyze_recent_episodes(self, n_episodes: int = None) -> dict:
        """
        최근 에피소드 분석 및 패턴 추적

        Args:
            n_episodes: 분석할 에피소드 수 (기본: window_size)

        Returns:
            분석 리포트
        """
        n = n_episodes or self.window_size

        # DB에서 최근 원고 로드
        manuscripts = []
        blueprints = []

        try:
            latest_ep = self.context.db.get_latest_episode_number() - 1
            start_ep = max(1, latest_ep - n + 1)

            for ep_num in range(start_ep, latest_ep + 1):
                # 원고 로드
                ms_data = self.context.db.get_manuscript(ep_num)
                if ms_data:
                    content = ms_data.get("content", "") if isinstance(ms_data, dict) else str(ms_data)
                    if content:
                        manuscripts.append(content)

                # 블루프린트 로드
                bp_data = self.context.db.get_blueprint(ep_num)
                if bp_data:
                    blueprints.append(bp_data)

        except Exception as e:
            logging.warning(f"[NarrativeDiversity] 에피소드 로드 실패: {e}")

        self._recent_manuscripts = manuscripts

        # 패턴 분석 실행
        self._analysis_report = self.pattern_tracker.analyze_manuscripts(manuscripts=manuscripts, blueprints=blueprints)

        # Diversity Sampler 초기화 (최근 원고를 참조 텍스트로)
        self.diversity_sampler = DiversitySampler(reference_texts=manuscripts)
        self.conditional_sampler = ConditionalDiversitySampler(
            pattern_tracker=self.pattern_tracker, reference_texts=manuscripts
        )

        logging.info(f"[NarrativeDiversity] {len(manuscripts)}화 분석 완료")
        if self._analysis_report:
            high_count = self._analysis_report.get("high_severity_count", 0)
            if high_count > 0:
                logging.info(f"[NarrativeDiversity] HIGH 경고 {high_count}개 감지!")

        return self._analysis_report

    def generate_diverse_blueprint(self, generator_fn: Callable[[], dict], n_samples: int = 3) -> tuple[dict, dict]:
        """
        Stage 3 (Architect): 항상 Diversity Sampling 적용

        Args:
            generator_fn: 블루프린트 생성 함수
            n_samples: 샘플 수

        Returns:
            (선택된 블루프린트, 메타데이터)
        """
        if self.diversity_sampler is None:
            # 분석 안 됐으면 단일 생성
            logging.info("[NarrativeDiversity] 분석 미완료 - 단일 블루프린트 생성")
            return generator_fn(), {"mode": "single", "reason": "no_analysis"}

        return self.diversity_sampler.sample_blueprints(generator_fn, n_samples)

    def generate_diverse_manuscript(
        self, generator_fn: Callable[[], str], n_samples: int = 3, force: bool = False
    ) -> tuple[str, dict]:
        """
        Stage 4 (Writer): 조건부 Diversity Sampling 적용

        Args:
            generator_fn: 원고 생성 함수
            n_samples: 샘플 수
            force: 강제 활성화

        Returns:
            (선택된 원고, 메타데이터)
        """
        if self.conditional_sampler is None:
            # 분석 안 됐으면 단일 생성
            logging.info("[NarrativeDiversity] 분석 미완료 - 단일 원고 생성")
            return generator_fn(), {"mode": "single", "reason": "no_analysis"}

        return self.conditional_sampler.sample_or_single(generator_fn, n_samples, force)

    def should_use_diversity_sampling_for_writer(self) -> tuple[bool, str]:
        """
        Writer에서 Diversity Sampling을 사용해야 하는지 판단

        Returns:
            (사용 여부, 이유)
        """
        if self._analysis_report is None:
            return False, "분석 미완료"

        return self.pattern_tracker.should_activate_diversity_sampling(self._analysis_report)

    def get_writer_injection(self) -> str:
        """
        Writer 프롬프트에 주입할 패턴 경고 문구

        Returns:
            프롬프트 주입 문자열
        """
        injection = ""

        # 1. Pattern Tracker 경고
        if self._analysis_report:
            pattern_injection = self.pattern_tracker.generate_writer_injection(self._analysis_report)
            if pattern_injection:
                injection += pattern_injection + "\n\n"

        # 2. Contrastive CoT 예시
        contrastive = self.CONTRASTIVE_EXAMPLES.get(self.genre, self.CONTRASTIVE_EXAMPLES["wuxia"])
        injection += contrastive

        return injection

    def get_architect_injection(self) -> str:
        """
        Architect 프롬프트에 주입할 구조적 다양성 지침

        Returns:
            프롬프트 주입 문자열
        """
        injection = """
[V48 STRUCTURAL DIVERSITY DIRECTIVE]

최근 에피소드 분석 결과를 바탕으로 구조적 다양성을 확보하라.

[씬 타입 균형]
- Core 씬: 30-50% (핵심 갈등/액션)
- Buffer 씬: 30-50% (분위기/관계/맥락)
- Cliffhanger: 1개 (마지막 씬)

[플롯 다양화 지침]
- 최근 5화에서 사용한 플롯 패턴을 반복하지 마라
- 도발→전투→승리 패턴이 2회 연속이면 다른 전개 사용
- 가능한 전개: 협상, 정보전, 함정, 오해, 회피, 역이용

[감정 곡선 다양화]
- 매화 동일한 감정 곡선 금지
- 기→승→전→결 외에도:
  - 전→결→기→승 (역전 구조)
  - 결→기→승→전 (회상 구조)
  - 승→전→결→기 (여운 구조)
"""

        # 패턴 분석 결과가 있으면 추가
        if self._analysis_report:
            warnings = self._analysis_report.get("warnings", [])
            plot_warnings = [w for w in warnings if w.get("type") == "PLOT_REPEAT"]
            if plot_warnings:
                injection += "\n[경고: 플롯 패턴 반복 감지]\n"
                for w in plot_warnings[:2]:
                    injection += f"- {w['message']}\n"

        return injection

    def get_analysis_summary(self) -> dict:
        """분석 결과 요약 반환"""
        if self._analysis_report is None:
            return {"status": "not_analyzed"}

        return {
            "status": "analyzed",
            "window_size": self.window_size,
            "high_severity_warnings": self._analysis_report.get("high_severity_count", 0),
            "diversity_sampling_recommended": self.should_use_diversity_sampling_for_writer()[0],
            "top_issues": [w["message"] for w in self._analysis_report.get("warnings", [])[:3]],
        }

    def save_state(self) -> bool:
        """상태를 DB에 저장"""
        return self.pattern_tracker.save_to_db(self.context.db)

    def load_state(self) -> bool:
        """DB에서 상태 로드"""
        return self.pattern_tracker.load_from_db(self.context.db)
