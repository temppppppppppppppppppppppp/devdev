from modules.core.inventory_state import compute_inventory_count_deltas, normalize_inventory_counts


def test_normalize_inventory_counts_merges_suffix_counts_and_dict_counts():
    raw = [
        "트레이딩용 컴퓨터 3대",
        {"name": "모니터", "count": 2},
        {"노트북": 1},
        "모니터",
    ]

    counts = normalize_inventory_counts(raw)

    assert counts == {
        "노트북": 1,
        "모니터": 3,
        "트레이딩용 컴퓨터": 3,
    }


def test_compute_inventory_count_deltas_reports_missing_and_growth():
    deltas = compute_inventory_count_deltas(
        {"트레이딩용 컴퓨터": 2, "모니터": 3},
        {"트레이딩용 컴퓨터": 3},
    )

    assert deltas == [
        {"name": "모니터", "from": 3, "to": 0, "delta": -3},
        {"name": "트레이딩용 컴퓨터", "from": 2, "to": 3, "delta": 1},
    ]
