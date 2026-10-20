import { m as motion } from 'framer-motion';
import type { AgentRunResponse } from '../../types/research';
import { Button } from '../ui/Button';
import { Markdown } from '../ui/Markdown';
import { Spinner } from '../ui/Spinner';
import { easeApple } from '../../lib/motion';

interface Props {
  run: AgentRunResponse | null;
}

export function ReportViewer({ run }: Props) {
  if (!run || run.status !== 'complete') {
    const running = run?.status === 'running';
    const failed = run?.status === 'failed';
    return (
      <div className="flex h-full flex-col">
        <h3 className="eyebrow mb-3">Report</h3>
        <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line/15 px-4">
          {running && <Spinner className="h-5 w-5 text-accent" />}
          <p className="text-center text-sm text-subtle">
            {running
              ? 'Writing your report...'
              : failed
              ? 'This run failed. Check your LLM settings and try again.'
              : 'Your report appears here when the agents finish.'}
          </p>
        </div>
      </div>
    );
  }

  const handleExport = () => {
    const content = `# Research Report\n\n**Query:** ${run.query}\n\n${run.finalReport}`;
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'report.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex flex-shrink-0 items-center justify-between">
        <h3 className="eyebrow">Report</h3>
        <Button size="sm" variant="secondary" onClick={handleExport}>Export .md</Button>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: easeApple }}
        className="flex-1 overflow-auto"
      >
        <p className="mb-3 text-xs text-subtle">Question: {run.query}</p>
        <Markdown text={run.finalReport} />
      </motion.div>
    </div>
  );
}
