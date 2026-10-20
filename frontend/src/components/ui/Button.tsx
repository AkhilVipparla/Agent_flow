import { forwardRef } from 'react';
import { m as motion, type HTMLMotionProps } from 'framer-motion';
import { clsx } from 'clsx';
import { Spinner } from './Spinner';

type Variant = 'primary' | 'signal' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface Props extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  children?: React.ReactNode;
}

const VARIANTS: Record<Variant, string> = {
  // Ink fill: the default call to action.
  primary: 'bg-fg text-bg hover:bg-fg/85',
  // Signal orange: reserved for the one main action on a screen.
  signal: 'bg-accent-solid text-accent-fg hover:brightness-105',
  secondary: 'border border-line/25 text-fg hover:bg-line/[0.06]',
  ghost: 'text-muted hover:text-fg hover:bg-line/[0.06]',
  danger: 'border border-danger/30 text-danger hover:bg-danger/10',
};

const SIZES: Record<Size, string> = {
  sm: 'h-8 px-3.5 text-[13px]',
  md: 'h-10 px-5 text-sm',
  lg: 'h-12 px-6 text-[15px]',
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = 'primary', size = 'md', loading, disabled, className, children, ...rest },
  ref,
) {
  const inactive = disabled || loading;
  return (
    <motion.button
      ref={ref}
      whileTap={inactive ? undefined : { scale: 0.97 }}
      whileHover={inactive ? undefined : { y: -0.5 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      disabled={inactive}
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-md font-medium whitespace-nowrap select-none',
        'transition-[background-color,filter,color] duration-200 disabled:opacity-45 disabled:cursor-not-allowed',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </motion.button>
  );
});
