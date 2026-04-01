import { lazy, Suspense, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, Outlet } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { LayoutProvider } from "@/contexts/LayoutContext";
import { AppShell } from "@/layouts/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ElectronTitleBar } from "@/components/ElectronTitleBar";
import { VersionGate } from "@/components/VersionGate";
import { UpdateAvailableScreen } from "@/components/UpdateAvailableScreen";
import { Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

const Index = lazy(() => import("./pages/Index"));
const DownloadPage = lazy(() => import("./pages/DownloadPage"));
const Auth = lazy(() => import("./pages/Auth"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const AuthCallback = lazy(() => import("./pages/AuthCallback"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Billing = lazy(() => import("./pages/Billing"));
const SubscriptionManagement = lazy(() => import("./pages/SubscriptionManagement"));
const ProfileSelection = lazy(() => import("./pages/ProfileSelection"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const LocalRuntimeSetupPage = lazy(() => import("./pages/LocalRuntimeSetupPage"));
const SFAPPage = lazy(() => import("./pages/sfap"));
const Error = lazy(() => import("./pages/Error"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 2 },
    mutations: { retry: 1 },
  },
});

function PageLoader() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex items-center justify-center bg-background" role="status" aria-live="polite" aria-label={t("app.loading")}>
      <Loader2 className="h-10 w-10 animate-spin text-primary" />
    </div>
  );
}

const App = () => {
  const { t } = useTranslation();
  useEffect(() => {
    if (typeof window !== "undefined") {
      document.documentElement.dataset.electron = window.electronAPI ? "true" : "";
    }
  }, []);

  return (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <ErrorBoundary>
        <HashRouter>
          <AuthProvider>
            <LayoutProvider>
              <VersionGate>
                <TooltipProvider>
                  <ElectronTitleBar />
                  <UpdateAvailableScreen />
                  <a href="#main-content" className="skip-link">
                    {t("app.skipToContent")}
                  </a>
                  <Toaster />
                  <Sonner />
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route element={<AppShell />}>
                        {/* Public routes */}
                        <Route path="/" element={<Index />} />
                        <Route path="/download" element={<DownloadPage />} />
                        <Route path="/auth" element={<Auth />} />
                        <Route path="/auth/callback" element={<AuthCallback />} />
                        <Route path="/forgot-password" element={<ForgotPassword />} />
                        <Route path="/reset-password" element={<ResetPassword />} />
                        <Route path="/error" element={<Error />} />

                        {/* Protected routes - require authentication */}
                        <Route
                          path="/profile-selection"
                          element={
                            <ProtectedRoute>
                              <ProfileSelection />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/billing"
                          element={
                            <ProtectedRoute>
                              <Billing />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/subscription"
                          element={
                            <ProtectedRoute>
                              <SubscriptionManagement />
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
                        <Route
                          path="/settings/environment"
                          element={
                            <ProtectedRoute>
                              <LocalRuntimeSetupPage />
                            </ProtectedRoute>
                          }
                        />
                        <Route
                          path="/sfap"
                          element={
                            <ProtectedRoute requireProfile>
                              <SFAPPage />
                            </ProtectedRoute>
                          }
                        />

                        {/* Protected routes - require authentication AND active profile */}
                        <Route
                          path="/dashboard"
                          element={
                            <ProtectedRoute requireProfile>
                              <Dashboard />
                            </ProtectedRoute>
                          }
                        />

                        {/* Catch-all */}
                        <Route path="*" element={<NotFound />} />
                      </Route>
                    </Routes>
                  </Suspense>
                </TooltipProvider>
              </VersionGate>
            </LayoutProvider>
          </AuthProvider>
        </HashRouter>
      </ErrorBoundary>
    </ThemeProvider>
  </QueryClientProvider>
  );
};

export default App;
