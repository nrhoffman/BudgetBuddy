"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Custom React hook that checks if the user is authenticated.
 *
 * This hook will:
 * - Check for a JWT token in `localStorage`.
 * - Call the `/api/auth/check-login` endpoint to verify the token.
 * - Redirect the user to the homepage (`"/"`) if not authenticated.
 * - Return a boolean indicating if authentication has been successfully checked.
 *
 * @returns `true` if the user is authenticated and the check is complete, otherwise `false`.
 *
 * @example
 * const authChecked = useAuthCheck();
 * if (!authChecked) {
 *   return <div>Loading...</div>;
 * }
 */
export function useAuthCheck(): boolean {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    /**
     * Performs authentication check by:
     * 1. Verifying if a token exists in localStorage.
     * 2. Calling the backend endpoint to validate the token.
     * 3. Handling redirection and cleanup on failure.
     */
    const checkAuth = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setAuthChecked(false);
        router.replace("/");
        return;
      }

      try {
        const res = await fetch("/api/auth/check-login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          localStorage.removeItem("token");
          setAuthChecked(false);
          router.replace("/");
        } else {
          setAuthChecked(true);
        }
      } catch (err) {
        console.error("Auth check failed", err);
        localStorage.removeItem("token");
        setAuthChecked(false);
        router.replace("/");
      }
    };

    checkAuth();
  }, [router]);

  return authChecked;
}
