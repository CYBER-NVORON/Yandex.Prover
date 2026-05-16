import { Clipboard, Download } from 'lucide-react';
import { useEffect, useState } from 'react';
import { downloadReport, getReport } from '../api/client';

interface ReportPanelProps {
  analysisId: string;
}

export function ReportPanel({ analysisId }: ReportPanelProps) {
  const [markdown, setMarkdown] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getReport(analysisId)
      .then((report) => {
        if (active) {
          setMarkdown(report.markdown);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : 'Не удалось загрузить отчёт.');
        }
      });
    return () => {
      active = false;
    };
  }, [analysisId]);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="primary-button px-4 py-2"
          onClick={() => void downloadReport(analysisId)}
        >
          <Download className="h-5 w-5" aria-hidden="true" />
          Скачать отчёт
        </button>
        <button
          type="button"
          className="secondary-button px-4 py-2"
          onClick={() => void navigator.clipboard.writeText(markdown)}
          disabled={!markdown}
        >
          <Clipboard className="h-5 w-5" aria-hidden="true" />
          Скопировать отчёт
        </button>
      </div>
      {error ? <div className="rounded-lg border border-red-200 border-l-4 border-l-red-500 bg-red-50 p-4 font-semibold text-red-950">{error}</div> : null}
      <pre className="soft-card max-h-[560px] overflow-auto whitespace-pre-wrap p-5 text-sm leading-6">
        {markdown || 'Загружаем отчёт...'}
      </pre>
    </section>
  );
}
