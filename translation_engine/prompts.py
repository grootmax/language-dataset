# target languages config & prompt templates

LANGUAGES = {
    "es": {
        "name": "Spanish",
        "iso_code": "es",
        "phonetic_adaptations": {
            "sh": "sh", # or 'ch' / 'x' based on pronunciation guides
            "ee": "i",
            "oo": "u",
            "v": "v/b",
            "a": "a",
            "aa": "a larga (hold longer)"
        },
        "grammar_gender_benchmarks": "Map Hindi grammatical gender (masculine/feminine) to Spanish grammatical gender (masculino/femenino). Highlight that Hindi has no neuter gender, similar to Spanish.",
        "instructional_rules": "Rename keys with suffix '_en' to '_es' and translate instructional texts and explanations into clear, educational Spanish."
    },
    "fr": {
        "name": "French",
        "iso_code": "fr",
        "phonetic_adaptations": {
            "sh": "ch",
            "ee": "i",
            "oo": "ou",
            "u": "ou (court)",
            "a": "a",
            "aa": "â"
        },
        "grammar_gender_benchmarks": "Map Hindi grammatical gender (masculine/feminine) to French grammatical gender (masculin/féminin). Highlight agreements.",
        "instructional_rules": "Rename keys with suffix '_en' to '_fr' and translate instructional texts and explanations into clear, educational French."
    },
    "de": {
        "name": "German",
        "iso_code": "de",
        "phonetic_adaptations": {
            "sh": "sch",
            "ch": "tsch",
            "ee": "i/ie",
            "oo": "u",
            "v": "w",
            "z": "s"
        },
        "grammar_gender_benchmarks": "Contrast Hindi's two-gender system (masculine/feminine) with German's three-gender system (masculine/feminine/neuter). Notice that Hindi lacks neuter.",
        "instructional_rules": "Rename keys with suffix '_en' to '_de' and translate instructional texts and explanations into clear, educational German."
    },
    "ja": {
        "name": "Japanese",
        "iso_code": "ja",
        "phonetic_adaptations": {
            "sh": "シャ/シ",
            "ee": "イー",
            "oo": "ウー",
            "a": "ア",
            "aa": "アー",
            "r": "ラ行"
        },
        "grammar_gender_benchmarks": "Contrast Hindi's strict grammatical gender with Japanese, which lacks grammatical noun gender entirely. Explain that adjective and verb agreements must be learned via Hindi rules.",
        "instructional_rules": "Rename keys with suffix '_en' to '_ja' and translate instructional texts and explanations into natural, educational Japanese."
    },
    "zh": {
        "name": "Mandarin Chinese",
        "iso_code": "zh",
        "phonetic_adaptations": {
            "sh": "sh (汉语拼音)",
            "ee": "i (衣)",
            "oo": "u (乌)",
            "a": "a (啊)",
            "aa": "a (长音)"
        },
        "grammar_gender_benchmarks": "Contrast Hindi's strict grammatical gender with Mandarin Chinese, which has no grammatical gender for inanimate nouns. Notice verb and adjective agreements in Hindi.",
        "instructional_rules": "Rename keys with suffix '_en' to '_zh' and translate instructional texts and explanations into clear, educational Simplified Chinese."
    },
    "ko": {
        "name": "Korean",
        "iso_code": "ko",
        "phonetic_adaptations": {
            "sh": "쉬/시",
            "ee": "이",
            "oo": "우",
            "a": "아",
            "aa": "아 (길게)"
        },
        "grammar_gender_benchmarks": "Contrast Hindi's strict grammatical gender with Korean, which has no grammatical gender. Explain agreement rules clearly in Korean.",
        "instructional_rules": "Rename keys with suffix '_en' to '_ko' and translate instructional texts and explanations into natural, polite, educational Korean."
    },
    "it": {
        "name": "Italian",
        "iso_code": "it",
        "phonetic_adaptations": {
            "sh": "sc(i)",
            "ee": "i",
            "oo": "u",
            "a": "a",
            "aa": "a lunga"
        },
        "grammar_gender_benchmarks": "Map Hindi grammatical gender (masculine/feminine) directly to Italian grammatical gender (maschile/femminile). Draw parallels with adjective agreement.",
        "instructional_rules": "Rename keys with suffix '_en' to '_it' and translate instructional texts and explanations into clear, educational Italian."
    },
    "pt": {
        "name": "Portuguese",
        "iso_code": "pt",
        "phonetic_adaptations": {
            "sh": "ch/x",
            "ee": "i",
            "oo": "u",
            "a": "a",
            "aa": "a longo"
        },
        "grammar_gender_benchmarks": "Map Hindi grammatical gender (masculine/feminine) directly to Portuguese grammatical gender (masculino/feminino). Highlight adjective agreements.",
        "instructional_rules": "Rename keys with suffix '_en' to '_pt' and translate instructional texts and explanations into clear, educational Portuguese."
    },
    "ru": {
        "name": "Russian",
        "iso_code": "ru",
        "phonetic_adaptations": {
            "sh": "ш",
            "ch": "ч",
            "ee": "и",
            "oo": "у",
            "a": "а",
            "aa": "долгий а"
        },
        "grammar_gender_benchmarks": "Contrast Hindi's two-gender system (masculine/feminine) with Russian's three-gender system (masculine/feminine/neuter). Emphasize verb past tense agreement in Hindi vs Russian.",
        "instructional_rules": "Rename keys with suffix '_en' to '_ru' and translate instructional texts and explanations into natural, educational Russian."
    },
    "ar": {
        "name": "Arabic",
        "iso_code": "ar",
        "phonetic_adaptations": {
            "sh": "ش",
            "ch": "تش",
            "ee": "ي",
            "oo": "و",
            "a": "فتحة",
            "aa": "ألف المد"
        },
        "grammar_gender_benchmarks": "Map Hindi grammatical gender (masculine/feminine) directly to Arabic grammatical gender (مذكر/مؤنث). Note that both languages have a strong distinction of gender in verbs and adjectives.",
        "instructional_rules": "Rename keys with suffix '_en' to '_ar' and translate instructional texts and explanations into high-quality, classical Arabic."
    },
    "te": {
        "name": "Telugu",
        "iso_code": "te",
        "phonetic_adaptations": {
            "sh": "శ/ష",
            "ee": "ఈ",
            "oo": "ఊ",
            "a": "అ",
            "aa": "ఆ (hold longer)"
        },
        "grammar_gender_benchmarks": "Map Hindi grammatical concepts directly to Telugu. Address nominal declensions, oblique stem declensions, postposition mappings (e.g. mapping Hindi postpositions like का, को, से, में, पर to Telugu case suffixes like యొక్క, కు/కి, తో, లో, పై/మీద), and ensure proper formal register usage in educational instruction.",
        "instructional_rules": "Rename keys with suffix '_en' to '_te' and translate instructional texts and explanations into clear, educational Telugu."
    }
}

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
