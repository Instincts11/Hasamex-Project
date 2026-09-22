"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ExplorerDetailRedirect() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  useEffect(() => {
    router.replace(`/transcripts/${params.id}${window.location.hash}`);
  }, [params.id, router]);

  return <p className="text-sm text-muted">Opening transcript…</p>;
}
