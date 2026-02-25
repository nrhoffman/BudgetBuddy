"use client";

import { useState } from "react";
import { useFinancialDataContext } from "@/app/context/FinancialDataContext";

export default function RefreshButton() {
  const { fetchAccounts, fetchInstitutions } = useFinancialDataContext();
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchAccounts(), fetchInstitutions()]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleRefresh}
      disabled={loading}
      className={`px-6 py-3 rounded-lg text-white shadow ${
        loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
      }`}
    >
      {loading ? "Refreshing..." : "Refresh"}
    </button>
  );
}