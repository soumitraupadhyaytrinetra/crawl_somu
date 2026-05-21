'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/competitors', label: 'Competitors' },
  { href: '/influencers', label: 'Influencers' },
  { href: '/events', label: 'Events' },
]

export default function NavSidebar() {
  const pathname = usePathname()
  return (
    <aside className="w-52 min-h-screen bg-slate-900 border-r border-slate-700 flex flex-col shrink-0">
      <div className="px-5 py-5 border-b border-slate-700">
        <div className="text-violet-400 font-bold text-lg leading-tight">MirrorFit</div>
        <div className="text-slate-500 text-xs tracking-widest uppercase mt-0.5">Intelligence</div>
      </div>
      <nav className="flex-1 py-3">
        {LINKS.map(({ href, label }) => {
          const active = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center px-5 py-2.5 text-sm transition-colors ${
                active
                  ? 'bg-violet-600/20 text-violet-300 border-r-2 border-violet-500'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
