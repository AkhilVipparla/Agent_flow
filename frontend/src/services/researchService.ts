import type { AgentRunResponse } from '../types/research';
import { apiClient } from './api';

export async function submitResearchQuery(query: string): Promise<AgentRunResponse> {
  const { data } = await apiClient.post<AgentRunResponse>('/query', { query });
  return data;
}

export async function listAgentRuns(): Promise<AgentRunResponse[]> {
  const { data } = await apiClient.get<AgentRunResponse[]>('/runs');
  return data;
}

export async function getAgentRun(id: string): Promise<AgentRunResponse> {
  const { data } = await apiClient.get<AgentRunResponse>(`/runs/${id}`);
  return data;
}
