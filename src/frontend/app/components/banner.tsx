"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Banner() {
  const router = useRouter();

  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    setIsLoggedIn(Boolean(token));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
    router.push("/");
  };

  if (isLoggedIn === null) return null;

  return (
    <header className="flex items-center justify-between px-8 py-6 bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg">
      <h1 className="text-4xl font-bold">Budget Buddy</h1>
      
      <div className="flex gap-4">
        {isLoggedIn && (
          <button
            onClick={() => router.push("/dashboard")}
            className="bg-white text-blue-600 font-semibold px-6 py-2 rounded-lg shadow hover:bg-gray-100 transition"
          >
            Dashboard
          </button>
        )}

        {isLoggedIn ? (
          <button
            onClick={handleLogout}
            className="bg-white text-red-600 font-semibold px-6 py-2 rounded-lg shadow hover:bg-gray-100 transition"
          >
            Logout
          </button>
        ) : (
          <button
            onClick={() => router.push("/sign-up")}
            className="bg-white text-blue-600 font-semibold px-6 py-2 rounded-lg shadow hover:bg-gray-100 transition"
          >
            Sign Up
          </button>
        )}
      </div>
    </header>
  );
}
