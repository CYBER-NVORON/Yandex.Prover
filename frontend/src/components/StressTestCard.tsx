import { Flame } from 'lucide-react';
import type { StressTest } from '../api/types';

interface StressTestCardProps {
  stressTest: StressTest;
}

export function StressTestCard({ stressTest }: StressTestCardProps) {
  return (
    <article className="rounded-lg bg-[#101114] p-6 text-white shadow-[0_18px_45px_rgba(16,17,20,0.16)]">
      <div className="flex items-center gap-3">
        <Flame className="h-7 w-7 text-yolk" aria-hidden="true" />
        <h2 className="text-2xl font-black">Разнеси мою идею</h2>
      </div>
      <div className="mt-6 rounded-lg border border-[#facc15] bg-white p-5 text-ink">
        <div className="text-xs font-black uppercase text-[#60616a]">Самый опасный вопрос</div>
        <p className="mt-2 text-2xl font-black leading-snug">{stressTest.most_dangerous_question}</p>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <InfoBlock title="Почему опасен" text={stressTest.why_dangerous} />
        <InfoBlock title="Слабое место" text={stressTest.exposed_weakness} />
        <InfoBlock title="Как ответить" text={stressTest.suggested_answer} />
        <InfoBlock title="Что добавить" text={stressTest.what_to_add} />
      </div>
    </article>
  );
}

function InfoBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-lg border border-white/20 bg-white/5 p-4">
      <div className="text-xs font-black uppercase text-yolk">{title}</div>
      <p className="mt-2 text-sm font-semibold leading-6">{text}</p>
    </div>
  );
}
