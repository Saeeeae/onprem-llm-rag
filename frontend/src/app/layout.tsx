import './globals.css'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'On-Premise LLM',
  description: 'Department + Role RBAC RAG system',
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
