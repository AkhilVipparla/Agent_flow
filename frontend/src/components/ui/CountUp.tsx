import { useEffect, useState } from 'react';
import { animate } from 'framer-motion/dom';
import { useReducedMotion } from 'framer-motion';

/** Number that eases from its previous value to the new one. */
export function CountUp({ value, suffix = '' }: { value: number; suffix?: string }) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(reduce ? value : 0);

  useEffect(() => {
    if (reduce) {
      setShown(value);
      return;
    }
    const controls = animate(shown, value, {
      duration: 0.9,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setShown(v),
    });
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, reduce]);

  return (
    <span className="tabular-nums">
      {Math.round(shown)}
      {suffix}
    </span>
  );
}
