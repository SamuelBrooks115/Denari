import { Link, Outlet, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const aboutLinks = [
  { href: "/about/mission", label: "Mission" },
  { href: "/about/strategy", label: "Our Strategy" },
  { href: "/about/focus", label: "Focus" },
  { href: "/about/leadership", label: "Leadership" },
  { href: "/about/news", label: "News" },
  { href: "/about/contact", label: "Contact Us" },
];

export default function AboutIndex() {
  const location = useLocation();
  const isRootAbout = location.pathname === "/about";

  if (isRootAbout) {
    return (
      <div className="min-h-screen bg-gradient-hero">
        <div className="container mx-auto px-4 py-16">
          <h1 className="text-5xl font-bold text-white text-center mb-8">About Denari</h1>
          <p className="text-xl text-denari-4 text-center max-w-3xl mx-auto mb-12">
            Learn more about our mission, team, and approach to financial modeling
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {aboutLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white/20 transition-all hover:scale-105"
              >
                <h3 className="text-xl font-semibold text-white">{link.label}</h3>
              </Link>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-denari-2 text-white p-6 space-y-2">
        <h2 className="text-xl font-bold mb-6">About Denari</h2>
        {aboutLinks.map((link) => (
          <Link
            key={link.href}
            to={link.href}
            className={cn(
              "block px-4 py-2 rounded-lg transition-colors",
              location.pathname === link.href
                ? "bg-primary text-white font-medium"
                : "text-denari-4 hover:bg-denari-1 hover:text-white"
            )}
          >
            {link.label}
          </Link>
        ))}
      </aside>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
