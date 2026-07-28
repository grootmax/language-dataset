import os
import json
from core_engine.sandbox import exec_sandboxed
from plugins.base import BasePlugin
from core_engine.schema import validate_structure

class ParametricFallbackPlugin(BasePlugin):
    """
    A shared parametric fallback plugin that parses a declarative JSON profile
    and applies script-level and grammatical validations.
    """
    def __init__(self, profile_data: dict):
        self.profile_data = profile_data
        self.language = profile_data.get("language", "").lower()
        self.permitted_genders = profile_data.get("permitted_genders", [])
        self.script_traits = profile_data.get("script_traits", {})

    def validate(self, data: dict, schema_type: str) -> None:
        def check_script_characters(text, lang):
            if lang in ("hindi", "marathi"):
                return any('\u0900' <= char <= '\u097f' for char in text), "Devanagari"
            elif lang == "telugu":
                return any('\u0c00' <= char <= '\u0c7f' for char in text), "Telugu"
            elif lang == "bengali":
                return any('\u0980' <= char <= '\u09ff' for char in text), "Bengali"
            return True, ""

        # Validate level items
        if schema_type == "level":
            for lvl in data.get("levels", []):
                for item in lvl.get("items", []):
                    # Grammatical check
                    if self.permitted_genders:
                        attributes = item.get("attributes", {})
                        gender = attributes.get("gender")
                        if gender:
                            if gender.lower() not in [g.lower() for g in self.permitted_genders]:
                                raise ValueError(
                                    f"Item '{item.get('id')}' has invalid gender '{gender}'. "
                                    f"Must be one of {self.permitted_genders}."
                                )
                        elif item.get("type") == "noun":
                            raise ValueError(
                                f"Noun item '{item.get('id')}' is missing grammatical gender under generic attributes block."
                            )

                    # Script validation
                    target = item.get("target", "")
                    item_type = item.get("type", "")
                    if target and item_type in ("letter", "vocabulary", "phrase", "grammar"):
                        is_valid, script_name = check_script_characters(target, self.language)
                        if not is_valid:
                            raise ValueError(
                                f"Linguistic validation error in item '{item.get('id')}': "
                                f"target '{target}' does not contain {script_name} characters."
                            )

        # Validate spine items
        elif schema_type == "spine":
            for item in data.get("spine", []):
                # Grammatical check
                if self.permitted_genders:
                    attributes = item.get("attributes", {})
                    gender = attributes.get("gender")
                    if gender:
                        if gender.lower() not in [g.lower() for g in self.permitted_genders]:
                            raise ValueError(
                                f"Spine item '{item.get('id')}' has invalid gender '{gender}'. "
                                f"Must be one of {self.permitted_genders}."
                            )
                    elif item.get("type") == "noun":
                        raise ValueError(
                            f"Spine noun item '{item.get('id')}' has missing or invalid gender: '{gender}'"
                        )

                # Script validation
                target = item.get("target", "")
                if target:
                    is_valid, script_name = check_script_characters(target, self.language)
                    if not is_valid:
                        raise ValueError(
                            f"Linguistic validation error in spine item '{item.get('id')}': "
                            f"target '{target}' does not contain {script_name} characters."
                        )

class Validator:
    """
    Core validator coordinating schema validation and target-language pluggable rules.
    """
    def __init__(self, plugins_dir="/app/plugins"):
        self.plugins_dir = plugins_dir
        self._plugin_cache = {}

    def load_plugin(self, language: str) -> BasePlugin:
        """
        Dynamically loads the plugin for the given language inside the restricted sandbox.
        """
        strict_mode = os.environ.get("STRICT_VALIDATION", "").lower() in ("true", "1", "yes")

        if not language:
            if strict_mode:
                raise ValueError("Strict Validation Error: Language is missing or could not be detected under strict validation mode.")
            return None
            
        language = language.lower()
        if language in self._plugin_cache:
            return self._plugin_cache[language]

        plugin_file = os.path.join(self.plugins_dir, f"{language}_plugin.py")
        if os.path.exists(plugin_file):
            with open(plugin_file, "r", encoding="utf-8") as f:
                source = f.read()

            # Execute inside the safe sandboxed environment
            extra_globals = {
                "BasePlugin": BasePlugin
            }
            sandbox_globals = exec_sandboxed(source, plugin_file, extra_globals)

            # Retrieve the dynamic subclass of BasePlugin
            plugin_class = None
            for name, obj in sandbox_globals.items():
                if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                    plugin_class = obj
                    break

            if not plugin_class:
                raise RuntimeError(f"No valid class inheriting from BasePlugin found in {plugin_file}")

            plugin_instance = plugin_class()
            self._plugin_cache[language] = plugin_instance
            return plugin_instance

        # Python plugin doesn't exist. Check for declarative JSON profile.
        profiles_dir = "/app/profiles"
        profile_file = os.path.join(profiles_dir, f"{language}.json")
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                plugin_instance = ParametricFallbackPlugin(profile_data)
                self._plugin_cache[language] = plugin_instance
                return plugin_instance
            except Exception as e:
                if strict_mode:
                    raise ValueError(f"Failed to load or parse profile for '{language}': {e}")
                else:
                    print(f"Warning: Failed to load profile for '{language}': {e}")
                    return None

        # Neither custom Python plugin nor JSON profile is found on disk
        if strict_mode:
            raise FileNotFoundError(f"Configuration profile for language '{language}' is missing under strict validation mode.")
        else:
            print(f"Warning: Configuration profile for language '{language}' is missing. Skipping dynamic validation.")
            return None

    def detect_language(self, data: dict) -> str:
        """
        Detects language from content or metadata patterns.
        """
        # Step 1: Scan for explicit configuration keys or suffixes
        def find_lang_by_keys(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    k_lower = k.lower()
                    if k_lower.endswith("_hi") or "title_hi" in k_lower or "name_hi" in k_lower:
                        return "hindi"
                    elif k_lower.endswith("_te") or "title_te" in k_lower or "name_te" in k_lower:
                        return "telugu"
                    elif k_lower.endswith("_bn") or "title_bn" in k_lower or "name_bn" in k_lower:
                        return "bengali"
                    elif k_lower.endswith("_mr") or "title_mr" in k_lower or "name_mr" in k_lower:
                        return "marathi"
                    elif k_lower.endswith("_de") or "title_de" in k_lower or "name_de" in k_lower:
                        return "german"
                    elif k_lower.endswith("_nl") or "title_nl" in k_lower or "name_nl" in k_lower:
                        return "dutch"
                    elif k_lower.endswith("_zh") or "title_zh" in k_lower or "name_zh" in k_lower:
                        return "chinese"
                    
                    res = find_lang_by_keys(v)
                    if res:
                        return res
            elif isinstance(d, list):
                for item in d:
                    res = find_lang_by_keys(item)
                    if res:
                        return res
            return None

        lang = find_lang_by_keys(data)
        if lang:
            return lang

        # Step 2: Check for character script boundaries in text values
        def check_val(v):
            if isinstance(v, str):
                if any('\u0c00' <= c <= '\u0c7f' for c in v):
                    return "telugu"
                if any('\u0980' <= c <= '\u09ff' for c in v):
                    return "bengali"
                if any('\u0900' <= c <= '\u097f' for c in v):
                    return "hindi"  # Default Devanagari to Hindi
                if any('\u4e00' <= c <= '\u9fff' for c in v):
                    return "chinese"
            elif isinstance(v, list):
                for item in v:
                    res = check_val(item)
                    if res:
                        return res
            elif isinstance(v, dict):
                for item in v.values():
                    res = check_val(item)
                    if res:
                        return res
            return None

        detected = check_val(data)
        if detected:
            return detected

        return None

    def validate(self, data: dict, schema_type: str, language: str = None) -> dict:
        """
        Executes normalization, core schema validation, and dynamic plugin rules.
        """
        if language is None:
            language = self.detect_language(data)

        # Strict validation mode check for language presence
        strict_mode = os.environ.get("STRICT_VALIDATION", "").lower() in ("true", "1", "yes")
        if strict_mode and not language:
            raise ValueError("Target language could not be detected, and was not explicitly specified under strict validation mode.")

        plugin = self.load_plugin(language) if language else None

        # Preprocess/Normalize legacy structures (e.g. legacy Hindi files)
        if plugin:
            normalized_data = plugin.normalize(data)
        else:
            normalized_data = data

        # Structural validation using generic schemas (replaces static database/table check)
        validate_structure(normalized_data, schema_type)

        # Dynamic semantic validation via sandboxed/fallback plugin
        if plugin:
            plugin.validate(normalized_data, schema_type)

        return normalized_data
