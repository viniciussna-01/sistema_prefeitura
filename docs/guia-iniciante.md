# Guia do Iniciante — Como rodar e atualizar o sistema

Este guia foi escrito para quem está começando agora. Ele não pressupõe
conhecimento de Docker, terminal ou servidores. Vá com calma, uma etapa por vez.

---

## 1. Entendendo o que você tem (o "mapa mental")

O sistema tem **três partes**. Pense assim:

| Parte | O que é | Onde roda |
|---|---|---|
| **Backend** | O "cérebro": guarda os dados e as regras | No seu computador (via Docker) ou num servidor |
| **Frontend** | A tela bonita que você abre no navegador | No seu computador (via Docker) ou num servidor |
| **Agente** | Programinha que usa o certificado e baixa os documentos | **Sempre** na máquina Windows que tem o certificado |

> **Analogia com o que você já conhece:** o Backend é como o banco de dados
> por trás de um relatório Power BI; o Frontend é o relatório em si (a parte
> visual); e o Agente é como uma macro do Excel que roda na sua máquina e
> interage com um site.

**Importante desde já:** rodar o Backend + Frontend com Docker vai te dar o
**sistema web completo funcionando** (login, cadastro de empresas,
agendamentos, painel...). Mas o **download real de notas** só acontece quando
o **Agente** está instalado numa máquina Windows com um **certificado digital
de verdade**. Para aprender e testar a plataforma, começamos pelo Backend +
Frontend.

---

## 2. O que é o Docker (e por que usamos)

Para o sistema funcionar, normalmente você precisaria instalar no seu
computador: Python, Node.js, um banco de dados (PostgreSQL), o Redis... É
trabalhoso e dá erro fácil.

O **Docker** resolve isso: ele cria "caixinhas" prontas (chamadas
*containers*) que já vêm com tudo instalado por dentro. Você dá **um comando**
e ele sobe tudo junto, configurado. Quando termina, você desliga e não deixa
sujeira no seu computador.

> Pense no Docker como um "mini-computador dentro do seu computador", já
> montado do jeito certo.

---

## 3. Instalando o Docker (só uma vez)

1. Acesse: https://www.docker.com/products/docker-desktop/
2. Baixe o **Docker Desktop para Windows** e instale (avançar, avançar,
   concluir). Ele pode pedir para reiniciar o computador — pode reiniciar.
3. Abra o **Docker Desktop**. Espere aparecer que ele está *running*
   (rodando). Deixe-o aberto sempre que for usar o sistema.

Pronto. Isso é feito **uma única vez**.

---

## 4. Trazendo o código para o seu computador

O código está no GitHub. Para baixá-lo você usa o **Git**.

1. Instale o Git: https://git-scm.com/download/win (avançar, avançar,
   concluir).
2. Crie uma pasta onde quiser guardar o projeto, por exemplo `C:\projetos`.
3. Abra o **Prompt de Comando** (aperte a tecla Windows, digite `cmd`, Enter).
4. Digite os comandos abaixo, **um de cada vez**, apertando Enter no fim de
   cada linha:

```cmd
cd C:\projetos
git clone https://github.com/viniciussna-01/sistema_prefeitura.git
cd sistema_prefeitura
git checkout claude/vigilant-lamport-lsl616
```

> O que cada linha faz:
> - `cd C:\projetos` → entra na sua pasta de projetos
> - `git clone ...` → **baixa** o projeto do GitHub
> - `cd sistema_prefeitura` → entra na pasta do projeto
> - `git checkout ...` → muda para a versão (branch) onde está o código

---

## 5. Criando o arquivo de configuração (`.env`)

O sistema precisa de um arquivo chamado `.env` com algumas senhas. Existe um
modelo pronto (`.env.example`); vamos copiá-lo. Ainda no Prompt de Comando,
dentro da pasta do projeto:

```cmd
copy .env.example .env
```

Para **aprender e testar na sua máquina**, o modelo já funciona como está.
(Quando for colocar no ar de verdade, aí sim trocamos as senhas — isso está
explicado no arquivo `docs/seguranca.md`.)

---

## 6. Ligando o sistema 🚀

Com o Docker Desktop aberto e você dentro da pasta do projeto, digite:

```cmd
docker compose up -d --build
```

- Na **primeira vez** demora alguns minutos (ele está montando as caixinhas).
  Tome um café. ☕
- Quando terminar, o sistema está no ar!

Abra o navegador e acesse:

- **A tela do sistema:** http://localhost:3000
- **A documentação técnica da API** (opcional): http://localhost:8000/docs

---

## 7. Primeiro uso

1. Em http://localhost:3000, clique em **Criar organização**.
2. Preencha nome da sua empresa/escritório, seu nome, e-mail e uma senha
   (mínimo 8 caracteres). Você será o **administrador**.
3. Explore o painel: cadastre uma **Empresa**, veja o **Dashboard**, crie um
   **Agendamento**.
4. Para o download real de notas, seria necessário instalar o **Agente** numa
   máquina com certificado (veja `docs/agente.md`) — mas para conhecer a
   plataforma, você já pode navegar por tudo.

---

## 8. Desligar e ligar de novo (sem perder nada)

**Para desligar** (os dados ficam guardados):

```cmd
docker compose stop
```

**Para ligar de novo depois:**

```cmd
docker compose start
```

**Para desligar e apagar as caixinhas** (os dados no banco continuam salvos
num volume do Docker):

```cmd
docker compose down
```

**Ver o que está acontecendo por dentro** (útil se algo der errado):

```cmd
docker compose logs -f
```

(Para sair dos logs, aperte `Ctrl + C`.)

---

## 9. Como ATUALIZAR o sistema

Existem duas situações diferentes. Entenda cada uma.

### Situação A — Pegar a versão mais nova do GitHub

Se alguém (você ou eu) melhorou o código no GitHub e você quer trazer as
novidades para o seu computador:

```cmd
cd C:\projetos\sistema_prefeitura
git pull
docker compose up -d --build
```

- `git pull` → **baixa as mudanças** do GitHub.
- `docker compose up -d --build` → **remonta** as caixinhas com o código novo.

### Situação B — Você mesmo mudou algum arquivo

Digamos que você editou um texto, uma cor ou um comportamento no código.

1. **Aplicar a mudança no sistema que roda na sua máquina:**

```cmd
docker compose up -d --build
```

2. **Salvar sua mudança no GitHub** (para não perder e poder compartilhar):

```cmd
git add .
git commit -m "descreva aqui o que você mudou"
git push
```

> - `git add .` → seleciona **tudo que você mudou**
> - `git commit -m "..."` → **tira uma foto** dessas mudanças com um recado
> - `git push` → **envia** para o GitHub

---

## 10. Quando algo der errado (calma!)

- **A tela não abre em localhost:3000** → confira se o Docker Desktop está
  aberto e "running"; espere 1–2 minutos após o `up`; rode
  `docker compose logs -f` para ver mensagens.
- **Deu erro no `docker compose up`** → geralmente é o Docker Desktop que não
  está aberto. Abra-o e tente de novo.
- **Quero começar do zero** → `docker compose down` e depois
  `docker compose up -d --build`.
- **Travei em algum comando** → aperte `Ctrl + C` para cancelar e recomeçar.

Nada que você faça aqui estraga seu computador. No pior caso, a gente
desliga tudo e sobe de novo.

---

## 11. Resumo dos comandos (cola rápida)

```cmd
:: Ligar
docker compose up -d --build

:: Desligar (mantém dados)
docker compose stop

:: Ligar de novo
docker compose start

:: Ver logs
docker compose logs -f

:: Atualizar do GitHub
git pull
docker compose up -d --build

:: Salvar suas mudanças no GitHub
git add .
git commit -m "o que mudei"
git push
```

Guarde este arquivo. Você não precisa decorar nada — é só consultar. 🙂
