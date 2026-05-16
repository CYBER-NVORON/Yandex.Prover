import { FileText } from 'lucide-react';
import type { ChangeEvent } from 'react';
import type { AnalysisSummary } from '../api/types';

interface HistorySidebarProps {
  history: AnalysisSummary[];
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function HistorySidebar({ history, selectedId, onSelect }: HistorySidebarProps) {
  function handleSelect(event: ChangeEvent<HTMLSelectElement>) {
    if (event.target.value) {
      onSelect(event.target.value);
    }
  }

  return (
    <div className="h-[calc(100vh-56px)] overflow-y-auto p-4">
      <div className="mb-4 text-xs font-bold uppercase tracking-wide text-[#60616a]">
        Последние материалы
      </div>

      {history.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[#d8ccb7] bg-[#fbf7ec] p-3 text-sm text-[#60616a]">
          Пока нет анализов. После первой загрузки материалы появятся здесь.
        </div>
      ) : (
        <div className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-[#60616a]">Открыть анализ</span>
            <select className="field py-2 text-sm" value={selectedId ?? ''} onChange={handleSelect}>
              <option value="">Выберите материал</option>
              {history.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.filename} · {item.persuasiveness_score}%
                </option>
              ))}
            </select>
          </label>

          <div className="space-y-2">
            {history.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelect(item.id)}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  selectedId === item.id
                    ? 'border-[#f0d24a] bg-[#fff1a8]'
                    : 'border-[#e8e0cf] bg-white hover:bg-[#fff8df]'
                }`}
              >
                <div className="flex items-start gap-2">
                  <FileText className="mt-0.5 h-4 w-4 shrink-0 text-[#d97706]" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-bold text-ink">{item.filename}</div>
                <div className="mt-1 flex items-center justify-between gap-2 text-xs text-[#60616a]">
                  <span className="truncate">{item.material_type}</span>
                  <span className="font-extrabold text-ink">{item.persuasiveness_score}%</span>
                </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
