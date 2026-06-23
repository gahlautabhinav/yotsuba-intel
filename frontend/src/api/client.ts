const BASE = 'http://localhost:8003'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${path}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  getStats: () => get<{ thread_count: number; tripcode_count: number }>('/stats'),
  getHealth: () => get<{ status: string }>('/health'),
  listThreads: () => get<Thread[]>('/threads/'),
  getThread: (id: number) => get<Thread>(`/threads/${id}`),
  getThreadPosts: (id: number) => get<Post[]>(`/threads/${id}/posts`),
  getThreadLinks: (id: number) => get<Link[]>(`/threads/${id}/links`),
  getThreadEmails: (id: number) => get<EmailItem[]>(`/threads/${id}/emails`),
  listTripcodes: () => get<Tripcode[]>('/tripcodes/'),
  getTripProfile: (trip: string) => get<TripProfile>(`/tripcodes/${encodeURIComponent(trip)}/profile`),
  correlateMd5: (md5: string) => post<Md5Result>('/correlate/md5', { md5 }),
  archiveSearch: (req: ArchiveSearchReq) => post<ArchivePost[]>('/archive/search', req),
  scrape: (url: string, download_images = false) => post<{ status: string }>('/scrape/', { url, download_images }),
  listLinks: () => get<Link[]>('/links/'),
  listEmails: () => get<EmailItem[]>('/emails/'),
}

// Types
export interface Thread {
  id: number
  board: string
  thread_no: number
  subject: string | null
  scraped_at: string
  post_count: number
  unique_ips: number | null
  is_archived: boolean
  raw_url: string | null
}

export interface Post {
  id: number
  thread_id: number
  post_no: number
  posted_at: string | null
  name: string
  trip: string | null
  country: string | null
  body_text: string | null
  has_file: boolean
  file_md5: string | null
  file_ext: string | null
}

export interface Link {
  id: number
  post_id: number
  platform: string
  raw_url: string
  handle: string | null
  confidence: number
  pivot_status?: string
  pivot_profile_data?: string | null
}

export interface EmailItem {
  id: number
  post_id: number
  email: string
  source: string
}

export interface Tripcode {
  id: number
  trip: string
  trip_strength: string
  post_count: number
  first_seen_at: string | null
  last_seen_at: string | null
  boards_seen: string | null
  timezone_guess: string | null
  timezone_confidence: number | null
}

export interface TripProfile {
  trip: string
  trip_strength: string
  post_count: number
  archive_post_count: number
  boards: string[]
  countries: string[]
  name_variants: string[]
  first_seen: string | null
  last_seen: string | null
  social_links: { platform: string; handle: string; confidence: number }[]
  emails: string[]
  pgp_fingerprints: string[]
  timezone_guess: string
  timezone_confidence: number
  timezone_histogram: number[]
  timezone_warning: string | null
  active_boards: string[]
}

export interface Md5Result {
  file_md5: string
  post_refs: PostRef[]
  post_count: number
  board_count: number
  has_tripcode_match: boolean
  confidence: number
  correlation_type: string
  is_likely_meme: boolean
  evidence: string[]
}

export interface PostRef {
  source: string
  board: string
  thread_no: number
  post_no: number
  posted_at: string | null
  name: string | null
  trip: string | null
  archive_url: string | null
}

export interface ArchivePost {
  source: string
  board: string
  thread_no: number
  post_no: number
  posted_at: string | null
  name: string | null
  trip: string | null
  body_text: string | null
  file_md5: string | null
  archive_url: string | null
}

export interface ArchiveSearchReq {
  trip?: string
  md5?: string
  name?: string
  sources?: string[]
  board?: string
}
