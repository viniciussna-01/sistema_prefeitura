# API — Referência rápida

Documentação interativa completa (OpenAPI/Swagger): `http://localhost:8000/docs`

Base: `/api/v1` · Autenticação de usuários: `Authorization: Bearer <JWT>` ·
Autenticação do agente: header `X-Agent-Token`.

## Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cria organização + primeiro admin; retorna tokens |
| POST | `/auth/login` | Login com e-mail/senha; retorna access + refresh |
| POST | `/auth/refresh` | Renova o par de tokens |
| GET | `/auth/me` | Dados do usuário autenticado |

Access token expira em 30 min (configurável); refresh em 7 dias.

## Usuários e permissões

| Método | Rota | Papel mínimo |
|---|---|---|
| GET | `/users` | viewer |
| POST | `/users` | admin |
| PATCH | `/users/{id}` | admin |

Papéis: `admin` (tudo), `operator` (opera empresas/execuções/agendamentos),
`viewer` (somente leitura). Menor privilégio por padrão.

## Empresas

CRUD em `/companies` (POST/PATCH/DELETE exigem `operator`).
CNPJ validado (11 ou 14 dígitos).

## Certificados (somente metadados)

| Método | Rota | Quem usa |
|---|---|---|
| GET | `/certificates?only_active=true` | dashboard |
| PUT | `/agents/me/certificates` | agente (sincronização) |

## Agentes

| Método | Rota | Quem usa |
|---|---|---|
| GET | `/agents` | dashboard (status online/offline) |
| POST | `/agents/enrollment-token` | admin — token de uso único, 15 min |
| POST | `/agents/enroll` | agente — troca token de matrícula por token permanente |
| POST | `/agents/me/heartbeat` | agente — a cada 30 s |
| GET | `/agents/me/jobs` | agente — coleta execuções pendentes (vira `dispatched`) |
| PATCH | `/agents/me/jobs/{execution_id}` | agente — status, logs, screenshots, downloads |
| GET | `/agents/version` | agente — auto-update |

## Execuções

| Método | Rota | Descrição |
|---|---|---|
| GET | `/executions?status_filter=&company_id=&limit=&offset=` | histórico |
| POST | `/executions` | inicia execução manual (empresa, certificado, portal, datas) |
| GET | `/executions/{id}` | detalhe |
| POST | `/executions/{id}/cancel` | cancela (propagado ao agente) |
| GET | `/executions/{id}/logs` | logs com nível e screenshot |
| GET | `/executions/{id}/downloads` | arquivos baixados (metadados) |

## Agendamentos

CRUD em `/schedules`. Campos: `cron_expression` (5 campos, validada),
`filters.period_days` (janela relativa de datas), `enabled`.

## Dashboard e auditoria

- `GET /dashboard/stats` — todos os contadores do painel.
- `GET /audit-logs?action=&limit=&offset=` — trilha de auditoria da organização.
- `GET /downloads` — histórico global de arquivos.

## Códigos de erro

- `401` token ausente/inválido/expirado · `403` papel insuficiente
- `404` recurso de outra organização é indistinguível de inexistente
- `409` conflito (e-mail duplicado) · `422` validação · `429` rate limit
