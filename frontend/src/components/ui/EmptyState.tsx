import type { ReactNode } from 'react';
import { m as motion } from 'framer-motion';
import { fadeUp } from '../../lib/motion';

interface Props {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: Props) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="show"
      className="flex flex-col items-center justify-center rounded-xl border border-dashed border-line/25 px-6 py-14 text-center"
    >
      <div className="mb-4 grid h-14 w-14 place-items-center rounded-lg border border-line/20 text-fg">{icon}</div>
      <h3 className="display text-[28px] leading-tight">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </motion.div>
  );
}
