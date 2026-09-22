import { coverageTone } from "@/lib/ui";

export function EvidenceCoverage({
  covered,
  total,
  singleExpert,
}: {
  covered: number;
  total: number;
  singleExpert?: boolean;
}) {
  const tone = coverageTone(covered, total);
  const styles = {
    full: "bg-support-soft text-support",
    partial: "bg-caution-soft text-caution",
    single: "bg-conflict-soft text-conflict",
  }[tone];

  return (
    <span
      className={`coverage-pill inline-flex shrink-0 items-center gap-2 rounded-full px-2.5 py-1 text-xs font-medium ${styles}`}
    >
      <span className="flex gap-0.5">
        {Array.from({ length: total }).map((_, index) => (
          <span
            key={index}
            className={`h-1.5 w-1.5 rounded-full ${index < covered ? "bg-current" : "bg-current/25"}`}
          />
        ))}
      </span>
      {singleExpert || tone === "single"
        ? "Single-expert observation"
        : `${covered} / ${total} experts`}
    </span>
  );
}
