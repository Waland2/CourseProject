import { useEffect, useMemo, useState } from 'react';

const buildPageItems = (page, totalPages) => {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set([1, totalPages, page - 1, page, page + 1]);

  if (page <= 3) {
    pages.add(2);
    pages.add(3);
    pages.add(4);
  }

  if (page >= totalPages - 2) {
    pages.add(totalPages - 1);
    pages.add(totalPages - 2);
    pages.add(totalPages - 3);
  }

  const sorted = [...pages]
    .filter((item) => item >= 1 && item <= totalPages)
    .sort((a, b) => a - b);

  const result = [];

  for (let index = 0; index < sorted.length; index += 1) {
    const current = sorted[index];
    const previous = sorted[index - 1];

    if (index > 0 && current - previous > 1) {
      result.push('ellipsis');
    }

    result.push(current);
  }

  return result;
};

export function Pagination({ page, totalPages, hasNext, hasPrevious, onChange }) {
  const safeTotalPages = Math.max(Number(totalPages) || 1, 1);
  const [inputValue, setInputValue] = useState(String(page));

  useEffect(() => {
    setInputValue(String(page));
  }, [page]);

  const pageItems = useMemo(() => {
    return buildPageItems(page, safeTotalPages);
  }, [page, safeTotalPages]);

  const handleGoToPage = (targetPage) => {
    const nextPage = Number(targetPage);

    if (!Number.isFinite(nextPage)) {
      return;
    }

    if (nextPage < 1 || nextPage > safeTotalPages || nextPage === page) {
      return;
    }

    onChange(nextPage);
  };

  const handleSubmit = () => {
    const parsed = Number.parseInt(inputValue, 10);

    if (Number.isNaN(parsed)) {
      setInputValue(String(page));
      return;
    }

    const normalized = Math.min(Math.max(parsed, 1), safeTotalPages);
    setInputValue(String(normalized));
    handleGoToPage(normalized);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="pagination">
      <button disabled={!hasPrevious} onClick={() => handleGoToPage(page - 1)}>
        {'<'}
      </button>

      <div className="pagination__pages">
        {pageItems.map((item, index) =>
          item === 'ellipsis' ? (
            <span key={`ellipsis-${index}`} className="pagination__ellipsis">
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              className={`pagination__page ${item === page ? 'pagination__page--active' : ''}`}
              onClick={() => handleGoToPage(item)}
            >
              {item}
            </button>
          )
        )}
      </div>

      <button disabled={!hasNext} onClick={() => handleGoToPage(page + 1)}>
        {'>'}
      </button>

      <div className="pagination__jump">
        <span>
          Страница {page} из {safeTotalPages}
        </span>

        <input
          type="number"
          min={1}
          max={safeTotalPages}
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          onKeyDown={handleKeyDown}
        />

        <button type="button" onClick={handleSubmit}>
          Перейти
        </button>
      </div>
    </div>
  );
}