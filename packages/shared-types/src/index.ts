export type WorkoutStatus = "planned" | "completed" | "missed";

export interface User {
  id: string;
  email: string | null;
  displayName: string | null;
  avatarUrl: string | null;
}

export interface Workout {
  id: string;
  title: string;
  description: string | null;
  plannedDistanceKm: number | null;
  plannedDurationMin: number | null;
  plannedPace: string | null;
  plannedHrZone: string | null;
  scheduledDate: string;
  status: WorkoutStatus;
  actualDistanceKm: number | null;
  actualDurationMin: number | null;
  actualAvgHr: number | null;
  actualAvgCadence: number | null;
  actualAvgPace: string | null;
  notes: string | null;
  aiAnalysis: string | null;
  aiAnalysisGeneratedAt: string | null;
}

export interface TrainingWeek {
  id: string;
  weekNumber: number;
  startsOn: string;
  focus: string | null;
  workouts: Workout[];
}

export interface TrainingPlan {
  id: string;
  title: string;
  description: string | null;
  goalRace: string | null;
  startsOn: string;
  weeks: TrainingWeek[];
}

export interface DashboardSummary {
  weeklyMileageKm: number;
  weeklyCompletedMileageKm: number;
  weeklyPlannedMileageKm: number;
  upcomingWorkout: Workout | null;
  recentWorkouts: Workout[];
  consistency: Array<{
    week: string;
    completed: number;
    planned: number;
  }>;
  aiInsight: string;
}
