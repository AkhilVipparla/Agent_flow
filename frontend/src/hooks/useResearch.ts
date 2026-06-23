import { useMutation } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { AgentName, AgentStatus, AgentStep } from '../types/agent';
import type { AgentRunResponse } from '../types/research';
import { submitResearchQuery } from '../services/researchService';

const ALL_AGENTS: AgentName[] = ['planner', 'rag', 'sql', 'search', 'file', 'critic', 'report'];

function idleSteps(): AgentStep[] {
  return ALL_AGENTS.map((agentName) => ({ agentName, status: 'idle' as AgentStatus }));
}

function applyStep(
  run: AgentRunResponse,
  name: AgentName,
  status: AgentStatus,
  durationMs?: number,
): AgentRunResponse {
  return {
    ...run,
    steps: run.steps.map((s) =>
      s.agentName === name ? { ...s, status, durationMs } : s,
    ),
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
    onMutate: () => {
      clearTimers();
      setCurrentRun(null);
    },
    onSuccess: (run) => {
      const initial: AgentRunResponse = { ...run, status: 'running', steps: idleSteps() };
      setCurrentRun(initial);

      const schedule = (fn: () => void, ms: number) => {
        timersRef.current.push(setTimeout(fn, ms));
      };

      // Planner starts
      schedule(() => setCurrentRun((r) => r && applyStep(r, 'planner', 'running')), 100);

      // Planner done → evidence agents start in parallel
      schedule(() => setCurrentRun((r) => {
        if (!r) return r;
        let s = applyStep(r, 'planner', 'complete', 820);
        s = applyStep(s, 'rag', 'running');
        s = applyStep(s, 'sql', 'running');
        s = applyStep(s, 'search', 'running');
        return s;
      }), 1000);

      // Evidence agents done → critic starts
      schedule(() => setCurrentRun((r) => {
        if (!r) return r;
        let s = applyStep(r, 'rag', 'complete', 1760);
        s = applyStep(s, 'sql', 'complete', 1430);
        s = applyStep(s, 'search', 'complete', 2080);
        s = applyStep(s, 'critic', 'running');
        return s;
      }), 2900);

      // Critic done → report starts
      schedule(() => setCurrentRun((r) => {
        if (!r) return r;
        let s = applyStep(r, 'critic', 'complete', 560);
        s = applyStep(s, 'report', 'running');
        return s;
      }), 3700);

      // Report done → run complete, reveal all data
      schedule(() => setCurrentRun((r) => {
        if (!r) return r;
        const s = applyStep(r, 'report', 'complete', 1180);
        return { ...s, status: 'complete' };
      }), 4900);
    },
    onError: () => {
      clearTimers();
    },
  });

  const submitQuery = useCallback((query: string) => mutate(query), [mutate]);

  const isRunning = isPending || currentRun?.status === 'running';

  return { submitQuery, currentRun, isRunning, error };
}
