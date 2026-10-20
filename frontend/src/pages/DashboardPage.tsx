import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { m as motion } from 'framer-motion';
import { useAuth } from '../lib/auth';
import { fadeUp, stagger } from '../lib/motion';
import { listAgentRuns } from '../services/researchService';
import { Button } from '../components/ui/Button';
import { CountUp } from '../components/ui/CountUp';
import { EmptyState } from '../components/ui/EmptyState';
import { ResearchIcon } from '../components/ui/icons';
import { PageHeader } from '../components/ui/PageHeader';
import { StatusPill } from '../components/ui/StatusPill';

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: listAgentRuns,
  });

  const completed = runs.filter((r) => r.status === 'complete');
  const avgConf =
    completed.length > 0
      ? completed.reduce((sum, r) => sum + r.evidence.confidenceScore, 0) / completed.length
      : 0;

  const stats = [
    { label: 'Total runs', value: runs.length, suffix: '' },
    { label: 'Completed', value: completed.length, suffix: '' },
    { label: 'Avg. confidence', value: Math.round(avgConf * 100), suffix: '%' },
  ];

  const firstName = user?.name.trim().split(' ')[0];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 md:px-10">
      <PageHeader
        eyebrow="Overview"
        title={`${greeting()}${firstName ? `, ${firstName}` : ''}.`}
        subtitle="Here is where your research stands."
        action={<Button variant="signal" onClick={() => navigate('/research')}>New research</Button>}
      />

      {/* One ruled band of numbers, not three cards. */}
      <motion.dl
        variants={stagger(0.08)}
        initial="hidden"
        animate="show"
        className="mb-14 grid divide-y divide-line/15 border-y border-line/15 sm:grid-cols-3 sm:divide-x sm:divide-y-0"
      >
        {stats.map(({ label, value, suffix }) => (
          <motion.div key={label} variants={fadeUp} className="px-0 py-6 sm:px-8 sm:first:pl-0">
            <dt className="eyebrow">{label}</dt>
            <dd className="display mt-3 text-[clamp(3.5rem,7vw,5.5rem)] leading-none">
              <CountUp value={value} suffix={suffix} />
            </dd>
          </motion.div>
        ))}
      </motion.dl>

      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="display text-[32px] leading-none">Recent runs</h2>
        {runs.length > 0 && <span className="eyebrow">{runs.length} total</span>}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => <div key={i} className="skeleton h-14" />)}
        </div>
      ) : runs.length === 0 ? (
        <EmptyState
          icon={<ResearchIcon className="h-7 w-7" />}
          title="No research yet"
          description="Ask your first question and the agents will plan, gather evidence and write it up."
          action={<Button variant="signal" onClick={() => navigate('/research')}>Start researching</Button>}
        />
      ) : (
        <motion.ul variants={stagger(0.04)} initial="hidden" animate="show" className="border-t border-line/15">
          {runs.map((run) => (
            <motion.li
              key={run.id}
              variants={fadeUp}
              className="flex items-center justify-between gap-4 border-b border-line/15 py-4"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-[16px]">{run.query}</p>
                <p className="mt-0.5 font-mono text-[11px] uppercase tracking-wider text-subtle">
                  {new Date(run.createdAt).toLocaleString()}
                </p>
              </div>
              <div className="flex flex-shrink-0 items-center gap-5">
                <div className="hidden items-center gap-2 sm:flex" title="Confidence">
                  <div className="h-px w-20 bg-line/20">
                    <motion.div
                      className="h-[3px] -translate-y-px bg-accent-solid"
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.round(run.evidence.confidenceScore * 100)}%` }}
                      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                    />
                  </div>
                  <span className="w-9 text-right font-mono text-xs tabular-nums text-muted">
                    {Math.round(run.evidence.confidenceScore * 100)}%
                  </span>
                </div>
                <StatusPill status={run.status} />
              </div>
            </motion.li>
          ))}
        </motion.ul>
      )}
    </div>
  );
}
