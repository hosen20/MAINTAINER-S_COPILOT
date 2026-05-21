import re
from typing import Any

REDACTION = "[REDACTED]"

PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"Authorization:\s*.+", re.IGNORECASE),
    re.compile(r"password\s*=\s*[^,\s]+", re.IGNORECASE),
    re.compile(r"postgresql://[^ \n]+", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----", re.DOTALL),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in PATTERNS:
        redacted = pattern.sub(REDACTION, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value