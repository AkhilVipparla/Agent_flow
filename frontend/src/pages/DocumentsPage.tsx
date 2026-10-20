import { useState } from 'react';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentPreview } from '../components/documents/DocumentPreview';
import { DocumentList } from '../components/documents/DocumentList';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { PageHeader } from '../components/ui/PageHeader';
import type { DocumentResponse } from '../types/document';

export function DocumentsPage() {
  const { documents, isLoading, uploadDocument, isUploading, deleteDocument, uploadError } = useDocuments();
  const [previewing, setPreviewing] = useState<DocumentResponse | null>(null);

  return (
    <div className="mx-auto max-w-4xl px-6 py-10 md:px-10">
      <PageHeader
        title="Documents"
        subtitle="Upload files and your research can search and cite them. Only you can see what you upload."
      />

      <DocumentUpload onUpload={uploadDocument} isUploading={isUploading} />

      {uploadError && (
        <p role="alert" className="mt-3 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          {uploadError}
        </p>
      )}

      {isLoading ? (
        <div className="mt-6 space-y-2.5">
          {[0, 1].map((i) => <div key={i} className="skeleton h-[60px] rounded-2xl" />)}
        </div>
      ) : (
        <DocumentList documents={documents} onDelete={deleteDocument} onView={setPreviewing} />
      )}

      {previewing && <DocumentPreview doc={previewing} onClose={() => setPreviewing(null)} />}
    </div>
  );
}
