import pytest
import os
import json
from translation_engine.translator import adapt_phonetics, simulate_translation, CurriculumTranslator

def test_adapt_phonetics():
    # Test German phonetic adaptations: sh -> sch, ch -> tsch, etc.
    assert adapt_phonetics("garam chaaval", "de") == "garam tschaawal"
    # Test Arabic phonetic adaptations: sh -> ش
    assert adapt_phonetics("shukriya", "ar") == "شukriya"
    # Test fallback/unsupported or empty cases
    assert adapt_phonetics(None, "de") is None
    assert adapt_phonetics("hello", "invalid") == "hello"

def test_simulate_translation_keys_and_values():
    raw_dict = {
        "title_en": "The first vowels",
        "gloss_en": "vowels",
        "example_word": {
            "hindi": "अनार",
            "read_as": "anaar",
            "english": "pomegranate"
        },
        "tags": ["vowel"]
    }
    
    translated = simulate_translation(raw_dict, "es")
    
    # Check that '_en' key was renamed to '_es'
    assert "title_es" in translated
    assert "title_en" not in translated
    # Check that contents have the [ES] prefix
    assert translated["title_es"] == "[ES] The first vowels"
    
    # Check that 'english' was renamed to 'es'
    example_word = translated["example_word"]
    assert "es" in example_word
    assert "english" not in example_word
    assert example_word["es"] == "[ES] pomegranate"
    
    # Check that non-translate keys (like tags, hindi, read_as) are untouched
    assert translated["tags"] == ["vowel"]
    assert example_word["hindi"] == "अनार"
    assert example_word["read_as"] == "anaar"

def test_translator_file_run(tmp_path):
    source_content = {
        "module": 1,
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "title_en": "The first three vowels",
                "title_hi": "अ आ इ",
                "is_micro_dialogue_level": False,
                "items": [
                    {
                        "id": "M01-L01-I1",
                        "type": "letter",
                        "target": "अ",
                        "read_as": "a",
                        "tags": ["vowel"],
                        "example_word": { "hindi": "अनार", "read_as": "anaar", "english": "pomegranate" },
                        "cards": {
                            "learn": {
                                "title_en": "Learn",
                                "explanation_en": "Learn Exp",
                                "examples": [
                                    { "hindi": "अनार", "read_as": "anaar", "english": "pomegranate" }
                                ]
                            },
                            "practice": {
                                "format": "hear_it_pick_letter",
                                "prompt_en": "Prompt",
                                "question": "अनार",
                                "options": ["अ", "आ"],
                                "answer_index": 0
                            },
                            "game": {
                                "format": "odd_sound_out",
                                "question_en": "Game Q",
                                "options": ["अनार", "अब"],
                                "answer_index": 1
                            }
                        },
                        "audio": {
                            "tts_strings": ["अ"],
                            "requires_recording": False
                        }
                    },
                    {
                        "id": "M01-L01-I2",
                        "type": "letter",
                        "target": "आ",
                        "read_as": "aa",
                        "tags": ["vowel"],
                        "example_word": { "hindi": "आम", "read_as": "aam", "english": "mango" },
                        "cards": {
                            "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                            "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                            "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                        },
                        "audio": { "tts_strings": [], "requires_recording": False }
                    },
                    {
                        "id": "M01-L01-I3",
                        "type": "letter",
                        "target": "इ",
                        "read_as": "i",
                        "tags": ["vowel"],
                        "example_word": { "hindi": "इमली", "read_as": "imlii", "english": "tamarind" },
                        "cards": {
                            "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                            "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                            "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                        },
                        "audio": { "tts_strings": [], "requires_recording": False }
                    }
                ],
                "summary": {
                    "recap_en": "Recap",
                    "key_forms": ["अ", "आ", "इ"],
                    "next_up_en": "Next"
                }
            }
        ]
    }
    
    source_file = tmp_path / "module01_levels01-05.json"
    with open(source_file, "w", encoding="utf-8") as f:
        json.dump(source_content, f)
        
    dest_file = tmp_path / "module01_levels01-05_es.json"
    
    translator = CurriculumTranslator("es")
    success = translator.translate_file(str(source_file), str(dest_file), use_simulation=True)
    
    assert success is True
    assert os.path.exists(dest_file)
    
    # Read output and verify
    with open(dest_file, "r", encoding="utf-8") as f:
        dest_content = json.load(f)
        
    assert dest_content["module"] == 1
    assert "module_name_es" not in dest_content # was not present in original, so not created unless configured
    assert dest_content["levels"][0]["title_es"] == "[ES] The first three vowels"
    assert "title_en" not in dest_content["levels"][0]

def test_dynamic_language_addition_and_translation(tmp_path):
    # This tests "Scenario: Open-Ended Language Addition" and "Scenario: Seamless Localization Generation"
    new_profile_path = "/app/profiles/zz.json"
    new_profile_content = {
        "language": "zzlang",
        "permitted_genders": ["masculine", "feminine", "common"],
        "active_phonetic_systems": [],
        "script_traits": {
            "is_abugida": False,
            "has_matra": False,
            "has_sound_family": False,
            "has_tones": False,
            "has_word_masks": False
        }
    }
    
    try:
        with open(new_profile_path, "w", encoding="utf-8") as f:
            json.dump(new_profile_content, f)
            
        from translation_engine import prompts
        prompts.NAME_TO_ISO["zzlang"] = "zz"
        prompts.ISO_TO_NAME["zz"] = "Zzlang"
        prompts.LANGUAGES = prompts.compile_languages_registry()
        
        assert "zz" in prompts.LANGUAGES
        
        source_content = {
            "module": 1,
            "phase": 1,
            "levels": [
                {
                    "level": 1,
                    "title_en": "Level Title",
                    "title_hi": "Title Hi",
                    "is_micro_dialogue_level": False,
                    "items": [
                        {
                            "id": "M01-L01-I1",
                            "type": "letter",
                            "target": "अ",
                            "read_as": "a",
                            "tags": ["vowel"],
                            "example_word": { "hindi": "अनार", "read_as": "anaar", "english": "pomegranate" },
                            "cards": {
                                "learn": {
                                    "title_en": "Learn",
                                    "explanation_en": "Learn Exp",
                                    "examples": [
                                        { "hindi": "अनार", "read_as": "anaar", "english": "pomegranate" }
                                    ]
                                },
                                "practice": {
                                    "format": "hear_it_pick_letter",
                                    "prompt_en": "Prompt",
                                    "question": "अनार",
                                    "options": ["अ", "आ"],
                                    "answer_index": 0
                                },
                                "game": {
                                    "format": "odd_sound_out",
                                    "question_en": "Game Q",
                                    "options": ["अनार", "अब"],
                                    "answer_index": 1
                                }
                            },
                            "audio": {
                                "tts_strings": ["अ"],
                                "requires_recording": False
                            }
                        },
                        {
                            "id": "M01-L01-I2",
                            "type": "letter",
                            "target": "आ",
                            "read_as": "aa",
                            "tags": ["vowel"],
                            "example_word": { "hindi": "आम", "read_as": "aam", "english": "mango" },
                            "cards": {
                                "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                                "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                                "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                            },
                            "audio": { "tts_strings": [], "requires_recording": False }
                        },
                        {
                            "id": "M01-L01-I3",
                            "type": "letter",
                            "target": "इ",
                            "read_as": "i",
                            "tags": ["vowel"],
                            "example_word": { "hindi": "इमली", "read_as": "imlii", "english": "tamarind" },
                            "cards": {
                                "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                                "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                                "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                            },
                            "audio": { "tts_strings": [], "requires_recording": False }
                        }
                    ],
                    "summary": {
                        "recap_en": "Recap",
                        "key_forms": ["अ", "आ", "इ"],
                        "next_up_en": "Next"
                    }
                }
            ]
        }
        
        source_file = tmp_path / "module01_levels01-05.json"
        with open(source_file, "w", encoding="utf-8") as f:
            json.dump(source_content, f)
            
        dest_file = tmp_path / "module01_levels01-05_zz.json"
        
        translator = CurriculumTranslator("zz")
        success = translator.translate_file(str(source_file), str(dest_file), use_simulation=True)
        assert success is True
        assert os.path.exists(dest_file)
        
        with open(dest_file, "r", encoding="utf-8") as f:
            dest_content = json.load(f)
        assert "title_zz" in dest_content["levels"][0]
        
    finally:
        if os.path.exists(new_profile_path):
            os.remove(new_profile_path)
        from translation_engine import prompts
        prompts.NAME_TO_ISO.pop("zzlang", None)
        prompts.ISO_TO_NAME.pop("zz", None)
        prompts.LANGUAGES = prompts.compile_languages_registry()
