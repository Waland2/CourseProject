import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="state-block">
      <h1>404</h1>
      <p>Страница не найдена.</p>
      <Link to="/" className="button button--primary">
        Вернуться на главную
      </Link>
    </div>
  );
}
