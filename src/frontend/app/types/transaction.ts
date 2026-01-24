/**
 * Represents a single transaction in an account.
 */
export type Transaction = {
  /** Unique identifier for the transaction */
  transaction_id: string;
  /** ID of the account this transaction belongs to */
  account_id: string;
  /** Transaction amount */
  amount: number;
  /** Transaction date in ISO format */
  date: string;
  /** Name of the transaction */
  name: string;
  /** Merchant name, if available */
  merchant_name: string;
  /** Personal finance category fields */
  category_primary: string;
  category_detailed: string;
  category_confidence_level: string;
  /** Whether the transaction is pending */
  pending: boolean;
  /** ISO currency code (optional) */
  iso_currency_code?: string;
  /** Unofficial currency code (optional) */
  unofficial_currency_code?: string;
};
