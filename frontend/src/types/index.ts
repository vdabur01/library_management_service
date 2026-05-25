export interface Book {
  id: number;
  title: string;
  author: string;
  isbn?: string;
  genre?: string;
  published_year?: number;
  total_copies: number;
  available_copies: number;
  created_at: string;
  updated_at?: string;
}

export interface BookCreate {
  title: string;
  author: string;
  isbn?: string;
  genre?: string;
  published_year?: number;
  total_copies: number;
}

export interface BookUpdate {
  title?: string;
  author?: string;
  isbn?: string;
  genre?: string;
  published_year?: number;
  total_copies?: number;
}

export interface Member {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface MemberCreate {
  name: string;
  email: string;
  phone?: string;
  address?: string;
}

export interface MemberUpdate {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  is_active?: boolean;
}

export type LendingStatus = "active" | "returned" | "overdue";

export interface BookSummary {
  id: number;
  title: string;
  author: string;
  isbn?: string;
}

export interface MemberSummary {
  id: number;
  name: string;
  email: string;
}

export interface Lending {
  id: number;
  book_id: number;
  member_id: number;
  borrowed_at: string;
  due_date: string;
  returned_at?: string;
  fine_amount: number;
  status: LendingStatus;
  book?: BookSummary;
  member?: MemberSummary;
  created_at: string;
}

export interface LendingCreate {
  book_id: number;
  member_id: number;
}

export interface Stats {
  total_books: number;
  total_members: number;
  active_lendings: number;
  overdue_lendings: number;
}
