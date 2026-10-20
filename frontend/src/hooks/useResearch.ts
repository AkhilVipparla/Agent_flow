import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useState } from 'react';
import type { AgentName, AgentStatus, AgentStep } from '../types/agent';
import type { AgentRunResponse } from '../types/research';
import { getAgentRun, submitResearchQuery } from '../services/researchService';

const ALL_AGENTS: AgentName[] = ['planner', 'rag', 'sql', 'search', 'critic', 'report'];
const ACTIVE_RUN_KEY = 'agentflow.activeRunId';
const POLL_MS = 1500;

function readActiveRunId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_RUN_KEY);
  } catch {
    return null;
  }
}

function writeActiveRunId(id: string | null) {
  try {
    if (id) localStorage.setItem(ACTIVE_RUN_KEY, id);
    else localStorage.removeItem(ACTIVE_RUN_KEY);
  } catch {
    // Storage unavailable (private mode); the run still works for this session.
  }
}

// The backend only reports agents that have started; show the rest as idle so
// the timeline always lists the full pipeline.
function withIdleSteps(run: AgentRunResponse): AgentRunResponse {
  const byName = new Map(run.steps.map((s) => [s.agentName, s]));
  const steps: AgentStep[] = ALL_AGENTS.map(
    (agentName) => byName.get(agentName) ?? { agentName, status: 'idle' as AgentStatus },
  );
  return { ...run, steps };
}

/**
 * Research runs execute on the server as a background job, so navigating away
 * never stops one. The active run id is remembered in localStorage and the run
 * is polled by id; the TanStack Query cache outlives the page, so coming back
 * shows live progress (or the finished report) immediately.
 */
export function useResearch() {
  const queryClient = useQueryClient();
  const [activeRunId, setActiveRunId] = useState<string | null>(readActiveRunId);

  const setActive = useCallback((id: string | null) => {
    writeActiveRunId(id);
    setActiveRunId(id);
  }, []);

  const { data: run, error: pollError } = useQuery({
    queryKey: ['run', activeRunId],
    queryFn: () => getAgentRun(activeRunId!),
    enabled: Boolean(activeRunId),
    refetchInterval: (query) => (query.state.data?.status === 'running' ? POLL_MS : false),
    retry: (count, err) => !(err as { response?: { status?: number } })?.response && count < 3,
  });

  // A remembered id the server no longer knows about (e.g. DB wiped): forget it.
  const notFound = (pollError as { response?: { status?: number } } | null)?.response?.status === 404;
  useEffect(() => {
    if (notFound) setActive(null);
  }, [notFound, setActive]);

  const { mutate, isPending, error: submitError } = useMutation({
    mutationFn: submitResearchQuery,
    onSuccess: (started) => {
      queryClient.setQueryData(['run', started.id], started);
      setActive(started.id);
    },
  });

  const submitQuery = useCallback((query: string) => mutate(query), [mutate]);

  const currentRun = run ? withIdleSteps(run) : null;
  const isRunning = isPending || run?.status === 'running';

  return { submitQuery, currentRun, isRunning, error: submitError };
}
