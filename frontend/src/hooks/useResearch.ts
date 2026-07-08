import { useMutation } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { AgentName, AgentStatus, AgentStep } from '../types/agent';
import type { AgentRunResponse } from '../types/research';
import { submitResearchQuery } from '../services/researchService';

const ALL_AGENTS: AgentName[] = ['planner', 'rag', 'sql', 'search', 'file', 'critic', 'report'];

function idleSteps(): AgentStep[] {
  return ALL_AGENTS.map((agentName) => ({ agentName, status: 'idle' as AgentStatus }));
}

function pendingRun(query: string): AgentRunResponse {
  return {
    id: 'pending',
    query,
    agentsExecuted: [],
    steps: idleSteps(),
    evidence: {
      retrievedDocuments: [],
      sqlResults: [],
      searchResults: [],
      citations: [],
      confidenceScore: 0,
    },
    finalReport: '',
    status: 'running',
    createdAt: new Date().toISOString(),
  };
}

function applyStep(run: AgentRunResponse, name: AgentName, status: AgentStatus): AgentRunResponse {
  return {
    ...run,
    steps: run.steps.map((s) => (s.agentName === name ? { ...s, status } : s)),
  };
}

export function useResearch() {
  const [currentRun, setCurrentRun] = useState<AgentRunResponse | null>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  }, []);

  useEffect(() => () => { timersRef.current.forEach(clearTimeout); }, []);

  const { mutate, isPending, error } = useMutation({
    mutationFn: submitResearchQuery,
    // While the backend runs the graph, show an indeterminate timeline:
    // planner first, then the evidence agents spin until the response lands.
    onMutate: (query: string) => {
      clearTimers();
      setCurrentRun(pendingRun(query));

      const schedule = (fn: () => void, ms: number) => {
        timersRef.current.push(setTimeout(fn, ms));
      };

      schedule(() => setCurrentRun((r) => r && applyStep(r, 'planner', 'running')), 100);
      schedule(() => setCurrentRun((r) => {
        if (!r) return r;
        let s = applyStep(r, 'planner', 'complete');
        s = applyStep(s, 'rag', 'running');
        s = applyStep(s, 'sql', 'running');
        s = applyStep(s, 'search', 'running');
        return s;
      }), 1500);
    },
    // Replace the placeholder with the real run: actual steps, durations,
    // evidence, and the generated report.
    onSuccess: (run) => {
      clearTimers();
      setCurrentRun(run);
    },
    onError: () => {
      clearTimers();
      setCurrentRun((r) => {
        if (!r) return r;
        return {
          ...r,
          status: 'failed',
          steps: r.steps.map((s) =>
            s.status === 'running' ? { ...s, status: 'failed' as AgentStatus } : s,
          ),
        };
      });
    },
  });

  const submitQuery = useCallback((query: string) => mutate(query), [mutate]);

  const isRunning = isPending || currentRun?.status === 'running';

  return { submitQuery, currentRun, isRunning, error };
}
