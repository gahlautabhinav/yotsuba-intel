import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import Skeleton from '../components/Skeleton'
import EmptyState from '../components/EmptyState'
import Badge from '../components/Badge'

type Tab = 'posts' | 'links' | 'emails'

export default function ThreadDetail() {
  const { id } = useParams<{ id: string }>()
  const tid = Number(id)
  const [tab, setTab] = useState<Tab>('posts')

  const thread = useQuery({ queryKey: ['thread', tid], queryFn: () => api.getThread(tid) })
  const posts  = useQuery({ queryKey: ['thread-posts', tid], queryFn: () => api.getThreadPosts(tid), enabled: tab === 'posts' })
  const links  = useQuery({ queryKey: ['thread-links', tid], queryFn: () => api.getThreadLinks(tid), enabled: tab === 'links' })
  const emails = useQuery({ queryKey: ['thread-emails', tid], queryFn: () => api.getThreadEmails(tid), enabled: tab === 'emails' })

  const t = thread.data

  return (
    <div className="space-y-4">
      <div>
        <Link to="/threads" className="text-xs text-mute hover:text-body font-mono">← threads</Link>
        {t && (
          <h1 className="text-lg font-medium text-ink mt-1">
            /{t.board}/ #{t.thread_no}
            {t.subject && <span className="text-body font-normal ml-2">{t.subject}</span>}
          </h1>
        )}
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-hairline pb-0">
        {(['posts','links','emails'] as Tab[]).map(tb => (
          <button
            key={tb}
            onClick={() => setTab(tb)}
            className={`px-3 py-1.5 text-sm rounded-[3px] rounded-b-none font-medium transition-colors ${
              tab === tb ? 'bg-canvas-soft text-ink border border-b-0 border-hairline' : 'text-body hover:text-ink'
            }`}
          >
            {tb.charAt(0).toUpperCase() + tb.slice(1)}
          </button>
        ))}
      </div>

      {/* Posts tab */}
      {tab === 'posts' && (
        <div>
          {posts.isLoading && <Skeleton rows={6} />}
          {posts.data && posts.data.length === 0 && <EmptyState message="No posts" />}
          {posts.data?.map(p => (
            <div key={p.id} className="bg-canvas-soft border border-hairline rounded-[4px] p-3 mb-2">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs text-mute">#{p.post_no}</span>
                <span className="text-xs text-body-strong">{p.name}</span>
                {p.trip && <span className="font-mono text-xs text-mute">{p.trip}</span>}
                {p.country && <span className="text-xs text-mute">[{p.country}]</span>}
                <span className="text-xs text-mute ml-auto font-mono">{p.posted_at?.replace('T',' ').slice(0,16)}</span>
              </div>
              <p className="text-sm text-body leading-relaxed whitespace-pre-wrap">{p.body_text}</p>
              {p.file_md5 && (
                <div className="mt-1.5">
                  <span className="font-mono text-xs text-mute">md5: {p.file_md5}</span>
                  {p.file_ext && <span className="font-mono text-xs text-mute ml-2">{p.file_ext}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Links tab */}
      {tab === 'links' && (
        <div>
          {links.isLoading && <Skeleton rows={4} />}
          {links.data && links.data.length === 0 && <EmptyState message="No social links extracted" />}
          {links.data && links.data.length > 0 && (
            <div className="border border-hairline rounded-[4px] overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-canvas-soft border-b border-hairline">
                    <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Platform</th>
                    <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Handle</th>
                    <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">URL</th>
                    <th className="text-right px-3 py-2 text-xs text-mute font-mono uppercase">Conf</th>
                    <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Pivot</th>
                  </tr>
                </thead>
                <tbody>
                  {links.data.map(l => (
                    <tr key={l.id} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft">
                      <td className="px-3 py-2 font-mono text-xs text-body">{l.platform}</td>
                      <td className="px-3 py-2 text-xs text-ink">{l.handle ?? '—'}</td>
                      <td className="px-3 py-2 max-w-xs truncate">
                        <a href={l.raw_url} target="_blank" rel="noopener noreferrer" className="font-mono text-xs text-mute hover:text-body-strong">{l.raw_url}</a>
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-body">{(l.confidence * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2">
                        <Badge variant={l.pivot_status === 'success' ? 'success' : l.pivot_status === 'failed' ? 'error' : 'mute'}>
                          {l.pivot_status ?? 'pending'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Emails tab */}
      {tab === 'emails' && (
        <div>
          {emails.isLoading && <Skeleton rows={3} />}
          {emails.data && emails.data.length === 0 && <EmptyState message="No emails extracted" />}
          {emails.data?.map(e => (
            <div key={e.id} className="flex items-center justify-between bg-canvas-soft border border-hairline rounded-[4px] px-4 py-2 mb-1.5">
              <span className="font-mono text-sm text-ink">{e.email}</span>
              <span className="text-xs text-mute">{e.source}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
