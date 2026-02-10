import { useState } from "react";
import type { Transaction } from "../../types/transaction";
import { TRANSACTION_CATEGORY_KEYS, TRANSACTION_CATEGORY_MAP } from "../../types/transactionTypes";
import { useAccounts } from "../../hooks/useAccounts";

type Props = {
  transaction: Transaction;
  accountId: string;
};

export default function TransactionCard({ transaction, accountId }: Props) {
  const { editTransaction, editingTransaction } = useAccounts();
  const [expanded, setExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [primaryCategory, setPrimaryCategory] = useState(transaction.category_primary || "");
  const [detailedCategory, setDetailedCategory] = useState(transaction.category_detailed || "");
  const [confidenceLevel, setConfidenceLevel] = useState(transaction.category_confidence_level || "");


  const [editPrimary, setEditPrimary] = useState(primaryCategory);
  const [editDetailed, setEditDetailed] = useState(detailedCategory);

  const showLowConfidenceFlag = confidenceLevel === "LOW";

  const handleSave = async () => {
    if (!editPrimary || !editDetailed) return;

    await editTransaction(
      accountId,
      transaction.id,
      editPrimary.toUpperCase(),
      editDetailed.toUpperCase()
    );

    setPrimaryCategory(editPrimary.toUpperCase());
    setDetailedCategory(editDetailed.toUpperCase());
    setConfidenceLevel("MANUAL"); // confirmed or manually fixed

    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditPrimary(primaryCategory);
    setEditDetailed(detailedCategory);
    setIsEditing(false);
  };

  return (
    <li className="p-3 border rounded relative">
      {!isEditing ? (
        <div className="flex justify-between items-center">
          <div onClick={() => setExpanded((prev) => !prev)} className="flex-1 cursor-pointer relative">
            <div className="font-medium flex items-center gap-1">
              {transaction.name}
            </div>
            <div className="text-sm text-gray-500">
              {primaryCategory} | {new Date(transaction.date).toLocaleDateString()}
            </div>
          </div>
              {showLowConfidenceFlag && (
                <span
                className="text-red-600 font-bold ml-1 text-xl"
                title="Low confidence category! Please confirm or update."
                >
                  ⚠️
              </span>
              )}
          <div className="flex items-center gap-2">
            <div
              className={`font-medium ${
                transaction.direction === "in" ? "text-green-600" : "text-red-600"
              }`}
            >
              ${transaction.amount}
            </div>
            <button
              onClick={() => setIsEditing(true)}
              className="px-2 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            >
              Edit
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <div>
            <label className="block text-sm font-medium">Primary Category</label>
            <select
              className="mt-1 border rounded px-2 py-1 w-full"
              value={editPrimary}
              onChange={(e) => {
                setEditPrimary(e.target.value);
                setEditDetailed("");
              }}
            >
              <option value="">Select Primary Category</option>
              {TRANSACTION_CATEGORY_KEYS.map((key) => (
                <option key={key} value={key.toUpperCase()}>
                  {key.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Detailed Category</label>
            <select
              className="mt-1 border rounded px-2 py-1 w-full"
              value={editDetailed}
              onChange={(e) => setEditDetailed(e.target.value)}
              disabled={!editPrimary}
            >
              <option value="">Select Detailed Category</option>
              {editPrimary &&
                TRANSACTION_CATEGORY_MAP[editPrimary.toUpperCase() as keyof typeof TRANSACTION_CATEGORY_MAP].map(
                  (sub) => (
                    <option key={sub} value={sub}>
                      {sub}
                    </option>
                  )
                )}
            </select>
          </div>
          <div className="flex gap-2 justify-end mt-2">
            <button
              onClick={handleSave}
              disabled={!editPrimary || !editDetailed || editingTransaction === transaction.id}
              className="px-3 py-1 bg-green-500 text-white rounded disabled:bg-gray-300"
            >
              {editingTransaction === transaction.id ? "Saving..." : "Save"}
            </button>
            <button
              onClick={handleCancel}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {!isEditing && expanded && (
        <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded">
          <div>Merchant Name: {transaction.merchant_name || "-"}</div>
          <div>Balance After: {transaction.balance_after || "-"}</div>
          <div>Detailed Category: {detailedCategory || "-"}</div>
          <div>Category Confidence: {confidenceLevel || "-"}</div>
          <div>Pending: {transaction.pending ? "Yes" : "No"}</div>
          <div>ISO Currency: {transaction.iso_currency_code || "-"}</div>
        </div>
      )}
    </li>
  );
}
