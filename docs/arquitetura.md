# Arquitetura

## Visão geral

```mermaid
flowchart LR
    subgraph Cliente["Máquina do cliente (Windows)"]
        AG[Agente Desktop<br/>pystray + Playwright]
        CERT[(Repositório de<br/>certificados do SO)]
        FILES[(Pastas locais<br/>por empresa)]
        BR[Edge/Chrome]
        AG --> BR
        BR --- CERT
        AG --> FILES
    end

    subgraph Nuvem["Infraestrutura SaaS"]
        FE[Frontend<br/>Next.js]
        API[Backend<br/>FastAPI]
        DB[(PostgreSQL)]
        RD[(Redis)]
        WK[Celery Worker]
        BT[Celery Beat]
        API --- DB
        API --- RD
        WK --- DB
        BT --> WK
    end

    PORTAIS[Portais NFS-e<br/>Nacional / São Paulo]

    FE -- "HTTPS + JWT" --> API
    AG -- "HTTPS + X-Agent-Token<br/>(polling)" --> API
    BR -- "TLS mútuo com<br/>certificado ICP-Brasil" --> PORTAIS
```

## Decisões-chave

| Decisão | Justificativa |
|---|---|
| Execução no agente (não no servidor) | A chave privada do certificado (A1/A3) nunca sai da máquina do cliente; A3 é fisicamente impossível de mover. |
| Polling do agente (pull) | Funciona atrás de NAT/firewall corporativo sem abrir portas; intervalo de 10 s dá latência aceitável. |
| Arquivos permanecem locais | Requisito do produto: backend guarda apenas metadados (nome, hash, tamanho, caminho). |
| Adaptadores de portal | Cada portal muda com frequência; o contrato `PortalAdapter` isola o acoplamento e permite trocar scraping por API oficial. |
| Celery beat p/ agendamentos | Expressões cron por agendamento no banco; o beat só varre `next_run_at <= now`, escalando para milhares de agendamentos. |

## Modelo de dados

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : possui
    ORGANIZATION ||--o{ COMPANY : possui
    ORGANIZATION ||--o{ AGENT : possui
    AGENT ||--o{ CERTIFICATE : detecta
    COMPANY ||--o{ SCHEDULE : agenda
    CERTIFICATE ||--o{ SCHEDULE : usa
    SCHEDULE ||--o{ EXECUTION : dispara
    COMPANY ||--o{ EXECUTION : alvo
    AGENT ||--o{ EXECUTION : executa
    EXECUTION ||--o{ DOWNLOAD : gera
    EXECUTION ||--o{ EXECUTION_LOG : registra
    ORGANIZATION ||--o{ AUDIT_LOG : audita

    CERTIFICATE {
        uuid id PK
        string thumbprint "somente metadados"
        string subject
        string cnpj_cpf
        enum tipo "A1 | A3"
        datetime not_after
    }
    EXECUTION {
        uuid id PK
        enum status "pending..cancelled"
        json filters "start_date, end_date, extra"
        int attempt
        bool cancel_requested
    }
```

## Ciclo de vida de uma execução

```mermaid
stateDiagram-v2
    [*] --> pending : usuário ou agendamento cria
    pending --> dispatched : agente coleta no polling
    pending --> cancelled : cancelamento imediato
    dispatched --> running : agente abre o navegador
    running --> success : todos os downloads concluídos
    running --> failed : erro (com screenshot)
    running --> cancelled : cancelamento confirmado pelo agente
    failed --> pending : watchdog re-tenta (attempt < max)
    dispatched --> failed : timeout do watchdog
    running --> failed : timeout do watchdog
    success --> [*]
    cancelled --> [*]
```

## Camadas do backend

```
app/
├── api/v1/        # Rotas HTTP (controllers) — validação e autorização
├── schemas/       # Contratos Pydantic (entrada/saída)
├── services/      # Regras de negócio reutilizáveis (auditoria, cron, matrícula)
├── models/        # Entidades SQLAlchemy (persistência)
├── workers/       # Tarefas Celery (agendador, watchdog, limpeza)
└── core/          # Config, segurança, banco, rate limit, dependências
```

Dependências apontam para dentro (API → services → models), seguindo
Clean Architecture pragmática. Tipagem forte em todas as camadas
(SQLAlchemy 2 `Mapped[]`, Pydantic v2, TypeScript `strict`).
