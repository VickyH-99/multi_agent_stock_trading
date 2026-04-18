import type { Metadata } from 'next';
import './globals.css';
import { Toaster } from 'react-hot-toast';
import Providers from './providers';

export const metadata: Metadata = {
  title: 'A股实时分析平台',
  description: '专业A股实时分析，主力资金流向，涨停板监控，技术指标',
  icons: { icon: '/favicon.svg' },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-dark-bg text-text-primary min-h-screen antialiased">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#161b22',
                color: '#e6edf3',
                border: '1px solid #30363d',
                fontSize: '13px',
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
