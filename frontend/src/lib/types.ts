export type Portal = "nfse_nacional" | "nfse_sp";
export type UserRole = "admin" | "operator" | "viewer";
export type ExecutionStatus =
  | "pending"
  | "dispatched"
  | "running"
  | "success"
  | "failed"
  | "cancelled";

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Company {
  id: string;
  name: string;
  cnpj: string;
  municipal_registration: string | null;
  default_portal: Portal;
  is_active: boolean;
  created_at: string;
}

export interface Certificate {
  id: string;
  agent_id: string;
  thumbprint: string;
  subject: string;
  issuer: string;
  cnpj_cpf: string | null;
  certificate_type: "A1" | "A3";
  not_before: string | null;
  not_after: string | null;
  is_active: boolean;
}

export interface Agent {
  id: string;
  name: string;
  machine_id: string;
  version: string;
  last_seen_at: string | null;
  downloads_dir: string | null;
  status: "online" | "offline";
}

export interface Execution {
  id: string;
  company_id: string;
  certificate_id: string | null;
  agent_id: string | null;
  schedule_id: string | null;
  portal: Portal;
  status: ExecutionStatus;
  filters: { start_date?: string; end_date?: string; extra?: Record<string, unknown> };
  attempt: number;
  max_attempts: number;
  started_at: string | null;
  finished_at: string | null;
  files_count: number;
  error_message: string | null;
  cancel_requested: boolean;
  created_at: string;
}

export interface ExecutionLog {
  id: string;
  level: "info" | "warning" | "error";
  message: string;
  screenshot_path: string | null;
  created_at: string;
}

export interface Download {
  id: string;
  execution_id: string;
  file_name: string;
  original_name: string | null;
  local_path: string;
  size_bytes: number;
  sha256: string | null;
  document_id: string | null;
  created_at: string;
}

export interface Schedule {
  id: string;
  name: string;
  company_id: string;
  certificate_id: string;
  portal: Portal;
  cron_expression: string;
  filters: { period_days?: number };
  enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_companies: number;
  total_certificates: number;
  total_agents: number;
  agents_online: number;
  last_execution_at: string | null;
  next_scheduled_at: string | null;
  executions_total: number;
  executions_running: number;
  executions_failed_7d: number;
  downloads_total: number;
  files_downloaded_7d: number;
  avg_execution_seconds: number | null;
  expiring_certificates: number;
}

export interface AuditLog {
  id: string;
  action: string;
  entity: string | null;
  entity_id: string | null;
  detail: Record<string, unknown>;
  ip_address: string | null;
  user_id: string | null;
  agent_id: string | null;
  created_at: string;
}

export const PORTAL_LABELS: Record<Portal, string> = {
  nfse_nacional: "NFS-e Nacional",
  nfse_sp: "NFS-e São Paulo",
};

export const STATUS_LABELS: Record<ExecutionStatus, string> = {
  pending: "Na fila",
  dispatched: "Enviado ao agente",
  running: "Executando",
  success: "Concluído",
  failed: "Falhou",
  cancelled: "Cancelado",
};
