import { useState } from 'react';
import {
  CUSTOM_PROVIDER_ID,
  OTHER_MODEL,
  findProvider,
  inferProviderId,
  providers,
} from '../services/providers';
import { DemoDatabasePreview, useDemoDatabase } from '../components/DemoDatabasePreview';
import { apiClient } from '../services/api';
import {
  clearCredentials,
  emptyCredentials,
  loadCredentials,
  saveCredentials,
  type StoredCredentials,
} from '../services/credentials';

interface TestResult {
  llm: { configured: boolean; ok?: boolean; error?: string };
  database: { configured: boolean; ok?: boolean; error?: string; tables?: number; demo?: boolean };
}

const inputClass =
  'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500';
const labelClass = 'block text-xs font-medium text-gray-600 mb-1';

function Field({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      <input
        className={inputClass}
        type={type}
        value={value}
        placeholder={placeholder}
        autoComplete="off"
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      <select className={inputClass} value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

function StatusLine({ name, result }: { name: string; result: TestResult['llm'] | TestResult['database'] }) {
  if (!result.configured) return <p className="text-xs text-gray-500">{name}: not configured</p>;
  if (result.ok) {
    const tables = 'tables' in result && result.tables !== undefined ? ` (${result.tables} tables found)` : '';
    const demo = 'demo' in result && result.demo ? ' to the demo database' : '';
    return <p className="text-xs text-green-700">{name}: connected{demo}{tables}</p>;
  }
  return <p className="text-xs text-red-600">{name}: {result.error ?? 'failed'}</p>;
}

export function SettingsPage() {
  const initial = loadCredentials();
  const [creds, setCreds] = useState<StoredCredentials>(() => {
    const llm = initial.credentials.llm;
    // Older saved settings have no provider: derive it from the base URL.
    return { ...initial.credentials, llm: { ...llm, provider: llm.provider || inferProviderId(llm.baseUrl) } };
  });
  const [customModel, setCustomModel] = useState(() => {
    const p = findProvider(initial.credentials.llm.provider || inferProviderId(initial.credentials.llm.baseUrl));
    const m = initial.credentials.llm.model;
    return !p || (m !== '' && !p.models.includes(m));
  });
  const demoQuery = useDemoDatabase();
  const demoAvailable = demoQuery.data?.available === true;
  const [remember, setRemember] = useState(initial.remembered);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const setLlm = (patch: Partial<StoredCredentials['llm']>) => {
    setCreds((c) => ({ ...c, llm: { ...c.llm, ...patch } }));
    setSaved(false);
  };
  const provider = findProvider(creds.llm.provider);
  const isCustomProvider = creds.llm.provider === CUSTOM_PROVIDER_ID;
  const showModelInput = isCustomProvider || customModel;

  const chooseProvider = (id: string) => {
    const next = findProvider(id);
    // Switching provider resets the model so a model from another provider can't linger.
    setLlm({ provider: id, baseUrl: next ? next.baseUrl : '', model: '' });
    setCustomModel(!next);
  };

  const chooseModel = (value: string) => {
    if (value === OTHER_MODEL) {
      setCustomModel(true);
      setLlm({ model: '' });
    } else {
      setCustomModel(false);
      setLlm({ model: value });
    }
  };

  const setUseDemoDb = (useDemoDb: boolean) => {
    setCreds((c) => ({ ...c, useDemoDb }));
    setSaved(false);
  };

  const setDb = (patch: Partial<StoredCredentials['db']>) => {
    setCreds((c) => ({ ...c, db: { ...c.db, ...patch } }));
    setSaved(false);
  };

  const save = () => {
    saveCredentials(creds, remember);
    setSaved(true);
  };

  const clearAll = () => {
    clearCredentials();
    setCreds(emptyCredentials);
    setRemember(false);
    setResult(null);
    setTestError(null);
    setSaved(false);
  };

  const test = async () => {
    saveCredentials(creds, remember);
    setSaved(true);
    setTesting(true);
    setResult(null);
    setTestError(null);
    try {
      const { data } = await apiClient.post<TestResult>('/settings/test');
      setResult(data);
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setTestError(detail ?? 'Could not reach the server.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="space-y-4">
        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-1">LLM provider</h2>
          <p className="text-sm text-gray-500 mb-4">
            Any OpenAI-compatible API (OpenAI, Gemini, Groq, OpenRouter, a local server...). Your key is kept in
            this browser and sent only with your own requests.
          </p>
          <div className="space-y-3">
            <Select
              label="Provider"
              value={creds.llm.provider}
              onChange={chooseProvider}
              options={[
                ...providers.map((p) => ({ value: p.id, label: p.label })),
                { value: CUSTOM_PROVIDER_ID, label: 'Custom (OpenAI-compatible)' },
              ]}
            />
            {isCustomProvider ? (
              <Field label="Base URL" value={creds.llm.baseUrl} onChange={(v) => setLlm({ baseUrl: v })}
                placeholder="https://my-provider.example.com/v1" />
            ) : (
              <p className="text-xs text-gray-500">Endpoint: {creds.llm.baseUrl}</p>
            )}
            <Field label="API key" type="password" value={creds.llm.apiKey} onChange={(v) => setLlm({ apiKey: v })}
              placeholder={provider?.keyHint ?? 'API key'} />
            {!isCustomProvider && provider && (
              <Select
                label="Model"
                value={customModel ? OTHER_MODEL : creds.llm.model}
                onChange={chooseModel}
                options={[
                  { value: '', label: 'Select a model...' },
                  ...provider.models.map((m) => ({ value: m, label: m })),
                  { value: OTHER_MODEL, label: 'Other (type a model name)' },
                ]}
              />
            )}
            {showModelInput && (
              <Field label={isCustomProvider ? 'Model' : 'Model name'} value={creds.llm.model}
                onChange={(v) => setLlm({ model: v })} placeholder="exact model id from your provider" />
            )}
          </div>
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-1">Database for SQL questions</h2>
          <p className="text-sm text-gray-500 mb-4">
            The SQL agent reads these tables to answer questions. Connect your own PostgreSQL database, or try the
            built-in demo data first.
          </p>

          <div className="mb-4 inline-flex rounded-lg border border-gray-300 p-0.5 text-xs font-medium" role="group"
            aria-label="Database source">
            <button type="button" onClick={() => setUseDemoDb(false)} aria-pressed={!creds.useDemoDb}
              className={`rounded-md px-3 py-1.5 transition-colors ${!creds.useDemoDb ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}>
              My own database
            </button>
            <button type="button" onClick={() => setUseDemoDb(true)} aria-pressed={creds.useDemoDb}
              disabled={!demoAvailable && !demoQuery.isLoading}
              title={!demoAvailable && !demoQuery.isLoading ? 'The demo database is not available on this server' : undefined}
              className={`rounded-md px-3 py-1.5 transition-colors disabled:opacity-40 ${creds.useDemoDb ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}>
              Demo database
            </button>
          </div>

          {creds.useDemoDb ? (
            <DemoDatabasePreview />
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Use a read-only database user. The connection is opened read-only, and any table or column names work.
              </p>
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <Field label="Host" value={creds.db.host} onChange={(v) => setDb({ host: v })}
                    placeholder="db.example.com" />
                </div>
                <Field label="Port" value={creds.db.port} onChange={(v) => setDb({ port: v })} />
                <div className="col-span-3">
                  <Field label="Database" value={creds.db.database} onChange={(v) => setDb({ database: v })} />
                </div>
                <div className="col-span-3 sm:col-span-1">
                  <Field label="User" value={creds.db.user} onChange={(v) => setDb({ user: v })} />
                </div>
                <div className="col-span-3 sm:col-span-2">
                  <Field label="Password" type="password" value={creds.db.password}
                    onChange={(v) => setDb({ password: v })} />
                </div>
              </div>
              <label className="mt-3 flex items-center gap-2 text-sm text-gray-600">
                <input type="checkbox" checked={creds.db.ssl} onChange={(e) => setDb({ ssl: e.target.checked })} />
                Require SSL
              </label>
            </>
          )}
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input type="checkbox" checked={remember}
              onChange={(e) => { setRemember(e.target.checked); setSaved(false); }} />
            Remember on this device (otherwise cleared when you close the tab)
          </label>
          <div className="mt-4 flex flex-wrap gap-2">
            <button onClick={save}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors">
              Save
            </button>
            <button onClick={test} disabled={testing}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors">
              {testing ? 'Testing...' : 'Save & test connection'}
            </button>
            <button onClick={clearAll}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-red-600 hover:bg-red-50 transition-colors">
              Clear my keys
            </button>
          </div>
          <div className="mt-3 space-y-1" aria-live="polite">
            {saved && !result && !testError && <p className="text-xs text-green-700">Saved in this browser.</p>}
            {testError && <p className="text-xs text-red-600">{testError}</p>}
            {result && (
              <>
                <StatusLine name="LLM" result={result.llm} />
                <StatusLine name="Database" result={result.database} />
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
