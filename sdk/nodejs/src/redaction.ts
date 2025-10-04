/**
 * PII and secrets redaction utilities
 */

import { GenAIConfig } from './config';

const PATTERNS: Record<string, RegExp> = {
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
  api_key: /\b[A-Za-z0-9_-]{20,}\b(?=.*key)/gi,
  credit_card: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g,
  phone: /\b\+?1?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
  ipv4: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g,
  bearer_token: /Bearer\s+[A-Za-z0-9._-]+/gi,
  aws_key: /(?:AWS|aws)[\w]*(?:key|KEY)[\w]*\s*[:=]\s*['"]?([A-Za-z0-9/+=]{40})['"]?/g,
  github_token: /gh[pousr]_[A-Za-z0-9_]{36,255}/g,
};

const REPLACEMENTS: Record<string, string> = {
  email: '[EMAIL_REDACTED]',
  ssn: '[SSN_REDACTED]',
  api_key: '[API_KEY_REDACTED]',
  credit_card: '[CC_REDACTED]',
  phone: '[PHONE_REDACTED]',
  ipv4: '[IP_REDACTED]',
  bearer_token: '[BEARER_TOKEN_REDACTED]',
  aws_key: '[AWS_KEY_REDACTED]',
  github_token: '[GITHUB_TOKEN_REDACTED]',
};

export function redactSensitiveData(text: string, config: GenAIConfig): string {
  let redacted = text;

  for (const patternName of config.redactPatterns) {
    const name = patternName.trim().toLowerCase();
    if (PATTERNS[name]) {
      const replacement = REPLACEMENTS[name] || '[REDACTED]';
      redacted = redacted.replace(PATTERNS[name], replacement);
    }
  }

  return redacted;
}

export function addRedactionPattern(name: string, pattern: RegExp, replacement: string = '[REDACTED]'): void {
  PATTERNS[name] = pattern;
  REPLACEMENTS[name] = replacement;
}
