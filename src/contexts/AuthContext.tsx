import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { User, Profile } from '@/types';
import { authApi, profilesApi, onSessionExpired, getRememberMe } from '@/lib/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  currentProfile: Profile | null;
  profiles: Profile[];
  rememberMe: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signup: (email: string, password: string, name: string, rememberMe?: boolean) => Promise<void>;
  logout: () => Promise<void>;
  setCurrentProfile: (profile: Profile | null) => void;
  setProfiles: (profiles: Profile[]) => void;
  fetchProfiles: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Transform API response to our Profile type
function transformProfile(apiProfile: any): Profile {
  return {
    id: apiProfile.id,
    userId: apiProfile.user_id,
    name: apiProfile.name,
    description: apiProfile.description || '',
    createdAt: apiProfile.created_at,
    updatedAt: apiProfile.updated_at,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentProfile, setCurrentProfileState] = useState<Profile | null>(null);
  const [profiles, setProfilesState] = useState<Profile[]>([]);
  const [rememberMe, setRememberMeState] = useState(() => getRememberMe());

  // Clear all auth state
  const clearAuthState = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
    setCurrentProfileState(null);
    setProfilesState([]);
  }, []);

  // Bootstrap: Check if token exists, validate with backend
  useEffect(() => {
    async function initializeAuth() {
      // If no token, immediately set as not authenticated
      if (!authApi.hasToken()) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Token exists, try to validate it
      try {
        const userData = await authApi.getMe();
        setUser({
          id: userData.id,
          email: userData.email,
          name: userData.name,
          createdAt: '',
          updatedAt: '',
        });
        setIsAuthenticated(true);

        // Fetch profiles
        try {
          const profilesData = await profilesApi.getAll();
          const transformedProfiles = profilesData.map(transformProfile);
          setProfilesState(transformedProfiles);

          // Restore current profile from storage
          const storedProfileId = profilesApi.getCurrentId();
          if (storedProfileId) {
            const profile = transformedProfiles.find(p => p.id === storedProfileId);
            if (profile) {
              setCurrentProfileState(profile);
            }
          }
        } catch {
          // Profiles fetch failed, but user is still authenticated
          setProfilesState([]);
        }
      } catch {
        // Token invalid or backend unreachable - clear auth state
        clearAuthState();
      } finally {
        setIsLoading(false);
      }
    }

    initializeAuth();
  }, [clearAuthState]);

  // Listen for session expiration events (401 responses)
  useEffect(() => {
    const unsubscribe = onSessionExpired(() => {
      clearAuthState();
    });
    return unsubscribe;
  }, [clearAuthState]);

  const login = async (email: string, password: string, remember: boolean = false) => {
    await authApi.login(email, password, remember);
    setRememberMeState(remember);
    
    // Fetch user data after successful login
    const userData = await authApi.getMe();
    setUser({
      id: userData.id,
      email: userData.email,
      name: userData.name,
      createdAt: '',
      updatedAt: '',
    });
    setIsAuthenticated(true);

    // Fetch profiles
    try {
      const profilesData = await profilesApi.getAll();
      setProfilesState(profilesData.map(transformProfile));
    } catch {
      setProfilesState([]);
    }
  };

  const loginWithGoogle = async () => {
    // Redirect to backend OAuth endpoint
    const apiUrl = import.meta.env.VITE_API_URL || '/api';
    window.location.href = `${apiUrl}/auth/google`;
  };

  const signup = async (email: string, password: string, name: string, remember: boolean = false) => {
    await authApi.signup(email, password, name, remember);
    setRememberMeState(remember);
    
    // Fetch user data after successful signup
    const userData = await authApi.getMe();
    setUser({
      id: userData.id,
      email: userData.email,
      name: userData.name,
      createdAt: '',
      updatedAt: '',
    });
    setIsAuthenticated(true);
    setProfilesState([]);
  };

  const logout = async () => {
    await authApi.logout();
    clearAuthState();
  };

  const setCurrentProfile = (profile: Profile | null) => {
    setCurrentProfileState(profile);
    if (profile) {
      profilesApi.setCurrentId(profile.id);
    } else {
      profilesApi.clearCurrentId();
    }
  };

  const setProfiles = (newProfiles: Profile[]) => {
    setProfilesState(newProfiles);
  };

  const fetchProfiles = async () => {
    if (!isAuthenticated) return;
    
    try {
      const profilesData = await profilesApi.getAll();
      setProfilesState(profilesData.map(transformProfile));
    } catch {
      // Silently fail - profiles will remain empty
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        currentProfile,
        profiles,
        rememberMe,
        login,
        loginWithGoogle,
        signup,
        logout,
        setCurrentProfile,
        setProfiles,
        fetchProfiles,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
