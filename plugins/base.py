import copy

LANG_MAP = {
    "spanish": ["spanish", "es"],
    "french": ["french", "fr"],
    "german": ["german", "de"],
    "japanese": ["japanese", "ja"],
    "chinese": ["chinese", "zh"],
    "korean": ["korean", "ko"],
    "italian": ["italian", "it"],
    "portuguese": ["portuguese", "pt"],
    "russian": ["russian", "ru"],
    "arabic": ["arabic", "ar"],
    "telugu": ["telugu", "te"],
    "hindi": ["hindi", "hi"],
}

def normalize_regional_keys(data: dict, keys_to_normalize: list) -> dict:
    """
    Specifically normalizes regional keys under example_word and cards.learn.examples.
    """
    if "levels" not in data:
        return data
        
    for lvl in data["levels"]:
        for item in lvl.get("items", []):
            # 1. Normalize example_word
            if "example_word" in item and isinstance(item["example_word"], dict):
                ex_word = item["example_word"]
                for k in list(ex_word.keys()):
                    if k in keys_to_normalize:
                        ex_word["text"] = ex_word.pop(k)
                        
            # 2. Normalize cards -> learn -> examples
            cards = item.get("cards")
            if isinstance(cards, dict):
                learn = cards.get("learn")
                if isinstance(learn, dict):
                    examples = learn.get("examples")
                    if isinstance(examples, list):
                        for ex in examples:
                            if isinstance(ex, dict):
                                for k in list(ex.keys()):
                                    if k in keys_to_normalize:
                                        ex["text"] = ex.pop(k)
    return data

class BasePlugin:
    """
    Abstract base class for target language validation plugins.
    Each language plugin must subclass this to provide custom validation rules
    and data normalization for legacy compatibility.
    """
    def __init__(self, language=None):
        self.language = language
    
    def normalize(self, data: dict) -> dict:
        """
        Transforms legacy input formats into the standard, language-agnostic schema
        format. Returns a new or modified dictionary.
        """
        data_copy = copy.deepcopy(data)
        
        # Determine regional keys to normalize
        keys_to_normalize = ["hindi", "hi"]
        if self.language:
            lang_lower = self.language.lower()
            if lang_lower in LANG_MAP:
                keys_to_normalize = copy.copy(LANG_MAP[lang_lower])
            else:
                for k, v in LANG_MAP.items():
                    if lang_lower in v or lang_lower == k:
                        keys_to_normalize = copy.copy(v)
                        break
        
        # Always include both detected language codes/names and "hindi" as fallbacks
        if "hindi" not in keys_to_normalize:
            keys_to_normalize.append("hindi")
        if "hi" not in keys_to_normalize:
            keys_to_normalize.append("hi")
            
        return normalize_regional_keys(data_copy, keys_to_normalize)

    def validate(self, data: dict, schema_type: str) -> None:
        """
        Performs custom language-specific validation rules (e.g. Devanagari script,
        gender specifications, tone validations) on the dataset.
        Should raise ValueError/TypeError or a custom Exception on failure.
        """
        pass
