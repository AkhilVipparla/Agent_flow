import type { AgentRunResponse } from '../../types/research';

interface Props {
  run: AgentRunResponse | null;
}

export function ReportViewer({ run }: Props) {
  if (!run || run.status !== 'complete') {
    return (
      <div className="flex flex-col h-full">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Report</h3>
        <div className="flex-1 flex items-center justify-center rounded-xl border-2 border-dashed border-gray-200">
          <p className="text-sm text-gray-400">
            {run?.status === 'running'
              ? 'Generating report…'
              : 'Report will appear once all agents complete.'}
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
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <h3 className="text-sm font-semibold text-gray-700">Report</h3>
        <button
          onClick={handleExport}
          className="px-3 py-1 text-xs font-medium rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Export .md
        </button>
      </div>
      <div className="flex-1 overflow-auto">
        <div className="rounded-xl border border-gray-100 bg-white p-5">
          <p className="text-xs text-gray-400 mb-3">Query: {run.query}</p>
          <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap font-sans">
            {run.finalReport}
          </div>
        </div>
      </div>
    </div>
  );
}
