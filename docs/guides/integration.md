# Integration Guide

Complete guide for integrating GenAI observability into your LLM/RAG applications.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [SDK Integration](#sdk-integration)
3. [Provider-Specific Guides](#provider-specific-guides)
4. [Advanced Configuration](#advanced-configuration)
5. [Best Practices](#best-practices)

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Your GenAI Application                 │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Embed  │→ │ Retrieve │→ │ Generate/Rerank  │  │
│  └─────────┘  └──────────┘  └──────────────────┘  │
│       ↓              ↓                  ↓          │
│  ┌─────────────────────────────────────────────┐  │
│  │         GenAI OpenTelemetry SDK             │  │
│  │  • Automatic instrumentation                 │  │
│  │  • Cost calculation                          │  │
│  │  • PII redaction                             │  │
│  └─────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────┘
                           │ OTLP (gRPC/HTTP)
                           ↓
              ┌────────────────────────┐
              │  OTel Collector        │
              │  • Batching            │
              │  • Sampling            │
              │  • Enrichment          │
              └────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                   ↓
   ┌─────────┐      ┌──────────┐       ┌──────────┐
   │ Tempo   │      │Prometheus│       │   Loki   │
   │ (Traces)│      │(Metrics) │       │  (Logs)  │
   └─────────┘      └──────────┘       └──────────┘
        └──────────────────┬──────────────────┘
                           ↓
                    ┌─────────────┐
                    │   Grafana   │
                    │ (Dashboards)│
                    └─────────────┘
```

## SDK Integration

### Python

#### Basic Setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from genai_otel import (
    trace_embed,
    trace_retrieve,
    trace_generate,
    GenAIConfig,
    set_config
)

# Configure GenAI settings
config = GenAIConfig(
    service_name="my-rag-service",
    environment="production",
    tenant_id="customer-123",
    log_prompts=False,
    sample_rate=0.1,
    redact_patterns=["email", "ssn", "api_key"]
)
set_config(config)

# Initialize OpenTelemetry
resource = Resource.create({
    "service.name": config.service_name,
    "service.version": "1.0.0",
    "deployment.environment": config.environment
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://otel-collector:4317"),
    max_queue_size=2048,
    max_export_batch_size=512
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

#### Decorator Usage

```python
import openai
from typing import List

class RAGService:
    @trace_embed(
        model="text-embedding-3-small",
        provider="openai",
        dimensions=1536
    )
    def embed_query(self, text: str):
        """Generate embedding for query"""
        return openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )

    @trace_retrieve(
        source="pinecone",
        top_k=10,
        index_name="knowledge-base",
        filters={"category": "docs"}
    )
    def retrieve_documents(self, vector: List[float]):
        """Retrieve relevant documents"""
        return self.index.query(
            vector=vector,
            top_k=10,
            filter={"category": {"$eq": "docs"}}
        )

    @trace_rerank(
        model="rerank-english-v3.0",
        provider="cohere",
        top_n=5
    )
    def rerank_results(self, query: str, docs: List[str]):
        """Rerank documents for relevance"""
        return cohere.rerank(
            query=query,
            documents=docs,
            top_n=5,
            model="rerank-english-v3.0"
        )

    @trace_generate(
        model="gpt-4-turbo",
        provider="openai",
        temperature=0.7,
        max_tokens=500
    )
    def generate_answer(self, prompt: str):
        """Generate answer using LLM"""
        return openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

    @trace_tool_call(
        tool_name="web_search",
        parameters={"max_results": 5}
    )
    def search_web(self, query: str):
        """Search web for additional context"""
        return self.search_api.query(query, max_results=5)
```

### Node.js/TypeScript

#### Basic Setup

```typescript
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

import {
  traceEmbed,
  traceRetrieve,
  traceGenerate,
  setConfig
} from '@genai-obs/otel';

// Configure GenAI settings
setConfig({
  serviceName: 'my-rag-service',
  environment: 'production',
  tenantId: 'customer-123',
  logPrompts: false,
  sampleRate: 0.1,
  redactPatterns: ['email', 'ssn', 'api_key']
});

// Initialize OpenTelemetry
const resource = Resource.default().merge(
  new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'my-rag-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'production'
  })
);

const provider = new NodeTracerProvider({ resource });
const exporter = new OTLPTraceExporter({
  url: 'http://otel-collector:4317'
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();
```

#### Decorator Usage

```typescript
import OpenAI from 'openai';

class RAGService {
  private openai = new OpenAI();

  @traceEmbed({
    model: 'text-embedding-3-small',
    provider: 'openai',
    dimensions: 1536
  })
  async embedQuery(text: string) {
    return await this.openai.embeddings.create({
      input: text,
      model: 'text-embedding-3-small'
    });
  }

  @traceRetrieve({
    source: 'pinecone',
    topK: 10,
    indexName: 'knowledge-base'
  })
  async retrieveDocuments(vector: number[]) {
    return await this.index.query({
      vector,
      topK: 10
    });
  }

  @traceGenerate({
    model: 'gpt-4-turbo',
    provider: 'openai',
    temperature: 0.7,
    maxTokens: 500
  })
  async generateAnswer(prompt: string) {
    return await this.openai.chat.completions.create({
      model: 'gpt-4-turbo',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 500
    });
  }
}
```

## Provider-Specific Guides

### OpenAI

```python
from genai_otel import trace_embed, trace_generate

@trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
def embed(text: str):
    return openai.embeddings.create(input=text, model="text-embedding-3-small")

@trace_generate(model="gpt-4", provider="openai", temperature=0.7)
def generate(prompt: str):
    return openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
```

### Anthropic (Claude)

```python
from genai_otel import trace_generate

@trace_generate(model="claude-3-opus-20240229", provider="anthropic", max_tokens=1000)
def generate_claude(prompt: str):
    return anthropic.messages.create(
        model="claude-3-opus-20240229",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
```

### Cohere

```python
from genai_otel import trace_embed, trace_rerank

@trace_embed(model="embed-english-v3.0", provider="cohere")
def embed_cohere(texts: List[str]):
    return cohere.embed(texts=texts, model="embed-english-v3.0")

@trace_rerank(model="rerank-english-v3.0", provider="cohere", top_n=5)
def rerank_cohere(query: str, docs: List[str]):
    return cohere.rerank(query=query, documents=docs, top_n=5)
```

### Pinecone

```python
from genai_otel import trace_retrieve

@trace_retrieve(source="pinecone", top_k=10, index_name="my-index")
def search_pinecone(vector: List[float]):
    return index.query(vector=vector, top_k=10, include_metadata=True)
```

### Weaviate

```python
from genai_otel import trace_retrieve

@trace_retrieve(source="weaviate", top_k=10, index_name="Document")
def search_weaviate(vector: List[float]):
    return client.query.get("Document", ["text", "title"]) \
        .with_near_vector({"vector": vector}) \
        .with_limit(10) \
        .do()
```

## Advanced Configuration

### Multi-Tenancy

```python
from genai_otel import GenAIConfig, set_config
from contextvars import ContextVar

# Context variable for tenant
current_tenant = ContextVar('current_tenant', default='default')

def set_tenant_context(tenant_id: str, user_id: str):
    """Set tenant context for all subsequent operations"""
    config = GenAIConfig(
        tenant_id=tenant_id,
        user_id=user_id
    )
    set_config(config)
    current_tenant.set(tenant_id)

# In your request handler
@app.route('/api/query')
def handle_query():
    tenant_id = request.headers.get('X-Tenant-ID')
    user_id = request.headers.get('X-User-ID')

    set_tenant_context(tenant_id, user_id)

    # All spans now include tenant_id and user_id
    result = rag_pipeline.run(request.json['query'])
    return jsonify(result)
```

### Custom Cost Pricing

```python
from genai_otel import CostCalculator, get_cost_calculator

# Add custom model pricing
calc = get_cost_calculator()
calc.add_custom_pricing(
    provider="custom",
    model="my-fine-tuned-gpt4",
    input_price_per_1m=50.0,
    output_price_per_1m=150.0
)
```

### Custom Redaction Patterns

```python
from genai_otel.redaction import add_redaction_pattern
import re

# Add custom PII pattern
add_redaction_pattern(
    name="employee_id",
    pattern=r"EMP-\d{6}",
    replacement="[EMPLOYEE_ID_REDACTED]"
)

add_redaction_pattern(
    name="internal_ip",
    pattern=r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    replacement="[INTERNAL_IP_REDACTED]"
)
```

### Sampling Strategies

```python
from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased,
    ParentBased,
    ALWAYS_ON,
    ALWAYS_OFF
)

# Sample based on trace attributes
class CustomSampler(Sampler):
    def should_sample(self, parent_context, trace_id, name, attributes=None, ...):
        # Always sample errors
        if attributes and attributes.get("error"):
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        # Always sample high-cost operations
        if attributes and attributes.get("gen_ai.usage.cost_usd", 0) > 1.0:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        # Sample 10% of normal traffic
        return TraceIdRatioBased(0.1).should_sample(...)

provider = TracerProvider(sampler=CustomSampler())
```

## Best Practices

### 1. Error Handling

```python
from opentelemetry import trace

@trace_generate(model="gpt-4", provider="openai")
def generate_with_retry(prompt: str, max_retries=3):
    span = trace.get_current_span()

    for attempt in range(max_retries):
        try:
            return openai.chat.completions.create(...)
        except openai.RateLimitError as e:
            span.add_event(f"Rate limit hit, retry {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
        except Exception as e:
            span.record_exception(e)
            raise
```

### 2. Batch Processing

```python
@trace_embed(model="text-embedding-3-small", provider="openai", batch_size=100)
def embed_batch(texts: List[str]):
    """Process embeddings in batches for efficiency"""
    return openai.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
@trace_retrieve(source="cache", top_k=10)
def cached_search(query_hash: str, vector_str: str):
    """Cache retrieval results"""
    vector = json.loads(vector_str)
    return index.query(vector=vector, top_k=10)
```

### 4. Cost Optimization

```python
# Use cheaper models for simple tasks
@trace_generate(model="gpt-3.5-turbo", provider="openai")
def classify_intent(query: str):
    """Use cheaper model for classification"""
    return openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Classify: {query}"}]
    )

# Use expensive models only when needed
@trace_generate(model="gpt-4", provider="openai")
def generate_complex_answer(prompt: str):
    """Use expensive model for complex generation"""
    return openai.chat.completions.create(...)
```

### 5. Security

```python
# Disable prompt logging in production
config = GenAIConfig(
    log_prompts=False,  # Never log prompts with PII
    redact_patterns=["email", "ssn", "api_key", "phone", "credit_card"],
    sample_rate=0.05  # Low sampling for production
)
set_config(config)
```

## Next Steps

- [Quickstart Guide](quickstart.md) - Get started in 15 minutes
- [Semantic Conventions](../semantic-conventions.md) - Understand span attributes
- [Alerting](../../alerting/README.md) - Configure alerts
- [Dashboards](../../dashboards/) - Customize visualizations
