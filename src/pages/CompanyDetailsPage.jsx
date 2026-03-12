import { useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQueries, useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api/companiesApi';
import { referenceApi } from '../api/referenceApi';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { RiskBadge } from '../components/RiskBadge';
import { SectionHeader } from '../components/SectionHeader';
import { StatCard } from '../components/StatCard';
import { MetricLineChart } from '../components/MetricLineChart';
import { MetricBarChart } from '../components/MetricBarChart';
import { formatNumber } from '../utils/formatters';

export function CompanyDetailsPage() {
  const { id } = useParams();
  const [selectedYear, setSelectedYear] = useState('');

  const yearsQuery = useQuery({
    queryKey: ['years'],
    queryFn: referenceApi.getYears,
  });

  const [companyQuery, historyQuery, similarQuery, benchmarkQuery, insightsQuery] = useQueries({
    queries: [
      {
        queryKey: ['company', id, selectedYear],
        queryFn: () => companiesApi.getCompanyById(id, selectedYear || undefined),
      },
      {
        queryKey: ['company-history', id],
        queryFn: () => companiesApi.getCompanyHistory(id),
      },
      {
        queryKey: ['similar-companies', id, selectedYear],
        queryFn: () =>
          companiesApi.getSimilarCompanies(id, {
            year: selectedYear || undefined,
            limit: 5,
          }),
      },
      {
        queryKey: ['company-benchmark', id, selectedYear],
        queryFn: () => companiesApi.getBenchmark(id, selectedYear || undefined),
      },
      {
        queryKey: ['company-insights', id, selectedYear],
        queryFn: () => companiesApi.getInsights(id, selectedYear || undefined),
      },
    ],
  });

  const company = companyQuery.data;
  const history = Array.isArray(historyQuery.data) ? historyQuery.data : [];
  const similar = Array.isArray(similarQuery.data) ? similarQuery.data : [];
  const benchmark = benchmarkQuery.data;
  const insights = insightsQuery.data;

  const selectedYearData = company?.selected_year_data || {};
  const publicSatisfaction = selectedYearData.public_satisfaction || {};
  const reliability = selectedYearData.reliability || {};
  const violations = selectedYearData.violations || {};
  const metrics = company?.metrics || {};

  const historyForChart = useMemo(() => {
    return history.map((item) => ({
      year: item.year,
      final_rating: item.final_rating,
      violations_amount: item.violations_amount,
      prescriptions: item.issued_prescriptions,
      fines: Number(item.sum_of_fine ?? 0),
      problem_index: item.metrics?.problem_index ?? item.problem_index ?? null,
      houses_quantity: item.houses_quantity,
      houses_area: item.houses_area,
      issued_prescriptions: item.issued_prescriptions,
      sum_of_fine: Number(item.sum_of_fine ?? 0),
    }));
  }, [history]);

  const isLoading =
    companyQuery.isLoading ||
    historyQuery.isLoading ||
    similarQuery.isLoading ||
    benchmarkQuery.isLoading ||
    insightsQuery.isLoading;

  const hasError =
    companyQuery.isError ||
    historyQuery.isError ||
    similarQuery.isError ||
    benchmarkQuery.isError ||
    insightsQuery.isError;

  if (isLoading) {
    return <Loader />;
  }

  if (hasError) {
    return <ErrorState message="Не удалось загрузить данные по организации." />;
  }

  if (!company) {
    return <ErrorState message="Данные по организации не найдены." />;
  }

  return (
    <div className="page-stack">
      <SectionHeader
        title={company.short_name || company.full_name || company.name}
        description={`ИНН: ${company.inn} · ${company.adm_area}`}
        action={
          <select value={selectedYear} onChange={(event) => setSelectedYear(event.target.value)}>
            <option value="">Последний доступный год</option>
            {(yearsQuery.data || []).map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        }
      />

      <section className="details-hero">
        <div className="panel panel--accent">
          <div className="details-hero__top">
            <div>
              <p className="eyebrow">Место в рейтинге</p>
              <h2>{selectedYearData.final_rating ?? '—'}</h2>
              <p>Год анализа: {company.year ?? '—'}</p>
              {/* <p>Официальный рейтинг: {selectedYearData.official_rating ?? '—'}</p> */}
            </div>
            <RiskBadge riskLevel={company.risk_level || insights?.risk_level} />
          </div>
          <p>{insights?.summary || 'Автоматически сформированный вывод отсутствует.'}</p>
        </div>

        <div className="stats-grid">
          <StatCard
            title="Домов в управлении"
            value={formatNumber(selectedYearData.houses_quantity, 0)}
          />
          <StatCard
            title="Общая площадь"
            value={`${formatNumber(selectedYearData.houses_area ?? selectedYearData.total_area, 0)} м²`}
          />
          <StatCard
            title="Индекс проблемности"
            value={formatNumber(metrics.problem_index)}
          />
          {/* <StatCard
            title="Индекс стабильности"
            value={formatNumber(company.stability_index)}
          /> */}
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          title="Нарушений на дом"
          value={formatNumber(metrics.violations_per_house)}
        />
        <StatCard
          title="Предписаний на дом"
          value={formatNumber(metrics.prescriptions_per_house)}
        />
        <StatCard
          title="Штрафов на дом"
          value={formatNumber(metrics.fines_per_house)}
        />
        <StatCard
          title="Штрафов на 1000 м²"
          value={formatNumber(metrics.fines_per_1000_m2)}
        />
      </section>

      <section className="grid-2">
        <div className="panel">
          <h3>Сильные стороны</h3>
          {(insights?.strengths || []).length ? (
            <ul className="feature-list compact">
              {insights.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <EmptyState message="Нет выделенных сильных сторон." />
          )}
        </div>

        <div className="panel">
          <h3>Слабые стороны</h3>
          {(insights?.weaknesses || []).length ? (
            <ul className="feature-list compact">
              {insights.weaknesses.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <EmptyState message="Нет выделенных слабых сторон." />
          )}
        </div>
      </section>

      {/* <section className="grid-2">
        <div className="panel">
          <h3>Удовлетворённость жителей</h3>
          <div className="benchmark-list">
            <div>
              <span>Сумма баллов</span>
              <strong>{formatNumber(publicSatisfaction.scores_sum)}</strong>
            </div>
            <div>
              <span>Оценка обращений</span>
              <strong>{formatNumber(publicSatisfaction.appeals_score)}</strong>
            </div>
            <div>
              <span>Оценка ответов</span>
              <strong>{formatNumber(publicSatisfaction.responses_score)}</strong>
            </div>
            <div>
              <span>Коэффициент</span>
              <strong>{formatNumber(publicSatisfaction.coefficient_value)}</strong>
            </div>
            <div>
              <span>Промежуточный рейтинг</span>
              <strong>{formatNumber(publicSatisfaction.intermediate_rating)}</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Надёжность</h3>
          <div className="benchmark-list">
            <div>
              <span>Сумма баллов</span>
              <strong>{formatNumber(reliability.scores_sum)}</strong>
            </div>
            <div>
              <span>Баллы по стандарту</span>
              <strong>{formatNumber(reliability.scores_by_standard)}</strong>
            </div>
            <div>
              <span>Промежуточный рейтинг</span>
              <strong>{formatNumber(reliability.intermediate_rating)}</strong>
            </div>
          </div>
        </div>
      </section> */}

      <section className="panel">
        <h3>Нарушения и санкции</h3>
        <div className="stats-grid">
          <StatCard title="Предписания" value={formatNumber(violations.issued_prescriptions, 0)} />
          <StatCard title="Нарушения" value={formatNumber(violations.violations_amount, 0)} />
          <StatCard title="Протоколы" value={formatNumber(violations.protocols_composed, 0)} />
          <StatCard title="Штрафы" value={formatNumber(violations.sum_of_fine, 0)} />
        </div>

        <div className="stats-grid">
          <StatCard
            title="Протоколы за неисполнение"
            value={formatNumber(violations.protocols_composed_for_failure, 0)}
          />
          <StatCard
            title="Исполненные мероприятия"
            value={formatNumber(violations.events_executed, 0)}
          />
          <StatCard
            title="Просроченные мероприятия"
            value={formatNumber(violations.events_not_executed_in_time, 0)}
          />
          <StatCard
            title="Расторгнутые договоры"
            value={formatNumber(violations.cancelled_contracts_amount, 0)}
          />
        </div>
      </section>

      <section>
        <SectionHeader
          title="Динамика по годам"
          description="Ключевые показатели организации в разрезе лет."
        />
        {history.length ? (
          <div className="grid-2">
            <MetricLineChart
              data={historyForChart}
              xKey="year"
              lines={[
                { dataKey: 'problem_index', name: 'Индекс проблемности' },
                { dataKey: 'final_rating', name: 'Место в рейтинге' },
              ]}
            />
            <MetricBarChart
              data={historyForChart}
              xKey="year"
              bars={[
                { dataKey: 'violations_amount', name: 'Нарушения' },
                { dataKey: 'prescriptions', name: 'Предписания' },
                { dataKey: 'fines', name: 'Штрафы' },
              ]}
            />
          </div>
        ) : (
          <EmptyState message="История по годам отсутствует." />
        )}
      </section>

      <section className="panel">
        <h3>История показателей</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Год</th>
                <th>Место в рейтинге</th>
                <th>Домов</th>
                <th>Нарушения</th>
                <th>Предписания</th>
                <th>Штрафы</th>
                <th>Индекс проблемности</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.year}>
                  <td>{item.year}</td>
                  <td>{item.final_rating}</td>
                  <td>{formatNumber(item.houses_quantity, 0)}</td>
                  <td>{formatNumber(item.violations_amount, 0)}</td>
                  <td>{formatNumber(item.issued_prescriptions, 0)}</td>
                  <td>{formatNumber(item.sum_of_fine, 0)}</td>
                  <td>{formatNumber(item.metrics?.problem_index ?? item.problem_index)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel">
          <h3>Похожие организации</h3>
          {similar.length ? (
            <div className="linked-list">
              {similar.map((item) => (
                <Link key={item.id} to={`/companies/${item.id}`} className="linked-list__item">
                  <strong>{item.short_name || item.name}</strong>
                  <span>{item.adm_area}</span>
                  <small>
                    Место в рейтинге: {item.final_rating ?? '—'} · similarity:{' '}
                    {formatNumber(item.similarity_score)}
                  </small>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState message="Похожие организации не найдены." />
          )}
        </div>

        <div className="panel">
          <h3>Сравнение со средней по группе</h3>
          {benchmark ? (
            <div className="benchmark-list">
              <div>
                <span>Нарушения на дом</span>
                <strong>{formatNumber(benchmark.company?.violations_per_house)}</strong>
                <small>
                  Среднее: {formatNumber(benchmark.peer_group_avg?.violations_per_house)}
                </small>
              </div>
              <div>
                <span>Штрафы на 1000 м²</span>
                <strong>{formatNumber(benchmark.company?.fines_per_1000_m2)}</strong>
                <small>
                  Среднее: {formatNumber(benchmark.peer_group_avg?.fines_per_1000_m2)}
                </small>
              </div>
              <div>
                <span>Индекс проблемности</span>
                <strong>{formatNumber(benchmark.company?.problem_index)}</strong>
                <small>
                  Среднее: {formatNumber(benchmark.peer_group_avg?.problem_index)}
                </small>
              </div>
              <p>{benchmark.summary}</p>
            </div>
          ) : (
            <EmptyState message="Сводка benchmark недоступна." />
          )}
        </div>
      </section>
    </div>
  );
}