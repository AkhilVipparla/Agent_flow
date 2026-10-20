import { m as motion } from 'framer-motion';
import type { AgentStatus } from '../../types/agent';
import { CheckIcon, CloseIcon } from '../ui/icons';

const LABELS: Record<AgentStatus, string> = {
  idle: 'Waiting',
  running: 'Working',
  complete: 'Done',
  failed: 'Failed',
  retrying: 'Retrying',
};

const TEXT: Record<AgentStatus, string> = {
  idle: 'text-subtle',
  running: 'text-accent',
  complete: 'text-ok',
  failed: 'text-danger',
  retrying: 'text-warn',
};

/** Circular state marker used in the timeline. */
export function AgentStatusDot({ status }: { status: AgentStatus }) {
  const live = status === 'running' || status === 'retrying';
  return (
    <span className="relative grid h-7 w-7 flex-shrink-0 place-items-center">
      {live && (
        <motion.span
          className={`absolute inset-0 rounded-full ${status === 'retrying' ? 'bg-warn/30' : 'bg-accent-solid/35'}`}
          animate={{ scale: [1, 1.5], opacity: [0.7, 0] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut' }}
        />
      )}
      <motion.span
        key={status}
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 500, damping: 26 }}
        className={`relative grid h-7 w-7 place-items-center rounded-full ${
          status === 'complete'
            ? 'bg-ok text-white'
            : status === 'failed'
            ? 'bg-danger text-white'
            : live
            ? 'bg-accent-solid text-accent-fg'
            : 'border-2 border-line/20 bg-surface'
        }`}
      >
        {status === 'complete' && <CheckIcon className="h-3.5 w-3.5" />}
        {status === 'failed' && <CloseIcon className="h-3.5 w-3.5" />}
        {live && <span className="h-2 w-2 rounded-full bg-accent-fg" />}
      </motion.span>
    </span>
  );
}

export function AgentStatusBadge({ status }: { status: AgentStatus }) {
  return <span className={`text-xs font-medium ${TEXT[status]}`}>{LABELS[status]}</span>;
}
