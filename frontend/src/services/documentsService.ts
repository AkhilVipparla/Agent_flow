import type { DocumentResponse, DocumentUploadResponse } from '../types/document';
import { apiClient } from './api';

export async function listDocuments(): Promise<DocumentResponse[]> {
  const { data } = await apiClient.get<DocumentResponse[]>('/documents');
  return data;
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await apiClient.post<DocumentUploadResponse>('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/** The original PDF as a Blob, fetched with the user's session so it stays private. */
export async function fetchDocumentFile(id: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/documents/${id}/file`, { responseType: 'blob' });
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/documents/${id}`);
}
