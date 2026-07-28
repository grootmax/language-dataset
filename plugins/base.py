class BasePlugin:
    """
    Abstract base class for target language validation plugins.
    Each language plugin must subclass this to provide custom validation rules
    and data normalization for legacy compatibility.
    """
    
    def normalize(self, data: dict) -> dict:
        """
        Transforms legacy input formats into the standard, language-agnostic schema
        format. Returns a new or modified dictionary.
        By default, returns the data unmodified.
        """
        return data

    def validate(self, data: dict, schema_type: str) -> None:
        """
        Performs custom language-specific validation rules (e.g. Devanagari script,
        gender specifications, tone validations) on the dataset.
        Should raise ValueError/TypeError or a custom Exception on failure.
        """
        pass
