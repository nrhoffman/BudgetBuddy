"use client";

import { useEffect, useState, useCallback } from "react";
import { usePlaidLink } from "react-plaid-link";

type UsePlaidOptions = {
  onSuccess?: () => Promise<void> | void;
};

export function usePlaid({ onSuccess }: UsePlaidOptions = {}) {
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [isOpening, setIsOpening] = useState(false);
  const [shouldOpen, setShouldOpen] = useState(false);
  const [pendingInstitution, setPendingInstitution] = useState<string | null>(null);

  const createLinkToken = useCallback(async () => {
    const token = localStorage.getItem("token");
    const res = await fetch("/api/bank/create-link-token", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    const data = await res.json();
    setLinkToken(data.link_token);
    return data.link_token;
  }, []);

  const createUpdateLinkToken = useCallback(async (institution_id: string) => {
    const token = localStorage.getItem("token");
    const res = await fetch(`/api/bank/create-update-link-token?institution_id=${institution_id}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      console.error("Failed to get update link token", await res.text());
      return null;
    }
    const data = await res.json();
    setLinkToken(data.link_token);
    return data.link_token;
  }, []);

  const { open, ready: plaidReady } = usePlaidLink({
    token: linkToken ?? "",
    onSuccess: async (public_token: string, metadata) => {
      try {
        if (pendingInstitution) {
          await fetch(
            `/api/bank/sync-institution-accounts?institution_id=${pendingInstitution}`,
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${localStorage.getItem("token")}`,
              },
            }
          );
          setPendingInstitution(null);
        } else {
          await fetch("/api/bank/exchange-token", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
            body: JSON.stringify({
              public_token,
              institution_id: metadata.institution?.institution_id,
              institution_name: metadata.institution?.name,
            }),
          });
        }

        if (onSuccess) await onSuccess();
      } finally {
        setLinkToken(null);
        setIsOpening(false);
      }
    },
    onExit: async () => {
      if (pendingInstitution) {
        await fetch(`/api/bank/undelete-institution-accounts`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ institution_id: pendingInstitution }),
        });
        setPendingInstitution(null);
      }
      setIsOpening(false);
    },
  });

  useEffect(() => {
    if (shouldOpen && linkToken && plaidReady) {
      open();
      setShouldOpen(false);
    }
  }, [shouldOpen, linkToken, plaidReady, open]);

  return {
    openPlaid: async () => {
      if (isOpening) return;
      setIsOpening(true);

      if (!linkToken) {
        const token = await createLinkToken();
        if (!token) {
          setIsOpening(false);
          return;
        }
      }

      setPendingInstitution(null);
      setShouldOpen(true);
    },

    openUpdatePlaid: async (institution_id: string) => {
      if (isOpening) return;
      setIsOpening(true);

      const token = await createUpdateLinkToken(institution_id);
      if (!token) {
        setIsOpening(false);
        return;
      }

      setPendingInstitution(institution_id);
      setShouldOpen(true);
    },

    ready: !isOpening,
    isOpening,
  };
}