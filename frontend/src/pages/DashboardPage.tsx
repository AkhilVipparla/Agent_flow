import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { listAgentRuns } from '../services/researchService';

export function DashboardPage() {
  const navigate = useNavigate();
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
    { label: 'Total Runs', value: String(runs.length), color: 'text-indigo-600' },
    { label: 'Completed', value: String(completed.length), color: 'text-green-600' },
    { label: 'Avg Confidence', value: `${Math.round(avgConf * 100)}%`, color: 'text-amber-600' },
  ];

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={() => navigate('/research')}
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition-colors"
        >
          + New Research
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {stats.map(({ label, value, color }) => (
          <div key={label} className="rounded-xl border border-gray-200 bg-white p-5">
            <p className="text-xs text-gray-400 mb-1">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <h2 className="text-sm font-semibold text-gray-700 mb-3">Recent Runs</h2>
      {isLoading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : runs.length === 0 ? (
        <p className="text-sm text-gray-400">No runs yet. Start your first research query.</p>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <div
              key={run.id}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-5 py-3"
            >
              <div className="flex-1 min-w-0 mr-4">
                <p className="text-sm font-medium text-gray-800 truncate">{run.query}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(run.createdAt).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="text-xs text-gray-500">
                  {Math.round(run.evidence.confidenceScore * 100)}% conf
                </span>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    run.status === 'complete'
                      ? 'bg-green-100 text-green-700'
                      : run.status === 'failed'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {run.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
