import type { ReportListResponse, ReportResponse } from '../types/report';
import { apiClient } from './api';

export async function listReports(): Promise<ReportListResponse> {
  const { data } = await apiClient.get<ReportListResponse>('/reports');
  return data;
}

export async function getReport(id: string): Promise<ReportResponse> {
  const { data } = await apiClient.get<ReportResponse>(`/reports/${id}`);
  return data;
}

export async function deleteReportById(id: string): Promise<void> {
  await apiClient.delete(`/reports/${id}`);
}
