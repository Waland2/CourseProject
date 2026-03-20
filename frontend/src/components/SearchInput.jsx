import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '../api/companiesApi';
import { SearchSuggestions } from './SearchSuggestions';

export function SearchInput({ placeholder = 'Найти УК по названию или ИНН', defaultValue = '' }) {
  const [value, setValue] = useState(defaultValue);
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ['suggestions', value],
    queryFn: () => companiesApi.getSuggestions(value),
    enabled: value.trim().length >= 2,
  });

  useEffect(() => {
    if (value.trim().length < 2) setOpen(false);
    else setOpen(true);
  }, [value]);

  return (
    <div className="search-box">
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onFocus={() => value.trim().length >= 2 && setOpen(true)}
        placeholder={placeholder}
      />
      {open ? <SearchSuggestions items={data || []} onSelect={() => setOpen(false)} /> : null}
    </div>
  );
}
