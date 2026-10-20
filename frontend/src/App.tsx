import { lazy, Suspense, useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { m as motion } from 'framer-motion';
import { LogoMark } from './components/ui/Logo';
import { useAuth } from './lib/auth';
// The sign-in page is what a signed-out visitor sees first, so it ships in the main bundle
// (lazy-loading it would add a request waterfall before first paint).
import { AuthPage } from './pages/AuthPage';

// The signed-in screens are separate chunks, so they only download once someone signs in
// and each page loads when first visited.
const Layout = lazy(() => import('./components/layout/Layout').then((m) => ({ default: m.Layout })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const DocumentsPage = lazy(() => import('./pages/DocumentsPage').then((m) => ({ default: m.DocumentsPage })));
const ReportsPage = lazy(() => import('./pages/ReportsPage').then((m) => ({ default: m.ReportsPage })));
const ResearchPage = lazy(() => import('./pages/ResearchPage').then((m) => ({ default: m.ResearchPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));

function Splash({ waking = false }: { waking?: boolean }) {
  // Only explain a long wait; a quick load should stay just the logo.
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    if (!waking) return;
    const id = window.setTimeout(() => setSlow(true), 4000);
    return () => window.clearTimeout(id);
  }, [waking]);

  return (
    <div className="grid h-screen place-items-center bg-bg px-6" role="status" aria-label="Loading">
      <div className="flex flex-col items-center gap-6 text-center">
        <motion.div
          animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        >
          <LogoMark className="h-12 w-12" />
        </motion.div>
        {slow && (
          <p className="max-w-xs text-sm text-muted">
            Waking up the server. On free hosting the first visit can take up to a minute.
          </p>
        )}
      </div>
    </div>
  );
}

function ServerUnreachable({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="grid h-screen place-items-center bg-bg px-6">
      <div className="max-w-sm text-center">
        <LogoMark className="mx-auto h-10 w-10" />
        <h1 className="display mt-6 text-[28px] leading-tight">Can&rsquo;t reach the server</h1>
        <p className="mt-2 text-sm text-muted">
          The server didn&rsquo;t answer. It may still be starting up, so try again in a moment.
        </p>
        <button
          onClick={onRetry}
          className="mt-6 rounded-md bg-fg px-4 py-2 text-sm font-medium text-bg transition-opacity hover:opacity-90"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

export function App() {
  const { user, isLoading, unreachable, retryConnection } = useAuth();

  if (isLoading) return <Splash waking />;
  if (unreachable) return <ServerUnreachable onRetry={retryConnection} />;

  return (
    <Suspense fallback={<Splash />}>
      {/* Everything lives behind the login; there is no anonymous access. */}
      {!user ? (
        <AuthPage />
      ) : (
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="research" element={<ResearchPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      )}
    </Suspense>
  );
}
