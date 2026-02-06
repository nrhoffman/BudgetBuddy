import { useState, useEffect, useCallback} from "react";

export interface Institution {
  institution_id: string;
  institution_name: string;
}

export function useInstitutions() {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInstitutions = async () => {
      const token = localStorage.getItem("token");
      if (!token) return setLoading(false);

      try {
        const res = await fetch("/api/accounts/get-institutions", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;

        const data: Institution[] = await res.json();
        setInstitutions(data);
      } catch (err) {
        console.error("Failed to fetch institutions", err);
      } finally {
        setLoading(false);
      }
    };

    fetchInstitutions();
  }, []);

    const getAccountsForInstitution = useCallback(
    async (institution_id: string) => {
      const token = localStorage.getItem("token");
      if (!token) return null;

      try {
        const res = await fetch(`/api/bank/get-accounts?institution_id=${institution_id}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          throw new Error("Failed to fetch accounts");
        }

        return await res.json();
      } catch (err) {
        console.error("Failed to fetch accounts", err);
        return null;
      }
    },
    []);

  return { institutions, loading, getAccountsForInstitution };
}
