class InventoryConflict(Exception):
    """The requested state transition conflicts with current inventory state."""


class InventoryNotFound(Exception):
    """The requested inventory resource does not exist."""
