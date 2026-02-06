"use client";

import { ReactNode } from "react";
import Banner from "../components/banner";
import DashboardSidebar from "../components/dashboard/DashboardSidebar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Banner />

      <div className="flex">
        <DashboardSidebar />
        <main className="flex-1 p-8">{children}</main>
      </div>
    </div>
  );
}
