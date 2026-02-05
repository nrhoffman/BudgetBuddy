"use client";

import { useState } from "react";
import clsx from "clsx";

const menuItems = [
  { key: "home", label: "Home" },
  { key: "banking", label: "Banking" },
  { key: "credit", label: "Credit" },
  { key: "loans", label: "Loans" },
  { key: "investing", label: "Investing" },
  { key: "budget", label: "Budget" },
  { key: "calculators", label: "Calculators" },
];

interface DashboardSidebarProps {
  activeMenu: string;
  onSelectMenu: (menu: string) => void;
}

export default function DashboardSidebar({ activeMenu, onSelectMenu }: DashboardSidebarProps) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen p-4 flex flex-col">
      <h2 className="text-xl font-bold mb-6">Budget Buddy</h2>
      <nav className="flex flex-col gap-2">
        {menuItems.map((item) => (
          <button
            key={item.key}
            onClick={() => onSelectMenu(item.key)}
            className={clsx(
              "text-left px-4 py-2 rounded-md hover:bg-gray-100",
              activeMenu === item.key && "bg-blue-100 font-semibold"
            )}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
