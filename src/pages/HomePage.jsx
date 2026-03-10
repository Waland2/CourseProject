import { Link } from 'react-router-dom';
import { SearchInput } from '../components/SearchInput';

const featureList = [
  'Поиск управляющих организаций по названию или ИНН',
  'Аналитическая карточка УК с готовыми выводами',
  'Сравнение организаций между собой и с аналогами',
  'Диаграммы по округам и рейтинги по ключевым метрикам',
];

const quickLinks = [
  { to: '/companies', title: 'Каталог УК', text: 'Фильтрация по округу, году и индексу проблемности.' },
  { to: '/comparison', title: 'Сравнение организаций', text: 'Сопоставление 2–3 УК по месту в рейтинге, штрафам и нарушениям.' },
  { to: '/districts', title: 'Аналитика округов', text: 'Средние показатели по административным округам.' },
  { to: '/rankings', title: 'Рейтинги и антирейтинги', text: 'Лидеры и проблемные организации по выбранной метрике.' },
];

export function HomePage() {
  return (
    <div className="page-stack">
      <section className="hero">
        <div>
          <span className="hero__badge">Аналитический сервис для оценки УК</span>
          <h1>Быстрый поиск, сравнение и оценка управляющих организаций</h1>
          <p>
            Приложение помогает быстро находить управляющие компании, смотреть ключевые показатели,
            анализировать риск и сравнивать организации между собой.
          </p>
        </div>
        <div className="hero__search-card">
          <h2>Найти организацию</h2>
          <SearchInput />
          <div className="hero__actions">
            <Link className="button button--primary" to="/companies">
              Открыть каталог
            </Link>
            <Link className="button" to="/comparison">
              Перейти к сравнению
            </Link>
          </div>
        </div>
      </section>

      <section className="grid-2">
        <div className="panel">
          <h2>Что умеет сервис</h2>
          <ul className="feature-list">
            {featureList.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>Почему это полезно</h2>
          <p>
            Интерфейс не ограничивается списком компаний. Он показывает динамику по годам, нормализованные
            метрики, риск-сигналы и сравнение со схожими организациями.
          </p>
          <p>
            Благодаря этому пользователь получает не просто набор чисел, а понятную оценку качества работы
            организации.
          </p>
        </div>
      </section>

      <section>
        <h2>Быстрые переходы</h2>
        <div className="cards-grid">
          {quickLinks.map((item) => (
            <Link key={item.to} to={item.to} className="feature-card">
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}