import React from 'react'

export interface Column<T> {
  key: string
  label: string
  render?: (row: T) => React.ReactNode
}

interface Props<T extends { id?: number }> {
  columns: Column<T>[]
  data: T[]
}

export default function DataTable<T extends { id?: number }>({ columns, data }: Props<T>) {
  if (data.length === 0) {
    return (
      <div className="text-slate-500 text-sm py-12 text-center border border-slate-700 rounded-lg">
        No data found
      </div>
    )
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-700">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left font-medium text-slate-300 whitespace-nowrap"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={row.id ?? i}
              className={`border-t border-slate-700 hover:bg-violet-600/10 transition-colors ${
                i % 2 === 0 ? 'bg-slate-900' : 'bg-slate-800'
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-2.5 text-slate-300 max-w-xs">
                  {col.render
                    ? col.render(row)
                    : <span className="truncate block">{String((row as Record<string, unknown>)[col.key] ?? '—')}</span>
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
