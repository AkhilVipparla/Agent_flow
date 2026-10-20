import type { AgentName, AgentStatus } from '../../types/agent';
import { AgentStatusBadge } from './AgentStatus';

interface AgentMeta {
  label: string;
}

const AGENT_META: Record<AgentName, AgentMeta> = {
  planner: { label: 'Planner' },
  rag:     { label: 'RAG' },
  sql:     { label: 'SQL' },
  search:  { label: 'Search' },
  critic:  { label: 'Critic' },
  report:  { label: 'Report' },
};

interface Props {
  agentName: AgentName;
  status: AgentStatus;
  durationMs?: number;
}

export function AgentCard({ agentName, status, durationMs }: Props) {
  const { label } = AGENT_META[agentName];
  return (
    <div className="flex items-center justify-between py-2.5 px-3 rounded-lg bg-white border border-gray-100 shadow-sm">
      <div className="flex items-center gap-2.5">
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
