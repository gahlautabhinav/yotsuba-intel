import { useQuery, useMutation } from '@tanstack/react-query'
import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import StatCard from '../components/StatCard'
import Skeleton from '../components/Skeleton'

export default function Dashboard() {
  const [url, setUrl] = useState('')
  const [jobId, setJobId] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([])
  const [scraping, setScraping] = useState(false)
  const [done, setDone] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)

  const stats = useQuery({ queryKey: ['stats'], queryFn: api.getStats })
  const health = useQuery({ queryKey: ['health'], queryFn: api.getHealth })
  const threads = useQuery({ queryKey: ['threads'], queryFn: api.listThreads })

  const scrape = useMutation({
    mutationFn: (u: string) => api.scrape(u),
    onSuccess: (data) => {
      setJobId(data.job_id)
      setLogs([])
      setDone(false)
      setScraping(true)
    },
  })

  // Open SSE stream whenever jobId changes
  useEffect(() => {
    if (!jobId) return
    if (esRef.current) esRef.current.close()

    const es = new EventSource(api.scrapeStreamUrl(jobId))
    esRef.current = es

    es.onmessage = (e) => {
      setLogs(prev => [...prev, e.data])
    }

    es.addEventListener('done', () => {
      setScraping(false)
      setDone(true)
      es.close()
      stats.refetch()
      threads.refetch()
    })

    es.onerror = () => {
      setScraping(false)
      es.close()
    }

    return () => es.close()
  }, [jobId])

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const recent = (threads.data ?? []).slice(-5).reverse()
  const canScrape = !!url && !scrape.isPending && !scraping

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
      <div className="bg-canvas-soft border border-hairline rounded-[4px] p-4 space-y-3">
        <p className="text-sm font-medium text-ink">Scrape thread</p>
        <div className="flex gap-2">
          <input
            className="flex-1 bg-canvas border border-hairline rounded-[3px] px-3 py-1.5 text-sm text-ink placeholder-mute font-mono focus:outline-none focus:border-body-strong"
            placeholder="https://boards.4chan.org/g/thread/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && canScrape && scrape.mutate(url)}
          />
          <button
            onClick={() => canScrape && scrape.mutate(url)}
            disabled={!canScrape}
            className="bg-primary text-on-primary rounded-[3px] px-4 py-1.5 text-sm font-medium disabled:opacity-40 min-w-[80px]"
          >
            {scraping ? 'Running…' : scrape.isPending ? 'Starting…' : 'Scrape'}
          </button>
        </div>

        {/* Live log terminal */}
        {(logs.length > 0 || scraping) && (
          <div className="mt-1">
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs text-mute font-mono uppercase tracking-widest">output</span>
              {scraping && (
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-body-strong animate-pulse" />
              )}
              {done && (
                <span className="text-xs text-mute font-mono">done</span>
              )}
            </div>
            <div
              ref={logRef}
              className="bg-canvas border border-hairline rounded-[4px] p-3 h-52 overflow-y-auto font-mono text-xs leading-5 text-body-strong space-y-px"
            >
              {logs.map((line, i) => (
                <div
                  key={i}
                  className={
                    line.startsWith('✓') ? 'text-body-strong' :
                    line.startsWith('✗') ? 'text-mute' :
                    line.startsWith('→') ? 'text-ink' :
                    'text-body'
                  }
                >
                  {line || ' '}
                </div>
              ))}
              {scraping && (
                <div className="text-mute animate-pulse">▋</div>
              )}
            </div>
          </div>
        )}

        {scrape.isError && (
          <p className="text-xs text-mute">Error starting scrape — check API is running.</p>
        )}
      </div>

      {/* Recent threads */}
      <div>
        <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Recent threads</p>
        {threads.isLoading ? <Skeleton rows={5} /> : (
          <div className="border border-hairline rounded-[4px] overflow-hidden">
            {recent.length === 0 ? (
              <p className="text-sm text-mute px-4 py-3">No threads scraped yet.</p>
            ) : recent.map(t => (
              <Link
                key={t.id}
                to={`/threads/${t.id}`}
                className="flex items-center justify-between px-4 py-2.5 border-b border-hairline last:border-b-0 hover:bg-canvas-soft transition-colors"
              >
                <div>
                  <span className="font-mono text-xs text-mute">/{t.board}/ #{t.thread_no}</span>
                  <p className="text-sm text-ink mt-0.5 truncate max-w-sm">{t.subject ?? '(no subject)'}</p>
                </div>
                <span className="text-xs text-mute font-mono">{t.post_count}p</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
