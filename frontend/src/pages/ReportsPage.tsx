import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useReports } from '../hooks/useReports';
import { ReportCard } from '../components/reports/ReportCard';
import { ReportExport } from '../components/reports/ReportExport';
import { getReport } from '../services/reportsService';
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

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Reports</h1>
        <p className="text-sm text-gray-400">{reports.length} report{reports.length !== 1 ? 's' : ''}</p>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : reports.length === 0 ? (
        <p className="text-sm text-gray-400">No reports yet. Run a research query to generate one.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {reports.map((report) => (
            <ReportCard key={report.id} report={report} onClick={() => handleCardClick(report)} />
          ))}
        </div>
      )}

      {selectedId !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="flex items-start justify-between p-6 border-b border-gray-100 flex-shrink-0">
              <div className="flex-1 min-w-0 mr-4">
                <h2 className="text-base font-semibold text-gray-900 leading-snug">
                  {fullReport?.query ?? '…'}
                </h2>
                {fullReport && (
                  <p className="text-xs text-gray-400 mt-1">
                    Confidence {Math.round(fullReport.confidenceScore * 100)}% ·{' '}
                    {new Date(fullReport.createdAt).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {fullReport && (
                  <ReportExport
                    content={`# ${fullReport.query}\n\n## Executive Summary\n\n${fullReport.executiveSummary}\n\n## Key Findings\n\n${fullReport.keyFindings.map((f, i) => `${i + 1}. ${f}`).join('\n')}`}
                    filename={`report-${fullReport.id}`}
                  />
                )}
                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600 text-lg leading-none transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
              {!fullReport ? (
                <p className="text-sm text-gray-400">Loading…</p>
              ) : (
                <div className="space-y-5">
                  <div>
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                      Executive Summary
                    </h3>
                    <p className="text-sm text-gray-700 leading-relaxed">{fullReport.executiveSummary}</p>
                  </div>

                  <div>
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                      Key Findings
                    </h3>
                    <ol className="space-y-1.5 list-decimal list-inside">
                      {fullReport.keyFindings.map((finding, i) => (
                        <li key={i} className="text-sm text-gray-700 leading-relaxed">
                          {finding}
                        </li>
                      ))}
                    </ol>
                  </div>

                  {fullReport.citations.length > 0 && (
                    <div>
                      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                        Citations
                      </h3>
                      <div className="space-y-2">
                        {fullReport.citations.map((c, i) => (
                          <div key={i} className="rounded-lg border border-gray-100 p-3 bg-gray-50">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 text-xs flex items-center justify-center font-semibold flex-shrink-0">
                                {i + 1}
                              </span>
                              <span className="text-xs font-semibold text-gray-700 truncate">{c.source}</span>
                              {c.page !== undefined && (
                                <span className="text-xs text-gray-400 flex-shrink-0">p.{c.page}</span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 italic pl-7">"{c.excerpt}"</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
