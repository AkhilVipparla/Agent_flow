import { Fragment, type ReactNode } from 'react';

// A deliberately small markdown renderer for report text: headings, ordered and bullet
// lists, bold and italics. It builds React nodes (never raw HTML), so report content
// can't inject markup.

function inline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    const token = match[0];
    if (token.startsWith('**')) parts.push(<strong key={key++} className="font-semibold text-fg">{token.slice(2, -2)}</strong>);
    else if (token.startsWith('`')) parts.push(<code key={key++} className="rounded bg-line/10 px-1 py-0.5 font-mono text-[0.9em]">{token.slice(1, -1)}</code>);
    else parts.push(<em key={key++}>{token.slice(1, -1)}</em>);
    last = match.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

export function Markdown({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i].trimEnd();
    if (!line.trim()) { i++; continue; }

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      blocks.push(
        level <= 2 ? (
          <h3 key={key++} className="display mb-2 mt-6 text-[26px] leading-tight first:mt-0">{inline(heading[2])}</h3>
        ) : (
          <h4 key={key++} className="mb-1.5 mt-4 text-[15px] font-semibold">{inline(heading[2])}</h4>
        ),
      );
      i++;
      continue;
    }

    if (/^\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+[.)]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+[.)]\s+/, ''));
        i++;
      }
      blocks.push(
        <ol key={key++} className="my-2 list-decimal space-y-1.5 pl-5 marker:text-subtle">
          {items.map((item, n) => <li key={n} className="pl-1">{inline(item)}</li>)}
        </ol>,
      );
      continue;
    }

    if (/^[-*•]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*•]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*•]\s+/, ''));
        i++;
      }
      blocks.push(
        <ul key={key++} className="my-2 list-disc space-y-1.5 pl-5 marker:text-subtle">
          {items.map((item, n) => <li key={n} className="pl-1">{inline(item)}</li>)}
        </ul>,
      );
      continue;
    }

    const paragraph: string[] = [];
    while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|\d+[.)]\s|[-*•]\s)/.test(lines[i].trim())) {
      paragraph.push(lines[i].trim());
      i++;
    }
    blocks.push(<p key={key++} className="my-2">{inline(paragraph.join(' '))}</p>);
  }

  return <div className="text-[15px] leading-relaxed text-fg/90"><Fragment>{blocks}</Fragment></div>;
}
