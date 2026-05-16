import { motion } from 'framer-motion';
import type { Claim } from '../api/types';
import { RiskBadge } from './RiskBadge';

interface ClaimCardsProps {
  claims: Claim[];
}

const riskRank: Record<string, number> = { high: 3, medium: 2, low: 1 };

export function ClaimCards({ claims }: ClaimCardsProps) {
  const riskyClaims = [...claims].sort((a, b) => riskRank[b.risk_level] - riskRank[a.risk_level]).slice(0, 5);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {riskyClaims.map((claim) => (
        <motion.article
          key={claim.id}
          className="soft-card border-l-[5px] border-l-[#d97706] p-4"
          whileHover={{ y: -4 }}
          transition={{ duration: 0.15 }}
        >
          <div className="flex flex-wrap gap-2">
            <RiskBadge risk={claim.risk_level} />
            <RiskBadge evidence={claim.evidence_status} />
          </div>
          <h3 className="mt-4 text-sm font-black uppercase text-[#60616a]">Рискованное утверждение</h3>
          <p className="mt-2 font-bold leading-6">{claim.text}</p>
          <p className="mt-3 text-sm text-[#60616a]">{claim.explanation}</p>
        </motion.article>
      ))}
    </div>
  );
}
