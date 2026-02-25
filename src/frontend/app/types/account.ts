import type { Transaction } from "./transaction";

/**
 * Represents a bank account with transactions.
 */
export type Account = {
  /** Unique account ID */
  id: string;

  /** Account name */
  name: string;

  /** Account type (checking, savings, credit, etc.) */
  type: string;

  /** Account subtype (optional) */
  subtype?: string | null;

  /** Institution Logo */
  logo?: string | null;

  /** Current account balance */
  balance: number;

  /** Available balance (optional) */
  available_balance?: number | null;

  /** Credit limit (optional, for credit accounts) */
  credit_limit?: number | null;

  /** ISO currency code */
  iso_currency_code?: string | null;

  /** Unofficial currency code */
  unofficial_currency_code?: string | null;

  /** Holder category (personal/business) */
  holder_category?: string | null;

  /** Initial balance at import time */
  initial_balance: number;

  /** Timestamp when initial import completed */
  initial_import_completed_at: string;

  /** APR/Interest of the account */
  apr: number | null;

  /** List of transactions for this account */
  transactions: Transaction[];
};
