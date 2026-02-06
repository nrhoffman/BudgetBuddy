"use client";

import { useEffect, useState } from "react";
import AccountsSidebar from "../../components/dashboard/AccountsSidebar";
import TransactionsPanel from "../../components/dashboard/TransactionsPanel";
import { useAccounts } from "../../hooks/useAccounts";
import { useAuthCheck } from "../../hooks/useAuthCheck";
import type { Account } from "../../types/account";

export default function BankingPage() {
  const authChecked = useAuthCheck();
  const {
    accounts,
    loading: accountsLoading,
    fetchAccounts,
    deleteAccount,
    editAccount,
    deleting,
    editingAccount,
  } = useAccounts();

  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  useEffect(() => {
    if (authChecked === true) {
      fetchAccounts();
    }
  }, [authChecked, fetchAccounts]);


  if (!authChecked || accountsLoading) return <div>Loading...</div>;
  
  return (
    <>
      <h1 className="text-5xl font-bold mb-2">Credit</h1>
      <p className="text-lg text-gray-600 mb-8">Keep on top of your credit</p>

      <div className="grid grid-cols-12 gap-6">
        <AccountsSidebar
          accounts={accounts.filter(a => a.type === "credit")}
          selectedAccount={selectedAccount}
          onSelectAccount={setSelectedAccount}
          onDeleteAccount={deleteAccount}
          onEditAccount={editAccount}
          deleting={deleting}
          editing={editingAccount}
        />
        <TransactionsPanel account={selectedAccount} />
      </div>
    </>
  );
}
