import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { lendingsApi, booksApi, membersApi } from "@/lib/api";
import type { Lending, Book, Member } from "@/types";
import Modal from "@/components/ui/Modal";

type Tab = "active" | "overdue" | "history";

export default function LendingPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>(searchParams.get("tab") === "overdue" ? "overdue" : "active");

  const [lendings, setLendings] = useState<Lending[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showBorrowModal, setShowBorrowModal] = useState(false);
  const [books, setBooks] = useState<Book[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [borrowForm, setBorrowForm] = useState({ book_id: "", member_id: "" });
  const [borrowError, setBorrowError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadLendings = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      if (tab === "active") setLendings(await lendingsApi.list({ status: "active" }));
      else if (tab === "overdue") setLendings(await lendingsApi.getOverdue());
      else setLendings(await lendingsApi.list({ status: "returned" }));
    } catch (e: unknown) { setError((e as Error).message); }
    finally { setLoading(false); }
  }, [tab]);

  useEffect(() => { loadLendings(); }, [loadLendings]);

  const switchTab = (t: Tab) => {
    setTab(t);
    navigate(t === "overdue" ? "/lending?tab=overdue" : "/lending", { replace: true });
  };

  const openBorrowModal = async () => {
    setBorrowError("");
    setBorrowForm({ book_id: "", member_id: "" });
    const [b, m] = await Promise.all([booksApi.list(), membersApi.list()]);
    setBooks(b.filter(bk => bk.available_copies > 0));
    setMembers(m.filter(mb => mb.is_active));
    setShowBorrowModal(true);
  };

  const handleBorrow = async (e: React.FormEvent) => {
    e.preventDefault();
    setBorrowError("");
    setSubmitting(true);
    try {
      await lendingsApi.borrow({ book_id: parseInt(borrowForm.book_id), member_id: parseInt(borrowForm.member_id) });
      setShowBorrowModal(false);
      switchTab("active");
    } catch (e: unknown) { setBorrowError((e as Error).message); }
    finally { setSubmitting(false); }
  };

  const handleComplete = async (lending: Lending) => {
    const bookTitle = lending.book?.title ?? `Book #${lending.book_id}`;
    const memberName = lending.member?.name ?? `Member #${lending.member_id}`;
    if (!confirm(`Complete lending of "${bookTitle}" for ${memberName}?`)) return;
    try { await lendingsApi.complete(lending.id); loadLendings(); }
    catch (e: unknown) { alert((e as Error).message); }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "active", label: "Active" },
    { id: "overdue", label: "Overdue" },
    { id: "history", label: "Returned" },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Lending</h1>
        <button className="btn-primary" onClick={openBorrowModal}>+ Borrow Book</button>
      </div>

      <div className="flex gap-1 mb-6 border-b">
        {tabs.map(t => (
          <button key={t.id} onClick={() => switchTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t.id ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {loading ? <div className="text-gray-400">Loading…</div>
        : lendings.length === 0 ? <div className="text-gray-400">No lendings to show.</div>
        : (
          <div className="card p-0 overflow-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {["Book","Member","Borrowed","Due Date","Returned","Fine","Status",...(tab !== "history" ? ["Actions"] : [])].map(h => <th key={h} className="table-header">{h}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {lendings.map(lending => (
                  <tr key={lending.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{lending.book?.title ?? `#${lending.book_id}`}</td>
                    <td className="table-cell">{lending.member?.name ?? `#${lending.member_id}`}</td>
                    <td className="table-cell text-gray-500">{new Date(lending.borrowed_at).toLocaleDateString()}</td>
                    <td className="table-cell text-gray-500">{lending.due_date}</td>
                    <td className="table-cell text-gray-500">{lending.returned_at ? new Date(lending.returned_at).toLocaleDateString() : "—"}</td>
                    <td className="table-cell">{lending.fine_amount > 0 ? <span className="text-red-600 font-semibold">${Number(lending.fine_amount).toFixed(2)}</span> : "—"}</td>
                    <td className="table-cell">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${lending.status === "active" ? "bg-blue-100 text-blue-700" : lending.status === "overdue" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>
                        {lending.status}
                      </span>
                    </td>
                    {tab !== "history" && (
                      <td className="table-cell">
                        <button onClick={() => handleComplete(lending)} className="btn-sm bg-green-100 text-green-700 hover:bg-green-200">Complete</button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      {showBorrowModal && (
        <Modal title="Borrow a Book" onClose={() => setShowBorrowModal(false)}>
          <form onSubmit={handleBorrow} className="flex flex-col gap-4">
            {borrowError && <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">{borrowError}</div>}
            <div>
              <label className="label">Member *</label>
              <select className="input" required value={borrowForm.member_id} onChange={e => setBorrowForm({ ...borrowForm, member_id: e.target.value })}>
                <option value="">Select member…</option>
                {members.map(m => <option key={m.id} value={m.id}>{m.name} ({m.email})</option>)}
              </select>
            </div>
            <div>
              <label className="label">Book *</label>
              <select className="input" required value={borrowForm.book_id} onChange={e => setBorrowForm({ ...borrowForm, book_id: e.target.value })}>
                <option value="">Select book…</option>
                {books.map(b => <option key={b.id} value={b.id}>{b.title} by {b.author} ({b.available_copies} available)</option>)}
              </select>
            </div>
            <p className="text-xs text-gray-500">Lending period: 14 days. Fine: $0.25/day if overdue.</p>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowBorrowModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={submitting}>{submitting ? "Processing…" : "Borrow"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
