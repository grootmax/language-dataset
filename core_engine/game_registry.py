class GameWidget:
    """
    API contract for an independent, pluggable learning game or widget.
    """
    def __init__(self, name: str, required_attributes: list, required_item_types: list = None):
        self.name = name
        self.required_attributes = required_attributes
        self.required_item_types = required_item_types or []

    def can_run(self, item: dict) -> bool:
        """
        Validates if the game component can execute against the given generic item properties.
        """
        # Type check
        if self.required_item_types and item.get("type") not in self.required_item_types:
            return False

        # Attribute checks
        attributes = item.get("attributes", {})
        for attr in self.required_attributes:
            if attr not in attributes:
                return False

        return True

    def run(self, item: dict) -> dict:
        """
        Runs the game widget on the target item.
        """
        if not self.can_run(item):
            raise ValueError(f"Game '{self.name}' cannot run on item '{item.get('id')}'. Unmet requirements.")
            
        return {
            "game_name": self.name,
            "status": "ready",
            "item_id": item.get("id"),
            "target": item.get("target"),
            "extracted_attributes": {
                attr: item.get("attributes", {}).get(attr) for attr in self.required_attributes
            }
        }

class GameRegistry:
    """
    Registry managing pluggable widgets dynamically without core engine updates.
    """
    def __init__(self):
        self._games = {}

    def register_game(self, name: str, game_widget: GameWidget) -> None:
        """
        Registers a game widget.
        """
        self._games[name] = game_widget

    def get_game(self, name: str) -> GameWidget:
        """
        Retrieves a registered game widget.
        """
        return self._games.get(name)

    def get_compatible_games(self, item: dict) -> list:
        """
        Returns list of game names compatible with the given item.
        """
        return [name for name, game in self._games.items() if game.can_run(item)]
