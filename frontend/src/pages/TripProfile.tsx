import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import Skeleton from '../components/Skeleton'
import Badge from '../components/Badge'

function TzHistogram({ histogram }: { histogram: number[] }) {
  const max = Math.max(...histogram, 1)
  return (
    <div className="flex items-end gap-px h-10 mt-2">
      {histogram.map((v, i) => (
        <div
          key={i}
          className="flex-1 bg-body-strong rounded-[1px] min-h-[2px]"
          style={{ height: `${Math.max(4, (v / max) * 40)}px`, opacity: v === 0 ? 0.15 : 1 }}
          title={`Hour ${i}: ${v} posts`}
        />
      ))}
    </div>
  )
}

export default function TripProfile() {
  const { trip } = useParams<{ trip: string }>()
  const decoded = decodeURIComponent(trip ?? '')
  const { data, isLoading, isError } = useQuery({
    queryKey: ['trip-profile', decoded],
    queryFn: () => api.getTripProfile(decoded),
  })

  if (isLoading) return <div className="space-y-4"><Skeleton rows={10} /></div>
  if (isError || !data) return (
    <div className="space-y-2">
      <Link to="/tripcodes" className="text-xs text-mute hover:text-body font-mono">← tripcodes</Link>
      <p className="text-sm text-mute">Profile unavailable. Run <code className="font-mono">chan profile --trip "{decoded}"</code> first.</p>
    </div>
  )

  return (
    <div className="space-y-5">
      <div>
        <Link to="/tripcodes" className="text-xs text-mute hover:text-body font-mono">← tripcodes</Link>
        <h1 className="text-lg font-medium text-ink mt-1 font-mono">{data.trip}</h1>
        <Badge variant={data.trip_strength === 'secure' ? 'success' : 'mute'}>{data.trip_strength}</Badge>
      </div>

      {/* Identity */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {[
          ['Posts (local)', data.post_count],
          ['Posts (archive)', data.archive_post_count],
          ['First seen', data.first_seen?.slice(0, 10) ?? '—'],
          ['Last seen', data.last_seen?.slice(0, 10) ?? '—'],
          ['Boards', data.boards.join(', ') || '—'],
          ['Countries', data.countries.join(', ') || '—'],
        ].map(([label, val]) => (
          <div key={String(label)} className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-3">
            <p className="text-xs text-mute font-mono uppercase tracking-widest mb-0.5">{label}</p>
            <p className="text-sm text-ink font-mono">{val}</p>
          </div>
        ))}
      </div>

      {/* Timezone */}
      <div className="bg-canvas-soft border border-hairline rounded-[4px] p-4">
        <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Timezone inference</p>
        <div className="flex items-center gap-3">
          <span className="text-lg font-medium font-mono text-ink">{data.timezone_guess}</span>
          <span className="text-xs text-body font-mono">{(data.timezone_confidence * 100).toFixed(0)}% confidence</span>
        </div>
        {data.timezone_histogram.length === 24 && (
          <>
            <TzHistogram histogram={data.timezone_histogram} />
            <div className="flex justify-between mt-1">
              <span className="text-xs text-mute font-mono">00:00</span>
              <span className="text-xs text-mute font-mono">12:00</span>
              <span className="text-xs text-mute font-mono">23:00</span>
            </div>
          </>
        )}
        {data.timezone_warning && (
          <p className="text-xs text-mute mt-2 italic">{data.timezone_warning}</p>
        )}
      </div>

      {/* Social links */}
      {data.social_links.length > 0 && (
        <div>
          <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Social links</p>
          <div className="border border-hairline rounded-[4px] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-canvas-soft border-b border-hairline">
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Platform</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Handle</th>
                  <th className="text-right px-3 py-2 text-xs text-mute font-mono uppercase">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {data.social_links.map((l, i) => (
                  <tr key={i} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft">
                    <td className="px-3 py-2 font-mono text-xs text-body">{l.platform}</td>
                    <td className="px-3 py-2 text-xs text-ink">{l.handle}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-body">{(l.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Emails */}
      {data.emails.length > 0 && (
        <div>
          <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Emails</p>
          {data.emails.map(e => (
            <div key={e} className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-2 mb-1.5 font-mono text-sm text-ink">{e}</div>
          ))}
        </div>
      )}

      {/* PGP */}
      {data.pgp_fingerprints.length > 0 && (
        <div>
          <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">PGP fingerprints</p>
          {data.pgp_fingerprints.map(fp => (
            <div key={fp} className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-2 mb-1.5 font-mono text-xs text-body-strong break-all">{fp}</div>
          ))}
        </div>
      )}

      {/* Name variants */}
      {data.name_variants.length > 0 && (
        <div>
          <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Name variants</p>
          <div className="flex flex-wrap gap-1.5">
            {data.name_variants.map(n => (
              <Badge key={n}>{n}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
