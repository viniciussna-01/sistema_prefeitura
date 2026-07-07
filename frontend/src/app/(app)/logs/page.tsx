"use client";

import { useEffect, useState } from "react";

import { Badge, EmptyState, Spinner, Table } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { AuditLog } from "@/lib/types";

export default function LogsPage() {
  const [logs, setLogs] = useState<AuditLog[] | null>(null);

  useEffect(() => {
    api<AuditLog[]>("/audit-logs").then(setLogs);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Logs de auditoria</h1>
        <p className="text-sm text-ink-muted">
          Registro imutável de logins, alterações e execuções
        </p>
      </div>

      {!logs ? (
        <Spinner />
      ) : logs.length === 0 ? (
        <EmptyState message="Nenhum registro de auditoria ainda." />
      ) : (
        <Table headers={["Ação", "Entidade", "Detalhes", "IP", "Data/hora"]}>
          {logs.map((log) => (
            <tr key={log.id} className="hover:bg-surface">
              <td className="px-4 py-3">
                <Badge tone="blue">{log.action}</Badge>
              </td>
              <td className="px-4 py-3 text-ink-muted">{log.entity ?? "—"}</td>
              <td className="max-w-md truncate px-4 py-3 font-mono text-xs text-ink-muted">
                {Object.keys(log.detail).length ? JSON.stringify(log.detail) : "—"}
              </td>
              <td className="px-4 py-3 text-ink-muted">{log.ip_address ?? "—"}</td>
              <td className="px-4 py-3 text-ink-muted">{formatDateTime(log.created_at)}</td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}
