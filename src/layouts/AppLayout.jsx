import { NavLink, Outlet } from 'react-router-dom';
import { SearchInput } from '../components/SearchInput';

const navItems = [
  { to: '/companies', label: 'Каталог УК' },
  { to: '/comparison', label: 'Сравнение' },
  { to: '/districts', label: 'Округа' },
];

export function AppLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="container app-header__inner">
          <nav className="main-nav">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'active' : '')}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="header-search">
            <SearchInput placeholder="Быстрый поиск УК" />
          </div>
        </div>
      </header>

      <main className="container page-content">
        <Outlet />
      </main>
    </div>
  );
}