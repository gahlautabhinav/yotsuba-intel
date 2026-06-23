export default function Skeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-8 bg-canvas-soft border border-hairline rounded-[4px] animate-pulse"
          style={{ opacity: 1 - i * 0.15 }}
        />
      ))}
    </div>
  )
}
