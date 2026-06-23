import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, Hash, Archive, Image, GitFork
} from 'lucide-react'

const NAV = [
  { to: '/dashboard',  icon: LayoutDashboard, label: 'Dashboard'  },
  { to: '/threads',    icon: MessageSquare,   label: 'Threads'    },
  { to: '/tripcodes',  icon: Hash,            label: 'Tripcodes'  },
  { to: '/correlate',  icon: GitFork,         label: 'Correlate'  },
  { to: '/archive',    icon: Archive,         label: 'Archive'    },
  { to: '/images',     icon: Image,           label: 'Images'     },
]

export default function Sidebar() {
  return (
    <aside className="fixed top-0 left-0 h-full w-[220px] bg-canvas border-r border-hairline flex flex-col z-10">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-hairline">
        <span className="font-mono text-sm text-ink tracking-tight">yotsuba-intel</span>
        <span className="font-serif italic text-mute text-xs ml-1">v1</span>
      </div>
      {/* Nav */}
      <nav className="flex-1 py-3 px-2">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-2.5 py-2 text-sm font-medium rounded-[3px] mb-0.5 transition-colors ${
                isActive
                  ? 'bg-canvas-soft text-ink'
                  : 'text-body hover:text-ink hover:bg-canvas-soft'
              }`
            }
          >
            <Icon size={15} strokeWidth={1.5} />
            {label}
          </NavLink>
        ))}
      </nav>
      {/* Footer */}
      <div className="px-4 py-3 border-t border-hairline">
        <p className="text-xs text-mute font-mono">4chan OSINT</p>
      </div>
    </aside>
  )
}
