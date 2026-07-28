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
        if module_num:
            for lvl in data.get("levels", []):
                for item in lvl.get("items", []):
                    item_id = item.get("id")
                    if item_id:
                        self.level_item_ids[module_num].add(item_id)
                        
        from translation_engine.validators import validate_file_comprehensive, ValidationError as ValErr
        try:
            validate_file_comprehensive(str(filepath))
        except ValErr as ve:
            raise ValidationFailure(str(ve))

    def validate_checkpoint_file(self, filepath, data):
        """Validates checkpoints contain exactly 10 questions and all referenced level items exist."""
        from translation_engine.validators import validate_file_comprehensive, ValidationError as ValErr
        try:
            validate_file_comprehensive(str(filepath))
        except ValErr as ve:
            raise ValidationFailure(str(ve))

    def validate_mock_file(self, filepath, data):
        """Validates mock exam size and 70/20/10 cumulative weight distribution rules."""
        from translation_engine.validators import validate_file_comprehensive, ValidationError as ValErr
        try:
            validate_file_comprehensive(str(filepath))
        except ValErr as ve:
            raise ValidationFailure(str(ve))

    def validate_final_exam_file(self, filepath, data):
        """Validates that the final exam contains exactly 60 questions total."""
        from translation_engine.validators import validate_file_comprehensive, ValidationError as ValErr
        try:
            validate_file_comprehensive(str(filepath))
        except ValErr as ve:
            raise ValidationFailure(str(ve))

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
