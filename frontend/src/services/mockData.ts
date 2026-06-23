import type { AgentRunResponse } from '../types/research';
import type { ReportResponse, ReportSummary } from '../types/report';
import type { DocumentResponse } from '../types/document';

export const MOCK_REPORT_SUMMARIES: ReportSummary[] = [
  { id: 'rep-001', query: 'Q4 revenue breakdown by region', confidenceScore: 0.91, createdAt: '2025-01-15T10:23:00Z' },
  { id: 'rep-002', query: 'Customer churn analysis — last 6 months', confidenceScore: 0.85, createdAt: '2025-01-18T14:05:00Z' },
  { id: 'rep-003', query: 'Infrastructure cost optimisation opportunities', confidenceScore: 0.72, createdAt: '2025-01-20T09:47:00Z' },
  { id: 'rep-004', query: 'Product roadmap feasibility review', confidenceScore: 0.88, createdAt: '2025-01-22T16:30:00Z' },
];

export const MOCK_FULL_REPORTS: Record<string, ReportResponse> = {
  'rep-001': {
    id: 'rep-001',
    query: 'Q4 revenue breakdown by region',
    executiveSummary:
      'Q4 total revenue reached $24.7M, a 14% increase year-over-year. EMEA led growth at +22% driven by enterprise contract renewals, while APAC posted +31% on the back of two significant new accounts. North America grew modestly at +6%, constrained by delayed procurement cycles in the financial services vertical.',
    keyFindings: [
      'EMEA revenue: $9.1M (+22% YoY) — largest absolute contributor.',
      'APAC revenue: $5.4M (+31% YoY) — fastest-growing region.',
      'North America revenue: $10.2M (+6% YoY) — growth constrained by procurement delays.',
      'Subscription ARR crossed $80M for the first time, adding $12M in Q4.',
      'Professional services revenue declined 8% due to a deliberate shift toward self-serve.',
    ],
    citations: [
      { source: 'Q4 2024 Financial Report.pdf', page: 12, excerpt: 'EMEA total billings for Q4 were $9.1M representing a 22% increase over Q4 2023.' },
      { source: 'Regional Sales Dashboard', excerpt: 'APAC closed 2 enterprise accounts >$1M ARR in November and December 2024.' },
      { source: 'ARR Tracking Spreadsheet.xlsx', excerpt: 'ARR as of 31 December 2024: $80.4M.' },
    ],
    confidenceScore: 0.91,
    createdAt: '2025-01-15T10:23:00Z',
  },
  'rep-002': {
    id: 'rep-002',
    query: 'Customer churn analysis — last 6 months',
    executiveSummary:
      'Net revenue retention stands at 108%, masking a gross churn rate of 6.2% over the past six months. Churn is concentrated in SMB accounts under $10K ARR. Enterprise accounts (>$100K ARR) showed zero churn. Primary churn drivers identified: onboarding friction, lack of integration with legacy ERP systems, and price sensitivity in the mid-market segment.',
    keyFindings: [
      'Gross churn rate: 6.2% over 6 months (annualised ~12.4%).',
      'SMB segment (<$10K ARR) accounts for 84% of churned accounts by count.',
      'Enterprise segment (>$100K ARR) churn: 0% — driven by multi-year contracts and dedicated CSM coverage.',
      'Top churn reason (42%): "Product does not integrate with our ERP."',
      'Average time-to-churn: 4.3 months post-contract start.',
    ],
    citations: [
      { source: 'Churn Analysis Report H2 2024.pdf', page: 3, excerpt: 'Gross churn rate for July–December 2024 was 6.2%, up from 5.1% in the prior period.' },
      { source: 'Customer Exit Survey Results', excerpt: '42% of churned customers cited ERP integration gaps as the primary reason for cancellation.' },
    ],
    confidenceScore: 0.85,
    createdAt: '2025-01-18T14:05:00Z',
  },
  'rep-003': {
    id: 'rep-003',
    query: 'Infrastructure cost optimisation opportunities',
    executiveSummary:
      'Current monthly cloud spend is $187K. Analysis identified $52K/month in savings across three areas: right-sizing over-provisioned compute instances ($28K), migrating cold storage to cheaper tiers ($14K), and eliminating unused staging environments ($10K). Payback period on migration effort is estimated at 2.1 months.',
    keyFindings: [
      'Total addressable savings: $52K/month ($624K annualised).',
      'Largest opportunity: 34 EC2 instances running at <15% average CPU — right-size to save $28K/month.',
      'Cold data in S3 Standard (>90 days): 14 TB — migrating to Glacier saves $14K/month.',
      'Unused staging environments: 6 environments with zero traffic for >60 days.',
      'Reserved Instance coverage is only 41% — increasing to 70% saves an additional $19K/month.',
    ],
    citations: [
      { source: 'AWS Cost Explorer Export Jan 2025.csv', excerpt: 'EC2 spend: $84,200/month. 34 instances show <15% average CPU utilisation over 30 days.' },
      { source: 'Cloud Architecture Review 2024.pdf', page: 8, excerpt: 'Staging environment policy requires quarterly audit; last audit completed March 2024.' },
    ],
    confidenceScore: 0.72,
    createdAt: '2025-01-20T09:47:00Z',
  },
  'rep-004': {
    id: 'rep-004',
    query: 'Product roadmap feasibility review',
    executiveSummary:
      'The proposed Q2 roadmap contains 14 initiatives. Engineering capacity assessment indicates 9 are achievable within the quarter, 3 require scope reduction, and 2 should be deferred to Q3. Critical path items include the API v3 migration and the new reporting module, both of which have downstream dependencies on the data team.',
    keyFindings: [
      '9 of 14 roadmap items are fully feasible within Q2 engineering capacity.',
      'API v3 migration is on the critical path — any delay cascades to 4 other initiatives.',
      'Reporting module requires 3 weeks of data engineering work not currently planned.',
      '2 initiatives (mobile offline mode, SSO v2) should defer to Q3 due to capacity constraints.',
      'External dependency on Stripe API v4 upgrade adds risk to the billing revamp initiative.',
    ],
    citations: [
      { source: 'Engineering Capacity Plan Q2 2025.pdf', page: 2, excerpt: 'Available engineering capacity Q2: 340 story points across 8 squads.' },
      { source: 'Product Roadmap Q2 2025.xlsx', excerpt: 'API v3 migration estimated at 80 story points; reporting module at 65 story points.' },
      { url: 'https://stripe.com/docs/upgrades', source: 'Stripe API Changelog', excerpt: 'Stripe API v4 requires migration from deprecated payment_intent.confirm flow.' },
    ],
    confidenceScore: 0.88,
    createdAt: '2025-01-22T16:30:00Z',
  },
};

export const MOCK_DOCUMENTS: DocumentResponse[] = [
  { id: 'doc-001', filename: 'Q4_2024_Financial_Report.pdf', fileType: 'pdf', chunkCount: 48, createdAt: '2025-01-10T08:00:00Z' },
  { id: 'doc-002', filename: 'Customer_Churn_H2_2024.pdf', fileType: 'pdf', chunkCount: 31, createdAt: '2025-01-12T11:30:00Z' },
  { id: 'doc-003', filename: 'AWS_Cost_Explorer_Jan2025.csv', fileType: 'csv', chunkCount: 214, createdAt: '2025-01-14T09:15:00Z' },
];

export const MOCK_RUNS: AgentRunResponse[] = [
  {
    id: 'run-001',
    query: 'Q4 revenue breakdown by region',
    agentsExecuted: ['planner', 'rag', 'sql', 'critic', 'report'],
    steps: [
      { agentName: 'planner', status: 'complete', durationMs: 820 },
      { agentName: 'rag', status: 'complete', durationMs: 1760 },
      { agentName: 'sql', status: 'complete', durationMs: 1430 },
      { agentName: 'search', status: 'idle' },
      { agentName: 'file', status: 'idle' },
      { agentName: 'critic', status: 'complete', durationMs: 560 },
      { agentName: 'report', status: 'complete', durationMs: 1180 },
    ],
    evidence: {
      retrievedDocuments: [
        { agent: 'rag', content: 'Q4 total billings across all regions reached $24.7M, up 14% year-over-year. The strongest growth was seen in APAC at 31%, followed by EMEA at 22%.', citations: [{ source: 'Q4_2024_Financial_Report.pdf', page: 12, excerpt: 'Total billings Q4 2024: $24.7M (+14% YoY).' }] },
      ],
      sqlResults: [
        { region: 'North America', revenue: 10200000, growth_pct: 6 },
        { region: 'EMEA', revenue: 9100000, growth_pct: 22 },
        { region: 'APAC', revenue: 5400000, growth_pct: 31 },
      ],
      searchResults: [],
      citations: [
        { source: 'Q4_2024_Financial_Report.pdf', page: 12, excerpt: 'Total billings Q4 2024: $24.7M (+14% YoY).' },
        { source: 'Regional Sales Dashboard', excerpt: 'APAC closed 2 enterprise accounts >$1M ARR in Q4.' },
      ],
      confidenceScore: 0.91,
    },
    finalReport: `## Executive Summary\n\nQ4 total revenue reached $24.7M, a 14% increase year-over-year. EMEA led growth at +22% driven by enterprise contract renewals, while APAC posted +31% on the back of two significant new accounts.\n\n## Key Findings\n\n1. EMEA revenue: $9.1M (+22% YoY)\n2. APAC revenue: $5.4M (+31% YoY)\n3. North America revenue: $10.2M (+6% YoY)\n4. Subscription ARR crossed $80M for the first time\n\n## Conclusion\n\nAll regions delivered positive growth. APAC shows the strongest momentum for Q1 investment.`,
    status: 'complete',
    createdAt: '2025-01-15T10:23:00Z',
  },
  {
    id: 'run-002',
    query: 'Customer churn analysis — last 6 months',
    agentsExecuted: ['planner', 'rag', 'sql', 'search', 'critic', 'report'],
    steps: [
      { agentName: 'planner', status: 'complete', durationMs: 910 },
      { agentName: 'rag', status: 'complete', durationMs: 2100 },
      { agentName: 'sql', status: 'complete', durationMs: 1650 },
      { agentName: 'search', status: 'complete', durationMs: 2400 },
      { agentName: 'file', status: 'idle' },
      { agentName: 'critic', status: 'complete', durationMs: 490 },
      { agentName: 'report', status: 'complete', durationMs: 1320 },
    ],
    evidence: {
      retrievedDocuments: [
        { agent: 'rag', content: 'Gross churn rate for July–December 2024 was 6.2%, up from 5.1% in the prior period. SMB accounts under $10K ARR represent 84% of churned accounts by count.', citations: [{ source: 'Churn Analysis Report H2 2024.pdf', page: 3, excerpt: 'Gross churn rate for July–December 2024 was 6.2%.' }] },
      ],
      sqlResults: [
        { segment: 'SMB (<$10K ARR)', churned_accounts: 142, churn_rate_pct: 9.8 },
        { segment: 'Mid-market ($10K–$100K ARR)', churned_accounts: 18, churn_rate_pct: 3.2 },
        { segment: 'Enterprise (>$100K ARR)', churned_accounts: 0, churn_rate_pct: 0 },
      ],
      searchResults: [
        { title: 'SaaS Churn Benchmarks 2024 — OpenView Partners', url: 'https://openviewpartners.com/saas-benchmarks', snippet: 'Median gross churn for B2B SaaS companies at $10M–$50M ARR is 8–12% annually.' },
      ],
      citations: [
        { source: 'Churn Analysis Report H2 2024.pdf', page: 3, excerpt: 'Gross churn rate 6.2%, average time-to-churn 4.3 months.' },
        { source: 'Customer Exit Survey Results', excerpt: '42% cited ERP integration gaps as primary churn reason.' },
      ],
      confidenceScore: 0.85,
    },
    finalReport: `## Executive Summary\n\nNet revenue retention is 108%, but gross churn of 6.2% over the past six months is concentrated in SMB accounts. Enterprise accounts show zero churn.\n\n## Key Findings\n\n1. Gross churn rate: 6.2% (6 months), annualised ~12.4%\n2. SMB segment accounts for 84% of churned accounts\n3. Top churn reason (42%): missing ERP integration\n4. Enterprise churn: 0%\n\n## Recommendation\n\nPrioritise ERP integration connectors and an improved SMB onboarding programme to reduce time-to-value below 30 days.`,
    status: 'complete',
    createdAt: '2025-01-18T14:05:00Z',
  },
];

export function buildMockRun(query: string): AgentRunResponse {
  return {
    id: `run-${Date.now()}`,
    query,
    agentsExecuted: ['planner', 'rag', 'sql', 'search', 'critic', 'report'],
    steps: [],
    evidence: {
      retrievedDocuments: [
        {
          agent: 'rag',
          content: `Internal knowledge base returned 5 document chunks relevant to: "${query}". Sources include policy documents, prior quarterly reports, and internal analysis memos. Key themes identified align with the query intent and provide a foundational evidence layer.`,
          citations: [
            { source: 'Internal Knowledge Base', excerpt: `Document excerpt relevant to: ${query}` },
            { source: 'Q4_2024_Financial_Report.pdf', page: 4, excerpt: 'Supporting data consistent with the research query.' },
          ],
        },
      ],
      sqlResults: [
        { metric: 'total_records', value: 342, period: 'Q4 2024' },
        { metric: 'avg_value', value: 18750, currency: 'USD' },
        { metric: 'growth_rate_pct', value: 14.2 },
        { metric: 'top_segment', value: 'Enterprise' },
      ],
      searchResults: [
        {
          title: 'Industry Analysis: Enterprise SaaS Trends 2024',
          url: 'https://example.com/saas-trends-2024',
          snippet: 'Enterprise SaaS adoption continued to accelerate in 2024, with average deal sizes growing 18% year-over-year. Multi-year contracts now represent 62% of new bookings.',
        },
        {
          title: 'Competitor Landscape Report — Q4 2024',
          url: 'https://example.com/competitor-report',
          snippet: 'Market leader positions remained stable in Q4. Challenger vendors gained share in the mid-market through aggressive pricing and improved integrations.',
        },
        {
          title: 'Gartner Magic Quadrant — Business Intelligence Platforms 2025',
          url: 'https://example.com/gartner-mq',
          snippet: 'Leaders in the 2025 Magic Quadrant demonstrated strong execution in AI-assisted analytics and self-serve capabilities.',
        },
      ],
      citations: [
        { source: 'Internal Knowledge Base', excerpt: `Document excerpt relevant to: ${query}` },
        { source: 'Q4_2024_Financial_Report.pdf', page: 4, excerpt: 'Supporting quantitative data from the Q4 financial period.' },
        { source: 'Industry Analysis: Enterprise SaaS Trends 2024', url: 'https://example.com/saas-trends-2024', excerpt: 'Enterprise SaaS adoption accelerated in 2024, average deal sizes +18% YoY.' },
      ],
      confidenceScore: 0.87,
    },
    finalReport: `## Executive Summary

Analysis drew on the enterprise knowledge base, structured business data, and live web sources. The Critic Agent assessed evidence quality and assigned a confidence score of 87%.

## Key Findings

1. Internal documentation confirms the observed trend across three independent sources, providing a consistent evidence base.
2. SQL analysis of the reporting database returned 342 matching records spanning Q4 2024, aggregated by segment and metric.
3. Web search corroborated findings with two industry reports published this month, both consistent with internal data.
4. Evidence quality exceeded the confidence threshold on the first pass — no retry loop was required.

## Evidence Summary

**RAG Agent** retrieved 5 document chunks from the Qdrant knowledge base, including policy documents and prior quarterly reports directly relevant to the query.

**SQL Agent** executed a structured query against the business database, returning 342 rows of transactional data aggregated by region and product line. Key metrics show a 14.2% growth rate.

**Search Agent** identified 3 relevant external sources confirming the observed pattern. Industry benchmarks are consistent with internal findings.

## Conclusion

The evidence base is sufficient to support high-confidence conclusions. All three data sources (internal documents, structured data, and external sources) are directionally consistent. See the Evidence Panel for detailed citations and source excerpts.`,
    status: 'complete',
    createdAt: new Date().toISOString(),
  };
}
