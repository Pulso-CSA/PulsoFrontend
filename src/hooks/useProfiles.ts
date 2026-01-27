import { useState } from 'react';
import { Profile } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { profilesApi } from '@/lib/api';

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

export function useProfiles() {
  const { profiles, setProfiles, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createProfile = async (data: { name: string; description?: string }): Promise<Profile> => {
    if (!isAuthenticated) {
      throw new Error('Usuário não autenticado');
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await profilesApi.create(data);
      const newProfile = transformProfile(response);
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

  const updateProfile = async (id: string, data: { name: string; description?: string }): Promise<Profile> => {
    if (!isAuthenticated) {
      throw new Error('Usuário não autenticado');
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await profilesApi.update(id, data);
      const updatedProfile = transformProfile(response);
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
    if (!isAuthenticated) {
      throw new Error('Usuário não autenticado');
    }

    setIsLoading(true);
    setError(null);

    try {
      await profilesApi.delete(id);
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
