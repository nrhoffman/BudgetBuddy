"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import { useAccounts } from "../hooks/useAccounts";
import { useAuthCheck } from "../hooks/useAuthCheck";
import { useInstitutions } from "../hooks/useInstitutions";

const PlaidLinkButton = dynamic(
  () => import("../components/dashboard/PlaidLinkButton"),
  { ssr: false }
);

export default function DashboardHomePage() {
  const authChecked = useAuthCheck();
  const { fetchAccounts, loading: accountsLoading } = useAccounts();
  const {
    institutions,
    loading: institutionsLoading,
    getAccountsForInstitution,
  } = useInstitutions();

  useEffect(() => {
    if (authChecked) {
      fetchAccounts();
    }
  }, [authChecked, fetchAccounts]);

  if (!authChecked || accountsLoading || institutionsLoading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="flex flex-col items-center mt-8 w-full max-w-4xl">
      <h1 className="text-5xl font-bold mb-6">Dashboard</h1>
      <p className="text-lg text-gray-600 mb-6">
        Manage your accounts, transactions, and financial goals.
      </p>

      <PlaidLinkButton onSuccess={fetchAccounts} />

      <h2 className="text-2xl font-semibold mt-8 mb-4 w-full flex justify-start">
        Linked Institutions
      </h2>

      {institutions.length > 0 ? (
        <div className="overflow-x-auto w-full">
          <table className="min-w-full bg-white border border-gray-200 shadow rounded">
            <thead>
              <tr className="bg-gray-100">
                <th className="py-3 px-6 text-left font-medium text-gray-700">Institution Name</th>
                <th className="py-3 px-6 text-right font-medium text-gray-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {institutions.map((inst) => (
                <tr key={inst.institution_id} className="border-t">
                  <td className="py-3 px-6 text-gray-800">{inst.institution_name}</td>
                  <td className="py-3 px-6 text-right">
                    <button
                      onClick={async () => {
                        const res = await getAccountsForInstitution(inst.institution_id);
                        if (res) {
                          alert(`Accounts synced for ${inst.institution_name}!`);
                        } else {
                          alert(`Failed to sync accounts for ${inst.institution_name}.`);
                        }
                      }}
                      className="px-4 py-2 text-sm font-medium rounded
                                bg-blue-600 text-white
                                hover:bg-blue-700"
                    >
                      Sync Accounts
                    </button>
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
  );
}
