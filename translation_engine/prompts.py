# target languages config & prompt templates
import json
import os

REGISTRY_PATH = "/app/profiles/registry.json"

def load_languages_from_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            try:
                registry = json.load(f)
                return registry.get("languages", {})
            except Exception:
                pass
    return {}

LANGUAGES = load_languages_from_registry()

def get_prompt_template(target_language_code, file_type):
    """
    Returns a comprehensive, parameterized system prompt for generating translation.
    """
    lang_info = LANGUAGES.get(target_language_code)
    if not lang_info:
        raise ValueError(f"Language '{target_language_code}' is not supported.")
        
    prompt = f"""You are an expert curriculum translator and localization engineer.
Your task is to translate and localize a Hindi teaching curriculum from English into {lang_info['name']} ('{target_language_code}').

TARGET LANGUAGE PROFILE for '{target_language_code}':
- Phonetic Adaptations: {lang_info['phonetic_adaptations']}
- Grammar/Gender Benchmarks: {lang_info['grammar_gender_benchmarks']}
- Instructional Translation Rules: {lang_info['instructional_rules']}

STRICT INSTRUCTIONS:
1. Translate all instructional texts, explanation texts, and prompts from English into {lang_info['name']}.
2. Keep the exact logical and structural schema of the JSON file intact.
3. Rename all keys with a suffix '_en' to ending with '_{target_language_code}' (e.g., 'title_en' -> 'title_{target_language_code}', 'explanation_en' -> 'explanation_{target_language_code}').
4. Do NOT translate technical fields, language-specific targets like 'hindi' or raw letter targets (e.g. 'अ'), IDs, answer indices, formats, or audio settings.
5. In vocabulary elements and read-as aids, adapt the phonetic read-as notations according to the specified phonetic adaptation rules for '{target_language_code}' where helpful.
6. Localize any 'english' translation inside 'example_word' or examples into {lang_info['name']}. Change the key 'english' to '{lang_info['name'].lower()}' or '{target_language_code}'.
7. Ensure 100% adherence to the structural schema and do NOT truncate or omit any sections. Return ONLY valid JSON matching the schema.
"""
    return prompt
