import type { TrainingPlan, Workout } from "@stridecoach/shared-types";
import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { WorkoutCard } from "@/components/workouts/WorkoutCard";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export function TrainingPlanPage() {
  const [plan, setPlan] = useState<TrainingPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .getActivePlan()
      .then(setPlan)
      .catch(() => setPlan(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function markComplete(workout: Workout) {
    const updated = await api.updateWorkout(workout.id, {
      status: "completed",
      actualDistanceKm: workout.plannedDistanceKm,
      actualDurationMin: workout.plannedDurationMin,
      actualAvgPace: workout.plannedPace,
    });

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

  async function deletePlan() {
    if (!plan) return;
    const confirmed = window.confirm(`Delete "${plan.title}" and all its workouts?`);
    if (!confirmed) return;
    await api.deletePlan(plan.id);
    setPlan(null);
  }

  if (isLoading) return <Skeleton className="h-96" />;
  if (!plan) return <EmptyPlan />;

  return (
    <div className="grid gap-5">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle>{plan.title}</CardTitle>
              <CardDescription>
                Starts {formatDate(plan.startsOn)} {plan.goalRace ? `for ${plan.goalRace}` : ""}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={deletePlan}>
              <Trash2 className="h-4 w-4" />
              Delete plan
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-6 text-muted-foreground">{plan.description}</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <Accordion type="single" collapsible defaultValue={plan.weeks[0]?.id}>
            {plan.weeks.map((week) => (
              <AccordionItem key={week.id} value={week.id}>
                <AccordionTrigger>
                  <span>
                    Week {week.weekNumber}: {week.focus}
                    <span className="ml-2 text-xs font-normal text-muted-foreground">
                      Starts {formatDate(week.startsOn)}
                    </span>
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="grid gap-3">
                    {week.workouts.map((workout) => (
                      <WorkoutCard key={workout.id} workout={workout} onComplete={markComplete} />
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
}

function EmptyPlan() {
  return (
    <Card>
      <CardContent className="p-8 text-center text-sm text-muted-foreground">
        No active plan yet. Import a CSV or Excel plan from Settings to start building your schedule.
      </CardContent>
    </Card>
  );
}
