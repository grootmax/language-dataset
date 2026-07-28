import os
import json
import pytest
from core_engine.validator import Validator
from plugins.base import BasePlugin

def test_fallback_validation_with_dutch_profile(monkeypatch):
    """
    Test that the Dutch profile is loaded from the JSON config and validated using the
    parametric fallback plugin (valid cases and invalid cases for genders).
    """
    # Ensure strict mode is off (or not affecting)
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)

    validator = Validator()

    valid_dutch_data = {
        "module": 1,
        "module_name_en": "Dutch Greetings",
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "NL-L01-I01",
                        "type": "noun",
                        "target": "boek",
                        "read_as": "boek",
                        "attributes": {
                            "gender": "neuter"  # valid according to dutch.json
                        }
                    }
                ]
            }
        ]
    }

    # Should succeed
    normalized = validator.validate(valid_dutch_data, "level", "dutch")
    assert normalized["levels"][0]["items"][0]["attributes"]["gender"] == "neuter"


def test_fallback_validation_with_dutch_profile_invalid_gender(monkeypatch):
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)
    validator = Validator()

    invalid_dutch_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "NL-L01-I02",
                        "type": "noun",
                        "target": "boek",
                        "read_as": "boek",
                        "attributes": {
                            "gender": "masculine"  # invalid according to dutch.json (only common, neuter)
                        }
                    }
                ]
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        validator.validate(invalid_dutch_data, "level", "dutch")
    assert "has invalid gender" in str(exc_info.value)


def test_fallback_validation_with_dutch_profile_missing_gender(monkeypatch):
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)
    validator = Validator()

    missing_gender_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "NL-L01-I03",
                        "type": "noun",
                        "target": "boek",
                        "read_as": "boek",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        validator.validate(missing_gender_data, "level", "dutch")
    assert "is missing grammatical gender under generic attributes block" in str(exc_info.value)


def test_strict_mode_raise_on_missing_profile(monkeypatch):
    """
    Strict validation mode should raise FileNotFoundError when profile/plugin is missing.
    """
    monkeypatch.setenv("STRICT_VALIDATION", "true")
    validator = Validator()

    # 'pseudolang' has neither plugin nor profile
    with pytest.raises(FileNotFoundError) as exc_info:
        validator.load_plugin("pseudolang")
    assert "Configuration profile for language 'pseudolang' is missing" in str(exc_info.value)


def test_production_fallback_no_raise_on_missing_profile(monkeypatch):
    """
    In production (strict mode false/unset), missing profile should not raise an error.
    """
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)
    validator = Validator()

    # Should not raise, should return None and let validation proceed without plugin
    plugin = validator.load_plugin("pseudolang")
    assert plugin is None

    # Validator validate should run without raising terminal errors
    generic_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "GEN-I1",
                        "type": "word",
                        "target": "hello",
                        "read_as": "hello"
                    }
                ]
            }
        ]
    }
    normalized = validator.validate(generic_data, "level", "pseudolang")
    assert normalized == generic_data


def test_strict_mode_raise_on_invalid_profile_json(monkeypatch, tmp_path):
    """
    Under strict mode, an unparseable or faulty JSON configuration file should raise ValueError.
    """
    monkeypatch.setenv("STRICT_VALIDATION", "true")
    validator = Validator()

    # Let's write an invalid JSON profile for 'brokenlang'
    profiles_dir = "/app/profiles"
    broken_profile_path = os.path.join(profiles_dir, "brokenlang.json")
    
    with open(broken_profile_path, "w", encoding="utf-8") as f:
        f.write("{invalid-json-content}")

    try:
        with pytest.raises(ValueError) as exc_info:
            validator.load_plugin("brokenlang")
        assert "Failed to load or parse profile" in str(exc_info.value)
    finally:
        if os.path.exists(broken_profile_path):
            os.remove(broken_profile_path)


def test_fallback_script_validations_telugu(monkeypatch):
    """
    The Telugu profile should execute Telugu character set validation.
    """
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)
    validator = Validator()

    # Telugu unicode range: \u0c00 to \u0c7f
    valid_telugu = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "TE-I1",
                        "type": "vocabulary",
                        "target": "తెలుగు", # valid Telugu characters
                        "read_as": "telugu",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    # Should succeed
    normalized = validator.validate(valid_telugu, "level", "telugu")
    assert normalized is not None

    # Invalid Telugu target (contains no Telugu characters, e.g. English text)
    invalid_telugu = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "TE-I2",
                        "type": "vocabulary",
                        "target": "EnglishTextOnly",
                        "read_as": "telugu",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        validator.validate(invalid_telugu, "level", "telugu")
    assert "does not contain Telugu characters" in str(exc_info.value)


def test_fallback_script_validations_bengali(monkeypatch):
    """
    The Bengali profile should execute Bengali character set validation.
    """
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)
    validator = Validator()

    # Bengali unicode range: \u0980 to \u09ff
    valid_bengali = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "BN-I1",
                        "type": "vocabulary",
                        "target": "বাংলা", # valid Bengali characters
                        "read_as": "bangla",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    # Should succeed
    normalized = validator.validate(valid_bengali, "level", "bengali")
    assert normalized is not None

    # Invalid Bengali target (contains no Bengali characters)
    invalid_bengali = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "BN-I2",
                        "type": "vocabulary",
                        "target": "EnglishTextOnly",
                        "read_as": "bangla",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        validator.validate(invalid_bengali, "level", "bengali")
    assert "does not contain Bengali characters" in str(exc_info.value)


def test_fallback_script_validations_marathi(monkeypatch):
    """
    The Marathi profile should execute Devanagari character set validation.
    """
    monkeypatch.delenv("STRICT_VALIDATION", raising=False)
    validator = Validator()

    # Marathi/Devanagari unicode range: \u0900 to \u097f
    valid_marathi = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "MR-I1",
                        "type": "vocabulary",
                        "target": "मराठी", # valid Marathi characters (Devanagari)
                        "read_as": "marathi",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    # Should succeed
    normalized = validator.validate(valid_marathi, "level", "marathi")
    assert normalized is not None

    # Invalid Marathi target (contains no Devanagari characters)
    invalid_marathi = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "MR-I2",
                        "type": "vocabulary",
                        "target": "EnglishTextOnly",
                        "read_as": "marathi",
                        "attributes": {}
                    }
                ]
            }
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        validator.validate(invalid_marathi, "level", "marathi")
    assert "does not contain Devanagari characters" in str(exc_info.value)


def test_no_custom_python_files_for_fallback_languages():
    """
    Confirms that no custom python plugin files exist for Marathi, Bengali, Telugu, and Dutch,
    guaranteeing they only use parametric fallback configs.
    """
    plugins_dir = "/app/plugins"
    for lang in ("marathi", "bengali", "telugu", "dutch"):
        py_file = os.path.join(plugins_dir, f"{lang}_plugin.py")
        assert not os.path.exists(py_file), f"Plugin file '{py_file}' should not exist! Category A languages must only use JSON fallback profiles."


def test_automatic_detection_from_script_boundaries():
    """
    Verifies that the validator automatically detects Telugu and Bengali by their scripts.
    """
    validator = Validator()

    # Telugu content
    telugu_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "TE-AUTO",
                        "type": "vocabulary",
                        "target": "తెలుగు",
                        "read_as": "telugu"
                    }
                ]
            }
        ]
    }
    assert validator.detect_language(telugu_data) == "telugu"

    # Bengali content
    bengali_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "BN-AUTO",
                        "type": "vocabulary",
                        "target": "বাংলা",
                        "read_as": "bangla"
                    }
                ]
            }
        ]
    }
    assert validator.detect_language(bengali_data) == "bengali"


def test_automatic_detection_from_configuration_keys():
    """
    Verifies that the validator automatically detects languages based on custom keys/metadata.
    """
    validator = Validator()

    # Marathi metadata
    marathi_data = {
        "module": 1,
        "module_name_mr": "Marathi Course",
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "MR-AUTO",
                        "type": "vocabulary",
                        "target": "मराठी",
                        "read_as": "marathi"
                    }
                ]
            }
        ]
    }
    assert validator.detect_language(marathi_data) == "marathi"
