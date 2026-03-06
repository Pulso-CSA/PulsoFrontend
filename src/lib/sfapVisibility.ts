/**
 * SFAP só é visível para usuários cujo nome completo (conta) seja exatamente: G!, E!, T!, P!
 */
export const SFAP_ALLOWED_USER_NAMES = ["G!", "E!", "T!", "P!"] as const;

export function isSfapAllowedForUser(fullName: string | undefined): boolean {
  if (!fullName) return false;
  return SFAP_ALLOWED_USER_NAMES.includes(fullName.trim() as (typeof SFAP_ALLOWED_USER_NAMES)[number]);
}
