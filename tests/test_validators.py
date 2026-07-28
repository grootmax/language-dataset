import pytest
from translation_engine.validators import (
    validate_json_schema,
    validate_card_math,
    validate_mock_exam_weights,
    validate_checkpoint_integrity,
    validate_final_exam_weights,
    ValidationError
)

def test_validate_card_math_valid():
    valid_data = {
        "module": 1,
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "title_en": "Test Level 1",
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
                                "title_en": "Learn Card",
                                "explanation_en": "Explanation",
                                "examples": [
                                    { "hindi": "अनार", "read_as": "anaar", "english": "pomegranate" }
                                ]
                            },
                            "practice": {
                                "format": "hear_it_pick_letter",
                                "prompt_en": "Practice Prompt",
                                "question": "अनार",
                                "options": ["अ", "आ"],
                                "answer_index": 0
                            },
                            "game": {
                                "format": "odd_sound_out",
                                "question_en": "Game Question",
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
                    "recap_en": "Summary recap",
                    "key_forms": ["अ", "आ", "इ"],
                    "next_up_en": "Next level"
                }
            }
        ]
    }
    
    assert validate_card_math(valid_data) is True
    # Should also pass JSON schema validation
    validate_json_schema(valid_data, "level")

def test_validate_card_math_invalid_items_count():
    invalid_data = {
        "module": 1,
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    { "id": "M01-L01-I1", "cards": {} },
                    { "id": "M01-L01-I2", "cards": {} }
                ],
                "summary": { "key_forms": [] }
            }
        ]
    }
    with pytest.raises(ValidationError, match="violated Card Math: has 2 items, expected exactly 3"):
        validate_card_math(invalid_data)

def test_validate_card_math_invalid_cards():
    invalid_data = {
        "module": 1,
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "M01-L01-I1",
                        "cards": {
                            "learn": {},
                            "practice": {} # missing game card
                        }
                    },
                    { "id": "M01-L01-I2", "cards": { "learn": {}, "practice": {}, "game": {} } },
                    { "id": "M01-L01-I3", "cards": { "learn": {}, "practice": {}, "game": {} } }
                ],
                "summary": { "key_forms": [] }
            }
        ]
    }
    with pytest.raises(ValidationError, match="violated Card Math: has cards .* expected exactly 'learn', 'practice', and 'game'"):
        validate_card_math(invalid_data)

def test_validate_card_math_missing_summary():
    invalid_data = {
        "module": 1,
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "items": []
            }
        ]
    }
    with pytest.raises(ValidationError, match="missing its level summary card under 'summary'"):
        validate_card_math(invalid_data)

def test_validate_checkpoint_integrity():
    valid_cp = {
        "module": 1,
        "checkpoints": [
            {
                "checkpoint": 1,
                "after_level": 5,
                "covers_levels": [1, 2, 3, 4, 5],
                "questions": [{} for _ in range(10)]
            }
        ]
    }
    assert validate_checkpoint_integrity(valid_cp) is True
    
    invalid_cp = {
        "module": 1,
        "checkpoints": [
            {
                "checkpoint": 1,
                "after_level": 5,
                "covers_levels": [1, 2, 3, 4, 5],
                "questions": [{} for _ in range(9)] # violated: 9 instead of 10
            }
        ]
    }
    with pytest.raises(ValidationError, match="violated Card Math standard: contains 9 questions, expected exactly 10"):
        validate_checkpoint_integrity(invalid_cp)

def test_validate_mock_exam_weights():
    # Module 1 (20 Q, 100% current)
    valid_m1_mock = {
        "module": 1,
        "kind": "mock_exam",
        "mock_exam": {
            "total_questions": 20,
            "questions": [
                {
                    "id": f"M01-MOCK-Q{i}",
                    "source_item_ids": ["M01-L01-I1"],
                    "type": "recognition",
                    "options": ["O"],
                    "answer_index": 0,
                    "prompt_en": "P",
                    "explanation_en": "E"
                } for i in range(20)
            ]
        }
    }
    assert validate_mock_exam_weights(valid_m1_mock) is True
    
    # Invalid: Module 1 mock has questions from other modules
    invalid_m1_mock = {
        "module": 1,
        "kind": "mock_exam",
        "mock_exam": {
            "total_questions": 20,
            "questions": [
                {
                    "id": "M01-MOCK-Q1",
                    "source_item_ids": ["M02-L01-I1"], # M02 is not current for M1
                    "type": "recognition",
                    "options": ["O"],
                    "answer_index": 0
                } for _ in range(20)
            ]
        }
    }
    with pytest.raises(ValidationError, match="Module 1 mock exam must be 100% current module questions"):
        validate_mock_exam_weights(invalid_m1_mock)

def test_validate_mock_exam_weights_m5():
    # Module 5 (30 Q: 21 current (70%), 9 previous (30%), at least 3 critical (10%))
    valid_m5_mock = {
        "module": 5,
        "kind": "mock_exam",
        "mock_exam": {
            "total_questions": 30,
            "questions": [
                {
                    "id": f"M05-MOCK-Q{i}",
                    "source_item_ids": ["M05-L01-I1"],
                    "type": "recognition",
                    "options": ["O"],
                    "answer_index": 0
                } for i in range(21)
            ] + [
                {
                    "id": f"M05-MOCK-Q{i}",
                    "source_item_ids": ["M04-L01-I1"],
                    "type": "recognition",
                    "options": ["O"],
                    "answer_index": 0,
                    "explanation_en": "gender oblique marker" # critical keyword
                } for i in range(21, 30)
            ]
        }
    }
    assert validate_mock_exam_weights(valid_m5_mock) is True

def test_dynamic_validation_keys_level_german():
    german_data = {
        "module": 1,
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "title_en": "Test Level 1",
                "is_micro_dialogue_level": False,
                "items": [
                    {
                        "id": "M01-L01-I1",
                        "type": "letter",
                        "target": "A",
                        "read_as": "a",
                        "pronunciation_notes": "None",
                        "tags": ["vowel"],
                        "example_word": { "german": "Apfel", "read_as": "apfel", "english": "apple" },
                        "cards": {
                            "learn": {
                                "title_en": "Learn Card",
                                "explanation_en": "Explanation",
                                "examples": [
                                    { "german": "Apfel", "read_as": "apfel", "english": "apple" }
                                ]
                            },
                            "practice": {
                                "format": "hear_it_pick_letter",
                                "prompt_en": "Practice Prompt",
                                "question": "Apfel",
                                "options": ["A", "B"],
                                "answer_index": 0
                            },
                            "game": {
                                "format": "odd_sound_out",
                                "question_en": "Game Question",
                                "options": ["Apfel", "Abends"],
                                "answer_index": 1
                            }
                        },
                        "audio": {
                            "tts_strings": ["A"],
                            "requires_recording": False
                        }
                    },
                    {
                        "id": "M01-L01-I2",
                        "type": "letter",
                        "target": "B",
                        "read_as": "b",
                        "pronunciation_notes": "None",
                        "tags": ["consonant"],
                        "example_word": { "german": "Birne", "read_as": "birne", "english": "pear" },
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
                        "target": "C",
                        "read_as": "c",
                        "pronunciation_notes": "None",
                        "tags": ["consonant"],
                        "example_word": { "german": "Citron", "read_as": "citron", "english": "lemon" },
                        "cards": {
                            "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                            "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                            "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                        },
                        "audio": { "tts_strings": [], "requires_recording": False }
                    }
                ],
                "summary": {
                    "recap_en": "Summary recap",
                    "key_forms": ["A", "B", "C"],
                    "next_up_en": "Next level"
                }
            }
        ]
    }
    
    # Should pass JSON schema validation and custom validation in validate.py
    validate_json_schema(german_data, "level")
    
    from validate import CurriculumValidator
    validator = CurriculumValidator("/app/tests/temp")
    validator.validate_level_file("/app/tests/temp/german_levels.json", german_data)

def test_dynamic_validation_keys_reading_phase5_german():
    german_reading_data = {
        "module": 12,
        "phase": 5,
        "levels": [
            {
                "level": 34,
                "title_en": "German Reading",
                "is_micro_dialogue_level": False,
                "items": [
                    {
                        "id": "M12-L34-I1",
                        "type": "reading",
                        "target": "Text",
                        "read_as": "text",
                        "german_text": "Es war einmal...",
                        "read_as": "es war einmal",
                        "german_translation": "Once upon a time...",
                        "reading_goal": "Understand narrative text",
                        "key_vocabulary": ["einmal"],
                        "comprehension_question": "Who was there?",
                        "inference_question": "Why?",
                        "difficulty": 1,
                        "tags": ["reading"],
                        "example_word": { "german": "Apfel", "read_as": "apfel", "english": "apple" },
                        "cards": {
                            "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                            "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                            "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                        },
                        "audio": { "tts_strings": [], "requires_recording": False }
                    },
                    {
                        "id": "M12-L34-I2",
                        "type": "word",
                        "target": "word2",
                        "read_as": "w2",
                        "pronunciation_notes": "None",
                        "difficulty": 1,
                        "tags": ["word"],
                        "cards": {
                            "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                            "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                            "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                        },
                        "audio": { "tts_strings": [], "requires_recording": False }
                    },
                    {
                        "id": "M12-L34-I3",
                        "type": "word",
                        "target": "word3",
                        "read_as": "w3",
                        "pronunciation_notes": "None",
                        "difficulty": 1,
                        "tags": ["word"],
                        "cards": {
                            "learn": { "title_en": "L", "explanation_en": "E", "examples": [] },
                            "practice": { "format": "F", "prompt_en": "P", "question": "Q", "options": ["O"], "answer_index": 0 },
                            "game": { "format": "G", "question_en": "Q", "options": ["O"], "answer_index": 0 }
                        },
                        "audio": { "tts_strings": [], "requires_recording": False }
                    }
                ],
                "summary": {
                    "recap_en": "Summary recap",
                    "key_forms": ["A", "B", "C"],
                    "next_up_en": "Next level"
                }
            }
        ]
    }
    
    # Run the validation through main CLI check
    from validate import CurriculumValidator
    validator = CurriculumValidator("/app/tests/temp")
    validator.validate_level_file("/app/tests/temp/german_levels.json", german_reading_data)

