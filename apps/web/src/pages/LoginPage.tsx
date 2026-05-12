import { Activity, Lock } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">StrideCoach</h1>
            <p className="text-sm text-muted-foreground">Run plans with calmer feedback loops.</p>
          </div>
        </div>
        <Card>
          <CardHeader>
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-md bg-muted text-primary">
              <Lock className="h-5 w-5" />
            </div>
            <CardTitle>Private beta</CardTitle>
            <CardDescription>
              StrideCoach is currently invite-only while we tune imports, Garmin screenshot analysis,
              and coaching feedback.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="rounded-md bg-muted p-4 text-sm leading-6 text-muted-foreground">
              New signups are paused. Existing testers can continue using their active sessions, and
              login access will reopen when the beta expands.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
