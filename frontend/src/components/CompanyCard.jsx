import { Link } from 'react-router-dom';
import { RiskBadge } from './RiskBadge';

const formatNumber = (value) => {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return String(value);
  }

  return new Intl.NumberFormat('ru-RU').format(number);
};

export function CompanyCard({ company }) {
  if (!company) {
    return null;
  }

  const {
    id,
    short_name,
    inn,
    adm_area,
    final_rating,
    houses_quantity,
    houses_area,
    problem_index,
    risk_level,
  } = company;

  return (
    <article className="company-card">
      <div className="company-card__header">
        <div className="company-card__title-block">
          <h3 className="company-card__title">{short_name || 'Без названия'}</h3>
          <p className="company-card__subtitle">ИНН: {inn || '—'}</p>
        </div>

        <RiskBadge riskLevel={risk_level} />
      </div>

      <div className="company-card__meta">
        <span>{adm_area || 'Округ не указан'}</span>
        <span>Место в рейтинге: {final_rating ?? '—'}</span>
      </div>

      <div className="company-card__metrics">
        <span>Домов: {formatNumber(houses_quantity)}</span>
        <span>Площадь: {formatNumber(houses_area)}</span>
        <span>Индекс проблемности: {problem_index ?? '—'}</span>
      </div>

      <div className="company-card__actions">
        <Link to={`/companies/${id}`} className="button button--primary">
          Подробнее
        </Link>
      </div>
    </article>
  );
}