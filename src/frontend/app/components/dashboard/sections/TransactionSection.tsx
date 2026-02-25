"use client";

import { useState } from "react";
import AccountsSidebar from "../sidebars/AccountsSidebar";
import TransactionsPanel from "../TransactionsPanel";
import { useFinancialDataContext } from "../../../context/FinancialDataContext";
import { Account } from "@/app/types/account";

interface Props {
  accountType: string;
}

export default function AccountTransactionsSection({ accountType }: Props) {
  const {
    accounts,
    deleteAccount,
    editAccount,
    deleting,
    editingAccount,
  } = useFinancialDataContext();

  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const filteredAccounts = accounts.filter(
    (a) => a.type === accountType
  );

  return (
    <div className="grid grid-cols-12 gap-6">
      <AccountsSidebar
        accounts={filteredAccounts}
        selectedAccount={selectedAccount}
        onSelectAccount={setSelectedAccount}
        onDeleteAccount={deleteAccount}
        onEditAccount={editAccount}
        deleting={typeof deleting === "string" ? deleting : ""}
        editing={editingAccount}
      />
      <TransactionsPanel
        account={selectedAccount}
        allAccounts={accounts}
      />
    </div>
  );
}