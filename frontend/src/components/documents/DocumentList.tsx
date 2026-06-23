import type { DocumentResponse } from '../../types/document';

interface Props {
  documents: DocumentResponse[];
  onDelete: (id: string) => void;
}

export function DocumentList({ documents, onDelete }: Props) {
  if (documents.length === 0) {
    return <p className="text-sm text-gray-400 mt-4">No documents uploaded yet.</p>;
  }

  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50">
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Filename</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Chunks</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Uploaded</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {documents.map((doc) => (
            <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-medium text-gray-800">{doc.filename}</td>
              <td className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{doc.fileType}</td>
              <td className="px-4 py-3 text-gray-500">{doc.chunkCount}</td>
              <td className="px-4 py-3 text-gray-400">
                {new Date(doc.createdAt).toLocaleDateString(undefined, {
                  year: 'numeric', month: 'short', day: 'numeric',
                })}
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => onDelete(doc.id)}
                  className="text-xs text-red-500 hover:text-red-700 font-medium transition-colors"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
