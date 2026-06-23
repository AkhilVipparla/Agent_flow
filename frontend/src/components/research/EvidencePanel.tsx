import { useState } from 'react';
import type { RunEvidence } from '../../types/research';

const TABS = ['Documents', 'SQL', 'Search', 'Citations'] as const;
type Tab = (typeof TABS)[number];

interface Props {
  evidence: RunEvidence | null;
}

export function EvidencePanel({ evidence }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('Documents');

  if (!evidence) {
    return (
      <div className="flex flex-col h-full">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Evidence Panel</h3>
        <div className="flex-1 flex items-center justify-center rounded-xl border-2 border-dashed border-gray-200">
          <p className="text-sm text-gray-400">Evidence will appear here as agents complete.</p>
        </div>
      </div>
    );
  }

  const score = Math.round(evidence.confidenceScore * 100);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <h3 className="text-sm font-semibold text-gray-700">Evidence Panel</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Confidence</span>
          <div className="w-20 h-1.5 rounded-full bg-gray-200 overflow-hidden">
            <div
              className="h-full rounded-full bg-indigo-500 transition-all duration-500"
              style={{ width: `${score}%` }}
            />
          </div>
          <span className="text-xs font-bold text-indigo-600">{score}%</span>
        </div>
      </div>

      <div className="flex gap-1 mb-3 border-b border-gray-200 flex-shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab
                ? 'text-indigo-600 border-indigo-600'
                : 'text-gray-500 border-transparent hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'Documents' && (
          <div className="space-y-3">
            {evidence.retrievedDocuments.length === 0 ? (
              <p className="text-sm text-gray-400">No documents retrieved.</p>
            ) : (
              evidence.retrievedDocuments.map((item, i) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3 bg-gray-50">
                  <p className="text-xs font-semibold text-indigo-600 uppercase mb-1">{item.agent}</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{item.content}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'SQL' && (
          <div className="space-y-2">
            {evidence.sqlResults.length === 0 ? (
              <p className="text-sm text-gray-400">No SQL results.</p>
            ) : (
              evidence.sqlResults.map((row, i) => (
                <pre key={i} className="rounded-lg bg-gray-50 border border-gray-100 p-3 text-xs text-gray-700 overflow-auto">
                  {JSON.stringify(row, null, 2)}
                </pre>
              ))
            )}
          </div>
        )}

        {activeTab === 'Search' && (
          <div className="space-y-3">
            {evidence.searchResults.length === 0 ? (
              <p className="text-sm text-gray-400">No search results.</p>
            ) : (
              evidence.searchResults.map((result, i) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <p className="text-sm font-medium text-gray-900">{result.title}</p>
                  <p className="text-xs text-indigo-500 truncate mt-0.5">{result.url}</p>
                  <p className="mt-1.5 text-sm text-gray-600 leading-relaxed">{result.snippet}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'Citations' && (
          <div className="space-y-3">
            {evidence.citations.length === 0 ? (
              <p className="text-sm text-gray-400">No citations.</p>
            ) : (
              evidence.citations.map((c, i) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3">
                  <div className="flex items-center gap-2 mb-1.5">
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
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
