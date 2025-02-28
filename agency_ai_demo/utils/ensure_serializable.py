import json


# Add a utility function to ensure all values are JSON serializable
def ensure_serializable(obj):
    """
    Recursively ensure that an object and all its contents are JSON serializable.
    Handles Pydantic Field objects by extracting their values.
    """
    # Handle None
    if obj is None:
        return None

    # Check if it's a Field object (has certain common Field attributes)
    if hasattr(obj, "default") and hasattr(obj, "description"):
        # Return the default value or None
        if obj.default is not None:
            return obj.default
        return None

    # Handle dictionaries
    if isinstance(obj, dict):
        return {k: ensure_serializable(v) for k, v in obj.items()}

    # Handle lists
    if isinstance(obj, list):
        return [ensure_serializable(item) for item in obj]

    # Return other objects as is
    return obj
