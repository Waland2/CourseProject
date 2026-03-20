export const formatNumber = (value, maximumFractionDigits = 2) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits }).format(Number(value));
};

export const formatRating = (value) => (value === null || value === undefined ? '—' : `${value}`);

export const getRiskMeta = (riskLevel) => {
  switch (riskLevel) {
    case 'low':
      return { label: 'Низкий риск', tone: 'success' };
    case 'medium':
      return { label: 'Средний риск', tone: 'warning' };
    case 'high':
      return { label: 'Высокий риск', tone: 'danger' };
    default:
      return { label: 'Нет данных', tone: 'neutral' };
  }
};

export const pluralizeYears = (year) => `${year} г.`;
