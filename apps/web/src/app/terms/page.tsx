import { LegalPage } from "@/components/public-site/public-pages";

const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_BERRYBRAIN_SUPPORT_EMAIL || "support email not configured";

export default function Terms() {
  return (
    <LegalPage title="Terms">
      <p>BerryBrain is a knowledge system for personal study, research, and note organization. Users are responsible for the material they store and process.</p>
      <p>The system may use local or configured cloud providers. Provider use must be configured by the local owner.</p>
      <p>Users should not store content they do not have the right to process. Automated insights, graph connections, and generated summaries are assistance outputs and should be reviewed before relying on them.</p>
      <p>Account misuse, abuse automation, credential stuffing, or attempts to bypass protective controls may lead to local lockout or instance restrictions.</p>
      <p>Support and account requests: {SUPPORT_EMAIL}.</p>
    </LegalPage>
  );
}
