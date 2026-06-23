import type { AgentName, AgentStatus } from '../../types/agent';
import { AgentStatusBadge } from './AgentStatus';

interface AgentMeta {
  label: string;
  icon: string;
}

const AGENT_META: Record<AgentName, AgentMeta> = {
  planner: { label: 'Planner',  icon: '🗺️' },
  rag:     { label: 'RAG',      icon: '📚' },
  sql:     { label: 'SQL',      icon: '🗃️' },
  search:  { label: 'Search',   icon: '🔍' },
  file:    { label: 'File',     icon: '📄' },
  critic:  { label: 'Critic',   icon: '⚖️' },
  report:  { label: 'Report',   icon: '📝' },
};

interface Props {
  agentName: AgentName;
  status: AgentStatus;
  durationMs?: number;
}

export function AgentCard({ agentName, status, durationMs }: Props) {
  const { label, icon } = AGENT_META[agentName];
  return (
    <div className="flex items-center justify-between py-2.5 px-3 rounded-lg bg-white border border-gray-100 shadow-sm">
      <div className="flex items-center gap-2.5">
        <span className="text-sm leading-none">{icon}</span>
        <span className="text-sm font-medium text-gray-800">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {durationMs !== undefined && (
          <span className="text-xs text-gray-400">{(durationMs / 1000).toFixed(1)}s</span>
        )}
        <AgentStatusBadge status={status} />
      </div>
    </div>
  );
}
