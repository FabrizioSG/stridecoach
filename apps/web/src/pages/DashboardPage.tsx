import type { DashboardSummary, Workout } from "@stridecoach/shared-types";
import { Brain, CalendarClock, Flame } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts";

import { MetricCard } from "@/components/dashboard/MetricCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { WorkoutCard } from "@/components/workouts/WorkoutCard";
import { api } from "@/lib/api";
import { formatDate, formatKm } from "@/lib/utils";

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .getDashboard()
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <DashboardLoading />;
  }

  if (!summary) {
    return <EmptyState />;
  }

  if (
    !summary.upcomingWorkout &&
    summary.recentWorkouts.length === 0 &&
    summary.weeklyPlannedMileageKm === 0
  ) {
    return <EmptyState />;
  }

  const upcoming = summary.upcomingWorkout;
  const consistencyData = summary.consistency.length
    ? summary.consistency
    : [{ week: "W1", completed: 0, planned: 0 }];
  const chartWidth = Math.max(720, consistencyData.length * 58);

  return (
    <div className="grid gap-5">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          title="Weekly mileage"
          value={`${formatMileage(summary.weeklyCompletedMileageKm)} / ${formatMileage(
            summary.weeklyPlannedMileageKm,
          )} km`}
          detail="Ran / planned this week"
          icon={Flame}
        />
        <Card className="xl:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle>Upcoming workout</CardTitle>
            <CardDescription>
              {upcoming ? `${formatDate(upcoming.scheduledDate)} - ${formatKm(upcoming.plannedDistanceKm)}` : "Nothing scheduled"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{upcoming?.title ?? "Recovery day"}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {upcoming?.description ?? "Use this window to stretch, sleep, and let the plan breathe."}
            </p>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle>Training consistency</CardTitle>
            <CardDescription>Completed workouts against the weekly plan.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto pb-2">
              <BarChart
                width={chartWidth}
                height={320}
                data={consistencyData}
                margin={{ top: 8, right: 20, left: -10, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="week" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Legend
                  verticalAlign="top"
                  align="right"
                  iconType="circle"
                  wrapperStyle={{ paddingBottom: 16, fontSize: 12 }}
                />
                <Bar dataKey="planned" name="Planned" fill="#94a3b8" radius={[6, 6, 0, 0]} />
                <Bar dataKey="completed" name="Completed" fill="#0f766e" radius={[6, 6, 0, 0]} />
              </BarChart>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">AI coach insights</h2>
          </div>
          <Card>
            <CardContent className="p-5">
              <p className="text-sm leading-6 text-muted-foreground">{summary.aiInsight}</p>
              <p className="mt-4 rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                Personalized workout analysis appears on each workout after you generate it.
              </p>
            </CardContent>
          </Card>
        </div>

        <div>
          <div className="mb-3 flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Recent workouts</h2>
          </div>
          <div className="grid gap-3">
            {summary.recentWorkouts.length ? (
              summary.recentWorkouts.map((workout: Workout) => <WorkoutCard key={workout.id} workout={workout} />)
            ) : (
              <EmptyState />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function formatMileage(value: number) {
  return value % 1 === 0 ? value.toFixed(0) : value.toFixed(1);
}

function DashboardLoading() {
  return (
    <div className="grid gap-4">
      <Skeleton className="h-32" />
      <Skeleton className="h-72" />
      <Skeleton className="h-40" />
    </div>
  );
}

function EmptyState() {
  return (
    <Card>
      <CardContent className="p-8 text-center text-sm text-muted-foreground">
        No training plan yet. Go to Settings to import a CSV or Excel plan when you are ready.
      </CardContent>
    </Card>
  );
}
