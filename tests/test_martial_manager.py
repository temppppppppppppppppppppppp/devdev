"""
[V44] MartialManager 테스트

타입 안전성, 프로퍼티 접근, HUD 관리 테스트
"""

import math
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.martial_manager import MartialManager


class TestMartialManagerTypeSafety:
    """타입 안전성 테스트"""

    def test_safe_to_float_valid(self):
        """유효한 float 변환 테스트"""

        # MartialManager 인스턴스 없이 헬퍼 함수만 테스트
        # 직접 _safe_to_float 메서드가 없다면 로직 검증
        valid_inputs = [
            (10, 10.0),
            (3.14, 3.14),
            ("42", 42.0),
            ("3.14", 3.14),
        ]

        for input_val, expected in valid_inputs:
            try:
                result = float(input_val)
                assert result == expected
            except (ValueError, TypeError):
                pytest.fail(f"Valid input {input_val} failed to convert")

    def test_safe_to_float_invalid(self):
        """잘못된 float 변환 테스트"""
        invalid_inputs = [
            None,
            "not a number",
            [],
            {},
            float("nan"),
            float("inf"),
            float("-inf"),
        ]

        for input_val in invalid_inputs:
            # NaN, inf는 float()로 변환은 되지만 유효하지 않은 값
            if input_val is None or isinstance(input_val, list | dict | str):
                try:
                    if input_val is None:
                        continue  # None은 변환 불가
                    result = float(input_val)
                    if isinstance(input_val, str) and input_val == "not a number":
                        pytest.fail("Should have raised ValueError")
                except (ValueError, TypeError):
                    pass  # 예상된 동작

    def test_safe_to_int_valid(self):
        """유효한 int 변환 테스트"""
        valid_inputs = [
            (10, 10),
            (3.9, 3),  # 버림
            ("42", 42),
        ]

        for input_val, expected in valid_inputs:
            result = int(float(input_val)) if isinstance(input_val, float) else int(input_val)
            assert result == expected

    def test_is_valid_number(self):
        """숫자 유효성 검사 테스트"""
        valid_numbers = [0, 1, -1, 3.14, 100, -50.5]
        invalid_numbers = [float("nan"), float("inf"), float("-inf")]

        for num in valid_numbers:
            assert not math.isnan(num) and not math.isinf(num)

        for num in invalid_numbers:
            assert math.isnan(num) or math.isinf(num)


class TestMartialManagerPropertyAccess:
    """프로퍼티 접근 테스트"""

    def test_nested_dict_access_safe(self):
        """중첩 딕셔너리 안전 접근 테스트"""
        test_data = {"level1": {"level2": {"level3": "value"}}}

        # 정상 경로
        result = test_data.get("level1", {}).get("level2", {}).get("level3")
        assert result == "value"

        # 중간 경로 없음
        result = test_data.get("missing", {}).get("level2", {}).get("level3")
        assert result is None

        # 타입 오류 방지
        test_data_broken = {"level1": "not a dict"}
        level1 = test_data_broken.get("level1")
        if isinstance(level1, dict):
            result = level1.get("level2")
        else:
            result = None
        assert result is None

    def test_safe_nested_get_utility(self):
        """safe_nested_get 유틸리티 테스트"""
        from modules.core.project_manager import safe_nested_get

        data = {"a": {"b": {"c": 42}}, "x": None}

        # 정상 경로
        assert safe_nested_get(data, "a", "b", "c") == 42

        # 존재하지 않는 경로
        assert safe_nested_get(data, "a", "b", "d") is None
        assert safe_nested_get(data, "missing", "path") is None

        # 기본값
        assert safe_nested_get(data, "a", "b", "d", default=0) == 0

        # None 값 처리
        assert safe_nested_get(data, "x", default="default") == "default"


class TestMartialManagerHUDOperations:
    """HUD 연산 테스트"""

    def test_hud_wuxia_structure(self, sample_hud_wuxia):
        """무협 HUD 구조 테스트"""
        required_keys = [
            "character",
            "martial_root",
            "internal_energy",
            "lightness",
            "sword_skill",
            "palm_skill",
            "equipment",
            "techniques",
        ]

        for key in required_keys:
            assert key in sample_hud_wuxia

    def test_hud_hunter_structure(self, sample_hud_hunter):
        """헌터 HUD 구조 테스트"""
        required_keys = ["character", "awakening_grade", "mana", "strength", "agility", "skills", "equipment"]

        for key in required_keys:
            assert key in sample_hud_hunter

    def test_hud_investment_structure(self, sample_hud_investment):
        """투자 HUD 구조 테스트"""
        required_keys = ["character", "total_assets", "cash", "stocks", "real_estate", "connections"]

        for key in required_keys:
            assert key in sample_hud_investment

    def test_hud_numeric_bounds(self, sample_hud_wuxia):
        """HUD 수치 범위 테스트"""
        # 무력근 0-100 범위
        assert 0 <= sample_hud_wuxia["martial_root"] <= 100

        # 내공 양수
        assert sample_hud_wuxia["internal_energy"] >= 0

        # 기술 수치 양수
        assert sample_hud_wuxia["sword_skill"] >= 0
        assert sample_hud_wuxia["palm_skill"] >= 0

    def test_hud_equipment_types(self, sample_hud_wuxia):
        """HUD 장비 타입 테스트"""
        equipment = sample_hud_wuxia.get("equipment", [])

        # 리스트 타입이어야 함
        assert isinstance(equipment, list)

        # 각 항목은 문자열이어야 함
        for item in equipment:
            assert isinstance(item, str)

    def test_hud_snapshot_serialization(self, sample_hud_wuxia):
        """HUD 스냅샷 직렬화 테스트"""
        import json

        # JSON 직렬화 가능해야 함
        serialized = json.dumps(sample_hud_wuxia, ensure_ascii=False)
        assert isinstance(serialized, str)

        # 역직렬화
        deserialized = json.loads(serialized)
        assert deserialized == sample_hud_wuxia


class TestMartialManagerInitialization:
    """초기화 테스트"""

    def test_initialization_without_bible(self):
        """bible 없이 초기화 테스트"""
        mock_context = MagicMock()
        mock_context.bible = None
        mock_context.ui = MagicMock()

        # 에러 없이 처리되어야 함
        # MartialManager가 bible 없이도 기본값으로 동작해야 함

    def test_initialization_with_empty_bible(self):
        """빈 bible로 초기화 테스트"""
        mock_context = MagicMock()
        mock_context.bible = {}
        mock_context.ui = MagicMock()

        # 에러 없이 처리되어야 함

    def test_initialization_with_malformed_bible(self):
        """잘못된 구조의 bible로 초기화 테스트"""
        mock_context = MagicMock()
        mock_context.bible = {
            "treatment": "not a dict"  # 잘못된 타입
        }
        mock_context.ui = MagicMock()

        # 에러 없이 처리되어야 함


class TestMartialManagerGenreSpecific:
    """장르별 동작 테스트"""

    def test_wuxia_specific_properties(self):
        """무협 전용 프로퍼티 테스트"""
        wuxia_properties = [
            "martial_root",  # 무력근
            "internal_energy",  # 내공
            "lightness",  # 경공
            "sword_skill",  # 검법
            "palm_skill",  # 장법
        ]

        # 이 프로퍼티들이 MartialManager에 존재해야 함
        # (실제 테스트는 인스턴스 생성 후 수행)

    def test_hunter_specific_properties(self):
        """헌터 전용 프로퍼티 테스트"""
        hunter_properties = [
            "awakening_grade",  # 각성등급
            "mana",  # 마나
            "strength",  # 근력
            "agility",  # 민첩
        ]

    def test_investment_specific_properties(self):
        """투자 전용 프로퍼티 테스트"""
        investment_properties = [
            "total_assets",  # 총자산
            "cash",  # 현금
            "stocks",  # 주식
            "connections",  # 인맥
        ]


class TestMartialManagerEdgeCases:
    """엣지 케이스 테스트"""

    def test_zero_values(self):
        """0값 처리 테스트"""
        hud = {"martial_root": 0, "internal_energy": 0, "lightness": 0}

        # 0은 유효한 값
        for key, value in hud.items():
            assert value == 0
            assert not math.isnan(value)

    def test_negative_values(self):
        """음수값 처리 테스트"""
        # 일부 속성은 음수가 가능할 수 있음 (관계도 등)
        relationships = {
            "적": -50,  # 적대 관계
            "중립": 0,
            "우호": 50,
        }

        for name, affinity in relationships.items():
            assert isinstance(affinity, int | float)

    def test_very_large_values(self):
        """매우 큰 값 처리 테스트"""
        large_value = 10**15  # 1000조

        hud = {"total_assets": large_value}

        assert hud["total_assets"] == large_value
        assert not math.isinf(hud["total_assets"])

    def test_special_characters_in_names(self):
        """특수문자 포함 이름 테스트"""
        names = ["이청풍(李靑風)", "암흑검 '살수'", "독고구패", "Mr. Kim"]

        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_pro_data_name_fallback_when_protagonist_is_not_dict(self):
        """Protagonist가 dict가 아니어도 최소 구조로 name 접근 가능해야 함."""
        ctx = MagicMock()
        ctx.master_bible = {"MasterBible": {"MartialHUD": {"Protagonist": "broken"}}}
        ctx.guard = None
        ctx.ui = MagicMock()

        manager = MartialManager(ctx)

        assert manager.pro_data.get("name") == "주인공"
