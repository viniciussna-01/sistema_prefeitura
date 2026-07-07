"use client";

import {
  Building2,
  CalendarClock,
  FileKey,
  LayoutDashboard,
  ListChecks,
  LogOut,
  MonitorSmartphone,
  ScrollText,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme";
import { cn } from "@/components/ui";
import { setTokens } from "@/lib/api";

const links = [
  { href: "/dashboard", label: "Visão geral", icon: LayoutDashboard },
  { href: "/companies", label: "Empresas", icon: Building2 },
  { href: "/certificates", label: "Certificados", icon: FileKey },
  { href: "/agents", label: "Agentes", icon: MonitorSmartphone },
  { href: "/executions", label: "Execuções", icon: ListChecks },
  { href: "/schedules", label: "Agendamentos", icon: CalendarClock },
  { href: "/logs", label: "Auditoria", icon: ScrollText },
  { href: "/settings", label: "Configurações", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-edge bg-surface-raised">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">
          SP
        </div>
        <span className="text-sm font-semibold">Sistema Prefeitura</span>
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              pathname.startsWith(href)
                ? "bg-accent-soft font-medium text-accent"
                : "text-ink-muted hover:bg-surface hover:text-ink"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="flex items-center justify-between border-t border-edge px-4 py-3">
        <ThemeToggle />
        <button
          onClick={() => {
            setTokens(null);
            router.push("/login");
          }}
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-muted hover:bg-surface"
        >
          <LogOut className="h-4 w-4" />
          Sair
        </button>
      </div>
    </aside>
  );
}
