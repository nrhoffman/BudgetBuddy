"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Banner from "./components/banner";

export default function Home() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) router.replace("/dashboard");
  }, [router]);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const username = (e.currentTarget.username as HTMLInputElement).value;
    const password = (e.currentTarget.password as HTMLInputElement).value;

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        alert("Invalid credentials");
        return;
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      setIsLoggedIn(true);
      router.push("/dashboard");
    } catch (err) {
      console.error(err);
      alert("Login failed");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
        <Banner />

      <main className="flex flex-col items-center justify-center text-center mt-20 px-4">
        <h2 className="text-5xl font-bold mb-6 text-gray-800">
          Take Control of Your Finances
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mb-10">
          Budget Buddy helps you track your spending, manage accounts, and stay on top of your financial goals.
        </p>

        {!isLoggedIn && (
          <div className="w-full max-w-md p-10 bg-white rounded-3xl shadow-lg mb-8">
            <h1 className="text-3xl font-bold mb-6 text-gray-800">Sign in</h1>
            <form className="flex flex-col gap-4" onSubmit={handleLogin}>
              <input
                name="username"
                type="text"
                placeholder="Username"
                className="p-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                name="password"
                type="password"
                placeholder="Password"
                className="p-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="p-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition"
              >
                Login
              </button>
            </form>
          </div>
        )}

        {!isLoggedIn && (
          <button
            onClick={() => router.push("/sign-up")}
            className="px-8 py-3 bg-green-500 text-white font-semibold rounded-xl shadow hover:bg-green-600 transition"
          >
            Get Started
          </button>
        )}
      </main>
    </div>
  );
}
