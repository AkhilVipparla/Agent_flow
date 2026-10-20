import { useEffect, useState } from 'react';
import type { DocumentResponse } from '../../types/document';
import { errorMessage } from '../../services/authService';
import { fetchDocumentFile } from '../../services/documentsService';
import { Button } from '../ui/Button';
import { CloseIcon } from '../ui/icons';

interface Props {
  doc: DocumentResponse;
  onClose: () => void;
}

/**
 * Quick look at an uploaded PDF without leaving the app.
 *
 * The file is fetched through the authenticated API (so it stays private to its owner) and shown
 * from a temporary blob: URL in the browser's own PDF viewer. The URL is revoked on close.
 */
export function DocumentPreview({ doc, onClose }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    fetchDocumentFile(doc.id)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err, 'Could not load this file.'));
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [doc.id]);

  // Escape closes, like any native preview.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-fg/45 p-0 sm:items-center sm:p-6"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Preview of ${doc.filename}`}
        onClick={(e) => e.stopPropagation()}
        className="page-enter flex h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-t-xl border border-line/20 bg-surface sm:rounded-xl"
      >
        <div className="flex flex-shrink-0 items-center justify-between gap-3 border-b border-line/15 px-5 py-3.5">
          <div className="min-w-0">
            <p className="eyebrow">Preview</p>
            <h2 className="display truncate text-[24px] leading-tight">{doc.filename}</h2>
          </div>
          <div className="flex flex-shrink-0 items-center gap-2">
            {url && (
              <>
                <a href={url} target="_blank" rel="noopener noreferrer" className="hidden sm:inline-flex">
                  <Button size="sm" variant="secondary" tabIndex={-1}>Open in new tab</Button>
                </a>
                <a href={url} download={doc.filename} className="hidden sm:inline-flex">
                  <Button size="sm" variant="secondary" tabIndex={-1}>Download</Button>
                </a>
              </>
            )}
            <button
              onClick={onClose}
              aria-label="Close preview"
              className="grid h-8 w-8 place-items-center rounded-md border border-line/20 text-muted transition-colors hover:border-fg/50 hover:text-fg"
            >
              <CloseIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="relative flex-1 bg-surface-2">
          {error ? (
            <p role="alert" className="p-8 text-center text-sm text-danger">{error}</p>
          ) : !url ? (
            <div className="grid h-full place-items-center">
              <p className="text-sm text-subtle">Loading the document...</p>
            </div>
          ) : (
            <>
              <iframe src={`${url}#view=FitH&navpanes=0`} title={`Preview of ${doc.filename}`} className="h-full w-full" />
              {/* Phones usually show only the first page inside an embedded viewer. */}
              <div className="absolute inset-x-0 bottom-0 flex justify-center gap-2 border-t border-line/15 bg-surface p-3 sm:hidden">
                <a href={url} target="_blank" rel="noopener noreferrer">
                  <Button size="sm" variant="primary" tabIndex={-1}>Open full document</Button>
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
