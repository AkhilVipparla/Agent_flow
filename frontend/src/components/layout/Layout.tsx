import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { m as motion } from 'framer-motion';
import { useAuth } from '../../lib/auth';
import { spring } from '../../lib/motion';
import { Logo } from '../ui/Logo';
import { ThemeToggle } from '../ui/ThemeToggle';
import {
  DashboardIcon,
  DocumentsIcon,
  LogoutIcon,
  ReportsIcon,
  ResearchIcon,
  SettingsIcon,
} from '../ui/icons';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', Icon: DashboardIcon },
  { to: '/research', label: 'Research', Icon: ResearchIcon },
  { to: '/reports', label: 'Reports', Icon: ReportsIcon },
  { to: '/documents', label: 'Documents', Icon: DocumentsIcon },
  { to: '/settings', label: 'Settings', Icon: SettingsIcon },
] as const;

function initials(name: string, email: string): string {
  const source = name.trim() || email;
  const parts = source.split(/[\s@._-]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? '?') + (parts[1]?.[0] ?? '')).toUpperCase();
}

function UserCard() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <div className="flex items-center gap-3 border-t border-line/15 pt-4">
      <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-fg font-mono text-[12px] font-medium text-bg">
        {initials(user.name, user.email)}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium leading-tight">{user.name || 'Signed in'}</p>
        <p className="truncate font-mono text-[11px] text-subtle">{user.email}</p>
      </div>
      <button
        onClick={() => void logout()}
        aria-label="Sign out"
        title="Sign out"
        className="grid h-8 w-8 flex-shrink-0 place-items-center rounded-md text-subtle transition-colors hover:bg-line/10 hover:text-fg"
      >
        <LogoutIcon className="h-[18px] w-[18px]" />
      </button>
    </div>
  );
}

export function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="h-screen overflow-hidden bg-bg">
      {/* Desktop sidebar: an indexed list, separated by hairlines. */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line/15 bg-bg px-6 py-6 md:flex">
        <Logo />
        <nav className="mt-10 flex-1" aria-label="Main">
          <ul className="border-t border-line/15">
            {NAV_ITEMS.map(({ to, label }, index) => (
              <li key={to} className="border-b border-line/15">
                <NavLink to={to} end={to === '/'} className="block">
                  {({ isActive }) => (
                    <span
                      className={`relative flex items-baseline gap-3 py-3 text-[15px] transition-colors ${
                        isActive ? 'font-medium text-fg' : 'text-muted hover:text-fg'
                      }`}
                    >
                      <span className="w-5 font-mono text-[11px] text-subtle">{String(index + 1).padStart(2, '0')}</span>
                      {label}
                      {isActive && (
                        <motion.span
                          layoutId="nav-marker"
                          transition={spring}
                          className="absolute right-0 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-accent-solid"
                        />
                      )}
                    </span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="eyebrow">Theme</span>
            <ThemeToggle />
          </div>
          <UserCard />
        </div>
      </aside>

      {/* Mobile bottom tab bar */}
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-30 flex justify-around border-t border-line/15 bg-bg px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 md:hidden"
      >
        {NAV_ITEMS.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex min-w-[56px] flex-col items-center gap-0.5 px-2 py-1 text-[10px] font-medium transition-colors ${
                isActive ? 'text-fg' : 'text-subtle'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`h-[22px] w-[22px] ${isActive ? 'text-accent' : ''}`} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <main className="h-full overflow-y-auto pb-20 md:pb-0 md:pl-64">
        {/* A CSS animation, not JS: it restarts when the key (route) changes and always
            finishes, so a page can never be left stuck at opacity 0. */}
        <div key={pathname} className="page-enter min-h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
