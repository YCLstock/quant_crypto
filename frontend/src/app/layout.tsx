import './globals.css' // 加入全域樣式匯入
import { Metadata } from 'next'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'Crypto Analytics',
  description: 'Cryptocurrency Market Analysis Platform',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}