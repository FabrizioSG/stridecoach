import type { WorkoutStatus } from "@stridecoach/shared-types";

import { Badge } from "@/components/ui/badge";

const labels: Record<WorkoutStatus, string> = {
  planned: "Planned",
  completed: "Completed",
  missed: "Missed",
};

export function StatusBadge({ status }: { status: WorkoutStatus }) {
  return <Badge variant={status}>{labels[status]}</Badge>;
}
