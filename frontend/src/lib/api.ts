const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit, silent401 = false): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem('token');
    if (!silent401 && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }, true),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }, true),

  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }, true),
};

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  username: string;
  is_admin: boolean;
}

export interface DashboardStats {
  total: number;
  today: number;
  this_week: number;
  this_month: number;
  by_category: StatItem[];
  by_type: StatItem[];
  by_tender_mode: StatItem[];
  daily_trend: TrendItem[];
  total_bid_amount: number;
  winning_count: number;
  top_count_companies: TopCompany[];
  top_amount_companies: TopCompany[];
  crawl_stats: CrawlStats;
  recent_crawl_tasks: CrawlTaskRecord[];
}

export interface CrawlStats {
  data_source_count: number;
  running_tasks: number;
  failed_tasks: number;
  total_records: number;
}

export interface CrawlTaskRecord {
  id: string;
  task_type: string;
  mode: string;
  status: string;
  record_count: number | null;
  elapsed_seconds: number | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
}

export interface StatItem {
  name: string;
  value: number;
}

export interface TrendItem {
  date: string;
  count: number;
}

export interface TopCompany {
  rank: number;
  name: string;
  count: number;
  total_amount: number;
}

export interface AnnouncementListResponse {
  total: number;
  page: number;
  size: number;
  items: AnnouncementItem[];
}

export interface AnnouncementItem {
  id: string;
  project_no: string | null;
  title: string;
  category: string | null;
  tender_mode_desc: string | null;
  tenderer_name: string | null;
  tenderer_contact: string | null;
  tenderer_phone: string | null;
  publish_date: string | null;
  winner_supplier: string;
  winner_amount: number | null;
  winner_credit_code: string;
  source_url: string | null;
  purchase_control_price: number | null;
  detail_fetched: number;
}

export interface AnnouncementDetail {
  id: string;
  project_id: number | null;
  project_no: string | null;
  title: string;
  announcement_type: number | null;
  announcement_type_desc: string | null;
  tender_mode_desc: string | null;
  category: string | null;
  publish_date: string | null;
  deadline: string | null;
  source_url: string | null;
  purchase_control_price: number | null;
  bid_price: number | null;
  winning_bidders: WinningBidder[] | null;
  tenderer_name: string | null;
  tenderer_contact: string | null;
  tenderer_phone: string | null;
  project_address: string | null;
  fund_source: string | null;
  tender_content: string | null;
  detail_fetched: number;
}

export interface WinningBidder {
  supplier_name: string | null;
  bid_amount: number | null;
  is_winning: number | null;
  rank: number | null;
  social_credit_code: string | null;
}

export interface CrawlerStatus {
  is_running: boolean;
  mode: string;
  task_id: string;
  elapsed: string;
  progress: Record<string, unknown>;
  result: Record<string, unknown>;
  recent_logs: LogEntry[];
  log_count: number;
}

export interface LogEntry {
  time: string;
  level: string;
  msg: string;
}
