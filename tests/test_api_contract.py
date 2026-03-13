"""
T8 pytest 게이트 — API 계약/오류코드/분기 회귀 테스트

참조 문서:
  docs/implementation/prompt-map-v1.json   (T1 동결)
  docs/implementation/api-contract-v1.yaml (T2 동결)
  docs/implementation/event-schema-v1.json (T3 동결)

BE 서버가 미구현 단계이므로 계약 규칙을 RouterStub에 내장해
오프라인으로 검증한다. 서버 구현 후 HTTP 호환 테스트로 교체 가능.

오류코드 커버 (api-contract-v1.yaml ErrorEnvelope.code enum):
  INVALID_KEY                       TC-KEY-001
  SUB_KEY_REQUIRED                  TC-KEY-002
  SUB_KEY_NOT_ALLOWED               TC-KEY-003
  INVALID_SUB_KEY                   TC-KEY-004
  RUN_ALREADY_ACTIVE                TC-DUP-001
  RISK_APPROVAL_REQUIRED            TC-RISK-001
  RISK_APPROVAL_EXPIRED             TC-RISK-002
  RISK_APPROVAL_DUAL_CONTROL_REQUIRED TC-RISK-003
  INVALID_PROMPT_ID                 TC-PRM-001
  PROMPT_ALREADY_RESOLVED           TC-PRM-002
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


# ---------------------------------------------------------------------------
# 계약 상수 (api-contract-v1.yaml / prompt-map-v1.json 기준)
# ---------------------------------------------------------------------------

VALID_KEYS = {"0", "1", "2", "3", "4", "5", "6", "7", "44", "77", "88", "99"}

# key=0만 sub_key 필요, 나머지는 불허
KEY_REQUIRES_SUB_KEY = {"0"}
KEY_FORBIDDEN_SUB_KEY = VALID_KEYS - KEY_REQUIRES_SUB_KEY

KEY_0_ALLOWED_SUB_KEYS = {"0", "1", "2", "3", "4", "5", "6", "7"}

RISK_KEYS = {"44", "77", "88", "99"}

APPROVAL_TTL_SEC = 300  # 5분; 테스트에서는 짧게 조정 가능


# ---------------------------------------------------------------------------
# 스텁 데이터 모델
# ---------------------------------------------------------------------------

@dataclass
class Approval:
    approval_id: str
    approvers: list[str]
    issued_at: float = field(default_factory=time.time)
    ttl: float = APPROVAL_TTL_SEC

    def is_expired(self) -> bool:
        return (time.time() - self.issued_at) > self.ttl

    def has_dual_control(self) -> bool:
        return len(set(self.approvers)) >= 2


@dataclass
class Prompt:
    prompt_id: str
    step_id: str
    resolved: bool = False
    value: Any = None
    source: str = "default"


@dataclass
class RunState:
    run_id: str
    status: str = "running"  # idle | starting | running | stopping | error
    prompts: dict[str, Prompt] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# RouterStub — 계약 규칙 구현체
# ---------------------------------------------------------------------------

class RouterStub:
    """api-contract-v1.yaml 계약을 구현한 오프라인 스텁."""

    def __init__(self) -> None:
        self._active_run: Optional[RunState] = None
        self._approvals: dict[str, Approval] = {}

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────

    def _ok(self, run_id: str | None = None, code: str = "OK",
            message: str = "ok", data: Any = None) -> dict:
        result = {"ok": True, "code": code, "message": message}
        if run_id is not None:
            result["run_id"] = run_id
        if data is not None:
            result["data"] = data
        return result

    def _err(self, code: str, message: str, status: int = 400) -> dict:
        return {"ok": False, "code": code, "message": message, "status": status}

    # ── POST /run ──────────────────────────────────────────────────────────

    def post_run(self, key: str, sub_key: str | None = None,
                 approval_id: str | None = None) -> dict:
        # 1. key 화이트리스트
        if key not in VALID_KEYS:
            return self._err("INVALID_KEY", f"key={key!r} is not valid", 400)

        # 2. sub_key 조건
        if key in KEY_REQUIRES_SUB_KEY:
            if sub_key is None:
                return self._err("SUB_KEY_REQUIRED", "sub_key is required when key=0", 400)
            if sub_key not in KEY_0_ALLOWED_SUB_KEYS:
                return self._err("INVALID_SUB_KEY", f"sub_key={sub_key!r} not allowed", 400)
        else:
            if sub_key is not None:
                return self._err("SUB_KEY_NOT_ALLOWED",
                                 f"key={key!r} does not accept sub_key", 400)

        # 3. 중복 실행 거절
        if self._active_run is not None:
            return self._err("RUN_ALREADY_ACTIVE", "another run is active", 409)

        # 4. 위험키 승인 검사
        if key in RISK_KEYS:
            if approval_id is None:
                return self._err("RISK_APPROVAL_REQUIRED",
                                 "approval_id required for risk key", 403)
            appr = self._approvals.get(approval_id)
            if appr is None:
                return self._err("RISK_APPROVAL_REQUIRED", "approval not found", 403)
            if appr.is_expired():
                return self._err("RISK_APPROVAL_EXPIRED", "approval has expired", 403)
            if not appr.has_dual_control():
                return self._err("RISK_APPROVAL_DUAL_CONTROL_REQUIRED",
                                 "dual control: 2 distinct approvers required", 403)

        # 5. 실행 수락
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        self._active_run = RunState(run_id=run_id)
        return {**self._ok(run_id=run_id, message="accepted"), "run_id": run_id}

    # ── POST /run/{run_id}/input ───────────────────────────────────────────

    def post_input(self, run_id: str, prompt_id: str, value: Any) -> dict:
        if self._active_run is None or self._active_run.run_id != run_id:
            return self._err("INVALID_PROMPT_ID", "run not found or wrong run_id", 400)
        prompt = self._active_run.prompts.get(prompt_id)
        if prompt is None:
            return self._err("INVALID_PROMPT_ID", f"prompt_id={prompt_id!r} not found", 400)
        if prompt.resolved:
            return self._err("PROMPT_ALREADY_RESOLVED",
                             f"prompt_id={prompt_id!r} already resolved", 409)
        prompt.resolved = True
        prompt.value = value
        prompt.source = "user"
        return self._ok(message="prompt accepted")

    # ── POST /stop ────────────────────────────────────────────────────────

    def post_stop(self) -> dict:
        if self._active_run is not None:
            self._active_run.status = "idle"
            self._active_run = None
        return self._ok(message="stopped")

    # ── GET /status ───────────────────────────────────────────────────────

    def get_status(self) -> dict:
        if self._active_run:
            return self._ok(data={"state": self._active_run.status,
                                   "run_id": self._active_run.run_id})
        return self._ok(data={"state": "idle", "run_id": None})

    # ── 테스트 헬퍼 ───────────────────────────────────────────────────────

    def _register_prompt(self, prompt_id: str, step_id: str = "step") -> None:
        """활성 run에 미해결 프롬프트 등록 (Mode B 시뮬레이션)."""
        assert self._active_run is not None
        self._active_run.prompts[prompt_id] = Prompt(prompt_id=prompt_id, step_id=step_id)

    def _register_approval(self, approvers: list[str],
                           ttl: float = APPROVAL_TTL_SEC) -> str:
        appr_id = f"appr-{uuid.uuid4().hex[:8]}"
        self._approvals[appr_id] = Approval(approval_id=appr_id,
                                             approvers=approvers, ttl=ttl)
        return appr_id

    def _reset(self) -> None:
        self._active_run = None
        self._approvals = {}


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------

import pytest


@pytest.fixture
def router() -> RouterStub:
    r = RouterStub()
    yield r
    r._reset()


# ---------------------------------------------------------------------------
# TC-KEY: key 화이트리스트 / sub_key 조건
# ---------------------------------------------------------------------------

class TestKeyValidation:

    def test_invalid_key_returns_INVALID_KEY(self, router):
        res = router.post_run("99999")
        assert res["ok"] is False
        assert res["code"] == "INVALID_KEY"
        assert res["status"] == 400

    def test_key0_without_sub_key_returns_SUB_KEY_REQUIRED(self, router):
        res = router.post_run("0")
        assert res["ok"] is False
        assert res["code"] == "SUB_KEY_REQUIRED"

    def test_key0_with_invalid_sub_key_returns_INVALID_SUB_KEY(self, router):
        res = router.post_run("0", sub_key="9")
        assert res["ok"] is False
        assert res["code"] == "INVALID_SUB_KEY"

    def test_key0_with_valid_sub_keys_accepted(self, router):
        for sk in KEY_0_ALLOWED_SUB_KEYS:
            router._reset()
            res = router.post_run("0", sub_key=sk)
            assert res["ok"] is True, f"sub_key={sk!r} should be accepted"

    def test_non_key0_with_sub_key_returns_SUB_KEY_NOT_ALLOWED(self, router):
        for k in ("1", "2", "3", "4", "6", "7"):
            router._reset()
            res = router.post_run(k, sub_key="1")
            assert res["ok"] is False
            assert res["code"] == "SUB_KEY_NOT_ALLOWED", f"key={k}"

    @pytest.mark.parametrize("k", ["1", "2", "3", "4", "5", "6", "7"])
    def test_normal_keys_accepted_without_sub_key(self, router, k):
        res = router.post_run(k)
        assert res["ok"] is True
        assert "run_id" in res


# ---------------------------------------------------------------------------
# TC-DUP: 중복 실행 거절
# ---------------------------------------------------------------------------

class TestDuplicateRunRejection:

    def test_second_run_while_active_returns_RUN_ALREADY_ACTIVE(self, router):
        r1 = router.post_run("2")
        assert r1["ok"] is True
        r2 = router.post_run("2")
        assert r2["ok"] is False
        assert r2["code"] == "RUN_ALREADY_ACTIVE"
        assert r2["status"] == 409

    def test_run_accepted_after_stop(self, router):
        router.post_run("2")
        router.post_stop()
        res = router.post_run("2")
        assert res["ok"] is True

    def test_different_key_also_rejected_while_active(self, router):
        router.post_run("1")
        res = router.post_run("3")
        assert res["code"] == "RUN_ALREADY_ACTIVE"


# ---------------------------------------------------------------------------
# TC-RISK: 위험키 승인 4케이스
# ---------------------------------------------------------------------------

class TestRiskKeyApproval:

    @pytest.mark.parametrize("k", ["44", "77", "88", "99"])
    def test_risk_key_without_approval_returns_RISK_APPROVAL_REQUIRED(self, router, k):
        res = router.post_run(k)
        assert res["ok"] is False
        assert res["code"] == "RISK_APPROVAL_REQUIRED"
        assert res["status"] == 403

    @pytest.mark.parametrize("k", ["44", "77", "88", "99"])
    def test_risk_key_with_unknown_approval_id_returns_RISK_APPROVAL_REQUIRED(self, router, k):
        res = router.post_run(k, approval_id="does-not-exist")
        assert res["code"] == "RISK_APPROVAL_REQUIRED"

    @pytest.mark.parametrize("k", ["44", "77", "88", "99"])
    def test_risk_key_with_expired_approval_returns_RISK_APPROVAL_EXPIRED(self, router, k):
        appr_id = router._register_approval(approvers=["alice", "bob"], ttl=0)
        time.sleep(0.01)
        res = router.post_run(k, approval_id=appr_id)
        assert res["ok"] is False
        assert res["code"] == "RISK_APPROVAL_EXPIRED"
        assert res["status"] == 403

    @pytest.mark.parametrize("k", ["44", "77", "88", "99"])
    def test_risk_key_single_approver_returns_DUAL_CONTROL_REQUIRED(self, router, k):
        appr_id = router._register_approval(approvers=["alice"])
        res = router.post_run(k, approval_id=appr_id)
        assert res["ok"] is False
        assert res["code"] == "RISK_APPROVAL_DUAL_CONTROL_REQUIRED"
        assert res["status"] == 403

    @pytest.mark.parametrize("k", ["44", "77", "88", "99"])
    def test_risk_key_dual_approvers_valid_accepted(self, router, k):
        appr_id = router._register_approval(approvers=["alice", "bob"])
        res = router.post_run(k, approval_id=appr_id)
        assert res["ok"] is True, f"key={k} dual-control approval should be accepted"

    def test_same_person_twice_not_dual_control(self, router):
        appr_id = router._register_approval(approvers=["alice", "alice"])
        res = router.post_run("44", approval_id=appr_id)
        assert res["code"] == "RISK_APPROVAL_DUAL_CONTROL_REQUIRED"


# ---------------------------------------------------------------------------
# TC-PRM: Mode B 프롬프트 왕복 / timeout
# ---------------------------------------------------------------------------

class TestModeB:

    def _start_run_with_prompt(self, router: RouterStub,
                               prompt_id: str = "p-001") -> tuple[str, str]:
        res = router.post_run("4")
        assert res["ok"] is True
        run_id = res["run_id"]
        router._register_prompt(prompt_id)
        return run_id, prompt_id

    def test_prompt_resolved_successfully(self, router):
        run_id, pid = self._start_run_with_prompt(router)
        res = router.post_input(run_id, pid, value="style_a")
        assert res["ok"] is True
        # 프롬프트 상태 확인
        assert router._active_run.prompts[pid].resolved is True
        assert router._active_run.prompts[pid].source == "user"

    def test_unknown_prompt_id_returns_INVALID_PROMPT_ID(self, router):
        run_id, _ = self._start_run_with_prompt(router)
        res = router.post_input(run_id, "no-such-prompt", value=1)
        assert res["ok"] is False
        assert res["code"] == "INVALID_PROMPT_ID"

    def test_wrong_run_id_returns_INVALID_PROMPT_ID(self, router):
        run_id, pid = self._start_run_with_prompt(router)
        res = router.post_input("wrong-run-id", pid, value=1)
        assert res["ok"] is False
        assert res["code"] == "INVALID_PROMPT_ID"

    def test_double_resolve_returns_PROMPT_ALREADY_RESOLVED(self, router):
        run_id, pid = self._start_run_with_prompt(router)
        router.post_input(run_id, pid, value="a")
        res2 = router.post_input(run_id, pid, value="b")
        assert res2["ok"] is False
        assert res2["code"] == "PROMPT_ALREADY_RESOLVED"
        assert res2["status"] == 409

    def test_prompt_timeout_applies_default(self, router):
        """
        timeout 시나리오: 서버가 timeout 후 default 값을 적용한다.
        스텁에서는 apply_timeout() 호출로 시뮬레이션.
        """
        run_id, pid = self._start_run_with_prompt(router)
        prompt = router._active_run.prompts[pid]
        # 타임아웃 후 default 적용 시뮬레이션
        prompt.resolved = True
        prompt.source = "default"
        prompt.value = "adopt_best"  # prompt-map 기본값
        # 이후 같은 prompt에 input 시도 → PROMPT_ALREADY_RESOLVED
        res = router.post_input(run_id, pid, value="override")
        assert res["code"] == "PROMPT_ALREADY_RESOLVED"

    def test_multiple_prompts_resolved_independently(self, router):
        run_id, pid1 = self._start_run_with_prompt(router, "p-001")
        router._register_prompt("p-002")
        router.post_input(run_id, "p-001", value="a")
        assert router._active_run.prompts["p-001"].resolved is True
        assert router._active_run.prompts["p-002"].resolved is False
        router.post_input(run_id, "p-002", value="b")
        assert router._active_run.prompts["p-002"].resolved is True


# ---------------------------------------------------------------------------
# TC-STOP: stop 멱등성
# ---------------------------------------------------------------------------

class TestStopIdempotency:

    def test_stop_while_idle_succeeds(self, router):
        res = router.post_stop()
        assert res["ok"] is True

    def test_stop_while_running_succeeds(self, router):
        router.post_run("2")
        res = router.post_stop()
        assert res["ok"] is True

    def test_double_stop_both_succeed(self, router):
        router.post_run("2")
        r1 = router.post_stop()
        r2 = router.post_stop()
        assert r1["ok"] is True
        assert r2["ok"] is True

    def test_after_stop_new_run_accepted(self, router):
        router.post_run("1")
        router.post_stop()
        res = router.post_run("1")
        assert res["ok"] is True


# ---------------------------------------------------------------------------
# TC-STATUS: /status 반환 형식
# ---------------------------------------------------------------------------

class TestStatus:

    def test_status_idle_when_no_run(self, router):
        res = router.get_status()
        assert res["ok"] is True
        assert res["data"]["state"] == "idle"
        assert res["data"]["run_id"] is None

    def test_status_running_during_run(self, router):
        r = router.post_run("2")
        res = router.get_status()
        assert res["data"]["state"] == "running"
        assert res["data"]["run_id"] == r["run_id"]

    def test_status_idle_after_stop(self, router):
        router.post_run("2")
        router.post_stop()
        res = router.get_status()
        assert res["data"]["state"] == "idle"


# ---------------------------------------------------------------------------
# TC-CONTRACT: 오류코드 enum 완전성 (api-contract-v1.yaml 기준)
# ---------------------------------------------------------------------------

EXPECTED_ERROR_CODES = {
    "INVALID_KEY",
    "SUB_KEY_REQUIRED",
    "SUB_KEY_NOT_ALLOWED",
    "INVALID_SUB_KEY",
    "RUN_ALREADY_ACTIVE",
    "RISK_APPROVAL_REQUIRED",
    "RISK_APPROVAL_EXPIRED",
    "RISK_APPROVAL_DUAL_CONTROL_REQUIRED",
    "INVALID_PROMPT_ID",
    "PROMPT_ALREADY_RESOLVED",
}

DOCUMENT_ONLY_ERROR_CODES = {
    "INTERNAL_ERROR",
    "INVALID_PROJECT",
    "INVALID_REQUEST",
}

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "docs" / "implementation" / "api-contract-v1.yaml"


def _load_contract_spec() -> dict[str, Any]:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


class TestErrorCodeCoverage:

    def _collect_codes(self, router: RouterStub) -> set[str]:
        """각 분기를 한 번씩 실행해 실제로 반환된 오류코드를 수집."""
        codes: set[str] = set()

        def hit(res: dict) -> None:
            if not res["ok"]:
                codes.add(res["code"])

        # INVALID_KEY
        hit(router.post_run("bad"))
        # SUB_KEY_REQUIRED
        hit(router.post_run("0"))
        # INVALID_SUB_KEY
        hit(router.post_run("0", sub_key="Z"))
        # SUB_KEY_NOT_ALLOWED
        hit(router.post_run("2", sub_key="1"))
        # RUN_ALREADY_ACTIVE
        router.post_run("1")
        hit(router.post_run("1"))
        router.post_stop()
        # RISK_APPROVAL_REQUIRED
        hit(router.post_run("44"))
        # RISK_APPROVAL_EXPIRED
        appr_id = router._register_approval(approvers=["a", "b"], ttl=0)
        time.sleep(0.01)
        hit(router.post_run("44", approval_id=appr_id))
        # RISK_APPROVAL_DUAL_CONTROL_REQUIRED
        appr_id2 = router._register_approval(approvers=["solo"])
        hit(router.post_run("44", approval_id=appr_id2))
        # INVALID_PROMPT_ID + PROMPT_ALREADY_RESOLVED
        router.post_run("4")
        run_id = router._active_run.run_id
        router._register_prompt("p")
        hit(router.post_input(run_id, "no-exist", value=1))
        router.post_input(run_id, "p", value=1)
        hit(router.post_input(run_id, "p", value=2))
        router.post_stop()

        return codes

    def test_all_10_error_codes_reachable(self, router):
        codes = self._collect_codes(router)
        missing = EXPECTED_ERROR_CODES - codes
        assert not missing, f"오류코드 미도달: {missing}"

    def test_no_unexpected_error_codes(self, router):
        codes = self._collect_codes(router)
        extra = codes - EXPECTED_ERROR_CODES
        assert not extra, f"정의되지 않은 오류코드 발생: {extra}"


class TestContractDocumentSurface:

    def test_contract_uses_bridge_server_port_8300(self):
        spec = _load_contract_spec()
        assert spec["servers"][0]["url"] == "http://127.0.0.1:8300"

    def test_contract_contains_quality_and_safe_ops_endpoints(self):
        spec = _load_contract_spec()
        required_paths = {
            "/quality/summary",
            "/quality/dashboard",
            "/safe-ops/preview",
            "/quality/review",
        }
        assert required_paths.issubset(spec["paths"])

    def test_error_envelope_enum_includes_document_only_codes(self):
        spec = _load_contract_spec()
        error_codes = set(
            spec["components"]["schemas"]["ErrorEnvelope"]["properties"]["code"]["enum"]
        )
        assert EXPECTED_ERROR_CODES.issubset(error_codes)
        assert DOCUMENT_ONLY_ERROR_CODES.issubset(error_codes)

    def test_status_envelope_enum_matches_runtime_states(self):
        spec = _load_contract_spec()
        status_states = set(
            spec["components"]["schemas"]["StatusEnvelope"]["properties"]["data"]["properties"]["state"]["enum"]
        )
        assert status_states == {"idle", "starting", "running", "stopping", "error"}
