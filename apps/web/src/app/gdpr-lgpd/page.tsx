import { LegalPage } from "@/components/public-site/public-pages";

const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_BERRYBRAIN_SUPPORT_EMAIL || "support email not configured";

export default function GdprLgpd() {
  return (
    <LegalPage title="GDPR and LGPD">
      <p>BerryBrain is designed around data minimization, transparency, and user-controlled processing. Notes and graph data are treated as personal knowledge data.</p>
      <p>Users may request access, correction, export, or deletion of account data. Local vault files remain under the operator's storage control.</p>
      <p>Processing purposes include authentication, account security, note indexing, graph construction, retrieval, insight generation, and optional provider integrations configured by the local owner.</p>
      <p>For LGPD and GDPR requests, include the account email, request type, and enough context to verify ownership. Do not include passwords, OTP codes, API keys, or private notes in email.</p>
      <p>Privacy and data protection contact: {SUPPORT_EMAIL}.</p>
    </LegalPage>
  );
}
