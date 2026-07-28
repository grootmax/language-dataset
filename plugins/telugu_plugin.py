from plugins.base import BasePlugin

class TeluguPlugin(BasePlugin):
    """
    Telugu validation plugin.
    Supports Telugu key normalization and other potential custom Telugu validations.
    """
    def __init__(self):
        super().__init__(language="telugu")
