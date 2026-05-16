import { FileUp, Play, X } from 'lucide-react';
import { FormEvent, useState } from 'react';

const materialTypes = [
  'реферат',
  'сочинение',
  'доклад',
  'курсовая',
  'диплом',
  'презентация/питч проекта',
  'публичное выступление',
];

const audienceTypes = ['учитель', 'преподаватель', 'комиссия', 'жюри', 'инвестор', 'коллеги', 'широкая аудитория'];

interface UploadPanelProps {
  disabled?: boolean;
  onSubmit: (payload: { file: File; title: string; materialType: string; audienceType: string }) => void;
}

export function UploadPanel({ disabled, onSubmit }: UploadPanelProps) {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [materialType, setMaterialType] = useState(materialTypes[0]);
  const [audienceType, setAudienceType] = useState(audienceTypes[0]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }
    onSubmit({ file, title, materialType, audienceType });
  }

  return (
    <form className="app-card mt-7 w-full space-y-5 p-5 md:p-6" onSubmit={submit}>
      <div>
        <h2 className="section-title">Загрузить материал</h2>
        <p className="mt-1 text-sm text-[#60616a]">Сервис проверяет готовый текст, презентацию или питч без внешнего поиска.</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(260px,0.8fr)_minmax(360px,1.2fr)]">
        <label className="block">
          <span className="sr-only">Название</span>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Название..."
            className="field"
            disabled={disabled}
          />
        </label>

        <label className="flex min-h-28 cursor-pointer flex-col justify-center rounded-lg border border-dashed border-[#d8ccb7] bg-[#fbf7ec] px-4 py-5 transition hover:bg-[#fff8df]">
          <span className="flex items-center gap-2 font-black">
            <FileUp className="h-5 w-5 text-[#d97706]" aria-hidden="true" />
            {file ? file.name : 'Добавить файл...'}
          </span>
          <span className="mt-2 text-sm text-[#60616a]">TXT, Markdown, PDF, DOCX или PPTX</span>
          <input
            type="file"
            accept=".txt,.md,.pdf,.docx,.pptx"
            className="sr-only"
            disabled={disabled}
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="sr-only">Тип материала</span>
          <select
            value={materialType}
            onChange={(event) => setMaterialType(event.target.value)}
            className="field"
            disabled={disabled}
          >
            {materialTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="sr-only">Аудитория</span>
          <select
            value={audienceType}
            onChange={(event) => setAudienceType(event.target.value)}
            className="field"
            disabled={disabled}
          >
            {audienceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:max-w-xl">
        <button
          type="button"
          className="secondary-button"
          disabled={disabled}
          onClick={() => {
            setTitle('');
            setFile(null);
          }}
        >
          <X className="h-5 w-5" aria-hidden="true" />
          Отмена
        </button>
        <button
          type="submit"
          className="primary-button"
          disabled={disabled || !file}
        >
          <Play className="h-5 w-5" aria-hidden="true" />
          Проанализировать
        </button>
      </div>
    </form>
  );
}
