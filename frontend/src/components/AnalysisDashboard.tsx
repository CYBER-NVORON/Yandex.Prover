import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Clock, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import type {
  AnalysisResult,
  BenchmarkComparison,
  ComparisonItem,
  OverthinkingGuard,
  RegulationAnalysis,
  RegulationCheckItem,
  ScoringBreakdown,
  BenchmarkGapLevel,
  RiskLevel,
} from '../api/types';
import { ClaimCards } from './ClaimCards';
import { ClaimsTable } from './ClaimsTable';
import { ImprovementPlan } from './ImprovementPlan';
import { QuestionsPanel } from './QuestionsPanel';
import { ReportPanel } from './ReportPanel';
import { ScoreCard } from './ScoreCard';
import { StressTestCard } from './StressTestCard';

const tabs = [
  'Обзор',
  'Готово к защите?',
  'Регламент',
  'Сравнение с эталоном',
  'Главная мысль и структура',
  'Карта доказательности',
  'Слабые места',
  'Вопросы аудитории',
  'План улучшения',
  'Отчёт',
] as const;

type Tab = (typeof tabs)[number];

interface AnalysisDashboardProps {
  result: AnalysisResult;
}

export function AnalysisDashboard({ result }: AnalysisDashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('Обзор');
  const verdict = useMemo(() => {
    if (result.persuasiveness_score >= 80) {
      return 'Идея выглядит убедительно';
    }
    if (result.persuasiveness_score >= 60) {
      return 'Есть сильная база, но есть риски';
    }
    return 'Материал нужно усилить перед показом аудитории';
  }, [result.persuasiveness_score]);

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-center gap-4">
        <div className="quiet-card px-4 py-2 font-extrabold">{result.title}</div>
        <div className="quiet-card min-w-60 flex-1 px-4 py-2 font-semibold text-[#60616a]">{result.filename}</div>
      </div>

      <div className="scrollbar-thin overflow-x-auto border-b border-[#e8e0cf]">
        <div className="flex min-w-max gap-2">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              className={`rounded-t-lg px-3 py-2 text-sm font-bold transition ${activeTab === tab ? 'bg-[#fff1a8] text-ink shadow-[inset_0_-3px_0_#facc15]' : 'bg-transparent text-[#60616a] hover:bg-white'
                }`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
        >
          {activeTab === 'Обзор' ? <Overview result={result} verdict={verdict} /> : null}
          {activeTab === 'Готово к защите?' ? <ReadinessPanel guard={result.overthinking_guard} /> : null}
          {activeTab === 'Регламент' ? <RegulationPanel analysis={result.regulation_analysis} /> : null}
          {activeTab === 'Сравнение с эталоном' ? <BenchmarkPanel comparison={result.benchmark_comparison} /> : null}
          {activeTab === 'Главная мысль и структура' ? <Structure result={result} /> : null}
          {activeTab === 'Карта доказательности' ? (
            <EvidenceMap claims={result.claims} warnings={result.warnings} />
          ) : null}
          {activeTab === 'Слабые места' ? <Weaknesses result={result} /> : null}
          {activeTab === 'Вопросы аудитории' ? (
            <div className="space-y-5">
              <StressTestCard stressTest={result.stress_test} />
              <QuestionsPanel questions={result.audience_questions} />
            </div>
          ) : null}
          {activeTab === 'План улучшения' ? <ImprovementPlan plan={result.improvement_plan} /> : null}
          {activeTab === 'Отчёт' ? <ReportPanel analysisId={result.id} /> : null}
        </motion.div>
      </AnimatePresence>
    </section>
  );
}

function Overview({ result, verdict }: { result: AnalysisResult; verdict: string }) {
  const breakdown = result.scoring_breakdown;
  return (
    <div className="space-y-5">
      <Warnings warnings={result.warnings} />
      <div className="grid gap-5 lg:grid-cols-[150px_1fr]">
        <ScoreRing score={result.persuasiveness_score} />
        <div className="accent-card p-5">
          <h2 className="text-2xl font-extrabold">{verdict}</h2>
          <p className="mt-3 font-semibold leading-7 text-[#303138]">{result.summary}</p>
          <div className="mt-4 rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-3 text-sm font-semibold">
            ИИ-анализ выполнен по загруженному материалу без внешнего поиска.
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-[#e8e0cf] bg-white p-3 text-sm">
              <span className="font-black">Аудитория: {result.audience_knowledge_level}/5</span>
              <span className="mt-1 block font-semibold text-[#60616a]">{result.audience_knowledge_label}</span>
            </div>
            <div className="rounded-lg border border-[#d7e3dc] bg-[#f5fbf7] p-3 text-sm">
              <span className="font-black">Фокус без перегруза</span>
              <span className="mt-1 block font-semibold text-[#3f6650]">
                {result.overthinking_guard.next_best_three_actions.length} действия с максимальным эффектом
              </span>
            </div>
          </div>
        </div>
      </div>
      <ScoreGrid breakdown={breakdown} />
      <div className="grid gap-4 md:grid-cols-2">
        <TextBox title="Главная мысль" text={result.main_idea} />
        <TextBox title="Сильные стороны" items={result.strengths} />
      </div>
    </div>
  );
}

const readinessLabels: Record<OverthinkingGuard['readiness_verdict'], string> = {
  ready: 'Готово',
  almost_ready: 'Почти готово',
  needs_work: 'Нужно доработать',
};

const confidenceLabels: Record<OverthinkingGuard['confidence_level'], string> = {
  low: 'низкая',
  medium: 'средняя',
  high: 'высокая',
};

const riskLabels: Record<RiskLevel, string> = {
  low: 'низкий риск',
  medium: 'средний риск',
  high: 'высокий риск',
};

const gapLabels: Record<BenchmarkGapLevel, string> = {
  low: 'небольшое отличие',
  medium: 'заметное отличие',
  high: 'сильное отличие',
};

function ReadinessPanel({ guard }: { guard: OverthinkingGuard }) {
  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-[#d7e3dc] bg-[#f5fbf7] p-5 shadow-[0_10px_26px_rgba(16,17,20,0.04)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-black text-[#3f6650]">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
              Готово к защите?
            </div>
            <h2 className="mt-2 text-3xl font-black">{readinessLabels[guard.readiness_verdict]}</h2>
          </div>
          <div className="rounded-lg border border-[#cfe0d5] bg-white px-4 py-3 text-sm font-bold">
            Уверенность: {confidenceLabels[guard.confidence_level]}
          </div>
        </div>
        <p className="mt-4 max-w-3xl text-base font-semibold leading-7 text-[#303138]">{guard.reassuring_summary}</p>
      </section>

      <section className="soft-card p-5">
        <h3 className="text-xl font-extrabold">Вот 3 действия с максимальным эффектом</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {guard.next_best_three_actions.map((action, index) => (
            <div key={action} className="rounded-lg border border-[#d7e3dc] bg-[#f5fbf7] p-4">
              <div className="grid h-8 w-8 place-items-center rounded-full bg-white text-sm font-black text-[#3f6650]">{index + 1}</div>
              <p className="mt-3 text-sm font-bold leading-6">{action}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <CalmList title="Критично" items={guard.critical_fixes} empty="Критичных правок не выделено." tone="critical" />
        <CalmList title="Можно не трогать" items={guard.safe_to_ignore} empty="Нет отдельного списка." tone="calm" />
        <CalmList title="Что больше не делать" items={guard.stop_doing_list} empty="Нет отдельного списка." tone="calm" />
        <CalmList title="Желательно, но не критично" items={guard.optional_improvements} empty="Дополнительные улучшения не обязательны." tone="optional" />
      </div>

      <section className="soft-card p-5">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-[#3f6650]" aria-hidden="true" />
          <h3 className="text-xl font-extrabold">План по времени</h3>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {Object.entries(guard.timeboxed_plan).map(([label, actions]) => (
            <div key={label} className="rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-4">
              <div className="font-black">{label}</div>
              <ul className="mt-3 space-y-2 text-sm font-semibold leading-5 text-[#303138]">
                {actions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-4 rounded-lg border border-[#d7e3dc] bg-[#f5fbf7] p-4 text-sm font-bold text-[#31533f]">
          {guard.when_to_stop}
        </p>
      </section>
    </div>
  );
}

function CalmList({
  title,
  items,
  empty,
  tone,
}: {
  title: string;
  items: string[];
  empty: string;
  tone: 'critical' | 'optional' | 'calm';
}) {
  const toneClass =
    tone === 'critical'
      ? 'border-amber-200 bg-amber-50'
      : tone === 'optional'
        ? 'border-[#e8e0cf] bg-[#fbf7ec]'
        : 'border-[#d7e3dc] bg-[#f5fbf7]';
  return (
    <section className="soft-card p-5">
      <h3 className="text-lg font-extrabold">{title}</h3>
      <ul className="mt-3 space-y-2">
        {(items.length ? items : [empty]).map((item) => (
          <li key={item} className={`rounded-lg border p-3 text-sm font-semibold leading-6 ${toneClass}`}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function RegulationPanel({ analysis }: { analysis: RegulationAnalysis | null }) {
  if (!analysis) {
    return <EmptyState text="Регламент не загружен. Сервис оценил материал по общим критериям." />;
  }
  return (
    <div className="space-y-5">
      <section className="accent-card p-5">
        <h2 className="text-2xl font-extrabold">Соответствие регламенту</h2>
        <p className="mt-3 font-semibold leading-7 text-[#303138]">{analysis.summary}</p>
        {analysis.event_regulation?.event_name ? (
          <p className="mt-3 text-sm font-bold text-[#60616a]">{analysis.event_regulation.event_name}</p>
        ) : null}
      </section>
      <div className="grid gap-4 md:grid-cols-3">
        <TextBox title="Выполнено" items={analysis.matched_requirements} />
        <TextBox title="Не выполнено" items={analysis.missing_requirements} />
        <TextBox title="Рискованные требования" items={analysis.high_risk_requirements} />
      </div>
      <section className="soft-card overflow-hidden">
        <div className="border-b border-[#e8e0cf] p-4">
          <h3 className="text-xl font-extrabold">Чек-лист соответствия</h3>
        </div>
        <div className="divide-y divide-[#e8e0cf]">
          {analysis.checklist.map((item) => (
            <RegulationChecklistItem key={`${item.requirement}-${item.status}`} item={item} />
          ))}
        </div>
      </section>
    </div>
  );
}

const regulationStatusLabels: Record<RegulationCheckItem['status'], string> = {
  met: 'выполнено',
  missing: 'не найдено',
  partially_met: 'частично',
  unverifiable: 'не проверить',
};

function RegulationChecklistItem({ item }: { item: RegulationCheckItem }) {
  const statusClass =
    item.status === 'met'
      ? 'bg-emerald-50 text-emerald-800'
      : item.status === 'missing'
        ? 'bg-rose-100 text-rose-800'
        : 'bg-amber-100 text-amber-900';
  return (
    <article className="grid gap-3 p-4 lg:grid-cols-[1fr_160px]">
      <div>
        <h4 className="font-extrabold">{item.requirement}</h4>
        <p className="mt-2 text-sm text-[#60616a]">{item.evidence_from_material}</p>
        <p className="mt-2 text-sm font-bold">{item.recommendation}</p>
      </div>
      <div className="flex flex-wrap items-start gap-2 lg:justify-end">
        <span className={`rounded-full px-3 py-1 text-xs font-black ${statusClass}`}>{regulationStatusLabels[item.status]}</span>
        <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-black text-zinc-800">{riskLabels[item.risk_level]}</span>
      </div>
    </article>
  );
}

function BenchmarkPanel({ comparison }: { comparison: BenchmarkComparison | null }) {
  if (!comparison) {
    return <EmptyState text="Эталонная работа не загружена. Сравнение не выполнялось." />;
  }
  return (
    <div className="space-y-5">
      <section className="accent-card p-5">
        <h2 className="text-2xl font-extrabold">Сравнение с эталоном</h2>
        <p className="mt-3 font-semibold leading-7 text-[#303138]">{comparison.summary}</p>
        <p className="mt-3 rounded-lg border border-[#d7dbe8] bg-[#f7f8fc] p-3 text-sm font-bold text-[#334155]">
          {comparison.do_not_copy_warning}
        </p>
      </section>
      <div className="grid gap-4 md:grid-cols-2">
        <TextBox title="Что у вас уже хорошо" items={comparison.what_user_material_does_better} />
        <TextBox title="Что эталон делает сильнее" items={comparison.what_benchmark_does_better} />
      </div>
      <section className="soft-card overflow-hidden">
        {/* <div className="border-b border-[#e8e0cf] p-4">
          <h3 className="text-xl font-extrabold">Различия</h3>
        </div> */}
        <div className="divide-y divide-[#e8e0cf]">
          {comparison.comparison_items.map((item) => (
            <GapRow key={item.aspect} item={item} />
          ))}
        </div>
      </section>
      <div className="grid gap-4 md:grid-cols-2">
        <TextBox title="Недостающие элементы" items={comparison.missing_elements} />
        <TextBox title="Что сделать" items={comparison.action_items} />
      </div>
    </div>
  );
}

function GapRow({ item }: { item: ComparisonItem }) {
  const gapClass =
    item.gap_level === 'high'
      ? 'bg-rose-100 text-rose-800'
      : item.gap_level === 'medium'
        ? 'bg-amber-100 text-amber-900'
        : 'bg-emerald-50 text-emerald-800';
  return (
    <article className="grid gap-3 p-4 lg:grid-cols-[180px_1fr_1fr]">
      <div>
        <h4 className="font-extrabold">{item.aspect}</h4>
        <span className={`mt-2 inline-flex rounded-full px-3 py-1 text-xs font-black ${gapClass}`}>{gapLabels[item.gap_level]}</span>
      </div>
      <p className="text-sm font-semibold leading-6 text-[#303138]">{item.user_material_observation}</p>
      <div>
        <p className="text-sm font-semibold leading-6 text-[#60616a]">{item.benchmark_observation}</p>
        <p className="mt-2 text-sm font-bold">{item.recommendation}</p>
      </div>
    </article>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <section className="soft-card p-6">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[#3f6650]" aria-hidden="true" />
        <p className="font-bold leading-7 text-[#303138]">{text}</p>
      </div>
    </section>
  );
}

function ScoreRing({ score }: { score: number }) {
  const normalized = Math.max(0, Math.min(100, score));
  return (
    <div className="flex items-center justify-center">
      <div
        className="grid h-36 w-36 place-items-center rounded-full bg-white shadow-[0_10px_26px_rgba(16,17,20,0.08)]"
        style={{ background: `conic-gradient(#facc15 ${normalized * 3.6}deg, #ffffff 0deg)` }}
      >
        <div className="grid h-28 w-28 place-items-center rounded-full bg-white text-4xl font-black">{score}%</div>
      </div>
    </div>
  );
}

function ScoreGrid({ breakdown }: { breakdown: ScoringBreakdown }) {
  const cards = [
    ['Ясность', breakdown.clarity_score],
    ['Структура', breakdown.structure_score],
    ['Аргументы', breakdown.argument_score],
    ['Доказательность', breakdown.evidence_score],
    ['Аудитория', breakdown.audience_score],
    ['Вопросы', breakdown.question_readiness_score],
  ] as const;

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {cards.map(([label, value]) => (
        <ScoreCard key={label} label={label} value={value} />
      ))}
    </div>
  );
}

function Structure({ result }: { result: AnalysisResult }) {
  return (
    <div className="grid gap-4">
      <TextBox title="Главная мысль" text={result.main_idea} />
      <TextBox title="Цель" text={result.structure_analysis.goal} />
      <TextBox title="Структура" text={result.structure_analysis.structure_summary} />
      <div className="grid gap-4 md:grid-cols-2">
        <TextBox title="Проблемы структуры" items={result.structure_analysis.problems} />
        <TextBox title="Что улучшить" items={result.structure_analysis.suggestions} />
      </div>
    </div>
  );
}

function EvidenceMap({ claims, warnings }: Pick<AnalysisResult, 'claims' | 'warnings'>) {
  return (
    <div className="space-y-5">
      <Warnings warnings={warnings} />
      <div className="accent-card p-4 text-sm font-bold">
        Оценка строится только по загруженному материалу. Внешняя проверка источников не выполняется.
      </div>
      <ClaimCards claims={claims} />
      <ClaimsTable claims={claims} />
    </div>
  );
}

function Weaknesses({ result }: { result: AnalysisResult }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {result.weaknesses.map((weakness) => (
        <article key={weakness.problem} className="soft-card p-5">
          <h3 className="text-xl font-extrabold">{weakness.problem}</h3>
          <p className="mt-3 text-sm text-[#60616a]">{weakness.why_problem}</p>
          <p className="mt-3 rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-3 text-sm font-semibold">{weakness.audience_signal}</p>
          <p className="mt-3 text-sm font-bold">{weakness.fix}</p>
        </article>
      ))}
    </div>
  );
}

function Warnings({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) {
    return null;
  }
  return (
    <div className="space-y-2">
      {warnings.map((warning) => (
        <div key={warning} className="flex items-start gap-2 rounded-lg border border-amber-200 border-l-4 border-l-amber-400 bg-amber-50 p-3 text-sm font-bold">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{localizeWarning(warning)}</span>
        </div>
      ))}
    </div>
  );
}

function localizeWarning(warning: string) {
  return warning
    .replaceAll('анализа claims', 'анализа утверждений')
    .replaceAll('из claims', 'из карты доказательности')
    .replaceAll('claims', 'утверждений');
}

function TextBox({ title, text, items }: { title: string; text?: string; items?: string[] }) {
  return (
    <section className="soft-card p-5">
      <h3 className="text-lg font-extrabold">{title}</h3>
      {text ? <p className="mt-3 leading-7 text-zinc-800">{text}</p> : null}
      {items ? (
        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <li key={item} className="rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-3 text-sm font-semibold">
              {item}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
