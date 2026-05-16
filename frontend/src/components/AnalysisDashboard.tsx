import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { AnalysisResult, ScoringBreakdown } from '../api/types';
import { ClaimCards } from './ClaimCards';
import { ClaimsTable } from './ClaimsTable';
import { ImprovementPlan } from './ImprovementPlan';
import { QuestionsPanel } from './QuestionsPanel';
import { ReportPanel } from './ReportPanel';
import { ScoreCard } from './ScoreCard';
import { StressTestCard } from './StressTestCard';

const tabs = [
  'Обзор',
  'Главная мысль и структура',
  'Карта доказательности',
  'Слабые места',
  'Вопросы аудитории',
  'План улучшения',
  'Разнеси мою идею',
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
              className={`rounded-t-lg px-3 py-2 text-sm font-bold transition ${
                activeTab === tab ? 'bg-[#fff1a8] text-ink shadow-[inset_0_-3px_0_#facc15]' : 'bg-transparent text-[#60616a] hover:bg-white'
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
          {activeTab === 'Главная мысль и структура' ? <Structure result={result} /> : null}
          {activeTab === 'Карта доказательности' ? (
            <EvidenceMap claims={result.claims} warnings={result.warnings} />
          ) : null}
          {activeTab === 'Слабые места' ? <Weaknesses result={result} /> : null}
          {activeTab === 'Вопросы аудитории' ? <QuestionsPanel questions={result.audience_questions} /> : null}
          {activeTab === 'План улучшения' ? <ImprovementPlan plan={result.improvement_plan} /> : null}
          {activeTab === 'Разнеси мою идею' ? <StressTestCard stressTest={result.stress_test} /> : null}
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
            {result.is_mock
              ? 'Демо-режим: mock provider'
              : 'Анализ выполнен через Alice AI / Yandex AI'}
            <span className="block text-[#60616a]">Модель: {result.provider_model}</span>
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
          <span>{warning}</span>
        </div>
      ))}
    </div>
  );
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
