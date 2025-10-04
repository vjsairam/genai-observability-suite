# Docker Compose Deployment

Complete observability stack for GenAI/LLM systems with OpenTelemetry, Prometheus, Grafana, Tempo, Jaeger, and Loki.

## Stack Components

| Component | Port | Purpose |
|-----------|------|---------|
| OTel Collector | 4317, 4318 | OTLP ingestion (gRPC, HTTP) |
| Jaeger UI | 16686 | Distributed tracing visualization |
| Tempo | 3200 | Trace storage backend |
| Prometheus | 9090 | Metrics storage & queries |
| Alertmanager | 9093 | Alert routing & notifications |
| Loki | 3100 | Log aggregation |
| Grafana | 3000 | Unified dashboards |

## Quick Start

### 1. Start Stack

```bash
cd deploy/docker
docker-compose up -d
```

### 2. Verify Services

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f otel-collector
```

### 3. Access UIs

- **Grafana**: http://localhost:3000 (admin/admin)
  - Pre-loaded dashboards: RAG Overview, LLM Backend, Cost & Budgets
- **Jaeger**: http://localhost:16686
  - Distributed trace viewer
- **Prometheus**: http://localhost:9090
  - Metrics explorer, alert status
- **Alertmanager**: http://localhost:9093
  - Alert management

### 4. Run Example App

```bash
# Run the Python RAG pipeline example
cd ../../examples/python-rag-pipeline
pip install -r requirements.txt
python app.py
```

### 5. View Results

1. **Grafana Dashboards**
   - Navigate to http://localhost:3000
   - Go to "Dashboards" → "GenAI Observability"
   - Open "RAG Overview" to see metrics

2. **Jaeger Traces**
   - Navigate to http://localhost:16686
   - Select service: "rag-pipeline-demo"
   - View distributed traces with all span types

3. **Prometheus Metrics**
   - Navigate to http://localhost:9090
   - Query: `gen_ai_requests_total`
   - Explore cost, tokens, latency metrics

## Configuration

### OTel Collector

Configure receivers, processors, and exporters in `otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
```

### Prometheus

Adjust scrape intervals and retention in `prometheus.yaml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
```

### Grafana Datasources

Datasources are auto-configured via `grafana-datasources.yaml`:
- Prometheus (metrics)
- Tempo (traces)
- Jaeger (traces)
- Loki (logs)

### Alerting

Edit alert thresholds in `../alerting/prometheus-rules.yaml`:

```yaml
- alert: GenAI_HighCostBurnRate
  expr: sum(rate(gen_ai_cost_usd_total[5m]) * 3600) > 50
```

Configure notification channels in `alertmanager.yaml`.

## Data Persistence

Volumes persist data across restarts:
- `prometheus-data`: Metrics (15-day retention by default)
- `tempo-data`: Traces
- `loki-data`: Logs (7-day retention)
- `grafana-data`: Dashboards, settings

To reset all data:
```bash
docker-compose down -v
```

## Scaling & Production

### Resource Limits

Add to `docker-compose.yaml`:

```yaml
services:
  otel-collector:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

### High Availability

For production, use Kubernetes with Helm (see `../helm/`):
- Multi-replica OTel Collectors
- Distributed Tempo storage (S3/GCS)
- Remote Prometheus storage (Thanos/Cortex)
- Loki clustering

### Security

1. **Enable Authentication**

```yaml
# grafana
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false
  - GF_SECURITY_ADMIN_PASSWORD=${ADMIN_PASSWORD}
```

2. **TLS for OTLP**

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        tls:
          cert_file: /certs/server.crt
          key_file: /certs/server.key
```

3. **Network Segmentation**

```yaml
networks:
  genai-obs:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

## Troubleshooting

### OTel Collector Not Receiving Data

```bash
# Check collector logs
docker-compose logs otel-collector

# Verify endpoint is accessible
curl -v http://localhost:4318/v1/traces

# Test OTLP export
grpcurl -plaintext localhost:4317 list
```

### Prometheus Not Scraping Metrics

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Verify OTel exporter
curl http://localhost:8889/metrics
```

### Grafana Dashboards Not Loading

```bash
# Check dashboard provisioning
docker-compose exec grafana ls /var/lib/grafana/dashboards

# Verify datasources
curl http://localhost:3000/api/datasources
```

### Jaeger Not Showing Traces

```bash
# Check Jaeger health
curl http://localhost:16686/

# Verify OTel → Jaeger export
docker-compose logs otel-collector | grep jaeger
```

## Monitoring the Stack

### Stack Health Check

```bash
# All services health
docker-compose ps

# OTel Collector health
curl http://localhost:13133/

# Prometheus targets
curl http://localhost:9090/-/healthy
```

### Resource Usage

```bash
# View resource consumption
docker stats

# Collector memory usage
docker-compose exec otel-collector cat /proc/meminfo
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (delete all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Next Steps

1. **Integrate Your App**: Update `OTEL_EXPORTER_OTLP_ENDPOINT` to point to collector
2. **Customize Dashboards**: Edit JSON files in `../../dashboards/`
3. **Add Alert Routes**: Configure Slack/PagerDuty in `alertmanager.yaml`
4. **Scale to K8s**: Deploy with Helm chart in `../helm/`
