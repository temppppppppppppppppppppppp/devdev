import json
from pathlib import Path


MASTER_PATH = Path("docs/2026-03-09/imf_kukje_heir_tf_master_001_070.json")
CONTINUITY_PATH = Path("docs/2026-03-09/imf_kukje_heir_tf_continuity_bible_v1.json")
STEP1_PATH = Path("docs/2026-03-09/imf_kukje_heir_tf_step1.json")
TREATMENT_PATH = Path("treatments/06_imf_kukje_heir_tr_block_070_draft.json")
BI_PATH = Path("bible/06_imf_kukje_heir_bi.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def last_relationship_states(master: dict) -> dict[str, str]:
    states: dict[str, str] = {}
    for block in master.get("draft_blocks", []):
        for delta in block.get("relationship_delta", []):
            target = delta.get("target")
            after = delta.get("after")
            if target and after:
                states[target] = after
    return states


def test_imf_chain_repair_restores_schema_and_title_contract():
    master = load_json(MASTER_PATH)
    treatment = load_json(TREATMENT_PATH)
    continuity = load_json(CONTINUITY_PATH)
    bi = load_json(BI_PATH)

    expected_schema = "IMF로 무너진 국제그룹 후계자 회귀물 Block 1-70 integrated treatment draft"

    assert master["_schema_description"] == expected_schema
    assert treatment["_schema_description"] == expected_schema
    assert master["project"]["title"] == "국제를 다시 세우는 후계자"
    assert treatment["project"]["title"] == master["project"]["title"]
    assert continuity["project_title"] == master["project"]["title"]
    assert bi["project_title"] == master["project"]["title"]
    assert continuity["title_aliases"] == ["국제를 다시 일으키는 유일한 후계자"]
    assert bi["title_aliases"] == continuity["title_aliases"]
    assert master["capital_milestones"][0]["section"] == "잔해 회수"
    assert treatment["capital_milestones"][0]["section"] == "잔해 회수"


def test_imf_chain_repair_derives_roles_and_end_states_from_source():
    master = load_json(MASTER_PATH)
    continuity = load_json(CONTINUITY_PATH)
    bi = load_json(BI_PATH)
    step1 = load_json(STEP1_PATH)

    seed_roles = {row["name"]: row["role"] for row in step1["seed_npcs"]}
    canonical_map = {row["canonical"]: row for row in continuity["canonical_name_map"]}

    assert canonical_map["서태윤"]["role"] == step1["project"]["protagonist"]["identity"]
    assert canonical_map["서태윤"]["replaced_aliases"] == ["서태윤 자신"]

    for name in ["박원식", "민서영", "오민석", "김해진", "한규철", "레온 첸", "배정호", "조태수"]:
        assert canonical_map[name]["role"] == seed_roles[name]
        assert canonical_map[name]["replaced_aliases"] == []

    assert canonical_map["서연옥 여사"]["role"] == "가문 원로"
    assert canonical_map["라시드 알 하산"]["role"] == "중동 발주처 실무총괄"
    assert bi["canonical_name_map"] == continuity["canonical_name_map"]

    end_states = last_relationship_states(master)
    expected_targets = {
        "서태윤": "서태윤 자신",
        "박원식": "박원식",
        "민서영": "민서영",
        "오민석": "오민석",
        "김해진": "김해진",
        "한규철": "한규철",
        "레온 첸": "레온 첸",
        "배정호": "배정호",
        "조태수": "조태수",
        "서연옥 여사": "서연옥 여사",
        "라시드 알 하산": "라시드 알 하산",
    }
    for name, target in expected_targets.items():
        assert continuity["npc_end_state"][name] == end_states[target]
    assert bi["npc_end_state"] == continuity["npc_end_state"]


def test_imf_chain_repair_removes_semantic_mojibake_from_continuity_artifacts():
    continuity = load_json(CONTINUITY_PATH)
    bi = load_json(BI_PATH)
    triple_q = "?" * 3
    broken_capital = "150" + "?"

    continuity_text = json.dumps(continuity, ensure_ascii=False)
    bi_text = json.dumps(bi, ensure_ascii=False)

    assert triple_q not in continuity_text
    assert triple_q not in bi_text
    assert broken_capital not in continuity_text
    assert broken_capital not in bi_text
    assert continuity["future_extension_guardrails"] == bi["future_extension_guardrails"]
    assert len(continuity["verified_chains"]["section_handoffs"]) == 6
