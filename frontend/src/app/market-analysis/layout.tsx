import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Market Analysis | Crypto Analytics',
  description: 'Real-time cryptocurrency market analysis dashboard',
}

export default function MarketAnalysisLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 items-center px-4">
          <a className="flex items-center space-x-2" href="/">
            <span className="font-bold">Crypto Analytics</span>
          </a>
        </div>
      </header>
      <main className="container mx-auto flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  )
}