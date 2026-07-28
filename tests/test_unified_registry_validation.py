import pytest
from core_engine.validator import Validator

def test_unregistered_language_rejected():
    validator = Validator()
    # The system rejects translation/validation requests for unregistered languages
    data = {
        "module": 1,
        "module_name_en": "Greetings",
        "levels": []
    }
    with pytest.raises(ValueError) as exc:
        validator.validate(data, "level", "unsupported_lang")
    assert "not explicitly registered" in str(exc.value)

def test_automatic_language_detection_character_block():
    validator = Validator()
    
    # Bengali data detection
    bengali_data = {
        "module": 1,
        "module_name_bn": "Bengali Module",
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "BN-L01-I1",
                        "type": "vocabulary",
                        "target": "বাংলা" # Bengali characters
                    }
                ]
            }
        ]
    }
    detected = validator.detect_language(bengali_data)
    assert detected == "bn"

    # Telugu data detection
    telugu_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "TE-L01-I1",
                        "type": "vocabulary",
                        "target": "తెలుగు" # Telugu characters
                    }
                ]
            }
        ]
    }
    detected_te = validator.detect_language(telugu_data)
    assert detected_te == "te"

def test_script_boundary_violation_fails_closed():
    validator = Validator()
    
    # Spanish data containing Telugu letter in target
    invalid_spanish_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "ES-L01-I1",
                        "type": "vocabulary",
                        "target": "hola తె", # 'తె' is Telugu, violating Spanish boundaries!
                        "attributes": {}
                    }
                ]
            }
        ]
    }
    with pytest.raises(ValueError) as exc:
        validator.validate(invalid_spanish_data, "level", "es")
    assert "Script boundary violation" in str(exc.value)

def test_structured_fallback_profile_applied():
    validator = Validator()
    profile = validator.get_profile("es")
    assert profile["script_traits"]["is_abugida"] is False
    assert profile["permitted_genders"] == ["masculine", "feminine"]
