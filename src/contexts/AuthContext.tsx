import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Profile, AuthState, LoginCredentials, SignupCredentials } from '@/types';

interface AuthContextType extends AuthState {
  currentProfile: Profile | null;
  profiles: Profile[];
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signup: (credentials: SignupCredentials) => Promise<void>;
  logout: () => Promise<void>;
  setCurrentProfile: (profile: Profile | null) => void;
  setProfiles: (profiles: Profile[]) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// TODO: Replace these with actual API calls to your backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

async function apiLogin(credentials: LoginCredentials): Promise<{ user: User; token: string }> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Falha no login');
  }
  
  return response.json();
}

async function apiLoginWithGoogle(): Promise<{ user: User; token: string }> {
  // TODO: Implement Google OAuth flow
  // This should redirect to your backend OAuth endpoint
  window.location.href = `${API_BASE_URL}/auth/google`;
  throw new Error('Redirecting to Google...');
}

async function apiSignup(credentials: SignupCredentials): Promise<{ user: User; token: string }> {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Falha no cadastro');
  }
  
  return response.json();
}

async function apiLogout(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getStoredToken()}`,
    },
  });
}

async function apiGetCurrentUser(): Promise<User | null> {
  const token = getStoredToken();
  if (!token) return null;
  
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  
  if (!response.ok) return null;
  
  const data = await response.json();
  return data.user;
}

async function apiGetProfiles(): Promise<Profile[]> {
  const token = getStoredToken();
  if (!token) return [];
  
  const response = await fetch(`${API_BASE_URL}/profiles`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  
  if (!response.ok) return [];
  
  const data = await response.json();
  return data.profiles || [];
}

function getStoredToken(): string | null {
  return sessionStorage.getItem('authToken');
}

function setStoredToken(token: string): void {
  sessionStorage.setItem('authToken', token);
}

function removeStoredToken(): void {
  sessionStorage.removeItem('authToken');
}

function getStoredProfileId(): string | null {
  return sessionStorage.getItem('currentProfileId');
}

function setStoredProfileId(profileId: string): void {
  sessionStorage.setItem('currentProfileId', profileId);
}

function removeStoredProfileId(): void {
  sessionStorage.removeItem('currentProfileId');
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentProfile, setCurrentProfileState] = useState<Profile | null>(null);
  const [profiles, setProfilesState] = useState<Profile[]>([]);

  // Initialize auth state on mount
  useEffect(() => {
    async function initializeAuth() {
      try {
        const currentUser = await apiGetCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          setIsAuthenticated(true);
          
          const userProfiles = await apiGetProfiles();
          setProfilesState(userProfiles);
          
          // Restore current profile from session
          const storedProfileId = getStoredProfileId();
          if (storedProfileId) {
            const profile = userProfiles.find(p => p.id === storedProfileId);
            if (profile) {
              setCurrentProfileState(profile);
            }
          }
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setIsLoading(false);
      }
    }
    
    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const { user: loggedInUser, token } = await apiLogin(credentials);
    setStoredToken(token);
    setUser(loggedInUser);
    setIsAuthenticated(true);
    
    const userProfiles = await apiGetProfiles();
    setProfilesState(userProfiles);
  };

  const loginWithGoogle = async () => {
    await apiLoginWithGoogle();
  };

  const signup = async (credentials: SignupCredentials) => {
    const { user: newUser, token } = await apiSignup(credentials);
    setStoredToken(token);
    setUser(newUser);
    setIsAuthenticated(true);
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      removeStoredToken();
      removeStoredProfileId();
      setUser(null);
      setIsAuthenticated(false);
      setCurrentProfileState(null);
      setProfilesState([]);
    }
  };

  const setCurrentProfile = (profile: Profile | null) => {
    setCurrentProfileState(profile);
    if (profile) {
      setStoredProfileId(profile.id);
    } else {
      removeStoredProfileId();
    }
  };

  const setProfiles = (newProfiles: Profile[]) => {
    setProfilesState(newProfiles);
  };

  const refreshUser = async () => {
    const currentUser = await apiGetCurrentUser();
    if (currentUser) {
      setUser(currentUser);
      const userProfiles = await apiGetProfiles();
      setProfilesState(userProfiles);
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
        login,
        loginWithGoogle,
        signup,
        logout,
        setCurrentProfile,
        setProfiles,
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
