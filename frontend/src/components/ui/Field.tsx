import { useId, useState } from 'react';
import { clsx } from 'clsx';
import { EyeIcon, EyeOffIcon } from './icons';

export const inputClass =
  'w-full h-11 rounded-md bg-surface border border-line/25 px-3.5 text-[15px] text-fg ' +
  'placeholder:text-subtle transition-[border-color,box-shadow] duration-200 ' +
  'hover:border-line/45 focus:outline-none focus:border-fg focus:ring-4 focus:ring-accent-solid/25';

interface FieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  autoComplete?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  className?: string;
}

export function Field({
  label, value, onChange, type = 'text', placeholder, autoComplete = 'off', hint, error, required, className,
}: FieldProps) {
  const id = useId();
  const [revealed, setRevealed] = useState(false);
  const isPassword = type === 'password';

  return (
    <div className={className}>
      <label htmlFor={id} className="eyebrow mb-1.5 block">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          className={clsx(inputClass, isPassword && 'pr-11', error && 'border-danger focus:border-danger focus:ring-danger/15')}
          type={isPassword && revealed ? 'text' : type}
          value={value}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          aria-invalid={Boolean(error)}
          onChange={(e) => onChange(e.target.value)}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setRevealed((r) => !r)}
            aria-label={revealed ? 'Hide' : 'Show'}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-subtle hover:text-fg transition-colors"
          >
            {revealed ? <EyeOffIcon className="h-[18px] w-[18px]" /> : <EyeIcon className="h-[18px] w-[18px]" />}
          </button>
        )}
      </div>
      {error ? (
        <p className="mt-1.5 text-xs text-danger">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-xs text-subtle">{hint}</p>
      ) : null}
    </div>
  );
}

interface SelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}

export function SelectField({ label, value, onChange, options, className }: SelectProps) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="eyebrow mb-1.5 block">
        {label}
      </label>
      <select id={id} className={clsx(inputClass, 'appearance-none pr-9 bg-no-repeat')}
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none' stroke='%238e8e93' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1 1.5l5 5 5-5'/%3E%3C/svg%3E\")",
          backgroundPosition: 'right 14px center',
        }}
        value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}
