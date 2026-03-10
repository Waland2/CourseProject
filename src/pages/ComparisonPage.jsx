import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api/companiesApi';
import { analyticsApi } from '../api/analyticsApi';
import { referenceApi } from '../api/referenceApi';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { SectionHeader } from '../components/SectionHeader';
import { MetricRadarChart } from '../components/MetricRadarChart';
import { formatNumber } from '../utils/formatters';

export function ComparisonPage() {
  const [search, setSearch] = useState('');
  const [year, setYear] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);

  const yearsQuery = useQuery({ queryKey: ['years'], queryFn: referenceApi.getYears });
  const searchQuery = useQuery({
    queryKey: ['comparison-search', search],
    queryFn: () => companiesApi.getSuggestions(search),
    enabled: search.trim().length >= 2,
  });

  const comparisonMutation = useMutation({
    mutationFn: analyticsApi.compareCompanies,
  });

  const toggleId = (id) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((item) => item !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const handleCompare = () => {
    if (selectedIds.length < 2) return;
    comparisonMutation.mutate({ company_ids: selectedIds, year: year ? Number(year) : undefined });
  };

  const radarData = useMemo(() => {
    const companies = comparisonMutation.data?.companies || [];
    return [
      {
        metric: 'Место в рейтинге',
        ...Object.fromEntries(companies.map((item) => [item.short_name || item.name, item.final_rating])),
      },
      {
        metric: 'Нарушения/дом',
        ...Object.fromEntries(companies.map((item) => [item.short_name || item.name, item.violations_per_house])),
      },
      {
        metric: 'Штрафы/1000 м²',
        ...Object.fromEntries(companies.map((item) => [item.short_name || item.name, item.fines_per_1000_m2])),
      },
      {
        metric: 'Индекс проблемности',
        ...Object.fromEntries(companies.map((item) => [item.short_name || item.name, item.problem_index])),
      },
    ];
  }, [comparisonMutation.data]);

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
          <button className="button button--primary" onClick={handleCompare} disabled={selectedIds.length < 2}>
            Сравнить
          </button>
        </div>

        {searchQuery.isLoading ? <Loader label="Ищем организации..." /> : null}
        {searchQuery.isError ? <ErrorState message={searchQuery.error.message} /> : null}

        <div className="selection-list">
          {(searchQuery.data || []).map((item) => (
            <button
              key={item.id}
              className={`selection-chip ${selectedIds.includes(item.id) ? 'selection-chip--active' : ''}`}
              onClick={() => toggleId(item.id)}
            >
              {item.short_name || item.name}
            </button>
          ))}
        </div>
      </section>

      {comparisonMutation.isPending ? <Loader label="Формируем сравнение..." /> : null}
      {comparisonMutation.isError ? <ErrorState message={comparisonMutation.error.message} /> : null}

      {comparisonMutation.data ? (
        <>
          <section className="panel">
            <h3>Итоговый вывод</h3>
            <p>{comparisonMutation.data.summary}</p>
          </section>

          <section className="panel">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Организация</th>
                    <th>Место в рейтинге</th>
                    <th>Нарушения/дом</th>
                    <th>Штрафы/1000 м²</th>
                    <th>Индекс проблемности</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonMutation.data.companies.map((company) => (
                    <tr key={company.id}>
                      <td>{company.short_name || company.name}</td>
                      <td>{company.final_rating}</td>
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
            <SectionHeader title="Визуальное сравнение" description="Radar chart по ключевым метрикам." />
            <MetricRadarChart
              data={radarData}
              keys={(comparisonMutation.data.companies || []).map((item) => ({
                dataKey: item.short_name || item.name,
                name: item.short_name || item.name,
              }))}
            />
          </section>
        </>
      ) : (
        <EmptyState message="Выбери минимум две организации, чтобы построить сравнение." />
      )}
    </div>
  );
}