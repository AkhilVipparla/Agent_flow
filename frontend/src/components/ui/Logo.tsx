import { clsx } from 'clsx';

/** Three nodes joined by lines: a question fanning out to its sources. One node carries the signal color. */
export function LogoMark({ className }: { className?: string }) {
  const paper = { fill: 'rgb(var(--bg))' };
  return (
    <svg viewBox="0 0 64 64" className={clsx('h-8 w-8 text-fg', className)} aria-hidden="true">
      <rect width="64" height="64" rx="10" fill="currentColor" />
      <path d="M20 32l24-13M20 32l24 13" style={{ stroke: 'rgb(var(--bg))' }} strokeWidth="3" strokeLinecap="round" fill="none" />
      <circle cx="19" cy="32" r="6" style={paper} />
      <circle cx="45" cy="18" r="6" style={paper} />
      <circle cx="45" cy="46" r="6" fill="#FF5A1F" />
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <div className={clsx('flex items-center gap-2.5', className)}>
      <LogoMark />
      <span className="display text-[24px] leading-none">AgentFlow</span>
    </div>
  );
}
