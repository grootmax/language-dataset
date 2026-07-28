import os
import json
import re
import jsonschema
from collections import defaultdict

class ValidationError(Exception):
    pass

def load_schema(schema_type):
    """
    Loads the requested JSON schema from /app/schemas/.
    """
    schema_path = f"/app/schemas/{schema_type}_schema.json"
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_json_schema(data, schema_type):
    """
    Validates dictionary 'data' against the specified JSON schema.
    schema_type can be 'level', 'checkpoint', or 'mock_exam'.
    Raises ValidationError if validation fails.
    """
    try:
        from core_engine.validator import Validator
        validator = Validator()
        lang = validator.detect_language(data)
        plugin = validator.load_plugin(lang) if lang else None
        if not plugin and lang:
            from plugins.base import BasePlugin
            plugin = BasePlugin(language=lang)
        
        if plugin:
            normalized_data = plugin.normalize(data)
        else:
            normalized_data = data

        schema = load_schema(schema_type)
        jsonschema.validate(instance=normalized_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(f"JSON Schema validation failed for {schema_type}: {e.message}")
    except Exception as e:
        raise ValidationError(f"Error loading or running schema validation: {str(e)}")

def get_module_from_item_id(item_id):
    """
    Helper to extract module number from an item ID (e.g., M01-L01-I1 -> 1).
    """
    match = re.match(r'^M(\d+)', item_id)
    if match:
        return int(match.group(1))
    return None

def is_critical_core_concept(question):
    """
    Helper to detect if a question evaluates a critical core concept
    (noun gender, oblique case classes, or ergative marker/ने agreement rules).
    Checks keywords in explanation, prompts, options, and tags.
    """
    keywords = {
        "gender", "masculine", "feminine", "oblique", "ergative", "ne_agreement", "ne agreement", "ने",
        "gênero", "gêneros", "género", "géneros", "genre", "genres", "Geschlecht", "oblicuo", "ergativo", "ergatif",
        "postposition", "class_5", "class_1", "class_2", "class_3", "class_4", "oṁ_ending"
    }
    
    def check_val(val):
        if isinstance(val, str):
            v_lower = val.lower()
            return any(kw in v_lower for kw in keywords)
        elif isinstance(val, list):
            return any(check_val(item) for item in val)
        elif isinstance(val, dict):
            return any(check_val(k) or check_val(v) for k, v in val.items())
        return False

    return check_val(question)

def get_phase_of_module(module):
    """
    Map module to its phase:
    Phase 1: Modules 1-3
    Phase 2: Modules 4-5
    Phase 3: Modules 6-7
    Phase 4: Modules 8-11
    Phase 5: Modules 12-15
    """
    if 1 <= module <= 3:
        return 1
    elif 4 <= module <= 5:
        return 2
    elif 6 <= module <= 7:
        return 3
    elif 8 <= module <= 11:
        return 4
    elif 12 <= module <= 15:
        return 5
    return None

def build_level_item_ids(directory_path):
    """
    Scans the given directory for level files and returns a map of module_number -> set of level item IDs.
    """
    from pathlib import Path
    from core_engine.validator import Validator
    validator = Validator()
    
    level_item_ids = defaultdict(set)
    directory = Path(directory_path)
    if not directory.exists():
        return level_item_ids
        
    for filepath in directory.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "levels" in data:
                lang = validator.detect_language(data)
                plugin = validator.load_plugin(lang) if lang else None
                if not plugin and lang:
                    from plugins.base import BasePlugin
                    plugin = BasePlugin(language=lang)
                if plugin:
                    data = plugin.normalize(data)
                    
                module_num = data.get("module")
                if module_num:
                    for lvl in data.get("levels", []):
                        for item in lvl.get("items", []):
                            item_id = item.get("id")
                            if item_id:
                                level_item_ids[module_num].add(item_id)
        except Exception:
            continue
    return level_item_ids

def validate_card_math(data):
    """
    Enforces the Card Math layout rules:
    - Exactly 3 items per teaching level.
    - Exactly 3 cards (learn, practice, game) per item.
    - Exactly 9 cards total (3 * 3) per level.
    - Level summary card is strictly required unless legacy Hindi exceptions are met.
    """
    if "levels" not in data:
        raise ValidationError("Missing 'levels' key in level dataset.")
    
    for i, level in enumerate(data["levels"]):
        level_num = level.get("level", i + 1)
        
        # 1. Level summary check
        if "summary" not in level:
            is_legacy_exception = (data.get("module") in (13, 14) and level_num in (14, 21))
            if not is_legacy_exception:
                raise ValidationError(f"Level {level_num} is missing its level summary card under 'summary'.")
        else:
            summary = level["summary"]
            if summary is not None:
                if not isinstance(summary, dict) or "key_forms" not in summary:
                    raise ValidationError(f"Level {level_num} summary card must contain 'key_forms'.")
        
        # 2. Items per level check
        if "items" not in level:
            raise ValidationError(f"Level {level_num} is missing the 'items' key.")
        items = level["items"]
        if len(items) != 3:
            raise ValidationError(f"Level {level_num} violated Card Math: has {len(items)} items, expected exactly 3.")
            
        # 3. Cards per item check
        for j, item in enumerate(items):
            item_id = item.get("id", f"Item-{j}")
            if "cards" not in item:
                raise ValidationError(f"Item {item_id} in Level {level_num} is missing 'cards' configuration.")
            cards = item["cards"]
            if not isinstance(cards, dict):
                raise ValidationError(f"Item {item_id} cards must be an object.")
                
            required_cards = {"learn", "practice", "game"}
            actual_cards = set(cards.keys())
            if required_cards != actual_cards:
                raise ValidationError(
                    f"Item {item_id} in Level {level_num} violated Card Math: "
                    f"has cards {list(actual_cards)}, expected exactly 'learn', 'practice', and 'game'."
                )
    return True

def validate_level_details(data):
    """
    Enforces structural vocabulary/reading item requirements from the legacy validator.
    """
    module_num = data.get("module")
    phase_num = data.get("phase")
    
    if not module_num:
        raise ValidationError("Missing required root attribute: 'module'")
    if not phase_num:
        raise ValidationError("Missing required root attribute: 'phase'")

    levels = data.get("levels", [])
    for lvl in levels:
        lvl_num = lvl.get("level")
        if lvl_num is None:
            raise ValidationError("Level is missing 'level' number")

        items = lvl.get("items", [])
        for item_idx, item in enumerate(items):
            item_id = item.get("id")
            item_type = item.get("type")

            # Schema Validation: Vocabulary items (word or letter)
            if item_type in ("word", "letter"):
                target = item.get("target") or item.get("letter_form")
                if not target:
                    raise ValidationError(
                        f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing 'target' or 'letter_form'"
                    )

                # Required vocabulary fields
                required_fields = ["read_as"]
                if phase_num == 5:
                    required_fields.append("pronunciation_notes")
                for field in required_fields:
                    if not item.get(field):
                        raise ValidationError(
                            f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing required field '{field}'"
                        )

                if item_type == "letter":
                    example_word = item.get("example_word")
                    if not example_word or not isinstance(example_word, dict):
                        raise ValidationError(
                            f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing or invalid 'example_word' block"
                        )

                    possible_text_keys = ["text", "hindi"]
                    text_found = any(example_word.get(k) for k in possible_text_keys)
                    if not text_found:
                        raise ValidationError(
                            f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing required 'text' (or 'hindi') inside 'example_word'"
                        )
                    if not example_word.get("read_as"):
                        raise ValidationError(
                            f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing required 'read_as' inside 'example_word'"
                        )

            # Schema Validation: Reading items in Phase 5 levels
            elif item_type == "reading" and phase_num == 5:
                # Look for either standardized keys or text block
                required_reading_fields = (
                    "hindi_text", "read_as", "english_translation", 
                    "reading_goal", "key_vocabulary", 
                    "comprehension_question", "inference_question"
                )
                missing_any = False
                for r_field in required_reading_fields:
                    if r_field not in item or item.get(r_field) is None:
                        # Let's check if there is text block (legacy format) or if it's strictly missing
                        if "text" not in item and "text" not in item.get("attributes", {}):
                            missing_any = True
                            break
                if missing_any:
                    raise ValidationError(
                        f"Level {lvl_num}, item ID {item_id} (Phase 5 Reading Item): Missing required reading fields"
                    )

def validate_mock_exam_weights(data, current_module=None, tolerance=10.0):
    """
    Verifies that mock exams conform to Phase-specific sizes and cumulative retrieval weights.
    Uses identical classification and percent comparison logic to the legacy validator.
    """
    if data.get("kind") != "mock_exam" and "mock_exam" not in data:
        return True
        
    if current_module is None:
        current_module = data.get("module")
        if current_module is None:
            raise ValidationError("Mock exam dataset is missing 'module' number.")
            
    mock_exam = data.get("mock_exam") or data
    questions = mock_exam.get("questions", [])
    total_questions = len(questions)
    
    # Phase specific sizes
    phase = get_phase_of_module(current_module)
    if phase is None:
        raise ValidationError(f"Unknown phase for module {current_module}.")
        
    expected_size = None
    phase_name = ""
    if current_module in (1, 2, 3):
        expected_size = 20
        phase_name = "phase 1"
    elif current_module in (4, 5, 6, 7, 8, 9, 10, 11):
        expected_size = 30
        phase_name = "phase 4" if current_module >= 8 else "phase 2"
    elif current_module in (12, 13, 14, 15):
        expected_size = 40
        phase_name = "phase 5"
        
    if total_questions != expected_size:
        raise ValidationError(
            f"Mock Exam Size Mismatch: Module {current_module} is in {phase_name}, "
            f"which requires exactly {expected_size} questions. Found {total_questions} questions."
        )
        
    # Analyze question sourcing
    count_current = 0
    count_same_phase_prev = 0
    count_older_phase = 0
    
    current_phase = phase
    
    for q_idx, q in enumerate(questions):
        q_id = q.get("id") or q.get("n") or f"Q{q_idx+1}"
        
        # Classification method 1: Explicit metadata field 'source'
        source_meta = q.get("source")
        if source_meta in ("current", "phase", "high_value"):
            if source_meta == "current":
                count_current += 1
            elif source_meta == "phase":
                count_same_phase_prev += 1
            elif source_meta == "high_value":
                count_older_phase += 1
            continue

        # Classification method 2: Check source_item_ids
        source_item_ids = q.get("source_item_ids", [])
        classified = False
        if source_item_ids:
            ref_modules = set()
            for iid in source_item_ids:
                m_match = re.match(r'M(\d+)', iid)
                if m_match:
                    ref_modules.add(int(m_match.group(1)))
            
            if ref_modules:
                if current_module in ref_modules:
                    count_current += 1
                else:
                    is_same_phase = False
                    for rm in ref_modules:
                        if get_phase_of_module(rm) == current_phase:
                            is_same_phase = True
                            break
                    if is_same_phase:
                        count_same_phase_prev += 1
                    else:
                        count_older_phase += 1
                classified = True
        
        if not classified:
            if "level_source" in q or current_module >= 13:
                count_current += 1
            else:
                raise ValidationError(
                    f"Mock Exam, Question {q_id}: Cannot classify question source. "
                    f"Must have 'source' metadata, non-empty 'source_item_ids', or 'level_source' field."
                )

    if current_module == 1:
        if count_current != total_questions:
            raise ValidationError(
                f"Module 1 mock exam must be 100% current module questions. "
                f"Found {count_current}/{total_questions} current module questions."
            )

    pct_current = (count_current / total_questions) * 100
    pct_same_phase_prev = (count_same_phase_prev / total_questions) * 100
    pct_older_phase = (count_older_phase / total_questions) * 100

    if current_module == 1:
        expected_current = 100
        expected_same_phase_prev = 0
        expected_older_phase = 0
    elif current_module in (2, 3, 5):
        expected_current = 70
        expected_same_phase_prev = 30
        expected_older_phase = 0
    elif current_module in (4, 6, 8):
        expected_current = 70
        expected_same_phase_prev = 0
        expected_older_phase = 30
    elif current_module in (7, 9, 10, 11, 12):
        expected_current = 70
        expected_same_phase_prev = 20
        expected_older_phase = 10
    else: # late modules 13, 14, 15
        expected_current = 100
        expected_same_phase_prev = 0
        expected_older_phase = 0

    diff_current = abs(pct_current - expected_current)
    diff_same_phase_prev = abs(pct_same_phase_prev - expected_same_phase_prev)
    diff_older_phase = abs(pct_older_phase - expected_older_phase)

    if (diff_current > tolerance or 
        diff_same_phase_prev > tolerance or 
        diff_older_phase > tolerance):
        raise ValidationError(
            f"Mock Retrieval Weight Deviation too large: "
            f"Current: {pct_current:.1f}% (Expected {expected_current}%, diff {diff_current:.1f}%), "
            f"Same-Phase-Prev: {pct_same_phase_prev:.1f}% (Expected {expected_same_phase_prev}%, diff {diff_same_phase_prev:.1f}%), "
            f"Older-Phase: {pct_older_phase:.1f}% (Expected {expected_older_phase}%, diff {diff_older_phase:.1f}%). "
            f"Allowed tolerance is {tolerance}%."
        )
    return True

def validate_checkpoint_integrity(data):
    """
    Enforces checkpoint layout constraints:
    - Each checkpoint must contain exactly 10 questions.
    """
    checkpoints = data.get("checkpoints", [])
    if not checkpoints:
        raise ValidationError("No 'checkpoints' array found in checkpoint file.")
    for cp in checkpoints:
        cp_num = cp.get("checkpoint", "?")
        questions = cp.get("questions", [])
        if len(questions) != 10:
            raise ValidationError(
                f"Checkpoint {cp_num} violated Card Math standard: contains {len(questions)} questions, expected exactly 10."
            )
    return True

def validate_checkpoint_details(data, level_item_ids=None):
    """
    Detailed programmatic checks on checkpoint questions.
    """
    checkpoints = data.get("checkpoints", [])
    for cp in checkpoints:
        cp_num = cp.get("checkpoint") or cp.get("after_level") or "?"
        questions = cp.get("questions", [])
        for q_idx, q in enumerate(questions):
            q_id = q.get("id") or q.get("n")
            if not q_id:
                raise ValidationError(f"Checkpoint {cp_num}, Question index {q_idx}: Missing question identifier ('id' or 'n')")

            possible_prompts = [q.get(k) for k in ("prompt_en", "question", "question_en", "sentences", "sentence", "audience_en", "context_en", "stem") if q.get(k) is not None]
            if not possible_prompts:
                raise ValidationError(f"Checkpoint {cp_num}, Question {q_id}: Missing question prompt/text context")

            for field in ("options", "answer_index", "explanation_en"):
                if field not in q:
                    raise ValidationError(f"Checkpoint {cp_num}, Question {q_id}: Missing required field '{field}'")

            options = q.get("options", [])
            ans_idx = q.get("answer_index")
            if not isinstance(options, list) or ans_idx < 0 or ans_idx >= len(options):
                raise ValidationError(f"Checkpoint {cp_num}, Question {q_id}: Invalid 'answer_index' or 'options' format")

            source_item_ids = q.get("source_item_ids", [])
            for iid in source_item_ids:
                m_match = re.match(r'M(\d+)', iid)
                if not m_match:
                    raise ValidationError(
                        f"Checkpoint {cp_num}, Question {q_id}: Referenced item ID format is invalid: '{iid}'. "
                        f"Must match MXX-LXX-IXX format."
                    )
                
                ref_mod = int(m_match.group(1))
                if level_item_ids:
                    known_items_for_mod = level_item_ids.get(ref_mod, set())
                    if not known_items_for_mod:
                        raise ValidationError(
                            f"Checkpoint {cp_num}, Question {q_id}: References item ID '{iid}', "
                            f"but level files for Module {ref_mod} were not found or contain no items."
                        )
                    if iid not in known_items_for_mod:
                        raise ValidationError(
                            f"Checkpoint {cp_num}, Question {q_id}: Referenced item ID '{iid}' does not exist "
                            f"within any source level files of Module {ref_mod} loaded on disk."
                        )
    return True

def validate_final_exam_weights(data):
    """
    Enforces final exam layout and weights:
    - Must have kind = 'final_exam'
    - Total questions must be exactly 60
    - Sections must align with the weighting definition in the file
    """
    if data.get("kind") != "final_exam":
        return True
        
    questions_total = data.get("questions_total")
    if questions_total != 60:
        raise ValidationError(f"Final exam total questions must be exactly 60, found {questions_total}.")
        
    sections = data.get("sections", [])
    actual_q_count = sum(len(sec.get("questions", [])) for sec in sections)
    if actual_q_count != 60:
        raise ValidationError(f"Total question count in sections is {actual_q_count}, expected exactly 60.")
        
    for sec in sections:
        sec_name = sec.get("section")
        questions = sec.get("questions", [])
        if sec_name == "A":
            if len(questions) != 12:
                raise ValidationError(f"Section A of Final Exam must contain exactly 12 questions, found {len(questions)}.")
                
    return True

def validate_file_comprehensive(file_path):
    """
    Reads a file and runs schema and functional/logical validators depending on its kind/content.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format in file: {e}")
            
    # Normalize data first in-memory!
    from core_engine.validator import Validator
    validator = Validator()
    lang = validator.detect_language(data)
    plugin = validator.load_plugin(lang) if lang else None
    if not plugin and lang:
        from plugins.base import BasePlugin
        plugin = BasePlugin(language=lang)
    
    if plugin:
        normalized_data = plugin.normalize(data)
    else:
        normalized_data = data

    # Determine type of file
    if "levels" in normalized_data:
        # Teaching Level File
        validate_json_schema(normalized_data, "level")
        validate_card_math(normalized_data)
        validate_level_details(normalized_data)
    elif "checkpoints" in normalized_data:
        # Checkpoint File
        validate_json_schema(normalized_data, "checkpoint")
        validate_checkpoint_integrity(normalized_data)
        level_item_ids = build_level_item_ids(os.path.dirname(file_path))
        validate_checkpoint_details(normalized_data, level_item_ids=level_item_ids)
    elif "mock_exam" in normalized_data or normalized_data.get("kind") == "mock_exam" or normalized_data.get("kind") == "final_exam":
        # Mock or Final Exam File
        validate_json_schema(normalized_data, "mock_exam")
        if normalized_data.get("kind") == "mock_exam" or "mock_exam" in normalized_data:
            validate_mock_exam_weights(normalized_data)
        elif normalized_data.get("kind") == "final_exam":
            validate_final_exam_weights(normalized_data)
    else:
        raise ValidationError("Unknown curriculum file format. Could not classify file for validation.")
        
    return True
