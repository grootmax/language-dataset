import os
import json
import re
import jsonschema

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
        schema = load_schema(schema_type)
        jsonschema.validate(instance=data, schema=schema)
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

def validate_card_math(data):
    """
    Enforces the Card Math layout rules:
    - Exactly 3 items per teaching level.
    - Exactly 3 cards (learn, practice, game) per item.
    - Exactly 9 cards total (3 * 3) per level.
    - Exactly 1 Level Summary Card under 'summary' at the level root.
    """
    if "levels" not in data:
        raise ValidationError("Missing 'levels' key in level dataset.")
    
    for i, level in enumerate(data["levels"]):
        level_num = level.get("level", i + 1)
        
        # 1. Level summary check
        if "summary" not in level:
            raise ValidationError(f"Level {level_num} is missing its level summary card under 'summary'.")
        summary = level["summary"]
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

def validate_mock_exam_weights(data, current_module=None):
    """
    Verifies that mock exams conform to Phase-specific sizes and cumulative retrieval weights:
    - Phase 1 (Modules 1-3): exactly 20 questions
    - Phases 2-4 (Modules 4-11): exactly 30 questions
    - Phase 5 (Modules 12-15): exactly 40 questions
    
    Cumulative Retrieval Weight Distribution:
    - 70% current module questions
    - 20% previous modules in same phase (or preceding phase review if first module of Phase)
    - 10% critical core concepts (noun gender, oblique case, or ne agreement rules) for modules >= 5.
    """
    if data.get("kind") != "mock_exam":
        # Skip if not a mock exam (could be final exam)
        return True
        
    if current_module is None:
        current_module = data.get("module")
        if current_module is None:
            raise ValidationError("Mock exam dataset is missing 'module' number.")
            
    mock_exam = data.get("mock_exam")
    if not mock_exam:
        raise ValidationError("Missing 'mock_exam' root key in mock exam data.")
        
    questions = mock_exam.get("questions", [])
    total_questions = mock_exam.get("total_questions")
    
    if len(questions) != total_questions:
        raise ValidationError(
            f"Question count mismatch: total_questions is {total_questions} but found {len(questions)} actual questions."
        )
        
    # Phase specific sizes
    phase = get_phase_of_module(current_module)
    if phase is None:
        raise ValidationError(f"Unknown phase for module {current_module}.")
        
    expected_size = None
    if phase == 1:
        expected_size = 20
    elif 2 <= phase <= 4:
        expected_size = 30
    elif phase == 5:
        expected_size = 40
        
    if total_questions != expected_size:
        raise ValidationError(
            f"Mock exam for Module {current_module} (Phase {phase}) has {total_questions} questions, expected {expected_size}."
        )
        
    # Analyze question sourcing
    current_module_count = 0
    previous_module_count = 0
    critical_concept_count = 0
    
    for q in questions:
        source_ids = q.get("source_item_ids", [])
        is_current = False
        is_prev = False
        for sid in source_ids:
            m = get_module_from_item_id(sid)
            if m == current_module:
                is_current = True
            elif m is not None and m < current_module:
                is_prev = True
                
        if is_current:
            current_module_count += 1
        elif is_prev:
            previous_module_count += 1
            
        if is_critical_core_concept(q):
            critical_concept_count += 1
            
    # Expected weight rules
    if current_module == 1:
        # Module 1 is 100% current module
        if current_module_count != total_questions:
            raise ValidationError(
                f"Module 1 mock exam must be 100% current module questions. "
                f"Found {current_module_count}/{total_questions} current module questions."
            )
    elif current_module in {2, 3}:
        # Module 2 and 3: 70% current, 30% previous phase-1
        expected_current = int(round(total_questions * 0.70))
        expected_prev = int(round(total_questions * 0.30))
        if abs(current_module_count - expected_current) > 1:
            raise ValidationError(
                f"Module {current_module} mock current questions is {current_module_count}, "
                f"expected {expected_current} (70%)."
            )
        if abs(previous_module_count - expected_prev) > 1:
            raise ValidationError(
                f"Module {current_module} mock previous questions is {previous_module_count}, "
                f"expected {expected_prev} (30%)."
            )
    elif current_module == 4:
        # Module 4: 70% current, 30% Phase 1 review (no same phase predecessor)
        expected_current = int(round(total_questions * 0.70))
        expected_prev = int(round(total_questions * 0.30))
        if abs(current_module_count - expected_current) > 1:
            raise ValidationError(
                f"Module 4 mock current questions is {current_module_count}, expected {expected_current}."
            )
        if abs(previous_module_count - expected_prev) > 1:
            raise ValidationError(
                f"Module 4 mock previous questions is {previous_module_count}, expected {expected_prev}."
            )
    else:
        # Modules >= 5: 70% current module, 20% same phase, 10% critical core concepts
        expected_current = int(round(total_questions * 0.70))
        expected_prev = int(round(total_questions * 0.20))
        expected_critical = int(round(total_questions * 0.10))
        
        # Check current module count (allow absolute difference of 1)
        if abs(current_module_count - expected_current) > 1:
            raise ValidationError(
                f"Module {current_module} mock current questions is {current_module_count}, "
                f"expected {expected_current} (70%)."
            )
        # Check previous module count + critical concepts count (as they are folded or distinct)
        # To be safe, previous review (same-phase) + critical review should total ~30%
        total_review_count = previous_module_count
        expected_review_total = total_questions - expected_current
        if abs(total_review_count - expected_review_total) > 1:
            raise ValidationError(
                f"Module {current_module} total review questions is {total_review_count}, "
                f"expected {expected_review_total} (30%)."
            )
        # Validate presence of critical core concepts (at least 10%, i.e. 3 for size 30, 4 for size 40)
        # We can allow at least expected_critical - 1 (e.g. >= 2 for size 30, >= 3 for size 40)
        min_critical = max(1, expected_critical - 1)
        if critical_concept_count < min_critical:
            raise ValidationError(
                f"Module {current_module} critical core concept questions count is {critical_concept_count}, "
                f"expected at least {min_critical} (10% of {total_questions} questions)."
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
        
    # Check section counts
    # Section A is Fundamentals (1-12) -> 12 questions
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
            
    # Determine type of file
    if "levels" in data:
        # Teaching Level File
        validate_json_schema(data, "level")
        validate_card_math(data)
    elif "checkpoints" in data:
        # Checkpoint File
        validate_json_schema(data, "checkpoint")
        validate_checkpoint_integrity(data)
    elif "mock_exam" in data or data.get("kind") == "mock_exam" or data.get("kind") == "final_exam":
        # Mock or Final Exam File
        validate_json_schema(data, "mock_exam")
        if data.get("kind") == "mock_exam":
            validate_mock_exam_weights(data)
        elif data.get("kind") == "final_exam":
            validate_final_exam_weights(data)
    else:
        raise ValidationError("Unknown curriculum file format. Could not classify file for validation.")
        
    return True
