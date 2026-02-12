import type { Transaction } from "./transaction";

/**
 * Represents a bank account with transactions.
 */
export type Account = {
  /** Unique account ID */
  id: string;
  /** Account name */
  name: string;
  /** Account type (checking, savings, etc.) */
  type: string;
  /** Current account balance */
  balance: number;
  /** List of transactions for this account */
  transactions: Transaction[];
  /** APR/Interest of the account */
  apr: number | null;
};
