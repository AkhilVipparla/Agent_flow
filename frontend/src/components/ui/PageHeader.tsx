import type { ReactNode } from 'react';

interface Props {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  /** Small mono label above the title, e.g. a section number. */
  eyebrow?: string;
}

export function PageHeader({ title, subtitle, action, eyebrow }: Props) {
  return (
    <div className="mb-10 flex flex-wrap items-end justify-between gap-4 border-b border-line/15 pb-8">
      <div>
        {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
        <h1 className="display text-[clamp(2.5rem,5vw,4rem)] leading-[0.98]">{title}</h1>
        {subtitle && <p className="mt-3 max-w-xl text-[16px] leading-relaxed text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
