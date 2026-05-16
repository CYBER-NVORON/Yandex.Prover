import { motion } from 'framer-motion';
import { FileCheck2, FileText, FileUp, Play, RotateCcw, Users } from 'lucide-react';
import type { CSSProperties } from 'react';
import { FormEvent, useState } from 'react';
import type { UploadAnalysisPayload } from '../api/types';

const customOption = 'Свой вариант';

const materialTypes = [
  'реферат',
  'сочинение',
  'доклад',
  'курсовая',
  'диплом',
  'презентация/питч проекта',
  'публичное выступление',
  customOption,
];

const audienceTypes = ['учитель', 'преподаватель', 'комиссия', 'жюри', 'инвестор', 'коллеги', 'широкая аудитория', customOption];

interface UploadPanelProps {
  disabled?: boolean;
  onSubmit: (payload: UploadAnalysisPayload) => void;
}

export function UploadPanel({ disabled, onSubmit }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [regulationFile, setRegulationFile] = useState<File | null>(null);
  const [benchmarkFile, setBenchmarkFile] = useState<File | null>(null);
  const [materialType, setMaterialType] = useState(materialTypes[0]);
  const [audienceType, setAudienceType] = useState(audienceTypes[0]);
  const [customMaterialType, setCustomMaterialType] = useState('');
  const [customAudienceType, setCustomAudienceType] = useState('');
  const [audienceKnowledgeLevel, setAudienceKnowledgeLevel] = useState(3);

  const resolvedMaterialType = materialType === customOption ? customMaterialType.trim() : materialType;
  const resolvedAudienceType = audienceType === customOption ? customAudienceType.trim() : audienceType;
  const canSubmit = Boolean(file && resolvedMaterialType && resolvedAudienceType);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || !resolvedMaterialType || !resolvedAudienceType) {
      return;
    }
    onSubmit({
      file,
      materialType: resolvedMaterialType,
      audienceType: resolvedAudienceType,
      audienceKnowledgeLevel,
      regulationFile,
      benchmarkFile,
    });
  }

  function reset() {
    setFile(null);
    setRegulationFile(null);
    setBenchmarkFile(null);
    setMaterialType(materialTypes[0]);
    setAudienceType(audienceTypes[0]);
    setCustomMaterialType('');
    setCustomAudienceType('');
    setAudienceKnowledgeLevel(3);
  }

  return (
    <motion.form
      className="app-card yandex-panel mt-5 w-full space-y-5 p-4 md:p-5"
      onSubmit={submit}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
    >
      {/* <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="section-title">Загрузка</h2>
          <p className="mt-1 text-sm font-semibold text-[#60616a]">Главный файл обязателен. Остальное помогает точнее проверить защиту.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-[#e8e0cf] bg-white px-3 py-1.5 text-xs font-black text-[#60616a]">
          <Sparkles className="h-4 w-4 text-[#fc3f1d]" aria-hidden="true" />
          без внешнего поиска
        </div>
      </div> */}

      <div className="grid gap-4 lg:grid-cols-3">
        <FilePicker
          required
          title="Материал"
          hint="TXT, MD, PDF, DOCX, PPTX"
          file={file}
          icon="main"
          disabled={disabled}
          onChange={setFile}
        />
        <FilePicker
          title="Регламент"
          hint="Требования, критерии, задание"
          file={regulationFile}
          icon="regulation"
          disabled={disabled}
          onChange={setRegulationFile}
        />
        <FilePicker
          title="Эталон"
          hint="Похожая сильная работа"
          file={benchmarkFile}
          icon="benchmark"
          disabled={disabled}
          onChange={setBenchmarkFile}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1.2fr]">
        <label className="block">
          <span className="mb-2 flex items-center gap-2 text-sm font-black">
            <FileText className="h-4 w-4 text-[#fc3f1d]" aria-hidden="true" />
            Тип материала
          </span>
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
          {materialType === customOption ? (
            <input
              value={customMaterialType}
              onChange={(event) => setCustomMaterialType(event.target.value)}
              className="field mt-3"
              placeholder="Например: научная статья, кейс, заявка..."
              disabled={disabled}
            />
          ) : null}
        </label>

        <label className="block">
          <span className="mb-2 flex items-center gap-2 text-sm font-black">
            <Users className="h-4 w-4 text-[#fc3f1d]" aria-hidden="true" />
            Аудитория
          </span>
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
          {audienceType === customOption ? (
            <input
              value={customAudienceType}
              onChange={(event) => setCustomAudienceType(event.target.value)}
              className="field mt-3"
              placeholder="Например: экспертный совет, родители, партнёры..."
              disabled={disabled}
            />
          ) : null}
        </label>

        <div className="rounded-lg border-2 border-[#101114] bg-white p-4 shadow-[4px_4px_0_#ffcc00]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-black">Знания аудитории</h3>
              <p className="mt-1 text-xs font-semibold text-[#60616a]">Настраивает глубину вопросов.</p>
            </div>
            <div className="grid h-10 w-10 place-items-center rounded-full bg-[#ffcc00] text-sm font-black">
              {audienceKnowledgeLevel}
            </div>
          </div>
          <input
            type="range"
            min={1}
            max={5}
            step={1}
            value={audienceKnowledgeLevel}
            onChange={(event) => setAudienceKnowledgeLevel(Number(event.target.value))}
            className="mt-4 w-full accent-[#fc3f1d]"
            disabled={disabled}
            aria-label="Уровень знаний аудитории"
          />
          <div className="relative mt-2 h-5 text-[11px] font-bold text-[#60616a]">
            <span className="absolute left-0 text-left">ноль</span>
            <span className="absolute left-1/4 -translate-x-1/2 text-center">базово</span>
            <span className="absolute left-1/2 -translate-x-1/2 text-center">среднее</span>
            <span className="absolute left-3/4 -translate-x-1/2 text-center">сильно</span>
            <span className="absolute right-0 text-right">эксперт</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <button type="button" className="secondary-button" disabled={disabled} onClick={reset}>
          <RotateCcw className="h-5 w-5" aria-hidden="true" />
          Сбросить
        </button>
        <motion.button
          type="submit"
          className="primary-button min-w-56"
          disabled={disabled || !canSubmit}
          whileHover={canSubmit && !disabled ? { y: -2 } : undefined}
          whileTap={canSubmit && !disabled ? { scale: 0.98 } : undefined}
        >
          <Play className="h-5 w-5" aria-hidden="true" />
          Проанализировать
        </motion.button>
      </div>
    </motion.form>
  );
}

function FilePicker({
  title,
  hint,
  file,
  required,
  disabled,
  icon,
  onChange,
}: {
  title: string;
  hint: string;
  file: File | null;
  required?: boolean;
  disabled?: boolean;
  icon: 'main' | 'regulation' | 'benchmark';
  onChange: (file: File | null) => void;
}) {
  const Icon = file ? FileCheck2 : FileUp;
  const accent = icon === 'main' ? '#ffcc00' : icon === 'regulation' ? '#dff4e7' : '#eef2ff';
  const shadow = icon === 'main' ? '#101114' : icon === 'regulation' ? '#2f7a4f' : '#3552a3';

  return (
    <motion.label
      className="group relative flex min-h-40 cursor-pointer flex-col justify-between overflow-hidden rounded-lg border-2 border-[#101114] bg-white p-4 shadow-[5px_5px_0_var(--card-shadow)] transition hover:-translate-y-0.5"
      style={{ '--card-accent': accent, '--card-shadow': shadow } as CSSProperties}
      whileHover={{ rotate: icon === 'main' ? -0.35 : 0.35 }}
    >
      <span className="absolute right-[-32px] top-[-32px] h-24 w-24 rounded-full bg-[var(--card-accent)]" aria-hidden="true" />
      <span className="relative flex items-start justify-between gap-3">
        <span>
          <span className="flex items-center gap-2 text-lg font-black">
            <Icon className="h-5 w-5 text-[#fc3f1d]" aria-hidden="true" />
            {title}
          </span>
          <span className="mt-1 block text-sm font-semibold text-[#60616a]">
            {file ? file.name : hint}
          </span>
        </span>
        {required ? (
          <span className="rounded-full bg-[#101114] px-2.5 py-1 text-[11px] font-black text-white">
            нужно
          </span>
        ) : null}
      </span>
      <span className="relative mt-5 inline-flex w-fit rounded-lg border-2 border-[#101114] bg-[#ffcc00] px-4 py-2 text-sm font-black shadow-[3px_3px_0_#101114] transition group-hover:bg-[#ffe05c]">
        {file ? 'Заменить файл' : 'Выбрать файл'}
      </span>
      <input
        type="file"
        accept=".txt,.md,.pdf,.docx,.pptx"
        className="sr-only"
        disabled={disabled}
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
    </motion.label>
  );
}
