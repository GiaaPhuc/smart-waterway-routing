import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Smart Waterway Routing',
  description:
    'Intelligent route planning for vessels navigating the Mekong Delta waterway network.',
  keywords: ['waterway', 'routing', 'navigation', 'Mekong Delta', 'vessel', 'smart'],
  authors: [{ name: 'Smart Waterway Team' }],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased font-sans min-h-screen bg-gradient-to-br from-ocean-950 via-ocean-900 to-teal-950">
        {children}
      </body>
    </html>
  )
}
