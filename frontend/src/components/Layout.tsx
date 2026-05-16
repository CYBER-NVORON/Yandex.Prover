import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, History } from 'lucide-react';
import type { ReactNode } from 'react';
import { useState } from 'react';
import type { AnalysisSummary } from '../api/types';
import { HistorySidebar } from './HistorySidebar';

interface LayoutProps {
  children: ReactNode;
  history: AnalysisSummary[];
  selectedId?: string;
  onSelectHistory: (id: string) => void;
}

export function Layout({ children, history, selectedId, onSelectHistory }: LayoutProps) {
  const [historyOpen, setHistoryOpen] = useState(false);

  return (
    <div className="min-h-screen bg-paper text-ink">
      <button
        type="button"
        className={`fixed top-5 z-50 grid h-11 w-11 place-items-center rounded-r-lg border border-l-0 border-[#e8e0cf] bg-white shadow-[0_10px_26px_rgba(16,17,20,0.08)] transition-all hover:bg-[#fff8df] ${
          historyOpen ? 'left-[calc(100vw-45px)] md:left-[319px]' : 'left-0'
        }`}
        onClick={() => setHistoryOpen((value) => !value)}
        aria-expanded={historyOpen}
        aria-controls="history-panel"
        aria-label={historyOpen ? 'Скрыть историю загрузок' : 'Показать историю загрузок'}
      >
        {historyOpen ? <ChevronLeft className="h-5 w-5" aria-hidden="true" /> : <ChevronRight className="h-5 w-5" aria-hidden="true" />}
      </button>

      <AnimatePresence initial={false}>
        {historyOpen ? (
          <>
            <motion.aside
              id="history-panel"
              key="history-panel"
              initial={{ x: -320, opacity: 0.8 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -320, opacity: 0.8 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="fixed inset-y-0 left-0 z-40 w-80 border-r border-[#e8e0cf] bg-white shadow-[18px_0_45px_rgba(16,17,20,0.10)]"
            >
              <div className="flex h-14 items-center gap-2 border-b border-[#e8e0cf] px-4">
                <History className="h-5 w-5 text-[#d97706]" aria-hidden="true" />
                <div className="text-sm font-extrabold">История загрузок</div>
              </div>
              <HistorySidebar history={history} selectedId={selectedId} onSelect={onSelectHistory} />
            </motion.aside>
            <motion.button
              key="history-backdrop"
              type="button"
              className="fixed inset-0 z-30 bg-black/10 md:hidden"
              aria-label="Закрыть историю загрузок"
              onClick={() => setHistoryOpen(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
          </>
        ) : null}
      </AnimatePresence>

      <main className={`app-shell transition-[padding-left] duration-300 ${historyOpen ? 'md:pl-[344px]' : ''}`}>
        <div className="mx-auto w-full max-w-none">{children}</div>
      </main>
    </div>
  );
}
