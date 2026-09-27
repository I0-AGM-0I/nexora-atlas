import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '../components/AppShell';
import { DashboardPage } from '../pages/DashboardPage';
import { SpendPage } from '../pages/SpendPage';
import { AnomaliesPage } from '../pages/AnomaliesPage';
import { OptimizationPage } from '../pages/OptimizationPage';
import { RecommendationDetailPage } from '../pages/RecommendationDetailPage';
import { ScenariosPage } from '../pages/ScenariosPage';
import { ForecastPage } from '../pages/ForecastPage';
import { ResourcesPage } from '../pages/ResourcesPage';
import { ResourceDetailPage } from '../pages/ResourceDetailPage';
import { IntegrationsPage } from '../pages/IntegrationsPage';
import { SettingsPage } from '../pages/SettingsPage';
import { ErrorState } from '../components/ErrorState';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell isDemo={true} />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/spend" element={<SpendPage />} />
          <Route path="/changes" element={<AnomaliesPage />} />
          <Route path="/changes/:id" element={<AnomaliesPage />} />
          <Route path="/anomalies" element={<AnomaliesPage />} />
          <Route path="/anomalies/:id" element={<AnomaliesPage />} />
          <Route path="/optimization" element={<OptimizationPage />} />
          <Route path="/optimization/:id" element={<RecommendationDetailPage />} />
          <Route path="/scenarios" element={<ScenariosPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/resources/:id" element={<ResourceDetailPage />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route
            path="*"
            element={
              <div className="py-12">
                <ErrorState
                  title="Route Not Found"
                  message="The requested route does not exist in the NEXORA ATLAS application."
                />
              </div>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
