import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatePresence, m as motion } from 'framer-motion';
import { useReports } from '../hooks/useReports';
import { ReportCard } from '../components/reports/ReportCard';
import { ReportExport } from '../components/reports/ReportExport';
import { getReport } from '../services/reportsService';
import { easeApple, stagger } from '../lib/motion';
import { CloseIcon, ReportsIcon } from '../components/ui/icons';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { Markdown } from '../components/ui/Markdown';
import type { ReportSummary } from '../types/report';

export function ReportsPage() {
  const { reports, isLoading } = useReports();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: fullReport } = useQuery({
    queryKey: ['report', selectedId],
    queryFn: () => getReport(selectedId!),
    enabled: selectedId !== null,
  });

  const handleCardClick = (report: ReportSummary) => setSelectedId(report.id);
  const handleClose = () => setSelectedId(null);

  // Escape closes the dialog, as in any native sheet.
  useEffect(() => {
    if (selectedId === null) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && handleClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selectedId]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 md:px-10">
      <PageHeader
        title="Reports"
        subtitle={reports.length ? `${reports.length} saved report${reports.length === 1 ? '' : 's'}` : 'Your finished research lives here.'}
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => <div key={i} className="skeleton h-36 rounded-2xl" />)}
        </div>
      ) : reports.length === 0 ? (
        <EmptyState
          icon={<ReportsIcon className="h-7 w-7" />}
          title="No reports yet"
          description="Run a research question and the finished report is saved here automatically."
        />
      ) : (
        <motion.div
          variants={stagger(0.05)}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
        >
          {reports.map((report) => (
            <ReportCard key={report.id} report={report} onClick={() => handleCardClick(report)} />
          ))}
        </motion.div>
      )}

      <AnimatePresence>
        {selectedId !== null && (
          <motion.div
            className="fixed inset-0 z-50 flex items-end justify-center bg-fg/45 p-0 sm:items-center sm:p-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          >
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Report"
              onClick={(e) => e.stopPropagation()}
              initial={{ opacity: 0, y: 40, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 24, scale: 0.98 }}
              transition={{ duration: 0.35, ease: easeApple }}
              className="flex max-h-[88vh] w-full max-w-2xl flex-col overflow-hidden rounded-t-xl border border-line/20 bg-surface sm:rounded-xl"
            >
              <div className="flex flex-shrink-0 items-start justify-between gap-4 border-b border-line/10 p-6">
                <div className="min-w-0 flex-1">
                  <h2 className="display text-[26px] leading-[1.1]">{fullReport?.query ?? '...'}</h2>
                  {fullReport && (
                    <p className="mt-1 text-xs text-subtle">
                      Confidence {Math.round(fullReport.confidenceScore * 100)}% ·{' '}
                      {new Date(fullReport.createdAt).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="flex flex-shrink-0 items-center gap-2">
                  {fullReport && (
                    <ReportExport
                      content={`# ${fullReport.query}\n\n## Executive Summary\n\n${fullReport.executiveSummary}\n\n## Key Findings\n\n${fullReport.keyFindings.map((f, i) => `${i + 1}. ${f}`).join('\n')}`}
                      filename={`report-${fullReport.id}`}
                    />
                  )}
                  <button
                    onClick={handleClose}
                    aria-label="Close report"
                    className="grid h-8 w-8 place-items-center rounded-md border border-line/20 text-muted transition-colors hover:border-fg/50 hover:text-fg"
                  >
                    <CloseIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-auto p-6">
                {!fullReport ? (
                  <div className="space-y-3">
                    <div className="skeleton h-4 w-1/3" />
                    <div className="skeleton h-4 w-full" />
                    <div className="skeleton h-4 w-5/6" />
                  </div>
                ) : (
                  <div className="space-y-7">
                    <section>
                      <h3 className="eyebrow mb-2">Executive summary</h3>
                      <p className="text-[15px] leading-relaxed">{fullReport.executiveSummary}</p>
                    </section>

                    <section>
                      <h3 className="eyebrow mb-2">Key findings</h3>
                      <Markdown text={fullReport.keyFindings.map((f, i) => `${i + 1}. ${f}`).join('\n')} />
                    </section>

                    {fullReport.citations.length > 0 && (
                      <section>
                        <h3 className="eyebrow mb-2">Citations</h3>
                        <div className="space-y-2">
                          {fullReport.citations.map((c, i) => (
                            <div key={i} className="rounded-lg border border-line/10 bg-surface-2/50 p-3.5">
                              <div className="mb-1 flex items-center gap-2">
                                <span className="grid h-5 w-5 flex-shrink-0 place-items-center rounded-sm bg-fg font-mono text-[11px] font-medium text-bg">
                                  {i + 1}
                                </span>
                                <span className="truncate text-xs font-semibold">{c.source}</span>
                                {c.page !== undefined && <span className="flex-shrink-0 text-xs text-subtle">p.{c.page}</span>}
                              </div>
                              <p className="pl-7 text-sm italic text-muted">&ldquo;{c.excerpt}&rdquo;</p>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
