from plugins.base import BasePlugin

class TeluguPlugin(BasePlugin):
    """
    Telugu validation plugin.
    Ensures that targets of phonetic/vocabulary items use the standard Telugu Unicode block.
    """
    
    def normalize(self, data: dict) -> dict:
        """
        Preprocesses legacy Telugu datasets or maps format if needed.
        """
        return data

    def validate(self, data: dict, schema_type: str) -> None:
        """
        Linguistic validation for Telugu.
        Ensures that targets of phonetic/vocabulary items use the standard Telugu block.
        """
        def has_telugu(text):
            return any('\u0c00' <= char <= '\u0c7f' for char in text)

        if schema_type == "level":
            for lvl in data.get("levels", []):
                for item in lvl.get("items", []):
                    target = item.get("target", "")
                    item_type = item.get("type", "")
                    
                    if item_type in ("letter", "vocabulary", "phrase", "grammar", "word") and target:
                        if not has_telugu(target):
                            raise ValueError(
                                f"Linguistic validation error in item '{item.get('id')}': "
                                f"target '{target}' does not contain Telugu characters."
                            )

        elif schema_type == "spine":
            for item in data.get("spine", []):
                target = item.get("target", "")
                if target and not has_telugu(target):
                    raise ValueError(
                        f"Linguistic validation error in spine item '{item.get('id')}': "
                        f"target '{target}' does not contain Telugu characters."
                    )
