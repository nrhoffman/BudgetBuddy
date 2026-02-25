"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useAccounts as useAccountsHook } from "../hooks/useAccounts";
import { useInstitutions as useInstitutionsHook } from "../hooks/useInstitutions";

interface FinancialDataContextType {
  accounts: ReturnType<typeof useAccountsHook>["accounts"];
  accountsLoading: boolean;
  fetchAccounts: () => Promise<void>;
  deleteAccount: ReturnType<typeof useAccountsHook>["deleteAccount"];
  editAccount: ReturnType<typeof useAccountsHook>["editAccount"];
  deleting: string | null;
  editingAccount: any;

  editTransaction: (
    accountId: string,
    transactionId: string,
    primary: string,
    detailed: string
  ) => Promise<void>;
  editingTransaction: string | null;

  institutions: ReturnType<typeof useInstitutionsHook>["institutions"];
  institutionsLoading: boolean;
  fetchInstitutions: () => Promise<void>;
  getAccountsForInstitution: ReturnType<typeof useInstitutionsHook>["getAccountsForInstitution"];
}

const FinancialDataContext = createContext<FinancialDataContextType | null>(null);

export function FinancialDataProvider({ children }: { children: React.ReactNode }) {
  const accountsHook = useAccountsHook();
  const institutionsHook = useInstitutionsHook();

  const [accountsLoading, setAccountsLoading] = useState(false);
  const [institutionsLoading, setInstitutionsLoading] = useState(false);

  const fetchAccounts = useCallback(async () => {
    setAccountsLoading(true);
    const fresh = await accountsHook.fetchAccounts();
    localStorage.setItem("accounts_cache", JSON.stringify(fresh));
    setAccountsLoading(false);
  }, [accountsHook]);

  const fetchInstitutions = useCallback(async () => {
    setInstitutionsLoading(true);
    const fresh = await institutionsHook.fetchInstitutions();
    localStorage.setItem("institutions_cache", JSON.stringify(fresh));
    setInstitutionsLoading(false);
  }, [institutionsHook]);

  useEffect(() => {
    const cachedAccounts = localStorage.getItem("accounts_cache");
    const cachedInstitutions = localStorage.getItem("institutions_cache");

    if (cachedAccounts && cachedAccounts !== "undefined")  {
      accountsHook.setAccounts(JSON.parse(cachedAccounts));
    }

    if (cachedInstitutions && cachedInstitutions !== "undefined") {
      institutionsHook.setInstitutions(JSON.parse(cachedInstitutions));
    }

    if (!cachedAccounts || cachedAccounts === "undefined") fetchAccounts();
    if (!cachedInstitutions || cachedInstitutions === "undefined") fetchInstitutions();
  }, []);

  return (
    <FinancialDataContext.Provider
      value={{
        accounts: accountsHook.accounts,
        accountsLoading,
        fetchAccounts,
        deleteAccount: accountsHook.deleteAccount,
        editAccount: accountsHook.editAccount,
        deleting: accountsHook.deleting,
        editingAccount: accountsHook.editingAccount,

        editTransaction: accountsHook.editTransaction,
        editingTransaction: accountsHook.editingTransaction,

        institutions: institutionsHook.institutions,
        institutionsLoading,
        fetchInstitutions,
        getAccountsForInstitution: institutionsHook.getAccountsForInstitution,
      }}
    >
      {children}
    </FinancialDataContext.Provider>
  );
}

export function useFinancialDataContext() {
  const context = useContext(FinancialDataContext);
  if (!context)
    throw new Error("useFinancialDataContext must be used within FinancialDataProvider");
  return context;
}