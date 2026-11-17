import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { LandingPage } from './pages/LandingPage';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectWorkspacePage } from './pages/ProjectWorkspacePage';
import { NewResearchRunPage } from './pages/NewResearchRunPage';
import { PlanReviewPage } from './pages/PlanReviewPage';
import { RunActivityPage } from './pages/RunActivityPage';
import { ReportViewerPage } from './pages/ReportViewerPage';
import { SettingsPage } from './pages/SettingsPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        Authenticating...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />

          {/* Protected Application Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId"
            element={
              <ProtectedRoute>
                <ProjectWorkspacePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/new-run"
            element={
              <ProtectedRoute>
                <NewResearchRunPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/research-runs/:runId/plan"
            element={
              <ProtectedRoute>
                <PlanReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/research-runs/:runId/activity"
            element={
              <ProtectedRoute>
                <RunActivityPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/research-runs/:runId/report"
            element={
              <ProtectedRoute>
                <ReportViewerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
