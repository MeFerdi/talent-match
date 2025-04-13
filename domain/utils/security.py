def validate_task_payload(payload):
    """
    Validates the structure and content of a task payload.

    Args:
        payload (dict): The task payload to validate.

    Returns:
        bool: True if the payload is valid, False otherwise.
    """
    if not isinstance(payload, dict):
        return False

    if "task_id" not in payload or "data" not in payload:
        return False

    if not isinstance(payload["task_id"], str):
        return False

    if not isinstance(payload["data"], dict):
        return False

    return True