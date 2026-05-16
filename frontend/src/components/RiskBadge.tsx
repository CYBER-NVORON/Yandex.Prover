import type { EvidenceStatus, RiskLevel } from '../api/types';

const riskLabels: Record<RiskLevel, string> = {
  low: 'низкий риск',
  medium: 'средний риск',
  high: 'высокий риск',
};

const evidenceLabels: Record<EvidenceStatus, string> = {
  supported_by_text: 'подтверждено текстом',
  needs_source: 'нужен источник',
  weak_argument: 'слабый аргумент',
  too_strong: 'слишком сильный вывод',
  unverifiable_from_text: 'не проверить по тексту',
  ok: 'достаточно',
};

const riskClasses: Record<RiskLevel, string> = {
  low: 'bg-emerald-50 text-emerald-800',
  medium: 'bg-amber-100 text-amber-900',
  high: 'bg-rose-100 text-rose-800',
};

const evidenceClasses: Record<EvidenceStatus, string> = {
  supported_by_text: 'bg-emerald-50 text-emerald-800',
  needs_source: 'bg-amber-100 text-amber-900',
  weak_argument: 'bg-orange-100 text-orange-900',
  too_strong: 'bg-rose-100 text-rose-800',
  unverifiable_from_text: 'bg-zinc-100 text-zinc-800',
  ok: 'bg-emerald-50 text-emerald-800',
};

interface RiskBadgeProps {
  risk?: RiskLevel;
  evidence?: EvidenceStatus;
}

export function RiskBadge({ risk, evidence }: RiskBadgeProps) {
  if (risk) {
    return (
      <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${riskClasses[risk]}`}>
        {riskLabels[risk]}
      </span>
    );
  }
  if (evidence) {
    return (
      <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${evidenceClasses[evidence]}`}>
        {evidenceLabels[evidence]}
      </span>
    );
  }
  return null;
}
