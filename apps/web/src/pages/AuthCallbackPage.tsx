import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { supabase } from "@/lib/supabase";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function completeSignIn() {
      if (!supabase) {
        setError("Supabase is not configured. Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
        return;
      }

      const authError = searchParams.get("error_description") ?? searchParams.get("error");
      if (authError) {
        setError(authError);
        return;
      }

      const code = searchParams.get("code");
      if (code) {
        const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
        if (exchangeError) {
          setError(exchangeError.message);
          return;
        }
      }

      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setError(
          "Supabase did not return a session. Check that the login origin and allowed redirect URL match exactly.",
        );
        return;
      }

      navigate("/", { replace: true });
    }

    completeSignIn();
  }, [navigate, searchParams]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-sm text-destructive">{error}</CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
      Completing sign in...
    </div>
  );
}
