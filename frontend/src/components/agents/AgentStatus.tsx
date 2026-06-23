import type { AgentStatus } from '../../types/agent';

interface StatusConfig {
  label: string;
  className: string;
}

const CONFIG: Record<AgentStatus, StatusConfig> = {
  idle:     { label: 'Idle',     className: 'bg-gray-100 text-gray-400' },
  running:  { label: 'Running',  className: 'bg-blue-100 text-blue-700 animate-pulse' },
  complete: { label: 'Complete', className: 'bg-green-100 text-green-700' },
  failed:   { label: 'Failed',   className: 'bg-red-100 text-red-700' },
  retrying: { label: 'Retrying', className: 'bg-amber-100 text-amber-700' },
};

interface Props {
  status: AgentStatus;
}

export function AgentStatusBadge({ status }: Props) {
  const { label, className } = CONFIG[status];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${className}`}>
      {label}
    </span>
  );
}
