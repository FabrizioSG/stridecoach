import type { GarminScreenshotMetrics, TrainingPlan, Workout } from "@stridecoach/shared-types";
import { Brain, Camera, LinkIcon, NotebookPen, RefreshCw, Upload, Watch } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/workouts/StatusBadge";
import { api, type StravaActivityCandidate } from "@/lib/api";
import { formatDate, formatKm } from "@/lib/utils";

export function WorkoutDetailsPage() {
  const { workoutId } = useParams();
  const [plan, setPlan] = useState<TrainingPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [candidates, setCandidates] = useState<StravaActivityCandidate[]>([]);
  const [linkMessage, setLinkMessage] = useState<string | null>(null);
  const [isLoadingCandidates, setIsLoadingCandidates] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [garminFiles, setGarminFiles] = useState<File[]>([]);
  const [garminMetrics, setGarminMetrics] = useState<GarminScreenshotMetrics | null>(null);
  const [garminMessage, setGarminMessage] = useState<string | null>(null);
  const [isImportingGarmin, setIsImportingGarmin] = useState(false);
  const [actualForm, setActualForm] = useState({
    distanceKm: "",
    durationMin: "",
    avgHr: "",
    avgCadence: "",
    avgPace: "",
    notes: "",
  });

  useEffect(() => {
    api
      .getActivePlan()
      .then(setPlan)
      .catch(() => setPlan(null))
      .finally(() => setIsLoading(false));
  }, []);

  const workout = useMemo(() => {
    const workouts = plan?.weeks.flatMap((week) => week.workouts) ?? [];
    return workouts.find((item) => item.id === workoutId) ?? workouts[0];
  }, [plan, workoutId]);

  useEffect(() => {
    if (!workout) return;
    setAnalysis(workout.aiAnalysis);
    setActualForm({
      distanceKm: workout.actualDistanceKm?.toString() ?? "",
      durationMin: workout.actualDurationMin?.toString() ?? "",
      avgHr: workout.actualAvgHr?.toString() ?? "",
      avgCadence: workout.actualAvgCadence?.toString() ?? "",
      avgPace: workout.actualAvgPace ?? "",
      notes: workout.notes ?? "",
    });
    setGarminMetrics(parseGarminMetrics(workout.garminScreenshotMetrics));
  }, [workout]);

  async function markComplete(selected: Workout) {
    const updated = await api.updateWorkout(selected.id, {
      status: "completed",
      actualDistanceKm: selected.plannedDistanceKm,
      actualDurationMin: selected.plannedDurationMin,
      actualAvgPace: selected.plannedPace,
    });

    replaceWorkout(updated);
  }

  async function saveActualWorkout() {
    if (!workout) return;
    const updated = await api.updateWorkout(workout.id, {
      status: "completed",
      actualDistanceKm: numberOrNull(actualForm.distanceKm),
      actualDurationMin: numberOrNull(actualForm.durationMin),
      actualAvgHr: numberOrNull(actualForm.avgHr),
      actualAvgCadence: numberOrNull(actualForm.avgCadence),
      actualAvgPace: actualForm.avgPace || null,
      notes: actualForm.notes || null,
    });
    replaceWorkout(updated);
  }

  function replaceWorkout(updated: Workout) {
    setPlan((current) =>
      current
        ? {
            ...current,
            weeks: current.weeks.map((week) => ({
              ...week,
              workouts: week.workouts.map((item) => (item.id === updated.id ? updated : item)),
            })),
          }
        : current,
    );
  }

  async function loadStravaCandidates() {
    if (!workout) return;
    setIsLoadingCandidates(true);
    setLinkMessage(null);
    try {
      const result = await api.getStravaCandidates(workout.id);
      setCandidates(result.activities);
      if (!result.activities.length) {
        setLinkMessage("No unmatched Strava activities found. Sync recent activities from Settings first.");
      }
    } catch {
      setLinkMessage("Unable to load Strava activities. Make sure Strava is connected.");
    } finally {
      setIsLoadingCandidates(false);
    }
  }

  async function linkCandidate(activity: StravaActivityCandidate) {
    if (!workout) return;
    setLinkMessage(null);
    try {
      const updated = await api.linkStravaActivity(workout.id, activity.id);
      replaceWorkout(updated);
      setCandidates((current) => current.filter((item) => item.id !== activity.id));
      setLinkMessage(`Linked ${activity.name}.`);
    } catch {
      setLinkMessage("Unable to link that activity.");
    }
  }

  async function unlinkStravaActivity() {
    if (!workout) return;
    setLinkMessage(null);
    try {
      const updated = await api.unlinkStravaActivity(workout.id);
      replaceWorkout(updated);
      setLinkMessage("Strava activity unlinked. Actual metrics were cleared.");
    } catch {
      setLinkMessage("Unable to unlink this activity.");
    }
  }

  async function generateAnalysis(regenerate = false) {
    if (!workout) return;
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const result = await api.analyzeWorkout(workout.id, regenerate);
      setAnalysis(
        result.analysis?.trim() ||
          `The API returned a successful response, but no visible analysis text. Length: ${
            result.analysisLength ?? 0
          }`,
      );
    } catch {
      setAnalysisError("Unable to generate analysis. Check your OpenAI API key and API logs.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function importGarminScreenshots() {
    if (!workout || garminFiles.length === 0) return;
    setIsImportingGarmin(true);
    setGarminMessage(null);
    try {
      const result = await api.importGarminScreenshots(workout.id, garminFiles);
      replaceWorkout(result.workout);
      setGarminMetrics(result.metrics);
      setAnalysis(null);
      setGarminMessage("Garmin screenshots imported. Actual workout data was updated.");
    } catch {
      setGarminMessage("Unable to read those screenshots. Try clearer Garmin stats screenshots.");
    } finally {
      setIsImportingGarmin(false);
    }
  }

  if (isLoading) return <Skeleton className="h-96" />;
  if (!workout) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-sm text-muted-foreground">
          No workout found. Import a training plan from Settings to add scheduled workouts.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
      <section className="grid gap-5">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>{workout.title}</CardTitle>
                <CardDescription>{formatDate(workout.scheduledDate)}</CardDescription>
              </div>
              <StatusBadge status={workout.status} />
            </div>
          </CardHeader>
          <CardContent className="grid gap-4">
            <p className="text-sm leading-6 text-muted-foreground">{workout.description}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <Detail label="Distance" value={formatKm(workout.plannedDistanceKm)} />
              <Detail label="Duration" value={`${workout.plannedDurationMin ?? "--"} min`} />
              <Detail label="Pace" value={workout.plannedPace ?? "Open"} />
              <Detail label="HR zone" value={workout.plannedHrZone ?? "Open"} />
            </div>
            {workout.status !== "completed" ? (
              <Button onClick={() => markComplete(workout)}>Mark workout complete</Button>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Camera className="h-5 w-5 text-primary" />
              <CardTitle>Garmin screenshots</CardTitle>
            </div>
            <CardDescription>
              Upload up to 3 Garmin stats screenshots to extract richer workout data for AI coaching.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed p-6 text-center hover:bg-muted/60">
              <Upload className="h-5 w-5 text-primary" />
              <span className="text-sm font-medium">Choose screenshots</span>
              <span className="text-xs text-muted-foreground">PNG, JPG, or HEIC if your browser supports it</span>
              <input
                className="hidden"
                type="file"
                accept="image/*"
                multiple
                onChange={(event) => {
                  const selected = Array.from(event.target.files ?? []);
                  setGarminFiles(selected.slice(0, 3));
                  setGarminMessage(
                    selected.length > 3 ? "Only the first 3 screenshots will be uploaded." : null,
                  );
                }}
              />
            </label>
            {garminFiles.length ? (
              <div className="grid gap-2 text-sm text-muted-foreground">
                {garminFiles.map((file) => (
                  <p key={`${file.name}-${file.size}`}>{file.name}</p>
                ))}
              </div>
            ) : null}
            <Button onClick={importGarminScreenshots} disabled={!garminFiles.length || isImportingGarmin}>
              <Camera className="h-4 w-4" />
              {isImportingGarmin ? "Reading screenshots" : "Import Garmin data"}
            </Button>
            {garminMessage ? <p className="text-sm text-muted-foreground">{garminMessage}</p> : null}
            <GarminMetricsPreview metrics={garminMetrics} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Watch className="h-5 w-5 text-primary" />
              <CardTitle>Actual workout</CardTitle>
            </div>
            <CardDescription>Save manual results or link a Strava activity below.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <Detail label="Distance" value={formatKm(workout.actualDistanceKm)} />
            <Detail label="Duration" value={`${workout.actualDurationMin ?? "--"} min`} />
            <Detail label="Average HR" value={workout.actualAvgHr ? `${workout.actualAvgHr} bpm` : "--"} />
            <Detail label="Cadence" value={workout.actualAvgCadence ? `${workout.actualAvgCadence} spm` : "--"} />
            <input
              className="rounded-md border bg-background px-3 py-2 text-sm"
              placeholder="Distance km"
              value={actualForm.distanceKm}
              onChange={(event) => setActualForm((form) => ({ ...form, distanceKm: event.target.value }))}
            />
            <input
              className="rounded-md border bg-background px-3 py-2 text-sm"
              placeholder="Duration min"
              value={actualForm.durationMin}
              onChange={(event) => setActualForm((form) => ({ ...form, durationMin: event.target.value }))}
            />
            <input
              className="rounded-md border bg-background px-3 py-2 text-sm"
              placeholder="Average HR"
              value={actualForm.avgHr}
              onChange={(event) => setActualForm((form) => ({ ...form, avgHr: event.target.value }))}
            />
            <input
              className="rounded-md border bg-background px-3 py-2 text-sm"
              placeholder="Average cadence"
              value={actualForm.avgCadence}
              onChange={(event) => setActualForm((form) => ({ ...form, avgCadence: event.target.value }))}
            />
            <input
              className="rounded-md border bg-background px-3 py-2 text-sm sm:col-span-2"
              placeholder="Average pace, e.g. 5:42/km"
              value={actualForm.avgPace}
              onChange={(event) => setActualForm((form) => ({ ...form, avgPace: event.target.value }))}
            />
            <Button className="sm:col-span-2" onClick={saveActualWorkout}>
              Save actual workout
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <LinkIcon className="h-5 w-5 text-primary" />
              <CardTitle>Link Strava activity</CardTitle>
            </div>
            <CardDescription>Manually match this workout if automatic sync misses it.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button variant="outline" onClick={loadStravaCandidates} disabled={isLoadingCandidates}>
              <RefreshCw className="h-4 w-4" />
              {isLoadingCandidates ? "Loading" : "Load unmatched activities"}
            </Button>
            {candidates.map((activity) => (
              <div key={activity.id} className="rounded-md border p-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{activity.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {activity.distanceKm ?? "--"} km · {activity.durationMin ?? "--"} min ·{" "}
                      {activity.averagePace ?? "pace --"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activity.startDate ? new Date(activity.startDate).toLocaleDateString() : "No date"}
                      {activity.score !== null ? ` · match ${activity.score}%` : ""}
                    </p>
                  </div>
                  <Button size="sm" onClick={() => linkCandidate(activity)}>
                    Link
                  </Button>
                </div>
              </div>
            ))}
            {linkMessage ? <p className="text-sm text-muted-foreground">{linkMessage}</p> : null}
            {workout.actualDistanceKm || workout.actualDurationMin ? (
              <Button variant="outline" onClick={unlinkStravaActivity}>
                Unlink Strava activity
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </section>

      <aside className="grid content-start gap-5">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <NotebookPen className="h-5 w-5 text-primary" />
              <CardTitle>Notes</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <textarea
              className="min-h-28 w-full rounded-md border bg-background px-3 py-2 text-sm"
              placeholder="How did it feel?"
              value={actualForm.notes}
              onChange={(event) => setActualForm((form) => ({ ...form, notes: event.target.value }))}
            />
            <Button className="mt-3" variant="outline" onClick={saveActualWorkout}>
              Save notes
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              <CardTitle>AI analysis</CardTitle>
            </div>
            <CardDescription>OpenAI-powered coaching summary for this workout.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button onClick={() => generateAnalysis(Boolean(analysis))} disabled={isAnalyzing}>
              <Brain className="h-4 w-4" />
              {isAnalyzing ? "Analyzing" : analysis ? "Regenerate analysis" : "Generate analysis"}
            </Button>
            {analysis ? (
              <div className="rounded-md bg-muted p-4 text-sm leading-6 text-muted-foreground">
                <ReactMarkdown
                  components={{
                    h3: ({ children }) => (
                      <h3 className="mb-1 mt-4 first:mt-0 text-sm font-semibold text-foreground">
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5">{children}</ul>,
                    li: ({ children }) => <li>{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                  }}
                >
                  {analysis}
                </ReactMarkdown>
              </div>
            ) : null}
            {analysisError ? <p className="text-sm text-destructive">{analysisError}</p> : null}
          </CardContent>
        </Card>
      </aside>
    </div>
  );
}

function numberOrNull(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseGarminMetrics(value: string | null): GarminScreenshotMetrics | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as GarminScreenshotMetrics;
  } catch {
    return null;
  }
}

function GarminMetricsPreview({ metrics }: { metrics: GarminScreenshotMetrics | null }) {
  if (!metrics) {
    return (
      <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
        No Garmin screenshot data imported yet.
      </div>
    );
  }

  const rawMetrics = metrics.rawMetrics ?? [];
  const summaryItems = [
    ["Distance", metrics.summary?.distanceKm ? `${metrics.summary.distanceKm} km` : null],
    ["Duration", metrics.summary?.durationMin ? `${metrics.summary.durationMin} min` : null],
    ["Avg pace", metrics.summary?.avgPace ?? null],
    ["Avg HR", metrics.summary?.avgHeartRate ? `${metrics.summary.avgHeartRate} bpm` : null],
    ["Cadence", metrics.summary?.avgCadence ? `${metrics.summary.avgCadence} spm` : null],
  ].filter((item): item is [string, string] => Boolean(item[1]));

  return (
    <div className="grid gap-3">
      {summaryItems.length ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {summaryItems.map(([label, value]) => (
            <Detail key={label} label={label} value={value} />
          ))}
        </div>
      ) : null}
      {rawMetrics.length ? (
        <div className="max-h-72 overflow-auto rounded-md border">
          <div className="grid divide-y">
            {rawMetrics.map((metric, index) => (
              <div
                key={`${metric.section}-${metric.label}-${index}`}
                className="grid gap-1 px-3 py-2 text-sm sm:grid-cols-[9rem_1fr_auto]"
              >
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  {metric.section}
                </span>
                <span>{metric.label}</span>
                <span className="font-medium text-foreground">{metric.value}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {metrics.notes?.length ? (
        <p className="text-xs text-muted-foreground">{metrics.notes.join(" ")}</p>
      ) : null}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted p-3">
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}
