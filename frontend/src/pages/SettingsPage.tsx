import { useState, type ReactNode } from 'react';
import { m as motion } from 'framer-motion';
import { DemoDatabasePreview, useDemoDatabase } from '../components/DemoDatabasePreview';
import { Button } from '../components/ui/Button';
import { Field, SelectField } from '../components/ui/Field';
import { CheckIcon, CloseIcon } from '../components/ui/icons';
import { PageHeader } from '../components/ui/PageHeader';
import { Segmented } from '../components/ui/Segmented';
import { fadeUp, stagger } from '../lib/motion';
import { apiClient } from '../services/api';
import { errorMessage } from '../services/authService';
import {
  clearCredentials,
  emptyCredentials,
  loadCredentials,
  saveCredentials,
  type StoredCredentials,
} from '../services/credentials';
import {
  CUSTOM_PROVIDER_ID,
  OTHER_MODEL,
  findProvider,
  inferProviderId,
  providers,
} from '../services/providers';

interface CheckResult {
  configured: boolean;
  ok?: boolean;
  error?: string;
  tables?: number;
  demo?: boolean;
}

interface TestResult {
  llm: CheckResult;
  search: CheckResult;
  database: CheckResult;
}

function Section({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <motion.section variants={fadeUp} className="card p-6">
      <h2 className="text-[19px] font-semibold">{title}</h2>
      <p className="mb-5 mt-1 text-sm text-muted">{description}</p>
      {children}
    </motion.section>
  );
}

function StatusLine({ name, result }: { name: string; result: CheckResult }) {
  if (!result.configured) {
    return <p className="text-[13px] text-subtle">{name}: not set up</p>;
  }
  const ok = result.ok === true;
  const detail = ok
    ? `connected${result.demo ? ' to the demo database' : ''}${result.tables !== undefined ? ` (${result.tables} tables)` : ''}`
    : result.error ?? 'failed';
  return (
    <motion.p
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-start gap-2 text-[13px] ${ok ? 'text-ok' : 'text-danger'}`}
    >
      {ok ? <CheckIcon className="mt-0.5 h-4 w-4 flex-shrink-0" /> : <CloseIcon className="mt-0.5 h-4 w-4 flex-shrink-0" />}
      <span>
        <span className="font-medium">{name}:</span> {detail}
      </span>
    </motion.p>
  );
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

  const touch = () => setSaved(false);
  const setLlm = (patch: Partial<StoredCredentials['llm']>) => {
    setCreds((c) => ({ ...c, llm: { ...c.llm, ...patch } }));
    touch();
  };
  const setDb = (patch: Partial<StoredCredentials['db']>) => {
    setCreds((c) => ({ ...c, db: { ...c.db, ...patch } }));
    touch();
  };
  const setUseDemoDb = (useDemoDb: boolean) => {
    setCreds((c) => ({ ...c, useDemoDb }));
    touch();
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

  const save = () => {
    saveCredentials(creds, remember);
    setSaved(true);
  };

  const clearAll = () => {
    clearCredentials();
    setCreds(emptyCredentials);
    setCustomModel(false);
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
      setTestError(errorMessage(err, 'The connection test failed.'));
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-6 py-10 md:px-10">
      <PageHeader
        title="Settings"
        subtitle="Bring your own keys. They stay in this browser, under your account, and are sent only with your own requests."
      />

      <motion.div variants={stagger(0.08)} initial="hidden" animate="show" className="space-y-5">
        <Section title="AI model" description="Any OpenAI-compatible provider: OpenAI, Claude, Gemini, Groq, OpenRouter, or your own server.">
          <div className="space-y-4">
            <SelectField
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
              <p className="text-xs text-subtle">Endpoint: {creds.llm.baseUrl}</p>
            )}
            <Field label="API key" type="password" value={creds.llm.apiKey} onChange={(v) => setLlm({ apiKey: v })}
              placeholder={provider?.keyHint ?? 'API key'} />
            {!isCustomProvider && provider && (
              <SelectField
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
        </Section>

        <Section
          title="Web search"
          description="Add a Tavily key to let the agents look things up on the web. Without one, web search is simply skipped."
        >
          <Field
            label="Tavily API key"
            type="password"
            value={creds.tavilyKey}
            onChange={(v) => { setCreds((c) => ({ ...c, tavilyKey: v })); touch(); }}
            placeholder="tvly-..."
            hint="Get a free key at tavily.com."
          />
        </Section>

        <Section
          title="Database for SQL questions"
          description="The SQL agent reads these tables to answer questions. Connect your own PostgreSQL database, or try the demo data first."
        >
          <Segmented<'own' | 'demo'>
            label="Database source"
            value={creds.useDemoDb ? 'demo' : 'own'}
            onChange={(v) => setUseDemoDb(v === 'demo')}
            className="mb-5"
            options={[
              { value: 'own', label: 'My own database' },
              {
                value: 'demo',
                label: 'Demo database',
                disabled: !demoAvailable && !demoQuery.isLoading,
                title: !demoAvailable && !demoQuery.isLoading ? 'The demo database is not available on this server' : undefined,
              },
            ]}
          />

          {creds.useDemoDb ? (
            <DemoDatabasePreview />
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted">
                Use a read-only database user. The connection is opened read-only, and any table or column names work.
              </p>
              <div className="grid grid-cols-3 gap-4">
                <Field className="col-span-2" label="Host" value={creds.db.host} onChange={(v) => setDb({ host: v })}
                  placeholder="db.example.com" />
                <Field label="Port" value={creds.db.port} onChange={(v) => setDb({ port: v })} />
                <Field className="col-span-3" label="Database" value={creds.db.database}
                  onChange={(v) => setDb({ database: v })} />
                <Field className="col-span-3 sm:col-span-1" label="User" value={creds.db.user}
                  onChange={(v) => setDb({ user: v })} />
                <Field className="col-span-3 sm:col-span-2" label="Password" type="password" value={creds.db.password}
                  onChange={(v) => setDb({ password: v })} />
              </div>
              <label className="flex cursor-pointer items-center gap-2.5 text-sm text-muted">
                <input type="checkbox" className="h-4 w-4 accent-[rgb(var(--accent))]" checked={creds.db.ssl}
                  onChange={(e) => setDb({ ssl: e.target.checked })} />
                Require SSL
              </label>
            </div>
          )}
        </Section>

        <motion.section variants={fadeUp} className="card p-6">
          <label className="flex cursor-pointer items-center gap-2.5 text-sm text-muted">
            <input type="checkbox" className="h-4 w-4 accent-[rgb(var(--accent))]" checked={remember}
              onChange={(e) => { setRemember(e.target.checked); touch(); }} />
            Remember on this device (otherwise cleared when you close the tab)
          </label>

          <div className="mt-5 flex flex-wrap gap-2.5">
            <Button onClick={save}>Save</Button>
            <Button variant="secondary" onClick={test} loading={testing}>Save and test</Button>
            <Button variant="danger" onClick={clearAll}>Clear my keys</Button>
          </div>

          <div className="mt-4 space-y-1.5" aria-live="polite">
            {saved && !result && !testError && (
              <p className="flex items-center gap-2 text-[13px] text-ok">
                <CheckIcon className="h-4 w-4" /> Saved in this browser.
              </p>
            )}
            {testError && <p className="text-[13px] text-danger">{testError}</p>}
            {result && (
              <>
                <StatusLine name="AI model" result={result.llm} />
                <StatusLine name="Web search" result={result.search} />
                <StatusLine name="Database" result={result.database} />
              </>
            )}
          </div>
        </motion.section>
      </motion.div>
    </div>
  );
}
