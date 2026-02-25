"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function DashboardSidebar() {
  const pathname = usePathname();

  const linkClass = (path: string) => {
    const isHome = path === "/dashboard";
    const isActive = isHome
      ? pathname === "/dashboard"
      : pathname.startsWith(path);

    return `block px-6 py-3 rounded-md text-lg font-medium transition-colors duration-200 ${
      isActive
        ? "bg-blue-100 text-blue-600 font-bold"
        : "text-gray-700 hover:bg-gray-100"
    }`;
  };

  return (
    <aside className="w-64 bg-white shadow-lg flex flex-col sticky top-0 h-screen p-6 overflow-y-auto">
      <nav className="flex-1">
        <ul className="space-y-3">
          <li>
            <Link href="/dashboard" className={linkClass("/dashboard")}>Home</Link>
          </li>
          <li>
            <Link href="/dashboard/banking" className={linkClass("/dashboard/banking")}>Banking</Link>
          </li>
          <li>
            <Link href="/dashboard/credit" className={linkClass("/dashboard/credit")}>Credit</Link>
          </li>
          <li>
            <Link href="/dashboard/loans" className={linkClass("/dashboard/loans")}>Loans</Link>
          </li>
          <li>
            <Link href="/dashboard/investing" className={linkClass("/dashboard/investing")}>Investing</Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}