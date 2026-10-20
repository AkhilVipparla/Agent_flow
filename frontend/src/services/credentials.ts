// Visitor-supplied LLM key and database login. Kept only in this browser and sent
// as request headers; the server never stores them.

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
  // Use the server's shared read-only demo database instead of the visitor's own.
  useDemoDb: boolean;
}

const STORAGE_KEY = 'agentflow.credentials';

export const emptyCredentials: StoredCredentials = {
  llm: { provider: 'openai', baseUrl: 'https://api.openai.com/v1', apiKey: '', model: '' },
  db: { host: '', port: '5432', database: '', user: '', password: '', ssl: true },
  useDemoDb: false,
};

// sessionStorage clears when the tab closes (safe on shared computers);
// localStorage is used only if the visitor opts in to "remember on this device".
function readFrom(storage: Storage): StoredCredentials | null {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    return raw ? { ...emptyCredentials, ...(JSON.parse(raw) as Partial<StoredCredentials>) } : null;
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
  clearCredentials();
  try {
    (remember ? window.localStorage : window.sessionStorage).setItem(STORAGE_KEY, JSON.stringify(credentials));
  } catch {
    /* storage blocked: credentials simply won't persist */
  }
}

export function clearCredentials(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
    window.sessionStorage.removeItem(STORAGE_KEY);
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

const VISITOR_KEY = 'agentflow.visitorId';
let memoryVisitorId: string | null = null;

// A random per-browser ID. The server treats it as the owner of every document,
// run and report this browser creates, so it must stay private and stable.
// (Unrelated to "Clear my keys": clearing keys must not orphan the visitor's data.)
export function getVisitorId(): string {
  try {
    const existing = window.localStorage.getItem(VISITOR_KEY);
    if (existing) return existing;
    const created = crypto.randomUUID();
    window.localStorage.setItem(VISITOR_KEY, created);
    return created;
  } catch {
    // Storage blocked: keep one ID for this page load so requests stay consistent.
    memoryVisitorId ??= crypto.randomUUID();
    return memoryVisitorId;
  }
}

export function credentialHeaders(): Record<string, string> {
  const { credentials } = loadCredentials();
  const headers: Record<string, string> = { 'X-Visitor-Id': getVisitorId() };
  const { llm, db } = credentials;
  if (llm.apiKey) {
    headers['X-LLM-Api-Key'] = llm.apiKey;
    if (llm.baseUrl) headers['X-LLM-Base-Url'] = llm.baseUrl;
    if (llm.model) headers['X-LLM-Model'] = llm.model;
  }
  if (credentials.useDemoDb) {
    headers['X-Use-Demo-Db'] = '1';
  } else {
    const dbUrl = buildDbUrl(db);
    if (dbUrl) headers['X-DB-Url'] = dbUrl;
  }
  return headers;
}
