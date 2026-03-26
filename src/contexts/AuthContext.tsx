import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { User, Profile } from '@/types';
import { authApi, profilesApi, onSessionExpired, getRememberMe, getApiBaseUrl } from '@/lib/api';
import { transformProfile } from '@/lib/profileUtils';

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
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
          picture: userData.picture,
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
    console.log("[AuthContext] login chamado", { email, remember });
    try {
      await authApi.login(email, password, remember);
    } catch (e) {
      console.error("[AuthContext] login falhou", e);
      throw e;
    }
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
    console.log("[AuthContext] login sucesso, buscando perfis");
    setIsAuthenticated(true);

    // Fetch profiles
    try {
      const profilesData = await profilesApi.getAll();
      setProfilesState(profilesData.map(transformProfile));
    } catch (e) {
      console.warn("[AuthContext] erro ao buscar perfis", e);
      setProfilesState([]);
    }
  };

  const loginWithGoogle = async () => {
    // Mesma base que /auth/login (proxy em dev em localhost; VITE_API_URL em build prod/Electron)
    const apiUrl = getApiBaseUrl();
    window.location.href = `${apiUrl}/auth/login/google`;
  };

  const signup = async (email: string, password: string, name: string, remember: boolean = false) => {
    const response = await authApi.signup(email, password, name, remember);
    setRememberMeState(remember);

    // Usar dados do signup quando disponíveis (evita GET /me com token recém-salvo)
    if (response?.user?.id && response?.user?.email) {
      setUser({
        id: response.user.id,
        email: response.user.email,
        name: response.user.name ?? name,
        createdAt: '',
        updatedAt: '',
      });
    } else {
      // Fallback: buscar /me (token já está salvo em setStoredTokens dentro do signup)
      const userData = await authApi.getMe();
      setUser({
        id: userData.id,
        email: userData.email,
        name: userData.name,
        createdAt: '',
        updatedAt: '',
      });
    }
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

  const refreshUser = async () => {
    if (!isAuthenticated) return;
    
    try {
      const userData = await authApi.getMe();
      setUser({
        id: userData.id,
        email: userData.email,
        name: userData.name,
        createdAt: '',
        updatedAt: '',
      });
    } catch {
      // Silently fail - user will remain unchanged
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
        refreshUser,
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
