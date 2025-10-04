"""PII and secrets redaction utilities."""

import re
from typing import Pattern

from genai_otel.config import GenAIConfig

# Redaction patterns
PATTERNS: dict[str, Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "api_key": re.compile(r"\b[A-Za-z0-9_-]{20,}\b(?=.*key)", re.IGNORECASE),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    "phone": re.compile(r"\b\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ipv4": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    "aws_key": re.compile(r"(?:AWS|aws)[\w]*(?:key|KEY)[\w]*\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
}

# Redaction replacements
REPLACEMENTS = {
    "email": "[EMAIL_REDACTED]",
    "ssn": "[SSN_REDACTED]",
    "api_key": "[API_KEY_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "ipv4": "[IP_REDACTED]",
    "bearer_token": "[BEARER_TOKEN_REDACTED]",
    "aws_key": "[AWS_KEY_REDACTED]",
    "github_token": "[GITHUB_TOKEN_REDACTED]",
}


def redact_sensitive_data(text: str, config: GenAIConfig) -> str:
    """
    Redact sensitive data from text based on configured patterns.

    Args:
        text: Input text to redact
        config: Configuration with redaction patterns

    Returns:
        Redacted text
    """
    redacted = text

    for pattern_name in config.redact_patterns:
        pattern_name = pattern_name.strip().lower()
        if pattern_name in PATTERNS:
            pattern = PATTERNS[pattern_name]
            replacement = REPLACEMENTS.get(pattern_name, "[REDACTED]")
            redacted = pattern.sub(replacement, redacted)

    return redacted


def add_redaction_pattern(name: str, pattern: str, replacement: str = "[REDACTED]") -> None:
    """
    Add a custom redaction pattern.

    Args:
        name: Pattern identifier
        pattern: Regex pattern string
        replacement: Replacement text
    """
    PATTERNS[name] = re.compile(pattern)
    REPLACEMENTS[name] = replacement
