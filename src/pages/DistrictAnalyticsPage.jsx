import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analyticsApi';
import { referenceApi } from '../api/referenceApi';
import { SectionHeader } from '../components/SectionHeader';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { MetricBarChart } from '../components/MetricBarChart';
import { formatNumber } from '../utils/formatters';
import { Link } from 'react-router-dom';

const getLatestYearValue = (years) => {
  if (!Array.isArray(years) || years.length === 0) {
    return '';
  }

  const normalizedYears = years
    .map((item) => String(item))
    .filter(Boolean);

  if (!normalizedYears.length) {
    return '';
  }

  return normalizedYears.reduce((latest, current) => {
    const latestNumber = Number(latest);
    const currentNumber = Number(current);

    if (Number.isFinite(latestNumber) && Number.isFinite(currentNumber)) {
      return currentNumber > latestNumber ? current : latest;
    }

    return current > latest ? current : latest;
  });
};

export function DistrictAnalyticsPage() {
  const [year, setYear] = useState('');

  const yearsQuery = useQuery({
    queryKey: ['years'],
    queryFn: referenceApi.getYears,
  });

  const latestYear = useMemo(() => getLatestYearValue(yearsQuery.data), [yearsQuery.data]);

  useEffect(() => {
    if (!year && latestYear) {
      setYear(latestYear);
    }
  }, [year, latestYear]);

  const analyticsQuery = useQuery({
    queryKey: ['district-analytics', year],
    queryFn: () => analyticsApi.getDistrictAnalytics(year || undefined),
    enabled: Boolean(year),
  });

  if (analyticsQuery.isLoading || yearsQuery.isLoading) {
    return <Loader />;
  }

  if (analyticsQuery.isError || yearsQuery.isError) {
    return <ErrorState message="Не удалось загрузить аналитику по округам." />;
  }

  const rawData = Array.isArray(analyticsQuery.data) ? analyticsQuery.data : [];

  const data = rawData.map((item) => ({
    ...item,
    avg_final_rating: Number(item.avg_final_rating ?? 0),
    avg_problem_index: Number(item.avg_problem_index ?? 0),
    companies_count: Number(item.companies_count ?? 0),
    avg_violations_amount: Number(item.avg_violations_amount ?? 0),
    avg_fines_per_1000_m2: Number(item.avg_fines_per_1000_m2 ?? 0),
  }));

  const ratingChartData = [...data].sort(
    (a, b) => a.avg_final_rating - b.avg_final_rating
  );

  const problemChartData = [...data].sort(
    (a, b) => b.avg_problem_index - a.avg_problem_index
  );

  return (
    <div className="page-stack">
      <SectionHeader
        title="Аналитика по округам"
        description="Агрегированные показатели по административным округам."
        action={
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            {(yearsQuery.data || []).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        }
      />

      {data.length === 0 ? (
        <EmptyState message="По выбранному периоду аналитика по округам отсутствует." />
      ) : (
        <>
          <div className="grid-2">
            <section className="panel">
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ margin: 0, marginBottom: 4 }}>
                  Среднее место в рейтинге по округам
                </h3>
                <p style={{ margin: 0, opacity: 0.7 }}>
                  Чем ниже значение, тем лучше позиция округа.
                </p>
              </div>

              <MetricBarChart
                data={ratingChartData}
                xKey="adm_area"
                bars={[
                  {
                    dataKey: 'avg_final_rating',
                    name: 'Среднее место в рейтинге',
                  },
                ]}
                layout="horizontal"
                valueFormatter={(value) => formatNumber(value)}
              />
            </section>

            <section className="panel">
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ margin: 0, marginBottom: 4 }}>
                  Средний индекс проблемности по округам
                </h3>
                <p style={{ margin: 0, opacity: 0.7 }}>
                  Чем выше значение, тем больше проблем в среднем.
                </p>
              </div>

              <MetricBarChart
                data={problemChartData}
                xKey="adm_area"
                bars={[
                  {
                    dataKey: 'avg_problem_index',
                    name: 'Средний индекс проблемности',
                  },
                ]}
                layout="horizontal"
                valueFormatter={(value) => formatNumber(value)}
              />
            </section>
          </div>

          <section className="panel">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Округ</th>
                    <th>Количество УК</th>
                    <th>Среднее место в рейтинге</th>
                    <th>Средний индекс проблемности</th>
                    <th>Нарушения/дом</th>
                    <th>Штрафы/1000 м²</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((item) => (
                    <tr key={item.adm_area}>
                      <td>{item.adm_area}</td>
                      <td>{formatNumber(item.companies_count, 0)}</td>
                      <td>{formatNumber(item.avg_final_rating)}</td>
                      <td>{formatNumber(item.avg_problem_index)}</td>
                      <td>{formatNumber(item.avg_violations_amount)}</td>
                      <td>{formatNumber(item.avg_fines_per_1000_m2)}</td>
                      <td>
                        <Link to={`/companies?adm_area=${encodeURIComponent(item.adm_area)}`}>
                          Открыть УК
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}