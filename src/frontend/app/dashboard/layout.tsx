"use client";

import { useEffect, ReactNode } from "react";
import { useFinancialDataContext, FinancialDataProvider } from "../context/FinancialDataContext";
import { useAuthCheck } from "../hooks/useAuthCheck";
import Banner from "../components/banner";
import DashboardSidebar from "../components/dashboard/sidebars/DashboardSidebar";

function DashboardLayoutInner({ children }: { children: ReactNode }) {
  const authChecked = useAuthCheck();
  const { fetchAccounts, fetchInstitutions } = useFinancialDataContext();

  useEffect(() => {
    if (authChecked) {
      fetchAccounts();
      fetchInstitutions();
    }
  }, [authChecked]);

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

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <FinancialDataProvider>
      <DashboardLayoutInner>{children}</DashboardLayoutInner>
    </FinancialDataProvider>
  );
}
