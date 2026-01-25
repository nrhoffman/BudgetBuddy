import { useState, useCallback } from "react";
import type { Account } from "../types/account";

export function useAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);

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
        setAccounts(prev =>
          prev.filter(acc => acc.id !== accountId)
        );
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

  /**
   * Updates an account's name.
   *
   * @param accountId - ID of the account to update
   * @param newName - New name for the account
   */
  const editAccount = async (accountId: string, newName: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      setEditing(accountId);
      const res = await fetch(
        `/api/accounts/update-account/${accountId}/${encodeURIComponent(newName)}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (res.ok) {
        setAccounts(prev =>
          prev.map(acc =>
            acc.id === accountId
              ? { ...acc, name: newName }
              : acc
          )
        );
      } else {
        const data = await res.json();
        alert(`Failed to update account: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Error updating account:", err);
      alert("Error updating account");
    } finally {
      setEditing(null);
    }
  };

  return {
    accounts,
    loading,
    fetchAccounts,
    deleteAccount,
    editAccount,
    deleting,
    editing,
  };
}
