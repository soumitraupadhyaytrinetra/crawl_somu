import type { Metadata } from 'next'
import NavSidebar from '@/components/NavSidebar'
import './globals.css'

export const metadata: Metadata = {
  title: 'MirrorFit Intelligence',
  description: 'Competitive intelligence dashboard for MirrorFit AI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans bg-slate-950 text-white flex min-h-screen">
        <NavSidebar />
        <main className="flex-1 p-8 overflow-auto min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}
