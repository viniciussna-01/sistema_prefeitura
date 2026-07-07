"use client";

import { Play } from "lucide-react";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { StatusBadge } from "@/components/status-badge";
import {
  Button,
  EmptyState,
  ErrorNote,
  Field,
  Input,
  Modal,
  Select,
  Spinner,
  Table,
} from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Certificate, Company, Execution, PORTAL_LABELS, Portal } from "@/lib/types";

export default function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[] | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    company_id: "",
    certificate_id: "",
    portal: "nfse_nacional" as Portal,
    start_date: "",
    end_date: "",
  });

  const load = useCallback(() => api<Execution[]>("/executions").then(setExecutions), []);

  useEffect(() => {
    load();
    api<Company[]>("/companies").then(setCompanies);
    api<Certificate[]>("/certificates").then(setCertificates);
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  const companyName = (id: string) => companies.find((c) => c.id === id)?.name ?? "—";

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api("/executions", {
        method: "POST",
        body: {
          company_id: form.company_id,
          certificate_id: form.certificate_id,
          portal: form.portal,
          filters: { start_date: form.start_date, end_date: form.end_date },
        },
      });
      setOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao iniciar execução");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Execuções</h1>
          <p className="text-sm text-ink-muted">Histórico e acompanhamento das automações</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Play className="h-4 w-4" /> Nova execução
        </Button>
      </div>

      {!executions ? (
        <Spinner />
      ) : executions.length === 0 ? (
        <EmptyState message="Nenhuma execução ainda. Inicie a primeira automação." />
      ) : (
        <Table headers={["Empresa", "Portal", "Período", "Status", "Arquivos", "Criada em"]}>
          {executions.map((execution) => (
            <tr key={execution.id} className="hover:bg-surface">
              <td className="px-4 py-3">
                <Link
                  href={`/executions/${execution.id}`}
                  className="font-medium text-accent hover:underline"
                >
                  {companyName(execution.company_id)}
                </Link>
              </td>
              <td className="px-4 py-3">{PORTAL_LABELS[execution.portal]}</td>
              <td className="px-4 py-3 text-ink-muted">
                {execution.filters.start_date} → {execution.filters.end_date}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={execution.status} />
              </td>
              <td className="px-4 py-3 text-ink-muted">{execution.files_count}</td>
              <td className="px-4 py-3 text-ink-muted">{formatDateTime(execution.created_at)}</td>
            </tr>
          ))}
        </Table>
      )}

      <Modal title="Nova execução" open={open} onClose={() => setOpen(false)}>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Empresa">
            <Select
              value={form.company_id}
              onChange={(event) => setForm({ ...form, company_id: event.target.value })}
              required
            >
              <option value="">Selecione…</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Certificado digital">
            <Select
              value={form.certificate_id}
              onChange={(event) => setForm({ ...form, certificate_id: event.target.value })}
              required
            >
              <option value="">Selecione…</option>
              {certificates.map((certificate) => (
                <option key={certificate.id} value={certificate.id}>
                  {certificate.subject} ({certificate.certificate_type})
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Portal">
            <Select
              value={form.portal}
              onChange={(event) => setForm({ ...form, portal: event.target.value as Portal })}
            >
              {Object.entries(PORTAL_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Data inicial">
              <Input
                type="date"
                value={form.start_date}
                onChange={(event) => setForm({ ...form, start_date: event.target.value })}
                required
              />
            </Field>
            <Field label="Data final">
              <Input
                type="date"
                value={form.end_date}
                onChange={(event) => setForm({ ...form, end_date: event.target.value })}
                required
              />
            </Field>
          </div>
          <ErrorNote message={error} />
          <Button type="submit" loading={saving} className="w-full">
            Iniciar execução
          </Button>
        </form>
      </Modal>
    </div>
  );
}
