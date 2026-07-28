from plugins.base import BasePlugin

class GermanPlugin(BasePlugin):
    """
    German validation plugin.
    Enforces that noun items must specify a valid gender in the generic attributes map.
    """
    def __init__(self):
        super().__init__(language="german")
    
    def validate(self, data: dict, schema_type: str) -> None:
        """
        Validates German nouns for grammatical gender.
        """
        if schema_type == "level":
            for lvl in data.get("levels", []):
                for item in lvl.get("items", []):
                    item_type = item.get("type", "")
                    
                    if item_type == "noun":
                        attributes = item.get("attributes", {})
                        gender = attributes.get("gender")
                        
                        if not gender:
                            raise ValueError(
                                f"German noun item '{item.get('id')}' is missing grammatical gender "
                                f"under generic attributes block."
                            )
                            
                        valid_genders = {"masculine", "feminine", "neuter"}
                        if gender.lower() not in valid_genders:
                            raise ValueError(
                                f"German noun item '{item.get('id')}' has invalid gender '{gender}'. "
                                f"Must be one of {valid_genders}."
                            )

        elif schema_type == "spine":
            for item in data.get("spine", []):
                item_type = item.get("type", "")
                if item_type == "noun":
                    attributes = item.get("attributes", {})
                    gender = attributes.get("gender")
                    if not gender or gender.lower() not in {"masculine", "feminine", "neuter"}:
                        raise ValueError(
                            f"German spine noun item '{item.get('id')}' has missing or invalid gender: '{gender}'"
                        )
