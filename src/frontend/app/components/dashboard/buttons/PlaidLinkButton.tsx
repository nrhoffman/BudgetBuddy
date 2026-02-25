"use client";

import { usePlaid } from "../../../hooks/usePlaid";

type PlaidLinkButtonProps = {
  onSuccess?: () => Promise<void> | void;
};

export default function PlaidLinkButton({ onSuccess }: PlaidLinkButtonProps) {
  const { openPlaid, ready, isOpening } = usePlaid({ onSuccess });

  return (
    <button
      disabled={!ready}
      onClick={openPlaid}
      className="px-6 py-3 bg-green-500 text-white rounded-lg shadow hover:bg-green-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isOpening ? "Opening..." : "Connect Institution"}
    </button>
  );
}