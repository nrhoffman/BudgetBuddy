"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { useFinancialDataContext } from "../context/FinancialDataContext";
import RefreshButton from "../components/dashboard/buttons/RefreshButton";
import { useAuthCheck } from "../hooks/useAuthCheck";
import { usePlaid } from "../hooks/usePlaid";

const PlaidSyncButton = dynamic(
  () => import("../components/dashboard/buttons/PlaidSyncButton"),
  { ssr: false }
);

const PlaidLinkButton = dynamic(
  () => import("../components/dashboard/buttons/PlaidLinkButton"),
  { ssr: false }
);

export default function DashboardHomePage() {
  const authChecked = useAuthCheck();
  const [syncingInstitutionId, setSyncingInstitutionId] = useState<string | null>(null);
  const {
    accounts,
    accountsLoading,
    fetchAccounts,
    institutions,
    institutionsLoading,
  } = useFinancialDataContext();

  const { openUpdatePlaid, isOpening } = usePlaid({ onSuccess: fetchAccounts });

  if (!authChecked || accountsLoading || institutionsLoading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="min-h-screen w-full px-12 py-10">

      {/* Centered Hero Section */}
      <div className="flex flex-col items-center text-center mb-12">
        <h1 className="text-5xl font-bold mb-6">Dashboard</h1>
        <p className="text-lg text-gray-600 mb-6 max-w-2xl">
          Manage your accounts, transactions, and financial goals.
        </p>

        <div className="flex gap-4">
          <PlaidLinkButton onSuccess={fetchAccounts} />
          <RefreshButton />
        </div>
      </div>

      {/* Left-Aligned Institutions Section */}
      <div className="w-full">
        {institutions.length > 0 ? (
          <div className="overflow-x-auto w-full">
            <table className="min-w-full bg-white border border-gray-200 shadow rounded">
              <thead>
                <tr className="bg-gray-100">
                  <th className="py-3 px-6 text-left font-medium text-gray-700">
                    Institution Name
                  </th>
                  <th className="py-3 px-6 text-right font-medium text-gray-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {institutions.map((inst) => (
                  <tr key={inst.institution_id} className="border-t">
                    <td className="py-3 px-6 text-gray-800 flex items-center gap-3">
                      {inst.institution_logo && (
                        <img
                          src={inst.institution_logo}
                          alt={`${inst.institution_name} logo`}
                          className="w-8 h-8 rounded object-contain"
                        />
                      )}
                      <span>{inst.institution_name}</span>
                    </td>
                    <td className="py-3 px-6 text-right">
                      <PlaidSyncButton
                        institutionId={inst.institution_id}
                        institutionName={inst.institution_name}
                        onSuccess={fetchAccounts}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500">No institutions linked yet.</p>
        )}
      </div>
    </div>
  );
}