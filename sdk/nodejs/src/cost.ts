/**
 * Cost calculation for various LLM providers and models
 */

interface ModelPricing {
  input: number;
  output: number;
}

interface ProviderPricing {
  [model: string]: ModelPricing;
}

// Pricing per 1M tokens (USD) - as of Jan 2025
const PRICING_TABLE: Record<string, ProviderPricing> = {
  openai: {
    'gpt-4-turbo': { input: 10.0, output: 30.0 },
    'gpt-4': { input: 30.0, output: 60.0 },
    'gpt-3.5-turbo': { input: 0.5, output: 1.5 },
    'text-embedding-3-small': { input: 0.02, output: 0.0 },
    'text-embedding-3-large': { input: 0.13, output: 0.0 },
    'text-embedding-ada-002': { input: 0.1, output: 0.0 },
  },
  anthropic: {
    'claude-3-opus-20240229': { input: 15.0, output: 75.0 },
    'claude-3-sonnet-20240229': { input: 3.0, output: 15.0 },
    'claude-3-haiku-20240307': { input: 0.25, output: 1.25 },
    'claude-3-5-sonnet-20241022': { input: 3.0, output: 15.0 },
  },
  cohere: {
    'command-r-plus': { input: 3.0, output: 15.0 },
    'command-r': { input: 0.5, output: 1.5 },
    'embed-english-v3.0': { input: 0.1, output: 0.0 },
    'rerank-english-v3.0': { input: 2.0, output: 0.0 },
  },
  together: {
    'meta-llama/Llama-3-70b': { input: 0.9, output: 0.9 },
    'meta-llama/Llama-3-8b': { input: 0.2, output: 0.2 },
    'mistralai/Mixtral-8x7B-Instruct-v0.1': { input: 0.6, output: 0.6 },
  },
};

export class CostCalculator {
  private pricing: Record<string, ProviderPricing>;

  constructor(customPricing?: Record<string, ProviderPricing>) {
    this.pricing = { ...PRICING_TABLE };
    if (customPricing) {
      Object.assign(this.pricing, customPricing);
    }
  }

  calculateCost(
    provider: string,
    model: string,
    inputTokens: number,
    outputTokens: number = 0
  ): number {
    const providerLower = provider.toLowerCase();
    const modelNormalized = this.normalizeModelName(model);

    if (!this.pricing[providerLower]) {
      return 0.0;
    }

    let modelPricing = this.pricing[providerLower][modelNormalized];

    if (!modelPricing) {
      // Try partial match for versioned models
      for (const [knownModel, pricing] of Object.entries(this.pricing[providerLower])) {
        if (knownModel.includes(modelNormalized) || modelNormalized.includes(knownModel)) {
          modelPricing = pricing;
          break;
        }
      }
    }

    if (!modelPricing) {
      return 0.0;
    }

    const inputCost = (inputTokens / 1_000_000) * modelPricing.input;
    const outputCost = (outputTokens / 1_000_000) * modelPricing.output;

    return parseFloat((inputCost + outputCost).toFixed(8));
  }

  private normalizeModelName(model: string): string {
    return model.trim().toLowerCase();
  }

  addCustomPricing(
    provider: string,
    model: string,
    inputPricePer1M: number,
    outputPricePer1M: number = 0.0
  ): void {
    const providerLower = provider.toLowerCase();
    if (!this.pricing[providerLower]) {
      this.pricing[providerLower] = {};
    }

    this.pricing[providerLower][model] = {
      input: inputPricePer1M,
      output: outputPricePer1M,
    };
  }
}

let calculator: CostCalculator | null = null;

export function getCostCalculator(): CostCalculator {
  if (!calculator) {
    calculator = new CostCalculator();
  }
  return calculator;
}
