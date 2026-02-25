"use client";

import TransactionCard from "./TransactionsCard";
import type { Transaction } from "../../types/transaction";
import type { Account } from "../../types/account";

type Props = {
  account: Account | null;
  allAccounts?: Account[];
};

export default function TransactionsPanel({ account, allAccounts }: Props) {
  let transactions: (Transaction & { accountName?: string })[] = [];

  if (account) {
    transactions = account.transactions;
  } else if (allAccounts) {
    transactions = allAccounts.flatMap((acc) =>
      acc.transactions.map((tx) => ({
        ...tx,
        accountId: acc.id,
        accountName: acc.name,
      }))
    );
  }

  const sortedTransactions = [...transactions].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  if (sortedTransactions.length === 0) {
    return (
      <div className="col-span-8 bg-white rounded shadow p-6 flex items-center justify-center">
        <p className="text-gray-500 text-center">No transactions available.</p>
      </div>
    );
  }

  return (
    <div className="col-span-8 bg-white rounded shadow p-6">
      {/* Header */}
      {account ? (
        <>
          <h2 className="text-xl font-semibold mb-4">{account.name}</h2>
          <p className="text-gray-600 mb-4">Balance: ${account.balance}</p>
        </>
      ) : (
        <h2 className="text-xl font-semibold mb-4">All Transactions</h2>
      )}

      {/* Transactions List */}
      <ul className="space-y-2">
        {sortedTransactions.map((tx) => (
          <TransactionCard
            key={`${tx.id}-${tx.account_id}`}
            transaction={tx}
            accountId={tx.account_id}
            accountName={tx.accountName}
          />
        ))}
      </ul>
    </div>
  );
}