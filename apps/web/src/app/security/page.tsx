import { LegalPage } from "@/components/public-site/public-pages";

export default function Security() {
  return (
    <LegalPage title="Security">
      <p>BerryBrain uses local administrator setup, secure session cookies, CSRF protection, rate limits, progressive lockout, and security audit events.</p>
      <p>Passwords are designed for Argon2id hashing in production.</p>
      <p>Admin operations require an authenticated local session whose email matches the configured administrator account.</p>
      <p>Security controls are designed to resist high-rate and replayed requests from any interception tool. The system blocks behavior, not tool names.</p>
      <p>Recommended production settings include HTTPS-only secure cookies, restricted CORS origins, a strong session secret, and a reverse proxy that exposes only the web entrypoint publicly.</p>
    </LegalPage>
  );
}
