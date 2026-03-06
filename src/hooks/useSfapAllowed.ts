import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { isSfapAllowedForUser } from "@/lib/sfapVisibility";
import { sfapApi } from "@/lib/api";

/**
 * Retorna se o perfil atualmente selecionado pode ver o SFAP.
 * Usa a API GET /sfap/visibility (com X-Profile-Id) como fonte da verdade.
 * Fallback: checagem local pelo nome do perfil (currentProfile.name) em G!, E!, T!, P!.
 */
export function useSfapAllowed(): boolean {
  const { currentProfile, isAuthenticated } = useAuth();
  const profileName = currentProfile?.name;
  const clientAllowed = isSfapAllowedForUser(profileName);

  const { data: apiVisibility, isSuccess } = useQuery({
    queryKey: ["sfap-visibility", isAuthenticated, currentProfile?.id],
    queryFn: () => sfapApi.visibility(),
    enabled: isAuthenticated === true && !!currentProfile?.id,
    staleTime: 2 * 60 * 1000,
    retry: false,
  });

  if (!isAuthenticated) return false;
  if (isSuccess && apiVisibility && typeof apiVisibility.allowed === "boolean") {
    return apiVisibility.allowed;
  }
  return clientAllowed;
}
