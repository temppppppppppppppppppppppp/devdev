"""
[V48 Premium] 서사 관성 극복을 위한 고급 패턴 추적 시스템

기존 RepetitionGuard(3-gram)를 확장하여:
1. 플롯 패턴 추적 (도발→전투→승리 등)
2. 씬 타입 분포 추적 (Core/Buffer 비율)
3. 클리셰 키워드 빈도 추적
4. 문장 구조 패턴 추적 (시작어, 종결어)
5. 캐릭터 반응 패턴 추적
"""

import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional


class PatternTracker:
    """
    서사 관성 극복을 위한 다층 패턴 추적 시스템

    Attributes:
        window_size: 분석할 이전 에피소드 수 (기본 10화)
        thresholds: 각 패턴 유형별 경고 임계값
    """

    # 무협 클리셰 키워드 (장르별 확장 가능)
    CLICHE_KEYWORDS = {
        'wuxia': [
            '살기', '기세', '경악', '전율', '경지', '내공', '진기',
            '눈빛이 빛났다', '입꼬리가 올라갔다', '차가운 미소',
            '순식간에', '찰나', '일순', '눈 깜짝할 사이',
            '감히', '어찌', '놀랍게도', '예상대로',
            '피가 솟구쳤다', '뼈가 으스러졌다', '고통에 몸부림쳤다'
        ],
        'hunter': [
            '각성', '스킬', '마나', '던전', '게이트', '몬스터',
            '레벨업', '스테이터스', '버프', '디버프',
            '눈앞이 하얘졌다', '메시지가 떴다', '시스템 알림'
        ],
        'investment': [
            '주가', '폭등', '폭락', '매수', '매도', '차트',
            '눈이 번쩍', '미소를 지었다', '심장이 뛰었다',
            '예상대로', '역시나', '드디어'
        ]
    }

    # 플롯 패턴 시퀀스 (감지 대상)
    PLOT_PATTERNS = [
        ('도발', '전투', '승리'),      # 가장 흔한 패턴
        ('위기', '각성', '역전'),      # 회귀물 패턴
        ('모욕', '복수', '통쾌'),      # 복수물 패턴
        ('수련', '돌파', '인정'),      # 성장물 패턴
        ('은혜', '보답', '동맹'),      # 관계물 패턴
        ('발견', '획득', '성장'),      # 파밍물 패턴
    ]

    # 문장 시작 패턴 (과다 사용 감지)
    SENTENCE_STARTERS = [
        '그는', '그녀는', '주인공은', '나는',
        '하지만', '그러나', '그리고', '그래서',
        '순간', '그때', '바로', '이윽고',
    ]

    def __init__(self, window_size: int = 10, genre: str = 'wuxia'):
        """
        Args:
            window_size: 분석할 이전 에피소드 수
            genre: 장르 (wuxia/hunter/investment)
        """
        self.window_size = window_size
        self.genre = genre
        self.cliche_keywords = self.CLICHE_KEYWORDS.get(genre, self.CLICHE_KEYWORDS['wuxia'])

        # 패턴 저장소
        self.pattern_history = {
            'plot_sequences': [],      # 플롯 패턴 시퀀스
            'scene_types': {'Core': 0, 'Buffer': 0, 'Cliffhanger': 0, 'Unknown': 0},  # 씬 타입 분포 (dict)
            'cliche_counts': Counter(),# 클리셰 사용 빈도
            'starter_counts': Counter(),# 문장 시작어 빈도
            'reaction_patterns': {},   # 캐릭터 반응 패턴 (dict)
        }

        # 임계값 설정
        self.thresholds = {
            'plot_repeat': 2,          # 동일 플롯 패턴 2회 이상 = 경고
            'cliche_ratio': 0.15,      # 클리셰 비율 15% 이상 = 경고
            'starter_dominance': 0.25, # 특정 시작어 25% 이상 = 경고
            'core_imbalance': 0.7,     # Core 씬 70% 이상 = 경고
        }

    def analyze_manuscripts(self, manuscripts: List[str], blueprints: List[dict] = None) -> Dict:
        """
        여러 원고를 분석하여 패턴 히스토리 구축

        Args:
            manuscripts: 원고 텍스트 리스트 (최근 N화)
            blueprints: 블루프린트 리스트 (씬 타입 분석용)

        Returns:
            분석 결과 딕셔너리
        """
        if not manuscripts:
            return {'status': 'no_data', 'warnings': []}

        # 최근 window_size 화만 분석
        recent_ms = manuscripts[-self.window_size:]
        recent_bp = blueprints[-self.window_size:] if blueprints else []

        # 1. 클리셰 빈도 분석
        self._analyze_cliches(recent_ms)

        # 2. 문장 시작어 분석
        self._analyze_sentence_starters(recent_ms)

        # 3. 플롯 패턴 분석 (LLM 없이 키워드 기반)
        self._analyze_plot_patterns(recent_ms)

        # 4. 씬 타입 분포 분석 (블루프린트 기반)
        if recent_bp:
            self._analyze_scene_types(recent_bp)

        # 5. 캐릭터 반응 패턴 분석
        self._analyze_reaction_patterns(recent_ms)

        return self._generate_analysis_report()

    def _analyze_cliches(self, manuscripts: List[str]):
        """클리셰 키워드 빈도 분석"""
        combined = '\n'.join(manuscripts)
        total_chars = len(combined)

        if total_chars == 0:
            return

        for keyword in self.cliche_keywords:
            count = combined.count(keyword)
            if count > 0:
                self.pattern_history['cliche_counts'][keyword] = count

    def _analyze_sentence_starters(self, manuscripts: List[str]):
        """문장 시작어 패턴 분석"""
        combined = '\n'.join(manuscripts)

        # 문장 분리 (. ! ? 기준)
        sentences = re.split(r'[.!?]\s*', combined)
        total_sentences = len([s for s in sentences if s.strip()])

        if total_sentences == 0:
            return

        for starter in self.SENTENCE_STARTERS:
            count = sum(1 for s in sentences if s.strip().startswith(starter))
            if count > 0:
                self.pattern_history['starter_counts'][starter] = count

    def _analyze_plot_patterns(self, manuscripts: List[str]):
        """플롯 패턴 시퀀스 감지 (키워드 기반)"""
        detected_patterns = []

        for i, ms in enumerate(manuscripts):
            for pattern in self.PLOT_PATTERNS:
                # 패턴의 모든 키워드가 순서대로 등장하는지 확인
                positions = []
                for keyword in pattern:
                    pos = ms.find(keyword)
                    if pos == -1:
                        break
                    positions.append(pos)

                # 모든 키워드가 순서대로 존재
                if len(positions) == len(pattern) and positions == sorted(positions):
                    detected_patterns.append({
                        'episode_index': i,
                        'pattern': pattern,
                        'pattern_name': '→'.join(pattern)
                    })

        self.pattern_history['plot_sequences'] = detected_patterns

    def _analyze_scene_types(self, blueprints: List[dict]):
        """씬 타입 분포 분석"""
        scene_types = {'Core': 0, 'Buffer': 0, 'Cliffhanger': 0, 'Unknown': 0}

        for bp in blueprints:
            scene_breakdown = bp.get('scene_breakdown', {})
            if isinstance(scene_breakdown, dict):
                for scene_key, scene_content in scene_breakdown.items():
                    if isinstance(scene_content, str):
                        if '[Core]' in scene_content:
                            scene_types['Core'] += 1
                        elif '[Buffer]' in scene_content:
                            scene_types['Buffer'] += 1
                        elif '[Cliffhanger]' in scene_content:
                            scene_types['Cliffhanger'] += 1
                        else:
                            scene_types['Unknown'] += 1

        self.pattern_history['scene_types'] = scene_types

    def _analyze_reaction_patterns(self, manuscripts: List[str]):
        """캐릭터 반응 패턴 분석"""
        reaction_keywords = [
            '눈을 가늘게 떴다', '미간을 찌푸렸다', '고개를 끄덕였다',
            '한숨을 내쉬었다', '이를 악물었다', '주먹을 불끈 쥐었다',
            '눈빛이 차가워졌다', '입꼬리가 올라갔다', '표정이 굳었다',
        ]

        combined = '\n'.join(manuscripts)
        reaction_counts = Counter()

        for reaction in reaction_keywords:
            count = combined.count(reaction)
            if count >= 2:  # 최소 2회 이상 사용된 것만
                reaction_counts[reaction] = count

        self.pattern_history['reaction_patterns'] = dict(reaction_counts.most_common(10))

    def _generate_analysis_report(self) -> Dict:
        """분석 결과 리포트 생성"""
        warnings = []

        # 1. 클리셰 과다 사용 체크
        total_cliche = sum(self.pattern_history['cliche_counts'].values())
        top_cliches = self.pattern_history['cliche_counts'].most_common(5)
        if top_cliches:
            most_used = top_cliches[0]
            if most_used[1] >= self.window_size * 3:  # 화당 3회 이상
                warnings.append({
                    'type': 'CLICHE_OVERUSE',
                    'severity': 'HIGH',
                    'message': f"'{most_used[0]}' 표현 과다 사용 ({most_used[1]}회/{self.window_size}화)",
                    'suggestion': f"대체 표현 사용 권장"
                })

        # 2. 문장 시작어 편중 체크
        total_starters = sum(self.pattern_history['starter_counts'].values())
        if total_starters > 0:
            top_starter = self.pattern_history['starter_counts'].most_common(1)
            if top_starter:
                ratio = top_starter[0][1] / total_starters
                if ratio >= self.thresholds['starter_dominance']:
                    warnings.append({
                        'type': 'STARTER_DOMINANCE',
                        'severity': 'MEDIUM',
                        'message': f"'{top_starter[0][0]}'로 시작하는 문장 비율 과다 ({ratio:.1%})",
                        'suggestion': "다양한 문장 시작 패턴 사용"
                    })

        # 3. 플롯 패턴 반복 체크
        plot_counter = Counter(p['pattern_name'] for p in self.pattern_history['plot_sequences'])
        for pattern_name, count in plot_counter.items():
            if count >= self.thresholds['plot_repeat']:
                warnings.append({
                    'type': 'PLOT_REPEAT',
                    'severity': 'HIGH',
                    'message': f"'{pattern_name}' 플롯 패턴 {count}회 반복",
                    'suggestion': "다른 전개 방식 시도 필요"
                })

        # 4. 씬 타입 불균형 체크
        scene_types = self.pattern_history['scene_types']
        total_scenes = sum(scene_types.values())
        if total_scenes > 0:
            core_ratio = scene_types.get('Core', 0) / total_scenes
            if core_ratio >= self.thresholds['core_imbalance']:
                warnings.append({
                    'type': 'CORE_IMBALANCE',
                    'severity': 'MEDIUM',
                    'message': f"Core 씬 비율 과다 ({core_ratio:.1%})",
                    'suggestion': "Buffer 씬 추가로 완급 조절"
                })

        # 5. 캐릭터 반응 패턴 반복 체크
        reaction_patterns = self.pattern_history['reaction_patterns']
        for reaction, count in reaction_patterns.items():
            if count >= self.window_size:  # 화당 1회 이상
                warnings.append({
                    'type': 'REACTION_REPEAT',
                    'severity': 'LOW',
                    'message': f"'{reaction}' 반응 과다 사용 ({count}회)",
                    'suggestion': "다양한 신체 반응 묘사 사용"
                })

        return {
            'status': 'analyzed',
            'window_size': self.window_size,
            'warnings': warnings,
            'high_severity_count': sum(1 for w in warnings if w['severity'] == 'HIGH'),
            'statistics': {
                'total_cliches': total_cliche,
                'top_cliches': top_cliches[:5],
                'plot_patterns_detected': len(self.pattern_history['plot_sequences']),
                'scene_distribution': scene_types,
                'top_reactions': list(reaction_patterns.items())[:5]
            }
        }

    def should_activate_diversity_sampling(self, report: Dict = None) -> Tuple[bool, str]:
        """
        Diversity Sampling 활성화 여부 판단

        Returns:
            (활성화 여부, 이유)
        """
        if report is None:
            report = self._generate_analysis_report()

        high_count = report.get('high_severity_count', 0)

        if high_count >= 2:
            return True, f"HIGH 심각도 경고 {high_count}개 감지 - Diversity Sampling 필수"
        elif high_count == 1:
            return True, f"HIGH 심각도 경고 감지 - Diversity Sampling 권장"
        else:
            return False, "패턴 반복 수준 양호 - 기본 생성 유지"

    def generate_writer_injection(self, report: Dict = None) -> str:
        """
        Writer 프롬프트에 주입할 경고 문구 생성

        Returns:
            프롬프트 주입 문자열
        """
        if report is None:
            report = self._generate_analysis_report()

        warnings = report.get('warnings', [])
        if not warnings:
            return ""

        # 심각도별 분류
        high_warnings = [w for w in warnings if w['severity'] == 'HIGH']
        medium_warnings = [w for w in warnings if w['severity'] == 'MEDIUM']

        injection = """
[V48 PATTERN TRACKER: 서사 관성 경고]
최근 {window}화 분석 결과, 아래 패턴 반복이 감지되었습니다.
이번 원고에서는 반드시 다른 방식을 사용하십시오.

""".format(window=self.window_size)

        if high_warnings:
            injection += "[HIGH 심각도 - 반드시 회피]\n"
            for w in high_warnings[:3]:
                injection += f"- {w['message']}\n  → {w['suggestion']}\n"
            injection += "\n"

        if medium_warnings:
            injection += "[MEDIUM 심각도 - 권장 회피]\n"
            for w in medium_warnings[:3]:
                injection += f"- {w['message']}\n  → {w['suggestion']}\n"

        # 구체적 대체 표현 제안
        top_cliches = report.get('statistics', {}).get('top_cliches', [])
        if top_cliches:
            injection += "\n[과다 사용 표현 대체 제안]\n"
            alternatives = self._suggest_alternatives(top_cliches[:3])
            for original, alts in alternatives.items():
                injection += f"- '{original}' 대신 → {', '.join(alts)}\n"

        return injection

    def _suggest_alternatives(self, top_cliches: List[Tuple[str, int]]) -> Dict[str, List[str]]:
        """클리셰 표현 대체안 제안"""
        alternatives_db = {
            '살기': ['적의', '해의', '흉한 기운', '음습한 기세'],
            '기세': ['위압감', '분위기', '존재감', '압도적 느낌'],
            '경악': ['놀람', '당혹', '충격', '어안이 벙벙'],
            '순식간에': ['눈 깜짝할 새', '찰나에', '일순간', '전광석화처럼'],
            '눈빛이 빛났다': ['눈동자가 반짝였다', '시선이 예리해졌다', '눈가에 힘이 들어갔다'],
            '입꼬리가 올라갔다': ['미소를 머금었다', '씩 웃었다', '희미한 미소가 번졌다'],
            '차가운 미소': ['냉소', '비웃음', '서늘한 웃음', '냉담한 표정'],
            '고개를 끄덕였다': ['수긍했다', '동의를 표했다', '묵묵히 인정했다'],
            '이를 악물었다': ['치아를 꽉 깨물었다', '분을 삼켰다', '울분을 참았다'],
        }

        result = {}
        for cliche, count in top_cliches:
            if cliche in alternatives_db:
                result[cliche] = alternatives_db[cliche]
            else:
                # 기본 대체안
                result[cliche] = ['(다른 표현으로 변경)', '(동의어 활용)', '(문장 재구성)']

        return result

    def save_to_db(self, db_manager) -> bool:
        """패턴 히스토리를 DB에 저장"""
        try:
            data = {
                'window_size': self.window_size,
                'genre': self.genre,
                'pattern_history': {
                    'cliche_counts': dict(self.pattern_history['cliche_counts']),
                    'starter_counts': dict(self.pattern_history['starter_counts']),
                    'plot_sequences': self.pattern_history['plot_sequences'],
                    'scene_types': self.pattern_history['scene_types'],
                    'reaction_patterns': self.pattern_history['reaction_patterns'],
                }
            }
            db_manager.update_anchor('pattern_tracker', data)
            return True
        except Exception as e:
            print(f"[PatternTracker] DB 저장 실패: {e}")
            return False

    def load_from_db(self, db_manager) -> bool:
        """DB에서 패턴 히스토리 로드"""
        try:
            data = db_manager.get_anchor('pattern_tracker')
            if data:
                self.window_size = data.get('window_size', 10)
                self.genre = data.get('genre', 'wuxia')
                history = data.get('pattern_history', {})
                self.pattern_history['cliche_counts'] = Counter(history.get('cliche_counts', {}))
                self.pattern_history['starter_counts'] = Counter(history.get('starter_counts', {}))
                self.pattern_history['plot_sequences'] = history.get('plot_sequences', [])
                self.pattern_history['scene_types'] = history.get('scene_types', {})
                self.pattern_history['reaction_patterns'] = history.get('reaction_patterns', {})
                return True
            return False
        except Exception as e:
            print(f"[PatternTracker] DB 로드 실패: {e}")
            return False
