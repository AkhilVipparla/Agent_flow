import { clsx } from 'clsx';

type RunStatus = 'running' | 'complete' | 'failed';

const STYLES: Record<RunStatus, string> = {
  running: 'bg-accent-solid/15 text-accent',
  complete: 'bg-ok/12 text-ok',
  failed: 'bg-danger/12 text-danger',
};

const LABELS: Record<RunStatus, string> = {
  running: 'Running',
  complete: 'Complete',
  failed: 'Failed',
};

export function StatusPill({ status }: { status: RunStatus }) {
  return (
    <span className={clsx('inline-flex items-center gap-1.5 rounded-sm px-2 py-1 font-mono text-[11px] font-medium uppercase tracking-wider', STYLES[status])}>
      <span className={clsx('h-1.5 w-1.5 rounded-full bg-current', status === 'running' && 'animate-pulse')} />
      {LABELS[status]}
    </span>
  );
}
