"use client";

import { useState } from "react";
import type { Transaction } from "../../types/transaction";

export default function TransactionCard({ transaction }: { transaction: Transaction }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li
      className="p-3 border rounded cursor-pointer hover:bg-gray-50"
      onClick={() => setExpanded((prev) => !prev)}
    >
      <div className="flex justify-between">
        <div>
          <div className="font-medium">{transaction.name}</div>
          <div className="text-sm text-gray-500">
            {transaction.category_primary} | {new Date(transaction.date).toLocaleDateString()}
          </div>
        </div>
        <div className="font-medium">${transaction.amount}</div>
      </div>

      {expanded && (
        <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded">
          <div>Merchant Name: {transaction.merchant_name || "-"}</div>
          <div>Detailed Category: {transaction.category_detailed || "-"}</div>
          <div>Category Confidence: {transaction.category_confidence_level || "-"}</div>
          <div>Transaction ID: {transaction.transaction_id}</div>
          <div>Account ID: {transaction.account_id}</div>
          <div>Pending: {transaction.pending ? "Yes" : "No"}</div>
          <div>ISO Currency: {transaction.iso_currency_code || "-"}</div>
        </div>
      )}
    </li>
  );
}
