import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { statsApi } from "@/lib/api";
import type { Stats } from "@/types";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    statsApi.get().then(setStats).catch((e: Error) => setError(e.message));
  }, []);

  const cards = stats
    ? [
        { label: "Total Books", value: stats.total_books, to: "/books", color: "bg-blue-500" },
        { label: "Total Members", value: stats.total_members, to: "/members", color: "bg-green-500" },
        { label: "Active Lendings", value: stats.active_lendings, to: "/lending", color: "bg-yellow-500" },
        { label: "Overdue Lendings", value: stats.overdue_lendings, to: "/lending?tab=overdue", color: "bg-red-500" },
      ]
    : [];

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Dashboard</h1>
      <p className="text-gray-500 mb-8">Welcome to the Neighborhood Library management system.</p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          Could not load stats: {error}. Make sure the backend is running.
        </div>
      )}

      {!stats && !error && <div className="text-gray-400">Loading stats…</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((c) => (
          <Link key={c.label} to={c.to} className="card hover:shadow-lg transition-shadow">
            <div className={`${c.color} text-white text-3xl font-bold rounded-lg p-4 mb-3 text-center`}>
              {c.value}
            </div>
            <p className="text-center text-gray-700 font-medium">{c.label}</p>
          </Link>
        ))}
      </div>

      <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { to: "/books", icon: "📖", title: "Manage Books", desc: "Add, edit, and remove books from the catalog." },
          { to: "/members", icon: "👥", title: "Manage Members", desc: "Register and update library member accounts." },
          { to: "/lending", icon: "🔄", title: "Lending Operations", desc: "Borrow and return books, track fines." },
        ].map(({ to, icon, title, desc }) => (
          <Link key={to} to={to} className="card hover:shadow-lg transition-shadow flex flex-col gap-2">
            <span className="text-2xl">{icon}</span>
            <h2 className="font-semibold text-lg">{title}</h2>
            <p className="text-sm text-gray-500">{desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
