"use client";

import { usePlaid } from "../../../hooks/usePlaid";

type PlaidSyncButtonProps = {
  institutionId: string;
  institutionName: string;
  onSuccess?: () => Promise<void> | void;
};

export default function PlaidSyncButton({
  institutionId,
  institutionName,
  onSuccess,
}: PlaidSyncButtonProps) {
  const { openUpdatePlaid, ready, isOpening } = usePlaid({ onSuccess });

  return (
    <button
      disabled={!ready}
      onClick={() => openUpdatePlaid(institutionId)}
      className="px-6 py-3 bg-green-500 text-white rounded-lg shadow hover:bg-green-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isOpening ? "Syncing..." : "Sync Accounts"}
    </button>
  );
}
