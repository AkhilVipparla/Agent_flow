// Preset OpenAI-compatible providers. Model lists are suggestions, not a gate: every
// provider also offers "Other" so a newly released model can be typed in.

export interface Provider {
  id: string;
  label: string;
  baseUrl: string;
  models: string[];
  keyHint: string;
}

export const CUSTOM_PROVIDER_ID = 'custom';
export const OTHER_MODEL = '__other__';

export const providers: Provider[] = [
  {
    id: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-4.1', 'gpt-4.1-mini', 'gpt-4o', 'gpt-4o-mini', 'o4-mini'],
    keyHint: 'sk-...',
  },
  {
    id: 'anthropic',
    label: 'Anthropic (Claude)',
    baseUrl: 'https://api.anthropic.com/v1/',
    models: ['claude-fable-5-1', 'claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-5-5'],
    keyHint: 'sk-ant-...',
  },
  {
    id: 'gemini',
    label: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    models: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.0-flash'],
    keyHint: 'AIza...',
  },
  {
    id: 'groq',
    label: 'Groq',
    baseUrl: 'https://api.groq.com/openai/v1',
    models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'openai/gpt-oss-120b'],
    keyHint: 'gsk_...',
  },
  {
    id: 'mistral',
    label: 'Mistral',
    baseUrl: 'https://api.mistral.ai/v1',
    models: ['mistral-large-latest', 'mistral-small-latest'],
    keyHint: 'Mistral API key',
  },
  {
    id: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    keyHint: 'sk-...',
  },
  {
    id: 'openrouter',
    label: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    models: [
      'openai/gpt-4o-mini',
      'google/gemini-2.5-flash',
      'meta-llama/llama-3.3-70b-instruct',
      'deepseek/deepseek-chat',
    ],
    keyHint: 'sk-or-...',
  },
  {
    id: 'ollama',
    label: 'Ollama (local)',
    baseUrl: 'http://localhost:11434/v1',
    models: ['qwen3:8b', 'llama3.1:8b', 'mistral:7b'],
    keyHint: 'any text, e.g. ollama',
  },
];

export function findProvider(id: string): Provider | undefined {
  return providers.find((p) => p.id === id);
}

// Credentials saved before the provider dropdown existed only have a base URL.
export function inferProviderId(baseUrl: string): string {
  const normalized = baseUrl.replace(/\/+$/, '');
  return providers.find((p) => p.baseUrl.replace(/\/+$/, '') === normalized)?.id ?? CUSTOM_PROVIDER_ID;
}
