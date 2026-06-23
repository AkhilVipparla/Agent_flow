import type { AgentRunResponse } from '../types/research';
import { buildMockRun, MOCK_RUNS } from './mockData';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function submitResearchQuery(query: string): Promise<AgentRunResponse> {
  await delay(300);
  return buildMockRun(query);
}

export async function listAgentRuns(): Promise<AgentRunResponse[]> {
  await delay(200);
  return MOCK_RUNS;
}

export async function getAgentRun(id: string): Promise<AgentRunResponse> {
  await delay(150);
  const run = MOCK_RUNS.find((r) => r.id === id);
  if (!run) throw new Error(`Run not found: ${id}`);
  return run;
}
