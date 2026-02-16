"""
[V44] 글도비 로깅 시스템

표준화된 로깅 인터페이스를 제공하여 일관된 로그 출력 및 파일 저장을 지원합니다.

Features:
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 듀얼 출력: 콘솔 + 파일
- 세션별 로그 파일 자동 생성
- Rich 콘솔 통합 (선택적)
- 기존 print() 호출 호환 레이어
"""

import logging
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


class LogLevel:
    """로그 레벨 상수"""

    DEBUG = logging.DEBUG  # 10
    INFO = logging.INFO  # 20
    WARNING = logging.WARNING  # 30
    ERROR = logging.ERROR  # 40
    CRITICAL = logging.CRITICAL  # 50


class StudioLogger:
    """
    [V44] 글도비 통합 로거

    Usage:
        from modules.core.logger import get_logger
        logger = get_logger("Stage4")
        logger.info("집필 시작")
        logger.error("오류 발생", exc_info=True)
    """

    _instance: Optional["StudioLogger"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_dir: Path | None = None, session_name: str | None = None):
        """
        로거 초기화

        Args:
            log_dir: 로그 파일 저장 디렉토리 (기본: logs/)
            session_name: 세션 이름 (기본: 타임스탬프)
        """
        # 이미 초기화된 경우 스킵
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 세션 정보
        self.session_start = datetime.now()
        self.session_name = session_name or self.session_start.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"session_{self.session_name}.log"

        # 루트 로거 설정
        self.root_logger = logging.getLogger("글도비")
        self.root_logger.setLevel(logging.DEBUG)  # 모든 레벨 수신

        # 기존 핸들러 제거 (중복 방지)
        self.root_logger.handlers.clear()

        # 콘솔 핸들러 (INFO 이상)
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(self._get_console_formatter())
        self.root_logger.addHandler(self.console_handler)

        # 파일 핸들러 (DEBUG 이상)
        self.file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self._get_file_formatter())
        self.root_logger.addHandler(self.file_handler)

        # 하위 로거 캐시
        self._loggers = {}

        # 메트릭 추적
        self._metrics = {"debug_count": 0, "info_count": 0, "warning_count": 0, "error_count": 0, "critical_count": 0}

    def _get_console_formatter(self) -> logging.Formatter:
        """콘솔용 포맷터 (간결)"""
        return logging.Formatter(fmt="%(message)s", datefmt="%H:%M:%S")

    def _get_file_formatter(self) -> logging.Formatter:
        """파일용 포맷터 (상세)"""
        return logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    def get_logger(self, name: str) -> logging.Logger:
        """
        명명된 로거 반환

        Args:
            name: 로거 이름 (예: "Stage4", "Writer", "DB")

        Returns:
            logging.Logger: 설정된 로거
        """
        if name not in self._loggers:
            logger = self.root_logger.getChild(name)
            self._loggers[name] = logger
        return self._loggers[name]

    def debug(self, msg: str, *args, **kwargs):
        """DEBUG 레벨 로그"""
        self._metrics["debug_count"] += 1
        self.root_logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """INFO 레벨 로그"""
        self._metrics["info_count"] += 1
        self.root_logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """WARNING 레벨 로그"""
        self._metrics["warning_count"] += 1
        self.root_logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """ERROR 레벨 로그"""
        self._metrics["error_count"] += 1
        self.root_logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """CRITICAL 레벨 로그"""
        self._metrics["critical_count"] += 1
        self.root_logger.critical(msg, *args, **kwargs)

    def log(self, msg: str, level: int = logging.INFO):
        """
        범용 로그 메서드 (StudioVisualizer 호환)

        Args:
            msg: 로그 메시지
            level: 로그 레벨 (기본: INFO)
        """
        # 이모지 기반 레벨 자동 감지
        if any(e in msg for e in ["🚨", "❌", "🛑"]):
            level = logging.ERROR
        elif any(e in msg for e in ["⚠️", "⚡"]):
            level = logging.WARNING
        elif any(e in msg for e in ["🐛", "🔍"]):
            level = logging.DEBUG

        self.root_logger.log(level, msg)

    def get_metrics(self) -> dict:
        """로그 메트릭 반환"""
        return {
            **self._metrics,
            "session_name": self.session_name,
            "session_start": self.session_start.isoformat(),
            "log_file": str(self.log_file),
        }

    def set_console_level(self, level: int):
        """콘솔 출력 레벨 변경"""
        self.console_handler.setLevel(level)

    def set_file_level(self, level: int):
        """파일 출력 레벨 변경"""
        self.file_handler.setLevel(level)

    def close(self) -> None:
        """로거 종료 및 리소스 정리"""
        for handler in self.root_logger.handlers[:]:
            handler.close()
            self.root_logger.removeHandler(handler)


# 전역 로거 인스턴스
_studio_logger: StudioLogger | None = None


def init_logger(log_dir: Path | None = None, session_name: str | None = None) -> StudioLogger:
    """
    로거 초기화 (애플리케이션 시작 시 한 번 호출)

    Args:
        log_dir: 로그 디렉토리
        session_name: 세션 이름

    Returns:
        StudioLogger: 초기화된 로거
    """
    global _studio_logger
    _studio_logger = StudioLogger(log_dir, session_name)
    return _studio_logger


def get_logger(name: str = "Main") -> logging.Logger:
    """
    명명된 로거 반환

    Args:
        name: 로거 이름

    Returns:
        logging.Logger: 설정된 로거
    """
    global _studio_logger
    if _studio_logger is None:
        _studio_logger = StudioLogger()
    return _studio_logger.get_logger(name)


def log(msg: str, level: int = logging.INFO):
    """
    간편 로그 함수 (print 대체)

    Args:
        msg: 로그 메시지
        level: 로그 레벨
    """
    global _studio_logger
    if _studio_logger is None:
        _studio_logger = StudioLogger()
    _studio_logger.log(msg, level)


# 편의 함수들
def debug(msg: str):
    log(msg, logging.DEBUG)


def info(msg: str):
    log(msg, logging.INFO)


def warning(msg: str):
    log(msg, logging.WARNING)


def error(msg: str):
    log(msg, logging.ERROR)


def critical(msg: str):
    log(msg, logging.CRITICAL)


class LoggerAdapter:
    """
    [V44] 기존 StudioVisualizer와 호환되는 어댑터

    기존 코드의 ui.log() 호출을 로깅 시스템으로 연결합니다.
    """

    def __init__(self, logger_name: str = "UI"):
        self._logger = get_logger(logger_name)

    def log(self, msg: str):
        """기존 ui.log() 호환"""
        self._logger.info(msg)

    def error(self, msg: str):
        """에러 로그"""
        self._logger.error(msg)

    def warning(self, msg: str):
        """경고 로그"""
        self._logger.warning(msg)

    def debug(self, msg: str):
        """디버그 로그"""
        self._logger.debug(msg)
