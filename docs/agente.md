# Agente Desktop

Aplicativo Windows que roda em segundo plano (bandeja do sistema) na máquina
que possui os certificados digitais. É o único componente que toca o
navegador e os portais.

## Responsabilidades

- Detectar certificados A1/A3 no repositório pessoal do Windows (`MY`).
- Enviar ao backend **apenas metadados** dos certificados.
- Coletar trabalhos por polling (10 s) e executar a automação Playwright.
- Organizar os downloads por empresa, renomeando colisões.
- Reportar progresso, logs, screenshots de falha e metadados dos arquivos.
- Auto-atualizar quando o backend anunciar versão nova.

## Instalação

```powershell
# Via fonte
cd agent
pip install -e .
sistema-agent --enroll <TOKEN_DE_MATRICULA> --api https://api.suaempresa.com.br
sistema-agent            # bandeja do sistema
sistema-agent --console  # modo console (debug/servidores)

# Executável standalone
pip install pyinstaller
pyinstaller build.spec   # → dist/SistemaPrefeituraAgent.exe
```

Para iniciar com o Windows: crie um atalho do executável em
`shell:startup` ou uma tarefa no Agendador de Tarefas.

## Configuração

`%APPDATA%\SistemaPrefeituraAgent\config.json`:

```json
{
  "api_url": "https://api.suaempresa.com.br",
  "agent_token": "…",
  "downloads_dir": "C:\\Users\\voce\\Downloads\\SistemaPrefeitura",
  "poll_interval_seconds": 10,
  "headless": false
}
```

## Certificados: como funciona (e o que nunca fazemos)

- **Nunca** exportamos, copiamos ou transmitimos a chave privada.
- A1 (arquivo instalado no repositório) e A3 (token/smartcard via CSP/KSP)
  são usados **pelo próprio navegador** no handshake TLS.
- O agente grava temporariamente a política
  `HKCU\Software\Policies\{Microsoft\Edge,Google\Chrome}\AutoSelectCertificateForUrls`
  restrita à URL do portal, para evitar o diálogo nativo de seleção; a
  política é removida ao final da execução (mesmo em caso de erro).
- Certificados A3 podem exigir o PIN do token — o diálogo do PIN é do
  middleware do fabricante e o usuário deve autorizá-lo (requisito de
  consentimento explícito).

## Estrutura do código

```
sistema_agent/
├── main.py           # CLI + bandeja do sistema
├── runner.py         # loop: heartbeat, certificados, jobs
├── api_client.py     # HTTPS com o backend
├── certificates.py   # enumeração/parse (somente metadados)
├── browser.py        # canal Edge/Chrome + política de auto-seleção
├── downloads.py      # organização e renomeio dos arquivos
├── updater.py        # auto-update (.new + swap script)
└── automation/
    ├── base.py           # contrato PortalAdapter + JobContext
    ├── registry.py       # portal → adaptador
    ├── nfse_nacional.py  # Emissor Nacional (www.nfse.gov.br)
    └── nfse_sp.py        # Prefeitura de São Paulo
```

## Escrevendo um novo adaptador

```python
class MeuPortalAdapter(PortalAdapter):
    certificate_url_pattern = "https://portal.exemplo.gov.br"

    def authenticate(self, page, ctx): ...
    def apply_filters(self, page, ctx): ...
    def list_documents(self, page, ctx) -> list[DocumentRef]: ...
    def download_document(self, page, ctx, doc, tmp_dir) -> Path: ...
```

Registre em `registry.py` e adicione o valor ao enum `Portal` no backend e
no frontend. **Se o portal tiver API oficial autorizada, implemente o
adaptador consumindo a API** (sem `page`) — o contrato aceita qualquer
estratégia interna.

> Os seletores dos adaptadores refletem a estrutura atual dos portais e
> devem ser validados em homologação; mudanças de layout do portal exigem
> ajuste apenas no arquivo do adaptador correspondente.
