import { m as motion } from 'framer-motion';
import { useTheme, type ThemeMode } from '../../lib/theme';
import { MonitorIcon, MoonIcon, SunIcon } from './icons';
import { spring } from '../../lib/motion';

const OPTIONS: { value: ThemeMode; label: string; Icon: typeof SunIcon }[] = [
  { value: 'light', label: 'Light', Icon: SunIcon },
  { value: 'system', label: 'System', Icon: MonitorIcon },
  { value: 'dark', label: 'Dark', Icon: MoonIcon },
];

/** Three-way light / system / dark switch. */
export function ThemeToggle() {
  const { mode, setMode } = useTheme();
  return (
    <div role="radiogroup" aria-label="Theme" className="inline-flex rounded-lg border border-line/20 p-0.5">
      {OPTIONS.map(({ value, label, Icon }) => {
        const active = mode === value;
        return (
          <button
            key={value}
            role="radio"
            aria-checked={active}
            aria-label={label}
            title={label}
            onClick={() => setMode(value)}
            className={`relative grid h-7 w-7 place-items-center rounded-md transition-colors ${
              active ? 'text-bg' : 'text-subtle hover:text-fg'
            }`}
          >
            {active && (
              <motion.span
                layoutId="theme-pill"
                transition={spring}
                className="absolute inset-0 rounded-md bg-fg"
              />
            )}
            <Icon className="relative h-3.5 w-3.5" />
          </button>
        );
      })}
    </div>
  );
}
