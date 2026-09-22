import { PageHeader } from "@/components/PageHeader";
import { TranscriptsBrowser } from "@/components/TranscriptsBrowser";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function TranscriptsPage() {
  let transcripts;
  try {
    const summaries = await api.transcripts();
    transcripts = await Promise.all(summaries.map((item) => api.transcript(item.transcript_id)));
  } catch {
    return (
      <div>
        <PageHeader title="Transcripts" subtitle="The analysis API is not reachable." />
        <p className="text-caution">Start the backend on port 8000, then refresh.</p>
      </div>
    );
  }
  return (
    <div>
      <PageHeader
        title="Transcripts"
        subtitle="Open a source interview. Citations from analysis pages scroll to the matching timestamp."
      />
      <TranscriptsBrowser transcripts={transcripts} />
    </div>
  );
}
