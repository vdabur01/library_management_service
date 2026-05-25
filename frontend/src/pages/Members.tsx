import { useState, useEffect, useCallback } from "react";
import { membersApi } from "@/lib/api";
import type { Member, MemberCreate } from "@/types";
import Modal from "@/components/ui/Modal";

const EMPTY: MemberCreate = { name: "", email: "", phone: "", address: "" };

export default function Members() {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editMember, setEditMember] = useState<Member | null>(null);
  const [form, setForm] = useState<MemberCreate>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setMembers(await membersApi.list()); }
    catch (e: unknown) { setError((e as Error).message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openAdd = () => { setEditMember(null); setForm(EMPTY); setFormError(""); setShowModal(true); };
  const openEdit = (m: Member) => {
    setEditMember(m);
    setForm({ name: m.name, email: m.email, phone: m.phone ?? "", address: m.address ?? "" });
    setFormError("");
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError("");
    try {
      editMember ? await membersApi.update(editMember.id, form) : await membersApi.create(form);
      setShowModal(false);
      load();
    } catch (e: unknown) { setFormError((e as Error).message); }
    finally { setSubmitting(false); }
  };

  const toggleActive = async (m: Member) => {
    try { await membersApi.update(m.id, { is_active: !m.is_active }); load(); }
    catch (e: unknown) { alert((e as Error).message); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Members</h1>
        <button className="btn-primary" onClick={openAdd}>+ Add Member</button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      {loading ? <div className="text-gray-400">Loading…</div>
        : members.length === 0 ? <div className="text-gray-400">No members yet.</div>
        : (
          <div className="card p-0 overflow-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>{["Name","Email","Phone","Address","Status","Joined","Actions"].map(h => <th key={h} className="table-header">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {members.map(m => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium">{m.name}</td>
                    <td className="table-cell">{m.email}</td>
                    <td className="table-cell text-gray-500">{m.phone ?? "—"}</td>
                    <td className="table-cell text-gray-500 max-w-xs truncate">{m.address ?? "—"}</td>
                    <td className="table-cell">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${m.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                        {m.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="table-cell text-gray-500">{new Date(m.created_at).toLocaleDateString()}</td>
                    <td className="table-cell">
                      <div className="flex gap-2">
                        <button onClick={() => openEdit(m)} className="btn-sm bg-blue-100 text-blue-700 hover:bg-blue-200">Edit</button>
                        <button onClick={() => toggleActive(m)} className={`btn-sm ${m.is_active ? "bg-yellow-100 text-yellow-700 hover:bg-yellow-200" : "bg-green-100 text-green-700 hover:bg-green-200"}`}>
                          {m.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      {showModal && (
        <Modal title={editMember ? "Edit Member" : "Add Member"} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {formError && <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">{formError}</div>}
            <div><label className="label">Name *</label><input className="input" required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="label">Email *</label><input className="input" type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></div>
            <div><label className="label">Phone</label><input className="input" value={form.phone ?? ""} onChange={e => setForm({ ...form, phone: e.target.value })} /></div>
            <div><label className="label">Address</label><textarea className="input" rows={2} value={form.address ?? ""} onChange={e => setForm({ ...form, address: e.target.value })} /></div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={submitting}>{submitting ? "Saving…" : editMember ? "Update" : "Create"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
