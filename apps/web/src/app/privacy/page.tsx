import { LegalPage } from "@/components/public-site/public-pages";

export default function Privacy() {
  return (
    <LegalPage title="Privacy">
      <p>BerryBrain is local-first. User notes remain in the configured vault unless the user enables external providers.</p>
      <p>When cloud AI, email, or external enrichment is configured, BerryBrain records provider, model, purpose, status, and evidence so the user can understand what left the local system.</p>
      <p>Account data is separated from note content. Security events may include timestamps, IP-derived request metadata, session state, and administrative actions needed to protect the service.</p>
      <p>Knowledge data is processed to build notes, concepts, graph edges, insights, and retrieval indexes. The product should never hide whether a result came from local processing or a configured external provider.</p>
      <p>For privacy requests, contact contato@optlabs.com.br.</p>
    </LegalPage>
  );
}
