from pathlib import Path


def test_director_yaml_mentions_work_identity_drift():
    src = Path("config/prompts/director.yaml").read_text(encoding="utf-8")
    assert "work identity drift" in src
    assert "forbidden_flattenings" in src
    assert "[작품 정체성 감리]" in src
