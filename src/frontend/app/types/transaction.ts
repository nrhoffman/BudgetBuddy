/**
 * Represents a single transaction in an account.
 */
export type Transaction = {
  /** Unique identifier for the transaction */
  id: string;

  /** ID of the account this transaction belongs to */
  account_id: string;

  /** Type of the account this transaction belongs to */
  account_type: string;

  /** Transaction amount */
  amount: number;

  /** Balance after transaction (optional) */
  balance_after?: number | null;

  /** Transaction date in ISO format */
  date: string;

  /** Authorized date (optional) */
  authorized_date?: string | null;

  /** Authorized datetime (optional) */
  authorized_datetime?: string | null;

  /** Name of the transaction */
  name: string;

  /** Merchant details (optional) */
  merchant_name?: string | null;
  merchant_entity_id?: string | null;
  merchant_website?: string | null;
  merchant_logo_url?: string | null;
  merchant_confidence_level?: string | null;

  /** Category info */
  category_primary?: string | null;
  category_detailed?: string | null;
  category_confidence_level?: string | null;
  plaid_category_version?: string | null;

  /** Payment metadata */
  payment_channel?: string | null;
  transaction_type?: string | null;
  transaction_code?: string | null;

  /** Location metadata */
  location_city?: string | null;
  location_region?: string | null;
  location_country?: string | null;
  location_lat?: number | null;
  location_lon?: number | null;
  store_number?: string | null;

  /** Classification flags */
  is_ach?: boolean;
  is_transfer?: boolean;
  is_internal_transfer?: boolean;
  is_recurring?: boolean;

  /** Whether the transaction is pending */
  pending: boolean;

  /** Currency fields */
  iso_currency_code?: string | null;
  unofficial_currency_code?: string | null;

  /** Direction of the transaction (in/out) */
  direction: "in" | "out";
};
