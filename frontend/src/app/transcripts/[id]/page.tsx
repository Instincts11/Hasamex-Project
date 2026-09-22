import { PageHeader } from "@/components/PageHeader";
import { TranscriptWorkspace } from "@/components/TranscriptWorkspace";
import { api } from "@/lib/api";
import { marketMeta } from "@/lib/ui";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function TranscriptDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const transcript = await api.transcript(id);
  const meta = marketMeta(transcript.market);

  return (
    <div>
      <Link href="/transcripts" className="text-sm font-medium text-accent hover:text-accent-hover">
        All transcripts
      </Link>
      <PageHeader
        eyebrow={`${meta.flag} ${transcript.market}`}
        title={transcript.expert}
        subtitle={`${transcript.role} · ${transcript.evidence_count} evidence items · ${transcript.segment_count} turns`}
      />
      <TranscriptWorkspace transcript={transcript} />
    </div>
  );
}
