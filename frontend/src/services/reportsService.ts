import type { ReportListResponse, ReportResponse } from '../types/report';
import { MOCK_FULL_REPORTS, MOCK_REPORT_SUMMARIES } from './mockData';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function listReports(): Promise<ReportListResponse> {
  await delay(200);
  return { reports: MOCK_REPORT_SUMMARIES, total: MOCK_REPORT_SUMMARIES.length };
}

export async function getReport(id: string): Promise<ReportResponse> {
  await delay(150);
  const report = MOCK_FULL_REPORTS[id];
  if (!report) throw new Error(`Report not found: ${id}`);
  return report;
}

export async function deleteReportById(id: string): Promise<void> {
  await delay(150);
  // Mock: no-op — in production this calls DELETE /reports/{id}
  console.log('deleteReport', id);
}
