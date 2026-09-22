"use client";

import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg text-ink">
      <TopBar />
      <Sidebar />
      <div className="content-offset pt-14 pl-[68px] min-[1201px]:pl-[252px] max-[510px]:pl-14">
        <main className="app-main w-full px-4 pb-12 pt-6 md:px-4 lg:px-4 min-[1441px]:px-10">{children}</main>
      </div>
    </div>
  );
}
