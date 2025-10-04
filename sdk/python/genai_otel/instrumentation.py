"""Core instrumentation helpers for GenAI operations."""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from genai_otel.config import get_config
from genai_otel.cost import get_cost_calculator
from genai_otel.redaction import redact_sensitive_data

T = TypeVar("T")

tracer = trace.get_tracer(__name__)


def trace_embed(
    model: str,
    provider: str = "openai",
    batch_size: Optional[int] = None,
    dimensions: Optional[int] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to trace embedding generation operations.

    Args:
        model: Model identifier (e.g., "text-embedding-3-small")
        provider: Provider name (e.g., "openai", "cohere")
        batch_size: Number of texts being embedded
        dimensions: Embedding vector dimensions

    Example:
        @trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
        def embed_text(text: str) -> List[float]:
            return openai.embeddings.create(input=text, model="text-embedding-3-small")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            config = get_config()
            with tracer.start_as_current_span(
                "gen_ai.embed",
                attributes={
                    "gen_ai.operation.name": "embed",
                    "gen_ai.request.model": model,
                    "gen_ai.request.provider": provider,
                    "gen_ai.environment": config.environment,
                },
            ) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)

                    # Set optional attributes
                    if batch_size:
                        span.set_attribute("gen_ai.request.batch_size", batch_size)
                    if dimensions:
                        span.set_attribute("gen_ai.response.dimensions", dimensions)

                    # Calculate tokens and cost (estimate for embeddings)
                    # Note: Actual token count should come from API response
                    if hasattr(result, "usage") and result.usage:
                        input_tokens = result.usage.total_tokens
                        span.set_attribute("gen_ai.usage.input_tokens", input_tokens)

                        cost = get_cost_calculator().calculate_cost(
                            provider, model, input_tokens
                        )
                        if cost > 0:
                            span.set_attribute("gen_ai.usage.cost_usd", cost)

                    span.set_attribute("gen_ai.request.duration_ms", int((time.time() - start_time) * 1000))
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:200])
                    raise

        return cast(Callable[..., T], wrapper)

    return decorator


def trace_retrieve(
    source: str,
    top_k: int,
    index_name: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to trace vector/document retrieval operations.

    Args:
        source: Vector store type (e.g., "pinecone", "weaviate", "chroma")
        top_k: Number of results requested
        index_name: Target index/collection name
        filters: Metadata filters applied

    Example:
        @trace_retrieve(source="pinecone", top_k=10, index_name="docs")
        def retrieve_docs(query_vector: List[float]) -> List[Document]:
            return index.query(vector=query_vector, top_k=10)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            config = get_config()
            with tracer.start_as_current_span(
                "gen_ai.retrieve",
                attributes={
                    "gen_ai.operation.name": "retrieve",
                    "gen_ai.retrieval.top_k": top_k,
                    "gen_ai.retrieval.source": source,
                    "gen_ai.environment": config.environment,
                },
            ) as span:
                start_time = time.time()
                try:
                    if index_name:
                        span.set_attribute("gen_ai.retrieval.index_name", index_name)
                    if filters:
                        span.set_attribute("gen_ai.retrieval.filters", str(filters)[:config.max_attribute_length])

                    result = func(*args, **kwargs)

                    # Extract results count
                    results_count = len(result) if hasattr(result, "__len__") else 0
                    span.set_attribute("gen_ai.retrieval.results_count", results_count)

                    # Calculate hit@k proxy (did we get any results?)
                    hit_at_k = 1 if results_count > 0 else 0
                    span.set_attribute("gen_ai.retrieval.hit_at_k", hit_at_k)

                    span.set_attribute("gen_ai.request.duration_ms", int((time.time() - start_time) * 1000))
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:200])
                    raise

        return cast(Callable[..., T], wrapper)

    return decorator


def trace_rerank(
    model: str,
    provider: str = "cohere",
    input_count: Optional[int] = None,
    top_n: Optional[int] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to trace reranking operations.

    Args:
        model: Reranker model (e.g., "cohere-rerank-v3")
        provider: Provider name
        input_count: Number of candidates to rerank
        top_n: Requested top-n results

    Example:
        @trace_rerank(model="rerank-english-v3.0", provider="cohere", top_n=5)
        def rerank_results(query: str, docs: List[str]) -> List[str]:
            return cohere.rerank(query=query, documents=docs, top_n=5)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            config = get_config()
            with tracer.start_as_current_span(
                "gen_ai.rerank",
                attributes={
                    "gen_ai.operation.name": "rerank",
                    "gen_ai.rerank.model": model,
                    "gen_ai.environment": config.environment,
                },
            ) as span:
                start_time = time.time()
                try:
                    if input_count:
                        span.set_attribute("gen_ai.rerank.input_count", input_count)
                    if top_n:
                        span.set_attribute("gen_ai.rerank.top_n", top_n)

                    result = func(*args, **kwargs)

                    # Extract output count
                    output_count = len(result) if hasattr(result, "__len__") else 0
                    span.set_attribute("gen_ai.rerank.output_count", output_count)

                    # Calculate cost if applicable
                    if hasattr(result, "meta") and hasattr(result.meta, "billed_units"):
                        search_units = result.meta.billed_units.search_units
                        # Approximate cost based on search units
                        cost = (search_units / 1000) * 2.0  # $2/1K searches for Cohere
                        span.set_attribute("gen_ai.usage.cost_usd", cost)

                    span.set_attribute("gen_ai.request.duration_ms", int((time.time() - start_time) * 1000))
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:200])
                    raise

        return cast(Callable[..., T], wrapper)

    return decorator


def trace_generate(
    model: str,
    provider: str = "openai",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    streaming: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to trace LLM text generation.

    Args:
        model: Model identifier (e.g., "gpt-4", "claude-3-opus")
        provider: Provider name (e.g., "openai", "anthropic")
        temperature: Sampling temperature
        max_tokens: Max completion length
        streaming: Whether streaming is used

    Example:
        @trace_generate(model="gpt-4", provider="openai", temperature=0.7)
        def generate_response(prompt: str) -> str:
            return openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            config = get_config()
            with tracer.start_as_current_span(
                "gen_ai.generate",
                attributes={
                    "gen_ai.operation.name": "generate",
                    "gen_ai.request.model": model,
                    "gen_ai.request.provider": provider,
                    "gen_ai.environment": config.environment,
                },
            ) as span:
                start_time = time.time()
                try:
                    if temperature is not None:
                        span.set_attribute("gen_ai.request.temperature", temperature)
                    if max_tokens:
                        span.set_attribute("gen_ai.request.max_tokens", max_tokens)
                    if streaming:
                        span.set_attribute("gen_ai.request.streaming", streaming)

                    # Log prompt if configured
                    if config.log_prompts and args:
                        prompt_text = str(args[0])[:config.max_attribute_length]
                        span.set_attribute("gen_ai.prompt", redact_sensitive_data(prompt_text, config))

                    result = func(*args, **kwargs)

                    # Extract token usage
                    if hasattr(result, "usage") and result.usage:
                        input_tokens = result.usage.prompt_tokens
                        output_tokens = result.usage.completion_tokens
                        total_tokens = result.usage.total_tokens

                        span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
                        span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
                        span.set_attribute("gen_ai.usage.total_tokens", total_tokens)

                        # Calculate cost
                        cost = get_cost_calculator().calculate_cost(
                            provider, model, input_tokens, output_tokens
                        )
                        if cost > 0:
                            span.set_attribute("gen_ai.usage.cost_usd", cost)

                    # Extract finish reason
                    if hasattr(result, "choices") and result.choices:
                        finish_reason = result.choices[0].finish_reason
                        span.set_attribute("gen_ai.response.finish_reason", finish_reason)

                    # Log completion if configured
                    if config.log_prompts and hasattr(result, "choices") and result.choices:
                        completion = result.choices[0].message.content[:config.max_attribute_length]
                        span.set_attribute("gen_ai.completion", redact_sensitive_data(completion, config))

                    span.set_attribute("gen_ai.request.duration_ms", int((time.time() - start_time) * 1000))
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:200])
                    raise

        return cast(Callable[..., T], wrapper)

    return decorator


def trace_tool_call(
    tool_name: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to trace agent tool/function invocations.

    Args:
        tool_name: Tool/function name
        parameters: Tool parameters (will be redacted)

    Example:
        @trace_tool_call(tool_name="web_search", parameters={"query": "..."})
        def search_web(query: str) -> Dict[str, Any]:
            return search_api.query(query)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            config = get_config()
            with tracer.start_as_current_span(
                "gen_ai.tool_call",
                attributes={
                    "gen_ai.operation.name": "tool_call",
                    "gen_ai.tool.name": tool_name,
                    "gen_ai.environment": config.environment,
                },
            ) as span:
                start_time = time.time()
                result_status = "success"
                error_type = None

                try:
                    if parameters:
                        params_str = str(parameters)[:config.max_attribute_length]
                        span.set_attribute("gen_ai.tool.parameters", redact_sensitive_data(params_str, config))

                    result = func(*args, **kwargs)

                    # Calculate result size
                    result_str = str(result)
                    result_size = len(result_str.encode("utf-8"))
                    span.set_attribute("gen_ai.tool.result_size_bytes", result_size)

                    span.set_attribute("gen_ai.request.duration_ms", int((time.time() - start_time) * 1000))
                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    result_status = "error"
                    error_type = type(e).__name__
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", error_type)
                    span.set_attribute("error.message", str(e)[:200])
                    raise

                finally:
                    span.set_attribute("gen_ai.tool.result_status", result_status)
                    if error_type:
                        span.set_attribute("gen_ai.tool.error_type", error_type)

        return cast(Callable[..., T], wrapper)

    return decorator
