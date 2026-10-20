import { useQuery } from '@tanstack/react-query';
import { m as motion } from 'framer-motion';
import { apiClient } from '../services/api';
import { fadeUp, stagger } from '../lib/motion';

export interface DemoTable {
  name: string;
  columns: { name: string; type: string }[];
  rowCount: number;
  sampleRows: Record<string, unknown>[];
}

export interface DemoDatabase {
  available: boolean;
  tables: DemoTable[];
  error?: string;
}

export function useDemoDatabase() {
  return useQuery({
    queryKey: ['demo-database'],
    queryFn: async () => (await apiClient.get<DemoDatabase>('/settings/demo')).data,
    staleTime: 60_000,
    retry: false,
  });
}

// Questions that fit the bundled retail sample data (backend/demo/demo_seed.sql).
const SAMPLE_QUESTIONS = [
  'Which customers placed the most orders?',
  'What is the total revenue by product category?',
  'How many orders were refunded, and what share of all orders is that?',
  'Which country has the highest sales?',
];

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—';
  return String(value);
}

export function DemoDatabasePreview() {
  const { data, isLoading, isError } = useDemoDatabase();

  if (isLoading) {
    return (
      <div className="space-y-2.5">
        {[0, 1, 2].map((i) => <div key={i} className="skeleton h-12 rounded-xl" />)}
      </div>
    );
  }
  if (isError || !data?.available) {
    return <p className="text-sm text-danger">{data?.error ?? 'The demo database is not available.'}</p>;
  }

  return (
    <motion.div variants={stagger(0.05)} initial="hidden" animate="show" className="space-y-3">
      <p className="text-sm text-muted">
        Shared, read-only sample data. Nothing you do here changes it. Ask questions about it on the Research page.
      </p>

      {data.tables.map((table, index) => (
        <motion.details
          key={table.name}
          variants={fadeUp}
          open={index === 0}
          className="group rounded-2xl border border-line/10 bg-line/[0.025]"
        >
          <summary className="flex cursor-pointer select-none list-none items-center justify-between px-4 py-3 [&::-webkit-details-marker]:hidden">
            <span className="font-medium">{table.name}</span>
            <span className="text-xs text-subtle">
              {table.rowCount} rows · {table.columns.length} columns
            </span>
          </summary>
          <div className="border-t border-line/10 px-4 py-3">
            <div className="mb-3 flex flex-wrap gap-1.5">
              {table.columns.map((c) => (
                <span key={c.name} className="rounded-md bg-line/[0.07] px-2 py-0.5 text-[11px] text-muted">
                  {c.name} <span className="text-subtle">{c.type}</span>
                </span>
              ))}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-xs">
                <thead>
                  <tr className="text-subtle">
                    {table.columns.map((c) => (
                      <th key={c.name} className="whitespace-nowrap py-1.5 pr-4 font-medium">{c.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {table.sampleRows.map((row, i) => (
                    <tr key={i} className="border-t border-line/10">
                      {table.columns.map((c) => (
                        <td key={c.name} className="whitespace-nowrap py-1.5 pr-4 tabular-nums">{formatCell(row[c.name])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {table.rowCount > table.sampleRows.length && (
              <p className="mt-2 text-[11px] text-subtle">
                Showing {table.sampleRows.length} of {table.rowCount} rows.
              </p>
            )}
          </div>
        </motion.details>
      ))}

      <motion.div variants={fadeUp} className="pt-1">
        <p className="eyebrow mb-1.5">Try asking</p>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted marker:text-subtle">
          {SAMPLE_QUESTIONS.map((q) => <li key={q}>{q}</li>)}
        </ul>
      </motion.div>
    </motion.div>
  );
}
