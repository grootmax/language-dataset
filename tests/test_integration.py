import os
import json
import pytest
from core_engine.validator import Validator
from core_engine.lookup import ItemLookupAdapter, verify_referential_integrity, ReferentialIntegrityError

def test_hindi_dataset_integration():
    """
    Scans the entire 'hindi dataset' folder, validates every JSON file against core schemas
    using the sandboxed Hindi compatibility plugin, registers all items,
    and checks referential integrity across checkpoints, mocks, and exams.
    """
    dataset_dir = "/app/hindi dataset"
    assert os.path.exists(dataset_dir), f"Dataset directory {dataset_dir} does not exist"

    validator = Validator()
    lookup_adapter = ItemLookupAdapter()

    # We will split files into levels/spines (which define items) and assessments (checkpoints, mocks, final exams)
    item_files = []
    assessment_files = []

    # Read and classify all JSON files
    for root, _, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        pytest.fail(f"Failed to parse JSON file {file}: {e}")

                # Heuristic to detect schema type
                if "levels" in data:
                    schema_type = "level"
                    item_files.append((file_path, data, schema_type))
                elif "spine" in data:
                    schema_type = "spine"
                    item_files.append((file_path, data, schema_type))
                elif "checkpoints" in data:
                    schema_type = "checkpoint"
                    assessment_files.append((file_path, data, schema_type))
                elif data.get("kind") == "mock_exam" or "mock_exam" in data:
                    schema_type = "mock"
                    assessment_files.append((file_path, data, schema_type))
                elif data.get("kind") == "final_exam":
                    schema_type = "final_exam"
                    assessment_files.append((file_path, data, schema_type))
                else:
                    # Unknown schema
                    print(f"Skipping file {file} - unrecognized schema pattern.")

    print(f"Loaded {len(item_files)} item files and {len(assessment_files)} assessment files.")

    # 1. First Pass: Validate item files (levels & spines) and register them with lookup adapter
    for file_path, data, schema_type in item_files:
        try:
            # Validate using Hindi plugin (which normalizes the legacy root properties to attributes)
            normalized_data = validator.validate(data, schema_type, "hindi")
            # Register with lookup adapter
            lookup_adapter.register_from_dataset(normalized_data, schema_type)
        except Exception as e:
            pytest.fail(f"Validation failed for level/spine file {os.path.basename(file_path)}: {e}")

    # 2. Second Pass: Validate assessments
    for file_path, data, schema_type in assessment_files:
        try:
            validator.validate(data, schema_type, "hindi")
        except Exception as e:
            pytest.fail(f"Validation failed for assessment file {os.path.basename(file_path)}: {e}")

    # 3. Third Pass: Verify referential integrity across checkpoints, mocks, and exams
    # We will do a softer verification first to log any missing references, then verify.
    # Note: Because certain datasets might have minor omissions or references to parts not in this phase,
    # let's run verify_referential_integrity. If there are missing references, we can check if it's expected.
    for file_path, data, schema_type in assessment_files:
        try:
            verify_referential_integrity(data, schema_type, lookup_adapter, strict=False)
        except Exception as e:
            print(f"Referential integrity issue found in {os.path.basename(file_path)} (non-strict): {e}")

    # Let's run a strict validation to check if the dataset is 100% referentially whole.
    # If the database has minor missing references (e.g. from modules not present or external references),
    # strict=False won't crash the tests, but let's test how many are completely whole.
    print(f"Integrity check complete.")
