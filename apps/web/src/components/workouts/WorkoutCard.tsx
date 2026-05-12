import type { Workout } from "@stridecoach/shared-types";
import { Calendar, CheckCircle2, Clock, Gauge } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatDate, formatKm } from "@/lib/utils";
import { StatusBadge } from "./StatusBadge";

interface WorkoutCardProps {
  workout: Workout;
  onComplete?: (workout: Workout) => void;
}

export function WorkoutCard({ workout, onComplete }: WorkoutCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold">{workout.title}</h3>
              <StatusBadge status={workout.status} />
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{workout.description}</p>
          </div>
          {onComplete && workout.status !== "completed" ? (
            <Button size="sm" variant="outline" onClick={() => onComplete(workout)}>
              <CheckCircle2 className="h-4 w-4" />
              Complete
            </Button>
          ) : null}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-muted-foreground sm:grid-cols-4">
          <span className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            {formatDate(workout.scheduledDate)}
          </span>
          <span className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-primary" />
            {formatKm(workout.plannedDistanceKm)}
          </span>
          <span className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            {workout.plannedDurationMin ?? "--"} min
          </span>
          <span>{workout.plannedHrZone ?? "Open effort"}</span>
        </div>

        <Button asChild variant="ghost" className="mt-3 px-0 text-primary hover:bg-transparent">
          <Link to={`/workouts/${workout.id}`}>View workout</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
