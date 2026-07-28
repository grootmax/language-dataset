import argparse
import sys
import os
import glob
from translation_engine.translator import CurriculumTranslator
from translation_engine.validators import validate_file_comprehensive, ValidationError
from translation_engine.prompts import LANGUAGES

def main():
    parser = argparse.ArgumentParser(
        description="Automated Translation & Validation Engine for Hindi Curriculum."
    )
    
    parser.add_argument(
        "-s", "--source",
        required=True,
        help="Path to the source JSON file or directory containing JSON files."
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Path to the output JSON file or directory where localized files will be saved."
    )
    
    parser.add_argument(
        "-t", "--target",
        help=f"Target language code. Supported: {', '.join(LANGUAGES.keys())}"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run validation checks on existing file(s) without translating."
    )
    
    parser.add_argument(
        "--no-simulation",
        action="store_false",
        dest="simulation",
        default=True,
        help="Run real LLM translation instead of programmatic simulation (requires OPENAI_API_KEY)."
    )
    
    args = parser.parse_args()
    
    # 1. Validation Only Mode
    if args.validate_only:
        print("Running in VALIDATION-ONLY mode...")
        if os.path.isdir(args.source):
            files = glob.glob(os.path.join(args.source, "*.json"))
            if not files:
                print(f"No JSON files found in directory: {args.source}")
                sys.exit(0)
            
            success = True
            print(f"Found {len(files)} JSON files. Commencing validation...")
            for f in sorted(files):
                try:
                    validate_file_comprehensive(f)
                    print(f"  [PASS] {os.path.basename(f)}")
                except Exception as e:
                    print(f"  [FAIL] {os.path.basename(f)}: {e}")
                    success = False
            
            if success:
                print("All files validated successfully!")
                sys.exit(0)
            else:
                print("Some files failed validation checks.")
                sys.exit(1)
        else:
            try:
                validate_file_comprehensive(args.source)
                print(f"[PASS] {args.source} is fully valid against all schemas and Card Math/Weight rules!")
                sys.exit(0)
            except Exception as e:
                print(f"[FAIL] {args.source} validation failed: {e}")
                sys.exit(1)
                
    # 2. Translation Mode
    if not args.target:
        parser.error("--target is required unless --validate-only is specified.")
        
    from translation_engine.prompts import normalize_language_code
    normalized_target = normalize_language_code(args.target)
    if normalized_target not in LANGUAGES:
        print(f"Error: Unsupported target language '{args.target}'. Supported: {list(LANGUAGES.keys())}")
        sys.exit(1)
    args.target = normalized_target
        
    # Translate single file or directory
    is_dir_source = os.path.isdir(args.source)
    
    if is_dir_source:
        if not args.output:
            print("Error: --output directory is required when --source is a directory.")
            sys.exit(1)
            
        os.makedirs(args.output, exist_ok=True)
        files = glob.glob(os.path.join(args.source, "*.json"))
        if not files:
            print(f"No JSON files found in source directory: {args.source}")
            sys.exit(0)
            
        print(f"Commencing translation of {len(files)} files to '{args.target}'...")
        translator = CurriculumTranslator(args.target)
        
        success_count = 0
        failure_count = 0
        
        for f in sorted(files):
            filename = os.path.basename(f)
            # e.g., output_dir/module01_levels01-05_es.json
            base, ext = os.path.splitext(filename)
            dest_filename = f"{base}_{args.target}{ext}"
            dest_path = os.path.join(args.output, dest_filename)
            
            try:
                translator.translate_file(f, dest_path, use_simulation=args.simulation)
                print(f"  [SUCCESS] {filename} -> {dest_filename}")
                success_count += 1
            except Exception as e:
                print(f"  [FAILED] {filename}: {e}")
                failure_count += 1
                
        print(f"\nBulk translation complete. Success: {success_count}, Failures: {failure_count}")
        if failure_count > 0:
            sys.exit(1)
        sys.exit(0)
        
    else:
        # Single file translation
        if not args.output:
            # Auto-generate output path
            base, ext = os.path.splitext(args.source)
            dest_path = f"{base}_{args.target}{ext}"
        else:
            dest_path = args.output
            if os.path.isdir(dest_path):
                # If output is a directory, put the file in that directory
                filename = os.path.basename(args.source)
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(dest_path, f"{base}_{args.target}{ext}")
                
        print(f"Translating {args.source} to '{args.target}' -> {dest_path}...")
        try:
            translator = CurriculumTranslator(args.target)
            translator.translate_file(args.source, dest_path, use_simulation=args.simulation)
            print("[SUCCESS] Translation and fail-fast validation completed successfully!")
            sys.exit(0)
        except Exception as e:
            print(f"[FAILED] {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
