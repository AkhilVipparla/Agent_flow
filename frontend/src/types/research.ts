import type { AgentName, AgentStep } from './agent';
import type { Citation } from './report';

export interface ResearchRequest {
  query: string;
  uploadedFiles?: string[];
}

export interface EvidenceItem {
  agent: AgentName;
  content: string;
  citations: Citation[];
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export interface RunEvidence {
  retrievedDocuments: EvidenceItem[];
  sqlResults: Record<string, unknown>[];
  searchResults: SearchResult[];
  citations: Citation[];
  confidenceScore: number;
}

export interface AgentRunResponse {
  id: string;
  query: string;
  agentsExecuted: AgentName[];
  steps: AgentStep[];
  evidence: RunEvidence;
  finalReport: string;
  status: 'running' | 'complete' | 'failed';
  createdAt: string;
}
