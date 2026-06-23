import type { AgentStep } from '../../types/agent';
import { AgentCard } from '../agents/AgentCard';

interface Props {
  steps: AgentStep[];
}

export function AgentTimeline({ steps }: Props) {
  return (
    <div className="flex flex-col h-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Agent Timeline</h3>
      {steps.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-gray-400 text-center px-4">Submit a query to see agent execution.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-2 overflow-auto">
          {steps.map((step) => (
            <AgentCard
              key={step.agentName}
              agentName={step.agentName}
              status={step.status}
              durationMs={step.durationMs}
            />
          ))}
        </div>
      )}
    </div>
  );
}
