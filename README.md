# GenAI Observability Suite

[![CI/CD](https://github.com/genai-obs/genai-observability-suite/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/genai-obs/genai-observability-suite/actions)
[![Security Scan](https://github.com/genai-obs/genai-observability-suite/workflows/Security%20Scanning/badge.svg)](https://github.com/genai-obs/genai-observability-suite/security)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> A turnkey AI observability stack for LLM/RAG systems: standardized OpenTelemetry traces/metrics/logs for prompts, tokens, costs, retrieval performance, and agent/tool spans—plus dashboards, SLOs, and ready-to-copy alert rules.

## ✨ Features

- 🎯 **Drop-in Instrumentation** - Python & Node.js SDKs with simple decorators
- 💰 **Automatic Cost Tracking** - Built-in pricing for OpenAI, Anthropic, Cohere, Together AI
- 📊 **Production Dashboards** - Pre-built Grafana dashboards for RAG, LLM, and Cost
- 🚨 **Smart Alerts** - Prometheus rules for latency, errors, cost burn, retrieval quality
- 🔒 **PII Redaction** - Automatic masking of emails, API keys, SSNs, credit cards
- 🔗 **Distributed Tracing** - Full visibility across embed → retrieve → rerank → generate
- 📈 **RAG Metrics** - Hit@k proxy, recall estimator, retrieval latency, reranker impact
- 🏗️ **Production Ready** - Docker Compose for local, Helm for Kubernetes

## 🚀 Quick Start

### 1. Start Observability Stack (Local)

```bash
git clone https://github.com/genai-obs/genai-observability-suite
cd genai-observability-suite/deploy/docker
docker-compose up -d
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

**Python:**
```python
from genai_otel import trace_embed, trace_retrieve, trace_generate

@trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
def embed_query(text: str):
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
```

**Node.js:**
```typescript
import { traceEmbed, traceRetrieve, traceGenerate } from '@genai-obs/otel';

class RAGService {
  @traceEmbed({ model: 'text-embedding-3-small', provider: 'openai', dimensions: 1536 })
  async embedQuery(text: string) { ... }

  @traceRetrieve({ source: 'pinecone', topK: 10, indexName: 'docs' })
  async searchDocs(vector: number[]) { ... }

  @traceGenerate({ model: 'gpt-4', provider: 'openai', temperature: 0.7 })
  async generateAnswer(prompt: string) { ... }
}
```

### 4. View Observability

- **Grafana**: http://localhost:3000 (admin/admin)
  - RAG Overview Dashboard
  - LLM Backend Performance
  - Cost & Budgets

- **Jaeger Traces**: http://localhost:16686
  - Distributed traces with token counts & costs

- **Prometheus**: http://localhost:9090
  - Metrics: `gen_ai_requests_total`, `gen_ai_cost_usd_total`, `gen_ai_tokens_total`

## 📦 What's Included

### SDKs
- **[Python SDK](sdk/python/)** - OpenTelemetry instrumentation for Python
- **[Node.js SDK](sdk/nodejs/)** - OpenTelemetry instrumentation for TypeScript/JavaScript

### Dashboards
- **[RAG Overview](dashboards/rag-overview.json)** - Request rates, latency, hit@k metrics
- **[LLM Backend](dashboards/llm-backend.json)** - Model performance, token usage
- **[Cost & Budgets](dashboards/cost-budgets.json)** - Spend tracking, burn rate, projections

### Alerting
- **[Prometheus Rules](alerting/prometheus-rules.yaml)** - 20+ production-ready alerts
  - P95 latency breach
  - Error rate spike
  - Cost burn > threshold
  - Retrieval miss spike
  - Provider downtime

### Deployment
- **[Docker Compose](deploy/docker/)** - Local development stack
  - OTel Collector, Prometheus, Grafana, Tempo, Jaeger, Loki
- **[Helm Chart](deploy/helm/)** - Production Kubernetes deployment
  - Multi-replica, auto-scaling, HA configuration

### Documentation
- **[Quickstart Guide](docs/guides/quickstart.md)** - Get running in 15 minutes
- **[Integration Guide](docs/guides/integration.md)** - Complete integration walkthrough
- **[Semantic Conventions](docs/semantic-conventions.md)** - Span attribute reference

### Examples
- **[Python RAG Pipeline](examples/python-rag-pipeline/)** - Complete RAG example with all span types

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      Your GenAI Application         │
│  ┌────────┐  ┌────────┐  ┌────────┐ │
│  │ Embed  │→ │Retrieve│→ │Generate│ │
│  └────────┘  └────────┘  └────────┘ │
│       ↓           ↓           ↓      │
│  ┌──────────────────────────────┐   │
│  │    GenAI OTel SDK            │   │
│  │ • Auto-instrumentation       │   │
│  │ • Cost calculation           │   │
│  │ • PII redaction              │   │
│  └──────────────────────────────┘   │
└──────────────────┬──────────────────┘
                   │ OTLP
                   ↓
        ┌─────────────────┐
        │  OTel Collector │
        └─────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ↓              ↓               ↓
┌────────┐  ┌───────────┐  ┌──────────┐
│ Tempo  │  │Prometheus │  │   Loki   │
│(Traces)│  │ (Metrics) │  │  (Logs)  │
└────────┘  └───────────┘  └──────────┘
                   │
                   ↓
            ┌─────────────┐
            │   Grafana   │
            └─────────────┘
```

## 📊 Example Output

### Distributed Trace
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

### Key Metrics
- `gen_ai_requests_total` - Total requests by operation, model, status
- `gen_ai_tokens_total` - Token usage by model, type (input/output)
- `gen_ai_cost_usd_total` - Cost tracking by provider, model, tenant
- `gen_ai_request_duration` - Latency histograms
- `gen_ai_retrieval_hit_at_k` - Retrieval quality gauge

## 🔐 Security & Privacy

- **PII Redaction**: Automatic masking of sensitive data (emails, SSNs, API keys)
- **No Prompts by Default**: Prompts/completions not logged unless explicitly enabled
- **Sampling**: Configurable sampling (default 1%) to reduce overhead
- **Signed Images**: All container images signed with Cosign
- **SBOM**: Software Bill of Materials for every release
- **Security Scans**: Trivy, Semgrep, Bandit in CI/CD

## 🚢 Deployment Options

### Local Development
```bash
cd deploy/docker
docker-compose up -d
```

### Kubernetes/Production
```bash
helm repo add genai-obs https://genai-obs.github.io/genai-observability-suite
helm install genai-obs genai-obs/genai-observability \
  -n genai-observability --create-namespace
```

## 📈 Roadmap

- [x] **W1-2**: SDK + sample app (Python/Node.js)
- [x] **W3**: Dashboards + alerts + docs
- [x] **W4-5**: Cost tracking, hit@k proxy, reranker metrics
- [x] **W6-7**: Helm chart + redaction policies
- [ ] **W8**: Hardening, "integration in 15 min" guide
- [ ] **Future**: LangChain/LlamaIndex auto-instrumentation, LLM-as-a-judge metrics

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built on:
- [OpenTelemetry](https://opentelemetry.io/)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [Tempo](https://grafana.com/oss/tempo/)
- [Jaeger](https://www.jaegertracing.io/)

## 📧 Contact

- **Issues**: https://github.com/genai-obs/genai-observability-suite/issues
- **Discussions**: https://github.com/genai-obs/genai-observability-suite/discussions

---

**⭐ If this project helps your GenAI observability, give it a star!**
