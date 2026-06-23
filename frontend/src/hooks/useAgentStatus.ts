import { useQuery } from '@tanstack/react-query';
import type { AgentStep } from '../types/agent';
import { getAgentRun } from '../services/researchService';

export function useAgentStatus(runId: string | undefined): { steps: AgentStep[]; isLoading: boolean } {
  const { data, isLoading } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => getAgentRun(runId!),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const run = query.state.data;
      if (!run || run.status === 'complete' || run.status === 'failed') return false;
      return 1500;
    },
  });

  return { steps: data?.steps ?? [], isLoading };
}
