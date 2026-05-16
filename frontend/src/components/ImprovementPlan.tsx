import { CheckCircle2 } from 'lucide-react';
import type { ImprovementPlan as ImprovementPlanType } from '../api/types';

interface ImprovementPlanProps {
  plan: ImprovementPlanType;
}

const columns = [
  ['За 30 минут', 'quick_fixes_30_min'],
  ['За 2 часа', 'improvements_2_hours'],
  ['До финальной версии', 'final_polish'],
] as const;

export function ImprovementPlan({ plan }: ImprovementPlanProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {columns.map(([title, key]) => (
        <section key={key} className="soft-card p-5">
          <h3 className="text-xl font-extrabold">{title}</h3>
          <div className="mt-4 space-y-3">
            {plan[key].map((item) => (
              <div key={item} className="flex items-start gap-2 rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-3 text-sm">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#d97706]" aria-hidden="true" />
                <span className="font-semibold">{item}</span>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
