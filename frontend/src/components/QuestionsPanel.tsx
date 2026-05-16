import type { AudienceQuestion } from '../api/types';
import { RiskBadge } from './RiskBadge';

interface QuestionsPanelProps {
  questions: AudienceQuestion[];
}

export function QuestionsPanel({ questions }: QuestionsPanelProps) {
  return (
    <div className="grid gap-4">
      {questions.map((question) => (
        <article key={question.id} className="soft-card p-5">
          <div className="flex flex-wrap items-center gap-3">
            <RiskBadge risk={question.risk_level} />
            <span className="rounded-full border border-[#f0d24a] bg-[#fff1a8] px-2.5 py-1 text-xs font-black text-[#201a05]">{question.category}</span>
            <span className="text-sm font-black text-[#60616a]">{question.asked_by}</span>
          </div>
          <h3 className="mt-3 text-xl font-extrabold">{question.question}</h3>
          <p className="mt-3 text-sm text-[#60616a]">
            <span className="font-black text-ink">Почему зададут: </span>
            {question.why_asked}
          </p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-3">
              <div className="text-xs font-black uppercase text-[#60616a]">Рекомендуемый ответ</div>
              <p className="mt-2 text-sm font-semibold">{question.suggested_answer}</p>
            </div>
            <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-3">
              <div className="text-xs font-black uppercase text-[#60616a]">Что добавить</div>
              <p className="mt-2 text-sm font-semibold">{question.how_to_improve_material}</p>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
