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

from typing import Callable, Dict, List, Tuple, Optional
from .pattern_tracker import PatternTracker
from .diversity_sampler import DiversitySampler, ConditionalDiversitySampler


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
        'wuxia': """
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

        'hunter': """
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

        'investment': """
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
"""
    }

    def __init__(self, context, genre: str = 'wuxia', window_size: int = 10):
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

    def analyze_recent_episodes(self, n_episodes: int = None) -> Dict:
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
            latest_ep = self.context.db.get_latest_episode_number()
            start_ep = max(1, latest_ep - n + 1)

            for ep_num in range(start_ep, latest_ep + 1):
                # 원고 로드
                ms_data = self.context.db.get_manuscript(ep_num)
                if ms_data:
                    content = ms_data.get('content', '') if isinstance(ms_data, dict) else str(ms_data)
                    if content:
                        manuscripts.append(content)

                # 블루프린트 로드
                bp_data = self.context.db.get_blueprint(ep_num)
                if bp_data:
                    blueprints.append(bp_data)

        except Exception as e:
            print(f"      [NarrativeDiversity] 에피소드 로드 실패: {e}")

        self._recent_manuscripts = manuscripts

        # 패턴 분석 실행
        self._analysis_report = self.pattern_tracker.analyze_manuscripts(
            manuscripts=manuscripts,
            blueprints=blueprints
        )

        # Diversity Sampler 초기화 (최근 원고를 참조 텍스트로)
        self.diversity_sampler = DiversitySampler(reference_texts=manuscripts)
        self.conditional_sampler = ConditionalDiversitySampler(
            pattern_tracker=self.pattern_tracker,
            reference_texts=manuscripts
        )

        print(f"      [NarrativeDiversity] {len(manuscripts)}화 분석 완료")
        if self._analysis_report:
            high_count = self._analysis_report.get('high_severity_count', 0)
            if high_count > 0:
                print(f"      [NarrativeDiversity] HIGH 경고 {high_count}개 감지!")

        return self._analysis_report

    def generate_diverse_blueprint(
        self,
        generator_fn: Callable[[], dict],
        n_samples: int = 3
    ) -> Tuple[dict, Dict]:
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
            print("      [NarrativeDiversity] 분석 미완료 - 단일 블루프린트 생성")
            return generator_fn(), {'mode': 'single', 'reason': 'no_analysis'}

        return self.diversity_sampler.sample_blueprints(generator_fn, n_samples)

    def generate_diverse_manuscript(
        self,
        generator_fn: Callable[[], str],
        n_samples: int = 3,
        force: bool = False
    ) -> Tuple[str, Dict]:
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
            print("      [NarrativeDiversity] 분석 미완료 - 단일 원고 생성")
            return generator_fn(), {'mode': 'single', 'reason': 'no_analysis'}

        return self.conditional_sampler.sample_or_single(generator_fn, n_samples, force)

    def should_use_diversity_sampling_for_writer(self) -> Tuple[bool, str]:
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
        contrastive = self.CONTRASTIVE_EXAMPLES.get(self.genre, self.CONTRASTIVE_EXAMPLES['wuxia'])
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
            warnings = self._analysis_report.get('warnings', [])
            plot_warnings = [w for w in warnings if w.get('type') == 'PLOT_REPEAT']
            if plot_warnings:
                injection += "\n[경고: 플롯 패턴 반복 감지]\n"
                for w in plot_warnings[:2]:
                    injection += f"- {w['message']}\n"

        return injection

    def get_analysis_summary(self) -> Dict:
        """분석 결과 요약 반환"""
        if self._analysis_report is None:
            return {'status': 'not_analyzed'}

        return {
            'status': 'analyzed',
            'window_size': self.window_size,
            'high_severity_warnings': self._analysis_report.get('high_severity_count', 0),
            'diversity_sampling_recommended': self.should_use_diversity_sampling_for_writer()[0],
            'top_issues': [
                w['message'] for w in self._analysis_report.get('warnings', [])[:3]
            ]
        }

    def save_state(self) -> bool:
        """상태를 DB에 저장"""
        return self.pattern_tracker.save_to_db(self.context.db)

    def load_state(self) -> bool:
        """DB에서 상태 로드"""
        return self.pattern_tracker.load_from_db(self.context.db)
