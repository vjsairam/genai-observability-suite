# GenAI Alerting Rules

Prometheus alerting rules for GenAI observability covering SLOs, cost control, and quality metrics.

## Alert Categories

### 1. SLO Alerts (`genai_slo_alerts`)

#### Latency Alerts
- **GenAI_HighLatency_P95** (warning)
  - Trigger: P95 latency > 5000ms for 5 minutes
  - Action: Investigate slow operations, check provider status

- **GenAI_CriticalLatency_P95** (critical)
  - Trigger: P95 latency > 10000ms for 2 minutes
  - Action: Immediate investigation, consider failover

#### Error Rate Alerts
- **GenAI_HighErrorRate** (warning)
  - Trigger: Error rate > 5% for 5 minutes
  - Action: Check error types, review logs

- **GenAI_CriticalErrorRate** (critical)
  - Trigger: Error rate > 10% for 2 minutes
  - Action: Immediate response, page on-call

### 2. Cost Alerts (`genai_cost_alerts`)

- **GenAI_HighCostBurnRate** (warning)
  - Trigger: Cost > $50/hour for 10 minutes
  - Action: Review usage patterns, check for runaway processes

- **GenAI_CriticalCostBurnRate** (critical)
  - Trigger: Cost > $100/hour for 5 minutes
  - Action: Immediate investigation, consider throttling

- **GenAI_DailyBudgetProjectionExceeded** (warning)
  - Trigger: Projected daily cost > $1000 for 15 minutes
  - Action: Review budget allocation, optimize usage

- **GenAI_ModelCostSpike** (warning)
  - Trigger: Cost increased 2x compared to 1 hour ago
  - Action: Investigate usage spike for specific model

### 3. Retrieval Quality Alerts (`genai_retrieval_alerts`)

- **GenAI_LowRetrievalHitRate** (warning)
  - Trigger: Hit@K rate < 70% for 10 minutes
  - Action: Review embeddings, check index health

- **GenAI_RetrievalMissSpike** (warning)
  - Trigger: >20% of retrievals return no results for 5 minutes
  - Action: Check index population, review queries

- **GenAI_SlowRetrieval** (warning)
  - Trigger: P95 retrieval latency > 500ms for 10 minutes
  - Action: Check vector store performance, review indexes

### 4. Token Usage Alerts (`genai_token_alerts`)

- **GenAI_TokenUsageSpike** (info)
  - Trigger: Token usage increased 3x compared to 1 hour ago
  - Action: Monitor for anomalies, verify expected behavior

- **GenAI_HighTokenRate** (info)
  - Trigger: Token rate > 100K tokens/sec for 15 minutes
  - Action: Consider scaling or throttling

### 5. Availability Alerts (`genai_availability_alerts`)

- **GenAI_ProviderDown** (critical)
  - Trigger: >50% requests failing with connectivity errors for 3 minutes
  - Action: Check provider status, implement failover

- **GenAI_RateLimitExceeded** (warning)
  - Trigger: Rate limit errors detected for 5 minutes
  - Action: Review rate limits, implement backoff/retry

### 6. Data Quality Alerts (`genai_data_quality_alerts`)

- **GenAI_NoDataReceived** (warning)
  - Trigger: No metrics received for 10 minutes
  - Action: Check instrumentation, verify exporters

- **GenAI_MetricsStale** (warning)
  - Trigger: Metrics not updated for 5 minutes
  - Action: Check pipeline, verify collection

## Configuration

### Load Rules into Prometheus

1. **Via ConfigMap (Kubernetes)**:
```yaml
kubectl create configmap genai-alerts \
  --from-file=prometheus-rules.yaml \
  -n monitoring
```

2. **Via Prometheus Config**:
```yaml
rule_files:
  - /etc/prometheus/rules/prometheus-rules.yaml
```

3. **Reload Prometheus**:
```bash
curl -X POST http://localhost:9090/-/reload
```

### Alert Routing (Alertmanager)

```yaml
route:
  group_by: ['alertname', 'component']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
        component: genai
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
        component: genai
      receiver: 'slack-genai'

    - match:
        type: cost
      receiver: 'slack-finops'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<your-pd-key>'

  - name: 'slack-genai'
    slack_configs:
      - api_url: '<your-webhook>'
        channel: '#genai-alerts'

  - name: 'slack-finops'
    slack_configs:
      - api_url: '<your-webhook>'
        channel: '#finops'
```

## Customization

### Adjust Thresholds

Edit `prometheus-rules.yaml` to customize thresholds:

```yaml
# Change latency threshold from 5000ms to 3000ms
expr: |
  histogram_quantile(0.95, ...) > 3000  # was 5000
```

### Add Custom Alerts

```yaml
- alert: GenAI_CustomMetric
  expr: |
    your_custom_metric > threshold
  for: 5m
  labels:
    severity: warning
    component: genai
  annotations:
    summary: "Your alert summary"
    description: "Detailed description"
```

### Silence Alerts

```bash
# Silence an alert for 2 hours
amtool silence add \
  alertname=GenAI_HighCostBurnRate \
  --duration=2h \
  --comment="Maintenance window"
```

## Testing Alerts

### Verify Rules Syntax
```bash
promtool check rules prometheus-rules.yaml
```

### Unit Test Alerts
```bash
promtool test rules alert-tests.yaml
```

### Trigger Test Alert
```bash
# Manually trigger alert
curl -X POST http://alertmanager:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname": "Test", "severity": "warning"},
    "annotations": {"summary": "Test alert"}
  }]'
```

## Runbooks

Alert annotations include `runbook_url` links. Create runbooks at:
- `/docs/runbooks/genai-high-latency.md`
- `/docs/runbooks/genai-high-errors.md`
- `/docs/runbooks/genai-cost-control.md`
- `/docs/runbooks/genai-low-hit-rate.md`
- `/docs/runbooks/genai-provider-down.md`
- `/docs/runbooks/genai-rate-limits.md`

## Integration with Dashboards

Alerts are visualized in Grafana dashboards:
- **RAG Overview**: Shows active alerts
- **Cost & Budgets**: Budget threshold lines
- **LLM Backend**: Provider health status

## Best Practices

1. **Alert Fatigue**: Tune thresholds to reduce noise
2. **Context**: Include relevant labels (model, provider, tenant_id)
3. **Actionable**: Every alert should have clear remediation steps
4. **Escalation**: Critical alerts should page, warnings go to Slack
5. **Documentation**: Keep runbooks up-to-date
