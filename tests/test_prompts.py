import pytest
from translation_engine.prompts import LANGUAGES, get_prompt_template

def test_languages_config():
    # Verify that all 10 target languages exist and are fully configured
    expected_languages = {"es", "fr", "de", "ja", "zh", "ko", "it", "pt", "ru", "ar", "te"}
    assert set(LANGUAGES.keys()) == expected_languages
    
    for code, lang in LANGUAGES.items():
        assert "name" in lang
        assert "phonetic_adaptations" in lang
        assert "grammar_gender_benchmarks" in lang
        assert "instructional_rules" in lang
        assert isinstance(lang["phonetic_adaptations"], dict)

def test_get_prompt_template():
    for code in LANGUAGES.keys():
        prompt = get_prompt_template(code, "level")
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert LANGUAGES[code]["name"] in prompt
        assert code in prompt
        
    with pytest.raises(ValueError):
        get_prompt_template("invalid_code", "level")
