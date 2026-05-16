import { motion } from 'framer-motion';

const steps = ['Извлекаем текст', 'Ищем главную мысль', 'Проверяем доказательность', 'Готовим вопросы аудитории'];

export function LoadingState() {
  return (
    <div className="app-card p-8">
      <div className="flex items-center gap-5">
        <motion.div
          className="h-16 w-16 rounded-full border-8 border-yolk border-r-transparent"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1.1, ease: 'linear' }}
        />
        <div>
          <h2 className="text-2xl font-black">Идёт анализ</h2>
          <p className="mt-1 max-w-xl text-sm text-[#60616a]">
            Сервис проверяет только загруженный материал и не ищет внешние источники.
          </p>
        </div>
      </div>
      <div className="mt-8 grid gap-3 md:grid-cols-4">
        {steps.map((step, index) => (
          <motion.div
            key={step}
            className="rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-4 text-sm font-bold"
            animate={{ y: [0, -6, 0] }}
            transition={{ repeat: Infinity, duration: 1.5, delay: index * 0.18 }}
          >
            {step}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
