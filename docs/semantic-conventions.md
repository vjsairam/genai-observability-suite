# GenAI OpenTelemetry Semantic Conventions

This document defines the standardized OpenTelemetry attributes for GenAI/LLM/RAG observability.

## Span Types

### 1. `gen_ai.embed`
**Purpose**: Track embedding generation operations

**Required Attributes**:
- `gen_ai.operation.name` (string): Operation name, e.g., "embed"
- `gen_ai.request.model` (string): Model identifier (e.g., "text-embedding-3-small")
- `gen_ai.request.provider` (string): Provider name (e.g., "openai", "cohere", "huggingface")
- `gen_ai.usage.input_tokens` (int): Number of input tokens
- `gen_ai.response.dimensions` (int): Embedding vector dimensions

**Optional Attributes**:
- `gen_ai.request.batch_size` (int): Number of texts embedded in batch
- `gen_ai.usage.cost_usd` (double): Estimated cost in USD
- `gen_ai.request.encoding_format` (string): e.g., "float", "base64"

### 2. `gen_ai.retrieve`
**Purpose**: Track vector/document retrieval operations

**Required Attributes**:
- `gen_ai.operation.name` (string): "retrieve"
- `gen_ai.retrieval.top_k` (int): Number of results requested
- `gen_ai.retrieval.results_count` (int): Actual results returned
- `gen_ai.retrieval.source` (string): Vector store type (e.g., "pinecone", "weaviate", "chroma")

**Optional Attributes**:
- `gen_ai.retrieval.filters` (string): Applied metadata filters (JSON)
- `gen_ai.retrieval.similarity_metric` (string): e.g., "cosine", "euclidean"
- `gen_ai.retrieval.min_score` (double): Minimum similarity threshold
- `gen_ai.retrieval.cache_hit` (boolean): Whether cache was used
- `gen_ai.retrieval.index_name` (string): Target index/collection

### 3. `gen_ai.rerank`
**Purpose**: Track reranking operations that reorder retrieved results

**Required Attributes**:
- `gen_ai.operation.name` (string): "rerank"
- `gen_ai.rerank.model` (string): Reranker model (e.g., "cohere-rerank-v3")
- `gen_ai.rerank.input_count` (int): Number of candidates to rerank
- `gen_ai.rerank.output_count` (int): Number of results after reranking

**Optional Attributes**:
- `gen_ai.rerank.top_n` (int): Requested top-n results
- `gen_ai.usage.cost_usd` (double): Reranking cost
- `gen_ai.rerank.score_delta` (double): Average score improvement

### 4. `gen_ai.generate`
**Purpose**: Track LLM text generation (completion/chat)

**Required Attributes**:
- `gen_ai.operation.name` (string): "generate" or "chat.completion"
- `gen_ai.request.model` (string): Model identifier (e.g., "gpt-4", "claude-3-opus")
- `gen_ai.request.provider` (string): Provider (e.g., "openai", "anthropic", "together")
- `gen_ai.usage.input_tokens` (int): Prompt tokens
- `gen_ai.usage.output_tokens` (int): Completion tokens
- `gen_ai.usage.total_tokens` (int): Total tokens

**Optional Attributes**:
- `gen_ai.request.temperature` (double): Sampling temperature
- `gen_ai.request.max_tokens` (int): Max completion length
- `gen_ai.request.top_p` (double): Nucleus sampling parameter
- `gen_ai.usage.cost_usd` (double): Estimated cost
- `gen_ai.response.finish_reason` (string): e.g., "stop", "length", "tool_calls"
- `gen_ai.request.streaming` (boolean): Whether streaming was used
- `gen_ai.cache.read_tokens` (int): Cached/reused tokens (prompt caching)
- `gen_ai.system_fingerprint` (string): Model version fingerprint

### 5. `gen_ai.tool_call`
**Purpose**: Track agent tool/function invocations

**Required Attributes**:
- `gen_ai.operation.name` (string): "tool_call"
- `gen_ai.tool.name` (string): Tool/function name
- `gen_ai.tool.result_status` (string): "success", "error", "timeout"

**Optional Attributes**:
- `gen_ai.tool.parameters` (string): JSON-encoded parameters (redacted)
- `gen_ai.tool.result_size_bytes` (int): Size of tool result
- `gen_ai.tool.error_type` (string): Error classification if failed

## Common Cross-Cutting Attributes

**All spans SHOULD include**:
- `gen_ai.tenant_id` (string): For multi-tenant cost/usage tracking
- `gen_ai.request_id` (string): End-to-end request correlation ID
- `gen_ai.user_id` (string): User identifier (hashed if PII-sensitive)
- `gen_ai.environment` (string): "prod", "staging", "dev"

**Error Tracking**:
- `error` (boolean): True if operation failed
- `error.type` (string): Error class (e.g., "RateLimitError", "APIError")
- `error.message` (string): Sanitized error message

## Metrics

### Counters
- `gen_ai.requests.total` - Total requests by {operation, model, provider, status}
- `gen_ai.tokens.total` - Total tokens by {operation, model, token_type=input|output}
- `gen_ai.cost.usd.total` - Total cost by {model, provider, tenant_id}

### Histograms
- `gen_ai.request.duration` - Request latency in milliseconds
- `gen_ai.tokens.per_request` - Token distribution per request
- `gen_ai.retrieval.results.count` - Retrieved document count distribution

### Gauges
- `gen_ai.cost.burn_rate` - Cost spend rate ($/hour) by model
- `gen_ai.retrieval.hit_at_k` - Hit@K proxy metric

## Log Sampling & Redaction

**Default Behavior**:
- Prompts/completions: NOT logged by default (only metadata)
- Sampling: 1% of requests log full payload
- Redaction: Mask API keys, emails, SSNs, credit cards

**Override via**:
- `GENAI_OTEL_LOG_PROMPTS=true` - Enable full prompt logging
- `GENAI_OTEL_SAMPLE_RATE=0.05` - Sample 5% of requests
- `GENAI_OTEL_REDACT_PATTERNS=email,ssn,api_key` - Redaction rules
