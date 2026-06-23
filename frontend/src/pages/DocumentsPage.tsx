import { useDocuments } from '../hooks/useDocuments';
import { DocumentList } from '../components/documents/DocumentList';
import { DocumentUpload } from '../components/documents/DocumentUpload';

export function DocumentsPage() {
  const { documents, isLoading, uploadDocument, isUploading, deleteDocument } = useDocuments();

  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Documents</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload documents to expand the knowledge base available to the RAG agent.
        </p>
      </div>

      <DocumentUpload onUpload={uploadDocument} isUploading={isUploading} />

      {isLoading ? (
        <p className="text-sm text-gray-400 mt-6">Loading…</p>
      ) : (
        <DocumentList documents={documents} onDelete={deleteDocument} />
      )}
    </div>
  );
}
