from modules.core.llm_schema import schema_to_dict, to_gemini_schema
from modules.core.response_schemas import DIRECTOR_AUDIT_SCHEMA, get_schema_for_task, get_schema_spec_for_task


def test_get_schema_spec_for_task_returns_dict_spec():
    spec = get_schema_spec_for_task("DIRECTOR_AUDIT")
    assert isinstance(spec, dict)
    assert spec["type"] == "object"
    assert "consistency_checklist" in spec["properties"]


def test_get_schema_for_task_rebuilds_gemini_schema_from_spec():
    schema = get_schema_for_task("DIRECTOR_AUDIT")
    assert "consistency_checklist" in schema.properties
    assert "fix_scope" in schema.required


def test_schema_roundtrip_preserves_required_and_nested_properties():
    spec = schema_to_dict(DIRECTOR_AUDIT_SCHEMA)
    rebuilt = to_gemini_schema(spec)
    assert set(rebuilt.required) == set(DIRECTOR_AUDIT_SCHEMA.required)
    assert set(rebuilt.properties["consistency_checklist"].properties.keys()) == set(
        DIRECTOR_AUDIT_SCHEMA.properties["consistency_checklist"].properties.keys()
    )
