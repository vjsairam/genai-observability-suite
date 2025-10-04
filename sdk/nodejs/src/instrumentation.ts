/**
 * Core instrumentation helpers for GenAI operations
 */

import { trace, Span, SpanStatusCode, context } from '@opentelemetry/api';
import { getConfig } from './config';
import { getCostCalculator } from './cost';
import { redactSensitiveData } from './redaction';

const tracer = trace.getTracer('genai-otel');

interface EmbedOptions {
  model: string;
  provider?: string;
  batchSize?: number;
  dimensions?: number;
}

interface RetrieveOptions {
  source: string;
  topK: number;
  indexName?: string;
  filters?: Record<string, any>;
}

interface RerankOptions {
  model: string;
  provider?: string;
  inputCount?: number;
  topN?: number;
}

interface GenerateOptions {
  model: string;
  provider?: string;
  temperature?: number;
  maxTokens?: number;
  streaming?: boolean;
}

interface ToolCallOptions {
  toolName: string;
  parameters?: Record<string, any>;
}

export function traceEmbed(options: EmbedOptions) {
  return function <T extends (...args: any[]) => any>(
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const config = getConfig();
      const startTime = Date.now();

      return tracer.startActiveSpan('gen_ai.embed', async (span: Span) => {
        try {
          span.setAttributes({
            'gen_ai.operation.name': 'embed',
            'gen_ai.request.model': options.model,
            'gen_ai.request.provider': options.provider || 'openai',
            'gen_ai.environment': config.environment,
          });

          if (options.batchSize) {
            span.setAttribute('gen_ai.request.batch_size', options.batchSize);
          }
          if (options.dimensions) {
            span.setAttribute('gen_ai.response.dimensions', options.dimensions);
          }

          const result = await originalMethod.apply(this, args);

          // Extract token usage if available
          if (result?.usage?.total_tokens) {
            const inputTokens = result.usage.total_tokens;
            span.setAttribute('gen_ai.usage.input_tokens', inputTokens);

            const cost = getCostCalculator().calculateCost(
              options.provider || 'openai',
              options.model,
              inputTokens
            );
            if (cost > 0) {
              span.setAttribute('gen_ai.usage.cost_usd', cost);
            }
          }

          span.setAttribute('gen_ai.request.duration_ms', Date.now() - startTime);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
          span.setAttributes({
            error: true,
            'error.type': error.constructor.name,
            'error.message': error.message?.substring(0, 200),
          });
          throw error;
        } finally {
          span.end();
        }
      });
    };

    return descriptor;
  };
}

export function traceRetrieve(options: RetrieveOptions) {
  return function <T extends (...args: any[]) => any>(
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const config = getConfig();
      const startTime = Date.now();

      return tracer.startActiveSpan('gen_ai.retrieve', async (span: Span) => {
        try {
          span.setAttributes({
            'gen_ai.operation.name': 'retrieve',
            'gen_ai.retrieval.top_k': options.topK,
            'gen_ai.retrieval.source': options.source,
            'gen_ai.environment': config.environment,
          });

          if (options.indexName) {
            span.setAttribute('gen_ai.retrieval.index_name', options.indexName);
          }
          if (options.filters) {
            span.setAttribute(
              'gen_ai.retrieval.filters',
              JSON.stringify(options.filters).substring(0, config.maxAttributeLength)
            );
          }

          const result = await originalMethod.apply(this, args);

          const resultsCount = Array.isArray(result) ? result.length : 0;
          span.setAttribute('gen_ai.retrieval.results_count', resultsCount);
          span.setAttribute('gen_ai.retrieval.hit_at_k', resultsCount > 0 ? 1 : 0);

          span.setAttribute('gen_ai.request.duration_ms', Date.now() - startTime);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
          span.setAttributes({
            error: true,
            'error.type': error.constructor.name,
            'error.message': error.message?.substring(0, 200),
          });
          throw error;
        } finally {
          span.end();
        }
      });
    };

    return descriptor;
  };
}

export function traceRerank(options: RerankOptions) {
  return function <T extends (...args: any[]) => any>(
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const config = getConfig();
      const startTime = Date.now();

      return tracer.startActiveSpan('gen_ai.rerank', async (span: Span) => {
        try {
          span.setAttributes({
            'gen_ai.operation.name': 'rerank',
            'gen_ai.rerank.model': options.model,
            'gen_ai.environment': config.environment,
          });

          if (options.inputCount) {
            span.setAttribute('gen_ai.rerank.input_count', options.inputCount);
          }
          if (options.topN) {
            span.setAttribute('gen_ai.rerank.top_n', options.topN);
          }

          const result = await originalMethod.apply(this, args);

          const outputCount = Array.isArray(result) ? result.length : 0;
          span.setAttribute('gen_ai.rerank.output_count', outputCount);

          span.setAttribute('gen_ai.request.duration_ms', Date.now() - startTime);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
          span.setAttributes({
            error: true,
            'error.type': error.constructor.name,
            'error.message': error.message?.substring(0, 200),
          });
          throw error;
        } finally {
          span.end();
        }
      });
    };

    return descriptor;
  };
}

export function traceGenerate(options: GenerateOptions) {
  return function <T extends (...args: any[]) => any>(
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const config = getConfig();
      const startTime = Date.now();

      return tracer.startActiveSpan('gen_ai.generate', async (span: Span) => {
        try {
          span.setAttributes({
            'gen_ai.operation.name': 'generate',
            'gen_ai.request.model': options.model,
            'gen_ai.request.provider': options.provider || 'openai',
            'gen_ai.environment': config.environment,
          });

          if (options.temperature !== undefined) {
            span.setAttribute('gen_ai.request.temperature', options.temperature);
          }
          if (options.maxTokens) {
            span.setAttribute('gen_ai.request.max_tokens', options.maxTokens);
          }
          if (options.streaming) {
            span.setAttribute('gen_ai.request.streaming', options.streaming);
          }

          // Log prompt if configured
          if (config.logPrompts && args.length > 0) {
            const promptText = String(args[0]).substring(0, config.maxAttributeLength);
            span.setAttribute('gen_ai.prompt', redactSensitiveData(promptText, config));
          }

          const result = await originalMethod.apply(this, args);

          // Extract token usage
          if (result?.usage) {
            const inputTokens = result.usage.prompt_tokens || 0;
            const outputTokens = result.usage.completion_tokens || 0;
            const totalTokens = result.usage.total_tokens || 0;

            span.setAttributes({
              'gen_ai.usage.input_tokens': inputTokens,
              'gen_ai.usage.output_tokens': outputTokens,
              'gen_ai.usage.total_tokens': totalTokens,
            });

            const cost = getCostCalculator().calculateCost(
              options.provider || 'openai',
              options.model,
              inputTokens,
              outputTokens
            );
            if (cost > 0) {
              span.setAttribute('gen_ai.usage.cost_usd', cost);
            }
          }

          // Extract finish reason
          if (result?.choices?.[0]?.finish_reason) {
            span.setAttribute('gen_ai.response.finish_reason', result.choices[0].finish_reason);
          }

          // Log completion if configured
          if (config.logPrompts && result?.choices?.[0]?.message?.content) {
            const completion = result.choices[0].message.content.substring(0, config.maxAttributeLength);
            span.setAttribute('gen_ai.completion', redactSensitiveData(completion, config));
          }

          span.setAttribute('gen_ai.request.duration_ms', Date.now() - startTime);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error: any) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
          span.setAttributes({
            error: true,
            'error.type': error.constructor.name,
            'error.message': error.message?.substring(0, 200),
          });
          throw error;
        } finally {
          span.end();
        }
      });
    };

    return descriptor;
  };
}

export function traceToolCall(options: ToolCallOptions) {
  return function <T extends (...args: any[]) => any>(
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const config = getConfig();
      const startTime = Date.now();
      let resultStatus = 'success';
      let errorType: string | undefined;

      return tracer.startActiveSpan('gen_ai.tool_call', async (span: Span) => {
        try {
          span.setAttributes({
            'gen_ai.operation.name': 'tool_call',
            'gen_ai.tool.name': options.toolName,
            'gen_ai.environment': config.environment,
          });

          if (options.parameters) {
            const paramsStr = JSON.stringify(options.parameters).substring(0, config.maxAttributeLength);
            span.setAttribute('gen_ai.tool.parameters', redactSensitiveData(paramsStr, config));
          }

          const result = await originalMethod.apply(this, args);

          const resultStr = JSON.stringify(result);
          const resultSize = Buffer.byteLength(resultStr, 'utf8');
          span.setAttribute('gen_ai.tool.result_size_bytes', resultSize);

          span.setAttribute('gen_ai.request.duration_ms', Date.now() - startTime);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error: any) {
          resultStatus = 'error';
          errorType = error.constructor.name;
          span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
          span.setAttributes({
            error: true,
            'error.type': errorType,
            'error.message': error.message?.substring(0, 200),
          });
          throw error;
        } finally {
          span.setAttribute('gen_ai.tool.result_status', resultStatus);
          if (errorType) {
            span.setAttribute('gen_ai.tool.error_type', errorType);
          }
          span.end();
        }
      });
    };

    return descriptor;
  };
}
