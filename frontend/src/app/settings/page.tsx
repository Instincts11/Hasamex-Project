import { PageHeader } from "@/components/PageHeader";
import { ThemeSettings } from "@/components/ThemeSettings";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let corpus = null;
  try {
    corpus = await api.health();
  } catch {
    corpus = null;
  }

  return (
    <div className="w-full">
      <PageHeader title="Settings" subtitle="Analysis workspace and grounding rules for this corpus." />
      <ThemeSettings />
      {corpus ? (
        <>
          <section className="card mt-4 p-6">
            <h3 className="font-semibold tracking-tight">Corpus</h3>
            <dl className="mt-4 grid gap-3 text-sm">
              <Row label="Experts" value={String(corpus.expert_count)} />
              <Row label="Transcripts" value={String(corpus.transcript_count)} />
              <Row label="Evidence items" value={String(corpus.evidence_count)} />
              <Row label="Guide questions" value={String(corpus.guide_question_count)} />
              <Row label="Synthesis provider" value={corpus.provider} />
            </dl>
          </section>
          <section className="card mt-4 p-6">
            <h3 className="font-semibold tracking-tight">Grounding rules</h3>
            <ul className="mt-3 space-y-2 text-sm text-ink-secondary">
              <li>Quotes displayed in the UI come from the original transcript store.</li>
              <li>The model may interpret evidence. It does not invent quotes, timestamps, or experts.</li>
              <li>Coverage is expert count, not an AI confidence score.</li>
              <li>Single-expert observations are labeled and never shown as consensus.</li>
            </ul>
          </section>
        </>
      ) : (
        <p className="mt-4 text-sm text-muted">Workspace status is unavailable while the API is offline.</p>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-line pb-3 last:border-0 last:pb-0">
      <dt className="text-muted">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
