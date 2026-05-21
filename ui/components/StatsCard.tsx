import Link from 'next/link'

interface Props {
  label: string
  value: string | number
  href?: string
  sub?: string
}

export default function StatsCard({ label, value, href, sub }: Props) {
  const inner = (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-violet-500/60 transition-colors cursor-default">
      <div className="text-slate-400 text-sm mb-1">{label}</div>
      <div className="text-3xl font-bold text-white">{value}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </div>
  )
  return href ? <Link href={href} className="block">{inner}</Link> : inner
}
