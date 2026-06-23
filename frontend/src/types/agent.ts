export type AgentName = 'planner' | 'rag' | 'sql' | 'search' | 'file' | 'critic' | 'report';

export type AgentStatus = 'idle' | 'running' | 'complete' | 'failed' | 'retrying';

export interface AgentStep {
  agentName: AgentName;
  status: AgentStatus;
  durationMs?: number;
}
