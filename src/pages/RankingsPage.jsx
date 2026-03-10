import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analyticsApi';
import { referenceApi } from '../api/referenceApi';
import { SectionHeader } from '../components/SectionHeader';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { formatNumber } from '../utils/formatters';

const metrics = [
  { value: 'final_rating', label: 'Место в рейтинге' },
  { value: 'problem_index', label: 'Индекс проблемности' },
  { value: 'violations_per_house', label: 'Нарушения на дом' },
  { value: 'fines_per_1000_m2', label: 'Штрафы на 1000 м²' },
];

const metricLabels = {
  final_rating: 'Место в рейтинге',
  problem_index: 'Индекс проблемности',
  violations_per_house: 'Нарушения на дом',
  fines_per_1000_m2: 'Штрафы на 1000 м²',
};

export function RankingsPage() {
  const [year, setYear] = useState('');
  const [admArea, setAdmArea] = useState('');
  const [metric, setMetric] = useState('problem_index');

  const yearsQuery = useQuery({
    queryKey: ['years'],
    queryFn: referenceApi.getYears,
  });

  const areasQuery = useQuery({
    queryKey: ['adm-areas'],
    queryFn: referenceApi.getAdmAreas,
  });

  const rankingQuery = useQuery({
    queryKey: ['ranking', year, admArea, metric],
    queryFn: () =>
      analyticsApi.getRanking({
        year: year || undefined,
        adm_area: admArea || undefined,
        metric,
        limit: 10,
      }),
  });

  if (rankingQuery.isLoading || yearsQuery.isLoading || areasQuery.isLoading) {
    return <Loader />;
  }

  if (rankingQuery.isError || yearsQuery.isError || areasQuery.isError) {
    return <ErrorState message="Не удалось загрузить рейтинг организаций." />;
  }

  const data = Array.isArray(rankingQuery.data) ? rankingQuery.data : [];

  return (
    <div className="page-stack">
      <SectionHeader
        title="Рейтинги и антирейтинги"
        description="Топ организаций по выбранной метрике."
      />

      <section className="filters-panel">
        <select value={year} onChange={(event) => setYear(event.target.value)}>
          <option value="">Последний доступный год</option>
          {(yearsQuery.data || []).map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select value={admArea} onChange={(event) => setAdmArea(event.target.value)}>
          <option value="">Все округа</option>
          {(areasQuery.data || []).map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select value={metric} onChange={(event) => setMetric(event.target.value)}>
          {metrics.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </section>

      {data.length === 0 ? (
        <EmptyState message="По выбранным параметрам рейтинг отсутствует." />
      ) : (
        <section className="panel">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Позиция</th>
                  <th>Организация</th>
                  <th>Округ</th>
                  <th>Метрика</th>
                  <th>Значение</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={`${item.position}-${item.id}`}>
                    <td>{item.position}</td>
                    <td>{item.short_name || item.name}</td>
                    <td>{item.adm_area}</td>
                    <td>{metricLabels[item.metric] || item.metric}</td>
                    <td>{formatNumber(item.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}