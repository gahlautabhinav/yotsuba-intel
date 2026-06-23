import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import Badge from '../components/Badge'
import EmptyState from '../components/EmptyState'

export default function Correlate() {
  const [md5, setMd5] = useState('')
  const correlate = useMutation({ mutationFn: (m: string) => api.correlateMd5(m) })

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-medium text-ink">MD5 Correlator</h1>
        <p className="text-xs text-mute mt-0.5">Cross-thread image reuse analysis</p>
      </div>

      <div className="bg-canvas-soft border border-hairline rounded-[4px] p-4">
        <label className="block text-xs text-mute font-mono uppercase tracking-widest mb-1.5">File MD5 (base64)</label>
        <div className="flex gap-2">
          <input
            className="flex-1 bg-canvas border border-hairline rounded-[3px] px-3 py-1.5 text-sm text-ink placeholder-mute font-mono focus:outline-none focus:border-body-strong"
            placeholder="e.g. Kq3UU28+lXxOmKB5U9Gx3Q=="
            value={md5}
            onChange={e => setMd5(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && md5 && correlate.mutate(md5)}
          />
          <button
            onClick={() => md5 && correlate.mutate(md5)}
            disabled={!md5 || correlate.isPending}
            className="bg-primary text-on-primary rounded-[3px] px-4 py-1.5 text-sm font-medium disabled:opacity-40"
          >
            {correlate.isPending ? 'Correlating…' : 'Correlate'}
          </button>
        </div>
      </div>

      {correlate.isError && <p className="text-sm text-mute">Error correlating MD5.</p>}

      {correlate.data && (() => {
        const d = correlate.data
        return (
          <div className="space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-3">
                <p className="text-xs text-mute font-mono uppercase tracking-widest mb-0.5">Posts</p>
                <p className="text-lg font-medium font-mono text-ink">{d.post_count}</p>
              </div>
              <div className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-3">
                <p className="text-xs text-mute font-mono uppercase tracking-widest mb-0.5">Boards</p>
                <p className="text-lg font-medium font-mono text-ink">{d.board_count}</p>
              </div>
              <div className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-3">
                <p className="text-xs text-mute font-mono uppercase tracking-widest mb-0.5">Confidence</p>
                <p className="text-lg font-medium font-mono text-ink">{(d.confidence * 100).toFixed(0)}%</p>
              </div>
              <div className="bg-canvas-soft border border-hairline rounded-[4px] px-4 py-3">
                <p className="text-xs text-mute font-mono uppercase tracking-widest mb-0.5">Type</p>
                <Badge variant={d.correlation_type === 'strong' ? 'success' : d.correlation_type === 'weak' ? 'mute' : 'default'}>
                  {d.is_likely_meme ? 'meme_discard' : d.correlation_type}
                </Badge>
              </div>
            </div>

            {/* Evidence */}
            {d.evidence.length > 0 && (
              <div className="bg-canvas-soft border border-hairline rounded-[4px] p-4">
                <p className="text-xs text-mute font-mono uppercase tracking-widest mb-2">Evidence</p>
                <ul className="space-y-1">
                  {d.evidence.map((e, i) => (
                    <li key={i} className="text-sm text-body flex items-start gap-2">
                      <span className="text-mute font-mono">→</span> {e}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Post refs */}
            {d.post_refs.length > 0 ? (
              <div className="border border-hairline rounded-[4px] overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-canvas-soft border-b border-hairline">
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Source</th>
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Board</th>
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Thread</th>
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Post</th>
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Name</th>
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Trip</th>
                      <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.post_refs.map((r, i) => (
                      <tr key={i} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft">
                        <td className="px-3 py-2 font-mono text-xs text-mute">{r.source}</td>
                        <td className="px-3 py-2 font-mono text-xs text-mute">/{r.board}/</td>
                        <td className="px-3 py-2 font-mono text-xs text-body">{r.thread_no}</td>
                        <td className="px-3 py-2 font-mono text-xs text-body">{r.post_no}</td>
                        <td className="px-3 py-2 text-xs text-ink">{r.name ?? '—'}</td>
                        <td className="px-3 py-2 font-mono text-xs text-mute">{r.trip ?? '—'}</td>
                        <td className="px-3 py-2 font-mono text-xs text-mute">{r.posted_at?.slice(0, 10) ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState message="No post references found" />
            )}
          </div>
        )
      })()}
    </div>
  )
}
