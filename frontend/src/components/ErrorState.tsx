import { AlertTriangle } from 'lucide-react';

interface ErrorStateProps {
  message: string;
  onDismiss: () => void;
}

export function ErrorState({ message, onDismiss }: ErrorStateProps) {
  const isYandex403 = message.toLowerCase().includes('yandex ai отклонил') || message.includes('ai.assistants.editor');

  return (
    <div className="rounded-lg border border-red-200 border-l-4 border-l-red-500 bg-red-50 p-5 text-red-950 shadow-[0_10px_26px_rgba(16,17,20,0.05)]">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-1 h-6 w-6 shrink-0" aria-hidden="true" />
        <div>
          <h2 className="text-lg font-black">Не удалось выполнить анализ</h2>
          <p className="mt-2 text-sm font-semibold">{message}</p>
          {isYandex403 ? (
            <p className="mt-3 text-sm">
              Проверьте folder id, API key, роли ai.assistants.editor и ai.languageModels.user, а также активный
              биллинг в Yandex Cloud.
            </p>
          ) : null}
          <button
            type="button"
            className="mt-4 rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-black hover:bg-red-100"
            onClick={onDismiss}
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
