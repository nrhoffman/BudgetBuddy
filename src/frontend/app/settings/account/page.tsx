"use client";

import { useAuthCheck } from "../../hooks/useAuthCheck";

export default function AccountSettingsPage() {
  const authChecked = useAuthCheck();

  if (!authChecked) return <div>Logging Out</div>;

  return (
    <>
      <h1 className="text-5xl font-bold mb-2">Settings</h1>
      <p className="text-lg text-gray-600 mb-8">Account Settings</p>
    </>
  );
}
