import Sidebar from "@/components/Sidebar";
import { AuthProvider } from "@/lib/auth-context";

export default function ArticleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1">{children}</main>
      </div>
    </AuthProvider>
  );
}
