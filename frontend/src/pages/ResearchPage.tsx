import { useResearch } from '../hooks/useResearch';
import { AgentTimeline } from '../components/research/AgentTimeline';
import { EvidencePanel } from '../components/research/EvidencePanel';
import { QuestionInput } from '../components/research/QuestionInput';
import { ReportViewer } from '../components/research/ReportViewer';

export function ResearchPage() {
  const { submitQuery, currentRun, isRunning } = useResearch();

  // Reveal evidence once at least one evidence agent has completed
  const evidenceReady =
    currentRun?.steps.some(
      (s) =>
        (s.agentName === 'rag' || s.agentName === 'sql' || s.agentName === 'search') &&
        s.status === 'complete',
    ) ?? false;

  return (
    <div className="flex flex-col h-full p-6 gap-4">
      <QuestionInput onSubmit={submitQuery} isDisabled={isRunning} />

      <div className="flex flex-1 gap-4 min-h-0">
        {/* Left column: Agent Timeline */}
        <div className="w-64 flex-shrink-0 bg-white rounded-xl border border-gray-200 p-4 overflow-auto">
          <AgentTimeline steps={currentRun?.steps ?? []} />
        </div>

        {/* Right column: Evidence + Report stacked */}
        <div className="flex flex-col flex-1 gap-4 min-w-0">
          <div className="flex-1 bg-white rounded-xl border border-gray-200 p-4 min-h-0 overflow-hidden">
            <EvidencePanel evidence={evidenceReady ? (currentRun?.evidence ?? null) : null} />
          </div>
          <div className="flex-1 bg-white rounded-xl border border-gray-200 p-4 min-h-0 overflow-hidden">
            <ReportViewer run={currentRun} />
          </div>
        </div>
      </div>
    </div>
  );
}
