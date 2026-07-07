# Fluxos

## Fluxo principal: execução manual

```mermaid
sequenceDiagram
    actor U as Usuário
    participant FE as Frontend
    participant API as Backend
    participant AG as Agente Desktop
    participant BR as Navegador (Edge/Chrome)
    participant P as Portal NFS-e

    U->>FE: Seleciona empresa, certificado,<br/>datas e filtros
    FE->>API: POST /executions (JWT)
    API-->>FE: execução "pending" (vinculada ao agente do certificado)

    loop polling a cada 10s
        AG->>API: GET /agents/me/jobs (X-Agent-Token)
    end
    API-->>AG: job {portal, empresa, thumbprint, filtros}

    AG->>AG: grava política AutoSelectCertificateForUrls (HKCU)
    AG->>BR: abre navegador (Playwright)
    BR->>P: TLS mútuo com certificado do repositório do SO
    AG->>API: PATCH job → running + log "autenticado"

    AG->>BR: aplica filtros de período
    AG->>BR: lista documentos (paginação)
    loop cada documento
        AG->>BR: download individual
        AG->>AG: organiza em <pasta>/<Empresa>/,<br/>renomeia se houver colisão
        AG->>API: PATCH job → metadados do arquivo (nome, hash, tamanho)
        API-->>AG: {cancel_requested} — interrompe se true
    end
    AG->>AG: remove política do registro
    AG->>API: PATCH job → success
    FE->>API: polling do status
    API-->>FE: success + arquivos + logs
```

## Fluxo de falha

1. Exceção durante a automação → agente captura **screenshot da página**.
2. Screenshot (base64) + stack trace são enviados no `PATCH` do job.
3. Backend grava `ExecutionLog(level=error, screenshot_path=...)` e marca `failed`.
4. O **watchdog** (Celery, a cada 60 s) re-enfileira se `attempt < max_attempts`.
5. Execuções sem progresso por `EXECUTION_TIMEOUT_MINUTES` são expiradas.

## Fluxo de agendamento

```mermaid
sequenceDiagram
    participant BT as Celery Beat
    participant WK as Worker
    participant DB as PostgreSQL
    participant AG as Agente

    BT->>WK: check_schedules (a cada 60s)
    WK->>DB: SELECT schedules WHERE enabled AND next_run_at <= now
    WK->>DB: INSERT execution (datas = últimos N dias)
    WK->>DB: UPDATE next_run_at = próximo cron
    AG->>DB: (via API) coleta a execução no próximo polling
```

Presets no dashboard: **todos os dias às 08:00** (`0 8 * * *`), **toda
segunda-feira** (`0 8 * * 1`), **todo dia 1º do mês** (`0 6 1 * *`) e cron
personalizado. Execução manual é o fluxo principal acima.

> Como o certificado só existe na máquina do cliente, agendamentos exigem o
> agente **online** no horário; jobs criados com o agente offline ficam na
> fila e são coletados assim que ele volta.

## Fluxo de matrícula do agente

1. Admin clica em **Gerar token de matrícula** (validade 15 min, uso único).
2. Na máquina do cliente: `sistema-agent --enroll <TOKEN> --api <URL>`.
3. Backend valida o token, cria o `Agent` e devolve um **token permanente**
   (guardado com hash SHA-256; exibido uma única vez).
4. O agente passa a enviar heartbeat (30 s) e a sincronizar os metadados dos
   certificados visíveis (5 min).
