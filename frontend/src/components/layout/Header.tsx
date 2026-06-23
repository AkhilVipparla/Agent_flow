import { useLocation } from 'react-router-dom';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/research': 'Research Workspace',
  '/reports': 'Reports',
  '/documents': 'Documents',
  '/settings': 'Settings',
};

export function Header() {
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? 'AgentFlow AI';

  return (
    <header className="flex items-center justify-between h-14 px-6 border-b border-gray-200 bg-white flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
          <span className="text-white text-xs font-bold select-none">AF</span>
        </div>
        <span className="text-sm font-semibold text-gray-900">{title}</span>
      </div>
      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
        <span className="text-indigo-600 text-xs font-semibold select-none">AV</span>
      </div>
    </header>
  );
}
