from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.llm_provider import LLMRequest
from modules.core.llm_router import LLMProviderRouter

DEFAULT_MODEL_CANDIDATES = (
    "claude-sonnet-4-6",
    "claude-sonnet-4-5",
    "claude-sonnet-4",
    "claude-haiku-4-5",
)
DEFAULT_REGION_CANDIDATES = (
    "us-central1",
    "us-east5",
    "global",
    "asia-east1",
    "europe-west1",
)
GCLOUD_CANDIDATE_PATHS = (
    r"C:\Users\User\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
    r"C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
)


@dataclass(slots=True)
class ProbeAttempt:
    model: str
    region: str
    status: str
    classification: str
    text: str | None = None
    provider: str | None = None
    backend: str | None = None
    family: str | None = None
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    error_type: str | None = None
    error: str | None = None
    elapsed_s: float | None = None


@dataclass(slots=True)
class ProbeReport:
    project_id: str | None
    billing_project: str | None
    env_location: str | None
    gcloud_path: str | None
    listed_models: list[str] = field(default_factory=list)
    attempts: list[ProbeAttempt] = field(default_factory=list)


def load_dotenv_file(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.is_file():
        return loaded
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value
        loaded[key] = value
    return loaded


def resolve_gcloud_path() -> str | None:
    found = shutil.which("gcloud")
    if found:
        return found
    for candidate in GCLOUD_CANDIDATE_PATHS:
        if Path(candidate).is_file():
            return candidate
    return None


def classify_exception(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    lowered = text.lower()
    if (
        "defaultcredentialserror" in lowered
        or "application default credentials" in lowered
        or "default credentials" in lowered
    ):
        return "auth"
    if "permissiondenied" in lowered or "permission denied" in lowered:
        return "permission"
    if "resource_exhausted" in lowered or "429" in lowered or "ratelimiterror" in lowered or "quota" in lowered:
        return "rate_limit"
    if "notfound" in lowered or "404" in lowered or "publisher model" in lowered:
        return "not_found_or_no_access"
    if "service_disabled" in lowered or "api not enabled" in lowered:
        return "api_disabled"
    return "other"


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = (value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def extract_model_ids(model_garden_payload: list[dict[str, Any]]) -> list[str]:
    extracted: list[str] = []
    for item in model_garden_payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if "/models/" not in name:
            continue
        extracted.append(name.rsplit("/models/", 1)[-1])
    return unique_in_order(extracted)


def list_model_garden_claude_models(
    *,
    gcloud_path: str,
    project_id: str,
    billing_project: str,
    limit: int,
) -> list[str]:
    command = [
        gcloud_path,
        "ai",
        "model-garden",
        "models",
        "list",
        "--project",
        project_id,
        "--billing-project",
        billing_project,
        "--model-filter=claude",
        f"--limit={limit}",
        "--format=json",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "gcloud model list failed")
    payload = json.loads(completed.stdout or "[]")
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected gcloud model-garden payload shape")
    return extract_model_ids(payload)


def probe_claude_vertex(*, model: str, region: str) -> ProbeAttempt:
    os.environ["VERTEX_LOCATION"] = region
    router = LLMProviderRouter(provider_configs={"anthropic_vertex": {"enabled": True}})
    provider = router.get_provider_for_model(f"anthropic-vertex:{model}")
    request = LLMRequest(
        model=f"anthropic-vertex:{model}",
        contents="Reply with exactly: claude-vertex-ok",
        config={"max_output_tokens": 16, "temperature": 0.0},
    )
    started = time.time()
    try:
        response = provider.generate(client=None, request=request)
        return ProbeAttempt(
            model=model,
            region=region,
            status="PASS",
            classification="pass",
            text=response.text,
            provider=response.provider,
            backend=response.backend,
            family=response.family,
            finish_reason=response.finish_reason,
            usage=response.usage,
            elapsed_s=round(time.time() - started, 2),
        )
    except Exception as exc:  # pragma: no cover - exercised in live probing
        return ProbeAttempt(
            model=model,
            region=region,
            status="FAIL",
            classification=classify_exception(exc),
            error_type=type(exc).__name__,
            error=str(exc),
            elapsed_s=round(time.time() - started, 2),
        )


def build_model_candidates(
    *,
    listed_models: list[str],
    env_model: str | None,
    explicit_models: list[str],
) -> list[str]:
    return unique_in_order(explicit_models + ([env_model] if env_model else []) + listed_models + list(DEFAULT_MODEL_CANDIDATES))


def build_region_candidates(*, env_region: str | None, explicit_regions: list[str]) -> list[str]:
    return unique_in_order(explicit_regions + ([env_region] if env_region else []) + list(DEFAULT_REGION_CANDIDATES))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-probe Claude-on-Vertex model/region combinations.")
    parser.add_argument("--env-file", default=str(ROOT / ".env"))
    parser.add_argument("--project-id")
    parser.add_argument("--billing-project")
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--region", action="append", default=[])
    parser.add_argument("--limit-models", type=int, default=20)
    parser.add_argument("--max-attempts", type=int, default=12)
    parser.add_argument("--stop-on-first-pass", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    loaded_env = load_dotenv_file(Path(args.env_file))
    project_id = args.project_id or os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    billing_project = args.billing_project or project_id
    env_model = os.getenv("CLAUDE_VERTEX_MODEL")
    env_region = os.getenv("VERTEX_LOCATION") or os.getenv("GOOGLE_CLOUD_LOCATION")
    gcloud_path = resolve_gcloud_path()

    report = ProbeReport(
        project_id=project_id,
        billing_project=billing_project,
        env_location=env_region,
        gcloud_path=gcloud_path,
    )

    listed_models: list[str] = []
    if gcloud_path and project_id and billing_project:
        try:
            listed_models = list_model_garden_claude_models(
                gcloud_path=gcloud_path,
                project_id=project_id,
                billing_project=billing_project,
                limit=args.limit_models,
            )
        except Exception as exc:  # pragma: no cover - live environment only
            report.attempts.append(
                ProbeAttempt(
                    model="__model_garden__",
                    region=env_region or "",
                    status="FAIL",
                    classification=classify_exception(exc),
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
            )
    report.listed_models = listed_models

    model_candidates = build_model_candidates(
        listed_models=listed_models,
        env_model=env_model,
        explicit_models=args.model,
    )
    region_candidates = build_region_candidates(env_region=env_region, explicit_regions=args.region)

    attempts = 0
    for model in model_candidates:
        for region in region_candidates:
            if attempts >= args.max_attempts:
                break
            attempt = probe_claude_vertex(model=model, region=region)
            report.attempts.append(attempt)
            attempts += 1
            if args.stop_on_first_pass and attempt.status == "PASS":
                break
        if attempts >= args.max_attempts:
            break
        if args.stop_on_first_pass and report.attempts and report.attempts[-1].status == "PASS":
            break

    payload = asdict(report)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) if args.json or args.output else _render_text_report(report, loaded_env)
    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(rendered)
    return 0


def _render_text_report(report: ProbeReport, loaded_env: dict[str, str]) -> str:
    lines = [
        "Claude-on-Vertex auto-probe",
        f"project_id: {report.project_id or 'unset'}",
        f"billing_project: {report.billing_project or 'unset'}",
        f"env_location: {report.env_location or 'unset'}",
        f"gcloud: {report.gcloud_path or 'missing'}",
        f"env_loaded_keys: {', '.join(sorted(loaded_env.keys())) if loaded_env else '(none)'}",
        f"listed_models: {', '.join(report.listed_models) if report.listed_models else '(none)'}",
        "attempts:",
    ]
    for attempt in report.attempts:
        if attempt.status == "PASS":
            lines.append(
                f"  PASS model={attempt.model} region={attempt.region} "
                f"provider={attempt.provider} backend={attempt.backend} "
                f"elapsed={attempt.elapsed_s}s text={attempt.text!r}"
            )
        else:
            lines.append(
                f"  FAIL model={attempt.model} region={attempt.region} "
                f"class={attempt.classification} error_type={attempt.error_type} error={attempt.error!r}"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
