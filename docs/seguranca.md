# Segurança

## Princípios

1. **A chave privada do certificado nunca sai da máquina do cliente.**
   O backend conhece apenas metadados (thumbprint, titular, validade).
2. **Menor privilégio**: papéis `admin`/`operator`/`viewer`; endpoints de
   escrita exigem papel mínimo; recursos de outra organização retornam 404.
3. **Defesa em profundidade**: JWT curto + refresh, tokens de agente com
   hash, rate limit, auditoria imutável.

## Autenticação e sessões

- Usuários: JWT HS256 (`SECRET_KEY` forte obrigatória em produção), access
  de 30 min + refresh de 7 dias, senhas com bcrypt.
- Agentes: token opaco de 48 bytes exibido uma única vez; armazenado como
  SHA-256; matrícula via token de uso único com TTL de 15 min gerado por admin.
- CSRF: a API é consumida com `Authorization`/`X-Agent-Token` em header (não
  cookies), o que elimina o vetor clássico de CSRF; CORS restrito a
  `CORS_ORIGINS`.

## Transporte e dados

- HTTPS obrigatório em produção (terminação TLS no proxy/ingress; use HSTS).
- `ENCRYPTION_KEY` (Fernet) disponível em `core/security.py` para cifrar
  qualquer campo sensível futuro em repouso.
- Screenshots de falha ficam no volume do backend e são expurgados após 30
  dias (tarefa Celery).

## Rate limit e abuso

- Janela fixa por IP no Redis (`RATE_LIMIT_PER_MINUTE`, padrão 120/min).
- Falha aberta somente se o Redis cair (disponibilidade sobre bloqueio);
  ajuste para falha fechada se o seu modelo de ameaça exigir.

## Auditoria

Toda ação relevante gera `AuditLog` com organização, usuário/agente, ação,
entidade, detalhes e IP: login, registro, CRUD de empresas/usuários/
agendamentos, criação e cancelamento de execuções, matrícula de agentes.

## Consentimento do certificado

- O uso do certificado é sempre disparado por um usuário autenticado da
  organização dona do agente (execução manual) ou por agendamento criado
  por esse usuário.
- Em A3, o PIN do token é solicitado pelo middleware do fabricante na
  máquina do cliente — autorização explícita e local.

## Checklist de produção

- [ ] `SECRET_KEY` e `ENCRYPTION_KEY` fortes e fora do repositório
- [ ] `ENVIRONMENT=production` (desliga o create_all; use Alembic)
- [ ] TLS/HSTS no proxy; `CORS_ORIGINS` apenas com o domínio real
- [ ] Backup do PostgreSQL e retenção dos audit logs
- [ ] Rotação do token do agente em caso de comprometimento da máquina
      (basta deletar o agente no dashboard e matricular de novo)
