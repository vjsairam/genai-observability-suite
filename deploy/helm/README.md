# GenAI Observability Helm Chart

Production-ready Kubernetes deployment for GenAI/LLM observability stack.

## Components

- **OpenTelemetry Collector** - OTLP ingestion and processing
- **Prometheus** - Metrics storage and alerting
- **Grafana** - Visualization and dashboards
- **Tempo** - Distributed tracing backend
- **Loki** - Log aggregation
- **Alertmanager** - Alert routing and notifications

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PersistentVolume provisioner (for production)
- Ingress controller (optional, for external access)
- Cert-manager (optional, for TLS)

## Installation

### Quick Start (Development)

```bash
# Add Helm repos
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install the chart
helm install genai-obs . -n genai-observability --create-namespace
```

### Production Installation

1. **Create namespace**

```bash
kubectl create namespace genai-observability
```

2. **Create secrets**

```bash
# Grafana admin password
kubectl create secret generic grafana-admin \
  --from-literal=admin-password='<strong-password>' \
  -n genai-observability

# PagerDuty integration key
kubectl create secret generic pagerduty \
  --from-literal=service-key='<pd-key>' \
  -n genai-observability

# Slack webhook
kubectl create secret generic slack \
  --from-literal=webhook-url='<slack-webhook>' \
  -n genai-observability
```

3. **Create custom values file**

```yaml
# values-production.yaml
global:
  environment: production
  clusterName: prod-us-east-1

grafana:
  adminPassword: ""  # Use secret
  ingress:
    enabled: true
    hosts:
      - grafana.yourdomain.com
    tls:
      - secretName: grafana-tls
        hosts:
          - grafana.yourdomain.com

tempo:
  storage:
    trace:
      backend: s3
      s3:
        bucket: your-traces-bucket
        region: us-east-1

loki:
  config:
    storage_config:
      aws:
        s3: s3://your-logs-bucket/loki
        region: us-east-1

prometheus:
  alertmanager:
    config:
      receivers:
        - name: 'pagerduty'
          pagerduty_configs:
            - service_key_file: /etc/secrets/pagerduty-key
```

4. **Install with custom values**

```bash
helm install genai-obs . \
  -f values-production.yaml \
  -n genai-observability
```

5. **Verify installation**

```bash
# Check all pods are running
kubectl get pods -n genai-observability

# Check services
kubectl get svc -n genai-observability
```

## Configuration

### OpenTelemetry Collector

Configure OTLP receivers:

```yaml
opentelemetry-collector:
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
            max_recv_msg_size_mib: 100
```

### Prometheus

Configure retention and storage:

```yaml
prometheus:
  server:
    retention: 30d
    persistentVolume:
      enabled: true
      size: 100Gi
      storageClass: gp3
```

### Grafana Dashboards

Dashboards are automatically provisioned from ConfigMap:

```bash
# Create dashboard ConfigMap
kubectl create configmap genai-dashboards \
  --from-file=../../dashboards/ \
  -n genai-observability
```

### Alert Rules

Load Prometheus rules:

```bash
# Create rules ConfigMap
kubectl create configmap prometheus-rules \
  --from-file=../../alerting/prometheus-rules.yaml \
  -n genai-observability

# Update Prometheus to use rules
helm upgrade genai-obs . \
  --set prometheus.serverFiles."alerts\.yaml"=prometheus-rules \
  -n genai-observability
```

## Access Services

### Port Forwarding (Development)

```bash
# Grafana
kubectl port-forward -n genai-observability svc/grafana 3000:80

# Prometheus
kubectl port-forward -n genai-observability svc/prometheus-server 9090:80

# OTel Collector
kubectl port-forward -n genai-observability svc/opentelemetry-collector 4317:4317
```

### Ingress (Production)

Services are exposed via Ingress when enabled:

- Grafana: https://grafana.yourdomain.com
- Prometheus: https://prometheus.yourdomain.com (if enabled)

## Scaling

### Horizontal Scaling

```yaml
opentelemetry-collector:
  replicaCount: 5

prometheus:
  server:
    replicaCount: 3

grafana:
  replicas: 3
```

### Vertical Scaling

```yaml
opentelemetry-collector:
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 1000m
      memory: 2Gi
```

### Autoscaling

```yaml
opentelemetry-collector:
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 80
    targetMemoryUtilizationPercentage: 80
```

## High Availability

### Multi-AZ Deployment

```yaml
opentelemetry-collector:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - opentelemetry-collector
          topologyKey: topology.kubernetes.io/zone
```

### Storage Redundancy

```yaml
tempo:
  storage:
    trace:
      backend: s3
      s3:
        bucket: genai-traces
        region: us-east-1
        # Multi-region replication configured at S3 level

prometheus:
  server:
    persistentVolume:
      enabled: true
      size: 100Gi
      storageClass: gp3
      # With EBS multi-attach or external storage
```

## Monitoring the Observability Stack

### Prometheus Metrics

Monitor the stack itself:

```promql
# OTel Collector throughput
rate(otelcol_receiver_accepted_spans[5m])
rate(otelcol_receiver_accepted_metric_points[5m])

# Prometheus ingestion
rate(prometheus_tsdb_head_samples_appended_total[5m])

# Tempo write throughput
rate(tempo_ingester_bytes_received_total[5m])
```

### ServiceMonitor (Prometheus Operator)

```yaml
serviceMonitor:
  enabled: true
  interval: 30s
  labels:
    prometheus: kube-prometheus
```

## Backup & Restore

### Prometheus

```bash
# Backup
kubectl exec -n genai-observability prometheus-server-0 -- \
  tar czf /tmp/prometheus-backup.tar.gz /data

# Restore
kubectl cp genai-observability/prometheus-server-0:/tmp/prometheus-backup.tar.gz \
  ./prometheus-backup.tar.gz
```

### Grafana Dashboards

```bash
# Export dashboards
kubectl exec -n genai-observability grafana-0 -- \
  grafana-cli admin export-dashboards

# Import from ConfigMap
kubectl apply -f dashboards-configmap.yaml
```

## Troubleshooting

### OTel Collector Not Receiving Data

```bash
# Check logs
kubectl logs -n genai-observability -l app=opentelemetry-collector

# Check service endpoints
kubectl get endpoints -n genai-observability opentelemetry-collector

# Test connectivity
kubectl run -n genai-observability test-pod --image=curlimages/curl --rm -it -- \
  curl -v http://opentelemetry-collector:4318/v1/traces
```

### Prometheus Not Scraping

```bash
# Check targets
kubectl port-forward -n genai-observability svc/prometheus-server 9090:80
# Visit http://localhost:9090/targets

# Check ServiceMonitor
kubectl get servicemonitor -n genai-observability
```

### Grafana Datasource Issues

```bash
# Check datasource config
kubectl get configmap -n genai-observability grafana-datasources -o yaml

# Test datasource connectivity
kubectl exec -n genai-observability grafana-0 -- \
  curl http://prometheus-server:80/api/v1/query?query=up
```

## Upgrade

```bash
# Update dependencies
helm dependency update

# Upgrade release
helm upgrade genai-obs . \
  -f values-production.yaml \
  -n genai-observability
```

## Uninstall

```bash
# Delete release
helm uninstall genai-obs -n genai-observability

# Delete namespace
kubectl delete namespace genai-observability

# Clean up PVCs (if needed)
kubectl delete pvc -n genai-observability --all
```

## Values Reference

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Deployment environment | `production` |
| `opentelemetry-collector.enabled` | Enable OTel Collector | `true` |
| `opentelemetry-collector.replicaCount` | Number of collector replicas | `2` |
| `prometheus.enabled` | Enable Prometheus | `true` |
| `prometheus.server.retention` | Metrics retention period | `15d` |
| `grafana.enabled` | Enable Grafana | `true` |
| `grafana.adminPassword` | Grafana admin password | `changeme` |
| `tempo.enabled` | Enable Tempo | `true` |
| `loki.enabled` | Enable Loki | `true` |
| `genai.cost.budgetLimit` | Daily cost budget (USD) | `1000` |
| `genai.sampling.rate` | Default sampling rate | `0.1` |

For complete values, see `values.yaml`.
