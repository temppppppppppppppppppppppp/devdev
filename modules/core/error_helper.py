"""
[V44] 에러 헬퍼 모듈

사용자 친화적 에러 메시지 및 해결책 제공
"""

import logging
from dataclasses import dataclass
from enum import Enum

from modules.core.constants import ManuscriptLimits


class ErrorCategory(Enum):
    """에러 카테고리"""

    DATABASE = "database"
    API = "api"
    FILE = "file"
    VALIDATION = "validation"
    MEMORY = "memory"
    NETWORK = "network"
    CONFIG = "config"
    AGENT = "agent"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """에러 정보 구조체"""

    category: ErrorCategory
    code: str
    message: str
    solution: str
    docs_link: str | None = None
    severity: str = "ERROR"  # DEBUG, INFO, WARNING, ERROR, CRITICAL


# 에러 코드 정의
ERROR_DEFINITIONS: dict[str, ErrorInfo] = {
    # Database Errors
    "DB_CONNECTION_FAILED": ErrorInfo(
        category=ErrorCategory.DATABASE,
        code="DB001",
        message="데이터베이스 연결에 실패했습니다",
        solution="프로젝트 폴더 권한을 확인하고, 다른 프로세스가 DB를 사용 중인지 확인하세요",
        docs_link="docs/troubleshooting.md#db-connection",
    ),
    "DB_INTEGRITY_ERROR": ErrorInfo(
        category=ErrorCategory.DATABASE,
        code="DB002",
        message="데이터 무결성 오류가 발생했습니다",
        solution="DB 파일이 손상되었을 수 있습니다. 백업에서 복원하거나 tools/RESET.py를 실행하세요",
        docs_link="docs/troubleshooting.md#db-integrity",
    ),
    "DB_LOCKED": ErrorInfo(
        category=ErrorCategory.DATABASE,
        code="DB003",
        message="데이터베이스가 잠겨 있습니다",
        solution="다른 프로세스(Streamlit 등)를 종료하고 재시도하세요",
        docs_link="docs/troubleshooting.md#db-locked",
    ),
    "DB_TRANSACTION_FAILED": ErrorInfo(
        category=ErrorCategory.DATABASE,
        code="DB004",
        message="트랜잭션 실행에 실패했습니다",
        solution="변경사항이 롤백되었습니다. 데이터를 확인 후 재시도하세요",
        severity="WARNING",
    ),
    # API Errors
    "API_TIMEOUT": ErrorInfo(
        category=ErrorCategory.API,
        code="API001",
        message="API 응답 시간이 초과되었습니다",
        solution="네트워크 연결을 확인하고, 잠시 후 재시도하세요. 프롬프트가 너무 길면 줄여보세요",
        docs_link="docs/troubleshooting.md#api-timeout",
    ),
    "API_QUOTA_EXCEEDED": ErrorInfo(
        category=ErrorCategory.API,
        code="API002",
        message="API 할당량이 초과되었습니다",
        solution="1-2분 대기 후 재시도하세요. 지속되면 Google Cloud Console에서 할당량을 확인하세요",
        docs_link="docs/troubleshooting.md#api-quota",
    ),
    "API_AUTH_FAILED": ErrorInfo(
        category=ErrorCategory.API,
        code="API003",
        message="API 인증에 실패했습니다",
        solution=".env 파일의 GOOGLE_API_KEY가 올바른지 확인하세요",
        docs_link="docs/troubleshooting.md#api-auth",
        severity="CRITICAL",
    ),
    "API_RESPONSE_MALFORMED": ErrorInfo(
        category=ErrorCategory.API,
        code="API004",
        message="API 응답 형식이 올바르지 않습니다",
        solution="자동 복구를 시도합니다. 실패하면 프롬프트를 단순화하여 재시도하세요",
        severity="WARNING",
    ),
    # File Errors
    "FILE_NOT_FOUND": ErrorInfo(
        category=ErrorCategory.FILE,
        code="FILE001",
        message="파일을 찾을 수 없습니다",
        solution="파일 경로를 확인하고, 프로젝트 구조가 올바른지 확인하세요",
    ),
    "FILE_PERMISSION_DENIED": ErrorInfo(
        category=ErrorCategory.FILE,
        code="FILE002",
        message="파일 접근 권한이 없습니다",
        solution="파일/폴더 권한을 확인하세요. 관리자 권한으로 실행해보세요",
    ),
    "FILE_ENCODING_ERROR": ErrorInfo(
        category=ErrorCategory.FILE,
        code="FILE003",
        message="파일 인코딩 오류가 발생했습니다",
        solution="파일이 UTF-8 인코딩인지 확인하세요",
    ),
    # Validation Errors
    "VALIDATION_LENGTH_SHORT": ErrorInfo(
        category=ErrorCategory.VALIDATION,
        code="VAL001",
        message="원고 길이가 최소 기준에 미달합니다",
        solution=f"원고가 {ManuscriptLimits.MIN_LENGTH}자 이상이 되도록 내용을 보강하세요",
        severity="WARNING",
    ),
    "VALIDATION_DEAD_NPC": ErrorInfo(
        category=ErrorCategory.VALIDATION,
        code="VAL002",
        message="사망한 캐릭터가 등장했습니다",
        solution="해당 캐릭터의 사망 상태를 확인하고, 블루프린트를 수정하세요",
        severity="ERROR",
    ),
    "VALIDATION_ITEM_ERROR": ErrorInfo(
        category=ErrorCategory.VALIDATION,
        code="VAL003",
        message="소유하지 않은 아이템이 사용되었습니다",
        solution="캐릭터의 현재 인벤토리를 확인하고, HUD를 업데이트하세요",
        severity="ERROR",
    ),
    "VALIDATION_LOCATION_ERROR": ErrorInfo(
        category=ErrorCategory.VALIDATION,
        code="VAL004",
        message="파괴된 장소가 방문되었습니다",
        solution="해당 장소의 상태를 확인하고, 블루프린트를 수정하세요",
        severity="ERROR",
    ),
    # Memory/VecMemory Errors
    "MEMORY_VECDB_LOCKED": ErrorInfo(
        category=ErrorCategory.MEMORY,
        code="MEM001",
        message="벡터 DB가 잠겨 있습니다",
        solution="memory/vec_memory.db 파일의 잠금을 해제하거나 프로세스를 재시작하세요",
        docs_link="docs/troubleshooting.md#vecmemory-lock",
    ),
    "MEMORY_VECDB_CORRUPT": ErrorInfo(
        category=ErrorCategory.MEMORY,
        code="MEM002",
        message="벡터 DB가 손상되었습니다",
        solution="memory/vec_memory.db 파일을 삭제하고 Stage 0을 재실행하세요",
        docs_link="docs/troubleshooting.md#vecmemory-corrupt",
        severity="CRITICAL",
    ),
    "MEMORY_EMBEDDING_FAILED": ErrorInfo(
        category=ErrorCategory.MEMORY,
        code="MEM003",
        message="임베딩 생성에 실패했습니다",
        solution="API 할당량을 확인하고, 잠시 후 재시도하세요",
        severity="WARNING",
    ),
    # Config Errors
    "CONFIG_MISSING": ErrorInfo(
        category=ErrorCategory.CONFIG,
        code="CFG001",
        message="필수 설정이 누락되었습니다",
        solution="config/settings.json 파일을 확인하세요",
        docs_link="docs/configuration.md",
    ),
    "CONFIG_INVALID": ErrorInfo(
        category=ErrorCategory.CONFIG,
        code="CFG002",
        message="설정 형식이 올바르지 않습니다",
        solution="JSON 형식을 확인하고, 필수 필드가 모두 있는지 확인하세요",
    ),
    # Agent Errors
    "AGENT_MAX_RETRIES": ErrorInfo(
        category=ErrorCategory.AGENT,
        code="AGT001",
        message="최대 재시도 횟수에 도달했습니다",
        solution="입력 데이터를 확인하고, 프롬프트를 조정해보세요",
        severity="WARNING",
    ),
    "AGENT_JSON_PARSE_FAILED": ErrorInfo(
        category=ErrorCategory.AGENT,
        code="AGT002",
        message="에이전트 응답 파싱에 실패했습니다",
        solution="자동 복구가 시도됩니다. 실패하면 수동 개입이 필요합니다",
        severity="WARNING",
    ),
}


class ErrorHelper:
    """
    [V44] 에러 헬퍼 클래스

    Usage:
        from modules.core.error_helper import ErrorHelper

        # 에러 메시지 출력
        ErrorHelper.print_error("DB_CONNECTION_FAILED", extra_info="SQLite error")

        # 에러 정보 조회
        info = ErrorHelper.get_error_info("API_TIMEOUT")
    """

    @staticmethod
    def get_error_info(error_code: str) -> ErrorInfo | None:
        """에러 코드로 에러 정보 조회"""
        return ERROR_DEFINITIONS.get(error_code)

    @staticmethod
    def format_error_message(error_code: str, extra_info: str = "") -> str:
        """
        포맷된 에러 메시지 생성

        Args:
            error_code: 에러 코드
            extra_info: 추가 정보 (원본 에러 메시지 등)

        Returns:
            str: 포맷된 에러 메시지
        """
        error_info = ERROR_DEFINITIONS.get(error_code)

        if not error_info:
            return f"[UNKNOWN ERROR] {extra_info}"

        lines = [
            f"[{error_info.code}] {error_info.message}",
        ]

        if extra_info:
            lines.append(f"   상세: {extra_info[:100]}")

        lines.append(f"   해결책: {error_info.solution}")

        if error_info.docs_link:
            lines.append(f"   문서: {error_info.docs_link}")

        return "\n".join(lines)

    @staticmethod
    def print_error(error_code: str, extra_info: str = "", ui=None):
        """
        에러 메시지 출력

        Args:
            error_code: 에러 코드
            extra_info: 추가 정보
            ui: StudioVisualizer 인스턴스 (있으면 ui.log 사용)
        """
        message = ErrorHelper.format_error_message(error_code, extra_info)
        error_info = ERROR_DEFINITIONS.get(error_code)

        # 심각도에 따른 이모지
        severity_emoji = {"DEBUG": "", "INFO": "", "WARNING": "", "ERROR": "", "CRITICAL": ""}
        emoji = severity_emoji.get(error_info.severity if error_info else "ERROR", "")

        full_message = f"{emoji} {message}"

        if ui and hasattr(ui, "log"):
            ui.log(full_message)
        else:
            logging.info(full_message)

    @staticmethod
    def classify_exception(exception: Exception) -> str:
        """
        예외를 에러 코드로 분류

        Args:
            exception: 예외 객체

        Returns:
            str: 에러 코드
        """
        error_str = str(exception).lower()
        exc_type = type(exception).__name__.lower()

        # 예외 타입별 분류
        if "timeout" in error_str or "deadline" in error_str:
            return "API_TIMEOUT"
        elif "quota" in error_str or "rate" in error_str or "429" in error_str:
            return "API_QUOTA_EXCEEDED"
        elif "auth" in error_str or "api_key" in error_str or "401" in error_str:
            return "API_AUTH_FAILED"
        elif "lock" in error_str:
            if "chroma" in error_str or "vector" in error_str:
                return "MEMORY_VECDB_LOCKED"
            return "DB_LOCKED"
        elif "corrupt" in error_str or "invalid" in error_str:
            if "chroma" in error_str:
                return "MEMORY_VECDB_CORRUPT"
            return "DB_INTEGRITY_ERROR"
        elif "permission" in error_str or "access" in error_str:
            return "FILE_PERMISSION_DENIED"
        elif "filenotfound" in exc_type or "no such file" in error_str:
            return "FILE_NOT_FOUND"
        elif "encoding" in error_str or "codec" in error_str:
            return "FILE_ENCODING_ERROR"
        elif "connection" in error_str or "network" in error_str:
            return "API_TIMEOUT"
        elif "json" in error_str or "parse" in error_str or "decode" in error_str:
            return "AGENT_JSON_PARSE_FAILED"
        elif "sqlite" in error_str or "database" in error_str:
            return "DB_CONNECTION_FAILED"

        return "UNKNOWN"

    @staticmethod
    def handle_exception(exception: Exception, context: str = "", ui=None):
        """
        예외 처리 및 사용자 친화적 메시지 출력

        Args:
            exception: 예외 객체
            context: 에러 발생 컨텍스트
            ui: UI 인스턴스
        """
        error_code = ErrorHelper.classify_exception(exception)
        extra_info = f"{context}: {str(exception)[:150]}" if context else str(exception)[:150]
        ErrorHelper.print_error(error_code, extra_info, ui)


# 편의 함수
def print_error(error_code: str, extra_info: str = "", ui=None):
    """에러 출력 (단축형)"""
    ErrorHelper.print_error(error_code, extra_info, ui)


def handle_exception(exception: Exception, context: str = "", ui=None):
    """예외 처리 (단축형)"""
    ErrorHelper.handle_exception(exception, context, ui)


def get_solution(error_code: str) -> str:
    """해결책 조회 (단축형)"""
    info = ErrorHelper.get_error_info(error_code)
    return info.solution if info else "알 수 없는 오류입니다."
