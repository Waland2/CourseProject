import { Link } from 'react-router-dom';

export function SearchSuggestions({ items = [], onSelect }) {
  if (!items.length) return null;

  return (
    <div className="suggestions">
      {items.map((item) => (
        <Link
          key={item.id}
          to={`/companies/${item.id}`}
          className="suggestions__item"
          onClick={onSelect}
        >
          <strong>{item.short_name || item.name || 'Без названия'}</strong>
          <span>{item.inn}</span>
          <small>{item.adm_area}</small>
        </Link>
      ))}
    </div>
  );
}