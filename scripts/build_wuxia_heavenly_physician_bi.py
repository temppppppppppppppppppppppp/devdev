#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build BI for wuxia_heavenly_physician from TR + Phase0 (deterministic sync)."""

import json
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.narrative_router.artifact_paths import (  # noqa: E402
    canonical_bi_path,
    canonical_tr_path,
    resolve_phase0_path,
)

def main():
    phase0_path = resolve_phase0_path("wuxia_heavenly_physician", root=ROOT)
    tr_path = canonical_tr_path("wuxia_heavenly_physician", root=ROOT)

    with open(phase0_path, "r", encoding="utf-8") as f:
        p0 = json.load(f)
    with open(tr_path, "r", encoding="utf-8") as f:
        tr = json.load(f)

    blocks = tr["blocks"]
    pd = p0["phase0_design"]
    last_me = blocks[-1]["martial_ext"]

    # === Realm history from TR transitions ===
    realm_history = []
    for b in blocks:
        me = b["martial_ext"]
        rb = me.get("realm_before", "")
        ra = me.get("realm_after", "")
        if rb != ra:
            realm_history.append({"block": b["block_id"], "realm": ra, "event": b["title"]})

    # === Martial arts from Phase0 ===
    martial_arts_final = []
    for art in pd["martial_art_path"]:
        martial_arts_final.append({
            "name": art["name"],
            "origin": art["origin"],
            "block_acquired": art["block_acquired"],
            "evolution": art["evolution"]
        })

    # === Injury log (major only) ===
    major_injuries = [
        {"block": "B07", "injury": "\ube44\ubb34 \uc911 \uc88c\uce21 \uc5b4\uae68 \uacbd\ubbf8\ud55c \ud0c0\ubc15\uc0c1", "recovery_block": "B08"},
        {"block": "B13", "injury": "\uc544\ubc84\uc9c0 \uce58\ub8cc \uc2e4\ud328 \u2014 \ub0b4\uacf5 \uacfc\uc18c\ube44 \uae30\ub825 \uc800\ud558", "recovery_block": "B14"},
        {"block": "B19", "injury": "\ub3c5\ubb38 \uc790\uac1d \ub9c8\ube44\ub3c5 \ud53c\ud574 \u2014 \uc67c\ud314 \ub9c8\ube44", "recovery_block": "B20"},
        {"block": "B28", "injury": "\uacfc\ub85c \uacbd\ub9e5 3\uac1c \ubbf8\uc138 \ud30c\ub834 (\uc218\ud0dc\uc591\uc18c\uc7a5\uacbd, \uc871\uc18c\uc591\ub2f4\uacbd, \uc871\ud0dc\uc74c\ube44\uacbd)", "recovery_block": "B36"},
        {"block": "B38", "injury": "\uc2a4\uc2b9 \uc0ac\ub9dd \uc2ec\ub9ac\uc801 \ud2b8\ub77c\uc6b0\ub9c8 \u2014 \uce68\uc744 \uc7a1\uc9c0 \ubabb\ud568", "recovery_block": "B40"},
        {"block": "B43", "injury": "\uc0b4\uce68 \ub0b4\uacf5 \uc5ed\ub958 \u2014 \uacbd\ub9e5 \uc804\uccb4 \ubbf8\uc138 \ucda9\uaca9, \ub0b4\uacf5 55\u219235\uac11\uc790", "recovery_block": "B46"},
        {"block": "B53", "injury": "\uc88c\ucc9c\uba85 \ud2b9\uc218 \ub3c5 \uc8fc\uc785 \u2014 \uacbd\ub9e5 \ubd80\ubd84 \uc624\uc5fc, \ub0b4\uacf5 85\u219250\uac11\uc790", "recovery_block": "B60"},
        {"block": "B57", "injury": "\uc18c\ud48d \uc911\uc0c1\uc73c\ub85c \uc778\ud55c \uac10\uc815\uc801 \ucda9\uaca9", "recovery_block": "B58"},
        {"block": "B63", "injury": "\uce60\uc131\uce68\ubc95 7\uce68 \uc2e4\ud328 \u2014 \uacbd\ub9e5 3\uac1c \ud30c\ub834", "recovery_block": "B69"},
    ]

    # === Faction history ===
    faction_history = []
    for entry in pd["faction_map"]["protagonist_faction"]["position_progression"]:
        faction_history.append({
            "arc": entry["arc"],
            "faction": "\uc9c4\uac00\uc7a5(\u9673\u5bb6\u838a)",
            "role": entry["position"],
            "event": entry["key_event"]
        })

    # === plot_roadmap (deterministic copy) ===
    plot_roadmap = []
    for b in blocks:
        me = b.get("martial_ext", {})
        plot_roadmap.append({
            "block_id": b["block_id"],
            "title": b["title"],
            "emotional_beat": b.get("emotional_beat", ""),
            "tension_level": b.get("tension_level", 0),
            "realm_before": me.get("realm_before", ""),
            "realm_after": me.get("realm_after", ""),
            "martial_event": me.get("action_type", ""),
            "foreshadow": b.get("foreshadow", []),
            "callback": b.get("callback", []),
            "location": b.get("location", ""),
            "time_span": b.get("time_span", "")
        })

    # === Assemble BI ===
    bi = {
        "_schema_version": "2.0",
        "_schema_description": p0["project"]["logline"],
        "_last_updated": str(date.today()),
        "_genre": "wuxia",
        "_work_id": "wuxia_heavenly_physician",
        "_family": "wuxguide",
        "_source_tr": canonical_tr_path("wuxia_heavenly_physician", root=ROOT).relative_to(ROOT).as_posix(),
        "_source_phase0": phase0_path.relative_to(ROOT).as_posix(),
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {
                    "title": p0["project"]["title"],
                    "genre_code": p0["project"]["genre_code"],
                    "logline": p0["project"]["logline"],
                    "core_premise": p0["project"]["core_premise"],
                    "total_blocks": 70,
                    "arcs": 7,
                    "blocks_per_arc": 10,
                    "time_span": p0["project"]["time_span"]
                },
                "CoreIdentity": {
                    "protagonist": p0["protagonist"]["name"],
                    "age_at_start": p0["protagonist"]["age_at_start"],
                    "opening_status": p0["protagonist"]["opening_status"],
                    "initial_goal": p0["protagonist"]["initial_goal"],
                    "mid_goal": p0["protagonist"]["mid_goal"],
                    "final_goal": p0["protagonist"]["final_goal"],
                    "true_strength": p0["protagonist"]["true_strength"],
                    "true_weakness": p0["protagonist"]["true_weakness"],
                    "combat_role": p0["protagonist"]["combat_role"]
                },
                "CommercialCode": {
                    "killing_points": [
                        "\uce68\uc774 \uace7 \ubb34\uacf5 \u2014 \uc804\ubb34\ud6c4\ubb34\ud55c \uc804\ud22c \uc2dc\uc2a4\ud15c",
                        "7\ub2e8\uacc4 \uacbd\uc9c0 \ub3c4\ub2ec\uc758 \uce74\ud0c0\ub974\uc2dc\uc2a4",
                        "\uc544\ubc84\uc9c0\uc640\uc758 \ud654\ud574 (B50) \u2014 \uc2dc\ub9ac\uc988 \ucd5c\ub300 \uac10\ub3d9",
                        "\uc2a4\uc2b9 \uc720\uc5b8\uc774 \uc5f4\uc5b4\uc8fc\ub294 \uc0b4\uce68 \uac01\uc131 (B38\u2192B43)",
                        "\ucd5c\uc885\uc804: \uc801\uc744 \uce58\ub8cc\ud558\uba70 \uc774\uae30\ub2e4 (B69)"
                    ],
                    "do_not_fake": pd["do_not_fake"],
                    "taboo_rules": pd["taboo_rules"]
                }
            }
        },
        "protagonist_config": p0["protagonist"],
        "MartialHUD": {
            "_description": "\ubb34\ud611 \uc804\uc6a9 HUD \u2014 \uacbd\uc9c0, \ub0b4\uacf5, \ubb34\uacf5, \uc138\ub825, \uc7a5\ube44\ub97c \ucd94\uc801",
            "Protagonist": {
                "actual_truth": {
                    "name": p0["protagonist"]["name"],
                    "alias": "\ucc9c\uc758\ubb34\uc30d(\u5929\u91ab\u6b66\u96d9)",
                    "age": 28,
                    "rank": "\ucc9c\ud558 \uc720\ub791 \uc758\uc6d0 / \uc9c4\uac00\uc7a5 \u524d \uac00\uc8fc",
                    "martial_status": {
                        "realm": last_me["realm_after"],
                        "realm_history": realm_history,
                        "internal_energy": last_me["internal_energy_after"],
                        "martial_arts": martial_arts_final,
                        "injury_log": major_injuries,
                        "kill_log": [],
                        "kill_count_note": "\uc804 \ube14\ub85d kill_count=0. \uc9c4\uc18c\ubc31\uc740 \ud55c \uba85\ub3c4 \uc8fd\uc774\uc9c0 \uc54a\uc74c. \ube44\uc0b4\uc0c1 \uc6d0\uce59."
                    },
                    "faction_status": {
                        "current_faction": last_me["faction_status"]["affiliation"],
                        "current_rank": last_me["faction_status"]["rank"],
                        "faction_history": faction_history,
                        "ally_factions": ["\ub9c8\uad50(B50~ \ub3d9\ub9f9)", "\ubb34\ub9bc\ub9f9 \ubcf8\uccb4(\ubc18\uc88c\ucc9c\uba85\ud30c)"],
                        "enemy_factions": ["\uc0ac\ud30c \ub3c5\ubb38(\uc18c\uba78)", "\ubb34\ub9bc\ub9f9 \uc554\ubd80(\uc18c\uba78)"]
                    },
                    "equipment": {
                        "weapons": [{
                            "name": "\uc758\uce68(\u91ab\u91dd) \uc138\ud2b8",
                            "grade": "\ucc9c\ud558\uba85\uce68 (\uce60\uc131\uce68\ubc95 \uc804\uc6a9)",
                            "origin": "\ud0dc\uc0b0 \uc11d\uad74 \uace0\ub300 \uc758\uc11c\uc640 \ud568\uaed8 \ubc1c\uacac. \uc758\ubb34\uc77c\uccb4 \uc804\uc6a9 \uae08\uce68."
                        }],
                        "artifacts": [
                            {"name": "\uc758\ub9e5(\u91ab\u8108)", "type": "\uc120\ucc9c \uccb4\uc9c8", "origin": "\uc5b4\uba38\ub2c8\uc5d0\uac8c\uc11c \uc774\uc2dd\ubc1b\uc740 \uc758\ubb34\uc77c\uccb4 \uc120\ucc9c\uc801 \uae30\ubc18"},
                            {"name": "\uace0\ub300 \uc758\uc11c (\uce60\uc131\uce68\ubc95 \uc6d0\uc804)", "type": "\ube44\uae09", "origin": "B22 \ud0dc\uc0b0 \uc11d\uad74 \ubc1c\uacac"},
                            {"name": "\ub3c5\uc5ed \ubc94\uc6a9 \ud574\ub3c5\uc81c", "type": "\uc57d\uc7ac", "origin": "B60 \ud64d\uc5f0 \ud608\uc561 \uae30\ubc18 \uc644\uc131"}
                        ]
                    },
                    "jianghu_reputation": {
                        "jianghu_title": "\ucc9c\uc758\ubb34\uc30d(\u5929\u91ab\u6b66\u96d9) \u2014 \ucc9c\uc758 \uc9c4\uc18c\ubc31",
                        "feared_by": [],
                        "trusted_by": ["\uc9c4\uac00\uc7a5", "\ubb34\ub9bc\ub9f9", "\ub9c8\uad50", "\uc57d\uc655\uace1", "\uac70\ub780 \ucd08\uc6d0", "\uc11c\uc5ed \ucc9c\ucd95"],
                        "rumor_state": "\ucc9c\ud558\ub97c \uc720\ub78c\ud558\uba70 \uce58\ub8cc\ud558\ub294 \uc804\uc124\uc758 \uc758\uc6d0. \ub3c5\uc5ed\uc744 \uc18c\uba78\uc2dc\ud0a8 \ucc9c\uc758."
                    },
                    "current_objective": "\ucc9c\ud558 \uc720\ub78c. \uc758\ubb34\uc77c\uccb4\ub97c \uc804\uc218\ud558\uba70 \ub2e4\uc74c \uc138\ub300\ub97c \uae30\ub974\ub2e4.",
                    "mid_term_goal": "(\ub2ec\uc131) \ub3c5\uc5ed \uce58\ub8cc, \uc758\ubb34\uc77c\uccb4 \uc99d\uba85, \uc544\ubc84\uc9c0 \uad6c\uc6d0",
                    "final_goal": "(\ub2ec\uc131) \ucc9c\uc758 \uacbd\uc9c0. \uc758\uc220\uacfc \ubb34\uacf5\uc758 \uacbd\uacc4\ub97c \ud5c8\ubb3c\uc5b4 \uc0c8 \uae38\uc744 \uc138\uc6c0.",
                    "causal_injuries": "\uc5b4\uba38\ub2c8\uc758 \uc758\ub9e5 \uc774\uc2dd \u2014 \uc758\ubb34\uc77c\uccb4 \ub2a5\ub825\uc758 \uadfc\uc6d0\uc774\uc790 \uc544\ubc84\uc9c0 \ub0c9\ub300\uc758 \uc6d0\uc778"
                },
                "public_reputation": {
                    "identity": "\ucc9c\uc758 \uc9c4\uc18c\ubc31. \uc9c4\uac00\uc7a5 \u524d \uac00\uc8fc. \ucc9c\ud558 \uc720\ub791 \uc758\uc6d0.",
                    "perceived_strength": "\ucc9c\uc758 \uacbd\uc9c0 \u2014 \uc758\ub150\ub9cc\uc73c\ub85c \uce58\ub8cc. \uce68 \uc5c6\uc774\ub3c4 \ubc31 \uba85 \ub3d9\uc2dc \uce58\ub8cc.",
                    "perceived_faction": "\uc9c4\uac00\uc7a5(\uc774\uc591) + \ubb34\ub9bc\ub9f9",
                    "jianghu_credit": "\ucd5c\uace0. \ub3c5\uc5ed \uc18c\uba78, \uc88c\ucc9c\uba85 '\uce58\ub8cc', \ubb34\ub9bc \ub300\uc804 \uc885\uacb0\uc758 \ud575\uc2ec."
                }
            }
        },
        "WorldState": {
            "era": p0["setting"]["era"],
            "region": p0["setting"]["region"],
            "jianghu_order": p0["setting"]["jianghu_order"],
            "martial_doctrine": p0["setting"]["martial_doctrine"],
            "realm_system": pd["realm_path"]["system"],
            "growth_metrics": pd["realm_path"]["growth_metrics"],
            "internal_energy_curve": pd["internal_energy_curve"]["key_points"]
        },
        "GenreRules": {
            "realm_system": pd["realm_path"]["system"],
            "realm_progression": pd["realm_path"]["arc_progression"],
            "taboo_rules": pd["taboo_rules"],
            "do_not_fake": pd["do_not_fake"]
        },
        "AssetLibrary": {"KeyNPCs": pd["npc_timeline"]},
        "FactionMap": pd["faction_map"],
        "Treasures": pd["treasure_path"],
        "Seeds": pd["foreshadow_map"],
        "opponent_transition_plan": pd["opponent_transition_plan"],
        "arcs": pd["arcs"],
        "plot_roadmap": plot_roadmap
    }

    # === Phase 3: Save UTF-8 ===
    output_path = canonical_bi_path("wuxia_heavenly_physician", root=ROOT)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bi, f, ensure_ascii=False, indent=2)

    # === Verify ===
    with open(output_path, "r", encoding="utf-8") as f:
        raw = f.read()
        verify = json.loads(raw)

    v = verify
    mhud = v["MartialHUD"]["Protagonist"]["actual_truth"]
    ci = v["MasterBible"]["ProjectData"]["CoreIdentity"]

    print(f"BI saved: {output_path.relative_to(ROOT).as_posix()}")
    print(f"JSON parse: PASS")
    print(f"plot_roadmap length: {len(v['plot_roadmap'])}")
    print(f"??? count: {raw.count('???')}")
    print(f"FFFD count: {raw.count(chr(0xFFFD))}")
    print(f"realm: {mhud['martial_status']['realm']}")
    print(f"protagonist match: {ci['protagonist'] == mhud['name']}")
    print(f"Title: {v['MasterBible']['ProjectData']['MetaInfo']['title']}")
    print(f"First title: {v['plot_roadmap'][0]['title']}")
    print(f"Last title: {v['plot_roadmap'][-1]['title']}")
    print(f"realm_history: {len(mhud['martial_status']['realm_history'])}")
    print(f"martial_arts: {len(mhud['martial_status']['martial_arts'])}")
    print(f"injury_log: {len(mhud['martial_status']['injury_log'])}")
    print(f"kill_log: {len(mhud['martial_status']['kill_log'])}")
    print(f"Seeds: {len(v['Seeds'])}")
    print(f"KeyNPCs: {len(v['AssetLibrary']['KeyNPCs'])}")
    print(f"File size: {len(raw):,} bytes")

if __name__ == "__main__":
    main()
