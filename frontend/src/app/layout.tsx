import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BoardRoom Agent",
  description: "Your Meetings. Understood. Remembered. Actioned.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gradient-to-b from-slate-900 via-slate-900 to-purple-900 min-h-screen text-white">
        {children}
      </body>
    </html>
  );
}