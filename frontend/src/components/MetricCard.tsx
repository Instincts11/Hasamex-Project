import { Icon } from "@/components/Icon";

type MetricIcon = "users" | "globe" | "file" | "quote";

export function MetricCard({
  value,
  label,
  hint,
  icon,
}: {
  value: string;
  label: string;
  hint?: string;
  icon?: MetricIcon;
}) {
  return (
    <div className="card relative z-10 h-full w-full p-5">
      <div className="flex items-start gap-3">
        {icon ? (
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-accent-soft text-accent min-[1501px]:h-12 min-[1501px]:w-12">
            <Icon name={icon} className="h-4 w-4 min-[1501px]:h-6 min-[1501px]:w-6" strokeWidth={2.4} />
          </span>
        ) : null}
        <div>
          <p className="text-3xl font-semibold tracking-tight text-ink">{value}</p>
          <p className="mt-0.5 text-sm font-medium text-ink-secondary">{label}</p>
          {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
        </div>
      </div>
    </div>
  );
}
