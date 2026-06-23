import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '▣' },
  { to: '/research', label: 'Research', icon: '◎' },
  { to: '/reports', label: 'Reports', icon: '◧' },
  { to: '/documents', label: 'Documents', icon: '◫' },
  { to: '/settings', label: 'Settings', icon: '◈' },
] as const;

export function Sidebar() {
  return (
    <nav className="w-56 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col py-5">
      <p className="px-5 mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
        Navigation
      </p>
      <ul className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`
              }
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
