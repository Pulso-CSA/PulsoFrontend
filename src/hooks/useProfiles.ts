import { useState } from 'react';
import { Profile } from '@/types';
import { useAuth } from '@/contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

function getStoredToken(): string | null {
  return sessionStorage.getItem('authToken');
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getStoredToken();
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Erro desconhecido' }));
    throw new Error(error.message || 'Erro na requisição');
  }
  
  return response.json();
}

export function useProfiles() {
  const { profiles, setProfiles } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createProfile = async (data: { name: string; description: string }): Promise<Profile> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/profiles`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
      
      const newProfile = response.profile;
      setProfiles([...profiles, newProfile]);
      return newProfile;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao criar perfil';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (id: string, data: { name: string; description: string }): Promise<Profile> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/profiles/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      
      const updatedProfile = response.profile;
      setProfiles(profiles.map(p => p.id === id ? updatedProfile : p));
      return updatedProfile;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao atualizar perfil';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteProfile = async (id: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await fetchWithAuth(`${API_BASE_URL}/profiles/${id}`, {
        method: 'DELETE',
      });
      
      setProfiles(profiles.filter(p => p.id !== id));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao deletar perfil';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    profiles,
    isLoading,
    error,
    createProfile,
    updateProfile,
    deleteProfile,
  };
}
