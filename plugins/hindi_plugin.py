import copy
from plugins.base import BasePlugin

class HindiPlugin(BasePlugin):
    """
    Hindi compatibility plugin validating Devanagari script rules & supporting legacy formats.
    """
    
    def normalize(self, data: dict) -> dict:
        """
        Preprocesses legacy Hindi datasets by moving custom properties into the 'attributes' block.
        """
        data_copy = copy.deepcopy(data)

        # Handle Level files
        if "levels" in data_copy:
            for lvl in data_copy["levels"]:
                for item in lvl.get("items", []):
                    # Separate standard schema keys from legacy Hindi-specific attributes
                    standard_keys = {"id", "type", "target", "read_as", "gloss_en", "difficulty", "tags", "attributes", "cards", "audio"}
                    item_keys = list(item.keys())
                    if "attributes" not in item:
                        item["attributes"] = {}
                    for k in item_keys:
                        if k not in standard_keys:
                            item["attributes"][k] = item.pop(k)

        # Handle Spine files
        elif "spine" in data_copy:
            for item in data_copy["spine"]:
                standard_keys = {"id", "level", "type", "target", "difficulty", "tags", "level_title_en", "derived_from_item", "attributes"}
                item_keys = list(item.keys())
                if "attributes" not in item:
                    item["attributes"] = {}
                for k in item_keys:
                    if k not in standard_keys:
                        item["attributes"][k] = item.pop(k)

        return data_copy

    def validate(self, data: dict, schema_type: str) -> None:
        """
        Linguistic validation for Hindi.
        Ensures that targets of phonetic/vocabulary items use the standard Devanagari block.
        """
        def has_devanagari(text):
            return any('\u0900' <= char <= '\u097f' for char in text)

        if schema_type == "level":
            for lvl in data.get("levels", []):
                for item in lvl.get("items", []):
                    target = item.get("target", "")
                    item_type = item.get("type", "")
                    
                    # We expect Devanagari characters in most level items (letters, words, vocabulary, etc.)
                    if item_type in ("letter", "vocabulary", "phrase", "grammar") and target:
                        if not has_devanagari(target):
                            raise ValueError(
                                f"Linguistic validation error in item '{item.get('id')}': "
                                f"target '{target}' does not contain Devanagari characters."
                            )

        elif schema_type == "spine":
            for item in data.get("spine", []):
                target = item.get("target", "")
                if target and not has_devanagari(target):
                    raise ValueError(
                        f"Linguistic validation error in spine item '{item.get('id')}': "
                        f"target '{target}' does not contain Devanagari characters."
                    )
