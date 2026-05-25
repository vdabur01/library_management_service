import { useState, useEffect, useCallback } from "react";
import { booksApi } from "@/lib/api";
import type { Book, BookCreate } from "@/types";
import Modal from "@/components/ui/Modal";

const EMPTY: BookCreate = { title: "", author: "", isbn: "", genre: "", published_year: undefined, total_copies: 1 };

export default function Books() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editBook, setEditBook] = useState<Book | null>(null);
  const [form, setForm] = useState<BookCreate>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setBooks(await booksApi.list()); }
    catch (e: unknown) { setError((e as Error).message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openAdd = () => { setEditBook(null); setForm(EMPTY); setFormError(""); setShowModal(true); };
  const openEdit = (b: Book) => {
    setEditBook(b);
    setForm({ title: b.title, author: b.author, isbn: b.isbn ?? "", genre: b.genre ?? "", published_year: b.published_year, total_copies: b.total_copies });
    setFormError("");
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError("");
    try {
      editBook ? await booksApi.update(editBook.id, form) : await booksApi.create(form);
      setShowModal(false);
      load();
    } catch (e: unknown) { setFormError((e as Error).message); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Delete "${title}"?`)) return;
    try { await booksApi.delete(id); load(); }
    catch (e: unknown) { alert((e as Error).message); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Books</h1>
        <button className="btn-primary" onClick={openAdd}>+ Add Book</button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {loading ? <div className="text-gray-400">Loading…</div>
        : books.length === 0 ? <div className="text-gray-400">No books yet.</div>
        : (
          <div className="card p-0 overflow-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>{["Title","Author","ISBN","Genre","Year","Copies","Available","Actions"].map(h => <th key={h} className="table-header">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {books.map(b => (
                  <tr key={b.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{b.title}</td>
                    <td className="table-cell">{b.author}</td>
                    <td className="table-cell text-gray-500">{b.isbn ?? "—"}</td>
                    <td className="table-cell text-gray-500">{b.genre ?? "—"}</td>
                    <td className="table-cell text-gray-500">{b.published_year ?? "—"}</td>
                    <td className="table-cell text-center">{b.total_copies}</td>
                    <td className="table-cell text-center">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${b.available_copies > 0 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                        {b.available_copies}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-2">
                        <button onClick={() => openEdit(b)} className="btn-sm bg-blue-100 text-blue-700 hover:bg-blue-200">Edit</button>
                        <button onClick={() => handleDelete(b.id, b.title)} className="btn-sm bg-red-100 text-red-700 hover:bg-red-200">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      {showModal && (
        <Modal title={editBook ? "Edit Book" : "Add Book"} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {formError && <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">{formError}</div>}
            <div><label className="label">Title *</label><input className="input" required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></div>
            <div><label className="label">Author *</label><input className="input" required value={form.author} onChange={e => setForm({ ...form, author: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">ISBN</label><input className="input" value={form.isbn ?? ""} onChange={e => setForm({ ...form, isbn: e.target.value })} /></div>
              <div><label className="label">Genre</label><input className="input" value={form.genre ?? ""} onChange={e => setForm({ ...form, genre: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Published Year</label><input className="input" type="number" value={form.published_year ?? ""} onChange={e => setForm({ ...form, published_year: e.target.value ? parseInt(e.target.value) : undefined })} /></div>
              <div><label className="label">Total Copies *</label><input className="input" type="number" min={1} required value={form.total_copies} onChange={e => setForm({ ...form, total_copies: parseInt(e.target.value) || 1 })} /></div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={submitting}>{submitting ? "Saving…" : editBook ? "Update" : "Create"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
