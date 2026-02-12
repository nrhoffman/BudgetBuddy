"use client";

import { useState } from "react";
import type { Account } from "../../types/account";

type Props = {
  accounts: Account[];
  selectedAccount: Account | null;
  onSelectAccount: (account: Account) => void;
  onDeleteAccount: (accountId: string) => void;
  onEditAccount: (accountId: string, newName: string, apr: number | null) => Promise<void>;
  deleting: string | null;
  editing: string | null;
};

export default function AccountsSidebar({
  accounts,
  selectedAccount,
  onSelectAccount,
  onDeleteAccount,
  onEditAccount,
  deleting,
  editing,
}: Props) {
  const [openOptionsId, setOpenOptionsId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editApr, setEditApr] = useState("");

  const startEdit = (account: Account) => {
    setEditingId(account.id);
    setEditName(account.name);
    setEditApr(account.apr?.toString() ?? "");
    setOpenOptionsId(null);
  };

  const saveEdit = async (account: Account) => {
    const trimmedName = editName.trim();
    const parsedApr = editApr === "" ? null : Number(editApr);

    const nameUnchanged = trimmedName === account.name;
    const aprUnchanged = parsedApr === (account.apr ?? null);

    if ((!trimmedName || nameUnchanged) && aprUnchanged) {
      setEditingId(null);
      return;
    }

    await onEditAccount(account.id, trimmedName, parsedApr);

    setEditingId(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName("");
    setEditApr("");
  };

  return (
    <div className="col-span-4 bg-white rounded shadow p-4 relative">
      <h2 className="text-lg font-semibold mb-4">Accounts</h2>

      {accounts.length === 0 ? (
        <p className="text-gray-500">No accounts linked yet.</p>
      ) : (
        <ul className="space-y-2">
          {accounts.map((account) => {
            const isSelected = selectedAccount?.id === account.id;
            const isOptionsOpen = openOptionsId === account.id;

            return (
              <li
                key={account.id}
                className={`flex justify-between items-center p-3 rounded border relative ${isSelected ? "bg-blue-50 border-blue-500" : "hover:bg-gray-50 border-transparent"
                  }`}
              >
                {/* Account Info */}
                <div
                  className="flex-1 cursor-pointer flex justify-between items-center"
                  onClick={() => onSelectAccount(account)}
                >
                  <div className="flex flex-col justify-center">
                    {editingId === account.id ? (
                      <div className="flex flex-col gap-2 w-full">
                        <input
                          autoFocus
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="font-medium text-sm px-1 py-0.5 border rounded w-full"
                        />

                        <input
                          type="number"
                          step="0.01"
                          placeholder="APR %"
                          value={editApr}
                          onChange={(e) => setEditApr(e.target.value)}
                          className="text-xs px-1 py-0.5 border rounded w-24"
                        />

                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => saveEdit(account)}
                            disabled={editing === account.id}
                            className="px-3 py-1 bg-green-500 text-white rounded disabled:bg-gray-300"
                          >
                            {editing === account.id ? "Saving..." : "Save"}
                          </button>

                          <button
                            onClick={cancelEdit}
                            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <span className="font-medium">{account.name}</span>
                    )}
                    {account.apr != null && (
                      <span className="text-xs text-gray-500">
                        Interest: {account.apr}%
                      </span>
                    )}
                    <span className="text-xs text-gray-500">{account.type}</span>
                  </div>
                  <span className="text-sm text-gray-600">{account.balance.toLocaleString()}</span>
                </div>

                {/* Options Menu */}
                <div className="relative flex-shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenOptionsId(isOptionsOpen ? null : account.id);
                    }}
                    className="p-1 rounded hover:bg-gray-200 flex items-center justify-center"
                  >
                    {/* Vertical three dots */}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-gray-600"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M10 3a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zm0 7a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zm0 7a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                    </svg>
                  </button>

                  {isOptionsOpen && (
                    <div
                      className="absolute right-0 mt-1 w-36 bg-white border rounded shadow z-10"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => startEdit(account)}
                        className="w-full text-left px-4 py-2 hover:bg-gray-50"
                      >
                        {editing === account.id ? "Editing..." : "Edit Account"}
                      </button>
                      <button
                        onClick={() => onDeleteAccount(account.id)}
                        className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50"
                      >
                        {deleting === account.id ? "Deleting..." : "Delete Account"}
                      </button>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
