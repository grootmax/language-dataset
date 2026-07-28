#!/usr/bin/env python3
import os
import sys
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict

# Define the 5 phases of modules
# Phase 1: Modules 1–3 (Script Phase)
# Phase 2: Modules 4–5 (Foundations Phase)
# Phase 3: Modules 6–7 (Grammar Core Phase)
# Phase 4: Modules 8–11 (Real Hindi Phase)
# Phase 5: Modules 12–15 (Fluency Phase)
MODULE_PHASES = {
    1: 1, 2: 1, 3: 1,
    4: 2, 5: 2,
    6: 3, 7: 3,
    8: 4, 9: 4, 10: 4, 11: 4,
    12: 5, 13: 5, 14: 5, 15: 5
}

class ValidationFailure(Exception):
    pass

class CurriculumValidator:
    def __init__(self, directory, tolerance=10, verbose=False):
        self.directory = Path(directory)
        self.tolerance = tolerance
        self.verbose = verbose
        
        self.level_files = []
        self.checkpoint_files = []
        self.mock_files = []
        self.final_exam_files = []
        self.other_files = []
        
        # Maps module_number -> set of level item IDs
        self.level_item_ids = defaultdict(set)
        
        # Validation statistics
        self.total_checked = 0
        self.total_passed = 0
        self.failures = []

    def log(self, msg):
        if self.verbose:
            print(msg)

    def log_success(self, msg):
        print(f"\033[92m[PASS] {msg}\033[0m")

    def log_failure(self, msg):
        print(f"\033[91m[FAIL] {msg}\033[0m")
        self.failures.append(msg)

    def scan_and_classify(self):
        """Scans the directory for JSON files and classifies them by schema."""
        if not self.directory.exists():
            print(f"Error: Directory {self.directory} does not exist.")
            sys.exit(1)

        for filepath in sorted(self.directory.glob("*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                self.log_failure(f"{filepath.name}: Failed to parse JSON: {e}")
                continue

            # Classify based on root structure and fields
            if "levels" in data:
                self.level_files.append((filepath, data))
                self.log(f"Classified {filepath.name} as Level File")
            elif "checkpoints" in data:
                self.checkpoint_files.append((filepath, data))
                self.log(f"Classified {filepath.name} as Checkpoint File")
            elif data.get("kind") == "final_exam":
                self.final_exam_files.append((filepath, data))
                self.log(f"Classified {filepath.name} as Final Exam File")
            elif data.get("kind") == "mock_exam" or "mock_exam" in data:
                self.mock_files.append((filepath, data))
                self.log(f"Classified {filepath.name} as Mock Exam File")
            elif "spine" in data:
                self.other_files.append((filepath, data, "Spine File"))
                self.log(f"Classified {filepath.name} as Spine File")
            elif data.get("kind") == "phase_checkpoint":
                self.other_files.append((filepath, data, "Phase Checkpoint File"))
                self.log(f"Classified {filepath.name} as Phase Checkpoint File")
            else:
                self.other_files.append((filepath, data, "Unknown File"))
                self.log(f"Classified {filepath.name} as Unknown File")

    def run_all_validations(self):
        """Runs the validation checks on all classified files."""
        print("=" * 60)
        print(f"Starting Curriculum Validation on folder: {self.directory}")
        print(f"Configured Mock weight tolerance: {self.tolerance}%")
        print("=" * 60)

        # Step 1: Pre-load and validate level files to build item reference database
        print("\n--- PHASE 1: LEVEL CONTENT VALIDATION ---")
        for filepath, data in self.level_files:
            self.total_checked += 1
            try:
                self.validate_level_file(filepath, data)
                self.total_passed += 1
                self.log_success(f"{filepath.name}: Level content matches rules.")
            except ValidationFailure as vf:
                self.log_failure(f"{filepath.name}: Level content validation failed: {vf}")
            except Exception as e:
                self.log_failure(f"{filepath.name}: Unexpected error validating levels: {e}")

        # Step 2: Validate checkpoint files (requires level item reference database)
        print("\n--- PHASE 2: CHECKPOINT VALIDATION ---")
        for filepath, data in self.checkpoint_files:
            self.total_checked += 1
            try:
                self.validate_checkpoint_file(filepath, data)
                self.total_passed += 1
                self.log_success(f"{filepath.name}: Checkpoints validated.")
            except ValidationFailure as vf:
                self.log_failure(f"{filepath.name}: Checkpoint validation failed: {vf}")
            except Exception as e:
                self.log_failure(f"{filepath.name}: Unexpected error validating checkpoints: {e}")

        # Step 3: Validate mock exam files (requires phase size and distribution rules)
        print("\n--- PHASE 3: MOCK EXAM VALIDATION ---")
        for filepath, data in self.mock_files:
            self.total_checked += 1
            try:
                self.validate_mock_file(filepath, data)
                self.total_passed += 1
                self.log_success(f"{filepath.name}: Mock exam validated.")
            except ValidationFailure as vf:
                self.log_failure(f"{filepath.name}: Mock exam validation failed: {vf}")
            except Exception as e:
                self.log_failure(f"{filepath.name}: Unexpected error validating mock exam: {e}")

        # Step 4: Validate final exam files
        print("\n--- PHASE 4: FINAL EXAM VALIDATION ---")
        for filepath, data in self.final_exam_files:
            self.total_checked += 1
            try:
                self.validate_final_exam_file(filepath, data)
                self.total_passed += 1
                self.log_success(f"{filepath.name}: Final exam validated.")
            except ValidationFailure as vf:
                self.log_failure(f"{filepath.name}: Final exam validation failed: {vf}")
            except Exception as e:
                self.log_failure(f"{filepath.name}: Unexpected error validating final exam: {e}")

        # Summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Files Analyzed: {self.total_checked}")
        print(f"Files Passed: {self.total_passed}")
        print(f"Files Failed: {len(self.failures)}")
        
        if self.failures:
            print("\nList of Failures:")
            for idx, failure in enumerate(self.failures, 1):
                print(f"  {idx}. {failure}")
            print("\nResult: \033[91mVALIDATION FAILED\033[0m")
            return False
        else:
            print("\nResult: \033[92mVALIDATION SUCCEEDED\033[0m")
            return True

    def validate_level_file(self, filepath, data):
        """Validates that each level has exactly 3 items and 9 cards, and matches schemas."""
        module_num = data.get("module")
        phase_num = data.get("phase")
        
        if not module_num:
            raise ValidationFailure("Missing required root attribute: 'module'")
        if not phase_num:
            raise ValidationFailure("Missing required root attribute: 'phase'")

        levels = data.get("levels", [])
        if not isinstance(levels, list):
            raise ValidationFailure("'levels' root attribute must be a list")

        for idx, lvl in enumerate(levels):
            lvl_num = lvl.get("level")
            if lvl_num is None:
                raise ValidationFailure(f"Level at index {idx} is missing 'level' number")

            items = lvl.get("items", [])
            if not isinstance(items, list):
                raise ValidationFailure(f"Level {lvl_num}: 'items' must be a list")

            # Rule: Exactly 3 items per level
            if len(items) != 3:
                raise ValidationFailure(f"Level {lvl_num}: Must contain exactly 3 items, found {len(items)}")

            total_cards = 0
            for item_idx, item in enumerate(items):
                item_id = item.get("id")
                if not item_id:
                    raise ValidationFailure(f"Level {lvl_num}, item {item_idx}: Missing required 'id' attribute")

                # Store for cross-referencing
                self.level_item_ids[module_num].add(item_id)

                item_type = item.get("type")
                if not item_type:
                    raise ValidationFailure(f"Level {lvl_num}, item ID {item_id}: Missing required 'type'")

                cards = item.get("cards")
                if not cards or not isinstance(cards, dict):
                    raise ValidationFailure(f"Level {lvl_num}, item ID {item_id}: Missing or invalid 'cards' dictionary")

                # Rule: Exactly 3 card sub-objects: learn, practice, game
                required_card_keys = {"learn", "practice", "game"}
                actual_card_keys = set(cards.keys())
                if required_card_keys != actual_card_keys:
                    raise ValidationFailure(
                        f"Level {lvl_num}, item ID {item_id}: Cards must contain exactly learn, practice, and game modes. "
                        f"Found: {actual_card_keys}"
                    )

                total_cards += len(required_card_keys)

                # Schema Validation: Vocabulary items (word or letter)
                if item_type in ("word", "letter"):
                    # Check target or letter_form
                    target = item.get("target") or item.get("letter_form")
                    if not target:
                        raise ValidationFailure(
                            f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing 'target' or 'letter_form'"
                        )

                    # Required vocabulary fields
                    for field in ("read_as", "pronunciation_notes"):
                        if not item.get(field):
                            raise ValidationFailure(
                                f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing required field '{field}'"
                            )

                    if item_type == "letter":
                        example_word = item.get("example_word")
                        if not example_word or not isinstance(example_word, dict):
                            raise ValidationFailure(
                                f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing or invalid 'example_word' block"
                            )

                        for sub_field in ("hindi", "read_as", "english"):
                            if not example_word.get(sub_field):
                                raise ValidationFailure(
                                    f"Level {lvl_num}, item ID {item_id} (Vocabulary Item): Missing required '{sub_field}' inside 'example_word'"
                                )

                # Schema Validation: Reading items in Phase 5 levels
                elif item_type == "reading" and phase_num == 5:
                    required_reading_fields = (
                        "hindi_text", "read_as", "english_translation", 
                        "reading_goal", "key_vocabulary", 
                        "comprehension_question", "inference_question"
                    )
                    for r_field in required_reading_fields:
                        if r_field not in item or item.get(r_field) is None:
                            # Let's check if there is text block (legacy format) or if it's strictly missing
                            if "text" not in item:
                                raise ValidationFailure(
                                    f"Level {lvl_num}, item ID {item_id} (Phase 5 Reading Item): Missing required field '{r_field}'"
                                )

            # Rule: Exactly 9 cards representing learn, practice, and game modes per level
            if total_cards != 9:
                raise ValidationFailure(f"Level {lvl_num}: Total cards must sum to exactly 9, found {total_cards}")

    def validate_checkpoint_file(self, filepath, data):
        """Validates checkpoints contain exactly 10 questions and all referenced level items exist."""
        module_num = data.get("module")
        if not module_num:
            raise ValidationFailure("Missing required root attribute: 'module'")

        checkpoints = data.get("checkpoints", [])
        if not isinstance(checkpoints, list):
            raise ValidationFailure("'checkpoints' root attribute must be a list")

        for idx, cp in enumerate(checkpoints):
            cp_num = cp.get("checkpoint") or cp.get("after_level") or f"index_{idx}"
            questions = cp.get("questions", [])
            if not isinstance(questions, list):
                raise ValidationFailure(f"Checkpoint {cp_num}: 'questions' must be a list")

            # Rule: Exactly 10 questions per checkpoint
            if len(questions) != 10:
                raise ValidationFailure(f"Checkpoint {cp_num}: Must contain exactly 10 questions, found {len(questions)}")

            # Validate each question's schema and verify referential integrity
            for q_idx, q in enumerate(questions):
                # Check for ID (or number) and Prompt (or question text)
                q_id = q.get("id") or q.get("n")
                if not q_id:
                    raise ValidationFailure(f"Checkpoint {cp_num}, Question index {q_idx}: Missing question identifier ('id' or 'n')")

                possible_prompts = [q.get(k) for k in ("prompt_en", "question", "question_en", "sentences", "sentence", "audience_en", "context_en", "stem") if q.get(k) is not None]
                if not possible_prompts:
                    raise ValidationFailure(f"Checkpoint {cp_num}, Question {q_id}: Missing question prompt/text context (e.g. 'prompt_en', 'question', 'question_en', 'sentences', 'stem', etc.)")

                for field in ("options", "answer_index", "explanation_en"):
                    if field not in q:
                        raise ValidationFailure(f"Checkpoint {cp_num}, Question {q_id}: Missing required field '{field}'")

                # Verify answer index validity
                options = q.get("options", [])
                ans_idx = q.get("answer_index")
                if not isinstance(options, list) or ans_idx < 0 or ans_idx >= len(options):
                    raise ValidationFailure(f"Checkpoint {cp_num}, Question {q_id}: Invalid 'answer_index' or 'options' format")

                # Referential Integrity Audit (optional in later checkpoint formats if not present)
                source_item_ids = q.get("source_item_ids", [])
                if not isinstance(source_item_ids, list):
                    raise ValidationFailure(f"Checkpoint {cp_num}, Question {q_id}: 'source_item_ids' must be a list")

                for iid in source_item_ids:
                    # Parse the target module of the item ID (e.g. M01-L01-I1 -> Module 1)
                    m_match = re.match(r'M(\d+)', iid)
                    if not m_match:
                        raise ValidationFailure(
                            f"Checkpoint {cp_num}, Question {q_id}: Referenced item ID format is invalid: '{iid}'. "
                            f"Must match MXX-LXX-IXX format."
                        )
                    
                    ref_mod = int(m_match.group(1))
                    # We assert they exist in the level files of that module
                    known_items_for_mod = self.level_item_ids.get(ref_mod, set())
                    if not known_items_for_mod:
                        # Maybe the level files of that module haven't been processed yet or are missing
                        raise ValidationFailure(
                            f"Checkpoint {cp_num}, Question {q_id}: References item ID '{iid}', "
                            f"but level files for Module {ref_mod} were not found or contain no items."
                        )
                    if iid not in known_items_for_mod:
                        raise ValidationFailure(
                            f"Checkpoint {cp_num}, Question {q_id}: Referenced item ID '{iid}' does not exist "
                            f"within any source level files of Module {ref_mod} loaded on disk."
                        )

    def validate_mock_file(self, filepath, data):
        """Validates mock exam size and 70/20/10 cumulative weight distribution rules."""
        module_num = data.get("module")
        if not module_num:
            raise ValidationFailure("Missing required root attribute: 'module'")

        # Mock exams can nest questions directly or inside a mock_exam dictionary
        if "mock_exam" in data and isinstance(data["mock_exam"], dict):
            mock_data = data["mock_exam"]
            questions = mock_data.get("questions", [])
        else:
            questions = data.get("questions", [])

        if not isinstance(questions, list):
            raise ValidationFailure("Mock exam questions must be a list")

        total_questions = len(questions)

        # Rule: Size requirement per Phase
        # Modules 1–3 (Script): 20Q
        # Modules 4–11 (Core Foundations): 30Q
        # Modules 12–15 (Fluency): 40Q
        if module_num in (1, 2, 3):
            expected_size = 20
            phase_name = "Script Phase (M1-M3)"
        elif module_num in (4, 5, 6, 7, 8, 9, 10, 11):
            expected_size = 30
            phase_name = "Core Foundations Phase (M4-M11)"
        elif module_num in (12, 13, 14, 15):
            expected_size = 40
            phase_name = "Fluency Phase (M12-M15)"
        else:
            raise ValidationFailure(f"Invalid or unsupported module number: {module_num}")

        if total_questions != expected_size:
            raise ValidationFailure(
                f"Mock Exam Size Mismatch: Module {module_num} is in {phase_name}, "
                f"which requires exactly {expected_size} questions. Found {total_questions} questions."
            )

        # Rule: 70/20/10 Retrieval Weight Distribution
        # Determine current module's phase
        current_phase = MODULE_PHASES.get(module_num)
        
        count_current = 0
        count_same_phase_prev = 0
        count_older_phase = 0

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
                # Find all referenced modules
                ref_modules = set()
                for iid in source_item_ids:
                    m_match = re.match(r'M(\d+)', iid)
                    if m_match:
                        ref_modules.add(int(m_match.group(1)))
                
                if ref_modules:
                    # If any referenced module matches the current mock's module, classify as current
                    if module_num in ref_modules:
                        count_current += 1
                    else:
                        # Check the phase of the referenced modules
                        # If any referenced module belongs to same phase, classify as same_phase_prev
                        # Otherwise classify as older_phase
                        is_same_phase = False
                        for rm in ref_modules:
                            if MODULE_PHASES.get(rm) == current_phase:
                                is_same_phase = True
                                break
                        
                        if is_same_phase:
                            count_same_phase_prev += 1
                        else:
                            count_older_phase += 1
                    classified = True
            
            if not classified:
                # Classification method 3: level_source (or assume current for late fluency modules)
                if "level_source" in q or module_num >= 13:
                    count_current += 1
                else:
                    raise ValidationFailure(
                        f"Mock Exam, Question {q_id}: Cannot classify question source. "
                        f"Must have 'source' metadata, non-empty 'source_item_ids', or 'level_source' field."
                    )

        # Calculate percentages
        pct_current = (count_current / total_questions) * 100
        pct_same_phase_prev = (count_same_phase_prev / total_questions) * 100
        pct_older_phase = (count_older_phase / total_questions) * 100

        # Define expected distributions and allowed deviations per module type
        if module_num == 1:
            expected_current = 100
            expected_same_phase_prev = 0
            expected_older_phase = 0
        elif module_num in (2, 3, 5):
            expected_current = 70
            expected_same_phase_prev = 30
            expected_older_phase = 0
        elif module_num in (4, 6, 8):
            expected_current = 70
            expected_same_phase_prev = 0
            expected_older_phase = 30
        elif module_num in (7, 9, 10, 11, 12):
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

        self.log(
            f"{filepath.name} Stats: "
            f"Current={pct_current:.1f}% (Expected={expected_current}%), "
            f"SamePhasePrev={pct_same_phase_prev:.1f}% (Expected={expected_same_phase_prev}%), "
            f"OlderPhase={pct_older_phase:.1f}% (Expected={expected_older_phase}%)"
        )

        if (diff_current > self.tolerance or 
            diff_same_phase_prev > self.tolerance or 
            diff_older_phase > self.tolerance):
            raise ValidationFailure(
                f"Mock Retrieval Weight Deviation too large: "
                f"Current: {pct_current:.1f}% (Expected {expected_current}%, diff {diff_current:.1f}%), "
                f"Same-Phase-Prev: {pct_same_phase_prev:.1f}% (Expected {expected_same_phase_prev}%, diff {diff_same_phase_prev:.1f}%), "
                f"Older-Phase: {pct_older_phase:.1f}% (Expected {expected_older_phase}%, diff {diff_older_phase:.1f}%). "
                f"Allowed tolerance is {self.tolerance}%."
            )

    def validate_final_exam_file(self, filepath, data):
        """Validates that the final exam contains exactly 60 questions total."""
        expected_total = 60
        questions_total = data.get("questions_total")
        
        if questions_total != expected_total:
            raise ValidationFailure(
                f"Final Exam: 'questions_total' root attribute says {questions_total}, "
                f"but must be exactly {expected_total}."
            )

        sections = data.get("sections", [])
        if not isinstance(sections, list):
            raise ValidationFailure("Final Exam: 'sections' root attribute must be a list")

        actual_questions_count = 0
        for idx, sec in enumerate(sections):
            sec_title = sec.get("title_en") or f"Section {idx+1}"
            questions = sec.get("questions", [])
            if not isinstance(questions, list):
                raise ValidationFailure(f"Final Exam, Section '{sec_title}': 'questions' must be a list")
            actual_questions_count += len(questions)

        if actual_questions_count != expected_total:
            raise ValidationFailure(
                f"Final Exam Size Mismatch: Sum of questions in all sections is {actual_questions_count}, "
                f"but must be exactly {expected_total}."
            )

def main():
    parser = argparse.ArgumentParser(
        description="CLI Validation Suite for Curriculum Content JSON Files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="/app/hindi dataset",
        help="Absolute or relative path to the directory containing JSON files"
    )
    parser.add_argument(
        "-t", "--tolerance",
        type=float,
        default=10.0,
        help="Absolute percent tolerance allowed for 70/20/10 mock retrieval distribution weights"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed tracking and classification information"
    )

    args = parser.parse_args()

    validator = CurriculumValidator(
        directory=args.directory,
        tolerance=args.tolerance,
        verbose=args.verbose
    )
    
    validator.scan_and_classify()
    success = validator.run_all_validations()
    
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
