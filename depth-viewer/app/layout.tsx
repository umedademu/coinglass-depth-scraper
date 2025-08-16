export const metadata = {
  title: 'Depth Viewer',
  description: 'Test page for depth-viewer project',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  )
}