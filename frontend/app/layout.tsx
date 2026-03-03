import "./globals.css";

export const metadata = {
  title: "AI Inference Gateway",
  description: "Multi-backend AI inference platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-100 text-gray-900">
        <div className="min-h-screen">
          <header className="bg-black text-white px-6 py-4">
            <h1 className="text-lg font-semibold">
              AI Inference Gateway
            </h1>
          </header>
          <main className="p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}