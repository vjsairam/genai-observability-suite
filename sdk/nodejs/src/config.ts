/**
 * Configuration management for GenAI OpenTelemetry SDK
 */

export interface GenAIConfig {
  // Service identification
  serviceName: string;
  environment: string;

  // OTLP Exporter
  otlpEndpoint: string;
  otlpProtocol: 'grpc' | 'http';

  // Sampling & Logging
  logPrompts: boolean;
  sampleRate: number;

  // PII Redaction
  redactPatterns: string[];

  // Cost tracking
  tenantId?: string;
  userId?: string;

  // Performance
  maxAttributeLength: number;
}

const defaultConfig: GenAIConfig = {
  serviceName: process.env.OTEL_SERVICE_NAME || 'genai-app',
  environment: process.env.GENAI_ENVIRONMENT || 'dev',
  otlpEndpoint: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
  otlpProtocol: (process.env.OTEL_EXPORTER_OTLP_PROTOCOL as 'grpc' | 'http') || 'grpc',
  logPrompts: process.env.GENAI_OTEL_LOG_PROMPTS?.toLowerCase() === 'true',
  sampleRate: parseFloat(process.env.GENAI_OTEL_SAMPLE_RATE || '0.01'),
  redactPatterns: (process.env.GENAI_OTEL_REDACT_PATTERNS || 'email,ssn,api_key,credit_card').split(','),
  tenantId: process.env.GENAI_TENANT_ID,
  userId: process.env.GENAI_USER_ID,
  maxAttributeLength: parseInt(process.env.GENAI_MAX_ATTR_LENGTH || '2000'),
};

let config: GenAIConfig = defaultConfig;

export function getConfig(): GenAIConfig {
  return config;
}

export function setConfig(newConfig: Partial<GenAIConfig>): void {
  config = { ...config, ...newConfig };

  // Validate
  if (config.sampleRate < 0 || config.sampleRate > 1) {
    throw new Error('sampleRate must be between 0 and 1');
  }
  if (config.maxAttributeLength < 100) {
    throw new Error('maxAttributeLength must be at least 100');
  }
}
