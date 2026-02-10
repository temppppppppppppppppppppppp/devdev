"""
[V40 Enhanced] 시스템 전역 상수 정의
모든 매직 넘버와 설정값을 중앙에서 관리
"""

# ============================================================================
# [V40] 장르 시스템 상수
# ============================================================================

class GenreTypes:
    """지원되는 장르 타입"""
    WUXIA = 'wuxia'
    HUNTER = 'hunter'
    INVESTMENT = 'investment'
    COMPOSER = 'composer'
    COOKING = 'cooking'
    ALT_HISTORY = 'alt_history'
    ACTOR = 'actor'
    SPORTS = 'sports'
    MEDICAL = 'medical'

    @classmethod
    def all(cls):
        return [cls.WUXIA, cls.HUNTER, cls.INVESTMENT, cls.COMPOSER, cls.COOKING, cls.ALT_HISTORY, cls.ACTOR, cls.SPORTS, cls.MEDICAL]

    @classmethod
    def get_name(cls, genre_type):
        """장르 타입 → 한글 이름"""
        return {
            cls.WUXIA: '무협',
            cls.HUNTER: '헌터',
            cls.INVESTMENT: '투자',
            cls.COMPOSER: '작곡가',
            cls.COOKING: '요리',
            cls.ALT_HISTORY: '대체역사',
            cls.ACTOR: '배우물',
            cls.SPORTS: '스포츠',
            cls.MEDICAL: '의학',
        }.get(genre_type, '알 수 없음')


# ============================================================================
# 재시도 및 제한 상수
# ============================================================================

class RetryLimits:
    """재시도 횟수 및 제한"""
    # 에이전트 재시도
    DIRECTOR_MAX_ATTEMPTS = 5          # 디렉터 검증 최대 시도 [V62.4]
    ANALYST_MAX_ATTEMPTS = 5           # Analyst Arc 설계 최대 시도 [V62.4]
    ARCHITECT_MAX_ATTEMPTS = 5         # 아키텍트 설계 최대 시도
    WRITER_MAX_ATTEMPTS = 5            # 작가 집필 최대 시도 [V62.4]
    BLUEPRINT_MAX_ATTEMPTS = 12        # 블루프린트 생성 최대 시도

    # 시스템 재시도
    USER_INPUT_ATTEMPTS = 3            # 사용자 입력 재시도
    CACHE_RETRY_ATTEMPTS = 3           # 캐시 생성 재시도

    # 타임아웃
    CACHE_TTL_SECONDS = 86400          # 캐시 유효 시간 (24시간)
    API_TIMEOUT_SECONDS = 300          # API 타임아웃 (5분)


class RecoveryLimits:
    """복구 관련 제한"""
    MAX_PARALLEL_RECOVERY = 2          # 병렬 복구 최대 시도 횟수
    CRITICAL_MISSING_THRESHOLD = 3     # 핵심 데이터 누락 임계값


class WritingLimits:
    """집필 관련 제한"""
    MAX_RETRY_PER_EPISODE = 5          # 에피소드당 최대 재시도 횟수
    MIN_EPISODE_LOOP_GUARD = 5         # 최소 에피소드 루프 가드
    MAX_FAILURE_STREAK = 3             # 연속 실패 허용 횟수


class Stage2Limits:
    """[V60.74] Stage 2 Arc 설계 관련 상수"""
    # 가변 페이싱 범위
    MIN_EP_COUNT = 3                   # 최소 화수 (Blitz)
    MAX_EP_COUNT = 7                   # 최대 화수 (Epic)
    DEFAULT_EP_COUNT = 5               # 기본 화수 (Standard)

    # tactical_doc 분량 기준
    MIN_CHARS_PER_EPISODE = 500        # 화당 최소 문자 수
    RECOMMENDED_CHARS_PER_EPISODE = 600  # 화당 권장 문자 수

    # 아이템 유사도 판단 기준
    ITEM_SIMILARITY_RATIO_MIN = 0.5    # 50% 이상 겹치면 유사
    ITEM_SIMILARITY_RATIO_MAX = 2.0    # 2배 이내 길이 차이면 유사

    # 내공 기본값
    INTERNAL_ENERGY_FALLBACK = 50      # 파싱 실패 시 보수적 기본값


class AIModels:
    """AI 모델 이름 상수"""
    # [V60.65] 기본 3-pro, 할당량 초과 시 2.5-pro 폴백

    # 점진적 모델 업그레이드 체계 - Architect
    TIER_1_ARCHITECT = "gemini-3-pro-preview"      # 1차 시도: 3 Pro
    TIER_2_ARCHITECT = "gemini-3-pro-preview"      # 2차 시도: 3 Pro
    TIER_3_ARCHITECT = "gemini-3-pro-preview"      # 3차+ 시도: 3 Pro

    # 점진적 모델 업그레이드 체계 - Writer
    TIER_1_WRITER = "gemini-3-pro-preview"         # 1차 시도: 3 Pro
    TIER_2_WRITER = "gemini-3-pro-preview"         # 2차 시도: 3 Pro
    TIER_3_WRITER = "gemini-3-pro-preview"         # 3차 시도 이후: 3 Pro

    EMERGENCY_FALLBACK = "gemini-2.5-pro"          # [V60.65] 긴급/할당량 초과 시 2.5 Pro
    QUOTA_FALLBACK = "gemini-2.5-pro"              # [V60.65] 429 에러 시 폴백 모델
    DEFAULT_WRITER = "gemini-3-pro-preview"
    DEFAULT_ARCHITECT = "gemini-3-pro-preview"
    DEFAULT_ANALYST = "gemini-3-pro-preview"
    DEFAULT_REVIEWER = "gemini-2.5-pro"

    # [V40 Fix] Stage 4 전용 고정 모델
    STAGE4_FIXED_WRITER_MODEL = "gemini-3-pro-preview"

    # Stage 2 전용 모델 상수
    STAGE2_MAIN_MODEL = "gemini-3-pro-preview"     # Stage 2 주요 생성 모델
    STAGE2_EXTRACTION_MODEL = "gemini-2.5-pro"     # Stage 2 추출 모델
    STAGE2_VALIDATION_MODEL = "gemini-2.5-pro"     # Stage 2 검증 모델


class BatchSizes:
    """배치 처리 크기"""
    ARC_BATCH_SIZE = 5                 # 아크 배치 크기
    EPISODE_BATCH_SIZE = 10            # 에피소드 배치 크기
    PARALLEL_ENRICH_MAX = 5            # 병렬 농축 최대 개수
    BLUEPRINT_BATCH_SIZE = 5           # 블루프린트 배치 크기


# ============================================================================
# 임계값 및 검증 상수
# ============================================================================

class Thresholds:
    """검증 임계값"""
    # 텍스트 유사도
    TACTICAL_DUPLICATE_THRESHOLD = 0.98     # 전술서 중복 판정 임계값
    PATTERN_MIN_HITS = 1                    # 패턴 최소 히트 수 (낮춤: 2→1)
    
    # 길이 제한
    MIN_TACTICAL_DOC_LENGTH = 100           # 전술서 최소 길이
    MAX_TACTICAL_DOC_LENGTH = 5000          # 전술서 최대 길이
    MIN_BLUEPRINT_LENGTH = 500              # 블루프린트 최소 길이
    MAX_BLUEPRINT_LENGTH = 8000             # 블루프린트 최대 길이
    MIN_MANUSCRIPT_LENGTH = 2000            # 원고 최소 길이
    
    # 캐시
    MIN_CACHE_CONTENT_LENGTH = 1500         # 캐시 최소 콘텐츠 길이 (토큰)
    
    # HUD 변화 감지
    HUD_CHANGE_THRESHOLD = 0.1              # HUD 변화 감지 임계값 (10%)


class VolumeSettings:
    """권 및 아크 설정"""
    ARCS_PER_VOLUME = 5                     # 권당 아크 개수
    EPISODES_PER_ARC = 5                    # 아크당 기본 에피소드 개수 (Standard 기준)
    MIN_EPISODES_PER_ARC = 3                # 아크당 최소 에피소드 (Blitz 최소)
    MAX_EPISODES_PER_ARC = 7                # 아크당 최대 에피소드 (Epic 최대)


class SceneSettings:
    """장면(Scene) 구성 설정"""
    TARGET_SCENE_COUNT = 6                  # 목표 장면 개수 (하향: 10→6)
    MIN_SCENE_COUNT = 4                     # 최소 장면 개수 (반려 기준)


# ============================================================================
# 온도 및 AI 파라미터
# ============================================================================

class AIParameters:
    """AI 모델 파라미터"""
    # 온도 설정
    TEMPERATURE_CREATIVE = 0.9              # 창의적 작업 (Writer)
    TEMPERATURE_BALANCED = 0.7              # 균형 작업 (Architect)
    TEMPERATURE_PRECISE = 0.3               # 정밀 작업 (Analyst, Director)
    TEMPERATURE_SURGERY = 0.3               # 수술 모드 (Arc Reconstruction)
    
    # Top-P 설정
    TOP_P_DEFAULT = 0.95
    TOP_P_FOCUSED = 0.85
    
    # 토큰 제한
    MAX_OUTPUT_TOKENS_SHORT = 2048          # 짧은 응답
    MAX_OUTPUT_TOKENS_MEDIUM = 4096         # 중간 응답
    MAX_OUTPUT_TOKENS_LONG = 8192           # 긴 응답


# ============================================================================
# HUD 및 상태 관리
# ============================================================================

# 무협 소설 캐릭터 지표 15대 메트릭 (DB 테이블 컬럼명과 일치)
MARTIAL_METRICS = [
    'alias', 'rank', 'realm', 'internal_energy', 'mental_method',
    'reputation', 'public_image', 'equipment', 'wealth', 'token',
    'misunderstanding', 'obsession', 'current_objective', 'qi_nature', 'causal_injuries'
]


class HUDKeys:
    """장르별 HUD 키 매핑"""
    # 무협
    WUXIA_PROTAGONIST = 'Protagonist'
    WUXIA_HUD_ROOT = 'MartialHUD'
    WUXIA_ACTUAL_TRUTH = 'actual_truth'

    # 헌터
    HUNTER_PROTAGONIST = 'Protagonist'
    HUNTER_HUD_ROOT = 'HunterHUD'
    HUNTER_ACTUAL_TRUTH = 'actual_truth'

    # 투자
    INVESTMENT_PROTAGONIST = 'Protagonist'
    INVESTMENT_HUD_ROOT = 'FinanceHUD'
    INVESTMENT_ACTUAL_TRUTH = 'actual_truth'

    # 작곡가
    COMPOSER_PROTAGONIST = 'Protagonist'
    COMPOSER_HUD_ROOT = 'ComposerHUD'
    COMPOSER_ACTUAL_TRUTH = 'actual_truth'

    # 요리
    COOKING_PROTAGONIST = 'Protagonist'
    COOKING_HUD_ROOT = 'CookingHUD'
    COOKING_ACTUAL_TRUTH = 'actual_truth'

    # 대체역사
    ALT_HISTORY_PROTAGONIST = 'Protagonist'
    ALT_HISTORY_HUD_ROOT = 'JoseonHUD'
    ALT_HISTORY_ACTUAL_TRUTH = 'actual_truth'

    # 배우물
    ACTOR_PROTAGONIST = 'Protagonist'
    ACTOR_HUD_ROOT = 'ActorHUD'
    ACTOR_ACTUAL_TRUTH = 'actual_truth'

    # 스포츠
    SPORTS_PROTAGONIST = 'Protagonist'
    SPORTS_HUD_ROOT = 'SportsHUD'
    SPORTS_ACTUAL_TRUTH = 'actual_truth'

    # 의학
    MEDICAL_PROTAGONIST = 'Protagonist'
    MEDICAL_HUD_ROOT = 'MedicalHUD'
    MEDICAL_ACTUAL_TRUTH = 'actual_truth'

    # 장르 → HUD root 매핑
    _GENRE_HUD_MAP = {
        'wuxia': 'MartialHUD',
        'hunter': 'HunterHUD',
        'investment': 'FinanceHUD',
        'composer': 'ComposerHUD',
        'cooking': 'CookingHUD',
        'alt_history': 'JoseonHUD',
        'actor': 'ActorHUD',
        'sports': 'SportsHUD',
        'medical': 'MedicalHUD',
        'fantasy': 'MartialHUD',
    }

    @classmethod
    def get_hud_root(cls, genre: str = '') -> str:
        """장르에 맞는 HUD root 키 반환. 알 수 없으면 MartialHUD 폴백."""
        return cls._GENRE_HUD_MAP.get(genre, 'MartialHUD')

    # [V61.10] 장르 역할명 블랙리스트 - HUD name 기본값 오염 방지
    _ROLE_NAME_BLACKLIST = {
        '투자자', '헌터', '무협인', '요리사', '작곡가', '배우', '주인공',
        '사냥꾼', '검사', '궁사', '마법사', '기사', '용사', '모험가',
        '조선인', '선비', '관리', '왕', '임금', '각성자',
        '선수', '운동선수', '의사', '닥터',
    }

    @classmethod
    def get_protagonist_name(cls, bible_root: dict, genre: str = '') -> str:
        """Bible에서 주인공 이름 추출. CoreIdentity와 교차검증.

        [V61.10] 역할명 오염 방지: HUD name이 장르 역할명(투자자, 헌터 등)이면
        CoreIdentity.protagonist를 우선 사용.

        탐색 순서:
        0. CoreIdentity.protagonist (권위적 소스)
        1. 장르별 HUD (FinanceHUD/HunterHUD/MartialHUD)
        2. 모든 HUD 후보 순회
        3. AssetLibrary.KeyNPCs에서 role='주인공'
        4. KeyNPCs[0]
        5. '주인공' 기본값
        """
        # [V61.10] 0순위: CoreIdentity.protagonist (가장 권위적)
        core_name = None
        try:
            core_name = bible_root.get('ProjectData', {}).get('CoreIdentity', {}).get('protagonist')
        except Exception:
            pass

        # 1순위: 장르별 HUD
        hud_keys = [cls.get_hud_root(genre)] if genre else []
        # 2순위: 모든 HUD 후보 순회
        for hk in ['MartialHUD', 'FinanceHUD', 'HunterHUD', 'ComposerHUD', 'CookingHUD', 'JoseonHUD', 'ActorHUD', 'SportsHUD', 'MedicalHUD']:
            if hk not in hud_keys:
                hud_keys.append(hk)

        hud_name = None
        for hud_key in hud_keys:
            hud = bible_root.get(hud_key, {})
            name = hud.get('Protagonist', {}).get('actual_truth', {}).get('name')
            if name:
                hud_name = name
                break

        # [V61.10] 교차검증: HUD name이 역할명이면 CoreIdentity 우선
        if hud_name and hud_name in cls._ROLE_NAME_BLACKLIST:
            if core_name and core_name not in cls._ROLE_NAME_BLACKLIST:
                print(f"      ⚠️ [V61.10] HUD name '{hud_name}'은 역할명 → CoreIdentity '{core_name}' 사용")
                return core_name
        # HUD name이 정상이면 그대로 사용
        if hud_name and hud_name not in cls._ROLE_NAME_BLACKLIST:
            return hud_name
        # CoreIdentity가 있으면 사용
        if core_name and core_name not in cls._ROLE_NAME_BLACKLIST:
            return core_name

        # 3순위: AssetLibrary.KeyNPCs
        assets = bible_root.get('AssetLibrary', {})
        key_npcs = assets.get('KeyNPCs', []) or assets.get('Key_NPCs', [])
        for npc in key_npcs:
            if isinstance(npc, dict) and ('주인공' in npc.get('role', '') or '주인' in npc.get('role', '')):
                if npc.get('name'):
                    return npc['name']
        # 4순위: 첫 번째 NPC
        if key_npcs and isinstance(key_npcs[0], dict) and key_npcs[0].get('name'):
            return key_npcs[0]['name']

        return '주인공'


class NPCHUDKeys:
    """장르별 NPC HUD 키"""
    WUXIA = 'NPC_Martial_HUD'
    HUNTER = 'NPC_Hunter_Status'
    INVESTMENT = 'NPC_Business_Profile'
    COMPOSER = 'NPC_Music_Profile'
    COOKING = 'NPC_Cooking_Profile'
    ALT_HISTORY = 'NPC_Joseon_Status'
    ACTOR = 'NPC_Actor_Profile'
    SPORTS = 'NPC_Sports_Profile'
    MEDICAL = 'NPC_Medical_Profile'

    @classmethod
    def get_key(cls, genre_type):
        """장르 타입에 따른 NPC HUD 키 반환"""
        return {
            GenreTypes.WUXIA: cls.WUXIA,
            GenreTypes.HUNTER: cls.HUNTER,
            GenreTypes.INVESTMENT: cls.INVESTMENT,
            GenreTypes.COMPOSER: cls.COMPOSER,
            GenreTypes.COOKING: cls.COOKING,
            GenreTypes.ALT_HISTORY: cls.ALT_HISTORY,
            GenreTypes.ACTOR: cls.ACTOR,
            GenreTypes.SPORTS: cls.SPORTS,
            GenreTypes.MEDICAL: cls.MEDICAL,
        }.get(genre_type, cls.WUXIA)


# ============================================================================
# 파일 경로 및 확장자
# ============================================================================

class FileExtensions:
    """파일 확장자"""
    JSON = '.json'
    TEXT = '.txt'
    MARKDOWN = '.md'
    ENV = '.env'
    DB = '.db'


class DirectoryNames:
    """디렉토리 이름"""
    CONFIG = 'config'
    DRAFTS = 'drafts'
    LOGS = 'logs'
    CHROMA_DB = 'chroma_db'
    DB_EXPORTS = 'db_exports'
    PROMPTS = 'prompts'
    CASH = 'cash'
    SEEDS = 'seeds'


# ============================================================================
# 로그 및 감사
# ============================================================================

class LogLevels:
    """로그 레벨"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class AuditEvents:
    """감사 이벤트 타입"""
    STAGE_START = 'stage_start'
    STAGE_COMPLETE = 'stage_complete'
    AGENT_CALL = 'agent_call'
    DIRECTOR_REJECT = 'director_reject'
    DIRECTOR_ACCEPT = 'director_accept'
    ENRICH_ERROR = 'enrich_error'
    FLOW_GUARD = 'flow_guard'
    ARC_RECONSTRUCTION = 'arc_reconstruction'
    CACHE_CREATED = 'cache_created'
    CACHE_REUSED = 'cache_reused'
    DB_COMMIT = 'db_commit'
    DB_ROLLBACK = 'db_rollback'


# ============================================================================
# 스테이지 및 프로세스
# ============================================================================

class Stages:
    """생산 공정 스테이지"""
    STAGE_0 = 0  # 성경(Bible) 생성
    STAGE_1 = 1  # 권(Volumes) 전략 수립
    STAGE_2 = 2  # 아크(Arcs) 설계
    STAGE_3 = 3  # 블루프린트 생성
    STAGE_4 = 4  # 원고 집필
    
    @classmethod
    def get_name(cls, stage_num):
        """스테이지 번호 → 이름"""
        return {
            cls.STAGE_0: 'Bible Generation',
            cls.STAGE_1: 'Volume Strategy',
            cls.STAGE_2: 'Arc Design',
            cls.STAGE_3: 'Blueprint Creation',
            cls.STAGE_4: 'Manuscript Writing'
        }.get(stage_num, 'Unknown Stage')


# ============================================================================
# 패턴 및 클리셰
# ============================================================================

class PatternTypes:
    """서사 패턴 타입"""
    POWER_UP = 'power_up'              # 파워업/성장
    CONFLICT = 'conflict'              # 갈등/전투
    REVELATION = 'revelation'          # 반전/폭로
    EMOTIONAL = 'emotional'            # 감정/관계
    COMEDY = 'comedy'                  # 코믹/일상
    CRISIS = 'crisis'                  # 위기/재난


# ============================================================================
# 에러 메시지
# ============================================================================

class ErrorMessages:
    """표준화된 에러 메시지"""
    # 캐시 관련
    CACHE_CREATION_FAILED = "캐시 생성 실패"
    CACHE_SAVE_FAILED = "캐시 정보 저장 실패"

    # DB 관련
    DB_COMMIT_FAILED = "데이터베이스 커밋 실패"
    DB_CONNECTION_FAILED = "데이터베이스 연결 실패"

    # 에이전트 관련
    AGENT_INITIALIZATION_FAILED = "에이전트 초기화 실패"
    AGENT_CALL_FAILED = "에이전트 호출 실패"

    # 검증 관련
    INVALID_GENRE = "지원하지 않는 장르입니다"
    ARC_VALIDATION_FAILED = "아크 검증 실패"
    BLUEPRINT_VALIDATION_FAILED = "블루프린트 검증 실패"
    INTEGRITY_CHECK_FAILED = "무결성 검사 실패"

    # 프로젝트 관련
    PROJECT_NOT_FOUND = "프로젝트를 찾을 수 없습니다"
    VECTOR_DB_LOCK_FAILED = "벡터 DB 잠금 실패"
    VECTOR_DB_CORRUPTED = "벡터 DB 손상 감지"

    # 프로세스 관련
    DIRECTOR_REJECT = "디렉터 거부"
    EMPTY_BATCH = "배치가 비어 있습니다"
    STAGE_PREREQUISITE_MISSING = "선행 스테이지가 완료되지 않았습니다"
    REFERENCE_LOAD_FAILED = "레퍼런스 데이터 로드 실패"
    SAFETY_LIMIT_REACHED = "안전 제한에 도달했습니다"

    # 입력 관련
    INVALID_INPUT = "잘못된 입력입니다"
    INPUT_OUT_OF_RANGE = "입력값이 허용 범위를 벗어났습니다"


# ============================================================================
# 성공 메시지
# ============================================================================

class SuccessMessages:
    """표준화된 성공 메시지"""
    # 캐시 관련
    CACHE_CREATED = "캐시 생성 완료"
    CACHE_SAVED = "캐시 정보 DB 저장 완료"
    CACHE_REUSED = "기존 캐시 재사용"

    # DB 관련
    DB_COMMIT_SUCCESS = "데이터베이스 저장 완료"
    DB_CONNECTION_SUCCESS = "데이터베이스 연결 성공"

    # 에이전트 관련
    AGENT_READY = "에이전트 준비 완료"
    ALL_AGENTS_READY = "모든 에이전트 안전하게 초기화 완료"

    # 스테이지 관련
    STAGE_COMPLETE = "스테이지 완료"
    BLUEPRINT_SAVED = "설계도 최종 박제 완료"
    MANUSCRIPT_SAVED = "원고 저장 완료"

    # 프로젝트 관련
    PROJECT_LOADED = "프로젝트 로드 완료"
    GENRE_SAVED = "프로젝트 장르 정보 저장"

    # 검증 관련
    VALIDATION_PASSED = "검증 통과"
    INTEGRITY_CHECK_PASSED = "무결성 점검 완료"
    REFERENCE_LOADED = "레퍼런스 데이터 로드 완료"


# ============================================================================
# 기타 상수
# ============================================================================

class Emojis:
    """로그용 이모지"""
    ROCKET = '🚀'
    CHECK = '✅'
    WARNING = '⚠️'
    ERROR = '❌'
    INFO = 'ℹ️'
    FIRE = '🔥'
    BRAIN = '🧠'
    HAMMER = '🔨'
    PENCIL = '✏️'
    BOOK = '📚'
    LOCK = '🔒'
    KEY = '🔑'
    SAVE = '💾'
    BOLT = '⚡'
    CRYSTAL = '💎'


# ============================================================================
# [V40 Premium] 고급 품질 관리 시스템 상수
# ============================================================================

class V40PremiumThresholds:
    """V40 Premium 품질 관리 시스템 임계값"""

    # RepetitionGuard (N-gram Deduplication)
    REPETITION_WINDOW_SIZE = 5              # 분석할 이전 에피소드 수
    REPETITION_THRESHOLD = 3                # 동일 n-gram 차단 기준 (N회 이상 반복)
    REPETITION_MIN_PHRASE_LENGTH = 5        # 최소 구문 길이 (문자 수)
    REPETITION_CLEAN_SCORE_MIN = 0.85       # 클린 점수 최소값 (85% 이상 통과)

    # EmotionTracker (감정선 아크 추적)
    EMOTION_VARIANCE_MIN = 0.5              # 단조로움 판정 분산 최소값
    EMOTION_HISTORY_WINDOW = 5              # 단조로움 검사 윈도우 (최근 N화)
    EMOTION_MIN_EPISODES_FOR_CHECK = 3      # 감정 추적 시작 최소 에피소드 수
    EMOTION_NEGATIVE_ALERT_AVG = -1.0       # 부정 감정 과다 경고 (평균값)
    EMOTION_POSITIVE_ALERT_AVG = 1.0        # 긍정 감정 과다 경고 (평균값)
    EMOTION_MAX_HISTORY_SIZE = 50           # 메모리 절약용 최대 이력 크기

    # ReferenceAnchor (참조 앵커 시스템)
    ANCHOR_RECENT_WINDOW = 10               # 관련 앵커 추출 범위 (최근 N화)
    ANCHOR_RECENCY_BONUS_THRESHOLD = 5      # 최신성 보너스 적용 범위 (N화 이내)
    ANCHOR_RECENCY_BONUS_SCORE = 10         # 최신성 보너스 점수
    ANCHOR_EXTRACTION_LIMIT = 5             # 에피소드당 추출할 앵커 수 (3~5개)
    ANCHOR_MAX_STORAGE = 100                # DB에 저장할 최대 앵커 수
    ANCHOR_COMPRESSION_THRESHOLD = 5000     # 원고 압축 기준 (문자 수)
    ANCHOR_COMPRESSED_PART_SIZE = 2000      # 압축 시 추출 부분 크기

    # Manuscript Quality (원고 품질)
    MANUSCRIPT_MIN_LENGTH_DIRECTOR = 4000   # Director 통과 최소 글자 수
    MANUSCRIPT_TARGET_LENGTH_WRITER = 5000  # Writer 목표 글자 수

    # Emotion States (감정 상태 값)
    EMOTION_STATE_DESPAIR = -2              # 절망
    EMOTION_STATE_FRUSTRATION = -1          # 좌절
    EMOTION_STATE_NEUTRAL = 0               # 평온
    EMOTION_STATE_HOPE = 1                  # 희망
    EMOTION_STATE_TRIUMPH = 2               # 승리


class V40PremiumAnchorTypes:
    """V40 Premium 참조 앵커 타입"""
    COMBAT = 'combat'                       # 전투
    ITEM = 'item'                           # 아이템
    RELATIONSHIP = 'relationship'           # 인간관계
    LOCATION = 'location'                   # 위치/이동
    POWER = 'power'                         # 경지/능력
    REVELATION = 'revelation'               # 비밀/폭로
    INJURY = 'injury'                       # 부상/상태
    DECISION = 'decision'                   # 중요 결정

    @classmethod
    def all(cls):
        """모든 앵커 타입 반환"""
        return [
            cls.COMBAT, cls.ITEM, cls.RELATIONSHIP, cls.LOCATION,
            cls.POWER, cls.REVELATION, cls.INJURY, cls.DECISION
        ]

    @classmethod
    def critical_types(cls):
        """필수 참조 앵커 타입 (설정 충돌 방지용)"""
        return [cls.ITEM, cls.INJURY, cls.POWER, cls.LOCATION]


class V40PremiumEmotionStates:
    """V40 Premium 감정 상태 정의"""
    DESPAIR = 'despair'                     # 절망
    FRUSTRATION = 'frustration'             # 좌절
    NEUTRAL = 'neutral'                     # 평온
    HOPE = 'hope'                           # 희망
    TRIUMPH = 'triumph'                     # 승리

    @classmethod
    def all(cls):
        """모든 감정 상태 반환"""
        return [cls.DESPAIR, cls.FRUSTRATION, cls.NEUTRAL, cls.HOPE, cls.TRIUMPH]

    @classmethod
    def get_value(cls, state):
        """감정 상태 → 수치 값 매핑"""
        return {
            cls.DESPAIR: V40PremiumThresholds.EMOTION_STATE_DESPAIR,
            cls.FRUSTRATION: V40PremiumThresholds.EMOTION_STATE_FRUSTRATION,
            cls.NEUTRAL: V40PremiumThresholds.EMOTION_STATE_NEUTRAL,
            cls.HOPE: V40PremiumThresholds.EMOTION_STATE_HOPE,
            cls.TRIUMPH: V40PremiumThresholds.EMOTION_STATE_TRIUMPH
        }.get(state, 0)
