import { m as motion } from 'framer-motion';
import type { ReportSummary } from '../../types/report';
import { fadeUp } from '../../lib/motion';
import { ChevronIcon } from '../ui/icons';

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

  const tone = score >= 80 ? 'text-ok bg-ok/12' : score >= 60 ? 'text-warn bg-warn/12' : 'text-danger bg-danger/12';

  return (
    <motion.button
      variants={fadeUp}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      onClick={onClick}
      className="card group flex h-full w-full flex-col p-5 text-left transition-colors hover:border-fg/40"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <span className={`rounded-sm px-2 py-1 font-mono text-[11px] font-medium uppercase tracking-wider tabular-nums ${tone}`}>{score}% conf.</span>
        <ChevronIcon className="h-4 w-4 text-subtle transition-transform group-hover:translate-x-0.5" />
      </div>
      <p className="display line-clamp-3 flex-1 text-[22px] leading-[1.15]">{report.query}</p>
      <p className="mt-4 text-xs text-subtle">{date}</p>
    </motion.button>
  );
}
