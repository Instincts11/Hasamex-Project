import { GuideQuestionCard } from "@/components/GuideQuestionCard";
import type { GuideQuestion, GuideQuestionResult } from "@/lib/types";

export function Guide({
  questions,
  results,
  expanded,
  loading,
  onToggle,
}: {
  questions: GuideQuestion[];
  results: Record<number, GuideQuestionResult>;
  expanded: number | null;
  loading: number | "all" | null;
  onToggle: (number: number) => void;
}) {
  return (
    <div className="grid w-full gap-4">
      {questions.map((question) => (
        <GuideQuestionCard
          key={question.number}
          questionNumber={question.number}
          questionText={question.text}
          result={results[question.number]}
          loading={loading === question.number || loading === "all"}
          expanded={expanded === question.number}
          onToggle={() => {
            if (loading) return;
            onToggle(question.number);
          }}
        />
      ))}
    </div>
  );
}
