"""Configuration management for GenAI OpenTelemetry SDK."""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GenAIConfig:
    """Configuration for GenAI instrumentation."""

    # Service identification
    service_name: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "genai-app"))
    environment: str = field(default_factory=lambda: os.getenv("GENAI_ENVIRONMENT", "dev"))

    # OTLP Exporter
    otlp_endpoint: str = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    otlp_protocol: str = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    )

    # Sampling & Logging
    log_prompts: bool = field(
        default_factory=lambda: os.getenv("GENAI_OTEL_LOG_PROMPTS", "false").lower() == "true"
    )
    sample_rate: float = field(
        default_factory=lambda: float(os.getenv("GENAI_OTEL_SAMPLE_RATE", "0.01"))
    )

    # PII Redaction
    redact_patterns: List[str] = field(
        default_factory=lambda: os.getenv(
            "GENAI_OTEL_REDACT_PATTERNS", "email,ssn,api_key,credit_card"
        ).split(",")
    )

    # Cost tracking
    tenant_id: Optional[str] = field(
        default_factory=lambda: os.getenv("GENAI_TENANT_ID")
    )
    user_id: Optional[str] = field(
        default_factory=lambda: os.getenv("GENAI_USER_ID")
    )

    # Performance
    max_attribute_length: int = field(
        default_factory=lambda: int(os.getenv("GENAI_MAX_ATTR_LENGTH", "2000"))
    )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError("sample_rate must be between 0.0 and 1.0")
        if self.max_attribute_length < 100:
            raise ValueError("max_attribute_length must be at least 100")


# Global configuration instance
_config: Optional[GenAIConfig] = None


def get_config() -> GenAIConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = GenAIConfig()
    return _config


def set_config(config: GenAIConfig) -> None:
    """Set global configuration instance."""
    global _config
    _config = config
