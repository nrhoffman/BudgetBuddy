import { useState, useCallback } from "react";
import type { Account } from "../types/account";

/**
 * Custom hook to fetch, manage, and delete user accounts.
 *
 * Provides functionality to:
 * - Fetch all accounts from the backend.
 * - Track loading state while fetching accounts.
 * - Delete a specific account with confirmation.
 * - Track which account is currently being deleted.
 *
 * @returns An object containing:
 * - `accounts`: Array of user accounts (`Account[]`)
 * - `loading`: Boolean indicating if accounts are being fetched
 * - `fetchAccounts`: Function to manually fetch accounts
 * - `deleteAccount`: Function to delete an account by ID
 * - `deleting`: ID of the account currently being deleted (or null)
 *
 * @example
 * const { accounts, loading, fetchAccounts, deleteAccount, deleting } = useFetchAccounts();
 */
export function useFetchAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  /**
   * Fetches accounts from the backend API.
   *
   * - Reads the JWT token from `localStorage`.
   * - Calls `/api/accounts/get-accounts` with the token.
   * - Updates the `accounts` state with the response.
   * - Sets `loading` to false after completion.
   */
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

  /**
   * Deletes an account by its ID.
   *
   * - Prompts the user for confirmation before deletion.
   * - Calls `/api/accounts/remove-account/{accountId}` with DELETE method.
   * - Removes the account from state if successful.
   * - Tracks the currently deleting account via `deleting` state.
   *
   * @param accountId - The ID of the account to delete
   */
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
        setAccounts(accounts.filter(acc => acc.id !== accountId));
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

  return { accounts, loading, fetchAccounts, deleteAccount, deleting };
}
