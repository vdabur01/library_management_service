import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Books from "./pages/Books";
import Members from "./pages/Members";
import Lending from "./pages/Lending";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="bg-blue-700 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
          <NavLink to="/" className="text-xl font-bold tracking-tight">
            📚 Library
          </NavLink>
          {[
            { to: "/books", label: "Books" },
            { to: "/members", label: "Members" },
            { to: "/lending", label: "Lending" },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                isActive ? "font-semibold underline" : "hover:text-blue-200 transition-colors"
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/books" element={<Books />} />
          <Route path="/members" element={<Members />} />
          <Route path="/lending" element={<Lending />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
