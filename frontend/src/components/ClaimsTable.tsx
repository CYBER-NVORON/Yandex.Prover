import type { Claim } from '../api/types';
import { RiskBadge } from './RiskBadge';

interface ClaimsTableProps {
  claims: Claim[];
}

export function ClaimsTable({ claims }: ClaimsTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-[#e8e0cf] bg-white shadow-[0_10px_26px_rgba(16,17,20,0.05)]">
      <table className="min-w-[900px] w-full border-collapse text-left text-sm">
        <thead className="bg-[#fbf7ec] text-ink">
          <tr>
            <th className="p-3">Утверждение</th>
            <th className="p-3">Тип</th>
            <th className="p-3">Доказательность</th>
            <th className="p-3">Риск</th>
            <th className="p-3">Что сделать</th>
          </tr>
        </thead>
        <tbody>
          {claims.map((claim) => (
            <tr key={claim.id} className="border-t border-[#e8e0cf] align-top">
              <td className="max-w-md p-3 font-semibold">{claim.text}</td>
              <td className="p-3">{claim.claim_type}</td>
              <td className="p-3">
                <RiskBadge evidence={claim.evidence_status} />
              </td>
              <td className="p-3">
                <RiskBadge risk={claim.risk_level} />
              </td>
              <td className="max-w-sm p-3 text-[#60616a]">{claim.recommendation}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
