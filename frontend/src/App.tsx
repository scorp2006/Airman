// Top-level app: routes + providers (auth, react-query, toasts).

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { ToastHost } from "./components/Toast";

import LoginPage from "./pages/Login";
import DashboardPage from "./pages/Dashboard";
import SortieBoardPage from "./pages/SortieBoard";
import SortieDetailPage from "./pages/SortieDetail";
import TrainingPage from "./pages/Training";
import AircraftPage from "./pages/Aircraft";
import AuditPage from "./pages/Audit";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5000, refetchOnWindowFocus: false },
  },
});

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/sorties" element={<SortieBoardPage />} />
              <Route path="/sorties/:id" element={<SortieDetailPage />} />
              <Route path="/training" element={<TrainingPage />} />
              <Route path="/aircraft" element={<AircraftPage />} />
              <Route path="/audit" element={<AuditPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
        <ToastHost />
      </AuthProvider>
    </QueryClientProvider>
  );
}
