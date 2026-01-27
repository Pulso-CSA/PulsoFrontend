import { Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireProfile?: boolean;
}

export function ProtectedRoute({ children, requireProfile = false }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, currentProfile } = useAuth();

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Not authenticated - redirect to auth
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  // Requires profile but none selected - redirect to profile selection
  if (requireProfile && !currentProfile) {
    return <Navigate to="/profile-selection" replace />;
  }

  return <>{children}</>;
}
