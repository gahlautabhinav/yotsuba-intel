import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Skeleton from '../components/Skeleton'
import EmptyState from '../components/EmptyState'
import Badge from '../components/Badge'

export default function Tripcodes() {
  const { data, isLoading } = useQuery({ queryKey: ['tripcodes'], queryFn: api.listTripcodes })

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-medium text-ink">Tripcodes</h1>
      {isLoading && <Skeleton rows={6} />}
      {!isLoading && (!data || data.length === 0) && (
        <EmptyState message="No tripcodes found" sub="Scrape threads with tripcode posters first." />
      )}
      {data && data.length > 0 && (
        <div className="border border-hairline rounded-[4px] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-canvas-soft border-b border-hairline">
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Trip</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Strength</th>
                <th className="text-right px-3 py-2 text-xs text-mute font-mono uppercase">Posts</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">First seen</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Timezone</th>
              </tr>
            </thead>
            <tbody>
              {data.map(tc => (
                <tr key={tc.id} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft transition-colors">
                  <td className="px-3 py-2">
                    <Link
                      to={`/tripcodes/${encodeURIComponent(tc.trip)}`}
                      className="font-mono text-xs text-body-strong hover:text-ink"
                    >
                      {tc.trip}
                    </Link>
                  </td>
                  <td className="px-3 py-2">
                    <Badge variant={tc.trip_strength === 'secure' ? 'success' : 'mute'}>{tc.trip_strength}</Badge>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-body">{tc.post_count}</td>
                  <td className="px-3 py-2 font-mono text-xs text-mute">{tc.first_seen_at?.slice(0, 10) ?? '—'}</td>
                  <td className="px-3 py-2 font-mono text-xs text-mute">{tc.timezone_guess ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
