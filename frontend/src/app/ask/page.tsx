import { ChatPanel } from "@/components/ChatPanel";
import { PageHeader } from "@/components/PageHeader";

export default function AskPage() {
  return (
    <div className="flex min-h-[calc(100dvh-8rem)] flex-col">
      <PageHeader
        title="Ask the Calls"
        subtitle="Ask questions across all expert interviews. Answers are grounded in the provided transcripts."
      />
      <ChatPanel />
    </div>
  );
}
