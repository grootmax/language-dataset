import jsonschema

# Common question schema helper
QUESTION_DEFINITION = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "n": {"type": "integer"},
        "source_item_ids": {
            "type": "array",
            "items": {"type": "string"}
        },
        "type": {"type": "string"},
        "prompt_en": {"type": "string"},
        "question_en": {"type": "string"},
        "options": {
            "type": "array",
            "items": {"type": "string"}
        },
        "options_read_as": {
            "type": "array",
            "items": {"type": "string"}
        },
        "answer_index": {"type": "integer"},
        "explanation_en": {"type": "string"}
    },
    "required": ["options", "answer_index"],
    "additionalProperties": True
}

# Language-agnostic Level Schema
LEVEL_SCHEMA = {
    "type": "object",
    "properties": {
        "module": {"type": "integer"},
        "module_name_en": {"type": "string"},
        "module_name_hi": {"type": "string"},
        "phase": {"type": "integer"},
        "batch": {
            "type": "object",
            "properties": {
                "levels_from": {"type": "integer"},
                "levels_to": {"type": "integer"}
            },
            "required": ["levels_from", "levels_to"],
            "additionalProperties": False
        },
        "levels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer"},
                    "title_en": {"type": "string"},
                    "title_hi": {"type": "string"},
                    "is_micro_dialogue_level": {"type": "boolean"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "target": {"type": "string"},
                                "read_as": {"type": "string"},
                                "gloss_en": {"type": "string"},
                                "difficulty": {"type": "integer"},
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "attributes": {
                                    "type": "object",
                                    "additionalProperties": True
                                },
                                "cards": {
                                    "type": "object"
                                },
                                "audio": {
                                    "type": "object"
                                }
                            },
                            "required": ["id", "type"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["level", "items"],
                "additionalProperties": True
            }
        }
    },
    "required": ["module", "levels"],
    "additionalProperties": True
}

# Language-agnostic Checkpoint Schema
CHECKPOINT_SCHEMA = {
    "type": "object",
    "properties": {
        "module": {"type": "integer"},
        "module_name_en": {"type": "string"},
        "checkpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "checkpoint": {"type": "integer"},
                    "after_level": {"type": "integer"},
                    "covers_levels": {
                        "type": "array",
                        "items": {"type": "integer"}
                    },
                    "title_en": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": QUESTION_DEFINITION
                    }
                },
                "required": ["questions"],
                "additionalProperties": True
            }
        }
    },
    "required": ["module", "checkpoints"],
    "additionalProperties": True
}

# Language-agnostic Spine Schema
SPINE_SCHEMA = {
    "type": "object",
    "properties": {
        "module": {"type": "integer"},
        "module_name_en": {"type": "string"},
        "module_name_hi": {"type": "string"},
        "phase": {"type": "integer"},
        "type": {"type": "string"},
        "partial": {"type": "boolean"},
        "provenance_en": {"type": "string"},
        "levels_present": {
            "type": "array",
            "items": {"type": "integer"}
        },
        "levels_missing": {
            "type": "array",
            "items": {"type": "integer"}
        },
        "total_items_present": {"type": "integer"},
        "expected_total_items": {"type": "integer"},
        "merge_instructions_en": {
            "type": "array",
            "items": {"type": "string"}
        },
        "spine": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "level": {"type": "integer"},
                    "type": {"type": "string"},
                    "target": {"type": "string"},
                    "difficulty": {"type": "integer"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "level_title_en": {"type": "string"},
                    "derived_from_item": {"type": "boolean"},
                    "attributes": {
                        "type": "object",
                        "additionalProperties": True
                    }
                },
                "required": ["id", "level"],
                "additionalProperties": False
            }
        }
    },
    "required": ["module", "spine"],
    "additionalProperties": True
}

# Language-agnostic Mock Exam Schema
# Allows questions directly at the root OR nested under "mock_exam" object
MOCK_SCHEMA = {
    "type": "object",
    "properties": {
        "module": {"type": "integer"},
        "module_name_en": {"type": "string"},
        "kind": {"type": "string", "enum": ["mock_exam"]},
        "mock_exam": {
            "type": "object",
            "properties": {
                "total_questions": {"type": "integer"},
                "weighting_note": {"type": "string"},
                "questions": {
                    "type": "array",
                    "items": QUESTION_DEFINITION
                }
            },
            "required": ["questions"],
            "additionalProperties": True
        },
        "questions": {
            "type": "array",
            "items": QUESTION_DEFINITION
        }
    },
    "required": ["module"],
    "anyOf": [
        {"required": ["mock_exam"]},
        {"required": ["questions"]}
    ],
    "additionalProperties": True
}

# Language-agnostic Final Exam Schema
FINAL_EXAM_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["final_exam"]},
        "covers_modules": {"type": "string"},
        "questions_total": {"type": "integer"},
        "sourcing_note_en": {"type": "string"},
        "weighting": {
            "type": "object",
            "additionalProperties": {"type": "integer"}
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string"},
                    "title_en": {"type": "string"},
                    "questions_range": {"type": "string"},
                    "note_en": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": QUESTION_DEFINITION
                    }
                },
                "required": ["section", "questions"],
                "additionalProperties": True
            }
        }
    },
    "required": ["kind", "sections"],
    "additionalProperties": True
}

SCHEMAS = {
    "level": LEVEL_SCHEMA,
    "checkpoint": CHECKPOINT_SCHEMA,
    "spine": SPINE_SCHEMA,
    "mock": MOCK_SCHEMA,
    "final_exam": FINAL_EXAM_SCHEMA
}

def validate_structure(data, schema_type):
    """
    Validates structural integrity of the given dataset against core schemas.
    Raises jsonschema.ValidationError on failure.
    """
    if schema_type not in SCHEMAS:
        raise ValueError(f"Unknown schema type: {schema_type}")
        
    from core_engine.locale_map import LOCALE_KEYS, detect_language_from_path_or_data, parameterize_core_schema
    lang = detect_language_from_path_or_data(data=data)
    mapping = LOCALE_KEYS.get(lang, LOCALE_KEYS["hindi"])
    
    schema = parameterize_core_schema(SCHEMAS[schema_type], mapping)
    jsonschema.validate(instance=data, schema=schema)
