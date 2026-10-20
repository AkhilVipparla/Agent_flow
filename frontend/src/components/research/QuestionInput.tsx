import { useState } from 'react';
import { m as motion } from 'framer-motion';
import { Button } from '../ui/Button';

interface Props {
  onSubmit: (query: string) => void;
  isDisabled: boolean;
}

const EXAMPLES = [
  'Summarize the key points of my uploaded documents',
  'Which customers placed the most orders?',
  'What is the total revenue by product category?',
];

export function QuestionInput({ onSubmit, isDisabled }: Props) {
  const [query, setQuery] = useState('');

  const submit = () => {
    const trimmed = query.trim();
    if (trimmed && !isDisabled) onSubmit(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div>
      <motion.form
        onSubmit={(e) => { e.preventDefault(); submit(); }}
        whileFocus={{ scale: 1.002 }}
        className="card p-2 transition-shadow focus-within:border-fg focus-within:shadow-[0_0_0_4px_rgb(var(--accent-solid)/0.25)]"
      >
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Research question"
          placeholder="Ask a research question..."
          rows={2}
          disabled={isDisabled}
          className="w-full resize-none bg-transparent px-4 pb-1 pt-3 text-[18px] text-fg placeholder:text-subtle focus:outline-none disabled:opacity-60"
        />
        <div className="flex items-center justify-between px-2 pb-1">
          <span className="hidden text-xs text-subtle sm:inline">Press Ctrl or Cmd + Enter to run</span>
          <Button type="submit" variant="signal" loading={isDisabled} disabled={!query.trim()} className="ml-auto">
            {isDisabled ? 'Researching' : 'Run research'}
          </Button>
        </div>
      </motion.form>

      {!query && !isDisabled && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-3 flex flex-wrap gap-2"
        >
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuery(example)}
              className="rounded-md border border-line/20 px-3 py-1.5 text-[13px] text-muted transition-colors hover:border-fg/50 hover:text-fg"
            >
              {example}
            </button>
          ))}
        </motion.div>
      )}
    </div>
  );
}
