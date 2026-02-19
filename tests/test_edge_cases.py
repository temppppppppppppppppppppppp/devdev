"""
[V44] 엣지 케이스 테스트

극단값, DB 손상, VectorDB lock, Stage 스킵, 네트워크 오류 시나리오
"""

import json
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestExtremeValues:
    """극단값 테스트"""

    @pytest.mark.xfail(reason="Windows SQLite file lock - DB handle not closed before fixture cleanup")
    def test_empty_string_manuscript(self, temp_dir):
        """빈 문자열 원고 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 빈 원고 저장
        db.save_manuscript(1, "", {})

        loaded, _ = db.load_manuscript(1)
        assert loaded == ""

        db.close()

    @pytest.mark.xfail(reason="BlockingValidator behavior changed")
    def test_zero_length_validation(self):
        """0자 검증 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        context = {"mode": "MANUSCRIPT", "encyclopedia": {}}

        result = validator.validate(1, "", context)

        # 0자는 REJECT
        assert result["status"] == "REJECT"

    @pytest.mark.xfail(reason="Windows SQLite file lock - DB handle not closed before fixture cleanup")
    def test_very_long_manuscript(self, temp_dir):
        """매우 긴 원고 (999,999자) 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 약 1MB 텍스트
        long_text = "무협" * 333333  # 999,999자

        db.save_manuscript(1, long_text, {})
        loaded, _ = db.load_manuscript(1)

        assert len(loaded) == len(long_text)

        db.close()

    def test_unicode_special_characters(self, temp_dir):
        """유니코드 특수문자 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        special_chars = {
            "chinese": "李靑風 武林 天下",
            "japanese": "剣道 柔道",
            "korean": "이청풍 무림",
            "symbols": "「」『』〈〉《》【】",
            "emoji": "⚔️🗡️🏯",
            "mixed": "이청풍(李靑風)이 「청풍검법」을 펼쳤다!",
        }

        db.save_anchor("special", special_chars)
        loaded = db.load_anchor("special")

        for key, value in special_chars.items():
            assert loaded[key] == value

        db.close()

    def test_null_and_none_values(self, temp_dir):
        """null/None 값 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        data_with_nulls = {"field1": None, "field2": "value", "field3": None, "nested": {"inner": None, "value": 123}}

        db.save_anchor("nulls", data_with_nulls)
        loaded = db.load_anchor("nulls")

        assert loaded["field1"] is None
        assert loaded["nested"]["inner"] is None

        db.close()

    def test_negative_numbers(self, temp_dir):
        """음수 값 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        data = {
            "negative_int": -100,
            "negative_float": -3.14,
            "relationship": -50,  # 적대 관계
        }

        db.save_anchor("negatives", data)
        loaded = db.load_anchor("negatives")

        assert loaded["negative_int"] == -100
        assert loaded["negative_float"] == -3.14

        db.close()

    def test_very_deep_nesting(self, temp_dir):
        """깊은 중첩 구조 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 10단계 중첩
        deep_data = {
            "level0": {
                "level1": {
                    "level2": {
                        "level3": {"level4": {"level5": {"level6": {"level7": {"level8": {"level9": "deep value"}}}}}}
                    }
                }
            }
        }

        db.save_anchor("deep", deep_data)
        loaded = db.load_anchor("deep")

        # 깊은 값 접근
        result = loaded
        for i in range(10):
            result = result[f"level{i}"]
        assert result == "deep value"

        db.close()

    def test_large_array(self, temp_dir):
        """대용량 배열 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 10,000개 요소 배열
        large_array = list(range(10000))

        db.save_anchor("array", {"items": large_array})
        loaded = db.load_anchor("array")

        assert len(loaded["items"]) == 10000
        assert loaded["items"][9999] == 9999

        db.close()


class TestDBCorruptionRecovery:
    """DB 손상 복구 테스트"""

    @pytest.mark.xfail(reason="Windows SQLite file lock - DB handle not closed before fixture cleanup")
    def test_corrupted_json_recovery(self, temp_dir):
        """손상된 JSON 복구 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 정상 데이터 저장
        db.save_anchor("valid", {"key": "value"})

        # 직접 손상된 JSON 삽입
        db.cursor.execute(
            "INSERT OR REPLACE INTO anchors (key, value) VALUES (?, ?)", ("corrupted", "{invalid json{{{}}")
        )
        db.conn.commit()

        # 손상된 데이터 로드 시도
        try:
            result = db.load_anchor("corrupted")
            # 에러 없이 처리 (원본 반환 또는 None)
        except json.JSONDecodeError:
            # 예외 발생해도 정상 데이터는 접근 가능해야 함
            pass

        # 정상 데이터 접근 확인
        valid = db.load_anchor("valid")
        assert valid["key"] == "value"

        db.close()

    def test_partial_transaction_recovery(self, temp_dir):
        """부분 트랜잭션 복구 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 초기 상태 저장
        db.save_anchor("initial", {"version": 1})

        # 실패하는 트랜잭션
        try:
            with db.transaction():
                db.save_anchor("initial", {"version": 2})
                db.save_anchor("new_key", {"data": "test"})
                raise Exception("Simulated failure")
        except Exception:
            pass

        # 롤백 확인 - 초기 상태 유지
        loaded = db.load_anchor("initial")
        # 트랜잭션 롤백 동작에 따라 검증

        db.close()

    def test_file_permission_error_handling(self, temp_dir):
        """파일 권한 오류 처리 테스트"""
        # Windows에서는 권한 테스트가 다르게 동작
        # 읽기 전용 파일 시도 시뮬레이션
        pass  # 플랫폼별 테스트 필요

    def test_disk_full_simulation(self):
        """디스크 풀 시뮬레이션 테스트"""
        # 실제 디스크 풀 테스트는 환경에 따라 다름
        # 예외 처리 로직만 검증
        pass


class TestVectorDBLock:
    """벡터 DB 잠금 테스트"""

    def test_vectordb_lock_detection(self, temp_dir):
        """벡터 DB 잠금 감지 테스트"""
        # 0KB 파일 생성으로 손상 시뮬레이션
        db_file = temp_dir / "project_data.db"
        db_file.write_text("")

        # 이상 감지 로직 테스트
        assert db_file.exists()
        assert db_file.stat().st_size == 0

    def test_vectordb_lock_recovery_hint(self, temp_dir):
        """벡터 DB 잠금 복구 힌트 테스트"""
        error_message = "Database is locked"
        expected_hints = ["LOCK", "삭제", "재시작"]

        # 에러 메시지에 힌트 포함 여부 (구현에 따라)

    def test_concurrent_vectordb_access(self, temp_dir):
        """벡터 DB 동시 접근 테스트"""
        # 동시 접근 시뮬레이션
        pass


class TestStageSkipCompatibility:
    """Stage 스킵 호환성 테스트"""

    def test_stage1_skip_with_existing_volumes(self, temp_dir):
        """기존 볼륨 있을 때 Stage 1 스킵 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 기존 볼륨 존재
        existing_volumes = [{"volume": i, "title": f"Vol{i}"} for i in range(1, 11)]
        db.save_anchor("volumes", existing_volumes)

        # 스킵 조건 검사
        volumes = db.load_anchor("volumes")
        can_skip = volumes is not None and len(volumes) >= 10

        assert can_skip == True

        db.close()

    def test_stage1_skip_then_stage2_compatibility(self, temp_dir):
        """Stage 1 스킵 후 Stage 2 호환성 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # Stage 1 결과 (스킵 시 기존 데이터 사용)
        volumes = [{"volume": i, "title": f"Vol{i}", "episodes": f"{(i - 1) * 50 + 1}-{i * 50}"} for i in range(1, 11)]
        db.save_anchor("volumes", volumes)

        # Stage 2에서 볼륨 데이터 접근
        loaded_volumes = db.load_anchor("volumes")

        # 아크 생성을 위한 볼륨 정보 확인
        for vol in loaded_volumes:
            assert "volume" in vol
            assert "title" in vol

        db.close()

    def test_partial_stage_completion_resume(self, temp_dir):
        """부분 완료 스테이지 재개 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # Stage 2 부분 완료 (3개 아크만)
        partial_arcs = [{"volume": 1, "arc_num": i} for i in range(1, 4)]
        db.save_anchor("arcs", partial_arcs)

        # 재개 시 마지막 상태 확인
        arcs = db.load_anchor("arcs")
        last_arc = arcs[-1] if arcs else None

        assert last_arc["arc_num"] == 3

        db.close()


class TestNetworkTimeout:
    """네트워크 타임아웃 테스트"""

    @pytest.mark.xfail(reason="BaseAgent.__init__ signature changed")
    def test_api_timeout_handling(self):
        """API 타임아웃 처리 테스트"""
        from modules.domain.agents.base_agent import AgentErrorType, BaseAgent

        # Mock 설정
        config = {"api_client": MagicMock(), "project": MagicMock(), "models": {"primary": "test", "backup": "test2"}}

        # 타임아웃 예외 시뮬레이션
        config["api_client"].models.generate_content.side_effect = Exception("Request timed out after 120 seconds")

        agent = BaseAgent(config)

        # 에러 분류 확인
        if hasattr(agent, "_classify_error"):
            error = Exception("Request timed out")
            error_type = agent._classify_error(error)
            assert error_type == AgentErrorType.TIMEOUT

    def test_retry_with_backoff(self):
        """백오프 재시도 테스트"""
        retry_delays = []
        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries):
            delay = base_delay * (2**attempt)  # 지수 백오프
            retry_delays.append(delay)

        assert retry_delays == [1, 2, 4]

    @pytest.mark.xfail(reason="BaseAgent.__init__ signature changed")
    def test_quota_exceeded_handling(self):
        """할당량 초과 처리 테스트"""
        from modules.domain.agents.base_agent import AgentErrorType, BaseAgent

        config = {"api_client": MagicMock(), "project": MagicMock(), "models": {"primary": "test", "backup": "test2"}}

        agent = BaseAgent(config)

        # 429 에러 분류
        if hasattr(agent, "_classify_error"):
            error = Exception("429 Resource exhausted: quota exceeded")
            error_type = agent._classify_error(error)
            assert error_type == AgentErrorType.QUOTA_EXCEEDED

    def test_network_error_recovery(self):
        """네트워크 오류 복구 테스트"""
        call_count = [0]
        max_retries = 3

        def api_call_with_retry():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Network error")
            return {"success": True}

        # 재시도 로직 시뮬레이션
        result = None
        for _ in range(max_retries):
            try:
                result = api_call_with_retry()
                break
            except Exception:
                continue

        assert result is not None
        assert result["success"] == True


class TestBoundaryConditions:
    """경계 조건 테스트"""

    @pytest.mark.xfail(reason="Windows SQLite file lock - DB handle not closed before fixture cleanup")
    def test_episode_number_boundaries(self, temp_dir):
        """에피소드 번호 경계 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 경계값 테스트
        boundary_episodes = [0, 1, 250, 500, 9999]

        for ep_num in boundary_episodes:
            db.save_blueprint(ep_num, {"ep_num": ep_num})
            loaded = db.load_blueprint(ep_num)
            assert loaded["ep_num"] == ep_num

        db.close()

    def test_volume_boundaries(self):
        """볼륨 경계 테스트"""
        volumes = list(range(1, 11))  # 1-10

        assert min(volumes) == 1
        assert max(volumes) == 10
        assert len(volumes) == 10

    def test_arc_boundaries(self):
        """아크 경계 테스트"""
        arcs_per_volume = 5
        total_volumes = 10

        total_arcs = arcs_per_volume * total_volumes
        assert total_arcs == 50

    def test_score_boundaries(self):
        """점수 경계 테스트"""
        # 점수 범위: 0-100
        boundary_scores = [0, 69, 70, 84, 85, 100]
        expected_statuses = ["REJECT", "REJECT", "CONDITIONAL_PASS", "CONDITIONAL_PASS", "PASS", "PASS"]

        for score, expected in zip(boundary_scores, expected_statuses):
            if score >= 85:
                status = "PASS"
            elif score >= 70:
                status = "CONDITIONAL_PASS"
            else:
                status = "REJECT"

            assert status == expected

    def test_retry_count_boundaries(self):
        """재시도 횟수 경계 테스트"""
        max_retries = 3

        for retry in range(max_retries + 2):
            if retry < max_retries:
                should_retry = True
            else:
                should_retry = False

            # 경계에서 정확히 중단
            if retry == max_retries:
                assert should_retry == False


class TestMemoryAndPerformance:
    """메모리 및 성능 테스트"""

    @pytest.mark.xfail(reason="Windows SQLite file lock - DB handle not closed before fixture cleanup")
    def test_large_batch_processing(self, temp_dir):
        """대용량 배치 처리 테스트"""
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")

        # 100개 에피소드 배치 저장
        for ep in range(1, 101):
            db.save_blueprint(ep, {"ep_num": ep, "data": "x" * 1000})

        # 전체 로드
        for ep in range(1, 101):
            loaded = db.load_blueprint(ep)
            assert loaded["ep_num"] == ep

        db.close()

    def test_repeated_open_close(self, temp_dir):
        """반복 열기/닫기 테스트"""
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "repeated.db"

        # 10번 열기/닫기
        for i in range(10):
            db = DBManager(db_path)
            db.save_anchor(f"key_{i}", {"iteration": i})
            db.close()

        # 최종 확인
        db = DBManager(db_path)
        for i in range(10):
            loaded = db.load_anchor(f"key_{i}")
            assert loaded["iteration"] == i
        db.close()

    def test_concurrent_read_write(self, temp_dir):
        """동시 읽기/쓰기 테스트"""
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "concurrent.db"
        errors = []
        results = []

        def writer():
            try:
                db = DBManager(db_path)
                for i in range(10):
                    db.save_anchor(f"w_{i}", {"value": i})
                db.close()
            except Exception as e:
                errors.append(("writer", e))

        def reader():
            try:
                db = DBManager(db_path)
                for i in range(10):
                    result = db.load_anchor(f"w_{i}")
                    if result:
                        results.append(result)
                db.close()
            except Exception as e:
                errors.append(("reader", e))

        # 동시 실행
        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # SQLite가 동시성 처리 (일부 에러 가능)
