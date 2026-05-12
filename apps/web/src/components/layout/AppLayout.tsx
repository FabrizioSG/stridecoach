import { Activity, CalendarDays, Home, Moon, Settings, Sun } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import { useTheme } from "./ThemeProvider";

const navItems = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/plan", label: "Plan", icon: CalendarDays },
  { to: "/workouts/demo", label: "Workout", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const { session } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-card/90 px-5 py-6 backdrop-blur lg:block">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <p className="font-semibold">StrideCoach</p>
            <p className="text-xs text-muted-foreground">Training OS</p>
          </div>
        </div>
        <nav className="mt-8 grid gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground",
                  isActive && "bg-primary/10 text-primary",
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/85 px-4 backdrop-blur md:px-8">
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-foreground">StrideCoach</p>
            <h1 className="text-lg font-semibold">{pageTitle(location.pathname)}</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle dark mode">
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <div className="hidden text-right text-sm md:block">
              <p className="font-medium">{session?.user.user_metadata.name ?? "Demo Runner"}</p>
              <p className="text-xs text-muted-foreground">Base building</p>
            </div>
          </div>
        </header>

        <main className="w-full px-4 pb-24 pt-5 md:px-6 lg:px-6 lg:pb-8">
          <Outlet />
        </main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t bg-card/95 px-2 py-2 backdrop-blur lg:hidden">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex flex-col items-center gap-1 rounded-md px-2 py-2 text-xs font-medium text-muted-foreground",
                isActive && "bg-primary/10 text-primary",
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

function pageTitle(pathname: string) {
  if (pathname.startsWith("/plan")) return "Training Plan";
  if (pathname.startsWith("/workouts")) return "Workout Details";
  if (pathname.startsWith("/settings")) return "Settings";
  return "Dashboard";
}
