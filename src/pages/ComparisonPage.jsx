import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api/companiesApi';
import { analyticsApi } from '../api/analyticsApi';
import { referenceApi } from '../api/referenceApi';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { SectionHeader } from '../components/SectionHeader';
import { SimpleComparisonChart } from '../components/SimpleComparisonChart';
import { formatNumber } from '../utils/formatters';

const COMPARISON_METRICS = [
  {
    value: 'final_rating',
    label: 'Место в рейтинге',
    description: 'Чем ниже значение, тем лучше.',
    reverse: false,
    formatter: (value) => formatNumber(value, 0),
  },
  {
    value: 'violations_per_house',
    label: 'Нарушения на дом',
    description: 'Чем ниже значение, тем лучше.',
    reverse: false,
    formatter: (value) => formatNumber(value),
  },
  {
    value: 'fines_per_1000_m2',
    label: 'Штрафы на 1000 м²',
    description: 'Чем ниже значение, тем лучше.',
    reverse: false,
    formatter: (value) => formatNumber(value),
  },
  {
    value: 'problem_index',
    label: 'Индекс проблемности',
    description: 'Чем ниже значение, тем лучше.',
    reverse: false,
    formatter: (value) => formatNumber(value),
  },
  {
    value: 'houses_quantity',
    label: 'Количество домов',
    description: 'Показывает масштаб управления. Это не оценка качества.',
    reverse: true,
    formatter: (value) => formatNumber(value, 0),
  },
];

export function ComparisonPage() {
  const [search, setSearch] = useState('');
  const [year, setYear] = useState('');
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('problem_index');

  const yearsQuery = useQuery({
    queryKey: ['years'],
    queryFn: referenceApi.getYears,
  });

  const searchQuery = useQuery({
    queryKey: ['comparison-search', search],
    queryFn: () => companiesApi.getSuggestions(search),
    enabled: search.trim().length >= 2,
  });

  const comparisonMutation = useMutation({
    mutationFn: analyticsApi.compareCompanies,
  });

  const selectedIds = useMemo(
    () => selectedCompanies.map((company) => company.id),
    [selectedCompanies]
  );

  const toggleCompany = (company) => {
    setSelectedCompanies((prev) => {
      const exists = prev.some((item) => item.id === company.id);

      if (exists) {
        return prev.filter((item) => item.id !== company.id);
      }

      if (prev.length >= 3) {
        return prev;
      }

      return [...prev, company];
    });
  };

  const removeCompany = (companyId) => {
    setSelectedCompanies((prev) => prev.filter((item) => item.id !== companyId));
  };

  const normalizedComparisonCompanies = useMemo(() => {
    const rawCompanies = comparisonMutation.data?.companies || [];

    return rawCompanies.map((company) => ({
      ...company,
      id: company.id ?? company.company_id,
      violations_per_house:
        company.violations_per_house ?? company.metrics?.violations_per_house ?? null,
      fines_per_1000_m2:
        company.fines_per_1000_m2 ?? company.metrics?.fines_per_1000_m2 ?? null,
      problem_index: company.problem_index ?? company.metrics?.problem_index ?? null,
      prescriptions_per_house:
        company.prescriptions_per_house ?? company.metrics?.prescriptions_per_house ?? null,
    }));
  }, [comparisonMutation.data]);

  const selectedMetricConfig = useMemo(() => {
    return (
      COMPARISON_METRICS.find((metric) => metric.value === selectedMetric) ||
      COMPARISON_METRICS[0]
    );
  }, [selectedMetric]);

  const chartData = useMemo(() => {
    const data = normalizedComparisonCompanies.map((company) => ({
      id: company.id,
      name: company.short_name || company.name || 'Без названия',
      value: Number(company[selectedMetricConfig.value] ?? 0),
    }));

    const sorted = [...data].sort((a, b) => {
      if (selectedMetricConfig.reverse) {
        return b.value - a.value;
      }

      return a.value - b.value;
    });

    return sorted;
  }, [normalizedComparisonCompanies, selectedMetricConfig]);

  const handleCompare = () => {
    if (selectedIds.length < 2) return;

    comparisonMutation.mutate({
      company_ids: selectedIds,
      year: year ? Number(year) : undefined,
    });
  };

  return (
    <div className="page-stack">
      <SectionHeader
        title="Сравнение организаций"
        description="Выберите от 2 до 3 организаций и получите аналитическое сопоставление."
      />

      <section className="panel">
        <div className="filters-panel">
          <input
            placeholder="Найти организацию"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          <select value={year} onChange={(event) => setYear(event.target.value)}>
            <option value="">Последний доступный год</option>
            {(yearsQuery.data || []).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <button
            className="button button--primary"
            onClick={handleCompare}
            disabled={selectedIds.length < 2}
          >
            Сравнить
          </button>
        </div>

        {searchQuery.isLoading ? <Loader label="Ищем организации..." /> : null}
        {searchQuery.isError ? <ErrorState message={searchQuery.error.message} /> : null}

        {(searchQuery.data || []).length ? (
          <>
            <h3 style={{ marginTop: 20, marginBottom: 12 }}>Результаты поиска</h3>
            <div className="selection-list">
              {(searchQuery.data || []).map((item) => {
                const isSelected = selectedIds.includes(item.id);
                const selectionLimitReached = selectedCompanies.length >= 3 && !isSelected;

                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`selection-chip ${isSelected ? 'selection-chip--active' : ''}`}
                    onClick={() => toggleCompany(item)}
                    disabled={selectionLimitReached}
                    title={selectionLimitReached ? 'Можно выбрать не более 3 организаций' : ''}
                  >
                    {item.short_name || item.name}
                  </button>
                );
              })}
            </div>
          </>
        ) : null}

        <div style={{ marginTop: 20 }}>
          <h3 style={{ marginTop: 0, marginBottom: 12 }}>Выбранные организации</h3>

          {selectedCompanies.length ? (
            <div className="selection-list">
              {selectedCompanies.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="selection-chip selection-chip--active"
                  onClick={() => removeCompany(item.id)}
                  title="Убрать из сравнения"
                >
                  {item.short_name || item.name} ×
                </button>
              ))}
            </div>
          ) : (
            <EmptyState message="Пока ничего не выбрано." />
          )}
        </div>
      </section>

      {comparisonMutation.isPending ? <Loader label="Формируем сравнение..." /> : null}
      {comparisonMutation.isError ? (
        <ErrorState message={comparisonMutation.error.message} />
      ) : null}

      {comparisonMutation.data ? (
        <>
          <section className="panel">
            <h3>Итог по сравнению</h3>

            <div className="benchmark-list">
              {comparisonMutation.data.best_final_rating ? (
                <div>
                  <span>Лучшая позиция в рейтинге</span>
                  <strong>{comparisonMutation.data.best_final_rating.company_name}</strong>
                  <small>
                    Место: {formatNumber(comparisonMutation.data.best_final_rating.value, 0)}
                    {comparisonMutation.data.best_final_rating.official_rating !== null &&
                    comparisonMutation.data.best_final_rating.official_rating !== undefined
                      ? ` · Официальный рейтинг: ${formatNumber(
                          comparisonMutation.data.best_final_rating.official_rating,
                          0
                        )}`
                      : ''}
                  </small>
                </div>
              ) : null}

              {comparisonMutation.data.lowest_final_rating ? (
                <div>
                  <span>Худшая позиция в рейтинге</span>
                  <strong>{comparisonMutation.data.lowest_final_rating.company_name}</strong>
                  <small>
                    Место: {formatNumber(comparisonMutation.data.lowest_final_rating.value, 0)}
                    {comparisonMutation.data.lowest_final_rating.official_rating !== null &&
                    comparisonMutation.data.lowest_final_rating.official_rating !== undefined
                      ? ` · Официальный рейтинг: ${formatNumber(
                          comparisonMutation.data.lowest_final_rating.official_rating,
                          0
                        )}`
                      : ''}
                  </small>
                </div>
              ) : null}

              {comparisonMutation.data.best_by_metric?.problem_index ? (
                <div>
                  <span>Лучший индекс проблемности</span>
                  <strong>{comparisonMutation.data.best_by_metric.problem_index.company_name}</strong>
                  <small>
                    Значение: {formatNumber(comparisonMutation.data.best_by_metric.problem_index.value)}
                  </small>
                </div>
              ) : null}

              {comparisonMutation.data.best_by_metric?.violations_per_house ? (
                <div>
                  <span>Меньше всего нарушений на дом</span>
                  <strong>
                    {comparisonMutation.data.best_by_metric.violations_per_house.company_name}
                  </strong>
                  <small>
                    Значение:{' '}
                    {formatNumber(
                      comparisonMutation.data.best_by_metric.violations_per_house.value
                    )}
                  </small>
                </div>
              ) : null}

              {comparisonMutation.data.best_by_metric?.fines_per_1000_m2 ? (
                <div>
                  <span>Лучший показатель штрафов на 1000 м²</span>
                  <strong>
                    {comparisonMutation.data.best_by_metric.fines_per_1000_m2.company_name}
                  </strong>
                  <small>
                    Значение:{' '}
                    {formatNumber(
                      comparisonMutation.data.best_by_metric.fines_per_1000_m2.value
                    )}
                  </small>
                </div>
              ) : null}

              {comparisonMutation.data.best_by_metric?.prescriptions_per_house ? (
                <div>
                  <span>Меньше всего предписаний на дом</span>
                  <strong>
                    {comparisonMutation.data.best_by_metric.prescriptions_per_house.company_name}
                  </strong>
                  <small>
                    Значение:{' '}
                    {formatNumber(
                      comparisonMutation.data.best_by_metric.prescriptions_per_house.value
                    )}
                  </small>
                </div>
              ) : null}
            </div>
          </section>

          <section className="panel">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Организация</th>
                    <th>Округ</th>
                    <th>Место в рейтинге</th>
                    <th>Нарушения/дом</th>
                    <th>Штрафы/1000 м²</th>
                    <th>Индекс проблемности</th>
                  </tr>
                </thead>
                <tbody>
                  {normalizedComparisonCompanies.map((company) => (
                    <tr key={company.id}>
                      <td>{company.short_name || company.name}</td>
                      <td>{company.adm_area || '—'}</td>
                      <td>{formatNumber(company.final_rating, 0)}</td>
                      <td>{formatNumber(company.violations_per_house)}</td>
                      <td>{formatNumber(company.fines_per_1000_m2)}</td>
                      <td>{formatNumber(company.problem_index)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <SectionHeader
              title="Визуальное сравнение"
              description={selectedMetricConfig.description}
              action={
                <select
                  value={selectedMetric}
                  onChange={(event) => setSelectedMetric(event.target.value)}
                >
                  {COMPARISON_METRICS.map((metric) => (
                    <option key={metric.value} value={metric.value}>
                      {metric.label}
                    </option>
                  ))}
                </select>
              }
            />

            {chartData.length ? (
              <SimpleComparisonChart
                data={chartData}
                dataKey="value"
                yKey="name"
                valueFormatter={selectedMetricConfig.formatter}
              />
            ) : (
              <EmptyState message="Нет данных для визуального сравнения." />
            )}
          </section>
        </>
      ) : (
        <EmptyState message="Выбери минимум две организации, чтобы построить сравнение." />
      )}
    </div>
  );
}