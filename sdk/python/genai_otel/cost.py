"""Cost calculation for various LLM providers and models."""

from typing import Dict, Optional


# Pricing per 1M tokens (USD) - as of Jan 2025
PRICING_TABLE: Dict[str, Dict[str, Dict[str, float]]] = {
    "openai": {
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "text-embedding-3-small": {"input": 0.02, "output": 0.0},
        "text-embedding-3-large": {"input": 0.13, "output": 0.0},
        "text-embedding-ada-002": {"input": 0.10, "output": 0.0},
    },
    "anthropic": {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    },
    "cohere": {
        "command-r-plus": {"input": 3.0, "output": 15.0},
        "command-r": {"input": 0.5, "output": 1.5},
        "embed-english-v3.0": {"input": 0.10, "output": 0.0},
        "rerank-english-v3.0": {"input": 2.0, "output": 0.0},
    },
    "together": {
        "meta-llama/Llama-3-70b": {"input": 0.9, "output": 0.9},
        "meta-llama/Llama-3-8b": {"input": 0.2, "output": 0.2},
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.6, "output": 0.6},
    },
}


class CostCalculator:
    """Calculate costs for LLM operations."""

    def __init__(self, custom_pricing: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None):
        """
        Initialize cost calculator.

        Args:
            custom_pricing: Optional custom pricing table to override defaults
        """
        self.pricing = PRICING_TABLE.copy()
        if custom_pricing:
            self.pricing.update(custom_pricing)

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
    ) -> float:
        """
        Calculate cost for a request.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (0 for embedding models)

        Returns:
            Cost in USD, or 0.0 if pricing unknown
        """
        provider_lower = provider.lower()

        # Normalize model name
        model_normalized = self._normalize_model_name(model)

        if provider_lower not in self.pricing:
            return 0.0

        model_pricing = self.pricing[provider_lower].get(model_normalized)
        if not model_pricing:
            # Try partial match for versioned models
            for known_model, pricing in self.pricing[provider_lower].items():
                if known_model in model_normalized or model_normalized in known_model:
                    model_pricing = pricing
                    break

        if not model_pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * model_pricing.get("input", 0.0)
        output_cost = (output_tokens / 1_000_000) * model_pricing.get("output", 0.0)

        return round(input_cost + output_cost, 8)

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        """Normalize model name for lookup."""
        return model.strip().lower()

    def add_custom_pricing(
        self,
        provider: str,
        model: str,
        input_price_per_1m: float,
        output_price_per_1m: float = 0.0,
    ) -> None:
        """
        Add custom pricing for a model.

        Args:
            provider: Provider name
            model: Model identifier
            input_price_per_1m: Input price per 1M tokens in USD
            output_price_per_1m: Output price per 1M tokens in USD
        """
        provider_lower = provider.lower()
        if provider_lower not in self.pricing:
            self.pricing[provider_lower] = {}

        self.pricing[provider_lower][model] = {
            "input": input_price_per_1m,
            "output": output_price_per_1m,
        }


# Global cost calculator instance
_calculator: Optional[CostCalculator] = None


def get_cost_calculator() -> CostCalculator:
    """Get or create global cost calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = CostCalculator()
    return _calculator
