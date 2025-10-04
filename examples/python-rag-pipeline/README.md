# Python RAG Pipeline Example

This example demonstrates a complete RAG pipeline with GenAI OpenTelemetry instrumentation.

## What It Demonstrates

- ✅ **Embedding** - Query embedding with token/cost tracking
- ✅ **Retrieval** - Vector search with hit@k metrics
- ✅ **Reranking** - Result reranking with performance tracking
- ✅ **Generation** - LLM completion with full token usage
- ✅ **Tool Calls** - External tool invocation (web search)

## Architecture

```
User Question
    ↓
[embed] → Query Embedding (1536d vector)
    ↓
[retrieve] → Vector Search (top-k=10)
    ↓
[rerank] → Rerank Results (top-n=2)
    ↓
[tool_call] → Web Search (optional context)
    ↓
[generate] → LLM Answer Generation
    ↓
Final Answer
```

## Setup

1. **Start Observability Stack**

```bash
cd ../../deploy/docker
docker-compose up -d
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Run Example**

```bash
python app.py
```

## What Gets Traced

Each operation creates a span with:

### Embed Span
- `gen_ai.operation.name`: "embed"
- `gen_ai.request.model`: "text-embedding-3-small"
- `gen_ai.usage.input_tokens`: 8
- `gen_ai.usage.cost_usd`: 0.00000016
- `gen_ai.response.dimensions`: 1536

### Retrieve Span
- `gen_ai.operation.name`: "retrieve"
- `gen_ai.retrieval.source`: "pinecone"
- `gen_ai.retrieval.top_k`: 10
- `gen_ai.retrieval.results_count`: 3
- `gen_ai.retrieval.hit_at_k`: 1

### Rerank Span
- `gen_ai.operation.name`: "rerank"
- `gen_ai.rerank.model`: "rerank-english-v3.0"
- `gen_ai.rerank.input_count`: 3
- `gen_ai.rerank.output_count`: 2

### Generate Span
- `gen_ai.operation.name`: "generate"
- `gen_ai.request.model`: "gpt-4"
- `gen_ai.usage.input_tokens`: 150
- `gen_ai.usage.output_tokens`: 45
- `gen_ai.usage.total_tokens`: 195
- `gen_ai.usage.cost_usd`: 0.0072

### Tool Call Span
- `gen_ai.operation.name`: "tool_call"
- `gen_ai.tool.name`: "web_search"
- `gen_ai.tool.result_status`: "success"
- `gen_ai.tool.result_size_bytes`: 256

## View Results

1. **Jaeger UI**: http://localhost:16686
   - See distributed traces with linked spans
   - Visualize end-to-end latency

2. **Grafana**: http://localhost:3000
   - RAG Overview dashboard
   - Cost tracking dashboard
   - Error analysis

3. **Prometheus**: http://localhost:9090
   - Query metrics: `gen_ai_requests_total`
   - Token usage: `gen_ai_tokens_total`
   - Cost tracking: `gen_ai_cost_usd_total`

## Sample Output

```
============================================================
❓ Question: What is RAG and how does it work?
============================================================

📊 Embedding query: What is RAG and how does it work?...
🔍 Retrieving documents from vector store...
   Found 3 documents

🎯 Reranking results for relevance...
   Reranked to top 2 documents

🌐 Searching web for: What is RAG and how does it work?
   Found 2 web results

💬 Generating answer with LLM...

============================================================
✅ Answer: RAG (Retrieval-Augmented Generation) is a technique
that combines document retrieval with language model generation
to produce more accurate and contextual responses...
============================================================
```

## Extending This Example

### Add Real API Calls

Replace mock responses with actual API calls:

```python
import openai

@trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
def embed_query(self, text: str):
    return openai.embeddings.create(input=text, model="text-embedding-3-small")
```

### Add Error Handling

```python
@trace_generate(model="gpt-4", provider="openai")
def generate_answer(self, prompt: str):
    try:
        return openai.chat.completions.create(...)
    except openai.RateLimitError as e:
        # Error automatically tracked in span
        raise
```

### Add Multi-Tenancy

```python
from genai_otel import GenAIConfig, set_config

config = GenAIConfig(
    tenant_id="customer-123",
    user_id="user-456"
)
set_config(config)
```
