"use client";

import { useState, useEffect } from "react";
import { usePlaidLink } from "react-plaid-link";

type PlaidLinkButtonProps = {
  onSuccess?: () => Promise<void> | void;
};

let plaidScriptLoaded = false;

function loadPlaidScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (plaidScriptLoaded) return resolve();

    const existing = document.querySelector(
      'script[src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"]'
    );
    if (existing) {
      plaidScriptLoaded = true;
      return resolve();
    }

    const script = document.createElement("script");
    script.src = "https://cdn.plaid.com/link/v2/stable/link-initialize.js";
    script.async = true;
    script.onload = () => {
      plaidScriptLoaded = true;
      resolve();
    };
    script.onerror = () => reject(new Error("Failed to load Plaid script"));
    document.body.appendChild(script);
  });
}

export default function PlaidLinkButton({ onSuccess }: PlaidLinkButtonProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    async function createLinkToken() {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/bank/create-link-token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        console.error("Failed to get link token", await res.text());
        return;
      }

      const data = await res.json();
      setLinkToken(data.link_token);
    }

    createLinkToken();
  }, []);

  useEffect(() => {
    loadPlaidScript()
      .then(() => setReady(true))
      .catch(console.error);
  }, []);

  const { open } = usePlaidLink({
    token: linkToken || "",
    onSuccess: async (public_token: string) => {
      const res = await fetch("/api/bank/exchange-token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ public_token }),
      });

      if (res.ok) {
        alert("Bank account linked!");
        if (onSuccess) await onSuccess();
      } else {
        const errorText = await res.text();
        alert(`Failed to link bank account: ${errorText}`);
      }
    },
  });

  return (
    <button
      disabled={!ready || !linkToken}
      onClick={() => open()}
      className="px-6 py-3 bg-green-500 text-white rounded-lg shadow hover:bg-green-600 transition"
    >
      Connect Bank Account
    </button>
  );
}
