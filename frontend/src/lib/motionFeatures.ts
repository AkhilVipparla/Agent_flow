// Loaded on demand by <LazyMotion> in main.tsx, so the animation engine downloads after
// first paint instead of blocking it. domMax is needed for layout / shared-element
// animations (the sliding pills and tab underlines).
import { domMax } from 'framer-motion';

export default domMax;
