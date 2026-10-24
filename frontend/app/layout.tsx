import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import Script from "next/script";
import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["500"],
});

export const metadata: Metadata = {
  title: "Student Retention System",
  description:
    "Predicts student term-over-term persistence (explainability, API, dashboard) and automates admissions-review eligibility checks (transcript extraction, multi-agent validation, handbook rules, human-in-the-loop decisions). Portfolio project, synthetic data only.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <head>
        {/* beforeInteractive: must execute before the client bundle evaluates
            lib/api.ts (which reads window.__ENV__ once at module-load time) —
            afterInteractive would run too late, after hydration already read
            an unset window.__ENV__. */}
        <Script src="/env.js" strategy="beforeInteractive" />
      </head>
      <body className="min-h-full flex flex-col font-sans">
        <Navbar />
        <div className="flex-1">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
