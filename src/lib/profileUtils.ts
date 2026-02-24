import type { Profile } from "@/types";

/** API profile response (snake_case ou camelCase) */
export interface ApiProfile {
  id: string;
  user_id?: string;
  userId?: string;
  name: string;
  description?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
}

/** Transforma resposta da API para o tipo Profile */
export function transformProfile(apiProfile: ApiProfile): Profile {
  return {
    id: apiProfile.id,
    userId: apiProfile.user_id ?? apiProfile.userId ?? "",
    name: apiProfile.name,
    description: apiProfile.description ?? "",
    createdAt: apiProfile.created_at ?? apiProfile.createdAt ?? "",
    updatedAt: apiProfile.updated_at ?? apiProfile.updatedAt ?? "",
  };
}
