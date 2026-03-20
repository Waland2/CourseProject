import { getRiskMeta } from '../utils/formatters';

export function RiskBadge({ riskLevel }) {
  const risk = getRiskMeta(riskLevel);
  return <span className={`badge badge--${risk.tone}`}>{risk.label}</span>;
}
