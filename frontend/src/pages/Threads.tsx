import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Skeleton from '../components/Skeleton'
import EmptyState from '../components/EmptyState'
import Badge from '../components/Badge'

export default function Threads() {
  const { data, isLoading } = useQuery({ queryKey: ['threads'], queryFn: api.listThreads })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-medium text-ink">Threads</h1>
      {isLoading && <Skeleton rows={8} />}
      {!isLoading && (!data || data.length === 0) && (
        <EmptyState message="No threads scraped" sub="Use the Dashboard to scrape a thread URL." />
      )}
      {data && data.length > 0 && (
        <div className="border border-hairline rounded-[4px] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-canvas-soft border-b border-hairline">
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase tracking-wider">Board</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase tracking-wider">Thread#</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase tracking-wider">Subject</th>
                <th className="text-right px-3 py-2 text-xs text-mute font-mono uppercase tracking-wider">Posts</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase tracking-wider">Scraped</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.map(t => (
                <tr key={t.id} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft transition-colors">
                  <td className="px-3 py-2 font-mono text-xs text-mute">/{t.board}/</td>
                  <td className="px-3 py-2 font-mono text-xs text-body-strong">
                    <Link to={`/threads/${t.id}`} className="hover:text-ink">{t.thread_no}</Link>
                  </td>
                  <td className="px-3 py-2 text-ink max-w-xs truncate">
                    <Link to={`/threads/${t.id}`} className="hover:underline">{t.subject ?? <span className="text-mute">(no subject)</span>}</Link>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-body">{t.post_count}</td>
                  <td className="px-3 py-2 font-mono text-xs text-mute">{t.scraped_at?.slice(0, 10)}</td>
                  <td className="px-3 py-2">
                    {t.is_archived ? <Badge variant="mute">archived</Badge> : <Badge variant="success">live</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
