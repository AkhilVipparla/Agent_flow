import { m as motion } from 'framer-motion';
import type { AgentName, AgentStatus } from '../../types/agent';
import { fadeUp } from '../../lib/motion';
import { AgentStatusBadge, AgentStatusDot } from './AgentStatus';

interface AgentMeta {
  label: string;
  description: string;
}

const AGENT_META: Record<AgentName, AgentMeta> = {
  planner: { label: 'Planner', description: 'Decides which agents to use' },
  rag: { label: 'Documents', description: 'Searches your uploaded files' },
  sql: { label: 'Database', description: 'Queries your data' },
  search: { label: 'Web search', description: 'Looks up current information' },
  critic: { label: 'Critic', description: 'Checks the evidence' },
  report: { label: 'Report', description: 'Writes the answer' },
};

interface Props {
  agentName: AgentName;
  status: AgentStatus;
  durationMs?: number;
  isLast?: boolean;
  // The planner decided this agent wasn't needed for the question.
  skipped?: boolean;
}

export function AgentCard({ agentName, status, durationMs, isLast, skipped }: Props) {
  const { label, description } = AGENT_META[agentName];
  return (
    <motion.li variants={fadeUp} className="relative flex gap-3 pb-5 last:pb-0">
      {/* Connector to the next step; fills in once this step is done. */}
      {!isLast && (
        <span className="absolute left-[13px] top-7 h-[calc(100%-1.75rem)] w-0.5 overflow-hidden rounded bg-line/10">
          <motion.span
            className="block w-full bg-ok"
            initial={false}
            animate={{ height: status === 'complete' ? '100%' : '0%' }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </span>
      )}
      <AgentStatusDot status={status} />
      <div className="min-w-0 flex-1 pt-0.5">
        <div className="flex items-center justify-between gap-2">
          <p className={`text-[14px] font-medium ${status === 'idle' ? 'text-muted' : 'text-fg'} ${skipped ? 'opacity-50' : ''}`}>{label}</p>
          <div className="flex items-center gap-2">
            {durationMs !== undefined && durationMs > 0 && (
              <span className="text-xs tabular-nums text-subtle">{(durationMs / 1000).toFixed(1)}s</span>
            )}
            {skipped ? (
              <span className="text-xs font-medium text-subtle">Skipped</span>
            ) : (
              <AgentStatusBadge status={status} />
            )}
          </div>
        </div>
        <p className="text-xs text-subtle">{description}</p>
      </div>
    </motion.li>
  );
}
