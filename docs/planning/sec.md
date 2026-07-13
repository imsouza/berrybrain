# Security, Auth, and Public Site Plan

## Summary
BerryBrain is now a free, open source, self-hosted app. The security model is a single local owner account per instance, not SaaS multi-user administration. Keep first-party login, email 2FA/recovery, anti-abuse controls, privacy/legal pages, and an English public marketing site.

## Auth
- [x] Implement app-owned auth in FastAPI.
- [x] Add users, sessions, email verification, password reset, 2FA challenges, login attempts, and audit events.
- [x] Use Argon2id for password hashing in production dependency set.
- [x] Use secure session cookies: `HttpOnly`, `Secure`, `SameSite`, rotation on login, logout-all support.
- [x] Require email verification before full account access.
- [x] Reset password tokens must be short-lived, single-use, and revoke old sessions.

## 2FA
- [x] Email OTP through SMTP using `contato@optlabs.com.br` as default sender.
- [x] Store only hashed OTP codes.
- [x] Add TTL, retry limit, resend cooldown, and one-time use.
- [ ] Add optional TOTP later for authenticator apps.

## Anti-Abuse
- [x] Rate-limit login, signup, reset password, email verification, and 2FA by IP/account/email.
- [x] Add progressive lockout for repeated failures.
- [x] Use generic auth errors to prevent user enumeration on login/reset.
- [x] Add CSRF protection for authenticated auth mutations.
- [x] Restrict CORS when configured and validate Origin on sensitive routes.
- [x] Add security headers: CSP, HSTS, frame restrictions, Referrer-Policy, Permissions-Policy.
- [x] Treat Caido/Burp as normal hostile traffic: block invalid/replayed/high-rate requests, not tool names.

## Email
- [x] Add SMTP env vars only: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
- [x] Never commit credentials.
- [x] Use `apzin` only as a reference for how Umbler SMTP is configured.
- [x] Log delivery status without logging secrets or OTP codes.

## Local Owner
- [x] Keep the first-run setup flow as the single local owner account.
- [x] Remove the public admin panel from the product surface.
- [x] Redirect legacy `/admin` routes to account settings.
- [x] Keep authenticated maintenance/audit controls server-side where still needed.
- [x] Every sensitive owner action writes an audit event.
- [ ] Rename legacy backend identifiers such as `BERRYBRAIN_ADMIN_EMAIL` and `/setup/admin` in a compatibility-safe migration.

## Public Site
- [x] Build English marketing pages:
  - landing page;
  - login;
- setup;
  - privacy;
  - terms;
  - security;
  - GDPR/LGPD;
  - contact.
- [x] Use BerryBrain logo and existing colors.
- [x] Add screenshots from `docs/planning/assets/print1.png`, `print2.jpeg`, `print3.png` to the public site.
- [x] Keep design simple, distinctive, privacy-first, and not generic AI-themed.
- [x] Support contact: `contato@optlabs.com.br`.
- [x] Make `/` open the public landing site.
- [x] Move the private BerryBrain app to `/brain` behind session checking.
- [x] Add structured navbar and footer with Product, Trust, Company, Privacy, Terms, GDPR/LGPD, Security, and Contact links.
- [x] Add account settings page for account, privacy, and security controls.
- [x] Add "Keep me signed in" session behavior on login.

## Repository Privacy
- GitHub tokens exposed in chat should be treated as compromised and rotated when possible.
- Remove token from git remote.
- Use SSH or credential manager.
- Make repo private with GitHub CLI only after safe auth is configured.

## Tests
- [x] Add schema and smoke tests for signup, generic login errors, admin allow/deny, and security headers.
- [ ] Add full browser E2E for signup, email verification, login, 2FA, reset password, lockout, CSRF, CORS, admin allow/deny, audit events, legal pages, and security headers.

## 2026-07-11 Implementation Log

- Added auth/security ORM tables: users, sessions, OTP challenges, login attempts, security audit events.
- Added `/api/v1/auth/signup`, `/verify-email`, `/login`, `/verify-2fa`, `/me`, `/logout`, `/logout-all`, `/password-reset/request`, and `/password-reset/confirm`.
- Added `/api/v1/admin/users`, lock/unlock, revoke sessions, and audit event listing guarded by the configured admin account session.
- Added SMTP OTP sender using `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM`.
- Added security headers and Origin validation middleware.
- Added public pages: `/welcome`, `/login`, `/signup`, `/privacy`, `/terms`, `/security`, `/gdpr-lgpd`, `/contact`, `/admin`.
- Added public screenshot assets to the landing preview.
- Moved public landing to `/`; private system app now lives at `/brain`.
- Added global public footer, professional navbar, richer legal/contact content, account settings page, and remember-me login behavior.
