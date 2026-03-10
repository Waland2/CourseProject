import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '../layouts/AppLayout';
import { HomePage } from '../pages/HomePage';
import { CatalogPage } from '../pages/CatalogPage';
import { CompanyDetailsPage } from '../pages/CompanyDetailsPage';
import { ComparisonPage } from '../pages/ComparisonPage';
import { DistrictAnalyticsPage } from '../pages/DistrictAnalyticsPage';
import { RankingsPage } from '../pages/RankingsPage';
import { NotFoundPage } from '../pages/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'companies', element: <CatalogPage /> },
      { path: 'companies/:id', element: <CompanyDetailsPage /> },
      { path: 'comparison', element: <ComparisonPage /> },
      { path: 'districts', element: <DistrictAnalyticsPage /> },
      { path: 'rankings', element: <RankingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
