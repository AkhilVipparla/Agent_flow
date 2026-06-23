import { useState } from 'react';

interface Props {
  onSubmit: (query: string) => void;
  isDisabled: boolean;
}

export function QuestionInput({ onSubmit, isDisabled }: Props) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) onSubmit(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a research question — e.g. What drove Q4 revenue growth? (⌘+Enter to submit)"
        rows={3}
        disabled={isDisabled}
        className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400 transition-colors"
      />
      <button
        type="submit"
        disabled={isDisabled || !query.trim()}
        className="px-5 py-3 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
      >
        {isDisabled ? 'Running…' : 'Run Research'}
      </button>
    </form>
  );
}
