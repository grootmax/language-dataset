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

def test_telugu_phonetic_adaptation():
    # Test valid syllabic transliteration outputs in Telugu
    assert adapt_phonetics("anaar", "te") == "అనార్"
    assert adapt_phonetics("aam", "te") == "ఆమ్"
    assert adapt_phonetics("paanii", "te") == "పానీ"
    assert adapt_phonetics("namastee", "te") == "నమస్తే"
    assert adapt_phonetics("namaste", "te") == "నమస్తె"
    assert adapt_phonetics("shukriya", "te") == "శుక్రియ"
    
    # Test filtering out comments
    assert adapt_phonetics("anaar # delicious fruit", "te") == "అనార్"
    assert adapt_phonetics("aam // mango", "te") == "ఆమ్"
    assert adapt_phonetics("paanii (water)", "te") == "పానీ"
    
    # Test filtering out single-letter vowels
    assert adapt_phonetics("a", "te") == "a"
    assert adapt_phonetics("i", "te") == "i"

