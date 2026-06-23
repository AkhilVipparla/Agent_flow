export interface Citation {
  source: string;
  url?: string;
  page?: number;
  excerpt: string;
}

export interface ReportSummary {
  id: string;
  query: string;
  confidenceScore: number;
  createdAt: string;
}

export interface ReportResponse {
  id: string;
  query: string;
  executiveSummary: string;
  keyFindings: string[];
  citations: Citation[];
  confidenceScore: number;
  createdAt: string;
}

export interface ReportListResponse {
  reports: ReportSummary[];
  total: number;
}
