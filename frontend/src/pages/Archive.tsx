import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api, ArchiveSearchReq } from '../api/client'
import EmptyState from '../components/EmptyState'

type SearchType = 'trip' | 'md5' | 'name'
const SOURCES = ['4plebs', 'desuarchive', 'warosu']

export default function Archive() {
  const [type, setType] = useState<SearchType>('trip')
  const [value, setValue] = useState('')
  const [board, setBoard] = useState('')
  const [sources, setSources] = useState<string[]>(SOURCES)

  const search = useMutation({
    mutationFn: () => {
      const req: ArchiveSearchReq = { sources: sources.length < 3 ? sources : undefined }
      if (type === 'trip') req.trip = value
      else if (type === 'md5') req.md5 = value
      else { req.name = value; if (board) req.board = board }
      return api.archiveSearch(req)
    },
  })

  const toggleSource = (s: string) =>
    setSources(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-medium text-ink">Archive Search</h1>
        <p className="text-xs text-mute mt-0.5">Search 4plebs, desuarchive, warosu</p>
      </div>

      <div className="bg-canvas-soft border border-hairline rounded-[4px] p-4 space-y-3">
        {/* Type selector */}
        <div className="flex gap-3">
          {(['trip','md5','name'] as SearchType[]).map(t => (
            <label key={t} className="flex items-center gap-1.5 cursor-pointer">
              <input type="radio" name="type" checked={type === t} onChange={() => setType(t)} className="accent-ink" />
              <span className="text-sm text-body font-mono">{t}</span>
            </label>
          ))}
        </div>

        {/* Input */}
        <input
          className="w-full bg-canvas border border-hairline rounded-[3px] px-3 py-1.5 text-sm text-ink placeholder-mute font-mono focus:outline-none focus:border-body-strong"
          placeholder={type === 'trip' ? '!ABC123XYZ' : type === 'md5' ? 'base64==' : 'poster name'}
          value={value}
          onChange={e => setValue(e.target.value)}
        />

        {/* Board (only for name) */}
        {type === 'name' && (
          <input
            className="w-full bg-canvas border border-hairline rounded-[3px] px-3 py-1.5 text-sm text-ink placeholder-mute font-mono focus:outline-none focus:border-body-strong"
            placeholder="board filter (e.g. g)"
            value={board}
            onChange={e => setBoard(e.target.value)}
          />
        )}

        {/* Sources */}
        <div className="flex gap-3">
          {SOURCES.map(s => (
            <label key={s} className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" checked={sources.includes(s)} onChange={() => toggleSource(s)} className="accent-ink" />
              <span className="text-xs text-body font-mono">{s}</span>
            </label>
          ))}
        </div>

        <button
          onClick={() => value && search.mutate()}
          disabled={!value || search.isPending || sources.length === 0}
          className="bg-primary text-on-primary rounded-[3px] px-4 py-1.5 text-sm font-medium disabled:opacity-40"
        >
          {search.isPending ? 'Searching…' : 'Search'}
        </button>
      </div>

      {search.isError && <p className="text-sm text-mute">Search failed. Check API is running.</p>}

      {search.data && search.data.length === 0 && (
        <EmptyState message="No results found" sub="Try a different query or more archive sources." />
      )}

      {search.data && search.data.length > 0 && (
        <div>
          <p className="text-xs text-mute font-mono mb-2">{search.data.length} result(s)</p>
          <div className="border border-hairline rounded-[4px] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-canvas-soft border-b border-hairline">
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Source</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Board</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Post#</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Name</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Trip</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Date</th>
                  <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Body</th>
                </tr>
              </thead>
              <tbody>
                {search.data.map((r, i) => (
                  <tr key={i} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft">
                    <td className="px-3 py-2 font-mono text-xs text-mute">{r.source}</td>
                    <td className="px-3 py-2 font-mono text-xs text-mute">/{r.board}/</td>
                    <td className="px-3 py-2 font-mono text-xs text-body">{r.post_no}</td>
                    <td className="px-3 py-2 text-xs text-ink">{r.name ?? '—'}</td>
                    <td className="px-3 py-2 font-mono text-xs text-mute">{r.trip ?? '—'}</td>
                    <td className="px-3 py-2 font-mono text-xs text-mute">{r.posted_at?.slice(0,10) ?? '—'}</td>
                    <td className="px-3 py-2 text-xs text-body max-w-xs truncate">
                      {r.archive_url
                        ? <a href={r.archive_url} target="_blank" rel="noopener noreferrer" className="hover:text-ink">{r.body_text?.slice(0, 60) ?? '→ archive'}</a>
                        : r.body_text?.slice(0, 60)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
