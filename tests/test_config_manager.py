"""[Phase 5-B] ConfigManager settings loader 단위 테스트

검증 대상 (5-B-1):
- validation.yaml 로드 성공 / 파싱 실패 방어
- 점(.) 구분 키 탐색 (get_guard_threshold, get_validation_policy)
- 누락 키 fallback / 타입 불일치 방어
- 캐시 동작 (cache + invalidate + force_reload)
- feature_flags 조회 / 기존 API 회귀

검증 대상 (5-B-2a):
- _threshold() 모듈 헬퍼를 통한 blocking/scoring 임계값 override 경로
- YAML 없는 경우 기존 하드코드 값 유지
- YAML 값 있는 경우 override 적용
"""

from pathlib import Path

from modules.core.config_manager import ConfigManager


def _write_validation_yaml(root: Path, body: str) -> None:
    settings_dir = root / "config" / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    (settings_dir / "validation.yaml").write_text(body, encoding="utf-8")


def test_load_settings_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.load_settings() == {}


def test_load_settings_reads_yaml(tmp_path, monkeypatch):
    _write_validation_yaml(
        tmp_path,
        "manuscript:\n  min_length: 4000\nfeature_flags:\n  enable_patch_mode: true\n",
    )
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    data = cm.load_settings()
    assert data["manuscript"]["min_length"] == 4000
    assert data["feature_flags"]["enable_patch_mode"] is True


def test_get_guard_threshold_returns_default_on_missing_key(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_guard_threshold("manuscript.unknown", 123) == 123


def test_get_guard_threshold_type_mismatch_fallback(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: oops\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_guard_threshold("manuscript.min_length", 4000) == 4000


def test_get_guard_threshold_numeric_coercion(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "thresholds:\n  hud_change: 1\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    value = cm.get_guard_threshold("thresholds.hud_change", 0.1)
    assert value == 1.0


def test_get_validation_policy_alias(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "retry:\n  writer_max_attempts: 5\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_validation_policy("retry.writer_max_attempts", 3) == 5


def test_get_feature_flag_bool(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "feature_flags:\n  enable_npc_history: true\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_feature_flag("enable_npc_history", False) is True


def test_get_feature_flag_type_mismatch_fallback(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "feature_flags:\n  enable_npc_history: 1\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_feature_flag("enable_npc_history", False) is False


def test_cache_and_invalidate(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()

    assert cm.get_guard_threshold("manuscript.min_length", 0) == 4000

    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 3500\n")
    # Cache still active
    assert cm.get_guard_threshold("manuscript.min_length", 0) == 4000

    cm.invalidate_settings_cache()
    assert cm.get_guard_threshold("manuscript.min_length", 0) == 3500


def test_force_reload_bypasses_cache(tmp_path, monkeypatch):
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.load_settings()["manuscript"]["min_length"] == 4000

    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 1234\n")
    assert cm.load_settings(force_reload=True)["manuscript"]["min_length"] == 1234


def test_malformed_yaml_returns_empty(tmp_path, monkeypatch):
    """잘못된 YAML 구문 → 빈 dict (비차단)"""
    _write_validation_yaml(tmp_path, "invalid: yaml: content: [broken")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.load_settings() == {}


def test_nested_three_levels(tmp_path, monkeypatch):
    """3단계 중첩 키 조회"""
    _write_validation_yaml(
        tmp_path,
        "scoring:\n  genre_thresholds:\n    wuxia: 70\n    hunter: 68\n",
    )
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.get_guard_threshold("scoring.genre_thresholds.hunter", 99) == 68


def test_none_default_accepts_any_type(tmp_path, monkeypatch):
    """default=None이면 타입 체크 스킵"""
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 4000\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.get_guard_threshold("manuscript.min_length") == 4000


def test_existing_api_model_lookup(tmp_path, monkeypatch):
    """기존 get_model_for_agent 회귀"""
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.get_model_for_agent("writer") == "gemini-3.1-pro-preview"
    assert cm.get_model_for_agent("unknown_agent") == "gemini-2.5-flash"


def test_existing_api_getitem(tmp_path, monkeypatch):
    """기존 subscript 접근 회귀"""
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm["limits"]["target_manuscript_length"] == 5000


def test_missing_feature_flag_default(tmp_path, monkeypatch):
    """없는 플래그 → custom default"""
    _write_validation_yaml(tmp_path, "feature_flags:\n  a: true\n")
    monkeypatch.chdir(tmp_path)
    cm = ConfigManager()
    assert cm.get_feature_flag("nonexistent", default=True) is True
    assert cm.get_feature_flag("nonexistent") is False


# ══════════════════════════════════════════════════════════════
# [Phase 5-B-2a] _threshold() 모듈 헬퍼 통합 테스트
# ══════════════════════════════════════════════════════════════


def test_blocking_threshold_no_yaml_uses_default(tmp_path, monkeypatch):
    """YAML 없을 때 blocking _threshold()가 기존 하드코드값 반환"""
    monkeypatch.chdir(tmp_path)
    # _threshold 캐시 초기화
    import modules.validation.blocking_validator as bv

    if hasattr(bv._threshold, "_cfg"):
        del bv._threshold._cfg

    from modules.core.constants import ManuscriptLimits

    result = bv._threshold("manuscript.min_length", ManuscriptLimits.MIN_LENGTH)
    assert result == 4000


def test_blocking_threshold_yaml_override(tmp_path, monkeypatch):
    """YAML 값이 있으면 override 적용"""
    monkeypatch.chdir(tmp_path)
    _write_validation_yaml(tmp_path, "manuscript:\n  min_length: 3000\n")

    import modules.validation.blocking_validator as bv

    if hasattr(bv._threshold, "_cfg"):
        del bv._threshold._cfg

    result = bv._threshold("manuscript.min_length", 4000)
    assert result == 3000


def test_scoring_threshold_no_yaml_uses_default(tmp_path, monkeypatch):
    """YAML 없을 때 scoring _threshold()가 기존 하드코드값 반환"""
    monkeypatch.chdir(tmp_path)

    import modules.validation.scoring_validator as sv

    if hasattr(sv._threshold, "_cfg"):
        del sv._threshold._cfg

    result = sv._threshold("scoring.default_pass_threshold", 70)
    assert result == 70


def test_scoring_threshold_yaml_override(tmp_path, monkeypatch):
    """YAML로 scoring 임계값 override"""
    monkeypatch.chdir(tmp_path)
    _write_validation_yaml(
        tmp_path,
        "scoring:\n  default_pass_threshold: 65\n  genre_thresholds:\n    wuxia: 60\n",
    )

    import modules.validation.scoring_validator as sv

    if hasattr(sv._threshold, "_cfg"):
        del sv._threshold._cfg

    assert sv._threshold("scoring.default_pass_threshold", 70) == 65
    assert sv._threshold("scoring.genre_thresholds.wuxia", 70) == 60


def test_threshold_type_mismatch_uses_default(tmp_path, monkeypatch):
    """YAML 타입 불일치 시 기존값 fallback"""
    monkeypatch.chdir(tmp_path)
    _write_validation_yaml(tmp_path, 'scene:\n  min_count: "four"\n')

    import modules.validation.blocking_validator as bv

    if hasattr(bv._threshold, "_cfg"):
        del bv._threshold._cfg

    result = bv._threshold("scene.min_count", 4)
    assert result == 4  # str이므로 int default로 fallback


# ══════════════════════════════════════════════════════════════
# [Phase 5-B-2b] continuity/advisory _threshold() 통합 테스트
# ══════════════════════════════════════════════════════════════


def test_continuity_proximity_no_yaml_default(tmp_path, monkeypatch):
    """YAML 없을 때 continuity proximity 기존값 150 유지"""
    monkeypatch.chdir(tmp_path)

    import modules.validation.continuity_validator as cv

    if hasattr(cv._threshold, "_cfg"):
        del cv._threshold._cfg

    assert cv._threshold("continuity.personality_proximity", 150) == 150


def test_continuity_proximity_yaml_override(tmp_path, monkeypatch):
    """YAML로 personality_proximity override"""
    monkeypatch.chdir(tmp_path)
    _write_validation_yaml(tmp_path, "continuity:\n  personality_proximity: 200\n")

    import modules.validation.continuity_validator as cv

    if hasattr(cv._threshold, "_cfg"):
        del cv._threshold._cfg

    assert cv._threshold("continuity.personality_proximity", 150) == 200


def test_advisory_max_suggestions_no_yaml_default(tmp_path, monkeypatch):
    """YAML 없을 때 advisory max_suggestions 기존값 5 유지"""
    monkeypatch.chdir(tmp_path)

    import modules.validation.advisory_validator as av

    if hasattr(av._threshold, "_cfg"):
        del av._threshold._cfg

    assert av._threshold("advisory.max_suggestions", 5) == 5


def test_advisory_max_suggestions_yaml_override(tmp_path, monkeypatch):
    """YAML로 advisory max_suggestions override"""
    monkeypatch.chdir(tmp_path)
    _write_validation_yaml(tmp_path, "advisory:\n  max_suggestions: 10\n")

    import modules.validation.advisory_validator as av

    if hasattr(av._threshold, "_cfg"):
        del av._threshold._cfg

    assert av._threshold("advisory.max_suggestions", 5) == 10
