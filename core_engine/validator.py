import os
from core_engine.sandbox import exec_sandboxed
from plugins.base import BasePlugin
from core_engine.schema import validate_structure

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
        if not language:
            return None
            
        language = language.lower()
        if language in self._plugin_cache:
            return self._plugin_cache[language]

        plugin_file = os.path.join(self.plugins_dir, f"{language}_plugin.py")
        if not os.path.exists(plugin_file):
            return None

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

    def _load_registry(self):
        import json
        registry_path = "/app/profiles/registry.json"
        if not os.path.exists(registry_path):
            raise RuntimeError(f"Unified registry file not found at {registry_path}")
        with open(registry_path, "r", encoding="utf-8") as f:
            self.registry = json.load(f)

    def get_profile(self, language: str) -> dict:
        if not hasattr(self, "registry") or not self.registry:
            self._load_registry()
            
        language = language.lower()
        if language not in self.registry.get("languages", {}):
            # Try finding by full name
            for k, v in self.registry.get("languages", {}).items():
                if v.get("language", "").lower() == language:
                    language = k
                    break
                    
        if language not in self.registry.get("languages", {}):
            raise ValueError(f"Language '{language}' is not explicitly registered in the unified registry. Failing closed.")
            
        profile = self.registry["languages"][language]
        
        # Structured Fallback Profile: provide default values for any missing sub-rules
        fallback_profile = {
            "language": profile.get("language", language),
            "iso_code": profile.get("iso_code", language),
            "permitted_genders": profile.get("permitted_genders", []),
            "active_phonetic_systems": profile.get("active_phonetic_systems", []),
            "script_traits": {
                "is_abugida": False,
                "has_matra": False,
                "has_sound_family": False,
                "has_tones": False,
                "has_word_masks": False
            },
            "script_boundaries": {
                "ranges": []
            }
        }
        if "script_traits" in profile:
            fallback_profile["script_traits"].update(profile["script_traits"])
        if "script_boundaries" in profile:
            fallback_profile["script_boundaries"].update(profile["script_boundaries"])
            
        return fallback_profile

    def detect_language(self, data: dict) -> str:
        """
        Detects language from content or metadata patterns using character block analysis.
        """
        if not hasattr(self, "registry") or not self.registry:
            self._load_registry()
            
        # Check explicit language keys
        for lang_code, lang_obj in self.registry.get("languages", {}).items():
            if f"module_name_{lang_code}" in data or f"title_{lang_code}" in str(data):
                return lang_code
                
        # Character block analysis over text values
        char_counts = {lang_code: 0 for lang_code in self.registry.get("languages", {})}
        
        def count_chars(v):
            if isinstance(v, str):
                for lang_code, lang_obj in self.registry.get("languages", {}).items():
                    ranges = lang_obj.get("script_boundaries", {}).get("ranges", [])
                    for start, end in ranges:
                        for char in v:
                            if start <= char <= end:
                                if start > "\u007F" or char.isalpha():
                                    char_counts[lang_code] += 1
            elif isinstance(v, list):
                for item in v:
                    count_chars(item)
            elif isinstance(v, dict):
                for item in v.values():
                    count_chars(item)
                    
        count_chars(data)
        
        # Priority rule: if any non-Latin language (starts above \u02FF) has a match > 0, we only consider those.
        non_latin_languages = {}
        latin_languages = {}
        for lang_code, count in char_counts.items():
            lang_obj = self.registry["languages"][lang_code]
            ranges = lang_obj.get("script_boundaries", {}).get("ranges", [])
            has_non_latin_range = any(start > "\u02FF" for start, end in ranges)
            if has_non_latin_range:
                non_latin_languages[lang_code] = count
            else:
                latin_languages[lang_code] = count
                
        if any(count > 0 for count in non_latin_languages.values()):
            active_candidates = {k: v for k, v in non_latin_languages.items() if v > 0}
        else:
            active_candidates = latin_languages
            
        best_lang = None
        max_count = 0
        for lang_code, count in active_candidates.items():
            if count > max_count:
                max_count = count
                best_lang = lang_code
                
        return best_lang

    def validate_script_boundaries(self, data: dict, language: str) -> None:
        profile = self.get_profile(language)
        ranges = profile.get("script_boundaries", {}).get("ranges", [])
        if not ranges:
            return
            
        def check_item(item):
            target = item.get("target")
            if target and isinstance(target, str):
                for char in target:
                    # Check if char is in allowed ranges
                    allowed = False
                    for start, end in ranges:
                        if start <= char <= end:
                            allowed = True
                            break
                    if not allowed:
                        # Allow safe characters (space, digits, punctuation)
                        # and ONLY raise error if the character is an alphabetic letter
                        if char.isalpha():
                            raise ValueError(
                                f"Script boundary violation: character '{char}' (U+{ord(char):04X}) "
                                f"in target '{target}' is outside the permitted script boundaries for language '{language}'."
                            )
                            
        def traverse(v):
            if isinstance(v, dict):
                if "target" in v:
                    check_item(v)
                for val in v.values():
                    traverse(val)
            elif isinstance(v, list):
                for item in v:
                    traverse(item)
                    
        traverse(data)

    def validate(self, data: dict, schema_type: str, language: str = None) -> dict:
        """
        Executes normalization, core schema validation, and dynamic plugin rules.
        """
        if not hasattr(self, "registry") or not self.registry:
            self._load_registry()
            
        if language is None:
            language = self.detect_language(data)
            
        if not language:
            raise ValueError("Language could not be detected, and none was specified. Failing closed.")
            
        # Normalize language to registry key
        language = language.lower()
        profile = self.get_profile(language)
        lang_code = profile["iso_code"]
        
        # Enforce fail-closed structure: if no valid profile exists, or if a validation plugin is expected but missing, fail closed.
        plugin = None
        plugin_file = os.path.join(self.plugins_dir, f"{lang_code}_plugin.py")
        if not os.path.exists(plugin_file):
            plugin_file = os.path.join(self.plugins_dir, f"{profile['language']}_plugin.py")
            
        if os.path.exists(plugin_file):
            plugin = self.load_plugin(profile["language"] if f"{profile['language']}_plugin.py" in plugin_file else lang_code)
            
        # Preprocess/Normalize legacy structures
        if plugin:
            normalized_data = plugin.normalize(data)
        else:
            normalized_data = data
            
        # Pure structural validation using generic schemas (replaces static database/table check)
        validate_structure(normalized_data, schema_type)
        
        # Dynamic script boundary checks
        self.validate_script_boundaries(normalized_data, lang_code)
        
        # Dynamic semantic validation via sandboxed plugin
        if plugin:
            plugin.validate(normalized_data, schema_type)
            
        return normalized_data
