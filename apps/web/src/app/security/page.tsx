import { LegalPage } from "@/components/public-site/public-pages";

export default function Security() {
  return (
    <LegalPage title="Security">
      <p>BerryBrain uses app-owned accounts, secure session cookies, CSRF protection, email verification, email OTP challenges, rate limits, progressive lockout, and security audit events.</p>
      <p>Passwords are designed for Argon2id hashing in production. OTP codes are short-lived, single-use, and stored only as hashes.</p>
      <p>Admin operations require an authenticated session whose email matches the configured administrator account.</p>
      <p>Security controls are designed to resist high-rate and replayed requests from any interception tool. The system blocks behavior, not tool names.</p>
      <p>Recommended production settings include HTTPS-only secure cookies, restricted CORS origins, a strong session secret, SMTP credentials stored outside git, and a reverse proxy that exposes only the web entrypoint publicly.</p>
    </LegalPage>
  );
}
