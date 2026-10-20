import type { Config } from 'tailwindcss';

// Semantic colors resolve to CSS variables (see index.css), so one class works in both
// light and dark mode and still supports opacity modifiers like border-line/15.
const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: token('bg'),
        surface: token('surface'),
        'surface-2': token('surface-2'),
        fg: token('fg'),
        muted: token('muted'),
        subtle: token('subtle'),
        line: token('line'),
        accent: token('accent'),
        'accent-solid': token('accent-solid'),
        'accent-fg': token('accent-fg'),
        ok: token('ok'),
        warn: token('warn'),
        danger: token('danger'),
      },
      fontFamily: {
        sans: ['"Geist Variable"', '"Geist Fallback"', 'ui-sans-serif', 'system-ui', '-apple-system', '"Segoe UI"', 'sans-serif'],
        serif: ['"Instrument Serif"', '"Instrument Serif Fallback"', 'ui-serif', 'Georgia', 'serif'],
        mono: ['"Geist Mono Variable"', '"Geist Mono Fallback"', 'ui-monospace', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },
      // Tighter corners than the Tailwind defaults: crisp, editorial rather than bubbly.
      borderRadius: {
        sm: '3px',
        DEFAULT: '4px',
        md: '6px',
        lg: '8px',
        xl: '10px',
        '2xl': '12px',
        '3xl': '14px',
      },
      transitionTimingFunction: {
        // Smooth ease-out used for entrances.
        out: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
} satisfies Config;
