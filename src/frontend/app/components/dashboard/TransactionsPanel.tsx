"use client";

import TransactionCard from "./TransactionsCard";
import type { Account } from "../../types/account";
import type { Transaction } from "../../types/transaction";

type Props = {
  account: Account | null;
};

export default function TransactionsPanel({ account }: Props) {
  if (!account) {
    return (
      <div className="col-span-8 bg-white rounded shadow p-6 flex items-center justify-center">
        <p className="text-gray-500 text-center">Select an account to view transactions</p>
      </div>
    );
  }

  return (
    <div className="col-span-8 bg-white rounded shadow p-6">
      <h2 className="text-xl font-semibold mb-2">{account.name}</h2>
      <p className="text-gray-600 mb-4">Balance: ${account.balance}</p>

      {account.transactions.length === 0 ? (
        <p className="text-gray-500 italic">No transactions available.</p>
      ) : (
        <ul className="space-y-2">
          {account.transactions.map((tx, idx) => (
            <TransactionCard key={`${tx.transaction_id}-${idx}`} transaction={tx} />
          ))}
        </ul>
      )}
    </div>
  );
}
