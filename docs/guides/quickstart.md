# GenAI Observability - Quickstart Guide

Get full observability for your GenAI/LLM application in 15 minutes.

## Prerequisites

- Docker & Docker Compose (for local)
- OR Kubernetes cluster (for production)
- Python 3.9+ or Node.js 16+ (for SDK)

## Option 1: Local Development (Docker Compose)

### 1. Start Observability Stack

```bash
git clone https://github.com/genai-obs/genai-observability-suite
cd genai-observability-suite/deploy/docker
docker-compose up -d
```

**Verify services:**
```bash
docker-compose ps

# Should show:
# - otel-collector (running)
# - prometheus (running)
# - grafana (running)
# - tempo/jaeger (running)
# - loki (running)
```

### 2. Install SDK

**Python:**
```bash
pip install genai-otel
```

**Node.js:**
```bash
npm install @genai-obs/otel
```

### 3. Instrument Your Code

**Python Example:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from genai_otel import trace_embed, trace_retrieve, trace_generate

# Initialize OpenTelemetry
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
)
trace.set_tracer_provider(provider)

# Instrument your functions
@trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
def embed_text(text: str):
    return openai.embeddings.create(input=text, model="text-embedding-3-small")

@trace_retrieve(source="pinecone", top_k=10, index_name="docs")
def search_docs(vector):
    return index.query(vector=vector, top_k=10)

@trace_generate(model="gpt-4", provider="openai", temperature=0.7)
def generate_answer(prompt: str):
    return openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

# Use in your RAG pipeline
def rag_pipeline(question: str):
    embedding = embed_text(question)
    docs = search_docs(embedding.data[0].embedding)
    context = "\n".join([d.text for d in docs])
    answer = generate_answer(f"Context: {context}\n\nQ: {question}")
    return answer
```

**Node.js Example:**

```typescript
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { traceEmbed, traceRetrieve, traceGenerate } from '@genai-obs/otel';

const provider = new NodeTracerProvider();
provider.addSpanProcessor(
  new BatchSpanProcessor(new OTLPTraceExporter({ url: 'http://localhost:4317' }))
);
provider.register();

class RAGService {
  @traceEmbed({ model: 'text-embedding-3-small', provider: 'openai', dimensions: 1536 })
  async embedText(text: string) {
    return await openai.embeddings.create({ input: text, model: 'text-embedding-3-small' });
  }

  @traceRetrieve({ source: 'pinecone', topK: 10, indexName: 'docs' })
  async searchDocs(vector: number[]) {
    return await index.query({ vector, topK: 10 });
  }

  @traceGenerate({ model: 'gpt-4', provider: 'openai', temperature: 0.7 })
  async generateAnswer(prompt: string) {
    return await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: prompt }]
    });
  }
}
```

### 4. View Observability

**Grafana Dashboards:**
1. Open http://localhost:3000 (admin/admin)
2. Navigate to "Dashboards" → "GenAI Observability"
3. View pre-built dashboards:
   - **RAG Overview** - Request rates, latency, hit@k
   - **LLM Backend** - Model performance, token usage
   - **Cost & Budgets** - Spend tracking, burn rate

**Distributed Traces:**
1. Open http://localhost:16686 (Jaeger UI)
2. Select your service name
3. View end-to-end traces with:
   - Linked spans (embed → retrieve → generate)
   - Token counts and costs
   - Error details

**Metrics Explorer:**
1. Open http://localhost:9090 (Prometheus)
2. Query metrics:
   ```promql
   gen_ai_requests_total
   gen_ai_cost_usd_total
   gen_ai_tokens_total
   ```

## Option 2: Kubernetes/Production

### 1. Install with Helm

```bash
# Add Helm repos
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install GenAI Observability
cd deploy/helm
helm install genai-obs . -n genai-observability --create-namespace
```

### 2. Configure SDK to Use Cluster Endpoint

**Python:**
```python
import os
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://opentelemetry-collector.genai-observability:4317"
```

**Node.js:**
```typescript
const exporter = new OTLPTraceExporter({
  url: 'http://opentelemetry-collector.genai-observability:4317'
});
```

### 3. Access Dashboards

**Port Forward (Dev):**
```bash
kubectl port-forward -n genai-observability svc/grafana 3000:80
```

**Ingress (Prod):**
Update `values.yaml`:
```yaml
grafana:
  ingress:
    enabled: true
    hosts:
      - grafana.yourdomain.com
```

## Configuration

### Environment Variables

```bash
# Service identification
export OTEL_SERVICE_NAME="my-rag-app"
export GENAI_ENVIRONMENT="production"

# Sampling
export GENAI_OTEL_SAMPLE_RATE="0.1"  # 10% sampling

# PII redaction
export GENAI_OTEL_REDACT_PATTERNS="email,ssn,api_key"

# Cost tracking
export GENAI_TENANT_ID="customer-123"
export GENAI_USER_ID="user-456"

# Prompt logging (disabled by default for privacy)
export GENAI_OTEL_LOG_PROMPTS="false"
```

### Python Configuration

```python
from genai_otel import GenAIConfig, set_config

config = GenAIConfig(
    service_name="my-app",
    environment="prod",
    log_prompts=False,
    sample_rate=0.1,
    tenant_id="customer-123"
)
set_config(config)
```

### Node.js Configuration

```typescript
import { setConfig } from '@genai-obs/otel';

setConfig({
  serviceName: 'my-app',
  environment: 'prod',
  logPrompts: false,
  sampleRate: 0.1,
  tenantId: 'customer-123'
});
```

## Example Metrics & Traces

### What You'll See

**Traces:**
```
rag_pipeline (500ms)
├── gen_ai.embed (50ms)
│   ├── model: text-embedding-3-small
│   ├── tokens: 8
│   └── cost: $0.00000016
├── gen_ai.retrieve (120ms)
│   ├── source: pinecone
│   ├── top_k: 10
│   ├── results_count: 10
│   └── hit_at_k: 1
└── gen_ai.generate (330ms)
    ├── model: gpt-4
    ├── input_tokens: 150
    ├── output_tokens: 45
    └── cost: $0.0072
```

**Metrics:**
- `gen_ai_requests_total{operation="generate",model="gpt-4",status="success"}` = 1234
- `gen_ai_cost_usd_total{provider="openai",model="gpt-4"}` = 45.67
- `gen_ai_tokens_total{model="gpt-4",token_type="input"}` = 150000

## Alerts

Prometheus alerts fire automatically for:

- **Latency**: P95 > 5s
- **Errors**: Error rate > 5%
- **Cost**: Burn rate > $50/hour
- **Quality**: Hit@K < 70%

View active alerts:
```bash
# Local
open http://localhost:9090/alerts

# Kubernetes
kubectl port-forward -n genai-observability svc/prometheus-server 9090:80
```

## Next Steps

1. **Customize Dashboards**: Edit JSON files in `dashboards/`
2. **Add Alert Routes**: Configure Slack/PagerDuty in `alerting/alertmanager.yaml`
3. **Optimize Costs**: Use dashboards to identify expensive models
4. **Improve Quality**: Monitor hit@k and retrieval performance
5. **Scale Up**: Deploy to Kubernetes with Helm chart

## Troubleshooting

### No Data in Grafana

1. Check OTel Collector:
   ```bash
   docker logs genai-otel-collector
   # or
   kubectl logs -n genai-observability -l app=opentelemetry-collector
   ```

2. Verify SDK configuration:
   ```python
   # Test OTLP endpoint
   curl -v http://localhost:4317
   ```

3. Check Prometheus targets:
   ```bash
   open http://localhost:9090/targets
   ```

### High Costs

1. Review Cost Dashboard for top models
2. Enable sampling to reduce telemetry overhead:
   ```bash
   export GENAI_OTEL_SAMPLE_RATE="0.05"  # 5%
   ```
3. Set budget alerts in `values.yaml`:
   ```yaml
   genai:
     cost:
       budgetLimit: 500  # Daily limit
   ```

### PII Leakage

1. Verify redaction is enabled:
   ```bash
   export GENAI_OTEL_REDACT_PATTERNS="email,ssn,api_key,phone"
   ```

2. Disable prompt logging:
   ```bash
   export GENAI_OTEL_LOG_PROMPTS="false"
   ```

## Support

- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder
- **Issues**: https://github.com/genai-obs/genai-observability-suite/issues
