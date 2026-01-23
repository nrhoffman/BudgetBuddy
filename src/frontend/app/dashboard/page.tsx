"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

import Banner from "../components/banner";
import AccountsSidebar from "../components/dashboard/AccountsSidebar";
import TransactionsPanel from "../components/dashboard/TransactionsPanel";

import { useFetchAccounts } from "../hooks/useFetchAccounts";
import { useAuthCheck } from "../hooks/useAuthCheck";

const PlaidLinkButton = dynamic(
  () => import("../components/dashboard/PlaidLinkButton"),
  { ssr: false }
);

export default function DashboardPage() {
  const authChecked = useAuthCheck();
  const {
    accounts,
    loading: accountsLoading,
    fetchAccounts,
    deleteAccount,
    deleting,
  } = useFetchAccounts();

  const [selectedAccount, setSelectedAccount] = useState<typeof accounts[number] | null>(null);
  const [linkingAccounts, setLinkingAccounts] = useState(false);

  useEffect(() => {
    if (authChecked) {
      fetchAccounts();
    }
  }, [authChecked, fetchAccounts]);

  if (!authChecked || accountsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading dashboard...
      </div>
    );
  }

  const handleAccountsUpdated = async () => {
    setLinkingAccounts(true);
    await fetchAccounts();
    setLinkingAccounts(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Banner />

      <main className="flex flex-col items-center justify-center px-4 mt-20">
        <h1 className="text-5xl font-bold text-gray-800 mb-6">Dashboard</h1>
        <p className="text-lg text-gray-600 max-w-2xl text-center mb-6">
          Manage your accounts, transactions, and financial goals.
        </p>

        <PlaidLinkButton onSuccess={handleAccountsUpdated} />

        {linkingAccounts && (
          <div className="mt-4 text-center text-blue-600 font-medium">
            Linking accounts...
          </div>
        )}

        <div className="mt-8 w-full max-w-6xl grid grid-cols-12 gap-6">
          <AccountsSidebar
            accounts={accounts}
            selectedAccount={selectedAccount}
            onSelectAccount={setSelectedAccount}
            onDeleteAccount={deleteAccount}
            deleting={deleting}
          />
          <TransactionsPanel account={selectedAccount} />
        </div>
      </main>
    </div>
  );
}
