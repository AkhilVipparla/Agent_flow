import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';

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

  if (isLoading) return <p className="text-xs text-gray-500">Loading demo data...</p>;
  if (isError || !data?.available) {
    return <p className="text-xs text-red-600">{data?.error ?? 'The demo database is not available.'}</p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500">
        Shared, read-only sample data. Nothing you do here changes it. Ask questions about it in Research.
      </p>

      {data.tables.map((table, index) => (
        <details key={table.name} open={index === 0} className="rounded-lg border border-gray-200">
          <summary className="cursor-pointer select-none px-3 py-2 text-sm font-medium text-gray-900">
            {table.name}
            <span className="ml-2 text-xs font-normal text-gray-500">
              {table.rowCount} rows · {table.columns.length} columns
            </span>
          </summary>
          <div className="border-t border-gray-100 px-3 py-2">
            <div className="mb-2 flex flex-wrap gap-1">
              {table.columns.map((c) => (
                <span key={c.name} className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-600">
                  {c.name} <span className="text-gray-400">{c.type}</span>
                </span>
              ))}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-xs">
                <thead>
                  <tr className="text-gray-500">
                    {table.columns.map((c) => (
                      <th key={c.name} className="whitespace-nowrap py-1 pr-4 font-medium">{c.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {table.sampleRows.map((row, i) => (
                    <tr key={i} className="border-t border-gray-100 text-gray-800">
                      {table.columns.map((c) => (
                        <td key={c.name} className="whitespace-nowrap py-1 pr-4">{formatCell(row[c.name])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {table.rowCount > table.sampleRows.length && (
              <p className="mt-1 text-[11px] text-gray-400">
                Showing {table.sampleRows.length} of {table.rowCount} rows.
              </p>
            )}
          </div>
        </details>
      ))}

      <div>
        <p className="mb-1 text-xs font-medium text-gray-600">Try asking</p>
        <ul className="list-disc pl-5 text-xs text-gray-600 space-y-0.5">
          {SAMPLE_QUESTIONS.map((q) => <li key={q}>{q}</li>)}
        </ul>
      </div>
    </div>
  );
}
