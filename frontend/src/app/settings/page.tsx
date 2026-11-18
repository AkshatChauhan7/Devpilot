"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Github, Key, Database, Server, Bell, User, Save, Loader2 } from "lucide-react";
import { useSession } from "next-auth/react";
import { useUIStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const { data: session } = useSession();
  const { theme, setTheme } = useUIStore();
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your DevPilot configuration</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="github">GitHub</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile</CardTitle>
              <CardDescription>Manage your account information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-2xl font-bold text-primary">
                    {session?.user?.name?.[0] || session?.user?.email?.[0] || "U"}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-medium">{session?.user?.name || "User"}</h3>
                  <p className="text-sm text-muted-foreground">{session?.user?.email}</p>
                  <p className="text-xs text-muted-foreground">@{session?.user?.username || session?.user?.email?.split("@")[0]}</p>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Name" defaultValue={session?.user?.name || ""} placeholder="Your name" />
                <Input label="Username" defaultValue={session?.user?.username || ""} placeholder="GitHub username" disabled />
                <Input label="Email" type="email" defaultValue={session?.user?.email || ""} placeholder="email@example.com" disabled />
                <Input label="GitHub ID" defaultValue={String((session?.user as any)?.githubId || "")} placeholder="GitHub ID" disabled />
              </div>
              <Button onClick={() => { setSaving(true); setTimeout(() => setSaving(false), 1000); }} disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* GitHub Tab */}
        <TabsContent value="github" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>GitHub Integration</CardTitle>
              <CardDescription>Manage your GitHub App installations and OAuth connections</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <Github className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <p className="font-medium">GitHub OAuth</p>
                    <p className="text-sm text-muted-foreground">Connected via GitHub OAuth</p>
                  </div>
                </div>
                <Badge variant="success">Connected</Badge>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">GitHub App Installations</h4>
                <p className="text-sm text-muted-foreground mb-4">
                  Install the DevPilot GitHub App on your organizations to enable repository automation.
                </p>
                <Button variant="outline" asChild>
                  <a href="https://github.com/apps/devpilot" target="_blank" rel="noopener noreferrer">
                    <Github className="mr-2 h-4 w-4" />
                    Install GitHub App
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Customize how DevPilot looks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-3">Theme</label>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { value: "light", label: "Light", icon: <Sun className="h-5 w-5" /> },
                    { value: "dark", label: "Dark", icon: <Moon className="h-5 w-5" /> },
                    { value: "system", label: "System", icon: <Server className="h-5 w-5" /> },
                  ].map((t) => (
                    <Button
                      key={t.value}
                      variant={theme === t.value ? "default" : "outline"}
                      className="h-20 flex-col gap-2"
                      onClick={() => setTheme(t.value as any)}
                    >
                      <div className="text-2xl">{t.icon}</div>
                      <span>{t.label}</span>
                    </Button>
                  ))}
                </div>
              </div>

              <div className="border-t pt-6">
                <label className="block text-sm font-medium mb-3">Sidebar</label>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-input" />
                    <span>Auto-collapse sidebar on mobile</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" className="rounded border-input" />
                    <span>Show sidebar icons only when collapsed</span>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>Configure how you receive updates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {[
                  { title: "Task completed", desc: "Get notified when tasks finish" },
                  { title: "Task failed", desc: "Get notified when tasks fail" },
                  { title: "Execution completed", desc: "Get notified when code executions finish" },
                  { title: "Pull request updates", desc: "Get notified about PR status changes" },
                  { title: "New repository analysis", desc: "Get notified when repository analysis completes" },
                ].map((n) => (
                  <label key={n.title} className="flex items-center justify-between cursor-pointer">
                    <div>
                      <p className="font-medium">{n.title}</p>
                      <p className="text-sm text-muted-foreground">{n.desc}</p>
                    </div>
                    <input type="checkbox" defaultChecked className="rounded border-input" />
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Advanced</CardTitle>
              <CardDescription>Developer settings and dangerous actions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="border-t pt-6">
                <h4 className="font-medium mb-3">Data Management</h4>
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Export Data</p>
                    <p className="text-sm text-muted-foreground">Download all your DevPilot data</p>
                  </div>
                  <Button variant="outline">Export</Button>
                </div>
                <div className="flex items-center justify-between p-4 border rounded-lg mt-3">
                  <div>
                    <p className="font-medium text-destructive">Delete Account</p>
                    <p className="text-sm text-muted-foreground">Permanently delete your account and all data</p>
                  </div>
                  <Button variant="destructive">Delete Account</Button>
                </div>
              </div>

              <div className="border-t pt-6">
                <h4 className="font-medium mb-3">Debug</h4>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Button variant="outline" onClick={() => console.log("Debug info", session)}>
                    <Server className="mr-2 h-4 w-4" />
                    Log Debug Info
                  </Button>
                  <Button variant="outline" onClick={() => localStorage.clear()}>
                    <Key className="mr-2 h-4 w-4" />
                    Clear Local Storage
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}