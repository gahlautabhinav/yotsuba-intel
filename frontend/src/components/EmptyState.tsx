export default function EmptyState({ message, sub }: { message: string; sub?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="bg-canvas-soft border border-hairline rounded-[4px] px-8 py-6 max-w-sm">
        <p className="text-body-strong text-sm font-medium">{message}</p>
        {sub && <p className="text-mute text-xs mt-1">{sub}</p>}
      </div>
    </div>
  )
}
