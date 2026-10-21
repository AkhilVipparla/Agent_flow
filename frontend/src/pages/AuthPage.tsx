import { useEffect, useState, type FormEvent } from 'react';
import { AnimatePresence, m as motion, useReducedMotion } from 'framer-motion';
import { useAuth } from '../lib/auth';
import { easeApple, spring } from '../lib/motion';
import { errorMessage } from '../services/authService';
import { Button } from '../components/ui/Button';
import { Field } from '../components/ui/Field';
import { Logo } from '../components/ui/Logo';
import { ThemeToggle } from '../components/ui/ThemeToggle';

type Mode = 'signin' | 'signup';

const STAGES = [
  { n: '01', title: 'Plan', detail: 'Your question is broken into steps and sources.' },
  { n: '02', title: 'Gather', detail: 'Documents, your database and the web, searched in parallel.' },
  { n: '03', title: 'Check', detail: 'A critic scores the evidence and sends it back if it falls short.' },
  { n: '04', title: 'Report', detail: 'A structured answer, with every claim cited.' },
] as const;

const STAGE_MS = 2600;

/** The four steps of a run, as an indexed list. The active step advances on its own. */
function Process() {
  const reduce = useReducedMotion();
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (reduce) return;
    const id = window.setInterval(() => setActive((s) => (s + 1) % STAGES.length), STAGE_MS);
    return () => window.clearInterval(id);
  }, [reduce]);

  return (
    <ol aria-label="How a research run works" className="border-t border-white/15">
      {STAGES.map((stage, index) => {
        const on = index === active;
        return (
          <li key={stage.n} className="relative border-b border-white/15">
            {/* Progress rule: fills across the active row while its time runs. */}
            {on && !reduce && (
              <motion.span
                key={`${active}-bar`}
                className="absolute left-0 top-[-1px] h-px bg-[#FF5A1F]"
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: STAGE_MS / 1000, ease: 'linear' }}
              />
            )}
            <div className={`flex items-baseline gap-4 py-3.5 [@media(max-height:760px)]:py-2 transition-opacity duration-500 ${on ? 'opacity-100' : 'opacity-40'}`}>
              <span className={`w-6 font-mono text-[11px] transition-colors ${on ? 'text-[#FF7A45]' : 'text-white/70'}`}>
                {stage.n}
              </span>
              <span className="display w-24 flex-shrink-0 text-[26px] leading-none">{stage.title}</span>
              <span className="text-[14px] leading-snug text-white/70">{stage.detail}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

const headlineWords = ['Ask', 'the', 'hard', 'question.'];
const accentWords = ['Agents', 'do', 'the', 'digging.'];

function BrandPanel() {
  const word = (w: string, i: number, extra = '') => (
    <span key={w + i} className="inline-block overflow-hidden pb-[0.08em] align-bottom">
      <motion.span
        className={`inline-block ${extra}`}
        initial={{ y: '105%' }}
        animate={{ y: '0%' }}
        transition={{ duration: 0.9, ease: easeApple, delay: 0.15 + i * 0.07 }}
      >
        {w}&nbsp;
      </motion.span>
    </span>
  );

  return (
    <div className="relative isolate flex flex-col overflow-hidden bg-[#0E0E0C] px-8 py-8 text-[#F0EDE4] sm:px-12 lg:min-h-screen lg:px-16 lg:py-9">
      {/* Column rules: the visible grid behind everything. */}
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-[0.07]"
        style={{ backgroundImage: 'repeating-linear-gradient(to right, #F0EDE4 0 1px, transparent 1px 25%)' }}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <svg viewBox="0 0 64 64" className="h-8 w-8" aria-hidden="true">
            <rect width="64" height="64" rx="10" fill="#F0EDE4" />
            <path d="M20 32l24-13M20 32l24 13" stroke="#0E0E0C" strokeWidth="3" strokeLinecap="round" fill="none" />
            <circle cx="19" cy="32" r="6" fill="#0E0E0C" />
            <circle cx="45" cy="18" r="6" fill="#0E0E0C" />
            <circle cx="45" cy="46" r="6" fill="#FF5A1F" />
          </svg>
          <span className="display text-[24px] leading-none">AgentFlow</span>
        </div>
        <span className="hidden font-mono text-[11px] uppercase tracking-[0.14em] text-white/50 sm:block">
          Agentic research
        </span>
      </div>

      <div className="my-auto py-8 lg:py-6">
        <h1 className="display text-[clamp(2.5rem,min(5.4vw,9vh),5.1rem)] leading-[0.95] tracking-[-0.02em]">
          <span className="block">{headlineWords.map((w, i) => word(w, i))}</span>
          <span className="block italic text-[#FF7A45]">
            {accentWords.map((w, i) => word(w, i + headlineWords.length))}
          </span>
        </h1>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: easeApple, delay: 0.7 }}
          className="mt-7 hidden max-w-md text-[17px] leading-relaxed text-white/65 lg:block lg:[@media(max-height:760px)]:hidden"
        >
          AgentFlow plans the research, searches your documents, queries your data and the web,
          checks its own work, and writes up what it found. With sources.
        </motion.p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: easeApple, delay: 0.9 }}
        className="hidden lg:block"
      >
        <Process />
        <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.14em] text-white/45">
          Private by default · Works with any table names · Bring your own keys
        </p>
      </motion.div>
    </div>
  );
}

export function AuthPage() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState<Mode>('signin');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [shake, setShake] = useState(0);

  const isSignup = mode === 'signup';

  const switchMode = (next: Mode) => {
    setMode(next);
    setError(null);
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      setShake((n) => n + 1);
      return;
    }
    if (isSignup && password.length < 8) {
      setError('Password must be at least 8 characters.');
      setShake((n) => n + 1);
      return;
    }
    setSubmitting(true);
    try {
      if (isSignup) await signup(email, password, name);
      else await login(email, password);
    } catch (err) {
      setError(errorMessage(err));
      setShake((n) => n + 1);
    } finally {
      setSubmitting(false);
    }
  };

  const tabs: { value: Mode; label: string }[] = [
    { value: 'signin', label: 'Sign in' },
    { value: 'signup', label: 'Create account' },
  ];

  return (
    <div className="grid min-h-screen bg-bg lg:grid-cols-2">
      <BrandPanel />

      <div className="relative flex flex-col px-6 py-8 sm:px-12">
        <div className="flex items-center justify-between lg:justify-end">
          <Logo className="lg:hidden" />
          <ThemeToggle />
        </div>

        <div className="mx-auto flex w-full max-w-[400px] flex-1 flex-col justify-center py-10">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: easeApple, delay: 0.1 }}
          >
            <div role="tablist" aria-label="Sign in or create an account" className="mb-8 flex gap-6 border-b border-line/15">
              {tabs.map((tab) => {
                const on = tab.value === mode;
                return (
                  <button
                    key={tab.value}
                    role="tab"
                    type="button"
                    aria-selected={on}
                    onClick={() => switchMode(tab.value)}
                    className={`relative pb-3 text-[15px] transition-colors ${on ? 'font-medium text-fg' : 'text-muted hover:text-fg'}`}
                  >
                    {tab.label}
                    {on && (
                      <motion.span
                        layoutId="auth-tab"
                        transition={spring}
                        className="absolute inset-x-0 -bottom-px h-0.5 bg-accent-solid"
                      />
                    )}
                  </button>
                );
              })}
            </div>

            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={mode}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.22 }}
                className="mb-7"
              >
                <h2 className="display text-[42px] leading-[1]">{isSignup ? 'Create your account' : 'Welcome back'}</h2>
                <p className="mt-2 text-[15px] text-muted">
                  {isSignup ? 'Your documents and reports stay private to you.' : 'Sign in to continue your research.'}
                </p>
              </motion.div>
            </AnimatePresence>

            <motion.form
              key={shake}
              onSubmit={onSubmit}
              noValidate
              animate={shake ? { x: [0, -8, 8, -5, 5, 0] } : undefined}
              transition={{ duration: 0.4 }}
              className="space-y-4"
            >
              <AnimatePresence initial={false}>
                {isSignup && (
                  <motion.div
                    key="name"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.28, ease: easeApple }}
                    className="overflow-hidden"
                  >
                    <div className="pb-1 pt-0.5">
                      <Field label="Name" value={name} onChange={setName} autoComplete="name" placeholder="Your name (optional)" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" placeholder="you@company.com" />
              <Field
                label="Password"
                type="password"
                value={password}
                onChange={setPassword}
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                placeholder={isSignup ? 'At least 8 characters' : 'Your password'}
              />

              <AnimatePresence>
                {error && (
                  <motion.p
                    role="alert"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden rounded-md border border-danger/30 px-3.5 py-2.5 text-[13px] text-danger"
                  >
                    {error}
                  </motion.p>
                )}
              </AnimatePresence>

              <Button type="submit" variant="signal" size="lg" loading={submitting} className="w-full">
                {isSignup ? 'Create account' : 'Sign in'}
                <span aria-hidden="true">&rarr;</span>
              </Button>
            </motion.form>
          </motion.div>
        </div>

        <p className="text-center font-mono text-[11px] uppercase tracking-[0.12em] text-subtle">
          Passwords are stored only as salted hashes
        </p>
      </div>
    </div>
  );
}
