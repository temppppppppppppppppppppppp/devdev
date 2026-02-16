"""
[V44] 에스케이프 유틸리티 모듈

중괄호 에스케이프 최적화 및 중복 방지
"""

import json
from typing import Any


class EscapeUtils:
    """
    [V44] 에스케이프 유틸리티 클래스

    Features:
    - 중복 에스케이프 방지
    - 에스케이프 필요 여부 사전 확인
    - LRU 캐시로 반복 연산 최적화
    - 배치 에스케이프 지원
    """

    @staticmethod
    def needs_escape(text: str) -> bool:
        """
        에스케이프 필요 여부 확인

        Args:
            text: 검사할 텍스트

        Returns:
            bool: 에스케이프가 필요하면 True
        """
        if not isinstance(text, str):
            return False

        # [V70] ESCAPE_MARKER 제거 — escape_braces()가 생성하지 않는 패턴이므로 무의미
        # 단일 중괄호가 있는지 확인 (이중 중괄호는 이미 에스케이프됨)
        return "{" in text or "}" in text

    @staticmethod
    def is_already_escaped(text: str) -> bool:
        """
        이미 에스케이프되었는지 확인

        Args:
            text: 검사할 텍스트

        Returns:
            bool: 이미 에스케이프되었으면 True
        """
        if not isinstance(text, str):
            return False

        # [V70] 이중 중괄호 패턴 감지 (여는/닫는 모두 검사)
        has_double_open = "{{" in text
        has_single_open = "{" in text.replace("{{", "")
        has_double_close = "}}" in text
        has_single_close = "}" in text.replace("}}", "")

        # 이중 중괄호만 있고 단일 중괄호가 없으면 이미 에스케이프됨
        return has_double_open and not has_single_open and has_double_close and not has_single_close

    @staticmethod
    def escape_braces(text: Any, force: bool = False) -> str:
        """
        중괄호 에스케이프 (최적화 버전)

        Args:
            text: 에스케이프할 텍스트
            force: True면 중복 검사 없이 강제 에스케이프

        Returns:
            str: 에스케이프된 텍스트
        """
        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        if not text:
            return ""

        # 중복 에스케이프 방지 (force=False 일 때)
        if not force and EscapeUtils.is_already_escaped(text):
            return text

        # 에스케이프 불필요 체크
        if not force and not EscapeUtils.needs_escape(text):
            return text

        return text.replace("{", "{{").replace("}", "}}")

    @staticmethod
    def escape_json_dump(data: Any, ensure_ascii: bool = False) -> str:
        """
        JSON 직렬화 + 에스케이프 통합

        Args:
            data: JSON 직렬화할 데이터
            ensure_ascii: ASCII 강제 여부

        Returns:
            str: 에스케이프된 JSON 문자열
        """
        try:
            json_str = json.dumps(data, ensure_ascii=ensure_ascii)
            return EscapeUtils.escape_braces(json_str)
        except (TypeError, ValueError):
            return EscapeUtils.escape_braces(str(data))

    @staticmethod
    def escape_batch(data_dict: dict[str, Any]) -> dict[str, str]:
        """
        여러 필드를 한 번에 에스케이프

        Args:
            data_dict: 에스케이프할 데이터 딕셔너리

        Returns:
            dict: 에스케이프된 데이터 딕셔너리
        """
        result = {}
        for key, value in data_dict.items():
            if isinstance(value, dict | list):
                result[key] = EscapeUtils.escape_json_dump(value)
            else:
                result[key] = EscapeUtils.escape_braces(value)
        return result

    @staticmethod
    def unescape_braces(text: str) -> str:
        """
        에스케이프 해제 (디버깅/로깅용)

        Args:
            text: 에스케이프 해제할 텍스트

        Returns:
            str: 원본 텍스트
        """
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        return text.replace("{{", "{").replace("}}", "}")


# 편의 함수들
def escape_braces(text: Any, force: bool = False) -> str:
    """에스케이프 함수 (단축형)"""
    return EscapeUtils.escape_braces(text, force)


def escape_json(data: Any, ensure_ascii: bool = False) -> str:
    """JSON 직렬화 + 에스케이프 (단축형)"""
    return EscapeUtils.escape_json_dump(data, ensure_ascii)


def escape_batch(data_dict: dict[str, Any]) -> dict[str, str]:
    """배치 에스케이프 (단축형)"""
    return EscapeUtils.escape_batch(data_dict)


def needs_escape(text: str) -> bool:
    """에스케이프 필요 여부 (단축형)"""
    return EscapeUtils.needs_escape(text)


def is_escaped(text: str) -> bool:
    """에스케이프 여부 확인 (단축형)"""
    return EscapeUtils.is_already_escaped(text)
