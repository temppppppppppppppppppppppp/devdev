from __future__ import annotations

from copy import deepcopy
from typing import Any

from google.genai import types

_TYPE_NAME_TO_GEMINI = {
    "string": types.Type.STRING,
    "integer": types.Type.INTEGER,
    "number": types.Type.NUMBER,
    "boolean": types.Type.BOOLEAN,
    "array": types.Type.ARRAY,
    "object": types.Type.OBJECT,
    "null": types.Type.NULL,
}

_GEMINI_TO_TYPE_NAME = {value: key for key, value in _TYPE_NAME_TO_GEMINI.items()}


def to_gemini_schema(spec: dict[str, Any] | None):
    """Convert provider-neutral dict schema into Gemini types.Schema."""

    if spec is None:
        return None

    kwargs: dict[str, Any] = {}
    type_name = spec.get("type")
    if type_name is not None:
        kwargs["type"] = _TYPE_NAME_TO_GEMINI.get(type_name, type_name)
    if "description" in spec:
        kwargs["description"] = spec["description"]
    if "enum" in spec:
        kwargs["enum"] = list(spec["enum"])
    if "required" in spec:
        kwargs["required"] = list(spec["required"])
    if "minimum" in spec:
        kwargs["minimum"] = spec["minimum"]
    if "maximum" in spec:
        kwargs["maximum"] = spec["maximum"]
    if "nullable" in spec:
        kwargs["nullable"] = bool(spec["nullable"])
    if "properties" in spec:
        kwargs["properties"] = {name: to_gemini_schema(child) for name, child in spec["properties"].items()}
    if "items" in spec and spec["items"] is not None:
        kwargs["items"] = to_gemini_schema(spec["items"])
    return types.Schema(**kwargs)


def schema_to_dict(schema: Any) -> dict[str, Any] | None:
    """Convert Gemini types.Schema (or nested provider-neutral data) into dict schema."""

    if schema is None:
        return None
    if isinstance(schema, dict):
        return deepcopy(schema)

    result: dict[str, Any] = {}
    schema_type = getattr(schema, "type", None)
    if schema_type is not None:
        result["type"] = _GEMINI_TO_TYPE_NAME.get(schema_type, str(schema_type).lower())

    description = getattr(schema, "description", None)
    if description:
        result["description"] = description

    enum = getattr(schema, "enum", None)
    if enum:
        result["enum"] = list(enum)

    required = getattr(schema, "required", None)
    if required:
        result["required"] = list(required)

    minimum = getattr(schema, "minimum", None)
    if minimum is not None:
        result["minimum"] = minimum

    maximum = getattr(schema, "maximum", None)
    if maximum is not None:
        result["maximum"] = maximum

    nullable = getattr(schema, "nullable", None)
    if nullable is not None:
        result["nullable"] = nullable

    properties = getattr(schema, "properties", None)
    if properties:
        result["properties"] = {name: schema_to_dict(child) for name, child in properties.items()}

    items = getattr(schema, "items", None)
    if items is not None:
        result["items"] = schema_to_dict(items)

    return result
