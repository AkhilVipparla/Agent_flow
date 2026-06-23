import type { DocumentResponse, DocumentUploadResponse } from '../types/document';
import { MOCK_DOCUMENTS } from './mockData';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const _localDocs: DocumentResponse[] = [...MOCK_DOCUMENTS];

export async function listDocuments(): Promise<DocumentResponse[]> {
  await delay(200);
  return [..._localDocs];
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  await delay(800);
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  const fileType = ext === 'pdf' ? 'pdf' : ext === 'csv' ? 'csv' : 'excel';
  const response: DocumentUploadResponse = {
    id: `doc-${Date.now()}`,
    filename: file.name,
    status: 'ingested',
    chunkCount: Math.floor(Math.random() * 60) + 10,
    createdAt: new Date().toISOString(),
  };
  _localDocs.push({
    id: response.id,
    filename: file.name,
    fileType,
    chunkCount: response.chunkCount,
    createdAt: response.createdAt,
  });
  return response;
}

export async function deleteDocument(id: string): Promise<void> {
  await delay(150);
  const idx = _localDocs.findIndex((d) => d.id === id);
  if (idx !== -1) _localDocs.splice(idx, 1);
}
