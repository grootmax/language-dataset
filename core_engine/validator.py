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

    _LANGUAGE_MAP = {
        "es": "spanish",
        "fr": "french",
        "ko": "korean",
        "it": "italian",
        "te": "telugu",
        "bn": "bengali",
        "mr": "marathi",
        "de": "german",
        "zh": "chinese",
        "hi": "hindi",
        "ja": "japanese",
        "ru": "russian",
        "ar": "arabic",
        "pt": "portuguese"
    }

    def load_plugin(self, language: str) -> BasePlugin:
        """
        Dynamically loads the plugin for the given language inside the restricted sandbox.
        """
        if not language:
            return None
            
        language = language.lower()
        # Resolve language code to full language name if mapped
        language = self._LANGUAGE_MAP.get(language, language)

        if language in self._plugin_cache:
            return self._plugin_cache[language]

        plugin_file = os.path.join(self.plugins_dir, f"{language}_plugin.py")
        if not os.path.exists(plugin_file):
            exact_path = os.path.abspath(plugin_file)
            err_msg = f"FAIL-CLOSED: Missing required validation plugin file for language '{language}'. Expected at: {exact_path}"
            # Log descriptive error detailing the exact missing plugin file
            import sys
            sys.stderr.write(f"ERROR: {err_msg}\n")
            raise FileNotFoundError(err_msg)

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

    def detect_language(self, data: dict) -> str:
        """
        Detects language from content or metadata patterns.
        """
        if "module_name_hi" in data or "title_hi" in str(data):
            return "hindi"

        # Check for Devanagari characters in text values
        def check_val(v):
            if isinstance(v, str):
                return any('\u0900' <= c <= '\u097f' for c in v)
            elif isinstance(v, list):
                return any(check_val(item) for item in v)
            elif isinstance(v, dict):
                return any(check_val(item) for item in v.values())
            return False

        if check_val(data):
            return "hindi"

        return None

    def validate(self, data: dict, schema_type: str, language: str = None) -> dict:
        """
        Executes normalization, core schema validation, and dynamic plugin rules.
        """
        if language is None:
            language = self.detect_language(data)

        plugin = self.load_plugin(language) if language else None

        # Preprocess/Normalize legacy structures (e.g. legacy Hindi files)
        if plugin:
            normalized_data = plugin.normalize(data)
        else:
            normalized_data = data

        # Structural validation using generic schemas (replaces static database/table check)
        validate_structure(normalized_data, schema_type)

        # Dynamic semantic validation via sandboxed plugin
        if plugin:
            plugin.validate(normalized_data, schema_type)

        return normalized_data
