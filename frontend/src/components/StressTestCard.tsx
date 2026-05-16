import { CircleHelp } from 'lucide-react';
import type { StressTest } from '../api/types';

interface StressTestCardProps {
  stressTest: StressTest;
}

export function StressTestCard({ stressTest }: StressTestCardProps) {
  return (
    <article className="rounded-lg border border-[#d7e3dc] bg-[#f5fbf7] p-6 shadow-[0_10px_26px_rgba(16,17,20,0.05)]">
      <div className="flex items-center gap-3">
        <CircleHelp className="h-7 w-7 text-[#3f6650]" aria-hidden="true" />
        <h2 className="text-2xl font-black">Самый важный вопрос</h2>
      </div>
      <div className="mt-6 rounded-lg border border-[#d7e3dc] bg-white p-5 text-ink">
        <div className="text-xs font-black uppercase text-[#60616a]">Вопрос, к которому стоит подготовиться</div>
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
    <div className="rounded-lg border border-[#d7e3dc] bg-white p-4">
      <div className="text-xs font-black uppercase text-[#3f6650]">{title}</div>
      <p className="mt-2 text-sm font-semibold leading-6 text-[#303138]">{text}</p>
    </div>
  );
}
