# GenAI OpenTelemetry SDK - Python

Drop-in OpenTelemetry instrumentation for GenAI/LLM/RAG systems with standardized semantics for prompts, tokens, costs, and retrieval performance.

## Features

- 🎯 **Zero-overhead instrumentation** - Simple decorators for embed, retrieve, rerank, generate, tool_call
- 💰 **Automatic cost tracking** - Built-in pricing for OpenAI, Anthropic, Cohere, Together AI
- 🔒 **PII redaction** - Automatic masking of emails, API keys, SSNs, credit cards
- 📊 **Rich metrics** - Token usage, latency, hit@k, error rates
- 🔗 **Distributed tracing** - Linked spans across entire RAG pipeline

## Installation

```bash
pip install genai-otel
```

## Quick Start

### 1. Initialize OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up tracer provider
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

### 2. Instrument Your Code

```python
from genai_otel import trace_embed, trace_retrieve, trace_generate
import openai

@trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
def embed_query(text: str):
    return openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

@trace_retrieve(source="pinecone", top_k=10, index_name="docs")
def retrieve_docs(query_vector):
    return index.query(vector=query_vector, top_k=10)

@trace_generate(model="gpt-4", provider="openai", temperature=0.7)
def generate_answer(prompt: str):
    return openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

# Use in your RAG pipeline
def rag_pipeline(question: str):
    # Each operation automatically creates linked spans
    embedding = embed_query(question)
    docs = retrieve_docs(embedding.data[0].embedding)
    context = "\n".join([d.text for d in docs])
    answer = generate_answer(f"Context: {context}\n\nQuestion: {question}")
    return answer
```

### 3. View Traces

Traces are exported to your configured OTLP endpoint with:
- **Span links** connecting embed → retrieve → generate
- **Token usage** and **cost** automatically calculated
- **Latency metrics** for each operation
- **Error tracking** with sanitized messages

## Configuration

Set via environment variables:

```bash
# OpenTelemetry
export OTEL_SERVICE_NAME="my-rag-app"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export GENAI_ENVIRONMENT="production"

# Logging & Sampling
export GENAI_OTEL_LOG_PROMPTS="false"          # Don't log prompts by default
export GENAI_OTEL_SAMPLE_RATE="0.01"           # Sample 1% of requests

# PII Redaction
export GENAI_OTEL_REDACT_PATTERNS="email,ssn,api_key,credit_card"

# Multi-tenancy
export GENAI_TENANT_ID="customer-123"
export GENAI_USER_ID="user-456"
```

Or configure programmatically:

```python
from genai_otel import GenAIConfig, set_config

config = GenAIConfig(
    service_name="my-app",
    environment="prod",
    log_prompts=False,
    sample_rate=0.01,
    redact_patterns=["email", "ssn", "api_key"]
)
set_config(config)
```

## Span Types

### Embedding (`trace_embed`)

```python
@trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
def embed(text: str):
    ...
```

Captures: model, provider, tokens, cost, dimensions

### Retrieval (`trace_retrieve`)

```python
@trace_retrieve(source="pinecone", top_k=10, index_name="docs")
def retrieve(vector):
    ...
```

Captures: source, top_k, results_count, hit@k, filters, cache_hit

### Reranking (`trace_rerank`)

```python
@trace_rerank(model="rerank-english-v3.0", provider="cohere", top_n=5)
def rerank(query: str, docs: list):
    ...
```

Captures: model, input_count, output_count, cost, score_delta

### Generation (`trace_generate`)

```python
@trace_generate(model="gpt-4", provider="openai", temperature=0.7, max_tokens=500)
def generate(prompt: str):
    ...
```

Captures: model, provider, input/output tokens, cost, temperature, finish_reason

### Tool Calls (`trace_tool_call`)

```python
@trace_tool_call(tool_name="web_search", parameters={"query": "..."})
def search_web(query: str):
    ...
```

Captures: tool_name, parameters (redacted), result_status, error_type

## Cost Tracking

Built-in pricing for major providers (as of Jan 2025):

```python
from genai_otel import CostCalculator

calc = CostCalculator()

# Automatic cost calculation
cost = calc.calculate_cost(
    provider="openai",
    model="gpt-4-turbo",
    input_tokens=1000,
    output_tokens=500
)
# Returns: 0.025 (USD)

# Add custom pricing
calc.add_custom_pricing(
    provider="custom",
    model="my-model",
    input_price_per_1m=10.0,
    output_price_per_1m=30.0
)
```

## PII Redaction

Automatic redaction of sensitive data in logs:

```python
from genai_otel.redaction import redact_sensitive_data
from genai_otel import get_config

text = "Contact john@example.com or call 555-123-4567"
redacted = redact_sensitive_data(text, get_config())
# Returns: "Contact [EMAIL_REDACTED] or call [PHONE_REDACTED]"
```

Supported patterns:
- Email addresses
- SSNs
- API keys
- Credit cards
- Phone numbers
- IP addresses
- Bearer tokens
- AWS keys
- GitHub tokens

## Metrics

All spans emit metrics to Prometheus:

- `gen_ai.requests.total{operation, model, provider, status}`
- `gen_ai.tokens.total{operation, model, token_type}`
- `gen_ai.cost.usd.total{model, provider, tenant_id}`
- `gen_ai.request.duration{operation}` (histogram)
- `gen_ai.retrieval.hit_at_k{source}` (gauge)

## Advanced Usage

### Multi-tenant Cost Tracking

```python
from genai_otel import GenAIConfig, set_config

# Set tenant context
config = GenAIConfig(tenant_id="customer-123", user_id="user-456")
set_config(config)

# All spans now include tenant_id and user_id for cost attribution
```

### Custom Span Attributes

```python
from opentelemetry import trace

@trace_generate(model="gpt-4", provider="openai")
def generate(prompt: str):
    span = trace.get_current_span()
    span.set_attribute("custom.workflow", "customer_support")
    span.set_attribute("custom.priority", "high")
    # ... rest of implementation
```

### Error Handling

```python
@trace_generate(model="gpt-4", provider="openai")
def generate_with_retry(prompt: str):
    try:
        return openai.chat.completions.create(...)
    except openai.RateLimitError as e:
        # Error automatically tracked with error.type="RateLimitError"
        raise
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black genai_otel/
ruff check genai_otel/

# Type check
mypy genai_otel/
```

## License

Apache 2.0
