import type { ReportSummary } from '../../types/report';

interface Props {
  report: ReportSummary;
  onClick: () => void;
}

export function ReportCard({ report, onClick }: Props) {
  const score = Math.round(report.confidenceScore * 100);
  const date = new Date(report.createdAt).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const scoreClass =
    score >= 80 ? 'bg-green-100 text-green-700' :
    score >= 60 ? 'bg-amber-100 text-amber-700' :
                  'bg-red-100 text-red-700';

  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-xl border border-gray-200 bg-white p-5 hover:border-indigo-300 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <p className="text-sm font-semibold text-gray-900 leading-snug group-hover:text-indigo-700 transition-colors">
          {report.query}
        </p>
        <span className={`flex-shrink-0 text-xs font-bold px-2 py-0.5 rounded-full ${scoreClass}`}>
          {score}%
        </span>
      </div>
      <p className="text-xs text-gray-400">{date}</p>
    </button>
  );
}
