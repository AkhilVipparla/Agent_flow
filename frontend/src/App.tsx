import { lazy, Suspense } from 'react';
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

function Splash() {
  return (
    <div className="grid h-screen place-items-center bg-bg" role="status" aria-label="Loading">
      <motion.div
        animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
      >
        <LogoMark className="h-12 w-12" />
      </motion.div>
    </div>
  );
}

export function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <Splash />;

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
