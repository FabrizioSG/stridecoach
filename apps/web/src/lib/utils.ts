import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric" }).format(new Date(value));
}

export function formatKm(value: number | null | undefined) {
  return typeof value === "number" ? `${value.toFixed(value % 1 ? 1 : 0)} km` : "Open";
}
