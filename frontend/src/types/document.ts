export type DocumentFileType = 'pdf' | 'excel' | 'csv';

export interface DocumentResponse {
  id: string;
  filename: string;
  fileType: DocumentFileType;
  chunkCount: number;
  createdAt: string;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  status: 'ingested' | 'failed';
  chunkCount: number;
  createdAt: string;
}
