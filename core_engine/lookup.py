class ReferentialIntegrityError(Exception):
    """
    Raised when referential integrity is violated, such as a question referencing
    a non-existent source item ID.
    """
    pass

class ItemLookupAdapter:
    """
    Generalized item-lookup adapter storing dynamic identifier mappings.
    """
    def __init__(self):
        self._items = {}

    def register_item(self, item_id: str, item_data: dict) -> None:
        """
        Registers an item under its unique ID.
        """
        self._items[item_id] = item_data

    def register_from_dataset(self, data: dict, schema_type: str) -> None:
        """
        Parses a dataset (level or spine) and registers all standard items found.
        """
        if schema_type == "level":
            for level in data.get("levels", []):
                for item in level.get("items", []):
                    self.register_item(item["id"], item)
        elif schema_type == "spine":
            for item in data.get("spine", []):
                self.register_item(item["id"], item)

    def get_item(self, item_id: str) -> dict:
        """
        Retrieves a registered item by ID.
        """
        return self._items.get(item_id)

    def exists(self, item_id: str) -> bool:
        """
        Returns True if the item is registered.
        """
        return item_id in self._items

def verify_referential_integrity(data: dict, schema_type: str, lookup_adapter: ItemLookupAdapter, strict: bool = True) -> None:
    """
    Verifies that all referenced items in checkpoints, mocks, or final exams exist in the lookup registry.
    Allows referenced items to be missing if 'prerequisite_inferred' is True.
    """
    errors = []

    if schema_type == "checkpoint":
        for cp in data.get("checkpoints", []):
            for q in cp.get("questions", []):
                q_id = q.get("id")
                source_ids = q.get("source_item_ids", [])
                for s_id in source_ids:
                    if not lookup_adapter.exists(s_id):
                        msg = f"Checkpoint Question '{q_id}' references non-existent item '{s_id}'."
                        errors.append(msg)

    elif schema_type == "mock":
        questions = data.get("mock_exam", {}).get("questions", [])
        for q in questions:
            q_id = q.get("id")
            source_ids = q.get("source_item_ids", [])
            for s_id in source_ids:
                if not lookup_adapter.exists(s_id):
                    msg = f"Mock Question '{q_id}' references non-existent item '{s_id}'."
                    errors.append(msg)

    elif schema_type == "final_exam":
        for sec in data.get("sections", []):
            sec_name = sec.get("section")
            for q in sec.get("questions", []):
                q_num = q.get("n")
                source_ids = q.get("source_item_ids", [])
                inferred = q.get("prerequisite_inferred", False)
                # If inferred, skip the strict presence check
                if inferred:
                    continue
                for s_id in source_ids:
                    if not lookup_adapter.exists(s_id):
                        msg = f"Final Exam Section '{sec_name}' Question {q_num} references non-existent item '{s_id}'."
                        errors.append(msg)

    if errors:
        error_msg = "\n".join(errors)
        if strict:
            raise ReferentialIntegrityError(error_msg)
        else:
            print(f"Warning: Referential integrity checks failed:\n{error_msg}")
