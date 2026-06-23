interface Props {
  label: string
  value: string | number
  sub?: string
}

export default function StatCard({ label, value, sub }: Props) {
  return (
    <div className="bg-canvas-soft border border-hairline rounded-[4px] px-5 py-4">
      <p className="text-xs text-mute font-mono uppercase tracking-widest mb-1">{label}</p>
      <p className="text-2xl font-medium text-ink leading-none">{value}</p>
      {sub && <p className="text-xs text-body mt-1">{sub}</p>}
    </div>
  )
}
