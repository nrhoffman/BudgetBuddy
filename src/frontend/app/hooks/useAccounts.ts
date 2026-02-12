import { useState, useCallback } from "react";
import type { Account } from "../types/account";

export function useAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [editingAccount, setEditingAccount] = useState<string | null>(null);
  const [editingTransaction, setEditingTransaction] = useState<string | null>(null);

  const fetchAccounts = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) return;

    try {
      const res = await fetch("/api/accounts/get-accounts", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const data = await res.json();
        setAccounts(data.accounts);
      }
    } catch (err) {
      console.error("Error fetching accounts:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteAccount = async (accountId: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    if (!confirm("Are you sure you want to delete this account?")) return;

    try {
      setDeleting(accountId);
      const res = await fetch(`/api/accounts/remove-account/${accountId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        setAccounts(prev => prev.filter(acc => acc.id !== accountId));
      } else {
        const data = await res.json();
        alert(`Failed to delete account: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Error deleting account:", err);
      alert("Error deleting account");
    } finally {
      setDeleting(null);
    }
  };

  const editAccount = async (accountId: string, newName: string, apr: number | null) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      setEditingAccount(accountId);
      const res = await fetch(
        `/api/accounts/update-account/${accountId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            account_name: newName,
            apr: apr,
          }),
        }
      );

      if (res.ok) {
        setAccounts(prev =>
          prev.map(acc => (acc.id === accountId ? { ...acc, name: newName, apr: apr } : acc))
        );
      } else {
        const data = await res.json();
        alert(`Failed to update account: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Error updating account:", err);
      alert("Error updating account");
    } finally {
      setEditingAccount(null);
    }
  };

  /**
   * Updates a transaction's categories.
   *
   * @param accountId - ID of the account containing the transaction
   * @param transactionId - ID of the transaction to update
   * @param categoryPrimary - New primary category (uppercase, e.g., INCOME)
   * @param categoryDetailed - New detailed category (uppercase, e.g., INCOME_DIVIDENDS)
   */
  const editTransaction = async (
    accountId: string,
    transactionId: string,
    categoryPrimary: string,
    categoryDetailed: string
  ) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      setEditingTransaction(transactionId);
      const res = await fetch(
        `/api/accounts/${accountId}/transactions/${transactionId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            category_primary: categoryPrimary,
            category_detailed: categoryDetailed,
          }),
        }
      );

      if (res.ok) {
        // Update local state
        setAccounts(prev =>
          prev.map(acc => {
            if (acc.id !== accountId) return acc;
            return {
              ...acc,
              transactions: acc.transactions.map(tx =>
                tx.id === transactionId
                  ? { ...tx, category_primary: categoryPrimary, category_detailed: categoryDetailed }
                  : tx
              ),
            };
          })
        );
      } else {
        const data = await res.json();
        alert(`Failed to update transaction: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Error updating transaction:", err);
      alert("Error updating transaction");
    } finally {
      setEditingTransaction(null);
    }
  };

  return {
    accounts,
    loading,
    fetchAccounts,
    deleteAccount,
    editAccount,
    editTransaction,
    deleting,
    editingAccount,
    editingTransaction,
  };
}
