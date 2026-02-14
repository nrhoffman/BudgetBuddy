"use client";

import { useState } from "react";
import { useAuthCheck } from "../../hooks/useAuthCheck";
import { useRouter } from "next/navigation";

type Step = "idle" | "confirm" | "password" | "final";

export default function DataSettingsPage() {
  const authChecked = useAuthCheck();
  const router = useRouter();

  const [step, setStep] = useState<Step>("idle");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  const resetFlow = () => {
  setStep("idle");
  setPassword("");
  setError("");
  };

  if (!authChecked) return <div>Logging Out</div>;

  // Step 2 — Verify Password With Backend
  const verifyPassword = async () => {
    if (!password) {
      setError("Password is required.");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) return;

    setIsVerifying(true);
    setError("");

    try {
      const res = await fetch(
        "/api/auth/verify-password",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ password }),
        }
      );

      if (!res.ok) {
        setPassword("");
        throw new Error("Invalid password");
      }

      setStep("final");
    } catch {
      setError("Incorrect password. Please try again.");
    } finally {
      setIsVerifying(false);
    }
  };

  // Step 3 — Final Delete
  const deleteAccount = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    setIsDeleting(true);
    setError("");

    try {
      const res = await fetch("/api/user/delete-all", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error("Deletion failed");
      }

      localStorage.removeItem("token");
      setPassword("");
      router.push("/");
    } catch {
      setError("Something went wrong while deleting.");
      setStep("password");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <h1 className="text-5xl font-bold mb-2">Data Settings</h1>
      <p className="text-lg text-gray-600 mb-8">
        Manage your stored financial data and account deletion.
      </p>

      <div className="mt-12 border border-red-200 bg-red-50 p-6 rounded-xl">
        <h2 className="text-xl font-semibold text-red-600 mb-4">
          Danger Zone
        </h2>

        <p className="text-sm text-red-700 mb-6">
          Deleting your account will permanently remove all accounts,
          transactions, and related financial data. This cannot be undone.
        </p>

        {/* Step 0 — Initial Button */}
        {step === "idle" && (
          <button
            onClick={() => setStep("confirm")}
            className="mt-4 inline-flex items-center justify-center
                       bg-red-600 text-white
                       px-6 py-3
                       rounded-lg
                       font-semibold
                       border border-red-700
                       shadow-sm
                       hover:bg-red-700
                       hover:shadow-md
                       active:scale-[0.98]
                       transition-all duration-150"
          >
            Delete Account & All Data
          </button>
        )}

        {/* Step 1 — First Confirmation */}
        {step === "confirm" && (
          <div className="mt-6 p-4 bg-white border border-red-300 rounded-lg">
            <p className="text-sm font-medium text-gray-800 mb-4">
              Are you sure? This action cannot be reversed.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setStep("password")}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Yes, Continue
              </button>

              <button
                onClick={resetFlow}
                className="px-4 py-2 border rounded-md"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Password Verification */}
        {step === "password" && (
          <div className="mt-6 p-4 bg-white border border-red-300 rounded-lg">
            <p className="text-sm text-gray-800 mb-3">
              Enter your password to continue.
            </p>

            <input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError("");
              }}
              className="w-full mb-3 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-red-400"
              placeholder="Your password"
            />

            {error && (
              <p className="text-sm text-red-600 mb-3">{error}</p>
            )}

            <div className="flex gap-3">
              <button
                onClick={verifyPassword}
                disabled={isVerifying}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {isVerifying ? "Verifying..." : "Verify"}
              </button>

              <button
                onClick={resetFlow}
                className="px-4 py-2 border rounded-md"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Step 3 — Final Confirmation */}
        {step === "final" && (
          <div className="mt-6 p-4 bg-white border border-red-400 rounded-lg">
            <p className="text-sm font-semibold text-red-700 mb-4">
              Final confirmation: This will permanently delete everything.
            </p>

            <div className="flex gap-3">
              <button
                onClick={deleteAccount}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-700 text-white rounded-md hover:bg-red-800 disabled:opacity-50"
              >
                {isDeleting ? "Deleting..." : "Permanently Delete"}
              </button>

              <button
                onClick={resetFlow}
                className="px-4 py-2 border rounded-md"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
