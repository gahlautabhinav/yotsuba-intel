import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Skeleton from '../components/Skeleton'
import EmptyState from '../components/EmptyState'

export default function Images() {
  const navigate = useNavigate()
  const threads = useQuery({ queryKey: ['threads'], queryFn: api.listThreads })

  const threadIds = threads.data?.map(t => t.id) ?? []

  // Fetch posts for all threads using Promise.all — avoids calling useQuery inside .map()
  const allPostsQuery = useQuery({
    queryKey: ['all-posts-with-files', threadIds],
    queryFn: async () => {
      const results = await Promise.all(threadIds.map(tid => api.getThreadPosts(tid)))
      return results.flat().filter(p => p.has_file && p.file_md5)
    },
    enabled: threadIds.length > 0,
  })

  const allPosts = allPostsQuery.data ?? []
  const loading = threads.isLoading || allPostsQuery.isLoading

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-medium text-ink">Images</h1>
        <p className="text-xs text-mute mt-0.5">Posts with file attachments — click MD5 to correlate</p>
      </div>
      {loading && <Skeleton rows={8} />}
      {!loading && allPosts.length === 0 && (
        <EmptyState message="No image posts found" sub="Scrape threads that have file attachments." />
      )}
      {!loading && allPosts.length > 0 && (
        <div className="border border-hairline rounded-[4px] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-canvas-soft border-b border-hairline">
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Post#</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Name / Trip</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Ext</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">MD5</th>
                <th className="text-left px-3 py-2 text-xs text-mute font-mono uppercase">Date</th>
              </tr>
            </thead>
            <tbody>
              {allPosts.map(p => (
                <tr key={p.id} className="border-b border-hairline last:border-b-0 hover:bg-canvas-soft">
                  <td className="px-3 py-2 font-mono text-xs text-body">#{p.post_no}</td>
                  <td className="px-3 py-2 text-xs text-ink">
                    {p.name}
                    {p.trip && <span className="font-mono text-mute ml-1">{p.trip}</span>}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-mute">{p.file_ext ?? '—'}</td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => navigate('/correlate', { state: { md5: p.file_md5 } })}
                      className="font-mono text-xs text-body-strong hover:text-ink truncate max-w-[160px] block text-left"
                      title={p.file_md5 ?? ''}
                    >
                      {p.file_md5?.slice(0, 16)}…
                    </button>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-mute">{p.posted_at?.slice(0,10) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
