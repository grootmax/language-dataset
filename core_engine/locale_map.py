LOCALE_KEYS = {
    "hindi": {
        "vocab_key": "hindi",
        "reading_text_key": "hindi_text",
        "module_name_key": "module_name_hi",
        "title_key": "title_hi",
        "iso": "hi"
    },
    "german": {
        "vocab_key": "german",
        "reading_text_key": "german_text",
        "module_name_key": "module_name_de",
        "title_key": "title_de",
        "iso": "de"
    },
    "spanish": {
        "vocab_key": "spanish",
        "reading_text_key": "spanish_text",
        "module_name_key": "module_name_es",
        "title_key": "title_es",
        "iso": "es"
    },
    "french": {
        "vocab_key": "french",
        "reading_text_key": "french_text",
        "module_name_key": "module_name_fr",
        "title_key": "title_fr",
        "iso": "fr"
    },
    "japanese": {
        "vocab_key": "japanese",
        "reading_text_key": "japanese_text",
        "module_name_key": "module_name_ja",
        "title_key": "title_ja",
        "iso": "ja"
    },
    "chinese": {
        "vocab_key": "chinese",
        "reading_text_key": "chinese_text",
        "module_name_key": "module_name_zh",
        "title_key": "title_zh",
        "iso": "zh"
    },
    "korean": {
        "vocab_key": "korean",
        "reading_text_key": "korean_text",
        "module_name_key": "module_name_ko",
        "title_key": "title_ko",
        "iso": "ko"
    },
    "italian": {
        "vocab_key": "italian",
        "reading_text_key": "italian_text",
        "module_name_key": "module_name_it",
        "title_key": "title_it",
        "iso": "it"
    },
    "portuguese": {
        "vocab_key": "portuguese",
        "reading_text_key": "portuguese_text",
        "module_name_key": "module_name_pt",
        "title_key": "title_pt",
        "iso": "pt"
    },
    "russian": {
        "vocab_key": "russian",
        "reading_text_key": "russian_text",
        "module_name_key": "module_name_ru",
        "title_key": "title_ru",
        "iso": "ru"
    },
    "arabic": {
        "vocab_key": "arabic",
        "reading_text_key": "arabic_text",
        "module_name_key": "module_name_ar",
        "title_key": "title_ar",
        "iso": "ar"
    },
    "dutch": {
        "vocab_key": "dutch",
        "reading_text_key": "dutch_text",
        "module_name_key": "module_name_nl",
        "title_key": "title_nl",
        "iso": "nl"
    },
    "telugu": {
        "vocab_key": "telugu",
        "reading_text_key": "telugu_text",
        "module_name_key": "module_name_te",
        "title_key": "title_te",
        "iso": "te"
    }
}

def detect_language_from_path_or_data(file_path=None, data=None):
    # Try to detect from file path first
    if file_path:
        path_lower = str(file_path).lower()
        # Check full language names first
        for lang, mapping in LOCALE_KEYS.items():
            if lang in path_lower:
                return lang
        # Check ISO codes next (with word boundaries or suffix match, e.g., _es.json, _de.json)
        for lang, mapping in LOCALE_KEYS.items():
            iso = mapping["iso"]
            if f"_{iso}." in path_lower or f"_{iso}/" in path_lower or path_lower.endswith(f"_{iso}"):
                return lang

    # Try to detect from data structure
    if data and isinstance(data, dict):
        # Check module_name_xx or title_xx or example_word keys
        for lang, mapping in LOCALE_KEYS.items():
            if mapping["module_name_key"] in data:
                return lang
            
        # Check check_val for Devanagari (Hindi fallback)
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

        # Check title_xx in stringified data
        data_str = str(data)
        for lang, mapping in LOCALE_KEYS.items():
            if mapping["title_key"] in data_str:
                return lang
            if mapping["vocab_key"] in data_str:
                return lang

    return "hindi"  # default fallback

def parameterize_core_schema(obj, lang_mapping):
    vocab_key = lang_mapping.get("vocab_key", "hindi")
    module_name_key = lang_mapping.get("module_name_key", "module_name_hi")
    title_key = lang_mapping.get("title_key", "title_hi")
    
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            new_key = k
            if k == "hindi":
                new_key = vocab_key
            elif k == "module_name_hi":
                new_key = module_name_key
            elif k == "title_hi":
                new_key = title_key
                
            new_obj[new_key] = parameterize_core_schema(v, lang_mapping)
        return new_obj
    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            if item == "hindi":
                new_list.append(vocab_key)
            elif item == "module_name_hi":
                new_list.append(module_name_key)
            elif item == "title_hi":
                new_list.append(title_key)
            else:
                new_list.append(parameterize_core_schema(item, lang_mapping))
        return new_list
    else:
        return obj
