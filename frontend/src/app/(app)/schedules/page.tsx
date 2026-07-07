"use client";

import { Plus, Trash2 } from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  Badge,
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
import { describeCron, formatDateTime } from "@/lib/format";
import { Certificate, Company, PORTAL_LABELS, Portal, Schedule } from "@/lib/types";

const CRON_PRESETS = [
  { value: "0 8 * * *", label: "Todos os dias às 08:00" },
  { value: "0 8 * * 1", label: "Toda segunda-feira às 08:00" },
  { value: "0 6 1 * *", label: "Todo dia 1º do mês às 06:00" },
  { value: "custom", label: "Personalizado (cron)" },
];

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[] | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [preset, setPreset] = useState(CRON_PRESETS[0].value);
  const [form, setForm] = useState({
    name: "",
    company_id: "",
    certificate_id: "",
    portal: "nfse_nacional" as Portal,
    cron_expression: CRON_PRESETS[0].value,
    period_days: 7,
  });

  const load = useCallback(() => api<Schedule[]>("/schedules").then(setSchedules), []);

  useEffect(() => {
    load();
    api<Company[]>("/companies").then(setCompanies);
    api<Certificate[]>("/certificates").then(setCertificates);
  }, [load]);

  const companyName = (id: string) => companies.find((c) => c.id === id)?.name ?? "—";

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api("/schedules", {
        method: "POST",
        body: {
          name: form.name,
          company_id: form.company_id,
          certificate_id: form.certificate_id,
          portal: form.portal,
          cron_expression: form.cron_expression,
          filters: { period_days: form.period_days },
        },
      });
      setOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao salvar agendamento");
    } finally {
      setSaving(false);
    }
  }

  async function toggle(schedule: Schedule) {
    await api(`/schedules/${schedule.id}`, {
      method: "PATCH",
      body: { enabled: !schedule.enabled },
    });
    await load();
  }

  async function remove(schedule: Schedule) {
    if (!confirm(`Excluir o agendamento "${schedule.name}"?`)) return;
    await api(`/schedules/${schedule.id}`, { method: "DELETE" });
    await load();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Agendamentos</h1>
          <p className="text-sm text-ink-muted">Rotinas automáticas de download</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> Novo agendamento
        </Button>
      </div>

      {!schedules ? (
        <Spinner />
      ) : schedules.length === 0 ? (
        <EmptyState message="Nenhum agendamento. Crie rotinas como “todos os dias às 08:00”." />
      ) : (
        <Table headers={["Nome", "Empresa", "Portal", "Recorrência", "Próxima execução", "Status", ""]}>
          {schedules.map((schedule) => (
            <tr key={schedule.id} className="hover:bg-surface">
              <td className="px-4 py-3 font-medium">{schedule.name}</td>
              <td className="px-4 py-3">{companyName(schedule.company_id)}</td>
              <td className="px-4 py-3">{PORTAL_LABELS[schedule.portal]}</td>
              <td className="px-4 py-3 text-ink-muted">{describeCron(schedule.cron_expression)}</td>
              <td className="px-4 py-3 text-ink-muted">{formatDateTime(schedule.next_run_at)}</td>
              <td className="px-4 py-3">
                <button onClick={() => toggle(schedule)} title="Ativar/desativar">
                  <Badge tone={schedule.enabled ? "green" : "neutral"}>
                    {schedule.enabled ? "Ativo" : "Pausado"}
                  </Badge>
                </button>
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => remove(schedule)}
                  className="rounded-lg p-1.5 text-ink-faint hover:bg-surface hover:text-red-500"
                  title="Excluir"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </td>
            </tr>
          ))}
        </Table>
      )}

      <Modal title="Novo agendamento" open={open} onClose={() => setOpen(false)}>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Nome">
            <Input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Ex.: NFS-e diário — Empresa A"
              required
              autoFocus
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
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
          </div>
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
          <Field label="Recorrência">
            <Select
              value={preset}
              onChange={(event) => {
                setPreset(event.target.value);
                if (event.target.value !== "custom") {
                  setForm({ ...form, cron_expression: event.target.value });
                }
              }}
            >
              {CRON_PRESETS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </Field>
          {preset === "custom" && (
            <Field label="Expressão cron (min hora dia mês dia-da-semana)">
              <Input
                value={form.cron_expression}
                onChange={(event) => setForm({ ...form, cron_expression: event.target.value })}
                placeholder="0 8 * * *"
                required
              />
            </Field>
          )}
          <Field label="Janela de busca (últimos N dias)">
            <Input
              type="number"
              min={1}
              max={365}
              value={form.period_days}
              onChange={(event) => setForm({ ...form, period_days: Number(event.target.value) })}
              required
            />
          </Field>
          <ErrorNote message={error} />
          <Button type="submit" loading={saving} className="w-full">
            Salvar
          </Button>
        </form>
      </Modal>
    </div>
  );
}
