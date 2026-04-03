from __future__ import annotations

import os
from typing import Any

from google import genai

from modules.core.provider_mode import (
    AMBIENT_MODE,
    GEMINI_DIRECT_MODE,
    VERTEX_AI_MODE,
    get_env_provider_mode,
    normalize_provider_mode,
)


def _load_raw_models_yaml() -> dict[str, Any]:
    from modules.core.models_config import load_models_yaml

    payload = load_models_yaml(apply_provider_mode=False)
    return payload if isinstance(payload, dict) else {}


def _raw_provider_config(name: str) -> dict[str, Any]:
    providers = _load_raw_models_yaml().get("providers", {})
    config = providers.get(name) if isinstance(providers, dict) else None
    return config.copy() if isinstance(config, dict) else {}


def _infer_mode_from_raw_models_config() -> str:
    vertex_cfg = _raw_provider_config("vertex_ai")
    if vertex_cfg.get("enabled"):
        return VERTEX_AI_MODE
    return GEMINI_DIRECT_MODE


def resolve_google_provider_mode(provider_mode: str | None = None) -> str:
    requested = normalize_provider_mode(provider_mode)
    if requested != AMBIENT_MODE:
        return requested
    env_mode = get_env_provider_mode()
    if env_mode != AMBIENT_MODE:
        return env_mode
    return _infer_mode_from_raw_models_config()


def resolve_google_api_key_names(provider_mode: str | None = None) -> list[str]:
    mode = resolve_google_provider_mode(provider_mode)
    if mode == VERTEX_AI_MODE:
        base_name = str(_raw_provider_config("vertex_ai").get("api_key_env") or "VERTEX_API_KEY")
    else:
        base_name = str(_raw_provider_config("gemini").get("api_key_env") or "GOOGLE_API_KEY")
    return [base_name, *(f"{base_name}_{i}" for i in range(2, 10))]


def load_google_api_keys(provider_mode: str | None = None) -> list[str]:
    keys: list[str] = []
    for env_name in resolve_google_api_key_names(provider_mode):
        value = str(os.getenv(env_name) or "").strip()
        if value:
            keys.append(value)
    return keys


def _resolve_vertex_auth_mode() -> str:
    config = _raw_provider_config("vertex_ai")
    return str(os.getenv("GEULDOBI_VERTEX_AUTH_MODE") or config.get("auth_mode") or "api_key").strip().lower()


def _load_credentials_from_env(credentials_env: str) -> Any | None:
    credentials_path = os.getenv(credentials_env)
    if not credentials_path:
        return None
    try:
        from google.auth import load_credentials_from_file
    except ImportError as exc:
        raise RuntimeError("google-auth is required to load Vertex AI credentials files.") from exc

    credentials, _ = load_credentials_from_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return credentials


def build_google_genai_client(*, api_key: str | None = None, provider_mode: str | None = None):
    mode = resolve_google_provider_mode(provider_mode)
    if mode == VERTEX_AI_MODE:
        config = _raw_provider_config("vertex_ai")
        auth_mode = _resolve_vertex_auth_mode()
        api_key_env = str(config.get("api_key_env") or "VERTEX_API_KEY")
        project_id_env = str(config.get("project_id_env") or "VERTEX_PROJECT_ID")
        location_env = str(config.get("location_env") or "VERTEX_LOCATION")
        credentials_env = str(config.get("credentials_env") or "GOOGLE_APPLICATION_CREDENTIALS")

        if auth_mode == "auto":
            auth_mode = "api_key" if str(api_key or os.getenv(api_key_env) or "").strip() else "project_credentials"

        if auth_mode == "api_key":
            resolved_api_key = str(api_key or os.getenv(api_key_env) or "").strip()
            if not resolved_api_key:
                raise RuntimeError(f"Vertex AI auth_mode=api_key requires {api_key_env}.")
            return genai.Client(vertexai=True, api_key=resolved_api_key)

        if auth_mode != "project_credentials":
            raise RuntimeError(f"Unsupported GEULDOBI vertex auth mode: {auth_mode}")

        project = str(os.getenv(project_id_env) or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
        location = str(os.getenv(location_env) or os.getenv("GOOGLE_CLOUD_LOCATION") or "").strip()
        if not project or not location:
            raise RuntimeError(
                f"Vertex AI auth_mode=project_credentials requires "
                f"{project_id_env}/{location_env} or GOOGLE_CLOUD_PROJECT/GOOGLE_CLOUD_LOCATION."
            )
        client_kwargs: dict[str, Any] = {
            "vertexai": True,
            "project": project,
            "location": location,
        }
        credentials = _load_credentials_from_env(credentials_env)
        if credentials is not None:
            client_kwargs["credentials"] = credentials
        return genai.Client(**client_kwargs)

    resolved_api_key = str(api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    return genai.Client(api_key=resolved_api_key or None)
