"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Github, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);

  const handleGitHubLogin = async () => {
    setLoading(true);
    await signIn("github", { callbackUrl: "/" });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10">
            <Zap className="h-10 w-10 text-primary" />
          </div>
          <CardTitle className="text-2xl">Welcome to DevPilot</CardTitle>
          <CardDescription>
            Autonomous AI-powered development assistant. Sign in with GitHub to get started.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            className="w-full"
            size="lg"
            onClick={handleGitHubLogin}
            disabled={loading}
            loading={loading}
          >
            <Github className="mr-2 h-5 w-5" />
            Continue with GitHub
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or</span>
            </div>
          </div>

          <p className="text-center text-sm text-muted-foreground">
            By continuing, you agree to our{" "}
            <a href="#" className="underline hover:text-primary">Terms of Service</a>
            {" "}and{" "}
            <a href="#" className="underline hover:text-primary">Privacy Policy</a>
          </p>

          <div className="text-center text-xs text-muted-foreground">
            DevPilot will request access to your repositories to enable AI-powered automation.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}