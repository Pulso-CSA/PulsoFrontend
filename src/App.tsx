import { lazy, Suspense } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Loader2 } from "lucide-react";

const Index = lazy(() => import("./pages/Index"));
const Auth = lazy(() => import("./pages/Auth"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const AuthCallback = lazy(() => import("./pages/AuthCallback"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Billing = lazy(() => import("./pages/Billing"));
const SubscriptionManagement = lazy(() => import("./pages/SubscriptionManagement"));
const ProfileSelection = lazy(() => import("./pages/ProfileSelection"));
const Error = lazy(() => import("./pages/Error"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 2 },
    mutations: { retry: 1 },
  },
});

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background" role="status" aria-live="polite" aria-label="Carregando">
      <Loader2 className="h-10 w-10 animate-spin text-primary" />
    </div>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <ErrorBoundary>
        <BrowserRouter>
          <AuthProvider>
            <TooltipProvider>
              <a href="#main-content" className="skip-link">
                Pular para o conteúdo principal
              </a>
              <Toaster />
              <Sonner />
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* Public routes */}
                  <Route path="/" element={<Index />} />
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
                </Routes>
              </Suspense>
            </TooltipProvider>
          </AuthProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
