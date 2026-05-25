import {
  Book, BookCreate, BookUpdate,
  Member, MemberCreate, MemberUpdate,
  Lending, LendingCreate,
  Stats,
  LendingStatus,
} from "@/types";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    // FastAPI 422: detail is an array of {loc, msg, type} objects
    if (Array.isArray(body.detail)) {
      const msg = body.detail
        .map((e: { loc?: string[]; msg: string }) => {
          const field = e.loc?.filter(s => s !== "body").join(".") ?? "";
          return field ? `${field}: ${e.msg}` : e.msg;
        })
        .join(" · ");
      throw new Error(msg || "Validation failed");
    }
    throw new Error(body.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const booksApi = {
  list: () => request<Book[]>("/books"),
  get: (id: number) => request<Book>(`/books/${id}`),
  create: (data: BookCreate) =>
    request<Book>("/books", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: BookUpdate) =>
    request<Book>(`/books/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<{ detail: string }>(`/books/${id}`, { method: "DELETE" }),
};

export const membersApi = {
  list: () => request<Member[]>("/members"),
  get: (id: number) => request<Member>(`/members/${id}`),
  create: (data: MemberCreate) =>
    request<Member>("/members", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: MemberUpdate) =>
    request<Member>(`/members/${id}`, { method: "PUT", body: JSON.stringify(data) }),
};

export const lendingsApi = {
  list: (params?: { status?: LendingStatus; member_id?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.member_id) qs.set("member_id", String(params.member_id));
    return request<Lending[]>(`/lendings${qs.toString() ? `?${qs}` : ""}`);
  },
  getOverdue: () => request<Lending[]>("/lendings/overdue"),
  getMemberLendings: (memberId: number) => request<Lending[]>(`/lendings/member/${memberId}`),
  borrow: (data: LendingCreate) =>
    request<Lending>("/lendings", { method: "POST", body: JSON.stringify(data) }),
  complete: (lendingId: number) =>
    request<Lending>(`/lendings/${lendingId}/complete`, { method: "PUT" }),
};

export const statsApi = {
  get: () => request<Stats>("/stats"),
};
