import { AnimatePresence, m as motion } from 'framer-motion';
import { useResearch } from '../hooks/useResearch';
import { errorMessage } from '../services/authService';
import { AgentTimeline } from '../components/research/AgentTimeline';
import { EvidencePanel } from '../components/research/EvidencePanel';
import { QuestionInput } from '../components/research/QuestionInput';
import { ReportViewer } from '../components/research/ReportViewer';
import { PageHeader } from '../components/ui/PageHeader';

export function ResearchPage() {
  const { submitQuery, currentRun, isRunning, error } = useResearch();

  // Reveal evidence once at least one evidence agent has completed
  const evidenceReady =
    currentRun?.steps.some(
      (s) =>
        (s.agentName === 'rag' || s.agentName === 'sql' || s.agentName === 'search') &&
        s.status === 'complete',
    ) ?? false;

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 md:px-10">
      <PageHeader title="Research" subtitle="Ask a question. The agents gather evidence and write it up." />

      <QuestionInput onSubmit={submitQuery} isDisabled={isRunning} />

      <AnimatePresence>
        {error && (
          <motion.p
            role="alert"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 overflow-hidden rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            {errorMessage(error, 'Could not start the research run.')}
          </motion.p>
        )}
      </AnimatePresence>

      <div className="mt-6 grid gap-4 lg:grid-cols-[18rem_1fr]">
        <div className="card p-5 lg:sticky lg:top-6 lg:self-start">
          <AgentTimeline steps={currentRun?.steps ?? []} planned={currentRun?.agentsExecuted ?? []} />
        </div>

        <div className="flex min-w-0 flex-col gap-4">
          <div className="card min-h-[16rem] p-5 lg:h-[22rem]">
            <EvidencePanel evidence={evidenceReady ? (currentRun?.evidence ?? null) : null} />
          </div>
          <div className="card min-h-[18rem] p-5 lg:min-h-[24rem]">
            <ReportViewer run={currentRun} />
          </div>
        </div>
      </div>
    </div>
  );
}
