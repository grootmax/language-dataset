import pytest
import jsonschema
from core_engine.schema import validate_structure
from core_engine.validator import Validator
from core_engine.sandbox import exec_sandboxed
from core_engine.lookup import ItemLookupAdapter, verify_referential_integrity, ReferentialIntegrityError
from core_engine.game_registry import GameRegistry, GameWidget

def test_generic_level_schema_valid():
    """
    Ensures that a standard language-agnostic level structure with generic attributes passes.
    """
    valid_data = {
        "module": 1,
        "module_name_en": "Greetings",
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "DE-L01-I01",
                        "type": "noun",
                        "target": "Buch",
                        "read_as": "Buch",
                        "attributes": {
                            "gender": "neuter"
                        }
                    }
                ]
            }
        ]
    }
    # Should not raise any validation error
    validate_structure(valid_data, "level")

def test_generic_level_schema_rejects_legacy_fields_at_root():
    """
    Ensures that language-specific properties like gender/matra/oblique at the root of items
    are rejected by the core schema (enforcing standard KV block structure).
    """
    invalid_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "DE-L01-I01",
                        "type": "noun",
                        "target": "Buch",
                        "read_as": "Buch",
                        "gender": "neuter" # Invalid at root!
                    }
                ]
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_structure(invalid_data, "level")

def test_sandbox_security_restrictions():
    """
    Verifies that the execution sandbox strictly prevents unauthorized module imports
    or dangerous builtins like open, eval, exec, etc.
    """
    # Attempting to import unauthorized module 'os'
    forbidden_import_code = """
import os
"""
    with pytest.raises(Exception) as exc_info:
        exec_sandboxed(forbidden_import_code)
    assert "Import of module 'os' is not permitted" in str(exc_info.value)

    # Attempting to use forbidden builtin 'open'
    forbidden_builtin_code = """
f = open("/etc/passwd", "r")
"""
    with pytest.raises(Exception) as exc_info:
        exec_sandboxed(forbidden_builtin_code)
    assert "name 'open' is not defined" in str(exc_info.value)

def test_german_plugin_dynamic_validation():
    """
    Ensures that a German dataset with neuter nouns is successfully loaded,
    normalized, and validated via the dynamic German plugin.
    """
    validator = Validator()
    
    german_data = {
        "module": 1,
        "module_name_en": "Objects",
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "GER-L01-I1",
                        "type": "noun",
                        "target": "Mädchen",
                        "read_as": "Mädchen",
                        "attributes": {
                            "gender": "neuter"
                        }
                    }
                ]
            }
        ]
    }
    
    # Validation should succeed
    normalized = validator.validate(german_data, "level", "german")
    assert normalized["levels"][0]["items"][0]["attributes"]["gender"] == "neuter"

    # Validation should fail if the gender attribute is missing
    invalid_german_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "GER-L01-I1",
                        "type": "noun",
                        "target": "Mädchen",
                        "read_as": "Mädchen",
                        "attributes": {}
                    }
                ]
            }
        ]
    }
    with pytest.raises(ValueError) as exc_info:
        validator.validate(invalid_german_data, "level", "german")
    assert "is missing grammatical gender" in str(exc_info.value)

def test_chinese_plugin_skips_and_accepts_tones():
    """
    Ensures that the Chinese plugin successfully processes dynamic metadata
    like tone values, while skipping phonetic/alphabet validations.
    """
    validator = Validator()
    
    chinese_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "ZH-L01-I1",
                        "type": "vocabulary",
                        "target": "你好",
                        "read_as": "nǐ hǎo",
                        "attributes": {
                            "tones": [3, 3]
                        }
                    }
                ]
            }
        ]
    }
    # Validate with chinese plugin
    normalized = validator.validate(chinese_data, "level", "chinese")
    assert normalized["levels"][0]["items"][0]["attributes"]["tones"] == [3, 3]

def test_referential_integrity():
    """
    Verifies that course content referential integrity functions correctly using
    the dynamic ItemLookupAdapter.
    """
    lookup = ItemLookupAdapter()
    
    level_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "M01-L01-I1",
                        "type": "letter",
                        "target": "A",
                        "read_as": "a"
                    }
                ]
            }
        ]
    }
    # Register items
    lookup.register_from_dataset(level_data, "level")
    assert lookup.exists("M01-L01-I1") is True
    assert lookup.exists("M01-L01-I2") is False

    # Valid checkpoint referring to existing item
    valid_cp = {
        "module": 1,
        "checkpoints": [
            {
                "checkpoint": 1,
                "questions": [
                    {
                        "id": "M01-CP1-Q1",
                        "source_item_ids": ["M01-L01-I1"],
                        "type": "recognition",
                        "prompt_en": "Which letter is this?",
                        "options": ["A", "B"],
                        "answer_index": 0
                    }
                ]
            }
        ]
    }
    verify_referential_integrity(valid_cp, "checkpoint", lookup)

    # Invalid checkpoint referring to non-existent item
    invalid_cp = {
        "module": 1,
        "checkpoints": [
            {
                "checkpoint": 1,
                "questions": [
                    {
                        "id": "M01-CP1-Q2",
                        "source_item_ids": ["M01-L01-I2"], # Does not exist!
                        "type": "recognition",
                        "prompt_en": "Which letter is this?",
                        "options": ["A", "B"],
                        "answer_index": 0
                    }
                ]
            }
        ]
    }
    with pytest.raises(ReferentialIntegrityError) as exc_info:
        verify_referential_integrity(invalid_cp, "checkpoint", lookup)
    assert "references non-existent item 'M01-L01-I2'" in str(exc_info.value)

def test_final_exam_referential_integrity_prerequisite_inferred():
    """
    Verifies that final exam verification allows missing items if the
    'prerequisite_inferred' flag is set to True.
    """
    lookup = ItemLookupAdapter()
    
    # In the database, we have M01-L01-I1 but NOT M01-L01-I2
    level_data = {
        "module": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "M01-L01-I1",
                        "type": "letter",
                        "target": "A",
                        "read_as": "a"
                    }
                ]
            }
        ]
    }
    lookup.register_from_dataset(level_data, "level")

    final_exam = {
        "kind": "final_exam",
        "sections": [
            {
                "section": "A",
                "questions": [
                    {
                        "n": 1,
                        "prerequisite_inferred": True, # Allowed to be missing from current loaded files
                        "prompt_en": "Some question...",
                        "options": ["x", "y"],
                        "answer_index": 0,
                        "source_item_ids": ["M01-L01-I2"] 
                    },
                    {
                        "n": 2,
                        "prerequisite_inferred": False, # NOT allowed to be missing!
                        "prompt_en": "Another question...",
                        "options": ["x", "y"],
                        "answer_index": 0,
                        "source_item_ids": ["M01-L01-I1"]
                    }
                ]
            }
        ]
    }
    # This should pass without raising ReferentialIntegrityError
    verify_referential_integrity(final_exam, "final_exam", lookup)

    # If prerequisite_inferred is False and source is missing, it should fail
    invalid_final_exam = {
        "kind": "final_exam",
        "sections": [
            {
                "section": "A",
                "questions": [
                    {
                        "n": 1,
                        "prerequisite_inferred": False, # Strict check
                        "prompt_en": "Some question...",
                        "options": ["x", "y"],
                        "answer_index": 0,
                        "source_item_ids": ["M01-L01-I2"] 
                    }
                ]
            }
        ]
    }
    with pytest.raises(ReferentialIntegrityError):
        verify_referential_integrity(invalid_final_exam, "final_exam", lookup)

def test_game_registry_contract():
    """
    Verifies that the GameRegistry handles dynamic widget registrations,
    correctly resolves item compatibility, and executes the standard API contract.
    """
    registry = GameRegistry()
    
    # Define a custom game requiring gender and word type
    gender_guessing_game = GameWidget(
        name="GenderGuess",
        required_attributes=["gender"],
        required_item_types=["noun"]
    )
    
    registry.register_game("GenderGuess", gender_guessing_game)

    compatible_item = {
        "id": "DE-01",
        "type": "noun",
        "target": "Buch",
        "attributes": {
            "gender": "neuter"
        }
    }
    
    incompatible_item = {
        "id": "DE-02",
        "type": "verb",
        "target": "gehen",
        "attributes": {}
    }

    assert gender_guessing_game.can_run(compatible_item) is True
    assert gender_guessing_game.can_run(incompatible_item) is False

    # Execute widget contract
    result = gender_guessing_game.run(compatible_item)
    assert result["game_name"] == "GenderGuess"
    assert result["status"] == "ready"
    assert result["extracted_attributes"]["gender"] == "neuter"

    with pytest.raises(ValueError):
        gender_guessing_game.run(incompatible_item)

    # Check registry query functions
    compatibles = registry.get_compatible_games(compatible_item)
    assert "GenderGuess" in compatibles

    incompatibles = registry.get_compatible_games(incompatible_item)
    assert "GenderGuess" not in incompatibles

def test_telugu_plugin_validation():
    validator = Validator()
    
    # Valid Telugu level content with Telugu characters (e.g. పానీ)
    telugu_data = {
        "module": 1,
        "module_name_en": "Greetings",
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "TE-L01-I1",
                        "type": "vocabulary",
                        "target": "పానీ",
                        "read_as": "paanii",
                        "attributes": {}
                    }
                ]
            }
        ]
    }
    
    # This should pass without raising any error
    normalized = validator.validate(telugu_data, "level", "te")
    assert normalized["levels"][0]["items"][0]["target"] == "పానీ"
    
    # Invalid Telugu level content where target contains only English/non-Telugu script characters
    invalid_telugu_data = {
        "module": 1,
        "module_name_en": "Greetings",
        "phase": 1,
        "levels": [
            {
                "level": 1,
                "items": [
                    {
                        "id": "TE-L01-I2",
                        "type": "vocabulary",
                        "target": "water", # Non-Telugu target
                        "read_as": "water",
                        "attributes": {}
                    }
                ]
            }
        ]
    }
    
    with pytest.raises(ValueError, match="does not contain Telugu characters"):
        validator.validate(invalid_telugu_data, "level", "te")

