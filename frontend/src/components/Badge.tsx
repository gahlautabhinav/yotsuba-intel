import React from 'react'

type Variant = 'default' | 'success' | 'warn' | 'error' | 'mute'

const STYLES: Record<Variant, string> = {
  default: 'bg-canvas-soft text-ink border-hairline',
  success: 'bg-canvas-soft text-body-strong border-hairline',
  warn:    'bg-canvas-soft text-body border-hairline',
  error:   'bg-canvas-soft text-mute border-hairline',
  mute:    'bg-canvas-soft text-mute border-hairline',
}

export default function Badge({ children, variant = 'default' }: { children: React.ReactNode; variant?: Variant }) {
  return (
    <span className={`inline-block px-1.5 py-0.5 text-xs font-mono rounded-[3px] border ${STYLES[variant]}`}>
      {children}
    </span>
  )
}
