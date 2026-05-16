import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { useState } from 'react';

const faq = [
  ['Что проверяет?', 'Готовый материал: структуру, доказательства, риски, вопросы аудитории.'],
  ['Что можно загрузить?', 'Основной файл обязателен. Регламент и эталон можно добавить отдельно.'],
  ['Пишет ли работу?', 'Нет. Сервис не генерирует работу за автора и не копирует эталон.'],
  ['Когда остановиться?', 'Во вкладке “Готово к защите?” есть 3 главных действия и стоп-условие.'],
];

export function Hero() {
  const [faqOpen, setFaqOpen] = useState(false);

  return (
    <>
      <header className="relative flex justify-center pt-1">
        <motion.div
          className="flex items-center gap-3"
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.28 }}
        >
          <div className="grid h-12 w-12 place-items-center rounded-lg border-2 border-[#101114] bg-[#ffcc00] text-2xl font-black shadow-[5px_5px_0_#101114]">
            Д
          </div>
          <div className="text-center">
            <h1 className="text-3xl font-black leading-none tracking-normal md:text-4xl">Доказатель</h1>
            <p className="mt-1 text-sm font-bold text-[#60616a]">Предзащита без лишней тревоги</p>
          </div>
        </motion.div>

        <motion.button
          type="button"
          className="fixed right-5 top-5 z-[60] grid h-12 w-12 place-items-center rounded-full border-2 border-[#101114] bg-white ring-4 ring-[#ffcc00] ring-offset-2 ring-offset-[#f4f1e8] transition hover:-translate-y-0.5 hover:bg-[#fffbdb]"
          onClick={() => setFaqOpen(true)}
          aria-label="Открыть справку"
          whileTap={{ scale: 0.94 }}
        >
          <span className="-translate-y-[1px] text-[28px] font-black leading-none text-[#101114]">?</span>
        </motion.button>
      </header>

      <AnimatePresence>
        {faqOpen ? (
          <motion.div
            className="fixed inset-0 z-[80] grid place-items-center bg-[#101114]/24 p-4 backdrop-blur-[2px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.section
              role="dialog"
              aria-modal="true"
              aria-label="Справка"
              className="w-full max-w-xl rounded-xl border-2 border-[#101114] bg-white p-5 shadow-[10px_10px_0_#ffcc00]"
              initial={{ opacity: 0, scale: 0.94, y: 18, rotate: -0.4 }}
              animate={{ opacity: 1, scale: 1, y: 0, rotate: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 12 }}
              transition={{ type: 'spring', stiffness: 260, damping: 22 }}
            >
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-2xl font-black">Справка</h2>
                <button
                  type="button"
                  className="grid h-10 w-10 place-items-center rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] transition hover:bg-[#ffef8a]"
                  onClick={() => setFaqOpen(false)}
                  aria-label="Закрыть справку"
                >
                  <X className="h-5 w-5" aria-hidden="true" />
                </button>
              </div>
              <div className="mt-4 space-y-2">
                {faq.map(([question, answer], index) => (
                  <motion.div
                    key={question}
                    className="rounded-lg border border-[#e8e0cf] bg-[#fbf7ec] p-3"
                    initial={{ opacity: 0, x: 18 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                  >
                    <div className="font-black">{question}</div>
                    <p className="mt-1 text-sm font-semibold leading-6 text-[#60616a]">{answer}</p>
                  </motion.div>
                ))}
              </div>
            </motion.section>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
