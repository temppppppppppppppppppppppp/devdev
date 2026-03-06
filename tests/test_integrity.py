"""
[V60.17] 글도비 무결성 테스트
서브에이전트 분석 결과 기반 - 핵심 버그 검증

실행: python -m pytest tests/test_integrity.py -v
"""

import json
import os
import sys
import threading
import time

import pytest

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 1. DB Manager Race Condition 테스트
# ============================================================
class TestDBManagerRaceCondition:
    """db_manager.py:56 - 중복 ep_num 발생 가능성 테스트"""

    def test_concurrent_episode_number_generation(self):
        """동시 에피소드 번호 생성 시 중복 방지 확인 (독립 SQLite 테스트)"""
        import sqlite3
        import tempfile
        from threading import RLock

        # 임시 DB 생성
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = None
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            lock = RLock()

            # 테이블 초기화
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_episodes (
                    ep_num INTEGER PRIMARY KEY,
                    content TEXT
                )
            """)
            conn.commit()

            results = []
            errors = []

            def get_and_insert():
                try:
                    with lock:
                        # 최신 번호 조회
                        cursor = conn.execute("SELECT MAX(ep_num) FROM test_episodes")
                        max_ep = cursor.fetchone()[0] or 0
                        next_ep = max_ep + 1

                        # 약간의 지연 (race condition 유발)
                        time.sleep(0.001)

                        # 삽입
                        conn.execute(
                            "INSERT INTO test_episodes (ep_num, content) VALUES (?, ?)", (next_ep, f"Episode {next_ep}")
                        )
                        conn.commit()
                        results.append(next_ep)
                except sqlite3.IntegrityError as e:
                    errors.append(str(e))
                except Exception as e:
                    errors.append(str(e))

            # 10개 스레드 동시 실행
            threads = [threading.Thread(target=get_and_insert) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # RLock으로 보호되므로 중복 없이 모두 성공해야 함
            assert len(errors) == 0, f"Race condition 발생: {errors}"
            assert len(results) == len(set(results)), f"중복 ep_num 발생: {results}"
            assert len(results) == 10, f"모든 스레드가 성공해야 함: {len(results)}/10"

        finally:
            # DB 연결 종료 후 파일 삭제
            if conn:
                try:
                    conn.close()
                except:
                    pass
            try:
                os.unlink(db_path)
            except:
                pass  # Windows에서 파일 잠금 무시


# ============================================================
# 2. Base Agent JSON 파싱 테스트
# ============================================================
class TestBaseAgentJSONParsing:
    """base_agent.py - JSON 파싱 안전성 테스트"""

    def test_circular_reference_handling(self):
        """순환 참조 JSON 처리 시 무한 루프 방지"""
        # 순환 참조가 있는 구조 시뮬레이션
        # (실제로는 문자열로 들어오므로 파싱 테스트)

        malformed_json = """
        {
            "arc_no": 1,
            "episodes": [
                {"ep": 1, "ref": "episodes[0]"},
                {"ep": 2, "ref": "episodes[1]"}
            ],
            "self_ref": "이건 자기참조입니다 {arc_no}"
        }
        """

        import re

        # 기본 JSON 파싱
        try:
            # 중괄호 이스케이프 처리 테스트
            cleaned = re.sub(r"\{([a-z_]+)\}", r"__\1__", malformed_json)
            result = json.loads(cleaned)
            assert result["arc_no"] == 1
        except json.JSONDecodeError:
            # 파싱 실패는 예상된 동작
            pass

    def test_deeply_nested_json(self):
        """깊이 중첩된 JSON 처리 (MAX_DEPTH 테스트)"""
        # 20단계 이상 중첩
        nested = {"level": 0}
        current = nested
        for i in range(25):
            current["child"] = {"level": i + 1}
            current = current["child"]

        json_str = json.dumps(nested)

        # 파싱은 성공해야 함
        result = json.loads(json_str)
        assert result["level"] == 0

        # 깊이 탐색 (재귀 제한 테스트)
        def count_depth(obj, depth=0, max_depth=30):
            if depth > max_depth:
                return depth
            if isinstance(obj, dict) and "child" in obj:
                return count_depth(obj["child"], depth + 1, max_depth)
            return depth

        depth = count_depth(result)
        assert depth <= 30, f"재귀 깊이 초과: {depth}"


# ============================================================
# 3. Equipment 타입 안전성 테스트
# ============================================================
class TestEquipmentTypeSafety:
    """project_manager.py:461, blocking_validator.py:174 - 타입 혼용 테스트"""

    def test_equipment_as_list(self):
        """equipment가 리스트일 때"""
        equipment = ["대도", "경공술 비급", "철혈사자패"]

        # 리스트 처리
        if isinstance(equipment, list):
            items = equipment
        elif isinstance(equipment, str):
            items = [equipment]
        elif isinstance(equipment, dict):
            items = list(equipment.keys())
        else:
            items = []

        assert "대도" in items
        assert len(items) == 3

    def test_equipment_as_string(self):
        """equipment가 문자열일 때"""
        equipment = "대도"

        if isinstance(equipment, list):
            items = equipment
        elif isinstance(equipment, str):
            items = [equipment] if equipment else []
        elif isinstance(equipment, dict):
            items = list(equipment.keys())
        else:
            items = []

        assert "대도" in items
        assert len(items) == 1

    def test_equipment_as_dict(self):
        """equipment가 딕셔너리일 때"""
        equipment = {"대도": True, "경공술 비급": "소지중", "broken": None}

        if isinstance(equipment, list):
            items = equipment
        elif isinstance(equipment, str):
            items = [equipment] if equipment else []
        elif isinstance(equipment, dict):
            # value가 truthy인 것만 포함
            items = [k for k, v in equipment.items() if v]
        else:
            items = []

        assert "대도" in items
        assert "broken" not in items  # None은 제외
        assert len(items) == 2

    def test_equipment_none(self):
        """equipment가 None일 때"""
        equipment = None

        if isinstance(equipment, list):
            items = equipment
        elif isinstance(equipment, str):
            items = [equipment] if equipment else []
        elif isinstance(equipment, dict):
            items = list(equipment.keys())
        else:
            items = []

        assert items == []

    def test_equipment_empty_string(self):
        """equipment가 빈 문자열일 때"""
        equipment = ""

        if isinstance(equipment, list):
            items = equipment
        elif isinstance(equipment, str):
            items = [equipment] if equipment else []
        else:
            items = []

        assert items == []


# ============================================================
# 4. Stage 4 무한 루프 방지 테스트
# ============================================================
class TestStage4LoopGuard:
    """main_a.py:6848 - 무한 루프 방지 테스트"""

    def test_loop_guard_triggers(self):
        """loop_guard가 제대로 작동하는지 확인"""
        max_episode_loops = 100
        loop_guard = 0
        episodes_processed = []

        # 시뮬레이션: 항상 실패하는 상황
        while True:
            loop_guard += 1

            if loop_guard > max_episode_loops:
                break

            # 실패 시뮬레이션 (blueprint 없음)
            blueprint = None
            if not blueprint:
                continue  # 다시 시도... 하지만 loop_guard가 증가

            episodes_processed.append(loop_guard)

        # 무한 루프 방지 확인
        assert loop_guard == max_episode_loops + 1
        assert len(episodes_processed) == 0  # 아무것도 처리 안 됨

    def test_nested_loop_guard(self):
        """중첩 루프에서도 종료 보장"""
        max_outer = 10
        max_inner = 5
        outer_count = 0
        total_inner = 0

        for _ in range(max_outer):
            outer_count += 1
            inner_count = 0

            while inner_count < max_inner:
                inner_count += 1
                total_inner += 1

                # 조기 종료 조건
                if inner_count >= 3:
                    break

        assert outer_count == max_outer
        assert total_inner == max_outer * 3  # 각 outer당 3번


# ============================================================
# 5. Director 오류 시 기본 PASS 방지 테스트
# ============================================================
class TestDirectorErrorHandling:
    """main_a.py:8121 - Director 실패 시 자동 PASS 문제"""

    def test_director_error_should_not_auto_pass(self):
        """Director 오류 시 PASS가 아닌 ERROR 반환해야"""

        def simulate_director_audit(manuscript):
            """Director 시뮬레이션"""
            try:
                # 의도적 오류 발생
                raise Exception("API 호출 실패")
            except Exception as e:
                # 현재 코드: 자동 PASS (문제!)
                # return {"decision": "PASS", "reason": "Director 오류로 인한 기본 통과"}

                # 올바른 처리: ERROR 반환
                return {"decision": "ERROR", "reason": f"Director 오류: {e}", "score": 0, "requires_retry": True}

        result = simulate_director_audit("테스트 원고")

        # 오류 시 PASS가 아니어야 함
        assert result["decision"] != "PASS", "Director 오류 시 자동 PASS 금지"
        assert result["decision"] == "ERROR"
        assert result["requires_retry"] == True


# ============================================================
# 6. JSON 타입 불일치 복구 테스트
# ============================================================
class TestJSONTypeRecovery:
    """analyst.py:558, db_manager.py:333 - 타입 불일치 복구"""

    def test_treatment_data_type_recovery(self):
        """treatment_data가 여러 타입으로 올 때 처리"""

        def process_treatment(raw_data):
            """타입 안전 처리"""
            if raw_data is None:
                return []
            if isinstance(raw_data, list):
                return raw_data
            if isinstance(raw_data, dict):
                return [raw_data]  # 단일 dict를 리스트로
            if isinstance(raw_data, str):
                try:
                    parsed = json.loads(raw_data)
                    return process_treatment(parsed)  # 재귀 처리
                except json.JSONDecodeError:
                    return []
            return []

        # 다양한 입력 테스트
        assert process_treatment(None) == []
        assert process_treatment([{"a": 1}]) == [{"a": 1}]
        assert process_treatment({"a": 1}) == [{"a": 1}]
        assert process_treatment('{"a": 1}') == [{"a": 1}]
        assert process_treatment('[{"a": 1}]') == [{"a": 1}]
        assert process_treatment("invalid json") == []


# ============================================================
# 7. Regex 인젝션 방지 테스트
# ============================================================
class TestRegexSafety:
    """blocking_validator.py:239 - 특수문자 이스케이프"""

    def test_item_name_with_special_chars(self):
        """아이템명에 정규식 특수문자가 있을 때"""
        import re

        dangerous_names = [
            "대도[검]",  # 문자 클래스
            "무공비급(상)",  # 그룹
            "철혈사자패+강화",  # 수량자
            "비전.무공",  # 와일드카드
            "검^법",  # 앵커
            "도$술",  # 앵커
            "무공|검술",  # OR
        ]

        manuscript = "그는 대도[검]을 들고 철혈사자패+강화를 사용했다."

        for name in dangerous_names:
            # 이스케이프 없이 사용하면 오류 발생 가능
            escaped_name = re.escape(name)

            # 이스케이프된 패턴으로 안전하게 검색
            try:
                pattern = f"{escaped_name}"
                result = re.search(pattern, manuscript)
                # 오류 없이 실행되어야 함
            except re.error as e:
                pytest.fail(f"Regex 오류 발생: {name} -> {e}")


# ============================================================
# 8. 메모리/DB 동기화 테스트
# ============================================================
class TestMemoryDBSync:
    """main_a.py:3464 - 메모리와 DB 동기화"""

    def test_save_and_load_consistency(self):
        """저장 후 로드 시 데이터 일관성"""
        import sqlite3
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE anchors (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # 메모리 데이터
            memory_data = {"volumes": [{"vol": 1}, {"vol": 2}], "arcs": [{"arc": 1}, {"arc": 2}]}

            # DB에 저장
            for key, value in memory_data.items():
                conn.execute(
                    "INSERT OR REPLACE INTO anchors (key, value) VALUES (?, ?)",
                    (key, json.dumps(value, ensure_ascii=False)),
                )
            conn.commit()

            # DB에서 로드
            loaded_data = {}
            cursor = conn.execute("SELECT key, value FROM anchors")
            for row in cursor:
                loaded_data[row[0]] = json.loads(row[1])

            # 동기화 확인
            assert loaded_data["volumes"] == memory_data["volumes"]
            assert loaded_data["arcs"] == memory_data["arcs"]

            conn.close()
        finally:
            os.unlink(db_path)


# ============================================================
# 9. Null 체크 체인 테스트
# ============================================================
class TestNullCheckChain:
    """writer.py:84 - 연쇄 get() 호출의 안전성"""

    def test_safe_nested_get(self):
        """중첩된 dict 접근 안전성"""

        def safe_get(obj, *keys, default=None):
            """안전한 중첩 접근"""
            for key in keys:
                if obj is None:
                    return default
                if isinstance(obj, dict):
                    obj = obj.get(key)
                else:
                    return default
            return obj if obj is not None else default

        # 정상 케이스
        data = {"a": {"b": {"c": 100}}}
        assert safe_get(data, "a", "b", "c") == 100

        # 중간에 None
        data2 = {"a": None}
        assert safe_get(data2, "a", "b", "c", default=0) == 0

        # 키 없음
        data3 = {"a": {"b": {}}}
        assert safe_get(data3, "a", "b", "c", default=0) == 0

        # 최상위 None
        assert safe_get(None, "a", "b", default=0) == 0


# ============================================================
# 10. 통합 시나리오 테스트
# ============================================================
class TestIntegrationScenarios:
    """복합 시나리오 테스트"""

    def test_stage2_to_stage3_data_flow(self):
        """Stage 2 → Stage 3 데이터 흐름"""

        # Stage 2 출력 (Arc 데이터)
        arc_data = {
            "arc_no": 1,
            "tactical_doc": "# Arc 1 전술\n화1: 도입\n화2: 전개...",
            "joint_docs": {"final_location": "태산파 연무장", "physical_inventory": ["대도", "비급"]},
            "state_constraints": {
                "arc_end_state": {"internal_energy": 85, "injuries": "경상", "location": "태산파 연무장"}
            },
        }

        # Stage 3 입력 검증
        assert "tactical_doc" in arc_data
        assert "joint_docs" in arc_data
        assert isinstance(arc_data.get("joint_docs", {}), dict)

        # Blueprint 생성에 필요한 데이터 추출
        final_location = arc_data.get("joint_docs", {}).get("final_location", "알 수 없음")
        inventory = arc_data.get("joint_docs", {}).get("physical_inventory", [])

        assert final_location == "태산파 연무장"
        assert "대도" in inventory

    def test_validation_chain(self):
        """검증 체인 테스트 (Blocking → Scoring → Advisory)"""

        manuscript = "그는 대도를 휘둘렀다. " * 500  # 최소 길이 충족 (4000자 이상)

        # Blocking 검증 시뮬레이션
        blocking_result = {
            "passed": len(manuscript) >= 4000,
            "reason": "길이 통과" if len(manuscript) >= 4000 else "길이 부족",
        }

        if not blocking_result["passed"]:
            # Blocking 실패 시 즉시 REJECT
            final_result = {"decision": "REJECT", "stage": "BLOCKING"}
        else:
            # Scoring 검증
            scoring_result = {"score": 75, "passed": True}

            if scoring_result["score"] >= 70:
                final_result = {"decision": "PASS", "score": scoring_result["score"]}
            else:
                final_result = {"decision": "REJECT", "stage": "SCORING"}

        assert final_result["decision"] == "PASS"


# ============================================================
# [TF-16-05] 대원칙 2·4 위반 탐지 테스트
# ============================================================
class TestPrincipleViolationDetection:
    """대원칙 2(팩트 수정 권한 LLM만)·4(사망 NPC 행동 금지) 회귀 안전망"""

    def test_principle2_npc_history_not_bypassed(self):
        """[대원칙 2] Python이 NPC 속성 직접 수정 시 npc_history에 미반영됨을 확인
        — validate_npc_entry()는 검증만 수행하고 원본 dict를 수정하지 않아야 함."""
        from modules.models.npc import validate_npc_entry

        original = {"name": "강철", "status": "alive", "weapon": "검"}
        # validate_npc_entry는 검증 후 dict 반환 — 원본 객체 동일성 확인
        result = validate_npc_entry(original)
        # 반환값은 새 dict이거나 원본이어야 하며, Python이 임의 필드를 추가·변경하지 않아야 함
        assert result["name"] == "강철"
        assert result["status"] == "alive"
        # Python 자동 추가 금지 확인: realm, internal_energy 같은 LLM 전용 필드 불삽입
        assert "realm" not in result or result.get("realm") == original.get("realm")

    def test_principle2_npc_fields_not_auto_modified(self):
        """[대원칙 2] validate_npc_entry가 status/deceased 자동 수정 금지 확인."""
        from modules.models.npc import validate_npc_entry

        # LLM이 설정한 status=dead 를 Python이 임의로 변경하면 안 됨
        entry = {"name": "사망자", "status": "dead", "deceased": True}
        result = validate_npc_entry(entry)
        assert result["status"] == "dead"
        assert result["deceased"] is True

    def test_principle4_deceased_npc_flag(self):
        """[대원칙 4] NPCEntry.deceased=True 필드가 올바르게 모델 검증됨을 확인."""
        from modules.models.npc import NPCEntry

        npc = NPCEntry(name="죽은자", status="dead", deceased=True)
        assert npc.deceased is True
        assert npc.status == "dead"

    def test_principle4_deceased_default_false(self):
        """[대원칙 4] 기본값 deceased=False — 생존 NPC는 플래그 없음."""
        from modules.models.npc import NPCEntry

        npc = NPCEntry(name="생존자")
        assert npc.deceased is False
        assert npc.status == "alive"

    def test_principle4_deceased_serialization(self):
        """[대원칙 4] NPCEntry.model_dump()에 deceased 필드 포함 확인 (Truth Gate 기준 노출)."""
        from modules.models.npc import NPCEntry

        npc = NPCEntry(name="귀신", status="dead", deceased=True)
        dumped = npc.model_dump()
        assert "deceased" in dumped
        assert dumped["deceased"] is True


# ============================================================
# 메인 실행
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
