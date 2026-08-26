const AUTH_CACHE_TTL_MS = 15_000;

let verifiedAt = 0;
let verificationRequest: Promise<boolean> | null = null;

export function hasRecentAuthenticatedSession(): boolean {
  return verifiedAt > 0 && Date.now() - verifiedAt < AUTH_CACHE_TTL_MS;
}

export async function verifyAuthenticatedSession(apiUrl: string): Promise<boolean> {
  if (hasRecentAuthenticatedSession()) return true;
  if (verificationRequest) return verificationRequest;

  verificationRequest = fetch(`${apiUrl}/api/v1/auth/me`, { credentials: "include" })
    .then((response) => {
      if (response.ok) {
        verifiedAt = Date.now();
        return true;
      }
      verifiedAt = 0;
      return false;
    })
    .catch(() => {
      verifiedAt = 0;
      return false;
    })
    .finally(() => {
      verificationRequest = null;
    });
  return verificationRequest;
}

export function clearAuthenticatedSessionCache(): void {
  verifiedAt = 0;
  verificationRequest = null;
}
