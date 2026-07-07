"use client";

import { Ban } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { StatusBadge } from "@/components/status-badge";
import { Badge, Button, Card, EmptyState, Spinner, Table } from "@/components/ui";
import { api } from "@/lib/api";
import { formatBytes, formatDateTime } from "@/lib/format";
import { Download, Execution, ExecutionLog, PORTAL_LABELS } from "@/lib/types";

const levelTones = { info: "neutral", warning: "amber", error: "red" } as const;

export default function ExecutionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [execution, setExecution] = useState<Execution | null>(null);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [downloads, setDownloads] = useState<Download[]>([]);

  const isActive = (status?: string) =>
    status === "pending" || status === "dispatched" || status === "running";

  const load = useCallback(async () => {
    const [exec, execLogs, execDownloads] = await Promise.all([
      api<Execution>(`/executions/${id}`),
      api<ExecutionLog[]>(`/executions/${id}/logs`),
      api<Download[]>(`/executions/${id}/downloads`),
    ]);
    setExecution(exec);
    setLogs(execLogs);
    setDownloads(execDownloads);
    return exec;
  }, [id]);

  useEffect(() => {
    load();
    const interval = setInterval(async () => {
      const exec = await load();
      if (!isActive(exec.status)) clearInterval(interval);
    }, 4000);
    return () => clearInterval(interval);
  }, [load]);

  if (!execution) return <Spinner />;

  async function cancel() {
    await api(`/executions/${id}/cancel`, { method: "POST" });
    await load();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Execução</h1>
          <p className="text-sm text-ink-muted">
            {PORTAL_LABELS[execution.portal]} · {execution.filters.start_date} →{" "}
            {execution.filters.end_date} · tentativa {execution.attempt}/{execution.max_attempts}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={execution.status} />
          {isActive(execution.status) && (
            <Button variant="danger" onClick={cancel}>
              <Ban className="h-4 w-4" /> Cancelar
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-ink-muted">Início</p>
          <p className="mt-1 font-medium">{formatDateTime(execution.started_at)}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink-muted">Fim</p>
          <p className="mt-1 font-medium">{formatDateTime(execution.finished_at)}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink-muted">Arquivos baixados</p>
          <p className="mt-1 font-medium">{execution.files_count}</p>
        </Card>
      </div>

      {execution.error_message && (
        <Card className="border-red-300 dark:border-red-900">
          <p className="mb-1 text-sm font-medium text-red-500">Erro</p>
          <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-ink-muted">
            {execution.error_message}
          </pre>
        </Card>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Arquivos ({downloads.length})</h2>
        {downloads.length === 0 ? (
          <EmptyState message="Nenhum arquivo baixado ainda." />
        ) : (
          <Table headers={["Arquivo", "Tamanho", "Caminho local", "Baixado em"]}>
            {downloads.map((download) => (
              <tr key={download.id} className="hover:bg-surface">
                <td className="px-4 py-3 font-medium">{download.file_name}</td>
                <td className="px-4 py-3 text-ink-muted">{formatBytes(download.size_bytes)}</td>
                <td className="max-w-md truncate px-4 py-3 text-ink-muted" title={download.local_path}>
                  {download.local_path}
                </td>
                <td className="px-4 py-3 text-ink-muted">{formatDateTime(download.created_at)}</td>
              </tr>
            ))}
          </Table>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Logs</h2>
        {logs.length === 0 ? (
          <EmptyState message="Sem logs ainda." />
        ) : (
          <Card className="space-y-2 font-mono text-xs">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start gap-3">
                <span className="shrink-0 text-ink-faint">{formatDateTime(log.created_at)}</span>
                <Badge tone={levelTones[log.level]}>{log.level}</Badge>
                <span>{log.message}</span>
              </div>
            ))}
          </Card>
        )}
      </section>
    </div>
  );
}
