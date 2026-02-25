"use client";

import { useState, useCallback } from "react";

export interface Institution {
  institution_id: string;
  institution_name: string;
  institution_logo?: string;
}

export function useInstitutions() {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchInstitutions = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) return [];

    setLoading(true);
    try {
      const res = await fetch("/api/accounts/get-institutions", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) throw new Error("Failed to fetch institutions");

      const data: Institution[] = await res.json();
      setInstitutions(data);
      return data;
    } catch (err) {
      console.error("Failed to fetch institutions", err);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    institutions,
    setInstitutions,
    loading,
    fetchInstitutions,
  };
}