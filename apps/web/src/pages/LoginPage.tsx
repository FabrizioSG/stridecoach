import { Activity, Chrome } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";

export function LoginPage() {
  const { isConfigured, signInWithGoogle } = useAuth();

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
            <CardTitle>Welcome back</CardTitle>
            <CardDescription>Continue with Google to open your training workspace.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Button onClick={signInWithGoogle} disabled={!isConfigured}>
              <Chrome className="h-4 w-4" />
              Continue with Google
            </Button>
            {!isConfigured ? (
              <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
                Supabase env vars are not configured yet, so the starter app will open in demo mode.
              </p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
