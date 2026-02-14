"use client";

import { ReactNode } from "react";
import SettingsSidebar from "../components/settings/SettingsSidebar";
import Banner from "../components/banner";

export default function SettingsLayout({ children }: { children: ReactNode }) {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Banner />

            <div className="flex flex-1">
                <SettingsSidebar />

                <main className="flex-1 p-8 bg-gray-50 text-gray-900">
                    {children}
                </main>
            </div>
        </div>
    );
}
