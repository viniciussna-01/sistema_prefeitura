"use client";

import { KeyRound } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Button, Card, EmptyState, Spinner, Table } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Agent } from "@/lib/types";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[] | null>(null);
  const [enrollmentToken, setEnrollmentToken] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const load = () => api<Agent[]>("/agents").then(setAgents);
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  async function generateToken() {
    setGenerating(true);
    try {
      const result = await api<{ enrollment_token: string }>("/agents/enrollment-token", {
        method: "POST",
      });
      setEnrollmentToken(result.enrollment_token);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Agentes desktop</h1>
          <p className="text-sm text-ink-muted">
            Aplicativos instalados nas máquinas dos clientes que executam as automações
          </p>
        </div>
        <Button onClick={generateToken} loading={generating}>
          <KeyRound className="h-4 w-4" /> Gerar token de matrícula
        </Button>
      </div>

      {enrollmentToken && (
        <Card className="space-y-2">
          <p className="text-sm font-medium">Token gerado (válido por 15 minutos):</p>
          <code className="block break-all rounded-lg bg-surface p-3 text-xs">
            {enrollmentToken}
          </code>
          <p className="text-xs text-ink-faint">
            Na máquina do cliente, rode:{" "}
            <code>sistema-agent --enroll {"<TOKEN>"} --api {"<URL_DO_BACKEND>"}</code>
          </p>
        </Card>
      )}

      {!agents ? (
        <Spinner />
      ) : agents.length === 0 ? (
        <EmptyState message="Nenhum agente matriculado. Gere um token e instale o agente na máquina do cliente." />
      ) : (
        <Table headers={["Nome", "Status", "Versão", "Último contato", "Pasta de downloads"]}>
          {agents.map((agent) => (
            <tr key={agent.id} className="hover:bg-surface">
              <td className="px-4 py-3 font-medium">{agent.name}</td>
              <td className="px-4 py-3">
                <Badge tone={agent.status === "online" ? "green" : "neutral"}>
                  {agent.status === "online" ? "Online" : "Offline"}
                </Badge>
              </td>
              <td className="px-4 py-3 text-ink-muted">v{agent.version}</td>
              <td className="px-4 py-3 text-ink-muted">{formatDateTime(agent.last_seen_at)}</td>
              <td className="max-w-xs truncate px-4 py-3 text-ink-muted" title={agent.downloads_dir ?? ""}>
                {agent.downloads_dir ?? "—"}
              </td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}
