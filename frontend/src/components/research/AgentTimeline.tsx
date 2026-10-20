import { m as motion } from 'framer-motion';
import type { AgentStep } from '../../types/agent';
import { stagger } from '../../lib/motion';
import { AgentCard } from '../agents/AgentCard';

interface Props {
  steps: AgentStep[];
  // Agents the planner chose for this question; empty until planning finishes.
  planned?: string[];
}

const OPTIONAL_AGENTS = ['rag', 'sql', 'search'];

export function AgentTimeline({ steps, planned = [] }: Props) {
  return (
    <div className="flex h-full flex-col">
      <h3 className="eyebrow mb-4">Agent timeline</h3>
      {steps.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="px-4 text-center text-sm text-subtle">Run a question to watch the agents work.</p>
        </div>
      ) : (
        <motion.ol variants={stagger(0.05)} initial="hidden" animate="show" className="overflow-auto">
          {steps.map((step, index) => (
            <AgentCard
              key={step.agentName}
              agentName={step.agentName}
              status={step.status}
              durationMs={step.durationMs}
              isLast={index === steps.length - 1}
              skipped={
                planned.length > 0 &&
                step.status === 'idle' &&
                OPTIONAL_AGENTS.includes(step.agentName) &&
                !planned.includes(step.agentName)
              }
            />
          ))}
        </motion.ol>
      )}
    </div>
  );
}
