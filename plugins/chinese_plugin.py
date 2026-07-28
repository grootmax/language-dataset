from plugins.base import BasePlugin

class ChinesePlugin(BasePlugin):
    """
    Chinese validation plugin.
    Skips alphabet/pronunciation checks and allows tone-focused fields under generic attributes.
    """
    
    def validate(self, data: dict, schema_type: str) -> None:
        """
        Custom validation rules for Chinese datasets.
        """
        if schema_type == "level":
            for lvl in data.get("levels", []):
                for item in lvl.get("items", []):
                    attributes = item.get("attributes", {})
                    
                    # We can support and validate tone configurations in attributes
                    if "tones" in attributes:
                        tones = attributes["tones"]
                        if not isinstance(tones, (list, str, int)):
                            raise TypeError(
                                f"Chinese item '{item.get('id')}' has invalid tones format: '{tones}'. "
                                f"Must be a list, string, or integer."
                            )
                    
                    # Skips standard alphabet tests because Chinese uses logographic characters (Hanzi)
                    # We can verify that target does NOT contain western alphabet only if it is Hanzi
                    target = item.get("target", "")
                    if target and any('\u4e00' <= c <= '\u9fff' for c in target):
                        # The target contains Chinese characters. This is valid.
                        pass
