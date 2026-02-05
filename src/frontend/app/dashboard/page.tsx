"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

import AccountsSidebar from "../components/dashboard/AccountsSidebar";
import Banner from "../components/banner";
import DashboardSidebar from "../components/dashboard/DashboardSidebar";
import TransactionsPanel from "../components/dashboard/TransactionsPanel";

import { useAccounts } from "../hooks/useAccounts";
import { useAuthCheck } from "../hooks/useAuthCheck";

const PlaidLinkButton = dynamic(
  () => import("../components/dashboard/PlaidLinkButton"),
  { ssr: false }
);

export default function DashboardPage() {
  const authChecked = useAuthCheck();
  const [activeMenu, setActiveMenu] = useState("home");
  const {
    accounts,
    loading: accountsLoading,
    fetchAccounts,
    deleteAccount,
    editAccount,
    deleting,
    editingAccount,
  } = useAccounts();

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
      {/* Banner */}
      <Banner />

      <div className="flex">
        {/* Sidebar */}
        <DashboardSidebar activeMenu={activeMenu} onSelectMenu={setActiveMenu} />

        {/* Main Content */}
        <main className="flex-1 p-8">
          {/* Home page */}
          {activeMenu === "home" && (
            <div className="flex flex-col items-center justify-center mt-8">
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
            </div>
          )}

          {/* Banking page */}
          {activeMenu === "banking" && (
            <div className="mt-8 w-full max-w-6xl mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-5xl font-bold text-gray-800 mb-2">Banking</h1>
                <p className="text-lg text-gray-600">
                  Keep on top of your banking
                </p>
              </div>

              <div className="grid grid-cols-12 gap-6">
                <AccountsSidebar
                  accounts={accounts.filter(
                    (account) => account.type === "depository"
                  )}
                  selectedAccount={selectedAccount}
                  onSelectAccount={setSelectedAccount}
                  onDeleteAccount={deleteAccount}
                  onEditAccount={editAccount}
                  deleting={deleting}
                  editing={editingAccount}
                />
                <TransactionsPanel account={selectedAccount} />
              </div>
            </div>
          )}

          {/* Credit page */}
          {activeMenu === "credit" && (
            <div className="mt-8 w-full max-w-6xl mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-5xl font-bold text-gray-800 mb-2">Credit</h1>
                <p className="text-lg text-gray-600">
                  Keep on top of your credit cards
                </p>
              </div>

              <div className="grid grid-cols-12 gap-6">
                <AccountsSidebar
                  accounts={accounts.filter(
                    (account) => account.type === "credit"
                  )}
                  selectedAccount={selectedAccount}
                  onSelectAccount={setSelectedAccount}
                  onDeleteAccount={deleteAccount}
                  onEditAccount={editAccount}
                  deleting={deleting}
                  editing={editingAccount}
                />
                <TransactionsPanel account={selectedAccount} />
              </div>
            </div>
          )}

          {/* Loans page */}
          {activeMenu === "loans" && (
            <div className="mt-8 w-full max-w-6xl mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-5xl font-bold text-gray-800 mb-2">Loans</h1>
                <p className="text-lg text-gray-600">
                  Keep on top of your loans
                </p>
              </div>

              <div className="grid grid-cols-12 gap-6">
                <AccountsSidebar
                  accounts={accounts.filter(
                    (account) => account.type === "loan"
                  )}
                  selectedAccount={selectedAccount}
                  onSelectAccount={setSelectedAccount}
                  onDeleteAccount={deleteAccount}
                  onEditAccount={editAccount}
                  deleting={deleting}
                  editing={editingAccount}
                />
                <TransactionsPanel account={selectedAccount} />
              </div>
            </div>
          )}

          {/* Investing page */}
          {activeMenu === "investing" && (
            <div className="mt-8 w-full max-w-6xl mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-5xl font-bold text-gray-800 mb-2">Investing</h1>
                <p className="text-lg text-gray-600">
                  Keep on top of your investments
                </p>
              </div>

              <div className="grid grid-cols-12 gap-6">
                  <AccountsSidebar
                    accounts={accounts.filter(
                      (account) => account.type === "investment"
                    )}
                    selectedAccount={selectedAccount}
                    onSelectAccount={setSelectedAccount}
                    onDeleteAccount={deleteAccount}
                    onEditAccount={editAccount}
                    deleting={deleting}
                    editing={editingAccount}
                  />
                <TransactionsPanel account={selectedAccount} />
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
