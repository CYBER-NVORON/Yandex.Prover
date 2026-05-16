import { motion, useSpring, useTransform } from 'framer-motion';
import { useEffect } from 'react';

interface ScoreCardProps {
  label: string;
  value: number;
}

export function ScoreCard({ label, value }: ScoreCardProps) {
  const spring = useSpring(0, { stiffness: 70, damping: 18 });
  const rounded = useTransform(spring, (latest) => Math.round(latest));

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return (
    <div className="soft-card p-4">
      <div className="text-sm font-semibold text-[#60616a]">{label}</div>
      <div className="mt-3 flex items-end gap-1">
        <motion.span className="text-3xl font-black text-ink">{rounded}</motion.span>
        <span className="mb-1 text-sm font-bold text-zinc-500">/100</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#f1eadb]">
        <div className="h-full bg-yolk" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}
