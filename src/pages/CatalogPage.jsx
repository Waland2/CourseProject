import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api/companiesApi';
import { referenceApi } from '../api/referenceApi';
import { CompanyCard } from '../components/CompanyCard';
import { Loader } from '../components/Loader';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { Pagination } from '../components/Pagination';
import { SectionHeader } from '../components/SectionHeader';
import { cleanParams } from '../utils/queryParams';

const PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 350;

const sortCompaniesWithNullRatingLast = (items, ordering) => {
  const list = Array.isArray(items) ? [...items] : [];

  if (ordering !== 'final_rating' && ordering !== '-final_rating') {
    return list;
  }

  return list.sort((a, b) => {
    const aRating = a?.final_rating;
    const bRating = b?.final_rating;

    const aIsEmpty = aRating === null || aRating === undefined || aRating === '';
    const bIsEmpty = bRating === null || bRating === undefined || bRating === '';

    if (aIsEmpty && bIsEmpty) return 0;
    if (aIsEmpty) return 1;
    if (bIsEmpty) return -1;

    const aNumber = Number(aRating);
    const bNumber = Number(bRating);

    if (ordering === '-final_rating') {
      return bNumber - aNumber;
    }

    return aNumber - bNumber;
  });
};

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

export function CatalogPage() {
  const [searchParams] = useSearchParams();

  const initialSearch = searchParams.get('search') || '';
  const initialYearFromParams = searchParams.get('year') || '';

  const [searchDraft, setSearchDraft] = useState(initialSearch);
  const [search, setSearch] = useState(initialSearch);
  const [year, setYear] = useState(initialYearFromParams);
  const [admArea, setAdmArea] = useState(searchParams.get('adm_area') || '');
  const [ordering, setOrdering] = useState(searchParams.get('ordering') || 'final_rating');
  const [page, setPage] = useState(1);

  const yearsQuery = useQuery({
    queryKey: ['years'],
    queryFn: referenceApi.getYears,
  });

  const areasQuery = useQuery({
    queryKey: ['adm-areas'],
    queryFn: referenceApi.getAdmAreas,
  });

  const latestYear = useMemo(() => getLatestYearValue(yearsQuery.data), [yearsQuery.data]);

  useEffect(() => {
    if (!year && latestYear) {
      setYear(latestYear);
    }
  }, [year, latestYear]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      const normalizedValue = searchDraft.trim();

      setPage((currentPage) => (currentPage === 1 ? currentPage : 1));
      setSearch((currentSearch) => (
        currentSearch === normalizedValue ? currentSearch : normalizedValue
      ));
    }, SEARCH_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [searchDraft]);

  const companiesParams = useMemo(() => {
    return cleanParams({
      search,
      year,
      adm_area: admArea,
      ordering,
      page,
      page_size: PAGE_SIZE,
    });
  }, [search, year, admArea, ordering, page]);

  const companiesQuery = useQuery({
    queryKey: ['companies', companiesParams],
    queryFn: () => companiesApi.getCompanies(companiesParams),
    enabled: Boolean(year),
    placeholderData: (previousData) => previousData,
  });

  const companiesData = companiesQuery.data || {};
  const rawResults = Array.isArray(companiesData.results) ? companiesData.results : [];

  const results = useMemo(() => {
    return sortCompaniesWithNullRatingLast(rawResults, ordering);
  }, [rawResults, ordering]);

  const next = companiesData.next || null;
  const previous = companiesData.previous || null;
  const count = Number.isFinite(Number(companiesData.count)) ? Number(companiesData.count) : 0;
  const totalPages = Math.max(Math.ceil(count / PAGE_SIZE), 1);

  const handleYearChange = (value) => {
    setPage(1);
    setYear(value);
  };

  const handleAdmAreaChange = (value) => {
    setPage(1);
    setAdmArea(value);
  };

  const handleOrderingChange = (value) => {
    setPage(1);
    setOrdering(value);
  };

  const isInitialLoading =
    yearsQuery.isLoading ||
    areasQuery.isLoading ||
    (companiesQuery.isLoading && !companiesQuery.data);

  if (isInitialLoading) {
    return <Loader />;
  }

  if (companiesQuery.isError || yearsQuery.isError || areasQuery.isError) {
    return <ErrorState message="Не удалось загрузить каталог организаций." />;
  }

  return (
    <div className="page-stack">
      <SectionHeader
        title="Каталог управляющих организаций"
        description={`Найдено организаций: ${count}`}
      />

      <section className="filters-panel">
        <div className="catalog-search-group">
          <input
            type="text"
            placeholder="Поиск по названию или ИНН"
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
          />
        </div>

        <select value={year} onChange={(event) => handleYearChange(event.target.value)}>
          {(yearsQuery.data || []).map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select value={admArea} onChange={(event) => handleAdmAreaChange(event.target.value)}>
          <option value="">Все округа</option>
          {(areasQuery.data || []).map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select value={ordering} onChange={(event) => handleOrderingChange(event.target.value)}>
          <option value="final_rating">Место в рейтинге ↑</option>
          <option value="-final_rating">Место в рейтинге ↓</option>
          <option value="-houses_quantity">Количество домов ↓</option>
          <option value="houses_quantity">Количество домов ↑</option>
          <option value="name">Название А-Я</option>
          <option value="-name">Название Я-А</option>
        </select>
      </section>

      {companiesQuery.isFetching ? <Loader label="Обновляем список..." /> : null}

      {results.length === 0 ? (
        <EmptyState message="По выбранным фильтрам организации не найдены." />
      ) : (
        <section className="cards-grid">
          {results.map((company) => (
            <CompanyCard key={company.id} company={company} />
          ))}
        </section>
      )}

      <Pagination
        page={page}
        totalPages={totalPages}
        hasNext={Boolean(next)}
        hasPrevious={Boolean(previous)}
        onChange={setPage}
      />
    </div>
  );
}