'use client'
import { useState, useEffect, useRef } from 'react'
import { startScrape, pollJobStatus } from '@/lib/api'
import type { Section } from '@/lib/types'

type State = 'idle' | 'running' | 'done' | 'error'

interface Props {
  section: Section
  onDone?: () => void
}

export default function ScrapeButton({ section, onDone }: Props) {
  const [state, setState] = useState<State>('idle')
  const [message, setMessage] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const handleClick = async () => {
    setState('running')
    setMessage('Starting...')
    try {
      const { job_id } = await startScrape(section)
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollJobStatus(job_id)
          setMessage(status.message)
          if (status.status === 'done') {
            clearInterval(pollRef.current!)
            setState('done')
            onDone?.()
            setTimeout(() => { setState('idle'); setMessage('') }, 10000)
          } else if (status.status === 'error') {
            clearInterval(pollRef.current!)
            setState('error')
            setTimeout(() => { setState('idle'); setMessage('') }, 10000)
          }
        } catch {
          clearInterval(pollRef.current!)
          setState('error')
          setMessage('Polling failed')
          setTimeout(() => { setState('idle'); setMessage('') }, 10000)
        }
      }, 3000)
    } catch {
      setState('error')
      setMessage('Failed to start scrape')
      setTimeout(() => { setState('idle'); setMessage('') }, 10000)
    }
  }

  const label = {
    idle: `Scrape ${section.charAt(0).toUpperCase() + section.slice(1)}`,
    running: 'Scraping...',
    done: 'Done ✓',
    error: 'Failed',
  }[state]

  const btnClass = {
    idle: 'bg-violet-600 hover:bg-violet-700',
    running: 'bg-slate-600 cursor-not-allowed',
    done: 'bg-green-700',
    error: 'bg-red-700',
  }[state]

  return (
    <div className="flex items-center gap-3">
      {state === 'running' && message && (
        <span className="text-slate-400 text-sm truncate max-w-xs">{message}</span>
      )}
      <button
        onClick={handleClick}
        disabled={state === 'running'}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors ${btnClass}`}
      >
        {state === 'running' && (
          <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        )}
        {label}
      </button>
    </div>
  )
}
