import { useState } from 'react';
import { AnimatePresence, m as motion } from 'framer-motion';
import type { RunEvidence } from '../../types/research';
import { fadeUp, spring, stagger } from '../../lib/motion';

const TABS = ['Documents', 'SQL', 'Search', 'Citations'] as const;
type Tab = (typeof TABS)[number];

interface Props {
  evidence: RunEvidence | null;
}

function Empty({ children }: { children: string }) {
  return <p className="py-6 text-center text-sm text-subtle">{children}</p>;
}

function SqlTable({ rows }: { rows: Record<string, unknown>[] }) {
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  return (
    <div className="overflow-x-auto rounded-xl border border-line/10">
      <table className="min-w-full text-left text-[13px]">
        <thead>
          <tr className="bg-line/[0.04] text-subtle">
            {columns.map((c) => (
              <th key={c} className="whitespace-nowrap px-3 py-2 font-medium">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-line/10">
              {columns.map((c) => (
                <td key={c} className="whitespace-nowrap px-3 py-2 tabular-nums">
                  {row[c] === null || row[c] === undefined ? '—' : String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EvidencePanel({ evidence }: Props) {
  // Until the user picks a tab, show the first one that actually has something in it.
  const [pickedTab, setActiveTab] = useState<Tab | null>(null);

  if (!evidence) {
    return (
      <div className="flex h-full flex-col">
        <h3 className="eyebrow mb-3">Evidence</h3>
        <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-line/15">
          <p className="px-4 text-center text-sm text-subtle">Evidence shows up here as the agents finish.</p>
        </div>
      </div>
    );
  }

  const score = Math.round(evidence.confidenceScore * 100);
  const hasContent: Record<Tab, boolean> = {
    Documents: evidence.retrievedDocuments.length > 0,
    SQL: evidence.sqlResults.length > 0,
    Search: evidence.searchResults.length > 0,
    Citations: evidence.citations.length > 0,
  };
  const activeTab: Tab = pickedTab ?? TABS.find((t) => hasContent[t]) ?? 'Documents';

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex flex-shrink-0 items-center justify-between">
        <h3 className="eyebrow">Evidence</h3>
        <div className="flex items-center gap-2" title="Confidence in the evidence">
          <span className="text-xs text-subtle">Confidence</span>
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-line/10">
            <motion.div
              className="h-full rounded-full bg-accent-solid"
              initial={{ width: 0 }}
              animate={{ width: `${score}%` }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
          <span className="text-xs font-semibold tabular-nums">{score}%</span>
        </div>
      </div>

      <div className="mb-3 flex flex-shrink-0 gap-1 border-b border-line/10">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`relative px-3 py-2 text-[13px] font-medium transition-colors ${
              activeTab === tab ? 'text-accent' : 'text-muted hover:text-fg'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <motion.span layoutId="evidence-tab" transition={spring} className="absolute inset-x-2 -bottom-px h-0.5 bg-accent-solid" />
            )}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={activeTab}
            variants={stagger(0.04)}
            initial="hidden"
            animate="show"
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {activeTab === 'Documents' &&
              (evidence.retrievedDocuments.length === 0 ? (
                <Empty>No documents retrieved.</Empty>
              ) : (
                evidence.retrievedDocuments.map((item, i) => (
                  <motion.div key={i} variants={fadeUp} className="rounded-lg border border-line/10 bg-surface-2/50 p-3.5">
                    <p className="eyebrow mb-1">{item.agent}</p>
                    <p className="text-sm leading-relaxed">{item.content}</p>
                  </motion.div>
                ))
              ))}

            {activeTab === 'SQL' &&
              (evidence.sqlResults.length === 0 ? (
                <Empty>No SQL results.</Empty>
              ) : (
                <motion.div variants={fadeUp}>
                  <SqlTable rows={evidence.sqlResults} />
                </motion.div>
              ))}

            {activeTab === 'Search' &&
              (evidence.searchResults.length === 0 ? (
                <Empty>No web results. Add a Tavily key in Settings to enable web search.</Empty>
              ) : (
                evidence.searchResults.map((result, i) => (
                  <motion.div key={i} variants={fadeUp} className="rounded-xl border border-line/10 p-3.5">
                    <p className="text-sm font-medium">{result.title}</p>
                    <p className="mt-0.5 truncate text-xs text-accent">{result.url}</p>
                    <p className="mt-1.5 text-sm leading-relaxed text-muted">{result.snippet}</p>
                  </motion.div>
                ))
              ))}

            {activeTab === 'Citations' &&
              (evidence.citations.length === 0 ? (
                <Empty>No citations.</Empty>
              ) : (
                evidence.citations.map((c, i) => (
                  <motion.div key={i} variants={fadeUp} className="rounded-xl border border-line/10 p-3.5">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className="grid h-5 w-5 flex-shrink-0 place-items-center rounded-sm bg-fg font-mono text-[11px] font-medium text-bg">
                        {i + 1}
                      </span>
                      <span className="truncate text-xs font-semibold">{c.source}</span>
                      {c.page !== undefined && <span className="flex-shrink-0 text-xs text-subtle">p.{c.page}</span>}
                    </div>
                    <p className="pl-7 text-sm italic text-muted">&ldquo;{c.excerpt}&rdquo;</p>
                  </motion.div>
                ))
              ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
