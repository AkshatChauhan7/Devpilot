"use client";

import { useSession, signOut } from "next-auth/react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { DashboardContent } from "./DashboardContent";
import { useUIStore } from "@/lib/store";

export function Dashboard({ user }: { user?: any }) {
  const { sidebarOpen, theme } = useUIStore();
  const { data: session } = useSession();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar user={session?.user} />
      <div className={cn("lg:pl-64 transition-all duration-300", sidebarOpen ? "" : "lg:pl-20")}>
        <Header user={session?.user} onSignOut={() => signOut({ callbackUrl: "/login" })} />
        <main className="p-4 lg:p-6">
          <DashboardContent />
        </main>
      </div>
    </div>
  );
}

import { cn } from "@/lib/utils";