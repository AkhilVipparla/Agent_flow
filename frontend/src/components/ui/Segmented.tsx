import { useId } from 'react';
import { m as motion } from 'framer-motion';
import { clsx } from 'clsx';
import { spring } from '../../lib/motion';

interface Option<T extends string> {
  value: T;
  label: string;
  disabled?: boolean;
  title?: string;
}

interface Props<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: Option<T>[];
  label: string;
  className?: string;
}

/** iOS-style segmented control: a pill that slides to the selected option. */
export function Segmented<T extends string>({ value, onChange, options, label, className }: Props<T>) {
  const group = useId();
  return (
    <div
      role="tablist"
      aria-label={label}
      className={clsx('inline-flex rounded-lg border border-line/20 p-0.5 text-[13px] font-medium', className)}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            role="tab"
            type="button"
            aria-selected={active}
            disabled={opt.disabled}
            title={opt.title}
            onClick={() => onChange(opt.value)}
            className={clsx(
              'relative rounded-md px-4 py-1.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed',
              active ? 'text-bg' : 'text-muted hover:text-fg',
            )}
          >
            {active && (
              <motion.span
                layoutId={`seg-${group}`}
                transition={spring}
                className="absolute inset-0 rounded-md bg-fg"
              />
            )}
            <span className="relative">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
