import type { DashboardSummary, TrainingPlan, Workout } from "@stridecoach/shared-types";

import { supabase } from "./supabase";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface StravaActivityCandidate {
  id: string;
  stravaActivityId: number;
  name: string;
  sportType: string | null;
  startDate: string | null;
  distanceKm: number | null;
  durationMin: number | null;
  averageHr: number | null;
  averageCadence: number | null;
  averagePace: string | null;
  score: number | null;
}

async function getAccessToken() {
  const session = await supabase?.auth.getSession();
  return session?.data.session?.access_token;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function upload<T>(path: string, formData: FormData): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`API upload failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getDashboard: () => request<DashboardSummary>("/plans/dashboard"),
  getActivePlan: () => request<TrainingPlan>("/plans/active"),
  getStravaStatus: () =>
    request<{
      connected: boolean;
      athleteId?: number;
      athleteName?: string | null;
      scope?: string | null;
      connectedAt?: string | null;
    }>("/strava/status"),
  connectStrava: () => request<{ authorizationUrl: string }>("/strava/connect"),
  syncStrava: () =>
    request<{ activities: Array<{ id: number; name: string }> }>("/strava/sync", { method: "POST" }),
  getStravaCandidates: (workoutId: string) =>
    request<{ activities: StravaActivityCandidate[] }>(`/strava/workouts/${workoutId}/candidates`),
  linkStravaActivity: (workoutId: string, activityId: string) =>
    request<Workout>(`/strava/workouts/${workoutId}/link`, {
      method: "POST",
      body: JSON.stringify({ activity_id: activityId }),
    }),
  unlinkStravaActivity: (workoutId: string) =>
    request<Workout>(`/strava/workouts/${workoutId}/link`, {
      method: "DELETE",
    }),
  analyzeWorkout: (workoutId: string, regenerate = false) =>
    request<{ analysis: string; analysisLength?: number }>(`/ai/workouts/${workoutId}/analysis?regenerate=${regenerate}`, {
      method: "POST",
    }),
  importTrainingPlan: (file: File, replaceExisting = false) => {
    const formData = new FormData();
    formData.append("file", file);
    return upload<TrainingPlan>(`/imports/training-plan?replace_existing=${replaceExisting}`, formData);
  },
  deletePlan: (planId: string) => request<void>(`/plans/${planId}`, { method: "DELETE" }),
  updateWorkout: (workoutId: string, payload: Partial<Workout>) =>
    request<Workout>(`/plans/workouts/${workoutId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};
