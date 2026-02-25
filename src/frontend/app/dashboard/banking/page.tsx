"use client";

import { useState } from "react";
import TransactionSection from "../../components/dashboard/sections/TransactionSection";
import InsightsSection from "../../components/dashboard/sections/InsightsSection";
import { useFinancialDataContext } from "../../context/FinancialDataContext";
import RefreshButton from "../../components/dashboard/buttons/RefreshButton";
import { useAuthCheck } from "../../hooks/useAuthCheck";

export default function BankingPage() {
  const authChecked = useAuthCheck();
  const [activeTab, setActiveTab] = useState<"transactions" | "insights">(
    "transactions"
  );
  const { accountsLoading } = useFinancialDataContext();

  if (!authChecked || accountsLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen w-full px-12 py-10">
      <div className="flex flex-col items-center text-center mb-10">
        <h1 className="text-5xl font-bold mb-2">Banking</h1>
        <p className="text-lg text-gray-600 mb-8">
          Keep on top of your banking
        </p>
        <RefreshButton />
      </div>

      <div className="border-b mb-8 flex gap-8 justify-center">
        <button
          onClick={() => setActiveTab("transactions")}
          className={`pb-3 text-lg transition border-b-2 ${
            activeTab === "transactions"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          Transactions
        </button>

        <button
          onClick={() => setActiveTab("insights")}
          className={`pb-3 text-lg transition border-b-2 ${
            activeTab === "insights"
              ? "border-blue-600 text-blue-600 font-semibold"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          Insights
        </button>
      </div>

      <div>
        {activeTab === "transactions" && (
          <TransactionSection accountType="depository" />
        )}

        {activeTab === "insights" && (
          <InsightsSection accountType="depository" />
        )}
      </div>
    </div>
  );
}
