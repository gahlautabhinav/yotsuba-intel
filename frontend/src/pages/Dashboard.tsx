import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api/client'
import StatCard from '../components/StatCard'
import Skeleton from '../components/Skeleton'

export default function Dashboard() {
  const [url, setUrl] = useState('')
  const stats = useQuery({ queryKey: ['stats'], queryFn: api.getStats })
  const health = useQuery({ queryKey: ['health'], queryFn: api.getHealth })
  const threads = useQuery({ queryKey: ['threads'], queryFn: api.listThreads })

  const scrape = useMutation({
    mutationFn: (u: string) => api.scrape(u),
    onSuccess: () => { setUrl(''); stats.refetch(); threads.refetch() },
  })

  const recent = (threads.data ?? []).slice(-5).reverse()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-medium text-ink">Dashboard</h1>
        <p className="text-xs text-mute mt-0.5 font-mono">
          API {health.data?.status === 'ok' ? '● online' : health.isLoading ? '○ checking' : '× offline'}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Threads" value={stats.data?.thread_count ?? '—'} />
        <StatCard label="Tripcodes" value={stats.data?.tripcode_count ?? '—'} />
      </div>

      {/* Scrape form */}
      <div className="bg-canvas-soft border border-hairline rounded-[4px] p-4">
        <p className="text-sm font-medium text-ink mb-2">Scrape thread</p>
        <div className="flex gap-2">
          <input
            className="flex-1 bg-canvas border border-hairline rounded-[3px] px-3 py-1.5 text-sm text-ink placeholder-mute font-mono focus:outline-none focus:border-body-strong"
            placeholder="https://boards.4chan.org/g/thread/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && url && scrape.mutate(url)}
          />
          <button
            onClick={() => url && scrape.mutate(url)}
            disabled={!url || scrape.isPending}
            className="bg-primary text-on-primary rounded-[3px] px-4 py-1.5 text-sm font-medium disabled:opacity-40"
          >
            {scrape.isPending ? 'Starting…' : 'Scrape'}
          </button>
        </div>
        {scrape.isSuccess && <p className="text-xs text-body mt-1.5">Started — reload in a few seconds.</p>}
        {scrape.isError && <p className="text-xs text-mute mt-1.5">Error: check API is running.</p>}
      </div>

      {/* Recent threads */}
      <div>
        <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Recent threads</p>
        {threads.isLoading ? <Skeleton rows={5} /> : (
          <div className="border border-hairline rounded-[4px] overflow-hidden">
            {recent.length === 0 ? (
              <p className="text-sm text-mute px-4 py-3">No threads scraped yet.</p>
            ) : recent.map(t => (
              <a
                key={t.id}
                href={`/threads/${t.id}`}
                className="flex items-center justify-between px-4 py-2.5 border-b border-hairline last:border-b-0 hover:bg-canvas-soft transition-colors"
              >
                <div>
                  <span className="font-mono text-xs text-mute">/{t.board}/ #{t.thread_no}</span>
                  <p className="text-sm text-ink mt-0.5 truncate max-w-sm">{t.subject ?? '(no subject)'}</p>
                </div>
                <span className="text-xs text-mute font-mono">{t.post_count}p</span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
