import { LogOut, PlugZap, RefreshCw, UploadCloud } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";

export function SettingsPage() {
  const { isConfigured, session, signOut } = useAuth();
  const [searchParams] = useSearchParams();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [replaceExistingPlan, setReplaceExistingPlan] = useState(false);
  const [stravaStatus, setStravaStatus] = useState<{
    connected: boolean;
    athleteName?: string | null;
    scope?: string | null;
  } | null>(null);
  const [stravaMessage, setStravaMessage] = useState<string | null>(
    searchParams.get("strava") === "connected" ? "Strava connected successfully." : null,
  );
  const [isConnectingStrava, setIsConnectingStrava] = useState(false);

  useEffect(() => {
    api
      .getStravaStatus()
      .then(setStravaStatus)
      .catch(() => setStravaStatus({ connected: false }));
  }, []);

  async function handleImportPlan(file: File | undefined) {
    if (!file) return;
    setIsImporting(true);
    setImportStatus(null);
    try {
      const result = await api.importTrainingPlan(file, replaceExistingPlan);
      const workoutCount = result.weeks.reduce((total, week) => total + week.workouts.length, 0);
      setImportStatus(`Imported ${result.title} with ${workoutCount} workouts.`);
    } catch {
      setImportStatus("Unable to upload the plan. Check that the API is running and you are signed in.");
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handleConnectStrava() {
    setIsConnectingStrava(true);
    setStravaMessage(null);
    try {
      const result = await api.connectStrava();
      window.location.href = result.authorizationUrl;
    } catch {
      setStravaMessage("Unable to start Strava connection. Check API credentials and server logs.");
      setIsConnectingStrava(false);
    }
  }

  async function handleSyncStrava() {
    setStravaMessage(null);
    try {
      const result = await api.syncStrava();
      setStravaMessage(`Fetched ${result.activities.length} recent Strava activities.`);
    } catch {
      setStravaMessage("Unable to sync Strava activities yet.");
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Supabase Auth is configured for Google OAuth only.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="rounded-md bg-muted p-4 text-sm">
            <p className="font-medium">{session?.user.email ?? "Demo mode"}</p>
            <p className="mt-1 text-muted-foreground">
              {isConfigured ? "Google OAuth is ready." : "Add Supabase env vars to enable login."}
            </p>
          </div>
          <Button variant="outline" onClick={signOut}>
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Integrations</CardTitle>
          <CardDescription>Connect activity sources and future data providers.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="rounded-md border p-4">
            <div className="flex items-start gap-3">
              <PlugZap className="mt-0.5 h-5 w-5 text-primary" />
              <div className="min-w-0 flex-1">
                <p className="font-medium">Strava</p>
                <p className="text-sm text-muted-foreground">
                  {stravaStatus?.connected
                    ? `Connected${stravaStatus.athleteName ? ` as ${stravaStatus.athleteName}` : ""}.`
                    : "Connect Strava to prepare activity syncing."}
                </p>
                {stravaStatus?.scope ? (
                  <p className="mt-1 text-xs text-muted-foreground">Scopes: {stravaStatus.scope}</p>
                ) : null}
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button onClick={handleConnectStrava} disabled={isConnectingStrava}>
                <PlugZap className="h-4 w-4" />
                {stravaStatus?.connected ? "Reconnect" : "Connect Strava"}
              </Button>
              {stravaStatus?.connected ? (
                <Button variant="outline" onClick={handleSyncStrava}>
                  <RefreshCw className="h-4 w-4" />
                  Sync recent
                </Button>
              ) : null}
            </div>
            {stravaMessage ? <p className="mt-3 text-sm text-muted-foreground">{stravaMessage}</p> : null}
          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Import training plan</CardTitle>
          <CardDescription>Upload a CSV or Excel plan to create scheduled workouts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-center">
          <div className="rounded-md border border-dashed p-4">
            <div className="flex items-start gap-3">
              <UploadCloud className="mt-1 h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Plan file</p>
                <p className="text-sm text-muted-foreground">
                  Expected columns include date, workout/title, distance, duration, pace, HR zone, and week.
                </p>
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="mt-4 block w-full text-sm text-muted-foreground file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:bg-primary/90"
              onChange={(event) => handleImportPlan(event.target.files?.[0])}
            />
            <label className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={replaceExistingPlan}
                onChange={(event) => setReplaceExistingPlan(event.target.checked)}
                className="h-4 w-4 rounded border-input"
              />
              Replace my existing imported plans
            </label>
            {importStatus ? (
              <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span>{importStatus}</span>
                <Button asChild size="sm" variant="ghost" className="px-0 text-primary hover:bg-transparent">
                  <Link to="/plan">View plan</Link>
                </Button>
              </div>
            ) : null}
          </div>
          <Button
            type="button"
            variant="outline"
            disabled={isImporting}
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud className="h-4 w-4" />
            {isImporting ? "Uploading" : "Choose file"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
