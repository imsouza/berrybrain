# Security, Auth, Admin, and Public Site Plan

## Summary
Build BerryBrain as a public SaaS-ready app with first-party login/signup, email 2FA, anti-abuse controls, admin management, privacy/legal pages, and an English public marketing site.

## Auth
- Implement app-owned auth in FastAPI.
- Add users, sessions, email verification, password reset, 2FA challenges, login attempts, and audit events.
- Use Argon2id for password hashing.
- Use secure session cookies: `HttpOnly`, `Secure`, `SameSite`, rotation on login, logout-all support.
- Require email verification before full account access.
- Reset password tokens must be short-lived, single-use, and revoke old sessions.

## 2FA
- Email OTP through Umbler SMTP using `contato@optlabs.com.br`.
- Store only hashed OTP codes.
- Add TTL, retry limit, resend cooldown, and one-time use.
- Add optional TOTP later for authenticator apps.

## Anti-Abuse
- Rate-limit login, signup, reset password, email verification, 2FA, and resend endpoints by IP, account, and email.
- Add progressive lockout for repeated failures.
- Use generic auth errors to prevent user enumeration.
- Add CSRF protection for authenticated mutations.
- Restrict CORS and validate Origin/Referer on sensitive routes.
- Add security headers: CSP, HSTS, frame restrictions, Referrer-Policy, Permissions-Policy.
- Treat Caido/Burp as normal hostile traffic: block invalid/replayed/high-rate requests, not tool names.

## Email
- Add SMTP env vars only: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
- Never commit credentials.
- Use `apzin` only as a reference for how Umbler SMTP is configured.
- Log delivery status without logging secrets or OTP codes.

## Admin
- Add `/admin` protected by GitHub SSO.
- Allow only GitHub username `imsouza`.
- Admin can view users, lock/unlock accounts, force password reset, revoke sessions, and inspect audit/security events.
- Every admin action writes an audit event.

## Public Site
- Build English marketing pages:
  - landing page;
  - login;
  - signup;
  - privacy;
  - terms;
  - security;
  - GDPR/LGPD;
  - contact.
- Use BerryBrain logo, existing colors, and screenshots from `docs/planning/assets/print1.png`, `print2.jpeg`, `print3.png`.
- Keep design simple, distinctive, privacy-first, and not generic AI-themed.
- Support contact: `contato@optlabs.com.br`.

## Repository Privacy
- The GitHub token exposed in chat must be revoked before use.
- Remove token from git remote.
- Use SSH or credential manager.
- Make repo private with GitHub CLI only after safe auth is configured.

## Tests
- Signup, email verification, login, 2FA, reset password, lockout, CSRF, CORS, admin SSO allow/deny, audit events, legal pages, and security headers.

