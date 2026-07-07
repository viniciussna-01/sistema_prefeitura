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
import { Company, PORTAL_LABELS, Portal } from "@/lib/types";

const emptyForm = {
  name: "",
  cnpj: "",
  municipal_registration: "",
  default_portal: "nfse_nacional" as Portal,
};

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[] | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => api<Company[]>("/companies").then(setCompanies), []);
  useEffect(() => {
    load();
  }, [load]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api("/companies", {
        method: "POST",
        body: { ...form, municipal_registration: form.municipal_registration || null },
      });
      setOpen(false);
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(company: Company) {
    if (!confirm(`Excluir a empresa "${company.name}"?`)) return;
    await api(`/companies/${company.id}`, { method: "DELETE" });
    await load();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Empresas</h1>
          <p className="text-sm text-ink-muted">Empresas monitoradas pelas automações</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> Nova empresa
        </Button>
      </div>

      {!companies ? (
        <Spinner />
      ) : companies.length === 0 ? (
        <EmptyState message="Nenhuma empresa cadastrada ainda. Crie a primeira para começar." />
      ) : (
        <Table headers={["Nome", "CNPJ", "Portal padrão", "Status", ""]}>
          {companies.map((company) => (
            <tr key={company.id} className="hover:bg-surface">
              <td className="px-4 py-3 font-medium">{company.name}</td>
              <td className="px-4 py-3 text-ink-muted">{company.cnpj}</td>
              <td className="px-4 py-3">{PORTAL_LABELS[company.default_portal]}</td>
              <td className="px-4 py-3">
                <Badge tone={company.is_active ? "green" : "neutral"}>
                  {company.is_active ? "Ativa" : "Inativa"}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => onDelete(company)}
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

      <Modal title="Nova empresa" open={open} onClose={() => setOpen(false)}>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Nome">
            <Input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              required
              autoFocus
            />
          </Field>
          <Field label="CNPJ">
            <Input
              value={form.cnpj}
              onChange={(event) => setForm({ ...form, cnpj: event.target.value })}
              placeholder="00.000.000/0000-00"
              required
            />
          </Field>
          <Field label="Inscrição municipal (opcional)">
            <Input
              value={form.municipal_registration}
              onChange={(event) =>
                setForm({ ...form, municipal_registration: event.target.value })
              }
            />
          </Field>
          <Field label="Portal padrão">
            <Select
              value={form.default_portal}
              onChange={(event) =>
                setForm({ ...form, default_portal: event.target.value as Portal })
              }
            >
              {Object.entries(PORTAL_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
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
