import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gen-Retry 轨迹档案",
  description:
    "用真实 canonical trajectories 对比图像 Retry 前后结果、Prompt 变化与 verifier 反馈。",
  icons: {
    icon: "/favicon.png",
    shortcut: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

