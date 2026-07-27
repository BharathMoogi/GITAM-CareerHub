from typing import Any, Dict


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive keys from dictionary payloads before logging or returning.
    """
    sensitive_keys = {"password", "hashed_password", "token", "secret", "access_token"}
    return {
        k: "******" if k.lower() in sensitive_keys else v
        for k, v in data.items()
    }
