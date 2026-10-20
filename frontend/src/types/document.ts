export type DocumentFileType = 'pdf' | 'excel' | 'csv';

export interface DocumentResponse {
  id: string;
  filename: string;
  fileType: DocumentFileType;
  chunkCount: number;
  createdAt: string;
  // The original file is stored and can be previewed (PDFs uploaded since previews were added).
  hasFile: boolean;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  status: 'ingested' | 'failed';
  chunkCount: number;
  createdAt: string;
}
