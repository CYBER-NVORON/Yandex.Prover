import { motion } from 'framer-motion';
import { HelpCircle, Search, ShieldCheck } from 'lucide-react';

const features = [
  {
    title: 'Находит слабые места',
    text: 'Показывает, где главная мысль теряется, аргумент звучит как мнение или вывод слишком широкий.',
    icon: Search,
  },
  {
    title: 'Проверяет доказательность',
    text: 'Отмечает утверждения, которым нужен источник или подтверждение внутри материала.',
    icon: ShieldCheck,
  },
  {
    title: 'Готовит вопросы аудитории',
    text: 'Формирует вопросы для предзащиты и стресс-теста. Сервис проверяет готовую работу.',
    icon: HelpCircle,
  },
];

export function Hero() {
  return (
    <section className="space-y-5">
      <motion.div
        className="app-card p-7 md:p-9"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <div className="mb-4 inline-flex rounded-full border border-[#f0d24a] bg-[#fff1a8] px-3 py-1 text-sm font-extrabold text-[#201a05]">
          AI-рецензент для предзащиты
        </div>
        <h1 className="text-5xl font-black leading-tight tracking-normal md:text-6xl">Доказатель</h1>
        <p className="mt-3 max-w-3xl text-xl font-semibold leading-8">Проверь, выдержит ли твоя идея вопросы аудитории.</p>
        <p className="mt-4 max-w-3xl text-base leading-7 text-[#60616a]">
          AI-рецензент для текстов, работ и выступлений. Сервис анализирует готовый материал, находит слабые места до
          того, как их найдёт аудитория, и помогает подготовить доказательную защиту.
        </p>
      </motion.div>

      <div className="grid gap-4 md:grid-cols-3">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <motion.article
              key={feature.title}
              className="soft-card min-h-36 p-5"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.08 * index }}
              whileHover={{ y: -4 }}
            >
              <Icon className="mb-3 h-6 w-6 text-[#d97706]" aria-hidden="true" />
              <h2 className="text-lg font-extrabold leading-tight">{feature.title}</h2>
              <p className="mt-2 text-sm leading-6 text-[#60616a]">{feature.text}</p>
            </motion.article>
          );
        })}
      </div>
    </section>
  );
}
