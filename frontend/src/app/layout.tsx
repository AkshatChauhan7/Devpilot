import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./styles/globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DevPilot - Autonomous AI Development Assistant",
  description: "Automate code generation, bug detection, testing, and deployment with AI-powered agents",
  keywords: ["AI", "development", "automation", "code generation", "bug detection", "testing"],
  authors: [{ name: "DevPilot" }],
  creator: "DevPilot",
  publisher: "DevPilot",
  robots: "index, follow",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://devpilot.ai",
    siteName: "DevPilot",
    title: "DevPilot - Autonomous AI Development Assistant",
    description: "Automate code generation, bug detection, testing, and deployment with AI-powered agents",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "DevPilot",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "DevPilot",
    description: "Autonomous AI Development Assistant",
    images: ["/og-image.png"],
  },
  verification: {
    google: "google-site-verification-code",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased bg-background text-foreground`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}