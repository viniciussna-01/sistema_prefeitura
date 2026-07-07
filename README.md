# Sistema Prefeitura — SaaS de Automação Fiscal com Certificado Digital

SaaS multi-tenant que automatiza o download de documentos fiscais dos portais
**NFS-e Nacional** (www.nfse.gov.br) e **NFS-e Prefeitura de São Paulo**
(nfe.prefeitura.sp.gov.br), autenticando com o **certificado digital
ICP-Brasil (A1/A3) instalado na máquina do cliente** — a chave privada nunca
sai do computador do usuário.

```
┌────────────┐   HTTPS/JWT   ┌────────────┐   HTTPS/token   ┌──────────────────┐
│  Frontend  │ ────────────► │  Backend   │ ◄─────────────  │  Agente Desktop  │
│  Next.js   │               │  FastAPI   │    (polling)    │  Windows/tray    │
└────────────┘               │ +Celery    │                 │  Playwright +    │
                             │ +Postgres  │                 │  cert. do SO     │
                             │ +Redis     │                 └──────────────────┘
                             └────────────┘                          │
                                                              Portais NFS-e
```

## Componentes

| Camada | Pasta | Stack |
|---|---|---|
| Frontend web | `frontend/` | Next.js 14, React 18, TypeScript, Tailwind (dark/light) |
| Backend API | `backend/` | Python 3.12, FastAPI, SQLAlchemy 2 (async), PostgreSQL, Redis, Celery |
| Agente desktop | `agent/` | Python, Playwright, bandeja do sistema (pystray), auto-update |

Documentação detalhada em [`docs/`](docs/):
[arquitetura e diagramas](docs/arquitetura.md) · [fluxos](docs/fluxos.md) ·
[API](docs/api.md) · [agente desktop](docs/agente.md) · [segurança](docs/seguranca.md)

## Subindo o ambiente (Docker)

```bash
cp .env.example .env
# edite SECRET_KEY, ENCRYPTION_KEY e senhas (instruções dentro do arquivo)
docker compose up -d --build
```

- Frontend: http://localhost:3000
- API + Swagger: http://localhost:8000/docs

Primeiro acesso: crie sua organização em `/register` (o primeiro usuário é
administrador), cadastre empresas, gere um **token de matrícula** na página
*Agentes* e instale o agente na máquina Windows que possui os certificados.

## Agente desktop (máquina do cliente, Windows)

```powershell
cd agent
pip install -e .
playwright install chromium   # opcional; o agente prefere Edge/Chrome do sistema
sistema-agent --enroll <TOKEN> --api https://api.suaempresa.com.br
sistema-agent                 # roda em segundo plano com ícone na bandeja
```

Executável standalone: `pip install pyinstaller && pyinstaller build.spec`
(gera `dist/SistemaPrefeituraAgent.exe`). O auto-update é controlado pelas
variáveis `AGENT_LATEST_VERSION` e `AGENT_DOWNLOAD_URL` do backend.

### Como o certificado é usado (sem exportar a chave!)

1. O agente **enumera** o repositório de certificados do Windows e envia ao
   backend **apenas metadados** (titular, CNPJ/CPF, validade, thumbprint).
2. Na execução, o navegador (Edge/Chrome via Playwright) faz o handshake TLS
   usando o repositório do Windows — inclusive tokens A3 via CSP/KSP.
3. A política `AutoSelectCertificateForUrls` é gravada temporariamente no
   registro (HKCU), restrita à URL do portal, para o navegador escolher o
   certificado sem diálogo nativo; é removida ao final.

## Organização dos downloads

Os arquivos ficam **na máquina do cliente**, um arquivo por documento (nunca
consolidados), organizados por empresa:

```
Downloads/SistemaPrefeitura/
├── Empresa_A/
│   ├── Documento_001.xlsx
│   └── Empresa_A_20260706_101500_123.xlsx   ← renomeado em colisão
└── Empresa_B/
    └── Documento_001.xlsx
```

O backend registra os metadados (nome, tamanho, SHA-256, caminho) para
histórico e auditoria no dashboard.

## Desenvolvimento local (sem Docker)

```bash
# Backend
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload          # usa SQLite por padrão

# Worker + beat (exigem Redis)
.venv/bin/celery -A app.workers.celery_app worker -B --loglevel=info

# Frontend
cd frontend && npm install && npm run dev

# Agente (modo console, qualquer SO para desenvolvimento)
cd agent && pip install -e . && sistema-agent --console
```

## Testes

```bash
cd backend && .venv/bin/python -m pytest    # 18 testes (API, permissões, fluxo completo)
cd agent   && python -m pytest              # 10 testes (downloads, certificados, adaptadores)
cd frontend && npm run typecheck && npm run build
```

## Migrações (produção)

Em desenvolvimento o schema é criado automaticamente. Em produção
(`ENVIRONMENT=production`), use Alembic:

```bash
cd backend
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## Escalabilidade e confiabilidade

- **Multi-tenant**: isolamento por organização em todas as consultas.
- **Filas**: Celery + Redis; beat dispara agendamentos e o *watchdog*.
- **Retry automático**: falhas voltam à fila até `EXECUTION_MAX_ATTEMPTS`.
- **Timeout**: execuções travadas expiram após `EXECUTION_TIMEOUT_MINUTES`.
- **Cancelamento**: propagado ao agente durante a execução.
- **Paralelismo**: vários agentes por organização; cada agente processa sua fila.
- **Monitoramento**: dashboard com atualização automática (polling 5–15 s).

## Adicionando um novo portal

Implemente `PortalAdapter` em `agent/sistema_agent/automation/`, registre em
`registry.py` e adicione o valor ao enum `Portal` do backend/frontend. Se o
portal oferecer **API oficial autorizada, prefira um adaptador de API** ao
invés de automação de interface — o contrato é o mesmo.

## Licença / Aviso

Automação de portais governamentais deve respeitar os termos de uso de cada
portal. Use com autorização dos titulares dos certificados.
