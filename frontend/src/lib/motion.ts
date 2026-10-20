import type { Transition, Variants } from 'framer-motion';

// Apple-style motion: quick ease-out for entrances, springs for direct manipulation.
export const easeApple = [0.22, 1, 0.36, 1] as const;

export const spring: Transition = { type: 'spring', stiffness: 380, damping: 32, mass: 0.8 };
export const softSpring: Transition = { type: 'spring', stiffness: 220, damping: 26 };

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: easeApple } },
};

export const stagger = (delay = 0.06, startDelay = 0): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: delay, delayChildren: startDelay } },
});

