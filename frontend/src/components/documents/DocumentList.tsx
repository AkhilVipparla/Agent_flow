import { AnimatePresence, m as motion } from 'framer-motion';
import type { DocumentResponse } from '../../types/document';
import { fadeUp, stagger } from '../../lib/motion';
import { Button } from '../ui/Button';
import { DocumentsIcon } from '../ui/icons';
import { EmptyState } from '../ui/EmptyState';

interface Props {
  documents: DocumentResponse[];
  onDelete: (id: string) => void;
  onView: (doc: DocumentResponse) => void;
}

const TYPE_STYLE: Record<string, string> = {
  pdf: 'border-danger/40 text-danger',
  excel: 'border-ok/40 text-ok',
  csv: 'border-accent/40 text-accent',
};

export function DocumentList({ documents, onDelete, onView }: Props) {
  if (documents.length === 0) {
    return (
      <div className="mt-6">
        <EmptyState
          icon={<DocumentsIcon className="h-7 w-7" />}
          title="No documents yet"
          description="Upload a file above and your research can cite it."
        />
      </div>
    );
  }

  return (
    <motion.ul variants={stagger(0.04)} initial="hidden" animate="show" className="mt-6 space-y-2.5">
      <AnimatePresence initial={false}>
        {documents.map((doc) => (
          <motion.li
            key={doc.id}
            variants={fadeUp}
            layout
            exit={{ opacity: 0, x: -24, transition: { duration: 0.2 } }}
            className="card flex items-center gap-4 px-5 py-3.5"
          >
            <span className={`rounded-sm border px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wider ${TYPE_STYLE[doc.fileType] ?? 'border-line/20 text-muted'}`}>
              {doc.fileType}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[15px] font-medium">{doc.filename}</p>
              <p className="text-xs text-subtle">
                {doc.chunkCount} section{doc.chunkCount === 1 ? '' : 's'} ·{' '}
                {new Date(doc.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
              </p>
            </div>
            {doc.fileType === 'pdf' && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => onView(doc)}
                disabled={!doc.hasFile}
                title={doc.hasFile ? 'View this PDF' : 'No preview for this file. Upload it again to enable one.'}
              >
                View
              </Button>
            )}
            <Button size="sm" variant="danger" onClick={() => onDelete(doc.id)}>Delete</Button>
          </motion.li>
        ))}
      </AnimatePresence>
    </motion.ul>
  );
}
