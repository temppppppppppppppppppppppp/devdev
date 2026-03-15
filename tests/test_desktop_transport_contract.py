import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
API_CONTRACT = yaml.safe_load(
    (ROOT / "docs/implementation/api-contract-v1.yaml").read_text(encoding="utf-8")
)
EVENT_SCHEMA = json.loads(
    (ROOT / "docs/implementation/event-schema-v1.json").read_text(encoding="utf-8")
)
MAIN_JS = (ROOT / "geuldobi-desktop/src/main.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "geuldobi-desktop/src/index.html").read_text(encoding="utf-8")
BRIDGE_SERVER = (ROOT / "modules/api/bridge_server.py").read_text(encoding="utf-8")
PROMPT_BROKER = (ROOT / "modules/api/prompt_broker.py").read_text(encoding="utf-8")


def _desktop_transport_contract() -> dict:
    return API_CONTRACT["x-desktop-bridge-transport"]


def _event_type_enum() -> frozenset[str]:
    return frozenset(EVENT_SCHEMA["properties"]["type"]["enum"])


def _payload_schema_for(event_type: str) -> dict:
    for clause in EVENT_SCHEMA["allOf"]:
        clause_type = clause["if"]["properties"]["type"]
        if clause_type.get("const") == event_type:
            return clause["then"]["properties"]["payload"]
        if event_type in clause_type.get("enum", []):
            return clause["then"]["properties"]["payload"]
    raise AssertionError(f"payload schema for {event_type!r} not found")


def _runtime_emitted_event_types() -> frozenset[str]:
    bridge_types = set(re.findall(r'_build_event\(run_id, "([^"]+)"', BRIDGE_SERVER))
    prompt_types = set(re.findall(r'_build_event\(run_id, "([^"]+)"', PROMPT_BROKER))
    if 'etype = "run_completed" if returncode == 0 else "run_failed"' in BRIDGE_SERVER:
        bridge_types.update({"run_completed", "run_failed"})
    return frozenset(bridge_types | prompt_types)


def test_desktop_bridge_transport_contract_matches_main_process_source():
    contract = _desktop_transport_contract()
    namespace = contract["renderer_boundary"]["desktop_transport_namespace"]

    assert namespace["envelope_version"] == "desktop_bridge_v1"
    assert namespace["network_error_code"] == "NETWORK_ERROR"
    assert namespace["http_error_code_format"] == "HTTP_<status_code>"

    assert 'networkErrorCode: "NETWORK_ERROR"' in MAIN_JS
    assert 'httpErrorPrefix: "HTTP_"' in MAIN_JS
    assert 'envelopeVersion: "desktop_bridge_v1"' in MAIN_JS
    assert 'namespace: "desktop_transport"' in MAIN_JS
    assert "backend_code:" in MAIN_JS
    assert "backend_message:" in MAIN_JS
    assert "url_path:" in MAIN_JS
    assert "transport_status:" in MAIN_JS

    websocket_runtime = contract["websocket_runtime"]
    assert websocket_runtime["url"] == "ws://127.0.0.1:8300/events"
    assert 'const EVENTS_WS_URL = "ws://127.0.0.1:8300/events";' in MAIN_JS
    assert "new WebSocket(wsUrl)" in INDEX_HTML


def test_runtime_websocket_event_types_match_schema_and_emitters():
    ws_contract = API_CONTRACT["paths"]["/events"]["x-websocket"]
    documented_types = frozenset(ws_contract["runtime_event_types"])
    runtime_types = _runtime_emitted_event_types()
    schema_types = _event_type_enum()

    assert documented_types == runtime_types
    assert schema_types == runtime_types
    assert "progress" not in schema_types


def test_runtime_websocket_payload_contract_matches_renderer_and_backend_usage():
    prompt_request = _payload_schema_for("prompt_request")
    assert set(prompt_request["required"]) == {
        "prompt_id",
        "step_id",
        "input_type",
        "default",
        "timeout_sec",
    }
    assert set(prompt_request["properties"]["input_type"]["enum"]) == {
        "enum",
        "int",
        "string",
        "bool",
        "enter",
        "multiline",
    }
    assert prompt_request["properties"]["options"]["items"]["required"] == ["key", "label"]
    assert "prompt_text" in prompt_request["properties"]

    run_started = _payload_schema_for("run_started")
    assert run_started["required"] == ["key"]
    assert 'broadcast(_build_event(run_id, "run_started", {"key": key}))' in BRIDGE_SERVER

    stdout = _payload_schema_for("stdout")
    assert stdout["required"] == ["text"]
    assert 'broadcast(_build_event(run_id, "stdout", {"text": text}))' in BRIDGE_SERVER

    run_exit = _payload_schema_for("run_failed")
    assert run_exit["required"] == ["returncode"]
    assert {
        "stdout_tail",
        "stderr_tail",
        "stderr_authoritative",
        "stderr_decode_policy",
        "failure_phase",
        "last_prompt_step",
        "duration_ms",
    }.issubset(
        run_exit["properties"]
    )
    assert '_build_event(run_id, etype, _build_run_exit_payload(runner, returncode))' in BRIDGE_SERVER

    prompt_resolved = _payload_schema_for("prompt_resolved")
    assert prompt_resolved["properties"]["source"]["enum"] == ["user", "default"]

    prompt_timeout = _payload_schema_for("prompt_timeout")
    assert prompt_timeout["required"] == ["prompt_id", "applied_default"]
