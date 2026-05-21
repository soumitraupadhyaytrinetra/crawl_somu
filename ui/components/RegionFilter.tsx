'use client'
import type { Region } from '@/lib/types'

const REGIONS: { value: Region; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'india', label: 'India' },
  { value: 'uae', label: 'UAE' },
  { value: 'global', label: 'Global' },
]

interface Props {
  value: Region
  onChange: (r: Region) => void
}

export default function RegionFilter({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {REGIONS.map(({ value: v, label }) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            value === v
              ? 'bg-violet-600 text-white'
              : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-600'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
