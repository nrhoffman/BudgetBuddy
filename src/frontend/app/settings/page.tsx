"use client";

import { redirect } from "next/navigation";
import { useAuthCheck } from "../hooks/useAuthCheck";

export default function SettingsPage() {
    const authChecked = useAuthCheck();

    if (!authChecked) {
        return <div>Logging Out...</div>;
    }
    redirect("/settings/account");
}
