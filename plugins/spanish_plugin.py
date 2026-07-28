from plugins.base import BasePlugin

class SpanishPlugin(BasePlugin):
    """
    Boilerplate validation stub for Spanish translation validation.
    Succeeds by default to not block development before custom rules are ready.
    """
    def validate(self, data: dict, schema_type: str) -> None:
        pass
