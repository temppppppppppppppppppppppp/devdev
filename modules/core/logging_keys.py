"""Helpers for deterministic cross-sink logging keys."""


def resolve_logging_session_id(*sources, fallback: str | None = None) -> str | None:
    """Resolve a stable runtime session id from known runtime objects.

    The helper intentionally ignores non-string attributes so MagicMock-heavy
    unit tests keep deterministic legacy keys unless they opt in explicitly.
    """
    for source in sources:
        value = None
        if isinstance(source, str):
            value = source
        elif isinstance(source, dict):
            value = source.get("metrics_session_id") or source.get("session_id")
        elif source is not None:
            candidate = getattr(source, "metrics_session_id", None)
            if isinstance(candidate, str) and candidate.strip():
                value = candidate
            else:
                candidate = getattr(source, "session_id", None)
                if isinstance(candidate, str) and candidate.strip():
                    value = candidate

        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized

    if isinstance(fallback, str):
        normalized = fallback.strip()
        if normalized:
            return normalized
    return None


def build_attempt_key(
    *,
    stage: int,
    ep_num: int | None = None,
    arc_num: int | None = None,
    attempt_num: int = 1,
    session_id: str | None = None,
) -> str:
    """Build a stable attempt key shared across DB and JSON sinks."""
    stage_num = int(stage or 0)
    episode_num = int(ep_num or 0)
    arc_no = int(arc_num or 0)
    attempt_no = max(1, int(attempt_num or 1))
    parts = [f"s{stage_num}", f"ep{episode_num}", f"arc{arc_no}", f"a{attempt_no}"]
    if session_id:
        parts.append(str(session_id).strip())
    return ":".join(parts)
