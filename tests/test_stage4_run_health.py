from modules.core.stage4_run_health import classify_stage4_run_health


def test_stage4_run_health_classifies_pure_pass():
    health = classify_stage4_run_health(
        attempt_artifact_meta={
            "attempt_num": 1,
            "artifact_path": "logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt",
            "final_verdict": "PASS",
        }
    )

    assert health["success_class"] == "pure_pass"
    assert health["success_classes"] == ["pure_pass"]
    assert health["pure_pass"] is True
    assert health["repaired_pass"] is False
    assert health["retry_heavy_pass"] is False


def test_stage4_run_health_classifies_retry_heavy_pass_from_path():
    health = classify_stage4_run_health(
        attempt_artifact_meta={
            "artifact_path": "logs/artifacts/stage4/ep_0010/attempt_05/final_manuscript__A.txt",
            "final_verdict": "PASS",
        }
    )

    assert health["success_class"] == "retry_heavy_pass"
    assert health["success_classes"] == ["retry_heavy_pass"]
    assert health["attempt_num"] == 5
    assert health["retry_heavy_pass"] is True


def test_stage4_run_health_classifies_repaired_pass():
    health = classify_stage4_run_health(
        attempt_artifact_meta={
            "attempt_num": 1,
            "artifact_path": "logs/artifacts/stage4/ep_0015/attempt_01/patched_after_fix__A.txt",
            "initial_verdict": "PASS_WITH_FIX",
            "final_verdict": "PASS",
        }
    )

    assert health["success_class"] == "repaired_pass"
    assert health["success_classes"] == ["repaired_pass"]
    assert health["repaired_pass"] is True
    assert health["artifact_class"] == "patched_after_fix"


def test_stage4_run_health_allows_repaired_and_retry_heavy_flags():
    health = classify_stage4_run_health(
        attempt_artifact_meta={
            "attempt_num": 5,
            "artifact_path": "logs/artifacts/stage4/ep_0012/attempt_05/patched_after_fix__A.txt",
            "patch_strategy": "inplace",
            "final_verdict": "PASS",
        }
    )

    assert health["success_class"] == "repaired_pass"
    assert health["success_classes"] == ["repaired_pass", "retry_heavy_pass"]
    assert health["repaired_pass"] is True
    assert health["retry_heavy_pass"] is True


def test_stage4_run_health_does_not_overclaim_pure_without_attempt_metadata():
    health = classify_stage4_run_health()

    assert health["success_class"] == "accepted_pass"
    assert health["success_classes"] == ["accepted_pass"]
    assert health["pure_pass"] is False
    assert health["repaired_pass"] is False
    assert health["retry_heavy_pass"] is False
