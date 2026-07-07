"use client";

import { Plus } from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  Badge,
  Button,
  Card,
  ErrorNote,
  Field,
  Input,
  Modal,
  Select,
  Spinner,
  Table,
} from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { User, UserRole } from "@/lib/types";

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrador",
  operator: "Operador",
  viewer: "Somente leitura",
};

export default function SettingsPage() {
  const [me, setMe] = useState<User | null>(null);
  const [users, setUsers] = useState<User[] | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "operator" as UserRole,
  });

  const load = useCallback(() => api<User[]>("/users").then(setUsers), []);

  useEffect(() => {
    api<User>("/auth/me").then(setMe);
    load();
  }, [load]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api("/users", { method: "POST", body: form });
      setOpen(false);
      setForm({ full_name: "", email: "", password: "", role: "operator" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao criar usuário");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(user: User) {
    await api(`/users/${user.id}`, { method: "PATCH", body: { is_active: !user.is_active } });
    await load();
  }

  const isAdmin = me?.role === "admin";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Configurações</h1>
        <p className="text-sm text-ink-muted">Sua conta e os usuários da organização</p>
      </div>

      {me && (
        <Card>
          <p className="text-sm text-ink-muted">Conectado como</p>
          <p className="mt-1 font-medium">
            {me.full_name} · {me.email} · <Badge tone="blue">{ROLE_LABELS[me.role]}</Badge>
          </p>
        </Card>
      )}

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Usuários</h2>
        {isAdmin && (
          <Button onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" /> Novo usuário
          </Button>
        )}
      </div>

      {!users ? (
        <Spinner />
      ) : (
        <Table headers={["Nome", "E-mail", "Papel", "Status", ""]}>
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-surface">
              <td className="px-4 py-3 font-medium">{user.full_name}</td>
              <td className="px-4 py-3 text-ink-muted">{user.email}</td>
              <td className="px-4 py-3">{ROLE_LABELS[user.role]}</td>
              <td className="px-4 py-3">
                <Badge tone={user.is_active ? "green" : "neutral"}>
                  {user.is_active ? "Ativo" : "Desativado"}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right">
                {isAdmin && user.id !== me?.id && (
                  <Button variant="secondary" onClick={() => toggleActive(user)}>
                    {user.is_active ? "Desativar" : "Reativar"}
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}

      <Modal title="Novo usuário" open={open} onClose={() => setOpen(false)}>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Nome completo">
            <Input
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              required
              autoFocus
            />
          </Field>
          <Field label="E-mail">
            <Input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
            />
          </Field>
          <Field label="Senha (mínimo 8 caracteres)">
            <Input
              type="password"
              minLength={8}
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
            />
          </Field>
          <Field label="Papel">
            <Select
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
            >
              {Object.entries(ROLE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
          <ErrorNote message={error} />
          <Button type="submit" loading={saving} className="w-full">
            Criar usuário
          </Button>
        </form>
      </Modal>
    </div>
  );
}
