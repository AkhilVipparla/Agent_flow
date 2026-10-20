// A user's own LLM key, web-search key and database login. Kept only in this browser,
// under the signed-in account, and sent as request headers. The server never stores them.

export interface LlmCredentials {
  provider: string;
  baseUrl: string;
  apiKey: string;
  model: string;
}

export interface DbCredentials {
  host: string;
  port: string;
  database: string;
  user: string;
  password: string;
  ssl: boolean;
}

export interface StoredCredentials {
  llm: LlmCredentials;
  db: DbCredentials;
  // Tavily API key for the web search agent.
  tavilyKey: string;
  // Use the server's shared read-only demo database instead of the user's own.
  useDemoDb: boolean;
}

export const emptyCredentials: StoredCredentials = {
  llm: { provider: 'openai', baseUrl: 'https://api.openai.com/v1', apiKey: '', model: '' },
  db: { host: '', port: '5432', database: '', user: '', password: '', ssl: true },
  tavilyKey: '',
  useDemoDb: false,
};

// Keys are stored per account so someone else signing in on the same browser can never
// use (or even see) them. AuthProvider sets the owner when the session changes.
let owner: string | null = null;

export function setCredentialsOwner(userId: string | null): void {
  owner = userId;
}

function storageKey(): string | null {
  return owner ? `agentflow.credentials.${owner}` : null;
}

// sessionStorage clears when the tab closes (safe on shared computers);
// localStorage is used only if the user opts in to "remember on this device".
function readFrom(storage: Storage): StoredCredentials | null {
  const key = storageKey();
  if (!key) return null;
  try {
    const raw = storage.getItem(key);
    if (!raw) return null;
    const saved = JSON.parse(raw) as Partial<StoredCredentials>;
    return {
      ...emptyCredentials,
      ...saved,
      llm: { ...emptyCredentials.llm, ...saved.llm },
      db: { ...emptyCredentials.db, ...saved.db },
    };
  } catch {
    return null;
  }
}

export function loadCredentials(): { credentials: StoredCredentials; remembered: boolean } {
  const remembered = readFrom(window.localStorage);
  if (remembered) return { credentials: remembered, remembered: true };
  return { credentials: readFrom(window.sessionStorage) ?? emptyCredentials, remembered: false };
}

export function saveCredentials(credentials: StoredCredentials, remember: boolean): void {
  const key = storageKey();
  if (!key) return;
  clearCredentials();
  try {
    (remember ? window.localStorage : window.sessionStorage).setItem(key, JSON.stringify(credentials));
  } catch {
    /* storage blocked: credentials simply won't persist */
  }
}

export function clearCredentials(): void {
  const key = storageKey();
  if (!key) return;
  try {
    window.localStorage.removeItem(key);
    window.sessionStorage.removeItem(key);
  } catch {
    /* ignore */
  }
}

export function buildDbUrl(db: DbCredentials): string | null {
  if (!db.host || !db.database || !db.user) return null;
  const auth = `${encodeURIComponent(db.user)}:${encodeURIComponent(db.password)}`;
  const port = db.port || '5432';
  const ssl = db.ssl ? '?ssl=require' : '';
  return `postgresql://${auth}@${db.host}:${port}/${encodeURIComponent(db.database)}${ssl}`;
}

export function credentialHeaders(): Record<string, string> {
  const { credentials } = loadCredentials();
  const headers: Record<string, string> = {};
  const { llm, db } = credentials;
  if (llm.apiKey) {
    headers['X-LLM-Api-Key'] = llm.apiKey;
    if (llm.baseUrl) headers['X-LLM-Base-Url'] = llm.baseUrl;
    if (llm.model) headers['X-LLM-Model'] = llm.model;
  }
  if (credentials.tavilyKey) headers['X-Tavily-Api-Key'] = credentials.tavilyKey;
  if (credentials.useDemoDb) {
    headers['X-Use-Demo-Db'] = '1';
  } else {
    const dbUrl = buildDbUrl(db);
    if (dbUrl) headers['X-DB-Url'] = dbUrl;
  }
  return headers;
}
