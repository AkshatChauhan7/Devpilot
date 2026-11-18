"use client";

import { SessionProvider } from "next-auth/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { useTheme } from "next-themes";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  const { theme, setTheme } = useTheme();

  useEffect(() => {
    const storedTheme = localStorage.getItem("devpilot-ui") ? JSON.parse(localStorage.getItem("devpilot-ui")!).state?.theme : "system";
    if (storedTheme && storedTheme !== "system") {
      setTheme(storedTheme);
    }
  }, [setTheme]);

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster />
      </QueryClientProvider>
    </SessionProvider>
  );
}