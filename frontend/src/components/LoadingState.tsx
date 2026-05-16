import { motion } from 'framer-motion';
import { Check, FileSearch, ListChecks, MessageCircleQuestion, ShieldCheck, Wand2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

const steps = [
  { title: 'Текст', caption: 'извлекаем', icon: FileSearch },
  { title: 'Утверждения', caption: 'отделяем от шума', icon: ListChecks },
  { title: 'Доказательность', caption: 'ищем риски', icon: ShieldCheck },
  { title: 'Вопросы', caption: 'готовим аудиторию', icon: MessageCircleQuestion },
  { title: 'Фокус', caption: '3 действия', icon: Wand2 },
];

export function LoadingState() {
  const [activeStep, setActiveStep] = useState(0);
  const progress = useMemo(() => Math.round(((activeStep + 1) / steps.length) * 100), [activeStep]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveStep((step) => (step < steps.length - 1 ? step + 1 : step));
    }, 1700);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <motion.section
      className="app-card yandex-panel overflow-hidden p-5"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24 }}
    >
      <div className="grid gap-5 lg:grid-cols-[180px_1fr]">
        <div className="grid place-items-center">
          <motion.div
            className="relative grid h-36 w-36 place-items-center rounded-full border-2 border-[#101114] bg-white shadow-[7px_7px_0_#ffcc00]"
            animate={{ rotate: [0, -1.5, 1.5, 0] }}
            transition={{ repeat: Infinity, duration: 2.8, ease: 'easeInOut' }}
          >
            <div
              className="absolute inset-3 rounded-full"
              style={{ background: `conic-gradient(#fc3f1d ${progress * 3.6}deg, #f0eadb 0deg)` }}
            />
            <div className="relative grid h-24 w-24 place-items-center rounded-full bg-white text-3xl font-black">
              {progress}%
            </div>
          </motion.div>
        </div>

        <div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-2xl font-black">Анализ идёт</h2>
              <p className="mt-1 text-sm font-semibold text-[#60616a]">Проверяем файл по шагам. Без внешнего поиска.</p>
            </div>
            <motion.div
              className="rounded-full border-2 border-[#101114] bg-[#ffcc00] px-4 py-2 text-sm font-black shadow-[3px_3px_0_#101114]"
              animate={{ y: [0, -3, 0] }}
              transition={{ repeat: Infinity, duration: 1.4 }}
            >
              шаг {Math.min(activeStep + 1, steps.length)} / {steps.length}
            </motion.div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-5">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isDone = index < activeStep;
              const isActive = index === activeStep;
              return (
                <motion.article
                  key={step.title}
                  className={`relative min-h-32 rounded-lg border-2 p-3 ${isDone
                      ? 'border-[#2f7a4f] bg-[#e8f8ee]'
                      : isActive
                        ? 'border-[#101114] bg-white shadow-[4px_4px_0_#ffcc00]'
                        : 'border-[#e8e0cf] bg-[#fbf7ec]'
                    }`}
                  animate={isActive ? { y: [0, -6, 0], rotate: [0, -0.7, 0.7, 0] } : { y: 0, rotate: 0 }}
                  transition={{ repeat: isActive ? Infinity : 0, duration: 1.5 }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className={`grid h-10 w-10 place-items-center rounded-full ${isDone ? 'bg-[#2f7a4f] text-white' : 'bg-[#ffcc00]'}`}>
                      {isDone ? <Check className="h-5 w-5" aria-hidden="true" /> : <Icon className="h-5 w-5" aria-hidden="true" />}
                    </div>
                    {isActive ? (
                      <motion.span
                        className="h-2 w-2 rounded-full bg-[#fc3f1d]"
                        animate={{ scale: [1, 1.7, 1], opacity: [1, 0.45, 1] }}
                        transition={{ repeat: Infinity, duration: 0.9 }}
                      />
                    ) : null}
                  </div>
                  <h3 className="mt-4 text-sm font-black">{step.title}</h3>
                  <p className="mt-1 text-xs font-semibold leading-5 text-[#60616a]">{step.caption}</p>
                </motion.article>
              );
            })}
          </div>
        </div>
      </div>
    </motion.section>
  );
}
