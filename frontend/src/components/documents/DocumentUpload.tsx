import { useRef } from 'react';

interface Props {
  onUpload: (file: File) => void;
  isUploading: boolean;
}

export function DocumentUpload({ onUpload, isUploading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && !isUploading) onUpload(file);
  };

  return (
    <div
      onClick={() => !isUploading && inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors ${
        isUploading
          ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
          : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50'
      }`}
    >
      <span className="text-3xl select-none">📎</span>
      <p className="text-sm font-medium text-gray-700">
        {isUploading ? 'Uploading…' : 'Click or drag a file to upload'}
      </p>
      <p className="text-xs text-gray-400">PDF, Excel (.xlsx / .xls), CSV — max 50 MB</p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.xlsx,.xls,.csv"
        onChange={handleChange}
        className="hidden"
        disabled={isUploading}
      />
    </div>
  );
}
