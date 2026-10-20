import { useRef, useState } from 'react';
import { m as motion } from 'framer-motion';
import { Spinner } from '../ui/Spinner';
import { UploadIcon } from '../ui/icons';

interface Props {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export function DocumentUpload({ onUpload, isUploading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && !isUploading) onUpload(file);
  };

  return (
    <motion.div
      role="button"
      tabIndex={0}
      aria-label="Upload a document"
      onClick={() => !isUploading && inputRef.current?.click()}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && !isUploading && inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      animate={{ scale: dragging ? 1.015 : 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 28 }}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-10 text-center transition-colors ${
        isUploading
          ? 'cursor-not-allowed border-line/10 bg-line/[0.03]'
          : dragging
          ? 'border-accent-solid bg-accent-solid/10'
          : 'border-line/30 hover:border-fg hover:bg-line/[0.03]'
      }`}
    >
      <motion.div
        animate={dragging ? { y: -4 } : { y: 0 }}
        className="mb-1 grid h-14 w-14 place-items-center rounded-lg border border-line/20 text-fg"
      >
        {isUploading ? <Spinner className="h-6 w-6" /> : <UploadIcon className="h-7 w-7" />}
      </motion.div>
      <p className="text-[16px] font-medium">
        {isUploading ? 'Reading your document...' : dragging ? 'Drop to upload' : 'Drop a file here, or click to browse'}
      </p>
      <p className="text-sm text-subtle">PDF, Excel (.xlsx / .xls) or CSV, up to 10 MB</p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.xlsx,.xls,.csv"
        onChange={handleChange}
        className="hidden"
        disabled={isUploading}
      />
    </motion.div>
  );
}
