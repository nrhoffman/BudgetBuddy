"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function SettingsSidebar() {
  const pathname = usePathname();

  const linkClass = (path: string) =>
    `block px-6 py-3 rounded-md text-lg font-medium transition-colors duration-200 ${
      pathname.startsWith(path) ? "bg-blue-100 text-blue-600 font-bold" : "text-gray-700 hover:bg-gray-100"
    }`;

  return (
    <aside className="w-64 h-screen p-6 bg-white shadow-lg flex flex-col">
      <nav className="flex-1">
        <ul className="space-y-3">
          <li>
            <Link href="/settings/account" className={linkClass("/settings/account")}>Account</Link>
          </li>
          <li>
            <Link href="/settings/data" className={linkClass("/settings/data")}>Data</Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
