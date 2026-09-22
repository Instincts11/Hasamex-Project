import { marketMeta } from "@/lib/ui";

export function CountryIcon({
  market,
  className = "h-4 w-6",
}: {
  market: string;
  className?: string;
}) {
  const meta = marketMeta(market);
  if (!meta.icon) {
    return <span aria-hidden>{meta.flag}</span>;
  }
  return (
    <img
      src={meta.icon}
      alt=""
      className={`inline-block rounded-[2px] object-cover ring-1 ring-line ${className}`}
    />
  );
}
