"use client";

import {
  AlertTriangle,
  Building2,
  CalendarClock,
  Download,
  FileKey,
  ListChecks,
  MonitorSmartphone,
  Timer,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Card, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/format";
import { DashboardStats } from "@/lib/types";

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  alert,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  hint?: string;
  alert?: boolean;
}) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-ink-muted">{label}</p>
          <p className={`mt-1 text-2xl font-semibold ${alert ? "text-red-500" : ""}`}>{value}</p>
          {hint && <p className="mt-1 text-xs text-ink-faint">{hint}</p>}
        </div>
        <div className="rounded-lg bg-accent-soft p-2 text-accent">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    let active = true;
    const load = () => api<DashboardStats>("/dashboard/stats").then((s) => active && setStats(s));
    load();
    const interval = setInterval(load, 15000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  if (!stats) return <Spinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Visão geral</h1>
        <p className="text-sm text-ink-muted">Acompanhe suas automações em tempo real</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Building2} label="Empresas" value={stats.total_companies} />
        <StatCard
          icon={FileKey}
          label="Certificados ativos"
          value={stats.total_certificates}
          hint={
            stats.expiring_certificates > 0
              ? `${stats.expiring_certificates} vencendo em 30 dias`
              : undefined
          }
          alert={stats.expiring_certificates > 0}
        />
        <StatCard
          icon={MonitorSmartphone}
          label="Agentes online"
          value={`${stats.agents_online}/${stats.total_agents}`}
        />
        <StatCard
          icon={ListChecks}
          label="Execuções em andamento"
          value={stats.executions_running}
          hint={`${stats.executions_total} no total`}
        />
        <StatCard
          icon={Download}
          label="Arquivos baixados"
          value={stats.downloads_total}
          hint={`${stats.files_downloaded_7d} nos últimos 7 dias`}
        />
        <StatCard
          icon={Timer}
          label="Tempo médio de execução"
          value={formatDuration(stats.avg_execution_seconds)}
        />
        <StatCard
          icon={XCircle}
          label="Falhas (7 dias)"
          value={stats.executions_failed_7d}
          alert={stats.executions_failed_7d > 0}
        />
        <StatCard
          icon={CalendarClock}
          label="Próxima execução agendada"
          value={stats.next_scheduled_at ? formatDateTime(stats.next_scheduled_at) : "—"}
          hint={`Última: ${formatDateTime(stats.last_execution_at)}`}
        />
      </div>

      {stats.expiring_certificates > 0 && (
        <Card className="flex items-center gap-3 border-amber-300 dark:border-amber-800">
          <AlertTriangle className="h-5 w-5 shrink-0 text-amber-500" />
          <p className="text-sm">
            <strong>{stats.expiring_certificates}</strong> certificado(s) vencem nos próximos 30
            dias. Renove-os para não interromper as automações.
          </p>
        </Card>
      )}
    </div>
  );
}
