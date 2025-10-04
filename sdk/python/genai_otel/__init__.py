"""
GenAI OpenTelemetry SDK

Provides standardized tracing, metrics, and logging for LLM/RAG systems.
"""

from genai_otel.instrumentation import (
    trace_embed,
    trace_retrieve,
    trace_rerank,
    trace_generate,
    trace_tool_call,
)
from genai_otel.config import GenAIConfig
from genai_otel.cost import CostCalculator

__version__ = "0.1.0"

__all__ = [
    "trace_embed",
    "trace_retrieve",
    "trace_rerank",
    "trace_generate",
    "trace_tool_call",
    "GenAIConfig",
    "CostCalculator",
]
