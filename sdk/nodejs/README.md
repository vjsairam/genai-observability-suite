# GenAI OpenTelemetry SDK - Node.js

Drop-in OpenTelemetry instrumentation for GenAI/LLM/RAG systems with standardized semantics for prompts, tokens, costs, and retrieval performance.

## Features

- 🎯 **Zero-overhead instrumentation** - TypeScript decorators for embed, retrieve, rerank, generate, tool_call
- 💰 **Automatic cost tracking** - Built-in pricing for OpenAI, Anthropic, Cohere, Together AI
- 🔒 **PII redaction** - Automatic masking of emails, API keys, SSNs, credit cards
- 📊 **Rich metrics** - Token usage, latency, hit@k, error rates
- 🔗 **Distributed tracing** - Linked spans across entire RAG pipeline

## Installation

```bash
npm install @genai-obs/otel
# or
yarn add @genai-obs/otel
```

## Quick Start

### 1. Initialize OpenTelemetry

```typescript
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';

const provider = new NodeTracerProvider();
const exporter = new OTLPTraceExporter({ url: 'http://localhost:4317' });
provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();
```

### 2. Instrument Your Code

```typescript
import { traceEmbed, traceRetrieve, traceGenerate } from '@genai-obs/otel';
import OpenAI from 'openai';

const openai = new OpenAI();

class RAGService {
  @traceEmbed({ model: 'text-embedding-3-small', provider: 'openai', dimensions: 1536 })
  async embedQuery(text: string) {
    return await openai.embeddings.create({
      input: text,
      model: 'text-embedding-3-small',
    });
  }

  @traceRetrieve({ source: 'pinecone', topK: 10, indexName: 'docs' })
  async retrieveDocs(queryVector: number[]) {
    return await index.query({ vector: queryVector, topK: 10 });
  }

  @traceGenerate({ model: 'gpt-4', provider: 'openai', temperature: 0.7 })
  async generateAnswer(prompt: string) {
    return await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }],
    });
  }

  async ragPipeline(question: string) {
    // Each operation automatically creates linked spans
    const embedding = await this.embedQuery(question);
    const docs = await this.retrieveDocs(embedding.data[0].embedding);
    const context = docs.map((d) => d.text).join('\n');
    const answer = await this.generateAnswer(`Context: ${context}\n\nQuestion: ${question}`);
    return answer;
  }
}
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

```typescript
import { setConfig } from '@genai-obs/otel';

setConfig({
  serviceName: 'my-app',
  environment: 'prod',
  logPrompts: false,
  sampleRate: 0.01,
  redactPatterns: ['email', 'ssn', 'api_key'],
});
```

## Decorator Options

### Embedding (`@traceEmbed`)

```typescript
@traceEmbed({
  model: 'text-embedding-3-small',
  provider: 'openai',
  dimensions: 1536
})
async embed(text: string) { ... }
```

### Retrieval (`@traceRetrieve`)

```typescript
@traceRetrieve({
  source: 'pinecone',
  topK: 10,
  indexName: 'docs'
})
async retrieve(vector: number[]) { ... }
```

### Reranking (`@traceRerank`)

```typescript
@traceRerank({
  model: 'rerank-english-v3.0',
  provider: 'cohere',
  topN: 5
})
async rerank(query: string, docs: string[]) { ... }
```

### Generation (`@traceGenerate`)

```typescript
@traceGenerate({
  model: 'gpt-4',
  provider: 'openai',
  temperature: 0.7,
  maxTokens: 500
})
async generate(prompt: string) { ... }
```

### Tool Calls (`@traceToolCall`)

```typescript
@traceToolCall({
  toolName: 'web_search',
  parameters: { query: '...' }
})
async searchWeb(query: string) { ... }
```

## Cost Tracking

Built-in pricing for major providers (as of Jan 2025):

```typescript
import { CostCalculator } from '@genai-obs/otel';

const calc = new CostCalculator();

// Automatic cost calculation
const cost = calc.calculateCost('openai', 'gpt-4-turbo', 1000, 500);
// Returns: 0.025 (USD)

// Add custom pricing
calc.addCustomPricing('custom', 'my-model', 10.0, 30.0);
```

## PII Redaction

Automatic redaction of sensitive data:

```typescript
import { redactSensitiveData, getConfig } from '@genai-obs/otel';

const text = 'Contact john@example.com or call 555-123-4567';
const redacted = redactSensitiveData(text, getConfig());
// Returns: "Contact [EMAIL_REDACTED] or call [PHONE_REDACTED]"
```

## TypeScript Support

Full TypeScript support with type definitions included.

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Test
npm test

# Lint & Format
npm run lint
npm run format
```

## License

Apache 2.0
